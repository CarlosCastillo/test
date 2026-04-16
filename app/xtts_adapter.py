from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class EngineCapabilities:
    supports_style_transfer: bool = False
    supports_training: bool = False
    supports_preview_generation: bool = False


class TtsEngineAdapter:
    def load_model(self) -> None:
        raise NotImplementedError

    def synthesize_preview(self, text: str, language: str, reference_files: list[str], params: dict | None = None) -> str:
        raise NotImplementedError

    def validate_references(self, files: list[str]) -> dict:
        raise NotImplementedError

    def get_capabilities(self) -> dict:
        raise NotImplementedError


class XttsV2Adapter(TtsEngineAdapter):
    """
    Stub para Iteración A.
    Preparado para reemplazar por integración real con Coqui XTTS v2 en Iteración B.
    """

    def __init__(self) -> None:
        self._loaded = False

    def load_model(self) -> None:
        self._loaded = False

    def synthesize_preview(self, text: str, language: str, reference_files: list[str], params: dict | None = None) -> str:
        raise NotImplementedError("XTTS preview generation se implementa en Iteración B")

    def validate_references(self, files: list[str]) -> dict:
        missing = [f for f in files if not Path(f).exists()]
        return {"ok": len(missing) == 0, "missing": missing}

    def get_capabilities(self) -> dict:
        return EngineCapabilities(supports_preview_generation=False).__dict__
