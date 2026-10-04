"""
Prejardhja e një rezultati: cili kod, cilat të dhëna, kur.

Harness-i e shkruan këtë te çdo eksperiment që kalon nëpër të (E1–E9). E10 dhe
E11 ekzekutohen nga skriptet e `ml/`, jashtë harness-it, dhe rezultatet e tyre nuk
mbanin sha-n e kodit as versionin e të dhënave, prandaj Figura 11 i shënonte
«pjesore». Ky modul i jep të njëjtën metadatë çdo skripti që shkruan një rezultat.

Një rezultat quhet i gjurmueshëm vetëm kur `working_tree_dirty` është false:
atëherë sha-ja e identifikon kodin. Prandaj skriptet duhet ekzekutuar nga një
pemë pune e pastër, me `--out` jashtë saj, sepse çdo skedar i ri brenda pemës,
përfshirë vetë rezultati, e bën pemën të papastër.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from analyte.domain.policy import POLICY_VERSION, RULES_VERSION


def git_state() -> tuple[str, bool | None]:
    """Sha-ja e kodit dhe nëse pema e punës kishte ndryshime të paruajtura."""
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True, timeout=10,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, check=True, timeout=10,
        ).stdout.strip()
        return revision, bool(status)
    except (subprocess.SubprocessError, OSError, FileNotFoundError):
        return "unknown", None


def code_metadata() -> dict[str, Any]:
    revision, dirty = git_state()
    return {
        "git_sha": revision,
        "working_tree_dirty": dirty,
        "rules_version": RULES_VERSION,
        "policy_version": POLICY_VERSION,
        "python": sys.version.split()[0],
    }


def digest(paths: Iterable[Path], *, length: int = 16) -> str:
    """Shuma kontrolluese e disa skedarëve, e varur nga emrat dhe nga përmbajtja e tyre."""
    h = hashlib.sha256()
    for path in sorted(paths, key=lambda p: p.name):
        h.update(path.name.encode("utf-8"))
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()[:length]


def metadata(experiment_id: str, dataset: dict[str, Any]) -> dict[str, Any]:
    """Metadata me të njëjtën formë si ajo e harness-it, që `trace_of` (Figura 11) ta lexojë."""
    return {
        "experiment_id": experiment_id,
        "dataset": dataset,
        "code": code_metadata(),
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
