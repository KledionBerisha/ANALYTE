"""
Harness-i i eksperimenteve.

    python -m evaluation.harness --dataset data/v1 --pipeline empty

Ekzekuton një ose të gjitha eksperimentet e §8.1 mbi një korpus dhe
shkruan `evaluation/results/{ID}/`. Ekziston përpara çdo shtrese të
sistemit me qëllim: matja para optimizimit do të thotë që rruga nga
korpusi te qeliza e tabelës të jetë e provuar kur të ketë diçka për të
matur, jo pas.

Çdo rezultat shkruhet bashkë me prejardhjen e vet: farën e korpusit,
versionin e tij me shumë kontrolluese të tabelave burimore, sha-në e
git-it, gjendjen e pastër ose jo të pemës së punës, dhe versionin e
katalogut të rregullave. Pa këto, një numër në Kapitullin 6 nuk mund të
rikrijohet dhe as të mbrohet (NFR3).

Gjendja e pemës së punës shënohet posaçërisht: një rezultat i prodhuar
mbi kod të pakommit-uar nuk është i rindërtueshëm, dhe kjo duhet të duket
në skedar e jo të kujtohet.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from analyte.domain.policy import POLICY_VERSION, RULES_VERSION

from . import dataset as dataset_module
from . import experiments as registry
from .dataset import Dataset
from .metrics import classification, crossref, extraction, prose, violations
from .pipeline import (
    ABLATIONS,
    BranchAPipeline,
    EmptyPipeline,
    GenerationPipeline,
    GroundingPipeline,
    OraclePipeline,
    Pipeline,
)

NOT_MEASURED = "[TO BE MEASURED]"

CONTEXT_METRICS = {
    "extraction": extraction.measure,
    "classification": classification.measure,
    "crossref": crossref.measure,
}
"""Metrika që krahasojnë kontekstin e nxjerrë me atë të vërtetë."""

OUTPUT_METRICS = {
    "prose": prose.measure,
    "violations": violations.measure,
}
"""Metrika që kanë nevojë edhe për tekstin e gjeneruar dhe verifikimin e tij."""


@dataclass(frozen=True, slots=True)
class ExperimentResult:
    """Rezultati i një eksperimenti bashkë me prejardhjen e tij."""

    experiment: registry.Experiment
    metadata: dict[str, Any]
    metrics: dict[str, Any] | None
    skipped_reason: str | None = None
    """Pse një eksperiment i ekzekutueshëm nuk u mat me këtë pipeline."""

    @property
    def measured(self) -> bool:
        return self.metrics is not None

    @property
    def reason(self) -> str | None:
        return self.experiment.pending_reason or self.skipped_reason

    def to_json(self) -> dict[str, Any]:
        return {
            "experiment": self.experiment.to_json(),
            "metadata": self.metadata,
            "metrics": self.metrics,
            "pending_reason": self.reason,
        }

    def headline(self) -> str:
        """Numri i vetëm që hyn në qelizën e matricës."""
        if not self.measured:
            return NOT_MEASURED
        return _headline(self.experiment.metric, self.metrics or {})


def run_experiment(
    experiment: registry.Experiment, data: Dataset, pipeline: Pipeline
) -> ExperimentResult:
    """Ekzekuton një eksperiment dhe kthen rezultatin me prejardhje."""
    scoped = data.filter(channel=experiment.channel)
    metadata = _metadata(experiment, scoped, pipeline)

    if not experiment.runnable:
        return ExperimentResult(experiment, metadata, None)

    # Çdo kusht ablacioni është pipeline më vete. Pa këtë kontroll, një
    # ekzekutim i vetëm do t'i mbushte E6-E9 me të njëjtat numra, dhe matrica
    # do të tregonte një ablacion që nuk ndodhi.
    ablation = getattr(pipeline, "ablation", None)
    if experiment.id in ABLATIONS and ablation != experiment.id:
        implemented = f"zbaton kushtin {ablation}" if ablation else "nuk gjeneron tekst"
        return ExperimentResult(
            experiment,
            metadata,
            None,
            skipped_reason=f"pipeline-i `{pipeline.name}` {implemented}",
        )

    outputs = [(case.truth, pipeline.run(case.document_input)) for case in scoped.cases]

    if experiment.metric in CONTEXT_METRICS:
        pairs = [(truth, output.context) for truth, output in outputs]
        metrics = CONTEXT_METRICS[experiment.metric](pairs)
    elif experiment.metric in OUTPUT_METRICS:
        metrics = OUTPUT_METRICS[experiment.metric](outputs)
    else:
        # Metrikë e regjistruar por pa zbatim të lidhur me pipeline-in:
        # zbuluesit (PK6) maten mbi çifte etiketash, jo mbi dokumente.
        return ExperimentResult(experiment, metadata, None)

    return ExperimentResult(experiment, metadata, metrics)


def _metadata(
    experiment: registry.Experiment, data: Dataset, pipeline: Pipeline
) -> dict[str, Any]:
    revision, dirty = _git_state()
    return {
        "experiment_id": experiment.id,
        "pipeline": {"name": pipeline.name, "version": pipeline.version},
        "dataset": {
            "name": data.name,
            "version": data.version,
            "seed": data.seed,
            "documents": len(data),
            "channel": experiment.channel or "all",
        },
        "code": {
            "git_sha": revision,
            "working_tree_dirty": dirty,
            "rules_version": RULES_VERSION,
            "policy_version": POLICY_VERSION,
            "python": sys.version.split()[0],
        },
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }


def _git_state() -> tuple[str, bool | None]:
    """Sha-ja e kodit dhe nëse pema e punës kishte ndryshime të paruajtura."""
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True, timeout=10,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, check=True, timeout=10,
        ).stdout.strip()
        return revision, bool(status)
    except (subprocess.SubprocessError, OSError, FileNotFoundError):
        return "unknown", None


def _headline(metric: str, payload: dict[str, Any]) -> str:
    if metric == "extraction":
        return _fmt(payload.get("micro", {}).get("f1"), "F1")
    if metric == "classification":
        return _fmt(payload.get("overall", {}).get("accuracy"), "saktësi")
    if metric == "crossref":
        return _fmt(payload.get("overall", {}).get("accuracy"), "saktësi")
    if metric == "prose":
        return _fmt(payload.get("negation_preservation"), "ruajtje mohimi") + _ci(
            payload.get("ci95_negation_preservation")
        )
    if metric == "violations":
        return _fmt(payload.get("rate_reaching_user_per_100_sentences"), "shkelje/100 fjali") + _ci(
            payload.get("ci95_reaching_user")
        )
    return NOT_MEASURED


def _ci(interval: dict[str, Any] | None) -> str:
    """Intervali i besimit pas numrit kryesor, kur ekziston.

    Me zero ngjarje, ose me sukses në çdo njësi, shtypet kufiri i rregullit
    të treshit dhe jo një interval me gjerësi zero: ai do të thoshte siguri
    që mostra nuk e jep.
    """
    if not interval:
        return ""
    if "rule_of_three_high" in interval:
        return f" [95%: ≤ {interval['rule_of_three_high']:.3f}]"
    if "rule_of_three_low" in interval:
        return f" [95%: ≥ {interval['rule_of_three_low']:.3f}]"
    return f" [95%: {interval['low']:.3f}–{interval['high']:.3f}]"


def _fmt(value: float | None, label: str) -> str:
    """Vlera e matur, ose shënimi se nuk kishte çfarë të matej.

    "n/a" dhe `[TO BE MEASURED]` nuk janë e njëjta gjë: e para do të thotë
    se eksperimenti u ekzekutua dhe emëruesi doli zero.
    """
    return f"{value:.3f} {label}" if value is not None else f"n/a ({label})"


# --------------------------------------------------------------------
# Shkrimi i rezultateve
# --------------------------------------------------------------------


def write_result(result: ExperimentResult, out_dir: Path) -> Path:
    directory = out_dir / result.experiment.id
    directory.mkdir(parents=True, exist_ok=True)

    path = directory / "result.json"
    path.write_text(
        json.dumps(result.to_json(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (directory / "table.md").write_text(_result_table(result), encoding="utf-8")
    return path


def _result_table(result: ExperimentResult) -> str:
    experiment = result.experiment
    metadata = result.metadata
    lines = [
        f"# {experiment.id} — {experiment.title}",
        "",
        f"**Kushti:** {experiment.condition}  ",
        f"**Përgjigjet:** {experiment.answers}  ",
        f"**Rezultati kryesor:** {result.headline()}",
        "",
        "| Prejardhja | Vlera |",
        "|---|---|",
        f"| Korpusi | `{metadata['dataset']['version']}` |",
        f"| Dokumente | {metadata['dataset']['documents']} ({metadata['dataset']['channel']}) |",
        f"| Fara | {metadata['dataset']['seed']} |",
        f"| Pipeline | `{metadata['pipeline']['name']}` v{metadata['pipeline']['version']} |",
        f"| Git | `{metadata['code']['git_sha'][:12]}`"
        f"{' (e papastër)' if metadata['code']['working_tree_dirty'] else ''} |",
        f"| Rregullat | `{metadata['code']['rules_version']}` |",
        f"| Kur | {metadata['created_at']} |",
        "",
    ]

    if not result.measured:
        lines += [f"> Ende e pamatur: {result.reason}.", ""]
    else:
        lines += ["```json", json.dumps(result.metrics, ensure_ascii=False, indent=2), "```", ""]

    return "\n".join(lines)


def write_summary(results: list[ExperimentResult], out_dir: Path) -> Path:
    """Matrica e §8.1 me qelizat e mbushura aty ku ka matje."""
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Matrica e eksperimenteve",
        "",
        "Qelizat `[TO BE MEASURED]` nuk janë boshllëqe: ato janë matje që",
        "presin komponentin e vet. Qelizat `n/a` janë matje të ekzekutuara",
        "mbi një emërues zero.",
        "",
        "| ID | Eksperimenti | Kushti | Përgjigjet | Rezultati | Pipeline |",
        "|---|---|---|---|---|---|",
    ]
    for result in results:
        experiment = result.experiment
        pipeline = result.metadata["pipeline"]["name"] if result.measured else "—"
        lines.append(
            f"| {experiment.id} | {experiment.title} | {experiment.condition} "
            f"| {experiment.answers} | {result.headline()} | {pipeline} |"
        )

    lines += ["", "## Prejardhja", ""]
    if results:
        metadata = results[0].metadata
        lines += [
            f"- Korpusi: `{metadata['dataset']['version']}`, farë {metadata['dataset']['seed']}",
            f"- Kodi: `{metadata['code']['git_sha']}`"
            + (" — pemë pune e papastër" if metadata["code"]["working_tree_dirty"] else ""),
            f"- Rregullat: `{metadata['code']['rules_version']}`, "
            f"politika: `{metadata['code']['policy_version']}`",
            "",
        ]

    path = out_dir / "summary.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# --------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------


GENERATORS = ("template",)
"""Gjeneruesit e njohur nga CLI. Modeli gjuhësor shtohet këtu kur të ketë."""


def build_generator(name: str):
    if name == "template":
        from analyte.generation.templates import TemplateGenerator

        return TemplateGenerator()
    raise SystemExit(f"gjenerues i panjohur '{name}'; njihen: {', '.join(GENERATORS)}")


def build_ocr(enabled: bool):
    """Motori OCR, ose `None`. Mungesa e tij ndal ekzekutimin qysh këtu, jo
    si 175 dokumente të dështuara në mes të matjes."""
    if not enabled:
        return None
    from analyte.ingestion.ocr import OcrUnavailable, TesseractOcr

    try:
        # Parazgjedhjet e motorit janë konfigurimi i akordimit (ADR 0012); i
        # njëjti përdoret nga shërbimi, që E2 të matë atë që sheh pacienti.
        return TesseractOcr()
    except OcrUnavailable as error:
        raise SystemExit(f"--ocr u kërkua, por {error}") from None


def build_classifier(run_dir: Path | None) -> tuple[Any, float | None]:
    """Modeli i Colab-it dhe pragu i tij nga E11.

    Pragu nuk jepet nga linja e komandës: ai lexohet nga rezultati i E11,
    ku u zgjodh mbi validimin. Një prag i dhënë me dorë këtu do të ishte
    akordim mbi të dhënat e vlerësimit.
    """
    if run_dir is None:
        return None, None
    from analyte.verification.classifier import TransformersPredictor

    predictor = TransformersPredictor(run_dir)
    result = Path("evaluation/results/E11") / predictor.mode / "result.json"
    if not result.exists():
        raise SystemExit(f"mungon {result}: ekzekutoni ml.evaluate_classifier përpara E9")
    return predictor, json.loads(result.read_text(encoding="utf-8"))["threshold"]


def build_pipeline(
    name: str,
    data: Dataset,
    generator: str = "template",
    ocr: bool = False,
    classifier: Path | None = None,
) -> Pipeline:
    engine = build_ocr(ocr)
    suffix = "+ocr" if engine is not None else ""
    if name in {"e7", "e8", "e9"}:
        predictor, threshold = build_classifier(classifier) if name == "e9" else (None, None)
        if name == "e9" and predictor is None:
            raise SystemExit("e9 kërkon --classifier me dosjen e ekzekutimit nga Colab")
        return GenerationPipeline(
            build_generator(generator),
            ablation=name.upper(),
            ocr=engine,
            classifier=predictor,
            threshold=threshold,
        )
    if name == "empty":
        return EmptyPipeline()
    if name == "oracle":
        return OraclePipeline(truth=data.truth_by_id())
    if name == "branch_a":
        return BranchAPipeline(name=f"branch_a{suffix}", ocr=engine)
    if name == "grounding":
        return GroundingPipeline(name=f"grounding{suffix}", ocr=engine)
    raise SystemExit(
        f"pipeline i panjohur '{name}'; njihen: empty, oracle, branch_a, grounding, e7, e8, e9"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="evaluation.harness",
        description="Ekzekuton eksperimentet e vlerësimit mbi një korpus.",
    )
    parser.add_argument("--dataset", type=Path, required=True, help="dosja e korpusit")
    parser.add_argument("--experiment", default="all", help="ID e eksperimentit ose 'all'")
    parser.add_argument(
        "--pipeline", default="empty", help="empty | oracle | branch_a | grounding | e7 | e8 | e9"
    )
    parser.add_argument(
        "--classifier", type=Path, default=None, help="dosja e ekzekutimit të Colab-it, për e9"
    )
    parser.add_argument(
        "--generator", default="template", help="gjeneruesi për e7 dhe e8: template"
    )
    parser.add_argument(
        "--ocr", action="store_true", help="lexo dokumentet e skanuara me Tesseract"
    )
    parser.add_argument("--limit", type=int, default=None, help="kufizo numrin e dokumenteve")
    parser.add_argument(
        "--out", type=Path, default=Path("evaluation/results"), help="dosja e rezultateve"
    )
    args = parser.parse_args(argv)

    data = dataset_module.load(args.dataset, limit=args.limit)
    pipeline = build_pipeline(args.pipeline, data, args.generator, args.ocr, args.classifier)

    chosen = (
        list(registry.EXPERIMENTS)
        if args.experiment == "all"
        else [registry.get(args.experiment)]
    )

    results = [run_experiment(experiment, data, pipeline) for experiment in chosen]
    for result in results:
        write_result(result, args.out)
        print(f"{result.experiment.id}: {result.headline()}")

    summary = write_summary(results, args.out)
    measured = sum(1 for r in results if r.measured)
    print(f"\n{measured}/{len(results)} të matura — {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
