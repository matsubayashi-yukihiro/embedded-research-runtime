from pathlib import Path

from err.core.theme import ThemeResolver
from err.models.project import PROJECT_MD_TEMPLATE
from err.models.theme import ThemeInfo


class ThemeStore:
    @staticmethod
    def create(themes_dir: Path, slug: str) -> ThemeInfo:
        """Create a new theme directory with an initial project.md.

        slug may be slash-separated for nested themes,
        e.g. 'turbulence-study/low-reynolds'.
        """
        parts = slug.strip("/").split("/")

        if len(parts) == 1:
            theme_dir = themes_dir / parts[0]
            parent_slug = None
        else:
            # Navigate to parent's themes/ directory
            current = themes_dir
            for part in parts[:-1]:
                current = current / part / "themes"
            theme_dir = current / parts[-1]
            parent_slug = "/".join(parts[:-1])

        if theme_dir.exists():
            raise FileExistsError(f"Theme already exists: {theme_dir}")

        theme_dir.mkdir(parents=True)
        (theme_dir / "project.md").write_text(PROJECT_MD_TEMPLATE, encoding="utf-8")

        return ThemeInfo(slug=parts[-1], path=theme_dir, parent_slug=parent_slug)

    @staticmethod
    def list(themes_dir: Path) -> list[ThemeInfo]:
        return ThemeResolver.find_all(themes_dir)
