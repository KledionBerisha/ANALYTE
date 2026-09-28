"""
Tabelat burimore: analitet, njësitë, terminologjia dhe rregullat e kombinimit.

Skedarët në `resources/` janë burimi i vetëm i së vërtetës. Dega A i
lexon për të ditur si ta interpretojë atë që gjen në dokument; gjeneruesi
i të dhënave sintetike lexon të njëjtët skedarë për të ditur çfarë të
shtypë. Një tabelë e dytë do të prodhonte mospërputhje që shfaqen si
gabime të sistemit dhe jo si gabime të të dhënave.

Moduli rri jashtë `domain/` sepse lexon skedarë, dhe domeni nuk bën I/O.
Ai rri brenda backend-it e jo te gjeneruesi sepse tabelat i përkasin
sistemit: gjeneruesi është vegël zhvillimi dhe mund të mos ekzistojë fare
në prodhim.

Të gjitha vlerat numerike lexohen si Decimal. Float-i do të prishte
barazinë e saktë mbi të cilën mbështetet rregulli R1.
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from functools import lru_cache
from pathlib import Path

def _resources_dir() -> Path:
    """Ku gjenden tabelat burimore.

    Parazgjedhja është dosja `resources/` e depove; ndryshorja e mjedisit
    lejon zëvendësimin e tyre pa prekur kodin — e nevojshme kur shërbimi
    vendoset i paketuar diku ku pema e depove nuk ekziston.
    """
    override = os.environ.get("ANALYTE_RESOURCES")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[3] / "resources"


RESOURCES_DIR = _resources_dir()


class Sex(str, Enum):
    """Gjinia biologjike — e nevojshme vetëm për intervalet referente.

    Ajo nuk hyn kurrë në GroundingContext: konteksti nuk mban të dhëna
    të pacientit (NFR5). Këtu shërben për të zgjedhur intervalin e
    duhur gjatë gjenerimit dhe mbetet në metadata e dokumentit.
    """

    MALE = "M"
    FEMALE = "F"


@dataclass(frozen=True, slots=True)
class Analyte:
    """Një analit i tabelës së brendshme.

    `variants` janë format si shtypen nga laboratorë të ndryshëm. Ato
    janë njëkohësisht materiali i gjeneruesit (çfarë shtypet) dhe i
    hartës LOINC (çfarë duhet njohur).
    """

    loinc_code: str
    name_canonical_sq: str
    variants: tuple[str, ...]
    unit: str
    alt_unit: str | None
    decimals: int
    panel: str
    narrative_name: str
    """Emri me të cilin mjeku e përmend analitin në tekst të lirë.

    Ndryshe nga `variants`, ky nuk është forma e shtypur në tabelë: në
    tabelë lexohet "BUN" ose "PLT", në narrativë shkruhet "Urea" ose
    "Trombocitet"."""
    narrative_plural: bool
    """A është `narrative_name` në shumës? Shqipja e kërkon foljen të
    përshtatur; pa këtë fushë dalin fjali si "Trombocitet del"."""
    ref_low_m: Decimal | None
    ref_high_m: Decimal | None
    ref_low_f: Decimal | None
    ref_high_f: Decimal | None
    critical_low: Decimal | None
    critical_high: Decimal | None
    sample_low: Decimal | None = None
    sample_high: Decimal | None = None
    """Vetëm për gjenerim: brezi i vlerave të besueshme për shtypje te
    analitet pa interval referent. Nuk është interval referent dhe nuk
    përdoret kurrë për klasifikim — po të përdorej, SP5 do të shkelej
    pikërisht nga gjeneruesi."""

    @property
    def has_reference(self) -> bool:
        """A e mbulon tabela e brendshme këtë analit?

        Analitet pa interval janë rasti i SP5: sistemi i njeh me emër
        por nuk guxon t'i interpretojë.
        """
        return self.ref_low_m is not None or self.ref_high_m is not None

    @property
    def is_sex_specific(self) -> bool:
        return (self.ref_low_m, self.ref_high_m) != (self.ref_low_f, self.ref_high_f)

    def reference_for(self, sex: Sex) -> tuple[Decimal | None, Decimal | None]:
        if sex is Sex.MALE:
            return self.ref_low_m, self.ref_high_m
        return self.ref_low_f, self.ref_high_f

    def quantize(self, value: Decimal) -> Decimal:
        """Rrumbullakon si do ta shtypte laboratori, me numrin e vet të presjeve."""
        return value.quantize(Decimal(1).scaleb(-self.decimals))


@dataclass(frozen=True, slots=True)
class UnitConversion:
    """Kthim nga njësia e shtypur në njësinë kanonike.

    `decimals` është numri i presjeve me të cilat shtypet njësia
    alternative — 135 g/L kundrejt 13.5 g/dL nuk kanë të njëjtën saktësi
    të shtypur.
    """

    unit_from: str
    unit_to: str
    factor: Decimal
    decimals: int
    loinc_code: str | None

    def to_canonical(self, value: Decimal) -> Decimal:
        return value * self.factor

    def from_canonical(self, value: Decimal) -> Decimal:
        return value / self.factor


@dataclass(frozen=True, slots=True)
class Term:
    """Një zë i tabelës terminologjike (Dega B)."""

    term: str
    explanation_sq: str
    source_ref: str
    category: str | None
    synonyms: tuple[str, ...]

    def surface_forms(self) -> tuple[str, ...]:
        """Të gjitha format me të cilat termi mund të shfaqet në tekst."""
        return (self.term, *self.synonyms)


@dataclass(frozen=True, slots=True)
class Pattern:
    """Një rregull kombinimi: çdo kusht duhet të plotësohet njëkohësisht.

    Kushti është një analit dhe drejtimi i statusit të tij. Drejtimi, jo
    statusi: një vlerë kritike e lartë është e lartë, dhe rregulli që nuk
    ndizet pikërisht te vlerat më të rënda do të ishte i pakuptimtë.
    """

    pattern_id: str
    conditions: tuple[tuple[str, str], ...]
    """Çifte (kodi LOINC, drejtimi) — drejtimi si vlerë e `Direction`."""
    source_ref: str


def _decimal(raw: str) -> Decimal | None:
    raw = raw.strip()
    return Decimal(raw) if raw else None


def _variants(raw: str) -> tuple[str, ...]:
    return tuple(v.strip() for v in raw.split("|") if v.strip())


def _read(name: str) -> list[dict[str, str]]:
    path = RESOURCES_DIR / name
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


@lru_cache(maxsize=1)
def load_analytes() -> tuple[Analyte, ...]:
    """Analitet me interval referent në tabelën e brendshme."""
    out = []
    for row in _read("analytes.csv"):
        out.append(
            Analyte(
                loinc_code=row["loinc_code"],
                name_canonical_sq=row["name_canonical_sq"],
                variants=_variants(row["name_variants"]),
                unit=row["unit"],
                alt_unit=row["alt_unit"].strip() or None,
                decimals=int(row["decimals"]),
                panel=row["panel"],
                narrative_name=row["narrative_name"],
                narrative_plural=row["narrative_plural"] == "1",
                ref_low_m=_decimal(row["ref_low_m"]),
                ref_high_m=_decimal(row["ref_high_m"]),
                ref_low_f=_decimal(row["ref_low_f"]),
                ref_high_f=_decimal(row["ref_high_f"]),
                critical_low=_decimal(row["critical_low"]),
                critical_high=_decimal(row["critical_high"]),
            )
        )
    return tuple(out)


@lru_cache(maxsize=1)
def load_analytes_without_reference() -> tuple[Analyte, ...]:
    """Analite që sistemi i njeh me emër por nuk i interpreton dot.

    Laboratorët matin shumë më tepër se sa mbulon një tabelë referente e
    ndërtuar me dorë. Këto raste nuk janë të rralla dhe nuk janë gabim:
    ato janë pikërisht ajo që SP5 rregullon. Pa to, korpusi nuk do ta
    testonte kurrë refuzimin e interpretimit.
    """
    out = []
    for row in _read("analytes_extra.csv"):
        out.append(
            Analyte(
                loinc_code=row["loinc_code"],
                name_canonical_sq=row["name_canonical_sq"],
                variants=_variants(row["name_variants"]),
                unit=row["unit"],
                alt_unit=None,
                decimals=int(row["decimals"]),
                panel=row["panel"],
                narrative_name=_variants(row["name_variants"])[0],
                narrative_plural=False,
                ref_low_m=None,
                ref_high_m=None,
                ref_low_f=None,
                ref_high_f=None,
                critical_low=None,
                critical_high=None,
                sample_low=_decimal(row["sample_low"]),
                sample_high=_decimal(row["sample_high"]),
            )
        )
    return tuple(out)


@lru_cache(maxsize=1)
def load_conversions() -> tuple[UnitConversion, ...]:
    out = []
    for row in _read("units.csv"):
        out.append(
            UnitConversion(
                unit_from=row["unit_from"],
                unit_to=row["unit_to"],
                factor=Decimal(row["factor"]),
                decimals=int(row["decimals"]),
                loinc_code=row["loinc_code"].strip() or None,
            )
        )
    return tuple(out)


@lru_cache(maxsize=1)
def load_terminology() -> tuple[Term, ...]:
    out = []
    for row in _read("terminology.csv"):
        out.append(
            Term(
                term=row["term"],
                explanation_sq=row["explanation_sq"],
                source_ref=row["source_ref"],
                category=row["category"].strip() or None,
                synonyms=_variants(row["synonyms"]),
            )
        )
    return tuple(out)


@lru_cache(maxsize=1)
def load_patterns() -> tuple[Pattern, ...]:
    out = []
    for row in _read("patterns.csv"):
        conditions = tuple(
            tuple(part.split(":", 1)) for part in _variants(row["conditions"])
        )
        out.append(Pattern(row["pattern_id"], conditions, row["source_ref"]))
    return tuple(out)


@lru_cache(maxsize=1)
def analytes_by_code() -> dict[str, Analyte]:
    everything = load_analytes() + load_analytes_without_reference()
    return {a.loinc_code: a for a in everything}


@lru_cache(maxsize=1)
def terms_by_name() -> dict[str, Term]:
    return {t.term: t for t in load_terminology()}


def conversion_for(analyte: Analyte) -> UnitConversion | None:
    """Kthimi që i përket njësisë alternative të këtij analiti.

    Kërkohet fillimisht një kthim i lidhur me kodin LOINC (masat molare
    janë specifike për substancën) dhe më pas një i përgjithshëm.
    """
    if analyte.alt_unit is None:
        return None
    conversions = load_conversions()
    wanted = (analyte.alt_unit, analyte.unit)
    for conv in conversions:
        if conv.loinc_code == analyte.loinc_code and (conv.unit_from, conv.unit_to) == wanted:
            return conv
    for conv in conversions:
        if conv.loinc_code is None and (conv.unit_from, conv.unit_to) == wanted:
            return conv
    return None
