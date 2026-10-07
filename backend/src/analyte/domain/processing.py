"""
Llojet e rezultatit të përpunimit që duhen njëkohësisht nga orkestrimi, nga regjistri i
auditimit dhe nga persistenca.

"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

from .enums import ProcessingState as S
from .models import VerificationResult, Violation

__all__ = ["Attempt", "Delivery", "Explanation", "Transition"]


@dataclass(frozen=True, slots=True)
class Transition:
    """Një hap i vetëm i regjistruar."""

    source: S
    target: S
    reason: str
    attempt: int | None = None
    """Numri i përpjekjes së gjenerimit, për kalimet brenda ciklit."""
    at: datetime = field(default_factory=lambda: datetime.now(UTC))


class Delivery(str, Enum):
    """Nga erdhi teksti që pa pacienti."""

    GENERATED = "generated"
    TEMPLATE = "template"


@dataclass(frozen=True, slots=True)
class Attempt:
    """Një përpjekje gjenerimi dhe vendimi mbi të.

    Një përpjekje që dështoi me përjashtim nuk ka as tekst as verifikim,
    por ka gabimin — dhe numërohet si përpjekje e plotë.
    """

    number: int
    generator: str
    text: str | None
    verification: VerificationResult | None
    error: str | None = None

    @property
    def passed(self) -> bool:
        return self.verification is not None and self.verification.passed

    @property
    def violations(self) -> tuple[Violation, ...]:
        return self.verification.violations if self.verification else ()

    def failure(self) -> str:
        """Pse përpjekja nuk u dorëzua, në një rresht për regjistrin."""
        if self.error is not None:
            return f"gjeneruesi dështoi: {self.error}"
        kinds = sorted({v.type.value for v in self.violations})
        return f"{len(self.violations)} shkelje: {', '.join(kinds)}"


@dataclass(frozen=True, slots=True)
class Explanation:
    """Teksti i dorëzuar bashkë me rrugën që e prodhoi."""

    text: str
    delivery: Delivery
    attempts: tuple[Attempt, ...]
    verification: VerificationResult
    """Verifikimi i tekstit të dorëzuar — i përpjekjes që kaloi, ose i
    shabllonit."""
