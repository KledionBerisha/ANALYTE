"""
Testet e rrugës së OCR-së.

Pjesa më e madhe nuk kërkon Tesseract: leximi i TSV-së dhe gjetja e
këndit testohen mbi të dhëna të ndërtuara këtu. Testi i vetëm që e
thërret motorin anashkalohet kur ai mungon, që testet të mbeten të
ekzekutueshme kudo — por jo në heshtje: pytest e shënon si të anashkaluar.
"""

from __future__ import annotations

import random
from uuid import uuid4

import pytest

from analyte.ingestion.ocr import estimate_skew, find_tesseract, rows_from_tsv
from evaluation.pipeline import BranchAPipeline, DocumentInput

HEADER = "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext"


def _word(block, line, left, top, text, conf="91.5"):
    return f"5\t1\t{block}\t1\t{line}\t1\t{left}\t{top}\t60\t30\t{conf}\t{text}"


def test_words_are_grouped_by_the_line_tesseract_found():
    tsv = "\n".join(
        [
            HEADER,
            _word(1, 1, 400, 100, "g/dL"),
            _word(1, 1, 100, 102, "Hemoglobina"),
            _word(1, 1, 300, 101, "13,4"),
            _word(1, 2, 100, 160, "Hematokriti"),
        ]
    )
    rows = rows_from_tsv(tsv, page=1, scale=72 / 300)
    assert [row.text for row in rows] == ["Hemoglobina 13,4 g/dL", "Hematokriti"]


def test_pixels_become_pdf_points_with_top_left_origin():
    tsv = "\n".join([HEADER, _word(1, 1, 300, 600, "X")])
    (row,) = rows_from_tsv(tsv, page=2, scale=72 / 300)
    box = row.fragments[0].bbox
    assert (box.x0, box.y0) == pytest.approx((72.0, 144.0))
    assert row.page == 2


def test_empty_words_and_non_text_blocks_are_dropped():
    tsv = "\n".join(
        [
            HEADER,
            "4\t1\t1\t1\t1\t0\t0\t0\t10\t10\t-1\t",
            _word(1, 1, 10, 10, "   "),
            _word(1, 1, 10, 10, "zhurmë", conf="-1"),
            _word(1, 1, 80, 10, "Glukoza"),
        ]
    )
    rows = rows_from_tsv(tsv, page=1, scale=1.0)
    assert [row.text for row in rows] == ["Glukoza"]


def _striped_page(angle: float):
    from PIL import Image, ImageDraw

    image = Image.new("L", (1200, 1600), 255)
    draw = ImageDraw.Draw(image)
    for top in range(100, 1500, 60):
        draw.rectangle((100, top, 1100, top + 18), fill=0)
    return image.rotate(angle, expand=False, fillcolor=255)


@pytest.mark.parametrize("angle", [-1.2, -0.5, 0.0, 0.8, 1.2])
def test_skew_is_found_and_undone(angle):
    """Këndi i gjetur është ai që e kthen faqen drejt: e kundërta e animit."""
    assert estimate_skew(_striped_page(angle)) == pytest.approx(-angle, abs=0.15)


# --------------------------------------------------------------------
# Pipeline-i
# --------------------------------------------------------------------


def _scanned_pdf(tmp_path, seed="ocr-test"):
    from data_generator.generate import render
    from data_generator.ground_truth import build_document
    from data_generator.ids import IdFactory

    rng = random.Random(seed)
    document = build_document(rng, IdFactory(rng), scanned_share=1.0)
    pdf, document = render(document, seed=11, index=0)
    path = tmp_path / "scan.pdf"
    path.write_bytes(pdf)
    return document, path


def test_without_ocr_a_scan_is_unread_not_empty(tmp_path):
    _, path = _scanned_pdf(tmp_path)
    output = BranchAPipeline().run(DocumentInput(uuid4(), path))
    assert output.state.value == "failed_ingestion"


def test_an_ocr_failure_is_recorded_as_such(tmp_path):
    _, path = _scanned_pdf(tmp_path)

    def broken(_):
        raise RuntimeError("motori u rrëzua")

    output = BranchAPipeline(ocr=broken).run(DocumentInput(uuid4(), path))
    assert output.state.value == "failed_ingestion"
    assert "motori u rrëzua" in output.failures[0]


@pytest.mark.skipif(find_tesseract() is None, reason="tesseract nuk është i instaluar")
def test_tesseract_reads_a_synthetic_scan(tmp_path):
    """Jo saktësia — ajo matet te E2 — por që rruga funksionon nga skaji në skaj."""
    from analyte.ingestion.ocr import TesseractOcr

    document, path = _scanned_pdf(tmp_path)
    output = BranchAPipeline(ocr=TesseractOcr(language="eng")).run(DocumentInput(uuid4(), path))
    assert output.state.value in {"grounded", "no_findings"}
    truth = {f.analyte_code for f in document.context.findings}
    assert {f.analyte_code for f in output.context.findings} & truth
