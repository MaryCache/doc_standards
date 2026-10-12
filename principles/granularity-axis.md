# 粒度境界の原則 — 工程ドキュメントの不変量（第1層）

> ステータス: サイクル1で反証実施（data-design 縦スライス）・核は維持。以後のサイクルで継続反証する（凍結しない）。

この文書は手法非依存（waterfall / agile を問わない）の粒度原則を定義する。ここに置くのは**真に不変な量だけ**である。具体的に「どの粒度を、どのファイルに、いつ書くか」は手法別のレシピ層（`waterfall/`・`agile/`）に降ろし、ここでは扱わない。たとえば「詳細設計は独立した文書として持つ」は不変量ではない（アジャイルではコード自体が詳細設計の真実になりうる）ため、原則には含めない。

## 目次

### 不変量（手法非依存の原則）

- [P2: 要件は What/Why、How は原則排除（正当な制約は例外）](#p2-要件は-whatwhyhow-は原則排除正当な制約は例外)
- [P4: 設計は要件へ全要素トレース可能・設計根拠は必須](#p4-設計は要件へ全要素トレース可能設計根拠は必須)
- [P5: 数値精度は工程マーカーである](#p5-数値精度は工程マーカーである)
- [P6: 検証可能性は工程を貫く不変量・テスト文書は要件を ID 参照する](#p6-検証可能性は工程を貫く不変量テスト文書は要件を-id-参照する)
- [P9: NFR は要件段階で並行検討・後回し禁止](#p9-nfr-は要件段階で並行検討後回し禁止)

### 検出補助（機械強制しないヒューリスティック）

- [P1: 主語ヒューリスティック](#p1-主語ヒューリスティック検出補助)
- [P3: 要件三層（StRS→SyRS→SRS）](#p3-要件三層strssyrssrs検出補助)
- [P7 / P8: テスト文書の階層と戦略・計画の分離](#p7--p8-テスト文書の階層と戦略計画の分離検出補助)
- [P10: IREB 要件粒度フレーム](#p10-ireb-要件粒度フレーム検出補助)

---

## 不変量（手法非依存の原則）

各原則には出典と信頼度を併記する。信頼度凡例: high=一次規格/逐語照合済、medium=practitioner/中信頼度。

### P2: 要件は What/Why、How は原則排除（正当な制約は例外）

要件には What（何を）と Why（なぜ）を書き、How（設計・実装の詳細）は**原則として排除する**。モジュール分割・関数割り当て・データ構造など実装の決定を要件に混入させない。

ただし、上位要求や外部条件に由来する**正当な制約**（セキュリティ・セーフティ要件、既定プロトコル、契約上指定されたベンダー等）は、その根拠を明示したうえで**例外として許容する**。これは絶対禁止ではない。

- 出典: IEEE 830-1998 §4.2(b)「Should not describe any design or implementation details. These should be described in the design stage」、§4.2「a properly written SRS limits the range of valid designs, but does not specify any particular design」[IEEE Xplore 720574 — standard, **high**、一次PDF照合済]。
- 出典（補強）: ISO/IEC/IEEE 29148:2018 — システム要件は「should not imply a specific implementation (vendor, protocol, etc.) unless constrained to do so by a higher-level requirement or constraint」[iso.org 72089 / cwnp.com — standard, **high**、一次PDF照合済]。
- 注（裏取り）: IEEE 830 は Recommended Practice であり mandatory な "shall" ではなく "should/should not" を用いる**強い推奨**である。§4.7.1 はセキュリティ/セーフティ等の必要な設計制約を明示的に許容する。したがって本原則は「原則排除＋根拠付き例外許容」と書く。

### P4: 設計は要件へ全要素トレース可能・設計根拠は必須

設計はその全要素が要件へトレース可能でなければならない（孤立した設計要素を作らない）。あわせて design rationale（設計判断・検討したオプション・却下案・トレードオフ）を必須セクションとして残す。

HLD（基本設計）と LLD（詳細設計）の境界をどこに引くかは規格上スコープ外であり、**組織判断に委ねられる**。第1層はこの境界線そのものを規定しない。

- 出典: IEEE 1016-2009 — SDD のビューポイント（Decomposition / Dependency / Interface / Detailed Design / Data Flow / State Machine / Interaction）を定義し、design rationale を必須セクション、全設計要素の SRS 要求へのトレーサビリティを義務付ける [IEEE Xplore 5167255 — standard, **high**]。
- 注: IEEE 1016 自身が「アーキテクチャと詳細設計の境界はシステム依存でスコープ外」と明記している [同 — standard, **high**]。
- サイクル1 反証注（2026-06-03）: 境界線は**レシピ層が引く**。第1層は中立のまま、レシピ層は成果物間（レシピ本体／スキーマ／責務対照表／ルーブリック）で境界を**一貫**させること。サイクル1 は「基本設計データ設計に物理を含めるか」の不整合を実例として検出した（[CONTRIBUTING.md](../CONTRIBUTING.md) の F1）。原則が境界に中立を保った判断はこの反証で立証されたため、原則本文は無変更。

### P5: 数値精度は工程マーカーである

数値の**精度のレベル**が工程を示す。概算値（「約3秒」「約100同時接続」）は上流（要件・基本設計）、厳密値（「3600ms@p99」「最大128同時セッション」）は詳細（詳細設計・構成仕様）に対応する。上流文書に厳密値が、下流文書に概算値が現れたら粒度のズレを疑う。

- 出典: [qiita yukikoblog8376 / R4 boundary_rules — practitioner, **medium**]。
- 注（裏取り・2026-10-11）: practitioner より強い一次資料（規格・論文・Wiegers や Gilb の原文）は**見つかっていない**（Wiegers『More About Software Requirements』の粒度の章と Gilb の Planguage は、本か二次の要約でしか確認できなかった）。一次資料が無いので信頼度を high から medium に下げた。

### P6: 検証可能性は工程を貫く不変量・テスト文書は要件を ID 参照する

要件は verifiable（検証可能）でなければならない。これは特定工程の性質ではなく工程を貫く不変量である。テスト文書は要件を「何をすべきか」から「どう確認するか（手順・入力・期待値）」へ**変換**して書き、要件文をそのまま**転記しない**（転記は二重管理と矛盾の温床になる）。要件はテスト文書から **ID で参照**する。

- 出典: ISO/IEC/IEEE 29148（verifiable 特性）/ Qbook 要件転記アンチパターン [practitioner, **high**]。

### P9: NFR は要件段階で並行検討・後回し禁止

非機能要件（NFR）は機能要件と**並行して要件段階で検討・合意する**。後工程への先送りを禁止する。

ただし、NFR の**具体値をどの文書に置くか**（SRS か基本設計か）は規格と実務で割れており、第1層では確定しない。具体値の置き場はレシピ層に委ねる。第1層が不変量とするのは「並行検討・後回し禁止」のみである。

- 出典: IPA 非機能要求グレード2018（6カテゴリ: 可用性 / 性能・拡張性 / 運用・保守性 / 移行性 / セキュリティ / システム環境）[IPA archive — standard, **high**] / ISO/IEC 25010:2023 SQuaRE 9特性 [iso.org 78176 — standard, **high**]。
- 注（裏取り）: NFR を SRS に置くか基本設計に置くかは規格（IEEE 830/29148）と日本実務（基本設計で具体値確定が多数）で割れ、重複は同期リスクになる。IPA 6カテゴリと ISO 25010 の9特性は部分対応で1対1ではない。

---

## 検出補助（機械強制しないヒューリスティック）

以下は粒度ズレの**検出を助ける手がかり**であり、いずれも **検出補助であり機械強制しない**。決定論的な lint ルールとして自動拒否に使うと誤検出を生むため、あくまで人間・LLM 判定の入力として扱う。

### P1: 主語ヒューリスティック（検出補助）

**検出補助であり機械強制しない。** 文の主語の抽象度で工程帰属を推定できる。主語が「利用者/業務」（What/Why）なら要件、「システム/コンポーネント」（外部から見た How）なら基本設計、「モジュール/メソッド/テーブル」（内部の How）なら詳細設計。

- 出典: 日本実務の 5W1H 配分と subject-of-sentence ヒューリスティック [zenn.dev/nyanchu, qiita yukikoblog8376 — practitioner, **medium**]。
- 注（裏取り）: **この主語ヒューリスティックの誤検出率は未検証**で、自動 lint ルール化の信頼性は未確立 [verification — open question]。検出補助としては有効だが機械強制は要追加調査。
- 注（食い違い・2026-10-11）: 要件の書き方の型 **EARS は、要件の主語を必ずシステム名にする**（「The <system name> shall <system response>」・規則は前提0個以上／きっかけ0〜1個／**システム名1つ**／応答1つ以上）[Alistair Mavin の EARS 公式ガイド https://alistairmavin.com/ears/ — practitioner（考案者本人）, **high**、原文照合済]。IEEE 流の「The system shall …」も同じ。英語圏の要件や EARS で書いた要件にこの主語の手がかりを当てると、**正しい要件を基本設計と取り違える**。主語が「システム」でも、外から見える応答（What）を述べていれば要件である。日本実務の 5W1H 配分の文脈に限って使う。high の根拠が practitioner 2本だけなので medium に下げた。

### P3: 要件三層（StRS→SyRS→SRS）（検出補助）

**検出補助であり機械強制しない。** 要件は StRS → SyRS → SRS と抽象度が降下する三層で捉えられる。設計解を先取りして解空間を不当に狭めないかの点検に使う。

- 出典: ISO/IEC/IEEE 29148:2018 が StRS/SyRS/SRS（+BRS）を定義 [iso.org 72089 — standard, **high**]。
- 注（裏取り）: 29148:2018 の**個別要件の9特性**は necessary/appropriate/unambiguous/complete/singular/feasible/verifiable/correct/conforming であり、"implementation free" や "traceable" は個別要件の9特性に**含まれない**（implementation-free は stakeholder 要件記述側の語、traceable は管理属性）。これを9特性として扱う引用は誤帰属。

### P7 / P8: テスト文書の階層と戦略・計画の分離（検出補助）

**検出補助であり機械強制しない。** テスト文書は抽象度で階層化される（計画 → 設計仕様 → ケース仕様 → 手順仕様）。設計仕様＝テスト条件＋高レベルケース（具体値なし）、ケース仕様＝具体値。階層を飛び越えてケース詳細を計画へ混入させない。あわせて、テスト戦略（組織/プログラム・複数リリースで安定）とテスト計画（プロジェクト・リリース毎更新）を分離する。

- 出典: ISTQB Glossary（各種別の逐語定義、test strategy=「組織またはプログラムで実施するテストレベルの高レベル記述」）/ BrowserStack [standard+practitioner, **high**、逐語照合済]。
- 注（裏取り）: 「計画→設計→ケース→手順」の4階層体系・各層への責務割当ては ISTQB Glossary ではなく源流の **IEEE 829（現 ISO/IEC/IEEE 29119-3）に由来**する。また **test plan はテスト仕様の包含対象ではない**（テスト仕様＝設計/ケース/手順の3種）。approach（どのように）はテスト戦略にも含まれ、戦略/計画の二分は厳密な規格境界ではない。

### P10: IREB 要件粒度フレーム（検出補助）

**検出補助であり機械強制しない。** 要件粒度を Summary Goal（初期/実現可能性フェーズ）→ User Goal（開発フェーズの基準粒度・スコープを曖昧なく定義できる粒度）→ Sub-function Goal（共通振る舞いのみ）の三層で捉える。開発仕様に Summary 粒度が残るのはエリシテーション未完のサイン。

- 出典: Simões & Vazquez「Functional Requirements and their levels of granularity」IREB RE Magazine, 2017-02-21（https://re-magazine.ireb.org/articles/functional-requirements-and-their-levels-of-granularity）[practitioner-article, **medium**、原文照合済 2026-10-11]。三層の定義（Summary＝業務の流れのような上位の要件／User＝特定の利用者の1つの作業／Sub-function＝作業の手順や規則）、User Goal を「スコープを曖昧なく定義する基準」とし、それより上の粒度は聞き取りが未完の印かもしれないとする点、Sub-function は振る舞いが複数の作業に共通するときに向く点は、上の要約と原文が一致した。
