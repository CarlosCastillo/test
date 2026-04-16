from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path
from uuid import uuid4

from .services import PACKS_DIR, REFS_DIR, get_voice, list_references, now_iso
from .db import BASE_DIR, get_conn


def export_voicepack(voice_id: str) -> Path:
    voice = get_voice(voice_id)
    if not voice:
        raise ValueError("Voz no encontrada")

    refs = list_references(voice_id)
    pack_name = f"{voice['name'].replace(' ', '_')}_{voice_id[:8]}.voicepack"
    pack_path = PACKS_DIR / pack_name

    manifest = {
        "pack_format_version": "1.0.0",
        "voice_id": voice["id"],
        "display_name": voice["name"],
        "engine": "coqui_xtts_v2",
        "created_at": now_iso(),
        "compatibility": {"min_voice_lab_version": "0.1.0"},
    }

    metadata = {
        "id": voice["id"],
        "name": voice["name"],
        "description": voice["description"],
        "voice_type": voice["voice_type"],
        "primary_language": voice["primary_language"],
        "tags": voice["tags"],
        "created_at": voice["created_at"],
        "reference_files": [Path(r["stored_path"]).name for r in refs],
        "preview_file": Path(voice["preview_path"]).name if voice.get("preview_path") else None,
        "default_params": voice.get("default_params"),
        "engine_assets": {"engine": "coqui_xtts_v2"},
    }

    with zipfile.ZipFile(pack_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        zf.writestr("metadata.json", json.dumps(metadata, indent=2, ensure_ascii=False))
        zf.writestr("config/default_params.json", json.dumps(metadata.get("default_params") or {}, indent=2, ensure_ascii=False))

        for ref in refs:
            ref_path = Path(ref["stored_path"])
            if ref_path.exists():
                zf.write(ref_path, arcname=f"references/{ref_path.name}")

        if voice.get("preview_path"):
            preview_path = Path(voice["preview_path"])
            if preview_path.exists():
                zf.write(preview_path, arcname=f"previews/{preview_path.name}")

    return pack_path


def import_voicepack(pack_path: Path) -> str:
    if not pack_path.exists():
        raise ValueError("Archivo de pack no existe")

    with zipfile.ZipFile(pack_path, "r") as zf:
        names = set(zf.namelist())
        if "manifest.json" not in names:
            raise ValueError("manifest.json no encontrado")
        if "metadata.json" not in names:
            raise ValueError("metadata.json no encontrado")

        manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
        metadata = json.loads(zf.read("metadata.json").decode("utf-8"))
        if not manifest.get("engine"):
            raise ValueError("Manifest inválido: engine faltante")

        new_voice_id = str(uuid4())
        preview_path = None

        with get_conn() as conn:
            conn.execute(
                """
                INSERT INTO voices (id, name, description, voice_type, primary_language, tags_json, created_at, preview_path, default_params_json, engine)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_voice_id,
                    metadata.get("name", f"Imported-{new_voice_id[:6]}"),
                    metadata.get("description", ""),
                    metadata.get("voice_type", "custom"),
                    metadata.get("primary_language", "es"),
                    json.dumps(metadata.get("tags", [])),
                    metadata.get("created_at") or now_iso(),
                    None,
                    json.dumps(metadata.get("default_params")) if metadata.get("default_params") else None,
                    manifest.get("engine", "coqui_xtts_v2"),
                ),
            )

            ref_dir = REFS_DIR / new_voice_id
            ref_dir.mkdir(parents=True, exist_ok=True)

            for name in zf.namelist():
                if name.startswith("references/") and not name.endswith("/"):
                    target = ref_dir / Path(name).name
                    with zf.open(name) as src, target.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
                    conn.execute(
                        """
                        INSERT INTO references (id, voice_id, original_name, stored_path, created_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (str(uuid4()), new_voice_id, Path(name).name, str(target), now_iso()),
                    )

            for name in zf.namelist():
                if name.startswith("previews/") and not name.endswith("/"):
                    preview_dir = BASE_DIR / "data" / "storage" / "previews" / new_voice_id
                    preview_dir.mkdir(parents=True, exist_ok=True)
                    target = preview_dir / Path(name).name
                    with zf.open(name) as src, target.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
                    preview_path = str(target)
                    break

            if preview_path:
                conn.execute("UPDATE voices SET preview_path = ? WHERE id = ?", (preview_path, new_voice_id))

        return new_voice_id
