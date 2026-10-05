"""`scripts/verify_corpus.py` dhe `.gitattributes`: një kopje e re e depos duhet t'i ruajë bajtet që u hashuan."""

from __future__ import annotations

import hashlib
from pathlib import Path

from scripts import verify_corpus

ROOT = Path(__file__).resolve().parents[2]


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_resources_are_marked_binary_so_git_keeps_their_bytes():
    rules = (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
    assert "resources/*.csv -text" in [line.strip() for line in rules]


def test_compare_separates_a_line_ending_change_from_a_content_change(tmp_path):
    crlf = b"a,b\r\n1,2\r\n"
    (tmp_path / "same.csv").write_bytes(crlf)
    (tmp_path / "eol.csv").write_bytes(crlf.replace(b"\r\n", b"\n"))  # git ktheu LF
    (tmp_path / "edited.csv").write_bytes(b"a,b\r\n1,3\r\n")
    (tmp_path / "mixed.csv").write_bytes(b"a,b\r\n1,3\n")
    manifest = {
        "same.csv": _sha(crlf),
        "eol.csv": _sha(crlf),
        "edited.csv": _sha(crlf),
        "mixed.csv": _sha(b"a,b\r\n1,2\n"),
        "gone.csv": _sha(crlf),
    }
    status = {row["file"]: row["status"] for row in verify_corpus.compare(manifest, tmp_path)}
    assert status == {
        "same.csv": "match",
        "eol.csv": "line_endings_only",
        "edited.csv": "changed",
        "mixed.csv": "changed_or_mixed_endings",
        "gone.csv": "missing",
    }
