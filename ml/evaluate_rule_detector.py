"""
E10 — zbuluesi me rregulla mbi korpusin e korruptuar (PK6).

    python -m ml.evaluate_rule_detector --n 120

Ky është eksperimenti i parë i PK6 dhe i vetmi që mund të ekzekutohet pa
model gjuhësor: korpusi ndërtohet nga shablloni determinist, dhe defektet
injektohen prej nesh, prandaj etiketat janë të sigurta.

**Si kthehet një listë shkeljesh në një etiketë të vetme.** Një defekt i
vetëm mund të aktivizojë disa rregulla — një numër i ndryshuar mund të
prishë edhe drejtimin. Matrica e ngatërrimit kërkon një etiketë për
mostër, prandaj merret shkelja e parë sipas rendit të katalogut. Zgjedhja
është e dukshme dhe e njëanshme në të njëjtin drejtim për çdo mostër;
alternativa — të numërohej si sukses çdo përputhje e pjesshme — do ta
zbukuronte rezultatin pikërisht aty ku ai duhet të jetë i ashpër.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from analyte.catalog import RESOURCES_DIR
from analyte.domain.enums import ViolationType
from analyte.domain.policy import RULES_VERSION
from analyte.verification.pipeline import RULES, verify
from data_generator.generate import GENERATOR_VERSION, RESOURCE_FILES
from data_generator.ground_truth import build_document
from data_generator.ids import IdFactory
from evaluation import provenance
from evaluation.metrics import detector
from evaluation.metrics.detector import Judgement
from ml.data.build_corruption_set import Sample, build_samples, write

CATALOGUE_ORDER = [rule_id for rule_id, _ in RULES]


def corpus(count: int, seed: int) -> list[tuple[str, object]]:
    """Kontekstet burimore, të prodhuara nga gjeneruesi sintetik."""
    out = []
    for index in range(count):
        rng = random.Random(f"corruption-corpus/{seed}/{index}")
        document = build_document(rng, IdFactory(rng), scanned_share=0.0)
        out.append((str(document.document_id), document.context))
    return out


def corpus_version(count: int, seed: int) -> str:
    """Identifikuesi i korpusit të korruptuar: versioni i gjeneruesit, përmasat, fara dhe shuma e
    tabelave burimore (një tabelë tjetër analitesh prodhon korpus tjetër)."""
    sources = provenance.digest([RESOURCES_DIR / name for name in RESOURCE_FILES], length=8)
    return f"{GENERATOR_VERSION}/corruption/s{seed}/n{count}/{sources}"


def judge(samples: list[Sample], contexts: dict[str, object]) -> list[Judgement]:
    """Ekzekuton rregullat mbi çdo mostër dhe kthen çiftet e etiketave."""
    judgements = []
    for sample in samples:
        result = verify(contexts[sample.document_id], sample.text)
        judgements.append(Judgement(sample.defect, _single_label(result.violations)))
    return judgements


def _single_label(violations) -> ViolationType | None:
    if not violations:
        return None
    order = {kind: index for index, kind in enumerate(ViolationType)}
    return min((v.type for v in violations), key=lambda kind: order[kind])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ml.evaluate_rule_detector")
    parser.add_argument("--n", type=int, default=120, help="dokumente burimore")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--split", default="test", help="test | val | train | all")
    parser.add_argument("--out", type=Path, default=Path("evaluation/results/E10"))
    parser.add_argument("--dump", type=Path, default=None, help="ruaj korpusin si JSONL")
    args = parser.parse_args(argv)

    documents = corpus(args.n, args.seed)
    contexts = {document_id: context for document_id, context in documents}
    samples = build_samples(documents, seed=args.seed)
    if args.dump:
        write(samples, args.dump)

    chosen = [s for s in samples if args.split == "all" or s.split == args.split]
    metrics = detector.measure(judge(chosen, contexts))

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "result.json").write_text(
        json.dumps(
            {
                "experiment": "E10",
                "detector": "rules",
                "rules_version": RULES_VERSION,
                "samples": len(chosen),
                "split": args.split,
                "source_documents": args.n,
                "seed": args.seed,
                "metadata": provenance.metadata(
                    "E10",
                    {
                        "name": "corruption-corpus",
                        "version": corpus_version(args.n, args.seed),
                        "seed": args.seed,
                        "documents": args.n,
                        "split": args.split,
                    },
                ),
                "metrics": metrics,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"mostra: {len(chosen)} ({args.split})")
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
