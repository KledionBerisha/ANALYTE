"""
Kontrata e gjeneruesit, ashtu si e sheh cikli gjenerim → verifikim.

Gjeneruesi merr kontekstin dhe shkeljet e përpjekjes së mëparshme, dhe
kthen tekst. Asgjë tjetër. Nuk ka parametër për dokumentin, për tekstin e
nxjerrë prej tij, as për narrativën e mjekut — e njëjta garanci që
`GroundingContext` shpreh për `build_prompt`, e zgjeruar te çdo
zbatim i gjeneruesit.

Shkeljet nuk e dobësojnë këtë garanci. Çdo `Violation` mban një fjali të
daljes së gjeneruar dhe arsyen e rregullit; asnjëra nuk vjen nga
dokumenti. Modeli sheh vetëm atë që ka shkruar vetë dhe pse u refuzua.

Protokolli ekziston përpara modelit gjuhësor me qëllim: makina e
gjendjeve testohet me gjenerues të rremë që japin tekst të saktë, tekst
me defekte të dhëna dhe përjashtime, dhe secila rrugë e Figurës 6 ka
testin e vet pa asnjë thirrje në rrjet.
"""

from __future__ import annotations

from typing import Protocol

from analyte.domain.models import GroundingContext, Violation


class Generator(Protocol):
    """Çdo gjë që shndërron kontekstin në shpjegim për pacientin."""

    name: str
    """Identifikuesi që ruhet me çdo përpjekje, p.sh. modeli dhe versioni i
    prompt-it. Pa të, një rezultat nuk mund t'i atribuohet konfigurimit
    që e prodhoi."""

    def __call__(self, context: GroundingContext, feedback: tuple[Violation, ...]) -> str:
        """Kthen shpjegimin.

        `feedback` është bosh në përpjekjen e parë. Në të dytën mban
        shkeljet e së parës, të plota: verifikimi nuk ndalet te e para
        pikërisht që kjo listë të mos jetë e cunguar.
        """
        ...
