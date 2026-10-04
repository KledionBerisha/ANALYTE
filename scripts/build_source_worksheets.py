"""
Fletët e punës për burimet që mungojnë: termat dhe kombinimet.

    python scripts/build_source_worksheets.py            # shkruan docs/thesis/worksheets/burimet.md
    python scripts/build_source_worksheets.py --check    # raporton sa burime mbeten vendmbajtëse

Të 82 termat (`resources/terminology.csv`) dhe 11 kombinimet
(`resources/patterns.csv`) kanë kolonën `source_ref` me vendmbajtës. Burimi nuk
mund të shkruhet nga ky skript: një burim vlen vetëm nëse e keni lexuar. Fleta
bën vetëm punën që nuk kërkon gjykim: radhit çdo zë me pohimin që duhet
mbështetur, e grupon sipas llojit dhe tregon se ku zakonisht gjenden burime të
llojit përkatës (lloje, jo citime). Pasi ta lexoni burimin, e shkruani te
kolona `source_ref` e CSV-së dhe e ekzekutoni skriptin sërish: zërat e plotësuar
dalin nga lista e të mbetura.

Një zë që nuk gjen burim fshihet nga CSV-ja: termi pa burim bëhet «term i
pashpjeguar» (SP6), dhe kombinimi pa burim hiqet.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "src"))

from analyte.catalog import analytes_by_code, load_patterns, load_terminology  # noqa: E402

DEFAULT_OUT = ROOT / "docs" / "thesis" / "worksheets" / "burimet.md"
PLACEHOLDER_MARKS = ("plotësohet",)

WHERE_TO_LOOK = {
    "gjendje": "përkufizim në gjuhë të thjeshtë (MeSH, MedlinePlus, faqe pacientësh të shërbimeve shëndetësore kombëtare)",
    "matje": "dokumentacioni i testit (LOINC) dhe një faqe pacienti që thotë çfarë mat testi",
    "proces": "tekst fiziologjie ose faqe pacienti (MedlinePlus, MeSH)",
    "shenjë": "faqe pacienti ose tekst klinik hyrës",
    "enzima": "faqe pacienti ose dokumentacion i testit (LOINC)",
}
DEFAULT_WHERE = "përkufizim në gjuhë të thjeshtë (MeSH, MedlinePlus) ose dokumentacion i testit (LOINC)"

PATTERN_DOMAIN = {
    "P01": "anemia", "P02": "anemia", "P03": "anemia",
    "P04": "diabeti", "P05": "veshkat", "P06": "mëlçia", "P07": "mëlçia",
    "P08": "tiroidja", "P09": "tiroidja", "P10": "inflamacioni ose infeksioni", "P11": "lipidet",
}
DIRECTION_SQ = {"decreased": "↓ ulët", "increased": "↑ lartë", "high": "↑ lartë", "low": "↓ ulët"}


def is_placeholder(source_ref: str) -> bool:
    return not source_ref.strip() or any(mark in source_ref for mark in PLACEHOLDER_MARKS)


def pending_terms():
    return [t for t in load_terminology() if is_placeholder(t.source_ref)]


def pending_patterns():
    return [p for p in load_patterns() if is_placeholder(p.source_ref)]


def describe_pattern(pattern) -> str:
    by_code = analytes_by_code()
    parts = []
    for code, direction in pattern.conditions:
        analyte = by_code.get(code)
        name = analyte.name_canonical_sq if analyte else code
        parts.append(f"{name} ({DIRECTION_SQ.get(direction, direction)})")
    return " + ".join(parts)


def build() -> str:
    terms, patterns = pending_terms(), pending_patterns()
    out = [
        "# Fletë pune: burimet që mungojnë",
        "",
        "*Gjeneruar nga `python scripts/build_source_worksheets.py`; mos e redaktoni këtu. Burimin e shkruani te kolona "
        "`source_ref` e `resources/terminology.csv` ose `resources/patterns.csv`, pastaj ekzekutoni skriptin sërish.*",
        "",
        "**Rregulla.** Shkruani vetëm burim që e keni lexuar dhe që e mbështet pohimin e kolonës «Pohimi». "
        "Nëse shpjegimi shqip është përkthimi juaj, thoni këtë te `source_ref`. Zërin që nuk e gjeni, fshijeni: "
        "termi bëhet «i pashpjeguar» (SP6), kombinimi hiqet. Asnjë citim nuk është shkruar këtu: rreshti «Ku të kërkohet» "
        "tregon lloje burimesh, jo burime.",
        "",
        f"Mbeten: **{len(terms)}** terma dhe **{len(patterns)}** kombinime.",
        "",
    ]

    out += ["## Kombinimet e analiteve", "",
            "Për secilin: një udhëzues ose standard i mjekësisë laboratorike që e lidh këtë kombinim me kërkesën që "
            "mjeku ta shohë (jo me diagnozë: SP1). Konfirmoni edhe shigjetat. Mentori ose një mjek duhet t'i rishikojë.",
            "",
            "| Kodi | Pohimi (kombinimi) | Fusha | Burimi i lexuar | Faqja ose seksioni |",
            "|---|---|---|---|---|"]
    for p in patterns:
        out.append(f"| {p.pattern_id} | {describe_pattern(p)} | {PATTERN_DOMAIN.get(p.pattern_id, '')} | | |")
    out.append("")

    by_category: dict[str, list] = {}
    for t in terms:
        by_category.setdefault(t.category or "tjetër", []).append(t)
    out += ["## Termat", ""]
    for category in sorted(by_category, key=lambda c: (-len(by_category[c]), c)):
        group = by_category[category]
        out += [f"### {category} ({len(group)})", "",
                f"Ku të kërkohet: {WHERE_TO_LOOK.get(category, DEFAULT_WHERE)}.", "",
                "| Termi | Pohimi (shpjegimi shqip) | Burimi i lexuar | Përkthim i imi? |",
                "|---|---|---|---|"]
        for t in sorted(group, key=lambda x: x.term):
            out.append(f"| {t.term} | {t.explanation_sq} | | |")
        out.append("")
    out += ["## Pas leximit",
            "",
            "1. Kontrolloni që asnjë shpjegim nuk përmban numër ose pohim diagnostik.",
            "2. Shkruani burimin te `source_ref`; ekzekutoni `python scripts/build_tables.py` dhe "
            "`python scripts/build_appendices.py` që T3, T5 dhe Shtojca A të pasqyrojnë burimet.",
            "3. Ekzekutoni `python -m pytest`: testet e terminologjisë dhe të kombinimeve do t'ju tregojnë nëse "
            "fshirja e një zëri prish diçka.",
            ""]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="build_source_worksheets")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--check", action="store_true", help="vetëm raporton sa burime mbeten")
    args = parser.parse_args(argv)

    terms, patterns = pending_terms(), pending_patterns()
    print(f"terma pa burim: {len(terms)} nga {len(load_terminology())}")
    print(f"kombinime pa burim: {len(patterns)} nga {len(load_patterns())}")
    if args.check:
        return 0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(build(), encoding="utf-8", newline="\n")
    print(f"shkruar {args.out.relative_to(ROOT) if ROOT in args.out.parents else args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
