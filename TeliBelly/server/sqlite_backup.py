# sqlite_backup.py - SQLite backup functionality for Telegram messages
import sqlite3
import os
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional


class SQLiteBackup:
    def __init__(self, db_path: str = "data/telegram_backup.db"):
        """Initialize SQLite backup with database path"""
        self.db_path = db_path
        self._ensure_data_directory()
        self._init_database()
        
    def _ensure_data_directory(self):
        """Ensure the data directory exists"""
        directory = os.path.dirname(self.db_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            print(f"📁 Created data directory: {directory}")
            
    def _init_database(self):
        """Initialize the SQLite database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create messages table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        channel_id TEXT,
                        channel_name TEXT,
                        message_id TEXT,
                        global_id TEXT,
                        datetime_utc TEXT,
                        datetime_local TEXT,
                        sender_id TEXT,
                        sender_name TEXT,
                        text TEXT,
                        text_translated TEXT,
                        links TEXT,
                        media_type TEXT,
                        views INTEGER,
                        forwards INTEGER,
                        message_hash TEXT UNIQUE,
                        added_at TEXT,
                        backup_timestamp TEXT
                    )
                ''')
                
                # Create channels table to track channel statistics
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS channels (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        channel_id TEXT UNIQUE,
                        channel_name TEXT,
                        last_backup_timestamp TEXT,
                        total_messages INTEGER DEFAULT 0,
                        fetchstatus TEXT,
                        fetchedStartedAt TEXT,
                        fetchedEndedAt TEXT
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_message_hash 
                    ON messages(message_hash)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_channel_id 
                    ON messages(channel_id)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_channel_name 
                    ON channels(channel_name)
                ''')
                
                conn.commit()
                print(f"💾 SQLite backup database initialized at: {self.db_path}")
                
        except Exception as e:
            print(f"❌ Error initializing SQLite database: {e}")
            raise
            
    def _generate_message_hash(self, message_data: Dict[str, Any]) -> str:
        """Generate unique hash for a message"""
        unique_string = f"{message_data.get('channel_id', '')}|{message_data.get('message_id', '')}|{message_data.get('datetime_utc', '')}"
        return hashlib.md5(unique_string.encode()).hexdigest()
        
    def backup_messages(self, messages: List[Dict[str, Any]], channel_name: str) -> int:
        """Backup messages to SQLite database"""
        if not messages:
            return 0
            
        backup_count = 0
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get channel ID from first message
                channel_id = messages[0].get('channel_id', '')
                
                # Update channel info
                cursor.execute('''
                    INSERT OR IGNORE INTO channels
                    (channel_id, channel_name, last_backup_timestamp, fetchstatus, fetchedStartedAt, fetchedEndedAt)
                    VALUES (?, ?, ?, NULL, NULL, NULL)
                ''', (channel_id, channel_name, datetime.now().isoformat()))

                cursor.execute('''
                    UPDATE channels
                    SET last_backup_timestamp = ?, channel_name = ?
                    WHERE channel_id = ?
                ''', (datetime.now().isoformat(), channel_name, channel_id))
                
                # Backup each message
                for msg in messages:
                    try:
                        # Generate hash if not present
                        if 'message_hash' not in msg:
                            msg_hash = self._generate_message_hash(msg)
                        else:
                            msg_hash = msg['message_hash']
                            
                        # Insert message data
                        cursor.execute('''
                            INSERT OR IGNORE INTO messages 
                            (channel_id, channel_name, message_id, global_id, 
                             datetime_utc, datetime_local, sender_id, sender_name,
                             text, text_translated, links, media_type, views, forwards,
                             message_hash, added_at, backup_timestamp)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            msg.get('channel_id', ''),
                            channel_name,
                            msg.get('message_id', ''),
                            msg.get('global_id', ''),
                            str(msg.get('datetime_utc', '')),
                            str(msg.get('datetime_local', '')),
                            msg.get('sender_id', ''),
                            msg.get('sender_name', ''),
                            msg.get('text', ''),
                            msg.get('text_translated', ''),
                            msg.get('links', ''),
                            msg.get('media_type', 'text'),
                            msg.get('views', 0),
                            msg.get('forwards', 0),
                            msg_hash,
                            msg.get('added_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                            datetime.now().isoformat()
                        ))
                        
                        if cursor.rowcount > 0:
                            backup_count += 1
                            
                    except Exception as e:
                        print(f"⚠️  Warning: Skipping message due to error: {e}")
                        continue
                        
                # Update channel message count
                cursor.execute('''
                    UPDATE channels 
                    SET total_messages = (
                        SELECT COUNT(*) FROM messages WHERE channel_id = ?
                    )
                    WHERE channel_id = ?
                ''', (channel_id, channel_id))
                
                conn.commit()
                
        except Exception as e:
            print(f"❌ Error backing up messages: {e}")
            raise
            
        print(f"💾 Backed up {backup_count} messages to SQLite database")
        return backup_count
        
    def get_backup_stats(self) -> Dict[str, Any]:
        """Get backup statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get total messages
                cursor.execute("SELECT COUNT(*) FROM messages")
                total_messages = cursor.fetchone()[0]
                
                # Get total channels
                cursor.execute("SELECT COUNT(*) FROM channels")
                total_channels = cursor.fetchone()[0]
                
                # Get database size
                db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                
                return {
                    "total_messages": total_messages,
                    "total_channels": total_channels,
                    "database_size": db_size,
                    "database_path": self.db_path
                }
                
        except Exception as e:
            print(f"❌ Error getting backup stats: {e}")
            return {
                "total_messages": 0,
                "total_channels": 0,
                "database_size": 0,
                "database_path": self.db_path
            }
            
    def get_channel_stats(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific channel"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT channel_name, last_backup_timestamp, total_messages
                    FROM channels 
                    WHERE channel_id = ?
                ''', (channel_id,))
                
                result = cursor.fetchone()
                if result:
                    return {
                        "channel_name": result[0],
                        "last_backup": result[1],
                        "message_count": result[2]
                    }
                    
        except Exception as e:
            print(f"❌ Error getting channel stats: {e}")
            
        return None
        
    def get_recent_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent messages from backup"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT channel_name, text_translated, datetime_local, sender_name
                    FROM messages 
                    ORDER BY datetime_local DESC 
                    LIMIT ?
                ''', (limit,))
                
                messages = []
                for row in cursor.fetchall():
                    messages.append({
                        "channel_name": row[0],
                        "text": row[1],
                        "datetime": row[2],
                        "sender": row[3]
                    })
                    
                return messages
                
        except Exception as e:
            print(f"❌ Error getting recent messages: {e}")
            return []