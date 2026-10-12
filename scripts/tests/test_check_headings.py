from pathlib import Path
import check_headings as ch

FIX = Path(__file__).parent / "fixtures"

def test_good_has_no_missing():
    text = (FIX / "data-design-good.md").read_text(encoding="utf-8")
    headings = ch.extract_headings(text)
    # F1 スタンスA: 基本設計データ設計の必須見出しは論理レベルのみ（物理は詳細設計へ分離）
    missing = ch.find_missing(headings, ["論理ER", "トレーサビリティ"])
    assert missing == []

def test_missing_traceability_is_detected():
    text = (FIX / "data-design-missing-headings.md").read_text(encoding="utf-8")
    headings = ch.extract_headings(text)
    # missing fixture は 論理ER のみ持ち トレーサビリティ を欠く
    missing = ch.find_missing(headings, ["論理ER", "トレーサビリティ"])
    assert "トレーサビリティ" in missing

def test_failopen_when_schema_absent():
    result = ch.check(str(FIX / "data-design-good.md"), "no-such-type")
    assert result["status"] == "skipped"

def test_deviation_status_on_missing():
    result = ch.check(str(FIX / "data-design-missing-headings.md"), "data-design")
    assert result["status"] == "deviation"
    assert "トレーサビリティ" in result["missing"]

def test_failopen_on_malformed_schema(tmp_path, monkeypatch):
    bad = tmp_path / "broken.json"
    bad.write_text("{ not valid json", encoding="utf-8")
    monkeypatch.setattr(ch, "SCHEMA_DIR", tmp_path)
    result = ch.check(str(FIX / "data-design-good.md"), "broken")
    assert result["status"] == "skipped"


# --- detailed-design-data（詳細設計・物理データ設計）スライス ---
# 必須見出し = 物理ER / テーブル定義 / 制約とインデックス / トレーサビリティ
# （目的とスコープは導入であり必須に含めない）。

_DD_REQUIRED = ["物理ER", "テーブル定義", "制約とインデックス", "トレーサビリティ"]

def test_dd_good_has_no_missing():
    result = ch.check(str(FIX / "detailed-design-data-good.md"), "detailed-design-data")
    assert result["status"] == "pass"
    assert result["missing"] == []

def test_dd_missing_physical_er_is_detected():
    # missing fixture は 物理ER を欠き、残り3見出しは持つ
    result = ch.check(str(FIX / "detailed-design-data-missing-headings.md"),
                      "detailed-design-data")
    assert result["status"] == "deviation"
    assert "物理ER" in result["missing"]
    # 残り3見出しは欠落しない（誤検出回帰防止）
    for h in ["テーブル定義", "制約とインデックス", "トレーサビリティ"]:
        assert h not in result["missing"]


# --- srs（要件定義・SRS）スライス ---
# 必須見出し = 機能要件一覧 / 非機能要件 / トレーサビリティ
# （目的とスコープ・ステークホルダー・ユースケースは必須に含めない）。
# 非機能要件の必須化＝P9（NFR 後回し禁止）の機械化。
# 機能要件を `機能要件一覧` に具体化する肝＝check_headings は部分一致ゆえ required `機能要件` は
# `非機能要件` の部分文字列（"機能要件" in "非機能要件" = True）になり、機能要件節が完全に欠落しても
# 非機能要件節の存在で誤って満たされたとみなされ status=pass で素通りしていた（偽 pass）。
# required を `機能要件一覧`（`機能要件一覧` ⊄ `非機能要件`）に具体化して包含を解消する
# （find_missing の部分一致ロジックは変えない＝他 doc_type が意図的部分一致に依存するため）。

_SRS_REQUIRED = ["機能要件一覧", "非機能要件", "トレーサビリティ"]

def test_srs_good_has_no_missing():
    result = ch.check(str(FIX / "srs-good.md"), "srs")
    assert result["status"] == "pass"
    assert result["missing"] == []

def test_srs_missing_nfr_is_detected():
    # missing fixture は 非機能要件 を欠き、機能要件一覧・トレーサビリティは持つ
    # （P9 後回し＝NFR 節欠落の検出例）
    result = ch.check(str(FIX / "srs-missing-headings.md"), "srs")
    assert result["status"] == "deviation"
    assert "非機能要件" in result["missing"]
    # 残り2見出しは欠落しない（誤検出回帰防止）
    for h in ["機能要件一覧", "トレーサビリティ"]:
        assert h not in result["missing"]

def test_srs_missing_functional_is_detected():
    # missing fixture は 機能要件一覧 を欠き、非機能要件＋トレーサビリティだけを持つ
    # （＝required `機能要件` が `非機能要件` の部分文字列だった頃に偽 pass していた構成）。
    # required を `機能要件一覧`（⊄ 非機能要件）に具体化したことで deviation で検出される。
    result = ch.check(str(FIX / "srs-missing-functional.md"), "srs")
    assert result["status"] == "deviation"
    assert "機能要件一覧" in result["missing"]
    # 残り2見出しは欠落しない（誤検出回帰防止＝偽 pass の裏面）
    for h in ["非機能要件", "トレーサビリティ"]:
        assert h not in result["missing"]


# --- test-case-spec（テスト・ケース仕様）スライス ---
# 必須見出し = テストケース / トレーサビリティ
# （目的とスコープ・テスト観点は必須に含めない）。
# トレーサビリティの必須化＝P6（テスト文書は要件を ID 参照）の機械化。

_TCS_REQUIRED = ["テストケース", "トレーサビリティ"]

def test_tcs_good_has_no_missing():
    result = ch.check(str(FIX / "test-case-spec-good.md"), "test-case-spec")
    assert result["status"] == "pass"
    assert result["missing"] == []

def test_tcs_missing_traceability_is_detected():
    # missing fixture は トレーサビリティ を欠き、テストケースは持つ
    # （P6 ID 参照の機械化＝トレーサビリティ節欠落の検出例）
    result = ch.check(str(FIX / "test-case-spec-missing-headings.md"), "test-case-spec")
    assert result["status"] == "deviation"
    assert "トレーサビリティ" in result["missing"]
    # 残る必須見出しは欠落しない（誤検出回帰防止）
    assert "テストケース" not in result["missing"]


# --- user-story（アジャイル・ユーザーストーリー）スライス ---
# 初の agile スライス。必須見出し = ユーザーストーリー / 受入基準。
# 受入基準（AC）節の必須化＝user-story スライスの機械層の主仕事（AC 欠落の検出）。
# それ以外の逸脱（主語/so that/実装動詞/AC件数/INVEST）は rubric の質的判定に委ねる（vocab は空・S4 非対称）。

_US_REQUIRED = ["ユーザーストーリー", "受入基準"]

def test_us_good_has_no_missing():
    result = ch.check(str(FIX / "user-story-good.md"), "user-story")
    assert result["status"] == "pass"
    assert result["missing"] == []

def test_us_missing_ac_is_detected():
    # missing fixture は 受入基準 を欠き、ユーザーストーリーは持つ
    # （AC 節欠落の検出＝user-story 機械層の主仕事）
    result = ch.check(str(FIX / "user-story-missing-headings.md"), "user-story")
    assert result["status"] == "deviation"
    assert "受入基準" in result["missing"]
    # 残る必須見出しは欠落しない（誤検出回帰防止）
    assert "ユーザーストーリー" not in result["missing"]


# --- acceptance-criteria（アジャイル・受入基準）スライス ---
# agile 2本目のスライス。必須見出し = 受入シナリオ / トレーサビリティ。
# トレーサビリティ節を持つ＝agile で初めて check_traceability が有効（skipped でなく）になる。
# Then 観測可能性は vocab（3語）で機械検出、GWT 構造・件数・トレース質は rubric の質的判定に委ねる。

_AC_REQUIRED = ["受入シナリオ", "トレーサビリティ"]

def test_ac_good_has_no_missing():
    result = ch.check(str(FIX / "acceptance-criteria-good.md"), "acceptance-criteria")
    assert result["status"] == "pass"
    assert result["missing"] == []

def test_ac_missing_traceability_is_detected():
    # missing fixture は トレーサビリティ を欠き、受入シナリオは持つ
    result = ch.check(str(FIX / "acceptance-criteria-missing-headings.md"), "acceptance-criteria")
    assert result["status"] == "deviation"
    assert "トレーサビリティ" in result["missing"]
    # 残る必須見出しは欠落しない（誤検出回帰防止）
    assert "受入シナリオ" not in result["missing"]


# --- external-design（ウォーターフォール基本設計・外部設計）スライス ---
# 必須見出し = 画面設計 / 外部インターフェース / トレーサビリティ
# 外部から観測可能な仕様（画面・帳票・外部 IF）の構造チェック。
# 内部実装マーカー（クラス図 / シーケンス図 / SQL / インデックス / テーブル定義）は
# vocab の禁止語で、ここでは見出しの存否のみ検査する。

_ED_REQUIRED = ["画面設計", "外部インターフェース", "トレーサビリティ"]

def test_ed_good_has_no_missing():
    result = ch.check(str(FIX / "external-design-good.md"), "external-design")
    assert result["status"] == "pass"
    assert result["missing"] == []

def test_ed_missing_if_is_detected():
    # missing fixture は 外部インターフェース を欠き、画面設計・トレーサビリティは持つ
    result = ch.check(str(FIX / "external-design-missing-headings.md"), "external-design")
    assert result["status"] == "deviation"
    assert "外部インターフェース" in result["missing"]
    # 残る2見出しは欠落しない（誤検出回帰防止）
    for h in ["画面設計", "トレーサビリティ"]:
        assert h not in result["missing"]


# --- architecture-design（ウォーターフォール基本設計・方式設計）スライス ---
# 必須見出し = アーキテクチャ方式 / 技術選定 / 横断懸念 / トレーサビリティ
# アーキテクチャスタイル・主要コンポーネント・技術選定・横断方針の構造チェック。
# 内部実装マーカー（クラス図 / メソッド仕様 / シーケンス図）は vocab の禁止語で検査する。
# SQL は技術名 PostgreSQL/NoSQL 等の部分文字列で誤爆するため vocab には入れず rubric で判定。

_AD_REQUIRED = ["アーキテクチャ方式", "技術選定", "横断懸念", "トレーサビリティ"]


def test_ad_good_has_no_missing():
    result = ch.check(str(FIX / "architecture-design-good.md"), "architecture-design")
    assert result["status"] == "pass"
    assert result["missing"] == []


def test_ad_missing_cross_concern_is_detected():
    # missing fixture は 横断懸念 を欠き、残り3見出しは持つ
    result = ch.check(str(FIX / "architecture-design-missing-headings.md"), "architecture-design")
    assert result["status"] == "deviation"
    assert "横断懸念" in result["missing"]
    # 残る3見出しは欠落しない（誤検出回帰防止）
    for h in ["アーキテクチャ方式", "技術選定", "トレーサビリティ"]:
        assert h not in result["missing"]


# --- nonfunctional-design（ウォーターフォール基本設計・非機能設計）スライス ---
# 必須見出し = 非機能要件 / 測定方法 / トレーサビリティ
# 「測定方法」を独立必須節にするのが肝＝非機能設計最大の痛み「具体グレード値はあるが
# 測定方法がない＝verifiable(P6) 違反」を見出し欠落で機械検出する。
# 実現手段マーカー（チューニング手順 / 計測スクリプト）は vocab の禁止語で検査する。
# 技術名・SQL・曖昧表現は誤爆ゆえ vocab に入れず rubric で判定。

_NFD_REQUIRED = ["非機能要件", "測定方法", "トレーサビリティ"]


def test_nfd_good_has_no_missing():
    result = ch.check(str(FIX / "nonfunctional-design-good.md"), "nonfunctional-design")
    assert result["status"] == "pass"
    assert result["missing"] == []


def test_nfd_missing_measurement_is_detected():
    # missing fixture は 測定方法 を欠き（具体値だけで測定方法なし＝verifiable 違反）、
    # 残り2見出しは持つ。測定方法欠落の機械検出を実証する。
    result = ch.check(str(FIX / "nonfunctional-design-missing-headings.md"), "nonfunctional-design")
    assert result["status"] == "deviation"
    assert "測定方法" in result["missing"]
    # 残る2見出しは欠落しない（誤検出回帰防止）
    for h in ["非機能要件", "トレーサビリティ"]:
        assert h not in result["missing"]


# --- operations-design（ウォーターフォール基本設計・運用/移行設計）スライス ---
# 必須見出し = 運用方針 / 移行方針 / トレーサビリティ
# 運用と移行を1スライスに統合し、運用側（監視・バックアップ・障害対応の方針）と
# 移行側（移行方針・切替・ロールバック）の双方の欠落を独立必須節で検出する。
# とりわけ「移行方針」を独立必須にするのが肝＝運用だけ書いて移行を落とす欠落を
# 見出し欠落で機械検出する（responsibility-map「運用/移行設計」を1細分に畳んだための仕掛け）。
# 実行手段マーカー（手順書 / 移行スクリプト）は vocab の禁止語で検査する。
# 技術名・SQL・「手順」単独は誤爆ゆえ vocab に入れず rubric で判定。

_OD_REQUIRED = ["運用方針", "移行方針", "トレーサビリティ"]


def test_od_good_has_no_missing():
    result = ch.check(str(FIX / "operations-design-good.md"), "operations-design")
    assert result["status"] == "pass"
    assert result["missing"] == []


def test_od_missing_migration_is_detected():
    # missing fixture は 移行方針 を欠き（運用だけで移行欠落）、残り2見出しは持つ。
    # 統合スライスで片側（移行）だけ落ちた欠落の機械検出を実証する。
    result = ch.check(str(FIX / "operations-design-missing-headings.md"), "operations-design")
    assert result["status"] == "deviation"
    assert "移行方針" in result["missing"]
    # 残る2見出しは欠落しない（誤検出回帰防止）
    for h in ["運用方針", "トレーサビリティ"]:
        assert h not in result["missing"]


# --- design-doc（アジャイル・Design Doc）スライス ---
# agile 3本目のスライス。必須見出し = Context / Non-Goals / トレーサビリティ。
# 必須を3本に絞る＝Design Doc は責務表上「全セクション強制記入＝逸脱」なので必須を増やすほど
# 哲学に反する（代替検討・横断懸念は推奨で必須にしない）。
# 機械表現の肝: 実見出しは `## Goals / Non-Goals`（スペース込み）で、required は `Non-Goals` を
# 入れる＝check_headings は部分一致なので、required に `Goals/Non-Goals`（スラッシュ込み）と書くと
# 実見出しのスペース込み `Goals / Non-Goals` に部分一致せず誤って欠落判定になる罠を避ける。
# Non-Goals 必須＝スコープ否定側（やらないこと）の欠落＝スコープクリープの主因を機械検出できる。

_DESIGN_DOC_REQUIRED = ["Context", "Non-Goals", "トレーサビリティ"]


def test_design_doc_good_has_no_missing():
    result = ch.check(str(FIX / "design-doc-good.md"), "design-doc")
    assert result["status"] == "pass"
    assert result["missing"] == []


def test_design_doc_missing_non_goals_is_detected():
    # missing fixture は Goals だけ書いて Non-Goals 節を欠く（Context と トレーサビリティ は持つ）。
    # required の `Non-Goals` が部分一致せず＝欠落検出。スコープ否定の欠落を機械検出する。
    result = ch.check(str(FIX / "design-doc-missing-headings.md"), "design-doc")
    assert result["status"] == "deviation"
    assert "Non-Goals" in result["missing"]
    # 残る2見出しは欠落しない（誤検出回帰防止）
    for h in ["Context", "トレーサビリティ"]:
        assert h not in result["missing"]


# --- test-plan（テスト・計画）スライス ---
# WF テスト工程の2本目（1本目＝test-case-spec＝ケース仕様）。テスト文書階層の「計画」レベル。
# 必須見出し = スコープ / 終了基準 / トレーサビリティ。
# 「終了基準」を独立必須にするのが肝＝Test Plan 最大の痛み「測定可能な完了条件が無い」
# （P6 verifiable 違反）を見出し欠落で機械検出する。「スコープ」は対象外+理由（スコープ否定）を
# 含ませる節（Design Doc の Non-Goals 同型）。体制・スケジュール・リスク等は推奨で必須にしない
# （IEEE 829 多セクションだが小さい計画で全節埋めさせる gold plating を避ける）。

_TP_REQUIRED = ["スコープ", "終了基準", "トレーサビリティ"]


def test_tp_good_has_no_missing():
    result = ch.check(str(FIX / "test-plan-good.md"), "test-plan")
    assert result["status"] == "pass"
    assert result["missing"] == []


def test_tp_missing_exit_criteria_is_detected():
    # missing fixture は 終了基準 を欠き（測定可能な完了条件の欠落＝verifiable 違反）、
    # スコープ・トレーサビリティは持つ。完了判定節欠落の機械検出を実証する。
    result = ch.check(str(FIX / "test-plan-missing-headings.md"), "test-plan")
    assert result["status"] == "deviation"
    assert "終了基準" in result["missing"]
    # 残る2見出しは欠落しない（誤検出回帰防止）
    for h in ["スコープ", "トレーサビリティ"]:
        assert h not in result["missing"]


# --- test-design-spec（テスト・設計仕様）スライス ---
# WF テスト工程の3本目（1本目＝test-case-spec＝ケース仕様・2本目＝test-plan＝計画）。
# テスト文書階層の「設計仕様」レベル＝ケース仕様の直上。
# 必須見出し = テスト条件 / 網羅方針 / トレーサビリティ。
# 「網羅方針」を独立必須にするのが肝＝設計仕様の核は「テスト条件をどう網羅するか」（テスト技法・
# カバレッジ）であり、テスト条件だけ並べて網羅の根拠が無い設計仕様＝設計仕様の体をなさない。
# 網羅方針節の欠落を見出し欠落で機械検出する。テスト観点・前提制約は推奨で必須にしない
# （IEEE 829 系の多セクションを全強制しない gold plating を避ける＝test-plan/design-doc と同方針）。

_TDS_REQUIRED = ["テスト条件", "網羅方針", "トレーサビリティ"]


def test_tds_good_has_no_missing():
    result = ch.check(str(FIX / "test-design-spec-good.md"), "test-design-spec")
    assert result["status"] == "pass"
    assert result["missing"] == []


def test_tds_missing_coverage_strategy_is_detected():
    # missing fixture は 網羅方針 を欠き（網羅の根拠が無い設計仕様）、
    # テスト条件・トレーサビリティは持つ。網羅方針節欠落の機械検出を実証する。
    result = ch.check(str(FIX / "test-design-spec-missing-headings.md"), "test-design-spec")
    assert result["status"] == "deviation"
    assert "網羅方針" in result["missing"]
    # 残る2見出しは欠落しない（誤検出回帰防止）
    for h in ["テスト条件", "トレーサビリティ"]:
        assert h not in result["missing"]


# --- test-procedure-spec（テスト・手順仕様）スライス ---
# WF テスト工程の4本目（1本目＝test-case-spec＝ケース仕様・2本目＝test-plan＝計画・
# 3本目＝test-design-spec＝設計仕様）。テスト文書階層の最下位「手順仕様」＝ケース仕様の直下。
# 必須見出し = 前提 / 実行手順 / トレーサビリティ。required の「前提」は実見出し「前提・セットアップ」に
# 部分一致する（中黒込みの required にすると完全一致依存になりうるため「前提」で機械表現）。
# 「前提・セットアップ」を独立必須にするのが肝＝手順だけあって開始状態・環境が不明なら再現不能。
# 前提節の欠落を見出し欠落で機械検出する（nonfunctional の測定方法必須化・test-design-spec の
# 網羅方針必須化と同型）。事後処理・実行環境は推奨で必須にしない（gold plating を避ける）。

_TPS_REQUIRED = ["前提", "実行手順", "トレーサビリティ"]


def test_tps_good_has_no_missing():
    result = ch.check(str(FIX / "test-procedure-spec-good.md"), "test-procedure-spec")
    assert result["status"] == "pass"
    assert result["missing"] == []


def test_tps_missing_prerequisite_is_detected():
    # missing fixture は 前提（前提・セットアップ）を欠き（開始状態・環境が不明＝再現不能）、
    # 実行手順・トレーサビリティは持つ。前提節欠落の機械検出を実証する。
    result = ch.check(str(FIX / "test-procedure-spec-missing-headings.md"), "test-procedure-spec")
    assert result["status"] == "deviation"
    assert "前提" in result["missing"]
    # 残る2見出しは欠落しない（誤検出回帰防止）
    for h in ["実行手順", "トレーサビリティ"]:
        assert h not in result["missing"]


# --- test-strategy（テスト・戦略）スライス ---
# WF テスト工程の5本目＝最上位（1本目＝test-case-spec＝ケース仕様・2本目＝test-plan＝計画・
# 3本目＝test-design-spec＝設計仕様・4本目＝test-procedure-spec＝手順仕様）。これで
# テスト文書階層の5レベル（戦略/計画/設計仕様/ケース仕様/手順仕様）が完備する。
# 必須見出し = テスト方針 / テストレベル / トレーサビリティ。required の「テストレベル」は
# 実見出し「テストレベル/タイプ」に部分一致する（中黒/スラッシュ込みの required にすると完全一致
# 依存になりうるため「テストレベル」で機械表現＝cycle-14 Goals/Non-Goals・test-procedure-spec の
# 前提→前提・セットアップ と同型）。「テストレベル/タイプ」を独立必須にするのが肝＝戦略の核は
# 組織標準のテストレベル/タイプの枠組みであり、それを欠くと各プロジェクトが拠り所無くレベルを決める。
# 自動化方針・テスト環境標準・組織体制は推奨で必須にしない（gold plating を避ける）。

_TS_REQUIRED = ["テスト方針", "テストレベル", "トレーサビリティ"]


def test_ts_good_has_no_missing():
    result = ch.check(str(FIX / "test-strategy-good.md"), "test-strategy")
    assert result["status"] == "pass"
    assert result["missing"] == []


def test_ts_missing_test_level_is_detected():
    # missing fixture は テストレベル（テストレベル/タイプ）を欠き（組織標準の枠組みが不明）、
    # テスト方針・トレーサビリティは持つ。テストレベル/タイプ節欠落の機械検出を実証する。
    # required の「テストレベル」が実見出し「テストレベル/タイプ」に部分一致する設計のため、
    # missing fixture では「テストレベル」の語を H1/他見出しに紛れ込ませない（cycle-15/16/17 のデコイ罠回避）。
    result = ch.check(str(FIX / "test-strategy-missing-headings.md"), "test-strategy")
    assert result["status"] == "deviation"
    assert "テストレベル" in result["missing"]
    # 残る2見出しは欠落しない（誤検出回帰防止）
    for h in ["テスト方針", "トレーサビリティ"]:
        assert h not in result["missing"]


# --- detailed-design-process（詳細設計・処理詳細）スライス ---
# WF 詳細設計の2本目（1本目＝detailed-design-data＝データ詳細・cycle-3）。データ詳細と対をなす「処理詳細」。
# 必須見出し = モジュール構造 / 処理仕様 / トレーサビリティ。required の「モジュール構造」は
# 実見出し「クラス・モジュール構造」に部分一致する（required に `クラス` を使うと本文「クラス図」言及や
# 推奨節で誤爆しやすいため、デコイ低リスクな後半語「モジュール構造」で機械表現＝cycle-14 Goals/Non-Goals・
# cycle-18 テストレベル と同型）。「処理仕様」を独立必須にするのが肝＝処理詳細の核はメソッド仕様
# （引数/戻り値/エラー処理）・処理ロジック・IPO であり、それを欠くと処理詳細の体をなさない。
# シーケンス図・アクティビティ図・状態遷移・例外処理詳細は推奨で必須にしない（gold plating を避ける）。

_DDP_REQUIRED = ["モジュール構造", "処理仕様", "トレーサビリティ"]


def test_ddp_good_has_no_missing():
    result = ch.check(str(FIX / "detailed-design-process-good.md"), "detailed-design-process")
    assert result["status"] == "pass"
    assert result["missing"] == []


def test_ddp_missing_process_spec_is_detected():
    # missing fixture は 処理仕様 を欠き（メソッド仕様・処理ロジックが無い）、
    # モジュール構造・トレーサビリティは持つ。処理仕様節欠落の機械検出を実証する。
    # 「処理仕様」が実見出しに部分一致する設計のため、missing fixture では「処理仕様」の語を
    # H1/他見出しに紛れ込ませない（cycle-15/16/17/18 のデコイ罠回避）。
    result = ch.check(str(FIX / "detailed-design-process-missing-headings.md"),
                      "detailed-design-process")
    assert result["status"] == "deviation"
    assert "処理仕様" in result["missing"]
    # 残る2見出しは欠落しない（誤検出回帰防止）
    for h in ["モジュール構造", "トレーサビリティ"]:
        assert h not in result["missing"]


# --- adr（アジャイル・Architecture Decision Record）スライス ---
# agile 4本目のスライス（1=user-story・2=acceptance-criteria・3=design-doc）。
# 必須見出し = Context / Decision / Status / 却下案 / Consequences。
# Nygard（2011）の Title（H1）/ Context / Decision / Status / Consequences に却下案を独自追加する。
# 必須を5節に絞る肝＝粒度境界のみを doc-standards が定義し、採番（ADR-NNNN）・生成・内容評価は
# architecture-decision-records スキルが所有する（S5・二重定義回避）。「却下案」必須＝Why の片側
# （却下理由）欠落＝事後正当化の主因を機械検出する（design-doc の Non-Goals 必須と同型のスコープ否定側強制）。
# Status は必須、関連 ADR は推奨で必須にしない（gold plating を避ける）。
# デコイ罠回避（ADR 固有・最重要）: ADR の正式名 "Architecture Decision Record" を H1/導入見出しに
# 英語フルで書くと required `Decision` が H1 に部分一致してデコイになり、`## Decision` 節を削っても
# 誤 pass する。good/missing fixture とも H1 は英語フル表記を避け（"決定記録" は `Decision` を含まない）、
# 導入見出しは `位置づけ`。required 各語が実見出しに1つだけ部分一致する設計（cycle-15〜19 のデコイ罠の最難関）。

_ADR_REQUIRED = ["Context", "Decision", "Status", "却下案", "Consequences"]


def test_adr_good_has_no_missing():
    result = ch.check(str(FIX / "adr-good.md"), "adr")
    assert result["status"] == "pass"
    assert result["missing"] == []


def test_adr_missing_rejected_alternatives_is_detected():
    # missing fixture は 却下案 を欠き（Why の片側＝採用案ありきで代替の比較なし）、
    # Context・Decision・Status・Consequences は持つ。却下案節欠落の機械検出を実証する。
    # デコイ罠回避: 欠落させたい `却下案` を H1/他見出しに紛れ込ませない。逆に required の
    # Context/Decision/Status/Consequences は実見出しに存在するので欠落しない（H1 の英語フル表記は避ける）。
    result = ch.check(str(FIX / "adr-missing-headings.md"), "adr")
    assert result["status"] == "deviation"
    assert "却下案" in result["missing"]
    # 残る4見出しは欠落しない（誤検出回帰防止＝デコイで誤 pass していないことの裏面）
    for h in ["Context", "Decision", "Status", "Consequences"]:
        assert h not in result["missing"]


# --- rfc（アジャイル・Request for Comments）スライス ---
# agile 5本目のスライス（1=user-story・2=acceptance-criteria・3=design-doc・4=adr）。
# 必須見出し = 提案内容 / 代替案 / 未解決の論点 / トレーサビリティ。
# RFC は ADR と時間軸で対をなす「決定前の提案/探索文書」＝代替案は『まだ生きている選択肢』
# （ADR の却下案＝『葬った選択肢』の対）。「未解決の論点」を独立必須にするのが RFC の核＝
# 『未決を装った既決＝RFC の体をなさない』を見出し欠落で機械検出（ADR の却下案必須・
# design-doc の Non-Goals 必須と同型のスコープ否定側強制）。動機・影響範囲・Prior art は推奨で
# 必須にしない（gold plating を避ける）。トレースは独立節を持ち check_traceability 有効
# （design-doc/acceptance-criteria 型・ADR とは非対称＝ADR は外部スキル所有形式と衝突回避で
# Context 内に書き skipped にした。RFC は doc-standards 固有で衝突しないため独立節を持つ）。
# デコイ罠回避: required 各語（提案内容/代替案/未解決の論点/トレーサビリティ）を H1・導入見出し
# （位置づけ）・推奨節・他見出しに紛れ込ませない。「提案」単独は本文「〜を提案する」で誤爆するため
# discriminating な複合語 `提案内容` を required にし実見出しを `## 提案内容` にする。H1 は
# `# RFC: ...（コメント要求・...）` で required 4語を一切含まない。

_RFC_REQUIRED = ["提案内容", "代替案", "未解決の論点", "トレーサビリティ"]


def test_rfc_good_has_no_missing():
    result = ch.check(str(FIX / "rfc-good.md"), "rfc")
    assert result["status"] == "pass"
    assert result["missing"] == []


def test_rfc_missing_open_questions_is_detected():
    # missing fixture は 未解決の論点 を欠き（未決を装った既決の主因＝決着していない問いを
    # 表に出さない）、提案内容・代替案・トレーサビリティは持つ。論点節欠落の機械検出を実証する。
    # デコイ罠回避: 欠落させたい `未解決の論点` を H1/他見出し/本文見出しに紛れ込ませない
    # （cycle-16/cycle-20 で実装者が踏んだ罠＝missing fixture の H1 に required 語が残り偽 pass する罠を避ける）。
    result = ch.check(str(FIX / "rfc-missing-headings.md"), "rfc")
    assert result["status"] == "deviation"
    assert "未解決の論点" in result["missing"]
    # 残る3見出しは欠落しない（誤検出回帰防止＝デコイで誤 pass していないことの裏面）
    for h in ["提案内容", "代替案", "トレーサビリティ"]:
        assert h not in result["missing"]


# --- pr-faq（アジャイル・Amazon Working Backwards／PR-FAQ）スライス ---
# agile 6本目のスライス（1=user-story・2=acceptance-criteria・3=design-doc・4=adr・5=rfc）。
# 必須見出し = プレスリリース / 想定問答 / 成功指標 / トレーサビリティ。
# PR-FAQ は『顧客視点の未来プレスリリース（1p）＋想定問答（FAQ・5p）で企画を逆算する』文書＝
# プレスリリースと想定問答の2部構成が定義そのもの（外せない）。「成功指標」を独立必須にするのが
# 機械検出の核＝『測定可能な成功条件の欠落＝絵に描いた餅』を見出し欠落で機械検出
# （ADR の却下案・design-doc の Non-Goals・RFC の未解決の論点・nonfunctional の測定方法 必須化と
# 同型＝核の否定/欠落側を独立必須にして機械検出する。Working Backwards の『どうなれば成功か』を譲らない）。
# 顧客の課題・社内向けの補足（Internal FAQ）・利用開始方法 は推奨で必須にしない（gold plating を避ける）。
# トレースは独立節を持ち check_traceability 有効（design-doc/acceptance-criteria/rfc 型・ADR とは非対称）。
# デコイ罠回避（最重要）: check_headings は部分一致ゆえ `FAQ`（3文字）を required にすると H1 や
# doc_type 名「PR-FAQ」に部分一致してデコイ化する（"FAQ" in "PR-FAQ" = True）。よって required は
# 日本語複合語 `想定問答` を使い実見出しを `## 想定問答（FAQ）` にする（"想定問答" は H1「PR-FAQ」に
# 含まれない）。H1 は `# PR-FAQ: ...（Working Backwards・...）` で required 4語
# （プレスリリース/想定問答/成功指標/トレーサビリティ）を一切含まない（"PR-FAQ" の "FAQ" は required
# `想定問答` と一致しないので安全）。Internal FAQ の推奨節は `## 社内向けの補足` 等にして「想定問答」を
# 含めない（2見出しに「想定問答」を入れるとデコイ化する）。

_PR_FAQ_REQUIRED = ["プレスリリース", "想定問答", "成功指標", "トレーサビリティ"]


def test_pr_faq_good_has_no_missing():
    result = ch.check(str(FIX / "pr-faq-good.md"), "pr-faq")
    assert result["status"] == "pass"
    assert result["missing"] == []


def test_pr_faq_missing_success_metrics_is_detected():
    # missing fixture は 成功指標 を欠き（測定可能な成功条件の欠落＝絵に描いた餅の主因）、
    # プレスリリース・想定問答・トレーサビリティは持つ。成功指標節欠落の機械検出を実証する。
    # デコイ罠回避: 欠落させたい `成功指標` を H1/他見出し/本文見出しに紛れ込ませない（decoy-clean）。
    # とりわけ required `想定問答` を実見出し `## 想定問答（FAQ）` 1つだけに部分一致させ、
    # H1「PR-FAQ」の "FAQ" がデコイにならないこと（"想定問答" を含まない）をこの fixture でも保つ。
    result = ch.check(str(FIX / "pr-faq-missing-headings.md"), "pr-faq")
    assert result["status"] == "deviation"
    assert "成功指標" in result["missing"]
    # 残る3見出しは欠落しない（誤検出回帰防止＝デコイで誤 pass していないことの裏面）
    for h in ["プレスリリース", "想定問答", "トレーサビリティ"]:
        assert h not in result["missing"]
