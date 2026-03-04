import sqlite3
from pathlib import Path

DB_PATH = Path("data/analytics.db")
SCHEMA_PATH = Path("src/db/schema.sql")

def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(schema)
        conn.commit()

    print(f"OK: Initialized DB at {DB_PATH.resolve()}")

if __name__ == "__main__":
    main()