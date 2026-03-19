from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer
import uvicorn

from err.core.context import ErrContext, ErrNotFoundError
from err.core.theme import ThemeNotFoundError, ThemeResolver
from err.models.run import RunRecord
from err.storage.run_store import RunStore
from err.storage.theme_store import ThemeStore

app = typer.Typer(help="ERR — Embedded Research Runtime")
run_app = typer.Typer(help="実行記録の管理")
app.add_typer(run_app, name="run")


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


@run_app.command("log")
def run_log(
    theme: str = typer.Argument(..., help="テーマスラッグ（例: turbulence-study）"),
    description: str = typer.Option(..., "--desc", "-d", help="実行の説明"),
    param: list[str] = typer.Option([], "--param", "-p", help="パラメータ key=value（複数可）"),
    status: str = typer.Option("completed", "--status", "-s", help="completed | failed | partial"),
    notes: str = typer.Option("", "--notes", "-n", help="メモ"),
):
    """実行記録をテーマに登録する。"""
    ctx = _require_context()
    try:
        theme_info = ThemeResolver.find_by_slug(ctx.themes_dir(), theme)
    except ThemeNotFoundError:
        typer.echo(f"テーマが見つかりません: {theme}", err=True)
        raise typer.Exit(code=1)

    params: dict = {}
    for p in param:
        if "=" not in p:
            typer.echo(f"パラメータの形式が不正です（key=value 形式で指定）: {p}", err=True)
            raise typer.Exit(code=1)
        k, v = p.split("=", 1)
        params[k.strip()] = v.strip()

    record = RunRecord(
        id=RunStore.create_id(),
        recorded_at=datetime.now(tz=timezone.utc),
        description=description,
        params=params,
        status=status,
        notes=notes,
    )
    path = RunStore.save(theme_info.path, record)
    typer.echo(f"実行記録を登録しました: {path}")


@run_app.command("list")
def run_list(
    theme: str = typer.Argument(..., help="テーマスラッグ"),
):
    """テーマの実行記録を一覧表示する。"""
    ctx = _require_context()
    try:
        theme_info = ThemeResolver.find_by_slug(ctx.themes_dir(), theme)
    except ThemeNotFoundError:
        typer.echo(f"テーマが見つかりません: {theme}", err=True)
        raise typer.Exit(code=1)

    records = RunStore.list(theme_info.path)
    if not records:
        typer.echo("実行記録がありません。")
        return
    for r in records:
        dt = r.recorded_at.strftime("%Y-%m-%d %H:%M")
        params_str = ", ".join(f"{k}={v}" for k, v in r.params.items())
        line = f"[{dt}] [{r.status}] {r.description}"
        if params_str:
            line += f"  ({params_str})"
        typer.echo(line)
        if r.notes:
            typer.echo(f"    → {r.notes}")


@app.command("serve")
def serve(
    host: str = typer.Option("127.0.0.1", help="バインドホスト"),
    port: int = typer.Option(8765, help="ポート番号"),
    dev: bool = typer.Option(False, "--dev", help="開発モード（ファイル変更時に自動リロード）"),
):
    """Web UI を起動する (localhost:8765)。"""
    ctx = _require_context()
    themes_dir = ctx.themes_dir()

    typer.echo(f"ERR Web UI を起動中: http://{host}:{port}")
    typer.echo(f"テーマディレクトリ: {themes_dir}")
    if dev:
        typer.echo("開発モード: ファイル変更時にブラウザが自動リロードされます")

    if dev:
        import os
        os.environ["ERR_THEMES_DIR"] = str(themes_dir)
        uvicorn.run(
            "err.web._dev:create_app",
            factory=True,
            host=host,
            port=port,
            reload=True,
            reload_dirs=["src/err"],
        )
    else:
        from err.web.app import create_app
        web_app = create_app(themes_dir)
        uvicorn.run(web_app, host=host, port=port)
