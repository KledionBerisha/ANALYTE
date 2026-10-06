"""
E8 dhe E9 mbi fjalitë e TEKSTIT TË DORËZUAR, krahas emëruesit të harness-it.

    python -m evaluation.delivered_denominator --out evaluation/results/supplementary/e8_e9_delivered_denominator.json

Harness-i numëron fjalitë e të gjitha drafteve të modelit (edhe të ndaluarave) dhe jo tekstin e shabllonit që u dorëzua në vend të tyre,
ndërsa shkeljet që arrijnë te përdoruesi janë ato të tekstit të dorëzuar. Ky modul i rekordon të dyja: ekzekuton E8 dhe E9 nga cache-i i modelit
(pa thirrje të reja; klienti i refuzon) dhe numëron fjalitë dhe shkeljet e `explain().text`.

Totali i harness-it duhet të dalë i njëjtë me rezultatin e ngrirë (8 892 fjali dhe 0 shkelje te E8; 10 359 dhe 41 te E9); nëse dallon, kodi ka
ndryshuar dhe numrat nuk janë të krahasueshëm. Ekzekutohet me kodin e ngrirë: pa kontroll OCR dhe me `r1.3`.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from analyte.domain.policy import LEGACY_RULES_VERSION, RULES_VERSIONS
from analyte.orchestration import process

from . import dataset as dataset_module
from . import harness, provenance
from .metrics.base import count_sentences

OUT = Path("evaluation/results/supplementary/e8_e9_delivered_denominator.json")


def run(dataset: Path, classifier: Path, rules: str = LEGACY_RULES_VERSION, ocr_guard: bool = False, with_e9: bool = True) -> dict:
    records: list[dict] = []
    real_explain = process.explain

    def spy(context, generator, **kwargs):
        explanation = real_explain(context, generator, **kwargs)
        records.append(
            {
                "delivery": explanation.delivery.value,
                "sentences": count_sentences(explanation.text),
                "violations": len(explanation.verification.violations) if explanation.verification else 0,
                "draft_sentences": sum(count_sentences(a.text) for a in explanation.attempts if a.text),
            }
        )
        return explanation

    process.explain = spy
    data = dataset_module.load(dataset)
    summary: dict = {}
    try:
        for name in ("e8", "e9") if with_e9 else ("e8",):
            records.clear()
            pipeline = harness.build_pipeline(
                name, data, "llm", True, classifier if name == "e9" else None, ocr_guard=ocr_guard, rules=rules
            )
            result = harness.run_experiment(harness.registry.get(name.upper()), data, pipeline)
            by = {"generated": [0, 0, 0], "template": [0, 0, 0]}
            for record in records:
                row = by[record["delivery"]]
                row[0] += 1
                row[1] += record["sentences"]
                row[2] += record["violations"]
            delivered = sum(v[1] for v in by.values())
            violations = sum(v[2] for v in by.values())
            client = harness._llm_client(pipeline)
            summary[name.upper()] = {
                "documents": len(records),
                "by_delivery": {k: {"documents": v[0], "sentences": v[1], "violations": v[2]} for k, v in by.items()},
                "delivered_sentences": delivered,
                "violations_in_delivered_text": violations,
                "rate_per_100_delivered_sentences": round(100 * violations / delivered, 4) if delivered else None,
                "rule_of_three_per_100_delivered": round(300 / delivered, 4) if violations == 0 and delivered else None,
                "template_share_of_delivered_sentences": round(by["template"][1] / delivered, 4) if delivered else None,
                "draft_sentences_all_attempts": sum(r["draft_sentences"] for r in records),
                "harness_sentences": result.metrics["sentences"],
                "harness_violations_reaching_user": result.metrics["violations_reaching_user"],
                "new_model_calls": client.usage.to_json() if client is not None else None,
            }
    finally:
        process.explain = real_explain
    generated = summary["E8"]["by_delivery"]["generated"]["sentences"]
    summary["E8"]["model_text_only"] = {
        "sentences": generated,
        "violations": summary["E8"]["by_delivery"]["generated"]["violations"],
        "rule_of_three_per_100": round(300 / generated, 4) if generated else None,
    }
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="evaluation.delivered_denominator")
    parser.add_argument("--dataset", type=Path, default=Path("data/v1"))
    parser.add_argument("--classifier", type=Path, default=Path("ml/artifacts/runs/sentence"))
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--rules", default=LEGACY_RULES_VERSION, choices=RULES_VERSIONS)
    parser.add_argument("--ocr-guard", action="store_true")
    parser.add_argument("--no-e9", action="store_true", help="vetëm E8 (E9 kërkon peshat e klasifikuesit)")
    args = parser.parse_args(argv)

    summary = run(args.dataset, args.classifier, args.rules, args.ocr_guard, not args.no_e9)
    report = {
        "what": "E8 dhe E9 mbi fjalitë e tekstit të dorëzuar (modeli ose shablloni rezervë), krahas emëruesit të harness-it",
        "metadata": provenance.code_metadata(args.rules),
        **summary,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("E8", "E9") if k in report}, ensure_ascii=False)[:1400])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
