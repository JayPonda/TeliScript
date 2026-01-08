#!/usr/bin/env python3
"""
Migration: Add 'added_at' column to messages table
Created: 2026-01-08

This migration adds a timestamp column to the messages table:
- added_at: datetime, nullable (for marking when a message was added)
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

        if 'added_at' not in columns:
            cursor.execute("ALTER TABLE messages ADD COLUMN added_at TEXT")
            print("✅ Migration successful: Added 'added_at' column")
        else:
            print("ℹ️ Migration skipped: 'added_at' column already exists")

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

        # Check if column exists
        cursor.execute("PRAGMA table_info(messages)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'added_at' not in columns:
            print("ℹ️ Rollback skipped: 'added_at' column doesn't exist")
            return True

        # SQLite doesn't support DROP COLUMN in older versions
        # We'll use a safe method: create new table, copy data, drop old, rename
        temp_columns = [col for col in columns if col != 'added_at']
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

        print("✅ Rollback successful: Removed 'added_at' column")
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