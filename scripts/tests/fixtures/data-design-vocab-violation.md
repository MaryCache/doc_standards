# データ設計書

## 目的とスコープ

本書はユーザー管理システムの論理データ設計を定義する。

## 論理ER

ユーザーと注文のエンティティ関係を定義する。論理設計の段階で btree インデックスを張る。
なぜなら業務上の都合でこのカラムを追加する。

```sql
CREATE TABLE users (
  id   SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL
);
```

## トレーサビリティ

各エンティティは要件定義書の機能要件F-01〜F-05に対応する。
