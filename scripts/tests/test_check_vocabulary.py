from pathlib import Path
import check_vocabulary as cv

FIX = Path(__file__).parent / "fixtures"

def test_strip_code_blocks_removes_fenced():
    text = "a\n```\nCREATE TABLE x (id int);\n```\nb"
    assert "CREATE TABLE" not in cv.strip_code_blocks(text)
    assert "a" in cv.strip_code_blocks(text)

def test_good_has_no_violations():
    result = cv.check(str(FIX / "data-design-good.md"), "data-design")
    assert result["status"] == "pass"
    assert result["hits"] == []

def test_violation_detected_outside_code():
    result = cv.check(str(FIX / "data-design-vocab-violation.md"), "data-design")
    assert result["status"] == "deviation"
    terms = [h["term"] for h in result["hits"]]
    assert "btree" in terms

def test_sql_in_code_block_not_flagged():
    result = cv.check(str(FIX / "data-design-vocab-violation.md"), "data-design")
    terms = [t.lower() for t in [h["term"] for h in result["hits"]]]
    assert "create table" not in terms

def test_failopen_when_vocab_absent():
    result = cv.check(str(FIX / "data-design-good.md"), "no-such-type")
    assert result["status"] == "skipped"

def test_failopen_on_malformed_vocab(tmp_path, monkeypatch):
    bad = tmp_path / "broken.json"
    bad.write_text("{ not valid json", encoding="utf-8")
    monkeypatch.setattr(cv, "VOCAB_DIR", tmp_path)
    result = cv.check(str(FIX / "data-design-good.md"), "broken")
    assert result["status"] == "skipped"


def test_find_hits_entry_missing_reason_does_not_crash(tmp_path, monkeypatch):
    """reason キーが欠落した forbidden エントリでも crash せず結果を返すこと。

    find_hits が entry["reason"] を直接参照するため、欠落時に KeyError が発生する
    バグを回帰防止する。reason 欠落時は空文字で補完し、ヒット自体は正常に返す。
    """
    vocab = tmp_path / "mytype.json"
    # reason キーを意図的に省いた不正エントリ
    vocab.write_text('{"forbidden":[{"term":"btree"}]}', encoding="utf-8")
    monkeypatch.setattr(cv, "VOCAB_DIR", tmp_path)

    md = tmp_path / "doc.md"
    md.write_text("btree インデックスを使う", encoding="utf-8")

    # crash せず結果が返ること（status は pass/deviation どちらでもよい、KeyError は禁止）
    result = cv.check(str(md), "mytype")
    assert result["status"] in ("pass", "deviation")


def test_find_hits_non_dict_entry_is_skipped(tmp_path, monkeypatch):
    """forbidden リストに文字列（dict でない）要素があっても crash せず無視されること。

    find_hits が entry["term"] を直接参照するため、文字列要素では TypeError が発生する
    バグを回帰防止する。不正エントリはスキップし、正常エントリのみ処理する。
    """
    vocab = tmp_path / "mytype.json"
    # 文字列要素（dict でない）を混在させた不正リスト
    vocab.write_text('{"forbidden":["btree"]}', encoding="utf-8")
    monkeypatch.setattr(cv, "VOCAB_DIR", tmp_path)

    md = tmp_path / "doc.md"
    md.write_text("btree インデックスを使う", encoding="utf-8")

    # crash せず、不正エントリは無視されること（status は pass になる）
    result = cv.check(str(md), "mytype")
    assert result["status"] != "deviation"  # 不正エントリが無視されたので deviation にならない
    assert result["hits"] == []


# --- detailed-design-data（詳細設計・物理データ設計）スライス ---
# 禁止語 = 「なぜなら業務」のみ。btree は詳細設計では正当な物理 index 種別なので
# 禁止語にしない（data-design とは逆方向）。

def test_dd_good_has_no_violations():
    result = cv.check(str(FIX / "detailed-design-data-good.md"), "detailed-design-data")
    assert result["status"] == "pass"
    assert result["hits"] == []

def test_dd_violation_detected_outside_code():
    result = cv.check(str(FIX / "detailed-design-data-vocab-violation.md"),
                      "detailed-design-data")
    assert result["status"] == "deviation"
    terms = [h["term"] for h in result["hits"]]
    assert "なぜなら業務" in terms

def test_dd_btree_in_prose_not_flagged():
    """btree は詳細設計の物理 index 種別として正当なので、地の文にあっても検出しない。

    violation fixture は「制約とインデックス」節の地の文（コードフェンス外）に btree を
    含む。data-design では btree は禁止語だが detailed-design-data では検出されないこと
    （逆方向の差）を回帰防止する。
    """
    result = cv.check(str(FIX / "detailed-design-data-vocab-violation.md"),
                      "detailed-design-data")
    terms = [t.lower() for t in [h["term"] for h in result["hits"]]]
    assert "btree" not in terms
    # good fixture（地の文に btree を含む）でも btree は検出されない＝ status=pass
    good = cv.check(str(FIX / "detailed-design-data-good.md"), "detailed-design-data")
    assert good["status"] == "pass"


# --- srs（要件定義・SRS）スライス ---
# 禁止語 = 設計構造マーカー4語（クラス図 / テーブル定義 / モジュール分割 / インデックス）。
# 要件に設計の解（How）が先取りされた検出点。技術スタック名（PostgreSQL/JWT/REST 等）は
# 禁止語にしない（正当な制約として根拠付きで現れうるため＝fail-open で人間棄却）。

def test_srs_good_has_no_violations():
    result = cv.check(str(FIX / "srs-good.md"), "srs")
    assert result["status"] == "pass"
    assert result["hits"] == []

def test_srs_violation_detected_outside_code():
    # violation fixture は機能要件節の地の文に テーブル定義・クラス図 を1つずつ含む
    result = cv.check(str(FIX / "srs-vocab-violation.md"), "srs")
    assert result["status"] == "deviation"
    terms = [h["term"] for h in result["hits"]]
    assert "テーブル定義" in terms
    assert "クラス図" in terms

def test_srs_marker_in_code_block_not_flagged():
    """フェンス内の設計構造マーカー（モジュール分割・インデックス）は検出しないこと。

    violation fixture はフェンス内に「モジュール分割」「インデックス」を置く。これらは
    レシピの越境 note と同様に列挙目的でフェンスに入っており、検査対象外（安全代替除外）
    であることを回帰防止する。地の文に出た テーブル定義・クラス図 のみが検出される。
    """
    result = cv.check(str(FIX / "srs-vocab-violation.md"), "srs")
    terms = [h["term"] for h in result["hits"]]
    assert "モジュール分割" not in terms
    assert "インデックス" not in terms


# --- test-case-spec（テスト・ケース仕様）スライス ---
# 禁止語 = 期待結果の曖昧表現マーカー3語（正しく表示 / 正しく動作 / 適切に処理）。
# 測定不能な期待結果＝検証可能でない記述の検出点（P6: 期待結果は測定可能/観測可能に書く）。
# 観測できる値・状態・コード・件数・しきい値比較で書けば検出されない（言い換えで回避）。

def test_tcs_good_has_no_violations():
    result = cv.check(str(FIX / "test-case-spec-good.md"), "test-case-spec")
    assert result["status"] == "pass"
    assert result["hits"] == []

def test_tcs_violation_detected_outside_code():
    # violation fixture はテストケース節の地の文に 正しく表示・適切に処理 を1つずつ含む
    result = cv.check(str(FIX / "test-case-spec-vocab-violation.md"), "test-case-spec")
    assert result["status"] == "deviation"
    terms = [h["term"] for h in result["hits"]]
    assert "正しく表示" in terms
    assert "適切に処理" in terms

def test_tcs_marker_in_code_block_not_flagged():
    """フェンス内の曖昧表現マーカー（正しく動作）は検出しないこと。

    violation fixture はフェンス内に「正しく動作」を列挙目的で置く。レシピの越境 note と
    同様にフェンス内は検査対象外（安全代替除外）であることを回帰防止する。地の文に出た
    正しく表示・適切に処理 のみが検出される。
    """
    result = cv.check(str(FIX / "test-case-spec-vocab-violation.md"), "test-case-spec")
    terms = [h["term"] for h in result["hits"]]
    assert "正しく動作" not in terms


# --- user-story（アジャイル・ユーザーストーリー）スライス ---
# vocab は空（forbidden:[]）＝設計上の判断。User Story の逸脱（主語=System / so that 欠落 /
# 実装動詞 / AC 件数 / INVEST）は構造・件数・文脈の判定で、特定の禁止トークンの部分一致では
# 拾えない（実装動詞は正当なユーザー目標と同一トークン・英語部分一致が誤爆）。質的判定は
# rubric/user-story.md に委ねる（S4 非対称・vocab を持つ WF スライスとの対比）。

def test_us_empty_vocab_returns_pass():
    """空 forbidden（[]）の vocab は status=pass を返す（skipped ではない）。

    これは意図的な挙動である。forbidden が空でも vocab ファイルは存在し JSON も正常なので
    skipped（ファイル不在/破損時のみ）にはならず、ヒット 0 件 → pass を返す。
    すなわち「禁止語の逸脱なし」という狭い主張を pass で表す。
    これは council Skeptic が実コードで確認した check() の挙動（hits=[] → pass）の回帰テストであり、
    user-story の vocab を意図的に空にした設計判断（S4）が機械上 pass として表れることを保証する。
    """
    result = cv.check(str(FIX / "user-story-good.md"), "user-story")
    assert result["status"] == "pass"
    assert result["hits"] == []


# --- acceptance-criteria（アジャイル・受入基準）スライス ---
# 禁止語 = 期待結果(Then)の曖昧表現マーカー3語（正しく表示 / 正しく動作 / 適切に処理）。
# user-story（vocab 空）と異なり vocab を持つ＝AC の Then の観測可能性は test-case-spec の
# 期待結果と同性質の P6 要請であり、3語は test-case-spec で部分一致誤爆なく機械検出できると
# 実証済みのため踏襲する。GWT 構造・Then への内部実装混入・件数・トレース質は rubric 主導
# （構造/文脈/件数判定ゆえ機械では拾えない）。技術名・SQL・GWT キーワードは誤爆ゆえ禁止語にしない。

def test_ac_good_has_no_violations():
    result = cv.check(str(FIX / "acceptance-criteria-good.md"), "acceptance-criteria")
    assert result["status"] == "pass"
    assert result["hits"] == []

def test_ac_violation_detected_outside_code():
    # violation fixture は受入シナリオ節の地の文(Then)に 正しく表示・適切に処理 を1つずつ含む
    result = cv.check(str(FIX / "acceptance-criteria-vocab-violation.md"), "acceptance-criteria")
    assert result["status"] == "deviation"
    terms = [h["term"] for h in result["hits"]]
    assert "正しく表示" in terms
    assert "適切に処理" in terms

def test_ac_marker_in_code_block_not_flagged():
    """フェンス内の曖昧表現マーカー（正しく動作）は検出しないこと。

    violation fixture はフェンス内に「正しく動作」を列挙目的で置く。レシピの越境 note と
    同様にフェンス内は検査対象外（安全代替除外）であることを回帰防止する。地の文に出た
    正しく表示・適切に処理 のみが検出される（test-case-spec スライスと同型）。
    """
    result = cv.check(str(FIX / "acceptance-criteria-vocab-violation.md"), "acceptance-criteria")
    terms = [h["term"] for h in result["hits"]]
    assert "正しく動作" not in terms


# --- external-design（ウォーターフォール基本設計・外部設計）スライス ---
# 禁止語 = 内部実装マーカー4語（クラス図 / シーケンス図 / インデックス / テーブル定義）。
# 外部観測仕様に内部実装が先取り混入した検出点（P2: 外部設計は外部観測仕様に限る）。
# SQL は技術名 PostgreSQL・NoSQL・MySQL・SQLite の部分文字列であり、部分一致チェッカーが
# 誤爆するため禁止語から意図的に除外する（cycle-8 で実機検出・architecture-design と同方針）。
# API語・技術スタック名・ピクセル/hexカラーは正当な外部設計記述になりうるため禁止語にせず
# rubric の質的観点に委ねる（P2 訂正・cycle-4 srs と同方針）。SQL クエリ/DB 操作文の混入も
# rubric/external-design.md の質的観点（内部仕様 leak）で判定する。

def test_ed_good_is_clean():
    result = cv.check(str(FIX / "external-design-good.md"), "external-design")
    assert result["status"] == "pass"
    assert result["hits"] == []

def test_ed_violation_detected():
    # violation fixture は地の文に クラス図・シーケンス図・インデックス を含む
    result = cv.check(str(FIX / "external-design-vocab-violation.md"), "external-design")
    assert result["status"] == "deviation"
    terms = [h["term"] for h in result["hits"]]
    # 地の文にある内部実装マーカーが検出されること
    assert "クラス図" in terms
    assert "シーケンス図" in terms
    assert "インデックス" in terms
    # テーブル定義は violation fixture ではコードフェンス内に置かれている＝
    # フェンス除外により hits に入らないことを external-design スライスでも明示（回帰ガード）。
    assert "テーブル定義" not in terms


def test_ed_tech_name_allowed():
    """技術名に SQL 部分文字列が含まれても external-design vocab では検出されないこと。

    vocab チェッカーは部分一致（substring）で判定する。「SQL」を禁止語にすると
    PostgreSQL・NoSQL・MySQL・SQLite 等の製品名がすべてヒットする（cycle-8 で実機確認）。
    外部設計では技術スタック名（例: 永続先の製品名）が正当な記述になりうるため、
    この誤爆を避けるため SQL は禁止語リストから除外する設計判断を下した
    （architecture-design と同方針）。SQL クエリ/DB 操作文の混入は
    rubric/external-design.md の質的観点（内部仕様 leak）で判定する。
    本テストはその決定の回帰防止として、技術名を含む散文を実 external-design vocab に
    かけても pass（ヒット 0 件）になることを保証する。
    """
    # 「PostgreSQL に保存する外部 API」は SQL を部分文字列として含む散文。実 vocab を読み込み、
    # その forbidden で SQL がヒットしない（＝禁止語から除外済み）ことを直接検証する。
    vocab = cv.load_vocab("external-design")
    hits = cv.find_hits("PostgreSQL に保存する外部 API", vocab["forbidden"])
    assert hits == [], f"技術名が誤検出された: {hits}"

def test_ed_index_forbidden_vs_detailed_allows():
    """「インデックス」は external-design では deviation だが detailed-design-data では pass。

    external-design vocab は「インデックス」を物理データ設計への越境として禁止する。
    一方 detailed-design-data vocab は「インデックス」を禁止しない（物理設計では正当）。
    この doc_type 別の非対称を回帰防止する。
    """
    # detailed-design-data は「インデックス」を禁止語として持たないことを前提とする。
    # もし detailed-design-data.json に「インデックス」が追加されたら、このテストの
    # 対比前提が崩れる（テスト冒頭のコメントで明示する）。
    prose_path = FIX / "external-design-vocab-violation.md"

    ed_result = cv.check(str(prose_path), "external-design")
    ed_terms = [h["term"] for h in ed_result["hits"]]
    assert "インデックス" in ed_terms, (
        "external-design で「インデックス」が検出されなかった（前提崩壊）"
    )

    dd_result = cv.check(str(prose_path), "detailed-design-data")
    dd_terms = [h["term"] for h in dd_result["hits"]]
    assert "インデックス" not in dd_terms, (
        "detailed-design-data で「インデックス」が検出された — "
        "detailed-design-data.json に禁止語が追加された可能性がある（対比前提の再確認が必要）"
    )


# --- architecture-design（ウォーターフォール基本設計・方式設計）スライス ---
# 禁止語 = 内部実装マーカー3語（クラス図 / メソッド仕様 / シーケンス図）のみ。
# SQL は技術名 PostgreSQL・NoSQL・MySQL・SQLite の部分文字列であり、
# 部分一致チェッカーが誤爆するため禁止語から意図的に除外する（cycle-8 で実機検出）。
# 技術スタック名・製品名・プロトコル名の適切さは rubric/architecture-design.md で質的に判定。

def test_ad_good_is_clean():
    result = cv.check(str(FIX / "architecture-design-good.md"), "architecture-design")
    assert result["status"] == "pass"
    assert result["hits"] == []


def test_ad_violation_detected():
    # violation fixture は地の文に クラス図・メソッド仕様・シーケンス図 を含む
    result = cv.check(str(FIX / "architecture-design-vocab-violation.md"), "architecture-design")
    assert result["status"] == "deviation"
    terms = [h["term"] for h in result["hits"]]
    assert "クラス図" in terms
    assert "メソッド仕様" in terms
    assert "シーケンス図" in terms


def test_ad_tech_name_allowed():
    """技術名に SQL 部分文字列が含まれても architecture-design vocab では検出されないこと。

    vocab チェッカーは部分一致（substring）で判定する。「SQL」を禁止語にすると
    PostgreSQL・NoSQL・MySQL・SQLite 等の製品名がすべてヒットする（cycle-8 で実機確認）。
    技術選定が方式設計の核である architecture-design では SQL 系製品名は正当な記述であり、
    この誤爆を避けるため SQL は禁止語リストに含めない設計判断を下した。
    本テストはその決定の回帰防止として、技術名を含む散文が pass を返すことを保証する。
    """
    # PostgreSQL・NoSQL どちらも SQL を部分文字列として含む
    prose = "永続化に PostgreSQL を採用、NoSQL は却下"
    hits = cv.find_hits(prose, [
        {"term": "クラス図", "reason": "内部設計"},
        {"term": "メソッド仕様", "reason": "内部設計"},
        {"term": "シーケンス図", "reason": "内部設計"},
    ])
    assert hits == [], f"技術名が誤検出された: {hits}"


def test_ad_method_spec_forbidden_vs_detailed_allows():
    """「メソッド仕様」は architecture-design では deviation だが detailed-design-data では pass。

    architecture-design vocab は「メソッド仕様」をコンポーネント内部の先取りとして禁止する。
    detailed-design-data vocab は「メソッド仕様」を禁止しない（内部設計では正当）。
    この doc_type 別の非対称を回帰防止する。
    前提確認: detailed-design-data.json の forbidden が「なぜなら業務」のみであることに依存する。
    もし detailed-design-data.json に「メソッド仕様」が追加されたら対比前提が崩れる。
    """
    prose_path = FIX / "architecture-design-vocab-violation.md"

    ad_result = cv.check(str(prose_path), "architecture-design")
    ad_terms = [h["term"] for h in ad_result["hits"]]
    assert "メソッド仕様" in ad_terms, (
        "architecture-design で「メソッド仕様」が検出されなかった（前提崩壊）"
    )

    dd_result = cv.check(str(prose_path), "detailed-design-data")
    dd_terms = [h["term"] for h in dd_result["hits"]]
    assert "メソッド仕様" not in dd_terms, (
        "detailed-design-data で「メソッド仕様」が検出された — "
        "detailed-design-data.json に禁止語が追加された可能性がある（対比前提の再確認が必要）"
    )


# --- nonfunctional-design（ウォーターフォール基本設計・非機能設計）スライス ---
# 禁止語 = 下流実装先取りマーカー2語（チューニング手順 / 計測スクリプト）。
# 非機能設計はターゲット値と測定方法（方針）まで・『どう実現するか』は詳細設計／運用設計へ
# という越境の検出点（P2）。responsibility-map「含まない＝チューニング手順／計測スクリプト」由来。
# 技術名・SQL は製品名 PostgreSQL/NoSQL/MySQL 等の部分文字列で誤爆するため禁止語にせず、
# 曖昧表現（高速に/安定して/十分な）も正当文脈と区別できず誤爆するため禁止語にせず、
# いずれも rubric/nonfunctional-design.md の質的観点に委ねる（cycle-8 と同方針）。

def test_nfd_good_is_clean():
    result = cv.check(str(FIX / "nonfunctional-design-good.md"), "nonfunctional-design")
    assert result["status"] == "pass"
    assert result["hits"] == []


def test_nfd_violation_detected():
    # violation fixture は地の文に チューニング手順 を含む（実現手段の先取り）
    result = cv.check(str(FIX / "nonfunctional-design-vocab-violation.md"), "nonfunctional-design")
    assert result["status"] == "deviation"
    terms = [h["term"] for h in result["hits"]]
    assert "チューニング手順" in terms
    # 計測スクリプト は violation fixture ではコードフェンス内に置かれている＝
    # フェンス除外により hits に入らないことを明示（回帰ガード）。
    assert "計測スクリプト" not in terms


def test_nfd_tech_name_allowed():
    """技術名に SQL 部分文字列が含まれても nonfunctional-design vocab では検出されないこと。

    vocab チェッカーは部分一致（substring）で判定する。「SQL」を禁止語にすると
    PostgreSQL・NoSQL・MySQL・SQLite 等の製品名がすべてヒットする（cycle-8 で実機確認）。
    非機能設計では測定対象環境の記述として技術スタック名・製品名が正当に現れるため、
    この誤爆を避けるため SQL は禁止語に含めない設計判断を下した（architecture/external と同方針）。
    本テストはその決定の回帰防止として、技術名を含む散文が実 vocab で pass を返すことを保証する。
    """
    # 「PostgreSQL の稼働を測定対象とする」は SQL を部分文字列として含む散文。実 vocab を読み込み、
    # その forbidden で SQL がヒットしない（＝禁止語に入れていない）ことを直接検証する。
    vocab = cv.load_vocab("nonfunctional-design")
    hits = cv.find_hits("PostgreSQL の稼働を測定対象とする。NoSQL は対象外", vocab["forbidden"])
    assert hits == [], f"技術名が誤検出された: {hits}"


# --- operations-design（ウォーターフォール基本設計・運用/移行設計）スライス ---
# 禁止語 = 下流実行先取りマーカー2語（手順書 / 移行スクリプト）。
# 運用・移行設計は方針・条件まで・『どう実行するか』は詳細設計／後続工程へ
# という越境の検出点（P2）。responsibility-map「含まない＝詳細な手順書／移行 SQL」由来。
# 「手順」単独は『運用手順の方針』『移行手順の方針』等の正当な方針記述で誤爆するため
# 成果物名『手順書』で絞る（"手順" 単独不採用＝S4 非対称・実機誤爆確認済み）。
# 技術名・SQL は製品名 PostgreSQL/NoSQL/MySQL 等の部分文字列で誤爆するため禁止語にせず、
# インフラ構成の詳細値・移行データ変換クエリ本文の全文混入も rubric/operations-design.md
# の質的観点に委ねる（cycle-8/9 と同方針）。

def test_od_good_is_clean():
    result = cv.check(str(FIX / "operations-design-good.md"), "operations-design")
    assert result["status"] == "pass"
    assert result["hits"] == []


def test_od_violation_detected():
    # violation fixture は地の文に 手順書 を含む（実行手段の先取り）
    result = cv.check(str(FIX / "operations-design-vocab-violation.md"), "operations-design")
    assert result["status"] == "deviation"
    terms = [h["term"] for h in result["hits"]]
    assert "手順書" in terms
    # 移行スクリプト は violation fixture ではコードフェンス内に置かれている＝
    # フェンス除外により hits に入らないことを明示（回帰ガード）。
    assert "移行スクリプト" not in terms


def test_od_tech_name_allowed():
    """技術名に SQL 部分文字列が含まれても operations-design vocab では検出されないこと。

    vocab チェッカーは部分一致（substring）で判定する。「SQL」を禁止語にすると
    PostgreSQL・NoSQL・MySQL・SQLite 等の製品名がすべてヒットする（cycle-8 で実機確認）。
    運用・移行設計では監視対象製品名・移行元/先の環境記述として技術スタック名が正当に
    現れるため、この誤爆を避けるため SQL は禁止語に含めない設計判断を下した
    （architecture/external/nonfunctional と同方針）。本テストはその決定の回帰防止として、
    技術名を含む散文が実 vocab で pass を返すことを保証する。
    """
    # 「PostgreSQL を監視対象とする。NoSQL は移行対象外」は SQL を部分文字列として含む散文。
    # 実 vocab を読み込み、その forbidden で SQL がヒットしないことを直接検証する。
    vocab = cv.load_vocab("operations-design")
    hits = cv.find_hits("PostgreSQL を監視対象とする。NoSQL は移行対象外", vocab["forbidden"])
    assert hits == [], f"技術名が誤検出された: {hits}"


def test_od_procedure_word_not_flagged():
    """「手順」単独は禁止語にしないため、『運用手順の方針』等の正当文で誤爆しないこと。

    『手順』を禁止語にすると『運用手順の方針』『移行手順の方針』等の正当な方針記述が
    すべてヒットする。成果物名『手順書』で絞る設計判断（S4 非対称）の回帰防止として、
    「手順」を含むが「手順書」を含まない正当な方針記述が pass になることを保証する。
    """
    vocab = cv.load_vocab("operations-design")
    # 「運用手順の方針を定める」は『手順』を含むが『手順書』は含まない正当な方針記述
    hits = cv.find_hits("運用手順の方針を定める。移行手順の方針も確定する", vocab["forbidden"])
    assert hits == [], f"汎用語『手順』が誤検出された: {hits}"


# --- design-doc（アジャイル・Design Doc）スライス ---
# vocab は空（forbidden:[]）＝設計上の判断（user-story と同型・acceptance-criteria とは非対称）。
# Design Doc の逸脱（全セクション強制記入/arc42 全12セクション埋め/C4 の L4 を最初から全描画/
# 自明な実装・バグ修正の過剰文書化/gold plating）は構造・量・文脈の判定で、特定の禁止トークンの
# 部分一致では原理的に拾えない。とりわけ『クラス図』を禁止語にすると C4/詳細設計への正当な委譲を
# 語る文で誤爆する。vocab の有無は『逸脱が機械で綺麗に拾えるか』で決まる（agile/WF の別ではない）。
# 質的判定は rubric/design-doc.md に委ねる（agile rubric 主導・S4）。

def test_design_doc_empty_vocab_returns_pass():
    """空 forbidden（[]）の vocab は status=pass を返す（skipped ではない）。

    user-story の空 vocab pass テストと同型。forbidden が空でも vocab ファイルは存在し
    JSON も正常なので skipped（ファイル不在/破損時のみ）にはならず、ヒット 0 件 → pass を返す。
    Design Doc の逸脱は機械の禁止語では拾えず rubric 主導という設計判断（S4）が、機械上
    pass として表れることを保証する（acceptance-criteria が vocab を持つのとは非対称）。
    """
    result = cv.check(str(FIX / "design-doc-good.md"), "design-doc")
    assert result["status"] == "pass"
    assert result["hits"] == []


# --- test-plan（テスト・計画）スライス ---
# 禁止語 = 終了基準の曖昧表現マーカー3語（正しく表示 / 正しく動作 / 適切に処理）を
# test-case-spec から踏襲（vocab 非空）。判断根拠（経験検証）: Test Plan の終了基準は P6
# （測定可能）の要請を持ち、「すべての画面が正しく表示されること」のような非測定の完了条件は
# 終了基準の主たる逸脱として出番があり（実機で deviation 確認）、かつ正当な地の文（カバレッジ%・
# pass 率・件数・しきい値）に対し誤爆しない（実機で pass 確認）。よって『逸脱が機械で綺麗に拾える』
# 条件を満たすため踏襲する＝vocab の有無は agile/WF の別でなく逸脱が綺麗に拾えるかで決まる
# （design-doc/cycle-14 の原則の WF 側適用）。技術名・SQL・ツール名（JUnit 等）は Test Plan で
# 正当に出るため禁止語にせず rubric へ（部分一致誤爆回避・非対称継続）。計画へのテストケース
# 具体値の混入・3語以外の曖昧表現（「十分に」等）は構造/文脈判定ゆえ rubric 主導。

def test_tp_good_has_no_violations():
    result = cv.check(str(FIX / "test-plan-good.md"), "test-plan")
    assert result["status"] == "pass"
    assert result["hits"] == []


def test_tp_violation_detected_outside_code():
    # violation fixture は終了基準節の地の文に 正しく表示・適切に処理 を1つずつ含む
    result = cv.check(str(FIX / "test-plan-vocab-violation.md"), "test-plan")
    assert result["status"] == "deviation"
    terms = [h["term"] for h in result["hits"]]
    assert "正しく表示" in terms
    assert "適切に処理" in terms


def test_tp_marker_in_code_block_not_flagged():
    """フェンス内の曖昧表現マーカー（正しく動作）は検出しないこと。

    violation fixture はフェンス内に「正しく動作」を列挙目的で置く。レシピの越境 note と
    同様にフェンス内は検査対象外（安全代替除外）であることを回帰防止する。地の文に出た
    正しく表示・適切に処理 のみが検出される（test-case-spec スライスと同型）。
    """
    result = cv.check(str(FIX / "test-plan-vocab-violation.md"), "test-plan")
    terms = [h["term"] for h in result["hits"]]
    assert "正しく動作" not in terms


def test_tp_tech_name_allowed():
    """技術名に SQL 部分文字列が含まれても test-plan vocab では検出されないこと。

    vocab チェッカーは部分一致（substring）で判定する。「SQL」を禁止語にすると
    PostgreSQL・NoSQL・MySQL・SQLite 等の製品名がすべてヒットする（cycle-8 で実機確認）。
    Test Plan ではリソース・環境記述として技術スタック名・ツール名が正当に現れるため、
    この誤爆を避けるため SQL は禁止語に含めない設計判断を下した（WF 既存スライスと同方針）。
    本テストはその決定の回帰防止として、技術名を含む散文が実 vocab で pass を返すことを保証する。
    """
    # 「PostgreSQL を本番同等構成で用意」は SQL を部分文字列として含む散文。実 vocab を読み込み、
    # その forbidden で SQL がヒットしない（＝3語のみで技術名を弾かない）ことを直接検証する。
    vocab = cv.load_vocab("test-plan")
    hits = cv.find_hits("PostgreSQL を本番同等構成で用意。JUnit で実行する", vocab["forbidden"])
    assert hits == [], f"技術名が誤検出された: {hits}"


# --- test-design-spec（テスト・設計仕様）スライス ---
# 禁止語 = テスト条件の曖昧表現マーカー3語（正しく表示 / 正しく動作 / 適切に処理）を
# test-case-spec/test-plan から踏襲（vocab 非空）。判断根拠（経験検証＝判断3）: 設計仕様の
# テスト条件（高レベルケース）も P6（観測可能）の要請を持ち、「受注登録機能が正しく動作する
# ことを確認する観点」のような非観測のテスト条件は主たる逸脱として出番がある（実機で deviation
# 確認）、かつ正当な地の文（テスト条件の境界識別・網羅方針の同値分割/境界値/C1 100%・テスト観点・
# トレーサビリティ・PostgreSQL を含む散文）に対し誤爆しない（実機で pass 確認）。よって『逸脱が
# 機械で綺麗に拾える』条件を満たすため踏襲する＝vocab の有無は agile/WF の別でなく逸脱が綺麗に
# 拾えるかで決まる（design-doc/cycle-14 の原則・test-plan/cycle-15 の WF 側実証の延長）。WF だから
# 自動的に持つのではなく経験検証して踏襲した（出番が乏しければ空にしていた）。技術名・SQL・ツール名は
# 正当に出るため禁止語にせず rubric へ（部分一致誤爆回避・非対称継続）。低レベルケース（具体値）の
# 混入は F1 同型の構造判定、3語以外の曖昧表現（「十分に」等）は文脈判定ゆえ rubric 主導。

def test_tds_good_has_no_violations():
    result = cv.check(str(FIX / "test-design-spec-good.md"), "test-design-spec")
    assert result["status"] == "pass"
    assert result["hits"] == []


def test_tds_violation_detected_outside_code():
    # violation fixture はテスト条件節の地の文に 正しく表示・適切に処理 を1つずつ含む
    result = cv.check(str(FIX / "test-design-spec-vocab-violation.md"), "test-design-spec")
    assert result["status"] == "deviation"
    terms = [h["term"] for h in result["hits"]]
    assert "正しく表示" in terms
    assert "適切に処理" in terms


def test_tds_marker_in_code_block_not_flagged():
    """フェンス内の曖昧表現マーカー（正しく動作）は検出しないこと。

    violation fixture はフェンス内に「正しく動作」を列挙目的で置く。レシピの越境 note と
    同様にフェンス内は検査対象外（安全代替除外）であることを回帰防止する。地の文に出た
    正しく表示・適切に処理 のみが検出される（test-case-spec/test-plan スライスと同型）。
    """
    result = cv.check(str(FIX / "test-design-spec-vocab-violation.md"), "test-design-spec")
    terms = [h["term"] for h in result["hits"]]
    assert "正しく動作" not in terms


def test_tds_tech_name_allowed():
    """技術名に SQL 部分文字列が含まれても test-design-spec vocab では検出されないこと。

    vocab チェッカーは部分一致（substring）で判定する。「SQL」を禁止語にすると
    PostgreSQL・NoSQL・MySQL・SQLite 等の製品名がすべてヒットする（cycle-8 で実機確認）。
    テスト設計仕様ではテスト条件の対象環境・網羅方針の記述として技術スタック名が正当に
    現れるため、この誤爆を避けるため SQL は禁止語に含めない設計判断を下した（WF 既存スライスと同方針）。
    本テストはその決定の回帰防止として、技術名を含む散文が実 vocab で pass を返すことを保証する。
    """
    # 「PostgreSQL を対象とした性能テスト条件」は SQL を部分文字列として含む散文。実 vocab を読み込み、
    # その forbidden で SQL がヒットしない（＝3語のみで技術名を弾かない）ことを直接検証する。
    vocab = cv.load_vocab("test-design-spec")
    hits = cv.find_hits("PostgreSQL を対象とした性能テスト条件を同値分割で導く", vocab["forbidden"])
    assert hits == [], f"技術名が誤検出された: {hits}"


# --- test-procedure-spec（テスト・手順仕様）スライス ---
# 禁止語 = 曖昧期待結果マーカー3語（正しく表示 / 正しく動作 / 適切に処理）を
# test-case-spec/test-plan/test-design-spec から踏襲（vocab 非空）。判断根拠（経験検証＝判断3）:
# 手順仕様は実行手順（操作・ステップ順）のみを書き、各操作の期待結果の合否判定（What to expect）は
# ケース仕様 test-case-spec の領分（実行↔判定の隣接境界＝このスライスの肝・判断1）。よって3語が手順に
# 出る＝「…が正しく表示されることを確認」のように期待結果の判定基準が手順へ混入したサインであり、
# 主たる逸脱として出番がある（実機で deviation 確認）。かつ正当な地の文（操作記述「ボタンを押す」
# 「データを入力する」・前提セットアップの状態/環境記述・トレーサビリティ・PostgreSQL を含む散文）に
# 対し誤爆しない（実機で pass 確認）。よって『逸脱が機械で綺麗に拾える』条件を満たすため踏襲する＝
# vocab の有無は agile/WF の別でなく逸脱が綺麗に拾えるかで決まる（design-doc/cycle-14 の原則・
# test-plan/test-design-spec の WF テスト工程での実証の延長）。WF だから自動的に持つのではなく経験検証
# して踏襲した（出番が乏しければ空にしていた）。技術名・SQL・ツール名は前提・セットアップ/実行環境で
# 正当に出るため禁止語にせず rubric へ（部分一致誤爆回避・非対称継続）。設計意図/テスト条件の逆流・
# ケース逐語転記・手順の粒度過大/過小は構造判定ゆえ rubric 主導。

def test_tps_good_has_no_violations():
    result = cv.check(str(FIX / "test-procedure-spec-good.md"), "test-procedure-spec")
    assert result["status"] == "pass"
    assert result["hits"] == []


def test_tps_violation_detected_outside_code():
    # violation fixture は実行手順節の地の文に 正しく表示・適切に処理 を1つずつ含む
    # （手順に期待結果の判定基準が混入＝実行↔判定の越境）
    result = cv.check(str(FIX / "test-procedure-spec-vocab-violation.md"), "test-procedure-spec")
    assert result["status"] == "deviation"
    terms = [h["term"] for h in result["hits"]]
    assert "正しく表示" in terms
    assert "適切に処理" in terms


def test_tps_marker_in_code_block_not_flagged():
    """フェンス内の曖昧表現マーカー（正しく動作）は検出しないこと。

    violation fixture はフェンス内に「正しく動作」を列挙目的で置く。レシピの越境 note と
    同様にフェンス内は検査対象外（安全代替除外）であることを回帰防止する。地の文に出た
    正しく表示・適切に処理 のみが検出される（test-case-spec/test-plan/test-design-spec スライスと同型）。
    """
    result = cv.check(str(FIX / "test-procedure-spec-vocab-violation.md"), "test-procedure-spec")
    terms = [h["term"] for h in result["hits"]]
    assert "正しく動作" not in terms


def test_tps_tech_name_allowed():
    """技術名に SQL 部分文字列が含まれても test-procedure-spec vocab では検出されないこと。

    vocab チェッカーは部分一致（substring）で判定する。「SQL」を禁止語にすると
    PostgreSQL・NoSQL・MySQL・SQLite 等の製品名がすべてヒットする（cycle-8 で実機確認）。
    手順仕様では前提・セットアップ／実行環境の記述として技術スタック名・製品名が正当に
    現れるため、この誤爆を避けるため SQL は禁止語に含めない設計判断を下した（WF 既存スライスと同方針）。
    本テストはその決定の回帰防止として、技術名を含む散文が実 vocab で pass を返すことを保証する。
    """
    # 「PostgreSQL を本番同等構成で用意し、データを投入する」は SQL を部分文字列として含む前提記述。
    # 実 vocab を読み込み、その forbidden で SQL がヒットしない（＝3語のみで技術名を弾かない）ことを検証する。
    vocab = cv.load_vocab("test-procedure-spec")
    hits = cv.find_hits("PostgreSQL を本番同等構成で用意し、フィクスチャを投入する", vocab["forbidden"])
    assert hits == [], f"技術名が誤検出された: {hits}"


# --- test-strategy（テスト・戦略）スライス ---
# vocab は空（forbidden:[]）＝設計上の判断。WF テスト工程5本（ケース仕様/計画/設計仕様/手順仕様/戦略）
# のうち唯一 vocab を持たない doc_type。判断根拠（判断3・経験検証）: 曖昧期待結果3語（正しく表示/
# 正しく動作/適切に処理）は「期待結果・完了条件・テスト条件・合否判定の定型句」であり、それらを書く層
# （ケース仕様/計画/設計仕様/手順仕様）では主たる逸脱として出番があり踏襲された。だが戦略は組織横断の
# テスト方針（品質目標・全体アプローチ・テストレベル/タイプの標準）を書く最上位層で、期待結果・完了条件・
# テスト条件・合否判定を書かない＝3語の主戦場が戦略レベルに存在しない。3語は技術的には出現しうるが、それは
# 「測定不能な品質目標（高品質/安定/十分 等の副詞・曖昧目標）」という広い逸脱の狭い字面サブセットにすぎず、
# その広い測定可能性問題は P6・誤爆性ゆえ rubric の領分（nonfunctional-design の曖昧表現を rubric にした
# のと同型）。無数の曖昧表現のうち3語だけ機械で切り出すのは偽の安心を与え、戦略の逸脱は綺麗には拾えない。
# よって空にする（既定＝迷ったら空）＝「vocab の有無は工程でなく逸脱が機械で綺麗に拾えるかで決まる」ことの
# 最強の実証（WF テスト5本中4踏襲1空・同一ファミリで逆の帰結）。戦略の主たる逸脱（プロジェクト固有詳細の
# 混入・測定不能な曖昧品質目標・V 字1対1の固定強制）は構造/文脈判定ゆえ rubric/test-strategy.md 主導。

def test_ts_empty_vocab_returns_pass():
    """空 forbidden（[]）の vocab は status=pass を返す（skipped ではない）。

    user-story / design-doc の空 vocab pass テストと同型。forbidden が空でも vocab ファイルは
    存在し JSON も正常なので skipped（ファイル不在/破損時のみ）にはならず、ヒット 0 件 → pass を返す。
    test-strategy の vocab を意図的に空にした設計判断（WF テスト5本中唯一空・判断3）が、機械上
    pass として表れることを保証する（同じ WF テスト工程の case/plan/design-spec/procedure-spec が
    vocab を持つのとは逆の帰結＝vocab の有無は工程でなく逸脱の機械可検出性で決まる実証）。
    """
    result = cv.check(str(FIX / "test-strategy-good.md"), "test-strategy")
    assert result["status"] == "pass"
    assert result["hits"] == []


# --- detailed-design-process（詳細設計・処理詳細）スライス ---
# 禁止語 = 「なぜなら業務」のみ＝detailed-design-data（cycle-3）から踏襲（vocab 非空）。
# 判断根拠（経験検証＝判断2）: 処理詳細も同じ詳細設計工程であり「含まない＝業務理由（要件既出）」を持つ。
# (a) 出番あり: 業務理由（上位 Why）を処理詳細に転記する逸脱は実際に起こり、「なぜなら業務…」型で出る
#   （実機で violation fixture が deviation を返すことを確認）。(b) 誤爆なし: 処理仕様・クラス構造・例外処理の
#   正当な地の文（メソッド名・技術名・PostgreSQL を含む散文）に「なぜなら業務」は誤爆しない（実機で good が pass）。
# 出番あり∧誤爆なしゆえ踏襲する＝vocab の有無は agile/WF の別でなく逸脱が機械で綺麗に拾えるかで決まる
# （design-doc/cycle-14 の原則）。技術名・製品名・メソッド名・SQL（全文）は処理仕様で正当に出るため禁止語にせず、
# とりわけ SQL は PostgreSQL/MySQL の部分文字列で誤爆するため rubric へ。ghost document（コード逐語）・
# 実質空（分岐/エラー条件/性能制約 未記述）は構造判定ゆえ rubric/detailed-design-process.md 主導。

def test_ddp_good_has_no_violations():
    result = cv.check(str(FIX / "detailed-design-process-good.md"), "detailed-design-process")
    assert result["status"] == "pass"
    assert result["hits"] == []


def test_ddp_violation_detected_outside_code():
    # violation fixture はクラス・モジュール構造節の地の文に なぜなら業務（業務理由転記）を含む
    result = cv.check(str(FIX / "detailed-design-process-vocab-violation.md"),
                      "detailed-design-process")
    assert result["status"] == "deviation"
    terms = [h["term"] for h in result["hits"]]
    assert "なぜなら業務" in terms


def test_ddp_tech_name_and_method_not_flagged():
    """技術名・SQL 部分文字列・メソッド名は detailed-design-process vocab では検出されないこと。

    禁止語は「なぜなら業務」のみで、処理仕様では技術名（PostgreSQL）・メソッド名・例外名が正当に
    出る。これらが地の文にあっても誤検出されない（good fixture は地の文に PostgreSQL/メソッド名を
    含むが pass）ことを回帰防止する。処理詳細は技術名・SQL を rubric で見る（vocab で弾かない）。
    """
    vocab = cv.load_vocab("detailed-design-process")
    hits = cv.find_hits(
        "OrderConfirmationService.confirm() は PostgreSQL に保存する。NoSQL は却下",
        vocab["forbidden"],
    )
    assert hits == [], f"技術名・メソッド名が誤検出された: {hits}"


# --- adr（アジャイル・Architecture Decision Record）スライス ---
# vocab は空（forbidden:[]）＝設計上の判断（design-doc/user-story と同型・acceptance-criteria とは非対称）。
# ADR の逸脱（事後正当化〔承認なし accepted〕/trivial な決定の ADR 化〔Prettier 等・可逆で影響小〕/
# Why の記述なし）は構造・文脈の判定で、特定の禁止トークンの部分一致では原理的に拾えない。
# 『却下案なし』（Why の片側欠落）は必須見出し『却下案』の欠落として check_headings が機械検出するため
# vocab 不要。残る逸脱（事後正当化・trivial・Why なし）に明確な定型句マーカーは無く、仮に置いても
# 正当な ADR 記述（承認済みの accepted 状態宣言・正当な小さい決定の言及）と同一トークンになり誤爆する。
# vocab の有無は『逸脱が機械で綺麗に拾えるか』で決まる（agile/WF の別ではない）。質的判定は rubric/adr.md
# に委ねる（agile rubric 主導・S4）。採番・生成・内容評価は architecture-decision-records スキルが所有（S5）。

def test_adr_empty_vocab_returns_pass():
    """空 forbidden（[]）の vocab は status=pass を返す（skipped ではない）。

    user-story / design-doc / test-strategy の空 vocab pass テストと同型。forbidden が空でも
    vocab ファイルは存在し JSON も正常なので skipped（ファイル不在/破損時のみ）にはならず、
    ヒット 0 件 → pass を返す。ADR の逸脱は機械の禁止語では拾えず rubric 主導という設計判断（S4）が、
    機械上 pass として表れることを保証する（acceptance-criteria が vocab を持つのとは非対称）。
    """
    result = cv.check(str(FIX / "adr-good.md"), "adr")
    assert result["status"] == "pass"
    assert result["hits"] == []


# --- rfc（アジャイル・Request for Comments）スライス ---
# vocab は空（forbidden:[]）＝設計上の判断（design-doc/user-story/adr/test-strategy と同型・
# acceptance-criteria とは非対称）。経験検証＝AC の曖昧期待結果3語（正しく表示/正しく動作/適切に処理）は
# 『観測可能な合否・完了条件・テスト結果』を書く doc_type でこそ誤爆なく拾える定型句だが、RFC は
# 『決定前の提案/探索文書』で期待結果・完了条件・テスト合否を書かない＝3語の出番（主戦場）が構造的に無い。
# 仮に置いても出番が無く検出に寄与せず、むしろ RFC が将来の振る舞いを地の文で語る正当な未決表明
# （例『提案する仕組みが正しく動作するかは未解決の論点で検討する』）に部分一致で誤爆しうる。
# RFC の逸脱（実装詳細の先取り・未決を装った既決・straw man 代替）は構造・文脈の判定で部分一致では拾えない。
# 『代替案なし』『未解決の論点なし』は必須見出し欠落として check_headings が、孤立提案（対応要求 ID 空セル）は
# 独立トレース節の空セルとして check_traceability が機械検出する。残る質的逸脱は rubric/rfc.md に委ねる
# （agile rubric 主導・S4）。技術名・製品名・SQL は禁止しない（RFC は技術選定の探索で技術名が正当に頻出）。

def test_rfc_empty_vocab_returns_pass():
    """空 forbidden（[]）の vocab は status=pass を返す（skipped ではない）。

    user-story / design-doc / adr / test-strategy の空 vocab pass テストと同型。forbidden が空でも
    vocab ファイルは存在し JSON も正常なので skipped（ファイル不在/破損時のみ）にはならず、
    ヒット 0 件 → pass を返す。RFC の逸脱は機械の禁止語では拾えず rubric 主導という設計判断（S4）が、
    機械上 pass として表れることを保証する（acceptance-criteria が vocab を持つのとは非対称）。
    """
    result = cv.check(str(FIX / "rfc-good.md"), "rfc")
    assert result["status"] == "pass"
    assert result["hits"] == []


# --- pr-faq（アジャイル・Amazon Working Backwards／PR-FAQ）スライス ---
# vocab は空（forbidden:[]）＝設計上の判断（rfc/design-doc/user-story/adr/test-strategy と同型・
# acceptance-criteria とは非対称＝6例目の空）。経験検証＝AC の曖昧期待結果3語（正しく表示/正しく動作/
# 適切に処理）は『観測可能な合否・完了条件・テスト結果』を書く doc_type でこそ誤爆なく拾える定型句だが、
# PR-FAQ は『顧客視点の未来プレスリリース＋想定問答で企画を逆算する提案文書』で期待結果・完了条件・
# テスト合否を書かない＝3語の出番（主戦場）が構造的に無い。仮に置いても出番が無く検出に寄与せず、
# むしろ PR が将来の顧客体験を便益として地の文で語る正当な文（例『在庫超過行が正しく表示されるように
# なる』のような未来の顧客体験記述）に部分一致で誤爆しうる（それは PR の顧客便益記述で逸脱でない）。
# PR-FAQ の真の逸脱（PR の内部機能リスト化・楽観バイアス・スライド化/15p 機能リスト・成功指標の
# 曖昧表現〔『大幅に改善』『高い満足度』〕）は構造・量・文脈の判定で部分一致では拾えない。とりわけ
# 成功指標の曖昧表現は副詞・形容詞（『大幅に』『高い』）で nonfunctional の『高速に』等と同じく
# 部分一致誤爆ゆえ rubric の領分。『プレスリリースなし』『想定問答なし』『成功指標なし』は必須見出し
# 欠落として check_headings が、顧客課題に紐付かない機能/主張（対応する顧客課題 ID 空セル＝
# Working Backwards 違反・プロダクトアウト）は独立トレース節の空セルとして check_traceability が機械検出する。
# 残る質的逸脱は rubric/pr-faq.md に委ねる（agile rubric 主導・S4）。技術名・製品名・SQL は禁止しない。

def test_pr_faq_empty_vocab_returns_pass():
    """空 forbidden（[]）の vocab は status=pass を返す（skipped ではない）。

    rfc / user-story / design-doc / adr / test-strategy の空 vocab pass テストと同型。forbidden が
    空でも vocab ファイルは存在し JSON も正常なので skipped（ファイル不在/破損時のみ）にはならず、
    ヒット 0 件 → pass を返す。PR-FAQ の逸脱は機械の禁止語では拾えず rubric 主導という設計判断（S4）が、
    機械上 pass として表れることを保証する（acceptance-criteria が vocab を持つのとは非対称＝6例目の空）。
    """
    result = cv.check(str(FIX / "pr-faq-good.md"), "pr-faq")
    assert result["status"] == "pass"
    assert result["hits"] == []
