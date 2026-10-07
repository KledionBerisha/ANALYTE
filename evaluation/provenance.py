"""
Prejardhja e një rezultati: cili kod, cilat të dhëna, kur.

"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from analyte.domain.policy import LEGACY_RULES_VERSION, POLICY_VERSION


def git_state() -> tuple[str, bool | None]:
    """Sha-ja e kodit dhe nëse pema e punës kishte ndryshime të paruajtura."""
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        ).stdout.strip()
        return revision, bool(status)
    except (subprocess.SubprocessError, OSError, FileNotFoundError):
        return "unknown", None


def code_metadata(rules_version: str = LEGACY_RULES_VERSION) -> dict[str, Any]:
    """Prejardhja e kodit. `rules_version` është katalogu me të cilin u ekzekutua eksperimenti: `r1.3` e ngrirë, përveç kur
    thuhet ndryshe (një ekzekutim me `r1.4` duhet ta thotë, përndryshe rezultati do të dukej si i ngrirë)."""
    revision, dirty = git_state()
    return {
        "git_sha": revision,
        "working_tree_dirty": dirty,
        "rules_version": rules_version,
        "policy_version": POLICY_VERSION,
        "python": sys.version.split()[0],
    }


def digest(paths: Iterable[Path], *, length: int = 16) -> str:
    """Shuma kontrolluese e disa skedarëve, e varur nga emrat dhe nga përmbajtja e tyre.

    Mbarimet e rreshtave (CRLF dhe LF) trajtohen njësoj: git i ndryshon ato kur skedari kalon nga një
    kopje pune te një tjetër (`core.autocrlf`), dhe një identifikues që ndryshon me to nuk do ta
    identifikonte të njëjtën lëndë në dy ekzekutime. Tabelat e burimeve (terminologjia, kombinimet)
    kanë mbarime të përziera në kopjen e punës; `manifest.json` i korpusit hash-on bajtet e
    papërpunuara dhe përputhet vetëm me kopjen ku u prodhua."""
    h = hashlib.sha256()
    for path in sorted(paths, key=lambda p: p.name):
        h.update(path.name.encode("utf-8"))
        h.update(b"\0")
        h.update(path.read_bytes().replace(b"\r\n", b"\n"))
        h.update(b"\0")
    return h.hexdigest()[:length]


def metadata(
    experiment_id: str, dataset: dict[str, Any], rules_version: str = LEGACY_RULES_VERSION
) -> dict[str, Any]:
    """Metadata me të njëjtën formë si ajo e harness-it, që `trace_of` (Figura 11) ta lexojë."""
    return {
        "experiment_id": experiment_id,
        "dataset": dataset,
        "code": code_metadata(rules_version),
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
