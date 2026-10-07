"""
Zbulimi i mohimit, në frymën e NegEx-it.

"""

from __future__ import annotations

from dataclasses import dataclass

from analyte.domain.enums import Polarity
from analyte.textnorm import fold

PSEUDO_NEGATIONS: tuple[str, ...] = (
    "nuk perjashtohet",
    "nuk mund te perjashtohet",
    "nuk eshte e perjashtuar",
    "jo domosdoshmerisht",
    "nuk mund te mohohet",
    "nuk eshte e pamundur",
)
"""Shprehje që përmbajnë shenjë mohuese por nuk mohojnë.

"Nuk përjashtohet X" do të thotë "X është i mundshëm" — pohim me rezervë.
Kjo trajtohet si pasiguri te `hedging`, jo si mohim."""

NEGATION_CUES: tuple[str, ...] = (
    "nuk",
    "s'",
    "asnje",
    "aspak",
    "pa shenja",
    "mungojne",
    "mungon",
    "mungese",
    "perjashtohet",
    "i/e panjohur",
)
"""Shenjat mohuese. Lista mbahet e shkurtër dhe e dukshme: çdo shtesë
duhet të ketë një shembull real pas vetes."""

SCOPE_TERMINATORS: tuple[str, ...] = (
    " por ",
    " ndersa ",
    " ndersa ",
    " ndonese ",
    " megjithate ",
    " ndaj ",
    ";",
)
"""Aty ku mbaron fusha e veprimit e mohimit."""


@dataclass(frozen=True, slots=True)
class NegationResult:
    """Vendimi për një fjali, bashkë me shenjën që e shkaktoi."""

    polarity: Polarity
    cue: str | None
    pseudo: bool = False

    @property
    def negated(self) -> bool:
        return self.polarity is Polarity.NEGATED


AFFIRMED = NegationResult(Polarity.AFFIRMED, None)


def detect(sentence: str) -> NegationResult:
    """Polariteti i një fjalie."""
    folded = fold(sentence)

    for phrase in PSEUDO_NEGATIONS:
        if phrase in folded:
            return NegationResult(Polarity.AFFIRMED, phrase, pseudo=True)

    scope = _scope(folded)
    for cue in NEGATION_CUES:
        if _contains_cue(scope, cue):
            return NegationResult(Polarity.NEGATED, cue)

    return AFFIRMED


def _scope(folded: str) -> str:
    """Pjesa e fjalisë ku mohimi ende vepron."""
    earliest = len(folded)
    for terminator in SCOPE_TERMINATORS:
        position = folded.find(terminator)
        if position != -1:
            earliest = min(earliest, position)
    return folded[:earliest]


def _contains_cue(scope: str, cue: str) -> bool:
    """Shenja kërkohet si fjalë e plotë.

    Pa këtë, "nuk" do të gjendej brenda fjalëve si "anuk..." dhe "pa" do
    të gjendej kudo. Kufijtë e fjalës janë e vetmja mbrojtje.
    """
    if " " in cue:
        return cue in scope
    padded = f" {scope} "
    return f" {cue} " in padded


def polarity_of(sentence: str) -> Polarity:
    return detect(sentence).polarity
