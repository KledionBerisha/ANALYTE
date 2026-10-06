"""
Kontrolli i besueshmërisë për vlerat e lexuara nga OCR-ja (ADR 0020).

**Problemi.** E3 mati 62 vlera me status të interpretuar dhe të gabuar, 11 prej tyre kritike të rreme. Të gjitha
vijnë nga i njëjti defekt i OCR-së: një presje dhjetore që humbet. Në 42 raste humbi te INTERVALI i shtypur
("2,5 - 4,5" lexohet "25 - 45"), dhe vlera e saktë del "e ulët"; në 20 humbi te VLERA ("46,6" lexohet "466"), dhe
vlera normale del "e lartë" ose "kritike". Nuk ka mënyrë ta dallosh nga teksti i leximit; ka dy shenja që
dallohen nga konteksti i vetë gjetjes.

**Dy kontrollet, të dyja vetëm për faqet e lexuara me OCR** (shtresa e tekstit të PDF-së nuk humb presje):

1. *Intervali i dëmtuar.* Nëse secili nga dy kufijtë e intervalit të shtypur është afërsisht 10, 100 ose 1000 herë ai i tabelës së
   brendshme për të njëjtin analit (me një tolerancë për ndryshimin normal ndërmjet laboratorëve), presja ka humbur.
   Intervali i shtypur hidhet dhe përdoret ai i tabelës — rruga që ekziston tashmë kur intervali nuk shtypet. Kur
   tabela nuk ka interval (ose gjinia nuk dihet), gjetja mbetet e painterpretueshme (SP5).
2. *Vlera e dyshimtë.* Vlera është shtypur pa presje te një analit që laboratori e shtyp me presje, ajo del mbi
   intervalin, dhe pjesëtimi me 10 ose 100 e fut brenda tij. Rreshti nuk merret: një rresht i humbur është më i mirë se
   një vlerë e gabuar që pacienti e lexon si të vetën (po ai arsyetim si te "njësi e palexueshme").

**Çfarë nuk kapet.** Vlera që ka humbur presjen por del brenda intervalit pas lëvizjes ("13" në vend të "1,3" kur edhe
13 është brenda), vlerat e tjera të lexuara gabim ("4,35" për "4,3", shifra e zëvendësuar), dhe një vlerë e vërtetë e
shtypur pa presje që rastësisht plotëson kushtin (p.sh. kreatininë 8 mg/dL e shtypur "8"): ajo humbet si rresht. Ky
është çmimi i kontrollit dhe matet te E3 me kontrollin ndezur.

3. *Përqindja e pamundur.* Një analit me njësi `%` e lexuar mbi 100 refuzohet (përkufizim, jo kufi mjekësor).

Pragjet (10, 100 dhe 1000 për intervalin, 10 dhe 100 për vlerën, toleranca 15%) u zgjodhën pasi u panë gabimet e E3; kjo deklarohet te ADR 0020.
"""

from __future__ import annotations

from decimal import Decimal

from analyte.catalog import Analyte, Sex, conversion_for

from .normalize import normalize_unit

SHIFTS: tuple[int, ...] = (10, 100)
"""Sa herë më i madh del një vlerë pasi humb një ose dy presje."""

INTERVAL_SHIFTS: tuple[int, ...] = (10, 100, 1000)
"""Te intervali secili kufi humb presjet e veta: "0,20 - 1,20" lexohet "20 - 1200" (100x dhe 1000x)."""

TOLERANCE = Decimal("0.15")
"""Sa mund të largohet intervali i shtypur nga ai i tabelës (laboratorët ndryshojnë pak) para se të quhet 10x."""


def damaged_interval(
    analyte: Analyte, low: Decimal | None, high: Decimal | None
) -> bool:
    """A është intervali i shtypur 10 ose 100 herë ai i tabelës (presje e humbur)?

    Krahasohet me të dyja gjinitë: kontrolli nuk duhet të varet nga gjinia e panjohur.
    """
    if not analyte.has_reference or (low is None and high is None):
        return False
    for sex in (Sex.MALE, Sex.FEMALE):
        table_low, table_high = analyte.reference_for(sex)
        if _matches(low, table_low) and _matches(high, table_high):
            return True
    return False


def _matches(printed: Decimal | None, table: Decimal | None) -> bool:
    """Kufiri i shtypur ≈ kufiri i tabelës × 10, 100 ose 1000. Një kufi që mungon nga të dyja anët përputhet."""
    if printed is None and table is None:
        return True
    if printed is None or table is None or table <= 0:
        return False
    return any(
        table * shift * (1 - TOLERANCE) <= printed <= table * shift * (1 + TOLERANCE)
        for shift in INTERVAL_SHIFTS
    )


def expected_decimals(analyte: Analyte, printed_unit: str) -> int | None:
    """Me sa presje e shtyp laboratori këtë analit në këtë njësi; None kur njësia është e panjohur."""
    unit = normalize_unit(printed_unit)
    if not unit or unit == analyte.unit:
        return analyte.decimals
    conversion = conversion_for(analyte)
    if conversion is not None and unit == conversion.unit_from:
        return conversion.decimals
    return None


def impossible_percentage(analyte: Analyte, printed_unit: str, value_canonical: Decimal) -> bool:
    """Një përqindje mbi 100 është e pamundur nga përkufizimi, jo nga mjekësia: nuk kërkon burim.

    Hematokriti "598" për 59,8 dhe "166" për 16,6 ishin dy gabimet e mbetura pas kontrollit të presjes: zhvendosja nuk e fut vlerën brenda
    intervalit, por vlera është e pamundur si përqindje. Vlen vetëm kur njësia e analitit është `%`; kufijtë fiziologjikë të analiteve të tjera
    kërkojnë burime të lexuara dhe nuk u shtuan.
    """
    unit = normalize_unit(printed_unit)
    return analyte.unit == "%" and unit in ("", "%") and value_canonical > 100


def lost_decimal(
    analyte: Analyte,
    value_text: str,
    printed_unit: str,
    value_canonical: Decimal,
    low: Decimal | None,
    high: Decimal | None,
) -> bool:
    """A është vlera e shtypur pa presje, mbi intervalin, dhe brenda tij pas një ose dy presjesh?"""
    if "," in value_text or "." in value_text:
        return False
    decimals = expected_decimals(analyte, printed_unit)
    if not decimals or high is None or value_canonical <= high:
        return False
    floor = low if low is not None else Decimal(0)
    return any(floor <= value_canonical / shift <= high for shift in SHIFTS)
