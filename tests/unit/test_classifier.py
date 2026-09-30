"""
Testet e Fazës 7 që nuk kërkojnë torch.

Modeli trajnohet në Colab; këtu testohet gjithçka rreth tij: që të dhënat
e trajnimit etiketojnë fjalinë e duhur, që grupi testues është saktësisht
ai i E10, që pragu zgjidhet pa parë testin, dhe që klasifikuesi në
verifikim nuk gjykon fjalitë që rregullat i kanë gjykuar tashmë.
"""

from __future__ import annotations

import random
from uuid import uuid4

import pytest

from analyte.domain.enums import DetectedBy, ViolationType
from analyte.domain.models import GroundingContext
from analyte.domain.policy import sentence_local_violations
from analyte.generation.templates import build as build_template
from analyte.verification import classifier
from ml import evaluate_classifier, leakage
from ml.data import build_classifier_set as dataset
from ml.data.build_corruption_set import build_samples
from ml.evaluate_rule_detector import corpus
from tests.fixtures.grounding_context import build_reference_context


@pytest.fixture(scope="module")
def small():
    documents = corpus(40, 7)
    contexts = dict(documents)
    return documents, contexts, build_samples(documents, seed=7)


# --------------------------------------------------------------------
# Të dhënat
# --------------------------------------------------------------------


def test_labels_are_exactly_the_sentence_local_violations():
    assert dataset.LABELS[0] == "clean"
    assert set(dataset.LABELS[1:]) == {v.value for v in sentence_local_violations()}


def test_the_defect_label_goes_to_the_sentence_that_changed(small):
    _, contexts, samples = small
    rows = dataset.sentence_rows(samples, contexts, random.Random(0))
    for row in rows:
        clean = build_template(contexts[row["document_id"]])
        if row["label"] == "clean":
            assert row["sentence"] in clean
        else:
            assert row["sentence"] not in clean, row


def test_a_deleted_sentence_leaves_nothing_to_label(small):
    _, contexts, samples = small
    rows = dataset.sentence_rows(samples, contexts, random.Random(0))
    assert ViolationType.OMITTED_RECOMMENDATION.value not in {row["label"] for row in rows}


def test_clean_sentences_are_capped(small):
    _, contexts, samples = small
    rows = dataset.sentence_rows(samples, contexts, random.Random(0))
    defective = sum(1 for row in rows if row["label"] != "clean")
    clean = sum(1 for row in rows if row["label"] == "clean")
    assert clean <= dataset.CLEAN_PER_DEFECT * defective


def test_the_test_texts_are_the_e10_test_samples():
    """E11 matet mbi të njëjtat mostra si E10, jo mbi mostra të ngjashme."""
    sets = dataset.build(dataset.E10_DOCUMENTS + 20, 42)
    e10 = [
        s
        for s in build_samples(corpus(dataset.E10_DOCUMENTS, 42), seed=42)
        if s.split == "test"
    ]
    assert len(sets["test_texts"]) == len(e10)
    assert [r["label"] for r in sets["test_texts"]] == [
        s.defect.value if s.defect else "clean" for s in e10
    ]


def test_no_document_is_in_two_splits(small):
    _, _, samples = small
    by_document = {}
    for sample in samples:
        by_document.setdefault(sample.document_id, set()).add(sample.split)
    assert all(len(splits) == 1 for splits in by_document.values())


# --------------------------------------------------------------------
# Nga fjalitë te teksti
# --------------------------------------------------------------------

LABELS = ["clean", "ungrounded_number", "polarity_flip"]


def test_text_takes_the_most_confident_defect_above_threshold():
    probabilities = [[0.9, 0.05, 0.05], [0.2, 0.7, 0.1], [0.1, 0.1, 0.8]]
    assert evaluate_classifier.text_label(probabilities, LABELS, 0.5) == "polarity_flip"
    assert evaluate_classifier.text_label(probabilities, LABELS, 0.85) == "clean"


def test_threshold_is_chosen_on_validation_rows_only():
    rows = [
        {"label": "ungrounded_number", "probabilities": [[0.4, 0.6, 0.0]]},
        {"label": "clean", "probabilities": [[0.6, 0.4, 0.0]]},
    ]
    threshold, scores = evaluate_classifier.choose_threshold(rows, LABELS)
    assert 0.4 < threshold <= 0.6
    assert set(scores) == set(evaluate_classifier.THRESHOLDS)


# --------------------------------------------------------------------
# Buxheti i alarmeve të rreme (vendim i autorit, 2026-09-30)
# --------------------------------------------------------------------


def _curve(points):
    return {t: {"macro_f1": f1, "false_alarm_rate": far} for t, (f1, far) in points.items()}


def test_budget_picks_the_best_threshold_among_those_within_budget():
    curve = _curve({0.3: (0.9, 0.5), 0.5: (0.6, 0.04), 0.7: (0.4, 0.0)})
    assert evaluate_classifier.choose_within_budget(curve, 0.05) == 0.5


def test_budget_is_inclusive_at_the_boundary_and_breaks_ties_low():
    curve = _curve({0.4: (0.5, 0.05), 0.6: (0.5, 0.05), 0.8: (0.7, 0.051)})
    assert evaluate_classifier.choose_within_budget(curve, 0.05) == 0.4


def test_no_threshold_within_budget_is_reported_not_invented():
    curve = _curve({0.3: (0.9, 0.5), 0.5: (0.6, 0.06)})
    assert evaluate_classifier.choose_within_budget(curve, 0.05) is None


def test_false_alarm_rate_counts_clean_texts_only():
    rows = (
        [{"label": "clean", "probabilities": [[0.3, 0.7, 0.0]]}] * 2
        + [{"label": "clean", "probabilities": [[0.95, 0.05, 0.0]]}] * 2
        + [{"label": "ungrounded_number", "probabilities": [[0.1, 0.9, 0.0]]}] * 6
    )
    curve = evaluate_classifier.validation_curve(rows, LABELS)
    assert curve[0.5]["false_alarm_rate"] == 0.5  # 2 nga 4 të pastra, jo nga 10 tekste
    assert curve[0.7]["false_alarm_rate"] == 0.5  # p = 0.7 kalon pragun 0.7 (>=)
    assert curve[0.75]["false_alarm_rate"] == 0.0
    assert curve[0.95]["false_alarm_rate"] == 0.0


def _run(directory, val, test):
    import json

    directory.mkdir(parents=True, exist_ok=True)
    (directory / "run.json").write_text(
        json.dumps({"labels": LABELS, "input": "sentence", "model": "m"}), encoding="utf-8"
    )
    for name, rows in (("val", val), ("test", test)):
        with (directory / f"predictions_{name}.jsonl").open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row) + "\n")
    return directory


def _texts(label, defect_p, count):
    return [
        {"label": label, "probabilities": [[1 - defect_p, defect_p, 0.0]]} for _ in range(count)
    ]


def _indistinguishable_validation():
    """Defektet dhe gjysma e të pastrave duken njësoj (0.6); gjysma tjetër e të pastrave 0.1."""
    return (
        _texts("ungrounded_number", 0.6, 10)
        + _texts("clean", 0.6, 10)
        + _texts("clean", 0.1, 10)
    )


def test_the_two_rules_disagree_when_the_best_f1_blocks_clean_text(tmp_path):
    run = _run(tmp_path / "r", _indistinguishable_validation(), _texts("clean", 0.1, 4))
    result = evaluate_classifier.evaluate(run)
    points = result["operating_points"]
    assert points["max_macro_f1"]["threshold"] == 0.3
    assert points["max_macro_f1"]["val"]["false_alarm_rate"] == 0.5
    assert points["false_alarm_budget"]["threshold"] == 0.65
    assert points["false_alarm_budget"]["val"]["false_alarm_rate"] == 0.0
    assert points["false_alarm_budget"]["budget"] == 0.05
    assert result["deployed"] == "false_alarm_budget"
    assert result["deployed_threshold"] == 0.65


def test_thresholds_depend_on_validation_rows_only(tmp_path):
    val = _indistinguishable_validation()
    easy = evaluate_classifier.evaluate(_run(tmp_path / "a", val, _texts("clean", 0.1, 4)))
    hard = evaluate_classifier.evaluate(
        _run(tmp_path / "b", val, _texts("ungrounded_number", 0.99, 4) + _texts("clean", 0.99, 4))
    )
    for rule in ("max_macro_f1", "false_alarm_budget"):
        assert easy["operating_points"][rule]["threshold"] == hard["operating_points"][rule]["threshold"]


def test_with_no_threshold_within_budget_nothing_is_deployed(tmp_path):
    val = _texts("ungrounded_number", 0.99, 5) + _texts("clean", 0.99, 5)
    result = evaluate_classifier.evaluate(_run(tmp_path / "r", val, _texts("clean", 0.1, 2)))
    assert result["operating_points"]["false_alarm_budget"] is None
    assert result["deployed"] is None and result["deployed_threshold"] is None
    assert result["operating_points"]["max_macro_f1"] is not None  # rregulli 1 del gjithsesi


def test_the_budget_is_a_parameter_with_the_authors_value_as_default(tmp_path):
    assert evaluate_classifier.FALSE_ALARM_BUDGET == 0.05
    run = _run(tmp_path / "r", _indistinguishable_validation(), _texts("clean", 0.1, 2))
    strict = evaluate_classifier.evaluate(run, budget=0.6)
    assert strict["operating_points"]["false_alarm_budget"]["threshold"] == 0.3


# --------------------------------------------------------------------
# Rrjedhja
# --------------------------------------------------------------------


def test_skeleton_hides_numbers_names_and_terms():
    vocabulary = leakage._vocabulary()
    a = leakage.skeleton("Për Glukozë në serum vlera e matur është 128 mg/dL.", vocabulary)
    b = leakage.skeleton("Për Kalium në serum vlera e matur është 6,9 mg/dL.", vocabulary)
    assert a == b


def test_a_prefix_owned_by_one_label_is_reported_as_a_shortcut():
    train = [
        {"document_id": "d1", "sentence": "Vërehet gjithashtu diçka.", "label": "fabricated_finding"},
        {"document_id": "d1", "sentence": "Vlera është normale.", "label": "clean"},
    ]
    val = [{"document_id": "d2", "sentence": "Vlera është normale.", "label": "clean"}]
    result = leakage.report(train, val)
    assert result["shortcuts"]["fabricated_finding"]["is_shortcut"]
    assert result["shared_documents"] == 0


# --------------------------------------------------------------------
# Klasifikuesi në verifikim
# --------------------------------------------------------------------


class _Fake:
    """Parashikues që e quan çdo fjali me "sigurisht" përmbysje mohimi."""

    version = "fake/1"
    labels = ("clean", "polarity_flip", "ungrounded_number")
    mode = "sentence"

    def __init__(self):
        self.seen = []

    def __call__(self, sentences, context):
        self.seen += sentences
        return [
            [0.1, 0.85, 0.05] if "sigurisht" in s else [0.95, 0.03, 0.02] for s in sentences
        ]


def test_classifier_violations_carry_their_confidence():
    context = build_reference_context()
    text = build_template(context) + " Kjo është sigurisht e qartë."
    result = classifier.verify_with_classifier(context, text, _Fake(), threshold=0.5)
    found = result.by_detector(DetectedBy.CLASSIFIER)

    assert len(found) == 1
    assert found[0].type is ViolationType.POLARITY_FLIP
    assert found[0].confidence == pytest.approx(0.85)
    assert result.classifier_version == "fake/1"


def test_sentences_the_rules_flagged_are_not_judged_again():
    """ADR 0009 — klasifikuesi vepron mbi atë që rregullat nuk e kapin."""
    context = build_reference_context()
    ruled = "Vlera ishte sigurisht 987654."
    text = f"{build_template(context)} {ruled}"
    predictor = _Fake()
    result = classifier.verify_with_classifier(context, text, predictor, threshold=0.5)

    assert ruled not in predictor.seen
    assert result.by_detector(DetectedBy.CLASSIFIER) == ()
    assert result.by_detector(DetectedBy.RULE) != ()


def test_below_threshold_is_silence():
    context = GroundingContext(document_id=uuid4())
    found = list(classifier.check(context, "Kjo është sigurisht e qartë.", _Fake(), 0.9))
    assert found == []


def test_context_mode_receives_the_serialized_context():
    context = build_reference_context()

    class Reader(_Fake):
        mode = "context"

        def __call__(self, sentences, serialized):
            self.context = serialized
            return super().__call__(sentences, serialized)

    predictor = Reader()
    list(classifier.check(context, "Një fjali.", predictor, 0.5))
    assert "Glukozë në serum 128 mg/dL e lartë" in predictor.context
    assert "mjeku: Nuk ka shenja të anemisë" in predictor.context
