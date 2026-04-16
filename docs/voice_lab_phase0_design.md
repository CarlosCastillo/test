# Voice Lab — Fase 0 (Diseño Técnico)

## 1) Arquitectura recomendada

Arquitectura propuesta: **monolito modular** (backend + UI ligera), centrado en un solo motor de síntesis en MVP (**Coqui XTTS v2**) y preparado para enchufar motores futuros vía interfaces.

### Capas

1. **UI/Application Layer**
   - Crear voz
   - Importar audios de referencia
   - Generar preview
   - Gestionar metadatos
   - Exportar/importar voice packs

2. **Domain Layer (núcleo de negocio)**
   - Entidades: `VoiceProfile`, `VoiceReference`, `VoicePreview`, `VoicePackManifest`
   - Casos de uso: `CreateVoice`, `GeneratePreview`, `ExportVoicePack`, `ImportVoicePack`, `UpdateMetadata`

3. **Engine Adapter Layer**
   - Interfaz común `TtsEngineAdapter`
   - Implementación MVP: `XttsV2Adapter`
   - Placeholder futuro: `OpenVoiceStyleAdapter`, `PiperTrainingAdapter`

4. **Infrastructure Layer**
   - Almacenamiento local (SQLite + filesystem)
   - Gestión de archivos (copias, checksums, rutas)
   - Reproductor de audio para previews
   - Empaquetado/desempaquetado (`.voicepack`)

## 2) Stack técnico propuesto

### Opción recomendada (rápida para MVP local)
- **Backend/API**: Python 3.11 + FastAPI
- **Motor TTS**: Coqui `TTS` (XTTS v2)
- **Persistencia**: SQLite (SQLModel o SQLAlchemy)
- **Procesado audio**: `ffmpeg` + `soundfile`/`librosa` (solo tareas necesarias)
- **UI**: escritorio web local con React + Vite (o UI mínima con plantillas)
- **Empaquetado**: `zipfile` estándar (`.voicepack`)

### Por qué este stack
- XTTS v2 está mejor integrado en ecosistema Python.
- Permite iterar rápido sin acoplarse a tu programa TTS principal.
- SQLite simplifica librería local (sin servidor externo).

## 3) Integración de XTTS v2 (MVP)

### Flujo mínimo de inferencia
1. Usuario crea voz (`name`, `language`, etc.).
2. Sube 1..N audios de referencia (`wav/mp3/flac`).
3. El sistema normaliza/valida audio (duración, sample rate, ruido básico).
4. `XttsV2Adapter` recibe:
   - texto de prueba
   - idioma
   - lista de referencias
   - parámetros básicos (temperature/top-k/top-p/speed si aplica)
5. Genera preview (`.wav`) y lo guarda en `storage/previews/...`.
6. Guarda metadatos de la voz y rutas de assets en DB.

### Contrato de adaptador
- `load_model()`
- `synthesize_preview(text, language, reference_files, params) -> preview_path`
- `validate_references(files) -> report`
- `get_capabilities() -> {supports_style_transfer: false, supports_training: false, ...}`

Esto permite enchufar OpenVoice/Piper después sin romper casos de uso.

## 4) Formato propuesto del voice pack

Extensión sugerida: **`.voicepack`** (zip).

```text
my_voice.voicepack
├── manifest.json
├── metadata.json
├── references/
│   ├── ref_01.wav
│   └── ref_02.wav
├── previews/
│   └── default_preview.wav
└── config/
    └── default_params.json
```

### `manifest.json` (mínimo)
- `pack_format_version` (ej. `1.0.0`)
- `voice_id`
- `display_name`
- `engine` (`coqui_xtts_v2`)
- `created_at`
- `files` (lista con hash SHA256 opcional)
- `compatibility` (versión mínima de Voice Lab / TTS host)

### `metadata.json` (campos funcionales)
- `id`, `name`, `description`
- `voice_type` (character, narrator, custom, etc.)
- `primary_language`
- `tags`[]
- `created_at`
- `reference_files`[]
- `preview_file`
- `default_params`
- `engine_assets` (rutas internas del pack)

### Regla de compatibilidad futura
Define desde ya:
- `source = "voice_lab"`
- `engine_family = "xtts"`
- `engine_version_range`

Así tu TTS principal podrá detectar “biblioteca catálogo” vs “biblioteca voice packs”.

## 5) Estructura de proyecto sugerida

```text
voice-lab/
├── apps/
│   ├── api/
│   │   ├── main.py
│   │   ├── routers/
│   │   └── schemas/
│   └── ui/
├── core/
│   ├── domain/
│   │   ├── entities.py
│   │   └── use_cases/
│   ├── engines/
│   │   ├── base.py
│   │   └── xtts_v2_adapter.py
│   ├── library/
│   │   ├── repository.py
│   │   └── storage_manager.py
│   └── packs/
│       ├── manifest.py
│       ├── exporter.py
│       └── importer.py
├── data/
│   ├── voice_lab.db
│   └── storage/
│       ├── references/
│       ├── previews/
│       └── packs/
└── docs/
```

## 6) Flujo general del programa

1. Crear perfil de voz vacío.
2. Adjuntar referencias.
3. Validar referencias y mostrar advertencias.
4. Generar preview con texto configurable.
5. Ajustar parámetros por defecto.
6. Guardar en librería local.
7. Exportar como `.voicepack`.
8. Importar pack y reindexar librería.

## 7) Dependencias principales

- `TTS` (Coqui)
- `torch` (CPU/GPU)
- `fastapi`, `uvicorn`
- `sqlmodel` o `sqlalchemy`
- `pydantic`
- `python-multipart` (uploads)
- `soundfile` / `librosa`
- `ffmpeg` (binario del sistema)

## 8) Límites reales del MVP con XTTS v2

### Sí es viable en local (MVP)
- Clonado **ligero** de voz por referencia (voice imitation aproximada).
- Previews rápidos con 1–3 referencias limpias.
- Gestión de librería local + metadatos.
- Export/import de packs reutilizables.

### Experimental / calidad variable
- “Clonado exacto” de identidad vocal (no garantizado).
- Robustez con audios ruidosos o muy cortos.
- Consistencia total entre frases largas.

### Requisitos de recursos
- **GPU recomendada** para flujo fluido (NVIDIA CUDA).
- En **CPU** funciona, pero puede ser lento para iteración diaria.
- Más VRAM = mejor experiencia para generación repetida.

### Potenciales cuellos de botella
- Tiempo de inferencia sin GPU.
- Gestión de dependencias de `torch`/CUDA.
- Calidad de dataset de referencia (si audio pobre, resultado pobre).

## 9) Qué dejar para fases posteriores

### Fase 2
- Mejor búsqueda/filtros, UX de biblioteca, edición rica de metadatos.
- Historial de previews y comparación A/B.

### Fase 3
- Capa de estilización (p. ej. OpenVoice).
- Pipeline no destructivo: `base_voice -> style_profile -> rendered_preview`.

### Fase 4
- Entrenamiento/fine-tuning serio y exportación robusta (evaluar Piper u otra ruta).
- Validaciones de licencias, dataset curation, evaluación objetiva de calidad.

## 10) Recomendación concreta para primera versión funcional (Fase 1)

Entrega mínima recomendada en 2–3 iteraciones cortas:

1. **Iteración A**
   - CRUD básico de voces
   - carga de referencias
   - persistencia en SQLite

2. **Iteración B**
   - generación de preview con XTTS v2
   - reproducción de preview
   - guardado de parámetros por defecto

3. **Iteración C**
   - export/import `.voicepack`
   - validación de manifest
   - manejo de errores y logs

Criterio de “MVP listo”:
- Puedes crear una voz, generar preview, guardarla, exportarla, reimportarla y volver a sintetizar sin tocar tu TTS principal.
