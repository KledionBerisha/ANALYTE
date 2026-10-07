"""
Prejardhja e rezultateve të E10 dhe E11.

"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evaluation import provenance
from ml import evaluate_classifier, evaluate_rule_detector


def test_code_metadata_names_the_code_the_rules_and_the_interpreter():
    code = provenance.code_metadata()
    assert set(code) == {
        "git_sha",
        "working_tree_dirty",
        "rules_version",
        "policy_version",
        "python",
    }
    assert code["rules_version"] and code["policy_version"]


def test_metadata_has_the_shape_the_traceability_figure_reads(monkeypatch):
    pytest.importorskip("matplotlib")
    from scripts.figures import evaluation_chain

    monkeypatch.setattr(provenance, "git_state", lambda: ("a" * 40, False))
    meta = provenance.metadata("EX", {"name": "n", "version": "v"})
    assert evaluation_chain.trace_of({"metadata": meta}) == "e plotë"
    monkeypatch.setattr(provenance, "git_state", lambda: ("a" * 40, True))
    assert (
        evaluation_chain.trace_of(
            {"metadata": provenance.metadata("EX", {"name": "n", "version": "v"})}
        )
        == "pa commit"
    )
    monkeypatch.setattr(provenance, "git_state", lambda: ("unknown", None))
    assert (
        evaluation_chain.trace_of({"metadata": provenance.metadata("EX", {"name": "n"})})
        == "pjesore"
    )


def test_digest_depends_on_content_and_names_but_not_on_the_order_given(tmp_path: Path):
    a, b = tmp_path / "a.txt", tmp_path / "b.txt"
    a.write_text("një", encoding="utf-8")
    b.write_text("dy", encoding="utf-8")
    first = provenance.digest([a, b])
    assert first == provenance.digest([b, a])
    b.write_text("tre", encoding="utf-8")
    assert provenance.digest([a, b]) != first
    renamed = tmp_path / "c.txt"
    renamed.write_text("tre", encoding="utf-8")
    assert provenance.digest([a, renamed]) != provenance.digest([a, b])


def test_the_corruption_corpus_version_changes_with_its_size_and_seed():
    base = evaluate_rule_detector.corpus_version(200, 42)
    assert base == evaluate_rule_detector.corpus_version(200, 42)
    assert base != evaluate_rule_detector.corpus_version(201, 42)
    assert base != evaluate_rule_detector.corpus_version(200, 7)
    assert base.startswith("gen-1.0/corruption/s42/n200/")


def _classifier_run(directory: Path, probability: float) -> Path:
    labels = ["clean", "ungrounded_number", "ungrounded_analyte"]
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "run.json").write_text(
        json.dumps({"labels": labels, "input": "sentence", "model": "m"}), encoding="utf-8"
    )
    rows = [
        {"label": "clean", "probabilities": [[1 - probability, probability, 0.0]]} for _ in range(4)
    ]
    for name in ("val", "test"):
        with (directory / f"predictions_{name}.jsonl").open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row) + "\n")
    return directory


def test_the_classifier_result_carries_provenance_tied_to_the_predictions_it_read(tmp_path: Path):
    first = evaluate_classifier.evaluate(_classifier_run(tmp_path / "a", 0.1))
    again = evaluate_classifier.evaluate(_classifier_run(tmp_path / "a2", 0.1))
    other = evaluate_classifier.evaluate(_classifier_run(tmp_path / "b", 0.9))
    meta = first["metadata"]
    assert meta["experiment_id"] == "E11"
    assert meta["code"]["git_sha"] and "working_tree_dirty" in meta["code"]
    assert meta["dataset"]["name"] == "colab-run/sentence"
    assert meta["dataset"]["documents"] == 4
    # e njëjta lëndë → i njëjti version; parashikime të ndryshme → version tjetër
    assert meta["dataset"]["version"] == again["metadata"]["dataset"]["version"]
    assert meta["dataset"]["version"] != other["metadata"]["dataset"]["version"]


def test_digest_does_not_depend_on_line_endings(tmp_path: Path):
    """Git shndërron mbarimet e rreshtave mes kopjeve të punës; e njëjta përmbajtje duhet të japë të njëjtin id."""
    files = {}
    for name, content in (
        ("lf", b"a,b\nc,d\n"),
        ("crlf", b"a,b\r\nc,d\r\n"),
        ("mixed", b"a,b\r\nc,d\n"),
    ):
        directory = tmp_path / name
        directory.mkdir()
        files[name] = directory / "t.csv"
        files[name].write_bytes(content)
    assert (
        provenance.digest([files["lf"]])
        == provenance.digest([files["crlf"]])
        == provenance.digest([files["mixed"]])
    )
    files["lf"].write_bytes(b"a,b\nc,e\n")
    # përmbajtja tjetër ndryshon id-në
    assert provenance.digest([files["lf"]]) != provenance.digest([files["crlf"]])
