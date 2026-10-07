"""
Këshillat me burim (ADR 0023): tabela, lidhja me gjetjet, shablloni, kërkesa dhe verifikimi.

Tabela e vërtetë dërgohet me rreshta bosh; testet që kanë nevojë për një këshillë të plotësuar e ndërtojnë
vetë dhe ia japin `attach` si tabelë. Asnjë fjali këtu nuk është këshillë e vërtetë mjekësore.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from analyte import catalog
from analyte.catalog import Advice, analytes_by_code, load_advice, load_analytes
from analyte.domain.enums import AnalyteStatus, Direction, ReferenceSource, ViolationType
from analyte.domain.models import AdviceEntry, AnalyteFinding, GroundingContext
from analyte.generation.prompt import build_prompt
from analyte.generation.templates import build
from analyte.grounding.branch_a.advice import attach
from analyte.verification.pipeline import verify
from tests.fixtures.grounding_context import DOCUMENT_ID

S = AnalyteStatus
HB, FERRITIN, GLUCOSE, TSH = "718-7", "2276-4", "2345-7", "3016-3"

HB_LOW = "Flisni me mjekun tuaj për këtë vlerë dhe për ushqimin tuaj."
GLUCOSE_HIGH = "Pyesni mjekun tuaj nëse kjo vlerë duhet përsëritur esëll."
TABLE = (
    Advice(HB, "decreased", HB_LOW, "Burim i lexuar nga autori (provë)"),
    Advice(GLUCOSE, "increased", GLUCOSE_HIGH, "Burim i lexuar nga autori (provë)"),
    Advice(FERRITIN, "decreased", "Fjali pa burim.", "[BURIMI — plotësohet]"),
    Advice(TSH, "increased", "", "Burim pa fjali"),
)


def finding(code: str, status: AnalyteStatus) -> AnalyteFinding:
    analyte = analytes_by_code()[code]
    if status is S.UNINTERPRETABLE:
        return AnalyteFinding(
            analyte_code=code,
            analyte_name_raw=analyte.name_canonical_sq,
            analyte_name_canonical=analyte.name_canonical_sq,
            value_raw="5",
            value=Decimal("5"),
            unit_canonical=analyte.unit,
            value_canonical=Decimal("5"),
            ref_source=ReferenceSource.NONE,
            status=status,
            page=1,
        )
    low, high = analyte.ref_low_f, analyte.ref_high_f
    width = high - low
    value = {
        S.CRITICAL_LOW: low - width,
        S.LOW: low - width / 10,
        S.NORMAL: (low + high) / 2,
        S.HIGH: high + width / 10,
        S.CRITICAL_HIGH: high + width,
    }[status].quantize(Decimal("0.01"))
    severity = None
    if status.is_abnormal:
        severity = (abs(value - (low if value < low else high)) / width).quantize(Decimal("0.001"))
    return AnalyteFinding(
        analyte_code=code,
        analyte_name_raw=analyte.name_canonical_sq,
        analyte_name_canonical=analyte.name_canonical_sq,
        value_raw=str(value),
        value=value,
        unit_canonical=analyte.unit,
        value_canonical=value,
        ref_low=low,
        ref_high=high,
        ref_source=ReferenceSource.INTERNAL_TABLE,
        status=status,
        severity=severity,
        page=1,
    )


def context(*findings: AnalyteFinding, advice: tuple[Advice, ...] = TABLE) -> GroundingContext:
    return GroundingContext(document_id=DOCUMENT_ID, findings=findings, advice=attach(findings, advice))


# --------------------------------------------------------------------
# Tabela
# --------------------------------------------------------------------


def test_the_table_has_one_row_per_analyte_and_direction():
    rows = load_advice()
    keys = {(a.loinc_code, a.direction) for a in rows}
    expected = {(a.loinc_code, d) for a in load_analytes() for d in ("increased", "decreased")}
    assert keys == expected and len(rows) == len(expected)


def test_a_row_is_filled_only_with_both_a_sentence_and_a_read_source():
    assert TABLE[0].is_filled and TABLE[1].is_filled
    assert not TABLE[2].is_filled, "burim vendmbajtës"
    assert not TABLE[3].is_filled, "pa fjali"


@pytest.mark.parametrize(
    "row",
    [
        {"loinc_code": "0000-0", "direction": "increased", "advice_sq": "", "source_ref": ""},
        {"loinc_code": HB, "direction": "high", "advice_sq": "", "source_ref": ""},
        {"loinc_code": HB, "direction": "increased", "advice_sq": "Mbani vlerën nën 12 g/dL.", "source_ref": "x"},
        {"loinc_code": HB, "direction": "increased", "advice_sq": "Pa pikë në fund", "source_ref": "x"},
        {"loinc_code": HB, "direction": "increased", "advice_sq": "Dy fjali. Jo një.", "source_ref": "x"},
    ],
    ids=["kod i panjohur", "drejtim i panjohur", "shifër", "pa pikë", "dy fjali"],
)
def test_the_loader_rejects_a_malformed_row(monkeypatch, row):
    monkeypatch.setattr(catalog, "_read", lambda name: [row])
    load_advice.cache_clear()
    try:
        with pytest.raises(ValueError):
            load_advice()
    finally:
        load_advice.cache_clear()


def test_the_loader_rejects_a_duplicate_key(monkeypatch):
    row = {"loinc_code": HB, "direction": "increased", "advice_sq": "", "source_ref": ""}
    monkeypatch.setattr(catalog, "_read", lambda name: [row, dict(row)])
    load_advice.cache_clear()
    try:
        with pytest.raises(ValueError):
            load_advice()
    finally:
        load_advice.cache_clear()


# --------------------------------------------------------------------
# Lidhja me gjetjet
# --------------------------------------------------------------------


def test_the_row_is_chosen_by_analyte_and_direction():
    hb, glucose = finding(HB, S.LOW), finding(GLUCOSE, S.CRITICAL_HIGH)
    entries = attach((hb, glucose), TABLE)
    assert [(e.finding_id, e.direction, e.advice_sq) for e in entries] == [
        (hb.id, Direction.DECREASED, HB_LOW),
        (glucose.id, Direction.INCREASED, GLUCOSE_HIGH),
    ]
    assert all(e.source_ref == "Burim i lexuar nga autori (provë)" for e in entries)


def test_normal_uninterpretable_and_opposite_directions_get_no_advice():
    findings = (finding(HB, S.NORMAL), finding(GLUCOSE, S.UNINTERPRETABLE), finding(GLUCOSE, S.LOW))
    assert attach(findings, TABLE) == ()


def test_unfilled_rows_never_reach_the_context():
    assert attach((finding(FERRITIN, S.LOW), finding(TSH, S.HIGH)), TABLE) == ()


def test_a_duplicated_analyte_gets_no_advice():
    assert attach((finding(HB, S.LOW), finding(HB, S.LOW)), TABLE) == ()


def test_the_shipped_table_attaches_nothing_until_rows_are_filled_from_read_sources():
    """Tabela e depos: çdo rresht i plotësuar duhet të ketë burim të lexuar; rreshti bosh nuk lidhet."""
    for row in load_advice():
        assert row.is_filled or not row.advice_sq or "plotësohet" in row.source_ref


def test_the_context_rejects_advice_for_an_unknown_finding():
    hb = finding(HB, S.LOW)
    entry = attach((hb,), TABLE)[0]
    with pytest.raises(ValueError):
        GroundingContext(document_id=DOCUMENT_ID, findings=(finding(GLUCOSE, S.HIGH),), advice=(entry,))


# --------------------------------------------------------------------
# Shablloni dhe kërkesa
# --------------------------------------------------------------------


def test_the_template_prints_the_advice_right_after_its_value():
    ctx = context(finding(HB, S.LOW), finding(GLUCOSE, S.HIGH))
    text = build(ctx)
    hb_sentence = text.index("Për Hemoglobinë në gjak")
    glucose_sentence = text.index("Për Glukozë në serum")
    assert hb_sentence < text.index(HB_LOW) < glucose_sentence < text.index(GLUCOSE_HIGH)
    assert verify(ctx, text).passed


def test_the_prompt_lists_the_advice_as_text_to_copy_and_forbids_more():
    ctx = context(finding(HB, S.LOW))
    user = build_prompt(ctx, ()).user
    assert "Këshilla me burim" in user and HB_LOW in user
    assert "mos shto asnjë këshillë tjetër" in user


def test_the_prompt_is_unchanged_when_there_is_no_advice():
    """Kërkesat e eksperimenteve (p1) nuk ndryshojnë: konteksti i tyre nuk ka këshilla."""
    ctx = context(finding(HB, S.LOW), advice=())
    assert "Këshilla" not in build_prompt(ctx, ()).user


# --------------------------------------------------------------------
# Verifikimi
# --------------------------------------------------------------------


def test_an_omitted_or_paraphrased_advice_is_an_omitted_recommendation():
    ctx = context(finding(HB, S.LOW))
    full = build(ctx)
    without = full.replace(HB_LOW, "").replace("  ", " ")
    paraphrased = full.replace(HB_LOW, "Bisedoni me mjekun për ushqimin.")
    assert verify(ctx, full).passed
    for text in (without, paraphrased):
        kinds = [v.type for v in verify(ctx, text).violations]
        assert kinds == [ViolationType.OMITTED_RECOMMENDATION]


def test_the_frozen_catalog_r1_3_does_not_check_advice():
    ctx = context(finding(HB, S.LOW))
    text = build(ctx).replace(HB_LOW, "").replace("  ", " ")
    assert verify(ctx, text, rules="r1.3").passed


def test_every_filled_row_of_the_shipped_table_survives_its_own_verification():
    """Një rresht i plotësuar që shkel R1, R2 ose SP1–SP3 do ta rrëzonte çdo dalje, edhe shabllonin."""
    status = {"increased": S.HIGH, "decreased": S.LOW}
    for row in load_advice():
        if not row.is_filled:
            continue
        ctx = context(finding(row.loinc_code, status[row.direction]), advice=(row,))
        assert ctx.advice, row
        result = verify(ctx, build(ctx))
        assert result.passed, (row, [v.evidence for v in result.violations])


# --------------------------------------------------------------------
# Eksperimentet e ngrira
# --------------------------------------------------------------------

CORPUS_PDF = Path(__file__).resolve().parents[2] / "data" / "v1" / "documents" / "doc_00002.pdf"


def test_every_experiment_pipeline_leaves_advice_off_by_default():
    """Si `ocr_guard` (ADR 0020): rezultatet e ngrira u matën pa këshilla dhe kërkesat e tyre nuk ndryshojnë."""
    from analyte.generation.templates import TemplateGenerator
    from evaluation.pipeline import GenerationPipeline, GroundingPipeline
    from evaluation.ungrounded import UngroundedPipeline

    assert GroundingPipeline().advice is False
    assert GenerationPipeline(TemplateGenerator(), ablation="E8").advice is False
    assert UngroundedPipeline.__dataclass_fields__["advice"].default is False
    assert "+advice" not in GenerationPipeline(TemplateGenerator(), ablation="E8").name
    assert "+advice" in GenerationPipeline(TemplateGenerator(), ablation="E8", advice=True).name


@pytest.mark.skipif(not CORPUS_PDF.exists(), reason="korpusi data/v1 mungon")
def test_the_service_attaches_advice_and_the_frozen_experiments_do_not():
    from uuid import uuid4

    from analyte.grounding.context import build
    from analyte.ingestion.pdf_text import read_pdf

    pages = read_pdf(CORPUS_PDF)
    service = build(uuid4(), pages).context
    frozen = build(uuid4(), pages, advice=False).context
    assert service.advice == attach(service.findings)
    assert frozen.advice == ()
    assert len(service.advice) == sum(1 for f in service.findings if f.status.is_abnormal and attach((f,)))


def test_advice_entries_round_trip_through_json():
    ctx = context(finding(HB, S.LOW))
    assert GroundingContext.model_validate(ctx.model_dump(mode="json")) == ctx
    assert isinstance(ctx.advice[0], AdviceEntry)
