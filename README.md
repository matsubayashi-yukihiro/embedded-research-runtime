# ERR — Embedded Research Runtime

研究企画文書と実行記録を接続する軽量研究運用ツール。

> 研究判断は人間が担う。ERR は、文書・実行・比較結果を切らさず接続するための基盤として動く。

---

## 概要

計算・シミュレーション・解析系の研究では、試行錯誤の断片（企画文書、メモ、実行条件、結果）が散逸しやすい。ERR は研究リポジトリの近傍に `.err/` ディレクトリを置くだけで、これらを接続し続けるための軽量基盤を提供する。

**ERR がすること**
- 研究テーマ（`project.md`）の管理と階層表示
- 実行記録の登録と閲覧
- Web UI によるテーマ状態の確認・編集

**ERR がしないこと**
- 研究テーマの自律的な立案
- 科学的妥当性の保証
- シミュレーション等の実行そのもの

---

## インストール

```bash
git clone <ERR_REPO_URL>
cd embedded-research-runtime
uv sync
```

実行方法：

```bash
# uv run 経由（どのディレクトリからでも動作）
uv run err --help

# または uv tool としてグローバルインストール
uv tool install .
err --help
```

---

## クイックスタート

```bash
# 研究リポジトリで初期化
cd ~/my-research-repo
err init

# テーマを作成
err init turbulence-study

# サブテーマを作成
err init turbulence-study/mesh-sensitivity

# テーマ一覧を表示
err list

# Web UI を起動
err serve        # http://localhost:8765
err serve --dev  # ファイル変更で自動リロード
```

---

## ディレクトリ構造

ERR は研究リポジトリに `.err/` ディレクトリを追加するだけ。既存ファイルは変更しない。

```
my-research-repo/
  .err/
    themes/
      turbulence-study/
        project.md          # テーマの上位インデックス
        runs/               # 実行記録
          20250315_143022.yaml
        themes/             # サブテーマ
          mesh-sensitivity/
            project.md
  src/
  ...
```

---

## project.md のフォーマット

### ルートテーマ

```markdown
---
title: テーマタイトル
status: active
---

研究の背景・目的・現在の考察など（自由 Markdown）。
```

### サブテーマ

```markdown
---
title: 何をするか（1行）
status: active
---

## 目的・背景

なぜこれをやるか。ルートテーマのどの問いに対応するか。

## 条件・パラメータ

- パラメータ名: 値

## 実行計画

- [ ] ステップ1
- [ ] ステップ2
```

`status` は `active` / `paused` / `closed` のいずれか。

---

## 実行記録

```bash
err run log turbulence-study \
  --desc "Re=5000、グリッド128でベースライン実行" \
  --param Re=5000 \
  --param mesh=128 \
  --status completed \
  --notes "収束は良好。次はRe=8000を試す"

# 実行記録の一覧
err run list turbulence-study
```

---

## CLI リファレンス

| コマンド | 説明 |
|---------|------|
| `err init` | `.err/themes/` を初期化 |
| `err init <slug>` | ルートテーマを作成 |
| `err init <parent>/<child>` | サブテーマを作成 |
| `err list` | テーマ一覧をツリー表示 |
| `err serve` | Web UI を起動（localhost:8765） |
| `err serve --dev` | 開発モード（自動リロード） |
| `err run log <slug> [options]` | 実行記録を登録 |
| `err run list <slug>` | 実行記録の一覧 |

---

## 依存

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

主な依存ライブラリ: FastAPI, Jinja2, Typer, Pydantic, markdown-it-py, watchfiles

---

## 基本思想

```
 project.md を読む
       ↓
 実験・シミュレーションを実行（ERR の外で）
       ↓
 err run log で記録
       ↓
 結果を見て project.md を更新
       ↓
 最初に戻る
```

研究状態の記録と可視化に徹することで、「今どこにいて、次にどこへ向かうか」を見失わない基盤として機能する。
