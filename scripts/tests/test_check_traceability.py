"""check_traceability（3つ目の決定論チェッカー）のテスト。

F5（cycle-10 レビュー検出）対応: 全 rubric が「トレーサビリティ表の空セル検出は
機械の担当」と書くのに既存2チェッカー（見出し/語彙の部分一致）には表解析が無く、
対応要件 ID 空欄の孤立設計要素（スコープクリープ候補・P4 違反）がどの層でも
未検出の穴になっていた。本テストは空セル検出（孤立設計要素）の決定論化を red→green で確かめる。

fail-open 哲学: 判定できない構造（節なし/表なし/ID 列同定不可）は deviation でなく
skipped に倒す（握りつぶしでなく「機械判定の対象外」を明示）。
"""
from pathlib import Path
import check_traceability as ct

FIX = Path(__file__).parent / "fixtures"


# --- strip_code_blocks（既存2チェッカーと同じフェンス除外） ---

def test_strip_code_blocks_removes_fenced():
    text = "a\n```\n| x | 対応要件 ID |\n|---|---|\n| y |  |\n```\nb"
    stripped = ct.strip_code_blocks(text)
    assert "対応要件 ID" not in stripped
    assert "a" in stripped


# --- 全セル埋まり → pass ---

def test_good_table_passes():
    result = ct.check(str(FIX / "traceability-good.md"), "external-design")
    assert result["status"] == "pass"
    assert result["orphans"] == []


# --- 空セル・ダッシュあり → deviation（orphans に該当） ---

def test_orphan_empty_cell_is_deviation():
    result = ct.check(str(FIX / "traceability-orphan.md"), "external-design")
    assert result["status"] == "deviation"
    # 空セル行（受注一覧画面）とダッシュ行（受注控え）の2件が孤立設計要素として挙がる
    elements = [o["element"] for o in result["orphans"]]
    assert "受注一覧画面" in elements
    assert "受注控え（帳票）" in elements
    # 埋まっている行（受注登録画面・共通エラー画面）は孤立に含めない（誤検出回帰防止）
    assert "受注登録画面" not in elements
    assert "共通エラー画面" not in elements


def test_orphan_carries_line_number():
    """orphans の各要素は行番号目安（line）を持つ（人が場所を辿れるように）。"""
    result = ct.check(str(FIX / "traceability-orphan.md"), "external-design")
    assert result["status"] == "deviation"
    for o in result["orphans"]:
        assert isinstance(o.get("line"), int)
        assert o["line"] > 0


# --- 「横断」等の記入済みは空欄でない＝孤立でない ---

def test_filled_cross_cutting_is_not_orphan():
    """「横断」「横断 NFR-USE-01」のような記入済みセルは空欄と区別し pass 側に置く。

    レシピは要件に直接紐付かない横断的要素を「横断」＋NFR ID で埋める運用。これは
    記入済み（=トレース済み）であって空セルではないため、孤立設計要素として検出しない。
    """
    result = ct.check(str(FIX / "traceability-good.md"), "external-design")
    # good fixture の「共通エラー画面 | 横断 NFR-USE-01」は孤立でない＝全体 pass
    assert result["status"] == "pass"


# --- SRS スタイル: 第1列が「要件 ID」でもトレース列「上位要求 ID」を選ぶ ---

def test_srs_style_picks_trace_column_not_first_column():
    """第1列ヘッダが「要件 ID」（設計要素名）でも、ID 列同定は第1列に釣られず
    トレース対象列「上位要求 ID」を選ぶこと。FR-02 の上位要求 ID 空欄を孤立として検出する。
    """
    result = ct.check(str(FIX / "traceability-srs-style.md"), "srs")
    assert result["status"] == "deviation"
    elements = [o["element"] for o in result["orphans"]]
    assert "FR-02" in elements
    # 埋まっている FR-01・NFR-SEC-01（横断）は孤立でない
    assert "FR-01" not in elements
    assert "NFR-SEC-01" not in elements


# --- トレーサビリティ節が無い（user-story 型） → skipped ---

def test_no_traceability_section_is_skipped():
    result = ct.check(str(FIX / "traceability-none.md"), "user-story")
    assert result["status"] == "skipped"
    assert result["orphans"] == []


# --- 節はあるが表が無い → skipped ---

def test_section_without_table_is_skipped():
    result = ct.check(str(FIX / "traceability-no-table.md"), "external-design")
    assert result["status"] == "skipped"


# --- ID 列を同定できない（逆引き表のみ） → skipped（「（なし）」誤爆回避） ---

def test_id_column_unidentifiable_is_skipped():
    """トレース対象列ヘッダが「対応」「上位要求」を含まない表は ID 列を一意同定できず
    skipped に倒す。逆引き表の「（なし）」をカバレッジ欠落であって空セルと誤認しない
    （S-1 false-positive 回避）。
    """
    result = ct.check(str(FIX / "traceability-reverse-only.md"), "test-case-spec")
    assert result["status"] == "skipped"


# --- コードフェンス内の空セル表 → 検査対象外（skipped か pass） ---

def test_fence_only_table_not_checked():
    result = ct.check(str(FIX / "traceability-fence-only.md"), "external-design")
    # フェンス内の例表は除外され、地の文に実表が無いので skipped（少なくとも deviation でない）
    assert result["status"] != "deviation"


# --- ファイル不在 → skipped（fail-open） ---

def test_failopen_on_missing_file():
    result = ct.check(str(FIX / "does-not-exist.md"), "external-design")
    assert result["status"] == "skipped"


# --- find_orphans の空欄判定ユニット ---

def test_is_empty_cell_recognizes_blank_and_dash():
    """空・空白のみ・各種ダッシュ/無し記号を空欄と判定し、記入済みは空欄でないと判定する。"""
    for blank in ["", "   ", "-", "—", "ー", "/", "N/A", "n/a", "ｰ", "－"]:
        assert ct.is_empty_cell(blank), f"{blank!r} は空欄と判定されるべき"
    for filled in ["FR-01", "横断", "横断 NFR-USE-01", "UC-02, FR-05"]:
        assert not ct.is_empty_cell(filled), f"{filled!r} は記入済みと判定されるべき"


# --- select_id_column のヒューリスティック ---

def test_select_id_column_prefers_taiou_over_first():
    """第1列が「要件 ID」でも、後続の「対応」を含む列を ID 列に選ぶ（第1列＝設計要素名）。"""
    header = ["要件 ID", "要件種別", "対応要件・NFR ID", "備考"]
    assert ct.select_id_column(header) == 2


def test_select_id_column_falls_back_to_jouikyuu():
    """「対応」列が無ければ「上位要求」を含む列を選ぶ（SRS スタイル）。"""
    header = ["要件 ID", "要件種別", "上位要求 ID", "備考"]
    assert ct.select_id_column(header) == 2


def test_select_id_column_none_when_unidentifiable():
    """「対応」も「上位要求」も無ければ ID 列を同定できず None（→ skipped）。"""
    header = ["要件 ID", "検証するケース ID", "カバレッジ"]
    assert ct.select_id_column(header) is None


def test_select_id_column_never_returns_first_column():
    """設計要素名（第1列）は ID 列に選ばない（たとえ「対応」を含んでも先頭は主語）。

    現実のレシピで先頭が「対応…」になる例は無いが、ヒューリスティックの不変条件
    （第1列は主語＝ID 列でない）を明示的に守る。
    """
    header = ["対応要件 ID", "備考"]  # 不自然だが先頭が「対応」を含むケース
    # 先頭は主語として扱い ID 列にしない → 同定不可（None）
    assert ct.select_id_column(header) is None


# --- acceptance-criteria（アジャイル・受入基準）スライス ---
# AC は agile で初めて check_traceability が有効（skipped でなく）になるスライス。
# user-story はトレース節を持たないため skipped だったが、AC はトレース表（対応 user-story 列）
# を持つため空セル＝孤立シナリオを決定論で検出できる。ID 列ヘッダは「対応 user-story」で
# select_id_column の「対応」を含む列ルールに乗る。

def test_ac_good_table_passes():
    """AC good fixture はトレース表が全セル埋まり＝孤立シナリオなし＝pass。"""
    result = ct.check(str(FIX / "acceptance-criteria-good.md"), "acceptance-criteria")
    assert result["status"] == "pass"
    assert result["orphans"] == []

def test_ac_orphan_empty_cell_is_deviation():
    """AC orphan fixture は空セル(AC-2)とダッシュ(AC-3)の2件を孤立シナリオとして検出する。"""
    result = ct.check(str(FIX / "acceptance-criteria-orphan.md"), "acceptance-criteria")
    assert result["status"] == "deviation"
    elements = [o["element"] for o in result["orphans"]]
    assert "AC-2" in elements
    assert "AC-3" in elements
    # 埋まっている AC-1 は孤立に含めない（誤検出回帰防止）
    assert "AC-1" not in elements
    # 行番号目安を持つ（人が場所を辿れるように）
    for o in result["orphans"]:
        assert isinstance(o.get("line"), int)
        assert o["line"] > 0


# --- design-doc（アジャイル・Design Doc）スライス ---
# design-doc は agile で2つ目の check_traceability 有効スライス（1つ目＝acceptance-criteria）。
# トレース表（対応 user-story 列）を持つため空セル＝孤立した設計判断を決定論で検出できる。
# ID 列ヘッダは「対応 user-story」で select_id_column の「対応」を含む列ルールに乗る。

def test_design_doc_good_table_passes():
    """design-doc good fixture はトレース表が全セル埋まり＝孤立判断なし＝pass。"""
    result = ct.check(str(FIX / "design-doc-good.md"), "design-doc")
    assert result["status"] == "pass"
    assert result["orphans"] == []

def test_design_doc_orphan_empty_cell_is_deviation():
    """design-doc orphan fixture は空セルとダッシュの2件を孤立した設計判断として検出する。"""
    result = ct.check(str(FIX / "design-doc-orphan.md"), "design-doc")
    assert result["status"] == "deviation"
    elements = [o["element"] for o in result["orphans"]]
    assert "在庫補充の自動発注" in elements
    assert "受注の修正フロー" in elements
    # 埋まっている「一括登録専用ユースケース」は孤立に含めない（誤検出回帰防止）
    assert "一括登録専用ユースケース" not in elements
    # 行番号目安を持つ（人が場所を辿れるように）
    for o in result["orphans"]:
        assert isinstance(o.get("line"), int)
        assert o["line"] > 0


# --- test-plan（テスト・計画）スライス ---
# WF テスト工程の2本目（1本目＝test-case-spec＝ケース仕様）。トレース表（対応要件/テストレベル列）
# を持つため空セル＝孤立テスト項目（根拠のないテスト）を決定論で検出できる。ID 列ヘッダは
# 「対応要件/テストレベル」で select_id_column の「対応」を含む列ルールに乗る（第1列＝テスト項目名は
# 主語として除外される）。

def test_tp_good_table_passes():
    """test-plan good fixture はトレース表が全セル埋まり＝孤立テスト項目なし＝pass。"""
    result = ct.check(str(FIX / "test-plan-good.md"), "test-plan")
    assert result["status"] == "pass"
    assert result["orphans"] == []

def test_tp_orphan_empty_cell_is_deviation():
    """test-plan orphan fixture は空セルとダッシュの2件を孤立テスト項目として検出する。"""
    result = ct.check(str(FIX / "test-plan-orphan.md"), "test-plan")
    assert result["status"] == "deviation"
    elements = [o["element"] for o in result["orphans"]]
    assert "出どころ不明のテスト項目" in elements
    assert "ダッシュで埋めたテスト項目" in elements
    # 埋まっている「受注登録の機能テスト」は孤立に含めない（誤検出回帰防止）
    assert "受注登録の機能テスト" not in elements
    # 行番号目安を持つ（人が場所を辿れるように）
    for o in result["orphans"]:
        assert isinstance(o.get("line"), int)
        assert o["line"] > 0


# --- test-design-spec（テスト・設計仕様）スライス ---
# WF テスト工程の3本目（設計仕様レベル＝ケース仕様の直上）。トレース表（対応要件/設計 ID 列）
# を持つため空セル＝孤立テスト条件（根拠のないテスト）を決定論で検出できる。ID 列ヘッダは
# 「対応要件/設計 ID」で select_id_column の「対応」を含む列ルールに乗る（第1列＝テスト条件名は
# 主語として除外される）。

def test_tds_good_table_passes():
    """test-design-spec good fixture はトレース表が全セル埋まり＝孤立テスト条件なし＝pass。"""
    result = ct.check(str(FIX / "test-design-spec-good.md"), "test-design-spec")
    assert result["status"] == "pass"
    assert result["orphans"] == []


def test_tds_orphan_empty_cell_is_deviation():
    """test-design-spec orphan fixture は空セルとダッシュの2件を孤立テスト条件として検出する。"""
    result = ct.check(str(FIX / "test-design-spec-orphan.md"), "test-design-spec")
    assert result["status"] == "deviation"
    elements = [o["element"] for o in result["orphans"]]
    assert "出どころ不明のテスト条件" in elements
    assert "ダッシュで埋めたテスト条件" in elements
    # 埋まっている「TCD-01 受注登録の正常系」は孤立に含めない（誤検出回帰防止）
    assert "TCD-01 受注登録の正常系" not in elements
    # 行番号目安を持つ（人が場所を辿れるように）
    for o in result["orphans"]:
        assert isinstance(o.get("line"), int)
        assert o["line"] > 0


# --- test-procedure-spec（テスト・手順仕様）スライス ---
# WF テスト工程の4本目（手順仕様レベル＝ケース仕様の直下）。トレース表（対応ケース ID 列）を
# 持つため空セル＝孤立手順（根拠のない実行）を決定論で検出できる。ID 列ヘッダは「対応ケース ID」で
# select_id_column の「対応」を含む列ルールに乗る（第1列＝実行手順名は主語として除外される）。

def test_tps_good_table_passes():
    """test-procedure-spec good fixture はトレース表が全セル埋まり＝孤立手順なし＝pass。"""
    result = ct.check(str(FIX / "test-procedure-spec-good.md"), "test-procedure-spec")
    assert result["status"] == "pass"
    assert result["orphans"] == []


def test_tps_orphan_empty_cell_is_deviation():
    """test-procedure-spec orphan fixture は空セルとダッシュの2件を孤立手順として検出する。"""
    result = ct.check(str(FIX / "test-procedure-spec-orphan.md"), "test-procedure-spec")
    assert result["status"] == "deviation"
    elements = [o["element"] for o in result["orphans"]]
    assert "出どころ不明の操作" in elements
    assert "ダッシュで埋めた操作" in elements
    # 埋まっている「手順1 受注登録の操作」は孤立に含めない（誤検出回帰防止）
    assert "手順1 受注登録の操作" not in elements
    # 行番号目安を持つ（人が場所を辿れるように）
    for o in result["orphans"]:
        assert isinstance(o.get("line"), int)
        assert o["line"] > 0


# --- test-strategy（テスト・戦略）スライス ---
# WF テスト工程の5本目＝最上位（戦略レベル＝計画の直上）。トレース表（対応する品質目標/上位標準/
# 事業目標 列）を持つため空セル＝孤立した方針（拠り所のない方針）を決定論で検出できる。ID 列ヘッダは
# 「対応する品質目標/上位標準/事業目標」で select_id_column の「対応」を含む列ルールに乗る（第1列＝
# テスト方針/レベル名は主語として除外される）。戦略は最上位ゆえトレースの方向は上位（品質目標/上位標準/
# 事業目標）へ＝各方針が根拠を持つかを見る。空セル検出は機械、紐付けの意味的妥当性は rubric。

def test_ts_good_table_passes():
    """test-strategy good fixture はトレース表が全セル埋まり＝孤立した方針なし＝pass。"""
    result = ct.check(str(FIX / "test-strategy-good.md"), "test-strategy")
    assert result["status"] == "pass"
    assert result["orphans"] == []


def test_ts_orphan_empty_cell_is_deviation():
    """test-strategy orphan fixture は空セルとダッシュの2件を孤立した方針として検出する。"""
    result = ct.check(str(FIX / "test-strategy-orphan.md"), "test-strategy")
    assert result["status"] == "deviation"
    elements = [o["element"] for o in result["orphans"]]
    assert "拠り所のない方針" in elements
    assert "ダッシュで埋めた方針" in elements
    # 埋まっている「シフトレフト方針」は孤立に含めない（誤検出回帰防止）
    assert "シフトレフト方針" not in elements
    # 行番号目安を持つ（人が場所を辿れるように）
    for o in result["orphans"]:
        assert isinstance(o.get("line"), int)
        assert o["line"] > 0


# --- detailed-design-process（詳細設計・処理詳細）スライス ---
# WF 詳細設計の2本目（1本目＝detailed-design-data＝データ詳細）。トレース表（対応 基本設計/要件 ID 列）を
# 持つため空セル＝孤立設計要素（根拠のない処理）を決定論で検出できる。ID 列ヘッダは
# 「対応 基本設計/要件 ID」で select_id_column の「対応」を含む列ルールに乗る（第1列＝設計要素名は
# 主語として除外される）。

def test_ddp_good_table_passes():
    """detailed-design-process good fixture はトレース表が全セル埋まり＝孤立設計要素なし＝pass。"""
    result = ct.check(str(FIX / "detailed-design-process-good.md"), "detailed-design-process")
    assert result["status"] == "pass"
    assert result["orphans"] == []


def test_ddp_orphan_empty_cell_is_deviation():
    """detailed-design-process orphan fixture は空セルとダッシュの2件を孤立設計要素として検出する。"""
    result = ct.check(str(FIX / "detailed-design-process-orphan.md"), "detailed-design-process")
    assert result["status"] == "deviation"
    elements = [o["element"] for o in result["orphans"]]
    assert "出どころ不明の処理" in elements
    assert "ダッシュで埋めた処理" in elements
    # 埋まっている「OrderConfirmationService」は孤立に含めない（誤検出回帰防止）
    assert "OrderConfirmationService" not in elements
    # 行番号目安を持つ（人が場所を辿れるように）
    for o in result["orphans"]:
        assert isinstance(o.get("line"), int)
        assert o["line"] > 0


# --- adr（アジャイル・Architecture Decision Record）スライス ---
# ADR は Nygard 標準形式（Title〔H1〕/Context/Decision/Status/Consequences）にトレース表を持たない。
# doc-standards はこれに却下案を独自追加して必須にする。
# この判断が何の要求/設計に driven されたかは Context 内に書く（独立トレース見出しにしない＝ADR 標準を
# 尊重し architecture-decision-records スキルの形式と衝突しない）。よって ADR は user-story と同型で
# トレーサビリティ必須見出しを持たず、check_traceability は skipped（fail-open）を返す。orphan fixture は
# 作らない（トレース節が無いので空セル検出の対象外）。本テストは「ADR good fixture → skipped」を確認する
# （user-story の skipped 挙動＝traceability-none.md による検証と同型）。

def test_adr_good_is_skipped_no_trace_section():
    """ADR good fixture はトレース節を持たない（トレースは Context 内）ため skipped を返す。

    user-story と同型の fail-open。ADR 標準形式にトレース表が無いことを反映し、空セル検出の
    対象外であることを明示する（deviation でも pass でもなく skipped）。
    """
    result = ct.check(str(FIX / "adr-good.md"), "adr")
    assert result["status"] == "skipped"
    assert result["orphans"] == []


# --- rfc（アジャイル・Request for Comments）スライス ---
# RFC は agile で3つ目の check_traceability 有効スライス（1=acceptance-criteria・2=design-doc）。
# ADR とは非対称＝ADR は採番/記録フォーマットを architecture-decision-records スキルが所有するため
# Context 内に書き skipped にしたが、RFC は doc-standards 固有の doc_type で外部スキル所有形式と
# 衝突しないので独立トレース節を持ち check_traceability を有効化する。各提案・論点→対応要求の
# 空セル＝孤立提案（スコープクリープ候補・P4 違反）を決定論で検出。ID 列ヘッダは「対応要求」で
# select_id_column の「対応」を含む列ルールに乗る（第1列＝提案・論点名は主語で除外）。

def test_rfc_good_table_passes():
    """rfc good fixture はトレース表が全セル埋まり＝孤立提案なし＝pass。"""
    result = ct.check(str(FIX / "rfc-good.md"), "rfc")
    assert result["status"] == "pass"
    assert result["orphans"] == []

def test_rfc_orphan_empty_cell_is_deviation():
    """rfc orphan fixture は対応要求列の空セルを孤立提案として検出する。"""
    result = ct.check(str(FIX / "rfc-orphan.md"), "rfc")
    assert result["status"] == "deviation"
    elements = [o["element"] for o in result["orphans"]]
    assert "監査ログの自動収集を提案" in elements
    # 埋まっている「行単位の部分成立を提案」は孤立に含めない（誤検出回帰防止）
    assert "行単位の部分成立を提案" not in elements
    # 行番号目安を持つ（人が場所を辿れるように）
    for o in result["orphans"]:
        assert isinstance(o.get("line"), int)
        assert o["line"] > 0


# --- pr-faq（アジャイル・Amazon Working Backwards／PR-FAQ）スライス ---
# PR-FAQ は agile で4つ目の check_traceability 有効スライス（1=acceptance-criteria・2=design-doc・3=rfc）。
# ADR とは非対称＝ADR は採番/記録フォーマットを architecture-decision-records スキルが所有するため
# Context 内に書き skipped にしたが、PR-FAQ は doc-standards 固有の doc_type で外部スキル所有形式と
# 衝突しないので独立トレース節を持ち check_traceability を有効化する。PR-FAQ は要件定義の入口（最上流）で
# 対応要求 ID がまだ無い段階ゆえ、トレース先は『対応する顧客課題／事業目標』にする（test-strategy が
# トレースを上位＝事業目標へ向けた前例と同型）。各主張・指標→対応する顧客課題の空セル＝顧客課題に
# 紐付かない機能/主張（Working Backwards 違反・プロダクトアウト・P4 違反）を決定論で検出。
# ID 列ヘッダは「対応する顧客課題」で select_id_column の「対応」を含む列ルールに乗る
# （第1列＝主張・指標名は主語で除外）。

def test_pr_faq_good_table_passes():
    """pr-faq good fixture はトレース表が全セル埋まり＝顧客課題に紐付かない主張なし＝pass。"""
    result = ct.check(str(FIX / "pr-faq-good.md"), "pr-faq")
    assert result["status"] == "pass"
    assert result["orphans"] == []

def test_pr_faq_orphan_empty_cell_is_deviation():
    """pr-faq orphan fixture は対応する顧客課題列の空セルを Working Backwards 違反として検出する。"""
    result = ct.check(str(FIX / "pr-faq-orphan.md"), "pr-faq")
    assert result["status"] == "deviation"
    elements = [o["element"] for o in result["orphans"]]
    assert "管理者向け一括登録ダッシュボードを提供" in elements
    # 埋まっている「行単位の部分成立で受注漏れを防ぐ」は孤立に含めない（誤検出回帰防止）
    assert "行単位の部分成立で受注漏れを防ぐ" not in elements
    # 行番号目安を持つ（人が場所を辿れるように）
    for o in result["orphans"]:
        assert isinstance(o.get("line"), int)
        assert o["line"] > 0
