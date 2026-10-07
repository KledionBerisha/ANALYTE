"""
Kontrolli i besueshmërisë i OCR-së: çfarë ndryshon mbi 168 dokumentet e skanuara (ADR 0020).

    python -m evaluation.ocr_guard_report                 # shkruan evaluation/results/supplementary/ocr_guard.json

"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from analyte.domain.enums import AnalyteStatus
from analyte.grounding.branch_a.extract import extract

from . import dataset as dataset_module
from . import provenance
from .harness import build_ocr
from .pipeline import _read_pages

OUT = Path("evaluation/results/supplementary/ocr_guard.json")
CRITICAL_HIGH = AnalyteStatus.CRITICAL_HIGH


def _tally(results, truth_by_doc) -> dict:
    wrong = 0
    false_critical = 0
    to_uninterpretable = 0
    rows = 0
    wrong_values = 0
    for doc, extraction in results.items():
        truth = {f.analyte_code: f for f in truth_by_doc[doc].findings}
        for finding in extraction.findings:
            reference = truth.get(finding.analyte_code)
            if reference is None:
                continue
            rows += 1
            if finding.value != reference.value:
                wrong_values += 1
            if finding.status is AnalyteStatus.UNINTERPRETABLE:
                if reference.status is not AnalyteStatus.UNINTERPRETABLE:
                    to_uninterpretable += 1
            elif finding.status is not reference.status:
                wrong += 1
                if finding.status is CRITICAL_HIGH and reference.status is not CRITICAL_HIGH:
                    false_critical += 1
    return {
        "matched_rows": rows,
        "wrong_values_in_matched_rows": wrong_values,
        "wrong_interpreted_status": wrong,
        "false_critical_high": false_critical,
        "interpretable_became_uninterpretable": to_uninterpretable,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="evaluation.ocr_guard_report")
    parser.add_argument("--dataset", type=Path, default=Path("data/v1"))
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument(
        "--limit", type=int, default=None, help="kufizo numrin e dokumenteve të skanuara"
    )
    args = parser.parse_args(argv)

    data = dataset_module.load(args.dataset)
    engine = build_ocr(True)
    scanned = [case for case in data.cases if case.is_scanned][: args.limit]

    plain, guarded, corrections, rejected_by_guard = {}, {}, Counter(), []
    truth_by_doc = {}
    for case in scanned:
        pages, failure = _read_pages(case.document_input, engine)
        if failure is not None:
            continue
        doc = str(case.document_id)
        truth_by_doc[doc] = case.truth
        plain[doc] = extract(pages, ocr_guard=False)
        guarded[doc] = extract(pages, ocr_guard=True)
        corrections[doc] = len(guarded[doc].corrections)
        kept = {f.analyte_code for f in guarded[doc].findings}
        truth = {f.analyte_code: f for f in case.truth.findings}
        for finding in plain[doc].findings:
            if finding.analyte_code not in kept and finding.analyte_code in truth:
                rejected_by_guard.append(
                    {
                        "read_value": str(finding.value),
                        "true_value": str(truth[finding.analyte_code].value),
                        "correct_value": finding.value == truth[finding.analyte_code].value,
                    }
                )

    before, after = _tally(plain, truth_by_doc), _tally(guarded, truth_by_doc)
    report = {
        "what": "kontrolli i besueshmërisë i OCR-së (ADR 0020), mbi dokumentet e skanuara të korpusit",
        "metadata": provenance.code_metadata(),
        "scanned_documents": len(truth_by_doc),
        "without_guard": before,
        "with_guard": after,
        "rows_rejected_by_value_check": len(rejected_by_guard),
        "of_which_the_read_value_was_correct": sum(r["correct_value"] for r in rejected_by_guard),
        "intervals_replaced_by_table": sum(corrections.values()),
        "documents_with_a_correction": sum(1 for n in corrections.values() if n),
        "note": (
            "Kontrolli u projektua pasi u panë gabimet e E3 mbi këto dokumente; numrat tregojnë sa e kap defektin e njohur, "
            "jo përgjithësimin. Dokumentet janë sintetike me OCR të simuluar nga skanimi; nuk ka dokumente reale."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "without_guard",
                    "with_guard",
                    "rows_rejected_by_value_check",
                    "of_which_the_read_value_was_correct",
                    "intervals_replaced_by_table",
                )
            },
            ensure_ascii=False,
            indent=1,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
