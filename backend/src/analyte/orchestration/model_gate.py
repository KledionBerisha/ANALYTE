"""
Kush dokument shkon te ofruesi i modelit, dhe kush jo (ADR 0019).

Modeli është një gjenerues që e dërgon kontekstin jashtë sistemit (`sends_data_off_system`). Për çdo dokument,
pasi konteksti ekziston, vendosen dy gjëra me radhë, dhe shablloni determinist del në çdo rast që dështon njëra:

  1. **Pëlqimi.** Pacienti duhet ta ketë dhënë për këtë ngarkim (`documents.model_consent`). Pa të, nuk ndërtohet
     asnjë kërkesë dhe nuk bëhet asnjë thirrje në rrjet.
  2. **Porta e çidentifikimit** (`generation.deidentify`). Nëse ndonjë varg i dokumentit që do të hynte te kërkesa
     duket se mban të dhëna personale, ose ndonjë vlerë e strukturuar nuk është e katalogut, dokumenti nuk dërgohet.

Pëlqimi nuk e anashkalon portën: ai është leje për të dërguar atë që porta lejon, jo për të dërguar një emër.

Gjeneruesit që nuk e shënojnë veten si dërgues (shablloni, gjeneruesit e rremë të testeve) kalojnë pa vendim: këtu
nuk ka asgjë që del nga sistemi, dhe `model_use` mbetet bosh.
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
