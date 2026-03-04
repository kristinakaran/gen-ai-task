CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    practice TEXT,
    level TEXT,
    location TEXT
);

CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    user_email TEXT,
    session_id TEXT,
    event_type TEXT,
    model TEXT,
    tokens INTEGER,
    cost REAL,
    tool TEXT,
    duration REAL,
    success INTEGER
);