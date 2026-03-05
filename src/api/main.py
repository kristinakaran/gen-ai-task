from pathlib import Path
import sqlite3
from typing import Optional

from fastapi import FastAPI, HTTPException, Query

DB_PATH = Path("data/analytics.db")

app = FastAPI(title="Claude Code Telemetry API", version="1.0.0")


def get_conn() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise HTTPException(status_code=500, detail=f"DB not found at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/health")
def health():
    return {"status": "ok", "db_path": str(DB_PATH), "db_exists": DB_PATH.exists()}


@app.get("/stats/summary")
def summary(
    practice: Optional[str] = None,
    start: Optional[str] = None,  # ISO string e.g. 2026-01-01T00:00:00Z
    end: Optional[str] = None,
):
    conn = get_conn()
    try:
        where = []
        params = []

        if practice:
            where.append("e.practice = ?")
            params.append(practice)

        if start:
            where.append("ev.timestamp >= ?")
            params.append(start)

        if end:
            where.append("ev.timestamp <= ?")
            params.append(end)

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        q = f"""
        SELECT
          COUNT(*) AS events,
          COUNT(DISTINCT ev.user_email) AS users,
          COUNT(DISTINCT ev.session_id) AS sessions,
          COALESCE(SUM(ev.tokens), 0) AS tokens,
          COALESCE(SUM(ev.cost), 0.0) AS cost
        FROM events ev
        LEFT JOIN employees e ON e.email = ev.user_email
        {where_sql}
        """

        row = conn.execute(q, params).fetchone()
        return dict(row)
    finally:
        conn.close()


@app.get("/stats/events-by-type")
def events_by_type(
    practice: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = Query(15, ge=1, le=100),
):
    conn = get_conn()
    try:
        where = []
        params = []

        if practice:
            where.append("e.practice = ?")
            params.append(practice)
        if start:
            where.append("ev.timestamp >= ?")
            params.append(start)
        if end:
            where.append("ev.timestamp <= ?")
            params.append(end)

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        q = f"""
        SELECT ev.event_type, COUNT(*) AS events
        FROM events ev
        LEFT JOIN employees e ON e.email = ev.user_email
        {where_sql}
        GROUP BY ev.event_type
        ORDER BY events DESC
        LIMIT ?
        """
        rows = conn.execute(q, params + [limit]).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@app.get("/stats/tokens-by-day")
def tokens_by_day(
    practice: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
):
    conn = get_conn()
    try:
        where = []
        params = []

        if practice:
            where.append("e.practice = ?")
            params.append(practice)
        if start:
            where.append("ev.timestamp >= ?")
            params.append(start)
        if end:
            where.append("ev.timestamp <= ?")
            params.append(end)

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        q = f"""
        SELECT SUBSTR(ev.timestamp, 1, 10) AS day,
               COALESCE(SUM(ev.tokens), 0) AS tokens
        FROM events ev
        LEFT JOIN employees e ON e.email = ev.user_email
        {where_sql}
        GROUP BY day
        ORDER BY day ASC
        """
        rows = conn.execute(q, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@app.get("/stats/cost-by-model")
def cost_by_model(
    practice: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
):
    conn = get_conn()
    try:
        where = ["ev.model IS NOT NULL", "ev.model != ''"]
        params = []

        if practice:
            where.append("e.practice = ?")
            params.append(practice)
        if start:
            where.append("ev.timestamp >= ?")
            params.append(start)
        if end:
            where.append("ev.timestamp <= ?")
            params.append(end)

        where_sql = "WHERE " + " AND ".join(where)

        q = f"""
        SELECT ev.model, COALESCE(SUM(ev.cost), 0.0) AS cost
        FROM events ev
        LEFT JOIN employees e ON e.email = ev.user_email
        {where_sql}
        GROUP BY ev.model
        ORDER BY cost DESC
        LIMIT ?
        """
        rows = conn.execute(q, params + [limit]).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()