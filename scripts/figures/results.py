"""
Figurat 18–21 — rezultatet e Kapitullit 6, nga skedarët e rezultateve.

Asnjë numër nuk shkruhet me dorë: çdo vlerë lexohet nga `evaluation/results/`
(E3, E10, E11, E12, ablacioni me modelin te `results/llm/`) dhe nga
`evaluation.kits.check()` për rregullat mbi grupin B, sepse ai rezultat nuk
ruhet si skedar. Një rezultat që mungon e ndalon figurën me mesazh, nuk e
zëvendëson me zero.

Si te figurat e tjera, asnjë kuptim nuk mbahet vetëm nga ngjyra: seritë
dallohen edhe nga forma e shenjës dhe nga mbushja, që figura të lexohet bardhezi.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import style  # vendos backend-in Agg para pyplot

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "evaluation" / "results"
LLM = RESULTS / "llm"

STATUS_ORDER = ["normal", "high", "low", "critical_high", "critical_low", "uninterpretable"]

# Renditja e klasave të detektorëve: e pastra së pari, pastaj llojet sipas dobësisë së
# njohur të tyre; e njëjta renditje te Figurat 20 dhe 21 që të krahasohen me sy.
CLASS_ORDER = [
    "clean",
    "ungrounded_number",
    "ungrounded_analyte",
    "direction_mismatch",
    "polarity_flip",
    "hedge_removed",
    "fabricated_finding",
    "omitted_recommendation",
    "missing_critical",
    "prohibited_claim",
    "ungrounded_term_explanation",
]

CONDITIONS = [
    ("E6", "A", "pa bazim", "pa bazim"),
    ("E7", "B", "vetëm bazim", "bazim"),
    ("E8", "C", "bazim dhe rregulla", "+ rregulla"),
    ("E9", "D", "bazim, rregulla dhe klasifikues", "+ klasifikues"),
]

SHORT = {
    "ungrounded_number": "u_number",
    "ungrounded_analyte": "u_analyte",
    "direction_mismatch": "direction",
    "polarity_flip": "polarity",
    "hedge_removed": "hedge",
    "fabricated_finding": "fabricated",
    "omitted_recommendation": "omitted_rec",
    "missing_critical": "missing_crit",
    "prohibited_claim": "prohibited",
    "ungrounded_term_explanation": "u_term",
}

HEAT = LinearSegmentedColormap.from_list("blue", [style.SURFACE, style.BLUE_TINT, style.BLUE, style.BLUE_DEEP])


class MissingResult(RuntimeError):
    """Skedari i rezultatit që figura e lexon nuk ekziston."""


def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        shown = path.relative_to(ROOT) if ROOT in path.parents else path
        raise MissingResult(f"mungon {shown}; ekzekuto eksperimentin para figurës")
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Të dhënat (pa matplotlib)
# ---------------------------------------------------------------------------


def ablation(llm: Path = LLM) -> list[dict[str, Any]]:
    """Katër kushtet A–D me modelin: norma te përdoruesi, intervali dhe shabllonet rezervë."""
    rows = []
    for experiment, letter, label, short in CONDITIONS:
        metrics = _load(llm / experiment / "result.json")["metrics"]
        ci = metrics["ci95_reaching_user"]
        rows.append(
            {
                "experiment": experiment,
                "letter": letter,
                "label": label,
                "short": short,
                "rate": metrics["rate_reaching_user_per_100_sentences"],
                "low": ci["low"],
                "high": ci["high"],
                "upper_bound": ci.get("rule_of_three_high"),
                "fallback_share": metrics.get("fallback_share"),
                "by_type_produced": metrics["by_type_produced"],
            }
        )
    return rows


def status_matrix(results: Path = RESULTS) -> tuple[list[str], list[list[int]]]:
    """Matrica e konfuzionit të E3: rreshti është e vërteta, kolona parashikimi."""
    cells = _load(results / "E3" / "result.json")["metrics"]["overall"]["matrix"]
    counts = [[int(cells.get(f"{t}->{p}", 0)) for p in STATUS_ORDER] for t in STATUS_ORDER]
    return STATUS_ORDER, counts


def confusion_counts(matrix: dict[str, int], classes: list[str]) -> list[list[int]]:
    return [[int(matrix.get(f"{t}->{p}", 0)) for p in classes] for t in classes]


def present_classes(*matrices: dict[str, int]) -> list[str]:
    """Klasat që shfaqen si e vërtetë ose si parashikim në ndonjërën matricë, sipas `CLASS_ORDER`."""
    seen = {part for m in matrices for key in m for part in key.split("->")}
    unknown = seen - set(CLASS_ORDER)
    if unknown:
        raise MissingResult(f"klasa pa vend në renditje: {sorted(unknown)}")
    return [c for c in CLASS_ORDER if c in seen]


def detectors() -> dict[str, dict[str, dict[str, Any]]]:
    """Metrikat e secilit detektor mbi dy mostrat: `synthetic` (E10 test, 192) dhe `natural` (grupi B, 105).

    Klasifikuesi është ai i vendosur në E9 (fjalia, rregulli 2). Rregullat mbi B
    rillogariten nga `evaluation.kits.check()`; ky është i vetmi llogaritje këtu.
    """
    from evaluation import kits

    classifier = _load(RESULTS / "E11" / "sentence" / "result.json")["operating_points"]["false_alarm_budget"]["metrics"]
    classifier_b = _load(RESULTS / "E11" / "sentence" / "kit_B.json")["operating_points"]["false_alarm_budget"]["metrics"]
    return {
        "Rregullat": {
            "synthetic": _load(RESULTS / "E10" / "result.json")["metrics"],
            "natural": kits.check()["B"],
        },
        "Klasifikuesi XLM-R": {"synthetic": classifier, "natural": classifier_b},
        "Gjykatësi Claude Sonnet": {
            "synthetic": _load(LLM / "E12" / "result.json")["metrics"],
            "natural": _load(LLM / "E12" / "kit_B.json")["metrics"],
        },
        "Gjykatësi Claude Haiku": {
            "synthetic": _load(LLM / "E12_haiku" / "result.json")["metrics"],
            "natural": _load(LLM / "E12_haiku" / "kit_B.json")["metrics"],
        },
    }


def shares(by_type: dict[str, int]) -> dict[str, float]:
    """Pjesa e secilit lloj në totalin e shkeljeve të një kushti, në përqindje."""
    total = sum(by_type.values())
    return {t: 100 * n / total for t, n in by_type.items() if total}


# ---------------------------------------------------------------------------
# Vizatimi
# ---------------------------------------------------------------------------


def _plain(ax) -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(style.FAINT)
    ax.tick_params(colors=style.MUTED, labelsize=7)


def _heatmap(ax, counts: list[list[int]], classes: list[str], *, annotate: float, label_size: float, title: str = "", show_y: bool = True, short: bool = False):
    """Matricë konfuzioni: ngjyra është pjesa e rreshtit (recall), numri brenda është numërimi."""
    rows = [sum(r) for r in counts]
    shares_ = [[(v / s if s else 0.0) for v in r] for r, s in zip(counts, rows)]
    ax.imshow(shares_, cmap=HEAT, vmin=0, vmax=1, aspect="equal")
    n = len(classes)
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    names = [SHORT.get(c, c) for c in classes] if short else classes
    ax.set_xticklabels(names, rotation=60, ha="right", fontsize=label_size, color=style.MUTED)
    ax.set_yticklabels(names if show_y else [""] * n, fontsize=label_size, color=style.MUTED)
    ax.tick_params(length=0)
    ax.set_xticks([i - 0.5 for i in range(n + 1)], minor=True)
    ax.set_yticks([i - 0.5 for i in range(n + 1)], minor=True)
    ax.grid(which="minor", color=style.SURFACE, linewidth=0.8)
    ax.tick_params(which="minor", length=0)
    for side in ax.spines.values():
        side.set_visible(False)
    for i, row in enumerate(counts):
        for j, value in enumerate(row):
            if not value:
                continue
            ax.text(j, i, str(value), ha="center", va="center", fontsize=annotate,
                    color=style.SURFACE if shares_[i][j] > 0.55 else style.INK)
    if title:
        ax.set_title(title, fontsize=7.5, color=style.INK, pad=5)


def figure_18():
    """Ablacioni: shkeljet që arrijnë te përdoruesi dhe çmimi i verifikimit."""
    rows = ablation()
    fig, (left, right) = plt.subplots(1, 2, figsize=(6.6, 3.5), gridspec_kw={"width_ratios": [1.35, 1]})
    fills = [style.FAINT, style.BLUE_TINT, style.BLUE, style.BLUE_DEEP]
    hatches = ["", "//", "", ".."]
    xs = range(len(rows))
    for x, row, fill, hatch in zip(xs, rows, fills, hatches):
        left.bar(x, row["rate"], width=0.62, color=fill, edgecolor=style.INK, linewidth=0.9, hatch=hatch)
        if row["upper_bound"] is not None:
            text = f"0.000\n(≤ {row['upper_bound']:.3f}, 95%)"
        else:
            left.errorbar(x, row["rate"], yerr=[[row["rate"] - row["low"]], [row["high"] - row["rate"]]],
                          color=style.INK, capsize=3, linewidth=0.9)
            text = f"{row['rate']:.2f}"
        left.text(x, row["high"] + 1.6 if row["upper_bound"] is None else 1.6, text, ha="center", va="bottom",
                  fontsize=7.5, color=style.INK)
    left.set_xticks(list(xs))
    left.set_xticklabels([f"{r['letter']}\n{r['short']}" for r in rows], fontsize=7)
    left.set_ylabel("shkelje që arrijnë te përdoruesi\npër 100 fjali (95% CI)", fontsize=7.5, color=style.MUTED)
    left.set_ylim(0, 64)
    left.yaxis.grid(True, color=style.NEUTRAL, linewidth=0.8)
    left.set_axisbelow(True)
    left.set_title("(a) Shkeljet që shohin rregullat", fontsize=8, color=style.INK, loc="left")
    _plain(left)

    # A dhe B nuk kalojnë verifikim, prandaj shablloni rezervë nuk zbatohet (nuk është 0%).
    shares_ = [(r["letter"], r["label"], r["fallback_share"] if r["experiment"] in ("E8", "E9") else None) for r in rows]
    for x, (letter, label, share) in enumerate(shares_):
        if share is None:
            right.text(x, 1.5, "nuk\nzbatohet", ha="center", va="bottom", fontsize=6.5, color=style.FAINT)
            continue
        right.bar(x, 100 * share, width=0.62, color=fills[x], edgecolor=style.INK, linewidth=0.9, hatch=hatches[x])
        right.text(x, 100 * share + 1.6, f"{100 * share:.1f}%", ha="center", va="bottom", fontsize=7.5, color=style.INK)
    right.set_xticks(list(xs))
    right.set_xticklabels([f"{r['letter']}\n{r['short']}" for r in rows], fontsize=7)
    right.set_ylabel("dokumente që shkojnë te shablloni, %", fontsize=7.5, color=style.MUTED)
    right.set_ylim(0, 74)
    right.set_xlim(-0.6, len(rows) - 0.4)
    right.yaxis.grid(True, color=style.NEUTRAL, linewidth=0.8)
    right.set_axisbelow(True)
    right.set_title("(b) Çmimi: shabllon rezervë", fontsize=8, color=style.INK, loc="left")
    _plain(right)

    fig.text(0.01, 0.01, "500 dokumente, OCR, ministral-14b-2512. B = vetëm bazim; C = + rregulla (+ një rigjenerim); D = C + klasifikues.\n«0.000» numëron vetëm shkeljet që rregullat shohin (§6.6.1).",
             fontsize=6.3, color=style.MUTED, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    return fig, rows


def figure_19():
    """Matrica e konfuzionit të statusit (E3, tërë korpusi, me OCR)."""
    classes, counts = status_matrix()
    fig, ax = plt.subplots(figsize=(5.6, 4.9))
    _heatmap(ax, counts, classes, annotate=7.5, label_size=7.5)
    ax.set_xlabel("statusi i dhënë nga sistemi", fontsize=7.5, color=style.MUTED, labelpad=6)
    ax.set_ylabel("statusi i vërtetë", fontsize=7.5, color=style.MUTED, labelpad=6)
    ax.xaxis.set_label_position("top")
    fig.text(0.01, 0.01, "Ngjyra është pjesa e rreshtit (recall); numri është numërimi. 8 832 vlera të përputhura.",
             fontsize=6.3, color=style.MUTED, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    return fig, counts


def figure_20():
    """Matricat e konfuzionit të tre qasjeve (rregulla, klasifikues, gjykatës) mbi dy mostra."""
    data = detectors()
    names = ["Rregullat", "Klasifikuesi XLM-R", "Gjykatësi Claude Sonnet"]
    samples = [("synthetic", "Korpusi i korruptuar (test, 192)"), ("natural", "Grupi B (fjali të autorit, 105)")]
    fig, axes = plt.subplots(2, 3, figsize=(7.0, 6.0))
    used = {}
    for r, (sample, sample_label) in enumerate(samples):
        classes = present_classes(*(data[n][sample]["confusion"]["matrix"] for n in names))
        for c, name in enumerate(names):
            ax = axes[r][c]
            counts = confusion_counts(data[name][sample]["confusion"]["matrix"], classes)
            _heatmap(ax, counts, classes, annotate=5.6, label_size=6.2, show_y=(c == 0), short=True,
                     title=f"{name}\nmacro F1 {data[name][sample]['macro_f1']:.3f}")
            used[(sample, name)] = counts
        axes[r][0].set_ylabel(sample_label, fontsize=7.2, color=style.INK, labelpad=8)
    fig.text(0.01, 0.005, "Rreshti është lloji i vërtetë, kolona lloji i parashikuar; ngjyra është pjesa e rreshtit. "
             "Klasifikuesi: fjalia, rregulli 2 (prag 0.85), ai i vendosur në E9.\nu_ = ungrounded_ (number, analyte, term); omitted_rec = omitted_recommendation.",
             fontsize=6.0, color=style.MUTED, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.045, 1, 1), h_pad=2.6, w_pad=0.6)
    return fig, used


def figure_21():
    """Llojet e shkeljeve: (a) çfarë prodhon modeli, (b) sa mirë i zbulon secili detektor mbi grupin B."""
    rows = ablation()
    data = detectors()
    produced = {r["letter"]: shares(r["by_type_produced"]) for r in rows if r["letter"] in ("A", "B", "C")}
    natural = {name: d["natural"]["per_defect_type"] for name, d in data.items()}
    types = [
        t for t in CLASS_ORDER[1:]
        if any(produced[k].get(t) for k in produced) or any((natural[n].get(t) or {}).get("support") for n in natural)
    ]
    ys = list(range(len(types)))[::-1]

    fig, (left, right) = plt.subplots(1, 2, figsize=(7.0, 4.6), sharey=True, gridspec_kw={"wspace": 0.06})
    # Zhvendosje e vogël vertikale, që shenjat me të njëjtën vlerë (p.sh. F1 = 1.0) të mos mbulojnë njëra-tjetrën.
    markers = {"A": ("o", style.FAINT, 0.18), "B": ("s", style.BLUE, 0.0), "C": ("^", style.BLUE_DEEP, -0.18)}
    names = {"A": "A — pa bazim", "B": "B — vetëm bazim", "C": "C — bazim + rregulla (drafte)"}
    for key, (marker, color, dy) in markers.items():
        xs = [produced[key].get(t, 0) for t in types]
        left.scatter(xs, [y + dy for y in ys], marker=marker, s=30, color=color, edgecolor=style.INK, linewidth=0.7,
                     label=names[key], zorder=3)
    left.set_xlabel("pjesa e shkeljeve të prodhuara nga modeli, %", fontsize=7.5, color=style.MUTED)
    left.set_title("(a) Çfarë prodhon modeli", fontsize=8, color=style.INK, loc="left")

    detector_marks = {
        "Rregullat": ("o", style.INK, 0.27),
        "Klasifikuesi XLM-R": ("s", style.FAINT, 0.09),
        "Gjykatësi Claude Sonnet": ("^", style.BLUE_DEEP, -0.09),
        "Gjykatësi Claude Haiku": ("D", style.BLUE, -0.27),
    }
    for name, (marker, color, dy) in detector_marks.items():
        pts = [(natural[name][t]["f1"], y + dy) for t, y in zip(types, ys)
               if natural[name].get(t) and natural[name][t]["support"] and natural[name][t]["f1"] is not None]
        right.scatter([p[0] for p in pts], [p[1] for p in pts], marker=marker, s=30, color=color,
                      edgecolor=style.INK, linewidth=0.7, label=name, zorder=3)
    for t, y in zip(types, ys):
        if not any((natural[n].get(t) or {}).get("support") for n in natural):
            right.text(0.5, y, "nuk ka mostër në grupin B", ha="center", va="center", fontsize=6.3, color=style.FAINT, style="italic")
    right.set_xlim(-0.05, 1.05)
    right.set_xlabel("F1 i detektimit mbi grupin B", fontsize=7.5, color=style.MUTED)
    right.set_title("(b) Sa mirë zbulohet (fjali natyrale)", fontsize=8, color=style.INK, loc="left")

    left.set_yticks(ys)
    left.set_yticklabels(types, fontsize=7, color=style.INK)
    left.set_xlim(-2, max(60, max(max(v.values()) for v in produced.values()) + 6))
    for ax in (left, right):
        ax.grid(True, axis="both", color=style.NEUTRAL, linewidth=0.8)
        ax.set_axisbelow(True)
        _plain(ax)
    left.legend(loc="upper center", bbox_to_anchor=(0.5, -0.17), fontsize=6.5, frameon=False, ncol=1)
    right.legend(loc="upper center", bbox_to_anchor=(0.5, -0.17), fontsize=6.5, frameon=False, ncol=2)
    fig.subplots_adjust(left=0.25, right=0.985, top=0.93, bottom=0.25)
    return fig, {"types": types, "produced": produced, "natural": natural}
