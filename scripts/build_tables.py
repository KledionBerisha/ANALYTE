"""
Ndërtimi i tabelave të punimit nga burimet e vërteta.

    python scripts/build_tables.py

Tabelat T1-T4 nuk shkruhen me dorë. Ato dalin nga po ata skedarë dhe po
ai katalog që përdor sistemi, sepse një tabelë e shtypur me dorë në
punim fillon të largohet nga kodi që ditën e dytë — dhe askush nuk e
vëren derisa dikush të kontrollojë një rresht.

Dalja shkon te `docs/thesis/tables/` dhe rigjenerohet sa herë burimet
ndryshojnë.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "src"))

from analyte.catalog import (  # noqa: E402
    Sex,
    load_analytes,
    load_analytes_without_reference,
    load_conversions,
    load_terminology,
)
from analyte.domain.policy import RULE_CATALOG, RULES_VERSION  # noqa: E402

OUT = ROOT / "docs" / "thesis" / "tables"

HEADER = (
    "<!-- E gjeneruar nga scripts/build_tables.py. Mos e ndrysho me dorë: "
    "ndrysho burimin te resources/ ose te domain/policy.py. -->\n\n"
)


def _interval(low, high) -> str:
    if low is None or high is None:
        return "—"
    return f"{low} – {high}"


def table_1() -> str:
    """T1 — paneli i analiteve dhe hartëzimi LOINC."""
    lines = [
        "### Tabela 1. Paneli i analiteve dhe hartëzimi LOINC",
        "",
        "Intervalet janë ato të tabelës së brendshme, e cila përdoret vetëm kur",
        "dokumenti nuk e shtyp vetë intervalin. Aty ku kufijtë ndryshojnë sipas",
        "gjinisë, jepen të dy.",
        "",
        "| Kodi LOINC | Analiti | Njësia | Paneli | Interval (M) | Interval (F) |",
        "|---|---|---|---|---|---|",
    ]
    for analyte in load_analytes():
        male = _interval(*analyte.reference_for(Sex.MALE))
        female = _interval(*analyte.reference_for(Sex.FEMALE))
        lines.append(
            f"| {analyte.loinc_code} | {analyte.name_canonical_sq} | {analyte.unit} "
            f"| {analyte.panel} | {male} | {female if analyte.is_sex_specific else '—'} |"
        )

    extra = load_analytes_without_reference()
    lines += [
        "",
        f"Tabela përmban {len(load_analytes())} analite me interval referent.",
        "",
        f"Krahas tyre, sistemi njeh me emër edhe {len(extra)} analite për të cilat",
        "tabela e brendshme nuk përmban interval. Këto nuk janë mangësi e tabelës",
        "por rasti që rregullon politika SP5: vlera matet, emri njihet, dhe",
        "interpretimi refuzohet.",
        "",
        "| Kodi LOINC | Analiti | Njësia |",
        "|---|---|---|",
    ]
    for analyte in extra:
        lines.append(f"| {analyte.loinc_code} | {analyte.name_canonical_sq} | {analyte.unit} |")
    return "\n".join(lines) + "\n"


def table_2() -> str:
    """T2 — faktorët e konvertimit të njësive."""
    lines = [
        "### Tabela 2. Faktorët e konvertimit të njësive",
        "",
        "Faktori shumëzon vlerën e shtypur në njësinë e parë për ta kthyer në",
        "njësinë kanonike. Konvertimi varet nga analiti kudo ku në të hyn masa",
        "molare, prandaj shumica e rreshtave janë specifikë për një kod LOINC.",
        "",
        "| Nga | Në | Faktori | Analiti |",
        "|---|---|---|---|",
    ]
    for conversion in load_conversions():
        code = conversion.loinc_code or "çdo analit"
        lines.append(
            f"| {conversion.unit_from} | {conversion.unit_to} "
            f"| {conversion.factor} | {code} |"
        )
    return "\n".join(lines) + "\n"


def table_3(limit: int = 20) -> str:
    """T3 — ekstrakt i tabelës terminologjike."""
    terms = load_terminology()
    lines = [
        "### Tabela 3. Ekstrakt i tabelës terminologjike",
        "",
        f"Tabela e plotë përmban {len(terms)} zëra dhe jepet në shtojcë. Këtu",
        f"paraqiten {limit} të parët për të treguar formatin.",
        "",
        "| Termi | Shpjegimi | Kategoria | Burimi |",
        "|---|---|---|---|",
    ]
    for term in terms[:limit]:
        lines.append(
            f"| {term.term} | {term.explanation_sq} | {term.category or '—'} "
            f"| {term.source_ref} |"
        )
    lines += [
        "",
        "> Kolona e burimit është ende vendmbajtëse. Çdo zë duhet të marrë një",
        "> referencë të verifikueshme përpara dorëzimit; pa të, tabela bëhet vetë",
        "> burim informacioni të paverifikuar dhe shkel arsyen për të cilën u",
        "> ndërtua.",
    ]
    return "\n".join(lines) + "\n"


def table_4() -> str:
    """T4 — katalogu i rregullave të verifikimit."""
    lines = [
        "### Tabela 4. Katalogu i rregullave të verifikimit",
        "",
        f"Versioni i katalogut: `{RULES_VERSION}`. Ai regjistrohet në çdo",
        "rezultat verifikimi, prandaj rezultatet e vjetra mbeten të lexueshme",
        "edhe pasi katalogu ndryshon.",
        "",
        "| Rregulli | Dega | Lloji i shkeljes | Përshkrimi | Fushëveprimi |",
        "|---|---|---|---|---|",
    ]
    for rule in RULE_CATALOG:
        scope = "tërë dalja" if rule.requires_context else "fjalia"
        lines.append(
            f"| {rule.id} | {rule.branch} | `{rule.violation.value}` "
            f"| {rule.description_sq} | {scope} |"
        )
    lines += [
        "",
        "Fushëveprimi ndan rregullat që vendosen nga një fjali e vetme nga ato që",
        "kërkojnë shikim mbi tërë daljen. Vetëm të parat mund të përbëjnë detyrë",
        "klasifikimi në nivel fjalie, prandaj kjo kolonë përcakton edhe se cilat",
        "shkelje mund të mësohen nga klasifikuesi i Fazës 7 dhe cilat jo.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, builder in (
        ("T1_analitet.md", table_1),
        ("T2_njesite.md", table_2),
        ("T3_terminologjia.md", table_3),
        ("T4_rregullat.md", table_4),
    ):
        path = OUT / name
        path.write_text(HEADER + builder(), encoding="utf-8")
        print(f"shkruar {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
