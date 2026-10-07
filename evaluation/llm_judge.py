"""
E12 — modeli gjuhësor si gjykatës (PK6): detektori i tretë.

    python -m evaluation.llm_judge --n 200 --split test      # E10 + grupi B

"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from analyte.domain.enums import ViolationType
from analyte.domain.models import GroundingContext
from analyte.domain.policy import RULE_BY_VIOLATION
from analyte.generation.llm import ProviderError
from analyte.generation.prompt import _findings, _terms
from evaluation import kits
from evaluation.metrics import detector
from evaluation.metrics.detector import Judgement

CLEAN = "clean"
JUDGE_VERSION = "j1"
LABELS = tuple(v.value for v in ViolationType)

SYSTEM = (
    "Ti je verifikues i shpjegimeve mjekësore në gjuhën shqipe. Merr një KONTEKST "
    "(e vërteta: vlerat laboratorike dhe pohimet e mjekut) dhe një SHPJEGIM për pacientin. "
    "Vendos nëse shpjegimi e shkel kontekstin. Shpjegimi ka më së shumti NJË shkelje.\n\n"
    "Llojet e shkeljeve:\n"
    + "\n".join(
        f"- {violation.value}: {rule.description_sq}"
        for violation, rule in RULE_BY_VIOLATION.items()
    )
    + '\n\nKthe vetëm një rresht JSON të formës {"label": "..."}, ku label është ose '
    f'një nga ({", ".join(LABELS)}), ose "{CLEAN}" nëse shpjegimi nuk e shkel kontekstin. '
    "Mos shpjego asgjë."
)

_LABEL = re.compile(r'"?label"?\s*[:=]\s*"?([a-z_]+)"?', re.IGNORECASE)


def judge_prompt(context: GroundingContext, text: str) -> tuple[str, str]:
    """Konteksti dhe teksti që gjykohet; asgjë tjetër."""
    blocks = ["KONTEKSTI", "Vlerat laboratorike:\n" + _findings(context)]
    if context.assertions:
        blocks.append(
            "Pohimet e mjekut:\n"
            + "\n".join(
                f"- {a.text_span} [polariteti: {a.polarity.value}; siguria: {a.certainty.value}; "
                f"lloji: {a.kind.value}]"
                for a in context.assertions
            )
        )
    terms = _terms(context)
    if terms:
        blocks.append("Termat:\n" + terms)
    if context.critical_findings():
        blocks.append("Ka vlera kritike: shpjegimi duhet t'i shfaqë.")
    blocks.append("SHPJEGIMI\n" + text)
    return SYSTEM, "\n\n".join(blocks)


def parse_label(answer: str) -> tuple[ViolationType | None, bool]:
    """(etiketa, a u lexua). `None` + `True` = `clean`; `None` + `False` = jo e lexueshme."""
    found = _LABEL.search(answer)
    token = found.group(1) if found else (answer.strip().split() or [""])[0]
    token = token.strip('"{}.,').lower()
    if token == CLEAN:
        return None, True
    if token in LABELS:
        return ViolationType(token), True
    return None, False


def judge_samples(
    client: Any, items: list[tuple[ViolationType | None, GroundingContext, str]]
) -> tuple[list[Judgement], int]:
    """Gjykimet mbi një listë mostrash, dhe sa përgjigje nuk u lexuan."""
    judgements: list[Judgement] = []
    unparsed = 0
    for actual, context, text in items:
        system, user = judge_prompt(context, text)
        try:
            answer = client.complete(system, user).text
        except ProviderError:
            # Këtu arrin vetëm një kërkesë e refuzuar ose një përgjigje e cunguar:
            # `StrictClient` e kthen `ProviderUnavailable` në `RunAborted` më herët.
            answer = ""
        label, parsed = parse_label(answer) if answer else (None, False)
        unparsed += 0 if parsed else 1
        judgements.append(Judgement(actual, label))
    return judgements, unparsed


def corruption_items(n: int, seed: int, split: str):
    from ml.data.build_corruption_set import build_samples
    from ml.evaluate_rule_detector import corpus

    documents = corpus(n, seed)
    contexts = {document_id: context for document_id, context in documents}
    samples = build_samples(documents, seed=seed)
    chosen = [s for s in samples if split == "all" or s.split == split]
    return [(s.defect, contexts[s.document_id], s.text) for s in chosen]


def kit_items():
    contexts = dict(kits.kit_contexts())
    rows = kits.read_rows(kits.KIT_DIR / "B_fjalite.csv", kits.B_COLUMNS, kits.B_OPTIONAL)
    items, errors = [], []
    for row in rows:
        try:
            context, text = kits.row_text(row, contexts)
        except ValueError as problem:
            errors.append({"id": row["id"], "reason": str(problem)})
            continue
        actual = None if row["etiketa"] == CLEAN else ViolationType(row["etiketa"])
        items.append((actual, context, text))
    return items, errors


def main(argv: list[str] | None = None) -> int:
    from analyte.config import get_settings
    from analyte.generation.llm import build_client
    from evaluation.harness import LLM_CACHE, RunAborted, StrictClient

    parser = argparse.ArgumentParser(prog="evaluation.llm_judge")
    parser.add_argument("--n", type=int, default=200, help="dokumente burimore (si te E10)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--split", default="test")
    parser.add_argument("--limit", type=int, default=None, help="vetëm për prova: mostrat e para")
    parser.add_argument("--only", choices=("corruption", "kit"), default=None)
    parser.add_argument("--out", type=Path, default=Path("evaluation/results/E12"))
    parser.add_argument("--llm-cache", type=Path, default=LLM_CACHE)
    args = parser.parse_args(argv)

    settings = get_settings()
    try:
        client = StrictClient(build_client(settings, role="judge", cache_dir=args.llm_cache))
    except ProviderError as error:
        raise SystemExit(f"E12: {error}") from None

    meta = {
        "experiment": "E12",
        "detector": "llm_judge",
        "judge_version": JUDGE_VERSION,
        "model": client.model,
        "provider": client.provider,
        "judge_equals_generator": (client.provider, client.model)
        == ((settings.llm_provider or "gemini"), settings.llm_model),
        "temperature": client.temperature,
        "thinking": client.thinking,
    }
    args.out.mkdir(parents=True, exist_ok=True)

    try:
        if args.only in (None, "corruption"):
            items = corruption_items(args.n, args.seed, args.split)[: args.limit]
            judgements, unparsed = judge_samples(client, items)
            result = {
                **meta,
                "samples": len(items),
                "split": args.split,
                "source_documents": args.n,
                "seed": args.seed,
                "unparsed": unparsed,
                "usage": client.usage.to_json(),
                "metrics": detector.measure(judgements),
            }
            (args.out / "result.json").write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            _print("korpusi i korruptuar", result)
        if args.only in (None, "kit"):
            items, errors = kit_items()
            items = items[: args.limit]
            judgements, unparsed = judge_samples(client, items)
            result = {
                **meta,
                "dataset": "kit-B",
                "samples": len(items),
                "errors": errors,
                "unparsed": unparsed,
                "usage": client.usage.to_json(),
                "authorship": "fjalitë e B i shkroi autori (sipas deklaratës së tij)",
                "metrics": detector.measure(judgements),
            }
            (args.out / "kit_B.json").write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            _print("grupi B", result)
    except RunAborted as stop:
        print(f"\nE12 u NDAL, nuk u vlerësua: {stop} ({client.usage.to_json()})", file=sys.stderr)
        return 2
    return 0


def _print(title: str, result: dict[str, Any]) -> None:
    metrics = result["metrics"]
    print(
        f"\n== {title}: mostra {result['samples']}, macro F1 {metrics['macro_f1']:.3f}, "
        f"të pastra të bllokuara {metrics['false_alarms_on_clean']}, të palexueshme {result['unparsed']}, "
        f"thirrje të reja {result['usage']['calls']} (cache {result['usage']['cache_hits']})"
    )
    for label, c in metrics["per_defect_type"].items():
        print(f"   {label:30} P={c['precision']} R={c['recall']} F1={c['f1']} (n={c['support']})")


if __name__ == "__main__":
    raise SystemExit(main())
