#!/usr/bin/env python3
"""doc-standards 機械判定: 必須見出しスキーマの欠落検出。

使い方: python3 check_headings.py <markdown_path> <doc_type>
fail-open: スキーマ未定義・読み込み不能なら status=skipped で exit 0（判定対象外）。
逸脱（必須見出し欠落）検出時のみ exit 1。検出は報告し、ブロックは利用側判断。
"""
import json
import re
import sys
from pathlib import Path

SCHEMA_DIR = Path(__file__).resolve().parent / "schema"
# 既知の制限: コードフェンス(```)内の # 行も見出しとして拾う。
# 方向は安全側（欠落を存在に見せうるだけ＝より fail-open、誤ブロックは生まない）。
HEADING_RE = re.compile(r'^#{1,6}\s+(.+?)\s*$', re.MULTILINE)


def extract_headings(md_text):
    """markdown の見出しテキストを行単位（セグメント）で抽出する。"""
    return [m.group(1).strip() for m in HEADING_RE.finditer(md_text)]


def load_schema(doc_type):
    """doc_type の必須見出しスキーマを読む。無ければ None（fail-open のトリガ）。"""
    path = SCHEMA_DIR / f"{doc_type}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def find_missing(headings, required):
    """required 各項目が見出し集合に部分一致するか。欠落リストを返す（境界=見出し行単位・大小無視）。

    部分一致（req.lower() in h）は意図的: 「論理ER（エンティティ関連）」のように
    スキーマ要求「論理ER」をサフィックス付き見出しが満たせるようにするため。
    注意: スキーマの required 名は十分に具体的であること。「ER」のように短い曖昧な
    要求名は無関係な別見出しに誤マッチするリスクがある。
    """
    norm = [h.lower() for h in headings]
    return [req for req in required if not any(req.lower() in h for h in norm)]


def check(md_path, doc_type):
    try:
        schema = load_schema(doc_type)
    except json.JSONDecodeError as e:
        # スキーマ JSON が壊れていても crash させない（fail-open）
        return {"doc_type": doc_type, "status": "skipped",
                "reason": f"invalid schema json: {e} (fail-open)", "missing": []}
    if schema is None:
        return {"doc_type": doc_type, "status": "skipped",
                "reason": "no schema (fail-open)", "missing": []}
    try:
        text = Path(md_path).read_text(encoding="utf-8")
    except OSError as e:
        return {"doc_type": doc_type, "status": "skipped",
                "reason": f"read error: {e} (fail-open)", "missing": []}
    missing = find_missing(extract_headings(text), schema.get("required_headings", []))
    return {"doc_type": doc_type, "status": "deviation" if missing else "pass",
            "missing": missing}


def main(argv):
    if len(argv) != 3:
        print("usage: check_headings.py <markdown_path> <doc_type>", file=sys.stderr)
        return 0  # 使い方ミスは fail-open
    result = check(argv[1], argv[2])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "deviation" else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
