from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from fastapi import UploadFile

from .db import BASE_DIR, get_conn, row_to_voice

ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}
STORAGE_DIR = BASE_DIR / "data" / "storage"
REFS_DIR = STORAGE_DIR / "references"
PREVIEWS_DIR = STORAGE_DIR / "previews"
PACKS_DIR = STORAGE_DIR / "packs"


for d in [REFS_DIR, PREVIEWS_DIR, PACKS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_voice(name: str, description: str, voice_type: str, primary_language: str, tags: list[str]) -> str:
    voice_id = str(uuid4())
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO voices (id, name, description, voice_type, primary_language, tags_json, created_at, preview_path, default_params_json, engine)
            VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, 'coqui_xtts_v2')
            """,
            (voice_id, name.strip(), description.strip(), voice_type.strip(), primary_language.strip(), json.dumps(tags), now_iso()),
        )
    return voice_id


def update_voice(voice_id: str, name: str, description: str, voice_type: str, primary_language: str, tags: list[str]) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE voices
            SET name = ?, description = ?, voice_type = ?, primary_language = ?, tags_json = ?
            WHERE id = ?
            """,
            (name.strip(), description.strip(), voice_type.strip(), primary_language.strip(), json.dumps(tags), voice_id),
        )


def list_voices() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM voices ORDER BY created_at DESC").fetchall()
    return [row_to_voice(r) for r in rows]


def get_voice(voice_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM voices WHERE id = ?", (voice_id,)).fetchone()
    return row_to_voice(row) if row else None


def delete_voice(voice_id: str) -> None:
    refs = list_references(voice_id)
    for ref in refs:
        Path(ref["stored_path"]).unlink(missing_ok=True)
    voice = get_voice(voice_id)
    if voice and voice.get("preview_path"):
        Path(voice["preview_path"]).unlink(missing_ok=True)
    with get_conn() as conn:
        conn.execute("DELETE FROM voices WHERE id = ?", (voice_id,))


def list_references(voice_id: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM references WHERE voice_id = ? ORDER BY created_at", (voice_id,)).fetchall()
    return [dict(r) for r in rows]


def _validate_upload_file(upload: UploadFile) -> None:
    ext = Path(upload.filename or "").suffix.lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise ValueError(f"Formato no soportado: {ext}")


def add_reference_file(voice_id: str, upload: UploadFile) -> str:
    if not get_voice(voice_id):
        raise ValueError("Voz no encontrada")
    _validate_upload_file(upload)

    ref_id = str(uuid4())
    ext = Path(upload.filename or "").suffix.lower()
    voice_ref_dir = REFS_DIR / voice_id
    voice_ref_dir.mkdir(parents=True, exist_ok=True)

    stored_path = voice_ref_dir / f"{ref_id}{ext}"
    with stored_path.open("wb") as f:
        shutil.copyfileobj(upload.file, f)

    if not stored_path.exists() or stored_path.stat().st_size == 0:
        raise ValueError("Archivo inválido o vacío")

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO references (id, voice_id, original_name, stored_path, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (ref_id, voice_id, upload.filename or stored_path.name, str(stored_path), now_iso()),
        )
    return ref_id


def delete_reference(reference_id: str) -> str | None:
    with get_conn() as conn:
        row = conn.execute("SELECT voice_id, stored_path FROM references WHERE id = ?", (reference_id,)).fetchone()
        if not row:
            return None
        voice_id = row["voice_id"]
        Path(row["stored_path"]).unlink(missing_ok=True)
        conn.execute("DELETE FROM references WHERE id = ?", (reference_id,))
    return voice_id


def parse_tags(raw: str) -> list[str]:
    return [t.strip() for t in raw.split(",") if t.strip()]


def ensure_files_exist(paths: Iterable[str]) -> bool:
    return all(Path(p).exists() for p in paths)
