"""
Nga rreshtat e faqes te gjetjet e strukturuara.

Nxjerrja punon me rreshta të rindërtuar nga pozicionet, jo me tekst të
rrafshuar. Kjo ka rëndësi: "Hb 13,0 g/dL 13,5 - 17,5" si varg i vetëm
kërkon hamendje se ku mbaron emri dhe ku fillon vlera, ndërsa si tre
fragmente me kolona të veta nuk kërkon asnjë.

Rregulli i njohjes së një rreshti të dhënash është i qëllimshëm i ngushtë:

  - ka të paktën dy fragmente,
  - fragmenti i parë nuk është numër — ai është emri,
  - një nga fragmentet e mëpasme fillon me numër — ajo është vlera.

Blloku i pacientit e kalon këtë provë vetëm rastësisht, dhe kur e kalon,
emri i tij nuk njihet nga tabela e analiteve dhe rreshti bie. Titujt e
paneleve dhe koka e kolonave nuk kanë numra dhe bien menjëherë.

Ajo që nuk njihet nuk hamendësohet. Emri i panjohur, njësia e pakthyeshme
dhe intervali që mungon prodhojnë secili pasojën e vet të dukshme — deri
te refuzimi i interpretimit — sepse një gjetje e shpikur këtu do të
mbahej si e mbështetur nga çdo shtresë e mëpasme.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from uuid import uuid4

from analyte.catalog import Analyte, Sex, analytes_by_code
from analyte.domain.enums import AnalyteStatus, ReferenceSource
from analyte.domain.models import AnalyteFinding, BoundingBox
from analyte.ingestion.pdf_text import PageText, TextRow

from . import loinc, ocr_guard as guard, reference
from .classify import classify
from .normalize import normalize_unit, parse_number, split_value_and_unit, to_canonical

FLAGS = {"H", "L", "HH", "LL", "*", "↑", "↓", "+", "-"}
"""Flamujt e shtypur që njihen. Shigjetat e vizatuara si vija nuk kanë
tekst dhe nuk lexohen dot nga kjo rrugë — humbje e njohur, pa pasojë te
PK1, sepse flamuri nuk është fushë e matur."""

SEX_MARKERS: dict[str, Sex] = {
    "mashkull": Sex.MALE,
    "m": Sex.MALE,
    "femer": Sex.FEMALE,
    "femër": Sex.FEMALE,
    "f": Sex.FEMALE,
}

_SEX_LINE = re.compile(r"gjinia\s*[:\-]?\s*(?P<value>[^\s,;]+)", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class RawRow:
    """Një rresht i njohur si të dhëna, përpara çdo interpretimi."""

    name: str
    value_text: str
    unit_text: str
    interval_text: str | None
    flag: str | None
    page: int
    bbox: BoundingBox


@dataclass(frozen=True, slots=True)
class Extraction:
    """Rezultati i nxjerrjes bashkë me atë që u la jashtë.

    Rreshtat e hedhur ruhen me arsyen e tyre. Pa këtë listë, analiza e
    gabimeve e Kapitullit 7 do të mbështetej te ndjesia: një PK1 i ulët
    nuk do të tregonte nëse faji ishte i segmentimit, i hartës LOINC apo i
    njësive.
    """

    findings: tuple[AnalyteFinding, ...]
    rejected: tuple[tuple[str, str], ...]
    patient_sex: Sex | None
    corrections: tuple[tuple[str, str], ...] = ()
    """Rreshtat e mbajtur por me një korrigjim nga kontrolli i OCR-së (ADR 0020): intervali i dëmtuar u zëvendësua."""

    def rejection_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for _, motive in self.rejected:
            counts[motive] = counts.get(motive, 0) + 1
        return dict(sorted(counts.items()))


def extract(pages: tuple[PageText, ...], *, new_id=uuid4, ocr_guard: bool = True) -> Extraction:
    """Nxjerr gjetjet nga faqet e lexuara.

    `ocr_guard` zbaton kontrollet e besueshmërisë (`ocr_guard.py`) mbi faqet e lexuara me OCR; faqet e tekstit nuk preken.
    """
    sex = find_patient_sex(pages)
    findings: list[AnalyteFinding] = []
    rejected: list[tuple[str, str]] = []
    corrections: list[tuple[str, str]] = []
    seen: set[str] = set()

    for page in pages:
        for row in page.rows:
            raw = parse_row(row)
            if raw is None:
                continue

            finding, motive = _to_finding(
                raw, sex, new_id, guarded=ocr_guard and page.ocr, corrections=corrections
            )
            if finding is None:
                rejected.append((raw.name, motive))
            elif finding.analyte_code in seen:
                # I njëjti analit dy herë në një dokument: mbahet i pari.
                rejected.append((raw.name, "dublikatë"))
            else:
                seen.add(finding.analyte_code)
                findings.append(finding)

    return Extraction(tuple(findings), tuple(rejected), sex, tuple(corrections))


def find_patient_sex(pages: tuple[PageText, ...]) -> Sex | None:
    """Gjinia e pacientit nga blloku i kokës.

    Nevojitet për zgjidhjen e intervalit kur ai nuk është shtypur. Kur nuk
    gjendet, analitet që varen nga gjinia mbeten pa interval — shih
    `reference.resolve`.
    """
    for page in pages:
        for row in page.rows:
            match = _SEX_LINE.search(row.text)
            if match:
                key = match.group("value").strip().casefold()
                if key in SEX_MARKERS:
                    return SEX_MARKERS[key]
    return None


def parse_row(row: TextRow) -> RawRow | None:
    """Njeh një rresht të dhënash dhe i ndan kolonat e tij."""
    fragments = row.fragments
    if len(fragments) < 2:
        return None

    name = fragments[0].text.strip()
    if not name or parse_number(name) is not None:
        return None

    value_text = unit_text = ""
    interval_text: str | None = None
    flag: str | None = None
    found_value = False

    for fragment in fragments[1:]:
        text = fragment.text.strip()
        if not found_value:
            split = split_value_and_unit(text)
            if split is not None:
                value_text = text.split(None, 1)[0]
                unit_text = split[1]
                found_value = True
                continue

        if text in FLAGS:
            flag = text
        elif reference.parse_printed(text) is not None:
            interval_text = text
        elif found_value and not unit_text and not _looks_like_prose(text):
            unit_text = normalize_unit(text)

    if not found_value:
        return None

    return RawRow(
        name=name,
        value_text=value_text,
        unit_text=unit_text,
        interval_text=interval_text,
        flag=flag,
        page=row.page,
        bbox=row.bbox,
    )


def _unit_like(text: str) -> bool:
    """Njësia ka shkronjë (`mg/dL`, `10^9/L`) ose është simbol si `%`.

    Një "njësi" me shifra dhe pa asnjë shkronjë nuk është njësi: është pjesë
    e një numri tjetër që ra në kolonën e gabuar. Njësia bosh lejohet — ajo
    trajtohet më tej si e panjohur (SP5).
    """
    text = text.strip()
    if not text or any(c.isalpha() for c in text):
        return True
    return not any(c.isdigit() for c in text)


def _looks_like_prose(text: str) -> bool:
    """Njësitë janë të shkurtra dhe pa hapësira; fjalitë jo."""
    return len(text) > 12 or " " in text.strip()


def _to_finding(
    raw: RawRow,
    sex: Sex | None,
    new_id,
    *,
    guarded: bool = False,
    corrections: list[tuple[str, str]] | None = None,
) -> tuple[AnalyteFinding | None, str]:
    code = loinc.resolve(raw.name)
    if code is None:
        return None, "analit i panjohur"

    analyte = analytes_by_code()[code]
    value = parse_number(raw.value_text)
    if value is None:
        return None, "vlerë e palexueshme"
    if not _unit_like(raw.unit_text):
        # "40,0 | 52,0": OCR-ja humbi vlerën dhe intervali u lexua si vlerë
        # me njësi. Kufiri i poshtëm do të dilte si "vlera e matur" — më mirë
        # rreshti i humbur se një vlerë e gabuar që pacienti e lexon si të tijën.
        return None, "njësi e palexueshme"

    converted = to_canonical(analyte, value, raw.unit_text)
    if converted is None:
        # Njësi e panjohur: vlera nuk krahasohet dot me asnjë interval,
        # prandaj mbahet si e painterpretueshme dhe jo si e humbur.
        return _uninterpretable(raw, analyte, value, code, new_id), ""

    value_canonical, unit_canonical = converted
    resolution = reference.resolve(analyte, raw.interval_text, raw.unit_text, sex)

    if guarded:
        if resolution.source is ReferenceSource.DOCUMENT and guard.damaged_interval(
            analyte, resolution.low, resolution.high
        ):
            # Presja humbi te intervali i shtypur: ai hidhet dhe përdoret tabela, ose gjetja mbetet pa interval.
            if corrections is not None:
                corrections.append((raw.name, "interval i dëmtuar nga OCR; zëvendësuar me tabelën"))
            resolution = reference.resolve(analyte, None, raw.unit_text, sex)
        if resolution.has_bounds and guard.lost_decimal(
            analyte,
            raw.value_text,
            raw.unit_text,
            value_canonical,
            resolution.low,
            resolution.high,
        ):
            return None, "vlerë e dyshimtë (OCR): presja dhjetore mungon"

    if not resolution.has_bounds:
        return _uninterpretable(raw, analyte, value, code, new_id), ""

    status, severity = classify(
        value_canonical,
        resolution.low,
        resolution.high,
        analyte.critical_low,
        analyte.critical_high,
    )

    return (
        AnalyteFinding(
            id=new_id(),
            analyte_code=code,
            analyte_name_raw=raw.name,
            analyte_name_canonical=analyte.name_canonical_sq,
            value_raw=raw.value_text,
            value=value,
            unit_raw=raw.unit_text or None,
            unit_canonical=unit_canonical,
            value_canonical=value_canonical,
            ref_low=resolution.low,
            ref_high=resolution.high,
            ref_source=resolution.source,
            status=status,
            severity=severity,
            page=raw.page,
            bbox=raw.bbox,
            flag_in_document=raw.flag,
        ),
        "",
    )


def _uninterpretable(
    raw: RawRow, analyte: Analyte, value: Decimal, code: str, new_id
) -> AnalyteFinding:
    """Gjetje e njohur por e painterpretueshme (SP5).

    Ajo mbahet dhe nuk hidhet: pacienti e ka vlerën në dokument dhe ka të
    drejtë ta shohë të renditur, me shënimin se nuk interpretohet. Heqja e
    saj do të fshihte një matje që laboratori e bëri vërtet.
    """
    return AnalyteFinding(
        id=new_id(),
        analyte_code=code,
        analyte_name_raw=raw.name,
        analyte_name_canonical=analyte.name_canonical_sq,
        value_raw=raw.value_text,
        value=value,
        unit_raw=raw.unit_text or None,
        unit_canonical=normalize_unit(raw.unit_text) or analyte.unit,
        value_canonical=value,
        ref_low=None,
        ref_high=None,
        ref_source=ReferenceSource.NONE,
        status=AnalyteStatus.UNINTERPRETABLE,
        severity=None,
        page=raw.page,
        bbox=raw.bbox,
        flag_in_document=raw.flag,
    )
