#!/usr/bin/env python3
"""
Database migration runner
Manages and runs migrations for the Telegram backup database
"""

import sqlite3
import sys
from pathlib import Path
from importlib import import_module


DB_PATH = "../data/telegram_backup.db"
MIGRATIONS_DIR = Path("../migrations")


def init_migrations_table():
    """Create migrations tracking table if it doesn't exist"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Failed to initialize migrations table: {e}")
        return False


def get_applied_migrations():
    """Get list of applied migrations"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM migrations ORDER BY applied_at")
        applied = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return applied
    except Exception as e:
        print(f"❌ Failed to get applied migrations: {e}")
        return []


def get_pending_migrations():
    """Get list of pending migrations"""
    if not MIGRATIONS_DIR.exists():
        return []
    
    applied = get_applied_migrations()
    all_migrations = sorted([f.stem for f in MIGRATIONS_DIR.glob("*.py") if not f.name.startswith("__")])
    
    return [m for m in all_migrations if m not in applied]


def record_migration(name: str):
    """Record a migration as applied"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("INSERT INTO migrations (name) VALUES (?)", (name,))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Failed to record migration: {e}")
        return False


def remove_migration_record(name: str):
    """Remove a migration record"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM migrations WHERE name = ?", (name,))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Failed to remove migration record: {e}")
        return False


def run_migration(name: str, direction: str = "up"):
    """Run a single migration"""
    try:
        # Import the migration module
        sys.path.append(str(MIGRATIONS_DIR.parent))
        module = import_module(f"migrations.{name}")
        
        # Call the appropriate function
        if direction == "up":
            result = module.migrate_up(DB_PATH)
        else:
            result = module.migrate_down(DB_PATH)
        
        if result:
            if direction == "up":
                record_migration(name)
            else:
                remove_migration_record(name)
        
        return result
    except Exception as e:
        print(f"❌ Failed to run migration {name}: {e}")
        return False


def migrate_up():
    """Run all pending migrations"""
    if not init_migrations_table():
        return False
    
    pending = get_pending_migrations()
    
    if not pending:
        print("✅ No pending migrations")
        return True
    
    print(f"Running {len(pending)} pending migration(s)...")
    
    for migration in pending:
        print(f"\nMigrating: {migration}")
        if not run_migration(migration, "up"):
            return False
    
    print(f"\n✅ Successfully applied {len(pending)} migration(s)")
    return True


def migrate_down(steps: int = 1):
    """Rollback last N migrations"""
    if not init_migrations_table():
        return False
    
    applied = get_applied_migrations()
    
    if not applied:
        print("✅ No migrations to rollback")
        return True
    
    to_rollback = applied[-steps:]
    print(f"Rolling back {len(to_rollback)} migration(s)...")
    
    for migration in reversed(to_rollback):
        print(f"\nRolling back: {migration}")
        if not run_migration(migration, "down"):
            return False
    
    print(f"\n✅ Successfully rolled back {len(to_rollback)} migration(s)")
    return True


def status():
    """Show migration status"""
    if not init_migrations_table():
        return False
    
    applied = get_applied_migrations()
    pending = get_pending_migrations()
    
    print("\n📊 Migration Status")
    print("=" * 50)
    
    if applied:
        print(f"\n✅ Applied ({len(applied)}):")
        for migration in applied:
            print(f"   • {migration}")
    else:
        print("\n✅ Applied: None")
    
    if pending:
        print(f"\n⏳ Pending ({len(pending)}):")
        for migration in pending:
            print(f"   • {migration}")
    else:
        print("\n⏳ Pending: None")
    
    return True


def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("Usage: python migrate.py [command]")
        print("\nCommands:")
        print("  up          Run all pending migrations")
        print("  down [n]    Rollback last N migrations (default: 1)")
        print("  status      Show migration status")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "up":
        success = migrate_up()
    elif command == "down":
        steps = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        success = migrate_down(steps)
    elif command == "status":
        success = status()
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
