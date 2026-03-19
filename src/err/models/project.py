from pathlib import Path

from pydantic import BaseModel

PROJECT_MD_TEMPLATE = """\
---
title: 研究タイトル（未設定）
status: active
current_question: ""
open_items: []
comparing_themes: []
next_runs: []
---

## 研究目的

## 現在の問い

## 保留事項

## 比較中テーマ

## 次の実行候補
"""


class ProjectFrontmatter(BaseModel):
    title: str = "研究タイトル（未設定）"
    status: str = "active"  # active | paused | closed
    current_question: str = ""
    open_items: list[str] = []
    comparing_themes: list[str] = []
    next_runs: list[dict] = []


class ProjectDoc(BaseModel):
    frontmatter: ProjectFrontmatter
    body: str
    path: Path
    theme_slug: str
    parent_slug: str | None = None

    model_config = {"arbitrary_types_allowed": True}
