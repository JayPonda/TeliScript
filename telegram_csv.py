# telegram_master_csv.py - CORRECTED VERSION
import csv
import os
from datetime import datetime
import hashlib


class TelegramMasterCSV:
    def __init__(self, master_file="data/telegram_messages_master.csv"):
        self.master_file = master_file
        self.existing_hashes = set()
        self.existing_ids = {}

        # Load existing data
        self._load_existing_data()

    def _load_existing_data(self):
        """Load existing message hashes"""
        if os.path.exists(self.master_file):
            try:
                with open(self.master_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)

                    if reader.fieldnames and "Message_Hash" in reader.fieldnames:
                        for row in reader:
                            msg_hash = row.get("Message_Hash", "")
                            if msg_hash:
                                self.existing_hashes.add(msg_hash)

                            # Track by channel_id + message_id
                            channel_id = row.get("Channel_ID", "")
                            msg_id = row.get("Message_ID", "")
                            if channel_id and msg_id:
                                if channel_id not in self.existing_ids:
                                    self.existing_ids[channel_id] = set()
                                self.existing_ids[channel_id].add(msg_id)

                        print(
                            f"📁 Loaded {len(self.existing_hashes)} existing messages"
                        )
                    else:
                        self._backup_old_file()
            except Exception as e:
                print(f"❌ Error loading master file: {e}")
                self._backup_old_file()
        else:
            print(f"📄 Creating new master file")

    def _backup_old_file(self):
        """Backup old format file"""
        if os.path.exists(self.master_file):
            try:
                backup_name = f"{self.master_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.rename(self.master_file, backup_name)
                print(f"📦 Backed up old file")
            except:
                pass

    def _generate_message_hash(self, message_data):
        """Generate unique hash for a message"""
        unique_string = f"{message_data['channel_id']}|{message_data['message_id']}|{message_data.get('datetime_utc', '')}"
        return hashlib.md5(unique_string.encode()).hexdigest()

    def _is_duplicate(self, message_data):
        """Check if message already exists"""
        # Check by hash
        msg_hash = self._generate_message_hash(message_data)
        if msg_hash in self.existing_hashes:
            return True

        # Check by channel_id + message_id
        channel_id = str(message_data.get("channel_id", ""))
        msg_id = str(message_data.get("message_id", ""))

        if channel_id in self.existing_ids and msg_id in self.existing_ids[channel_id]:
            return True

        return False

    def _clean_text(self, text):
        """Clean text for CSV"""
        if not text:
            return ""
        # Remove null characters and strip
        text = str(text).replace("\0", "").replace("\x00", "").strip()
        return text

    def add_messages(self, messages, channel_name):
        """Add messages to master CSV"""
        if not messages:
            print(f"   📭 No messages to add")
            return 0

        new_messages = []
        duplicates = 0

        for msg in messages:
            # Skip duplicates
            if self._is_duplicate(msg):
                duplicates += 1
                continue

            # Generate hash
            msg_hash = self._generate_message_hash(msg)
            msg["message_hash"] = msg_hash

            # Track in memory
            self.existing_hashes.add(msg_hash)
            channel_id = str(msg.get("channel_id", ""))
            msg_id = str(msg.get("message_id", ""))
            if channel_id and msg_id:
                if channel_id not in self.existing_ids:
                    self.existing_ids[channel_id] = set()
                self.existing_ids[channel_id].add(msg_id)

            new_messages.append(msg)

        if new_messages:
            # Append to master file
            file_exists = os.path.exists(self.master_file)

            with open(self.master_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                # Write header if file is new
                if not file_exists or os.path.getsize(self.master_file) == 0:
                    writer.writerow(
                        [
                            "Message_Hash",
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
                            "Added_At",
                        ]
                    )

                # Write new messages
                for msg in new_messages:
                    writer.writerow(
                        [
                            msg.get("message_hash", ""),
                            msg.get("channel_id", ""),
                            channel_name,
                            msg.get("message_id", ""),
                            msg.get("global_id", ""),
                            (
                                msg.get("datetime_utc", "").strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                )
                                if hasattr(msg.get("datetime_utc", ""), "strftime")
                                else msg.get("datetime_utc", "")
                            ),
                            (
                                msg.get("datetime_local", "").strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                )
                                if hasattr(msg.get("datetime_local", ""), "strftime")
                                else msg.get("datetime_local", "")
                            ),
                            msg.get("sender_id", ""),
                            msg.get("sender_name", ""),
                            msg.get("media_type", "text"),
                            self._clean_text(msg.get("text", ""))[:4000],
                            msg.get("views", 0),
                            msg.get("forwards", 0),
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        ]
                    )

            print(f"   ✅ Added {len(new_messages)} new messages")
            if duplicates > 0:
                print(f"   ⏭️  Skipped {duplicates} duplicates")
        else:
            print(f"   ⏭️  All {len(messages)} messages already exist")

        return len(new_messages)

    def get_stats(self):
        """Get statistics"""
        stats = {
            "total_messages": len(self.existing_hashes),
            "channels": len(self.existing_ids),
            "file_size": (
                os.path.getsize(self.master_file)
                if os.path.exists(self.master_file)
                else 0
            ),
        }
        return stats
