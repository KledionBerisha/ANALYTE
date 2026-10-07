"""
Kontrolli i rrjedhjes për klasifikuesin e Fazës 7.

    python -m ml.leakage --data ml/artifacts/classifier_data

"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from analyte.catalog import analytes_by_code, load_terminology

CLEAN = "clean"
SHORTCUT_LABEL_SHARE = 0.5
SHORTCUT_CLEAN_SHARE = 0.01

_DIGITS = re.compile(r"\d+(?:[.,]\d+)?")


def _vocabulary() -> list[tuple[re.Pattern[str], str]]:
    names = set()
    for analyte in analytes_by_code().values():
        names |= {analyte.name_canonical_sq, *analyte.variants}
    terms = set()
    for term in load_terminology():
        terms |= set(term.surface_forms())
    ordered = sorted(((n, "‹A›") for n in names), key=lambda x: -len(x[0]))
    ordered += sorted(((t, "‹T›") for t in terms), key=lambda x: -len(x[0]))
    return [
        (re.compile(rf"(?<!\w){re.escape(s)}(?!\w)", re.IGNORECASE), mark) for s, mark in ordered
    ]


def skeleton(sentence: str, vocabulary: list[tuple[re.Pattern[str], str]]) -> str:
    """Forma e fjalisë pa numra, pa emra analitesh dhe pa terma."""
    text = _DIGITS.sub("‹N›", sentence)
    for pattern, mark in vocabulary:
        text = pattern.sub(mark, text)
    return " ".join(text.casefold().split())


def _prefix(sentence: str) -> str:
    return " ".join(sentence.casefold().split()[:2])


def report(train: list[dict[str, Any]], val: list[dict[str, Any]]) -> dict[str, Any]:
    vocabulary = _vocabulary()
    train_documents = {row["document_id"] for row in train}
    val_documents = {row["document_id"] for row in val}

    seen = {skeleton(row["sentence"], vocabulary) for row in train}
    overlap: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for row in val:
        counts = overlap[row["label"]]
        counts[0] += skeleton(row["sentence"], vocabulary) in seen
        counts[1] += 1

    by_label: dict[str, Counter[str]] = defaultdict(Counter)
    for row in train:
        by_label[row["label"]][_prefix(row["sentence"])] += 1
    clean_total = sum(by_label[CLEAN].values()) or 1

    shortcuts = {}
    for label, prefixes in sorted(by_label.items()):
        if label == CLEAN:
            continue
        prefix, count = prefixes.most_common(1)[0]
        label_share = count / sum(prefixes.values())
        clean_share = by_label[CLEAN][prefix] / clean_total
        shortcuts[label] = {
            "prefix": prefix,
            "share_of_label": round(label_share, 3),
            "share_of_clean": round(clean_share, 4),
            "is_shortcut": label_share >= SHORTCUT_LABEL_SHARE
            and clean_share <= SHORTCUT_CLEAN_SHARE,
        }

    return {
        "shared_documents": len(train_documents & val_documents),
        "val_skeleton_seen_in_train": {
            label: {"seen": s, "total": t, "share": round(s / t, 3)}
            for label, (s, t) in sorted(overlap.items())
        },
        "shortcuts": shortcuts,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ml.leakage")
    parser.add_argument("--data", type=Path, default=Path("ml/artifacts/classifier_data"))
    parser.add_argument("--out", type=Path, default=Path("evaluation/results/E11/leakage.json"))
    args = parser.parse_args(argv)

    def read(name: str) -> list[dict[str, Any]]:
        with (args.data / name).open(encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    result = report(read("train.jsonl"), read("val.jsonl"))
    result["data_meta"] = json.loads((args.data / "meta.json").read_text(encoding="utf-8"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"dokumente të përbashkëta trajnim/validim: {result['shared_documents']}")
    print("\nskeleti i validimit i parë në trajnim:")
    for label, row in result["val_skeleton_seen_in_train"].items():
        print(f"  {label:24} {row['share']:.3f} ({row['seen']}/{row['total']})")
    print("\nfillimi më i shpeshtë për çdo lloj:")
    for label, row in result["shortcuts"].items():
        flag = "  ← SHKURTORE" if row["is_shortcut"] else ""
        print(
            f"  {label:24} “{row['prefix']}” {row['share_of_label']:.2f} e llojit, "
            f"{row['share_of_clean']:.4f} e të pastrave{flag}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
