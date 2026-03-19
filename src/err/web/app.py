from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from err.web.routes import themes as themes_router

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_STATIC_DIR = Path(__file__).parent / "static"


def create_app(themes_dir: Path) -> FastAPI:
    app = FastAPI(title="ERR — Embedded Research Runtime")

    app.state.themes_dir = themes_dir
    app.state.templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")
    app.include_router(themes_router.router)

    return app
