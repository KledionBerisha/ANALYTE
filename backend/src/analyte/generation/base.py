"""
Kontrata e gjeneruesit, ashtu si e sheh cikli gjenerim → verifikim.

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
