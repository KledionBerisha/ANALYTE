"""
Zbulimi i pasigurisë së shprehur.

Mjeku shkruan me shkallë të ndryshme sigurie, dhe ajo shkallë është
përmbajtje e vërtetë e raportit. "Nuk përjashtohet hipotiroidizëm" nuk
është e njëjta gjë me "ka hipotiroidizëm", dhe dallimi mes tyre është
pikërisht ai që humbet më lehtë kur teksti thjeshtohet: fjalia bëhet më e
qartë, më e lexueshme dhe e pasaktë.

Prandaj rregulli R6 e ndalon heqjen e saj, dhe prandaj ky modul ekziston:
pa e njohur pasigurinë në burim, nuk ka si të matet nëse ajo mbijetoi.

Lista e shenjave është e vogël dhe e dukshme. Ajo mbulon katër mënyrat me
të cilat shqipja e shpreh rezervën: foljet modale ("mund të"), ndajfoljet
("ndoshta", "ka gjasa"), foljet e dukjes ("duket", "sugjeron") dhe mohimin
e përjashtimit ("nuk përjashtohet"). Kjo e fundit është njëkohësisht
pseudo-mohim te `negation`, dhe të dy modulet duhet ta trajtojnë njësoj:
pohim, por me rezervë.
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
