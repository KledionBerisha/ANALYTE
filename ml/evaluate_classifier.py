"""
E11 — klasifikuesi mbi grupin testues të E10 (PK6).

    python -m ml.evaluate_classifier --run ml/artifacts/runs/sentence

"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from analyte.domain.enums import ViolationType
from evaluation import provenance
from evaluation.metrics import detector
from evaluation.metrics.detector import Judgement

CLEAN = "clean"
FALSE_ALARM_BUDGET = 0.05
"""Pjesa më e madhe e teksteve të pastra të validimit që lejohet të bllokohet
(vendim i autorit, 2026-09-30)."""
THRESHOLDS = tuple(round(0.30 + 0.05 * step, 2) for step in range(14))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def text_label(probabilities: list[list[float]], labels: list[str], threshold: float) -> str:
    """Etiketa e tekstit nga probabilitetet e fjalive të tij."""
    clean = labels.index(CLEAN)
    best_label, best_p = CLEAN, threshold
    for row in probabilities:
        for index, p in enumerate(row):
            if index != clean and p >= best_p:
                best_label, best_p = labels[index], p
    return best_label


def judge(rows: list[dict[str, Any]], labels: list[str], threshold: float) -> list[Judgement]:
    def as_type(label: str) -> ViolationType | None:
        return None if label == CLEAN else ViolationType(label)

    return [
        Judgement(
            as_type(row["label"]), as_type(text_label(row["probabilities"], labels, threshold))
        )
        for row in rows
    ]


def validation_curve(
    rows: list[dict[str, Any]], labels: list[str]
) -> dict[float, dict[str, float]]:
    """Për çdo prag: macro F1 mbi llojet e defektit dhe pjesa e teksteve të pastra
    që bllokohen. Të dyja rregullat e zgjedhjes lexojnë të njëjtën kurbë."""
    clean_texts = sum(1 for row in rows if row["label"] == CLEAN)
    curve = {}
    for threshold in THRESHOLDS:
        measured = detector.measure(judge(rows, labels, threshold))
        curve[threshold] = {
            "macro_f1": measured["macro_f1"] or 0.0,
            "false_alarm_rate": (
                measured["false_alarms_on_clean"] / clean_texts if clean_texts else 0.0
            ),
        }
    return curve


def choose_threshold(rows: list[dict[str, Any]], labels: list[str]) -> tuple[float, dict]:
    """Pragu me macro F1 më të lartë mbi validimin; në barazim, më i ulëti."""
    curve = validation_curve(rows, labels)
    best = max(THRESHOLDS, key=lambda t: (curve[t]["macro_f1"], -t))
    return best, {t: point["macro_f1"] for t, point in curve.items()}


def choose_within_budget(curve: dict[float, dict[str, float]], budget: float) -> float | None:
    """Pragu me macro F1 më të lartë ndër ata që bllokojnë jo më shumë se `budget`
    të teksteve të pastra; në barazim, më i ulëti. `None` nëse asnjë s'e plotëson."""
    eligible = [t for t, point in curve.items() if point["false_alarm_rate"] <= budget]
    return max(eligible, key=lambda t: (curve[t]["macro_f1"], -t)) if eligible else None


def _point(
    rule: str, threshold: float, curve: dict, test: list[dict[str, Any]], labels: list[str]
) -> dict[str, Any]:
    metrics = detector.measure(judge(test, labels, threshold))
    clean_texts = sum(1 for row in test if row["label"] == CLEAN)
    return {
        "rule": rule,
        "threshold": threshold,
        "chosen_on": "val",
        "val": {k: round(v, 4) for k, v in curve[threshold].items()},
        "test_false_alarm_rate": (
            round(metrics["false_alarms_on_clean"] / clean_texts, 4) if clean_texts else None
        ),
        "metrics": metrics,
    }


def evaluate(run_dir: Path, budget: float = FALSE_ALARM_BUDGET) -> dict[str, Any]:
    run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    labels = run["labels"]
    val = read_jsonl(run_dir / "predictions_val.jsonl")
    test = read_jsonl(run_dir / "predictions_test.jsonl")

    curve = validation_curve(val, labels)
    best, _ = choose_threshold(val, labels)
    within = choose_within_budget(curve, budget)
    budgeted = None
    if within is not None:
        budgeted = {**_point("false_alarm_budget", within, curve, test, labels), "budget": budget}
    points = {
        "max_macro_f1": _point("max_macro_f1", best, curve, test, labels),
        "false_alarm_budget": budgeted,
    }
    deployed = "false_alarm_budget" if budgeted else None
    return {
        "experiment": "E11",
        "detector": "classifier",
        "input": run["input"],
        "model": run["model"],
        "samples": len(test),
        "test_clean_texts": sum(1 for row in test if row["label"] == CLEAN),
        "val_clean_texts": sum(1 for row in val if row["label"] == CLEAN),
        "structurally_invisible": [ViolationType.OMITTED_RECOMMENDATION.value],
        "false_alarm_budget": budget,
        "operating_points": points,
        "deployed": deployed,
        "deployed_threshold": budgeted["threshold"] if budgeted else None,
        "val_by_threshold": {
            str(t): {k: round(v, 4) for k, v in point.items()} for t, point in curve.items()
        },
        "run": {k: v for k, v in run.items() if k != "labels"},
        "metadata": provenance.metadata(
            "E11",
            {
                # hyrja janë parashikimet e Colab-it; ato identifikohen me shumën e skedarëve që u lexuan
                "name": f"colab-run/{run['input']}",
                "version": "sha256:"
                + provenance.digest(
                    [
                        run_dir / "run.json",
                        run_dir / "predictions_val.jsonl",
                        run_dir / "predictions_test.jsonl",
                    ]
                ),
                "documents": len(test),
            },
        ),
    }


def _report(point: dict[str, Any] | None, title: str, clean_texts: int) -> None:
    print(f"\n== {title}")
    if point is None:
        print("   asnjë prag nuk e plotëson buxhetin")
        return
    metrics = point["metrics"]
    print(
        f"   pragu {point['threshold']}   validim: macro F1 {point['val']['macro_f1']}, "
        f"{point['val']['false_alarm_rate']:.0%} e të pastrave të bllokuara"
    )
    print(
        f"   TEST: macro F1 {metrics['macro_f1']:.4f}   "
        f"të pastra të bllokuara {metrics['false_alarms_on_clean']}/{clean_texts}"
    )
    for label, counts in metrics["per_defect_type"].items():
        print(
            f"     {label:30} P={counts['precision']} R={counts['recall']} "
            f"F1={counts['f1']} (n={counts['support']})"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ml.evaluate_classifier")
    parser.add_argument("--run", type=Path, required=True, help="dosja e një ekzekutimi nga Colab")
    parser.add_argument("--out", type=Path, default=Path("evaluation/results/E11"))
    parser.add_argument(
        "--false-alarm-budget",
        type=float,
        default=FALSE_ALARM_BUDGET,
        help="pjesa e teksteve të pastra të validimit që lejohet të bllokohet",
    )
    args = parser.parse_args(argv)

    result = evaluate(args.run, args.false_alarm_budget)
    out = args.out / result["input"]
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(
        f"hyrja: {result['input']}   mostra: {result['samples']} (test)   "
        f"buxheti i alarmeve të rreme: {args.false_alarm_budget:.0%}"
    )
    points = result["operating_points"]
    _report(points["max_macro_f1"], "rregulli 1: macro F1 më i lartë", result["test_clean_texts"])
    _report(points["false_alarm_budget"], "rregulli 2: brenda buxhetit", result["test_clean_texts"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
