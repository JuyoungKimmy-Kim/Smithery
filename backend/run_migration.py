"""
Run database migration for MCP Auth Tokens table
"""

import sqlite3
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Run the migration SQL file"""
    db_path = "mcp_market.db"
    migration_file = "backend/database/migrations/add_mcp_auth_tokens_table.sql"

    if not os.path.exists(db_path):
        logger.error(f"Database file not found: {db_path}")
        return False

    if not os.path.exists(migration_file):
        logger.error(f"Migration file not found: {migration_file}")
        return False

    try:
        # Read migration SQL
        with open(migration_file, 'r') as f:
            migration_sql = f.read()

        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute migration
        logger.info("Running migration: add_mcp_auth_tokens_table.sql")
        cursor.executescript(migration_sql)

        conn.commit()
        conn.close()

        logger.info("✅ Migration completed successfully!")
        logger.info("Created table: mcp_auth_tokens")
        return True

    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = run_migration()
    exit(0 if success else 1)
