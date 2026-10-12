# データ設計書（詳細設計・物理）

## 目的とスコープ

本書はユーザー管理システムの物理データ設計を定義する。

## テーブル定義

**ユーザー（users）**

| カラム | 型 | NOT NULL |
|---|---|---|
| user_id | BIGSERIAL | YES |
| email | VARCHAR(255) | YES |

## 制約とインデックス

FK カラムには原則インデックスを作成する。

```sql
CREATE INDEX orders_user_id_idx ON orders USING btree (user_id);
```

## トレーサビリティ

各テーブル（物理名）を要件 ID に紐付ける。

| テーブル（物理名） | 対応要件 ID |
|---|---|
| users | UC-01 |
