from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .db import init_db
from .services import PACKS_DIR, create_voice, delete_reference, delete_voice, get_voice, list_references, list_voices, parse_tags, update_voice, add_reference_file
from .voicepack import export_voicepack, import_voicepack
from .xtts_adapter import XttsV2Adapter

app = FastAPI(title="Voice Lab - Iteración A")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

xtts_adapter = XttsV2Adapter()


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/")
def home(request: Request):
    voices = list_voices()
    return templates.TemplateResponse("index.html", {"request": request, "voices": voices})


@app.post("/voices")
def create_voice_route(
    name: str = Form(...),
    description: str = Form(""),
    voice_type: str = Form("custom"),
    primary_language: str = Form("es"),
    tags: str = Form(""),
):
    voice_id = create_voice(name, description, voice_type, primary_language, parse_tags(tags))
    return RedirectResponse(url=f"/voices/{voice_id}", status_code=303)


@app.get("/voices/{voice_id}")
def voice_detail(request: Request, voice_id: str):
    voice = get_voice(voice_id)
    if not voice:
        raise HTTPException(status_code=404, detail="Voz no encontrada")
    refs = list_references(voice_id)
    return templates.TemplateResponse("voice_detail.html", {"request": request, "voice": voice, "references": refs})


@app.post("/voices/{voice_id}/update")
def update_voice_route(
    voice_id: str,
    name: str = Form(...),
    description: str = Form(""),
    voice_type: str = Form("custom"),
    primary_language: str = Form("es"),
    tags: str = Form(""),
):
    if not get_voice(voice_id):
        raise HTTPException(status_code=404, detail="Voz no encontrada")
    update_voice(voice_id, name, description, voice_type, primary_language, parse_tags(tags))
    return RedirectResponse(url=f"/voices/{voice_id}", status_code=303)


@app.post("/voices/{voice_id}/delete")
def delete_voice_route(voice_id: str):
    if not get_voice(voice_id):
        raise HTTPException(status_code=404, detail="Voz no encontrada")
    delete_voice(voice_id)
    return RedirectResponse(url="/", status_code=303)


@app.post("/voices/{voice_id}/references")
def add_reference_route(voice_id: str, files: list[UploadFile] = File(...)):
    if not get_voice(voice_id):
        raise HTTPException(status_code=404, detail="Voz no encontrada")

    for upload in files:
        try:
            add_reference_file(voice_id, upload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        finally:
            upload.file.close()

    return RedirectResponse(url=f"/voices/{voice_id}", status_code=303)


@app.post("/references/{reference_id}/delete")
def delete_reference_route(reference_id: str):
    voice_id = delete_reference(reference_id)
    if not voice_id:
        raise HTTPException(status_code=404, detail="Referencia no encontrada")
    return RedirectResponse(url=f"/voices/{voice_id}", status_code=303)


@app.post("/voices/{voice_id}/export")
def export_voicepack_route(voice_id: str):
    try:
        pack_path = export_voicepack(voice_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FileResponse(path=pack_path, media_type="application/zip", filename=pack_path.name)


@app.post("/packs/import")
def import_voicepack_route(file: UploadFile = File(...)):
    if not file.filename or not file.filename.endswith(".voicepack"):
        raise HTTPException(status_code=400, detail="Archivo inválido, se espera .voicepack")

    tmp_path = PACKS_DIR / f"tmp_{file.filename}"
    with tmp_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    file.file.close()

    try:
        new_voice_id = import_voicepack(tmp_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    return RedirectResponse(url=f"/voices/{new_voice_id}", status_code=303)


@app.get("/health")
def health():
    return {"ok": True, "engine_adapter": xtts_adapter.get_capabilities(), "iteration": "A"}
