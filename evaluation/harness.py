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
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import dataset as dataset_module
from . import experiments as registry
from . import provenance
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
    llm = _llm_metadata(pipeline)
    if llm is not None:
        metadata["llm"] = llm

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


def _llm_client(pipeline: Pipeline) -> Any | None:
    """Klienti i modelit që përdor pipeline-i, ose `None` (shablloni, rregullat)."""
    return getattr(getattr(pipeline, "generator", None), "client", None)


def _llm_metadata(pipeline: Pipeline) -> dict[str, Any] | None:
    """Modeli dhe parametrat e tij, bashkë me kostot e ekzekutimit.

    Pa to, një rezultat i LLM-së nuk atribuohet dot: i njëjti emër modeli me
    temperaturë ose arsyetim tjetër jep tekst tjetër. `usage` numëron thirrjet e
    reja kundrejt atyre nga cache-i: ekzekutimi i dytë i të njëjtit eksperiment
    duhet të tregojë zero thirrje."""
    client = _llm_client(pipeline)
    if client is None:
        return None
    from analyte.generation.prompt import PROMPT_VERSION

    from .ungrounded import UNGROUNDED_PROMPT_VERSION

    return {
        "provider": client.provider,
        "model": client.model,
        "temperature": client.temperature,
        "thinking": client.thinking,
        "max_output_tokens": client.max_output_tokens,
        "prompt_version": (
            UNGROUNDED_PROMPT_VERSION if getattr(pipeline, "ablation", "") == "E6" else PROMPT_VERSION
        ),
        "usage": client.usage.to_json(),
    }


def _metadata(
    experiment: registry.Experiment, data: Dataset, pipeline: Pipeline
) -> dict[str, Any]:
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
        "code": provenance.code_metadata(),
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }


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


GENERATORS = ("template", "llm")
"""Gjeneruesit e njohur nga CLI: shablloni dhe modeli gjuhësor nga `.env`."""

LLM_CACHE = Path("evaluation/cache/llm")
"""Përgjigjet e modelit, një skedar për kërkesë. Ruhen me qëllim në depo: pa to,
një rezultat nuk rikrijohet pa thirrje të reja ndaj një model që mund të
tërhiqet (shih `analyte.generation.llm`)."""


class RunAborted(BaseException):
    """Ofruesi nuk u arrit: ekzekutimi ndalet, nuk numërohet si gabim i modelit.

    Është `BaseException` me qëllim: cikli gjenerim → verifikim kap `Exception`
    dhe një ofrues i rënë do të dukej si dështim i modelit, do ta çonte dokumentin
    te shablloni dhe do ta hidhte poshtë ekzekutimin pa e thënë. Përgjigjet e
    dhëna deri atëherë janë në cache, ndaj një ekzekutim i ri vazhdon aty ku u ndal."""


class StrictClient:
    """Klienti i modelit që e kthen `ProviderUnavailable` në `RunAborted`."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)

    def complete(self, system: str, user: str):
        from analyte.generation.llm import ProviderUnavailable

        try:
            return self._client.complete(system, user)
        except ProviderUnavailable as error:
            raise RunAborted(str(error)) from None


def build_llm_client(*, model: str | None = None, cache: Path = LLM_CACHE) -> StrictClient:
    """Klienti nga `.env`; ndalon qysh këtu nëse mungon ofruesi, modeli ose çelësi."""
    from analyte.config import get_settings
    from analyte.generation.llm import ProviderError, build_client

    try:
        return StrictClient(build_client(get_settings(), model=model, cache_dir=cache))
    except ProviderError as error:
        raise SystemExit(f"--generator llm: {error}") from None
    except Exception as error:  # konfigurim i paplotë (p.sh. sekretet e shërbimit)
        raise SystemExit(f"--generator llm: konfigurimi nuk lexohet: {type(error).__name__}") from None


def build_generator(name: str, cache: Path = LLM_CACHE):
    if name == "template":
        from analyte.generation.templates import TemplateGenerator

        return TemplateGenerator()
    if name == "llm":
        from analyte.generation.llm import LlmGenerator

        return LlmGenerator(build_llm_client(cache=cache))
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
    akordim mbi të dhënat e vlerësimit. Është pika brenda buxhetit të
    alarmeve të rreme (`deployed_threshold`), jo ajo me macro F1 më të lartë:
    kjo e dyta bllokon pothuajse çdo tekst të pastër.
    """
    if run_dir is None:
        return None, None
    from analyte.verification.classifier import TransformersPredictor

    predictor = TransformersPredictor(run_dir)
    result = Path("evaluation/results/E11") / predictor.mode / "result.json"
    if not result.exists():
        raise SystemExit(f"mungon {result}: ekzekutoni ml.evaluate_classifier përpara E9")
    threshold = json.loads(result.read_text(encoding="utf-8")).get("deployed_threshold")
    if threshold is None:
        raise SystemExit(
            f"{result} nuk ka prag brenda buxhetit të alarmeve të rreme; E9 nuk mund të ekzekutohet"
        )
    return predictor, threshold


def build_pipeline(
    name: str,
    data: Dataset,
    generator: str = "template",
    ocr: bool = False,
    classifier: Path | None = None,
    cache: Path = LLM_CACHE,
) -> Pipeline:
    engine = build_ocr(ocr)
    suffix = "+ocr" if engine is not None else ""
    if name == "e6":
        if generator != "llm":
            raise SystemExit("e6 (pa bazim) kërkon --generator llm: shablloni nuk ka çfarë të lexojë")
        from .ungrounded import UngroundedPipeline

        return UngroundedPipeline(client=build_llm_client(cache=cache), ocr=engine)
    if name in {"e7", "e8", "e9"}:
        predictor, threshold = build_classifier(classifier) if name == "e9" else (None, None)
        if name == "e9" and predictor is None:
            raise SystemExit("e9 kërkon --classifier me dosjen e ekzekutimit nga Colab")
        return GenerationPipeline(
            build_generator(generator, cache),
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
        f"pipeline i panjohur '{name}'; njihen: empty, oracle, branch_a, grounding, e6, e7, e8, e9"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="evaluation.harness",
        description="Ekzekuton eksperimentet e vlerësimit mbi një korpus.",
    )
    parser.add_argument("--dataset", type=Path, required=True, help="dosja e korpusit")
    parser.add_argument("--experiment", default="all", help="ID e eksperimentit ose 'all'")
    parser.add_argument(
        "--pipeline", default="empty", help="empty | oracle | branch_a | grounding | e6 | e7 | e8 | e9"
    )
    parser.add_argument(
        "--classifier", type=Path, default=None, help="dosja e ekzekutimit të Colab-it, për e9"
    )
    parser.add_argument(
        "--generator", default="template", help="gjeneruesi për e6–e9: template | llm"
    )
    parser.add_argument(
        "--llm-cache", type=Path, default=LLM_CACHE, help="dosja e përgjigjeve të modelit"
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
    pipeline = build_pipeline(
        args.pipeline, data, args.generator, args.ocr, args.classifier, args.llm_cache
    )

    chosen = (
        list(registry.EXPERIMENTS)
        if args.experiment == "all"
        else [registry.get(args.experiment)]
    )

    try:
        results = [run_experiment(experiment, data, pipeline) for experiment in chosen]
    except RunAborted as stop:
        client = _llm_client(pipeline)
        used = f" ({client.usage.to_json()})" if client is not None else ""
        print(
            f"\nEkzekutimi u NDAL, nuk u vlerësua: {stop}{used}\n"
            "Përgjigjet e dhëna janë në cache; ekzekutoje po atë komandë më vonë (p.sh. pas "
            "rivendosjes së kuotës) dhe ai vazhdon aty ku u ndal.",
            file=sys.stderr,
        )
        return 2
    for result in results:
        write_result(result, args.out)
        print(f"{result.experiment.id}: {result.headline()}")

    summary = write_summary(results, args.out)
    measured = sum(1 for r in results if r.measured)
    print(f"\n{measured}/{len(results)} të matura — {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
