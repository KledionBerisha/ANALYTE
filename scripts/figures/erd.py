"""
Figura 7 — diagrami entitet-lidhje i bazës së të dhënave.

Tabelat, çelësat primarë, çelësat e huaj dhe kardinaliteti lexohen nga
`Base.metadata` (`persistence/tables.py`), jo nga një kopje e shtypur. Kutitë
tregojnë vetëm çelësat dhe numrin e kolonave të tjera: me njëzet kolona për
gjetje laboratorike, figura do të ishte e palexueshme në gjerësinë e një
faqeje, dhe skema e plotë është Shtojca G.

Vendosja në faqe është e shkruar me dorë; `check_positions` dështon nëse një
tabelë e re nuk ka vend, që figura të mos heqë një tabelë pa u vënë re.
"""

from __future__ import annotations

from sqlalchemy import Table

from analyte.persistence.tables import Base

from . import style

LOGICAL_LINKS: dict[tuple[str, str], str] = {
    ("audit_events", "user_id"): "users",
    ("audit_events", "document_id"): "documents",
    ("cross_references", "assertion_id"): "report_assertions",
    ("cross_references", "finding_id"): "lab_findings",
}
"""Kolona që referojnë një tabelë pa çelës të huaj, me qëllim. Audit: gjurma
duhet të mbijetojë fshirjes së dokumentit (shih `AuditEventRow`). Krahasimet e
kryqëzuara: ruajnë identifikuesit e domenit të pohimeve dhe të gjetjeve. Vizatohen
me vijë të ndërprerë, që të mos duken si lidhje të zbatuara nga baza."""

POSITIONS: dict[str, tuple[float, float]] = {
    "audit_events": (0.95, 5.75),
    "users": (0.95, 4.0),
    "auth_sessions": (0.95, 2.45),
    "refresh_tokens": (0.95, 1.1),
    "login_failures": (3.0, 0.8),
    "registration_attempts": (3.0, 2.3),
    "email_confirmations": (3.0, 5.7),
    "documents": (3.25, 3.6),
}
"""Vendosjet e shkruara me dorë. Fëmijët e `documents` nuk janë këtu: ata
vendosen njëri mbi tjetrin sipas lartësisë së tyre, që kutitë të mos
mbivendosen kur ndryshon numri i çelësave."""

CHILDREN = (
    "lab_findings",
    "cross_references",  # mes dy tabelave që lidhet logjikisht, që vijat e ndërprera të jenë të shkurtra
    "report_assertions",
    "document_glossary",
    "document_unexplained_terms",
    "pattern_observations",
    "processing_jobs",
    "explanations",
)
COLUMN_X = 5.55
GAP = 0.13

VERIFICATION_X = 8.25

WIDTH, HEIGHT = 9.5, 6.9
LINE = 0.135
CHAR = 0.057


def check_positions() -> None:
    tables = {t.name for t in Base.metadata.sorted_tables}
    placed = set(POSITIONS) | set(CHILDREN) | {"verification_results", "violations"}
    missing, extra = tables - placed, placed - tables
    if missing or extra:
        raise ValueError(
            "Figura 7 nuk përputhet me bazën — "
            f"pa vend: {sorted(missing)}; pa tabelë: {sorted(extra)}"
        )
    for (table, column), target in LOGICAL_LINKS.items():
        if column not in Base.metadata.tables[table].c or target not in tables:
            raise ValueError(f"lidhje logjike e vjetruar: {table}.{column} → {target}")


def relations() -> list[tuple[str, str, str, bool, bool]]:
    """(prindi, fëmija, kolona, një-me-një, logjike) për çdo lidhje."""
    found = []
    for table in Base.metadata.sorted_tables:
        for fk in table.foreign_keys:
            found.append(
                (fk.column.table.name, table.name, fk.parent.name, bool(fk.parent.unique), False)
            )
    for (table, column), parent in LOGICAL_LINKS.items():
        found.append((parent, table, column, False, True))
    return found


def _lines(table: Table) -> list[tuple[str, str]]:
    """(etiketa, teksti) për kolonat e çelësave, dhe një rresht për të tjerat."""
    foreign = {fk.parent.name for fk in table.foreign_keys}
    logical = {c for (t, c) in LOGICAL_LINKS if t == table.name}
    rows, other = [], 0
    for column in table.columns:
        if column.primary_key:
            rows.append(("PK", column.name))
        elif column.name in foreign:
            rows.append(("FK", column.name))
        elif column.name in logical:
            rows.append(("ref", column.name))
        else:
            other += 1
    if other:
        rows.append(("", f"+ {other} kolona të tjera"))
    return rows


def _size(table: Table) -> tuple[float, float, list[tuple[str, str]]]:
    lines = _lines(table)
    width = max(
        len(table.name) * 0.064,
        max(len(f"{tag:<3} {text}") for tag, text in lines) * CHAR,
    ) + 0.24
    return width, 0.24 + LINE * len(lines), lines


def _layout(sizes: dict[str, tuple[float, float, list]]) -> dict[str, tuple[float, float]]:
    """Qendrat e kutive: ato të shkruara me dorë, fëmijët e stivuar, dhe zinxhiri
    i verifikimit pranë `explanations`."""
    centers = dict(POSITIONS)
    y = HEIGHT - 0.2
    for name in CHILDREN:
        height = sizes[name][1]
        centers[name] = (COLUMN_X, y - height / 2)
        y -= height + GAP
    explanations_y = centers["explanations"][1]
    verification_h, violations_h = sizes["verification_results"][1], sizes["violations"][1]
    violations_y = max(explanations_y - 0.05, violations_h / 2 + 0.3)
    verification_y = violations_y + violations_h / 2 + 0.3 + verification_h / 2
    centers["verification_results"] = (VERIFICATION_X, verification_y)
    centers["violations"] = (VERIFICATION_X, violations_y)
    return centers


def build():
    check_positions()
    fig, ax = style.canvas(WIDTH, HEIGHT, (0, WIDTH), (0, HEIGHT))

    tables = {t.name: t for t in Base.metadata.sorted_tables}
    sizes = {name: _size(table) for name, table in tables.items()}
    centers = _layout(sizes)

    boxes: dict[str, style.Box] = {}
    for name, table in tables.items():
        width, height, lines = sizes[name]
        cx, cy = centers[name]
        boxes[name] = style.box(ax, cx, cy, width, height, "", fill=style.SURFACE, lw=1.0)
        top = cy + height / 2
        style.box(ax, cx, top - 0.11, width, 0.22, name, fill=style.BLUE_TINT,
                  size=7, weight="bold", lw=1.0)
        for i, (tag, text) in enumerate(lines):
            y = top - 0.22 - LINE * (i + 0.6)
            note = tag == ""
            style.label(ax, cx - width / 2 + 0.09, y, tag, size=6.2,
                        color=style.BLUE_DEEP, ha="left", weight="bold")
            style.label(ax, cx - width / 2 + 0.09 + (0 if note else 0.27), y, text,
                        size=6.2, ha="left", style="italic" if note else "normal",
                        color=style.MUTED if note else style.INK)

    relation_list = relations()
    starts = _fan_starts(boxes, relation_list)
    for parent, child, _column, one_to_one, logical in relation_list:
        a, b = boxes[parent], boxes[child]
        if (parent, child) in starts:
            # Vijë nga e djathta e prindit te e majta e fëmijës: nuk kalon kurrë
            # prapa një kutie tjetre të të njëjtës kolonë.
            start, end = starts[(parent, child)], (b.left, b.cy)
        else:
            start, end = a.anchor((b.cx, b.cy)), b.anchor((a.cx, a.cy))
        style.arrow(ax, start, end, head=False, lw=1.0, ls="--" if logical else "-",
                    color=style.MUTED if logical else style.INK)
        if logical:
            continue
        if (parent, child) in starts:
            # Fëmijët e një kolone ndajnë një "1" të vetëm te prindi; "N" qëndron
            # në të majtë të kutisë së fëmijës, jashtë kornizës.
            style.label(ax, end[0] - 0.13, end[1] + 0.11, "1" if one_to_one else "N",
                        size=6.5, color=style.INK, weight="bold")
        else:
            _mark(ax, start, end, "1")
            _mark(ax, end, start, "1" if one_to_one else "N")
    for parent in {p for p, _ in starts}:
        a = boxes[parent]
        style.label(ax, a.right + 0.12, a.top - 0.05, "1", size=6.5, color=style.INK, weight="bold")

    _key(ax)
    return fig, relations()


def _fan_starts(boxes, relation_list) -> dict[tuple[str, str], tuple[float, float]]:
    """Pikat e nisjes në anën e djathtë të prindit për fëmijët që ndodhen në të
    djathtë të tij, të renditura sipas lartësisë së fëmijës që vijat të mos
    kryqëzohen. Vetëm lidhjet e zbatuara (jo ato logjike)."""
    by_parent: dict[str, list[str]] = {}
    for parent, child, _c, _o, logical in relation_list:
        if not logical and boxes[child].left > boxes[parent].right + 0.1:
            by_parent.setdefault(parent, []).append(child)
    starts = {}
    for parent, children in by_parent.items():
        a = boxes[parent]
        children.sort(key=lambda c: -boxes[c].cy)
        span = a.h / 2 - 0.1
        for index, child in enumerate(children):
            share = 0.5 if len(children) == 1 else index / (len(children) - 1)
            starts[(parent, child)] = (a.right, a.cy + span - 2 * span * share)
    return starts


def _mark(ax, origin, toward, text: str) -> None:
    """Kardinaliteti pranë një skaji, pak mbi vijë."""
    dx, dy = toward[0] - origin[0], toward[1] - origin[1]
    length = max((dx * dx + dy * dy) ** 0.5, 1e-9)
    x = origin[0] + dx / length * 0.17 - dy / length * 0.09
    y = origin[1] + dy / length * 0.17 + dx / length * 0.09
    style.label(ax, x, y, text, size=6.5, color=style.INK, weight="bold")


def _key(ax) -> None:
    style.label(ax, 0.1, 0.3, "PK çelës primar  ·  FK çelës i huaj  ·  1 — N  një prind, shumë fëmijë",
                size=6.8, ha="left")
    style.label(ax, 0.1, 0.1, "vija e ndërprerë (ref): lidhje logjike pa çelës të huaj, me qëllim",
                size=6.8, ha="left")
