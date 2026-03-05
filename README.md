
Claude Code Telemetry Analytics Platform

This project is an end-to-end analytics platform for processing Claude Code telemetry data.
It ingests raw telemetry logs, stores them in a structured SQLite database, and exposes interactive insights through both a Streamlit dashboard and REST API.

------------------------------------------------------------

WHAT THE PROJECT DOES

ETL ingestion
- Loads employee metadata from output/employees.csv
- Parses JSONL telemetry logs from output/telemetry_logs.jsonl
- Extracts attributes such as timestamp, event type, model, tokens, cost, tool usage and duration
- Inserts structured data into a SQLite database

Analytics
The platform generates several analytics insights:
- Token usage trends over time
- Event distribution by type
- Model cost comparison
- Token usage by practice/team
- Tool usage patterns
- Peak usage heatmap (day of week × hour)

Dashboard
An interactive dashboard built with Streamlit provides:
- Filtering by practice/team
- Filtering by date range
- Multiple visualizations for telemetry insights
- Exploration of usage patterns

API (Bonus Feature)
A REST API built with FastAPI provides programmatic access to analytics data.

Example endpoints:
GET /health
GET /stats/summary
GET /stats/events-by-type
GET /stats/tokens-by-day
GET /stats/cost-by-model

API documentation:
http://127.0.0.1:8000/docs

------------------------------------------------------------

REQUIREMENTS

Python 3.11+
Virtual environment recommended

------------------------------------------------------------

SETUP

Create virtual environment (Windows PowerShell)

python -m venv .venv
.\.venv\Scripts\Activate.ps1

Install dependencies

pip install -r requirements.txt

If dependencies change:

pip freeze > requirements.txt

------------------------------------------------------------

RUN THE PIPELINE

Initialize the database

python src/db/init_db.py

Ingest telemetry data

python src/etl/ingest.py

Example output:

Inserted/updated employees: <N>
Inserted events: <N> | Skipped: <N>

=== SANITY CHECK ===
Employees: <N>
Events: <N>

------------------------------------------------------------

RUN THE DASHBOARD

streamlit run src/dashboard/app.py

Then open the URL printed in the terminal (for example):

http://localhost:8504

------------------------------------------------------------

RUN THE API (BONUS)

python -m uvicorn src.api.main:app --reload

Open API documentation:

http://127.0.0.1:8000/docs

------------------------------------------------------------

TECHNOLOGIES

Python
SQLite
Pandas
Streamlit
Matplotlib
FastAPI
