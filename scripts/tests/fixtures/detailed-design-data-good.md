# データ設計書（詳細設計・物理）

## 目的とスコープ

本書はユーザー管理システムの物理データ設計を定義する。基本設計の論理 ER を受けて物理に展開する。

## 物理ER

物理テーブルとカラム（物理名）・データ型・NULL 可否・PK・FK・代表インデックスを定義する。

```
テーブル: users（ユーザー）
  PK: user_id    BIGSERIAL    NOT NULL
      email      VARCHAR(255) NOT NULL  UNIQUE
      created_at TIMESTAMPTZ  NOT NULL

テーブル: orders（受注）
  PK: order_id   BIGSERIAL    NOT NULL
      user_id    BIGINT       NOT NULL  FK → users.user_id
```

## テーブル定義

**ユーザー（users）**

| カラム | 型 | NOT NULL | デフォルト | 備考 |
|---|---|---|---|---|
| user_id | BIGSERIAL | YES | — | サロゲートキー |
| email | VARCHAR(255) | YES | — | ログイン ID |
| created_at | TIMESTAMPTZ | YES | NOW() | 登録日時（UTC） |

## 制約とインデックス

インデックス設計の方針: FK カラムには原則インデックスを作成する。
厳密な index 種別は本工程で確定する。検索頻度の高いカラムには btree インデックスを採用する。

```sql
CREATE INDEX orders_user_id_idx ON orders USING btree (user_id);
```

## トレーサビリティ

各テーブル（物理名）を要件 ID に紐付ける。

| テーブル（物理名） | テーブル（論理名） | 対応要件 ID |
|---|---|---|
| users | ユーザー | UC-01, FR-03 |
| orders | 受注 | UC-02, FR-05 |
