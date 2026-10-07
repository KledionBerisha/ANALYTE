"""
Zbulimi i pasigurisë së shprehur.

"""

from __future__ import annotations

from dataclasses import dataclass

from analyte.domain.enums import Certainty
from analyte.textnorm import fold

HEDGE_CUES: tuple[str, ...] = (
    "mund te",
    "ndoshta",
    "ka gjasa",
    "duket",
    "duken",
    "sugjeron",
    "sugjerojne",
    "e mundshme",
    "i mundshem",
    "nuk perjashtohet",
    "nuk mund te perjashtohet",
    "ka te ngjare",
    "dyshohet",
    "me shume gjasa",
)


@dataclass(frozen=True, slots=True)
class HedgeResult:
    """Vendimi për një fjali, bashkë me shenjën që e shkaktoi."""

    certainty: Certainty
    cue: str | None

    @property
    def hedged(self) -> bool:
        return self.certainty is Certainty.HEDGED


CONFIRMED = HedgeResult(Certainty.CONFIRMED, None)


def detect(sentence: str) -> HedgeResult:
    """Siguria e shprehur në një fjali.

    Kërkohet shenja më e gjatë e para, që "nuk përjashtohet" të mos
    raportohet si "mund të" kur të dyja shfaqen në të njëjtën fjali; shenja
    e raportuar përdoret në dëshminë e shkeljes dhe duhet të jetë ajo që
    vërtet e shkaktoi vendimin.
    """
    folded = fold(sentence)
    for cue in sorted(HEDGE_CUES, key=len, reverse=True):
        if cue in folded:
            return HedgeResult(Certainty.HEDGED, cue)
    return CONFIRMED


def certainty_of(sentence: str) -> Certainty:
    return detect(sentence).certainty
