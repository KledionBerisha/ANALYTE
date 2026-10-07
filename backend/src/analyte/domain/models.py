"""
Modelet e domenit të ANALYTE.

Ky modul nuk importon asgjë nga pjesa tjetër e sistemit. Ai përmban
vetëm përfaqësimin e të dhënave, pa I/O dhe pa logjikë biznesi.
Kjo e mban kontratën e të dhënave të qëndrueshme ndërsa modulet e
tjera ndryshojnë.

Objekti qendror është GroundingContext. Ai është i vetmi input që
shtresa e gjenerimit i jep modelit gjuhësor. Kjo është garancia
arkitekturore e punimit e shprehur si nënshkrim tipi:

    def build_prompt(ctx: GroundingContext) -> str

Modeli nuk ka qasje te dokumenti i papërpunuar, te teksti i nxjerrë
prej tij, apo te ndonjë burim tjetër.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .enums import (
    AnalyteStatus,
    AssertionKind,
    Certainty,
    CrossReferenceState,
    DetectedBy,
    Direction,
    Polarity,
    ReferenceSource,
    ViolationType,
)


class DomainModel(BaseModel):
    """Bazë e përbashkët.

    frozen=True: objektet e domenit janë të pandryshueshme pasi
    krijohen. Një gjetje e nxjerrë nuk duhet të modifikohet nga
    shtresat e mëpasme — çdo transformim prodhon objekt të ri, çka e
    bën gjurmën e auditimit të plotë.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", use_enum_values=False)


class BoundingBox(DomainModel):
    """Pozicioni i një elementi në faqe, në pikë PDF.

    Ruhet që ndërfaqja të mund të theksojë zonën burimore të një vlere.
    Është e lirë për t'u ruajtur tani dhe e shtrenjtë për t'u shtuar më vonë.
    """

    x0: float
    y0: float
    x1: float
    y1: float


class AnalyteFinding(DomainModel):
    """Një vlerë laboratorike e nxjerrë, e normalizuar dhe e klasifikuar.

    Ruhen si vlera e papërpunuar (ashtu si është shtypur) ashtu edhe ajo
    e normalizuar. E para nevojitet për auditim dhe për vlerësimin e
    PK1; e dyta për klasifikim dhe verifikim.
    """

    id: UUID = Field(default_factory=uuid4)

    # Identiteti i analitit
    analyte_code: str = Field(description="Kodi LOINC")
    analyte_name_raw: str = Field(description="Emri ashtu si është shtypur")
    analyte_name_canonical: str

    # Vlera
    value_raw: str = Field(description="Teksti origjinal, p.sh. '0,95'")
    value: Decimal
    unit_raw: str | None = None
    unit_canonical: str
    value_canonical: Decimal = Field(description="Pas konvertimit të njësisë")

    # Intervali referent
    ref_low: Decimal | None = None
    ref_high: Decimal | None = None
    ref_source: ReferenceSource

    # Interpretimi
    status: AnalyteStatus
    severity: Decimal | None = Field(
        default=None,
        description=(
            "Largësia nga kufiri i intervalit pjesëtuar me gjerësinë e "
            "intervalit. None kur statusi është NORMAL ose UNINTERPRETABLE."
        ),
    )

    # Prejardhja
    page: int = Field(ge=1)
    bbox: BoundingBox | None = None
    measured_at: date | None = None
    flag_in_document: str | None = Field(
        default=None, description="Flamuri i shtypur nga laboratori: H, L, *, ↑"
    )

    @model_validator(mode="after")
    def check_reference_consistency(self) -> AnalyteFinding:
        """Konsistenca ndërmjet intervalit, burimit të tij dhe statusit.

        Këto janë kushte që nuk duhet të shkelen kurrë. Nëse shkelen, ka
        gabim në shtresën e nxjerrjes dhe jo në të dhënat — prandaj
        dështojmë herët në vend që të ruajmë gjendje të pamundur.
        """
        has_bounds = self.ref_low is not None or self.ref_high is not None

        if self.ref_source is ReferenceSource.NONE and has_bounds:
            raise ValueError(
                "ref_source=NONE por intervali ekziston; burimi i vërtetë duhet regjistruar"
            )
        if self.ref_source is not ReferenceSource.NONE and not has_bounds:
            raise ValueError(f"ref_source={self.ref_source.value} por intervali mungon")

        # SP5: pa interval nuk ka interpretim
        if not has_bounds and self.status is not AnalyteStatus.UNINTERPRETABLE:
            raise ValueError(
                "vlerë pa interval referent duhet të jetë UNINTERPRETABLE (SP5)"
            )
        if has_bounds and self.status is AnalyteStatus.UNINTERPRETABLE:
            raise ValueError("intervali ekziston; statusi nuk mund të jetë UNINTERPRETABLE")

        if (
            self.ref_low is not None
            and self.ref_high is not None
            and self.ref_low >= self.ref_high
        ):
            raise ValueError("ref_low duhet të jetë më i vogël se ref_high")

        if self.status in {AnalyteStatus.NORMAL, AnalyteStatus.UNINTERPRETABLE}:
            if self.severity is not None:
                raise ValueError("severity duhet të jetë None për këtë status")
        elif self.severity is None:
            raise ValueError(f"severity kërkohet për statusin {self.status.value}")

        return self

    def grounded_numbers(self) -> set[Decimal]:
        """Numrat që teksti i gjeneruar lejohet t'i përmendë për këtë gjetje.

        Rregulli R1 i verifikimit e përdor këtë. Përfshin vlerën dhe të dy
        kufijtë e intervalit — pacienti duhet të mund ta shohë intervalin
        në shpjegim.
        """
        allowed = {self.value, self.value_canonical}
        if self.ref_low is not None:
            allowed.add(self.ref_low)
        if self.ref_high is not None:
            allowed.add(self.ref_high)
        return allowed


class ReportAssertion(DomainModel):
    """Një pohim i nxjerrë nga teksti narrativ i mjekut.

    char_start/char_end lejojnë gjurmimin prapa te teksti origjinal, i
    nevojshëm si për auditim ashtu edhe për anotimin manual gjatë
    vlerësimit të PK4.
    """

    id: UUID = Field(default_factory=uuid4)
    text_span: str
    analyte_code: str | None = Field(
        default=None, description="None kur pohimi nuk lidhet me një analit të matshëm"
    )
    direction: Direction
    polarity: Polarity
    certainty: Certainty
    kind: AssertionKind
    char_start: int = Field(ge=0)
    char_end: int = Field(gt=0)

    @model_validator(mode="after")
    def check_span(self) -> ReportAssertion:
        if self.char_end <= self.char_start:
            raise ValueError("char_end duhet të jetë më i madh se char_start")
        return self


class CrossReference(DomainModel):
    """Rezultati i krahasimit ndërmjet një pohimi dhe një gjetjeje."""

    id: UUID = Field(default_factory=uuid4)
    analyte_code: str
    state: CrossReferenceState
    assertion_id: UUID | None = None
    finding_id: UUID | None = None

    @model_validator(mode="after")
    def check_references(self) -> CrossReference:
        """Secila gjendje kërkon kombinimin e vet të referencave."""
        s = self.state
        if s in {CrossReferenceState.AGREEMENT, CrossReferenceState.CONTRADICTION}:
            if self.assertion_id is None or self.finding_id is None:
                raise ValueError(f"{s.value} kërkon si assertion_id ashtu edhe finding_id")
        elif s is CrossReferenceState.MENTIONED_NOT_MEASURED:
            if self.assertion_id is None or self.finding_id is not None:
                raise ValueError("mentioned_not_measured kërkon vetëm assertion_id")
        elif s is CrossReferenceState.MEASURED_NOT_MENTIONED:
            if self.finding_id is None or self.assertion_id is not None:
                raise ValueError("measured_not_mentioned kërkon vetëm finding_id")
        return self


class GlossaryEntry(DomainModel):
    """Një zë nga tabela terminologjike shqip.

    source_ref është i detyrueshëm: çdo shpjegim duhet të jetë i
    gjurmueshëm te një burim, përndryshe tabela bëhet vetë burim
    informacioni të paverifikuar.
    """

    term: str
    explanation_sq: str
    source_ref: str
    category: str | None = None
    synonyms: tuple[str, ...] = ()


class PatternObservation(DomainModel):
    """Një kombinim rezultatesh që kërkon vlerësim nga profesionisti.

    Nuk mban emër gjendjeje dhe nuk mban shpjegim. Një kombinim i
    hemoglobinës së ulët me ferritinë të ulët ka emër në literaturë, por
    emri është diagnozë (SP1); vëzhgimi thotë vetëm se këto vlera, bashkë,
    meritojnë vëmendjen e mjekut. Kush është kombinimi dhe pse u zgjodh
    regjistrohet te `pattern_id` dhe `source_ref`, për auditim.
    """

    pattern_id: str
    finding_ids: tuple[UUID, ...] = Field(min_length=2)
    source_ref: str


class AdviceEntry(DomainModel):
    """Një këshillë e përgjithshme me burim, e lidhur me një gjetje jashtë intervalit (ADR 0023).

    Nuk është gjenerim dhe nuk është e mjekut: është një fjali e tabelës
    `resources/advice.csv`, e zgjedhur nga analiti dhe drejtimi i gjetjes dhe e
    shtypur fjalë për fjalë. Si fjalori, mban burimin e vet; pa burim të lexuar
    rreshti nuk hyn fare në kontekst. Fjalia nuk thotë çfarë ka pacienti dhe nuk
    jep trajtim: SP1–SP3 e gjykojnë edhe atë, si çdo fjali tjetër të daljes.
    """

    finding_id: UUID
    analyte_code: str
    direction: Direction
    advice_sq: str
    source_ref: str


class GroundingContext(DomainModel):
    """I VETMI input që i jepet modelit gjuhësor.

    Ky objekt është garancia arkitekturore e punimit. Shtresa e
    gjenerimit ka nënshkrimin:

        def build_prompt(ctx: GroundingContext) -> str

    Nuk ka parametër për dokumentin e papërpunuar, për tekstin e
    nxjerrë, apo për ndonjë burim tjetër. Nëse dikush shton një të
    tillë, garancia bie — prandaj ekziston një test i dedikuar që
    kontrollon nënshkrimin.
    """

    document_id: UUID
    findings: tuple[AnalyteFinding, ...] = ()
    assertions: tuple[ReportAssertion, ...] = ()
    cross_refs: tuple[CrossReference, ...] = ()
    glossary: tuple[GlossaryEntry, ...] = ()
    unexplained_terms: tuple[str, ...] = Field(
        default=(),
        description=(
            "Terma të gjetur në dokument por jo në tabelën terminologjike. "
            "SP6: modeli udhëzohet të mos i shpjegojë."
        ),
    )
    patterns: tuple[PatternObservation, ...] = Field(
        default=(),
        description="Kombinimet e rregullave deterministe ndërmjet analiteve.",
    )
    advice: tuple[AdviceEntry, ...] = Field(
        default=(),
        description=(
            "Këshillat me burim të tabelës për gjetjet jashtë intervalit (ADR 0023); "
            "kopjohen fjalë për fjalë dhe R8 i kërkon në dalje."
        ),
    )

    @model_validator(mode="after")
    def check_internal_consistency(self) -> GroundingContext:
        """Referencat brenda kontekstit duhet të zgjidhen.

        Nëse një cross_ref i referohet një gjetjeje që nuk është këtu,
        verifikimi do të dështonte në mënyrë të pashpjegueshme më vonë.
        """
        finding_ids = {f.id for f in self.findings}
        assertion_ids = {a.id for a in self.assertions}

        for ref in self.cross_refs:
            if ref.finding_id is not None and ref.finding_id not in finding_ids:
                raise ValueError(f"cross_ref i referohet gjetjes së panjohur {ref.finding_id}")
            if ref.assertion_id is not None and ref.assertion_id not in assertion_ids:
                raise ValueError(f"cross_ref i referohet pohimit të panjohur {ref.assertion_id}")

        for pattern in self.patterns:
            unknown = set(pattern.finding_ids) - finding_ids
            if unknown:
                raise ValueError(f"modeli {pattern.pattern_id} i referohet gjetjeve të panjohura")

        for entry in self.advice:
            if entry.finding_id not in finding_ids:
                raise ValueError(
                    f"këshilla për {entry.analyte_code} i referohet gjetjes së panjohur {entry.finding_id}"
                )

        explained = {e.term.casefold() for e in self.glossary}
        overlap = explained & {t.casefold() for t in self.unexplained_terms}
        if overlap:
            raise ValueError(f"terma njëkohësisht të shpjeguar dhe të pashpjeguar: {overlap}")

        return self

    # --- Ndihmësa për shtresën e verifikimit ---

    def critical_findings(self) -> tuple[AnalyteFinding, ...]:
        """Gjetjet që duhet detyrimisht të shfaqen në dalje (R4, SP4)."""
        return tuple(f for f in self.findings if f.status.is_critical)

    def all_grounded_numbers(self) -> set[Decimal]:
        """Bashkësia e numrave që teksti i gjeneruar lejohet të përmbajë (R1)."""
        allowed: set[Decimal] = set()
        for f in self.findings:
            allowed |= f.grounded_numbers()
        return allowed

    def known_analyte_codes(self) -> set[str]:
        """Analitet që lejohen të përmenden (R2)."""
        return {f.analyte_code for f in self.findings}

    def status_of(self, analyte_code: str) -> AnalyteStatus | None:
        """Statusi i një analiti, për kontrollin e drejtimit (R3)."""
        for f in self.findings:
            if f.analyte_code == analyte_code:
                return f.status
        return None

    def is_empty(self) -> bool:
        """Konteksti bosh çon në gjendjen NO_FINDINGS, jo në gjenerim."""
        return not self.findings and not self.assertions


class Violation(DomainModel):
    """Një shkelje e vetme e zbuluar nga shtresa e verifikimit."""

    id: UUID = Field(default_factory=uuid4)
    type: ViolationType
    detected_by: DetectedBy
    sentence: str = Field(description="Fjalia e gjeneruar që shkaktoi shkeljen")
    evidence: str = Field(description="Çfarë pritej kundrejt asaj që u gjet")
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="None për rregullat — ato janë deterministe, jo probabilistike",
    )

    @model_validator(mode="after")
    def check_confidence(self) -> Violation:
        if self.detected_by is DetectedBy.RULE and self.confidence is not None:
            raise ValueError("rregullat janë deterministe; confidence duhet të jetë None")
        return self


class VerificationResult(DomainModel):
    """Vendimi i shtresës së verifikimit për një tekst të gjeneruar."""

    id: UUID = Field(default_factory=uuid4)
    explanation_id: UUID
    violations: tuple[Violation, ...] = ()
    rules_version: str
    classifier_version: str | None = None
    duration_ms: int = Field(ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def passed(self) -> bool:
        """NFR1: vetëm teksti pa shkelje i shfaqet përdoruesit."""
        return not self.violations

    def by_detector(self, detector: DetectedBy) -> tuple[Violation, ...]:
        """Ndarja sipas detektorit — të dhënat e drejtpërdrejta për PK6."""
        return tuple(v for v in self.violations if v.detected_by is detector)

    def by_type(self, vtype: ViolationType) -> tuple[Violation, ...]:
        """Ndarja sipas llojit — të dhënat për Tabelën 13."""
        return tuple(v for v in self.violations if v.type is vtype)
