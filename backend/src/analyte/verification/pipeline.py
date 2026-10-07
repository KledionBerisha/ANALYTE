"""
Shtresa e verifikimit: rregullat mbi një tekst të gjeneruar.

"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator
from uuid import UUID, uuid4

from analyte.domain.models import GroundingContext, VerificationResult, Violation

from . import rules_exact, rules_policy, rules_prose, ruleset

Rule = Callable[[GroundingContext, str], Iterator[Violation]]

RULES: tuple[tuple[str, Rule], ...] = (
    ("R1", rules_exact.check_numbers),
    ("R2", rules_exact.check_analytes),
    ("R3", rules_exact.check_direction),
    ("R4", rules_exact.check_critical_coverage),
    ("R5", rules_prose.check_polarity),
    ("R6", rules_prose.check_hedging),
    ("R7", rules_prose.check_fabrication),
    ("R8", rules_prose.check_recommendations),
    ("R9", rules_prose.check_term_explanations),
    ("SP1-3", rules_policy.check_prohibited_claims),
)


def verify(
    context: GroundingContext,
    text: str,
    *,
    explanation_id: UUID | None = None,
    rules: str | None = None,
) -> VerificationResult:
    """Zbaton katalogun e plotë të rregullave mbi një tekst.

    Kohëzgjatja matet dhe ruhet: verifikimi qëndron ndërmjet gjenerimit
    dhe dorëzimit, prandaj kostoja e tij është pjesë e sjelljes së
    sistemit dhe jo hollësi zbatimi.

    `rules` zgjedh versionin e katalogut (`r1.3` të ngrirë, ose `r1.4`); pa të përdoret ai i
    parazgjedhur. Versioni i përdorur ruhet në rezultat.
    """
    started = time.perf_counter()
    violations: list[Violation] = []
    with ruleset.using(rules) as version:
        for _, rule in RULES:
            violations.extend(rule(context, text))
    duration = int((time.perf_counter() - started) * 1000)

    return VerificationResult(
        explanation_id=explanation_id or uuid4(),
        violations=tuple(violations),
        rules_version=version,
        duration_ms=duration,
    )
