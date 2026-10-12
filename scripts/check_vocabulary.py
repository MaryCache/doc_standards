#!/usr/bin/env python3
"""doc-standards 機械判定: 禁止語彙の散在検出。

使い方: python3 check_vocabulary.py <markdown_path> <doc_type>
fail-open: 語彙定義未存在・不正 JSON・ファイル読み込み不能 → status=skipped で exit 0。
逸脱（禁止語検出）時のみ exit 1。検出は報告し、ブロックは利用側判断。
検査はコードフェンス(``` ... ```)除去後の散文に限定（安全代替除外）。
"""
import json
import re
import sys
from pathlib import Path

VOCAB_DIR = Path(__file__).resolve().parent / "vocab"

# コードフェンス除去用。DOTALL で複数行対応。
# 既知の限界: 未閉鎖フェンス・`~~~` チルダフェンス・インライン単一バッククォート・
# 4スペースインデントのコードブロックは除去対象外。
# data-design 文書はバッククォート三連(```)を規約とする前提で十分（check_headings.py の
# 既知制限コメントと同パリティ）。
_FENCE_RE = re.compile(r'```.*?```', re.DOTALL)


def strip_code_blocks(md_text):
    """markdown テキストからコードフェンス(``` ... ```)で囲まれたブロックを除去する。

    SQLやDDL例を検査から除外するための前処理。
    """
    return _FENCE_RE.sub('', md_text)


def load_vocab(doc_type):
    """doc_type の禁止語彙定義を読む。ファイル不在なら None（fail-open のトリガ）。

    JSONDecodeError は呼び出し元の check() でキャッチする（fail-open）。
    """
    path = VOCAB_DIR / f"{doc_type}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def find_hits(prose, forbidden):
    """prose 中に forbidden 各語が部分一致するか検査し、ヒット一覧を返す。

    部分一致（term.lower() in prose.lower()）は意図的: 「btree」のような
    技術用語は語境界をまたいで表記されることがあり、厳密な単語境界マッチより
    再現率を優先する。誤検知リスクはスキーマ側の用語設計（十分に具体的な語）
    で制御する（check_headings.py の substring 判断と同方針）。

    fail-open: dict でないエントリ・"term" キー欠落エントリは無視する（TypeError/KeyError
    を抑止。スキーマ不正でも crash させない）。"reason" 欠落時は空文字で補完。
    """
    lower_prose = prose.lower()
    hits = []
    for entry in forbidden:
        # dict でない要素（文字列等）はスキーマ不正として無視する（fail-open）
        if not isinstance(entry, dict):
            continue
        term = entry.get("term")
        # "term" キーが無いエントリも無視する（スキーマ不正）
        if term is None:
            continue
        if term.lower() in lower_prose:
            # "reason" 欠落は空文字で補完する（crash より報告を優先）
            hits.append({"term": term, "reason": entry.get("reason", "")})
    return hits


def check(md_path, doc_type):
    """md_path を doc_type の禁止語彙で検査し、結果辞書を返す。

    total fail-open: vocab 未定義・JSON 破損・ファイル読み込み不能のいずれでも
    status=skipped を返す（exit 0）。逸脱のみ status=deviation（exit 1）。
    """
    try:
        vocab = load_vocab(doc_type)
    except json.JSONDecodeError as e:
        # 語彙 JSON が壊れていても crash させない（fail-open）
        return {"doc_type": doc_type, "status": "skipped",
                "reason": f"invalid vocab json: {e} (fail-open)", "hits": []}
    if vocab is None:
        return {"doc_type": doc_type, "status": "skipped",
                "reason": "no vocab definition (fail-open)", "hits": []}
    try:
        text = Path(md_path).read_text(encoding="utf-8")
    except OSError as e:
        return {"doc_type": doc_type, "status": "skipped",
                "reason": f"read error: {e} (fail-open)", "hits": []}

    # コードフェンス内の語は検査対象外（安全代替除外）
    prose = strip_code_blocks(text)
    hits = find_hits(prose, vocab.get("forbidden", []))
    return {"doc_type": doc_type, "status": "deviation" if hits else "pass",
            "hits": hits}


def main(argv):
    """CLI エントリポイント。逸脱で exit 1、それ以外（pass / skipped / 引数誤り）で exit 0。"""
    if len(argv) != 3:
        print("usage: check_vocabulary.py <markdown_path> <doc_type>", file=sys.stderr)
        return 0  # 使い方ミスは fail-open
    result = check(argv[1], argv[2])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "deviation" else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
