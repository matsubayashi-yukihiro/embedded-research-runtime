from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from err.core.theme import ThemeNotFoundError, ThemeResolver
from err.models.project import ProjectFrontmatter
from err.storage.project_store import ProjectStore
from err.storage.run_store import RunStore
from err.storage.theme_store import ThemeStore

router = APIRouter()


def _get_templates(request: Request) -> Jinja2Templates:
    return request.app.state.templates


def _themes_dir(request: Request) -> Path:
    return request.app.state.themes_dir


@router.get("/", response_class=HTMLResponse)
async def theme_list(request: Request):
    themes_dir = _themes_dir(request)
    flat = ThemeStore.list(themes_dir)
    tree = ThemeResolver.build_tree(flat)
    templates = _get_templates(request)
    return templates.TemplateResponse(
        "theme_list.html", {"request": request, "themes": tree}
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
    templates = _get_templates(request)
    return templates.TemplateResponse(
        "project_edit.html",
        {"request": request, "theme": theme, "doc": doc},
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

    # Sub-themes
    flat = ThemeStore.list(themes_dir)
    children = [t for t in flat if t.parent_slug == theme.full_slug]

    # Run records
    runs = RunStore.list(theme.path)

    # Render Markdown body
    from markdown_it import MarkdownIt
    md = MarkdownIt()
    body_html = md.render(doc.body)

    # Breadcrumbs: list of (label, url)
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
