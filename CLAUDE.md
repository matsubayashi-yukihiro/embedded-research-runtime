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

```markdown
---
title: テーマタイトル
status: active
current_question: "現在の中心的な問い（1文）"
open_items:
  - 未解決の問い・保留事項（具体的に）
  - （複数可）
comparing_themes:
  - 比較対象のテーマスラッグや概念名
next_runs:
  - description: 次に実行すべき具体的ステップ
    params: {key: value}        # 省略可
---

Markdown 本文（背景・目的・現在の考察など）
```

### フィールドの意図

| フィールド | 役割 |
|-----------|------|
| `title` | 人間が読むテーマ名 |
| `status` | `active` / `paused` / `closed` |
| `current_question` | 今まさに問っていること。1文に絞る |
| `open_items` | 未解決・保留中の具体的な問いや課題 |
| `comparing_themes` | 比較中の他テーマや対立仮説 |
| `next_runs` | 次にやる実行・実験・解析のリスト |
| body | 背景・目的・現在の考察。自由 Markdown |

---

## 既存の研究企画書を ERR に登録する手順

研究企画書（設計書・構想メモ）を ERR テーマとして登録する場合の標準手順です。

### 1. 各企画書をルートテーマとして登録

企画書 1 本 = ルートテーマ 1 つ。

```bash
err init <slug>
```

slug は企画書の主題を表す英語ケバブケース（例: `event-accumulation-model`）。

### 2. project.md を企画書の内容で書き直す

`err init` が生成する雛形を以下の対応で上書きする：

| project.md フィールド | 企画書の対応箇所 |
|---------------------|----------------|
| `title` | 企画書のタイトル（H1） |
| `current_question` | 研究の中心的な問い。「研究上の問い」「中心仮説」「研究目的」などのセクションから **最重要の 1 文** に絞る |
| `open_items` | 未解決課題・検証すべき問い。「研究上の問い」「反証可能な予測」「保留事項」などから箇条書きで抽出 |
| `next_runs` | 実装・検証の次ステップ。「実装段階」「stage」「フェーズ」などから抽出 |
| body | **研究目的と中心仮説のみを 200〜400 字で要約。** 全文転記しない。末尾に `> 元資料: <ファイルパス>` を記載 |

### 3. サブテーマを作成する

企画書内に「stage」「フェーズ」「研究課題」として明示されている項目をサブテーマとして登録する。

```bash
err init <parent-slug>/<sub-slug>
```

サブテーマの project.md には、企画書の該当箇所から抽出した内容を書く。
サブテーマの `current_question` は親テーマより具体的・狭いスコープにする。

### 4. 確認

```bash
err list
```

---

## テーマ階層の設計指針

```
ルートテーマ       企画書・研究プログラム単位
  └─ サブテーマ    個別研究課題・実装フェーズ・検証項目単位
       └─ ...      さらに細かい検討項目（必要に応じて）
```

- ルートテーマの `current_question` は研究プログラム全体を貫く問い
- サブテーマは独立して作業・実行できる粒度に設定する
- サブテーマ名は「何を検証するか」が一目でわかる名前にする

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
