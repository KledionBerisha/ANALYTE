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

Kur kushti rigjeneron, çdo draft i modelit numërohet ndër të prodhuarat,
dhe fjalitë e të gjithë drafteve formojnë emëruesin e të dyja shkallëve.
Emëruesi i përbashkët i bën të krahasueshme drejtpërdrejt: dallimi mes tyre
është pikërisht ajo që verifikimi ndali.

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
from .base import _round, bootstrap_ratio, count_sentences


def measure(pairs: list[tuple[GroundingContext, PipelineOutput]]) -> dict[str, Any]:
    sentences = 0
    produced: dict[str, int] = {v.value: 0 for v in ViolationType}
    reaching_user: dict[str, int] = {v.value: 0 for v in ViolationType}
    by_detector: dict[str, int] = {d.value: 0 for d in DetectedBy}

    per_document: list[tuple[int, int, int]] = []
    """(të prodhuara, te përdoruesi, fjali) për çdo dokument — njësia e
    rimostrimit për intervalet e besimit."""

    documents_with_output = 0
    documents_with_violation = 0
    fallbacks = 0
    clean_deliveries = 0

    for _, output in pairs:
        if output.state is ProcessingState.TEMPLATE_FALLBACK:
            fallbacks += 1
        drafts = output.drafts()
        if not drafts:
            continue

        documents_with_output += 1
        had_violation = False
        document_sentences = document_produced = 0
        for text, verification in drafts:
            document_sentences += count_sentences(text)
            for violation in verification.violations if verification else ():
                had_violation = True
                document_produced += 1
                produced[violation.type.value] += 1
                by_detector[violation.detected_by.value] += 1
        sentences += document_sentences
        if had_violation:
            documents_with_violation += 1

        # Verifikimi e ndal daljen; shkelja mbërrin te përdoruesi vetëm nëse
        # është në tekstin që iu dorëzua — drafti i pranuar ose shablloni.
        reaching = output.violations_reaching_user()
        for violation in reaching:
            reaching_user[violation.type.value] += 1
        if not reaching:
            clean_deliveries += 1
        per_document.append((document_produced, len(reaching), document_sentences))

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
        "ci95_produced": bootstrap_ratio(
            [(p, s) for p, _, s in per_document], scale=100.0
        ),
        "ci95_reaching_user": bootstrap_ratio(
            [(r, s) for _, r, s in per_document], scale=100.0
        ),
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
