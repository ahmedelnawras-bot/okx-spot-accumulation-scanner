from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from accumulation_scanner.config import settings


def db_path() -> str:
    url = settings.database_url
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "", 1)
    return "scanner.db"


@contextmanager
def connect():
    path = db_path()
    if path != ":memory":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inst_id TEXT NOT NULL,
            first_accumulation_seen TEXT NOT NULL,
            created_at TEXT NOT NULL,
            accumulation_score REAL NOT NULL,
            accumulation_age_days INTEGER NOT NULL,
            accumulation_velocity REAL NOT NULL,
            fresh_accumulation_score REAL NOT NULL,
            distribution_score REAL NOT NULL,
            capital_efficiency_score REAL NOT NULL,
            status TEXT NOT NULL,
            reasons TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1
        );
        CREATE INDEX IF NOT EXISTS idx_signals_inst_created ON signals(inst_id, created_at);

        CREATE TABLE IF NOT EXISTS score_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inst_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            accumulation_score REAL NOT NULL,
            fresh_accumulation_score REAL NOT NULL,
            velocity REAL NOT NULL,
            status TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_id INTEGER NOT NULL,
            inst_id TEXT NOT NULL,
            horizon_days INTEGER NOT NULL,
            evaluated_at TEXT NOT NULL,
            future_return_pct REAL NOT NULL,
            max_gain_pct REAL NOT NULL,
            max_drawdown_pct REAL NOT NULL,
            verdict TEXT NOT NULL,
            UNIQUE(signal_id, horizon_days)
        );

        CREATE TABLE IF NOT EXISTS scan_rejections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inst_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            reason TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS daily_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_date TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            payload TEXT NOT NULL
        );
        """)
