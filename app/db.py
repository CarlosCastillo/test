from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "voice_lab.db"


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS voices (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                voice_type TEXT DEFAULT 'custom',
                primary_language TEXT DEFAULT 'es',
                tags_json TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                preview_path TEXT,
                default_params_json TEXT,
                engine TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS references (
                id TEXT PRIMARY KEY,
                voice_id TEXT NOT NULL,
                original_name TEXT NOT NULL,
                stored_path TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(voice_id) REFERENCES voices(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute("PRAGMA foreign_keys = ON")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def row_to_voice(row: sqlite3.Row) -> dict:
    data = dict(row)
    data["tags"] = json.loads(data.pop("tags_json") or "[]")
    params = data.pop("default_params_json")
    data["default_params"] = json.loads(params) if params else None
    return data
