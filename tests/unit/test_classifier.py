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
