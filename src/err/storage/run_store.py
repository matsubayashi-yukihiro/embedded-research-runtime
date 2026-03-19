from datetime import datetime, timezone
from pathlib import Path

import yaml

from err.models.run import RunRecord


class RunStore:
    @staticmethod
    def runs_dir(theme_path: Path) -> Path:
        return theme_path / "runs"

    @staticmethod
    def create_id() -> str:
        return datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%S")

    @staticmethod
    def save(theme_path: Path, record: RunRecord) -> Path:
        runs_dir = RunStore.runs_dir(theme_path)
        runs_dir.mkdir(exist_ok=True)
        path = runs_dir / f"{record.id}.yaml"
        data = record.model_dump()
        data["recorded_at"] = data["recorded_at"].isoformat()
        path.write_text(yaml.dump(data, allow_unicode=True, sort_keys=False))
        return path

    @staticmethod
    def list(theme_path: Path) -> list[RunRecord]:
        runs_dir = RunStore.runs_dir(theme_path)
        if not runs_dir.exists():
            return []
        records = []
        for f in sorted(runs_dir.glob("*.yaml"), reverse=True):
            data = yaml.safe_load(f.read_text())
            if data:
                records.append(RunRecord(**data))
        return records
