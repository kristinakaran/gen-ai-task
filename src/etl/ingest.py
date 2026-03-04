import csv
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple

DB_PATH = Path("data/analytics.db")
EMPLOYEES_CSV = Path("output/employees.csv")
TELEMETRY_JSONL = Path("output/telemetry_logs.jsonl")


def safe_int(x: Any) -> Optional[int]:
    try:
        if x is None or x == "":
            return None
        return int(float(x))
    except Exception:
        return None


def safe_float(x: Any) -> Optional[float]:
    try:
        if x is None or x == "":
            return None
        return float(x)
    except Exception:
        return None


def parse_cloudwatch_line(line: str) -> Iterable[Dict[str, Any]]:
    """
    Each JSONL line is a CloudWatch subscription "DATA_MESSAGE" containing logEvents[].
    Each logEvent.message is itself a JSON string.
    We yield parsed inner event dicts:
      { body, attributes, scope, resource }
    """
    outer = json.loads(line)
    for le in outer.get("logEvents", []):
        msg = le.get("message")
        if not msg:
            continue
        try:
            inner = json.loads(msg)
        except json.JSONDecodeError:
            continue
        yield inner


def map_event(inner: Dict[str, Any]) -> Dict[str, Any]:
    attrs = inner.get("attributes", {}) or {}
    body = inner.get("body")

    # Common fields
    ts = attrs.get("event.timestamp")  # ISO string
    user_email = attrs.get("user.email")
    session_id = attrs.get("session.id")
    event_type = attrs.get("event.name") or body  # fallback

    model = attrs.get("model")
    tool = attrs.get("tool_name") or attrs.get("terminal.type")

    # Tokens: some events have input/output tokens, some not
    in_tok = safe_int(attrs.get("input_tokens"))
    out_tok = safe_int(attrs.get("output_tokens"))
    tokens = None
    if in_tok is not None or out_tok is not None:
        tokens = (in_tok or 0) + (out_tok or 0)

    cost = safe_float(attrs.get("cost_usd"))

    # duration in ms -> seconds
    dur_ms = safe_float(attrs.get("duration_ms"))
    duration = (dur_ms / 1000.0) if dur_ms is not None else None

    # success can be "true"/"false"
    success_raw = attrs.get("success")
    success = None
    if isinstance(success_raw, str):
        if success_raw.lower() == "true":
            success = 1
        elif success_raw.lower() == "false":
            success = 0
    elif isinstance(success_raw, bool):
        success = 1 if success_raw else 0

    return {
        "timestamp": ts,
        "user_email": user_email,
        "session_id": session_id,
        "event_type": event_type,
        "model": model,
        "tokens": tokens,
        "cost": cost,
        "tool": tool,
        "duration": duration,
        "success": success,
    }


def ingest_employees(conn: sqlite3.Connection) -> int:
    if not EMPLOYEES_CSV.exists():
        raise FileNotFoundError(f"Missing {EMPLOYEES_CSV}")

    inserted = 0
    with EMPLOYEES_CSV.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)  # uses header row automatically
        rows = []
        for r in reader:
            rows.append(
                (
                    r.get("email"),
                    r.get("full_name"),
                    r.get("practice"),
                    r.get("level"),
                    r.get("location"),
                )
            )

    conn.executemany(
        """
        INSERT OR REPLACE INTO employees (email, full_name, practice, level, location)
        VALUES (?, ?, ?, ?, ?)
        """,
        rows,
    )
    inserted = len(rows)
    return inserted


def ingest_events(conn: sqlite3.Connection) -> Tuple[int, int]:
    if not TELEMETRY_JSONL.exists():
        raise FileNotFoundError(f"Missing {TELEMETRY_JSONL}")

    inserted = 0
    skipped = 0

    with TELEMETRY_JSONL.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                for inner in parse_cloudwatch_line(line):
                    mapped = map_event(inner)

                    # Minimal validation: must have timestamp and event_type
                    if not mapped["timestamp"] or not mapped["event_type"]:
                        skipped += 1
                        continue

                    conn.execute(
                        """
                        INSERT INTO events
                        (timestamp, user_email, session_id, event_type, model, tokens, cost, tool, duration, success)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            mapped["timestamp"],
                            mapped["user_email"],
                            mapped["session_id"],
                            mapped["event_type"],
                            mapped["model"],
                            mapped["tokens"],
                            mapped["cost"],
                            mapped["tool"],
                            mapped["duration"],
                            mapped["success"],
                        ),
                    )
                    inserted += 1

            except Exception:
                # if the whole outer line is broken, skip it
                skipped += 1
                continue

            # Commit in chunks so it's fast but safe
            if line_no % 500 == 0:
                conn.commit()

    conn.commit()
    return inserted, skipped


def print_sanity(conn: sqlite3.Connection) -> None:
    employees_count = conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
    events_count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    top_types = conn.execute(
        """
        SELECT event_type, COUNT(*) AS c
        FROM events
        GROUP BY event_type
        ORDER BY c DESC
        LIMIT 10
        """
    ).fetchall()

    print("=== SANITY CHECK ===")
    print(f"Employees: {employees_count}")
    print(f"Events:    {events_count}")
    print("Top event types:")
    for t, c in top_types:
        print(f"  {t}: {c}")


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"DB not found at {DB_PATH}. Run: python src/db/init_db.py"
        )

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")

        emp_n = ingest_employees(conn)
        print(f"Inserted/updated employees: {emp_n}")

        ev_n, skipped = ingest_events(conn)
        print(f"Inserted events: {ev_n} | Skipped: {skipped}")

        print_sanity(conn)


if __name__ == "__main__":
    main()