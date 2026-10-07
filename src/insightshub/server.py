"""ASGI entry point: a FastAPI app with the NiceGUI frontend mounted on it."""

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from nicegui import app as nicegui_app
from nicegui import ui
from insightshub.config import settings
from insightshub import pages


logging.basicConfig(level=logging.INFO)
logging.getLogger("nicegui").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title=settings.app_name)


@app.get("/health", include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}


nicegui_app.add_static_files("/static", STATIC_DIR)

#ui.run(fastapi_app=app, title='Dev test server')
ui.run_with(
    app,
    title=settings.app_name,
    storage_secret=settings.storage_secret,
    show_welcome_message=False,
)
