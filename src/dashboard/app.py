import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from src.analytics import queries

st.set_page_config(page_title="Claude Code Usage Analytics", layout="wide")

st.write("APP STARTED")
st.write("Python:", sys.version)
st.write("Root:", ROOT)


@st.cache_data
def load_all():
    conn = queries.get_connection()
    events = queries.load_events(conn)
    employees = queries.load_employees(conn)
    conn.close()
    return queries.enrich(events, employees)


def bar_chart(df, x, y, title, top_n=15):
    d = df.head(top_n)
    fig = plt.figure()
    plt.bar(d[x].astype(str), d[y])
    plt.title(title)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    st.pyplot(fig)


def line_chart(df, x, y, title):
    fig = plt.figure()
    plt.plot(df[x], df[y])
    plt.title(title)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    st.pyplot(fig)


def heatmap(pivot, title):
    fig = plt.figure()
    plt.imshow(pivot.values, aspect="auto")
    plt.title(title)
    plt.xlabel("Hour (UTC)")
    plt.ylabel("Day of week (0=Mon)")
    plt.xticks(range(len(pivot.columns)), pivot.columns)
    plt.yticks(range(len(pivot.index)), pivot.index)
    plt.tight_layout()
    st.pyplot(fig)


def main():
    st.title("Claude Code Usage Analytics")

    df = load_all()

    min_ts = df["timestamp"].min()
    max_ts = df["timestamp"].max()

    st.sidebar.header("Filters")
    practices_all = sorted(
        [p for p in df["practice"].dropna().unique().tolist() if str(p).strip() != ""]
    )
    practices = st.sidebar.multiselect("Practice", options=practices_all, default=practices_all)

    date_range = st.sidebar.date_input("Date range (UTC)", value=(min_ts.date(), max_ts.date()))
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        start_ts = pd.Timestamp(start_date).tz_localize("UTC")
        end_ts = pd.Timestamp(end_date).tz_localize("UTC") + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    else:
        start_ts, end_ts = None, None

    fdf = queries.filter_df(df, practices, start_ts, end_ts)
    k = queries.kpis(fdf)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Events", f"{k['events']:,}")
    c2.metric("Users", f"{k['users']:,}")
    c3.metric("Sessions", f"{k['sessions']:,}")
    c4.metric("Tokens", f"{k['tokens']:,}")
    c5.metric("Cost (USD)", f"{k['cost']:.4f}")

    st.divider()

    left, right = st.columns(2)

    with left:
        daily = queries.tokens_by_day(fdf)
        st.subheader("Tokens over time")
        line_chart(daily, "day", "tokens", "Tokens per day (UTC)")

        st.subheader("Events by type")
        by_type = queries.events_by_type(fdf)
        bar_chart(by_type, "event_type", "events", "Top event types", top_n=12)
        st.dataframe(by_type, use_container_width=True)

    with right:
        st.subheader("Cost by model")
        by_model = queries.cost_by_model(fdf)
        if len(by_model) > 0:
            bar_chart(by_model, "model", "cost", "Top models by cost", top_n=10)
            st.dataframe(by_model, use_container_width=True)
        else:
            st.info("No model data in selected range.")

        st.subheader("Tokens by practice")
        by_practice = queries.tokens_by_practice(fdf)
        if len(by_practice) > 0:
            bar_chart(by_practice, "practice", "tokens", "Tokens by practice", top_n=10)
            st.dataframe(by_practice, use_container_width=True)
        else:
            st.info("No practice data in selected range.")

    st.divider()

    bottom_left, bottom_right = st.columns(2)

    with bottom_left:
        st.subheader("Tool usage")
        tools = queries.tool_usage(fdf)
        bar_chart(tools, "tool", "events", "Top tools by events", top_n=12)
        st.dataframe(tools, use_container_width=True)

    with bottom_right:
        st.subheader("Peak usage (heatmap)")
        pivot = queries.peak_hours(fdf)
        heatmap(pivot, "Events by day-of-week and hour (UTC)")


if __name__ == "__main__":
    main()