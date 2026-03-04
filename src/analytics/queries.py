import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = Path("data/analytics.db")


def get_connection() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"DB not found at {DB_PATH}. Run: python src/db/init_db.py")
    return sqlite3.connect(DB_PATH)


def load_events(conn: sqlite3.Connection) -> pd.DataFrame:
    df = pd.read_sql_query(
        """
        SELECT
          e.id,
          e.timestamp,
          e.user_email,
          e.session_id,
          e.event_type,
          e.model,
          e.tokens,
          e.cost,
          e.tool,
          e.duration,
          e.success
        FROM events e
        """,
        conn,
    )

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df["tokens"] = pd.to_numeric(df["tokens"], errors="coerce").fillna(0).astype(int)
    df["cost"] = pd.to_numeric(df["cost"], errors="coerce").fillna(0.0)
    df["duration"] = pd.to_numeric(df["duration"], errors="coerce")
    df["success"] = pd.to_numeric(df["success"], errors="coerce")
    return df


def load_employees(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query(
        """
        SELECT
          email,
          full_name,
          practice,
          level,
          location
        FROM employees
        """,
        conn,
    )


def enrich(events: pd.DataFrame, employees: pd.DataFrame) -> pd.DataFrame:
    emp = employees.rename(columns={"email": "user_email"})
    return events.merge(emp, on="user_email", how="left")


def filter_df(df: pd.DataFrame, practices, start_ts, end_ts) -> pd.DataFrame:
    out = df.copy()
    if start_ts is not None:
        out = out[out["timestamp"] >= start_ts]
    if end_ts is not None:
        out = out[out["timestamp"] <= end_ts]
    if practices:
        out = out[out["practice"].isin(practices)]
    return out


def kpis(df: pd.DataFrame) -> dict:
    return {
        "events": int(df["id"].nunique()),
        "users": int(df["user_email"].nunique(dropna=True)),
        "sessions": int(df["session_id"].nunique(dropna=True)),
        "tokens": int(df["tokens"].sum()),
        "cost": float(df["cost"].sum()),
    }


def tokens_by_day(df: pd.DataFrame) -> pd.DataFrame:
    d = df.dropna(subset=["timestamp"]).copy()
    d["day"] = d["timestamp"].dt.floor("D")
    out = d.groupby("day", as_index=False).agg(tokens=("tokens", "sum"), cost=("cost", "sum"), events=("id", "count"))
    return out.sort_values("day")


def events_by_type(df: pd.DataFrame) -> pd.DataFrame:
    out = df.groupby("event_type", as_index=False).agg(events=("id", "count"), tokens=("tokens", "sum"), cost=("cost", "sum"))
    return out.sort_values("events", ascending=False)


def cost_by_model(df: pd.DataFrame) -> pd.DataFrame:
    d = df[df["model"].notna() & (df["model"] != "")]
    out = d.groupby("model", as_index=False).agg(cost=("cost", "sum"), events=("id", "count"), tokens=("tokens", "sum"))
    return out.sort_values("cost", ascending=False)


def tokens_by_practice(df: pd.DataFrame) -> pd.DataFrame:
    d = df[df["practice"].notna() & (df["practice"] != "")]
    out = d.groupby("practice", as_index=False).agg(tokens=("tokens", "sum"), cost=("cost", "sum"), users=("user_email", "nunique"))
    return out.sort_values("tokens", ascending=False)


def tool_usage(df: pd.DataFrame) -> pd.DataFrame:
    d = df[df["tool"].notna() & (df["tool"] != "")]
    out = d.groupby("tool", as_index=False).agg(events=("id", "count"), tokens=("tokens", "sum"))
    return out.sort_values("events", ascending=False)


def peak_hours(df: pd.DataFrame) -> pd.DataFrame:
    d = df.dropna(subset=["timestamp"]).copy()
    d["dow"] = d["timestamp"].dt.dayofweek
    d["hour"] = d["timestamp"].dt.hour
    return d.pivot_table(index="dow", columns="hour", values="id", aggfunc="count", fill_value=0).sort_index()