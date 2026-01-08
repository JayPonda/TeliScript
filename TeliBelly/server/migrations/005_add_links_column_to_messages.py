#!/usr/bin/env python3
"""
Migration: Add 'links' column to messages table
Created: 2026-01-02

This migration adds a text column to the messages table to store
any links extracted from the message text.
"""

import sqlite3
from pathlib import Path

def migrate_up(db_path: str) -> bool:
    """Apply the migration"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(messages)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'links' not in columns:
            cursor.execute("ALTER TABLE messages ADD COLUMN links TEXT")
            print("✅ Migration successful: Added column 'links'")
        else:
            print("ℹ️ Migration skipped: Column 'links' already exists")
        
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def migrate_down(db_path: str) -> bool:
    """Rollback the migration"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(messages)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'links' not in columns:
            print("ℹ️ Rollback skipped: Column 'links' does not exist")
            return True
        
        # Create temporary table without the 'links' column
        temp_columns = [col for col in columns if col != 'links']
        
        # Ensure there are columns to create a table with
        if not temp_columns:
            # This is an unlikely edge case where 'links' is the only column
            cursor.execute("DROP TABLE messages")
            print("✅ Rollback successful: Dropped 'messages' table as it only contained 'links' column.")
            conn.commit()
            conn.close()
            return True

        temp_columns_str = ', '.join(f'"{col}"' for col in temp_columns)
        
        conn.execute("BEGIN TRANSACTION")

        cursor.execute(f"CREATE TABLE messages_backup({', '.join(f'{col[1]} {col[2]}' for col in cursor.execute('PRAGMA table_info(messages_temp)').fetchall() if col[1] in temp_columns)})")

        cursor.execute(f"""
            CREATE TABLE messages_backup AS 
            SELECT {temp_columns_str} FROM messages
        """)
        
        cursor.execute("DROP TABLE messages")
        cursor.execute("ALTER TABLE messages_backup RENAME TO messages")
        
        # Recreate indexes if they existed on the original table
        # We assume the same indexes as in 000_create_initial_tables
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_message_hash ON messages(message_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_channel_id ON messages(channel_id)")
        
        conn.commit()
        conn.close()
        
        print("✅ Rollback successful: Removed 'links' column")
        return True
    except Exception as e:
        # If something went wrong, rollback the transaction
        # if conn:
        # conn.rollback()
        print(f"❌ Rollback failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    db_path_str = str(Path(__file__).parent.parent / "data" / "telegram_backup.db")
    
    if len(sys.argv) > 1 and sys.argv[1] == "down":
        migrate_down(db_path_str)
    else:
        migrate_up(db_path_str)
