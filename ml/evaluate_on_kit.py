"""
E11 mbi grupin B — klasifikuesi mbi fjali të shkruara jashtë gjeneruesit (PK6).

    python -m ml.evaluate_on_kit --run ml/artifacts/runs/sentence
    python -m ml.evaluate_on_kit --run ml/artifacts/runs/context

"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from analyte.domain.enums import ViolationType
from analyte.textnorm import sentences as split_sentences
from analyte.verification.classifier import serialize_context
from evaluation import kits
from evaluation.metrics import detector
from evaluation.metrics.detector import Judgement
from ml import evaluate_classifier

CLEAN = "clean"


def judge_rows(
    rows: list[dict[str, str]],
    contexts: dict[str, Any],
    predict,
    labels: list[str],
    thresholds: dict[str, float],
) -> tuple[dict[str, list[Judgement]], list[kits.RowError]]:
    """Një gjykim për çdo prag, mbi të njëjtat probabilitete (llogariten një herë)."""
    out: dict[str, list[Judgement]] = {name: [] for name in thresholds}
    errors: list[kits.RowError] = []
    for row in rows:
        try:
            context, text = kits.row_text(row, contexts)
        except ValueError as problem:
            errors.append(kits.RowError(row["id"], str(problem)))
            continue
        probabilities = predict(
            [s for s, _, _ in split_sentences(text)], serialize_context(context)
        )
        actual = None if row["etiketa"] == CLEAN else ViolationType(row["etiketa"])
        for name, threshold in thresholds.items():
            label = evaluate_classifier.text_label(probabilities, labels, threshold)
            out[name].append(Judgement(actual, None if label == CLEAN else ViolationType(label)))
    return out, errors


def evaluate(run_dir: Path, results_dir: Path = Path("evaluation/results/E11")) -> dict[str, Any]:
    from analyte.verification.classifier import TransformersPredictor

    predictor = TransformersPredictor(run_dir)
    e11 = json.loads((results_dir / predictor.mode / "result.json").read_text(encoding="utf-8"))
    thresholds = {
        name: point["threshold"]
        for name, point in e11["operating_points"].items()
        if point is not None
    }
    rows = kits.read_rows(kits.KIT_DIR / "B_fjalite.csv", kits.B_COLUMNS, kits.B_OPTIONAL)
    judgements, errors = judge_rows(
        rows, dict(kits.kit_contexts()), predictor, list(predictor.labels), thresholds
    )
    return {
        "experiment": "E11",
        "dataset": "kit-B",
        "input": predictor.mode,
        "model": e11["run"]["model"],
        "thresholds_from": f"E11/{predictor.mode}/result.json (zgjedhur mbi validimin)",
        "samples": len(rows) - len(errors),
        "errors": [{"id": e.row_id, "reason": e.reason} for e in errors],
        "authorship": "fjalitë e B i shkroi autori (sipas deklaratës së tij)",
        "operating_points": {
            name: {"threshold": thresholds[name], "metrics": detector.measure(judgements[name])}
            for name in thresholds
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ml.evaluate_on_kit")
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("evaluation/results/E11"))
    args = parser.parse_args(argv)

    result = evaluate(args.run, args.out)
    target = args.out / result["input"] / "kit_B.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        f"hyrja: {result['input']}   mostra B: {result['samples']}   gabime rreshtash: {len(result['errors'])}"
    )
    for name, point in result["operating_points"].items():
        m = point["metrics"]
        print(
            f"\n== {name}  pragu {point['threshold']}   macro F1 {m['macro_f1']:.3f}   "
            f"të pastra të bllokuara {m['false_alarms_on_clean']}/30"
        )
        for label, c in m["per_defect_type"].items():
            print(
                f"   {label:30} P={c['precision']} R={c['recall']} F1={c['f1']} (n={c['support']})"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
