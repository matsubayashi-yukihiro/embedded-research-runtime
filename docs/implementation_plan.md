# ERR 実装計画書

> **文書種別**: 実装計画書
> **対象スコープ**: フェーズ 1 — テーマ管理 + project.md 管理 + Web UI
> **前提文書**: [err_concept.md](./err_concept.md)

---

## 設計原則

- **研究リポジトリへの侵食最小化**: 研究リポジトリ内に置くのは `.err/` ディレクトリのみ。ERR のコード・設定ファイルは一切置かない
- **ERR アプリはグローバルツール**: `uv tool install` または `pip install` で一度入れ、任意の研究リポジトリで使い回す
- **機能スコープを絞る**: フェーズ 1 はテーマ管理と project.md の表示・編集のみ。実行記録・比較系列は後続フェーズ

---

## 研究リポジトリ側のフットプリント

```
~/my-sim-repo/           ← 既存の研究リポジトリ（変更なし）
  .err/
    themes/
      turbulence-study/
        project.md       ← テーマごとの project.md（フェーズ1）
        runs/            ← フェーズ2 以降
        series/          ← フェーズ2 以降
        themes/
          low-reynolds/
            project.md   ← サブテーマの project.md
      heat-transfer/
        project.md
  src/
  ...
```

研究リポジトリのルートや既存ファイルには一切手を加えない。
`.err/` を `.gitignore` するか Git 管理するかは研究者の判断に委ねる。
テーマの親子関係はディレクトリ構造で暗黙的に表現する。

---

## ERR アプリのディレクトリ構成

```
embedded-research-runtime/
  src/
    err/
      __init__.py
      cli.py                   # typer CLI エントリポイント
      core/
        __init__.py
        context.py             # .err/ ディレクトリの検出・パス解決
        theme.py               # テーマの探索・階層管理
      models/
        __init__.py
        project.py             # ProjectDoc Pydantic モデル
        theme.py               # ThemeInfo モデル
      storage/
        __init__.py
        project_store.py       # project.md 読み書き
        theme_store.py         # テーマ一覧の探索・管理
      web/
        __init__.py
        app.py                 # FastAPI アプリ定義
        routes/
          __init__.py
          themes.py            # テーマ一覧・個別テーマルート
        templates/
          base.html
          theme_list.html      # テーマ一覧（ツリー表示）
          project_view.html
          project_edit.html
        static/
          style.css
  pyproject.toml
  main.py                      # 既存（変更なし）
```

---

## 依存パッケージ

```toml
# pyproject.toml
[project]
dependencies = [
    "fastapi>=0.115",
    "uvicorn>=0.30",
    "jinja2>=3.1",
    "typer>=0.12",
    "pydantic>=2.7",
    "python-frontmatter>=1.1",
    "markdown-it-py>=3.0",
]

[project.scripts]
err = "err.cli:app"
```

---

## データモデル

### ProjectDoc — `src/err/models/project.py`

```python
class ProjectFrontmatter(BaseModel):
    title: str
    status: str = "active"       # active | paused | closed
    current_question: str = ""
    open_items: list[str] = []
    comparing_themes: list[str] = []  # 比較中テーマのリスト
    next_runs: list[dict] = []   # [{description: str, params: {k: v}}]

class ProjectDoc(BaseModel):
    frontmatter: ProjectFrontmatter
    body: str                    # Markdown 本文（frontmatter 以外）
    path: Path                   # ファイルパス（保存用）
    theme_slug: str              # テーマのスラッグ（例: "turbulence-study"）
    parent_slug: str | None = None  # 親テーマのスラッグ（ルートテーマは None）
```

### ThemeInfo — `src/err/models/theme.py`

```python
class ThemeInfo(BaseModel):
    slug: str                    # テーマのスラッグ（ディレクトリ名）
    path: Path                   # テーマディレクトリの絶対パス
    parent_slug: str | None = None
    children: list["ThemeInfo"] = []

    @property
    def full_slug(self) -> str:
        """親テーマを含むフルパス（例: "turbulence-study/low-reynolds"）"""
        if self.parent_slug:
            return f"{self.parent_slug}/{self.slug}"
        return self.slug
```

### project.md テンプレート（`err init <theme-name>` が生成する初期ファイル）

```markdown
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
```

---

## CLI コマンド — `src/err/cli.py`

| コマンド | 動作 |
|---------|------|
| `err init` | カレントディレクトリに `.err/themes/` を初期化。既存の場合は警告して終了 |
| `err init <theme-name>` | `.err/themes/<theme-name>/project.md` を生成 |
| `err init <parent>/<child>` | 親テーマ配下にサブテーマを生成 |
| `err serve` | カレントディレクトリから `.err/` を検出し、`localhost:8765` で Web UI を起動（テーマ一覧を表示） |
| `err list` | テーマ一覧をツリー形式で表示 |

`.err/` が見つからない場合は `err init` を促すエラーメッセージを表示。

---

## Web UI ルート — `src/err/web/routes/themes.py`

| パス | メソッド | 説明 |
|-----|---------|------|
| `/` | GET | テーマ一覧をツリー表示 |
| `/themes/<slug>` | GET | 指定テーマの project.md を HTML レンダリングして表示 |
| `/themes/<slug>/edit` | GET | frontmatter フィールド + Markdown 本文を編集フォームで表示 |
| `/themes/<slug>/edit` | POST | フォームの内容を保存 → `/themes/<slug>` にリダイレクト |

※ `<slug>` はネストしたテーマの場合 `parent/child` のようにスラッシュ区切りのパスとなる（例: `/themes/turbulence-study/low-reynolds`）。

### テーマ一覧レイアウト（`/`）

- テーマをツリー構造で表示（ネスト可）
- 各テーマのタイトル・ステータス・現在の問いを概要表示
- テーマ名クリックで個別ページへ遷移

### テーマ表示レイアウト（`/themes/<slug>`）

- パンくずリスト: ホーム > 親テーマ > 現テーマ
- ヘッダー: タイトル・ステータス・「編集」ボタン
- サイドバー: frontmatter フィールド（現在の問い・保留事項・比較中テーマ・次の実行候補）
- メイン: Markdown 本文を HTML レンダリング
- サブテーマがある場合はサブテーマ一覧を表示

### テーマ編集レイアウト（`/themes/<slug>/edit`）

- frontmatter フィールド: 各フィールドを個別の input/textarea で編集
- Markdown 本文: textarea で直接編集
- 「保存」ボタン → POST → `/themes/<slug>` へリダイレクト

---

## 各モジュールの責務

### `core/context.py` — ErrContext

```
ErrContext.find(start: Path) -> ErrContext
  カレントディレクトリから上位をたどって .err/ を検出。
  見つからなければ ErrNotFoundError を raise。

ErrContext.themes_dir() -> Path      # .err/themes/
```

### `core/theme.py` — ThemeResolver

```
ThemeResolver.find_all(themes_dir: Path) -> list[ThemeInfo]
  themes/ 配下を再帰的に探索し、project.md を持つディレクトリをテーマとして返す。
  ネストされた themes/ サブディレクトリも探索する。

ThemeResolver.find_by_slug(themes_dir: Path, slug: str) -> ThemeInfo
  スラッシュ区切りの slug（例: "turbulence-study/low-reynolds"）からテーマを解決。
  見つからなければ ThemeNotFoundError を raise。

ThemeResolver.build_tree(themes: list[ThemeInfo]) -> list[ThemeInfo]
  フラットなテーマリストをツリー構造に組み立てる。
```

### `storage/project_store.py` — ProjectStore

```
ProjectStore.load(path: Path) -> ProjectDoc
  python-frontmatter で frontmatter + body をパース。
  frontmatter を ProjectFrontmatter に validate。

ProjectStore.save(doc: ProjectDoc) -> None
  ProjectDoc を YAML frontmatter + Markdown body に直列化して書き込み。
```

### `storage/theme_store.py` — ThemeStore

```
ThemeStore.create(themes_dir: Path, slug: str) -> ThemeInfo
  テーマディレクトリと初期 project.md を生成。
  slug がスラッシュ区切りの場合、親テーマの themes/ 配下に作成。

ThemeStore.list(themes_dir: Path) -> list[ThemeInfo]
  ThemeResolver.find_all() のラッパー。
```

---

## 実装ステップ

| # | タスク | 対象ファイル |
|---|-------|------------|
| 1 | pyproject.toml 更新（依存・scripts） | `pyproject.toml` |
| 2 | パッケージ構成作成（`__init__.py` 群） | `src/err/**/__init__.py` |
| 3 | ErrContext 実装 | `src/err/core/context.py` |
| 4 | ThemeInfo モデル実装 | `src/err/models/theme.py` |
| 5 | ProjectDoc モデル実装 | `src/err/models/project.py` |
| 6 | ThemeResolver 実装 | `src/err/core/theme.py` |
| 7 | ThemeStore 実装 | `src/err/storage/theme_store.py` |
| 8 | ProjectStore 実装 | `src/err/storage/project_store.py` |
| 9 | FastAPI アプリ + ルート実装 | `src/err/web/app.py`, `routes/themes.py` |
| 10 | Jinja2 テンプレート作成 | `src/err/web/templates/*.html` |
| 11 | CSS 作成 | `src/err/web/static/style.css` |
| 12 | CLI 実装 | `src/err/cli.py` |
| 13 | uv sync + 動作確認 | — |

---

## 検証手順

```bash
# 1. 依存インストール
cd ~/embedded-research-runtime
uv sync

# 2. テスト用研究ディレクトリで初期化
mkdir -p ~/test-research && cd ~/test-research
err init
# → .err/themes/ が作成されることを確認

# 3. テーマ作成
err init turbulence-study
# → .err/themes/turbulence-study/project.md が生成されることを確認

# 4. サブテーマ作成
err init turbulence-study/low-reynolds
# → .err/themes/turbulence-study/themes/low-reynolds/project.md が生成されることを確認

# 5. テーマ一覧確認
err list
# → ツリー形式でテーマが表示されることを確認

# 6. Web UI 起動
err serve
# → http://localhost:8765 でテーマ一覧が表示されることを確認

# 7. テーマ表示・編集フロー確認
# /themes/turbulence-study で表示 → /themes/turbulence-study/edit で編集 → 保存 → 反映確認

# 8. ファイル確認
cat ~/test-research/.err/themes/turbulence-study/project.md
# → frontmatter + 本文が正しく保存されていることを確認
```

---

## 後続フェーズ（本計画書スコープ外）

| フェーズ | 内容 |
|---------|------|
| フェーズ 2 | `err run log` — 実行記録（テーマごとの `runs/*.yaml`）の登録・一覧表示 |
| フェーズ 3 | 比較系列（テーマごとの `series/*.yaml`）の管理 UI |
| フェーズ 4 | 差し戻し候補の整理 UI（結果 → project.md 更新候補の提示） |
| フェーズ 5 | メモ・リンク管理（テーマごとのメモ保存・実行との紐付け） |
| フェーズ 6 | AI 統合・表現規律の実装（事実・推定・解釈・提案の分離表示） |
