#!/usr/bin/env python3
"""
Migration: Add tags functionality to messages and create tags table
Created: 2025-12-25

This migration:
1. Adds a 'tags' column to the messages table (TEXT, comma-separated tags)
2. Creates a 'tags' table with:
   - id: INTEGER PRIMARY KEY
   - name: TEXT UNIQUE NOT NULL
   - message_ids: TEXT (comma-separated message IDs)
"""

import sqlite3
from pathlib import Path


def migrate_up(db_path: str) -> bool:
    """Apply the migration"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Add tags column to messages table if it doesn't exist
        cursor.execute("PRAGMA table_info(messages)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'tags' not in columns:
            cursor.execute("ALTER TABLE messages ADD COLUMN tags TEXT")
            print("✅ Added 'tags' column to messages table")
        else:
            print("ℹ️ 'tags' column already exists in messages table")
        
        # 2. Create tags table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                message_ids TEXT
            )
        """)
        print("✅ Created tags table")
        
        conn.commit()
        conn.close()
        
        print("✅ Migration successful: Added tags functionality")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def migrate_down(db_path: str) -> bool:
    """Rollback the migration"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if tags column exists
        cursor.execute("PRAGMA table_info(messages)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Remove tags column from messages table
        if 'tags' in columns:
            # SQLite doesn't support DROP COLUMN in older versions
            # We'll use a safe method: create new table, copy data, drop old, rename
            temp_columns = [col for col in columns if col != 'tags']
            temp_columns_str = ', '.join(temp_columns)
            
            cursor.execute(f"""
                CREATE TABLE messages_backup AS 
                SELECT {temp_columns_str} FROM messages
            """)
            
            cursor.execute("DROP TABLE messages")
            cursor.execute("ALTER TABLE messages_backup RENAME TO messages")
            
            # Recreate indexes
            cursor.execute("""
                CREATE INDEX idx_message_hash 
                ON messages(message_hash)
            """)
            cursor.execute("""
                CREATE INDEX idx_channel_id 
                ON messages(channel_id)
            """)
            print("✅ Removed 'tags' column from messages table")
        else:
            print("ℹ️ 'tags' column doesn't exist in messages table")
        
        # Drop tags table if it exists
        cursor.execute("DROP TABLE IF EXISTS tags")
        print("✅ Dropped tags table")
        
        conn.commit()
        conn.close()
        
        print("✅ Rollback successful: Removed tags functionality")
        return True
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    db_path = Path(__file__).parent.parent / "data" / "telegram_backup.db"
    
    if len(sys.argv) > 1 and sys.argv[1] == "down":
        migrate_down(str(db_path))
    else:
        migrate_up(str(db_path))