"""
Bazat e përbashkëta të metrikave.

Të gjitha metrikat e punimit kthehen në të njëjtat tri madhësi ose në një
matricë ngatërrimi. Përkufizimi i tyre qëndron këtu, në një vend, që një
numër i raportuar në Kapitullin 6 të ketë kuptimin e njëjtë kudo ku
shfaqet.

Rasti kufitar i emëruesit zero trajtohet me qëllim: kur nuk ka asgjë për
t'u matur kthehet `None` dhe jo zero. Zeroja është pohim — "e matëm dhe
doli zero" — ndërsa `None` thotë "nuk kishte çfarë të matej". Tabela e
rezultateve i shtyp ndryshe, sepse ato janë gjëra të ndryshme.
"""

from __future__ import annotations

import re
from typing import Any, NamedTuple


class PRF(NamedTuple):
    """Saktësia, mbulimi dhe F1, bashkë me numëruesit prej të cilëve dolën.

    Numëruesit mbahen sepse pa ta një F1 i raportuar nuk mund të
    rillogaritet dhe as të bashkohet me një tjetër.
    """

    true_positive: int
    false_positive: int
    false_negative: int

    @property
    def precision(self) -> float | None:
        predicted = self.true_positive + self.false_positive
        return self.true_positive / predicted if predicted else None

    @property
    def recall(self) -> float | None:
        actual = self.true_positive + self.false_negative
        return self.true_positive / actual if actual else None

    @property
    def f1(self) -> float | None:
        precision, recall = self.precision, self.recall
        if precision is None or recall is None or precision + recall == 0:
            return None
        return 2 * precision * recall / (precision + recall)

    @property
    def support(self) -> int:
        """Sa raste të vërteta kishte. Pesha e kësaj klase në mesatare."""
        return self.true_positive + self.false_negative

    def __add__(self, other: "PRF") -> "PRF":
        return PRF(
            self.true_positive + other.true_positive,
            self.false_positive + other.false_positive,
            self.false_negative + other.false_negative,
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "tp": self.true_positive,
            "fp": self.false_positive,
            "fn": self.false_negative,
            "precision": _round(self.precision),
            "recall": _round(self.recall),
            "f1": _round(self.f1),
            "support": self.support,
        }


EMPTY = PRF(0, 0, 0)


def micro_average(parts: dict[str, PRF]) -> PRF:
    """Bashkimi i numëruesve përpara pjesëtimit.

    Mikro-mesatarja u jep peshë rasteve dhe jo klasave. Për nxjerrjen kjo
    është ajo që duhet: një fushë e shtypur rrallë nuk duhet të peshojë
    sa një e shtypur në çdo rresht.
    """
    total = EMPTY
    for value in parts.values():
        total = total + value
    return total


def macro_f1(parts: dict[str, PRF]) -> float | None:
    """Mesatarja e F1-ve të klasave, pa peshë.

    Raportohet krahas mikro-mesatares sepse klasat e rralla — defektet e
    rralla te PK6 — zhduken plotësisht nën mikro-mesataren.
    """
    scores = [part.f1 for part in parts.values() if part.f1 is not None]
    return sum(scores) / len(scores) if scores else None


class ConfusionMatrix:
    """Numërim i çifteve (e vërteta, e parashikuara).

    Mbahet si fjalor e jo si tabelë me rend të fiksuar, sepse etiketat e
    mundshme ndryshojnë sipas metrikës; rendi vendoset vetëm kur shtypet.
    """

    def __init__(self) -> None:
        self._counts: dict[tuple[str, str], int] = {}

    def add(self, actual: str, predicted: str) -> None:
        key = (actual, predicted)
        self._counts[key] = self._counts.get(key, 0) + 1

    @property
    def total(self) -> int:
        return sum(self._counts.values())

    @property
    def correct(self) -> int:
        return sum(count for (actual, predicted), count in self._counts.items()
                   if actual == predicted)

    @property
    def accuracy(self) -> float | None:
        return self.correct / self.total if self.total else None

    def labels(self) -> list[str]:
        seen = {label for pair in self._counts for label in pair}
        return sorted(seen)

    def per_class(self) -> dict[str, PRF]:
        """P/R/F1 për secilën klasë, e nxjerrë nga e njëjta matricë."""
        out: dict[str, PRF] = {}
        for label in self.labels():
            tp = self._counts.get((label, label), 0)
            fp = sum(c for (a, p), c in self._counts.items() if p == label and a != label)
            fn = sum(c for (a, p), c in self._counts.items() if a == label and p != label)
            out[label] = PRF(tp, fp, fn)
        return out

    def to_json(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "accuracy": _round(self.accuracy),
            "matrix": {
                f"{actual}->{predicted}": count
                for (actual, predicted), count in sorted(self._counts.items())
            },
            "per_class": {label: prf.to_json() for label, prf in self.per_class().items()},
        }


_SENTENCE_END = re.compile(r"[.!?](?:\s|$)")


def count_sentences(text: str) -> int:
    """Sa fjali ka një tekst.

    PK5 raportohet për 100 fjali, prandaj emëruesi duhet të jetë i
    përkufizuar dhe jo i nënkuptuar. Numërimi është i thjeshtë me qëllim:
    teksti i gjeneruar është prozë e shkurtër shpjeguese pa shkurtime me
    pikë, dhe një numërues më i zgjuar do të fshihte se nga vjen numri.
    """
    stripped = text.strip()
    if not stripped:
        return 0
    return max(1, len(_SENTENCE_END.findall(stripped)))


def _round(value: float | None, digits: int = 4) -> float | None:
    return None if value is None else round(value, digits)


BOOTSTRAP_RESAMPLES = 2000
BOOTSTRAP_SEED = 20260928
BOOTSTRAP_LEVEL = 0.95


def bootstrap_ratio(
    units: list[tuple[float, float]],
    *,
    scale: float = 1.0,
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
    level: float = BOOTSTRAP_LEVEL,
) -> dict[str, Any] | None:
    """Intervali i besimit për një raport Σnumërues / Σemërues (§7 e specifikimit).

    Njësia e rimostrimit është dokumenti, jo fjalia: fjalitë e një
    dokumenti ndajnë kontekstin dhe gabimet e tyre nuk janë të pavarura.
    Rimostrimi sipas fjalisë do ta ngushtonte intervalin pa të drejtë.

    **Zero ngjarje.** Kur numëruesi është zero kudo, çdo rimostrim jep zero
    dhe intervali përqindor del [0, 0] — sikur pasiguria të mos ekzistonte.
    Prandaj raportohet edhe kufiri i sipërm sipas "rregullit të treshit"
    (3/n për 95%), që tabela ta shtypë në vend të zeros së rreme. Rasti i
    kundërt — çdo njësi sukses, si ruajtja e plotë e mohimeve — merr kufirin
    e poshtëm 1 − 3/n.

    Fara është e fiksuar: i njëjti rezultat jep gjithmonë të njëjtin
    interval, dhe numri në Kapitullin 6 mund të rillogaritet.
    """
    import random

    units = [(float(n), float(d)) for n, d in units if d > 0]
    denominator = sum(d for _, d in units)
    if not units or denominator == 0:
        return None

    numerator = sum(n for n, _ in units)
    rng = random.Random(seed)
    size = len(units)
    estimates = []
    for _ in range(resamples):
        sample = [units[rng.randrange(size)] for _ in range(size)]
        total = sum(d for _, d in sample)
        estimates.append(scale * sum(n for n, _ in sample) / total)
    estimates.sort()

    tail = (1.0 - level) / 2.0
    low = estimates[int(tail * (resamples - 1))]
    high = estimates[int((1.0 - tail) * (resamples - 1))]
    result: dict[str, Any] = {
        "estimate": _round(scale * numerator / denominator),
        "low": _round(low),
        "high": _round(high),
        "level": level,
        "resamples": resamples,
        "unit": "document",
        "units": size,
    }
    if numerator == 0:
        result["rule_of_three_high"] = _round(scale * 3.0 / denominator)
    elif numerator == denominator:
        # E njëjta pasqyrë për ruajtjen e plotë: asnjë humbje nuk do të thotë
        # se humbja nuk ndodh kurrë, vetëm se nuk u pa në këtë mostër.
        result["rule_of_three_low"] = _round(scale * max(0.0, 1.0 - 3.0 / denominator))
    return result
