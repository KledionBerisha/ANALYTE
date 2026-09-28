"""
Testet e grupeve të shkruara me dorë.

Këtu nuk testohet cilësia e rregullave — atë e mat autori me fjalitë e
veta. Testohet që matja të jetë e besueshme para se të ketë çfarë të
masë: kontekstet janë të qëndrueshme, shablloni i tyre kalon çdo rregull
(përndryshe çdo fjali e B-së do të merrte shkelje që nuk janë të saj), dhe
një `build` i dytë nuk fshin punën e autorit.
"""

from __future__ import annotations

import pytest

from analyte.generation.templates import build as build_template
from analyte.grounding.branch_b.assertions import extract_assertions
from analyte.verification.pipeline import verify
from evaluation import kits


@pytest.fixture(scope="module")
def contexts():
    return kits.kit_contexts()


def test_there_are_twenty_five_fixed_contexts(contexts):
    again = kits.kit_contexts.__wrapped__()
    assert [kit_id for kit_id, _ in contexts] == [f"A{n:02d}" for n in range(1, 26)]
    for (_, first), (_, second) in zip(contexts, again):
        assert [f.value_canonical for f in first.findings] == [
            f.value_canonical for f in second.findings
        ]
        assert [a.text_span for a in first.assertions] == [a.text_span for a in second.assertions]


def test_contexts_cover_every_case_the_policy_names(contexts):
    covered = {key for _, context in contexts for key, on in kits._features(context).items() if on}
    assert covered == {
        "critical",
        "uninterpretable",
        "negated",
        "hedged",
        "recommendation",
        "unexplained",
        "pattern",
    }


def test_contexts_are_short_enough_to_write_by_hand(contexts):
    for kit_id, context in contexts:
        assert len(context.findings) <= kits.MAX_FINDINGS, kit_id


def test_template_passes_every_rule_on_every_kit_context(contexts):
    """Kushti i B-së: çdo shkelje e gjetur vjen nga fjalia e autorit."""
    for kit_id, context in contexts:
        result = verify(context, build_template(context))
        assert result.passed, (kit_id, [(v.type.value, v.evidence) for v in result.violations])


# --------------------------------------------------------------------
# Skedarët e autorit
# --------------------------------------------------------------------


def test_build_never_overwrites_the_authors_files(tmp_path):
    kits.build(tmp_path)
    written = tmp_path / "A_shpjegimet.md"
    written.write_text("## A01\n\nTeksti i autorit.\n", encoding="utf-8")

    kits.build(tmp_path)
    assert "Teksti i autorit." in written.read_text(encoding="utf-8")


def test_explanations_are_read_by_heading_and_empty_ones_skipped(tmp_path):
    path = tmp_path / "A.md"
    path.write_text(
        "# Titull\n\n## A01\n\nRreshti i parë.\nRreshti i dytë.\n\n## A02\n\n\n## A03\nTre.\n",
        encoding="utf-8",
    )
    assert kits.read_explanations(path) == {"A01": "Rreshti i parë. Rreshti i dytë.", "A03": "Tre."}


def test_a_csv_without_the_expected_columns_is_refused(tmp_path):
    path = tmp_path / "B.csv"
    path.write_text("id,fjalia\nB001,Diçka.\n", encoding="utf-8")
    with pytest.raises(ValueError, match="etiketa"):
        kits.read_rows(path, kits.B_COLUMNS)


# --------------------------------------------------------------------
# Matja
# --------------------------------------------------------------------


def test_template_explanations_raise_no_alarm(contexts):
    lookup = dict(contexts)
    report = kits.check_explanations({"A01": build_template(lookup["A01"])}, lookup)
    assert report["flagged"] == 0


def _row(row_id, context, sentence, label):
    return {"id": row_id, "konteksti": context, "fjalia": sentence, "etiketa": label, "shenim": ""}


def test_sentences_are_judged_inside_their_own_context(contexts):
    lookup = dict(contexts)
    rows = [
        _row("B1", "A01", "Rezultati juaj duhet parë me qetësi nga mjeku juaj", "clean"),
        _row("B2", "A01", "Vlera juaj arriti në 4321", "ungrounded_number"),
        _row("B3", "A99", "Çfarëdo", "clean"),
        _row("B4", "A01", "Çfarëdo", "nje_etikete_e_shpikur"),
    ]
    metrics, errors = kits.check_sentences(rows, lookup)

    assert metrics["samples"] == 2
    assert metrics["per_defect_type"]["ungrounded_number"]["recall"] == 1.0
    assert metrics["false_alarms_on_clean"] == 0
    assert {e.row_id for e in errors} == {"B3", "B4"}


def _narrative_row(sentence, **overrides):
    found = extract_assertions(sentence)[0]
    row = {
        "id": "C1",
        "fjalia": sentence,
        "lloji": found.kind.value,
        "polariteti": found.polarity.value,
        "siguria": found.certainty.value,
        "analiti": "",
        "drejtimi": found.direction.value,
        "shenim": "",
    }
    row.update(overrides)
    return row


def test_narrative_labels_that_agree_score_one():
    metrics, errors = kits.check_narrative([_narrative_row("Nuk ka shenja anemie.")])
    assert errors == []
    assert metrics["accuracy"]["polariteti"] == 1.0


def test_narrative_label_that_disagrees_scores_zero():
    sentence = "Nuk ka shenja anemie."
    found = extract_assertions(sentence)[0]
    flipped = "affirmed" if found.polarity.value == "negated" else "negated"
    metrics, _ = kits.check_narrative([_narrative_row(sentence, polariteti=flipped)])
    assert metrics["accuracy"]["polariteti"] == 0.0


def test_narrative_rows_with_unknown_values_are_reported_not_scored():
    rows = [
        _narrative_row("Nuk ka shenja anemie.", polariteti="ndoshta"),
        _narrative_row("Nuk ka shenja anemie.", analiti="Analiti i shpikur"),
    ]
    metrics, errors = kits.check_narrative(rows)
    assert metrics["sentences"] == 0
    assert len(errors) == 2
