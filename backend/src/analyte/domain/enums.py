"""
Mbyllja e fjalorëve të domenit.

Këto enum-e janë kontrata ndërmjet moduleve. Shtimi i një vlere këtu
ndikon në shtresën e verifikimit, në bazën e të dhënave dhe në
metrikat e vlerësimit, prandaj çdo ndryshim duhet të jetë i
qëllimshëm.

Vlerat janë në anglisht sepse ato ruhen në bazën e të dhënave dhe
përdoren në kod; teksti për përdoruesin përkthehet në shtresën e
prezantimit.
"""

from enum import Enum


class AnalyteStatus(str, Enum):
    """Klasifikimi i një vlere kundrejt intervalit referent.

    UNINTERPRETABLE nuk është gabim: ai shënon rastin kur nuk u gjet
    asnjë interval referent. Politika e sigurisë SP5 kërkon që sistemi
    të refuzojë interpretimin në këtë rast në vend që të hamendësojë.
    """

    CRITICAL_LOW = "critical_low"
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL_HIGH = "critical_high"
    UNINTERPRETABLE = "uninterpretable"

    @property
    def is_abnormal(self) -> bool:
        return self in {
            AnalyteStatus.CRITICAL_LOW,
            AnalyteStatus.LOW,
            AnalyteStatus.HIGH,
            AnalyteStatus.CRITICAL_HIGH,
        }

    @property
    def is_critical(self) -> bool:
        return self in {AnalyteStatus.CRITICAL_LOW, AnalyteStatus.CRITICAL_HIGH}

    @property
    def direction(self) -> "Direction":
        """Drejtimi që nënkupton ky status.

        Përdoret nga rregulli R3 i verifikimit për të kontrolluar nëse
        një pohim drejtimi në tekstin e gjeneruar përputhet me statusin.
        """
        if self in {AnalyteStatus.CRITICAL_LOW, AnalyteStatus.LOW}:
            return Direction.DECREASED
        if self in {AnalyteStatus.CRITICAL_HIGH, AnalyteStatus.HIGH}:
            return Direction.INCREASED
        if self is AnalyteStatus.NORMAL:
            return Direction.NORMAL
        return Direction.UNSPECIFIED


class ReferenceSource(str, Enum):
    """Nga erdhi intervali referent i përdorur për klasifikim.

    Raportohet në rezultatet e PK2: përpjesa e vlerave të klasifikuara
    me interval nga dokumenti kundrejt tabelës së brendshme është
    tregues i cilësisë së nxjerrjes.
    """

    DOCUMENT = "document"
    INTERNAL_TABLE = "internal_table"
    NONE = "none"


class Direction(str, Enum):
    """Drejtimi i shprehur për një analit, në gjetje ose në pohim."""

    INCREASED = "increased"
    DECREASED = "decreased"
    NORMAL = "normal"
    UNSPECIFIED = "unspecified"


class Polarity(str, Enum):
    """Pohim ose mohim. NegEx-i vendos këtë fushë."""

    AFFIRMED = "affirmed"
    NEGATED = "negated"


class Certainty(str, Enum):
    """Niveli i sigurisë i shprehur nga mjeku.

    HEDGED mbulon "e mundshme", "sugjeruese për", "nuk përjashtohet".
    Heqja e këtij niveli në thjeshtim është shkelje (rregulli R6).
    """

    CONFIRMED = "confirmed"
    HEDGED = "hedged"


class AssertionKind(str, Enum):
    """Çfarë lloj pohimi është nxjerrë nga narrativa."""

    FINDING = "finding"
    RECOMMENDATION = "recommendation"
    TERM_MENTION = "term_mention"


class CrossReferenceState(str, Enum):
    """Rezultati i krahasimit raport ↔ laborator.

    MEASURED_NOT_MENTIONED zbulon mungesa dhe jo gabime; është kategoria
    më e vështirë për t'u vërejtur nga një lexues njerëzor.
    """

    AGREEMENT = "agreement"
    CONTRADICTION = "contradiction"
    MENTIONED_NOT_MEASURED = "mentioned_not_measured"
    MEASURED_NOT_MENTIONED = "measured_not_mentioned"


class ViolationType(str, Enum):
    """Llojet e shkeljeve që shtresa e verifikimit mund të zbulojë.

    Renditja pasqyron katalogun e rregullave R1-R9 të Kapitullit 5.
    Këto janë gjithashtu klasat e defekteve në korpusin e korruptuar,
    prandaj Tabela 13 (performanca sipas llojit) indeksohet me to.
    """

    # Dega A — verifikim i saktë
    UNGROUNDED_NUMBER = "ungrounded_number"          # R1
    UNGROUNDED_ANALYTE = "ungrounded_analyte"        # R2
    DIRECTION_MISMATCH = "direction_mismatch"        # R3
    MISSING_CRITICAL = "missing_critical"            # R4
    # Dega B — verifikim semantik
    POLARITY_FLIP = "polarity_flip"                  # R5
    HEDGE_REMOVED = "hedge_removed"                  # R6
    FABRICATED_FINDING = "fabricated_finding"        # R7
    OMITTED_RECOMMENDATION = "omitted_recommendation"  # R8
    UNGROUNDED_TERM_EXPLANATION = "ungrounded_term_explanation"  # R9
    # Politika e sigurisë
    PROHIBITED_CLAIM = "prohibited_claim"            # SP1-SP3

    @property
    def branch(self) -> str:
        exact = {
            ViolationType.UNGROUNDED_NUMBER,
            ViolationType.UNGROUNDED_ANALYTE,
            ViolationType.DIRECTION_MISMATCH,
            ViolationType.MISSING_CRITICAL,
        }
        return "A" if self in exact else "B"


class DetectedBy(str, Enum):
    """Cili mekanizëm e zbuloi shkeljen.

    Kjo fushë është burimi i drejtpërdrejtë i të dhënave për PK6.
    Pa të, krahasimi rregulla vs. klasifikues kërkon riekzekutim të
    të gjitha eksperimenteve.
    """

    RULE = "rule"
    CLASSIFIER = "classifier"
    LLM_JUDGE = "llm_judge"


class ProcessingState(str, Enum):
    """Gjendjet e makinës së përpunimit (Figura 6).

    NO_FINDINGS është gjendje e veçantë: dokumenti u përpunua me sukses
    por nuk dha asnjë gjetje. Pa të, një dokument i palexueshëm do të
    prodhonte dalje bosh pa shpjegim — dështim i heshtur.
    """

    UPLOADED = "uploaded"
    REJECTED = "rejected"
    INGESTING = "ingesting"
    OCR_RUNNING = "ocr_running"
    TEXT_EXTRACTED = "text_extracted"
    FAILED_INGESTION = "failed_ingestion"
    PARSING = "parsing"
    NO_FINDINGS = "no_findings"
    GROUNDED = "grounded"
    GENERATING = "generating"
    VERIFYING = "verifying"
    TEMPLATE_FALLBACK = "template_fallback"
    DELIVERED = "delivered"

    @property
    def is_terminal(self) -> bool:
        return self in {
            ProcessingState.REJECTED,
            ProcessingState.FAILED_INGESTION,
            ProcessingState.NO_FINDINGS,
            ProcessingState.DELIVERED,
        }
