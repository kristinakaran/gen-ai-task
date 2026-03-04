import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path("data") / "analytics.db"

def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """
    Single responsibility: opens a sqlite connection.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn