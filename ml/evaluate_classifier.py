"""
E11 — klasifikuesi mbi grupin testues të E10 (PK6).

    python -m ml.evaluate_classifier --run ml/artifacts/runs/sentence

Lexon probabilitetet që prodhoi `train_classifier.py` në Colab dhe i kthen
në një etiketë për tekst, me të njëjtën metrikë si E10.

**Nga fjalitë te teksti.** Teksti merr etiketën e fjalisë me
probabilitetin më të lartë për një defekt, nëse ai kalon pragun; përndryshe
është i pastër. Kjo është e njëjta formë vendimi si te rregullat — një
etiketë për tekst — dhe e lejon krahasimin mostër për mostër.

**Pragu zgjidhet mbi validimin dhe vetëm atje.** Vlerat 0,30-0,95
provohen mbi tekstet e validimit; ajo me macro F1 më të lartë zbatohet e
pandryshuar mbi testin. Një prag i zgjedhur mbi testin do ta bënte E11 të
pakrahasueshëm me E10, ku rregullat nuk kanë asnjë parametër të akorduar.

**Rekomandimi i fshirë mbetet i padukshëm.** Ai nuk lë fjali për të
gjykuar, prandaj klasifikuesi i fjalisë ka mbulim zero mbi të nga ndërtimi,
jo nga dobësia. Numërohet në metrikë si i tillë, sepse testi është i
njëjtë me atë të E10, dhe shënohet veçmas në rezultat.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from analyte.domain.enums import ViolationType
from evaluation.metrics import detector
from evaluation.metrics.detector import Judgement

CLEAN = "clean"
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
        Judgement(as_type(row["label"]), as_type(text_label(row["probabilities"], labels, threshold)))
        for row in rows
    ]


def choose_threshold(rows: list[dict[str, Any]], labels: list[str]) -> tuple[float, dict]:
    """Pragu me macro F1 më të lartë mbi validimin; në barazim, më i ulëti."""
    scores = {}
    for threshold in THRESHOLDS:
        scores[threshold] = detector.measure(judge(rows, labels, threshold))["macro_f1"] or 0.0
    best = max(THRESHOLDS, key=lambda t: (scores[t], -t))
    return best, scores


def evaluate(run_dir: Path) -> dict[str, Any]:
    run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    labels = run["labels"]
    val = read_jsonl(run_dir / "predictions_val.jsonl")
    test = read_jsonl(run_dir / "predictions_test.jsonl")

    threshold, val_scores = choose_threshold(val, labels)
    metrics = detector.measure(judge(test, labels, threshold))
    return {
        "experiment": "E11",
        "detector": "classifier",
        "input": run["input"],
        "model": run["model"],
        "threshold": threshold,
        "threshold_chosen_on": "val",
        "val_macro_f1_by_threshold": {str(t): round(s, 4) for t, s in val_scores.items()},
        "samples": len(test),
        "structurally_invisible": [ViolationType.OMITTED_RECOMMENDATION.value],
        "run": {k: v for k, v in run.items() if k != "labels"},
        "metrics": metrics,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ml.evaluate_classifier")
    parser.add_argument("--run", type=Path, required=True, help="dosja e një ekzekutimi nga Colab")
    parser.add_argument("--out", type=Path, default=Path("evaluation/results/E11"))
    args = parser.parse_args(argv)

    result = evaluate(args.run)
    out = args.out / result["input"]
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    metrics = result["metrics"]
    print(f"hyrja: {result['input']}   pragu (nga validimi): {result['threshold']}")
    print(f"mostra: {result['samples']} (test)")
    print(f"macro F1: {metrics['macro_f1']}")
    print(f"alarme të rreme mbi tekst të pastër: {metrics['false_alarms_on_clean']}")
    print("\nsipas llojit të defektit:")
    for label, counts in metrics["per_defect_type"].items():
        print(
            f"  {label:32} P={counts['precision']} R={counts['recall']} "
            f"F1={counts['f1']} (n={counts['support']})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
