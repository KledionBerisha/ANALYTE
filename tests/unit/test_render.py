"""
Testet e vizatimit dhe të simulimit të skanimit.

Vizatuesi është vendi ku e vërteta bazë dhe dokumenti mund të ndahen nga
njëri-tjetri pa u vënë re: një kolonë e zhvendosur, një faqe e llogaritur
ndryshe ose një kuti e kthyer në sistemin e gabuar të koordinatave nuk
prishin asgjë që duket. Prandaj testet këtu e lexojnë PDF-në e prodhuar
dhe kërkojnë aty atë që e vërteta bazë premton.
"""

import random

import pymupdf
import pytest

from data_generator.degrade import ScanProfile, _rotate_box, degrade_pdf, sample_profile
from data_generator.generate import build_corpus, render
from data_generator.ground_truth import build_document
from data_generator.ids import IdFactory
from data_generator.render import LAYOUTS, render_document

SEED = 11
CORPUS_SIZE = 12


@pytest.fixture(scope="module")
def rendered():
    """Korpus i vogël i vizatuar: (e vërteta e plotësuar, bajtet e PDF-së)."""
    out = []
    for index, document in enumerate(build_corpus(SEED, CORPUS_SIZE)):
        pdf, document = render(document, SEED, index)
        out.append((document, pdf))
    return out


# --------------------------------------------------------------------
# Kutitë kufizuese
# --------------------------------------------------------------------


def test_every_finding_gets_a_box(rendered):
    for document, _ in rendered:
        for finding in document.context.findings:
            assert finding.bbox is not None, finding.analyte_name_raw


def test_box_contains_the_text_it_claims(rendered):
    """Prova e vetme që koordinatat janë në sistemin e duhur: nxirr
    tekstin brenda kutisë dhe kërko aty emrin dhe vlerën.

    Origjina lart-majtas kundrejt poshtë-majtas është gabim që nuk bie
    kurrë në sy derisa dikush vizaton theksimin në ndërfaqe — muaj më vonë.
    """
    checked = 0
    for document, pdf_bytes in rendered:
        if document.is_scanned:
            continue  # faqja e skanuar nuk ka shtresë teksti fare
        with pymupdf.open(stream=pdf_bytes, filetype="pdf") as pdf:
            for finding in document.context.findings:
                box = finding.bbox
                rect = pymupdf.Rect(box.x0, box.y0, box.x1, box.y1)
                text = pdf.load_page(finding.page - 1).get_textbox(rect)
                assert finding.analyte_name_raw in text
                assert finding.value_raw in text
                checked += 1
    assert checked > 50, "korpusi i provës nuk pati mjaftueshëm rreshta dixhitalë"


def _any_box(seed: int):
    rng = random.Random(seed)
    document = build_document(rng, IdFactory(rng))
    _, boxes = render_document(document)
    return next(iter(boxes.values()))


def test_rotation_leaves_a_straight_page_untouched():
    box = _any_box(1)
    assert _rotate_box(box, 0.0) == box


def test_rotation_widens_the_box():
    """Një rresht i anuar zë më shumë vend në një kuti me brinjë paralele
    me boshtet; nëse kutia nuk zgjerohet, rrotullimi nuk u zbatua."""
    box = _any_box(2)
    turned = _rotate_box(box, 1.2)
    assert turned.y1 - turned.y0 > box.y1 - box.y0


# --------------------------------------------------------------------
# Faqet
# --------------------------------------------------------------------


def test_pdf_has_at_least_the_pages_the_truth_claims(rendered):
    """Narrativa mund të shtojë një faqe në fund; faqet e gjetjeve jo."""
    for document, pdf_bytes in rendered:
        with pymupdf.open(stream=pdf_bytes, filetype="pdf") as pdf:
            assert pdf.page_count >= document.page_count
            for row in document.rows:
                assert 1 <= row.page <= pdf.page_count


def test_all_layouts_are_exercised(rendered):
    layouts = {document.lab.layout for document, _ in rendered}
    assert layouts == set(LAYOUTS)


# --------------------------------------------------------------------
# Kanali: dixhital kundrejt i skanuar
# --------------------------------------------------------------------


def test_scanned_pages_have_no_text_layer(rendered):
    """Nëse një dokument i skanuar do të mbante tekst, rruga e OCR-së nuk
    do të ushtrohej kurrë dhe PK1 për të skanuarat do të ishte fals."""
    scanned = [(d, p) for d, p in rendered if d.is_scanned]
    assert scanned, "korpusi i provës nuk pati asnjë dokument të skanuar"
    for _, pdf_bytes in scanned:
        with pymupdf.open(stream=pdf_bytes, filetype="pdf") as pdf:
            for page in pdf:
                assert not page.get_text().strip()


def test_digital_pages_keep_their_text_layer(rendered):
    digital = [(d, p) for d, p in rendered if not d.is_scanned]
    assert digital
    for document, pdf_bytes in digital:
        with pymupdf.open(stream=pdf_bytes, filetype="pdf") as pdf:
            assert document.lab.lab_name in pdf.load_page(0).get_text()


def test_corpus_contains_both_channels(rendered):
    channels = {document.is_scanned for document, _ in rendered}
    assert channels == {True, False}


# --------------------------------------------------------------------
# Përsëritshmëria e PDF-së
# --------------------------------------------------------------------


def test_rendering_is_byte_identical(rendered):
    """PDF-ja mban vulë kohe dhe identifikues dokumenti nëse nuk i thuhet
    ndryshe; pa `invariant` korpusi nuk do të ishte i rindërtueshëm."""
    fresh = build_corpus(SEED, CORPUS_SIZE)
    for index, (_, pdf_bytes) in enumerate(rendered):
        again, _ = render(fresh[index], SEED, index)
        assert again == pdf_bytes


def test_scan_profile_depends_only_on_the_seed():
    first = sample_profile(random.Random("x"))
    second = sample_profile(random.Random("x"))
    assert first == second


def test_degradation_is_byte_identical():
    rng = random.Random(3)
    document = build_document(rng, IdFactory(rng))
    pdf, boxes = render_document(document)
    profile = ScanProfile(
        dpi=150,
        angle_deg=0.7,
        blur_radius=0.5,
        noise_sigma=6.0,
        contrast=1.0,
        brightness=0.0,
        jpeg_quality=70,
        speckle_rate=0.0002,
    )
    first, first_boxes = degrade_pdf(pdf, boxes, profile, 99)
    second, second_boxes = degrade_pdf(pdf, boxes, profile, 99)
    assert first == second
    assert first_boxes == second_boxes
