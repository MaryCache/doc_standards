# データ設計レシピ — ウォーターフォール詳細設計（物理）

> **レイヤー**: 第2層レシピ（手法別具体指針・詳細設計）
> **原則参照**: [`../../principles/granularity-axis.md`](../../principles/granularity-axis.md) が唯一の真実。本ファイルは原則を再定義しない（制約 S3）。
> **責務対照**: [`../../principles/responsibility-map.md`](../../principles/responsibility-map.md) の詳細設計行を参照（DB 物理設計：型/NULL/FK/index/正規化）。

> **機械判定 整備済み**（doc_type=`detailed-design-data`・`scripts/schema/detailed-design-data.json`＋`scripts/vocab/detailed-design-data.json`＋`rubric/detailed-design-data.md` あり。`check_*.py <path> detailed-design-data` で実判定＝pass/deviation を返す）。基本設計データ設計（[`../basic-design/data-design.md`](../basic-design/data-design.md)＝論理）と対をなす詳細設計（物理）スライス。

---

## 目的とスコープ

基本設計のデータ設計（論理 ER：[`../basic-design/data-design.md`](../basic-design/data-design.md)）で確定したエンティティ・関連・正規化レベルを受けて、**物理**に展開する工程範囲を定める。

| 工程 | 本レシピでの扱い |
|---|---|
| **基本設計（論理）** | 前提（入力）。論理 ER・テーブル一覧・主要ビジネスルールは基本設計レシピで確定済みとする。本レシピでは再記述しない |
| **詳細設計（物理）** | 対象。テーブル名・カラム名（物理名）・データ型・NULL 可否・PK・FK・代表インデックス・DDL をここで確定する |

責務対照表（responsibility-map.md の詳細設計行）は「DB 物理設計（型/NULL/FK/index/正規化）・厳密数値（3600ms@p99 等）」を含む範囲、「SQL 全文・業務理由（要件既出）・基本設計で確定済みの機能スコープ／論理 ER の再記述」を含まない範囲と定める。

**境界を越えた記述の扱い**:
- 物理 ER 節に業務上の理由（要件既出の Why）が混入していたら削除する（P2: 要件は What/Why、How は原則排除。重複は同期リスク）。
- 論理レベルの記述（エンティティ定義・正規化判断そのもの）は基本設計レシピへ戻す。

---

## 物理ER

**含む**: テーブル名・カラム名（物理名）・データ型・NULL 可否・PK・FK・代表的なインデックス設計。

**含まない**: 業務上の理由（要件定義で既出の Why は再掲しない。P2: 要件は What/Why、How は原則排除、かつ重複は同期リスク）。
> 業務背景は SRS に一元管理し、物理 ER はあくまで「どう実装するか」の記述に徹する。

### 例（最小限・テンプレート用）

```
テーブル: orders（受注）
  PK: order_id   BIGSERIAL    NOT NULL
      customer_id BIGINT      NOT NULL  FK → customers.customer_id
      ordered_at  TIMESTAMPTZ NOT NULL
      status      VARCHAR(20) NOT NULL  CHECK (status IN ('pending','confirmed','shipped','cancelled'))

テーブル: order_items（受注明細）
  PK: item_id    BIGSERIAL    NOT NULL
      order_id   BIGINT       NOT NULL  FK → orders.order_id
      product_id BIGINT       NOT NULL  FK → products.product_id
      quantity   INTEGER      NOT NULL  CHECK (quantity >= 1)
      unit_price NUMERIC(12,2) NOT NULL
```

---

## テーブル定義

各テーブルについて、以下の項目を1テーブル1ブロックで記述する。

| 項目 | 記述内容 |
|---|---|
| テーブル論理名・物理名 | 両方を記載 |
| 目的（1〜2文） | このテーブルが何を表すか |
| カラム一覧 | カラム名・型・NOT NULL・デフォルト・備考 |
| PK | 主キー定義 |
| FK | 参照先テーブル・カラム |
| 業務ルール | このテーブル固有の制約・不変条件 |

**SQL 全文はここには書かない**。DDL が必要な場合は制約とインデックス節に `sql` フェンスブロックで記述する。

### 例（最小限・テンプレート用）

**受注（orders）**

| カラム | 型 | NOT NULL | デフォルト | 備考 |
|---|---|---|---|---|
| order_id | BIGSERIAL | YES | — | サロゲートキー |
| customer_id | BIGINT | YES | — | FK: customers |
| ordered_at | TIMESTAMPTZ | YES | NOW() | 注文日時（UTC） |
| status | VARCHAR(20) | YES | 'pending' | 列挙値は制約で定義 |

業務ルール:
- `status` が `cancelled` に遷移した後は変更不可（アプリ層で制御）。
- キャンセル済み受注の明細は物理削除しない（履歴保持要件由来）。

---

## 制約とインデックス

制約の命名規約・インデックス設計の方針・SQL の置き場所を定める節。

**命名規約（プロジェクト固有値に置換すること）**:
- PK: `{テーブル名}_pkey`
- FK: `{テーブル名}_{参照テーブル名}_fkey`
- UNIQUE: `{テーブル名}_{カラム名(s)}_key`
- CHECK: `{テーブル名}_{制約内容略称}_check`

**インデックス設計の基準**:
- FK カラムには原則インデックスを作成する（JOIN コスト低減）。
- 検索頻度・選択性・更新頻度を根拠として記載する（P4: 設計根拠は必須）。
- 複合インデックスのカラム順は「等値条件→範囲条件→ORDER BY カラム」を基準とする。
- 厳密な index 種別・パラメータ（btree/hash・fillfactor 等）はこの詳細設計工程で確定する（P5: 厳密値は詳細設計工程のマーカーである）。

**SQL は必ずフェンスブロック内に記述する**（語彙チェッカーがコードブロック内の SQL を対象外とするため）。

### 例（最小限・テンプレート用）

```sql
-- 受注テーブル: status の検索頻度が高い（一覧画面のフィルタ条件）
CREATE INDEX orders_status_idx ON orders USING btree (status);

-- 受注明細テーブル: order_id FK + 正引き JOIN が主要アクセスパターン
CREATE INDEX order_items_order_id_idx ON order_items (order_id);

-- 顧客×注文日時の複合（管理画面の顧客別注文履歴一覧）
CREATE INDEX orders_customer_ordered_idx ON orders (customer_id, ordered_at DESC);
```

---

## トレーサビリティ

各テーブル（物理名）を要件 ID に紐付ける。孤立したテーブル（要件の根拠のない設計要素）を作らない。基本設計の論理 ER トレースを物理テーブル粒度へ展開したものであり、論理エンティティ→物理テーブルの対応も明示する。
> P4: 設計は要件へ全要素トレース可能でなければならない。孤立した設計要素はスコープクリープの検出点になる。

**表の書き方**:
- 要件 ID は SRS の章番号・ユースケース番号・機能要件 ID のいずれかを統一して使う。
- 1テーブルが複数要件に対応する場合はカンマ区切りで列挙する。
- 要件に紐付かないテーブル（ログ・監査等の横断的テーブル）は「横断」と記載し、対応する NFR の ID を付ける。

| テーブル（物理名） | テーブル（論理名） | 対応要件 ID | 備考 |
|---|---|---|---|
| customers | 顧客 | UC-01, FR-03 | 顧客登録・検索要件 |
| orders | 受注 | UC-02, FR-05, FR-06 | 受注登録・ステータス管理要件 |
| order_items | 受注明細 | UC-02, FR-05 | 受注明細の数量・金額要件 |
| products | 商品 | UC-03, FR-08 | 商品マスタ管理要件 |
| audit_logs | 監査ログ | NFR-SEC-02 | 横断的なセキュリティ要件（操作ログ） |

**逸脱の判定基準**:
- 「対応要件 ID」が空のテーブルが存在する → 孤立設計要素（スコープクリープ候補）。要件への追記または削除を検討する。
- テーブルが要件に存在しない機能を実現している → 要件定義工程へのフィードバックが必要。
