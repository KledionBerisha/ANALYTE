"""
Mbrojtja e të dhënave (ADR 0019): pëlqimi për modelin, porta e çidentifikimit, fshirja, eksporti dhe afati i ruajtjes.

"""

from __future__ import annotations

import dataclasses
import importlib
import json
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import func, select

from analyte import erasure
from analyte.config import Settings
from analyte.generation.llm import Completion, LlmGenerator
from analyte.generation.templates import TemplateGenerator, build
from analyte.orchestration.tasks import Services, run_document
from analyte.persistence.database import create_schema, make_engine, make_session_factory
from analyte.persistence.storage import EncryptedStore
from analyte.persistence.tables import (
    AdviceRow,
    AssertionRow,
    AuditEventRow,
    AuthSessionRow,
    CrossReferenceRow,
    DocumentRow,
    EmailConfirmationRow,
    ExplanationRow,
    FindingRow,
    GlossaryRow,
    JobRow,
    LoginFailureRow,
    PatternRow,
    RefreshTokenRow,
    UnexplainedTermRow,
    UserRow,
    VerificationRow,
    ViolationRow,
)
from tests.fixtures.mailbox import client_for, register_confirmed

PASSWORD = "fjalekalim-testi-i-gjate"
FILENAME = "Analiza_Arben_Krasniqi_2026.pdf"

DOCUMENT_TABLES = (
    JobRow,
    FindingRow,
    AssertionRow,
    CrossReferenceRow,
    GlossaryRow,
    UnexplainedTermRow,
    PatternRow,
    AdviceRow,
    ExplanationRow,
    VerificationRow,
    ViolationRow,
)


# Ndërtimi


def _pdf(seed: str, narrative: str | None = None) -> bytes:
    from data_generator.generate import render
    from data_generator.ground_truth import build_document
    from data_generator.ids import IdFactory

    for index in range(20):
        rng = random.Random(f"{seed}/{index}")
        document = build_document(rng, IdFactory(rng), scanned_share=0.0)
        if document.context.findings:
            if narrative is not None:
                document = dataclasses.replace(document, narrative_text=narrative)
            return render(document, seed=5, index=index)[0]
    raise AssertionError("asnjë dokument me gjetje")  # pragma: no cover


@pytest.fixture(scope="module")
def pdfs():
    return {
        "a": _pdf("protect-a"),
        "b": _pdf("protect-b"),
        "named": _pdf(
            "protect-named",
            "Dr. Arben Krasniqi vëren anemi të lehtë te Pacienti Valmir Shala. Rekomandohet kontroll pas tre muajsh.",
        ),
    }


class FakeClient:
    """Ofrues i simuluar: numëron çdo kërkesë dhe kthen tekstet e dhëna me radhë."""

    provider, model, cache = "fake", "fake-model-1", None

    def __init__(self, outputs=()) -> None:
        self.outputs, self.prompts = list(outputs), []

    def complete(self, system: str, user: str) -> Completion:
        self.prompts.append(user)
        return Completion(text=self.outputs.pop(0), model=self.model)


class World:
    def __init__(
        self, tmp: Path, generator, runner=None, database_url: str | None = None, **overrides
    ) -> None:
        """`database_url` jepet nga testet e PostgreSQL-it, që e kanë skemën nga migrimet; pa të përdoret SQLite."""
        tmp.mkdir(parents=True, exist_ok=True)
        self.settings = Settings(
            _env_file=None,  # kopja e zhvilluesit mund të ketë çelësin e vërtetë; testet nuk e lexojnë
            database_url=database_url or f"sqlite:///{tmp / 'a.db'}",
            jwt_secret="t" * 48,
            storage_key=Fernet.generate_key().decode(),
            storage_dir=tmp / "storage",
            job_runner="inline",
            ocr=False,
            **overrides,
        )
        engine = make_engine(self.settings.database_url)
        if database_url is None:
            create_schema(engine)
        self.services = Services(
            sessions=make_session_factory(engine),
            store=EncryptedStore(self.settings.storage_dir, self.settings.storage_key),
            generator=generator,
        )
        self.client = client_for(self.settings, self.services, runner)

    def user(self, email: str) -> dict[str, str]:
        register_confirmed(self.client, email, PASSWORD)
        tokens = self.client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()
        return {"Authorization": f"Bearer {tokens['access_token']}"}

    def upload(self, headers, pdf: bytes, consent: bool | None = None, name: str = FILENAME) -> str:
        data = None if consent is None else {"model_consent": "true" if consent else "false"}
        response = self.client.post(
            "/documents", headers=headers, files={"file": (name, pdf, "application/pdf")}, data=data
        )
        assert response.status_code == 202, response.text
        return response.json()["id"]

    def explanation(self, headers, document_id: str) -> dict:
        response = self.client.get(f"/documents/{document_id}/explanation", headers=headers)
        assert response.status_code == 200, response.text
        return response.json()

    def counts(self) -> dict[str, int]:
        with self.services.sessions() as session:
            return {
                table.__tablename__: session.scalar(select(func.count()).select_from(table))
                for table in (*DOCUMENT_TABLES, DocumentRow)
            }

    def stored_files(self) -> set[str]:
        return {path.name for path in self.services.store.root.glob("*.bin")}

    def audit(self, event_type: str | None = None) -> list[AuditEventRow]:
        with self.services.sessions() as session:
            query = select(AuditEventRow).order_by(AuditEventRow.id)
            if event_type:
                query = query.where(AuditEventRow.event_type == event_type)
            return list(session.scalars(query))

    def document_row(self, document_id: str) -> DocumentRow:
        with self.services.sessions() as session:
            return session.get(DocumentRow, UUID(document_id))


def _model_world(tmp: Path, outputs=(), **overrides) -> tuple[World, FakeClient]:
    fake = FakeClient(outputs)
    return World(tmp, LlmGenerator(fake), service_generator="model", **overrides), fake


# Pëlqimi për modelin


@pytest.mark.parametrize("consent", [None, False])
def test_without_consent_the_template_is_used_and_the_provider_is_never_called(
    tmp_path, pdfs, consent
):
    world, fake = _model_world(tmp_path)  # pa dalje në radhë: një thirrje do të hidhte IndexError
    headers = world.user("pa-pelqim@shembull.al")
    document_id = world.upload(headers, pdfs["a"], consent=consent)

    body = world.explanation(headers, document_id)
    codes = [n["code"] for n in body["notices"]]
    assert fake.prompts == []
    assert body["generator"] == "template"
    assert "model_declined" in codes and "model" not in codes and "fallback" not in codes
    assert "pëlqimin" in next(n["text"] for n in body["notices"] if n["code"] == "model_declined")
    assert body["verification"]["passed"] is True and body["verification"]["is_fallback"] is False

    row = world.document_row(document_id)
    assert (row.model_consent, row.model_consent_at, row.model_use) == (False, None, "no_consent")
    assert [e.payload for e in world.audit("document.model_consent")] == [{"given": False}]
    assert [e.payload for e in world.audit("document.model_use")] == [
        {"use": "no_consent", "kinds": []}
    ]


def test_consent_is_stored_with_a_time_audited_and_the_model_is_used(tmp_path, pdfs):
    from analyte.grounding.context import build as build_grounding
    from analyte.ingestion.router import route

    world, fake = _model_world(tmp_path)
    headers = world.user("me-pelqim@shembull.al")
    # Përgjigjja e modelit është shablloni i kontekstit të vërtetë: kalon verifikimin.

    path = tmp_path / "d.pdf"
    path.write_bytes(pdfs["a"])
    context = build_grounding(UUID(int=1), route(path).pages).context
    fake.outputs.append(build(context))

    before = datetime.now(UTC)
    response = world.client.post(
        "/documents",
        headers=headers,
        files={"file": (FILENAME, pdfs["a"], "application/pdf")},
        data={"model_consent": "true"},
    )
    assert response.status_code == 202 and response.json()["model_consent"] is True
    document_id = response.json()["id"]

    row = world.document_row(document_id)
    assert (
        row.model_consent is True
        and row.model_consent_at is not None
        and row.model_consent_at >= before
    )
    assert row.model_use == "used" and row.model_gate_kinds is None
    assert len(fake.prompts) == 1
    body = world.explanation(headers, document_id)
    assert body["generator"].startswith("fake:fake-model-1:") and "model" in [
        n["code"] for n in body["notices"]
    ]
    assert (
        world.client.get(f"/documents/{document_id}", headers=headers).json()["model_consent"]
        is True
    )

    assert [e.payload for e in world.audit("document.model_consent")] == [{"given": True}]
    assert [e.payload for e in world.audit("document.model_use")] == [{"use": "used", "kinds": []}]
    serialized = json.dumps([e.payload for e in world.audit()], ensure_ascii=False)
    assert "me-pelqim" not in serialized and FILENAME not in serialized


def test_a_name_in_a_doctor_quote_stops_the_model_even_with_consent_and_the_patient_sees_the_original_quote(
    tmp_path, pdfs
):
    from analyte.grounding.context import build as build_grounding
    from analyte.ingestion.router import route

    path = tmp_path / "n.pdf"
    path.write_bytes(pdfs["named"])
    context = build_grounding(UUID(int=2), route(path).pages).context
    assert any("Krasniqi" in a.text_span for a in context.assertions), (
        "PDF-ja e provës duhet ta ketë emrin te citimi"
    )

    world, fake = _model_world(tmp_path)
    headers = world.user("emer@shembull.al")
    document_id = world.upload(headers, pdfs["named"], consent=True)

    body = world.explanation(headers, document_id)
    codes = [n["code"] for n in body["notices"]]
    assert fake.prompts == []  # dështim i mbyllur: asnjë kërkesë, as për pjesën e pastër
    assert body["generator"] == "template" and body["verification"]["passed"] is True
    assert "model_withheld" in codes and "model_declined" not in codes and "model" not in codes
    notice = next(n["text"] for n in body["notices"] if n["code"] == "model_withheld")
    # kategoritë, jo vargu
    assert "emër" in notice and "Krasniqi" not in notice and "Shala" not in notice
    assert "Krasniqi" in body["text"]  # citimi i mjekut del i pandryshuar, jo i redaktuar

    row = world.document_row(document_id)
    assert row.model_use == "identifying_content" and "name_like" in row.model_gate_kinds.split(",")
    event = world.audit("document.model_use")[0]
    assert event.payload["use"] == "identifying_content" and "name_like" in event.payload["kinds"]
    serialized = json.dumps([e.payload for e in world.audit()], ensure_ascii=False)
    assert "Krasniqi" not in serialized and "Shala" not in serialized


def test_a_template_only_service_ignores_a_consent_it_never_asked_for(tmp_path, pdfs):
    world = World(tmp_path, TemplateGenerator())  # service_generator = template
    headers = world.user("pa-model@shembull.al")
    response = world.client.post(
        "/documents",
        headers=headers,
        files={"file": (FILENAME, pdfs["a"], "application/pdf")},
        data={"model_consent": "true"},
    )
    assert response.json()["model_consent"] is False
    document_id = response.json()["id"]
    row = world.document_row(document_id)
    assert (row.model_consent, row.model_consent_at, row.model_use) == (False, None, None)
    assert world.audit("document.model_consent") == [] and world.audit("document.model_use") == []
    assert not [
        n
        for n in world.explanation(headers, document_id)["notices"]
        if n["code"].startswith("model")
    ]


def test_privacy_config_says_what_the_service_does(tmp_path):
    off = World(tmp_path / "off", TemplateGenerator(), llm_provider="mistral")
    assert off.client.get("/privacy/config").json() == {
        "model_enabled": False,
        "model_provider": None,
        "retention_days": 0,
    }
    on, _ = _model_world(tmp_path / "on", llm_provider="mistral", document_retention_days=90)
    assert on.client.get("/privacy/config").json() == {
        "model_enabled": True,
        "model_provider": "mistral",
        "retention_days": 90,
    }


# Fshirja e një dokumenti


def test_deleting_a_document_removes_rows_and_file_leaves_the_other_user_alone_and_scrubs_the_hash(
    tmp_path, pdfs
):
    world = World(tmp_path, TemplateGenerator())
    alice, bob = world.user("alice@shembull.al"), world.user("bob@shembull.al")
    bob_doc = world.upload(bob, pdfs["b"], name="bob.pdf")
    bob_counts, bob_files, bob_text = (
        world.counts(),
        world.stored_files(),
        world.explanation(bob, bob_doc)["text"],
    )

    alice_doc = world.upload(alice, pdfs["a"])
    assert world.counts() != bob_counts and len(world.stored_files()) == 2

    assert world.client.delete(f"/documents/{bob_doc}", headers=alice).status_code == 404  # jo 403
    assert world.counts() != bob_counts  # asgjë nuk u fshi
    assert world.client.delete(f"/documents/{alice_doc}", headers=alice).status_code == 204

    assert world.counts() == bob_counts  # çdo tabelë e derivuar e Alice-s është bosh
    assert world.stored_files() == bob_files  # skedari i koduar i saj u hoq vërtet nga depoja
    assert world.explanation(bob, bob_doc)["text"] == bob_text
    # përsëritja
    assert world.client.delete(f"/documents/{alice_doc}", headers=alice).status_code == 404

    events = [e for e in world.audit() if e.document_id == UUID(alice_doc)]
    assert {"document.uploaded", "document.deleted"} <= {e.event_type for e in events}
    uploaded = next(e for e in events if e.event_type == "document.uploaded")
    assert "sha256" not in uploaded.payload and "size_bytes" in uploaded.payload


def test_deletion_requires_authentication(tmp_path, pdfs):
    world = World(tmp_path, TemplateGenerator())
    headers = world.user("anonim@shembull.al")
    document_id = world.upload(headers, pdfs["a"])
    assert world.client.delete(f"/documents/{document_id}").status_code == 401
    assert world.client.get("/me/export").status_code == 401
    assert (
        world.client.request("DELETE", "/me/data", json={"password": PASSWORD}).status_code == 401
    )
    assert world.counts()["documents"] == 1


def test_an_upload_that_fails_after_the_file_was_written_leaves_no_file_behind(
    tmp_path, pdfs, monkeypatch
):
    """Skedari shkruhet para rreshtit; nëse rreshti nuk ruhet (p.sh. llogaria u fshi pikërisht tani), skedari nuk
    mbetet pa pronar."""
    from analyte.audit import logger as audit

    world = World(tmp_path, TemplateGenerator(), runner=_NotYet())
    headers = world.user("dështim@shembull.al")

    def fail(*args, **kwargs):
        raise RuntimeError("baza nuk e ruajti")

    monkeypatch.setattr(audit, "document_uploaded", fail)
    with pytest.raises(RuntimeError):
        world.upload(headers, pdfs["a"])
    assert world.stored_files() == set() and world.counts()["documents"] == 0


# Fshirja e llogarisë


def _erase(world: World, headers, password: str = PASSWORD):
    return world.client.request("DELETE", "/me/data", headers=headers, json={"password": password})


def test_erasing_an_account_removes_everything_of_it_and_nothing_of_anyone_else(tmp_path, pdfs):
    world = World(tmp_path, TemplateGenerator())
    bob = world.user("bob@shembull.al")
    bob_doc = world.upload(bob, pdfs["b"], name="bob.pdf")
    bob_counts, bob_files, bob_text = (
        world.counts(),
        world.stored_files(),
        world.explanation(bob, bob_doc)["text"],
    )

    alice = world.user("alice@shembull.al")
    world.upload(alice, pdfs["a"])
    world.upload(alice, pdfs["a"], name="dytë.pdf")
    # Një hyrje e dështuar e Alice-s lë një numërues me HMAC të email-it të saj.
    world.client.post(
        "/auth/login", json={"email": "alice@shembull.al", "password": "gabim-gabim-gabim"}
    )
    with world.services.sessions() as session:
        alice_id = session.scalar(select(UserRow.id).where(UserRow.email == "alice@shembull.al"))
        assert session.scalar(select(func.count()).select_from(LoginFailureRow)) == 1

    assert _erase(world, alice).status_code == 204

    assert world.counts() == bob_counts
    assert world.stored_files() == bob_files
    assert world.explanation(bob, bob_doc)["text"] == bob_text
    with world.services.sessions() as session:
        assert (
            session.scalar(select(UserRow.id).where(UserRow.email == "alice@shembull.al")) is None
        )
        assert session.scalar(select(func.count()).select_from(UserRow)) == 1
        assert session.scalar(select(func.count()).select_from(LoginFailureRow)) == 0
        assert (
            session.scalars(select(AuthSessionRow).where(AuthSessionRow.user_id == alice_id)).all()
            == []
        )
        assert (
            session.scalars(
                select(EmailConfirmationRow).where(EmailConfirmationRow.user_id == alice_id)
            ).all()
            == []
        )
        remaining_sessions = {row.user_id for row in session.scalars(select(AuthSessionRow))}
        # vetëm ajo e Bob-it
        assert alice_id not in remaining_sessions and len(remaining_sessions) == 1
        assert session.scalar(select(func.count()).select_from(RefreshTokenRow)) == 1

    # Gjurma mbetet pa identifikues përdoruesi dhe pa email, emër skedari apo hash.
    events = world.audit()
    assert alice_id not in {e.user_id for e in events}
    assert "user.erased" in {e.event_type for e in events}
    assert next(e for e in events if e.event_type == "user.erased").payload == {"documents": 2}
    serialized = json.dumps([e.payload for e in events], ensure_ascii=False)
    assert "alice" not in serialized and "dytë" not in serialized and FILENAME not in serialized
    uploads = [e for e in events if e.event_type == "document.uploaded"]
    # vetëm ai i Bob-it
    assert len(uploads) == 3 and sum("sha256" in e.payload for e in uploads) == 1

    # Pas fshirjes tokeni nuk vlen, dhe llogaria nuk hyn më.
    assert world.client.get("/auth/me", headers=alice).status_code == 401
    assert (
        world.client.post(
            "/auth/login", json={"email": "alice@shembull.al", "password": PASSWORD}
        ).status_code
        == 401
    )
    assert _erase(world, alice).status_code == 401  # përsëritja: tokeni nuk ekziston më


def test_a_wrong_password_deletes_nothing_and_is_throttled(tmp_path, pdfs):
    world = World(tmp_path, TemplateGenerator(), login_max_failures_pair=3)
    headers = world.user("e-keqe@shembull.al")
    world.upload(headers, pdfs["a"])

    for _ in range(3):
        response = _erase(world, headers, "fjalekalim-i-gabuar")
        assert response.status_code == 403
    assert world.counts()["documents"] == 1

    blocked = _erase(world, headers, PASSWORD)  # kufizimi para fjalëkalimit, si te hyrja
    assert blocked.status_code == 429 and "Retry-After" in blocked.headers
    assert world.counts()["documents"] == 1
    assert world.client.get("/auth/me", headers=headers).status_code == 200


def test_erasing_requires_the_password_in_the_body(tmp_path):
    world = World(tmp_path, TemplateGenerator())
    headers = world.user("pa-trup@shembull.al")
    assert world.client.request("DELETE", "/me/data", headers=headers).status_code == 422
    assert _erase(world, headers, "").status_code == 422
    assert world.client.get("/auth/me", headers=headers).status_code == 200


def test_erasing_twice_in_a_row_is_harmless(tmp_path, pdfs):
    """Dy kërkesa që kaluan autentikimin para fshirjes: e dyta gjen asgjë për të fshirë dhe nuk del në gabim."""
    world = World(tmp_path, TemplateGenerator())
    headers = world.user("dyfish@shembull.al")
    world.upload(headers, pdfs["a"])
    with world.services.sessions() as session:
        user = session.scalar(select(UserRow).where(UserRow.email == "dyfish@shembull.al"))
        assert erasure.erase_user(session, world.services.store, user, world.settings) == 1
        session.commit()
    with (
        world.services.sessions() as session
    ):  # i njëjti objekt përdoruesi, tashmë i fshirë nga një kërkesë tjetër
        assert erasure.erase_user(session, world.services.store, user, world.settings) == 0
        session.commit()
    assert world.counts()["documents"] == 0 and world.stored_files() == set()


def test_a_document_deleted_while_it_is_being_processed_leaves_nothing_behind(tmp_path, pdfs):
    """Pronari (ose afati) e fshin dokumentin ndërsa punëtori po gjeneron: puna përfundon pa përjashtim dhe nuk shkruan
    asgjë pas vetes; as rresht, as skedar."""

    class DeletingGenerator:
        name = "fshirës"

        def __call__(self, context, feedback):
            with world.services.sessions() as session:
                document = session.get(DocumentRow, context.document_id)
                erasure.erase_documents(session, world.services.store, [document])
                session.commit()
            return build(context)

    world = World(tmp_path, DeletingGenerator(), runner=_NotYet())
    headers = world.user("garë@shembull.al")
    document_id = world.upload(headers, pdfs["a"])
    assert world.counts()["documents"] == 1

    run_document(world.services, UUID(document_id))  # nuk ngrihet përjashtim

    assert set(world.counts().values()) == {0}
    assert world.stored_files() == set()


class _NotYet:
    def submit(self, document_id) -> None:
        pass  # punëtori nis më vonë, nga testi


def test_a_foreign_key_violation_because_the_document_just_vanished_is_swallowed_any_other_is_raised(
    tmp_path, pdfs, monkeypatch
):
    """Çelësi i huaj refuzon rreshtat e rinj kur dokumenti u fshi pikërisht tani: kjo nuk është defekt. Çdo
    `IntegrityError` tjetër është."""
    from sqlalchemy.exc import IntegrityError

    from analyte.persistence import repository

    world = World(tmp_path, TemplateGenerator(), runner=_NotYet())
    headers = world.user("integritet@shembull.al")
    vanished, real_defect = (
        world.upload(headers, pdfs["a"]),
        world.upload(headers, pdfs["a"], name="dytë.pdf"),
    )

    def delete_then_fail(session, context):
        if context.document_id == UUID(vanished):
            erasure.erase_documents(
                session, world.services.store, [session.get(DocumentRow, context.document_id)]
            )
            session.commit()
        raise IntegrityError("INSERT", {}, Exception("FOREIGN KEY constraint failed"))

    monkeypatch.setattr(repository, "save_context", delete_then_fail)
    run_document(world.services, UUID(vanished))  # pa përjashtim
    assert [r.id for r in _documents(world)] == [UUID(real_defect)]
    with pytest.raises(IntegrityError):
        run_document(world.services, UUID(real_defect))


# Eksporti


def test_export_has_the_owners_data_and_never_credentials_or_other_users(tmp_path, pdfs):
    world = World(tmp_path, TemplateGenerator())
    bob = world.user("bob-eksport@shembull.al")
    world.upload(bob, pdfs["b"], name="SKEDARI_I_BOBIT.pdf")
    alice = world.user("alice-eksport@shembull.al")
    document_id = world.upload(alice, pdfs["a"])
    tokens = world.client.post(
        "/auth/login", json={"email": "alice-eksport@shembull.al", "password": PASSWORD}
    ).json()

    response = world.client.get("/me/export", headers=alice)
    assert response.status_code == 200
    assert (
        response.headers["cache-control"] == "no-store"
        and "attachment" in response.headers["content-disposition"]
    )
    data = response.json()
    text = response.text

    assert data["account"]["email"] == "alice-eksport@shembull.al"
    assert [d["id"] for d in data["documents"]] == [document_id]
    document = data["documents"][0]
    assert document["filename"] == FILENAME and document["state"] == "delivered"
    assert (
        document["findings"]
        and document["explanation"]["text"] == world.explanation(alice, document_id)["text"]
    )
    assert {"analyte_name_canonical", "value", "unit_canonical", "status"} <= set(
        document["findings"][0]
    )
    assert document["model"] == {
        "consent": False,
        "consent_at": None,
        "use": None,
        "gate_kinds": [],
    }
    assert {e["event_type"] for e in data["audit_events"]} >= {
        "document.uploaded",
        "state.transition",
    }

    for forbidden in (
        "bob-eksport",
        "SKEDARI_I_BOBIT",
        "password",
        "argon2",
        tokens["access_token"],
        tokens["refresh_token"],
    ):
        assert forbidden not in text, forbidden
    assert "user.exported" in {e.event_type for e in world.audit()}


def test_export_of_an_account_without_documents(tmp_path):
    world = World(tmp_path, TemplateGenerator())
    headers = world.user("bosh@shembull.al")
    data = world.client.get("/me/export", headers=headers).json()
    assert data["documents"] == [] and data["account"]["email"] == "bosh@shembull.al"


# Afati i ruajtjes

NOW = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)


def _aged(world: World, document_id: str, age_days: int) -> None:
    with world.services.sessions() as session:
        session.get(DocumentRow, UUID(document_id)).uploaded_at = NOW - timedelta(days=age_days)
        session.commit()


def test_retention_deletes_only_what_is_older_than_the_limit_with_the_same_path_as_deletion(
    tmp_path, pdfs
):
    world = World(tmp_path, TemplateGenerator())
    headers = world.user("afat@shembull.al")
    old, edge, fresh = (world.upload(headers, pdfs["a"], name=f"{i}.pdf") for i in range(3))
    _aged(world, old, 100)
    _aged(world, edge, 30)  # saktësisht në afat: ruhet
    _aged(world, fresh, 29)

    result = erasure.purge_expired(
        world.services.sessions, world.services.store, now=NOW, retention_days=30
    )
    assert (result.purged, result.failed) == (1, 0)
    assert {r.id for r in _documents(world)} == {UUID(edge), UUID(fresh)}
    assert len(world.stored_files()) == 2

    # Një orë më vonë "edge" kalon afatin ("fresh" jo); përsëritja e së njëjtës kohë nuk fshin asgjë tjetër.
    assert (
        erasure.purge_expired(
            world.services.sessions, world.services.store, now=NOW, retention_days=30
        ).purged
        == 0
    )
    later = NOW + timedelta(hours=1)
    assert (
        erasure.purge_expired(
            world.services.sessions, world.services.store, now=later, retention_days=30
        ).purged
        == 1
    )
    assert {r.id for r in _documents(world)} == {UUID(fresh)} and len(world.stored_files()) == 1

    expired = world.audit("document.expired")
    assert [e.payload for e in expired] == [{"retention_days": 30}, {"retention_days": 30}]
    assert all(
        "sha256" not in e.payload
        for e in world.audit("document.uploaded")
        if e.document_id in {UUID(old), UUID(edge)}
    )


def _documents(world: World) -> list[DocumentRow]:
    with world.services.sessions() as session:
        return list(session.scalars(select(DocumentRow)))


def test_retention_of_zero_keeps_everything(tmp_path, pdfs):
    world = World(tmp_path, TemplateGenerator())
    headers = world.user("pa-afat@shembull.al")
    document_id = world.upload(headers, pdfs["a"])
    _aged(world, document_id, 10_000)
    assert world.settings.document_retention_days == 0
    result = erasure.purge_expired(
        world.services.sessions, world.services.store, now=NOW, retention_days=0
    )
    assert (result.purged, result.failed) == (0, 0) and len(_documents(world)) == 1


def test_one_document_that_cannot_be_deleted_does_not_stop_the_others(tmp_path, pdfs):
    world = World(tmp_path, TemplateGenerator())
    headers = world.user("pengese@shembull.al")
    stuck, other = (
        world.upload(headers, pdfs["a"]),
        world.upload(headers, pdfs["a"], name="tjetri.pdf"),
    )
    _aged(world, stuck, 90)
    _aged(world, other, 90)
    stuck_path = world.document_row(stuck).storage_path

    class Failing(EncryptedStore):
        def delete(self, name: str) -> None:
            if name == stuck_path:
                raise PermissionError("nuk fshihet")
            super().delete(name)

    store = Failing(world.settings.storage_dir, world.settings.storage_key)
    result = erasure.purge_expired(world.services.sessions, store, now=NOW, retention_days=30)
    assert (result.purged, result.failed) == (1, 1)
    # Dokumenti që nuk u fshi mbetet i plotë dhe i ripërsëritshëm, nuk ka skedar pa rresht.
    assert {r.id for r in _documents(world)} == {UUID(stuck)} and world.stored_files() == {
        stuck_path
    }
    assert (
        erasure.purge_expired(
            world.services.sessions, world.services.store, now=NOW, retention_days=30
        ).purged
        == 1
    )


def test_the_retention_setting_defaults_to_off_and_rejects_negative_values():
    base = {
        "_env_file": None,
        "jwt_secret": "t" * 48,
        "storage_key": Fernet.generate_key().decode(),
    }
    assert Settings(**base).document_retention_days == 0
    assert Settings(**base, document_retention_days=45).document_retention_days == 45
    with pytest.raises(ValueError):
        Settings(**base, document_retention_days=-1)


def test_the_worker_schedules_the_purge(monkeypatch):
    monkeypatch.setenv("ANALYTE_JWT_SECRET", "t" * 48)
    monkeypatch.setenv("ANALYTE_STORAGE_KEY", Fernet.generate_key().decode())
    from analyte.config import get_settings

    get_settings.cache_clear()
    try:
        worker = importlib.reload(importlib.import_module("analyte.orchestration.worker"))
        jobs = [
            job
            for job in worker.WorkerSettings.cron_jobs
            if job.coroutine is worker.purge_expired_job
        ]
        # puna e fshirjes është e planifikuar (bashkë me atë të rindërgimit, ADR 0018)
        assert len(jobs) == 1
        assert jobs[0].minute == {7} and jobs[0].hour is None  # çdo orë
    finally:
        get_settings.cache_clear()
