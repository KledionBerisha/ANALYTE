"""
Skema OpenAPI e shërbimit, për tipat e ndërfaqes.

    python scripts/export_openapi.py
    cd frontend && npm run api:types

Skema nxirret pa nisur shërbimin: aplikacioni ndërtohet me sekrete të
rastësishme dhe me bazë në kujtesë, sepse skema varet vetëm nga pikat
fundore dhe modelet, jo nga konfigurimi. Tipat e ndërfaqes dalin prej saj
dhe nuk shkruhen me dorë — një tip i shkruar me dorë largohet nga API-ja
që ditën e dytë.
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

from cryptography.fernet import Fernet  # noqa: E402

from analyte.config import Settings  # noqa: E402
from analyte.generation.templates import TemplateGenerator  # noqa: E402
from analyte.main import create_app  # noqa: E402
from analyte.orchestration.tasks import InlineRunner, Services  # noqa: E402
from analyte.persistence.database import make_engine, make_session_factory  # noqa: E402
from analyte.persistence.storage import EncryptedStore  # noqa: E402

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
