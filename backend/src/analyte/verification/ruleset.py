"""
Versioni aktiv i katalogut të rregullave.

`r1.3` mbetet i riprodhueshëm: eksperimentet e ngrira (E4, E6–E9, E10, E11 dhe rezultatet mbi B, C) u matën me të, dhe
përgjigjet e modelit në cache varen nga cilat drafte i ndalonte ai katalog. `r1.4` përmirëson katër rregulla (R1, R2, R3, R9)
dhe është versioni që përdor shërbimi. Versioni zgjidhet me `verify(..., rules=...)`; rregullat e lexojnë këtu, që të mos
duhet të kalojnë një parametër nëpër çdo funksion ndihmës.

`ContextVar` e bën zgjedhjen të sigurt për fije dhe për detyra asinkrone: një verifikim me `r1.3` nuk e ndryshon një tjetër
që po ekzekutohet njëkohësisht me `r1.4`.
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
        raise ValueError(f"version i panjohur i rregullave: {chosen}; njihen {', '.join(RULES_VERSIONS)}")
    token = _active.set(chosen)
    try:
        yield chosen
    finally:
        _active.reset(token)
