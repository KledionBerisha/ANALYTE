"""
PK6 — krahasimi i zbuluesve: rregulla, klasifikues, gjykatës LLM.

Të tre zbuluesit vlerësohen mbi të njëjtin grup testues të korpusit të
korruptuar, ku çdo mostër mban saktësisht një defekt ose asnjë. Metrika
është P/R/F1 e përgjithshme dhe sipas llojit të defektit.

Ndarja sipas llojit është thelbi dhe jo hollësi. Pritshmëria e
formuluar përpara matjes është se rregullat do të mbizotërojnë te
defektet numerike — një numër që nuk gjendet në kontekst nuk kërkon
kuptim për t'u kapur — dhe do të humbasin te mohimi dhe pasiguria, ku
kërkohet të kuptohet fjalia. Një F1 i vetëm i përgjithshëm do ta fshihte
plotësisht këtë dhe do ta bënte krahasimin të padobishëm.

Moduli nuk di gjë për korpusin e korruptuar dhe as për modelet: ai merr
çifte etiketash. Kjo e bën të matshëm çdo zbulues, përfshirë atë që ende
nuk ekziston.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, NamedTuple

from analyte.domain.enums import ViolationType

from .base import ConfusionMatrix, macro_f1, micro_average

CLEAN = "clean"
"""Etiketa për mostrën pa defekt. Fals pozitivët mbi të janë çmimi i
verifikimit: tekst i saktë i ndaluar pa nevojë."""


class Judgement(NamedTuple):
    """Një mostër: çfarë ishte vërtet dhe çfarë tha zbuluesi.

    `None` do të thotë "asnjë defekt" në të dyja anët.
    """

    actual: ViolationType | None
    predicted: ViolationType | None


def measure(judgements: Iterable[Judgement]) -> dict[str, Any]:
    matrix = ConfusionMatrix()
    for judgement in judgements:
        matrix.add(_label(judgement.actual), _label(judgement.predicted))

    per_class = matrix.per_class()
    defects = {label: counts for label, counts in per_class.items() if label != CLEAN}

    return {
        "samples": matrix.total,
        "confusion": matrix.to_json(),
        "per_defect_type": {label: counts.to_json() for label, counts in sorted(defects.items())},
        "micro": micro_average(defects).to_json(),
        "macro_f1": macro_f1(defects),
        "false_alarms_on_clean": _false_alarms(matrix),
    }


def _label(violation: ViolationType | None) -> str:
    return CLEAN if violation is None else violation.value


def _false_alarms(matrix: ConfusionMatrix) -> int:
    """Mostra të pastra të shënuara si me defekt.

    Te një sistem që ndal daljen mbi çdo shkelje, ky numër përkthehet
    drejtpërdrejt në shpjegime të sakta që përdoruesi nuk i sheh kurrë.
    """
    per_class = matrix.per_class()
    clean = per_class.get(CLEAN)
    return clean.false_negative if clean else 0
