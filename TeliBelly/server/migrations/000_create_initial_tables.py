#!/usr/bin/env python3
"""
Migration: 000_create_initial_tables
Created: 2026-01-02

This is the initial migration to create the core tables:
- channels: Stores information about each Telegram channel.
- messages: Stores individual messages from channels.
"""

import sqlite3
from pathlib import Path

def migrate_up(db_path: str) -> bool:
    """Apply the migration to create initial tables"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # --- Create channels table ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL,
                channel_name TEXT UNIQUE NOT NULL,
                total_messages INTEGER DEFAULT 0,
                last_backup_timestamp TEXT
            )
        """)
        print("✅ Created 'channels' table")

        # --- Create messages table ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER,
                channel_name TEXT,
                message_id INTEGER,
                global_id INTEGER,
                datetime_utc TEXT,
                datetime_local TEXT,
                sender_id INTEGER,
                sender_name TEXT,
                text TEXT,
                text_translated TEXT,
                media_type TEXT,
                views INTEGER,
                forwards INTEGER,
                message_hash TEXT
            )
        """)
        print("✅ Created 'messages' table")

        # --- Create indexes ---
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_message_hash ON messages(message_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_channel_id ON messages(channel_id)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_channel_name ON channels(channel_name)")
        print("✅ Created indexes")

        conn.commit()
        conn.close()
        
        print("✅ Migration successful: Initial tables created")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def migrate_down(db_path: str) -> bool:
    """Rollback the migration by dropping the tables"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS messages")
        print("✅ Dropped 'messages' table")
        
        cursor.execute("DROP TABLE IF EXISTS channels")
        print("✅ Dropped 'channels' table")

        conn.commit()
        conn.close()
        
        print("✅ Rollback successful: Initial tables dropped")
        return True
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    # This makes the script runnable standalone for testing
    db_path = Path(__file__).resolve().parent.parent / "data" / "telegram_backup.db"
    
    if len(sys.argv) > 1 and sys.argv[1] == "down":
        migrate_down(str(db_path))
    else:
        migrate_up(str(db_path))
