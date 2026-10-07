"""
Modeli gjuhësor te aplikacioni i uebit (ADR 0017).

"""

from __future__ import annotations

import random
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from analyte.config import Settings
from analyte.generation.llm import Completion, LlmGenerator, ProviderError
from analyte.generation.templates import TemplateGenerator, build
from analyte.orchestration.tasks import Services, build_generator, build_services
from analyte.persistence.database import create_schema, make_engine, make_session_factory
from analyte.persistence.storage import EncryptedStore
from tests.fixtures.mailbox import client_for, register_confirmed

PASSWORD = "fjalekalim-testi-i-gjate"
FILENAME = "Analiza_Arben_Krasniqi_2026.pdf"


def _settings(tmp: Path, **overrides) -> Settings:
    return Settings(
        _env_file=None,  # kopja e zhvilluesit mund të ketë çelësin e vërtetë; testet nuk e lexojnë
        database_url=f"sqlite:///{tmp / 'a.db'}",
        jwt_secret="t" * 48,
        storage_key=Fernet.generate_key().decode(),
        storage_dir=tmp / "storage",
        job_runner="inline",
        ocr=False,
        **overrides,
    )


def _document():
    from data_generator.generate import render
    from data_generator.ground_truth import build_document
    from data_generator.ids import IdFactory

    for index in range(20):
        rng = random.Random(f"model-service/{index}")
        document = build_document(rng, IdFactory(rng), scanned_share=0.0)
        if document.context.findings:
            return render(document, seed=5, index=index)
    raise AssertionError("asnjë dokument me gjetje")  # pragma: no cover


class FakeClient:
    """Një ofrues i simuluar: kthen tekstet e dhëna me radhë, ose hedh gabimin e dhënë."""

    provider, model, cache = "fake", "fake-model-1", None

    def __init__(self, outputs=(), error: Exception | None = None) -> None:
        self.outputs, self.error, self.prompts = list(outputs), error, []

    def complete(self, system: str, user: str) -> Completion:
        self.prompts.append(user)
        if self.error is not None:
            raise self.error
        return Completion(text=self.outputs.pop(0), model=self.model)


def _app(tmp: Path, generator):
    # pëlqimi pyetet vetëm kur modeli është i ndezur (ADR 0019)
    settings = _settings(tmp, service_generator="model")
    engine = make_engine(settings.database_url)
    create_schema(engine)
    services = Services(
        sessions=make_session_factory(engine),
        store=EncryptedStore(settings.storage_dir, settings.storage_key),
        generator=generator,
    )
    client = client_for(settings, services)
    register_confirmed(client, "model@shembull.al", PASSWORD)
    token = client.post(
        "/auth/login", json={"email": "model@shembull.al", "password": PASSWORD}
    ).json()["access_token"]
    return client, {"Authorization": f"Bearer {token}"}


def _upload(client, headers, pdf: bytes, consent: bool = True) -> str:
    """Këto teste provojnë rrugën e modelit, prandaj pacienti jep pëlqimin (ADR 0019); pa të shih `test_data_protection.py`."""
    response = client.post(
        "/documents",
        headers=headers,
        files={"file": (FILENAME, pdf, "application/pdf")},
        data={"model_consent": "true" if consent else "false"},
    )
    assert response.status_code == 202, response.text
    return response.json()["id"]


# Zgjedhja e gjeneruesit


def test_by_default_the_app_generates_with_the_template(tmp_path):
    assert isinstance(build_generator(_settings(tmp_path)), TemplateGenerator)


def test_a_provider_configured_for_the_experiments_does_not_turn_the_model_on_in_the_app(tmp_path):
    """`.env` ka ofruesin dhe çelësin për harness-in; kjo vetëm nuk duhet t'u dërgojë ngarkimet e vërteta një ofruesi."""
    settings = _settings(
        tmp_path, llm_provider="mistral", llm_model="ministral-14b-2512", llm_api_key="çelës-prove"
    )
    assert settings.service_generator == "template"
    assert isinstance(build_generator(settings), TemplateGenerator)
    assert isinstance(build_services(settings).generator, TemplateGenerator)


def test_with_the_switch_on_the_app_generates_with_the_model_and_keeps_no_cache(tmp_path):
    settings = _settings(
        tmp_path,
        service_generator="model",
        llm_provider="mistral",
        llm_model="ministral-14b-2512",
        llm_api_key="çelës-prove",
    )
    generator = build_generator(settings)
    assert isinstance(generator, LlmGenerator)
    assert generator.name.startswith("mistral:ministral-14b-2512:")
    assert generator.client.cache is None  # asnjë përgjigje e pacientit nuk shkruhet në disk


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"llm_provider": "mistral", "llm_model": "ministral-14b-2512"}, "ANALYTE_LLM_API_KEY"),
        ({"llm_provider": "mistral", "llm_api_key": "çelës-prove"}, "ANALYTE_LLM_MODEL"),
        (
            {"llm_provider": "nuk-ekziston", "llm_model": "m", "llm_api_key": "çelës-prove"},
            "ofrues i panjohur",
        ),
        ({}, "ofrues i panjohur"),  # çelësi `model` pa ofrues fare
    ],
)
def test_an_incomplete_model_configuration_stops_the_service_at_start(tmp_path, overrides, message):
    with pytest.raises(ProviderError, match=message):
        build_services(_settings(tmp_path, service_generator="model", **overrides))


# Rruga e plotë me modelin


@pytest.fixture(scope="module")
def document():
    """Dokumenti dhe e vërteta e tij, me këshillat e tabelës të bashkangjitura ashtu si i bashkangjit shërbimi.

    Korpusi nuk i mban këshillat (ADR 0023), kurse shërbimi ia shton kontekstit; R8 kërkon fjalitë e tyre
    fjalë për fjalë, prandaj teksti i shabllonit që i jepet modelit të rremë duhet ndërtuar mbi po atë kontekst.
    """
    from dataclasses import replace

    from analyte.grounding.branch_a.advice import attach

    pdf, truth = _document()
    context = truth.context.model_copy(update={"advice": attach(truth.context.findings)})
    return pdf, replace(truth, context=context)


def _explanation(client, headers, document_id):
    return client.get(f"/documents/{document_id}/explanation", headers=headers).json()


def test_a_verified_model_text_is_delivered_with_the_model_notice(tmp_path, document):
    pdf, truth = document
    good = build(truth.context)
    fake = FakeClient([good])
    client, headers = _app(tmp_path, LlmGenerator(fake))

    body = _explanation(client, headers, _upload(client, headers, pdf))
    assert body["generator"] == "fake:fake-model-1:p1"
    assert body["verification"]["passed"] is True and body["verification"]["is_fallback"] is False
    assert "model" in [n["code"] for n in body["notices"]]
    assert len(fake.prompts) == 1


def test_what_is_sent_to_the_provider_never_holds_the_patients_name_or_the_filename(
    tmp_path, document
):
    pdf, truth = document
    fake = FakeClient([build(truth.context)])
    client, headers = _app(tmp_path, LlmGenerator(fake))
    _upload(client, headers, pdf)

    sent = "\n".join(fake.prompts)
    assert sent  # u dërgua diçka: provë që kontrolli nuk është bosh
    for part in truth.patient_name.split():
        assert part not in sent, part
    assert "Arben" not in sent and "Krasniqi_2026" not in sent and FILENAME not in sent


def test_a_rejected_first_attempt_is_retried_once_with_the_violations_and_then_delivered(
    tmp_path, document
):
    pdf, truth = document
    good = build(truth.context)
    fake = FakeClient([good + " Vlera e matur është 987654.", good])
    client, headers = _app(tmp_path, LlmGenerator(fake))
    document_id = _upload(client, headers, pdf)

    body = _explanation(client, headers, document_id)
    assert body["verification"]["passed"] is True and body["generator"] == "fake:fake-model-1:p1"
    assert len(fake.prompts) == 2
    # shkelja e përpjekjes së parë shkon te e dyta, si te eksperimentet
    assert "987654" in fake.prompts[1]
    attempts = client.get(f"/documents/{document_id}/verification", headers=headers).json()[
        "attempts"
    ]
    assert [(a["attempt"], a["delivered"]) for a in attempts] == [(1, False), (2, True)]


def test_two_rejected_attempts_fall_back_to_the_template_without_the_model_notice(
    tmp_path, document
):
    pdf, truth = document
    bad = build(truth.context) + " Vlera e matur është 987654."
    client, headers = _app(tmp_path, LlmGenerator(FakeClient([bad, bad])))

    body = _explanation(client, headers, _upload(client, headers, pdf))
    codes = [n["code"] for n in body["notices"]]
    assert (
        body["verification"]["is_fallback"] is True and "fallback" in codes and "model" not in codes
    )
    assert "987654" not in body["text"]


def test_a_provider_outage_does_not_lose_the_document(tmp_path, document):
    pdf, truth = document
    fake = FakeClient(error=ProviderError("ofruesi nuk u arrit"))
    client, headers = _app(tmp_path, LlmGenerator(fake))
    document_id = _upload(client, headers, pdf)

    status = client.get(f"/documents/{document_id}/status", headers=headers).json()
    body = _explanation(client, headers, document_id)
    assert status["state"] == "delivered"
    assert (
        body["verification"]["is_fallback"] is True
        and body["text"].strip() == build(truth.context).strip()
    )
    assert len(fake.prompts) == 2  # dy përpjekje, pastaj shablloni
    attempts = client.get(f"/documents/{document_id}/verification", headers=headers).json()[
        "attempts"
    ]
    assert [a["delivered"] for a in attempts][
        -1
    ] is True  # rreshti i dorëzuar është ai i shablloni rezervë


def test_the_template_alone_carries_no_model_notice(tmp_path, document):
    pdf, _ = document
    client, headers = _app(tmp_path, TemplateGenerator())
    body = _explanation(client, headers, _upload(client, headers, pdf))
    assert body["generator"] == "template"
    assert "model" not in [n["code"] for n in body["notices"]]
