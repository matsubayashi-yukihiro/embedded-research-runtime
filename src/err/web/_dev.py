"""Dev-mode entry point for uvicorn factory reload.

uvicorn calls create_app() as a factory when --reload is active.
ERR_THEMES_DIR env var is set by the CLI before handing off to uvicorn.
"""
import os
from pathlib import Path

from err.web.app import create_app as _create_app


def create_app():
    themes_dir = Path(os.environ["ERR_THEMES_DIR"])
    return _create_app(themes_dir, dev=True)
