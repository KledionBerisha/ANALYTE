"""
Ndërtimi i tabelave të punimit nga burimet e vërteta.

    python scripts/build_tables.py

"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "src"))

from analyte.catalog import (
    Sex,
    analytes_by_code,
    load_analytes,
    load_analytes_without_reference,
    load_conversions,
    load_patterns,
    load_terminology,
)
from analyte.domain.policy import RULE_CATALOG, RULES_VERSION

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
            f"| {conversion.unit_from} | {conversion.unit_to} | {conversion.factor} | {code} |"
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
            f"| {term.term} | {term.explanation_sq} | {term.category or '—'} | {term.source_ref} |"
        )
    unsourced = sum(1 for t in terms if "plotësohet" in t.source_ref)
    if unsourced:
        lines += [
            "",
            f"> Kolona e burimit është ende vendmbajtëse për {unsourced} nga {len(terms)} zëra.",
            "> Çdo zë duhet të marrë një referencë të verifikueshme përpara dorëzimit;",
            "> pa të, tabela bëhet vetë burim informacioni të paverifikuar dhe shkel",
            "> arsyen për të cilën u ndërtua.",
        ]
    else:
        lines += [
            "",
            "> Çdo zë mban në kolonën e burimit faqen ose përshkruesin (MeSH, MedlinePlus,",
            "> Cleveland Clinic, Testing.com) që u lexua më 2026-10-06 dhe që e mbështet",
            "> shpjegimin shqip; shpjegimi është formulim i autorit, jo përkthim i burimit.",
            "> Citimi i evidencës për secilin zë ruhet te",
            "> `docs/thesis/worksheets/burimet_e_gjetura.md`.",
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


def table_5() -> str:
    """T5 — rregullat e kombinimit ndërmjet analiteve."""
    names = {code: a.name_canonical_sq for code, a in analytes_by_code().items()}
    arrow = {"increased": "↑", "decreased": "↓"}
    lines = [
        "### Tabela 5. Rregullat e kombinimit ndërmjet analiteve",
        "",
        "Një rregull ndizet kur të gjitha kushtet plotësohen njëkohësisht.",
        "Vlera kritike numërohet sipas drejtimit të saj; vlera pa interval",
        "referent nuk merr pjesë (SP5). Rregulli nuk emërton gjendje: dalja thotë",
        "vetëm se kombinimi kërkon vlerësim nga profesionisti shëndetësor.",
        "",
        "| ID | Kushtet | Burimi |",
        "|---|---|---|",
    ]
    for pattern in load_patterns():
        conditions = " + ".join(
            f"{names[code]} {arrow[direction]}" for code, direction in pattern.conditions
        )
        lines.append(f"| {pattern.pattern_id} | {conditions} | {pattern.source_ref} |")
    patterns = load_patterns()
    if any("plotësohet" in p.source_ref for p in patterns):
        lines += [
            "",
            "> Kombinimet u zgjodhën si të njohura gjerësisht dhe duhen konfirmuar nga",
            "> mentori ose nga një mjek, bashkë me burimin e secilit, përpara",
            "> dorëzimit.",
        ]
    else:
        lines += [
            "",
            "> Burimi i secilit kombinim u lexua më 2026-10-06; citimi i evidencës dhe",
            "> shkalla e mbështetjes (e plotë ose e pjesshme) për secilin jepen te",
            "> `docs/thesis/worksheets/burimet_e_gjetura.md`. Kombinimet duhen konfirmuar",
            "> nga mentori ose nga një mjek përpara dorëzimit.",
        ]
    return "\n".join(lines) + "\n"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, builder in (
        ("T1_analitet.md", table_1),
        ("T2_njesite.md", table_2),
        ("T3_terminologjia.md", table_3),
        ("T4_rregullat.md", table_4),
        ("T5_kombinimet.md", table_5),
    ):
        path = OUT / name
        path.write_text(HEADER + builder(), encoding="utf-8")
        print(f"shkruar {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
