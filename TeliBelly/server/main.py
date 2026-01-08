# main.py - SIMPLIFIED (no separate translator import)
import asyncio
import os
import sqlite3
import asyncio
from datetime import datetime, timedelta
from telegram_auth import TelegramAuth
from telegram_fetch import MessageFetcher
from telegram_master_xlsx import TelegramMasterXLSX
from sqlite_backup import SQLiteBackup

def is_db_empty(db_path: str) -> bool:
    """Check if the messages table in the database is empty."""
    if not os.path.exists(db_path):
        return True
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            # Check if messages table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
            if cursor.fetchone() is None:
                return True # Table doesn't exist, so it's empty
            
            cursor.execute("SELECT COUNT(*) FROM messages")
            count = cursor.fetchone()[0]
            return count == 0
    except (sqlite3.OperationalError, IndexError):
        # Handle cases where the DB is malformed or table doesn't exist
        return True

async def process_channel(channel, i, total_channels, db_path, fetcher, master, sqlite_backup, lock):
    """Processes a single channel: fetches, translates, and backs up messages."""
    print(f"[{i}/{total_channels}] 📢 Starting: {channel['name']}")
    try:
        # --- Ensure channel exists in the database ---
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM channels WHERE channel_name = ?", (channel['name'],))
                if not cursor.fetchone():
                    today = datetime.now()
                    first_day_of_current_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    first_day_of_previous_month = (first_day_of_current_month - timedelta(days=1)).replace(day=1)
                    cursor.execute(
                        "INSERT INTO channels (channel_id, channel_name, last_backup_timestamp) VALUES (?, ?, ?)",
                        (channel['id'], channel['name'], first_day_of_previous_month.isoformat())
                    )
                    conn.commit()
                    print(f"   ℹ️ Added new channel '{channel['name']}' to DB.")
        except Exception as e:
            print(f"   ⚠️ Error ensuring channel '{channel['name']}' exists: {e}. Skipping.")
            return 0

        # --- Determine days_back for this channel ---
        days_back = 30
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT last_backup_timestamp FROM channels WHERE channel_name = ?", (channel['name'],))
                row = cursor.fetchone()
                if row and row[0]:
                    timestamp_str = row[0]
                    try:
                        last_backup_date = datetime.fromisoformat(timestamp_str)
                    except ValueError:
                        last_backup_date = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    days_diff = (datetime.now() - last_backup_date).days
                    days_back = min(30, max(1, days_diff))
                    print(f"   🗓️ Last backup for '{channel['name']}' was {days_diff} days ago. Fetching {days_back} days.")
                else:
                    print(f"   🗓️ No backup timestamp for '{channel['name']}'. Fetching last 30 days.")
        except Exception as e:
            print(f"   ⚠️ Could not query last backup timestamp for '{channel['name']}' ({e}). Fetching last 30 days.")

        # --- Fetch messages (concurrent part) ---
        messages = await fetcher.fetch_messages(channel["dialog"], days_back=days_back, limit=1000)

        if not messages:
            print(f"   📭 No new messages found for '{channel['name']}'.")
            return 0

        # --- Format messages ---
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "channel_id": channel["id"], "channel_name": channel["name"],
                "message_id": msg["message"].id, "global_id": msg.get("global_id"),
                "datetime_utc": msg["datetime_utc"], "datetime_local": msg["datetime_local"],
                "sender_id": msg["sender_id"], "sender_name": msg["sender_name"],
                "text": msg["text"], "media_type": msg["media_type"],
                "views": msg["views"], "forwards": msg["forwards"],
            })

        # --- CRITICAL SECTION: Writing to shared files (Excel/DB) ---
        newly_added_count = 0
        async with lock:
            # Add to master Excel file (and perform translation)
            new_to_master_count = master.add_messages(formatted_messages, channel["name"])
            
            # Backup to SQLite database
            if new_to_master_count > 0:
                sqlite_backup.backup_messages(formatted_messages, channel["name"])
                newly_added_count = new_to_master_count
        
        if newly_added_count > 0:
            print(f"   ✅ Added {newly_added_count} new messages for '{channel['name']}'.")
        else:
            # This can happen if messages were fetched but already exist in the master file
            print(f"   ☑️ Fetched {len(messages)} messages for '{channel['name']}', but none were new.")

        return newly_added_count

    except Exception as e:
        print(f"❌ Error processing channel {channel['name']}: {e}")
        import traceback
        traceback.print_exc()
        return 0

async def main():
    """Main script with integrated translation"""
    print("="*60)
    print("🤖 TELEGRAM SCRAPER WITH AUTO-TRANSLATION")
    print("🌍 Timezone: Asia/Kolkata | Auto-translate: Any language → English")
    print("="*60)

    # Initialize components - translation is built-in!
    auth = TelegramAuth()
    outputDirectory = "../data"
    db_path = outputDirectory + "/telegram_backup.db"
    master_file_path = outputDirectory + "/telegram_messages_master.xlsx"
    
    master = TelegramMasterXLSX(
        master_file_path,
        db_path,
    )
    sqlite_backup = SQLiteBackup(db_path)

    # If DB is empty but master file is not, backup master file and start fresh
    if is_db_empty(db_path):
        if hasattr(master, 'master_file') and os.path.exists(master.master_file):
            print("ℹ️ Database message table is empty, but a master file exists.")
            backup_path = master.master_file + f".bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            print(f"   Backing up existing master file to '{backup_path}' to ensure a fresh start.")
            os.rename(master.master_file, backup_path)
            
            # Re-initialize master to have an empty cache and work with a new file
            master = TelegramMasterXLSX(master_file_path, db_path)

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

        # Show stats before processing
        stats_before = master.get_stats()
        print(f"\n📊 MASTER FILE STATS (before run):")
        print(f"   Total messages: {stats_before['total_messages']:,}")
        print(f"   Channels in DB: {stats_before['channels']}")

        # Initialize fetcher and lock for concurrency
        fetcher = MessageFetcher(auth.client)
        lock = asyncio.Lock()

        # Process channels concurrently
        print("\n" + "="*60)
        print(f"🚀 CONCURRENTLY PROCESSING {len(channels_data)} CHANNELS")
        print("="*60)

        tasks = []
        for i, channel in enumerate(channels_data, 1):
            task = process_channel(channel, i, len(channels_data), db_path, fetcher, master, sqlite_backup, lock)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)

        # Final summary
        print("\n" + "="*60)
        print("📊 FINAL SUMMARY")
        print("="*60)
        
        total_new_messages = sum(r for r in results if r is not None)
        channels_with_new_messages = sum(1 for r in results if r is not None and r > 0)

        stats_after = master.get_stats()

        print(f"Channels processed: {len(channels_data)}")
        print(f"Channels with new messages: {channels_with_new_messages}")
        print(f"New messages added to master file: {total_new_messages}")
        print(f"Total in master: {stats_after['total_messages']:,}")

        if stats_before["total_messages"] > 0 and (stats_after["total_messages"] - stats_before["total_messages"]) > 0:
            growth = ((stats_after["total_messages"] - stats_before["total_messages"]) / stats_before["total_messages"] * 100)
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
        print(f"❌ Error in main execution: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if 'auth' in locals() and auth.client.is_connected():
            await auth.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
