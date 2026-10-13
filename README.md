<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/brand/logo/doc_standards-dark.svg">
  <img alt="doc_standards" src="assets/brand/logo/doc_standards.svg" width="420">
</picture>

# doc-standards

ソフトウェアの工程ドキュメントを、工程にふさわしい深さで書くための標準ライブラリと、それを使う Claude Code のスキルです。

要件書に実装の手順が混ざったり、基本設計にテーブル定義が入り込んだりすると、どの工程で何を決めたのかが追えなくなります。
このライブラリは、工程ごとに「書くこと・書かないこと・次の工程へ渡すこと」を決め、その線からはみ出した記述を見つけます。
この README では、はみ出した記述を「逸脱」と呼びます。

## 仕組み

ライブラリは、原則（`principles/`）、レシピ（`waterfall/` と `agile/`）、判定（`scripts/` と `rubric/`）の3つの層でできています。

`principles/` の原則は、手法に依存しない粒度の決まりです。
たとえば「要件は What と Why を書き、How を書かない」「設計の要素はすべて要件までたどれる」といった不変の条件を定めています。
ほかの層はすべてここを参照し、原則を書き換えたり言い換えたりしません。

`waterfall/` と `agile/` のレシピは、原則を文書の種類ごとに具体化したものです。
文書ごとに、必須の見出し、各節に含めるもの・含めないもの、記入例を載せています。

判定は、機械で決められるものと、読んで判断するものに分けています。
`scripts/` の3つのチェッカーは、必須見出しの欠落、その工程で使うべきでない語、トレーサビリティ表の空欄を、同じ入力には同じ結果で返します。
`rubric/` のルーブリックは、抽象度の混入や設計根拠の有無のように、文脈を読まないと決められない観点を、人間または LLM が判定するための基準です。

## 対応している文書

19種類の文書に、レシピ・チェッカーの定義・ルーブリックがそろっています。
表の doc_type は、チェッカーとスキルに渡す名前です。

| 手法 | 工程 | doc_type | レシピ |
|---|---|---|---|
| ウォーターフォール | 要件定義 | `srs` | `waterfall/requirements/srs.md` |
| ウォーターフォール | 基本設計（論理データ） | `data-design` | `waterfall/basic-design/data-design.md` |
| ウォーターフォール | 基本設計（外部設計） | `external-design` | `waterfall/basic-design/external-design.md` |
| ウォーターフォール | 基本設計（方式設計） | `architecture-design` | `waterfall/basic-design/architecture-design.md` |
| ウォーターフォール | 基本設計（非機能設計） | `nonfunctional-design` | `waterfall/basic-design/nonfunctional-design.md` |
| ウォーターフォール | 基本設計（運用・移行設計） | `operations-design` | `waterfall/basic-design/operations-design.md` |
| ウォーターフォール | 詳細設計（物理データ） | `detailed-design-data` | `waterfall/detailed-design/data-design.md` |
| ウォーターフォール | 詳細設計（処理） | `detailed-design-process` | `waterfall/detailed-design/process-design.md` |
| ウォーターフォール | テスト戦略 | `test-strategy` | `waterfall/test/test-strategy.md` |
| ウォーターフォール | テスト計画 | `test-plan` | `waterfall/test/test-plan.md` |
| ウォーターフォール | テスト設計仕様 | `test-design-spec` | `waterfall/test/test-design-spec.md` |
| ウォーターフォール | テストケース仕様 | `test-case-spec` | `waterfall/test/test-case-spec.md` |
| ウォーターフォール | テスト手順仕様 | `test-procedure-spec` | `waterfall/test/test-procedure-spec.md` |
| アジャイル | ユーザーストーリー | `user-story` | `agile/user-story.md` |
| アジャイル | 受入基準（Given-When-Then） | `acceptance-criteria` | `agile/acceptance-criteria.md` |
| アジャイル | Design Doc | `design-doc` | `agile/design-doc.md` |
| アジャイル | ADR | `adr` | `agile/adr.md` |
| アジャイル | RFC | `rfc` | `agile/rfc.md` |
| アジャイル | PR-FAQ | `pr-faq` | `agile/pr-faq.md` |

## 使い方

### Claude Code のスキルとして使う

リポジトリをスキルのディレクトリへ clone します。

```sh
git clone https://github.com/MaryCache/doc_standards ~/.claude/skills/doc-standard
```

リポジトリの直下にある `SKILL.md` がスキルの本体で、ライブラリのファイルを相対パスで読みます。
そのため、clone した場所がそのままスキルとして動きます。
プロジェクトだけで使うなら、そのプロジェクトの `.claude/skills/doc-standard` に clone しても同じです。

スキルは「設計書を書いて」「このドキュメントの粒度をチェックして」のような依頼で起動します。
書くときはレシピに沿って下書きを作り、チェックするときは機械判定とルーブリックの判定を分けて報告します。

### 手で使う

文書を書くときは、まず `principles/granularity-axis.md` で粒度の決まりを確かめ、上の表から自分の文書のレシピを開きます。
書き終えたら、チェッカーにファイルと doc_type を渡します。

```sh
python3 scripts/check_headings.py path/to/doc.md srs
python3 scripts/check_vocabulary.py path/to/doc.md srs
python3 scripts/check_traceability.py path/to/doc.md srs
```

チェッカーは Python 3 の標準ライブラリだけで動きます。
結果は JSON で出て、`status` は `pass`・`deviation`・`skipped` のどれかです。
逸脱を見つけたときだけ終了コード 1 を返すので、CI に組み込めます。

`skipped` は、判定を見送った印です。
定義が無い doc_type や読めないファイルのように判定できなかったとき、逸脱と決めつけずに `skipped` を返すので、`pass` と同じ扱いにはしないでください。
トレーサビリティ表を持たない `user-story` と `adr` は、`check_traceability.py` では常に `skipped` になります。

チェッカーが見るのは見出しと語の字面だけです。
抽象度の混入のような逸脱は、`rubric/<doc_type>.md` のルーブリックで確かめてください（`srs` なら `rubric/srs.md`）。

## ディレクトリ構成

```
doc-standards/
├── SKILL.md       Claude Code のスキル本体
├── principles/    手法に依存しない粒度の原則（ほかの層はすべてここを参照する）
├── waterfall/     ウォーターフォールのレシピ（要件・基本設計・詳細設計・テスト）
├── agile/         アジャイルのレシピ
├── scripts/       機械判定のチェッカー
│   ├── schema/    doc_type ごとの必須見出し
│   ├── vocab/     doc_type ごとの禁止語
│   └── tests/     チェッカーのテストと見本の文書
├── rubric/        doc_type ごとの質的判定の基準
└── CONTRIBUTING.md
```

## 変更するとき

原則・レシピ・チェッカーの定義（`scripts/schema/` と `scripts/vocab/`）・ルーブリックは互いに参照しています。
そのため、どれか1つを変えたら、参照しているほかのファイルも直す必要があります。
どこをそろえるかの手順は `CONTRIBUTING.md` にまとめています。

チェッカーのテストは pytest で動きます。

```sh
python3 -m pytest scripts/tests
```

## ライセンス

MIT License です。
詳しくは `LICENSE` を見てください。

原則とレシピは、IEEE 830、ISO/IEC/IEEE 29148、IEEE 829 などの規格や、公開されている記事を参考にしています。
引用は短い文と用語にとどめ、出典を本文に書いています。
