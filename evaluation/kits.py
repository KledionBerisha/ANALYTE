"""
Shembujt e shkruar me dorë: përgatitja dhe matja e tyre.

    python -m evaluation.kits build     # shkruan kontekstet dhe skeletet
    python -m evaluation.kits check     # mat atë që është plotësuar

Korpusi sintetik dhe korpusi i korruptuar dalin nga shabllonet e sistemit, dhe
çdo zbulues i shkruar me ato shabllone para syve mat kryesisht sa mirë i
mban mend ato. Tri grupet këtu shkruhen nga autori, me fjalët e veta, dhe
janë e vetmja lëndë e punimit që nuk ka kaluar nëpër gjenerues:

  - **A — shpjegime referuese.** 25 kontekste të fiksuara, secili me
    shpjegimin që autori do t'i jepte pacientit. Shërbejnë si pikë
    krahasimi për testin e modelit gjuhësor në shqip, dhe që sot si matja
    e vetme e alarmeve të rreme të rregullave mbi prozë të natyrshme.
  - **B — fjali me defekt.** Fjali të daljes, secila me një defekt të
    vetëm ose asnjë, të shkruara për kontekstet e A-së. Grupi testues i
    PK6 që nuk rrjedh nga korruptuesit e sistemit.
  - **C — narrativë mjeku.** Fjali raporti me etiketat e tyre — polariteti,
    siguria, lloji, analiti, drejtimi. Matja e Degës B jashtë fjalorit të
    gjeneruesit.

Kontekstet e A-së janë të shkurtuara: dokumenti sintetik mbart deri në
njëzet analite, dhe njëzet e pesë shpjegime të tilla do të ishin punë
javësh. Shkurtimi ruan gjetjet jonormale, kritike dhe pa interval, ato që
mjeku i përmend, dhe dy normale; krahasimi i kryqëzuar dhe kombinimet
rindërtohen mbi gjetjet që mbetën.
"""

from __future__ import annotations

import argparse
import csv
import random
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from analyte.domain.enums import (
    AnalyteStatus,
    AssertionKind,
    Certainty,
    Direction,
    Polarity,
    ViolationType,
)
from analyte.domain.models import GroundingContext
from analyte.domain.policy import ATTRIBUTION_PREFIX_SQ, DISCLAIMER_SQ, sentence_local_violations
from analyte.generation.templates import build as build_template
from analyte.grounding.branch_a import loinc
from analyte.grounding.branch_a.patterns import detect as detect_patterns
from analyte.grounding.branch_b.assertions import extract_assertions
from analyte.grounding.branch_b.crossref import build_cross_references
from analyte.verification.pipeline import verify

KIT_DIR = Path(__file__).resolve().parent / "handwritten"
CONTEXT_COUNT = 25
MAX_FINDINGS = 7
NORMAL_KEPT = 2

B_COLUMNS = ("id", "konteksti", "fjalia", "etiketa", "shenim")
B_OPTIONAL = ("burimi",)
"""Kolona e pëlqyer, e detyrueshme vetëm për `polarity_flip` dhe `hedge_removed`:
fjala e saktë e pohimit të mjekut që fjalia e zëvendëson (shih `check_sentences`)."""

REPLACES_SOURCE_QUOTE = frozenset({ViolationType.POLARITY_FLIP, ViolationType.HEDGE_REMOVED})
C_COLUMNS = ("id", "fjalia", "lloji", "polariteti", "siguria", "analiti", "drejtimi", "shenim")

B_LABELS: tuple[str, ...] = ("clean",) + tuple(
    kind.value for kind in ViolationType if kind in sentence_local_violations()
)
"""Vetëm shkeljet e vendosshme nga një fjali: mungesat (R4, R8) nuk
shkruhen dot si fjali."""

STATUS_SQ = {
    AnalyteStatus.CRITICAL_LOW: "kritike e ulët",
    AnalyteStatus.LOW: "e ulët",
    AnalyteStatus.NORMAL: "normale",
    AnalyteStatus.HIGH: "e lartë",
    AnalyteStatus.CRITICAL_HIGH: "kritike e lartë",
    AnalyteStatus.UNINTERPRETABLE: "pa interval — nuk interpretohet (SP5)",
}


# --------------------------------------------------------------------
# Kontekstet e A-së
# --------------------------------------------------------------------


@lru_cache(maxsize=1)
def kit_contexts() -> tuple[tuple[str, GroundingContext], ...]:
    """25 kontekste të fiksuara, të zgjedhura që të mbulojnë çdo rast.

    Zgjedhja është lakmitare dhe deterministe: dokumenti merret kur shton
    diçka që grupi ende nuk e ka në sasinë e kërkuar. Të njëjtat 25 dalin
    në çdo ekzekutim, që shpjegimet e autorit të mbeten të lidhura me
    kontekstin e vet.
    """
    from data_generator.ground_truth import build_document
    from data_generator.ids import IdFactory

    wanted = {
        "critical": 5,
        "uninterpretable": 5,
        "negated": 8,
        "hedged": 6,
        "recommendation": 8,
        "unexplained": 5,
        "pattern": 3,
    }
    have = dict.fromkeys(wanted, 0)
    chosen: list[GroundingContext] = []
    spare: list[GroundingContext] = []

    for index in range(3000):
        satisfied = all(have[key] >= wanted[key] for key in wanted)
        if len(chosen) == CONTEXT_COUNT or (
            satisfied and len(chosen) + len(spare) >= CONTEXT_COUNT
        ):
            break
        rng = random.Random(f"kit-A/{index}")
        context = _trim(build_document(rng, IdFactory(rng), scanned_share=0.0).context)
        if context.is_empty():
            continue
        features = _features(context)
        if any(features[key] and have[key] < wanted[key] for key in wanted):
            chosen.append(context)
            for key in wanted:
                have[key] += bool(features[key])
        elif len(spare) < CONTEXT_COUNT:
            spare.append(context)

    chosen += spare[: CONTEXT_COUNT - len(chosen)]
    return tuple((f"A{number:02d}", context) for number, context in enumerate(chosen, start=1))


def _features(context: GroundingContext) -> dict[str, bool]:
    assertions = context.assertions
    return {
        "critical": bool(context.critical_findings()),
        "uninterpretable": any(f.status is AnalyteStatus.UNINTERPRETABLE for f in context.findings),
        "negated": any(a.polarity is Polarity.NEGATED for a in assertions),
        "hedged": any(a.certainty is Certainty.HEDGED for a in assertions),
        "recommendation": any(a.kind is AssertionKind.RECOMMENDATION for a in assertions),
        "unexplained": bool(context.unexplained_terms),
        "pattern": bool(context.patterns),
    }


def _trim(context: GroundingContext) -> GroundingContext:
    """Konteksti me gjetjet që kanë diçka për të thënë, dhe pak normale."""
    mentioned = {a.analyte_code for a in context.assertions if a.analyte_code}

    def priority(finding) -> int:
        if finding.status.is_critical:
            return 0
        if finding.status is AnalyteStatus.UNINTERPRETABLE:
            return 1
        if finding.analyte_code in mentioned:
            return 2
        if finding.status.is_abnormal:
            return 3
        return 4

    unusual = [f for f in context.findings if priority(f) < 4]
    normal = [f for f in context.findings if priority(f) == 4][:NORMAL_KEPT]
    kept_ids = {f.id for f in sorted(unusual, key=priority)[: MAX_FINDINGS - len(normal)] + normal}
    findings = tuple(f for f in context.findings if f.id in kept_ids)

    return GroundingContext(
        document_id=context.document_id,
        findings=findings,
        assertions=context.assertions,
        cross_refs=build_cross_references(findings, context.assertions),
        glossary=context.glossary,
        unexplained_terms=context.unexplained_terms,
        patterns=detect_patterns(findings),
    )


def render_contexts(contexts: tuple[tuple[str, GroundingContext], ...]) -> str:
    """Kontekstet si fletë leximi për autorin."""
    lines = [
        "<!-- E gjeneruar nga `python -m evaluation.kits build`. Mos e ndrysho me dorë. -->",
        "",
        "# Kontekstet e grupit A",
        "",
        "Secili kontekst është gjithçka që do të shihte modeli gjuhësor. Shpjegimi",
        "juaj shkon te `A_shpjegimet.md`, nën të njëjtin identifikues.",
        "",
    ]
    for kit_id, context in contexts:
        lines += [f"## {kit_id}", "", "| Analiti | Vlera | Intervali | Statusi |", "|---|---|---|---|"]
        for f in context.findings:
            interval = "—"
            if f.ref_low is not None and f.ref_high is not None:
                interval = f"{f.ref_low} – {f.ref_high}"
            elif f.ref_high is not None:
                interval = f"deri {f.ref_high}"
            elif f.ref_low is not None:
                interval = f"nga {f.ref_low}"
            lines.append(
                f"| {f.analyte_name_canonical} | {f.value_canonical} {f.unit_canonical} "
                f"| {interval} | {STATUS_SQ[f.status]} |"
            )
        lines.append("")

        names = {f.id: f.analyte_name_canonical for f in context.findings}
        for pattern in context.patterns:
            joined = " + ".join(names[i] for i in pattern.finding_ids)
            lines.append(f"- **Kombinim ({pattern.pattern_id}):** {joined}")
        if context.assertions:
            lines += ["", "**Mjeku ka shkruar:**", ""]
            for a in context.assertions:
                marks = []
                if a.polarity is Polarity.NEGATED:
                    marks.append("mohim")
                if a.certainty is Certainty.HEDGED:
                    marks.append("me rezervë")
                if a.kind is AssertionKind.RECOMMENDATION:
                    marks.append("rekomandim")
                suffix = f" *({', '.join(marks)})*" if marks else ""
                lines.append(f"- “{a.text_span}”{suffix}")
        if context.glossary:
            lines += ["", "**Terma që lejohen të shpjegohen:**", ""]
            lines += [f"- {e.term} — {e.explanation_sq}" for e in context.glossary]
        if context.unexplained_terms:
            lines += ["", "**Terma që nuk shpjegohen (SP6):** " + ", ".join(context.unexplained_terms)]
        lines += ["", "---", ""]
    return "\n".join(lines)


def skeleton_explanations(contexts: tuple[tuple[str, GroundingContext], ...]) -> str:
    lines = [
        "# Shpjegimet referuese — grupi A",
        "",
        "Shkruani nën çdo titull shpjegimin që do t'i jepnit pacientit. Mos e",
        "fshini titullin; teksti nën të lexohet deri te titulli tjetër.",
        "",
    ]
    for kit_id, _ in contexts:
        lines += [f"## {kit_id}", "", ""]
    return "\n".join(lines)


# --------------------------------------------------------------------
# Leximi i asaj që shkroi autori
# --------------------------------------------------------------------


HEADING = re.compile(r"^##\s+(A\d\d)\s*$", re.MULTILINE)


def read_explanations(path: Path) -> dict[str, str]:
    """Shpjegimet e plotësuara; titujt bosh anashkalohen."""
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    parts = HEADING.split(text)
    out = {}
    for kit_id, body in zip(parts[1::2], parts[2::2]):
        body = " ".join(body.split())
        if body:
            out[kit_id] = body
    return out


def read_rows(
    path: Path, columns: tuple[str, ...], optional: tuple[str, ...] = ()
) -> list[dict[str, str]]:
    """Rreshtat e plotësuar të një CSV-je; rreshtat pa fjali anashkalohen.

    `optional` janë kolona që mund të mungojnë: rreshtat i marrin bosh.

    `utf-8-sig`: Excel dhe disa redaktorë e ruajnë "UTF-8" me një shenjë në fillim
    të skedarit (BOM). Pa këtë, emri i kolonës së parë lexohej si `﻿id` dhe
    skedari refuzohej me "mungon kolona id", ndërsa përmbajtja ishte e saktë."""
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = set(columns) - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"{path.name}: mungojnë kolonat {sorted(missing)}")
        return [
            {key: (row.get(key) or "").strip() for key in (*columns, *optional)}
            for row in reader
            if (row.get("fjalia") or "").strip()
        ]


# --------------------------------------------------------------------
# Matja
# --------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RowError:
    """Një rresht që nuk u mat dot, me arsyen."""

    row_id: str
    reason: str


def check_explanations(
    explanations: dict[str, str], contexts: dict[str, GroundingContext]
) -> dict[str, Any]:
    """Rregullat mbi shpjegimet e autorit: çdo shkelje është alarm i rremë
    ose gabim i autorit, dhe të dyja duhen parë me sy."""
    report = {}
    for kit_id, text in sorted(explanations.items()):
        result = verify(contexts[kit_id], text)
        report[kit_id] = [
            {"type": v.type.value, "sentence": v.sentence, "evidence": v.evidence}
            for v in result.violations
        ]
    flagged = sum(1 for violations in report.values() if violations)
    return {
        "explanations": len(report),
        "flagged": flagged,
        "false_alarm_share": flagged / len(report) if report else None,
        "by_explanation": report,
    }


def check_sentences(
    rows: list[dict[str, str]], contexts: dict[str, GroundingContext]
) -> tuple[dict[str, Any], list[RowError]]:
    """PK6 mbi fjalitë e B-së.

    Fjalia futet te shablloni i kontekstit të vet, para shënimit përmbyllës,
    ashtu si korruptuesit e E10. Shablloni kalon çdo rregull, prandaj çdo
    shkelje e gjetur vjen nga fjalia.

    **Përjashtim: `polarity_flip` dhe `hedge_removed` zëvendësojnë citimin.**
    Shablloni i mban tashmë citimet e sakta të mjekut, dhe R5/R6 gjykojnë
    citimin e parë që përputhet. Një citim i përmbysur i shtuar në fund do të
    ishte i dyti, kurrë i gjykuar, dhe matja do të tregonte zero për një arsye
    që s'ka të bëjë me aftësinë e rregullit. Ashtu si te korruptuesit e E10,
    fjalia zëvendëson citimin burimor — fjalën e të cilit e jep kolona `burimi`.
    """
    from evaluation.metrics import detector
    from evaluation.metrics.detector import Judgement
    from ml.evaluate_rule_detector import _single_label

    judgements, errors = [], []
    for row in rows:
        try:
            context, text = row_text(row, contexts)
        except ValueError as problem:
            errors.append(RowError(row["id"], str(problem)))
            continue
        actual = None if row["etiketa"] == "clean" else ViolationType(row["etiketa"])
        judgements.append(Judgement(actual, _single_label(verify(context, text).violations)))

    return detector.measure(judgements), errors


def row_text(
    row: dict[str, str], contexts: dict[str, GroundingContext]
) -> tuple[GroundingContext, str]:
    """Konteksti i një rreshti B dhe teksti i plotë ku fjalia e tij është futur.

    Të dy vlerësuesit — rregullat këtu dhe klasifikuesi te `ml/evaluate_on_kit.py` —
    gjykojnë të njëjtin tekst, prandaj ndërtimi i tij jetë një funksion i vetëm.
    Hedh `ValueError` me arsyen nëse rreshti nuk mund të matet.
    """
    context = contexts.get(row["konteksti"])
    if context is None:
        raise ValueError(f"konteksti '{row['konteksti']}' nuk ekziston")
    if row["etiketa"] not in B_LABELS:
        raise ValueError(f"etiketë e panjohur '{row['etiketa']}'")
    clean = build_template(context)
    sentence = row["fjalia"].rstrip(".") + "."
    actual = None if row["etiketa"] == "clean" else ViolationType(row["etiketa"])
    if actual in REPLACES_SOURCE_QUOTE:
        source = f"{ATTRIBUTION_PREFIX_SQ} {row.get('burimi', '')}."
        if not row.get("burimi"):
            raise ValueError("mungon `burimi`: citimi që zëvendësohet")
        if source not in clean:
            raise ValueError(f"`burimi` nuk është citim i kontekstit: {source!r}")
        return context, clean.replace(source, sentence, 1)
    return context, clean.replace(DISCLAIMER_SQ, f"{sentence} {DISCLAIMER_SQ}")


def check_narrative(rows: list[dict[str, str]]) -> tuple[dict[str, Any], list[RowError]]:
    """Dega B mbi fjalitë e C-së, fushë për fushë."""
    fields = ("lloji", "polariteti", "siguria", "analiti", "drejtimi")
    allowed = {
        "lloji": {k.value for k in AssertionKind},
        "polariteti": {p.value for p in Polarity},
        "siguria": {c.value for c in Certainty},
        "drejtimi": {d.value for d in Direction},
    }
    correct = dict.fromkeys(fields, 0)
    confusions: dict[str, dict[str, int]] = {field: {} for field in fields}
    measured, errors = 0, []

    for row in rows:
        bad = [f for f, values in allowed.items() if row[f] and row[f] not in values]
        if bad:
            errors.append(RowError(row["id"], f"vlerë e panjohur te {', '.join(bad)}"))
            continue
        expected_code = loinc.resolve(row["analiti"]) if row["analiti"] else None
        if row["analiti"] and expected_code is None:
            errors.append(RowError(row["id"], f"analit i panjohur '{row['analiti']}'"))
            continue

        found = extract_assertions(row["fjalia"])
        got = found[0] if found else None
        predicted = {
            "lloji": got.kind.value if got else "asnjë",
            "polariteti": got.polarity.value if got else "asnjë",
            "siguria": got.certainty.value if got else "asnjë",
            "analiti": (got.analyte_code or "") if got else "asnjë",
            "drejtimi": got.direction.value if got else "asnjë",
        }
        expected = {**{f: row[f] for f in fields}, "analiti": expected_code or ""}

        measured += 1
        for field in fields:
            if field != "analiti" and not expected[field]:
                continue
            key = f"{expected[field] or '—'} → {predicted[field] or '—'}"
            confusions[field][key] = confusions[field].get(key, 0) + 1
            correct[field] += expected[field] == predicted[field]

    accuracy = {f: (correct[f] / measured if measured else None) for f in fields}
    return {"sentences": measured, "accuracy": accuracy, "confusion": confusions}, errors


# --------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------


def build(directory: Path = KIT_DIR) -> list[Path]:
    """Shkruan kontekstet; skeletet shkruhen vetëm nëse mungojnë.

    Asnjë skedar i autorit nuk mbishkruhet — një `build` i dytë pas
    plotësimit nuk duhet të fshijë javë pune.
    """
    directory.mkdir(parents=True, exist_ok=True)
    contexts = kit_contexts()
    written = []

    sheet = directory / "A_kontekstet.md"
    sheet.write_text(render_contexts(contexts), encoding="utf-8")
    written.append(sheet)

    skeletons = {
        "A_shpjegimet.md": skeleton_explanations(contexts),
        "B_fjalite.csv": ",".join((*B_COLUMNS, *B_OPTIONAL)) + "\n",
        "C_narrativa.csv": ",".join(C_COLUMNS) + "\n",
    }
    for name, content in skeletons.items():
        path = directory / name
        if not path.exists():
            path.write_text(content, encoding="utf-8")
            written.append(path)
    return written


def duplicate_rows(rows: list[dict[str, str]]) -> list[list[str]]:
    """Grupet e rreshtave me të njëjtin kontekst, fjali dhe burim.

    Një rresht i përsëritur numërohet dy herë dhe e fryn llojin e tij: dhjetë
    rreshta me një dublikat janë në fakt nëntë. Pikat dhe hapësirat e fundit
    nuk i bëjnë rreshtat të ndryshëm — vlerësuesi i heq.
    """
    groups: dict[tuple[str, str, str], list[str]] = {}
    for row in rows:
        key = (row["konteksti"], row["fjalia"].rstrip(". ").strip(), row.get("burimi", ""))
        groups.setdefault(key, []).append(row["id"])
    return [ids for ids in groups.values() if len(ids) > 1]


def check(directory: Path = KIT_DIR) -> dict[str, Any]:
    contexts = dict(kit_contexts())
    b_rows = read_rows(directory / "B_fjalite.csv", B_COLUMNS, B_OPTIONAL)
    b_metrics, b_errors = check_sentences(b_rows, contexts)
    c_metrics, c_errors = check_narrative(read_rows(directory / "C_narrativa.csv", C_COLUMNS))
    return {
        "A": check_explanations(read_explanations(directory / "A_shpjegimet.md"), contexts),
        "B": b_metrics,
        "B_duplicates": duplicate_rows(b_rows),
        "C": c_metrics,
        "errors": [{"id": e.row_id, "reason": e.reason} for e in b_errors + c_errors],
    }


def main(argv: list[str] | None = None) -> int:
    import json

    parser = argparse.ArgumentParser(prog="evaluation.kits")
    parser.add_argument("command", choices=("build", "check"))
    parser.add_argument("--dir", type=Path, default=KIT_DIR)
    args = parser.parse_args(argv)

    if args.command == "build":
        for path in build(args.dir):
            print(f"shkruar {path}")
        return 0

    report = check(args.dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
