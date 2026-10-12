#!/usr/bin/env python3
"""doc-standards 機械判定: トレーサビリティ表の空セル（孤立設計要素）検出。

使い方: python3 check_traceability.py <markdown_path> <doc_type>

F5（cycle-10 レビュー検出）対応の3つ目の決定論チェッカー。全 rubric が
「トレーサビリティ表の空セル検出は機械の担当」と書くのに、既存2チェッカー
（check_headings＝見出し部分一致／check_vocabulary＝禁止語部分一致）には表解析が
無く、対応要件 ID が空欄の孤立設計要素（スコープクリープ候補・P4 違反）がどの層でも
未検出の穴になっていた。本チェッカーが「対応要件 ID 列が空の行」を決定論で検出し、
rubric の主張を真にする。

fail-open 厳守: 判定できない構造（トレーサビリティ節なし／表なし／ID 列を一意同定
不可）は deviation でなく status=skipped で exit 0 に倒す。「機械判定の対象外」を
握りつぶさず明示するため。逸脱（空セル＝孤立設計要素）検出時のみ exit 1。検出は
報告し、ブロックは利用側判断。stdlib のみ（json/re/sys/pathlib）。

既存 check_headings.py / check_vocabulary.py は変更しない（新規ファイル追加のみ）。
共通の strip_code_blocks は import でなくコピーした。理由: 既存スクリプトを import
すると check_vocabulary を実行依存に巻き込み（壊すリスク）、かつ実装はワンライナ
正規表現で重複コストが小さいため、独立性（既存を壊さない）を優先した。
"""
import json
import re
import sys
from pathlib import Path

# コードフェンス除去用。DOTALL で複数行対応。check_vocabulary.py と同パリティ。
# 既知の限界: 未閉鎖フェンス・`~~~` チルダフェンス・4スペースインデントブロックは
# 除去対象外。トレーサビリティ表は ``` 三連フェンスを規約とする前提で十分。
_FENCE_RE = re.compile(r'```.*?```', re.DOTALL)

# `## ` レベル以上（H1〜H6）の見出し行を捉える。トレーサビリティ節範囲の境界判定に使う。
_HEADING_RE = re.compile(r'^(#{1,6})\s+(.+?)\s*$')

# markdown 表の区切り行（`|---|---|` / `| :--- | ---: |` 等）。ヘッダ直下のこの行で
# 表の開始を確定する。セルは空白とハイフン・コロンのみで構成される。
_SEPARATOR_RE = re.compile(r'^\s*\|?[\s:|-]+\|[\s:|-]*$')

# 空欄（=孤立）とみなす「無し」記号の集合。各種ダッシュ（ハイフン/全角長音/em ダッシュ/
# 全角ハイフンマイナス/半角カナ長音）とスラッシュ・N/A。「横断」等の記入済みは含めない。
# 大小無視で比較するため小文字で持つ。
_EMPTY_TOKENS = {"", "-", "—", "ー", "/", "n/a", "ｰ", "－", "‐", "–"}


def strip_code_blocks(md_text):
    """markdown テキストからコードフェンス(``` ... ```)で囲まれたブロックを除去する。

    フェンス内の「表の書き方」例表を検査から除外するための前処理（既存チェッカーと
    同じ誤検知回避）。地の文の実トレーサビリティ表だけを対象にする。
    """
    return _FENCE_RE.sub('', md_text)


def find_traceability_section(md_text):
    """「トレーサビリティ」を含む `## ` 見出しから次の同レベル以上の見出しまでを返す。

    見出しテキストの部分一致は check_headings.py の find_missing と同じ寛容さ。節範囲は
    「見出し行の次行」から「次に現れる同レベル以下（=同じか浅い階層）の見出しの直前」
    まで。節が無ければ None を返す（fail-open のトリガ＝user-story 等はここで skipped）。

    返り値: (lines, start_lineno) の組。lines は節内の行リスト、start_lineno は節内
    先頭行の元テキスト上の1始まり行番号（orphans の行番号目安に使う）。
    """
    lines = md_text.split("\n")
    section_level = None
    start_idx = None
    for i, line in enumerate(lines):
        m = _HEADING_RE.match(line)
        if m is None:
            continue
        level = len(m.group(1))
        title = m.group(2)
        if section_level is None:
            # まだ節に入っていない: トレーサビリティ見出しを探す
            if "トレーサビリティ" in title:
                section_level = level
                start_idx = i + 1  # 見出し行の次行から節本体
        else:
            # 節に入っている: 同レベル以上（浅いか同じ）の見出しで節終了
            if level <= section_level:
                return lines[start_idx:i], start_idx + 1  # 1始まり行番号
    if section_level is None:
        return None
    # 節が文書末尾まで続く場合
    return lines[start_idx:], start_idx + 1


def extract_tables(section_lines):
    """節内の markdown 表を抽出して [(header_cells, rows)] のリストで返す。

    表の検出規約（既存チェッカーと整合的にシンプルに保つ）:
      - 「`|` を含む行」+「直後が区切り行（`|---|---|`）」のペアで表開始を確定する。
      - 以降 `|` を含む連続行をデータ行として取り込み、`|` を含まない行で表終了。
    rows の各要素は (cells, lineno) の組。lineno は section_lines 内での1始まりオフセット
    （呼び出し側が節先頭行番号を足して元テキスト行番号に直す）。
    header_cells / cells はパイプで分割しトリムしたセル文字列のリスト。
    """
    tables = []
    n = len(section_lines)
    i = 0
    while i < n:
        line = section_lines[i]
        # ヘッダ候補: パイプを含む行で、次行が区切り行
        if "|" in line and i + 1 < n and _SEPARATOR_RE.match(section_lines[i + 1]):
            header = _split_row(line)
            rows = []
            j = i + 2  # 区切り行の次からデータ行
            while j < n and "|" in section_lines[j]:
                # 区切り行が表の途中に再出現することは想定しないが、出たらデータ扱いせず終了
                if _SEPARATOR_RE.match(section_lines[j]):
                    break
                rows.append((_split_row(section_lines[j]), j + 1))  # 1始まりオフセット
                j += 1
            tables.append((header, rows))
            i = j
        else:
            i += 1
    return tables


def _split_row(line):
    """markdown 表の1行をセル文字列のリストに分割する（前後の空パイプを除く）。

    `| a | b |` → ["a", "b"]。先頭/末尾の `|` による空要素は落とし、各セルは trim する。
    """
    parts = line.split("|")
    # 先頭・末尾の `|` 由来の空要素を除く（行頭/行末がパイプの一般的な書式）
    if parts and parts[0].strip() == "":
        parts = parts[1:]
    if parts and parts[-1].strip() == "":
        parts = parts[:-1]
    return [p.strip() for p in parts]


def select_id_column(header):
    """ヘッダ行から「対応要件 ID（トレース対象）」列のインデックスを選ぶ。

    ヒューリスティック（誤爆回避 = fail-open のため厳格に絞る）:
      1. 第1列は常に設計要素名（主語: 画面名/エンティティ/ケース ID/要件 ID/アーキ判断/
         本書の NFR/本書の方針）であり ID 列にしない。実レシピ9種すべてで第1列は主語。
      2. 第2列以降で、ヘッダに「対応」を含む列を最優先で選ぶ。これは external/architecture/
         nonfunctional/operations/data-design（基本・詳細）/test-case-spec 主表の
         トレース列見出し（対応要件 ID／対応要件・NFR ID／対応 SRS NFR ID／要件 ID／
         対応要件 ID／NFR ID）すべてを覆う。
      3. 「対応」列が無ければ「上位要求」を含む列を選ぶ。これは srs のトレース列
         「上位要求 ID」を覆う（srs は第1列が「要件 ID」＝主語で罠になるため、ここで
         第1列を除外していることが効く）。
      4. いずれも無ければ None を返す（同定不可＝skipped）。test-case-spec の逆引き表
         （要件 ID｜検証するケース ID｜カバレッジ）は「対応」「上位要求」を含まないため
         ここで弾かれ、「（なし）」を空セルと誤認しない（S-1 false-positive 回避）。

    複数候補があれば最初に見つかった「対応」列を採る（実レシピでは対応列は高々1つ）。
    """
    # 第1列（主語）は除外して 1 以降を走査する（不変条件: 設計要素名は ID 列でない）
    for idx in range(1, len(header)):
        if "対応" in header[idx]:
            return idx
    for idx in range(1, len(header)):
        if "上位要求" in header[idx]:
            return idx
    return None


def is_empty_cell(cell):
    """セル文字列が空欄（=孤立設計要素）かを判定する。

    空・空白のみ・各種ダッシュ/「無し」記号（- — ー / N/A 等）を空欄とみなす。
    「横断」「横断 NFR-USE-01」のような記入済みはトレース済みであり空欄でない
    （レシピの横断運用を孤立と誤検出しないため）。比較は trim + 小文字化。
    """
    return cell.strip().lower() in _EMPTY_TOKENS


def find_orphans(tables, section_start_lineno):
    """表群から孤立設計要素（ID 列が空セルの行）を抽出する。

    各表でヘッダから ID 列を同定し、同定できた表のデータ行を走査する。ID 列のセルが
    空欄なら孤立設計要素として element（第1列＝設計要素名）と line（元テキスト1始まり
    行番号目安）を記録する。第1列だけを見出し継続等で空にした行の誤爆を避けるため、
    判定は ID 列セルのみで行う（第1列の空は無視）。

    返り値: (orphans, identified) の組。
      orphans: [{"element": str, "line": int}]
      identified: ID 列を同定できた表が1つでもあれば True（False なら呼び出し側で skipped）
    """
    orphans = []
    identified = False
    for header, rows in tables:
        id_col = select_id_column(header)
        if id_col is None:
            continue  # ID 列を同定できない表は対象外（fail-open）
        identified = True
        for cells, offset in rows:
            # 列数が ID 列に満たない不揃い行は判定不能としてスキップ（誤爆回避）
            if id_col >= len(cells):
                continue
            if is_empty_cell(cells[id_col]):
                # 第1列を設計要素名として記録（無ければ空文字）
                element = cells[0] if cells else ""
                orphans.append({
                    "element": element,
                    "line": section_start_lineno + offset - 1,
                })
    return orphans, identified


def check(md_path, doc_type):
    """md_path のトレーサビリティ表を検査し、結果辞書を返す。

    total fail-open: ファイル読み込み不能・節なし・表なし・ID 列同定不可のいずれでも
    status=skipped を返す（exit 0）。孤立設計要素（空セル）検出時のみ status=deviation
    （exit 1）。それ以外は pass。
    """
    try:
        text = Path(md_path).read_text(encoding="utf-8")
    except OSError as e:
        return {"doc_type": doc_type, "status": "skipped",
                "reason": f"read error: {e} (fail-open)", "orphans": []}

    # フェンス内の例表は検査対象外（地の文の実表のみ対象）
    prose = strip_code_blocks(text)

    section = find_traceability_section(prose)
    if section is None:
        return {"doc_type": doc_type, "status": "skipped",
                "reason": "no traceability section (fail-open)", "orphans": []}
    section_lines, section_start_lineno = section

    tables = extract_tables(section_lines)
    if not tables:
        return {"doc_type": doc_type, "status": "skipped",
                "reason": "no table in traceability section (fail-open)", "orphans": []}

    orphans, identified = find_orphans(tables, section_start_lineno)
    if not identified:
        return {"doc_type": doc_type, "status": "skipped",
                "reason": "id column not identifiable (fail-open)", "orphans": []}

    return {"doc_type": doc_type,
            "status": "deviation" if orphans else "pass",
            "orphans": orphans}


def main(argv):
    """CLI エントリポイント。逸脱で exit 1、それ以外（pass / skipped / 引数誤り）で exit 0。"""
    if len(argv) != 3:
        print("usage: check_traceability.py <markdown_path> <doc_type>", file=sys.stderr)
        return 0  # 使い方ミスは fail-open
    result = check(argv[1], argv[2])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "deviation" else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
