"""
Testet e Degës A: lexim, njohje, normalizim, zgjidhje intervali.

"""

from decimal import Decimal

import pytest

from analyte.catalog import Sex, analytes_by_code
from analyte.domain.enums import AnalyteStatus, ReferenceSource
from analyte.domain.models import BoundingBox
from analyte.grounding.branch_a import loinc, reference
from analyte.grounding.branch_a.extract import extract, find_patient_sex, parse_row
from analyte.grounding.branch_a.normalize import (
    normalize_unit,
    parse_number,
    split_value_and_unit,
    to_canonical,
)
from analyte.ingestion.pdf_text import PageText, TextFragment, TextRow, group_into_rows
from analyte.ingestion.router import Channel, route

GLUCOSE = "2345-7"
HEMOGLOBIN = "718-7"
CREATININE = "2160-0"


# Numrat dhe njësitë


@pytest.mark.parametrize(
    "text,expected",
    [("13,4", Decimal("13.4")), ("13.4", Decimal("13.4")), ("128", Decimal(128))],
)
def test_decimal_separator_is_accepted_either_way(text, expected):
    assert parse_number(text) == expected


@pytest.mark.parametrize("text", ["", "abc", "1.234,5", "12-14", "H", "1,2,3"])
def test_non_numbers_are_refused(text):
    assert parse_number(text) is None


def test_thousands_separator_is_refused_rather_than_guessed():
    """ "1.234" mund të jetë njëmijë e dyqind ose një presje e tridhjetë e
    katër. Refuzimi është gabim i dukshëm; hamendja është gabim i heshtur
    me faktor një mijë."""
    assert parse_number("1.234") == Decimal("1.234")
    assert parse_number("1.234.567") is None


@pytest.mark.parametrize(
    "printed,expected",
    [("mg/dl", "mg/dL"), ("MG/DL", "mg/dL"), ("µmol/L", "umol/L"), ("g / dL", "g/dL")],
)
def test_unit_spelling_is_normalized(printed, expected):
    assert normalize_unit(printed) == expected


def test_value_and_unit_split_from_one_cell():
    assert split_value_and_unit("13,4 g/dL") == (Decimal("13.4"), "g/dL")
    assert split_value_and_unit("128") == (Decimal(128), "")
    assert split_value_and_unit("pa vlerë") is None


def test_alternate_unit_is_converted_to_canonical():
    creatinine = analytes_by_code()[CREATININE]
    converted = to_canonical(creatinine, Decimal(88), "umol/L")
    assert converted is not None
    value, unit = converted
    assert unit == "mg/dL"
    assert value == Decimal("1.00")


def test_unknown_unit_is_not_silently_accepted():
    """Vlera në njësi të panjohur nuk krahasohet dot me asnjë interval;
    thirrësi duhet ta shënojë të painterpretueshme dhe jo ta kalojë."""
    assert to_canonical(analytes_by_code()[GLUCOSE], Decimal(5), "parsec") is None


# Harta LOINC


@pytest.mark.parametrize(
    "printed,code",
    [
        ("Hemoglobina", HEMOGLOBIN),
        ("HGB", HEMOGLOBIN),
        ("hb", HEMOGLOBIN),
        ("ALT (GPT)", "1742-6"),
        ("Vol. mes. eritrocitar", "787-2"),
        ("Glukoza (esëll)", GLUCOSE),
    ],
)
def test_printed_names_map_to_their_code(printed, code):
    assert loinc.resolve(printed) == code


def test_diacritics_do_not_decide_identity():
    """OCR-ja i ngatërron rregullisht ë me e dhe ç me c. Një hartë që i
    dallon do të dështonte pikërisht te kanali ku ndihma nevojitet më shumë."""
    assert loinc.resolve("Pllakezat") == loinc.resolve("Pllakëzat")


def test_unknown_name_stays_unknown():
    """Asnjë përputhje e afërt: "Kalciumi" dhe "Kaliumi" ndryshojnë për një
    shkronjë dhe ngatërrimi i tyre do të hynte i heshtur në një shpjegim."""
    assert loinc.resolve("Kaliumi") != loinc.resolve("Kalciumi")
    assert loinc.resolve("Substancë e panjohur") is None


# Intervali referent


@pytest.mark.parametrize(
    "printed,expected",
    [
        ("70 - 99", (Decimal(70), Decimal(99))),
        ("3,5 – 5,1", (Decimal("3.5"), Decimal("5.1"))),
        ("< 200", (None, Decimal(200))),
        ("> 40", (Decimal(40), None)),
    ],
)
def test_printed_intervals_are_parsed(printed, expected):
    assert reference.parse_printed(printed) == expected


@pytest.mark.parametrize("printed", ["99 - 70", "abc - def", "70", ""])
def test_malformed_intervals_are_refused(printed):
    assert reference.parse_printed(printed) is None


def test_printed_interval_wins_over_the_internal_table():
    """Laboratori e di me çfarë metode ka matur; tabela jonë jo."""
    glucose = analytes_by_code()[GLUCOSE]
    resolved = reference.resolve(glucose, "65 - 105", "mg/dL", Sex.MALE)
    assert resolved.source is ReferenceSource.DOCUMENT
    assert (resolved.low, resolved.high) == (Decimal(65), Decimal(105))


def test_printed_interval_is_converted_like_the_value():
    creatinine = analytes_by_code()[CREATININE]
    resolved = reference.resolve(creatinine, "62 - 115", "umol/L", Sex.MALE)
    assert resolved.source is ReferenceSource.DOCUMENT
    assert resolved.low == Decimal("0.70") and resolved.high == Decimal("1.30")


def test_internal_table_is_used_when_nothing_is_printed():
    resolved = reference.resolve(analytes_by_code()[GLUCOSE], None, "mg/dL", Sex.FEMALE)
    assert resolved.source is ReferenceSource.INTERNAL_TABLE
    assert resolved.has_bounds


def test_unknown_sex_leaves_the_interval_unresolved():
    """Zgjedhja e intervalit me short do të ishte shkelje e SP5 e maskuar
    si mbulim."""
    resolved = reference.resolve(analytes_by_code()[HEMOGLOBIN], None, "g/dL", None)
    assert resolved.source is ReferenceSource.NONE
    assert not resolved.has_bounds


# Segmentimi i rreshtave


def _fragment(text: str, x0: float, baseline: float) -> TextFragment:
    return TextFragment(
        text=text, bbox=BoundingBox(x0=x0, y0=baseline - 10, x1=x0 + 40, y1=baseline)
    )


def test_fragments_on_one_baseline_become_one_row():
    fragments = [
        _fragment("Glukoza", 56, 200),
        _fragment("128", 300, 200.5),
        _fragment("mg/dL", 310, 200),
        _fragment("Kaliumi", 56, 216),
    ]
    rows = group_into_rows(fragments, page=1)
    assert len(rows) == 2
    assert [f.text for f in rows[0].fragments] == ["Glukoza", "128", "mg/dL"]


def test_data_row_is_split_into_columns():
    row = TextRow(
        page=1,
        fragments=(
            _fragment("Glukoza", 56, 200),
            _fragment("128", 300, 200),
            _fragment("mg/dL", 310, 200),
            _fragment("70 - 99", 390, 200),
            _fragment("H", 520, 200),
        ),
    )
    raw = parse_row(row)
    assert raw is not None
    assert (raw.name, raw.value_text, raw.unit_text) == ("Glukoza", "128", "mg/dL")
    assert raw.interval_text == "70 - 99"
    assert raw.flag == "H"


def test_joined_value_and_unit_is_split():
    row = TextRow(
        page=1,
        fragments=(_fragment("Hb", 56, 200), _fragment("13,4 g/dL", 280, 200)),
    )
    raw = parse_row(row)
    assert raw is not None and raw.value_text == "13,4" and raw.unit_text == "g/dL"


@pytest.mark.parametrize(
    "fragments",
    [
        [("HEMOGRAMË E PLOTË", 56)],
        [("Analiti", 56), ("Rezultati", 300), ("Intervali referent", 390)],
        [("Mosha: 75 vjeç", 56)],
        [("Pacienti: Arben Hoxha", 56), ("Data e analizës: 21.01.2026", 320)],
    ],
)
def test_header_and_title_rows_are_not_data(fragments):
    row = TextRow(page=1, fragments=tuple(_fragment(t, x, 200) for t, x in fragments))
    assert parse_row(row) is None


def test_patient_sex_is_read_from_the_header():
    page = PageText(
        number=1,
        rows=(TextRow(page=1, fragments=(_fragment("Gjinia: Femër", 56, 100),)),),
    )
    assert find_patient_sex((page,)) is Sex.FEMALE


# Skedari i artë: dokument i plotë, nga PDF-ja te gjetjet


@pytest.fixture(scope="module")
def golden(tmp_path_factory):
    """Një dokument dixhital i fiksuar, i vizatuar dhe i lexuar sërish."""
    import random

    from data_generator.generate import render
    from data_generator.ground_truth import build_document
    from data_generator.ids import IdFactory

    for index in range(20):
        rng = random.Random(f"golden/{index}")
        document = build_document(rng, IdFactory(rng), scanned_share=0.0)
        if document.rows:
            break

    pdf, document = render(document, seed=99, index=index)
    directory = tmp_path_factory.mktemp("golden")
    path = directory / "golden.pdf"
    path.write_bytes(pdf)
    return document, path


def test_golden_document_routes_to_the_text_layer(golden):
    _, path = golden
    routing = route(path)
    assert routing.channel is Channel.TEXT_LAYER


def test_golden_document_extracts_every_field_exactly(golden):
    """Prova nga skaji në skaj: PDF → rreshta → gjetje, fushë për fushë."""
    document, path = golden
    result = extract(route(path).pages)

    truth = {f.analyte_code: f for f in document.context.findings}
    predicted = {f.analyte_code: f for f in result.findings}
    assert predicted.keys() == truth.keys(), result.rejection_counts()

    for code, expected in truth.items():
        got = predicted[code]
        assert got.value_canonical == expected.value_canonical, code
        assert got.unit_canonical == expected.unit_canonical, code
        assert (got.ref_low, got.ref_high) == (expected.ref_low, expected.ref_high), code
        assert got.ref_source is expected.ref_source, code
        assert got.status is expected.status, code
        assert got.severity == expected.severity, code
        assert got.page == expected.page, code


def test_golden_document_keeps_uninterpretable_values(golden):
    """Vlera pa interval nuk hidhet: pacienti e ka atë në dokument dhe ka
    të drejtë ta shohë, me shënimin se nuk interpretohet (SP5)."""
    document, path = golden
    result = extract(route(path).pages)
    expected = {
        f.analyte_code
        for f in document.context.findings
        if f.status is AnalyteStatus.UNINTERPRETABLE
    }
    got = {f.analyte_code for f in result.findings if f.status is AnalyteStatus.UNINTERPRETABLE}
    assert got == expected


def test_scanned_document_has_no_text_layer_to_route_to(tmp_path):
    """Kanali i skanuar duhet të shkojë te OCR-ja dhe jo të lexohet si
    dokument bosh: ndryshimi mes "nuk u lexua" dhe "nuk kishte asgjë" është
    gjendje e veçantë e makinës (Figura 6)."""
    import random

    from data_generator.generate import render
    from data_generator.ground_truth import build_document
    from data_generator.ids import IdFactory

    rng = random.Random("scanned-golden")
    document = build_document(rng, IdFactory(rng), scanned_share=1.0)
    pdf, _ = render(document, seed=5, index=0)
    path = tmp_path / "scanned.pdf"
    path.write_bytes(pdf)

    assert route(path).channel is Channel.OCR


def test_an_interval_misread_as_value_and_unit_is_rejected():
    """OCR-ja humbi vlerën; "40,0 | 52,0" nuk guxon të dalë si vlerë 40 me njësi 52,0."""
    from analyte.domain.models import BoundingBox
    from analyte.grounding.branch_a.extract import extract
    from analyte.ingestion.pdf_text import PageText, TextFragment, TextRow

    def row(*texts):
        fragments = tuple(
            TextFragment(t, BoundingBox(x0=100.0 * i, y0=10.0, x1=100.0 * i + 50, y1=20.0))
            for i, t in enumerate(texts)
        )
        return TextRow(page=1, fragments=fragments)

    result = extract((PageText(number=1, rows=(row("Hematokriti", "40,0 52,0"),)),))
    assert result.findings == ()
    assert ("Hematokriti", "njësi e palexueshme") in result.rejected


def test_a_symbol_unit_is_still_a_unit():
    from analyte.grounding.branch_a.extract import _unit_like

    assert _unit_like("%") and _unit_like("mg/dL") and _unit_like("10^9/L") and _unit_like("")
    assert not _unit_like("52,0") and not _unit_like("145")
