"""
Kontrolli i besueshmërisë i OCR-së (ADR 0020).

"""

from __future__ import annotations

from decimal import Decimal

import pytest

from analyte.catalog import analytes_by_code
from analyte.domain.enums import AnalyteStatus, ReferenceSource
from analyte.domain.models import BoundingBox
from analyte.grounding.branch_a import loinc, ocr_guard
from analyte.grounding.branch_a.extract import extract
from analyte.ingestion.pdf_text import PageText, TextFragment, TextRow

D = Decimal


def _analyte(name: str):
    return analytes_by_code()[loinc.resolve(name)]


# intervali i dëmtuar


@pytest.mark.parametrize(
    ("name", "low", "high", "damaged"),
    [
        ("Kaliumi", D("35"), D("51"), True),  # 3,5 - 5,1 pa presje
        ("Kaliumi", D("335"), D("531"), True),  # zhurmë shtesë, përsëri ≈100x
        ("Fosfori", D("25"), D("45"), True),  # 2,5 - 4,5
        (
            "Bilirubina totale",
            D("20"),
            D("1200"),
            True,
        ),  # 0,20 - 1,20: kufijtë humbën presje të ndryshme (100x dhe 1000x)
        ("Proteina totale", D("64"), D("830"), True),  # 6,4 - 8,3
        ("Kaliumi", D("3.6"), D("5.2"), False),  # laborator me kufij pak të ndryshëm
        ("Kaliumi", D("3.5"), D("5.1"), False),  # saktësisht tabela
        ("Glukoza", D("70"), D("99"), False),  # analit pa presje: kufijtë e vërtetë janë të mëdhenj
        ("Kaliumi", None, None, False),
    ],
)
def test_a_printed_interval_ten_or_a_hundred_times_the_table_is_damaged(name, low, high, damaged):
    assert ocr_guard.damaged_interval(_analyte(name), low, high) is damaged


# vlera e dyshimtë


def test_a_value_without_a_separator_above_the_interval_that_fits_after_one_shift_is_suspect():
    ht = _analyte("Hematokriti")  # shtypet me një presje, intervali 40,0 - 52,0
    assert ocr_guard.lost_decimal(ht, "466", "%", D("466"), D("40.0"), D("52.0"))


@pytest.mark.parametrize(
    ("text", "value", "low", "high", "why"),
    [
        ("46,6", D("46.6"), D("40.0"), D("52.0"), "ka presje"),
        ("47", D("47"), D("40.0"), D("52.0"), "brenda intervalit; nuk është e dyshimtë"),
        (
            "620",
            D("620"),
            D("40.0"),
            D("52.0"),
            "as 62,0 as 6,20 nuk është brenda: nuk është presje e humbur",
        ),
        (
            "9",
            D("9"),
            D("40.0"),
            D("52.0"),
            "nën intervalin: presja humb vetëm duke e fryrë vlerën",
        ),
    ],
)
def test_it_does_not_touch_what_is_not_the_lost_decimal_pattern(text, value, low, high, why):
    ht = _analyte("Hematokriti")
    assert not ocr_guard.lost_decimal(ht, text, "%", value, low, high), why


def test_a_percentage_above_one_hundred_is_impossible_by_definition():
    ht = _analyte("Hematokriti")
    assert ocr_guard.impossible_percentage(ht, "%", D("598"))
    assert ocr_guard.impossible_percentage(ht, "", D("166"))
    assert not ocr_guard.impossible_percentage(ht, "%", D("59.8"))
    # njësi tjetër: asnjë kufi
    assert not ocr_guard.impossible_percentage(_analyte("Glukoza"), "mg/dL", D("600"))


def test_an_impossible_percentage_is_rejected_on_a_scanned_page_only():
    ocr_row = _page(_row("Hematokriti", "166", "%", "40,0 - 52,0"), ocr=True)
    assert extract(ocr_row, ocr_guard=True).rejection_counts() == {
        "vlerë e pamundur (OCR): përqindje mbi 100": 1
    }
    text_row = _page(_row("Hematokriti", "166", "%", "40,0 - 52,0"), ocr=False)
    assert len(extract(text_row, ocr_guard=True).findings) == 1


def test_an_analyte_printed_without_decimals_is_never_suspect():
    glucose = _analyte("Glukoza")  # 0 presje: "600" është vlerë e mundshme
    assert not ocr_guard.lost_decimal(glucose, "600", "mg/dL", D("600"), D("70"), D("99"))


# nxjerrja e plotë


def _row(*texts: str) -> TextRow:
    fragments = tuple(
        TextFragment(t, BoundingBox(x0=100.0 * i, y0=10.0, x1=100.0 * i + 50, y1=20.0))
        for i, t in enumerate(texts)
    )
    return TextRow(page=1, fragments=fragments)


def _page(*rows: TextRow, ocr: bool) -> tuple[PageText, ...]:
    return (PageText(number=1, rows=rows, ocr=ocr),)


def test_a_damaged_printed_interval_is_replaced_by_the_table_and_the_value_is_classified_correctly():
    # Vlera e saktë 3,9; OCR-ja e lexoi intervalin "3,6 - 5,2" si "36 - 52". Pa kontroll: "e ulët" (3,9 < 36).
    pages = _page(_row("Kaliumi", "3,9", "mmol/L", "36 - 52"), _row("Gjinia: Mashkull"), ocr=True)

    guarded = extract(pages, ocr_guard=True)
    (finding,) = guarded.findings
    assert finding.ref_source is ReferenceSource.INTERNAL_TABLE
    assert finding.status is AnalyteStatus.NORMAL
    assert guarded.corrections and "interval i dëmtuar" in guarded.corrections[0][1]

    raw = extract(pages, ocr_guard=False)
    assert raw.findings[0].status is AnalyteStatus.LOW  # sjellja e E3 pa kontroll
    assert raw.corrections == ()


def test_a_suspect_value_is_rejected_not_interpreted():
    # 3,9 pa presje: del "e lartë"
    pages = _page(_row("Kaliumi", "39", "mmol/L", "3,5 - 5,1"), ocr=True)

    guarded = extract(pages, ocr_guard=True)
    assert guarded.findings == ()
    assert guarded.rejection_counts() == {"vlerë e dyshimtë (OCR): presja dhjetore mungon": 1}

    raw = extract(pages, ocr_guard=False)
    # gabimi i E3: vlerë normale del e lartë
    assert raw.findings[0].status in (
        AnalyteStatus.HIGH,
        AnalyteStatus.CRITICAL_HIGH,
    )


def test_a_text_layer_page_is_never_guarded():
    pages = _page(_row("Hematokriti", "466", "%", "40,0 - 52,0"), ocr=False)
    # teksti i PDF-së është i saktë; nuk preket
    assert len(extract(pages, ocr_guard=True).findings) == 1


def test_a_correct_scanned_row_passes_through_unchanged():
    pages = _page(_row("Hematokriti", "46,6", "%", "40,0 - 52,0"), ocr=True)
    guarded = extract(pages, ocr_guard=True)
    assert guarded.findings and guarded.findings[0].status is AnalyteStatus.NORMAL
    assert guarded.corrections == () and guarded.rejected == ()
