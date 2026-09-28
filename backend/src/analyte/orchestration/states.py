"""
Kalimet e lejuara të makinës së përpunimit (Figura 6).

Tabela e mëposhtme është Figura 6 e shprehur si të dhëna. Kodi që e
drejton dokumentin nuk vendos vetë se ku mund të shkojë: ai kërkon një
kalim, dhe regjistri e refuzon çdo kalim që nuk është në tabelë. Kështu
figura në punim dhe sjellja e sistemit nuk mund të ndahen pa u vënë re —
një test kontrollon që çdo gjendje është e arritshme dhe që gjendjet
përfundimtare nuk kanë dalje.

**Dy kalime që specifikimi nuk i ka.** `GENERATING → GENERATING` dhe
`GENERATING → TEMPLATE_FALLBACK` mbulojnë rastin kur gjeneruesi hedh
përjashtim — një API që nuk përgjigjet, një kufi kërkesash i tejkaluar.
Specifikimi e njeh vetëm dështimin e verifikimit. Përjashtimi trajtohet si
përpjekje e dështuar, sepse alternativa — dokument i ngecur në një
gjendje jopërfundimtare — është pikërisht dështimi i heshtur që
`NO_FINDINGS` u shpik për ta shmangur. Shih ADR 0011.

Çdo kalim regjistrohet. Regjistri është lënda e log-ut të auditimit dhe
e analizës së gabimeve: nga ai lexohet sa dokumente arritën te shablloni
dhe në cilën përpjekje.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime

from analyte.domain.enums import ProcessingState as S

TRANSITIONS: dict[S, frozenset[S]] = {
    S.UPLOADED: frozenset({S.REJECTED, S.INGESTING}),
    S.INGESTING: frozenset({S.TEXT_EXTRACTED, S.OCR_RUNNING}),
    S.OCR_RUNNING: frozenset({S.TEXT_EXTRACTED, S.FAILED_INGESTION}),
    S.TEXT_EXTRACTED: frozenset({S.PARSING}),
    S.PARSING: frozenset({S.NO_FINDINGS, S.GROUNDED}),
    S.GROUNDED: frozenset({S.GENERATING}),
    S.GENERATING: frozenset({S.VERIFYING, S.GENERATING, S.TEMPLATE_FALLBACK}),
    S.VERIFYING: frozenset({S.DELIVERED, S.GENERATING, S.TEMPLATE_FALLBACK}),
    S.TEMPLATE_FALLBACK: frozenset({S.DELIVERED}),
    S.REJECTED: frozenset(),
    S.FAILED_INGESTION: frozenset(),
    S.NO_FINDINGS: frozenset(),
    S.DELIVERED: frozenset(),
}


class IllegalTransition(ValueError):
    """Një kalim që Figura 6 nuk e lejon.

    Ky është gabim programimi dhe jo gjendje e dokumentit, prandaj nuk
    kapet: një orkestrues që tenton kalim të palejuar duhet të ndalet aty
    ku gabimi është ende i dukshëm.
    """


@dataclass(frozen=True, slots=True)
class Transition:
    """Një hap i vetëm i regjistruar."""

    source: S
    target: S
    reason: str
    attempt: int | None = None
    """Numri i përpjekjes së gjenerimit, për kalimet brenda ciklit."""
    at: datetime = field(default_factory=lambda: datetime.now(UTC))


class StateLog:
    """Gjendja e tanishme e një dokumenti dhe rruga që e solli aty.

    `listener` thirret me çdo kalim në çastin që ndodh. Kështu shërbimi e
    shkruan gjendjen në bazë ndërsa dokumenti ende përpunohet — pyetja
    "në ç'gjendje është?" merr përgjigje gjatë OCR-së, jo vetëm pas saj
    (NFR4) — pa e ditur orkestruesi se ekziston një bazë të dhënash.
    """

    def __init__(
        self,
        start: S = S.UPLOADED,
        listener: Callable[[Transition], None] | None = None,
    ) -> None:
        self._state = start
        self._transitions: list[Transition] = []
        self._listener = listener

    @property
    def state(self) -> S:
        return self._state

    @property
    def transitions(self) -> tuple[Transition, ...]:
        return tuple(self._transitions)

    def advance(self, target: S, reason: str = "", *, attempt: int | None = None) -> None:
        if target not in TRANSITIONS[self._state]:
            raise IllegalTransition(f"{self._state.value} → {target.value}")
        transition = Transition(self._state, target, reason, attempt)
        self._transitions.append(transition)
        self._state = target
        if self._listener is not None:
            self._listener(transition)
