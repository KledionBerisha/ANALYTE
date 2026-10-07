"""
Vizatimi i dokumentit sintetik në PDF.

Ky modul është i vetmi vend ku e vërteta bazë kthehet në diçka që
sistemi mund ta shohë. Prandaj ai nuk vendos asgjë: çdo varg që shtypet
vjen gati nga `PrintedRow`, dhe faqja e çdo rreshti është llogaritur më
parë nga `ground_truth`. Vizatuesi vetëm i vendos ato në letër dhe
kthen koordinatat.

"""

from __future__ import annotations

import io
from dataclasses import dataclass
from uuid import UUID

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas

from analyte.domain.models import BoundingBox

from .ground_truth import LINES_PER_PAGE, DocumentTruth, PrintedRow, page_for_line

PAGE_WIDTH, PAGE_HEIGHT = A4

MARGIN_X = 56.0
BODY_TOP = PAGE_HEIGHT - 200.0
"""Ku fillon trupi i tabelës.

Mbi të rrinë titulli i laboratorit, blloku i pacientit dhe koka e
kolonave. Ulja e kësaj vlere nën lartësinë e atij blloku i shkel ato mbi
njëra-tjetrën — gabim që nuk duket në asnjë test dhe duket menjëherë në
faqe."""

SEX_LABELS = {"M": "Mashkull", "F": "Femër"}


@dataclass(frozen=True, slots=True)
class Layout:
    """Pozicionet dhe madhësitë e një formati faqeje.

    `value_x` është skaji i djathtë i kolonës së vlerës: vlerat
    rreshtohen djathtas si në raportet reale, që presja dhjetore të bjerë
    në të njëjtën vijë.
    """

    name: str
    font: str
    font_size: float
    line_height: float
    name_x: float
    value_x: float
    unit_x: float
    interval_x: float
    flag_x: float
    unit_joined: bool
    """Njësia ngjitet pas vlerës në të njëjtën qelizë në vend që të ketë
    kolonë të vetën — ndryshim i vogël në pamje, i madh për segmentimin."""
    rules: bool
    """Vija ndarëse nën titullin e panelit dhe nën kokën e kolonave."""
    two_column_header: bool


LAYOUTS: dict[str, Layout] = {
    "tabelor": Layout(
        name="tabelor",
        font="Helvetica",
        font_size=9.0,
        line_height=16.0,
        name_x=MARGIN_X,
        value_x=300.0,
        unit_x=310.0,
        interval_x=390.0,
        flag_x=520.0,
        unit_joined=False,
        rules=True,
        two_column_header=False,
    ),
    "kompakt": Layout(
        name="kompakt",
        font="Helvetica",
        font_size=8.0,
        line_height=14.0,
        name_x=MARGIN_X,
        value_x=280.0,
        unit_x=286.0,
        interval_x=380.0,
        flag_x=500.0,
        unit_joined=True,
        rules=False,
        two_column_header=False,
    ),
    "dykolonësh": Layout(
        name="dykolonësh",
        font="Helvetica",
        font_size=9.5,
        line_height=17.0,
        name_x=MARGIN_X,
        value_x=290.0,
        unit_x=300.0,
        interval_x=375.0,
        flag_x=515.0,
        unit_joined=False,
        rules=True,
        two_column_header=True,
    ),
}


def render_document(document: DocumentTruth) -> tuple[bytes, dict[UUID, BoundingBox]]:
    """Vizaton dokumentin dhe kthen PDF-në bashkë me kutitë e rreshtave."""
    layout = LAYOUTS[document.lab.layout]
    buffer = io.BytesIO()
    # invariant=1: pa të, reportlab-i shkruan vulën e kohës dhe një
    # identifikues të rastësishëm dokumenti, dhe dy ekzekutime me të
    # njëjtin seed do të jepnin PDF të ndryshëm (NFR3).
    canvas = Canvas(buffer, pagesize=A4, invariant=1)
    canvas.setTitle(f"Raport laboratorik — {document.lab.lab_name}")

    boxes: dict[UUID, BoundingBox] = {}
    line = 0
    page = 1
    _draw_page_header(canvas, document, layout)

    for panel_title, rows in _group_rows(document):
        if page_for_line(line) != page:
            page = _next_page(canvas, document, layout, page)
        _draw_panel_title(canvas, layout, panel_title, _y_for(line, layout))
        line += 1

        for row in rows:
            if page_for_line(line) != page:
                page = _next_page(canvas, document, layout, page)
            y = _y_for(line, layout)
            _draw_row(canvas, layout, row, y)
            boxes[row.finding_id] = _box_for(layout, y)
            assert row.page == page, (
                f"paginimi i vizatuesit nuk përputhet me të vërtetën bazë: "
                f"rreshti pret faqen {row.page}, vizatuesi është te {page}"
            )
            line += 1

    _draw_narrative(canvas, document, layout, line, page)
    canvas.showPage()
    canvas.save()
    return buffer.getvalue(), boxes


def _group_rows(document: DocumentTruth) -> list[tuple[str, list[PrintedRow]]]:
    """Rreshtat e grupuar sipas panelit, në rendin e shtypjes."""
    groups: list[tuple[str, list[PrintedRow]]] = []
    for row in document.rows:
        if not groups or groups[-1][0] != row.panel_title:
            groups.append((row.panel_title, []))
        groups[-1][1].append(row)
    return groups


def _y_for(line: int, layout: Layout) -> float:
    """Vija bazë e rreshtit të dhënë, brenda faqes së vet."""
    return BODY_TOP - (line % LINES_PER_PAGE) * layout.line_height


def _next_page(canvas: Canvas, document: DocumentTruth, layout: Layout, page: int) -> int:
    canvas.showPage()
    _draw_page_header(canvas, document, layout, continued=True)
    return page + 1


def _draw_page_header(
    canvas: Canvas, document: DocumentTruth, layout: Layout, *, continued: bool = False
) -> None:
    """Blloku i kokës: laboratori, pacienti, data.

    Këtu qëndron edhe emri i pacientit. Ai është i trilluar dhe nuk hyn
    kurrë në GroundingContext; roli i tij është vetëm të zërë vendin e një
    bllloku teksti që nxjerrja duhet ta kapërcejë pa e ngatërruar me të
    dhëna laboratorike.
    """
    canvas.setFont("Helvetica-Bold", 13)
    canvas.drawString(MARGIN_X, PAGE_HEIGHT - 60, document.lab.lab_name)

    canvas.setFont(layout.font, layout.font_size)
    sex = SEX_LABELS[document.patient_sex.value]
    left = [
        f"Pacienti: {document.patient_name}",
        f"Gjinia: {sex}",
        f"Mosha: {document.patient_age} vjeç",
    ]
    right = [
        f"Data e analizës: {document.measured_at.strftime('%d.%m.%Y')}",
        f"Nr. i protokollit: {str(document.document_id)[:8].upper()}",
        "Materiali: gjak venoz",
    ]

    if layout.two_column_header:
        for index, text in enumerate(left):
            canvas.drawString(MARGIN_X, PAGE_HEIGHT - 90 - index * 14, text)
        for index, text in enumerate(right):
            canvas.drawString(320, PAGE_HEIGHT - 90 - index * 14, text)
    else:
        for index, text in enumerate(left + right):
            canvas.drawString(MARGIN_X, PAGE_HEIGHT - 90 - index * 12, text)

    if continued:
        canvas.setFont(layout.font, layout.font_size - 1)
        canvas.drawRightString(PAGE_WIDTH - MARGIN_X, PAGE_HEIGHT - 60, "vazhdim")

    if layout.rules:
        canvas.setLineWidth(0.6)
        canvas.line(MARGIN_X, BODY_TOP + 20, PAGE_WIDTH - MARGIN_X, BODY_TOP + 20)
        canvas.setFont("Helvetica-Bold", layout.font_size - 0.5)
        canvas.drawString(layout.name_x, BODY_TOP + 26, "Analiti")
        canvas.drawRightString(layout.value_x, BODY_TOP + 26, "Rezultati")
        if not layout.unit_joined:
            canvas.drawString(layout.unit_x, BODY_TOP + 26, "Njësia")
        canvas.drawString(layout.interval_x, BODY_TOP + 26, "Intervali referent")
        canvas.setFont(layout.font, layout.font_size)


def _draw_panel_title(canvas: Canvas, layout: Layout, title: str, y: float) -> None:
    canvas.setFont("Helvetica-Bold", layout.font_size + 0.5)
    canvas.drawString(MARGIN_X, y, title)
    canvas.setFont(layout.font, layout.font_size)
    if layout.rules:
        canvas.setLineWidth(0.3)
        canvas.line(MARGIN_X, y - 4, PAGE_WIDTH - MARGIN_X, y - 4)


def _draw_row(canvas: Canvas, layout: Layout, row: PrintedRow, y: float) -> None:
    canvas.drawString(layout.name_x, y, row.name_printed)

    if layout.unit_joined:
        # Vlera dhe njësia në një qelizë të vetme, të rreshtuara majtas:
        # presja dhjetore nuk bie më në të njëjtën vijë dhe segmentimi i
        # kolonave nuk mund të mbështetet te ajo.
        canvas.drawString(layout.value_x - 44, y, f"{row.value_printed} {row.unit_printed}")
    else:
        canvas.drawRightString(layout.value_x, y, row.value_printed)
        canvas.drawString(layout.unit_x, y, row.unit_printed)

    if row.interval_printed:
        canvas.drawString(layout.interval_x, y, row.interval_printed)

    if row.flag_printed:
        _draw_flag(canvas, layout, row.flag_printed, y)


def _draw_flag(canvas: Canvas, layout: Layout, flag: str, y: float) -> None:
    """Flamuri i laboratorit.

    Shigjetat vizatohen si vija dhe jo si shkronja: fontet standarde të
    PDF-së nuk i kanë ato në kodimin e vet, dhe regjistrimi i një fonti
    të sistemit do ta bënte daljen të varur nga makina ku gjenerohet.
    Një shigjetë e vizatuar është gjithashtu pikërisht ajo që sheh një
    skaner.
    """
    if flag in {"↑", "↓"}:
        up = flag == "↑"
        x = layout.flag_x + 3
        top, bottom = y + 8, y
        canvas.setLineWidth(0.9)
        canvas.line(x, bottom, x, top)
        tip = top if up else bottom
        direction = -1 if up else 1
        canvas.line(x, tip, x - 2.5, tip + 3 * direction)
        canvas.line(x, tip, x + 2.5, tip + 3 * direction)
    else:
        canvas.setFont("Helvetica-Bold", layout.font_size)
        canvas.drawString(layout.flag_x, y, flag)
        canvas.setFont(layout.font, layout.font_size)


def _box_for(layout: Layout, y: float) -> BoundingBox:
    """Kutia e rreshtit, nga emri deri te flamuri, me origjinë lart-majtas."""
    top = PAGE_HEIGHT - (y + layout.font_size)
    bottom = PAGE_HEIGHT - (y - layout.font_size * 0.3)
    return BoundingBox(
        x0=layout.name_x - 2,
        y0=round(top, 2),
        x1=layout.flag_x + 14,
        y1=round(bottom, 2),
    )


def _draw_narrative(
    canvas: Canvas, document: DocumentTruth, layout: Layout, line: int, page: int
) -> None:
    """Teksti i lirë i mjekut, nën tabelën e vlerave.

    Dy arsye e nisin atë në faqe të re, dhe të dyja duhen kontrolluar.

    E dukshmja: nuk ka mbetur vend poshtë tabelës. E padukshmja: rreshti i
    radhës i takon faqes tjetër. `_y_for` e mat pozicionin brenda faqes me
    mbetje, prandaj rreshti i parë i faqes së re kthehet në krye të saj —
    dhe pa këtë kontroll narrativa vizatohej sipër tabelës, e lexueshme për
    syrin si dy tekste të përziera dhe e palexueshme fare për nxjerrjen.

    Kjo nuk prek faqet e gjetjeve: narrativa vjen gjithmonë pas tyre.
    """
    if page_for_line(line) != page:
        canvas.showPage()
        _draw_page_header(canvas, document, layout, continued=True)
        y = BODY_TOP
    else:
        y = _y_for(line, layout) - 10
        if y < 220:
            canvas.showPage()
            _draw_page_header(canvas, document, layout, continued=True)
            y = BODY_TOP

    canvas.setFont("Helvetica-Bold", layout.font_size + 1)
    canvas.drawString(MARGIN_X, y, "VLERËSIMI I MJEKUT")
    y -= 18

    canvas.setFont(layout.font, layout.font_size)
    width = PAGE_WIDTH - 2 * MARGIN_X
    for text in _wrap(canvas, document.narrative_text, layout, width):
        canvas.drawString(MARGIN_X, y, text)
        y -= layout.line_height

    y -= 10
    canvas.setFont(layout.font, layout.font_size - 1)
    canvas.drawString(MARGIN_X, y, "Mjeku përgjegjës: Dr. A. Krasniqi")


def _wrap(canvas: Canvas, text: str, layout: Layout, width: float) -> list[str]:
    """Thyerje rreshtash lakmitare mbi gjerësinë reale të shkronjave."""
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if canvas.stringWidth(candidate, layout.font, layout.font_size) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines
