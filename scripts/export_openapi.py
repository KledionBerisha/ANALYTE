"""
Skema OpenAPI e shërbimit, për tipat e ndërfaqes.

    python scripts/export_openapi.py
    cd frontend && npm run api:types

"""

from __future__ import annotations

import json
import secrets
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "src"))
sys.path.insert(0, str(ROOT))

from cryptography.fernet import Fernet

from analyte.config import Settings
from analyte.generation.templates import TemplateGenerator
from analyte.main import create_app
from analyte.orchestration.tasks import InlineRunner, Services
from analyte.persistence.database import make_engine, make_session_factory
from analyte.persistence.storage import EncryptedStore

OUT = ROOT / "frontend" / "src" / "lib" / "api" / "openapi.json"


def main() -> int:
    storage = Path(tempfile.mkdtemp())
    settings = Settings(
        database_url="sqlite://",
        jwt_secret=secrets.token_urlsafe(48),
        storage_key=Fernet.generate_key().decode(),
        storage_dir=storage,
        job_runner="inline",
        ocr=False,
        mail_backend="console",  # skema nuk varet nga posta; asnjë email nuk dërgohet
    )
    services = Services(
        sessions=make_session_factory(make_engine(settings.database_url)),
        store=EncryptedStore(storage, settings.storage_key),
        generator=TemplateGenerator(),
    )
    schema = create_app(settings, services, InlineRunner(services)).openapi()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"shkruar {OUT.relative_to(ROOT)} ({len(schema['paths'])} shtigje)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
