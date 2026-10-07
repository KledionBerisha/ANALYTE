"""
Skripti i pamjeve të ndërfaqes (Figurat 12–16): zgjedhja e dokumentit dhe pjesët që s'kërkojnë shfletues.

"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import export_screenshots as shots

ROOT = Path(__file__).resolve().parents[2]


def _corpus(tmp_path: Path, documents: list[dict]) -> Path:
    entries = []
    for index, doc in enumerate(documents):
        relative = f"documents/doc_{index:05d}"
        (tmp_path / "documents").mkdir(exist_ok=True)
        truth = {
            "context": {
                "findings": [{"status": s} for s in doc["statuses"]],
                "cross_refs": [{"state": st} for st in doc["states"]],
            }
        }
        (tmp_path / f"{relative}.json").write_text(json.dumps(truth), encoding="utf-8")
        entries.append(
            {
                "index": index,
                "file": f"{relative}.json",
                "pdf": f"{relative}.pdf",
                "is_scanned": doc["scanned"],
            }
        )
    (tmp_path / "manifest.json").write_text(json.dumps({"documents": entries}), encoding="utf-8")
    return tmp_path


def test_the_document_has_a_critical_value_a_contradiction_and_is_digital(tmp_path):
    data = _corpus(
        tmp_path,
        [
            {
                "scanned": False,
                "statuses": ["normal"] * 5,
                "states": ["agreement"],
            },  # as kritik as kundërshtim
            {
                "scanned": True,
                "statuses": ["critical_high"] + ["normal"] * 3,
                "states": ["contradiction"],
            },  # e skanuar
            {
                "scanned": False,
                "statuses": ["critical_low"] + ["normal"] * 9,
                "states": ["contradiction"],
            },  # i përshtatshëm, i gjatë
            {
                "scanned": False,
                "statuses": ["critical_high"] + ["normal"] * 2,
                "states": ["contradiction"],
            },  # i përshtatshëm, më i shkurtri
            {
                "scanned": False,
                "statuses": ["high"] * 3,
                "states": ["contradiction"],
            },  # pa vlerë kritike
        ],
    )
    assert shots.pick_document(data) == data / "documents/doc_00003.pdf"


def test_no_suitable_document_is_an_error_not_a_silent_default(tmp_path):
    data = _corpus(tmp_path, [{"scanned": False, "statuses": ["normal"], "states": ["agreement"]}])
    with pytest.raises(SystemExit, match="vlerë kritike dhe kundërshtim"):
        shots.pick_document(data)


@pytest.mark.skipif(
    not (ROOT / "data" / "v1" / "manifest.json").exists(), reason="korpusi data/v1 mungon"
)
def test_the_real_corpus_gives_the_document_named_in_the_thesis():
    assert shots.pick_document(ROOT / "data" / "v1").name == "doc_00335.pdf"


def test_figure_names_cover_exactly_figures_12_to_16():
    assert sorted(shots.NAMES) == [12, 13, 14, 15, 16]
    thesis = (ROOT / "docs" / "thesis" / "teza_v3.md").read_text(encoding="utf-8")
    for name in shots.NAMES.values():
        assert f"figures/{name}.png" in thesis, name  # çdo pamje që skripti prodhon është te teksti


def test_a_busy_port_is_detected(tmp_path):
    import socket

    with socket.socket() as busy:
        busy.bind(("127.0.0.1", 0))
        busy.listen()
        port = busy.getsockname()[1]
        assert shots._port_free(port) is False
    assert shots._port_free(port) is True
