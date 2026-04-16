Voice Lab - Iteración A

Resumen
- Implementación mínima funcional para validar arquitectura, librería local y formato .voicepack.
- No incluye todavía generación real de preview con XTTS (queda preparado mediante adaptador stub).

Qué funciona en Iteración A
- Crear, listar, editar y eliminar voces.
- Guardar metadata en SQLite.
- Agregar/listar/eliminar referencias de audio por voz.
- Validación básica de referencias (extensión permitida + archivo no vacío).
- Exportar una voz como .voicepack con estructura manifest/metadata/references/previews/config.
- Importar .voicepack validando presencia y lectura de manifest.json y metadata.json.
- Reconstruir voz importada en librería local.

Qué queda preparado pero no implementado
- Integración real con Coqui XTTS v2 para synthesize_preview.
- Pipeline de generación y reproducción avanzada de previews.
- Estilización (OpenVoice) y entrenamiento (Piper).

Requisitos
- Python 3.11+

Ejecución
1) Crear entorno virtual:
   python -m venv .venv
   source .venv/bin/activate

2) Instalar dependencias:
   pip install -r requirements.txt

3) Iniciar app:
   uvicorn app.main:app --reload

4) Abrir en navegador:
   http://127.0.0.1:8000

Cómo probar el flujo solicitado
1) Crear voz
- En la pantalla principal, completa el formulario "Crear voz" y envía.

2) Importar referencias
- En el detalle de la voz, usa "Agregar referencias" con uno o varios audios.

3) Editar metadata
- En el detalle, cambia nombre/descripción/tipo/idioma/tags y guarda.

4) Exportar voice pack
- En el detalle de voz, click en "Exportar .voicepack".

5) Importar voice pack
- En la home, usa "Importar .voicepack" y sube el archivo exportado.

Estructura
- app/main.py: rutas web + UI server-rendered
- app/db.py: inicialización y conexión SQLite
- app/services.py: CRUD de voces y referencias + storage local
- app/voicepack.py: export/import de paquetes
- app/xtts_adapter.py: interfaz y stub XTTS (Iteración A)
- app/templates/: interfaz HTML mínima
- data/: SQLite y storage de referencias/previews/packs
