"""
Figura 11 — tubacioni i vlerësimit dhe gjurmueshmëria e eksperimenteve.

"""

from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path
from typing import Any

from evaluation import experiments as registry

from . import style

RESULTS = Path(__file__).resolve().parents[2] / "evaluation" / "results"

MEASURED, READY, BLOCKED = "measured", "ready", "blocked"
WIDTH = 6.3


def load_results(directory: Path = RESULTS) -> dict[str, dict[str, Any]]:
    """Rezultati i secilit eksperimenti. E11 ka një rezultat për çdo hyrje
    (`E11/sentence/`, `E11/context/`); mban i pari sipas emrit, dhe për figurën
    vlen vetëm që ekziston."""
    found: dict[str, dict[str, Any]] = {}
    for path in sorted(directory.glob("E*/result.json")) + sorted(
        directory.glob("E*/*/result.json")
    ):
        experiment_id = path.relative_to(directory).parts[0]
        found.setdefault(experiment_id, json.loads(path.read_text(encoding="utf-8")))
    # Eksperimentet me modelin gjuhësor (E4, E6, E12 dhe versionet e E7–E9 me modelin) jetojnë te `llm/`.
    # Një eksperiment që ka rezultat vetëm atje është i matur; ai që ka të dyja mban atë me shabllon.
    for path in sorted(directory.glob("llm/E*/result.json")):
        experiment_id = path.parent.name.split("_")[0]  # `E12_haiku` është kontrolli i E12
        found.setdefault(experiment_id, json.loads(path.read_text(encoding="utf-8")))
    return found


def status_of(experiment: registry.Experiment, results: dict[str, dict]) -> str:
    result = results.get(experiment.id)
    if result is not None and not result.get("pending_reason"):
        return MEASURED
    return READY if experiment.runnable else BLOCKED


def trace_of(result: dict[str, Any] | None) -> str:
    """`e plotë`, `pa commit` ose `pjesore`; bosh nëse s'ka rezultat."""
    if result is None:
        return ""
    metadata = result.get("metadata") or {}
    code, dataset = metadata.get("code") or {}, metadata.get("dataset") or {}
    if not (code.get("git_sha") and dataset.get("version")):
        return "pjesore"
    return "pa commit" if code.get("working_tree_dirty") else "e plotë"


def provenance_fields(results: dict[str, dict]) -> list[str]:
    """Fushat e metadata-s së një rezultati të vërtetë, të grupuara sipas prindit."""
    for result in results.values():
        metadata = result.get("metadata")
        if metadata:
            lines, plain = [], []
            for key, value in metadata.items():
                if isinstance(value, dict):
                    lines.append(f"{key}: " + ", ".join(value))
                else:
                    plain.append(key)
            return [", ".join(plain)] + lines if plain else lines
    return []


def _wrap(text: str, width: int) -> list[str]:
    return textwrap.wrap(text, width, break_long_words=False) or [""]


def _flow(ax, top: float, results: dict[str, dict]) -> float:
    """Katër kutitë e rrjedhës; kthen pjesën e poshtme të shiritit."""
    metadata = next((r["metadata"] for r in results.values() if r.get("metadata")), {})
    dataset = metadata.get("dataset", {})
    # E10 dhe E11 dalin nga skriptet e `ml/`, jo nga harness-i: metadata e tyre nuk ka `pipeline`.
    # Emri i plotë i një pipeline-i mban modelin, kërkesën dhe pragun (`e9[mistral:…:p1]+ocr+xlm-…@0.85`); figura
    # tregon vetëm familjen, që të mos mbushet kutia.
    pipelines = sorted(
        {
            re.split(r"[\[+]", r["metadata"]["pipeline"]["name"])[0]
            for r in results.values()
            if (r.get("metadata") or {}).get("pipeline")
        }
    )
    metrics = sorted({e.metric for e in registry.EXPERIMENTS})

    stages = [
        (
            "Korpusi",
            [
                "data_generator",
                f"{dataset.get('version', '?')}",
                f"fara {dataset.get('seed', '?')}",
            ],
        ),
        ("Pipeline", ["në rezultatet:", ", ".join(pipelines) or "?"]),
        ("Metrika", ["evaluation/metrics,", f"{len(metrics)} module:", ", ".join(metrics)]),
        ("result.json", ["prejardhja në çdo rezultat:"] + provenance_fields(results)),
    ]
    widths, gap = [1.5, 1.0, 1.35, 1.8], 0.12
    wrapped = [
        [line for text in body for line in _wrap(text, int(w * 19))]
        for (_, body), w in zip(stages, widths)
    ]
    height = 0.3 + 0.125 * max(len(lines) for lines in wrapped)
    x = (WIDTH - (sum(widths) + gap * 3)) / 2
    previous = None
    for (title, _), lines, box_w in zip(stages, wrapped, widths):
        cx, cy = x + box_w / 2, top - height / 2
        current = style.box(ax, cx, cy, box_w, height, "", fill=style.BLUE_TINT, lw=1.0)
        style.label(ax, cx, top - 0.14, title, size=7.5, color=style.INK, weight="bold")
        for j, line in enumerate(lines):
            style.label(
                ax,
                cx - box_w / 2 + 0.07,
                top - 0.3 - 0.125 * j,
                line,
                size=6.2,
                color=style.INK,
                ha="left",
            )
        if previous:
            style.arrow(ax, (previous.right + 0.01, cy), (current.left - 0.01, cy), lw=1.2)
        previous = current
        x += box_w + gap
    return top - height


def build():
    results = load_results()
    experiments = registry.EXPERIMENTS

    row_h, header_h, strip_top_pad = 0.36, 0.3, 0.2
    # lartësia e shiritit llogaritet para vizatimit, që kanavaca të ketë madhësinë e duhur
    probe_fig, probe_ax = style.canvas(WIDTH, 4, (0, WIDTH), (0, 4))
    strip_bottom = _flow(probe_ax, 4 - strip_top_pad, results)
    style.plt.close(probe_fig)
    strip_h = (4 - strip_top_pad) - strip_bottom

    legend_h = 0.85
    height = strip_top_pad + strip_h + 0.35 + header_h + row_h * len(experiments) + legend_h
    fig, ax = style.canvas(WIDTH, height, (0, WIDTH), (0, height))
    strip_bottom = _flow(ax, height - strip_top_pad, results)

    columns = {
        "id": 0.08,
        "title": 0.5,
        "pk": 2.85,
        "data": 3.3,
        "metric": 4.3,
        "status": 5.15,
        "trace": 5.78,
    }
    y = strip_bottom - 0.35
    for key, text in (
        ("id", "ID"),
        ("title", "Eksperimenti"),
        ("pk", "Pyetja"),
        ("data", "Të dhënat"),
        ("metric", "Metrika"),
        ("status", "Statusi"),
        ("trace", "Gjurma"),
    ):
        style.label(ax, columns[key], y, text, size=7, ha="left", color=style.INK, weight="bold")
    ax.plot([0.05, WIDTH - 0.05], [y - 0.14, y - 0.14], color=style.INK, lw=0.8, zorder=2)

    for index, experiment in enumerate(experiments):
        cy = y - header_h - row_h * (index + 0.5) + 0.06
        status = status_of(experiment, results)
        condition = "" if experiment.condition in ("—", "") else f" · {experiment.condition}"
        style.label(
            ax,
            columns["id"],
            cy,
            experiment.id,
            size=7.5,
            ha="left",
            color=style.INK,
            weight="bold",
        )
        style.label(
            ax,
            columns["title"],
            cy + 0.05,
            experiment.title + condition,
            size=6.8,
            ha="left",
            color=style.INK,
        )
        if status != MEASURED:
            reason = (
                experiment.waiting_for or experiment.pending_reason or "gati për t'u ekzekutuar"
            )
            style.label(
                ax,
                columns["title"],
                cy - 0.09,
                reason,
                size=5.8,
                ha="left",
                color=style.MUTED,
                style="italic",
            )
        style.label(
            ax,
            columns["pk"],
            cy,
            experiment.answers.replace("vlefshmëri e jashtme", "jashtme"),
            size=6.8,
            ha="left",
            color=style.INK,
        )
        style.label(
            ax, columns["data"], cy, experiment.dataset, size=6.8, ha="left", color=style.INK
        )
        style.label(
            ax, columns["metric"], cy, experiment.metric, size=6.8, ha="left", color=style.INK
        )
        _status_cell(ax, columns["status"], cy, status)
        style.label(
            ax,
            columns["trace"],
            cy,
            trace_of(results.get(experiment.id)),
            size=6.3,
            ha="left",
            color=style.INK,
        )
        ax.plot(
            [0.05, WIDTH - 0.05],
            [cy - row_h / 2 + 0.06 - 0.0] * 2,
            color="#dcdbd5",
            lw=0.5,
            zorder=1,
        )

    _legend(ax, 0.1)
    return fig, {e.id: status_of(e, results) for e in experiments}


def _status_cell(ax, x: float, cy: float, status: str) -> None:
    w, h = 0.58, 0.2
    text = {MEASURED: "i matur", READY: "gati", BLOCKED: "i bllokuar"}[status]
    options = {
        MEASURED: dict(fill=style.BLUE_DEEP, edge=style.BLUE_DEEP, color="#ffffff", ls="-"),
        READY: dict(fill=style.SURFACE, edge=style.BLUE, color=style.INK, ls="-"),
        BLOCKED: dict(fill=style.NEUTRAL, edge=style.MUTED, color=style.MUTED, ls="--"),
    }[status]
    style.box(ax, x + w / 2, cy, w, h, text, size=6, weight="bold", lw=1.0, **options)


def _legend(ax, y: float) -> None:
    lines = (
        "i matur = ekziston një result.json te evaluation/results/E*/ ose evaluation/results/llm/E*/.  gati = mund të ekzekutohet, por s'ka rezultat.",
        "gjurma: e plotë = version korpusi dhe git sha;  pa commit = prodhuar me ndryshime të pakomituara",
        "(sha nuk e përcakton kodin);  pjesore = pa metadata të plota.",
    )
    for i, line in enumerate(lines):
        style.label(ax, 0.1, y + 0.6 - 0.15 * i, line, size=6.2, ha="left")
    for x, status in ((0.1, MEASURED), (0.85, READY), (1.6, BLOCKED)):
        _status_cell(ax, x, y + 0.05, status)
