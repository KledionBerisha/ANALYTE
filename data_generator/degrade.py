"""
Simulimi i skanimit.

"""

from __future__ import annotations

import io
import math
import random
from dataclasses import dataclass
from uuid import UUID

import numpy as np
import pymupdf
from PIL import Image, ImageFilter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

from analyte.domain.models import BoundingBox

from .render import PAGE_HEIGHT, PAGE_WIDTH


@dataclass(frozen=True, slots=True)
class ScanProfile:
    """Sa keq është skanuar kjo kopje.

    Vlerat kampionohen për dokument, jo për faqe: një skaner i keq është i
    keq në të gjitha faqet, dhe një korpus ku çdo faqe prishet ndryshe do
    të ishte më i lehtë se realiteti.
    """

    dpi: int
    angle_deg: float
    blur_radius: float
    noise_sigma: float
    contrast: float
    brightness: float
    jpeg_quality: int
    speckle_rate: float


def sample_profile(rng: random.Random) -> ScanProfile:
    return ScanProfile(
        dpi=rng.choice((150, 200, 300)),
        angle_deg=rng.uniform(-1.2, 1.2),
        blur_radius=rng.uniform(0.3, 0.9),
        noise_sigma=rng.uniform(3.0, 11.0),
        contrast=rng.uniform(0.85, 1.15),
        brightness=rng.uniform(-18.0, 8.0),
        jpeg_quality=rng.randint(55, 85),
        speckle_rate=rng.uniform(0.0, 0.0006),
    )


def degrade_pdf(
    pdf_bytes: bytes,
    boxes: dict[UUID, BoundingBox],
    profile: ScanProfile,
    seed: int,
) -> tuple[bytes, dict[UUID, BoundingBox]]:
    """Kthen PDF-në me shtresë teksti në PDF me faqe si fotografi.

    Kthen gjithashtu kutitë e transformuara, që e vërteta bazë të mbetet
    e vërtetë edhe pas animit.
    """
    source = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    generator = np.random.default_rng(seed)

    buffer = io.BytesIO()
    canvas = Canvas(buffer, pagesize=(PAGE_WIDTH, PAGE_HEIGHT), invariant=1)
    for index in range(source.page_count):
        page = source.load_page(index)
        image = _rasterize(page, profile.dpi)
        image = _apply_scanner_artifacts(image, profile, generator)
        canvas.drawImage(
            ImageReader(image),
            0,
            0,
            width=PAGE_WIDTH,
            height=PAGE_HEIGHT,
            preserveAspectRatio=False,
        )
        canvas.showPage()
    canvas.save()
    source.close()

    rotated = {finding_id: _rotate_box(box, profile.angle_deg) for finding_id, box in boxes.items()}
    return buffer.getvalue(), rotated


def _rasterize(page: pymupdf.Page, dpi: int) -> Image.Image:
    pixmap = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
    return Image.frombytes("L", (pixmap.width, pixmap.height), pixmap.samples)


def _apply_scanner_artifacts(
    image: Image.Image, profile: ScanProfile, generator: np.random.Generator
) -> Image.Image:
    """Anim, shkreptimë, zhurmë dhe kompresim — në këtë rend.

    Rendi ka rëndësi: zhurma duhet të vijë pas turbullimit, përndryshe
    turbullimi do ta zbuste atë dhe rezultati do të ishte shumë më i
    pastër se një skanim i vërtetë.
    """
    image = image.rotate(profile.angle_deg, resample=Image.BILINEAR, expand=False, fillcolor=255)
    image = image.filter(ImageFilter.GaussianBlur(profile.blur_radius))

    pixels = np.asarray(image, dtype=np.float32)
    pixels = (pixels - 128.0) * profile.contrast + 128.0 + profile.brightness
    pixels += generator.normal(0.0, profile.noise_sigma, pixels.shape)

    if profile.speckle_rate > 0:
        mask = generator.random(pixels.shape) < profile.speckle_rate
        pixels[mask] = generator.integers(0, 60, size=int(mask.sum()))

    image = Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8), mode="L")

    compressed = io.BytesIO()
    image.save(compressed, format="JPEG", quality=profile.jpeg_quality)
    compressed.seek(0)
    return Image.open(compressed).copy()


def _rotate_box(box: BoundingBox, angle_deg: float) -> BoundingBox:
    """Kutia pas rrotullimit rreth qendrës së faqes.

    PIL-i rrotullon kundërorar për kënd pozitiv, ndërsa y-ja këtu rritet
    poshtë; prandaj këndi merret me shenjë të kundërt. Rezultati është
    kutia më e vogël me brinjë paralele me boshtet që përmban të katër
    kulmet e rrotulluara — pak më e gjerë se origjinali, ashtu siç është
    vërtet një rresht i anuar.
    """
    if angle_deg == 0:
        return box

    theta = math.radians(-angle_deg)
    cos, sin = math.cos(theta), math.sin(theta)
    cx, cy = PAGE_WIDTH / 2, PAGE_HEIGHT / 2

    corners = ((box.x0, box.y0), (box.x1, box.y0), (box.x1, box.y1), (box.x0, box.y1))
    moved = []
    for x, y in corners:
        dx, dy = x - cx, y - cy
        moved.append((cx + dx * cos - dy * sin, cy + dx * sin + dy * cos))

    xs = [point[0] for point in moved]
    ys = [point[1] for point in moved]
    return BoundingBox(
        x0=round(min(xs), 2),
        y0=round(min(ys), 2),
        x1=round(max(xs), 2),
        y1=round(max(ys), 2),
    )
