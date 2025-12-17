# telegram_auth.py
from telethon import TelegramClient
import pytz
import os
import sys
from dotenv import load_dotenv


class TelegramAuth:
    def __init__(self, session_name="telegram_session"):
        self.session_name = session_name
        self.client = None
        self.timezone = pytz.timezone("Asia/Kolkata")

    def validate_environment(self):
        """Validate and load environment variables"""
        load_dotenv()

        api_id = os.getenv("TELEGRAM_API_ID")
        api_hash = os.getenv("TELEGRAM_API_HASH")
        phone = os.getenv("TELEGRAM_PHONE_NUMBER")

        errors = []
        if not api_id:
            errors.append("TELEGRAM_API_ID not set")
        elif not api_id.isdigit():
            errors.append("TELEGRAM_API_ID must contain only digits")

        if not api_hash:
            errors.append("TELEGRAM_API_HASH not set")

        if not phone:
            errors.append("TELEGRAM_PHONE_NUMBER not set")
        elif not phone.startswith("+"):
            errors.append("TELEGRAM_PHONE_NUMBER must start with '+'")

        if errors:
            print("❌ Configuration errors:")
            for error in errors:
                print(f"   - {error}")
            sys.exit(1)

        return int(api_id), api_hash, phone

    async def authenticate(self):
        """Authenticate with Telegram"""
        API_ID, API_HASH, PHONE = self.validate_environment()

        print("🔐 Authenticating...")
        self.client = TelegramClient(self.session_name, API_ID, API_HASH)

        try:
            await self.client.start(PHONE)
            me = await self.client.get_me()
            print(f"✅ Logged in as: {me.first_name or 'User'} (ID: {me.id})")
            return True
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False

    async def get_all_channels(self, limit=100):
        """Get all channels and groups"""
        print("📡 Discovering channels...")

        channels = []
        async for dialog in self.client.iter_dialogs(limit=limit):
            if dialog.is_channel or dialog.is_group:
                channels.append(
                    {
                        "dialog": dialog,
                        "id": dialog.entity.id,
                        "name": dialog.name,
                        "type": (
                            "Channel"
                            if dialog.is_channel
                            else (
                                "Supergroup"
                                if hasattr(dialog.entity, "megagroup")
                                and dialog.entity.megagroup
                                else "Group"
                            )
                        ),
                    }
                )

        print(f"✅ Found {len(channels)} channels/groups")
        return channels

    async def disconnect(self):
        """Disconnect client"""
        if self.client:
            await self.client.disconnect()
            print("🔌 Disconnected from Telegram")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.authenticate()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
