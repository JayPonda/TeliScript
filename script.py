import asyncio
from datetime import datetime, timedelta
from telethon import TelegramClient
import pytz
import os
import sys
import csv
import dotenv

dotenv.load_dotenv()

def validate_environment():
    """Validate and load environment variables"""
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("💡 Create a .env file with these contents:")
        print("""
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_PHONE_NUMBER=+1234567890
""")
        sys.exit(1)

    from dotenv import load_dotenv
    load_dotenv()

    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE_NUMBER')

    errors = []
    if not api_id:
        errors.append("TELEGRAM_API_ID not set")
    elif not api_id.isdigit():
        errors.append("TELEGRAM_API_ID must contain only digits")

    if not api_hash:
        errors.append("TELEGRAM_API_HASH not set")

    if not phone:
        errors.append("TELEGRAM_PHONE_NUMBER not set")
    elif not phone.startswith('+'):
        errors.append("TELEGRAM_PHONE_NUMBER must start with '+'")

    if errors:
        print("❌ Configuration errors:")
        for error in errors:
            print(f"   - {error}")
        sys.exit(1)

    return int(api_id), api_hash, phone


def save_messages_to_csv(messages, channel_name, channel_id, filename=None):
    """Save messages to CSV file with ALL identifiers"""
    if not messages:
        return None

    if not filename:
        clean_name = "".join(
            c if c.isalnum() or c in " _-" else "_" for c in channel_name
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"telegram_{clean_name}_{timestamp}.csv"

    try:
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            # Enhanced header with all identifiers
            writer.writerow(
                [
                    "Channel_ID",
                    "Channel_Name",
                    "Message_ID",
                    "Global_ID",
                    "Date_UTC",
                    "Date_Local",
                    "Sender_ID",
                    "Sender_Name",
                    "Message_Type",
                    "Message_Text",
                    "Views",
                    "Forwards",
                    "Replies",
                    "Media_Type",
                ]
            )

            for item in messages:
                msg = item["message"]
                msg_utc = item["datetime_utc"]
                msg_local = item["datetime_local"]

                # Get message identifiers
                message_id = msg.id  # Chat-specific message ID
                global_id = getattr(
                    msg, "global_id", "N/A"
                )  # Global message ID if available

                # Get sender info with ID
                sender_name = item.get("sender_name", channel_name)
                sender_id = item.get("sender_id", "")

                # Get message type
                message_type = "text"
                media_type = "none"
                if msg.media:
                    message_type = "media"
                    media_type = msg.media.__class__.__name__.replace(
                        "MessageMedia", ""
                    )
                elif msg.sticker:
                    message_type = "sticker"
                    media_type = "sticker"
                elif msg.poll:
                    message_type = "poll"
                    media_type = "poll"

                # Get message content
                message_text = ""
                if msg.text:
                    message_text = msg.text.replace("\n", " ").replace("\r", " ")[:2000]

                # Get engagement metrics
                views = getattr(msg, "views", 0) or 0
                forwards = getattr(msg, "forwards", 0) or 0
                replies = getattr(msg, "replies", None)
                reply_count = (
                    replies.replies if replies and hasattr(replies, "replies") else 0
                )

                writer.writerow(
                    [
                        channel_id,
                        channel_name,
                        message_id,
                        global_id,
                        msg_utc.strftime("%Y-%m-%d %H:%M:%S"),
                        msg_local.strftime("%Y-%m-%d %H:%M:%S"),
                        sender_id,
                        sender_name,
                        message_type,
                        message_text,
                        views,
                        forwards,
                        reply_count,
                        media_type,
                    ]
                )

        return os.path.abspath(filename)
    except Exception as e:
        print(f"❌ Error saving CSV: {e}")
        return None


async def get_channel_messages(client, channel_dialog, days_back=3):
    """Get messages from a specific channel for last N days with full IDs"""
    channel_name = channel_dialog.name
    channel_id = channel_dialog.entity.id

    print(f"\n📡 Processing: {channel_name} (ID: {channel_id})")
    print("-" * 60)

    tz = pytz.timezone("Asia/Kolkata")
    now_local = datetime.now(tz)
    start_date_local = now_local - timedelta(days=days_back)
    start_date_utc = start_date_local.astimezone(pytz.UTC)

    print(
        f"   Date range: {start_date_local.strftime('%Y-%m-%d')} to {now_local.strftime('%Y-%m-%d')}"
    )

    messages = []
    message_count = 0

    try:
        # Get detailed message information
        async for message in client.iter_messages(channel_dialog.entity, limit=1000):
            message_count += 1
            msg_utc = message.date.replace(tzinfo=pytz.UTC)

            # Stop if we're getting messages older than the date range
            if msg_utc < start_date_utc:
                if message_count <= 10:  # If very few messages, show all
                    continue
                else:
                    break

            # Convert to local time
            msg_local = msg_utc.astimezone(tz)

            # Only include if within date range
            if start_date_local <= msg_local <= now_local:
                # Get sender info with ID
                sender_name = channel_name
                sender_id = ""
                try:
                    sender = await message.get_sender()
                    if sender:
                        # Get sender ID
                        sender_id = getattr(sender, "id", "")

                        # Get sender name
                        if hasattr(sender, "title"):
                            sender_name = sender.title
                        elif hasattr(sender, "first_name"):
                            sender_name = sender.first_name
                            if hasattr(sender, "last_name") and sender.last_name:
                                sender_name += f" {sender.last_name}"

                        # Add username if available
                        if hasattr(sender, "username") and sender.username:
                            sender_name += f" (@{sender.username})"
                except:
                    pass

                messages.append(
                    {
                        "datetime_utc": msg_utc,
                        "datetime_local": msg_local,
                        "message": message,
                        "sender_name": sender_name,
                        "sender_id": sender_id,
                    }
                )

        print(
            f"   📊 Scanned {message_count} messages, found {len(messages)} from last {days_back} days"
        )

        if messages:
            # Show sample of message IDs
            print(f"   🆔 Sample Message IDs: ", end="")
            sample_ids = [str(msg["message"].id) for msg in messages[:3]]
            print(", ".join(sample_ids))
            if len(messages) > 3:
                print(f"   ... and {len(messages)-3} more")

            # Save to CSV with all identifiers
            csv_file = save_messages_to_csv(messages, channel_name, channel_id)
            if csv_file:
                print(f"   💾 Saved with IDs to: {os.path.basename(csv_file)}")

            return len(messages), csv_file, messages
        else:
            print(f"   📭 No messages from last {days_back} days")
            return 0, None, []

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return 0, None, []


async def show_message_id_example(client, channel_dialog):
    """Show detailed example of message identifiers"""
    print("\n" + "=" * 60)
    print("🔍 MESSAGE ID EXAMPLE")
    print("=" * 60)

    try:
        # Get one message to show all details
        async for message in client.iter_messages(channel_dialog.entity, limit=1):
            print(f"Channel: {channel_dialog.name}")
            print(f"Channel ID: {channel_dialog.entity.id}")
            print(f"Message ID (in this chat): {message.id}")
            print(f"Date: {message.date}")

            # Try to get global ID if available
            if hasattr(message, "global_id"):
                print(f"Global Message ID: {message.global_id}")
            else:
                print(f"Global Message ID: Not available in this API response")

            # Get sender info
            sender = await message.get_sender()
            if sender:
                print(f"Sender ID: {sender.id}")
                if hasattr(sender, "username"):
                    print(f"Sender Username: @{sender.username}")

            # Show message attributes
            print(f"\n📋 All available attributes:")
            for attr in dir(message):
                if not attr.startswith("_"):
                    try:
                        value = getattr(message, attr)
                        if not callable(value) and not isinstance(
                            value, (list, dict, tuple)
                        ):
                            if isinstance(value, (str, int, float, bool, type(None))):
                                print(f"  {attr}: {value}")
                    except:
                        pass

            break

    except Exception as e:
        print(f"Error: {e}")


async def main():
    """Automatically fetch messages from ALL channels with full IDs"""
    print("=" * 60)
    print("🤖 TELEGRAM MESSAGE FETCHER WITH IDS")
    print("🌍 Timezone: Asia/Kolkata | Days: Last 3")
    print("=" * 60)

    # Validate environment
    API_ID, API_HASH, PHONE = validate_environment()

    # Start client
    async with TelegramClient("telegram_session", API_ID, API_HASH) as client:
        try:
            await client.start(PHONE)
            me = await client.get_me()
            print(f"✅ Logged in as: {me.first_name or 'User'} (ID: {me.id})")

            # ===== GET ALL CHANNELS =====
            print("\n🔍 Discovering channels...")
            print("-" * 40)

            all_channels = []
            async for dialog in client.iter_dialogs(limit=100):
                if dialog.is_channel or dialog.is_group:
                    all_channels.append(dialog)

            print(f"✅ Found {len(all_channels)} channels/groups")

            if not all_channels:
                print("❌ No channels found!")
                return

            # Show first channel as example
            if all_channels:
                await show_message_id_example(client, all_channels[0])

            # ===== PROCESS EACH CHANNEL =====
            print("\n" + "=" * 60)
            print("🚀 PROCESSING ALL CHANNELS")
            print("=" * 60)

            total_messages = 0
            successful_channels = 0
            csv_files = []
            all_messages_data = []

            for i, channel in enumerate(all_channels, 1):
                print(f"\n[{i}/{len(all_channels)}] ", end="")

                messages_count, csv_file, messages = await get_channel_messages(
                    client, channel, days_back=3
                )

                if messages_count > 0:
                    total_messages += messages_count
                    successful_channels += 1
                    if csv_file:
                        csv_files.append(csv_file)
                    all_messages_data.extend(messages)

            # ===== SUMMARY =====
            print("\n" + "=" * 60)
            print("📊 PROCESSING SUMMARY")
            print("=" * 60)
            print(f"Total channels processed: {len(all_channels)}")
            print(f"Channels with messages: {successful_channels}")
            print(f"Total messages fetched: {total_messages}")
            print(f"CSV files created: {len(csv_files)}")

            if csv_files:
                print("\n📁 CSV FILES SAVED (with message IDs):")
                for csv_file in csv_files:
                    print(f"  • {os.path.basename(csv_file)}")

                # Create master CSV with all messages
                master_filename = f"telegram_ALL_messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                print(f"\n📦 Creating master file: {master_filename}")

                try:
                    with open(
                        master_filename, "w", newline="", encoding="utf-8"
                    ) as master_file:
                        writer = csv.writer(master_file)
                        writer.writerow(
                            [
                                "Channel_ID",
                                "Channel_Name",
                                "Message_ID",
                                "Global_ID",
                                "Date_UTC",
                                "Date_Local",
                                "Sender_ID",
                                "Sender_Name",
                                "Message_Type",
                                "Message_Text",
                                "Views",
                                "Forwards",
                            ]
                        )

                        for item in all_messages_data:
                            msg = item["message"]
                            writer.writerow(
                                [
                                    item.get("channel_id", ""),
                                    item.get("channel_name", ""),
                                    msg.id,
                                    getattr(msg, "global_id", "N/A"),
                                    item["datetime_utc"].strftime("%Y-%m-%d %H:%M:%S"),
                                    item["datetime_local"].strftime(
                                        "%Y-%m-%d %H:%M:%S"
                                    ),
                                    item.get("sender_id", ""),
                                    item.get("sender_name", ""),
                                    "text" if msg.text else "media",
                                    msg.text[:500] if msg.text else "[Media]",
                                    getattr(msg, "views", 0),
                                    getattr(msg, "forwards", 0),
                                ]
                            )

                    print(f"✅ Master file created: {master_filename}")

                except Exception as e:
                    print(f"❌ Error creating master file: {e}")

            print("\n✨ Processing complete!")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
