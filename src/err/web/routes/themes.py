from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from markdown_it import MarkdownIt
from mdit_py_plugins.dollarmath import dollarmath_plugin

from err.core.theme import ThemeNotFoundError, ThemeResolver
from err.models.project import ProjectFrontmatter
from err.storage.project_store import ProjectStore
from err.storage.run_store import RunStore
from err.storage.theme_store import ThemeStore

router = APIRouter()

_md = MarkdownIt()
dollarmath_plugin(_md, allow_labels=True, allow_space=True, allow_digits=False)


def _get_templates(request: Request) -> Jinja2Templates:
    return request.app.state.templates


def _themes_dir(request: Request) -> Path:
    return request.app.state.themes_dir


def _get_themes_cached(request: Request) -> tuple[list, list]:
    """Return (sidebar_tree, flat_list). Re-walks only if themes_dir mtime changed."""
    themes_dir = _themes_dir(request)
    try:
        mtime = themes_dir.stat().st_mtime
    except FileNotFoundError:
        mtime = 0.0

    cache = request.app.state.sidebar_cache
    if cache is not None and cache[0] == mtime:
        return cache[1], cache[2]

    flat = ThemeStore.list(themes_dir)
    tree = ThemeResolver.build_tree(flat)
    request.app.state.sidebar_cache = (mtime, tree, flat)
    return tree, flat


def _invalidate_sidebar_cache(request: Request) -> None:
    request.app.state.sidebar_cache = None


def _render_body(request: Request, theme_path: Path, body: str) -> str:
    """Render Markdown body HTML, caching by project.md mtime."""
    project_md_path = theme_path / "project.md"
    try:
        mtime = project_md_path.stat().st_mtime
    except FileNotFoundError:
        return _md.render(body)

    cache_key = (str(project_md_path), mtime)
    render_cache = request.app.state.render_cache

    if cache_key not in render_cache:
        stale = [k for k in render_cache if k[0] == str(project_md_path)]
        for k in stale:
            del render_cache[k]
        render_cache[cache_key] = _md.render(body)

    return render_cache[cache_key]


@router.get("/", response_class=HTMLResponse)
async def theme_list(request: Request):
    sidebar_themes, _ = _get_themes_cached(request)
    templates = _get_templates(request)
    return templates.TemplateResponse(
        "theme_list.html",
        {"request": request, "sidebar_themes": sidebar_themes},
    )


@router.get("/themes/{slug:path}/edit", response_class=HTMLResponse)
async def theme_edit_form(request: Request, slug: str):
    themes_dir = _themes_dir(request)
    try:
        theme = ThemeResolver.find_by_slug(themes_dir, slug)
    except ThemeNotFoundError:
        return HTMLResponse(f"Theme not found: {slug}", status_code=404)

    doc = ProjectStore.load(
        theme.path / "project.md",
        theme_slug=theme.slug,
        parent_slug=theme.parent_slug,
    )
    sidebar_themes, _ = _get_themes_cached(request)
    templates = _get_templates(request)
    return templates.TemplateResponse(
        "project_edit.html",
        {"request": request, "theme": theme, "doc": doc, "sidebar_themes": sidebar_themes},
    )


@router.post("/themes/{slug:path}/edit")
async def theme_edit_save(
    request: Request,
    slug: str,
    title: str = Form(...),
    status: str = Form(...),
    current_question: str = Form(""),
    open_items_raw: str = Form(""),
    comparing_themes_raw: str = Form(""),
    body: str = Form(""),
):
    themes_dir = _themes_dir(request)
    try:
        theme = ThemeResolver.find_by_slug(themes_dir, slug)
    except ThemeNotFoundError:
        return HTMLResponse(f"Theme not found: {slug}", status_code=404)

    doc = ProjectStore.load(
        theme.path / "project.md",
        theme_slug=theme.slug,
        parent_slug=theme.parent_slug,
    )

    open_items = [line.strip() for line in open_items_raw.splitlines() if line.strip()]
    comparing_themes = [
        t.strip() for t in comparing_themes_raw.splitlines() if t.strip()
    ]

    doc.frontmatter = ProjectFrontmatter(
        title=title,
        status=status,
        current_question=current_question,
        open_items=open_items,
        comparing_themes=comparing_themes,
        next_runs=doc.frontmatter.next_runs,
    )
    doc.body = body
    ProjectStore.save(doc)
    _invalidate_sidebar_cache(request)

    return RedirectResponse(url=f"/themes/{slug}", status_code=303)


@router.get("/themes/{slug:path}", response_class=HTMLResponse)
async def theme_view(request: Request, slug: str):
    themes_dir = _themes_dir(request)
    try:
        theme = ThemeResolver.find_by_slug(themes_dir, slug)
    except ThemeNotFoundError:
        return HTMLResponse(f"Theme not found: {slug}", status_code=404)

    doc = ProjectStore.load(
        theme.path / "project.md",
        theme_slug=theme.slug,
        parent_slug=theme.parent_slug,
    )

    sidebar_themes, flat = _get_themes_cached(request)
    children = [t for t in flat if t.parent_slug == theme.full_slug]

    runs = RunStore.list(theme.path)

    body_html = _render_body(request, theme.path, doc.body)

    breadcrumbs = _build_breadcrumbs(slug)

    templates = _get_templates(request)
    return templates.TemplateResponse(
        "project_view.html",
        {
            "request": request,
            "theme": theme,
            "doc": doc,
            "body_html": body_html,
            "children": children,
            "breadcrumbs": breadcrumbs,
            "runs": runs,
            "sidebar_themes": sidebar_themes,
        },
    )


def _build_breadcrumbs(slug: str) -> list[tuple[str, str]]:
    """Return [(label, url), ...] for breadcrumb navigation."""
    crumbs = [("ホーム", "/")]
    parts = slug.split("/")
    for i, part in enumerate(parts):
        partial_slug = "/".join(parts[: i + 1])
        crumbs.append((part, f"/themes/{partial_slug}"))
    return crumbs
