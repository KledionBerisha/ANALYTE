"""
E12 me gjykatës Claude, pa API: mostrat dalin në skedarë, gjykohen nga subagjentë, kthehen si etiketa.

    python -m evaluation.judge_batches export DIR --key KEY.json
    # subagjentët lexojnë DIR/instructions.md dhe një DIR/chunk_NN.json, shkruajnë DIR/answers_NN.jsonl
    python -m evaluation.judge_batches ingest DIR --key KEY.json --model "<si u thirr>"

Ekziston sepse gjykatësi me API kërkon një ofrues me kuotë, dhe asnjë i falas nuk
e mbulon E12 mirë. Gjykatës është një model Claude i thirrur nga Claude Code si
subagjent: një përdorim i abonimit, jo i një çelësi API.

**Çfarë sheh gjykatësi.** Të njëjtat mostra si te `evaluation.llm_judge` (192 tekste të
E10 dhe 105 rreshta të B), të njëjtën kërkesë (`judge_prompt`: konteksti, teksti dhe
përkufizimet e katalogut), dhe po atë format përgjigjeje. Skedarët e batch-eve
**nuk përmbajnë etiketat e vërteta**: ato janë te `--key`, jashtë dosjes që lexon
gjykatësi, dhe e vërteta bashkohet vetëm te `ingest`. Mostrat përzihen me farë të
fiksuar, që asnjë batch të mos jetë një lloj i vetëm defekti.

**Kufizime që duhen raportuar.** (1) Temperatura dhe mostrimi nuk fiksohen: i njëjti
ekzekutim nuk garantohet të japë të njëjtat etiketa; prandaj çdo përgjigje ruhet te
`answers_*.jsonl` dhe vlerësimi rillogaritet prej tyre. (2) Gjykatësi është po ai
asistent që ndihmoi ta ndërtojë sistemin; nuk është i pavarur prej tij. (3) Skedari i
etiketave është në të njëjtin disk: mbrohet nga udhëzimi, jo nga një ndarje teknike.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from analyte.domain.enums import ViolationType

from .llm_judge import (
    CLEAN,
    JUDGE_VERSION,
    LABELS,
    SYSTEM,
    corruption_items,
    judge_prompt,
    kit_items,
    parse_label,
)
from .metrics import detector
from .metrics.detector import Judgement

SHUFFLE_SEED = 7
CHUNK_SIZE = 20


@dataclass(frozen=True, slots=True)
class Item:
    id: str
    source: str  # "E10" ose "B"
    actual: ViolationType | None
    user: str


def build_items(n: int = 200, seed: int = 42, split: str = "test") -> list[Item]:
    """Të gjitha mostrat, me identifikues të qëndrueshëm: E10-000…, B-000…."""
    items: list[Item] = []
    for index, (actual, context, text) in enumerate(corruption_items(n, seed, split)):
        items.append(Item(f"E10-{index:03d}", "E10", actual, judge_prompt(context, text)[1]))
    rows, _errors = kit_items()
    for index, (actual, context, text) in enumerate(rows):
        items.append(Item(f"B-{index:03d}", "B", actual, judge_prompt(context, text)[1]))
    return items


def instructions() -> str:
    return (
        "# Detyra e gjykatësit\n\n"
        "Gjyko një grup shpjegimesh sipas udhëzimeve më poshtë. Mos hap asnjë skedar tjetër "
        "përveç `instructions.md` dhe skedarit tënd `chunk_NN.json`, dhe mos kërko etiketa: gjykimi "
        "duhet të vijë vetëm nga konteksti dhe teksti që të jepen.\n\n"
        "Çdo element i `items` ka `id` dhe `user` (konteksti dhe shpjegimi që gjykohet). Për çdo "
        "element, vendos një etiketë sipas udhëzimeve të sistemit.\n\n"
        "## Udhëzimet e sistemit\n\n"
        f"{SYSTEM}\n\n"
        "## Si ta kthesh\n\n"
        "Shkruaj skedarin `answers_NN.jsonl` (NN si te chunk-u yt), një rresht JSON për element:\n\n"
        '    {"id": "…", "label": "…"}\n\n'
        f"`label` është një nga ({', '.join(LABELS)}) ose `{CLEAN}`. Një rresht për çdo `id`, asnjë tjetër, "
        "pa shpjegime në skedar.\n"
    )


def export(directory: Path, key_path: Path, *, n: int = 200, seed: int = 42, split: str = "test",
           chunk_size: int = CHUNK_SIZE) -> dict[str, Any]:
    items = build_items(n, seed, split)
    order = list(range(len(items)))
    random.Random(SHUFFLE_SEED).shuffle(order)

    directory.mkdir(parents=True, exist_ok=True)
    (directory / "instructions.md").write_text(instructions(), encoding="utf-8")
    chunks = [order[i : i + chunk_size] for i in range(0, len(order), chunk_size)]
    for number, indexes in enumerate(chunks):
        payload = {"chunk": number, "items": [{"id": items[i].id, "user": items[i].user} for i in indexes]}
        (directory / f"chunk_{number:02d}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8"
        )

    key = {
        "judge_version": JUDGE_VERSION,
        "shuffle_seed": SHUFFLE_SEED,
        "order": [items[i].id for i in range(len(items))],
        "actual": {i.id: (i.actual.value if i.actual else CLEAN) for i in items},
        "source": {i.id: i.source for i in items},
        "user_sha256": {i.id: hashlib.sha256(i.user.encode("utf-8")).hexdigest() for i in items},
    }
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_text(json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")
    manifest = {
        "judge_version": JUDGE_VERSION,
        "items": len(items),
        "chunks": len(chunks),
        "chunk_size": chunk_size,
        "shuffle_seed": SHUFFLE_SEED,
        "sources": {s: sum(1 for i in items if i.source == s) for s in ("E10", "B")},
    }
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    return manifest


def read_answers(directory: Path) -> tuple[dict[str, str], list[str]]:
    """id → përgjigja e papërpunuar (e fundit fiton), dhe problemet e gjetura."""
    answers: dict[str, str] = {}
    problems: list[str] = []
    for path in sorted(directory.glob("answers_*.jsonl")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                answers[str(record["id"])] = str(record["label"])
            except (ValueError, KeyError, TypeError):
                problems.append(f"{path.name}:{number}: rresht i palexueshëm")
    return answers, problems


def ingest(directory: Path, key_path: Path, *, model: str) -> dict[str, dict[str, Any]]:
    key = json.loads(key_path.read_text(encoding="utf-8"))
    answers, problems = read_answers(directory)
    unknown = sorted(set(answers) - set(key["actual"]))
    if unknown:
        raise ValueError(f"identifikues të panjohur te përgjigjet: {unknown[:5]}")

    judgements: dict[str, list[Judgement]] = {"E10": [], "B": []}
    unparsed = {"E10": 0, "B": 0}
    missing = {"E10": [], "B": []}
    for item_id in key["order"]:
        source = key["source"][item_id]
        actual_raw = key["actual"][item_id]
        actual = None if actual_raw == CLEAN else ViolationType(actual_raw)
        raw = answers.get(item_id)
        if raw is None:
            missing[source].append(item_id)
            predicted, parsed = None, False
        else:
            predicted, parsed = parse_label(json.dumps({"label": raw}))
        unparsed[source] += 0 if parsed else 1
        judgements[source].append(Judgement(actual, predicted))

    meta = {
        "experiment": "E12",
        "detector": "llm_judge",
        "judge_version": key["judge_version"],
        "judge": "claude-subagent",
        "model": model,
        "temperature": "nuk fiksohet (subagjent)",
        "judge_equals_generator": False,
        "answer_problems": problems,
        "note": "gjykatësi është asistenti që ndihmoi ta ndërtojë sistemin; përgjigjet janë te answers_*.jsonl",
    }
    result = {}
    for source, name in (("E10", "result"), ("B", "kit_B")):
        result[name] = {
            **meta,
            "samples": len(judgements[source]),
            "unparsed": unparsed[source],
            "missing": missing[source],
            "metrics": detector.measure(judgements[source]),
        }
    result["result"].update({"split": "test", "dataset": "corruption-test"})
    result["kit_B"].update(
        {"dataset": "kit-B", "authorship": "fjalitë e B i shkroi autori (sipas deklaratës së tij)"}
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="evaluation.judge_batches")
    parser.add_argument("command", choices=("export", "ingest"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--key", type=Path, required=True)
    parser.add_argument("--model", default="", help="si u thirr gjykatësi (për ingest)")
    parser.add_argument("--out", type=Path, default=Path("evaluation/results/E12"))
    args = parser.parse_args(argv)

    if args.command == "export":
        manifest = export(args.directory, args.key)
        print(json.dumps(manifest))
        return 0

    if not args.model:
        raise SystemExit("--model është i detyrueshëm: rezultati duhet të thotë kush gjykoi")
    results = ingest(args.directory, args.key, model=args.model)
    args.out.mkdir(parents=True, exist_ok=True)
    for name, payload in results.items():
        (args.out / f"{name}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        m = payload["metrics"]
        print(
            f"{name}: mostra {payload['samples']}, macro F1 {m['macro_f1']:.3f}, të pastra të bllokuara "
            f"{m['false_alarms_on_clean']}, të palexueshme {payload['unparsed']}, të munguara {len(payload['missing'])}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
