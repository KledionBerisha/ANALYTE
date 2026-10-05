"""
Katalogu `r1.4` kundrejt `r1.3` (ADR 0021).

Çdo test tregon një rast ku dy versionet ndryshojnë, me fjali të shkruara me dorë që nuk janë të shabllonit. Dy gjëra
mbahen njëkohësisht: `r1.3` mbetet i ngrirë (rezultatet e matura me të duhet të riprodhohen), dhe `r1.4` kap atë që auditi i
E8 dhe grupet A, B treguan se r1.3 e humbte, pa dhënë alarm te teksti i saktë.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

import pytest

from analyte.domain.enums import AnalyteStatus, ReferenceSource, ViolationType
from analyte.domain.models import AnalyteFinding, GlossaryEntry, GroundingContext
from analyte.grounding.branch_b import assertions, negation
from analyte.domain.enums import AssertionKind, Polarity
from analyte.verification.pipeline import verify
from analyte.verification import ruleset

D = Decimal
DOC = UUID("22222222-2222-2222-2222-222222222222")


def finding(code, canonical, raw, value, low, high, status, unit="mg/dL"):
    outside = status is not AnalyteStatus.NORMAL
    return AnalyteFinding(
        analyte_code=code,
        analyte_name_raw=raw,
        analyte_name_canonical=canonical,
        value_raw=str(value),
        value=D(str(value)),
        unit_raw=unit,
        unit_canonical=unit,
        value_canonical=D(str(value)),
        ref_low=D(str(low)),
        ref_high=D(str(high)),
        ref_source=ReferenceSource.DOCUMENT,
        status=status,
        severity=D("0.5") if outside else None,
        page=1,
    )


HDL = finding("2085-9", "Kolesterol HDL", "HDL", 72, 40, 69, AnalyteStatus.HIGH)
VITD = finding("1989-3", "Vitaminë D 25-OH", "Vitamina D", 17.8, 30.0, 100.0, AnalyteStatus.LOW, "ng/mL")
CALCIUM = finding("17861-6", "Kalcium në serum", "Kalciumi", 7.5, 8.6, 10.2, AnalyteStatus.LOW)
CREATININE = finding("2160-0", "Kreatininë në serum", "Kreatinina", 1.6, 0.6, 1.1, AnalyteStatus.HIGH)
SODIUM = finding("2951-2", "Natrium në serum", "Natriumi", 142, 135, 145, AnalyteStatus.NORMAL, "mmol/L")
HEMOGLOBIN = finding("718-7", "Hemoglobinë në gjak", "Hemoglobina", 13.4, 12.0, 16.0, AnalyteStatus.NORMAL, "g/dL")


def ctx(*findings, glossary=()):
    return GroundingContext(document_id=DOC, findings=tuple(findings), glossary=tuple(glossary))


def kinds(context, text, rules):
    return {v.type for v in verify(context, text, rules=rules).violations}


# --- versionimi ----------------------------------------------------------------------------------


def test_the_verifier_stamps_the_version_it_ran_and_rejects_an_unknown_one():
    context = ctx(HDL)
    assert verify(context, "Kolesteroli HDL është 72 mg/dL.", rules="r1.3").rules_version == "r1.3"
    assert verify(context, "Kolesteroli HDL është 72 mg/dL.").rules_version == "r1.4"
    with pytest.raises(ValueError):
        verify(context, "x", rules="r9.9")


def test_the_active_version_is_restored_after_a_verification():
    before = ruleset.active()
    verify(ctx(HDL), "Kolesteroli HDL është 72 mg/dL.", rules="r1.3")
    assert ruleset.active() == before


# --- trajtat e shquara ---------------------------------------------------------------------------


def test_a_definite_analyte_name_is_not_read_as_another_analyte():
    # r1.3 e lexonte "Kolesteroli HDL" si kolesterol total (analit që dokumenti nuk e ka matur).
    text = "Kolesteroli HDL është 72 mg/dL, mbi 40 – 69."
    assert ViolationType.UNGROUNDED_ANALYTE in kinds(ctx(HDL), text, "r1.3")
    assert kinds(ctx(HDL), text, "r1.4") == set()


def test_digits_inside_a_definite_analyte_name_are_not_numbers():
    # r1.3 lexonte "25" te "Vitamina D 25-OH" si numër i pabazuar.
    text = "Vitamina D 25-OH është 17.8 ng/mL, nën 30.0 – 100.0."
    assert ViolationType.UNGROUNDED_NUMBER in kinds(ctx(VITD), text, "r1.3")
    assert kinds(ctx(VITD), text, "r1.4") == set()


def test_genitive_forms_of_an_analyte_name_are_recognised_as_mentions():
    # "alanin aminotransferazës", "leukociteve", "klorit": nuk duhet të numërohen si analite të papërmendura.
    context = ctx(CALCIUM)
    text = "Vlera e kalciumit është 7.5 mg/dL, nën 8.6 – 10.2."
    assert kinds(context, text, "r1.4") == set()


def test_a_wrongly_inflected_neighbour_is_still_not_confused():
    # "Kaliumi" dhe "Kalciumi" mbeten dy analite; lakimi nuk i bashkon.
    context = ctx(CALCIUM)
    assert ViolationType.UNGROUNDED_ANALYTE in kinds(context, "Kaliumi është 7.5 mg/dL.", "r1.4")


# --- R1: numri i përket analitit tjetër ----------------------------------------------------------


def test_a_value_placed_on_the_wrong_analyte_is_flagged_only_by_r14():
    context = ctx(CALCIUM, CREATININE)
    text = "Kalciumi është 1.6 mg/dL, nën 8.6 – 10.2."  # 1.6 është vlera e kreatininës
    assert kinds(context, text, "r1.3") == set()  # numri ekziston diku te konteksti
    assert ViolationType.UNGROUNDED_NUMBER in kinds(context, text, "r1.4")


def test_a_sentence_with_two_analytes_is_not_judged_for_number_ownership():
    context = ctx(CALCIUM, CREATININE)
    text = "Kalciumi është 7.5 mg/dL, ndërsa kreatinina është 1.6 mg/dL."
    assert kinds(context, text, "r1.4") == set()


# --- R3: sipas klauzolës, fjalori i zgjeruar -----------------------------------------------------


def test_two_analytes_with_different_directions_in_one_sentence_are_judged_separately():
    context = ctx(CALCIUM, CREATININE)
    text = "Kalciumi është i ulët ndërsa kreatinina është e lartë."
    assert ViolationType.DIRECTION_MISMATCH in kinds(context, text, "r1.3")  # alarm i rremë
    assert kinds(context, text, "r1.4") == set()


def test_plain_adjectives_and_noun_forms_of_direction_are_understood():
    context = ctx(CALCIUM)
    assert kinds(context, "Kalciumi është i lartë.", "r1.3") == set()  # r1.3 nuk e njihte
    assert ViolationType.DIRECTION_MISMATCH in kinds(context, "Kalciumi është i lartë.", "r1.4")
    assert ViolationType.DIRECTION_MISMATCH in kinds(context, "Vërehet rritja e kalciumit.", "r1.4")
    assert kinds(context, "Vërehet ulja e kalciumit.", "r1.4") == set()


def test_a_predicate_clause_without_its_own_analyte_belongs_to_the_previous_clause():
    context = ctx(HEMOGLOBIN)
    assert kinds(context, "Hemoglobina është 13.4 g/dL dhe bie brenda 12.0 – 16.0.", "r1.4") == set()
    assert ViolationType.DIRECTION_MISMATCH in kinds(
        context, "Hemoglobina është 13.4 g/dL dhe është nën intervalin 12.0 – 16.0.", "r1.4"
    )


def test_a_negated_direction_is_judged_per_clause():
    context = ctx(CALCIUM)
    assert kinds(context, "Kalciumi nuk është i lartë.", "r1.4") == set()
    assert ViolationType.DIRECTION_MISMATCH in kinds(context, "Kalciumi nuk është i ulët.", "r1.4")


def test_a_glossary_definition_is_not_a_mention_of_the_analyte_it_contains():
    # "qelizat e kuqe" brenda shpjegimit të hemoglobinës është emër i eritrociteve, por këtu është pjesë e përkufizimit.
    erythrocytes = finding("789-8", "Eritrocite", "Eritrocitet", 4.6, 4.5, 5.9, AnalyteStatus.NORMAL, "10^12/L")
    glossary = [GlossaryEntry(term="hemoglobinë", explanation_sq="proteina që bart oksigjenin në qelizat e kuqe", source_ref="x")]
    context = ctx(erythrocytes, glossary=glossary)
    text = "Kjo do të thotë se proteina që bart oksigjenin në qelizat e kuqe është më e lartë se sa duhet."
    assert ViolationType.DIRECTION_MISMATCH not in kinds(context, text, "r1.4")  # eritrocitet nuk u përmendën


# --- R3: pohimi i përgjithshëm -------------------------------------------------------------------


def test_a_blanket_claim_that_hides_an_abnormal_finding_is_flagged():
    context = ctx(CALCIUM, SODIUM)
    text = "Natriumi është normal. Të gjitha vlerat e tjera janë brenda intervalit referent."
    assert kinds(context, text, "r1.3") == set()
    assert ViolationType.DIRECTION_MISMATCH in kinds(context, text, "r1.4")


def test_a_blanket_claim_is_fine_when_the_abnormal_finding_was_named_first():
    context = ctx(CALCIUM, SODIUM)
    text = "Kalciumi është nën intervalin referent. Të gjitha vlerat e tjera janë brenda intervalit referent."
    assert ViolationType.DIRECTION_MISMATCH not in kinds(context, text, "r1.4")


def test_a_specific_claim_about_other_analyses_is_not_a_blanket_claim():
    context = ctx(CALCIUM, SODIUM)
    text = "Në analizat e tjera, natriumi është 142 dhe është brenda intervalit referent (135 – 145)."
    assert ViolationType.DIRECTION_MISMATCH not in kinds(context, text, "r1.4")


# --- R9: shpjegim i shpikur në kllapa ------------------------------------------------------------


def test_an_invented_gloss_after_an_abbreviation_is_flagged_only_by_r14():
    tsh = finding("3016-3", "Hormoni stimulues i tiroides", "TSH", 6.5, 0.4, 4.0, AnalyteStatus.HIGH, "mIU/L")
    text = "TSH (hormoni i stimulimit të mëlçisë) është 6.5 mIU/L, mbi 0.4 – 4.0."
    assert kinds(ctx(tsh), text, "r1.3") == set()
    assert ViolationType.UNGROUNDED_TERM_EXPLANATION in kinds(ctx(tsh), text, "r1.4")


def test_units_intervals_and_glossary_text_in_parentheses_are_accepted():
    glossary = [GlossaryEntry(term="hemolizë", explanation_sq="shkatërrim i parakohshëm i qelizave të kuqe", source_ref="x")]
    context = ctx(HEMOGLOBIN, glossary=glossary)
    ok = (
        "Hemoglobina (mg/dL) është 13.4. "
        "Hemoglobina (intervali referent: 12.0 – 16.0) është normale. "
        "Hemoliza (shkatërrimi i parakohshëm i qelizave të kuqe të gjakut) nuk u pa."
    )
    assert ViolationType.UNGROUNDED_TERM_EXPLANATION not in kinds(context, ok, "r1.4")


# --- Dega B: fjalori i rekomandimit dhe i pseudo-mohimit -----------------------------------------


def test_a_negated_recommendation_is_still_a_recommendation_with_negated_polarity():
    (found,) = assertions.extract_assertions("Nuk nevojitet kontroll i mëtejshëm.")
    assert found.kind is AssertionKind.RECOMMENDATION and found.polarity is Polarity.NEGATED


def test_cannot_be_denied_is_a_pseudo_negation_not_a_negation():
    assert negation.polarity_of("Hipotiroidizmi nuk mund të mohohet.") is Polarity.AFFIRMED
    assert negation.polarity_of("Nuk ka shenja të anemisë.") is Polarity.NEGATED
