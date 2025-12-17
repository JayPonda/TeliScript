# telegram_master_csv.py
import csv
import os
from datetime import datetime
import hashlib

class TelegramMasterCSV:
    def __init__(self, master_file='telegram_messages_master.csv'):
        self.master_file = master_file
        self.existing_hashes = set()
        self.existing_ids = {}  # Store channel_id -> message_ids mapping
        
        # Load existing data if file exists
        self._load_existing_data()
    
    def _load_existing_data(self):
        """Load existing message hashes to avoid duplicates"""
        if os.path.exists(self.master_file):
            try:
                with open(self.master_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    
                    # Check if it's our format (has Message_Hash column)
                    if reader.fieldnames and 'Message_Hash' in reader.fieldnames:
                        for row in reader:
                            msg_hash = row.get('Message_Hash', '')
                            if msg_hash:
                                self.existing_hashes.add(msg_hash)
                            
                            # Also track by channel_id + message_id
                            channel_id = row.get('Channel_ID', '')
                            msg_id = row.get('Message_ID', '')
                            if channel_id and msg_id:
                                if channel_id not in self.existing_ids:
                                    self.existing_ids[channel_id] = set()
                                self.existing_ids[channel_id].add(msg_id)
                        
                        print(f"📁 Loaded {len(self.existing_hashes)} existing messages from master file")
                    else:
                        print(f"⚠️  Old format CSV. Creating backup and starting fresh.")
                        self._backup_old_file()
            except Exception as e:
                print(f"❌ Error loading master file: {e}")
                self._backup_old_file()
        else:
            print(f"📄 Creating new master file: {self.master_file}")
    
    def _backup_old_file(self):
        """Backup old format file"""
        if os.path.exists(self.master_file):
            try:
                backup_name = f"{self.master_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.rename(self.master_file, backup_name)
                print(f"📦 Backed up old file to: {backup_name}")
            except:
                pass
    
    def _generate_message_hash(self, message_data):
        """Generate unique hash for a message"""
        # Create unique identifier from channel_id + message_id + timestamp
        unique_string = f"{message_data['channel_id']}|{message_data['message_id']}|{message_data.get('datetime_utc', '')}"
        return hashlib.md5(unique_string.encode()).hexdigest()
    
    def _is_duplicate(self, message_data):
        """Check if message already exists in master file"""
        # Method 1: Check by hash
        msg_hash = self._generate_message_hash(message_data)
        if msg_hash in self.existing_hashes:
            return True
        
        # Method 2: Check by channel_id + message_id
        channel_id = str(message_data.get('channel_id', ''))
        msg_id = str(message_data.get('message_id', ''))
        
        if channel_id in self.existing_ids and msg_id in self.existing_ids[channel_id]:
            return True
        
        return False
    
    def add_messages(self, messages, channel_name):
        """Add new messages to master CSV, skipping duplicates"""
        if not messages:
            print(f"   📭 No messages to add")
            return 0
        
        new_messages = []
        duplicates = 0
        
        for msg in messages:
            if not self._is_duplicate(msg):
                # Generate hash and add to tracking
                msg_hash = self._generate_message_hash(msg)
                msg['message_hash'] = msg_hash
                self.existing_hashes.add(msg_hash)
                
                # Track by channel_id + message_id
                channel_id = str(msg.get('channel_id', ''))
                msg_id = str(msg.get('message_id', ''))
                if channel_id and msg_id:
                    if channel_id not in self.existing_ids:
                        self.existing_ids[channel_id] = set()
                    self.existing_ids[channel_id].add(msg_id)
                
                new_messages.append(msg)
            else:
                duplicates += 1
        
        if new_messages:
            # Append to master file
            file_exists = os.path.exists(self.master_file)
            
            with open(self.master_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header if file is new
                if not file_exists or os.path.getsize(self.master_file) == 0:
                    writer.writerow([
                        'Message_Hash', 'Channel_ID', 'Channel_Name', 'Message_ID', 
                        'Global_ID', 'Date_UTC', 'Date_Local', 'Sender_ID', 
                        'Sender_Name', 'Message_Type', 'Message_Text', 'Views', 
                        'Forwards', 'Added_At'
                    ])
                
                # Write new messages
                for msg in new_messages:
                    writer.writerow([
                        msg.get('message_hash', ''),
                        msg.get('channel_id', ''),
                        channel_name,
                        msg.get('message_id', ''),
                        msg.get('global_id', ''),
                        msg.get('datetime_utc', '').strftime('%Y-%m-%d %H:%M:%S') if hasattr(msg.get('datetime_utc', ''), 'strftime') else msg.get('datetime_utc', ''),
                        msg.get('datetime_local', '').strftime('%Y-%m-%d %H:%M:%S') if hasattr(msg.get('datetime_local', ''), 'strftime') else msg.get('datetime_local', ''),
                        msg.get('sender_id', ''),
                        msg.get('sender_name', ''),
                        msg.get('media_type', 'text'),
                        self._clean_text(msg.get('text', ''))[:5000],
                        msg.get('views', 0),
                        msg.get('forwards', 0),
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ])
            
            print(f"   ✅ Added {len(new_messages)} new messages ({duplicates} duplicates skipped)")
        else:
            print(f"   ⏭️  All {len(messages)} messages already exist in master file")
        
        return len(new_messages)
    
    def _clean_text(self, text):
        """Clean text for CSV"""
        if not text:
            return ''
        # Remove problematic characters and limit length
        text = str(text).replace('\0', '').replace('\x00', '').strip()
        return text
    
    def get_stats(self):
        """Get statistics about the master file"""
        stats = {
            'total_messages': len(self.existing_hashes),
            'channels': len(self.existing_ids),
            'file_size': os.path.getsize(self.master_file) if os.path.exists(self.master_file) else 0
        }
        
        # Count messages per channel
        stats['messages_per_channel'] = {
            channel_id: len(msg_ids) 
            for channel_id, msg_ids in self.existing_ids.items()
        }
        
        return stats
    
    def export_channel_csv(self, channel_id=None, channel_name=None):
        """Export messages from a specific channel to separate CSV"""
        if not os.path.exists(self.master_file):
            print("❌ Master file doesn't exist")
            return None
        
        try:
            with open(self.master_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                channel_messages = []
                
                for row in reader:
                    if channel_id and row.get('Channel_ID') == str(channel_id):
                        channel_messages.append(row)
                    elif channel_name and row.get('Channel_Name') == channel_name:
                        channel_messages.append(row)
                
            if channel_messages:
                # Create channel-specific CSV
                if channel_name:
                    clean_name = "".join(c if c.isalnum() or c in ' _-' else '_' for c in channel_name)
                else:
                    clean_name = f"channel_{channel_id}"
                
                export_file = f"{clean_name}_export_{datetime.now().strftime('%Y%m%d')}.csv"
                
                with open(export_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
                    writer.writeheader()
                    writer.writerows(channel_messages)
                
                print(f"✅ Exported {len(channel_messages)} messages to: {export_file}")
                return export_file
            else:
                print(f"📭 No messages found for channel")
                return None
                
        except Exception as e:
            print(f"❌ Export error: {e}")
            return None