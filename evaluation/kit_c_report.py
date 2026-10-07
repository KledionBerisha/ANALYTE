"""
Grupi C: Dega B mbi fjali të shkruara nga autori, e ndarë sipas llojit të fjalisë.

    python -m evaluation.kit_c_report                # shkruan evaluation/results/supplementary/kit_C.json

"""

from __future__ import annotations

import glob
import json
import re
import sys
from pathlib import Path
from typing import Any

from analyte.grounding.branch_a import loinc
from analyte.grounding.branch_b.assertions import extract_assertions

from . import kits

C_PATH = kits.KIT_DIR / "C_narrativa.csv"
FIELDS = ("lloji", "polariteti", "siguria", "analiti", "drejtimi")
GROUPS = (
    ("negacione të thjeshta", 1, 15),
    ("pseudo-negacione", 16, 25),
    ("me rezervë", 26, 35),
    ("rekomandime", 36, 45),
    ("pohime të drejtpërdrejta", 46, 60),
)


def _norm(text: str) -> str:
    return re.sub(r"[^\w ]", "", text.lower()).strip()


def generator_sentences(corpus: Path = Path("data/v1")) -> set[str] | None:
    """Fjalitë që gjeneruesi prodhon, ose `None` kur korpusi nuk është i ndërtuar."""
    files = glob.glob(str(corpus / "documents" / "*.json"))
    if not files:
        return None
    sentences: set[str] = set()
    for path in files:
        record = json.loads(Path(path).read_text(encoding="utf-8"))
        text = record.get("narrative_text") or record.get("truth", {}).get("narrative_text", "")
        for sentence in re.split(r"(?<=[.!?])\s+", text or ""):
            if sentence.strip():
                sentences.add(_norm(sentence))
    contexts = kits.KIT_DIR / "A_kontekstet.md"
    if contexts.exists():
        for quote in re.findall(r"- “([^”]+)”", contexts.read_text(encoding="utf-8")):
            sentences.add(_norm(quote))
    return sentences


def _predict(sentence: str) -> dict[str, str]:
    found = extract_assertions(sentence)
    got = found[0] if found else None
    if got is None:
        return dict.fromkeys(FIELDS, "asnjë")
    return {
        "lloji": got.kind.value,
        "polariteti": got.polarity.value,
        "siguria": got.certainty.value,
        "analiti": got.analyte_code or "",
        "drejtimi": got.direction.value,
    }


def _expected(row: dict[str, str]) -> dict[str, str]:
    code = loinc.resolve(row["analiti"]) if row["analiti"] else ""
    return {**{f: row[f] for f in FIELDS}, "analiti": code or ""}


def build_report(path: Path = C_PATH, corpus: Path = Path("data/v1")) -> dict[str, Any]:
    rows = kits.read_rows(path, kits.C_COLUMNS)
    generator = generator_sentences(corpus)
    records = []
    for row in rows:
        expected, predicted = _expected(row), _predict(row["fjalia"])
        records.append(
            {
                "id": row["id"],
                "sentence": row["fjalia"],
                "identical_to_generator": None
                if generator is None
                else _norm(row["fjalia"]) in generator,
                "expected": expected,
                "predicted": predicted,
                "all_correct": all(expected[f] == predicted[f] for f in FIELDS),
                "extracted": predicted["lloji"] != "asnjë",
            }
        )

    def summarise(subset: list[dict[str, Any]]) -> dict[str, Any]:
        n = len(subset)
        return {
            "rows": n,
            "all_correct": sum(r["all_correct"] for r in subset),
            "extracted": sum(r["extracted"] for r in subset),
            "per_field": {
                f: sum(r["expected"][f] == r["predicted"][f] for r in subset) for f in FIELDS
            },
        }

    by_group = {
        name: summarise([r for r in records if lo <= int(r["id"][1:]) <= hi])
        for name, lo, hi in GROUPS
    }
    report: dict[str, Any] = {
        "experiment": "kit-C",
        "answers": "Dega B (nxjerrja e pohimeve) mbi fjali të shkruara nga autori",
        "authorship": "fjalitë e C i shkroi autori (sipas deklaratës së tij)",
        "all": summarise(records),
        "by_group": by_group,
        "failures": [r for r in records if not r["all_correct"]],
    }
    if generator is not None:
        identical = [r for r in records if r["identical_to_generator"]]
        report["identical_to_generator"] = [r["id"] for r in identical]
        report["not_identical"] = summarise([r for r in records if not r["identical_to_generator"]])
        report["identical"] = summarise(identical)
    return report


def main(argv: list[str] | None = None) -> int:
    out = Path("evaluation/results/supplementary/kit_C.json")
    report = build_report()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    total = report["all"]
    print(
        f"rreshta {total['rows']}: të gjitha fushat saktë {total['all_correct']}, nxjerrë fare {total['extracted']}"
    )
    for name, group in report["by_group"].items():
        print(
            f"  {name:28} {group['all_correct']}/{group['rows']} saktë, nxjerrë {group['extracted']}/{group['rows']}"
        )
    if "not_identical" in report:
        n = report["not_identical"]
        print(
            f"identike me gjeneruesin: {len(report['identical_to_generator'])}; "
            f"jo identike: {n['all_correct']}/{n['rows']} saktë"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
