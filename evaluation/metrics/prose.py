"""
PK3 — besnikëria e thjeshtimit.

Pyetja është e ngushtë dhe e përcaktuar: a mbijeton kuptimi i mjekut në
tekstin e thjeshtuar? Tri gjëra mund të prishen, dhe secila matet veçmas
sepse secila ka shkak tjetër:

  - **Polariteti.** "Nuk ka shenja anemie" që bëhet "ka shenja anemie" e
    përmbys kuptimin plotësisht. Matet si përpjesa e pohimeve të mohuara
    të burimit që e ruajnë mohimin.
  - **Pasiguria.** "Nuk përjashtohet hipotiroidizëm" që bëhet
    "ka hipotiroidizëm" e kthen hamendjen në diagnozë. Kjo është forma më
    e rrezikshme e humbjes, sepse teksti del më i qartë dhe më i lexueshëm
    pikërisht duke u bërë i pasaktë.
  - **Shtesat.** Gjetje që nuk ekziston në kontekst, e shfaqur në dalje.

Numëruesi vjen nga shkeljet e verifikimit dhe emëruesi nga e vërteta bazë
e burimit. Kjo do të thotë se PK3 mat aq sa sheh verifikimi: nëse një
mohim përmbyset dhe asnjë rregull nuk e kap, PK3 do të tregojë ruajtje të
përsosur. Prandaj PK3 lexohet gjithmonë bashkë me PK6, që mat pikërisht
aftësinë zbuluese; asnjëri nga të dy nuk qëndron vetëm.
"""

from __future__ import annotations

from typing import Any

from analyte.domain.enums import AssertionKind, Certainty, Polarity, ViolationType
from analyte.domain.models import GroundingContext

from ..pipeline import PipelineOutput
from .base import _round, count_sentences


def measure(pairs: list[tuple[GroundingContext, PipelineOutput]]) -> dict[str, Any]:
    negated = hedged = recommendations = 0
    flips = hedge_losses = omissions = fabrications = 0
    sentences = 0
    generated = 0

    for truth, output in pairs:
        if not output.explanation:
            # Emëruesi numëron vetëm dokumentet që prodhuan tekst. Një
            # dokument pa dalje nuk dëshmon as ruajtje as humbje, dhe po ta
            # linim mohimin e tij në emërues me zero humbje, një sistem që
            # nuk shkruan asgjë do të dilte me ruajtje të përsosur.
            continue

        generated += 1
        sentences += count_sentences(output.explanation)
        negated += sum(1 for a in truth.assertions if a.polarity is Polarity.NEGATED)
        hedged += sum(1 for a in truth.assertions if a.certainty is Certainty.HEDGED)
        recommendations += sum(
            1 for a in truth.assertions if a.kind is AssertionKind.RECOMMENDATION
        )

        violations = output.verification.violations if output.verification else ()
        for violation in violations:
            if violation.type is ViolationType.POLARITY_FLIP:
                flips += 1
            elif violation.type is ViolationType.HEDGE_REMOVED:
                hedge_losses += 1
            elif violation.type is ViolationType.OMITTED_RECOMMENDATION:
                omissions += 1
            elif violation.type is ViolationType.FABRICATED_FINDING:
                fabrications += 1

    return {
        "documents": len(pairs),
        "documents_with_output": generated,
        "sentences": sentences,
        "negation_preservation": _preservation(negated, flips),
        "hedge_preservation": _preservation(hedged, hedge_losses),
        "recommendation_preservation": _preservation(recommendations, omissions),
        "fabricated_findings_per_100_sentences": _per_hundred(fabrications, sentences),
        "counts": {
            "negated_assertions": negated,
            "hedged_assertions": hedged,
            "recommendations": recommendations,
            "polarity_flips": flips,
            "hedges_removed": hedge_losses,
            "recommendations_omitted": omissions,
            "fabricated_findings": fabrications,
        },
    }


def _preservation(source: int, lost: int) -> float | None:
    """Përpjesa e ruajtur.

    Kthen `None` kur burimi nuk kishte asgjë të tillë: një dokument pa
    mohime nuk dëshmon as ruajtje as humbje, dhe 1.0 aty do të ishte
    shpikje e një suksesi që nuk u mat.
    """
    if source == 0:
        return None
    return _round(max(0.0, (source - lost) / source))


def _per_hundred(count: int, sentences: int) -> float | None:
    if sentences == 0:
        return None
    return _round(100.0 * count / sentences)
