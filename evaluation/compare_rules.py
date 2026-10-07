"""
Katalogu `r1.4` kundrejt `r1.3` mbi të njëjtat mostra (ADR 0021).

    python -m evaluation.compare_rules                    # shkruan evaluation/results/supplementary/rules_r14.json

"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from analyte.domain.enums import ProcessingState, ViolationType
from analyte.generation.templates import build as build_template
from analyte.verification.pipeline import verify
from ml import evaluate_rule_detector as e10
from ml.data.build_corruption_set import build_samples

from . import dataset as dataset_module
from . import kits, provenance
from .harness import build_pipeline
from .metrics import detector

AUDIT_DIR = Path("evaluation/cache/audit_e8")
OUT = Path("evaluation/results/supplementary/rules_r14.json")
VERSIONS = ("r1.3", "r1.4")
RULE_LABELS = {v.value for v in ViolationType}


def template_check(data) -> dict:
    out = {}
    for version in VERSIONS:
        bad = sum(
            1
            for case in data.cases
            if verify(case.truth, build_template(case.truth), rules=version).violations
        )
        out[version] = {"documents": len(data.cases), "documents_with_violations": bad}
    return out


def e10_test(n: int, seed: int) -> dict:
    documents = e10.corpus(n, seed)
    contexts = {doc_id: context for doc_id, context in documents}
    chosen = [s for s in build_samples(documents, seed=seed) if s.split == "test"]
    result = {}
    for version in VERSIONS:
        metrics = detector.measure(e10.judge(chosen, contexts, version))
        result[version] = {
            "samples": metrics["samples"],
            "macro_f1": metrics["macro_f1"],
            "micro": metrics["micro"],
            "false_alarms_on_clean": metrics["false_alarms_on_clean"],
        }
    return result


def kit_sets() -> dict:
    out = {}
    for version in VERSIONS:
        report = kits.check(rules=version)
        b = report["B"]
        out[version] = {
            "A_flagged": report["A"]["flagged"],
            "A_explanations": report["A"]["explanations"],
            "B_macro_f1": b["macro_f1"],
            "B_micro": b["micro"],
            "B_false_alarms_on_clean": b["false_alarms_on_clean"],
            "B_f1_by_type": {t: m.get("f1") for t, m in b["per_defect_type"].items()},
        }
    return out


def audit(data) -> dict:
    key = json.loads((AUDIT_DIR / "key.json").read_text(encoding="utf-8"))["items"]
    answers: dict[str, list] = {}
    for path in sorted(AUDIT_DIR.glob("answers_*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                answers[row["id"]] = row.get("problems", [])

    pipeline = build_pipeline("e8", data, "llm", ocr=True)  # kodi i ngrirë, siç u audituan
    rows = []
    for item_id, meta in sorted(key.items()):
        if meta["source"] != "generated":
            continue
        output = pipeline.run(data.cases[meta["document_index"]].document_input)
        if output.state is not ProcessingState.DELIVERED:
            continue
        flagged = {
            version: sorted(
                {
                    v.type.value
                    for v in verify(output.context, output.explanation, rules=version).violations
                }
            )
            for version in VERSIONS
        }
        audit_labels = sorted(
            {p["label"] for p in answers.get(item_id, []) if p["label"] in RULE_LABELS}
        )
        rows.append(
            {
                "id": item_id,
                "audit_rule_labels": audit_labels,
                "audit_any": bool(answers.get(item_id)),
                **flagged,
            }
        )

    with_problem = [r for r in rows if r["audit_rule_labels"]]
    clean = [r for r in rows if not r["audit_any"]]
    return {
        "texts": len(rows),
        "r1.3_flags": sum(bool(r["r1.3"]) for r in rows),
        "r1.4_flags": sum(bool(r["r1.4"]) for r in rows),
        "audit_rule_type_problem_texts": len(with_problem),
        "of_which_r1.4_flags": sum(bool(r["r1.4"]) for r in with_problem),
        "of_which_r1.4_flags_a_type_the_audit_named": sum(
            bool(set(r["audit_rule_labels"]) & set(r["r1.4"])) for r in with_problem
        ),
        "audit_clean_texts": len(clean),
        "r1.4_flags_among_audit_clean": sum(bool(r["r1.4"]) for r in clean),
        "r1.4_flag_types": dict(Counter(t for r in rows for t in r["r1.4"])),
        "per_text": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="evaluation.compare_rules")
    parser.add_argument("--dataset", type=Path, default=Path("data/v1"))
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--n", type=int, default=200, help="dokumente burimore për E10")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    data = dataset_module.load(args.dataset)
    report = {
        "what": "r1.4 kundrejt r1.3 mbi shabllonin, E10, grupet A dhe B, dhe auditin e E8 (ADR 0021)",
        "metadata": provenance.code_metadata("r1.3 dhe r1.4"),
        "template": template_check(data),
        "E10_test": e10_test(args.n, args.seed),
        "kits": kit_sets(),
        "audit_E8": audit(data),
        "note": (
            "r1.4 u hartua pasi u panë gabimet e grupeve A, B, të auditit dhe të E10: ato nuk janë më mostra të pastra për të. "
            "Numrat tregojnë sa kap defektet e njohura dhe sa mban pastërtinë e shabllonit, jo përgjithësimin."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    brief = {k: report[k] for k in ("template", "E10_test", "kits")}
    brief["audit_E8"] = {k: v for k, v in report["audit_E8"].items() if k != "per_text"}
    print(json.dumps(brief, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
