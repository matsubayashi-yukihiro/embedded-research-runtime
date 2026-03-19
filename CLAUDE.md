# CLAUDE.md — ERR 操作ガイド（AI 向け）

ERR（Embedded Research Runtime）は、研究企画文書と実行記録を接続する軽量研究運用ツールです。
このファイルは、coding AI が ERR リポジトリを操作する際の参照仕様書です。

---

## ERR の基本思想

- **研究判断は人間が担う。AI は文書整理・登録・変換を担う。**
- `project.md` はテーマの「生きた上位インデックス」であり、完成物ではなく現在の研究状態を表す。
- 研究テーマはネスト可能。企画書単位がルートテーマ、そこから研究課題・サブテーマが派生する。

---

## セットアップ

```bash
# ERR リポジトリで依存インストール
uv sync

# 研究リポジトリで初期化（.err/themes/ を作成）
cd <研究リポジトリ>
uv run --project <ERR リポジトリパス> err init

# ERR を uv tool としてインストール済みの場合
err init
```

---

## ディレクトリ構造（研究リポジトリ側）

```
<研究リポジトリ>/
  .err/
    themes/
      <theme-slug>/
        project.md          # テーマの上位インデックス
        runs/               # 実行記録 (Phase 2)
          <timestamp>.yaml
        themes/             # サブテーマ
          <sub-slug>/
            project.md
```

---

## CLI コマンド

```bash
err init                        # .err/themes/ を初期化
err init <slug>                 # ルートテーマを作成
err init <parent>/<child>       # サブテーマを作成
err list                        # テーマ一覧をツリー表示
err serve                       # Web UI を起動 (localhost:8765)
err serve --dev                 # 開発モード（ファイル変更で自動リロード）
err run log <slug> \
  --desc "説明" \
  --param key=value \           # 複数可
  --status completed \          # completed | failed | partial
  --notes "メモ"                # 実行記録を登録
err run list <slug>             # 実行記録一覧
```

---

## project.md のフォーマット

### ルートテーマ

```markdown
---
title: テーマタイトル
status: active
---

元資料の Markdown 本文をそのままコピー。

> 元資料: <ファイルパス>
```

| フィールド | 役割 |
|-----------|------|
| `title` | 人間が読むテーマ名 |
| `status` | `active` / `paused` / `closed` |
| body | 元資料の本文をそのままコピー。末尾に `> 元資料: <パス>` を追記する |

### サブテーマ

サブテーマは、ルートテーマから派生する具体的な研究計画・検証項目・実装タスク単位。デフォルトフォーマット：

```markdown
---
title: 何をするか（1行）
status: active
---

## 目的・背景

なぜこれをやるか。ルートテーマのどの問いに対応するか。

## 条件・パラメータ

- パラメータ名: 値（変動させる場合は範囲）
- 固定条件: ...

## 実行計画

- [ ] ステップ1
- [ ] ステップ2

## メモ
```

フォーマットは自由に省略・拡張してよい。共通して必要なのは `title` と `status` のみ。

---

## 既存の研究企画書を ERR に登録する手順

研究企画書（設計書・構想メモ・仕様書など）を ERR テーマとして登録する場合の手順です。

### 1. ルートテーマを作成

企画書 1 本 = ルートテーマ 1 つ。

```bash
err init <slug>
```

slug は企画書の主題を表す英語ケバブケース（例: `event-accumulation-model`）。

### 2. project.md に元資料をコピーする

以下のシェルコマンドで frontmatter・本文・引用行を一括生成する：

```bash
# <タイトル> = 元資料の先頭 H1（# ...）をそのまま使う
# <slug> = ステップ1で指定したスラッグ
# <元資料パス> = 登録する Markdown ファイルのパス

{
  printf -- "---\ntitle: <タイトル>\nstatus: active\n---\n\n"
  cat <元資料パス>
  printf "\n\n> 元資料: <元資料パス>\n"
} > .err/themes/<slug>/project.md
```

- 本文は AI が読んで書き直さない。シェルで機械的にコピーする
- `err init` が生成した雛形は上書きされる（余分なフィールドは除去される）
- 元資料の内容を解釈・整形・要約する必要はない

### 3. 確認

```bash
err list
```

---

## テーマ階層の設計指針

```
ルートテーマ       企画書・研究プログラム単位
  └─ サブテーマ    具体的な検証・実装・パラメータ調査の単位
```

- サブテーマは独立して実行できる粒度に設定する
- サブテーマ名は「何を検証するか」が一目でわかる名前にする
- **サブテーマは企画書登録時には作らない。** ユーザーが研究を進める中で必要に応じて切る

---

## 実行記録の登録指針

実験・シミュレーション・解析を実行したら `err run log` で記録する。

- `--desc`: 何をやったかを 1 文で（例: "Reynolds数1000、グリッド128で基本ケース実行"）
- `--param`: 変えたパラメータのみ記録（固定値は書かない）
- `--notes`: 結果の第一印象・気になった挙動・次への接続（価値判断ではなく観察として）

---

## Web UI

```bash
err serve       # http://localhost:8765
err serve --dev # ファイル変更でブラウザ自動リロード
```

テーマ一覧 → テーマ詳細（frontmatter + Markdown 本文 + 実行記録）→ 編集フォーム
