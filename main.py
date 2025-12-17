# main.py - COMPLETE WORKING VERSION
import asyncio
import os
from telegram_auth import TelegramAuth
from telegram_fetch import MessageFetcher
from telegram_master_csv import TelegramMasterCSV

async def main():
    """Main script with master CSV"""
    print("="*60)
    print("🤖 TELEGRAM MASTER CSV SCRAPER")
    print("🌍 Timezone: Asia/Kolkata | Days: Last 3")
    print("="*60)

    # Initialize components
    auth = TelegramAuth()
    csv_master = TelegramMasterCSV()  # Single master file

    try:
        # Step 1: Connect to Telegram
        connected = await auth.connect()  # Fixed: Now has connect() method
        if not connected:
            print("❌ Failed to connect to Telegram")
            return

        # Step 2: Get channels
        channels_data = await auth.get_channels(
            limit=50
        )  # Fixed: Now has get_channels() method
        if not channels_data:
            print("❌ No channels found")
            await auth.disconnect()
            return

        # Show stats before processing
        stats_before = csv_master.get_stats()
        print(f"\n📊 CURRENT MASTER STATS:")
        print(f"   Total messages: {stats_before['total_messages']:,}")
        print(f"   Channels in DB: {stats_before['channels']}")

        # Step 3: Initialize fetcher
        fetcher = MessageFetcher(auth.client)

        # Step 4: Process channels
        print("\n" + "="*60)
        print("🚀 PROCESSING CHANNELS")
        print("="*60)

        total_new_messages = 0
        processed_channels = 0

        for i, channel in enumerate(channels_data, 1):
            print(f"\n[{i}/{len(channels_data)}] Processing: {channel['name']}")

            # Fetch messages
            messages = await fetcher.fetch_messages(
                channel["dialog"], days_back=3, limit=1000
            )

            if messages:
                # Format for CSV
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

                # Add to master CSV
                new_count = csv_master.add_messages(formatted_messages, channel["name"])
                total_new_messages += new_count
                processed_channels += 1
            else:
                print(f"   📭 No new messages found")

        # Final stats
        print("\n" + "="*60)
        print("📊 FINAL SUMMARY")
        print("="*60)

        stats_after = csv_master.get_stats()

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
            print(f"Growth: +{growth:.1f}%")

        print(f"\n📁 Master file: {os.path.abspath(csv_master.master_file)}")
        print("\n✨ Process complete!")

    except Exception as e:
        print(f"❌ Error in main: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Always disconnect
        await auth.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
