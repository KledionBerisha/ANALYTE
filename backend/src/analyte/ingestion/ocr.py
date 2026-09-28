"""
Njohja optike: faqja si fotografi → rreshta me pozicione.

Dalja ka të njëjtën formë si ajo e shtresës së tekstit — `PageText` me
rreshta dhe kuti — që nxjerrësi të mos dijë nga cila rrugë erdhi faqja.
Ndryshimi i vetëm është cilësia, dhe pikërisht ajo matet te E2.

**Rreshtat i ndërton Tesseract-i, jo toleranca e vijës bazë.** Skanimi i
anuar 1° e zhvendos vijën bazë rreth 10 pikë nga njëri skaj i faqes te
tjetri — më shumë se trefishi i tolerancës që përdor shtresa e tekstit.
Tesseract-i i gjen rreshtat duke ndjekur vetë vijën e anuar, prandaj
grupimi i tij përdoret drejtpërdrejt.

**Drejtimi i faqes korrigjohet para leximit.** Këndi gjendet duke provuar
rrotullime të vogla dhe duke zgjedhur atë që i bën rreshtat më të mprehtë
në projeksionin horizontal. Tesseract-i e duron një anim të vogël, por jo
pa kosto te shifrat, dhe shifrat janë gjithçka këtu.

**Asnjë korrigjim i përmbajtjes.** Nëse OCR-ja lexon "157" aty ku shkruhet
"15,7", ky modul nuk e di dhe nuk e hamendëson. Vlera e gabuar ose kalon
te nxjerrësi si e tillë, ose refuzohet prej tij; në të dy rastet ajo
shfaqet në rezultatet e E2, jo e fshehur pas një "rregullimi".

Motori thirret si program i jashtëm. Rruga e tij dhe e të dhënave të
gjuhës lexohen nga `ANALYTE_TESSERACT` dhe `ANALYTE_TESSDATA`, me vendet
e zakonshme si parazgjedhje.
"""

from __future__ import annotations

import csv
import io
import os
import shutil
import subprocess
from collections import OrderedDict
from pathlib import Path

import pymupdf

from analyte.domain.models import BoundingBox

from .pdf_text import PageText, TextFragment, TextRow

WINDOWS_DEFAULT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
DEFAULT_DPI = 300
SKEW_RANGE = 2.0
SKEW_STEP = 0.1
SKEW_WIDTH = 800
"""Gjerësia në piksel ku kërkohet këndi. Mjafton për projeksionin dhe e
mban kërkimin të shpejtë: dyzet rrotullime të një faqeje të plotë në 300
dpi do të zgjasnin më shumë se vetë leximi."""


class OcrUnavailable(RuntimeError):
    """Motori ose gjuha nuk gjenden. Makina e gjendjeve e regjistron si
    FAILED_INGESTION me këtë arsye."""


def find_tesseract() -> Path | None:
    configured = os.environ.get("ANALYTE_TESSERACT")
    if configured:
        return Path(configured)
    found = shutil.which("tesseract")
    if found:
        return Path(found)
    return WINDOWS_DEFAULT if WINDOWS_DEFAULT.exists() else None


def find_tessdata(language: str) -> Path | None:
    """Dosja me `<gjuha>.traineddata`, ose `None` për parazgjedhjen e motorit."""
    configured = os.environ.get("ANALYTE_TESSDATA")
    if configured:
        return Path(configured)
    local = os.environ.get("LOCALAPPDATA")
    if local:
        candidate = Path(local) / "tesseract" / "tessdata"
        if (candidate / f"{language.split('+')[0]}.traineddata").exists():
            return candidate
    return None


class TesseractOcr:
    """OCR me Tesseract, i thirrshëm si `Ocr` i makinës së gjendjeve."""

    def __init__(
        self,
        language: str = "sqi",
        dpi: int = DEFAULT_DPI,
        psm: int = 6,
        executable: Path | None = None,
        tessdata: Path | None = None,
    ) -> None:
        self.language = language
        self.dpi = dpi
        self.psm = psm
        self.executable = executable or find_tesseract()
        self.tessdata = tessdata or find_tessdata(language)
        if self.executable is None or not Path(self.executable).exists():
            raise OcrUnavailable("programi tesseract nuk u gjet")

    @property
    def name(self) -> str:
        return f"tesseract[{self.language},{self.dpi}dpi,psm{self.psm}]"

    def __call__(self, path: Path) -> tuple[PageText, ...]:
        pages = []
        with pymupdf.open(path) as document:
            for number, page in enumerate(document, start=1):
                image = _render(page, self.dpi)
                image = image.rotate(
                    estimate_skew(image), resample=_bilinear(), expand=False, fillcolor=255
                )
                rows = rows_from_tsv(self._run(image), number, scale=72.0 / self.dpi)
                pages.append(PageText(number=number, rows=rows))
        return tuple(pages)

    def _run(self, image) -> str:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        command = [str(self.executable), "stdin", "stdout"]
        if self.tessdata is not None:
            command += ["--tessdata-dir", str(self.tessdata)]
        command += ["-l", self.language, "--psm", str(self.psm), "-c", "tessedit_create_tsv=1"]
        result = subprocess.run(command, input=buffer.getvalue(), capture_output=True)
        if result.returncode != 0:
            message = result.stderr.decode("utf-8", "replace").strip().splitlines()
            raise OcrUnavailable(message[-1] if message else "tesseract dështoi")
        return result.stdout.decode("utf-8", "replace")


def _render(page: pymupdf.Page, dpi: int):
    from PIL import Image

    pixmap = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
    return Image.frombytes("L", (pixmap.width, pixmap.height), pixmap.samples)


def _bilinear():
    from PIL import Image

    return Image.BILINEAR


def estimate_skew(image) -> float:
    """Këndi që i bën rreshtat më të mprehtë, në gradë.

    Mprehtësia matet si shuma e katrorëve të ndryshimeve ndërmjet shumave
    të rreshtave të pikselëve: një faqe e drejtë ka rreshta teksti dhe
    hapësira të bardha të ndara qartë, një faqe e anuar i përzien ato.
    """
    import numpy as np

    width, height = image.size
    small = image.resize((SKEW_WIDTH, max(1, int(height * SKEW_WIDTH / width))))
    ink = small.point(lambda value: 255 if value < 128 else 0)

    best_angle, best_score = 0.0, -1.0
    steps = int(round(2 * SKEW_RANGE / SKEW_STEP))
    for step in range(steps + 1):
        angle = round(-SKEW_RANGE + step * SKEW_STEP, 2)
        rotated = np.asarray(ink.rotate(angle, expand=False, fillcolor=0), dtype=np.float64)
        profile = rotated.sum(axis=1)
        score = float(np.square(np.diff(profile)).sum())
        if score > best_score:
            best_angle, best_score = angle, score
    return best_angle


def rows_from_tsv(tsv: str, page: int, scale: float) -> tuple[TextRow, ...]:
    """Fjalët e Tesseract-it, të grupuara sipas rreshtit që gjeti ai vetë.

    Koordinatat kthehen nga piksel në pikë PDF (origjinë lart-majtas, si
    te shtresa e tekstit). Fjalët bosh dhe ato me besueshmëri negative —
    blloqe pa tekst — hidhen.
    """
    lines: OrderedDict[tuple[str, str, str], list[TextFragment]] = OrderedDict()
    reader = csv.DictReader(io.StringIO(tsv), delimiter="\t", quoting=csv.QUOTE_NONE)
    for word in reader:
        text = (word.get("text") or "").strip()
        if word.get("level") != "5" or not text or float(word.get("conf") or -1) < 0:
            continue
        left, top = float(word["left"]), float(word["top"])
        width, height = float(word["width"]), float(word["height"])
        box = BoundingBox(
            x0=left * scale,
            y0=top * scale,
            x1=(left + width) * scale,
            y1=(top + height) * scale,
        )
        key = (word["block_num"], word["par_num"], word["line_num"])
        lines.setdefault(key, []).append(TextFragment(text=text, bbox=box))

    rows = [
        TextRow(page=page, fragments=tuple(sorted(fragments, key=lambda f: f.x0)))
        for fragments in lines.values()
    ]
    return tuple(sorted(rows, key=lambda row: row.bbox.y0))
