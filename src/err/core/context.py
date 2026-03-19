from pathlib import Path


class ErrNotFoundError(Exception):
    """Raised when .err/ directory cannot be found."""


class ErrContext:
    def __init__(self, err_dir: Path) -> None:
        self._err_dir = err_dir

    @classmethod
    def find(cls, start: Path | None = None) -> "ErrContext":
        """Walk up from start (default: cwd) to find .err/ directory."""
        current = (start or Path.cwd()).resolve()
        for directory in [current, *current.parents]:
            candidate = directory / ".err"
            if candidate.is_dir():
                return cls(candidate)
        raise ErrNotFoundError(
            "No .err/ directory found. Run 'err init' to initialize."
        )

    def themes_dir(self) -> Path:
        return self._err_dir / "themes"
