# ERR 使用シナリオ集

> **文書種別**: 使用イメージ / ユーザー体験設計
> **目的**: ERR が完成した際に、研究者が日常業務でどう使うかを具体的に描く
> **前提文書**: [err_concept.md](./err_concept.md), [implementation_plan.md](./implementation_plan.md)

---

## ERR のインストール

ERR は Python パッケージとして提供される。`uv` を使ってインストールする。

```bash
# リポジトリを取得
git clone <ERR_REPO_URL>
cd embedded-research-runtime

# 仮想環境の作成と依存関係のインストール
uv sync
```

これ以降、`err` コマンドは以下のいずれかで実行できる。

```bash
# 方法 A: uv run 経由（仮想環境の有効化不要、推奨）
uv run err --help

# 方法 B: 仮想環境を有効化してから実行
source .venv/bin/activate
err --help
```

**ポイント**: `uv run err <cmd>` はどのディレクトリからでも動作するが、ERR のデータ（`.err/`）は **実行時のカレントディレクトリ** に作られる。研究リポジトリのルートで実行すること。

---

## 前提となる状況

あなたは流体シミュレーションの研究者で、`~/cfd-platform/` という研究リポジトリを持っている。
このリポジトリはシミュレーション基盤（ソルバー、メッシュ生成、後処理スクリプト等）であり、この基盤の上で複数の研究テーマを並行して進めている。

---

## シナリオ 1: 研究リポジトリに ERR を導入する

新しい研究テーマを始めるにあたり、ERR を導入する。

```bash
cd ~/cfd-platform
err init
# → .err/themes/ ディレクトリが作成される
```

最初の研究テーマ「乱流境界層の遷移メカニズム」を登録する。

```bash
err init turbulence-transition
# → .err/themes/turbulence-transition/project.md が生成される
```

生成された project.md を開き（Web UI でもエディタでも可）、研究の出発点を書く。

```yaml
---
title: 乱流境界層の遷移メカニズム
status: active
current_question: "Re=5000 付近で観測される間欠的な遷移パターンの支配因子は何か"
open_items:
  - 初期擾乱の与え方が結果に与える影響が未検証
  - メッシュ解像度の十分性が未確認
comparing_themes: []
next_runs:
  - description: "Re=5000, 初期擾乱なし（ベースライン）"
    params: {Re: 5000, perturbation: none, mesh: coarse}
  - description: "Re=5000, ランダム擾乱"
    params: {Re: 5000, perturbation: random, mesh: coarse}
---

## 研究目的

乱流境界層の遷移過程における間欠性の発生条件を特定する。
特に、低レイノルズ数領域での遷移パターンが初期条件にどの程度依存するかを明らかにしたい。

## 現在の問い

Re=5000 付近で時折観測される間欠的パターンは、初期擾乱の種類に依存するのか、
それとも流れ場固有の不安定性から必然的に生じるのか。

## 保留事項

- 先行研究 (Smith et al. 2023) では Re=3000〜8000 で異なる遷移形態を報告しているが、
  メッシュ条件が異なるため直接比較が難しい

## 比較中テーマ

（まだ比較実行を始めていないため空欄）

## 次の実行候補

1. ベースライン実行: Re=5000, 擾乱なし, coarse メッシュ
2. ランダム擾乱実行: Re=5000, ランダム擾乱, coarse メッシュ
3. 上記 2 つの比較で初期擾乱の影響を初期評価する
```

**ポイント**: この時点では実行は一切していない。まず「何を調べたいのか」「最初に何を試すのか」を project.md に言語化する。

---

## シナリオ 2: Web UI で研究状態を確認・編集する

```bash
cd ~/cfd-platform
err serve
# → http://localhost:8765 で Web UI が起動
```

### テーマ一覧画面（`/`）

ブラウザを開くとテーマ一覧が表示される。

```
ERR — ~/cfd-platform

テーマ一覧
──────────────────────────────────────
▼ turbulence-transition          [active]
  「Re=5000 付近で観測される間欠的な遷移パターンの支配因子は何か」
```

テーマ名をクリックすると個別ページに遷移する。

### テーマ個別画面（`/themes/turbulence-transition`）

左サイドバーに frontmatter の構造化情報、メインエリアに Markdown 本文が表示される。
「編集」ボタンを押すとフォーム画面に遷移し、frontmatter のフィールドと本文をそれぞれ編集できる。

**使いどころ**: シミュレーションを数本走らせた後、結果を見ながら Web UI で project.md を更新する。ターミナルとブラウザを行き来しながら使う。

---

## シナリオ 3: 研究が進んでサブテーマが生まれる

ベースライン実行とランダム擾乱実行を比較した結果、初期擾乱の影響が予想以上に大きいことが分かった。
メッシュ解像度を変えた系統的な比較が必要だと判断し、サブテーマを切る。

```bash
err init turbulence-transition/mesh-sensitivity
# → .err/themes/turbulence-transition/themes/mesh-sensitivity/project.md が生成される
```

サブテーマの project.md を記入する。

```yaml
---
title: メッシュ解像度の遷移結果への影響
status: active
current_question: "coarse/medium/fine の 3 段階で遷移タイミングに有意差が出るか"
open_items:
  - fine メッシュの計算コストが高く、全条件は回せない可能性
comparing_themes:
  - "coarse vs medium vs fine（Re=5000, 擾乱なし）"
next_runs:
  - description: "Re=5000, 擾乱なし, medium メッシュ"
    params: {Re: 5000, perturbation: none, mesh: medium}
  - description: "Re=5000, 擾乱なし, fine メッシュ"
    params: {Re: 5000, perturbation: none, mesh: fine}
---

## 研究目的

親テーマ (turbulence-transition) で coarse メッシュでの結果が得られたが、
メッシュ依存性が未評価のため、結論の信頼性が不明。
3 段階のメッシュ解像度で同一条件の比較を行い、結果の収束性を確認する。

...
```

テーマ一覧は自動的にツリー構造で表示される。

```bash
err list
# 出力:
# turbulence-transition          [active]
#   └── mesh-sensitivity         [active]
```

Web UI のテーマ一覧でも同じツリーが表示される。
サブテーマの個別画面にはパンくずリスト（ホーム > turbulence-transition > mesh-sensitivity）が表示され、親テーマに戻れる。

---

## シナリオ 4: 複数テーマを並行管理する

乱流遷移の研究と並行して、別の研究テーマ「伝熱促進フィンの形状最適化」も進めることになった。

```bash
err init fin-optimization
```

テーマ一覧が更新される。

```bash
err list
# 出力:
# fin-optimization               [active]
# turbulence-transition          [active]
#   └── mesh-sensitivity         [active]
```

Web UI のトップページには全テーマが一覧表示され、それぞれの「現在の問い」が見える。
これにより、複数テーマを抱えていても「今どのテーマで何を問うているか」を一望できる。

---

## シナリオ 5: 研究の一時中断と再開

メッシュ感度の検証が一段落し、計算リソースの都合で一時中断する。

Web UI の編集画面で status を `paused` に変更し、保留理由を open_items に追記する。

```yaml
status: paused
open_items:
  - fine メッシュの結果が medium と 5% 以内の差。ただし Re=8000 では未確認
  - 計算リソース確保待ち（3 月末まで）
```

数週間後、リソースが確保できたら status を `active` に戻し、project.md の「次の実行候補」に Re=8000 の条件を追加して再開する。

**ポイント**: project.md が「中断時に何が分かっていて、何が残っているか」の記録になる。再開時に記憶に頼らなくて済む。

---

## シナリオ 6: 日常的なワークフロー（フェーズ 1）

フェーズ 1 での ERR の使い方は、端的に言うと以下のサイクルである。

```
 ┌─────────────────────────────────────────────────┐
 │  1. project.md を読み、次に何をすべきか確認する  │
 │              ↓                                   │
 │  2. シミュレーションを実行する（ERR の外で）      │
 │              ↓                                   │
 │  3. 結果を見て、project.md を更新する             │
 │     - current_question を更新                    │
 │     - open_items に新たな疑問を追加              │
 │     - next_runs を更新                           │
 │     - 必要ならサブテーマを作成                   │
 │              ↓                                   │
 │  4. 1 に戻る                                     │
 └─────────────────────────────────────────────────┘
```

フェーズ 1 の ERR は **実行そのものは管理しない**。
シミュレーションの起動・結果の保存は研究者が既存のワークフローで行う。
ERR が担うのは「何を問い、何を試し、何が分かり、次に何をするか」という研究状態の記録と可視化である。

---

## シナリオ 7: 後続フェーズで広がる使い方（将来像）

フェーズ 1 では project.md の管理のみだが、後続フェーズでは以下が加わる。

### フェーズ 2 — 実行記録

```bash
err run log --theme turbulence-transition \
  --params '{"Re": 5000, "perturbation": "none", "mesh": "coarse"}' \
  --output ./results/run_001/
```

実行の条件と出力パスが `.err/themes/turbulence-transition/runs/` に記録される。
Web UI から実行履歴を一覧でき、project.md の next_runs から実行記録への接続が生まれる。

### フェーズ 3 — 比較系列

複数の実行をグループ化し、「何を固定して何を変えたか」を明示する。

```bash
err series create --theme turbulence-transition \
  --name "mesh-convergence" \
  --fixed '{"Re": 5000, "perturbation": "none"}' \
  --variable mesh \
  --runs run_001,run_002,run_003
```

Web UI で比較系列ごとに結果を並べて見られるようになる。

### フェーズ 4 — 差し戻し候補

比較系列の結果から、project.md への更新候補が自動整理される。

```
差し戻し候補:
- [提案] current_question を更新: メッシュ収束が確認できたため、
  次の問いは「擾乱の種類による遷移パターンの違い」に進めるか
- [確認] open_items の「メッシュ解像度の十分性が未確認」は解決済みの可能性
- [保留] Re=8000 での検証は未実施のため、open_items に残すべき
```

研究者がこれを確認し、採否を判断して project.md を更新する。

---

## ERR が使われない場面

ERR はすべての研究作業を覆うものではない。以下の作業は ERR の外で行う。

- シミュレーションコードの開発・デバッグ → 通常の開発ワークフロー
- 論文の執筆 → LaTeX / Word 等
- 図の作成・可視化 → Python スクリプト / ParaView 等
- チームとの議論・報告 → Slack / ミーティング等

ERR が扱うのは、これらの活動の **間をつなぐ研究状態の記録** である。
「今どこにいて、次にどこへ向かうか」を見失わないための基盤として使う。
