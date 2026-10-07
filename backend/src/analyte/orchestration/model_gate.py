"""
Kush dokument shkon te ofruesi i modelit, dhe kush jo (ADR 0019).

"""

from __future__ import annotations

from analyte.domain.models import GroundingContext
from analyte.generation import deidentify
from analyte.generation.base import Generator
from analyte.generation.templates import TemplateGenerator

from .process import Chooser, GeneratorChoice

USED = "used"
NO_CONSENT = "no_consent"
IDENTIFYING = "identifying_content"


def sends_data_off_system(generator: Generator) -> bool:
    return bool(getattr(generator, "sends_data_off_system", False))


def chooser(generator: Generator, consent: bool) -> Chooser | None:
    """Zgjedhësi për një dokument, ose None kur gjeneruesi nuk e dërgon kontekstin jashtë sistemit."""
    if not sends_data_off_system(generator):
        return None

    def choose(context: GroundingContext) -> GeneratorChoice:
        if not consent:
            return GeneratorChoice(TemplateGenerator(), NO_CONSENT)
        verdict = deidentify.inspect(context)
        if not verdict.clean:
            return GeneratorChoice(TemplateGenerator(), IDENTIFYING, verdict.kinds)
        return GeneratorChoice(generator, USED)

    return choose
