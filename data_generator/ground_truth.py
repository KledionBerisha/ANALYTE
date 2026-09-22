"""
Ndërtimi i një dokumenti sintetik dhe i së vërtetës bazë të tij.

Rezultati ka dy pjesë që duhen mbajtur të ndara:

  - `rows` dhe `narrative_text`: çfarë shtypet në PDF. Kjo është e vetmja
    gjë që sistemi do të shohë.
  - `context`: çfarë duhet të nxirrte një sistem i përsosur. Kjo nuk i
    jepet kurrë sistemit; ajo krahasohet me atë që sistemi prodhoi.

Renditja e veprimeve ka rëndësi. Statusi i synuar zgjidhet i pari, pastaj
vlera, pastaj mënyra e shtypjes (njësia, intervali, presja dhjetore), dhe
vetëm në fund rillogaritet statusi i vërtetë mbi vlerën dhe intervalin
ashtu si dalin të shtypura. Nëse do ta ruanim statusin e synuar, një
dokument që shtyp interval paksa të ndryshëm nga tabela jonë do të mbante
etiketë të rreme.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, replace
from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from analyte.domain.enums import (
    AnalyteStatus,
    CrossReferenceState,
    Direction,
    Polarity,
    ReferenceSource,
)
from analyte.domain.models import (
    AnalyteFinding,
    BoundingBox,
    CrossReference,
    GlossaryEntry,
    GroundingContext,
    ReportAssertion,
)
from analyte.grounding.branch_a.classify import classify

from .catalog import (
    Analyte,
    Sex,
    analytes_by_code,
    conversion_for,
    load_analytes,
    terms_by_name,
)
from .distributions import sample_status, sample_unreferenced_value, sample_value
from .ids import IdFactory
from .narrative import Name, build_narrative
from .panels import PANEL_TITLES, compose_order

LINES_PER_PAGE = 32
"""Sa rreshta teksti nxë trupi i një faqeje, titujt e paneleve të përfshirë.

Paginimi vendoset këtu dhe jo te vizatuesi: numri i faqes është pjesë e
së vërtetës bazë dhe duhet të jetë i njohur para se dokumenti të
vizatohet. Vizatuesi numëron rreshtat njësoj — `render.py` e kontrollon
këtë me përputhje të drejtpërdrejtë, prandaj një ndryshim i heshtur i
njërës anë dështon menjëherë."""

SCANNED_SHARE = 0.35
"""Përpjesa e dokumenteve që kalojnë nëpër simulimin e skanimit. PK1 dhe
PK2 raportohen veçmas për dokumente dixhitale dhe të skanuara, prandaj të
dyja duhet të jenë të pranishme në sasi të matshme."""

LAB_NAMES: tuple[str, ...] = (
    "Laboratori Klinik Qendror",
    "Poliklinika Diagnostike Alba",
    "Laboratori Biomjekësor Vita",
    "Qendra Laboratorike Medika",
)

FIRST_NAMES: dict[Sex, tuple[str, ...]] = {
    Sex.MALE: ("Arben", "Besnik", "Dritan", "Endrit", "Gentian", "Ilir", "Lorenc", "Valon"),
    Sex.FEMALE: ("Albana", "Blerta", "Diana", "Elona", "Fatmira", "Jehona", "Mirela", "Vjosa"),
}
"""Emri ndjek gjininë e kampionuar. Kjo nuk është hollësi kozmetike:
gjinia përcakton intervalin referent, dhe një dokument ku emri thotë një
gjë e fusha tjetër do të ishte pikërisht lloji i mospërputhjes që nxjerrja
duhet ta shohë vetëm kur ne e fusim me qëllim."""

LAST_NAMES: tuple[str, ...] = (
    "Hoxha", "Krasniqi", "Berisha", "Gashi", "Shala", "Bytyqi", "Dervishi",
    "Kelmendi", "Rexhepi", "Zeneli", "Morina", "Selimi",
)

EARLIEST = date(2024, 1, 1)
LATEST = date(2026, 6, 30)


@dataclass(frozen=True, slots=True)
class LabStyle:
    """Zgjedhjet e shtypjes që dallojnë një laborator nga tjetri.

    Këto janë pikërisht ndryshimet që e bëjnë nxjerrjen të vështirë:
    presje apo pikë dhjetore, interval i shtypur apo jo, flamur H/L apo
    shigjetë, njësi tradicionale apo SI.
    """

    lab_name: str
    layout: str
    decimal_comma: bool
    interval_policy: str  # "all" | "some" | "none"
    flag_style: str | None  # "HL" | "arrow" | "star" | None
    uses_alt_units: bool


@dataclass(frozen=True, slots=True)
class PrintedRow:
    """Një rresht ashtu si shfaqet në dokument.

    Vizatuesi i PDF-së merr vetëm këtë. Nëse diçka nuk është këtu, ajo
    nuk shtypet — dhe sistemi nuk ka si ta dijë.
    """

    finding_id: UUID
    panel: str
    panel_title: str
    name_printed: str
    value_printed: str
    unit_printed: str
    interval_printed: str | None
    flag_printed: str | None
    page: int


@dataclass(frozen=True, slots=True)
class DocumentTruth:
    """Dokumenti sintetik: çfarë shtypet dhe çfarë duhet nxjerrë prej tij."""

    document_id: UUID
    lab: LabStyle
    patient_name: str
    patient_sex: Sex
    patient_age: int
    measured_at: date
    rows: tuple[PrintedRow, ...]
    narrative_text: str
    page_count: int
    is_scanned: bool
    context: GroundingContext

    def with_boxes(self, boxes: dict[UUID, "BoundingBox"]) -> "DocumentTruth":
        """Kthen të njëjtin dokument me kutitë kufizuese të plotësuara.

        Pozicionet dihen vetëm pasi faqja të jetë vizatuar, ndërsa gjetjet
        janë të pandryshueshme. Prandaj vizatuesi nuk i modifikon ato por
        kthen koordinatat, dhe këtu ndërtohet një kontekst i ri — gjurma e
        auditimit mbetet e plotë dhe asnjë gjetje nuk ndryshon nën këmbët e
        askujt.
        """
        findings = tuple(
            f.model_copy(update={"bbox": boxes[f.id]}) if f.id in boxes else f
            for f in self.context.findings
        )
        context = self.context.model_copy(update={"findings": findings})
        return replace(self, context=context)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "document_id": str(self.document_id),
            "lab": {
                "lab_name": self.lab.lab_name,
                "layout": self.lab.layout,
                "decimal_comma": self.lab.decimal_comma,
                "interval_policy": self.lab.interval_policy,
                "flag_style": self.lab.flag_style,
                "uses_alt_units": self.lab.uses_alt_units,
            },
            "patient": {
                "name": self.patient_name,
                "sex": self.patient_sex.value,
                "age": self.patient_age,
            },
            "measured_at": self.measured_at.isoformat(),
            "page_count": self.page_count,
            "is_scanned": self.is_scanned,
            "rows": [
                {
                    "finding_id": str(r.finding_id),
                    "panel": r.panel,
                    "panel_title": r.panel_title,
                    "name_printed": r.name_printed,
                    "value_printed": r.value_printed,
                    "unit_printed": r.unit_printed,
                    "interval_printed": r.interval_printed,
                    "flag_printed": r.flag_printed,
                    "page": r.page,
                }
                for r in self.rows
            ],
            "narrative_text": self.narrative_text,
            "context": self.context.model_dump(mode="json"),
        }


def sample_lab_style(rng: random.Random) -> LabStyle:
    return LabStyle(
        lab_name=rng.choice(LAB_NAMES),
        layout=rng.choice(("tabelor", "kompakt", "dykolonësh")),
        decimal_comma=rng.random() < 0.7,
        interval_policy=rng.choices(("all", "some", "none"), weights=(0.6, 0.3, 0.1), k=1)[0],
        flag_style=rng.choices(
            ("HL", "arrow", "star", None), weights=(0.45, 0.2, 0.1, 0.25), k=1
        )[0],
        uses_alt_units=rng.random() < 0.35,
    )


def build_document(
    rng: random.Random, new_id: IdFactory, *, scanned_share: float = SCANNED_SHARE
) -> DocumentTruth:
    """Prodhon një dokument të plotë me të vërtetën bazë të tij."""
    lab = sample_lab_style(rng)
    sex = rng.choice((Sex.MALE, Sex.FEMALE))
    first = rng.choice(FIRST_NAMES[sex])
    patient_name = f"{first} {rng.choice(LAST_NAMES)}"
    age = rng.randint(18, 85)
    measured_at = EARLIEST + timedelta(days=rng.randint(0, (LATEST - EARLIEST).days))
    document_id = new_id()

    is_scanned = rng.random() < scanned_share
    groups = compose_order(rng)
    findings: list[AnalyteFinding] = []
    rows: list[PrintedRow] = []
    line = 0

    for panel, analytes in groups:
        line += 1  # titulli i panelit zë një rresht si çdo tjetër
        for analyte in analytes:
            finding, row = _build_row(
                rng, new_id, analyte, sex, lab, measured_at, panel, page_for_line(line)
            )
            findings.append(finding)
            rows.append(row)
            line += 1

    page_count = max(1, page_for_line(max(line - 1, 0)))

    measured_codes = {f.analyte_code for f in findings}
    display_names = {
        code: Name(a.narrative_name, a.narrative_plural)
        for code, a in analytes_by_code().items()
    }
    unmeasured = tuple(
        (a.loinc_code, Name(a.narrative_name, a.narrative_plural))
        for a in load_analytes()
        if a.loinc_code not in measured_codes
    )

    narrative = build_narrative(
        rng, tuple(findings), display_names, unmeasured, new_id
    )

    context = GroundingContext(
        document_id=document_id,
        findings=tuple(findings),
        assertions=narrative.assertions,
        cross_refs=build_cross_references(tuple(findings), narrative.assertions, new_id),
        glossary=_glossary_for(narrative.explained_terms),
        unexplained_terms=narrative.unexplained_terms,
    )

    return DocumentTruth(
        document_id=document_id,
        lab=lab,
        patient_name=patient_name,
        patient_sex=sex,
        patient_age=age,
        measured_at=measured_at,
        rows=tuple(rows),
        narrative_text=narrative.text,
        page_count=page_count,
        is_scanned=is_scanned,
        context=context,
    )


def page_for_line(line: int) -> int:
    """Faqja në të cilën bie rreshti i dhënë, duke numëruar nga zero."""
    return line // LINES_PER_PAGE + 1


def _build_row(
    rng: random.Random,
    new_id: IdFactory,
    analyte: Analyte,
    sex: Sex,
    lab: LabStyle,
    measured_at: date,
    panel: str,
    page: int,
) -> tuple[AnalyteFinding, PrintedRow]:
    name_printed = rng.choice(analyte.variants)

    if not analyte.has_reference:
        return _build_unreferenced_row(
            rng, new_id, analyte, lab, measured_at, panel, page, name_printed
        )

    target = sample_status(rng, analyte, sex)
    canonical = sample_value(rng, analyte, sex, target)

    ref_low, ref_high = analyte.reference_for(sex)
    assert ref_low is not None and ref_high is not None
    ref_low, ref_high = _maybe_perturb(rng, analyte, ref_low, ref_high)

    conversion = conversion_for(analyte) if lab.uses_alt_units else None
    if conversion is not None and rng.random() < 0.5:
        printed_value = _quantize(conversion.from_canonical(canonical), conversion.decimals)
        unit_printed = analyte.alt_unit or analyte.unit
        value_canonical = analyte.quantize(conversion.to_canonical(printed_value))
        printed_low = _quantize(conversion.from_canonical(ref_low), conversion.decimals)
        printed_high = _quantize(conversion.from_canonical(ref_high), conversion.decimals)
        ref_low = analyte.quantize(conversion.to_canonical(printed_low))
        ref_high = analyte.quantize(conversion.to_canonical(printed_high))
        decimals_printed = conversion.decimals
    else:
        printed_value = canonical
        unit_printed = analyte.unit
        value_canonical = canonical
        printed_low, printed_high = ref_low, ref_high
        decimals_printed = analyte.decimals

    prints_interval = _prints_interval(rng, lab)
    if prints_interval:
        ref_source = ReferenceSource.DOCUMENT
        interval_printed = _format_interval(
            printed_low, printed_high, decimals_printed, lab.decimal_comma
        )
    else:
        # Intervali nuk u shtyp: sistemi do ta gjejë te tabela e brendshme,
        # prandaj e vërteta bazë mban intervalin e asaj tabele.
        ref_source = ReferenceSource.INTERNAL_TABLE
        interval_printed = None
        ref_low, ref_high = analyte.reference_for(sex)
        assert ref_low is not None and ref_high is not None

    status, severity = classify(
        value_canonical, ref_low, ref_high, analyte.critical_low, analyte.critical_high
    )

    finding = AnalyteFinding(
        id=new_id(),
        analyte_code=analyte.loinc_code,
        analyte_name_raw=name_printed,
        analyte_name_canonical=analyte.name_canonical_sq,
        value_raw=_format_number(printed_value, decimals_printed, lab.decimal_comma),
        value=printed_value,
        unit_raw=unit_printed,
        unit_canonical=analyte.unit,
        value_canonical=value_canonical,
        ref_low=ref_low,
        ref_high=ref_high,
        ref_source=ref_source,
        status=status,
        severity=severity,
        page=page,
        bbox=None,  # plotësohet nga vizatuesi i PDF-së
        measured_at=measured_at,
        flag_in_document=_flag_for(status, lab.flag_style),
    )

    row = PrintedRow(
        finding_id=finding.id,
        panel=panel,
        panel_title=PANEL_TITLES.get(panel, panel.upper()),
        name_printed=name_printed,
        value_printed=finding.value_raw,
        unit_printed=unit_printed,
        interval_printed=interval_printed,
        flag_printed=finding.flag_in_document,
        page=page,
    )
    return finding, row


def _build_unreferenced_row(
    rng: random.Random,
    new_id: IdFactory,
    analyte: Analyte,
    lab: LabStyle,
    measured_at: date,
    panel: str,
    page: int,
    name_printed: str,
) -> tuple[AnalyteFinding, PrintedRow]:
    """Analit i matur pa interval referent — rasti i SP5.

    Asnjë interval nuk shtypet dhe asnjë nuk gjendet në tabelë, prandaj
    statusi mbetet UNINTERPRETABLE dhe asnjë flamur nuk vendoset: flamuri
    do të nënkuptonte një krahasim që askush nuk e ka bërë.
    """
    value = sample_unreferenced_value(rng, analyte)
    value_raw = _format_number(value, analyte.decimals, lab.decimal_comma)

    finding = AnalyteFinding(
        id=new_id(),
        analyte_code=analyte.loinc_code,
        analyte_name_raw=name_printed,
        analyte_name_canonical=analyte.name_canonical_sq,
        value_raw=value_raw,
        value=value,
        unit_raw=analyte.unit,
        unit_canonical=analyte.unit,
        value_canonical=value,
        ref_low=None,
        ref_high=None,
        ref_source=ReferenceSource.NONE,
        status=AnalyteStatus.UNINTERPRETABLE,
        severity=None,
        page=page,
        bbox=None,
        measured_at=measured_at,
        flag_in_document=None,
    )

    row = PrintedRow(
        finding_id=finding.id,
        panel=panel,
        panel_title=PANEL_TITLES.get(panel, panel.upper()),
        name_printed=name_printed,
        value_printed=value_raw,
        unit_printed=analyte.unit,
        interval_printed=None,
        flag_printed=None,
        page=page,
    )
    return finding, row


def _prints_interval(rng: random.Random, lab: LabStyle) -> bool:
    if lab.interval_policy == "all":
        return True
    if lab.interval_policy == "none":
        return False
    return rng.random() < 0.6


def _maybe_perturb(
    rng: random.Random, analyte: Analyte, low: Decimal, high: Decimal
) -> tuple[Decimal, Decimal]:
    """Laboratorë të ndryshëm shtypin intervale paksa të ndryshme.

    Pa këtë, intervali i shtypur do të përputhej gjithmonë me tabelën e
    brendshme dhe nxjerrja e intervalit nga dokumenti nuk do të matej
    kurrë vërtet: sistemi do të dilte i saktë edhe po ta injoronte fare
    atë që shtypet.
    """
    if rng.random() >= 0.10:
        return low, high
    step = Decimal(1).scaleb(-analyte.decimals)
    shifted_low = low + step * rng.randint(-2, 1)
    shifted_high = high + step * rng.randint(-1, 2)
    # Kufi i poshtëm negativ nuk shtypet askund; për analitet që nisin nga
    # zero ndryshimi shkon vetëm lart.
    return max(shifted_low, Decimal(0)), shifted_high


def _quantize(value: Decimal, decimals: int) -> Decimal:
    return value.quantize(Decimal(1).scaleb(-decimals))


def _format_number(value: Decimal, decimals: int, decimal_comma: bool) -> str:
    text = format(_quantize(value, decimals), f".{decimals}f")
    return text.replace(".", ",") if decimal_comma else text


def _format_interval(
    low: Decimal, high: Decimal, decimals: int, decimal_comma: bool
) -> str:
    return (
        f"{_format_number(low, decimals, decimal_comma)} - "
        f"{_format_number(high, decimals, decimal_comma)}"
    )


def _flag_for(status: AnalyteStatus, style: str | None) -> str | None:
    if style is None or not status.is_abnormal:
        return None
    if style == "HL":
        return "H" if status.direction is Direction.INCREASED else "L"
    if style == "arrow":
        return "↑" if status.direction is Direction.INCREASED else "↓"
    return "*"


def build_cross_references(
    findings: tuple[AnalyteFinding, ...],
    assertions: tuple[ReportAssertion, ...],
    new_id: IdFactory,
) -> tuple[CrossReference, ...]:
    """Krahasimi raport ↔ laborator, një gjendje për analit.

    Pohimet pa analit (rekomandimet dhe përmendjet e termave) nuk hyjnë
    këtu: ato nuk pretendojnë asgjë për një vlerë të matur.

    Identifikuesi jepet nga fabrika e mbjellë dhe jo nga `uuid4()` i
    modelit: një identifikues i rastësishëm i vetëm mjafton që i njëjti
    seed të prodhojë dy korpuse të ndryshëm.
    """
    by_code = {f.analyte_code: f for f in findings}
    refs: list[CrossReference] = []
    mentioned: set[str] = set()

    for assertion in assertions:
        code = assertion.analyte_code
        if code is None or code in mentioned:
            continue
        mentioned.add(code)

        finding = by_code.get(code)
        if finding is None:
            refs.append(
                CrossReference(
                    id=new_id(),
                    analyte_code=code,
                    state=CrossReferenceState.MENTIONED_NOT_MEASURED,
                    assertion_id=assertion.id,
                )
            )
            continue

        refs.append(
            CrossReference(
                id=new_id(),
                analyte_code=code,
                state=(
                    CrossReferenceState.AGREEMENT
                    if _agrees(assertion, finding.status)
                    else CrossReferenceState.CONTRADICTION
                ),
                assertion_id=assertion.id,
                finding_id=finding.id,
            )
        )

    for finding in findings:
        if finding.analyte_code not in mentioned:
            refs.append(
                CrossReference(
                    id=new_id(),
                    analyte_code=finding.analyte_code,
                    state=CrossReferenceState.MEASURED_NOT_MENTIONED,
                    finding_id=finding.id,
                )
            )

    return tuple(refs)


def _agrees(assertion: ReportAssertion, status: AnalyteStatus) -> bool:
    """A përputhet pohimi me statusin e matur?

    Mohimi nuk është e kundërta e pohimit: "nuk rezulton mbi intervalin"
    përputhet me çdo status që nuk është i rritur, jo vetëm me atë të
    ulët. Prandaj polariteti trajtohet veçmas nga drejtimi.
    """
    claimed = assertion.direction
    if claimed is Direction.UNSPECIFIED:
        return True
    if assertion.polarity is Polarity.NEGATED:
        return status.direction is not claimed
    return status.direction is claimed


def _glossary_for(terms: tuple[str, ...]) -> tuple[GlossaryEntry, ...]:
    """Zërat e tabelës terminologjike për termat e përmendur.

    Vetëm termat që janë vërtet në tabelë përfundojnë këtu; kjo është ana
    tjetër e SP6, prandaj një term i panjohur nuk hyn në heshtje.
    """
    table = terms_by_name()
    entries = []
    for term in terms:
        found = table.get(term)
        if found is None:
            continue
        entries.append(
            GlossaryEntry(
                term=found.term,
                explanation_sq=found.explanation_sq,
                source_ref=found.source_ref,
                category=found.category,
                synonyms=found.synonyms,
            )
        )
    return tuple(entries)
