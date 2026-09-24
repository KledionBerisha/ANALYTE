"""
Testet e Degës B: terma, mohim, pasiguri, pohime, krahasim i kryqëzuar.

Fjalitë e provës janë shkruar me dorë dhe NUK janë ato të gjeneruesit.
Kjo është e qëllimshme: detektorët u shkruan duke pasur parasysh
shabllonet e korpusit, prandaj një provë mbi ato shabllone do të tregonte
vetëm se kodi kujton veten. Fjalitë këtu përdorin ndërtime të tjera — për
aq sa mund të shkruhen pa dokumente reale, të cilat mbeten prova e vetme
e vërtetë (E13).
"""

from uuid import uuid4

import pytest

from analyte.domain.enums import (
    AnalyteStatus,
    AssertionKind,
    Certainty,
    CrossReferenceState,
    Direction,
    Polarity,
    ReferenceSource,
)
from analyte.domain.models import AnalyteFinding, ReportAssertion
from analyte.grounding.branch_b import hedging, negation, terminology
from analyte.grounding.branch_b.assertions import (
    extract_assertions,
    find_analyte,
    find_direction,
    find_report_text,
    split_sentences,
    unexplained_terms,
)
from analyte.grounding.branch_b.crossref import build_cross_references
from decimal import Decimal


# --------------------------------------------------------------------
# Mohimi
# --------------------------------------------------------------------


@pytest.mark.parametrize(
    "sentence",
    [
        "Nuk vërehen shenja të infeksionit.",
        "Pacienti nuk ka ankesa të tjera.",
        "Mungojnë shenjat e dëmtimit hepatik.",
        "Asnjë vlerë nuk del jashtë kufijve.",
        "Gjatë kontrollit nuk u gjet ndonjë ndryshim.",
    ],
)
def test_negated_sentences_are_recognised(sentence):
    assert negation.polarity_of(sentence) is Polarity.NEGATED


@pytest.mark.parametrize(
    "sentence",
    [
        "Vërehet rritje e lehtë e enzimave hepatike.",
        "Vlerat janë të qëndrueshme krahasuar me kontrollin e kaluar.",
        "Gjendja e përgjithshme mbetet e mirë.",
    ],
)
def test_affirmed_sentences_stay_affirmed(sentence):
    assert negation.polarity_of(sentence) is Polarity.AFFIRMED


@pytest.mark.parametrize(
    "sentence",
    [
        "Nuk përjashtohet anemia.",
        "Nuk mund të përjashtohet një proces inflamator.",
    ],
)
def test_pseudo_negation_does_not_negate(sentence):
    """"Nuk përjashtohet X" pohon me rezervë.

    Po ta lexonim si mohim, do të përmbysnim kuptimin e mjekut pikërisht
    ashtu si rregulli R5 druhet se do ta bëjë modeli gjuhësor.
    """
    result = negation.detect(sentence)
    assert result.polarity is Polarity.AFFIRMED
    assert result.pseudo
    assert hedging.certainty_of(sentence) is Certainty.HEDGED


def test_negation_scope_stops_at_the_contrast():
    """Mohimi i një gjymtyre nuk shtrihet te tjetra."""
    assert negation.polarity_of("Kaliumi nuk është i rritur, por natriumi është i lartë.") is (
        Polarity.NEGATED
    )


def test_negation_in_the_second_clause_is_a_known_limitation():
    """Kufizim i dokumentuar: fusha e veprimit lexohet nga fillimi i fjalisë.

    "Natriumi është i lartë, por kaliumi nuk është i rritur" ka dy pohime
    me polaritete të ndryshme, ndërsa modeli i të dhënave mban një
    polaritet për pohim. Zgjidhja e vërtetë është ndarja e fjalisë në dy
    pohime, jo zbutja e fushës së veprimit — prandaj sjellja e sotme
    fiksohet këtu që ndryshimi i saj të jetë i vetëdijshëm.
    """
    sentence = "Natriumi është i lartë, por kaliumi nuk është i rritur."
    assert negation.polarity_of(sentence) is Polarity.AFFIRMED


def test_cues_are_matched_as_whole_words():
    """Pa kufij fjale, "pa" dhe "nuk" do të gjendeshin brenda fjalëve."""
    assert negation.polarity_of("Vlera e pastër u konfirmua.") is Polarity.AFFIRMED


# --------------------------------------------------------------------
# Pasiguria
# --------------------------------------------------------------------


@pytest.mark.parametrize(
    "sentence",
    [
        "Ndryshimi mund të jetë kalimtar.",
        "Ndoshta bëhet fjalë për një gjetje të rastësishme.",
        "Vlerat sugjerojnë një proces kronik.",
        "Duket se gjendja është përmirësuar.",
        "Ka gjasa të jetë pasojë e mjekimit.",
        "Dyshohet për mungesë hekuri.",
    ],
)
def test_hedged_sentences_are_recognised(sentence):
    assert hedging.certainty_of(sentence) is Certainty.HEDGED


@pytest.mark.parametrize(
    "sentence",
    [
        "Vlera është konfirmuar në dy matje.",
        "Gjetja përputhet me kontrollin e mëparshëm.",
    ],
)
def test_confirmed_sentences_stay_confirmed(sentence):
    assert hedging.certainty_of(sentence) is Certainty.CONFIRMED


def test_reported_cue_is_the_one_that_decided():
    """Dëshmia e shkeljes përmban shenjën; ajo duhet të jetë e vërteta."""
    assert hedging.detect("Nuk përjashtohet se mund të jetë kalimtare.").cue == (
        "nuk perjashtohet"
    )


# --------------------------------------------------------------------
# Termat
# --------------------------------------------------------------------


@pytest.mark.parametrize(
    "sentence,term",
    [
        ("Shenjat e anemisë janë të pranishme.", "anemi"),
        ("Trajtimi i hipotiroidizmit vazhdon.", "hipotiroidizëm"),
        ("Vlerat tregojnë hemolizë të lehtë.", "hemolizë"),
        ("U vlerësua funksioni renal.", "funksioni renal"),
        ("Rezultati del jashtë intervalit referent.", "interval referent"),
    ],
)
def test_terms_are_found_through_albanian_inflection(sentence, term):
    assert term in {match.term.term for match in terminology.detect_terms(sentence)}


def test_longer_term_wins_over_the_shorter_one_it_contains():
    matches = terminology.detect_terms("U mat filtrimi glomerular.")
    assert [match.term.term for match in matches] == ["filtrim glomerular"]


def test_glossary_carries_a_source_for_every_entry():
    """SP6 nga ana e dukshme: çdo shpjegim ka burim të regjistruar."""
    entries = terminology.glossary_for("Vërehet anemi dhe inflamacion.")
    assert entries
    assert all(entry.source_ref.strip() for entry in entries)


def test_unknown_medical_words_are_reported_not_explained():
    """SP6: termi jashtë tabelës shënohet i pashpjeguar."""
    found = unexplained_terms("Vërehet anizocitozë dhe poikilocitozë e lehtë.")
    assert set(found) == {"anizocitozë", "poikilocitozë"}


def test_analyte_names_are_not_reported_as_unknown_terms():
    """"Glukoza" mbaron me -oza por trajtohet nga Dega A."""
    assert unexplained_terms("Glukoza është matur esëll.") == ()


def test_common_words_with_medical_endings_are_not_terms():
    """"Paraqitet" është folje; pa kjo mbrojtje ajo dilte term i
    pashpjeguar në pothuajse çdo dokument."""
    assert unexplained_terms("Pacienti paraqitet për kontroll.") == ()
    assert unexplained_terms("Profili lipidik është brenda kufijve.") == ()


# --------------------------------------------------------------------
# Pohimet
# --------------------------------------------------------------------


def test_sentence_offsets_point_back_at_the_text():
    text = "Fjalia e parë. Fjalia e dytë."
    sentences = split_sentences(text)
    assert [text[s.start : s.end] for s in sentences] == ["Fjalia e parë.", "Fjalia e dytë."]


def test_assertion_offsets_point_back_at_the_text():
    text = "Kaliumi rezulton mbi intervalin referent. Rekomandohet kontroll."
    for assertion in extract_assertions(text, new_id=uuid4):
        assert text[assertion.char_start : assertion.char_end] == assertion.text_span


def test_neutral_sentences_produce_no_assertion():
    """Një pohim i shpikur do të kërkonte më vonë mbështetje që nuk ekziston."""
    assert extract_assertions("Pacienti paraqitet për kontroll rutinë.") == ()


def test_recommendation_is_recognised_without_an_analyte():
    assertions = extract_assertions("Rekomandohet përsëritja e analizave.")
    assert len(assertions) == 1
    assert assertions[0].kind is AssertionKind.RECOMMENDATION
    assert assertions[0].analyte_code is None


def test_finding_is_linked_to_its_analyte():
    assertions = extract_assertions("Kreatinina rezulton mbi intervalin referent.")
    assert assertions[0].kind is AssertionKind.FINDING
    assert assertions[0].analyte_code == "2160-0"


def test_longer_analyte_name_wins():
    """"HDL-kolesteroli" dhe "Kolesteroli" janë dy analite me dy intervale."""
    assert find_analyte("HDL-kolesteroli është i ulët.") == "2085-9"
    assert find_analyte("Kolesteroli total është i lartë.") == "2093-3"


def test_direction_is_kept_apart_from_polarity():
    """"Nuk rezulton mbi intervalin" ka drejtim INCREASED dhe polaritet
    NEGATED. Bashkimi i tyre do ta bënte të pamundur dallimin mes "është i
    ulët" dhe "nuk është i lartë"."""
    sentence = "Glukoza nuk rezulton mbi intervalin referent."
    assertion = extract_assertions(sentence)[0]
    assert assertion.direction is Direction.INCREASED
    assert assertion.polarity is Polarity.NEGATED


def test_report_text_is_located_and_unwrapped():
    from analyte.domain.models import BoundingBox
    from analyte.ingestion.pdf_text import PageText, TextFragment, TextRow

    def row(text: str, y: float) -> TextRow:
        return TextRow(
            page=1,
            fragments=(
                TextFragment(text=text, bbox=BoundingBox(x0=56, y0=y - 10, x1=400, y1=y)),
            ),
        )

    page = PageText(
        number=1,
        rows=(
            row("Glukoza", 100),
            row("VLERËSIMI I MJEKUT", 200),
            row("Kaliumi rezulton mbi intervalin", 214),
            row("referent. Rekomandohet kontroll.", 228),
            row("Mjeku përgjegjës: Dr. A. Krasniqi", 260),
        ),
    )
    assert find_report_text((page,)) == (
        "Kaliumi rezulton mbi intervalin referent. Rekomandohet kontroll."
    )


# --------------------------------------------------------------------
# Krahasimi i kryqëzuar
# --------------------------------------------------------------------


def _finding(code: str, status: AnalyteStatus) -> AnalyteFinding:
    return AnalyteFinding(
        analyte_code=code,
        analyte_name_raw="X",
        analyte_name_canonical="X",
        value_raw="1",
        value=Decimal("1"),
        unit_canonical="u",
        value_canonical=Decimal("1"),
        ref_low=Decimal("0"),
        ref_high=Decimal("10"),
        ref_source=ReferenceSource.INTERNAL_TABLE,
        status=status,
        severity=None if status is AnalyteStatus.NORMAL else Decimal("1"),
        page=1,
    )


def _assertion(code: str | None, direction: Direction, polarity=Polarity.AFFIRMED):
    return ReportAssertion(
        text_span="x",
        analyte_code=code,
        direction=direction,
        polarity=polarity,
        certainty=Certainty.CONFIRMED,
        kind=AssertionKind.FINDING,
        char_start=0,
        char_end=1,
    )


def test_agreement_and_contradiction():
    high = _finding("2345-7", AnalyteStatus.HIGH)
    agree = _assertion("2345-7", Direction.INCREASED)
    refs = build_cross_references((high,), (agree,))
    assert refs[0].state is CrossReferenceState.AGREEMENT

    disagree = _assertion("2345-7", Direction.DECREASED)
    refs = build_cross_references((high,), (disagree,))
    assert refs[0].state is CrossReferenceState.CONTRADICTION


def test_negation_is_not_the_opposite_of_affirmation():
    """"Nuk rezulton mbi intervalin" përputhet me çdo status që nuk është i
    rritur, jo vetëm me atë të ulët."""
    normal = _finding("2345-7", AnalyteStatus.NORMAL)
    denial = _assertion("2345-7", Direction.INCREASED, Polarity.NEGATED)
    assert build_cross_references((normal,), (denial,))[0].state is (
        CrossReferenceState.AGREEMENT
    )


def test_mentioned_but_not_measured():
    refs = build_cross_references((), (_assertion("2345-7", Direction.INCREASED),))
    assert refs[0].state is CrossReferenceState.MENTIONED_NOT_MEASURED
    assert refs[0].finding_id is None


def test_measured_but_not_mentioned():
    """Kategoria që lexuesi njerëzor nuk e vëren: mungesa e një komenti."""
    refs = build_cross_references((_finding("2345-7", AnalyteStatus.HIGH),), ())
    assert refs[0].state is CrossReferenceState.MEASURED_NOT_MENTIONED
    assert refs[0].assertion_id is None


def test_recommendations_do_not_produce_cross_references():
    recommendation = _assertion(None, Direction.UNSPECIFIED)
    assert build_cross_references((), (recommendation,)) == ()


# --------------------------------------------------------------------
# Nga skaji në skaj
# --------------------------------------------------------------------


@pytest.fixture(scope="module")
def grounded(tmp_path_factory):
    """Një dokument dixhital i fiksuar, i vizatuar dhe i bazuar sërish."""
    import random

    from analyte.grounding.context import build
    from analyte.ingestion.router import route
    from data_generator.generate import render
    from data_generator.ground_truth import build_document
    from data_generator.ids import IdFactory

    rng = random.Random("branch-b-golden")
    document = build_document(rng, IdFactory(rng), scanned_share=0.0)
    pdf, document = render(document, seed=3, index=0)
    path = tmp_path_factory.mktemp("golden") / "doc.pdf"
    path.write_bytes(pdf)
    return document, build(document.document_id, route(path).pages)


def test_narrative_is_recovered_exactly(grounded):
    """Rreshtat e mbështjellë bashkohen sërish në tekstin origjinal; pa këtë
    pozicionet e pohimeve nuk krahasohen dot me anotimin."""
    document, grounding = grounded
    assert grounding.narrative_text == document.narrative_text


def test_every_assertion_of_the_source_is_recovered(grounded):
    document, grounding = grounded
    expected = {a.text_span for a in document.context.assertions}
    got = {a.text_span for a in grounding.context.assertions}
    assert got == expected


def test_polarity_and_certainty_survive(grounded):
    document, grounding = grounded
    predicted = {a.text_span: a for a in grounding.context.assertions}
    for assertion in document.context.assertions:
        got = predicted[assertion.text_span]
        assert got.polarity is assertion.polarity, assertion.text_span
        assert got.certainty is assertion.certainty, assertion.text_span
        assert got.kind is assertion.kind, assertion.text_span


def test_cross_reference_states_match_the_truth(grounded):
    document, grounding = grounded
    expected = {r.analyte_code: r.state for r in document.context.cross_refs}
    got = {r.analyte_code: r.state for r in grounding.context.cross_refs}
    assert got == expected
