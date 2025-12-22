# telegram_master_csv.py - WITH TRANSLATION COLUMN
import csv
import os
from datetime import datetime
import hashlib
import re
from googletrans import Translator


class TelegramMasterCSV:

    def __init__(self, master_file="data/telegram_messages_master.csv"):
        self.master_file = master_file
        self.existing_hashes = set()
        self.existing_ids = {}
        self.translator = Translator()

        # Load existing data
        self._load_existing_data()

    def _load_existing_data(self):
        """Load existing message hashes"""
        if os.path.exists(self.master_file):
            try:
                with open(self.master_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)

                    if reader.fieldnames:
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
            except Exception as e:
                print(f"❌ Error loading master file: {e}")
        else:
            print(f"📄 Creating new master file")

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

    def _translate_if_russian(self, text):
        """Translate Russian text to English"""
        if not text or not isinstance(text, str):
            return ""

        # Check if text has Cyrillic characters
        cyrillic_count = sum(1 for char in text if "\u0400" <= char <= "\u04ff")
        if cyrillic_count == 0:
            return text  # Not Russian, keep original

        try:
            # Translate Russian to English
            translated = self.translator.translate(text, src="ru", dest="en")
            return translated.text
        except:
            return text  # Return original on error

    def _clean_text(self, text):
        """Clean text for CSV"""
        if not text:
            return ""
        text = str(text).replace("\0", "").replace("\x00", "").strip()
        return text[:4000]  # Limit length

    def _extract_links(self, text):
        """Extract markdown links from text"""
        if not text or not isinstance(text, str):
            return ""
        
        # Pattern to match markdown links: [](url)
        pattern = r'\]\(([^)]+)\)'
        matches = re.findall(pattern, text)
        
        # Return as comma-separated string
        return ",".join(matches)

    def add_messages(self, messages, channel_name):
        """Add messages with automatic translation"""
        if not messages:
            print(f"   📭 No messages to add")
            return 0

        new_messages = []
        duplicates = 0
        translated_count = 0

        for msg in messages:
            # Skip duplicates
            if self._is_duplicate(msg):
                duplicates += 1
                continue

            # Generate hash
            msg_hash = self._generate_message_hash(msg)
            msg["message_hash"] = msg_hash

            # Get original text
            original_text = self._clean_text(msg.get("text", ""))

            # Translate if Russian
            translated_text = self._translate_if_russian(original_text)
            if translated_text != original_text:
                translated_count += 1

            # Add both texts to message data
            msg["text_translated"] = translated_text

            # Extract links from original text
            links = self._extract_links(original_text)
            msg["links"] = links

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
            # Check file exists and get headers
            file_exists = os.path.exists(self.master_file)
            headers = []

            if file_exists:
                # Read existing headers
                with open(self.master_file, "r", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    headers = next(reader, [])

            # Define our headers (include Translated_Text and Date_Local_Date)
            our_headers = [
                "Date_Local_Date",
                "Channel_Name",
                "Translated_Text",
                "Links",
                "Message_Type",
                "Message_Hash",
                "Channel_ID",
                "Message_ID",
                "Global_ID",
                "Date_UTC",
                "Date_Local",
                "Sender_ID",
                "Sender_Name",
                "Views",
                "Forwards",
                "Added_At",
            ]

            # If file exists but doesn't have our headers, we need to rewrite
            if file_exists and set(headers) != set(our_headers):
                print(f"   🔄 Updating CSV format to include translation column")
                self._update_csv_format(our_headers)

            # Append to master file
            with open(self.master_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                # Write header if file is new
                if not file_exists:
                    writer.writerow(our_headers)

                # Write new messages
                for msg in new_messages:
                    # Extract date part from Date_Local
                    date_local_value = (
                        msg.get("datetime_local", "").strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                        if hasattr(msg.get("datetime_local", ""), "strftime")
                        else msg.get("datetime_local", "")
                    )

                    # Extract just the date part (YYYY-MM-DD)
                    date_local_date_value = ""
                    if date_local_value and " " in date_local_value:
                        date_local_date_value = date_local_value.split(" ")[0]
                    elif date_local_value:
                        # If it's already just a date
                        date_local_date_value = date_local_value

                    writer.writerow(
                        [
                            date_local_date_value,
                            channel_name,
                            msg.get("text_translated", ""),
                            msg.get("links", ""),
                            msg.get("media_type", "text"),
                            msg.get("message_hash", ""),
                            msg.get("channel_id", ""),
                            msg.get("message_id", ""),
                            msg.get("global_id", ""),
                            (
                                msg.get("datetime_utc", "").strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                )
                                if hasattr(msg.get("datetime_utc", ""), "strftime")
                                else msg.get("datetime_utc", "")
                            ),
                            date_local_value,
                            msg.get("sender_id", ""),
                            msg.get("sender_name", ""),
                            msg.get("views", 0),
                            msg.get("forwards", 0),
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        ]
                    )

            print(f"   ✅ Added {len(new_messages)} new messages")
            if translated_count > 0:
                print(f"   🔤 Translated {translated_count} Russian messages")
            if duplicates > 0:
                print(f"   ⏭️  Skipped {duplicates} duplicates")
        else:
            print(f"   ⏭️  All {len(messages)} messages already exist")

        return len(new_messages)

    def _update_csv_format(self, new_headers):
        """Update existing CSV to new format with translation column"""
        try:
            # Read existing data
            with open(self.master_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                old_rows = list(reader)
                old_headers = reader.fieldnames

            # Create backup
            backup_file = (
                f"{self.master_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            os.rename(self.master_file, backup_file)
            print(f"   📦 Created backup: {backup_file}")

            # Write new format
            with open(self.master_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=new_headers)
                writer.writeheader()

                for row in old_rows:
                    new_row = {}
                    for header in new_headers:
                        if header in old_headers:
                            new_row[header] = row[header]
                        elif header == "Original_Text":
                            new_row[header] = row.get("Message_Text", "")
                        elif header == "Translated_Text":
                            # Translate existing Russian messages
                            text = row.get("Message_Text", "")
                            new_row[header] = self._translate_if_russian(text)
                        elif header == "Date_Local_Date":
                            # Extract date part from Date_Local column
                            date_local = row.get("Date_Local", "")
                            if date_local and " " in date_local:
                                new_row[header] = date_local.split(" ")[0]
                            else:
                                new_row[header] = date_local
                        elif header == "Links":
                            # Extract links from Message_Text if it exists
                            text = row.get("Message_Text", "")
                            new_row[header] = self._extract_links(text)
                        else:
                            new_row[header] = ""
                    writer.writerow(new_row)

            print(f"   🔄 Updated CSV format with translation column and date column")

        except Exception as e:
            print(f"   ❌ Error updating format: {e}")

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
