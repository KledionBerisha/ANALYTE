"""
Pamjet e ndërfaqes për punim (Figurat 12–16), nga aplikacioni që punon.

    pip install -e ".[screenshots]"
    python scripts/export_screenshots.py                      # Chromium i Playwright, ose Edge/Chrome i instaluar
    python scripts/export_screenshots.py --channel msedge
    python scripts/export_screenshots.py --out /tmp/pamjet --document data/v1/documents/doc_00335.pdf

Skripti nuk prek asgjë të vërtetë: ndez shërbimin në proces me bazë SQLite të përkohshme, sekrete të
rastësishme, postë në kujtesë dhe gjeneruesin determinist (parazgjedhja e aplikacionit; modeli është zgjedhje e shprehur,
ADR 0017, dhe pamjet nuk duhet të varen nga një ofrues i jashtëm), dhe ndez serverin e zhvillimit të ndërfaqes. Regjistron
një përdorues provë, e konfirmon me lidhjen nga posta e kujtesës, hyn përmes formularit, ngarkon një dokument të
korpusit sintetik dhe ruan pamjet:

  12  faqja e hyrjes
  13  hapat e përpunimit, ndërsa ndodhin (përpunimi ngadalësohet qëllimisht, që hapi i tanishëm të duket)
  14  gjetjet laboratorike dhe faqja origjinale me rreshtin e theksuar
  15  shpjegimi me treguesin e verifikimit
  16  krahasimi i raportit mjekësor me rezultatet (kundërshtimet që duhen diskutuar me mjekun)

Dokumenti zgjidhet nga e vërteta bazë e korpusit: dixhital, me një vlerë kritike dhe një kundërshtim raport–laborator,
me më pak gjetje (që pamja të lexohet). Pamjet tregojnë tekstin e shabllonit dhe të dhëna sintetike.

Portat 8000 dhe 3000 duhet të jenë të lira; skripti i lë të lira kur mbaron.
"""

from __future__ import annotations

import argparse
import json
import re
import secrets
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "src"))
sys.path.insert(0, str(ROOT))

DEFAULT_OUT = ROOT / "docs" / "thesis" / "figures"
API_PORT, WEB_PORT = 8000, 3000
VIEWPORT = (1280, 900)
API, WEB = f"http://localhost:{API_PORT}", f"http://localhost:{WEB_PORT}"
NAMES = {
    12: "figura_12_faqja_e_hyrjes",
    13: "figura_13_perpunimi",
    14: "figura_14_gjetjet",
    15: "figura_15_shpjegimi",
    16: "figura_16_krahasimi",
}


# --------------------------------------------------------------------
# Dokumenti
# --------------------------------------------------------------------


def pick_document(data: Path) -> Path:
    """Dokumenti i parë (sipas numrit më të vogël të gjetjeve) që është dixhital, me vlerë kritike dhe me kundërshtim."""
    manifest = json.loads((data / "manifest.json").read_text(encoding="utf-8"))
    best: tuple[int, int, Path] | None = None
    for entry in manifest["documents"]:
        if entry["is_scanned"]:
            continue
        truth = json.loads((data / entry["file"]).read_text(encoding="utf-8"))["context"]
        critical = any(str(f["status"]).startswith("critical") for f in truth["findings"])
        contradiction = any(x["state"] == "contradiction" for x in truth["cross_refs"])
        if critical and contradiction:
            candidate = (len(truth["findings"]), entry["index"], data / entry["pdf"])
            best = min(best, candidate) if best else candidate
    if best is None:
        raise SystemExit("asnjë dokument i korpusit nuk ka vlerë kritike dhe kundërshtim; jepni --document")
    return best[2]


# --------------------------------------------------------------------
# Shërbimet
# --------------------------------------------------------------------


class SlowGenerator:
    """Gjeneruesi determinist, me pritje: hapat e përpunimit duken te ndërfaqja gjatë një çasti të gjatë sa pamja."""

    def __init__(self, delay: float) -> None:
        from analyte.generation.templates import TemplateGenerator

        self.inner, self.delay = TemplateGenerator(), delay
        self.name = self.inner.name

    def __call__(self, context, feedback=()):
        time.sleep(self.delay)
        return self.inner(context, feedback)


class ThreadRunner:
    """Punët kryhen në një fill, jo brenda kërkesës: ngarkimi kthen 202 dhe ndërfaqja ndjek hapat ndërsa ndodhin."""

    def __init__(self, services) -> None:
        self.services = services

    def submit(self, document_id: UUID) -> None:
        from analyte.orchestration.tasks import run_document

        threading.Thread(target=run_document, args=(self.services, document_id), daemon=True).start()


def _port_free(port: int) -> bool:
    with socket.socket() as probe:
        return probe.connect_ex(("127.0.0.1", port)) != 0


def start_backend(tmp: Path, delay: float):
    import uvicorn
    from cryptography.fernet import Fernet

    from analyte.config import Settings
    from analyte.mail import OutboxMailer
    from analyte.main import create_app
    from analyte.orchestration.tasks import Services
    from analyte.persistence.database import create_schema, make_engine, make_session_factory
    from analyte.persistence.storage import EncryptedStore

    settings = Settings(
        database_url=f"sqlite:///{tmp / 'pamje.db'}",
        jwt_secret=secrets.token_urlsafe(48),
        storage_key=Fernet.generate_key().decode(),
        storage_dir=tmp / "storage",
        job_runner="inline",  # nuk përdoret: jepet `ThreadRunner`
        ocr=False,
        mail_backend="console",
    )
    engine = make_engine(settings.database_url)
    create_schema(engine)
    services = Services(
        sessions=make_session_factory(engine),
        store=EncryptedStore(settings.storage_dir, settings.storage_key),
        generator=SlowGenerator(delay),
    )
    outbox = OutboxMailer()
    app = create_app(settings, services, ThreadRunner(services), outbox)
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=API_PORT, log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    return server, outbox


def start_frontend(log: Path) -> subprocess.Popen:
    handle = log.open("w", encoding="utf-8")
    return subprocess.Popen(
        ["npm", "run", "dev"], cwd=ROOT / "frontend", shell=sys.platform == "win32",
        stdout=handle, stderr=subprocess.STDOUT,
    )


def stop(process: subprocess.Popen) -> None:
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
    else:
        process.terminate()


def wait_for(url: str, seconds: float) -> None:
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=3)
            return
        except Exception:
            time.sleep(1)
    raise SystemExit(f"{url} nuk u ngrit brenda {seconds:.0f} sekondave")


# --------------------------------------------------------------------
# Shfletuesi
# --------------------------------------------------------------------


def launch(playwright, channel: str | None):
    """Chromium i Playwright nëse është shkarkuar; përndryshe Edge ose Chrome i instaluar në makinë."""
    candidates = [channel] if channel else [None, "msedge", "chrome"]
    last: Exception | None = None
    for name in candidates:
        try:
            return playwright.chromium.launch(channel=name) if name else playwright.chromium.launch()
        except Exception as error:  # noqa: BLE001 — provohet kandidati tjetër
            last = error
    raise SystemExit(f"nuk u gjet shfletues (provuar: {candidates}): {last}")


def hide_dev_overlay(page) -> None:
    """Shenja e serverit të zhvillimit të Next.js (rrrethi «N») nuk është pjesë e ndërfaqes."""
    page.add_style_tag(content="nextjs-portal { display: none !important; }")


def shot_region(page, locators, path: Path, *, height: int = VIEWPORT[1]) -> None:
    """Pamje e drejtkëndëshit që mbulon disa elemente.

    Dritarja zgjatet vetëm kur elementi është më i gjatë se ajo (`height`); një dritare shumë e gjatë nuk lë faqen të rrëshqasë,
    dhe atëherë faqja origjinale `sticky` nuk del pranë gjetjeve. Pamja merret në koordinata të dritares, jo të dokumentit:
    faqja origjinale është `sticky`, kështu që pozicioni i saj në dokument varet nga rrëshqitja.
    """
    page.set_viewport_size({"width": VIEWPORT[0], "height": height})
    hide_dev_overlay(page)
    first = locators[0]
    first.scroll_into_view_if_needed()
    page.evaluate("(y) => window.scrollBy(0, y)", first.bounding_box()["y"] - 24)
    page.wait_for_timeout(300)
    boxes = [locator.bounding_box() for locator in locators]
    left = min(b["x"] for b in boxes)
    top = min(b["y"] for b in boxes)
    right = max(b["x"] + b["width"] for b in boxes)
    bottom = max(b["y"] + b["height"] for b in boxes)
    pad = 12
    page.screenshot(
        path=str(path),
        clip={"x": max(0, left - pad), "y": max(0, top - pad), "width": right - left + 2 * pad, "height": bottom - top + 2 * pad},
    )
    page.set_viewport_size({"width": VIEWPORT[0], "height": VIEWPORT[1]})


def section_with(page, heading: str | re.Pattern):
    return page.locator("section", has=page.get_by_role("heading", name=heading))


def capture(page, outbox, pdf: Path, out: Path) -> list[Path]:
    written: list[Path] = []

    def target(number: int) -> Path:
        path = out / f"{NAMES[number]}.png"
        written.append(path)
        return path

    page.goto(f"{WEB}/login")
    page.get_by_role("button", name="Hyr").wait_for(timeout=90_000)
    hide_dev_overlay(page)
    page.screenshot(path=str(target(12)))

    email, password = "pamje@shembull.test", secrets.token_urlsafe(18)
    request = page.context.request
    assert request.post(f"{API}/auth/register", data={"email": email, "password": password}).status == 202
    link = re.search(r"/confirm\?token=([A-Za-z0-9_\-]+)", outbox.to(email)[-1].body)
    assert link, "mesazhi i konfirmimit nuk ka lidhje"
    assert request.post(f"{API}/auth/confirm", data={"token": link.group(1)}).status == 204

    page.fill('input[type="email"]', email)
    page.fill('input[type="password"]', password)
    page.get_by_role("button", name="Hyr").click()
    page.wait_for_url("**/documents", timeout=30_000)
    page.set_input_files('input[type="file"]', str(pdf))

    page.get_by_role("heading", name="Duke e përpunuar dokumentin").wait_for(timeout=30_000)
    page.wait_for_timeout(1800)
    hide_dev_overlay(page)
    page.screenshot(path=str(target(13)))

    page.get_by_role("heading", name="Shpjegimi", exact=True).wait_for(timeout=60_000)
    page.wait_for_timeout(1200)
    shot_region(page, [section_with(page, "Shpjegimi")], target(15), height=1400)  # e gjatë: duhet të hyjë e tëra

    findings = section_with(page, "Vlerat")
    findings.locator("tbody tr").first.click()
    page.wait_for_timeout(1200)  # faqja origjinale ngarkohet dhe rreshti theksohet
    shot_region(page, [findings, section_with(page, "Dokumenti origjinal")], target(14))

    shot_region(page, [section_with(page, re.compile("diskutuar me mjekun"))], target(16))
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="export_screenshots")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--document", type=Path, default=None, help="PDF; parazgjedhja zgjidhet nga korpusi data/v1")
    parser.add_argument("--channel", default=None, help="msedge | chrome (shfletues i instaluar); bosh = provon të gjitha")
    parser.add_argument("--delay", type=float, default=4.0, help="sekonda pritje te gjeneruesi, që hapat të duken")
    args = parser.parse_args(argv)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit('mungon Playwright: pip install -e ".[screenshots]"') from None
    for port in (API_PORT, WEB_PORT):
        if not _port_free(port):
            raise SystemExit(f"porta {port} është e zënë; mbylleni shërbimin që e përdor")
    pdf = args.document or pick_document(ROOT / "data" / "v1")
    args.out.mkdir(parents=True, exist_ok=True)

    # SQLite mban skedarin hapur sa ndezet fillat e serverit; fshirja e dosjes së përkohshme mund të dështojë në Windows.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as raw:
        tmp = Path(raw)
        server, outbox = start_backend(tmp, args.delay)
        web = start_frontend(tmp / "web.log")
        try:
            wait_for(f"{API}/health", 30)
            wait_for(f"{WEB}/login", 120)
            with sync_playwright() as playwright:
                browser = launch(playwright, args.channel)
                context = browser.new_context(
                    viewport={"width": VIEWPORT[0], "height": VIEWPORT[1]}, device_scale_factor=2, locale="sq-AL"
                )
                try:
                    written = capture(context.new_page(), outbox, pdf, args.out)
                finally:
                    browser.close()
        finally:
            server.should_exit = True
            stop(web)
    for path in sorted(written):
        print(f"{path.relative_to(ROOT) if ROOT in path.parents else path}")
    print(f"dokumenti: {pdf.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
