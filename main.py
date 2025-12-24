# main.py - SIMPLIFIED (no separate translator import)
import asyncio
import os
from datetime import datetime
from telegram_auth import TelegramAuth
from telegram_fetch import MessageFetcher
from telegram_master_xlsx import TelegramMasterXLSX
from sqlite_backup import SQLiteBackup

async def main():
    """Main script with integrated translation"""
    print("="*60)
    print("🤖 TELEGRAM SCRAPER WITH AUTO-TRANSLATION")
    print("🌍 Timezone: Asia/Kolkata | Auto-translate: Any language → English")
    print("="*60)

    # Initialize components - translation is built-in!
    auth = TelegramAuth()
    master = TelegramMasterXLSX()
    sqlite_backup = SQLiteBackup()

    try:
        # Connect to Telegram
        print("🔐 Connecting to Telegram...")
        connected = await auth.connect()
        if not connected:
            print("❌ Failed to connect")
            return

        # Get channels
        print("📡 Discovering channels...")
        channels_data = await auth.get_channels(limit=50)
        if not channels_data:
            print("❌ No channels found")
            await auth.disconnect()
            return

        # Show stats
        stats_before = master.get_stats()
        print(f"\n📊 MASTER FILE STATS:")
        print(f"   Total messages: {stats_before['total_messages']:,}")
        print(f"   Channels in DB: {stats_before['channels']}")

        # Initialize fetcher
        fetcher = MessageFetcher(auth.client)

        # Process channels
        print("\n" + "="*60)
        print("🚀 PROCESSING & TRANSLATING CHANNELS")
        print("="*60)

        total_new_messages = 0
        processed_channels = 0

        for i, channel in enumerate(channels_data, 1):
            print(f"\n[{i}/{len(channels_data)}] 📢 {channel['name']}")
            print("-" * 40)

            # Fetch messages
            messages = await fetcher.fetch_messages(
                channel["dialog"], days_back=datetime.now().day - 1, limit=1000
            )

            if messages:
                # Format messages for CSV
                formatted_messages = []

                for msg in messages:
                    formatted_messages.append(
                        {
                            "channel_id": channel["id"],
                            "channel_name": channel["name"],
                            "message_id": msg["message"].id,
                            "global_id": msg.get("global_id"),
                            "datetime_utc": msg["datetime_utc"],
                            "datetime_local": msg["datetime_local"],
                            "sender_id": msg["sender_id"],
                            "sender_name": msg["sender_name"],
                            "text": msg["text"],
                            "media_type": msg["media_type"],
                            "views": msg["views"],
                            "forwards": msg["forwards"],
                        }
                    )

                # Add to master - translation happens here!
                new_count = master.add_messages(formatted_messages, channel["name"])

                # Backup to SQLite
                if new_count > 0:
                    sqlite_backup.backup_messages(formatted_messages, channel["name"])
                    print(f"   💾 Backed up {new_count} messages to SQLite")

                total_new_messages += new_count
                processed_channels += 1

                # Show channel summary
                if new_count > 0:
                    print(f"   ✅ Added {new_count} new messages")
            else:
                print(f"   📭 No new messages found")

        # Final summary
        print("\n" + "="*60)
        print("📊 FINAL SUMMARY")
        print("="*60)

        stats_after = master.get_stats()

        print(f"Channels processed: {len(channels_data)}")
        print(f"Channels with new messages: {processed_channels}")
        print(f"New messages added: {total_new_messages}")
        print(f"Total in master: {stats_after['total_messages']:,}")

        if stats_before["total_messages"] > 0:
            growth = (
                (stats_after["total_messages"] - stats_before["total_messages"])
                / stats_before["total_messages"]
                * 100
            )
            print(f"Database growth: +{growth:.1f}%")

        # Show SQLite backup stats
        backup_stats = sqlite_backup.get_backup_stats()
        print(f"💾 SQLite backup stats:")
        print(f"   Total messages: {backup_stats['total_messages']:,}")
        print(f"   Total channels: {backup_stats['total_channels']}")
        print(f"   Database size: {backup_stats['database_size']:,} bytes")

        print(f"\n📁 Master file: {os.path.abspath(master.master_file)}")
        print("✨ Process complete! All non-English messages are automatically translated to English.")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await auth.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
