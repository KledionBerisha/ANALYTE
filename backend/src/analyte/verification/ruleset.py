"""
Versioni aktiv i katalogut të rregullave.

"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from analyte.domain.policy import LEGACY_RULES_VERSION, RULES_VERSION, RULES_VERSIONS

_active: ContextVar[str] = ContextVar("analyte_rules_version", default=RULES_VERSION)


def active() -> str:
    return _active.get()


def modern() -> bool:
    """A është aktiv katalogu i ri (`r1.4`)? `r1.3` është ai i ngrirë."""
    return _active.get() != LEGACY_RULES_VERSION


@contextmanager
def using(version: str | None) -> Iterator[str]:
    """Aktivizon një version për kohëzgjatjen e bllokut. `None` do të thotë versioni i parazgjedhur."""
    chosen = version or RULES_VERSION
    if chosen not in RULES_VERSIONS:
        raise ValueError(
            f"version i panjohur i rregullave: {chosen}; njihen {', '.join(RULES_VERSIONS)}"
        )
    token = _active.set(chosen)
    try:
        yield chosen
    finally:
        _active.reset(token)
