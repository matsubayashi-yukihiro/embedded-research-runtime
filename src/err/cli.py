from pathlib import Path
from typing import Optional

import typer
import uvicorn

from err.core.context import ErrContext, ErrNotFoundError
from err.core.theme import ThemeNotFoundError, ThemeResolver
from err.storage.theme_store import ThemeStore

app = typer.Typer(help="ERR — Embedded Research Runtime")


def _require_context() -> ErrContext:
    try:
        return ErrContext.find()
    except ErrNotFoundError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1)


@app.command("init")
def init(
    slug: Optional[str] = typer.Argument(None, help="テーマ名（例: turbulence-study または parent/child）"),
):
    """ERR を初期化するか、新しいテーマを作成する。"""
    if slug is None:
        # Initialize .err/themes/ in current directory
        err_dir = Path.cwd() / ".err"
        themes_dir = err_dir / "themes"
        if themes_dir.exists():
            typer.echo(f".err/themes/ は既に存在します: {themes_dir}", err=True)
            raise typer.Exit(code=1)
        themes_dir.mkdir(parents=True)
        typer.echo(f"初期化しました: {themes_dir}")
    else:
        ctx = _require_context()
        try:
            theme = ThemeStore.create(ctx.themes_dir(), slug)
            typer.echo(f"テーマを作成しました: {theme.path / 'project.md'}")
        except FileExistsError as e:
            typer.echo(str(e), err=True)
            raise typer.Exit(code=1)


@app.command("list")
def list_themes():
    """テーマ一覧をツリー形式で表示する。"""
    ctx = _require_context()
    flat = ThemeStore.list(ctx.themes_dir())
    if not flat:
        typer.echo("テーマがありません。'err init <theme-name>' でテーマを作成してください。")
        return
    tree = ThemeResolver.build_tree(flat)
    _print_tree(tree, indent=0)


def _print_tree(themes, indent: int) -> None:
    for theme in themes:
        prefix = "  " * indent + ("└─ " if indent else "")
        typer.echo(f"{prefix}{theme.slug}")
        if theme.children:
            _print_tree(theme.children, indent + 1)


@app.command("serve")
def serve(
    host: str = typer.Option("127.0.0.1", help="バインドホスト"),
    port: int = typer.Option(8765, help="ポート番号"),
):
    """Web UI を起動する (localhost:8765)。"""
    ctx = _require_context()
    themes_dir = ctx.themes_dir()

    from err.web.app import create_app
    web_app = create_app(themes_dir)

    typer.echo(f"ERR Web UI を起動中: http://{host}:{port}")
    typer.echo(f"テーマディレクトリ: {themes_dir}")
    uvicorn.run(web_app, host=host, port=port)
