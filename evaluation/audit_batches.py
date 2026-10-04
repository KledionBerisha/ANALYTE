"""
Auditi i pavarur i tekstit që arriti te përdoruesi në E8 (PK5): a ka gabime që rregullat nuk i shohin?

    python -m evaluation.audit_batches collect DIR --key KEY.json      # mostra nga E8 (nga cache)
    # subagjentët lexojnë DIR/instructions.md dhe një DIR/chunk_NN.json, shkruajnë DIR/answers_NN.jsonl
    python -m evaluation.audit_batches ingest DIR --key KEY.json --model "<si u thirr>"

**Pse ekziston.** Metrika e PK5 numëron shkeljet me të njëjtat rregulla që e bllokojnë tekstin.
"0 shkelje arrijnë te përdoruesi" do të thotë pra "asnjë që rregullat e shohin", jo "asnjë gabim".
Ky audit e mat atë që mbetet: një gjykatës lexon tekstin e dorëzuar kundrejt kontekstit dhe liston çdo
problem, përfshirë `other_unsupported` — një pohim që nuk është te konteksti dhe që asnjë rregull nuk e
kontrollon (njohuri mjekësore e shtuar, qetësim, këshillë, shpjegim i një testi).

**Mostra.** Nga 500 dokumentet e E8: 90 tekste të gjeneruara që kaluan verifikimin (të ndara
proporcionalisht dixhital/skanuar, me farë të fiksuar) dhe 10 shabllone rezervë si kontroll. Teksti i
shabllonit është i bazuar nga ndërtimi; nëse gjykatësi gjen "probleme" aty, ato janë gabimet e vetë
gjykatësit ose të kontekstit të nxjerrë.

**Kufizime.** Gjykatësi është modeli Claude (subagjent, pa temperaturë të fiksuar) dhe nuk ka të vërtetë
bazë për këtë pyetje; mostra është 100 tekste. Vlerësimi është një kufi i poshtëm i gabimeve që rregullat
humbin, jo një normë e matur me saktësi. Çdo përgjigje ruhet dhe çdo "problem" ka një citat që mund të
kontrollohet me dorë.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from analyte.domain.enums import ProcessingState, ViolationType
from analyte.domain.models import GroundingContext
from analyte.domain.policy import RULE_BY_VIOLATION

from .llm_judge import judge_prompt

SAMPLE_SEED = 11
GENERATED_N = 90
TEMPLATE_N = 10
CHUNK_SIZE = 20
OTHER = "other_unsupported"
LABELS = tuple(v.value for v in ViolationType) + (OTHER,)

SYSTEM = (
    "Ti auditon shpjegime mjekësore në gjuhën shqipe që do t'i shfaqen pacientit. Merr një KONTEKST "
    "(e vërteta: vlerat laboratorike dhe pohimet e mjekut) dhe një SHPJEGIM. Gjej ÇDO problem në "
    "shpjegim kundrejt kontekstit. Mund të ketë zero, një ose disa.\n\nLlojet e problemeve:\n"
    + "\n".join(f"- {v.value}: {r.description_sq}" for v, r in RULE_BY_VIOLATION.items())
    + f"\n- {OTHER}: një pohim që nuk jepet te konteksti dhe që nuk është një nga llojet e mësipërme — "
    "njohuri mjekësore e shtuar (p.sh. çfarë bën një test ose një qelizë), interpretim, qetësim ose "
    "alarmim ('nuk është e rrezikshme'), këshillë, krahasim me të tjerë, apo çdo informacion tjetër "
    "që pacienti nuk e merr nga konteksti.\n\n"
    "Mos e quaj problem: tekstet e detyrueshme të sistemit (njoftimi për vlera kritike, shënimi "
    "përmbyllës, njoftimi që një term ose vlerë nuk shpjegohet), citimet e mjekut me parashtesën "
    "'Mjeku ka shënuar:' kur përputhen me pohimet e dhëna, dhe shpjegimet e termave që jepen te "
    "konteksti (edhe riformuluar pa shtuar asgjë).\n\n"
    "Për çdo element, kthe një rresht JSON: {\"id\": \"...\", \"problems\": [{\"label\": \"...\", "
    "\"quote\": \"fjalët e shpjegimit që e shkaktojnë, deri në 15 fjalë\"}]}. `problems` është [] "
    "kur shpjegimi nuk ka asnjë problem."
)


def collect(directory: Path, key_path: Path) -> dict[str, Any]:
    """Mostra nga E8 (me cache-in e modelit), pa thirrje të reja."""
    from evaluation import dataset as ds
    from evaluation.harness import build_pipeline
    from analyte.generation import templates

    data = ds.load(Path("data/v1"))
    pipeline = build_pipeline("e8", data, "llm", ocr=True)
    generated, fallback = [], []
    for index, case in enumerate(data.cases):
        output = pipeline.run(case.document_input)
        if output.state is ProcessingState.DELIVERED:
            generated.append((index, case.channel, "generated", output.explanation, output.context))
        elif output.state is ProcessingState.TEMPLATE_FALLBACK:
            fallback.append(
                (index, case.channel, "template", templates.build(output.context), output.context)
            )
    usage = pipeline.generator.client.usage.to_json()

    rng = random.Random(SAMPLE_SEED)
    by_channel: dict[str, list] = {"digital": [], "scanned": []}
    for row in generated:
        by_channel[row[1]].append(row)
    share = len(by_channel["scanned"]) / max(len(generated), 1)
    scanned_n = round(GENERATED_N * share)
    chosen = rng.sample(by_channel["scanned"], scanned_n) + rng.sample(
        by_channel["digital"], GENERATED_N - scanned_n
    )
    chosen += rng.sample(fallback, TEMPLATE_N)
    rng.shuffle(chosen)

    directory.mkdir(parents=True, exist_ok=True)
    key = {"items": {}, "sample_seed": SAMPLE_SEED}
    chunks: list[list[dict[str, str]]] = []
    for number, (index, channel, source, text, context) in enumerate(chosen):
        item_id = f"A-{number:03d}"
        key["items"][item_id] = {"document_index": index, "channel": channel, "source": source}
        if number % CHUNK_SIZE == 0:
            chunks.append([])
        chunks[-1].append({"id": item_id, "user": judge_prompt(context, text)[1]})
    for number, items in enumerate(chunks):
        (directory / f"chunk_{number:02d}.json").write_text(
            json.dumps({"chunk": number, "items": items}, ensure_ascii=False, indent=1), encoding="utf-8"
        )
    (directory / "instructions.md").write_text(instructions(), encoding="utf-8")
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_text(json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")
    summary = {
        "documents": len(data.cases),
        "generated_delivered": len(generated),
        "template_fallbacks": len(fallback),
        "sampled": len(chosen),
        "chunks": len(chunks),
        "llm_calls_made": usage["calls"],
    }
    (directory / "manifest.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    return summary


def instructions() -> str:
    return (
        "# Detyra e auditorit\n\n"
        "Audito një grup shpjegimesh sipas udhëzimeve më poshtë. Mos hap asnjë skedar tjetër përveç "
        "`instructions.md` dhe skedarit tënd `chunk_NN.json`. Gjykimi duhet të vijë vetëm nga konteksti "
        "dhe teksti që të jepen.\n\n"
        "Çdo element i `items` ka `id` dhe `user` (konteksti dhe shpjegimi që auditohet).\n\n"
        f"## Udhëzimet\n\n{SYSTEM}\n\n"
        "## Si ta kthesh\n\nShkruaj `answers_NN.jsonl` (NN si te chunk-u yt): një rresht JSON për çdo `id`, "
        "pa asnjë rresht tjetër. `label` është një nga "
        f"({', '.join(LABELS)}).\n"
    )


def ingest(directory: Path, key_path: Path, *, model: str) -> dict[str, Any]:
    key = json.loads(key_path.read_text(encoding="utf-8"))
    answers: dict[str, list[dict[str, str]]] = {}
    bad: list[str] = []
    for path in sorted(directory.glob("answers_*.jsonl")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                answers[str(record["id"])] = [
                    {"label": str(p["label"]), "quote": str(p.get("quote", ""))}
                    for p in record.get("problems", [])
                ]
            except (ValueError, KeyError, TypeError):
                bad.append(f"{path.name}:{number}")
    unknown = sorted(set(answers) - set(key["items"]))
    if unknown:
        raise ValueError(f"identifikues të panjohur: {unknown[:5]}")

    def summarise(source: str | None, channel: str | None = None) -> dict[str, Any]:
        ids = [
            i for i, meta in key["items"].items()
            if (source is None or meta["source"] == source) and (channel is None or meta["channel"] == channel)
        ]
        answered = [i for i in ids if i in answers]
        with_problem = [i for i in answered if answers[i]]
        labels = Counter(p["label"] for i in answered for p in answers[i])
        rule_visible = sum(c for l, c in labels.items() if l != OTHER and l in {v.value for v in ViolationType})
        return {
            "items": len(ids),
            "answered": len(answered),
            "missing": [i for i in ids if i not in answers],
            "texts_with_problem": len(with_problem),
            "share_with_problem": round(len(with_problem) / len(answered), 4) if answered else None,
            "problems_by_label": dict(labels.most_common()),
            "texts_only_other_unsupported": sum(
                1 for i in with_problem if all(p["label"] == OTHER for p in answers[i])
            ),
            "problems_of_rule_types": rule_visible,
        }

    return {
        "experiment": "audit-E8",
        "judge": "claude-subagent",
        "model": model,
        "sample_seed": key["sample_seed"],
        "unreadable_lines": bad,
        "generated_passed_verification": summarise("generated"),
        "generated_digital": summarise("generated", "digital"),
        "generated_scanned": summarise("generated", "scanned"),
        "template_fallback_control": summarise("template"),
        "answers": answers,
        "note": "kufi i poshtëm i gabimeve që rregullat humbin; gjykatësi është asistenti që ndihmoi ta ndërtojë sistemin",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="evaluation.audit_batches")
    parser.add_argument("command", choices=("collect", "ingest"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--key", type=Path, required=True)
    parser.add_argument("--model", default="")
    parser.add_argument("--out", type=Path, default=Path("evaluation/results/llm/AUDIT_E8"))
    args = parser.parse_args(argv)

    if args.command == "collect":
        print(json.dumps(collect(args.directory, args.key)))
        return 0
    if not args.model:
        raise SystemExit("--model është i detyrueshëm")
    result = ingest(args.directory, args.key, model=args.model)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for name in ("generated_passed_verification", "generated_digital", "generated_scanned", "template_fallback_control"):
        s = result[name]
        print(f"{name}: {s['texts_with_problem']}/{s['answered']} tekste me problem ({s['share_with_problem']}), {s['problems_by_label']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
