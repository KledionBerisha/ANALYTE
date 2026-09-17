"""
Testet e gjeneruesit të korpusit sintetik.

Gjeneruesi prodhon njëkohësisht dokumentin dhe etiketat e tij. Nëse
etiketa nuk i përgjigjet asaj që shtypet, çdo metrikë e mëpasme mat
diçka tjetër nga ajo që mendon se mat — dhe kjo nuk duket në asnjë
rezultat. Prandaj testet këtu nuk kontrollojnë "a punon", por
"a është e vërteta bazë vërtet e vërtetë".
"""

import re
from decimal import Decimal

import pytest

from analyte.domain.enums import (
    AnalyteStatus,
    AssertionKind,
    CrossReferenceState,
    Direction,
    Polarity,
    ReferenceSource,
)
from analyte.grounding.branch_a.classify import classify
from data_generator.catalog import (
    Sex,
    analytes_by_code,
    load_analytes,
    load_analytes_without_reference,
    terms_by_name,
)
from data_generator.generate import build_corpus, summarize, write_corpus
from data_generator.narrative import (
    EXPLAINED_TERM_SENTENCES,
    UNEXPLAINED_TERM_SENTENCES,
)

CORPUS_SIZE = 40


@pytest.fixture(scope="module")
def corpus():
    return build_corpus(seed=42, count=CORPUS_SIZE)


# --------------------------------------------------------------------
# Përsëritshmëria — NFR3
# --------------------------------------------------------------------


def test_same_seed_gives_identical_bytes(tmp_path):
    """Definicioni i përfundimit të Fazës 2: dy ekzekutime, të njëjtët bajt."""
    first, second = tmp_path / "a", tmp_path / "b"
    write_corpus(build_corpus(7, 5), 7, first)
    write_corpus(build_corpus(7, 5), 7, second)

    files = sorted(p.relative_to(first) for p in first.rglob("*.json"))
    assert files
    for relative in files:
        assert (first / relative).read_bytes() == (second / relative).read_bytes()


def test_different_seeds_give_different_corpora():
    assert build_corpus(1, 3)[0].to_json_dict() != build_corpus(2, 3)[0].to_json_dict()


def test_document_does_not_depend_on_corpus_size():
    """Dokumenti i tretë është i njëjti pavarësisht sa u kërkuan gjithsej.

    Kjo e bën gjenerimin të ndashëm në procese dhe korpusin e vogël
    nënbashkësi të saktë të atij të madh.
    """
    short = build_corpus(42, 4)[3]
    long = build_corpus(42, 30)[3]
    assert short.to_json_dict() == long.to_json_dict()


def test_manifest_records_resource_checksums(tmp_path):
    import json

    write_corpus(build_corpus(3, 2), 3, tmp_path)
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["seed"] == 3
    assert set(manifest["resources"]) == {
        "analytes.csv",
        "analytes_extra.csv",
        "units.csv",
        "terminology.csv",
    }
    assert len(manifest["documents"]) == 2


# --------------------------------------------------------------------
# Pajtueshmëria e etiketave me atë që shtypet
# --------------------------------------------------------------------


def test_every_row_matches_its_finding(corpus):
    for document in corpus:
        by_id = {f.id: f for f in document.context.findings}
        assert len(document.rows) == len(document.context.findings)
        for row in document.rows:
            finding = by_id[row.finding_id]
            assert row.value_printed == finding.value_raw
            assert row.unit_printed == finding.unit_raw
            assert row.flag_printed == finding.flag_in_document
            assert row.page == finding.page


def test_status_follows_from_value_and_interval(corpus):
    """Statusi i etiketuar duhet të dalë nga vlera dhe intervali të cilët
    janë ruajtur bashkë me të — jo nga qëllimi i gjeneruesit."""
    catalog = analytes_by_code()
    for document in corpus:
        for finding in document.context.findings:
            analyte = catalog[finding.analyte_code]
            expected = classify(
                finding.value_canonical,
                finding.ref_low,
                finding.ref_high,
                analyte.critical_low,
                analyte.critical_high,
            )
            assert finding.status is expected.status
            assert finding.severity == expected.severity


def test_printed_interval_is_present_exactly_when_source_is_document(corpus):
    for document in corpus:
        by_id = {f.id: f for f in document.context.findings}
        for row in document.rows:
            finding = by_id[row.finding_id]
            is_from_document = finding.ref_source is ReferenceSource.DOCUMENT
            assert (row.interval_printed is not None) is is_from_document


def test_values_without_reference_stay_uninterpretable(corpus):
    """SP5 nga ana e gjeneruesit: asnjë vlerë pa interval nuk merr status."""
    for document in corpus:
        for finding in document.context.findings:
            if finding.ref_source is ReferenceSource.NONE:
                assert finding.status is AnalyteStatus.UNINTERPRETABLE
                assert finding.flag_in_document is None


def test_decimal_comma_is_applied_consistently(corpus):
    for document in corpus:
        for row in document.rows:
            if document.lab.decimal_comma:
                assert "." not in row.value_printed
            else:
                assert "," not in row.value_printed


# --------------------------------------------------------------------
# Narrativa dhe pohimet
# --------------------------------------------------------------------


def test_assertion_offsets_point_at_their_own_text(corpus):
    """Pozicionet janë e vërteta bazë e nxjerrjes së pohimeve; nëse ato
    rrëshqasin qoftë edhe me një karakter, PK4 mat zhurmë."""
    for document in corpus:
        text = document.narrative_text
        for assertion in document.context.assertions:
            assert text[assertion.char_start : assertion.char_end] == assertion.text_span


def test_narrative_contains_no_standalone_numbers(corpus):
    """Asnjë numër më vete në narrativë.

    Një vlerë e shtypur në tekstin e mjekut do të zgjeronte heshtazi
    bashkësinë e numrave të mbështetur dhe do ta zbutte rregullin R1
    pikërisht aty ku ai duhet të jetë i ashpër. Prandaj shkruhet "pas tre
    muajsh" dhe jo "pas 3 muajsh".

    Shifrat brenda emrave — B12, FT4, FT3 — mbeten dhe janë të
    pashmangshme: ato janë pjesë e emrit të analitit. Kjo është kërkesë
    për nxjerrësin e numrave të rregullit R1: ai duhet të njohë kufijtë e
    fjalës, përndryshe do të raportojë "12" si numër të papërmbajtur.
    """
    pattern = re.compile(r"(?<![^\W_])\d+(?:[.,]\d+)?(?![^\W_])")
    for document in corpus:
        assert not pattern.search(document.narrative_text), document.narrative_text


def test_each_analyte_gets_at_most_one_assertion(corpus):
    for document in corpus:
        codes = [a.analyte_code for a in document.context.assertions if a.analyte_code]
        assert len(codes) == len(set(codes))


def test_every_document_has_a_recommendation(corpus):
    """R8 mat ruajtjen e rekomandimeve; pa rekomandim në burim nuk ka çfarë
    të matet."""
    for document in corpus:
        kinds = {a.kind for a in document.context.assertions}
        assert AssertionKind.RECOMMENDATION in kinds


def test_term_sentences_are_split_by_the_terminology_table():
    """Fjalitë e shpjegueshme duhet të jenë në tabelë dhe ato të
    pashpjegueshme jashtë saj — ndryshe SP6 nuk testohet dot."""
    table = terms_by_name()
    for sentence in EXPLAINED_TERM_SENTENCES:
        assert sentence.term in table
    for sentence in UNEXPLAINED_TERM_SENTENCES:
        assert sentence.term not in table


def test_glossary_covers_only_mentioned_known_terms(corpus):
    table = terms_by_name()
    for document in corpus:
        context = document.context
        for entry in context.glossary:
            assert entry.term in table
            assert entry.explanation_sq == table[entry.term].explanation_sq
        for term in context.unexplained_terms:
            assert term not in table


# --------------------------------------------------------------------
# Krahasimi i kryqëzuar
# --------------------------------------------------------------------


def test_cross_references_cover_every_finding_and_assertion(corpus):
    for document in corpus:
        context = document.context
        states = {r.analyte_code: r.state for r in context.cross_refs}
        for finding in context.findings:
            assert finding.analyte_code in states
        for assertion in context.assertions:
            if assertion.analyte_code:
                assert assertion.analyte_code in states


def test_agreement_means_the_directions_match(corpus):
    for document in corpus:
        context = document.context
        findings = {f.id: f for f in context.findings}
        assertions = {a.id: a for a in context.assertions}
        for ref in context.cross_refs:
            if ref.state not in {
                CrossReferenceState.AGREEMENT,
                CrossReferenceState.CONTRADICTION,
            }:
                continue
            status = findings[ref.finding_id].status
            assertion = assertions[ref.assertion_id]
            if assertion.direction is Direction.UNSPECIFIED:
                continue
            matches = status.direction is assertion.direction
            if assertion.polarity is Polarity.NEGATED:
                matches = not matches
            expected = (
                CrossReferenceState.AGREEMENT if matches else CrossReferenceState.CONTRADICTION
            )
            assert ref.state is expected


# --------------------------------------------------------------------
# Mbulimi i korpusit
# --------------------------------------------------------------------


def test_corpus_covers_every_case_the_evaluation_needs(corpus):
    """Një korpus pa vlera kritike, pa mospërputhje dhe pa vlera të
    painterpretueshme do të dukej i shëndetshëm dhe do të linte pa matur
    pikërisht rastet që punimi pretendon se i trajton."""
    summary = summarize(corpus)
    assert summary["status"].keys() >= {"normal", "low", "high"}
    assert summary["status"].get("critical_high", 0) + summary["status"].get(
        "critical_low", 0
    ) > 0
    assert summary["status"].get("uninterpretable", 0) > 0
    assert set(summary["reference_source"]) == {"document", "internal_table", "none"}
    assert set(summary["cross_reference_state"]) == {
        "agreement",
        "contradiction",
        "mentioned_not_measured",
        "measured_not_mentioned",
    }
    assert summary["certainty"].get("hedged", 0) > 0
    assert summary["polarity"].get("negated", 0) > 0
    assert summary["unexplained_terms"] > 0


# --------------------------------------------------------------------
# Tabelat burimore
# --------------------------------------------------------------------


def test_analyte_table_is_well_formed():
    analytes = load_analytes()
    assert len(analytes) >= 30, "specifikimi kërkon 30-40 analite"
    codes = [a.loinc_code for a in analytes]
    assert len(codes) == len(set(codes))
    for analyte in analytes:
        low_m, high_m = analyte.reference_for(Sex.MALE)
        low_f, high_f = analyte.reference_for(Sex.FEMALE)
        assert low_m is not None and high_m is not None
        assert low_m < high_m and low_f is not None and high_f is not None and low_f < high_f
        assert analyte.variants and analyte.narrative_name
        if analyte.critical_low is not None:
            assert analyte.critical_low < low_m
        if analyte.critical_high is not None:
            assert analyte.critical_high > high_m


def test_extra_analytes_have_no_reference_but_can_be_sampled():
    for analyte in load_analytes_without_reference():
        assert not analyte.has_reference
        assert analyte.sample_low is not None and analyte.sample_high is not None
        assert analyte.sample_low < analyte.sample_high


def test_sex_specific_ranges_exist():
    """Pa analite të varura nga gjinia, zgjidhja e intervalit do të ishte
    e parëndësishme dhe Dega A do të dukej më e saktë se ç'është."""
    assert any(a.is_sex_specific for a in load_analytes())


def test_quantization_matches_printed_decimals():
    glucose = analytes_by_code()["2345-7"]
    assert glucose.quantize(Decimal("128.4")) == Decimal("128")
    potassium = analytes_by_code()["2823-3"]
    assert potassium.quantize(Decimal("6.94")) == Decimal("6.9")
