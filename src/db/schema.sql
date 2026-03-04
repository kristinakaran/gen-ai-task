PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS employees (
  email TEXT PRIMARY KEY,
  full_name TEXT,
  practice TEXT,
  level TEXT,
  location TEXT
);

CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT NOT NULL,
  user_email TEXT,
  session_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  model TEXT,
  tokens INTEGER,
  cost REAL,
  tool TEXT,
  duration REAL,
  success INTEGER,
  FOREIGN KEY (user_email) REFERENCES employees(email)
);

CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_user_email ON events(user_email);
CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_session_id ON events(session_id);