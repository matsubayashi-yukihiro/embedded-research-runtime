from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RunRecord(BaseModel):
    id: str                                   # タイムスタンプベース (例: 20240315T143022)
    recorded_at: datetime
    description: str
    params: dict[str, Any] = Field(default_factory=dict)
    status: str = "completed"                 # completed | failed | partial
    notes: str = ""
