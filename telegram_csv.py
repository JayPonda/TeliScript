# telegram_csv.py
import csv
import os
from datetime import datetime


class CSVHandler:
    def __init__(self, output_dir="./output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def save_channel_messages(self, messages, channel_name):
        """Save messages from a single channel to CSV"""
        if not messages:
            return None

        # Clean filename
        clean_name = self._clean_filename(channel_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(
            self.output_dir, f"telegram_{clean_name}_{timestamp}.csv"
        )

        try:
            with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
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

                for msg in messages:
                    writer.writerow(
                        [
                            msg["channel_id"],
                            msg["channel_name"],
                            msg["message_id"],
                            msg["global_id"] or "",
                            msg["datetime_utc"].strftime("%Y-%m-%d %H:%M:%S"),
                            msg["datetime_local"].strftime("%Y-%m-%d %H:%M:%S"),
                            msg["sender_id"],
                            msg["sender_name"],
                            msg["media_type"],
                            (
                                msg["text"][:2000].replace("\n", " ").replace("\r", " ")
                                if msg["text"]
                                else ""
                            ),
                            msg["views"],
                            msg["forwards"],
                        ]
                    )

            print(f"   💾 Saved to: {os.path.basename(filename)}")
            return filename

        except Exception as e:
            print(f"   ❌ Error saving CSV: {e}")
            return None

    def save_all_messages(self, all_messages, filename=None):
        """Save all messages from all channels to a single CSV"""
        if not all_messages:
            return None

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(
                self.output_dir, f"telegram_ALL_messages_{timestamp}.csv"
            )

        try:
            with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
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

                for channel_msgs in all_messages:
                    for msg in channel_msgs:
                        writer.writerow(
                            [
                                msg["channel_id"],
                                msg["channel_name"],
                                msg["message_id"],
                                msg["global_id"] or "",
                                msg["datetime_utc"].strftime("%Y-%m-%d %H:%M:%S"),
                                msg["datetime_local"].strftime("%Y-%m-%d %H:%M:%S"),
                                msg["sender_id"],
                                msg["sender_name"],
                                msg["media_type"],
                                (
                                    msg["text"][:2000]
                                    .replace("\n", " ")
                                    .replace("\r", " ")
                                    if msg["text"]
                                    else ""
                                ),
                                msg["views"],
                                msg["forwards"],
                            ]
                        )

            print(f"✅ Master file created: {os.path.basename(filename)}")
            return filename

        except Exception as e:
            print(f"❌ Error saving master CSV: {e}")
            return None

    def _clean_filename(self, name):
        """Clean a string to be safe for filenames"""
        import re

        # Replace non-alphanumeric characters with underscores
        clean = re.sub(r"[^\w\s-]", "", name)
        clean = re.sub(r"[-\s]+", "_", clean)
        return clean.strip("_")
