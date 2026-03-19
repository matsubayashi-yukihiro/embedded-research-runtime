import asyncio
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from err.web.routes import themes as themes_router

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_STATIC_DIR = Path(__file__).parent / "static"


async def _watch_files(queues: set[asyncio.Queue]) -> None:
    """テンプレート・静的ファイルの変更を検知して全SSEクライアントに通知する。"""
    from watchfiles import awatch
    async for _ in awatch(_TEMPLATES_DIR, _STATIC_DIR):
        for q in list(queues):
            await q.put("reload")


def create_app(themes_dir: Path, dev: bool = False) -> FastAPI:
    app = FastAPI(title="ERR — Embedded Research Runtime")

    app.state.themes_dir = themes_dir
    app.state.dev_mode = dev

    templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))
    templates.env.globals["dev_mode"] = dev
    app.state.templates = templates

    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")
    app.include_router(themes_router.router)

    if dev:
        _reload_queues: set[asyncio.Queue] = set()

        @app.on_event("startup")
        async def _start_watcher():
            asyncio.create_task(_watch_files(_reload_queues))

        @app.get("/dev/livereload")
        async def livereload():
            q: asyncio.Queue = asyncio.Queue()
            _reload_queues.add(q)

            async def event_stream():
                try:
                    while True:
                        try:
                            await asyncio.wait_for(q.get(), timeout=25)
                            yield "event: reload\ndata: {}\n\n"
                        except asyncio.TimeoutError:
                            yield ": keepalive\n\n"
                finally:
                    _reload_queues.discard(q)

            return StreamingResponse(event_stream(), media_type="text/event-stream")

    return app
