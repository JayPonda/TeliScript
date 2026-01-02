#!/usr/bin/env python3
"""
Migration: Add fetch status columns to channels table
Created: 2025-12-25

This migration adds fetch tracking columns to the channels table:
- fetchstatus: TEXT (status of the fetch operation)
- fetchedStartedAt: TEXT (timestamp when fetch started)
- fetchedEndedAt: TEXT (timestamp when fetch ended)
"""

import sqlite3
from pathlib import Path


def migrate_up(db_path: str) -> bool:
    """Apply the migration"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check what columns already exist in channels table
        cursor.execute("PRAGMA table_info(channels)")
        columns = [col[1] for col in cursor.fetchall()]

        added_columns = []

        # Add fetchstatus column if it doesn't exist
        if 'fetchstatus' not in columns:
            cursor.execute("ALTER TABLE channels ADD COLUMN fetchstatus TEXT")
            added_columns.append('fetchstatus')

        # Add fetchedStartedAt column if it doesn't exist
        if 'fetchedStartedAt' not in columns:
            cursor.execute("ALTER TABLE channels ADD COLUMN fetchedStartedAt TEXT")
            added_columns.append('fetchedStartedAt')

        # Add fetchedEndedAt column if it doesn't exist
        if 'fetchedEndedAt' not in columns:
            cursor.execute("ALTER TABLE channels ADD COLUMN fetchedEndedAt TEXT")
            added_columns.append('fetchedEndedAt')

        conn.commit()
        conn.close()

        if added_columns:
            print(f"✅ Migration successful: Added columns {added_columns} to channels table")
        else:
            print("ℹ️ Migration skipped: All columns already exist in channels table")

        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def migrate_down(db_path: str) -> bool:
    """Rollback the migration"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check what columns exist in channels table
        cursor.execute("PRAGMA table_info(channels)")
        columns = [col[1] for col in cursor.fetchall()]

        # Determine which columns we need to remove
        columns_to_remove = ['fetchstatus', 'fetchedStartedAt', 'fetchedEndedAt']
        existing_columns_to_remove = [col for col in columns_to_remove if col in columns]

        if not existing_columns_to_remove:
            print("ℹ️ Rollback skipped: Fetch columns don't exist in channels table")
            return True

        # SQLite doesn't support DROP COLUMN in older versions
        # We'll use a safe method: create new table, copy data, drop old, rename
        # Keep all original columns plus any columns that weren't added by this migration
        keep_columns = [col for col in columns if col not in columns_to_remove]
        keep_columns_str = ', '.join(keep_columns)

        cursor.execute(f"""
            CREATE TABLE channels_backup AS
            SELECT {keep_columns_str} FROM channels
        """)

        cursor.execute("DROP TABLE channels")
        cursor.execute("ALTER TABLE channels_backup RENAME TO channels")

        # Recreate indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_channel_name
            ON channels(channel_name)
        """)

        conn.commit()
        conn.close()

        print(f"✅ Rollback successful: Removed columns {existing_columns_to_remove} from channels table")
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