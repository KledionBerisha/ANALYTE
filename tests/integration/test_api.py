"""
Testet e API-së, nga ngarkimi te shpjegimi.

Shërbimi ekzekutohet i plotë — makina e gjendjeve, verifikimi, baza, kodimi
i skedarëve — mbi SQLite dhe me punë të menjëhershme, pa Redis. Dokumentet
janë PDF-të e gjeneruesit sintetik, ashtu si te testet e degëve.

Tri grupe pohimesh mbajnë gjithçka këtu:

  - **Kontrata.** Çdo shpjegim mban verifikimin e vet; gabimet kanë formën
    RFC 7807; dokumenti i tjetrit nuk ekziston për ty.
  - **Rrugët e Figurës 6** arrijnë në API me gjendjen e duhur dhe me atë që
    ka kuptim të kthehet për secilën.
  - **Të dhënat nuk rrjedhin.** Skedari në disk është i koduar, emri i tij
    nuk shfaqet askund në bazë, dhe log-u i auditimit nuk mban as emër, as
    email, as vlerë.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from uuid import UUID

import pymupdf
import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import select

from analyte.config import Settings
from analyte.generation.templates import TemplateGenerator, build
from analyte.main import create_app
from tests.fixtures.mailbox import client_for, register_confirmed, token_in
from analyte.orchestration.tasks import InlineRunner, Services
from analyte.persistence.database import create_schema, make_engine, make_session_factory
from analyte.persistence.storage import EncryptedStore
from analyte.persistence.tables import AuditEventRow, DocumentRow, ExplanationRow

PASSWORD = "fjalekalim-testi-i-gjate"
FILENAME = "Analiza_Arben_Krasniqi_2026.pdf"
"""Emër skedari me emër personi, siç e ngarkojnë pacientët vërtet."""


# --------------------------------------------------------------------
# Ndërtimi
# --------------------------------------------------------------------


def _pdf(scanned: bool, seed: str) -> tuple[bytes, object]:
    from data_generator.generate import render
    from data_generator.ground_truth import build_document
    from data_generator.ids import IdFactory

    for index in range(20):
        rng = random.Random(f"{seed}/{index}")
        document = build_document(rng, IdFactory(rng), scanned_share=1.0 if scanned else 0.0)
        if document.context.findings:
            return render(document, seed=5, index=index)
    raise AssertionError("asnjë dokument me gjetje")  # pragma: no cover


def _blank() -> bytes:
    document = pymupdf.open()
    page = document.new_page()
    for line in range(12):
        page.insert_text((72, 72 + 20 * line), f"Rreshti {line + 1}: njoftim administrativ.")
    data = document.tobytes()
    document.close()
    return data


@pytest.fixture(scope="module")
def pdfs():
    digital, truth = _pdf(False, "api-digital")
    scanned, _ = _pdf(True, "api-scanned")
    return {
        "digital": digital,
        "truth": truth,
        "scanned": scanned,
        "blank": _blank(),
        "not_pdf": b"Kjo nuk eshte PDF.\n",
    }


def _services(tmp: Path, generator=None) -> tuple[Settings, Services]:
    settings = Settings(
        database_url=f"sqlite:///{tmp / 'analyte.db'}",
        jwt_secret="t" * 48,
        storage_key=Fernet.generate_key().decode(),
        storage_dir=tmp / "storage",
        job_runner="inline",
        ocr=False,
    )
    engine = make_engine(settings.database_url)
    create_schema(engine)
    services = Services(
        sessions=make_session_factory(engine),
        store=EncryptedStore(settings.storage_dir, settings.storage_key),
        generator=generator or TemplateGenerator(),
    )
    return settings, services


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("api")
    settings, services = _services(tmp)
    client = client_for(settings, services)
    return client, services, tmp


def _headers(client: TestClient, email: str) -> dict[str, str]:
    register_confirmed(client, email, PASSWORD)
    tokens = client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _upload(client, headers, content: bytes, name: str = FILENAME):
    return client.post(
        "/documents", headers=headers, files={"file": (name, content, "application/pdf")}
    )


@pytest.fixture(scope="module")
def alice(world):
    return _headers(world[0], "alice@shembull.al")


@pytest.fixture(scope="module")
def delivered(world, alice, pdfs):
    client = world[0]
    response = _upload(client, alice, pdfs["digital"])
    assert response.status_code == 202, response.text
    return response.json()["id"]


# --------------------------------------------------------------------
# Hyrja
# --------------------------------------------------------------------


def test_register_confirm_login_and_me(world):
    client = world[0]
    created = client.post("/auth/register", json={"email": "Besa@Shembull.AL", "password": PASSWORD})
    assert created.status_code == 202
    assert "email" not in created.json()  # përgjigja nuk tregon asgjë për llogarinë
    # mesazhi shkon te adresa e normalizuar; llogaria nuk hyn para konfirmimit
    assert [m.subject for m in client.outbox.to("besa@shembull.al")] == ["Konfirmoni email-in tuaj në ANALYTE"]
    before = client.post("/auth/login", json={"email": "besa@shembull.al", "password": PASSWORD})
    assert before.status_code == 403
    register_token = token_in(client.outbox.to("besa@shembull.al")[-1])
    assert client.post("/auth/confirm", json={"token": register_token}).status_code == 204

    tokens = client.post(
        "/auth/login", json={"email": "besa@shembull.al", "password": PASSWORD}
    ).json()
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.json()["email"] == "besa@shembull.al"


def test_short_password_and_malformed_email_are_refused(world):
    client = world[0]
    assert client.post(
        "/auth/register", json={"email": "short@shembull.al", "password": "shkurt"}
    ).status_code == 422
    for bad in ("pa-at.shembull.al", "a@b", "a b@shembull.al", "a@shembull.al\nBcc: x@y.al", "a,b@shembull.al"):
        assert client.post("/auth/register", json={"email": bad, "password": PASSWORD}).status_code == 422, bad
    assert client.outbox.to("short@shembull.al") == []


def test_login_failure_does_not_reveal_which_part_was_wrong(world):
    client = world[0]
    register_confirmed(client, "gent@shembull.al", PASSWORD)
    wrong_password = client.post(
        "/auth/login", json={"email": "gent@shembull.al", "password": "gabim-gabim-gabim"}
    )
    unknown_email = client.post(
        "/auth/login", json={"email": "askush@shembull.al", "password": PASSWORD}
    )
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json()["title"] == unknown_email.json()["title"]


def test_refresh_and_access_tokens_are_not_interchangeable(world):
    client = world[0]
    register_confirmed(client, "dea@shembull.al", PASSWORD)
    tokens = client.post("/auth/login", json={"email": "dea@shembull.al", "password": PASSWORD}).json()

    assert client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 200
    assert client.post("/auth/refresh", json={"refresh_token": tokens["access_token"]}).status_code == 401
    as_access = {"Authorization": f"Bearer {tokens['refresh_token']}"}
    assert client.get("/auth/me", headers=as_access).status_code == 401


def test_errors_are_problem_details(world):
    response = world[0].get("/documents")
    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/problem+json")
    assert {"type", "title", "status"} <= response.json().keys()


# --------------------------------------------------------------------
# Rruga e plotë
# --------------------------------------------------------------------


def test_upload_is_processed_to_delivery(world, alice, delivered):
    status = world[0].get(f"/documents/{delivered}/status", headers=alice).json()
    assert status["state"] == "delivered"
    assert status["terminal"] is True
    assert [t["target"] for t in status["transitions"]] == [
        "ingesting",
        "text_extracted",
        "parsing",
        "grounded",
        "generating",
        "verifying",
        "delivered",
    ]


def test_findings_come_back_exactly(world, alice, delivered, pdfs):
    """Numrat dhjetorë kalojnë bazën dhe JSON-in pa u bërë numra lundrues."""
    findings = world[0].get(f"/documents/{delivered}/findings", headers=alice).json()
    truth = {f.analyte_code: f for f in pdfs["truth"].context.findings}
    assert {f["analyte_code"] for f in findings} == set(truth)
    for f in findings:
        assert f["value_canonical"] == format(truth[f["analyte_code"]].value_canonical, "f")


def test_explanation_always_carries_its_verification(world, alice, delivered):
    body = world[0].get(f"/documents/{delivered}/explanation", headers=alice).json()
    assert body["verification"] == {
        "passed": True,
        "mode": "rules",
        "violation_count": 0,
        "is_fallback": False,
    }
    assert body["disclaimer"] in body["text"]
    assert body["generator"] == "template"


def test_verification_lists_every_attempt(world, alice, delivered):
    body = world[0].get(f"/documents/{delivered}/verification", headers=alice).json()
    assert [a["attempt"] for a in body["attempts"]] == [1]
    assert body["attempts"][0]["delivered"] is True


def test_history_lists_the_users_documents(world, alice, delivered):
    page = world[0].get("/documents", headers=alice).json()
    assert delivered in {item["id"] for item in page["items"]}
    assert all(item["filename"] == FILENAME for item in page["items"])


# --------------------------------------------------------------------
# Rrugët e tjera të Figurës 6
# --------------------------------------------------------------------


def test_a_non_pdf_is_rejected_by_the_state_machine(world, alice, pdfs):
    client = world[0]
    document_id = _upload(client, alice, pdfs["not_pdf"], "shenime.txt").json()["id"]
    status = client.get(f"/documents/{document_id}/status", headers=alice).json()
    assert status["state"] == "rejected"
    assert "PDF" in status["reason"]
    assert client.get(f"/documents/{document_id}/explanation", headers=alice).status_code == 409


def test_a_scan_without_ocr_is_unread_not_empty(world, alice, pdfs):
    client = world[0]
    document_id = _upload(client, alice, pdfs["scanned"]).json()["id"]
    status = client.get(f"/documents/{document_id}/status", headers=alice).json()
    assert status["state"] == "failed_ingestion"
    assert client.get(f"/documents/{document_id}/findings", headers=alice).json() == []


def test_a_document_without_content_has_no_explanation(world, alice, pdfs):
    client = world[0]
    document_id = _upload(client, alice, pdfs["blank"]).json()["id"]
    assert client.get(f"/documents/{document_id}/status", headers=alice).json()["state"] == "no_findings"
    response = client.get(f"/documents/{document_id}/explanation", headers=alice)
    assert response.status_code == 409


def test_an_oversized_upload_is_refused(world, alice):
    too_big = b"%PDF-" + b"0" * (20 * 1024 * 1024)
    assert _upload(world[0], alice, too_big).status_code == 413


def test_double_failure_is_stored_as_a_fallback(tmp_path, pdfs):
    """SP8 — dy përpjekje të refuzuara, shablloni i dorëzuar, gjurma e plotë."""

    class Defective:
        name = "i-prishur"

        def __call__(self, context, feedback):
            return f"{build(context)} Vlera e matur është 987654."

    settings, services = _services(tmp_path, Defective())
    client = client_for(settings, services)
    headers = _headers(client, "sp8@shembull.al")
    document_id = _upload(client, headers, pdfs["digital"]).json()["id"]

    body = client.get(f"/documents/{document_id}/explanation", headers=headers).json()
    assert body["verification"]["is_fallback"] is True
    assert "987654" not in body["text"]
    assert [n["code"] for n in body["notices"] if n["code"] == "fallback"] == ["fallback"]

    attempts = client.get(f"/documents/{document_id}/verification", headers=headers).json()["attempts"]
    assert [(a["attempt"], a["is_fallback"], a["delivered"]) for a in attempts] == [
        (1, False, False),
        (2, False, False),
        (3, True, True),
    ]
    assert attempts[0]["verification"]["violations"][0]["type"] == "ungrounded_number"


def test_state_is_visible_while_processing(tmp_path, pdfs):
    """Kalimet shkruhen ndërsa ndodhin, jo vetëm në fund (NFR4)."""
    seen = []

    class Watching:
        name = "vëzhgues"

        def __call__(self, context, feedback):
            with services.sessions() as session:
                seen.append(session.get(DocumentRow, context.document_id).state)
            return build(context)

    settings, services = _services(tmp_path, Watching())
    client = client_for(settings, services)
    headers = _headers(client, "watch@shembull.al")
    _upload(client, headers, pdfs["digital"])
    assert seen == ["generating"]


def test_a_crash_is_recorded_not_hidden(tmp_path, pdfs, monkeypatch):
    import analyte.orchestration.tasks as tasks

    def broken(*args, **kwargs):
        raise RuntimeError("defekt i simuluar")

    monkeypatch.setattr(tasks, "process", broken)
    settings, services = _services(tmp_path)
    client = client_for(settings, services)
    headers = _headers(client, "crash@shembull.al")
    document_id = _upload(client, headers, pdfs["digital"]).json()["id"]

    status = client.get(f"/documents/{document_id}/status", headers=headers).json()
    assert status["job"]["failed"] is True
    assert status["terminal"] is False
    with services.sessions() as session:
        events = session.scalars(select(AuditEventRow.payload).where(
            AuditEventRow.event_type == "processing.failed"
        )).all()
    assert events == [{"error_type": "RuntimeError"}]


# --------------------------------------------------------------------
# Ndarja ndërmjet përdoruesve
# --------------------------------------------------------------------


def test_another_users_document_does_not_exist_for_you(world, delivered):
    client = world[0]
    mallory = _headers(client, "mallory@shembull.al")
    for path in ("", "/status", "/findings", "/assertions", "/explanation", "/verification"):
        assert client.get(f"/documents/{delivered}{path}", headers=mallory).status_code == 404, path
    assert client.delete(f"/documents/{delivered}", headers=mallory).status_code == 404
    assert client.get("/documents", headers=mallory).json()["total"] == 0


# --------------------------------------------------------------------
# Të dhënat
# --------------------------------------------------------------------


def test_stored_files_are_encrypted(world, delivered):
    _, services, _ = world
    with services.sessions() as session:
        document = session.get(DocumentRow, UUID(delivered))
        raw = (services.store.root / document.storage_path).read_bytes()
        assert not raw.startswith(b"%PDF")
        assert FILENAME.encode() not in document.filename_encrypted
        assert services.store.get(document.storage_path).startswith(b"%PDF")


def test_no_file_name_email_or_value_reaches_the_audit_log(world, delivered, pdfs):
    _, services, _ = world
    with services.sessions() as session:
        payloads = json.dumps(
            [e.payload for e in session.scalars(select(AuditEventRow)).all()], ensure_ascii=False
        )
    assert "Krasniqi" not in payloads
    assert "@" not in payloads
    for finding in pdfs["truth"].context.findings:
        assert f'"{finding.value_raw}"' not in payloads


def test_deleting_removes_the_data_but_keeps_the_trace(world, pdfs):
    client, services, _ = world
    headers = _headers(client, "fshirje@shembull.al")
    document_id = _upload(client, headers, pdfs["digital"]).json()["id"]
    with services.sessions() as session:
        storage_path = session.get(DocumentRow, UUID(document_id)).storage_path

    assert client.delete(f"/documents/{document_id}", headers=headers).status_code == 204
    assert client.get(f"/documents/{document_id}", headers=headers).status_code == 404
    assert not (services.store.root / storage_path).exists()

    uid = UUID(document_id)
    with services.sessions() as session:
        assert session.scalars(select(ExplanationRow).where(ExplanationRow.document_id == uid)).all() == []
        kinds = session.scalars(
            select(AuditEventRow.event_type).where(AuditEventRow.document_id == uid)
        ).all()
    assert "document.uploaded" in kinds and "document.deleted" in kinds


# --------------------------------------------------------------------
# Pikat publike dhe të pandërtuara
# --------------------------------------------------------------------


def test_terminology_is_public(world):
    client = world[0]
    terms = client.get("/terminology").json()
    assert len(terms) > 50
    assert client.get("/terminology/anemia").json()["term"] == "anemi"
    assert client.get("/terminology/nje-term-qe-nuk-ekziston").status_code == 404


def test_chat_says_it_is_not_built(world, alice, delivered):
    response = world[0].post(f"/documents/{delivered}/chat", headers=alice)
    assert response.status_code == 501


def test_pages_are_served_as_images_to_the_owner_only(world, alice, delivered):
    client = world[0]
    meta = client.get(f"/documents/{delivered}/pages", headers=alice).json()
    assert meta["count"] >= 1 and meta["width"] > 0

    image = client.get(f"/documents/{delivered}/pages/1", headers=alice)
    assert image.headers["content-type"] == "image/png"
    assert image.content.startswith(b"\x89PNG")
    assert client.get(f"/documents/{delivered}/pages/99", headers=alice).status_code == 404

    mallory = _headers(client, "mallory2@shembull.al")
    assert client.get(f"/documents/{delivered}/pages/1", headers=mallory).status_code == 404
