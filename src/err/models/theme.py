from pathlib import Path

from pydantic import BaseModel


class ThemeInfo(BaseModel):
    slug: str
    path: Path
    parent_slug: str | None = None
    children: list["ThemeInfo"] = []

    model_config = {"arbitrary_types_allowed": True}

    @property
    def full_slug(self) -> str:
        """Return slash-separated full path, e.g. 'turbulence-study/low-reynolds'."""
        if self.parent_slug:
            return f"{self.parent_slug}/{self.slug}"
        return self.slug

    @property
    def run_files(self) -> list[str]:
        """Return sorted YAML filenames from runs/ dir."""
        runs_dir = self.path / "runs"
        if not runs_dir.is_dir():
            return []
        return sorted(f.name for f in runs_dir.glob("*.yaml"))
