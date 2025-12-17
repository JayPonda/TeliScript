# telegram_fetch.py - COMPLETE WORKING VERSION
import asyncio
from datetime import datetime, timedelta
import pytz

class MessageFetcher:

    def __init__(self, client, timezone="Asia/Kolkata"):
        self.client = client
        self.timezone = pytz.timezone(timezone)

    async def fetch_messages(self, channel_dialog, days_back=3, limit=1000):
        """Fetch messages from a channel for last N days"""
        channel_name = channel_dialog.name
        channel_id = channel_dialog.entity.id

        print(f"\n📡 Processing: {channel_name} (ID: {channel_id})")
        print("-" * 50)

        now_local = datetime.now(self.timezone)
        start_date_local = now_local - timedelta(days=days_back)
        start_date_utc = start_date_local.astimezone(pytz.UTC)

        print(
            f"   Date range: {start_date_local.strftime('%Y-%m-%d')} to {now_local.strftime('%Y-%m-%d')}"
        )

        messages = []
        message_count = 0

        try:
            async for message in self.client.iter_messages(
                channel_dialog.entity, limit=limit
            ):
                message_count += 1
                msg_utc = message.date.replace(tzinfo=pytz.UTC)

                # Stop if messages are older than date range
                if msg_utc < start_date_utc:
                    if message_count <= 10:
                        continue
                    else:
                        break

                # Convert to local time
                msg_local = msg_utc.astimezone(self.timezone)

                # Only include if within date range
                if start_date_local <= msg_local <= now_local:
                    # Get sender info
                    sender_name, sender_id = await self._get_sender_info(
                        message, channel_name
                    )

                    messages.append(
                        {
                            "datetime_utc": msg_utc,
                            "datetime_local": msg_local,
                            "message": message,
                            "sender_name": sender_name,
                            "sender_id": sender_id,
                            "text": message.text or "",
                            "media_type": self._get_media_type(message),
                            "views": getattr(message, "views", 0) or 0,
                            "forwards": getattr(message, "forwards", 0) or 0,
                            "global_id": getattr(message, "global_id", None),
                        }
                    )

            print(
                f"   📊 Scanned {message_count} messages, found {len(messages)} from last {days_back} days"
            )

            if messages:
                self._show_message_summary(messages)

            return messages

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return []

    async def _get_sender_info(self, message, channel_name):
        """Get sender name and ID"""
        sender_name = channel_name
        sender_id = ""

        try:
            sender = await message.get_sender()
            if sender:
                sender_id = getattr(sender, "id", "")

                if hasattr(sender, "title"):
                    sender_name = sender.title
                elif hasattr(sender, "first_name"):
                    sender_name = sender.first_name
                    if hasattr(sender, "last_name") and sender.last_name:
                        sender_name += f" {sender.last_name}"

                if hasattr(sender, "username") and sender.username:
                    sender_name += f" (@{sender.username})"
        except:
            pass

        return sender_name, sender_id

    def _get_media_type(self, message):
        """Get media type if message has media"""
        if message.media:
            return message.media.__class__.__name__.replace("MessageMedia", "")
        elif message.sticker:
            return "sticker"
        elif message.poll:
            return "poll"
        return "text"

    def _show_message_summary(self, messages):
        """Show summary of fetched messages"""
        messages_by_date = {}
        for msg in messages:
            date_key = msg["datetime_local"].strftime("%Y-%m-%d")
            if date_key not in messages_by_date:
                messages_by_date[date_key] = 0
            messages_by_date[date_key] += 1

        print(f"   📅 Distribution: ", end="")
        for date in sorted(messages_by_date.keys()):
            print(f"{date}: {messages_by_date[date]} | ", end="")
        print()
