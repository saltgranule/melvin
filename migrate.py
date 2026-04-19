import sqlite3
import os
import datetime

# path to your melvin database
DB_PATH = "Backend/python/melvin.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"error: database not found at {DB_PATH}")
        return

    print(f"starting migration for {DB_PATH}...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. ensure guild_configs has all modern fields
    cursor.execute("PRAGMA table_info(guild_configs)")
    columns = [row[1] for row in cursor.fetchall()]

    # list of (column_name, sql_type)
    required_guild_cols = [
        ("base_enabled", "BOOLEAN DEFAULT 1"),
        ("moderation_enabled", "BOOLEAN DEFAULT 1"),
        ("logging_enabled", "BOOLEAN DEFAULT 0"),
        ("tickets_enabled", "BOOLEAN DEFAULT 0"),
        ("frogboard_enabled", "BOOLEAN DEFAULT 0"),
        ("levels_enabled", "BOOLEAN DEFAULT 0"),
        ("economy_enabled", "BOOLEAN DEFAULT 0"),
        ("counting_enabled", "BOOLEAN DEFAULT 0"),
        ("commands_ran", "INTEGER DEFAULT 0"),
        ("message_count", "INTEGER DEFAULT 0"),
        ("joined_at", f"DATETIME DEFAULT '{datetime.datetime.utcnow().isoformat()}'")
    ]

    for col_name, col_type in required_guild_cols:
        if col_name not in columns:
            print(f"-> adding missing column: guild_configs.{col_name}")
            try:
                cursor.execute(f"ALTER TABLE guild_configs ADD COLUMN {col_name} {col_type}")
                conn.commit()
            except Exception as e:
                print(f"   ! failed: {e}")
        else:
            print(f"-> column exists: guild_configs.{col_name}")

    # 2. ensure dashboard_logs table exists (fallback if init_db didn't run)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dashboard_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id BIGINT,
            user_id BIGINT,
            user_name VARCHAR(100),
            user_avatar VARCHAR(255),
            action VARCHAR(255),
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    print("-> checked dashboard_logs table.")

    conn.close()
    print("migration complete.")

if __name__ == "__main__":
    migrate()
