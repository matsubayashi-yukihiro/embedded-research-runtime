from pathlib import Path

from err.models.theme import ThemeInfo


class ThemeNotFoundError(Exception):
    """Raised when a theme with the given slug cannot be found."""


class ThemeResolver:
    @staticmethod
    def find_all(themes_dir: Path) -> list[ThemeInfo]:
        """Recursively discover all themes under themes_dir.

        A theme is a directory that contains project.md.
        Subthemes live under <theme>/themes/<subtheme>/.
        """
        results: list[ThemeInfo] = []
        ThemeResolver._walk(themes_dir, parent_slug=None, results=results)
        return results

    @staticmethod
    def _walk(
        directory: Path,
        parent_slug: str | None,
        results: list[ThemeInfo],
    ) -> None:
        if not directory.is_dir():
            return
        for entry in sorted(directory.iterdir()):
            if not entry.is_dir():
                continue
            if entry.name == "themes":
                # This is a sub-themes container — handled by parent iteration
                continue
            project_md = entry / "project.md"
            if project_md.exists():
                theme = ThemeInfo(slug=entry.name, path=entry, parent_slug=parent_slug)
                results.append(theme)
                # Recurse into nested themes/
                sub_themes_dir = entry / "themes"
                ThemeResolver._walk(sub_themes_dir, parent_slug=theme.full_slug, results=results)

    @staticmethod
    def find_by_slug(themes_dir: Path, slug: str) -> ThemeInfo:
        """Resolve a slash-separated slug to a ThemeInfo.

        Examples:
          'turbulence-study'               → themes/turbulence-study/
          'turbulence-study/low-reynolds'  → themes/turbulence-study/themes/low-reynolds/
        """
        parts = slug.strip("/").split("/")
        current_dir = themes_dir
        parent_slug: str | None = None

        for i, part in enumerate(parts):
            candidate = current_dir / part
            if not candidate.is_dir() or not (candidate / "project.md").exists():
                raise ThemeNotFoundError(f"Theme not found: {slug!r}")
            if i < len(parts) - 1:
                parent_slug = "/".join(parts[: i + 1])
                current_dir = candidate / "themes"
            else:
                return ThemeInfo(slug=part, path=candidate, parent_slug=parent_slug)

        raise ThemeNotFoundError(f"Theme not found: {slug!r}")

    @staticmethod
    def build_tree(themes: list[ThemeInfo]) -> list[ThemeInfo]:
        """Build a nested tree from a flat list.

        Returns only root-level themes; children are attached recursively.
        """
        by_full_slug: dict[str, ThemeInfo] = {t.full_slug: t for t in themes}
        roots: list[ThemeInfo] = []

        for theme in themes:
            if theme.parent_slug is None:
                roots.append(theme)
            else:
                parent = by_full_slug.get(theme.parent_slug)
                if parent is not None:
                    parent.children.append(theme)

        return roots
