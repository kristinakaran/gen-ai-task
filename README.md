# Claude Code Telemetry Analytics Platform

This project is an end-to-end analytics platform for processing Claude
Code telemetry data. It ingests raw telemetry logs, stores them in a
structured SQLite database, and exposes interactive insights through a
Streamlit dashboard.

------------------------------------------------------------------------

## What the project does

-   **ETL ingestion**
    -   Loads employee metadata from `output/employees.csv`
    -   Parses JSONL telemetry logs from `output/telemetry_logs.jsonl`
    -   Extracts important attributes such as timestamp, event type,
        model, tokens, cost, tool usage and duration
    -   Inserts structured data into a SQLite database
-   **Analytics**
    -   Token usage trends over time
    -   Event distribution by type
    -   Model cost comparison
    -   Token usage by practice/team
    -   Tool usage patterns
    -   Peak usage heatmap (day of week × hour)
-   **Dashboard**
    -   Interactive Streamlit dashboard
    -   Filters by practice and date range
    -   Multiple visualizations for telemetry insights

------------------------------------------------------------------------

## Requirements

-   Python 3.11+ recommended
-   Virtual environment

------------------------------------------------------------------------

## Setup

### 1. Create a virtual environment

Windows (PowerShell):

python -m venv .venv ..venv`\Scripts`{=tex}`\Activate`{=tex}.ps1

------------------------------------------------------------------------

### 2. Install dependencies

pip install -r requirements.txt

If dependencies change:

pip freeze \> requirements.txt

------------------------------------------------------------------------

## Run the pipeline

### 1. Initialize the database

This creates the SQLite database and applies the schema.

python .`\src`{=tex}`\db`{=tex}`\init`{=tex}\_db.py

------------------------------------------------------------------------

### 2. Ingest telemetry data

Loads employees and telemetry events into the database.

python .`\src`{=tex}`\etl`{=tex}`\ingest`{=tex}.py

Example output:

Inserted/updated employees: `<N>`{=html} Inserted events: `<N>`{=html}
\| Skipped: `<N>`{=html}

=== SANITY CHECK === Employees: `<N>`{=html} Events: `<N>`{=html}

------------------------------------------------------------------------

## Run the dashboard

streamlit run .`\src`{=tex}`\dashboard`{=tex}`\app`{=tex}.py

Then open the URL printed in the terminal (for example):

http://localhost:8504

------------------------------------------------------------------------

## Technologies

-   Python
-   SQLite
-   Pandas
-   Streamlit
-   Matplotlib
