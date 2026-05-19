"""Database initialization and connection management."""

import sqlite3
from pathlib import Path

from neet_predictor.config import DB_FILE, SCHEMA_FILE


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Get a SQLite connection with foreign keys enabled."""
    path = db_path or DB_FILE
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | None = None) -> Path:
    """Create the database from schema.sql. Returns the db path."""
    path = db_path or DB_FILE
    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_FILE}")

    schema_sql = SCHEMA_FILE.read_text(encoding="utf-8")
    conn = get_connection(path)
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()
    return path


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    """Check if a table exists in the database."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    return cursor.fetchone() is not None


def row_count(conn: sqlite3.Connection, table_name: str) -> int:
    """Get the number of rows in a table."""
    cursor = conn.execute(f"SELECT COUNT(*) FROM [{table_name}]")  # noqa: S608
    return cursor.fetchone()[0]
