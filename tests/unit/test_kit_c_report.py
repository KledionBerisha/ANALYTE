"""Raporti i grupit C: ndarja sipas llojit dhe mbivendosja me gjeneruesin."""

from __future__ import annotations

from evaluation import kit_c_report

HEADER = "id,fjalia,lloji,polariteti,siguria,analiti,drejtimi,shenim\n"


def _write(tmp_path, rows):
    path = tmp_path / "C.csv"
    path.write_text(HEADER + "\n".join(rows) + "\n", encoding="utf-8")
    return path


def test_report_counts_correct_and_unextracted_rows_separately(tmp_path):
    path = _write(
        tmp_path,
        [
            "C01,TSH është mbi intervalin referent.,finding,affirmed,confirmed,Hormoni stimulues i tiroides,increased,",
            "C02,Rekomandohet kontroll pas tre muajsh.,recommendation,affirmed,confirmed,,unspecified,",
            "C03,Një fjali që nuk thotë asgjë mjekësore.,finding,affirmed,confirmed,,unspecified,",
        ],
    )
    report = kit_c_report.build_report(path, corpus=tmp_path / "pa-korpus")
    assert report["all"]["rows"] == 3
    assert report["all"]["all_correct"] == 2 and report["all"]["extracted"] == 2
    assert [r["id"] for r in report["failures"]] == ["C03"]
    assert "identical_to_generator" not in report  # pa korpus nuk pretendohet asgjë


def test_groups_follow_the_row_numbers_of_the_recipe(tmp_path):
    rows = [
        f"C{n:02d},TSH është mbi intervalin referent.,finding,affirmed,confirmed,Hormoni stimulues i tiroides,increased,"
        for n in (1, 16, 26, 36, 46)
    ]
    report = kit_c_report.build_report(_write(tmp_path, rows), corpus=tmp_path / "pa-korpus")
    assert [g["rows"] for g in report["by_group"].values()] == [1, 1, 1, 1, 1]
    assert list(report["by_group"]) == [name for name, _, _ in kit_c_report.GROUPS]


def test_expected_analyte_is_resolved_to_its_code_before_comparison():
    expected = kit_c_report._expected(
        {
            "lloji": "finding",
            "polariteti": "affirmed",
            "siguria": "confirmed",
            "analiti": "Hormoni stimulues i tiroides",
            "drejtimi": "increased",
        }
    )
    assert expected["analiti"] == "3016-3"


def test_installed_group_c_loads_without_errors():
    """Skedari i autorit kalon vlerësuesin e formatit: asnjë rresht i refuzuar."""
    from evaluation import kits

    rows = kits.read_rows(kits.KIT_DIR / "C_narrativa.csv", kits.C_COLUMNS)
    assert len(rows) == 60
    assert kits.check_narrative(rows)[1] == []
