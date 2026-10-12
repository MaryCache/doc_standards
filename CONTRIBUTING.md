# CONTRIBUTING — 原則変更時の下流同期チェックリスト（制約 S3 の運用手順）

> **レイヤー**: 運用規約（メンテナンス手順）。
> **原則参照**: [`principles/granularity-axis.md`](principles/granularity-axis.md) が唯一の真実。本ファイルは原則を再定義せず、**原則を変えたときに下流をどう揃えるか**の手順だけを定める（制約 S3）。
> **呼ばれ元**: [`principles/responsibility-map.md`](principles/responsibility-map.md) 末尾のメンテナンス規約が本ファイルを指す。

---

## 位置づけ — 二層構造と「投影」の向き

このライブラリは **原則層が唯一の真実**で、レシピ・スキーマ・語彙・ルーブリックはその**投影**である。

```
principles/        ← 唯一の真実（手法非依存の不変量 P2/P4/P5/P6/P9 ＋ 工程×成果物の責務境界）
  ├─ granularity-axis.md      不変量
  └─ responsibility-map.md    含む/含まない/渡す/逸脱・委譲表
        │ 投影（参照のみ・再定義しない）
        ▼
waterfall/ , agile/           手法別レシピ
scripts/schema/*.json         必須見出し（機械判定）
scripts/vocab/*.json          禁止語（機械判定）
rubric/*.md                   質的判定（機械で測れない観点）
SKILL.md                      Claude Code のスキル本体（このライブラリを読んで生成・チェックする）
```

> **現状の実装範囲（cycle-22 時点）**: 実装済みは19 doc_type（WF13＋agile6）＝**WF**: `data-design`（`waterfall/basic-design/data-design.md`・基本設計＝論理データ設計）／ `external-design`（`waterfall/basic-design/external-design.md`・基本設計＝外部設計・cycle-7）／ `architecture-design`（`waterfall/basic-design/architecture-design.md`・基本設計＝方式/アーキ設計・cycle-8）／ `nonfunctional-design`（`waterfall/basic-design/nonfunctional-design.md`・基本設計＝非機能設計・cycle-9）／ `operations-design`（`waterfall/basic-design/operations-design.md`・基本設計＝運用/移行設計・cycle-10）／ `detailed-design-data`（`waterfall/detailed-design/data-design.md`・詳細設計＝物理データ）／ `detailed-design-process`（`waterfall/detailed-design/process-design.md`・詳細設計＝処理詳細〔クラス/モジュール構造・処理仕様〕・cycle-19＝詳細設計2本目・data と**対**〔データ側=DB 物理／処理側=クラス・処理で軸を割り二重定義しない〕・必須は絞る〔モジュール構造/処理仕様/トレーサビリティ〕・ghost doc/実質空の両端は rubric・vocab は `なぜなら業務` を data から踏襲〔業務理由転記が機械で綺麗に拾える〕）／ `srs`（`waterfall/requirements/srs.md`・要件定義）／ `test-case-spec`（`waterfall/test/test-case-spec.md`・テストケース仕様・cycle-5）／ `test-plan`（`waterfall/test/test-plan.md`・テスト計画＝IEEE 829 系・cycle-15＝WF テスト工程2本目・必須は絞る〔スコープ/終了基準/トレーサビリティ〕・vocab は test-case-spec 3語踏襲〔終了基準の P6〕）／ `test-design-spec`（`waterfall/test/test-design-spec.md`・テスト設計仕様＝IEEE 829 系・cycle-16＝WF テスト工程3本目・ケース仕様の直上・必須は絞る〔テスト条件/網羅方針/トレーサビリティ〕・**設計仕様↔ケース仕様は F1〔論理/物理〕同型＝抽象/具体を割る**・網羅方針独立必須は nonfunctional の測定方法必須化と同型・vocab は3語踏襲〔経験検証〕）／ `test-procedure-spec`（`waterfall/test/test-procedure-spec.md`・テスト手順仕様＝IEEE 829 系・cycle-17＝WF テスト工程4本目・ケース仕様の直下・必須は絞る〔前提/実行手順/トレーサビリティ〕・**実行↔判定の分離**〔手順＝How to run／判定＝ケース仕様の What to expect・操作はケース仕様の単一働きかけと軸が直交〕・前提独立必須は再現性担保・vocab は3語踏襲〔期待結果混入のサイン・経験検証〕）／ `test-strategy`（`waterfall/test/test-strategy.md`・テスト戦略＝組織横断・cycle-18＝WF テスト工程5本目・最上位＝**テスト工程5レベル完備**・必須は絞る〔テスト方針/テストレベル/トレーサビリティ〕・戦略↔計画は組織↔プロジェクトの抽象度境界・**vocab は WF テスト5本中唯一空**〔戦略は方針レベルで3語の主戦場が無い＝「綺麗に拾える＝踏襲」厳格適用→空・原則の最強実証〕）、**agile**: `user-story`（`agile/user-story.md`・ユーザーストーリー＝初の agile スライス・cycle-6）／ `acceptance-criteria`（`agile/acceptance-criteria.md`・受入基準＝Given-When-Then・cycle-13＝agile 初のトレース有効スライス・agile だが vocab を持つ）／ `design-doc`（`agile/design-doc.md`・設計合意文書＝Google Style/arc42/C4・cycle-14＝vocab を空に戻す・必須は絞る〔全セクション強制が逸脱〕・ADR 委譲 S5）／ `adr`（`agile/adr.md`・Architecture Decision Record・cycle-20＝**委譲二重定義の S5 試金石**〔doc-standards は ADR の粒度境界〔必須5節 Context/Decision/Status/却下案/Consequences〔初版は4節・2026-10 に Nygard 2011 に合わせ Status を必須へ〕 の存在・却下案明示・trivial/事後正当化でない〕を定義／architecture-decision-records スキルが採番・生成・内容評価を所有＝design-doc/architecture-design が ADR を**リンク委譲する側**と対〕・却下案独立必須で Why 片側欠落を機械検出・vocab 空〔逸脱は構造/文脈〕・トレースは Context 内＝check_traceability skipped・H1 デコイ〔Decision〕回避）／ `rfc`（`agile/rfc.md`・Request for Comments＝決定前の探索/提案文書・cycle-21＝agile 5本目〔**ADR と時間軸で対**＝RFC の代替案は**生きた選択肢**／ADR の却下案は**葬った選択肢**・RFC 探索→採択→ADR 記録の向きで連鎖〕・必須は絞る〔提案内容/代替案/未解決の論点/トレーサビリティ〕・**`未解決の論点` を独立必須にして「未決を装った既決」を機械検出**〔ADR 却下案・design-doc Non-Goals と同型〕・vocab 空〔提案文書で期待結果を書かず3語の主戦場が無い＝design-doc/adr 型・5例目〕・**独立トレース有効**〔ADR と非対称＝RFC は doc-standards 固有で外部スキル所有形式と衝突せず check_traceability 有効〕）／ `pr-faq`（`agile/pr-faq.md`・PR-FAQ＝Amazon Working Backwards＝顧客視点の未来プレスリリース＋想定問答で企画を逆算・cycle-22＝agile 6本目〔agile コア体系の締めくくり〕・必須は絞る〔プレスリリース/想定問答/成功指標/トレーサビリティ〕・**`成功指標` を独立必須にして「測定可能な成功条件の欠落＝絵に描いた餅」を機械検出**〔ADR 却下案・design-doc Non-Goals・RFC 未解決の論点・nonfunctional 測定方法と同型〕・`FAQ` は3文字で H1「PR-FAQ」に部分一致しデコイ化ゆえ required を複合語 `想定問答` に回避・vocab 空〔企画逆算で期待結果を書かず3語の主戦場が無い＝6例目〕・**独立トレース有効**〔トレース先は対応する顧客課題/事業目標＝顧客課題に紐付かない機能＝Working Backwards 違反/プロダクトアウトを空セル検出〕・PR の内部機能リスト化/楽観バイアス/スライド化は rubric）。基本設計（M3）はこれで5細分すべて（データ設計・外部設計・方式設計・非機能設計・運用/移行設計）が整備済み＝**基本設計 M3 完成**。**WF テスト工程は戦略/計画/設計仕様/ケース/手順の5レベル完備**。残る未実装は `waterfall/` の他 `doc_type`（agile 主要成果物は user-story/AC/design-doc/ADR/RFC/PR-FAQ で出揃った）で、本チェックリストはそれらが増えても同じ手順で回せるように書いてある（上図・`grep` 例に出る未実装パスはその前提）。

**S3（最重要・冒頭再掲）**: レシピ層は原則層を**参照するだけで再定義しない**。差異が要るなら原則層に variant を足し、双方がそこを指す。下流と原則が矛盾したら、**常に原則層を真**とする。

---

## 目次

1. [principles/ を変更したら](#1-principles-を変更したら)
2. [レシピ層の境界判断を変えたら](#2-レシピ層の境界判断を変えたら)
3. [逆方向の不変条件（下流が原則と食い違ったとき）](#3-逆方向の不変条件下流が原則と食い違ったとき)

---

## 1. principles/ を変更したら

`granularity-axis.md` の不変量（P2/P4/P5/P6/P9）または `responsibility-map.md` の境界表を変えたら、下流4種を順に同期する。各ステップはチェックボックスで潰す。

### ① レシピの整合確認（`waterfall/` ・ `agile/`）

- [ ] 変更した原則に触れているレシピを列挙する（例: `grep -rn "granularity-axis" waterfall/ agile/`、特定原則なら `grep -rn "P5" waterfall/ agile/ rubric/`）。
- [ ] レシピ本文の用語・境界記述が、変更後の原則と一致しているか確認する（原則の言い換え・先取り再定義がレシピに残っていないか）。
- [ ] レシピ冒頭バナーの原則参照リンク（`原則参照: granularity-axis.md が唯一の真実…(S3)`）と本文中のアンカーリンクが、変更後の見出し（アンカー）に解決するか確認する。

### ② スキーマ・語彙の更新要否（`scripts/schema/*.json` ・ `scripts/vocab/*.json`）

- [ ] 原則が**必須見出しの前提**を変えたか判定する。変えたなら該当 `scripts/schema/<doc_type>.json` の `required_headings` を同期する（見出しの追加・削除・改称）。
- [ ] 原則が**禁止語の前提**を変えたか判定する（ある工程に置いてよい/いけない語の線が動いたか）。変えたなら該当 `scripts/vocab/<doc_type>.json` の `forbidden` を同期し、各 `reason` に対応原則（例: `P5`/`P2`）を書く。
- [ ] スキーマ・語彙を変えたら、その判定を確かめる fixture（`scripts/tests/fixtures/`）も合わせて更新する。

### ③ ルーブリックの更新要否（`rubric/*.md`）

- [ ] 各観点が参照する**原則アンカー**（`参照原則: [P4](principles/granularity-axis.md#...)`）が、変更後の見出しに解決するか確認する。
- [ ] 観点の判定問い・合格基準が、変更後の原則と矛盾しないか確認する。機械判定（schema/vocab）に移った項目をルーブリックに重複させない／その逆も同様。

### ④ 変更根拠を記録

- [ ] **なぜ変えたか**・**どの反証や一次規格に基づくか**を、PR の説明に記録する。原則変更は「思いつき」ではなく反証や一次規格の裏取りに紐づける（granularity-axis.md は凍結せず継続反証する方針）。

### ⑤ 機械確認（同期が崩れていないか）

変更した `<doc_type>` の fixture とレシピ本体に対して、3チェッカーを通す（使い方は `python3 <script> <markdown_path> <doc_type>`）。

- [ ] `python3 scripts/check_headings.py <該当ファイル> <doc_type>` … 正常系 fixture とレシピ本体は **pass (exit 0)**、見出し欠落 fixture は **deviation (exit 1)** を返すこと。
- [ ] `python3 scripts/check_vocabulary.py <該当ファイル> <doc_type>` … 正常系は **pass**、禁止語違反 fixture は **deviation** を返すこと。
- [ ] `python3 scripts/check_traceability.py <該当ファイル> <doc_type>` … 正常系（トレーサビリティ表が全セル埋まり）は **pass**、空セル（孤立設計要素）のある fixture は **deviation**、トレーサビリティ節を持たない doc_type は **skipped**（fail-open）を返すこと。
- [ ] スクリプトのテストを通す（`python3 -m pytest scripts/tests/`）。
- [ ] 変更で増減した**アンカーリンク**（レシピ・ルーブリックから原則への `#見出し` リンク）が実在見出しに解決することを目視確認する。

---

## 2. レシピ層の境界判断を変えたら

**原則は HLD/LLD 等の工程境界線を規定しない（中立）**。境界線を引くのはレシピ層の責務である（granularity-axis.md P4 注）。だからこそ、境界を動かしたら**同じ `doc_type` の4成果物で一貫させる**必要がある。

| 成果物 | 同期する箇所 |
|---|---|
| レシピ本体（`waterfall/`・`agile/`） | スコープ表・各節の含む/含まない |
| `scripts/schema/<doc_type>.json` | 必須見出し（境界が動けば必須節が増減する） |
| `principles/responsibility-map.md` | 該当工程行の「含む / 含まない / 隣接へ渡す / 逸脱の判定基準」 |
| `rubric/<doc_type>.md` | 観点・参照原則アンカー（境界前提が変わると合格基準が動く） |

### 決着済み事例 — F1: 基本設計データ設計に物理を含めるか（この手順を踏んだ実例）

**F1** が、この「境界が成果物間で食い違った」実例である。当初は3成果物が「物理＝詳細設計（基本設計の対象外）」、2成果物が「物理＝基本設計に必須」と述べて両立しなかった（機械チェッカーは字面しか見ないため検出不能＝人間が裁定）。**2026-06-03 の判断でスタンスA（論理/物理を工程で割る）に決着し、cycle-2 で本節2の手順どおり同期した。** 本節を「原則／境界変更にこの手順を踏んだ実例」として残す。

着地の流れ（実施記録。スタンスの中身は F1 を参照。本ファイルは手順を示す）:

- [x] **スタンス決定**（人間が裁定）＝スタンスA（基本設計データ設計＝論理ERのみ、物理は詳細設計へ）。
- [x] 上表の**4成果物を同期**（basic レシピを論理のみに削減＋物理を `waterfall/detailed-design/data-design.md` へ移設 → schema を `["論理ER","トレーサビリティ"]` → responsibility-map 仮置き解除 → rubric を論理前提へ）。
- [x] **機械確認**（fixtures/tests を TDD 更新・pytest 13緑・両チェッカー期待どおり・basic レシピ pass）。
- [x] **決定と根拠を記録**し、F1 を「未決」→「決着＝A・再同期完了」へ更新。responsibility-map の仮置き宣言も解除済み。

---

## 3. 逆方向の不変条件（下流が原則と食い違ったとき）

下流（レシピ／スキーマ／語彙／ルーブリック）が原則と矛盾したら、**下流を直す**。原則を勝手に曲げてはいけない（S3）。

- [ ] まず矛盾が「下流の誤り」か「原則を変えるべき妥当な反証」かを切り分ける。
- [ ] **下流の誤り**なら下流だけを修正し、原則は触らない。
- [ ] **原則を変える妥当性がある**（一次規格の更新・反証ログでの破綻立証など）なら、それは原則変更であり、§1 の ①〜⑤ を回す（下流をその場で曲げて済ませない）。

> 原則変更は影響範囲が広い。「下流が言うことを聞かないから原則を緩める」方向の変更は S3 違反であり、認めない。原則を変えるなら反証で裏取りし、根拠を記録に残し、4種を同期する — それが本ファイルの全体である。
