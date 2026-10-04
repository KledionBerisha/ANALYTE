"""
Figurat 1–5, 9 dhe 10 — diagramet konceptuale të Kapitullit 5.

Rrugët e sistemit nuk vizatohen nga fantazia: ku kodi ka një listë (rregullat
R1–R9, llojet e defekteve, gjendjet e krahasimit të kryqëzuar, përpjekjet e
gjenerimit, ndarja e korpusit, numri i analiteve) figura e lexon atë listë, dhe
një test kontrollon që ajo që është shkruar në kuti përputhet me burimin.
Vendosja në faqe është e vetmja gjë e shkruar me dorë.

Kodimi është i njëjtë në të gjitha figurat dhe nuk mbështetet te ngjyra vetëm:
  kuti me vijë të plotë  — hap deterministe;
  kuti me vijë me pika    — hap i mësuar ose statistikor (modeli gjuhësor, klasifikuesi);
  kuti e theksuar (blu)   — kontributi qendror i figurës;
  kuti me skaj gri        — hyrje ose dalje e përpunimit.
"""

from __future__ import annotations

from matplotlib.patches import FancyBboxPatch

from analyte.catalog import load_patterns, load_terminology
from analyte.domain.enums import CrossReferenceState
from analyte.domain.policy import MAX_GENERATION_ATTEMPTS, RULE_CATALOG

from . import style

DET, MODEL, KEY, IO = "det", "model", "key", "io"
_KINDS = {
    DET: dict(fill=style.SURFACE, edge=style.INK, ls="-"),
    MODEL: dict(fill=style.NEUTRAL, edge=style.INK, ls=(0, (3, 2))),
    KEY: dict(fill=style.BLUE_TINT, edge=style.BLUE_DEEP, ls="-"),
    IO: dict(fill=style.SURFACE, edge=style.FAINT, ls="-"),
}

UNIT = 0.5
"""Inç për njësi të të dhënave: të gjitha figurat janë 6.5 inç të gjera mbi 13 njësi."""


def node(ax, cx, cy, w, h, title, sub="", kind=DET, *, title_size=7.4, sub_size=6.3) -> style.Box:
    """Kuti me titull të trashë dhe, nën të, rreshta shpjegues; blloku qendërzohet vertikalisht."""
    spec = _KINDS[kind]
    box = style.box(ax, cx, cy, w, h, "", fill=spec["fill"], edge=spec["edge"], ls=spec["ls"], lw=1.2)
    t_lines = title.count("\n") + 1
    s_lines = (sub.count("\n") + 1) if sub else 0
    t_h, s_h = t_lines * 0.27, s_lines * 0.23
    gap = 0.13 if sub else 0.0
    block = t_h + gap + s_h
    top = cy + block / 2
    ax.text(cx, top - t_h / 2, title, ha="center", va="center", fontsize=title_size, fontweight="bold",
            color=style.INK, zorder=6, linespacing=1.15)
    if sub:
        ax.text(cx, top - t_h - gap - s_h / 2, sub, ha="center", va="center", fontsize=sub_size,
                color=style.MUTED, zorder=6, linespacing=1.2)
    return box


def frame(ax, x0, y0, x1, y1, title="", *, ls=(0, (2, 2)), edge=style.FAINT, title_size=6.8):
    """Kornizë me vija rreth një grupi kutish."""
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0,rounding_size=0.07",
                                fill=False, edgecolor=edge, linewidth=0.9, linestyle=ls, zorder=1))
    if title:
        ax.text((x0 + x1) / 2, y1 - 0.28, title, ha="center", va="center", fontsize=title_size,
                fontweight="bold", color=style.INK, zorder=6)


def legend(ax, y, *, kinds=(DET, MODEL, KEY, IO), x=0.3, width=12.6):
    names = {DET: "hap deterministe", MODEL: "hap i mësuar", KEY: "kontributi qendror",
             IO: "hyrje ose dalje"}
    step_ = width / len(kinds)
    for i, kind in enumerate(kinds):
        cx = x + step_ * i + 0.35
        spec = _KINDS[kind]
        style.box(ax, cx, y, 0.6, 0.36, "", fill=spec["fill"], edge=spec["edge"], ls=spec["ls"], lw=1.0)
        ax.text(cx + 0.5, y, names[kind], ha="left", va="center", fontsize=6.3, color=style.MUTED, zorder=6)


def path(ax, points, *, head=True, **kw):
    """Shigjetë me kthesa: segmente të drejta, koka vetëm te i fundit."""
    for i, (a, b) in enumerate(zip(points, points[1:])):
        style.arrow(ax, a, b, head=head and i == len(points) - 2, **kw)


def flow(ax, a: style.Box, b: style.Box, *, dashed=False):
    """Shigjetë e drejtë nga një kuti te tjetra, ndërmjet skajeve."""
    style.connect(ax, a, b, ls="--" if dashed else "-")


def note(ax, x, y, text, *, ha="center", size=6.2, rotation=0, color=style.MUTED, italic=False):
    ax.text(x, y, text, ha=ha, va="center", fontsize=size, color=color, rotation=rotation, zorder=6,
            fontstyle="italic" if italic else "normal", linespacing=1.2)


# ---------------------------------------------------------------------------
# Figura 1 — fazat e zhvillimit
# ---------------------------------------------------------------------------

PHASES = [
    "Shtrirja dhe shqyrtimi\ni literaturës",
    "Gjeneruesi i të dhënave\nsintetike",
    "Infrastruktura\ne vlerësimit",
    "Dega\nlaboratorike",
    "Dega e raportit\nmjekësor",
    "Gjenerimi dhe verifikimi\nme rregulla",
    "Klasifikuesi i\nverifikimit",
    "Eksperimentet\ndhe ablacioni",
    "Aplikacioni\nweb",
]


def figure_01():
    """Nëntë fazat; fazat 2 dhe 3 (baza e matjes) paraprijnë të gjitha fazat e mëpasme."""
    fig, ax = style.canvas(6.5, 5.3, (0, 13), (-1.2, 10.0))
    w, h = 3.7, 1.55
    y1, y2, y3 = 8.6, 5.5, 2.4
    n: dict[int, style.Box] = {}
    n[1] = node(ax, 2.1, y1, w, h, "1", PHASES[0], IO)
    n[2] = node(ax, 6.5, y1, w, h, "2", PHASES[1], KEY)
    n[3] = node(ax, 10.9, y1, w, h, "3", PHASES[2], KEY)
    frame(ax, 8.85, y2 - 1.2, 12.95, y2 + 1.2)
    n[4] = node(ax, 9.95, y2, 1.85, 1.55, "4", PHASES[3], DET, sub_size=6.0)
    n[5] = node(ax, 11.85, y2, 1.85, 1.55, "5", PHASES[4], DET, sub_size=6.0)
    n[6] = node(ax, 5.2, y2, w, h, "6", PHASES[5], KEY)
    n[7] = node(ax, 1.5, y2, 2.7, h, "7", PHASES[6], MODEL)
    n[8] = node(ax, 2.1, y3, w, h, "8", PHASES[7], DET)
    n[9] = node(ax, 6.5, y3, w, h, "9", PHASES[8], DET)
    flow(ax, n[1], n[2])
    flow(ax, n[2], n[3])
    style.arrow(ax, (10.9, y1 - h / 2), (10.9, y2 + 1.2))
    style.arrow(ax, (8.85, y2), (n[6].right, y2))
    style.arrow(ax, (n[6].left, y2), (n[7].right, y2))
    style.arrow(ax, (1.5, y2 - h / 2), (1.5, y3 + h / 2 + 0.0))
    flow(ax, n[8], n[9])
    note(ax, 10.9, y3 + 0.25, "Fazat 2 dhe 3 prodhojnë të dhënat\ndhe mjetet matëse; paraprijnë 4–9.\nShigjetat tregojnë varësitë.", size=6.4)
    legend(ax, -0.7)
    return fig, n


# ---------------------------------------------------------------------------
# Figura 2 — arkitektura e përgjithshme
# ---------------------------------------------------------------------------


def figure_02():
    """Pesë shtresat dhe rrjedha e të dhënave; PostgreSQL mban gjendjen dhe gjurmën e auditimit."""
    fig, ax = style.canvas(6.5, 6.7, (0, 13), (-1.5, 12.9))
    cx, w = 5.0, 9.4
    pres = node(ax, cx, 11.8, w, 1.3, "Shtresa e prezantimit", "Next.js, React; ndërfaqe në shqip")
    api = node(ax, cx, 9.9, w, 1.3, "Shtresa e API-së", "FastAPI, REST; hyrje me JWT dhe seanca të revokueshme")
    orch = node(ax, cx, 7.9, w, 1.6, "Shtresa e orkestrimit", "arq mbi Redis; makina e gjendjeve (Figura 6),\nrigjenerimi dhe shablloni rezervë")
    frame(ax, 0.3, 3.2, 9.7, 6.6, edge=style.INK, ls="-")
    ax.text(cx, 6.25, "Shtresa e bazimit (determinist)", ha="center", va="center", fontsize=7.4, fontweight="bold", color=style.INK, zorder=6)
    a = node(ax, 2.1, 4.55, 2.7, 1.4, "Dega A", "rezultate\nlaboratorike")
    b = node(ax, 5.0, 4.55, 2.7, 1.4, "Dega B", "raporti\nmjekësor")
    ctx = node(ax, 8.2, 4.55, 2.7, 1.4, "GroundingContext", "objekti i vetëm\ni kalimit", KEY, title_size=6.9)
    # bus: të dyja degët kanë dalje te konteksti
    path(ax, [(a.cx, a.bottom), (a.cx, 3.7), (ctx.cx - 0.8, 3.7)], head=False)
    path(ax, [(b.cx, b.bottom), (b.cx, 3.7)], head=False)
    style.arrow(ax, (ctx.cx - 0.8, 3.7), (ctx.cx - 0.8, ctx.bottom))
    gen = node(ax, cx, 2.15, w, 1.2, "Gjenerimi", "shablloni determinist (parazgjedhja) ose modeli gjuhësor, zgjedhje e\nshprehur; modeli merr vetëm GroundingContext", MODEL)
    ver = node(ax, cx, 0.35, w, 1.3, f"Shtresa e verifikimit", f"R1–R9 + SP1–SP3, pastaj klasifikuesi; deri në {MAX_GENERATION_ATTEMPTS} përpjekje", KEY)
    # rrjedha
    style.arrow(ax, (cx - 0.5, pres.bottom), (cx - 0.5, api.top))
    style.arrow(ax, (cx + 0.5, api.top), (cx + 0.5, pres.bottom), color=style.MUTED)
    note(ax, cx + 0.8, 10.8, "REST", ha="left")
    style.arrow(ax, (cx, api.bottom), (cx, orch.top))
    style.arrow(ax, (cx, orch.bottom), (cx, 6.6))
    style.arrow(ax, (ctx.cx + 0.8, ctx.bottom), (ctx.cx + 0.8, gen.top))
    style.arrow(ax, (cx, gen.bottom), (cx, ver.top))
    # kthimi: teksti i verifikuar ose rezervë
    path(ax, [(9.7, 0.35), (10.2, 0.35), (10.2, 7.9), (9.7, 7.9)], color=style.MUTED, ls="--")
    note(ax, 9.98, 4.1, "teksti i verifikuar ose rezervë", rotation=90, size=5.8)
    db = node(ax, 11.85, 5.4, 2.1, 9.6, "PostgreSQL", "ruan gjendjen,\ngjetjet,\nshpjegimet dhe\ngjurmën e\nauditimit për\nshtresat 2–5;\nskedarët janë\nnë ruajtje të\nenkriptuar", IO, sub_size=6.0)
    legend(ax, -1.05)
    return fig, {"api": api, "db": db}


# ---------------------------------------------------------------------------
# Figura 3 — dega laboratorike
# ---------------------------------------------------------------------------


def figure_03():
    """Fazat e degës A; OCR-ja është rruga e dytë e fazës së parë, kombinimet vijnë pas klasifikimit."""
    fig, ax = style.canvas(6.5, 4.6, (0, 13), (-1.3, 8.4))
    y1, y2, y3 = 6.9, 4.0, 1.4
    pdf = node(ax, 1.25, y1, 1.9, 1.4, "PDF", "dokumenti\ni ngarkuar", IO, sub_size=6.0)
    route = node(ax, 4.15, y1, 3.1, 1.6, "1 · Rrugëzimi", "ka shtresë teksti\ntë përdorshme?", sub_size=6.0)
    rows = node(ax, 8.0, y1, 3.0, 1.6, "2 · Rindërtimi", "i rreshtave nga koordinatat\ne fjalëve", sub_size=6.0)
    norm = node(ax, 11.35, y1, 2.8, 1.6, "3 · Normalizimi", "emri → LOINC;\nnjësitë", sub_size=6.0)
    ocr = node(ax, 4.15, y2 - 0.1, 3.1, 1.3, "OCR", "Tesseract, pas drejtimit\ntë faqes", MODEL, sub_size=6.0)
    ref = node(ax, 11.2, y2, 3.0, 1.6, "4 · Intervali referent", "dokumenti; në mungesë,\ntabela e brendshme", sub_size=6.0, title_size=7.0)
    cls = node(ax, 7.75, y2, 3.1, 1.6, "5 · Klasifikimi", "sipas intervalit; pa interval:\ni painterpretueshëm (SP5)", sub_size=6.0)
    out = node(ax, 7.75, y3, 3.9, 1.5, "Gjetjet e strukturuara", "me koordinata; rreshtat e hedhur\nruhen me arsyen (faza 6)", KEY, sub_size=6.0)
    patterns = load_patterns()
    pat = node(ax, 2.9, y3, 3.3, 1.3, "Kombinimet", f"{len(patterns)} rregulla {patterns[0].pattern_id}–{patterns[-1].pattern_id}\nmbi gjetjet", DET, sub_size=6.0)
    flow(ax, pdf, route)
    style.arrow(ax, (route.right, y1), (rows.left, y1))
    note(ax, (route.right + rows.left) / 2, y1 + 0.45, "po", size=6.0)
    flow(ax, rows, norm)
    style.arrow(ax, (route.cx, route.bottom), (route.cx, ocr.top), ls="--", color=style.MUTED)
    note(ax, route.cx + 0.25, 5.2, "jo", ha="left", size=6.0)
    path(ax, [(ocr.right, ocr.cy), (6.1, ocr.cy), (6.1, y1 - 0.4), (rows.left, y1 - 0.4)], ls="--", color=style.MUTED)
    style.arrow(ax, (norm.cx, norm.bottom), (norm.cx, ref.top))
    style.arrow(ax, (ref.left, y2), (cls.right, y2))
    style.arrow(ax, (cls.cx, cls.bottom), (cls.cx, out.top))
    style.arrow(ax, (out.left, y3), (pat.right, y3))
    note(ax, (out.left + pat.right) / 2, y3 + 0.4, "mbi gjetjet", size=5.8)
    legend(ax, -0.9)
    return fig, {"route": route, "out": out}


# ---------------------------------------------------------------------------
# Figura 4 — dega e raportit mjekësor
# ---------------------------------------------------------------------------

CROSS_LABELS = {
    CrossReferenceState.AGREEMENT: "përputhje",
    CrossReferenceState.CONTRADICTION: "kundërshtim",
    CrossReferenceState.MENTIONED_NOT_MEASURED: "përmendur, jo matur",
    CrossReferenceState.MEASURED_NOT_MENTIONED: "matur, jo përmendur",
}


def figure_04():
    """Pesë hapat e degës B; krahasimi i kryqëzuar ka katër gjendje të mundshme."""
    fig, ax = style.canvas(6.5, 4.4, (0, 13), (-0.6, 8.8))
    y1, y2 = 7.2, 4.1
    doc = node(ax, 1.2, y1, 1.9, 1.4, "Teksti", "i nxjerrë nga\ndokumenti", IO, sub_size=6.0)
    seg = node(ax, 4.2, y1, 3.2, 1.6, "1 · Gjetja e narrativës", "nën titullin e vet;\nndarja në fjali", sub_size=6.0, title_size=7.0)
    term = node(ax, 7.8, y1, 3.2, 1.6, "2 · Njohja e termave", f"tabela terminologjike\n({len(load_terminology())} terma): gjendet ose jo", sub_size=6.0, title_size=7.0)
    neg = node(ax, 11.4, y1, 3.0, 1.6, "3 · Mohimi dhe\npasiguria", "shenja si NegEx;\nshprehje rezerve", sub_size=6.0, title_size=7.0)
    asr = node(ax, 11.4, y2, 3.0, 1.6, "4 · Pohimet", "një pohim për fjali, me\nllojin, polaritetin, sigurinë", sub_size=5.8)
    xref = node(ax, 7.5, y2, 3.4, 1.6, "5 · Krahasimi i kryqëzuar", "pohimet kundrejt\ngjetjeve laboratorike", KEY, sub_size=6.0, title_size=7.0)
    ctx = node(ax, 3.4, y2, 3.0, 1.6, "GroundingContext", "së bashku me\ndegën A", IO, sub_size=6.0, title_size=6.9)
    flow(ax, doc, seg)
    flow(ax, seg, term)
    flow(ax, term, neg)
    style.arrow(ax, (neg.cx, neg.bottom), (neg.cx, asr.top))
    style.arrow(ax, (asr.left, y2), (xref.right, y2))
    style.arrow(ax, (xref.left, y2), (ctx.right, y2))
    labels = list(CROSS_LABELS.values())
    note(ax, 6.5, 1.85, "Gjendja e çdo krahasimi:", size=6.8, color=style.INK)
    for i, text in enumerate(labels):
        cx = 1.85 + i * 3.1
        style.box(ax, cx, 0.75, 2.9, 0.65, text, size=6.6, edge=style.INK, fill=style.SURFACE)
    style.arrow(ax, (xref.cx, xref.bottom), (xref.cx, 2.1), ls=(0, (1, 2)), color=style.FAINT, head=False)
    return fig, {"states": labels}


# ---------------------------------------------------------------------------
# Figura 5 — shtresa e verifikimit
# ---------------------------------------------------------------------------


def rule_ranges() -> dict[str, str]:
    """Rregullat e katalogut sipas degës, si «R1–R4»; SP-të (rregulla politike) numërohen veçmas."""
    ranges = {}
    for branch in ("A", "B"):
        ids = [r.id for r in RULE_CATALOG if r.branch == branch and r.id.startswith("R")]
        ranges[branch] = f"{ids[0]}–{ids[-1]}"
    return ranges


def figure_05():
    """Rregullat (nga katalogu), klasifikuesi, bashkimi i flamujve dhe vendimi."""
    ranges = rule_ranges()
    fig, ax = style.canvas(6.5, 5.5, (0, 13), (-1.3, 10.0))
    inp = node(ax, 2.7, 8.6, 3.4, 1.4, "Teksti i gjeneruar", "+ GroundingContext\n(konteksti i plotë)", IO, sub_size=6.0)
    rules = node(ax, 8.4, 8.6, 5.4, 2.1, "Rregullat deterministe",
                 f"A: {ranges['A']}  numra, analite, drejtim, kritike\n"
                 f"B: {ranges['B']}  polaritet, siguri, gjetje të reja,\nrekomandime, terma\n"
                 "SP1–SP3  diagnozë, trajtim, prognozë", KEY, sub_size=6.0)
    clf = node(ax, 8.4, 5.5, 5.4, 1.5, "Klasifikuesi XLM-R", "sheh fjalinë (varianti i dytë: edhe një\npërmbledhje e shkurtër e kontekstit)", MODEL, sub_size=6.0)
    union = node(ax, 8.4, 3.2, 5.4, 1.2, "Bashkimi i flamujve", "çdo flamur nga cilado qasje është shkelje", DET, sub_size=6.0)
    ok = node(ax, 2.7, 3.2, 3.4, 1.2, "Pa shkelje", "i dorëzohet përdoruesit", IO, sub_size=6.0)
    bad = node(ax, 8.4, 0.85, 5.4, 1.4, "Me shkelje", f"rigjenerim me përshkrimin e shkeljes;\npas {MAX_GENERATION_ATTEMPTS} përpjekjesh: shablloni (SP8)", DET, sub_size=6.0)
    style.arrow(ax, (inp.right, inp.cy), (rules.left, inp.cy))
    style.arrow(ax, (rules.cx, rules.bottom), (rules.cx, clf.top))
    note(ax, rules.cx + 0.2, 7.15 - 0.05, "rregullat ekzekutohen të parat", ha="left", size=6.0)
    style.arrow(ax, (clf.cx, clf.bottom), (clf.cx, union.top))
    # flamujt e rregullave shkojnë drejt te bashkimi, jo përmes klasifikuesit
    path(ax, [(rules.left, rules.cy - 0.6), (5.0, rules.cy - 0.6), (5.0, union.cy), (union.left, union.cy)], color=style.MUTED, ls="--")
    note(ax, 4.85, 6.0, "flamujt e rregullave", rotation=90, size=5.8)
    style.arrow(ax, (union.left - 0.0, union.cy - 0.35), (ok.right, ok.cy - 0.35))
    style.arrow(ax, (union.cx, union.bottom), (union.cx, bad.top))
    path(ax, [(bad.left, bad.cy), (0.3, bad.cy), (0.3, inp.cy), (inp.left, inp.cy)], color=style.MUTED, ls="--")
    note(ax, 0.58, 4.6, "teksti i ri verifikohet sërish", rotation=90, size=5.8)
    legend(ax, -0.85)
    return fig, ranges


# ---------------------------------------------------------------------------
# Figura 9 — gjenerimi i korpusit sintetik
# ---------------------------------------------------------------------------


def figure_09():
    """Rendi i veprimeve për çdo dokument; e vërteta bazë rillogaritet pas shtypjes."""
    from analyte.catalog import load_analytes

    n_analytes = len(load_analytes())
    fig, ax = style.canvas(6.5, 5.0, (0, 13), (-1.2, 9.6))
    w, h = 3.7, 1.55
    y1, y2, y3 = 8.2, 5.2, 2.0
    src = node(ax, 2.1, y1, w, h, "Tabelat burimore + fara", f"{n_analytes} analite, njësi, terma;\nçdo dokument ka farën e vet", IO, sub_size=6.0)
    tgt = node(ax, 6.5, y1, w, h, "1 · Statusi i synuar", "pastaj kampionohet një vlerë\nqë e plotëson", sub_size=6.0)
    prt = node(ax, 10.9, y1, w, h, "2 · Mënyra e shtypjes", "njësia, intervali, presja, flamuj;\n3 formate faqeje", sub_size=6.0)
    tru = node(ax, 10.9, y2, w, h, "3 · E vërteta bazë", "statusi rillogaritet mbi vlerën dhe\nintervalin ashtu si u shtypën", KEY, sub_size=6.0)
    pdf = node(ax, 6.5, y2, w, h, "4 · PDF dixhital", "tekst dhe narrativa;\nkoordinata të njohura", sub_size=6.0)
    scan = node(ax, 2.1, y2, w, h, "5 · Skanim i simuluar", "për rreth një të tretën: rrotullim,\nzhurmë, pa shtresë teksti", MODEL, sub_size=6.0)
    frame(ax, 0.25, y3 - 1.05, 12.75, y3 + 1.05, "")
    note(ax, 6.5, y3 + 0.82, "Dalja e korpusit", size=6.8, color=style.INK)
    pdfs = node(ax, 2.1, y3 - 0.1, 3.5, 1.2, "PDF", "dixhitale dhe të skanuara", IO, sub_size=6.0)
    gt = node(ax, 6.5, y3 - 0.1, 3.5, 1.2, "E vërteta bazë", "JSON; sistemi nuk e sheh kurrë", IO, sub_size=6.0)
    man = node(ax, 10.9, y3 - 0.1, 3.5, 1.2, "Manifesti", "versioni, fara, shumat e burimeve", IO, sub_size=5.8)
    flow(ax, src, tgt)
    flow(ax, tgt, prt)
    style.arrow(ax, (prt.cx, prt.bottom), (prt.cx, tru.top))
    style.arrow(ax, (tru.left, y2), (pdf.right, y2))
    style.arrow(ax, (pdf.left, y2), (scan.right, y2), ls="--")
    style.arrow(ax, (scan.cx, scan.bottom), (scan.cx, y3 + 1.05))
    path(ax, [(pdf.cx, pdf.bottom), (pdf.cx, 3.85), (3.2, 3.85), (3.2, y3 + 1.05)])
    path(ax, [(tru.cx, tru.bottom), (tru.cx, 3.85), (6.9, 3.85), (6.9, y3 + 1.05)])
    legend(ax, -0.75)
    return fig, {"analytes": n_analytes}


# ---------------------------------------------------------------------------
# Figura 10 — korpusi i korruptuar
# ---------------------------------------------------------------------------


def figure_10():
    """Teksti i pastër i shabllonit, saktësisht një defekt i injektuar, etiketë automatike."""
    from ml.data.build_corruption_set import CORRUPTORS, SPLIT_WEIGHTS, SPLITS

    names = [v.value for v, _ in CORRUPTORS]
    fig, ax = style.canvas(6.5, 5.3, (0, 13), (-1.2, 10.0))
    ctx = node(ax, 1.9, 8.6, 3.3, 1.3, "GroundingContext", "një për dokument burimor", IO, sub_size=6.0, title_size=6.9)
    tpl = node(ax, 6.0, 8.6, 3.8, 1.3, "Teksti i pastër", "shablloni; kalon çdo rregull", sub_size=6.0)
    clean = node(ax, 1.9, 5.3, 3.3, 1.5, "Mostër e pastër", "teksti origjinal,\npa defekt", IO, sub_size=6.0)
    lab = node(ax, 6.0, 5.3, 3.8, 1.9, "Mostër e etiketuar", "teksti me defekt dhe lloji i\ndefektit, nga vetë korruptimi\n(pa anotim me dorë)", KEY, sub_size=6.0)
    split = node(ax, 4.3, 1.8, 7.2, 1.6, "Ndarja sipas dokumentit burimor",
                 "  ·  ".join(f"{s} {int(round(100 * wt))}%" for s, wt in zip(SPLITS, SPLIT_WEIGHTS))
                 + "\nmostrat e një dokumenti nuk ndahen mes grupeve", sub_size=6.0)
    frame(ax, 8.6, 1.2, 12.85, 9.5)
    note(ax, 10.72, 9.15, f"{len(names)} defekte; saktësisht\nnjë për mostër", size=6.6, color=style.INK)
    for i, name in enumerate(names):
        style.box(ax, 10.72, 8.0 - i * 0.98, 3.7, 0.7, name, size=5.9, mono=True, edge=style.INK, fill=style.SURFACE)
    flow(ax, ctx, tpl)
    style.arrow(ax, (tpl.right, tpl.cy), (8.6, tpl.cy))
    style.arrow(ax, (8.6, lab.cy), (lab.right, lab.cy))
    style.arrow(ax, (tpl.cx - 1.0, tpl.bottom), (clean.right - 0.3, clean.top), )
    style.arrow(ax, (clean.cx, clean.bottom), (clean.cx, split.top))
    style.arrow(ax, (lab.cx, lab.bottom), (lab.cx, split.top))
    legend(ax, -0.75)
    return fig, {"defects": names, "splits": list(SPLITS)}
