"""
Klasifikuesi mbi grupin B: lidhja, jo modeli.

"""

from __future__ import annotations

import pytest

from evaluation import kits
from ml import evaluate_on_kit

LABELS = list(kits.B_LABELS)


@pytest.fixture(scope="module")
def contexts():
    return dict(kits.kit_contexts())


def _row(row_id, sentence, label, **extra):
    return {
        "id": row_id,
        "konteksti": "A01",
        "fjalia": sentence,
        "etiketa": label,
        "shenim": "",
        "burimi": "",
        **extra,
    }


def _predictor(marker: str, label: str, strength: float):
    """Një parashikues që jep `strength` për `label` te fjalia që mban `marker`."""
    index = LABELS.index(label)

    def predict(sentences, _context):
        rows = []
        for sentence in sentences:
            row = [0.0] * len(LABELS)
            if marker in sentence:
                row[index] = strength
                row[0] = 1 - strength
            else:
                row[0] = 1.0
            rows.append(row)
        return rows

    return predict


def test_the_classifier_judges_the_same_text_as_the_rules(contexts):
    row = _row("B1", "Vlera juaj arriti në 4321", "ungrounded_number")
    _context, text = kits.row_text(row, contexts)
    assert "Vlera juaj arriti në 4321." in text

    seen = []

    def spy(sentences, ctx):
        seen.append(list(sentences))
        return [[1.0] + [0.0] * (len(LABELS) - 1)] * len(sentences)

    evaluate_on_kit.judge_rows([row], contexts, spy, LABELS, {"t": 0.5})
    assert any("Vlera juaj arriti në 4321." in s for s in seen[0])


def test_each_threshold_is_applied_unchanged_to_the_same_probabilities(contexts):
    rows = [
        _row("B1", "Vlera juaj arriti në 4321", "ungrounded_number"),
        _row("B2", "Rezultati juaj duhet parë me qetësi", "clean"),
    ]
    predict = _predictor("4321", "ungrounded_number", 0.6)
    judged, errors = evaluate_on_kit.judge_rows(
        rows, contexts, predict, LABELS, {"low": 0.5, "high": 0.9}
    )
    assert not errors
    low = {j.actual is not None: j.predicted is not None for j in judged["low"]}
    high = {j.actual is not None: j.predicted is not None for j in judged["high"]}
    assert low == {True: True, False: False}  # 0.6 kalon 0.5
    assert high == {True: False, False: False}  # 0.6 nuk kalon 0.9


def test_a_row_that_cannot_be_measured_is_reported_not_counted(contexts):
    rows = [
        _row("B1", "Çfarëdo", "nje_etikete_e_shpikur"),
        _row("B2", "Mjeku ka shënuar: Çfarëdo", "polarity_flip"),  # pa `burimi`
        {**_row("B3", "Çfarëdo", "clean"), "konteksti": "A99"},
    ]
    judged, errors = evaluate_on_kit.judge_rows(
        rows, contexts, _predictor("x", "ungrounded_number", 1.0), LABELS, {"t": 0.5}
    )
    assert judged["t"] == []
    assert {e.row_id for e in errors} == {"B1", "B2", "B3"}


def test_source_quote_rows_replace_the_quote_for_the_classifier_too(contexts):
    """Ky është i njëjti ndërtim si te rregullat: citimi burimor del nga teksti."""
    kit_id, context = next(
        (k, c)
        for k, c in contexts.items()
        if any(a.polarity.value == "negated" and a.analyte_code for a in c.assertions)
    )
    assertion = next(
        a for a in context.assertions if a.polarity.value == "negated" and a.analyte_code
    )
    flipped = f"{kits.ATTRIBUTION_PREFIX_SQ} " + assertion.text_span.replace(" nuk ", " ")
    row = {
        **_row("B1", flipped, "polarity_flip"),
        "konteksti": kit_id,
        "burimi": assertion.text_span,
    }
    _, text = kits.row_text(row, contexts)
    assert f"{kits.ATTRIBUTION_PREFIX_SQ} {assertion.text_span}." not in text
    assert flipped.rstrip(".") + "." in text
