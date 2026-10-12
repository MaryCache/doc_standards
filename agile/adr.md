# ADR（アーキテクチャ決定記録）レシピ — アジャイル ADR

> **レイヤー**: 第2層レシピ（手法別具体指針・**agile**・ADR）
> **原則参照**: [`../principles/granularity-axis.md`](../principles/granularity-axis.md) が唯一の真実。本ファイルは原則を再定義しない（制約 S3）。
> **責務対照**: [`../principles/responsibility-map.md`](../principles/responsibility-map.md) の**アジャイル責務対照表の ADR 行**を参照（含む＝1 判断につき 1 ADR・Context/Decision/Status/Consequences・却下案の明示／含まない＝trivial な決定〔Prettier 等・可逆で影響小〕・決定済みの再宣言／隣接＝SAD の意思決定層・採番生成は architecture-decision-records スキルに委譲／逸脱＝事後正当化〔承認なし accepted〕・trivial な決定の ADR 化・Why の記述なし）。

---

## 位置づけ（agile 第2層の 4 本目のスライス）

これは doc-standards で**4 本目の agile レシピ**である（1 本目＝[`./user-story.md`](./user-story.md)・2 本目＝[`./acceptance-criteria.md`](./acceptance-criteria.md)・3 本目＝[`./design-doc.md`](./design-doc.md)）。User Story が WHO/WHAT/WHY を、Acceptance Criteria がその価値の観測可能な合否を、Design Doc が「どう作るか」の設計合意を living doc として形成するのに対し、**ADR は1つの設計判断を「なぜその形なのか」とともに永続記録する**（Nygard 形式＝タイトル／背景／決定／状態／帰結）。Design Doc が ADR を**リンク委譲する側**（重要判断を ADR に逃がす）であったのに対し、本スライスは**その委譲先の成果物自体**の粒度を定義する側である。

agile の第2層は**成果物ライフサイクル軸**（living docs として育ち、必要になった時点で詳細を確定する JIT 詳細化）で整理する。WF の**工程フェーズ軸**とは軸が異なる——これが**非対称設計の原則（S4）**である。ただし**原則層（第1層）は手法非依存で共通**であり、What/Why と How の分離（P2）・トレーサビリティ（P4）・設計根拠の必須（P4: design rationale）は WF でも agile でも変わらない不変量である。本レシピもそれらを再定義せず参照するだけである（S3）。

### 必須は絞る／関連 ADR は推奨（このスライス固有の設計理由）

Nygard（2011）の節は Title（H1）/ Context / Decision / Status / Consequences である（出典: Michael Nygard, [Documenting Architecture Decisions](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions)）。doc-standards は H1 のタイトルに加え、`却下案` を足した5節（Context / Decision / Status / 却下案 / Consequences）を必須にする。Nygard の原文に却下案の節は無く、これは本ライブラリ独自の追加である。追加の理由は下記「なぜ `却下案` が必須なのか」に示す。それ以外（関連 ADR 等）は推奨にとどめる。必須を増やすほど小さい判断にまで全節を埋めさせる過剰テンプレ化（gold plating）を招くため、design-doc / test 系と同じく必須は絞る。

- **必須節**: `Context`（背景・なぜこの判断が必要か・driven by 要求/設計）／`Decision`（決定内容）／`Status`（実際の承認状態）／`却下案`（検討した代替と却下理由＝Why の両側・本ライブラリ独自の追加）／`Consequences`（帰結・トレードオフ）。
- **推奨節（必須にしない）**: `関連 ADR`（前提・後継 ADR への参照）等。必須にすると過剰テンプレ化を招く。

> **なぜ `却下案` が必須なのか（機械表現の肝・design-doc の Non-Goals 必須と同型）**: 採用した `Decision` だけ書いて**却下した代替（Why の片側）を欠く**と、その判断は「採用案ありき」の事後正当化と区別がつかなくなる。設計根拠（design rationale）は採用理由と却下理由の**両側**で初めて成立する（P4）。スコープ否定側の欠落がスコープクリープの主因であるのと同じく、却下側の欠落こそ ADR の質を崩す主因であり、意味的にも `却下案` 必須が正しい。機械判定（[`../scripts/check_headings.py`](../scripts/check_headings.py)）は見出しの**部分一致**で必須を見るため、スキーマ（[`../scripts/schema/adr.json`](../scripts/schema/adr.json)）の `required_headings` に `却下案` を入れ、本レシピの実見出しを `## 却下案（検討した代替）` として、`却下案` がその見出しの部分文字列になるようにしている。

> **デコイの罠（ADR 固有・最重要・cycle-15〜19 教訓の最難関）**: ADR の正式名は "Architecture **Decision** Record" である。これを **H1 や導入見出しに英語フルで書くと、required の `Decision` がそこに部分一致してデコイになり**、`## Decision` 節を削っても誤って pass する。本レシピの H1 は `# ADR（アーキテクチャ決定記録）レシピ — アジャイル ADR` のように**英語フル表記を避け**（"決定記録" は英語 `Decision` を含まない・"アーキテクチャ決定" も含まない）、導入見出しは `位置づけ` とする。`Context`/`Status`/`却下案`/`Consequences` も H1・導入・推奨節見出しに部分一致で紛れ込ませない。required 各語が**実見出しに1つだけ**部分一致する設計を守る（cycle-14 Goals/Non-Goals・cycle-18 テストレベル・cycle-19 処理仕様と同型のデコイ回避だが、ADR は正式名に required 語を含む点で最難関）。

**境界を越えた記述の扱い**:
- **trivial な決定**（Prettier 等・可逆で影響小）を ADR 化していたら、それは過剰文書化である（責務対照表「含まない」）。ADR は1判断1記録で、影響範囲・不可逆性のある判断に限る。
- **決定済みの再宣言**（既に確定した方針を ADR として焼き直す）はしない（責務対照表「含まない」）。
- **事後正当化**（承認なしの accepted・採用案ありきで都合よい却下理由を後付け）を避ける（責務対照表「逸脱」）。`却下案` を Why の両側で実際の比較として書く。
- **Why の片側**（却下案を欠き採用案だけ書く）は `却下案` を書いて両側にする。
- **トレースは Context 内に書く**（独立見出しにしない・後述）。

---

## Context

**含む**: この判断をいま要する理由——解こうとしている課題・現状の痛み・きっかけになった要求や設計。あわせて、**この判断が何の要求/設計に driven されたか**（対応する要求 ID・user-story・Design Doc）を Context 内に書く（トレースは Context 内・独立見出しにしない＝後述）。

**含まない**: 決定の答えそのもの（それは `Decision` で書く）・trivial な判断の冗長な背景（そもそも ADR 化しない）。

Context は「なぜこの判断が必要か」を書く節である。trivial な決定（Prettier 等・可逆で影響小）にまで ADR を起こすのは過剰文書化であり、Context が薄くなる（書くべき非自明な背景が無い）兆候でもある。Context が書けないなら、その判断は ADR を要しない可能性が高い。

### 例（最小限・テンプレート用）

```
Context（背景・課題・driven by）:
  受注の一括登録（US-01・Design Doc「受注一括登録」driven by FR-12）で、在庫超過行の
  扱いが未確定。全行強整合か行単位部分成立かは性能と業務要件に直結する非自明な判断であり、
  決める前に承認を得る（事後正当化を避ける）。driven 元（US-01 / FR-12）は本 Context 内に書く。
```

---

## Decision

決定した内容そのものを書く。1つの ADR は1つの判断を記録する（1 判断 1 ADR）。

**含む**: 採用した決定の内容（何を・どの方式で決めたか）。

**含まない**: 却下した代替の比較（それは `却下案` で書く）・帰結やトレードオフ（それは `Consequences` で書く）。

### 例（最小限・テンプレート用）

```
Decision:
  行単位の部分成立を採用する。在庫内の行は登録を成立させ、在庫超過の行のみ業務エラーで弾く。
  一括登録全体は1トランザクションにせず、行ごとに引当・確定する。
```

---

## Status

実際の承認状態を正直に書く。提案中（proposed）／承認（accepted）／非推奨（deprecated）／置き換え（superseded）を示し、後継 ADR がある場合はその参照を添える。承認なしの accepted（事後正当化）は逸脱である。

### 例（最小限・テンプレート用）

```
Status:
  提案中（proposed）。設計レビューでの承認待ち。
```

---

## 却下案（検討した代替）

検討した代替と、その却下理由を**Why の両側**（採用理由と却下理由）で書く。設計根拠（design rationale）は両側で初めて成立する（P4）。

**含む**: 比較した代替案・各案の却下理由（トレードオフ）・採用案の採用理由。実際に比較したトレードオフを書く。

**含まない**: 採用案ありきで都合よく後付けした却下理由（事後正当化）。代替を検討していないなら正直にその旨を書く（捏造しない）。

却下案は**事後正当化にしない**。「採用案ありき」で都合のよい却下理由を後付けするのではなく、実際に比較したトレードオフを書く。Why の片側（採用理由）だけで却下側を欠くと、その ADR は設計根拠の体をなさない。

> **RFC を経た判断のとき**: この判断が RFC（コメント要求）を経たものなら、却下案には2系統が混じる——RFC で**生きていた代替**のうち採らなかったもの（決定の瞬間に [`rfc.md`](./rfc.md) の `代替案` からここへ移った選択肢）と、ADR で初めて検討して却下したもの。前者は RFC と**時間軸で対**をなす（生きた代替 → 葬った代替）。責務は依然 RFC＝決定前／ADR＝決定後で割れており（二重定義でなく相互参照）、ここを編集するときは RFC 側の連鎖記述（`rfc.md` の `代替案` 節）も併せて確認する。

### 例（最小限・テンプレート用）

```
案A: 全行一括の強整合（1行でも在庫超過なら全件失敗）。
  却下理由: 繁忙期の数百行登録で1行の不足が全件やり直しになり、受注漏れ防止の価値(US-01)を損なう。
            どの行が通り落ちたか利用者が観測できない。
案B: 行単位の部分成立（採用）。
  採用理由: 在庫内の行は確実に成立し、落ちた行だけ提示できる。部分成立が外から観測できる。
```

---

## Consequences

この判断の帰結とトレードオフを、判断の影響範囲とともに書く。

**含む**: 良い帰結・悪い帰結（トレードオフ）・この判断が及ぼす影響範囲（後続の判断・呼び出し側に移る責務等）。

**含まない**: 決定の再記述（`Decision` の繰り返し）・却下案の比較（`却下案` の繰り返し）。

### 例（最小限・テンプレート用）

```
Consequences:
  良い帰結: 部分成立で受注漏れが減る。落ちた行を利用者が即把握できる。
  トレードオフ: 行ごと引当で在庫の一時的不整合ウィンドウが生じうるため悲観ロックで直列化する。
                「全部成功/全部失敗」を期待する呼び出し側に、部分成立であることを明示する責務が移る。
```

---

## 推奨節（関連 ADR）

> **推奨節（必須ではない）**。必須にすると小さい ADR でも全節を埋めさせる過剰テンプレ化（gold plating）を招くため必須にしない。推奨節の見出しには必須語（`Context`/`Decision`/`Status`/`却下案`/`Consequences`）を**含めない**（デコイ回避）。

- **関連 ADR**: 前提となる ADR・この ADR を置き換える後継 ADR への参照。

---

## トレースは背景節に書く（独立トレース節を設けない／check_traceability は skipped）

ADR の標準形式（Nygard）に**独立したトレーサビリティ表は無い**。この判断が何の要求/設計に driven されたか（対応する要求 ID・user-story・Design Doc）は **`Context` 内**に書く。独立したトレース見出しを設けない理由は、ADR 標準形式を尊重し、採番・生成を所有する [`architecture-decision-records`](../principles/responsibility-map.md#3-既存スキル委譲表) スキルの記録フォーマットと衝突させないためである（S5・二重定義回避）。

> したがって ADR は**トレーサビリティ必須見出しを持たず**、機械の [`../scripts/check_traceability.py`](../scripts/check_traceability.py) は**トレース節が無いため skipped（fail-open）を返す**。これは [`./user-story.md`](./user-story.md) と同型であり、トレース表（対応 user-story 列）を持つ [`./acceptance-criteria.md`](./acceptance-criteria.md) / [`./design-doc.md`](./design-doc.md) とは非対称である。トレース表が無いので**空セル検出（孤立要素）の対象外**であり、orphan の検出は ADR では発生しない。driven 元が Context に書かれているか・意味的に妥当かは [`../rubric/adr.md`](../rubric/adr.md) の質的判定（Context の質）で見る。

---

## ADR の採番・生成・内容評価はスキルが所有（委譲分担の明示・S5・二重定義回避）

**doc-standards は ADR の「粒度境界」だけを定義する。** すなわち (a) 必須5節（Context / Decision / Status / 却下案 / Consequences）の存在・(b) 却下案が Why の両側で明示されているか・(c) trivial な決定でないか・(d) 事後正当化でないか、である。これに対し、**ADR の採番（ADR-NNNN の番号体系）・記録の生成・内容の評価（却下案が技術的に妥当か・決定が正しいか）は [`architecture-decision-records`](../principles/responsibility-map.md#3-既存スキル委譲表) スキルが所有する（S5）。**

この分担が本スライス最大の肝である。Design Doc / 方式設計が ADR を**リンク委譲する側**（重要判断を ADR に逃がし、本文に二重定義しない）であったのと対をなし、本スライスは ADR の**粒度を定義する側**である。両者が同じ ADR を別の角度から扱うため、**役割を割って二重定義を避ける**:

| 関心事 | 所有 | 内容 |
|---|---|---|
| ADR の**粒度境界** | doc-standards（本レシピ・[`../rubric/adr.md`](../rubric/adr.md)） | 必須5節の存在・却下案の明示・trivial でない・事後正当化でない |
| ADR の**採番・生成・内容評価** | `architecture-decision-records` スキル | ADR-NNNN 採番・記録フォーマット・却下案や決定の技術的妥当性 |

doc-standards 側で ADR の番号体系・記録フォーマットを**二重定義しない**（S3 と整合: 委譲先が source of truth）。本レシピは ADR の Nygard 形式（Context/Decision/Status/Consequences は ADR 標準）を**再定義せず、粒度の必須節として参照する**。ADR の内容の正否（却下案が妥当か・決定が正しいか）は本レシピも rubric も評価しない——それはスキルおよびレビュースキル（`review-handoff` / `santa-method`）の責務である。

---

## vocab の説明（ADR は vocab を空にする／逸脱は rubric 主導）

**本 doc_type（adr）の機械語彙チェック（vocab）は空である**（[`../scripts/vocab/adr.json`](../scripts/vocab/adr.json) の forbidden は `[]`）。これは設計上の判断であり、欠落ではない。

ADR の逸脱（事後正当化〔承認なし accepted〕・trivial な決定の ADR 化・Why の記述なし）は、いずれも**構造・文脈の判定**であって、特定の禁止トークンの部分一致では原理的に拾えない。「却下案なし」（Why の片側欠落）は必須見出し `却下案` の欠落として [`../scripts/check_headings.py`](../scripts/check_headings.py) が機械検出するため vocab は不要であり、残る逸脱（事後正当化・trivial・Why なし）に明確な定型句マーカーは無い。仮に `accepted` を禁止語にしても、それは**正当な承認状態の宣言**（承認済みの Status）と同一トークンであり、事後正当化（承認なしの accepted）だけを切り分けられず誤爆する。trivial の判定（Prettier 等・可逆で影響小）も製品名・文脈に依存し、部分一致では拾えない。

> **vocab の有無は『その doc_type の逸脱が機械で綺麗に拾えるか』で決まる**——agile か WF かの別ではない。[`./acceptance-criteria.md`](./acceptance-criteria.md) は Then の曖昧期待結果3語が部分一致誤爆なく拾えたから vocab を持ち、[`./user-story.md`](./user-story.md) / [`./design-doc.md`](./design-doc.md) と本 ADR は拾えないから vocab を空にする。ADR の逸脱は **design-doc 同型で構造/文脈ゆえ空**である。これが agile の **rubric 主導**の正しい現れであり、機械で綺麗に拾える逸脱だけ機械に任せ（＝却下案節の欠落のみ）、それ以外（事後正当化・trivial な決定の ADR 化・Consequences/Context の質・委譲境界）は [`../rubric/adr.md`](../rubric/adr.md) の質的判定へ委ねる。
