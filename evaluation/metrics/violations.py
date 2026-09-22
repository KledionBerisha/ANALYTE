"""
PK5 — shkalla e pohimeve të pambështetura.

Metrika kryesore e punimit dhe e vetmja që nuk hiqet kurrë (§14.3).
Shprehet si shkelje për 100 fjali të gjeneruara, e ndarë sipas llojit.

Dallimi që bart tërë argumentin është mes dy numrave:

  - **shkeljet e prodhuara** — sa gabime bëri modeli gjuhësor;
  - **shkeljet që mbërrijnë te përdoruesi** — sa prej tyre kaluan.

Kushtet E6 dhe E7 (pa verifikim) i kanë të dy numrat të barabartë. Kushtet
E8 dhe E9 e ulin të dytin pa e prekur të parin, sepse verifikimi nuk e bën
modelin më të mirë — ai vendos çfarë del jashtë. Nëse këto dy numra
raportohen si një i vetëm, ablacioni humbet kuptimin.

Përpjesa e daljeve që përfunduan në shabllonin determinist raportohet
gjithashtu: ajo është çmimi i verifikimit. Një sistem që refuzon gjithçka
ka zero shkelje te përdoruesi dhe nuk shërben për asgjë; pa këtë numër
kjo nuk do të dukej.
"""

from __future__ import annotations

from typing import Any

from analyte.domain.enums import DetectedBy, ProcessingState, ViolationType
from analyte.domain.models import GroundingContext

from ..pipeline import PipelineOutput
from .base import _round, count_sentences


def measure(pairs: list[tuple[GroundingContext, PipelineOutput]]) -> dict[str, Any]:
    sentences = 0
    produced: dict[str, int] = {v.value: 0 for v in ViolationType}
    reaching_user: dict[str, int] = {v.value: 0 for v in ViolationType}
    by_detector: dict[str, int] = {d.value: 0 for d in DetectedBy}

    documents_with_output = 0
    documents_with_violation = 0
    fallbacks = 0
    clean_deliveries = 0

    for _, output in pairs:
        if output.state is ProcessingState.TEMPLATE_FALLBACK:
            fallbacks += 1
        if not output.explanation:
            continue

        documents_with_output += 1
        sentences += count_sentences(output.explanation)

        violations = output.verification.violations if output.verification else ()
        if violations:
            documents_with_violation += 1
        else:
            clean_deliveries += 1

        for violation in violations:
            produced[violation.type.value] += 1
            by_detector[violation.detected_by.value] += 1
            # Verifikimi e ndal daljen; pra shkelja mbërrin te përdoruesi
            # vetëm nëse teksti u dorëzua megjithatë.
            if output.delivered:
                reaching_user[violation.type.value] += 1

    total_produced = sum(produced.values())
    total_reaching = sum(reaching_user.values())

    return {
        "documents": len(pairs),
        "documents_with_output": documents_with_output,
        "sentences": sentences,
        "violations_produced": total_produced,
        "violations_reaching_user": total_reaching,
        "rate_produced_per_100_sentences": _rate(total_produced, sentences),
        "rate_reaching_user_per_100_sentences": _rate(total_reaching, sentences),
        "by_type_produced": dict(sorted(produced.items())),
        "by_type_reaching_user": dict(sorted(reaching_user.items())),
        "by_detector": dict(sorted(by_detector.items())),
        "documents_with_violation": documents_with_violation,
        "clean_deliveries": clean_deliveries,
        "template_fallbacks": fallbacks,
        "fallback_share": _share(fallbacks, len(pairs)),
    }


def _rate(count: int, sentences: int) -> float | None:
    if sentences == 0:
        return None
    return _round(100.0 * count / sentences)


def _share(count: int, total: int) -> float | None:
    if total == 0:
        return None
    return _round(count / total)
