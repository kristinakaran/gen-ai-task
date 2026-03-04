import sqlite3

conn = sqlite3.connect("data/analytics.db")

tables = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()

print("Tables in DB:")
for t in tables:
    print("-", t[0])