#!/usr/bin/env python3
"""
Migration: Add 'like' and 'read' columns to messages table
Created: 2025-12-25

This migration adds two boolean columns to the messages table:
- like: boolean, default False (for marking liked messages)
- read: boolean, default False (for marking read messages)
"""

import sqlite3
from pathlib import Path


def migrate_up(db_path: str) -> bool:
    """Apply the migration"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(messages)")
        columns = [col[1] for col in cursor.fetchall()]
        
        added_columns = []
        
        if 'like' not in columns:
            cursor.execute("ALTER TABLE messages ADD COLUMN like BOOLEAN DEFAULT 0")
            added_columns.append('like')
        
        if 'read' not in columns:
            cursor.execute("ALTER TABLE messages ADD COLUMN read BOOLEAN DEFAULT 0")
            added_columns.append('read')
        
        conn.commit()
        conn.close()
        
        if added_columns:
            print(f"✅ Migration successful: Added columns {added_columns}")
        else:
            print("ℹ️ Migration skipped: Columns already exist")
        
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def migrate_down(db_path: str) -> bool:
    """Rollback the migration"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # SQLite doesn't support DROP COLUMN in older versions
        # We'll use a safe method: create new table, copy data, drop old, rename
        cursor.execute("PRAGMA table_info(messages)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'like' not in columns and 'read' not in columns:
            print("ℹ️ Rollback skipped: Columns don't exist")
            return True
        
        # Create temporary table without the columns
        temp_columns = [col for col in columns if col not in ['like', 'read']]
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
        
        conn.commit()
        conn.close()
        
        print("✅ Rollback successful: Removed 'like' and 'read' columns")
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
