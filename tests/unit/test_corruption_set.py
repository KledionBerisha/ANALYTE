"""
Testet e korpusit të korruptuar.

"""

import random

import pytest

from analyte.domain.enums import ViolationType
from analyte.generation.templates import build
from analyte.verification.pipeline import verify
from data_generator.ground_truth import build_document
from data_generator.ids import IdFactory
from ml.data.build_corruption_set import CORRUPTORS, Sample, build_samples, load, write


@pytest.fixture(scope="module")
def documents():
    """Mjaftueshëm dokumente sa të shfaqen të shtatë llojet e defekteve.

    Pohimet me rezervë janë të rralla — rreth një në tetë dokumente — dhe
    me një grup të vogël prove lloji i tyre mungon fare. Zgjidhja është
    grup më i madh dhe jo pohim më i butë: një test që pranon mungesën e
    një lloji nuk do ta vërente kurrë prishjen e tij.
    """
    out = []
    for index in range(30):
        rng = random.Random(f"corr{index}")
        document = build_document(rng, IdFactory(rng), scanned_share=0.0)
        out.append((str(document.document_id), document.context))
    return out


@pytest.fixture(scope="module")
def samples(documents):
    return build_samples(documents, seed=3)


def test_every_document_yields_one_clean_sample(samples, documents):
    clean = [s for s in samples if s.defect is None]
    assert len(clean) == len(documents)


def test_clean_samples_really_are_clean(samples, documents):
    """Baza duhet të kalojë çdo rregull, përndryshe defektet e injektuara
    mbi të nuk kanë etiketë të besueshme."""
    contexts = dict(documents)
    for sample in samples:
        if sample.defect is None:
            assert verify(contexts[sample.document_id], sample.text).passed


def test_corruption_actually_changes_the_text(samples, documents):
    contexts = dict(documents)
    for sample in samples:
        if sample.defect is not None:
            clean = build(contexts[sample.document_id])
            assert sample.text != clean


def test_every_defect_type_is_produced(samples):
    produced = {s.defect for s in samples if s.defect}
    expected = {defect for defect, _ in CORRUPTORS}
    assert produced == expected


def test_each_corruption_is_detected_as_its_own_defect(samples, documents):
    """Çdo defekt i injektuar duhet të aktivizojë rregullin e vet.

    Ky nuk është matje e PK6 — ai bëhet mbi grupin testues me metrikat e
    vlerësimit. Këtu kontrollohet vetëm që lidhja defekt-rregull nuk është
    prishur në heshtje.
    """
    contexts = dict(documents)
    missed: list[tuple[str, str]] = []
    for sample in samples:
        if sample.defect is None:
            continue
        detected = {v.type for v in verify(contexts[sample.document_id], sample.text).violations}
        if sample.defect not in detected:
            missed.append((sample.defect.value, sample.detail))

    assert len(missed) <= len(samples) * 0.1, missed


def test_splits_follow_the_source_document(samples):
    """Dy mostra nga i njëjti dokument nuk bien kurrë në grupe të ndryshme.

    Ndarja sipas fjalisë do të lejonte klasifikuesin e Fazës 7 të mësonte
    dokumentin dhe jo defektin.
    """
    by_document: dict[str, set[str]] = {}
    for sample in samples:
        by_document.setdefault(sample.document_id, set()).add(sample.split)
    assert all(len(splits) == 1 for splits in by_document.values())


def test_every_split_is_represented(samples):
    assert {s.split for s in samples} == {"train", "val", "test"}


def test_building_is_reproducible(documents):
    assert [s.to_json() for s in build_samples(documents, seed=3)] == [
        s.to_json() for s in build_samples(documents, seed=3)
    ]


def test_round_trip_through_jsonl(samples, tmp_path):
    path = write(samples, tmp_path / "corruption.jsonl")
    restored = load(path)
    assert [s.to_json() for s in restored] == [s.to_json() for s in samples]


def test_number_corruption_never_lands_on_a_grounded_value(samples, documents):
    """Kurthi kryesor: një "korruptim" që prodhon vlerë të mbështetur do të
    ishte mostër me etiketë të rreme."""
    contexts = dict(documents)
    for sample in samples:
        if sample.defect is not ViolationType.UNGROUNDED_NUMBER:
            continue
        detected = {v.type for v in verify(contexts[sample.document_id], sample.text).violations}
        assert ViolationType.UNGROUNDED_NUMBER in detected, sample.detail


def test_sample_serialisation_keeps_the_label():
    sample = Sample("doc", "tekst", ViolationType.HEDGE_REMOVED, "test", "x")
    assert sample.to_json()["defect"] == "hedge_removed"
