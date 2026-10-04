"""
Testet e modelit gjuhësor: kërkesa, klienti, cache dhe lidhja me harness-in.

Asnjë test nuk bën thirrje në rrjet: ofruesi zëvendësohet me një transport të
rremë (`httpx.MockTransport`), koha me një orë të rreme. Kjo është kushti që
makina e gjendjeve të mbetet e provueshme pa kuotë dhe pa çelës, ashtu si te
gjeneruesit e rremë të `test_orchestration`.
"""

from __future__ import annotations

import inspect
import json
import random
import re

import httpx
import pytest

from analyte.domain.enums import ProcessingState, ViolationType
from analyte.domain.models import Violation
from analyte.domain.enums import DetectedBy
from analyte.domain.policy import (
    ATTRIBUTION_PREFIX_SQ,
    CRITICAL_BANNER_SQ,
    DISCLAIMER_SQ,
    MAX_GENERATION_ATTEMPTS,
)
from analyte.generation import prompt as prompt_module
from analyte.generation.llm import (
    GeminiClient,
    LlmGenerator,
    ProviderError,
    ProviderUnavailable,
    ResponseCache,
)
from analyte.generation.prompt import PROMPT_VERSION, build_prompt
from analyte.orchestration.process import explain
from evaluation.harness import RunAborted, StrictClient
from tests.fixtures.grounding_context import build_reference_context

KEY = "AIza-fake-test-key-must-never-be-written-anywhere-123456"


# --------------------------------------------------------------------
# Ofruesi i rremë
# --------------------------------------------------------------------


def _ok(text="Një shpjegim.", **extra):
    payload = {
        "candidates": [{"content": {"parts": [{"text": text}]}, "finishReason": "STOP"}],
        "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 4, "thoughtsTokenCount": 7},
        "modelVersion": "gemini-test",
    }
    payload.update(extra)
    return httpx.Response(200, json=payload)


class Server:
    """Kthen përgjigjet e radhës dhe mban mend çfarë mori."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests: list[httpx.Request] = []

    def __call__(self, request):
        self.requests.append(request)
        response = self.responses.pop(0) if self.responses else _ok()
        return response if isinstance(response, httpx.Response) else response()


def user_text(request: httpx.Request) -> str:
    """Teksti i përdoruesit që u dërgua, i lexuar nga trupi JSON."""
    return json.loads(request.read())["contents"][0]["parts"][0]["text"]


def system_text(request: httpx.Request) -> str:
    return json.loads(request.read())["systemInstruction"]["parts"][0]["text"]


class Clock:
    def __init__(self):
        self.now = 0.0
        self.sleeps: list[float] = []

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


def _client(server, clock=None, **options):
    clock = clock or Clock()
    return GeminiClient(
        api_key=KEY,
        model=options.pop("model", "gemini-test"),
        transport=httpx.MockTransport(server),
        sleep=clock.sleep,
        clock=clock.time,
        requests_per_minute=options.pop("requests_per_minute", 0),
        **options,
    )


# --------------------------------------------------------------------
# Kërkesa
# --------------------------------------------------------------------


def test_prompt_takes_only_the_context_and_feedback():
    """Garancia e punimit: asnjë parametër për dokumentin ose tekstin e nxjerrë."""
    assert list(inspect.signature(build_prompt).parameters) == ["context", "feedback"]


def test_prompt_contains_what_the_context_says_and_nothing_with_an_identity():
    context = build_reference_context()
    prompt = build_prompt(context)
    for finding in context.findings:
        assert finding.analyte_name_canonical in prompt.user
    assert DISCLAIMER_SQ in prompt.user
    assert str(context.document_id) not in prompt.user + prompt.system
    assert not re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-", prompt.user + prompt.system)
    assert prompt.version == PROMPT_VERSION


def test_critical_banner_is_given_only_when_there_is_a_critical_value():
    context = build_reference_context()
    assert context.critical_findings()
    assert CRITICAL_BANNER_SQ in build_prompt(context).user
    calm = context.model_copy(update={"findings": tuple(f for f in context.findings if not f.status.is_critical)})
    assert CRITICAL_BANNER_SQ not in build_prompt(calm).user


def test_doctor_statements_are_handed_over_attributed_and_verbatim():
    context = build_reference_context()
    user = build_prompt(context).user
    for assertion in context.assertions:
        assert f"{ATTRIBUTION_PREFIX_SQ} {assertion.text_span}." in user


def test_unexplained_terms_are_marked_so_the_model_does_not_explain_them():
    context = build_reference_context()
    assert context.unexplained_terms
    user = build_prompt(context).user
    for term in context.unexplained_terms:
        assert f"{term}: PA SHPJEGIM" in user


def test_feedback_carries_the_violating_sentence_and_the_rule_but_nothing_else():
    context = build_reference_context()
    violation = Violation(
        type=ViolationType.UNGROUNDED_NUMBER,
        detected_by=DetectedBy.RULE,
        sentence="Vlera është 987654.",
        evidence="numri 987654 nuk gjendet ndër vlerat e nxjerra",
    )
    user = build_prompt(context, (violation,)).user
    assert "Vlera është 987654." in user
    assert "numri 987654 nuk gjendet" in user
    assert "Çdo numër në tekst duhet të gjendet" in user
    assert "987654" not in build_prompt(context).user


def test_prompt_module_does_not_reach_for_a_document():
    source = inspect.getsource(prompt_module)
    for forbidden in ("pdf", "PageText", "ingestion"):
        assert forbidden not in source.replace("pdf_", "")


# --------------------------------------------------------------------
# Klienti
# --------------------------------------------------------------------


def test_successful_call_returns_text_and_usage_and_sends_the_key_only_in_a_header():
    server = Server(_ok("Përshëndetje."))
    client = _client(server)
    completion = client.complete("sistemi", "përdoruesi")
    assert completion.text == "Përshëndetje."
    assert (completion.input_tokens, completion.output_tokens, completion.thought_tokens) == (10, 4, 7)
    request = server.requests[0]
    assert request.headers["x-goog-api-key"] == KEY
    assert KEY not in str(request.url)
    assert (system_text(request), user_text(request)) == ("sistemi", "përdoruesi")


def test_thought_parts_are_not_part_of_the_answer():
    payload = {
        "candidates": [
            {
                "content": {"parts": [{"text": "mendim", "thought": True}, {"text": "përgjigje"}]},
                "finishReason": "STOP",
            }
        ]
    }
    client = _client(Server(httpx.Response(200, json=payload)))
    assert client.complete("s", "u").text == "përgjigje"


def test_request_body_pins_temperature_thinking_and_token_limit():
    server = Server()
    _client(server, temperature=0.0, thinking="low", max_output_tokens=777).complete("s", "u")
    config = json.loads(server.requests[0].read())["generationConfig"]
    assert config == {
        "temperature": 0.0,
        "maxOutputTokens": 777,
        "thinkingConfig": {"thinkingLevel": "low"},
    }


def test_transient_errors_are_retried_with_a_growing_wait_and_retry_after_is_honoured():
    clock = Clock()
    server = Server(
        httpx.Response(429, json={"error": {"message": "kuota"}}, headers={"retry-after": "30"}),
        httpx.Response(503, json={"error": {"message": "i zënë"}}),
        _ok("më në fund"),
    )
    client = _client(server, clock)
    assert client.complete("s", "u").text == "më në fund"
    assert len(server.requests) == 3
    assert clock.sleeps[0] >= 30
    assert clock.sleeps[1] > 2
    assert client.usage.retries == 2 and client.usage.calls == 1


def test_exhausted_retries_raise_provider_unavailable_not_a_generic_error():
    server = Server(*[httpx.Response(429, json={"error": {"message": "kuota ditore"}})] * 10)
    client = _client(server, max_retries=2)
    with pytest.raises(ProviderUnavailable, match="3 përpjekjesh"):
        client.complete("s", "u")
    assert len(server.requests) == 3


def test_network_failure_is_transient():
    def boom(request):
        raise httpx.ConnectError("pa rrjet")

    client = GeminiClient(
        api_key=KEY, model="m", transport=httpx.MockTransport(boom), sleep=lambda s: None,
        requests_per_minute=0, max_retries=1,
    )
    with pytest.raises(ProviderUnavailable, match="rrjeti"):
        client.complete("s", "u")


def test_rejected_request_is_permanent_and_never_echoes_the_key():
    server = Server(httpx.Response(400, json={"error": {"message": f"çelësi {KEY} është i pavlefshëm"}}))
    client = _client(server)
    with pytest.raises(ProviderError) as caught:
        client.complete("s", "u")
    assert not isinstance(caught.value, ProviderUnavailable)
    assert KEY not in str(caught.value)
    assert len(server.requests) == 1


@pytest.mark.parametrize("finish", ["MAX_TOKENS", "SAFETY", "RECITATION"])
def test_truncated_or_blocked_answers_are_not_used(finish):
    payload = {"candidates": [{"content": {"parts": [{"text": "gjysma e"}]}, "finishReason": finish}]}
    with pytest.raises(ProviderError, match=finish):
        _client(Server(httpx.Response(200, json=payload))).complete("s", "u")


def test_answer_without_text_or_candidate_is_an_error():
    with pytest.raises(ProviderError):
        _client(Server(httpx.Response(200, json={"candidates": []}))).complete("s", "u")
    empty = {"candidates": [{"content": {"parts": []}, "finishReason": "STOP"}]}
    with pytest.raises(ProviderError, match="pa tekst"):
        _client(Server(httpx.Response(200, json=empty))).complete("s", "u")


def test_calls_are_spaced_to_the_requested_rate():
    clock = Clock()
    client = _client(Server(), clock, requests_per_minute=6)  # një thirrje çdo 10 s
    client.complete("s", "një")
    client.complete("s", "dy")
    assert clock.sleeps == [pytest.approx(10.0)]


# --------------------------------------------------------------------
# Cache
# --------------------------------------------------------------------


def test_second_identical_request_is_served_from_disk_without_a_call(tmp_path):
    server = Server(_ok("e para"))
    client = _client(server, cache=ResponseCache(tmp_path))
    first = client.complete("s", "u")
    second = client.complete("s", "u")
    assert (first.cached, second.cached) == (False, True)
    assert first.text == second.text == "e para"
    assert len(server.requests) == 1
    assert (client.usage.calls, client.usage.cache_hits) == (1, 1)


def test_cache_survives_a_new_process_and_stores_the_request_for_audit(tmp_path):
    _client(Server(_ok("ruajtur")), cache=ResponseCache(tmp_path)).complete("sistemi", "konteksti")
    fresh = _client(Server(), cache=ResponseCache(tmp_path))
    assert fresh.complete("sistemi", "konteksti").text == "ruajtur"
    assert fresh.usage.calls == 0
    record = json.loads(next(tmp_path.rglob("*.json")).read_text(encoding="utf-8"))
    assert record["request"]["user"] == "konteksti" and record["request"]["model"] == "gemini-test"
    assert KEY not in json.dumps(record)


@pytest.mark.parametrize(
    "change",
    [{"model": "tjetër"}, {"temperature": 0.7}, {"thinking": "high"}, {"max_output_tokens": 99}],
)
def test_any_changed_parameter_misses_the_cache(tmp_path, change):
    cache = ResponseCache(tmp_path)
    _client(Server(_ok("a")), cache=cache).complete("s", "u")
    other = _client(Server(_ok("b")), cache=cache, **change)
    assert other.complete("s", "u").text == "b"


def test_changed_prompt_misses_the_cache(tmp_path):
    cache = ResponseCache(tmp_path)
    client = _client(Server(_ok("a"), _ok("b"), _ok("c")), cache=cache)
    assert client.complete("s", "u").text == "a"
    assert client.complete("s", "u.").text == "b"
    assert client.complete("s2", "u").text == "c"


def test_failed_calls_are_never_cached(tmp_path):
    cache = ResponseCache(tmp_path)
    client = _client(Server(httpx.Response(400, json={"error": {"message": "x"}}), _ok("mirë")), cache=cache)
    with pytest.raises(ProviderError):
        client.complete("s", "u")
    assert client.complete("s", "u").text == "mirë"


# --------------------------------------------------------------------
# Gjeneruesi dhe cikli
# --------------------------------------------------------------------


def test_generator_names_the_model_and_the_prompt_version():
    generator = LlmGenerator(_client(Server()))
    assert generator.name == f"gemini:gemini-test:{PROMPT_VERSION}"


def test_second_attempt_prompt_contains_the_first_attempts_violations(tmp_path):
    from analyte.generation import templates

    context = build_reference_context()
    good = templates.build(context)
    bad = good.replace(DISCLAIMER_SQ, f"Vlera e matur është 987654. {DISCLAIMER_SQ}")
    server = Server(_ok(bad), _ok(good))
    generator = LlmGenerator(_client(server))

    explanation = explain(context, generator)

    assert len(explanation.attempts) == 2 and explanation.attempts[1].passed
    first, second = (user_text(r) for r in server.requests)
    assert "987654" not in first
    assert "numri 987654 nuk gjendet" in second


def test_unreachable_provider_stops_the_run_instead_of_becoming_a_template_fallback():
    """`ProviderUnavailable` nuk është gabim i modelit: cikli nuk guxon ta numërojë."""
    context = build_reference_context()
    down = _client(Server(*[httpx.Response(503, json={})] * 5), max_retries=1)
    generator = LlmGenerator(StrictClient(down))
    with pytest.raises(RunAborted):
        explain(context, generator)


def test_refused_answer_is_a_failed_attempt_and_two_of_them_fall_back_to_the_template():
    context = build_reference_context()
    blocked = {"candidates": [{"finishReason": "SAFETY"}]}
    server = Server(*[httpx.Response(200, json=blocked)] * MAX_GENERATION_ATTEMPTS)
    explanation = explain(context, LlmGenerator(_client(server)))
    assert explanation.delivery.value == "template"
    assert all(a.error and "SAFETY" in a.error for a in explanation.attempts)


# --------------------------------------------------------------------
# E6
# --------------------------------------------------------------------


def _pdf(tmp_path):
    from data_generator.generate import render
    from data_generator.ground_truth import build_document
    from data_generator.ids import IdFactory

    for index in range(20):
        rng = random.Random(f"e6/{index}")
        document = build_document(rng, IdFactory(rng), scanned_share=0.0)
        if document.context.findings:
            path = tmp_path / "doc.pdf"
            path.write_bytes(render(document, seed=7, index=index)[0])
            return path, document.context
    raise AssertionError("asnjë dokument me gjetje")  # pragma: no cover


def test_e6_gives_the_document_text_to_the_model_and_counts_its_violations(tmp_path):
    from uuid import uuid4

    from evaluation.pipeline import DocumentInput
    from evaluation.ungrounded import UngroundedPipeline

    path, truth = _pdf(tmp_path)
    server = Server(_ok("Dokumenti thotë se vlera është 987654."))
    pipeline = UngroundedPipeline(client=_client(server))

    output = pipeline.run(DocumentInput(uuid4(), path))

    sent = user_text(server.requests[0])
    assert "Ky është dokumenti mjekësor i pacientit" in sent
    assert truth.findings[0].analyte_name_raw in sent
    assert output.explanation.startswith("Dokumenti thotë")
    assert any(v.type is ViolationType.UNGROUNDED_NUMBER for v in output.verification.violations)
    assert output.violations_reaching_user() == output.verification.violations
    assert len(output.attempts) == 1 and pipeline.ablation == "E6"
    assert pipeline.name.startswith("e6[gemini:gemini-test:u1]")


def test_e6_uses_no_safety_rules_and_no_structure(tmp_path):
    from evaluation.ungrounded import SYSTEM, build_prompt
    from analyte.ingestion.pdf_text import read_pdf

    path, _ = _pdf(tmp_path)
    system, user = build_prompt(read_pdf(path))
    assert system == SYSTEM
    for rule in ("mos shpik", "KOPJOJE", "Mjeku ka shënuar"):
        assert rule.lower() not in (system + user).lower()


def test_e6_pipeline_is_refused_under_another_ablations_id():
    from evaluation import experiments as registry
    from evaluation.harness import run_experiment
    from evaluation.ungrounded import UngroundedPipeline

    result = run_experiment(registry.get("E8"), _EmptyData(), UngroundedPipeline(client=_client(Server())))
    assert not result.measured and "E6" in (result.skipped_reason or "")


class _EmptyData:
    name, version, seed, manifest, cases = "x", "x", 0, {}, ()

    def filter(self, *, channel=None):
        return self

    def __len__(self):
        return 0


def test_unreachable_provider_aborts_e6_too(tmp_path):
    from uuid import uuid4

    from evaluation.pipeline import DocumentInput
    from evaluation.ungrounded import UngroundedPipeline

    path, _ = _pdf(tmp_path)
    down = _client(Server(*[httpx.Response(429, json={})] * 3), max_retries=1)
    with pytest.raises(RunAborted):
        UngroundedPipeline(client=StrictClient(down)).run(DocumentInput(uuid4(), path))


# --------------------------------------------------------------------
# E12 — gjykatësi
# --------------------------------------------------------------------


class _Answers:
    """Klient i rremë: kthen përgjigjet e radhës dhe regjistron kërkesat."""

    def __init__(self, *answers):
        self.answers = list(answers)
        self.sent: list[tuple[str, str]] = []

    def complete(self, system, user):
        from analyte.generation.llm import Completion

        self.sent.append((system, user))
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return Completion(text=answer, model="j")


@pytest.mark.parametrize(
    "answer,expected",
    [
        ('{"label": "polarity_flip"}', (ViolationType.POLARITY_FLIP, True)),
        ('```json\n{"label":"clean"}\n```', (None, True)),
        ("label: ungrounded_number", (ViolationType.UNGROUNDED_NUMBER, True)),
        ("clean", (None, True)),
        ("Nuk jam i sigurt.", (None, False)),
        ('{"label": "diçka_e_shpikur"}', (None, False)),
    ],
)
def test_judge_answers_are_read_as_a_label_or_counted_as_unparsed(answer, expected):
    from evaluation.llm_judge import parse_label

    assert parse_label(answer) == expected


def test_judge_sees_the_context_the_text_and_the_catalogue_definitions_only():
    from evaluation.llm_judge import judge_prompt

    context = build_reference_context()
    system, user = judge_prompt(context, "Një tekst i gjykuar.")
    assert "Një tekst i gjykuar." in user
    for finding in context.findings:
        assert finding.analyte_name_canonical in user
    assert "Çdo numër në tekst duhet të gjendet" in system  # përkufizimi i R1 nga katalogu
    assert "clean" in system
    assert str(context.document_id) not in system + user


def test_judge_scores_through_the_same_detector_metric_as_the_other_two():
    from evaluation.llm_judge import judge_samples
    from evaluation.metrics import detector

    context = build_reference_context()
    items = [
        (None, context, "tekst i pastër"),
        (ViolationType.POLARITY_FLIP, context, "tekst me defekt"),
        (ViolationType.UNGROUNDED_NUMBER, context, "tjetër"),
    ]
    client = _Answers('{"label":"clean"}', '{"label":"polarity_flip"}', "pa formë")
    judgements, unparsed = judge_samples(client, items)
    assert unparsed == 1
    assert [j.predicted for j in judgements] == [None, ViolationType.POLARITY_FLIP, None]
    metrics = detector.measure(judgements)
    assert metrics["false_alarms_on_clean"] == 0
    assert metrics["per_defect_type"]["polarity_flip"]["f1"] == 1.0
    assert metrics["per_defect_type"]["ungrounded_number"]["recall"] == 0.0


def test_refused_judge_call_counts_as_unparsed_not_as_a_crash():
    from evaluation.llm_judge import judge_samples

    context = build_reference_context()
    client = _Answers(ProviderError("SAFETY"))
    judgements, unparsed = judge_samples(client, [(ViolationType.UNGROUNDED_NUMBER, context, "t")])
    assert unparsed == 1 and judgements[0].predicted is None


def test_judge_set_is_the_same_192_texts_as_e10():
    from evaluation.llm_judge import corruption_items

    items = corruption_items(200, 42, "test")
    assert len(items) == 192
    assert sum(1 for actual, _, _ in items if actual is None) == 30


# --------------------------------------------------------------------
# Kuotat
# --------------------------------------------------------------------


def _quota(quota_id, retry="8s"):
    return httpx.Response(
        429,
        json={
            "error": {
                "message": "kuota",
                "details": [
                    {"@type": "type.googleapis.com/google.rpc.QuotaFailure",
                     "violations": [{"quotaId": quota_id}]},
                    {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": retry},
                ],
            }
        },
    )


def test_daily_quota_stops_at_once_instead_of_retrying_for_minutes():
    clock = Clock()
    server = Server(_quota("GenerateRequestsPerDayPerProjectPerModel-FreeTier", "15592s"), _ok())
    with pytest.raises(ProviderUnavailable, match="kuota e ofruesit u shteru"):
        _client(server, clock).complete("s", "u")
    assert len(server.requests) == 1 and clock.sleeps == []


def test_per_minute_quota_waits_what_the_provider_says_and_then_succeeds():
    clock = Clock()
    server = Server(_quota("GenerateRequestsPerMinutePerProjectPerModel-FreeTier", "23s"), _ok("pas pritjes"))
    assert _client(server, clock).complete("s", "u").text == "pas pritjes"
    assert clock.sleeps[0] >= 23


# --------------------------------------------------------------------
# Ofruesit me API `chat/completions` (Mistral, Groq, Cerebras, OpenRouter)
# --------------------------------------------------------------------


def _chat_ok(content="Përgjigje.", finish="stop"):
    return httpx.Response(
        200,
        json={
            "model": "mistral-test-2512",
            "choices": [{"message": {"role": "assistant", "content": content}, "finish_reason": finish}],
            "usage": {"prompt_tokens": 21, "completion_tokens": 5},
        },
    )


def _openai_client(server, **options):
    from analyte.generation.llm import OpenAIChatClient

    clock = Clock()
    return OpenAIChatClient(
        api_key=KEY,
        model="mistral-test",
        base_url="https://api.example.test/v1/",
        transport=httpx.MockTransport(server),
        sleep=clock.sleep,
        clock=clock.time,
        requests_per_minute=0,
        provider="mistral",
        **options,
    )


def test_chat_client_sends_bearer_auth_messages_and_limits_and_reads_usage():
    server = Server(_chat_ok("Përshëndetje."))
    completion = _openai_client(server, temperature=0.0, max_output_tokens=321).complete("sistemi", "përdoruesi")
    request = server.requests[0]
    body = json.loads(request.read())
    assert str(request.url) == "https://api.example.test/v1/chat/completions"
    assert request.headers["authorization"] == f"Bearer {KEY}" and KEY not in str(request.url)
    assert body["messages"] == [
        {"role": "system", "content": "sistemi"},
        {"role": "user", "content": "përdoruesi"},
    ]
    assert (body["temperature"], body["max_tokens"]) == (0.0, 321)
    assert "thinking" not in json.dumps(body).lower()
    assert (completion.text, completion.input_tokens, completion.output_tokens) == ("Përshëndetje.", 21, 5)


def test_chat_client_reads_reasoning_models_chunked_content_and_skips_the_thinking():
    content = [{"type": "thinking", "thinking": "mendim"}, {"type": "text", "text": "përgjigja"}]
    assert _openai_client(Server(_chat_ok(content))).complete("s", "u").text == "përgjigja"


def test_chat_client_refuses_truncated_or_empty_answers():
    with pytest.raises(ProviderError, match="length"):
        _openai_client(Server(_chat_ok("gjysma", finish="length"))).complete("s", "u")
    with pytest.raises(ProviderError, match="pa tekst"):
        _openai_client(Server(_chat_ok(""))).complete("s", "u")


def test_chat_client_stops_at_once_when_the_daily_or_monthly_quota_is_gone():
    body = {"error": {"message": "Rate limit reached: tokens per day (TPD): Limit 200000"}}
    server = Server(httpx.Response(429, json=body), _chat_ok())
    with pytest.raises(ProviderUnavailable, match="kuota e ofruesit"):
        _openai_client(server).complete("s", "u")
    assert len(server.requests) == 1


def test_chat_client_retries_a_per_minute_limit_and_honours_retry_after():
    clock = Clock()
    from analyte.generation.llm import OpenAIChatClient

    server = Server(
        httpx.Response(429, json={"message": "Too many requests"}, headers={"retry-after": "20"}),
        _chat_ok("pas pritjes"),
    )
    client = OpenAIChatClient(
        api_key=KEY, model="m", base_url="https://x.test/v1", transport=httpx.MockTransport(server),
        sleep=clock.sleep, clock=clock.time, requests_per_minute=0,
    )
    assert client.complete("s", "u").text == "pas pritjes"
    assert clock.sleeps[0] >= 20


def test_chat_client_never_echoes_the_key_and_uses_a_separate_cache_key_per_provider(tmp_path):
    server = Server(httpx.Response(401, json={"error": {"message": f"çelës i gabuar {KEY}"}}))
    with pytest.raises(ProviderError) as caught:
        _openai_client(server).complete("s", "u")
    assert KEY not in str(caught.value)

    cache = ResponseCache(tmp_path)
    _openai_client(Server(_chat_ok("nga mistral")), cache=cache).complete("s", "u")
    assert _client(Server(_ok("nga gemini")), cache=cache).complete("s", "u").text == "nga gemini"


class _Settings:
    """Konfigurim i rremë me po ato fusha që lexon `build_client`."""

    def __init__(self, **values):
        from pydantic import SecretStr

        base = dict(
            llm_provider="mistral", llm_base_url="", llm_model="mistral-test",
            llm_api_key=SecretStr(KEY), llm_judge_provider="", llm_judge_api_key=None,
            llm_judge_base_url="", llm_judge_model="", llm_temperature=0.0, llm_thinking="low",
            llm_max_output_tokens=100, llm_requests_per_minute=5, llm_timeout_seconds=10,
        )
        base.update(values)
        for name, value in base.items():
            setattr(self, name, value)


def test_build_client_picks_the_provider_class_and_the_known_base_url():
    from analyte.generation.llm import GeminiClient, OpenAIChatClient, build_client

    mistral = build_client(_Settings())
    assert isinstance(mistral, OpenAIChatClient) and mistral.base_url == "https://api.mistral.ai/v1"
    assert isinstance(build_client(_Settings(llm_provider="gemini")), GeminiClient)
    custom = build_client(_Settings(llm_provider="openai_compatible", llm_base_url="https://h.test/v1"))
    assert custom.base_url == "https://h.test/v1"


def test_build_client_refuses_incomplete_configuration_before_any_call():
    from analyte.generation.llm import build_client

    for bad in (
        {"llm_provider": ""},
        {"llm_provider": "diçka"},
        {"llm_model": ""},
        {"llm_api_key": None},
        {"llm_provider": "openai_compatible", "llm_base_url": ""},
    ):
        with pytest.raises(ProviderError):
            build_client(_Settings(**bad))


def test_judge_can_be_another_provider_with_its_own_key():
    from pydantic import SecretStr

    from analyte.generation.llm import GeminiClient, build_client

    settings = _Settings(
        llm_judge_provider="gemini", llm_judge_model="gemini-test",
        llm_judge_api_key=SecretStr("judge-key-123"),
    )
    judge = build_client(settings, role="judge")
    assert isinstance(judge, GeminiClient) and judge.api_key == "judge-key-123"
    generator = build_client(settings)
    assert generator.api_key == KEY and generator.provider == "mistral"
    inherited = build_client(_Settings(), role="judge")
    assert inherited.provider == "mistral" and inherited.api_key == KEY


def test_chat_client_treats_a_zero_request_limit_as_a_model_outside_the_plan():
    server = Server(
        httpx.Response(
            429, json={"message": "Rate limit exceeded"}, headers={"x-ratelimit-limit-req-minute": "0"}
        ),
        _chat_ok(),
    )
    with pytest.raises(ProviderUnavailable, match="kuota e ofruesit"):
        _openai_client(server).complete("s", "u")
    assert len(server.requests) == 1


# --------------------------------------------------------------------
# E12 me gjykatës Claude (batch-e)
# --------------------------------------------------------------------


@pytest.fixture(scope="module")
def exported(tmp_path_factory):
    from evaluation import judge_batches

    root = tmp_path_factory.mktemp("judge")
    manifest = judge_batches.export(root / "batches", root / "key.json", n=200, seed=42, split="test")
    return root, manifest


def test_export_covers_the_same_297_samples_in_mixed_chunks(exported):
    root, manifest = exported
    assert manifest["items"] == 192 + 105 and manifest["sources"] == {"E10": 192, "B": 105}
    chunks = sorted((root / "batches").glob("chunk_*.json"))
    assert len(chunks) == manifest["chunks"] == 15
    ids = [item["id"] for c in chunks for item in json.loads(c.read_text(encoding="utf-8"))["items"]]
    assert len(ids) == len(set(ids)) == 297
    first = json.loads(chunks[0].read_text(encoding="utf-8"))["items"]
    assert len({i["id"].split("-")[0] for i in first}) == 2  # përzierje E10 dhe B, jo një burim


def test_batch_files_contain_no_true_labels(exported):
    root, _ = exported
    key = json.loads((root / "key.json").read_text(encoding="utf-8"))
    assert key["actual"]  # etiketat janë te çelësi...
    for path in (root / "batches").iterdir():
        text = path.read_text(encoding="utf-8")
        assert '"actual"' not in text and '"etiketa"' not in text
    for chunk in (root / "batches").glob("chunk_*.json"):
        text = chunk.read_text(encoding="utf-8")
        for label in ("polarity_flip", "hedge_removed", "fabricated_finding", "direction_mismatch"):
            assert label not in text  # ...dhe emrat e llojeve nuk rrjedhin te teksti i gjykuar
    assert "polarity_flip" in (root / "batches" / "instructions.md").read_text(encoding="utf-8")


def test_judge_prompt_in_the_batches_is_the_same_as_the_api_judges(exported):
    from evaluation.llm_judge import SYSTEM

    root, _ = exported
    assert SYSTEM in (root / "batches" / "instructions.md").read_text(encoding="utf-8")


def _answer_all(root, wrong=(), drop=()):
    from evaluation import judge_batches

    key = json.loads((root / "key.json").read_text(encoding="utf-8"))
    lines = []
    for item_id in key["order"]:
        if item_id in drop:
            continue
        label = "clean" if item_id in wrong else key["actual"][item_id]
        lines.append(json.dumps({"id": item_id, "label": label}))
    (root / "batches" / "answers_00.jsonl").write_text("\n".join(lines), encoding="utf-8")
    return judge_batches


def test_ingest_scores_a_perfect_judge_as_perfect(exported):
    root, _ = exported
    judge_batches = _answer_all(root)
    result = judge_batches.ingest(root / "batches", root / "key.json", model="prova")
    assert result["result"]["metrics"]["macro_f1"] == 1.0 and result["kit_B"]["metrics"]["macro_f1"] == 1.0
    assert result["result"]["samples"] == 192 and result["kit_B"]["samples"] == 105
    assert result["result"]["unparsed"] == 0 and result["kit_B"]["missing"] == []
    assert result["kit_B"]["model"] == "prova" and result["kit_B"]["judge"] == "claude-subagent"


def test_ingest_counts_missing_answers_as_misses_not_as_silence(exported):
    root, _ = exported
    key = json.loads((root / "key.json").read_text(encoding="utf-8"))
    victim = next(i for i in key["order"] if key["actual"][i] == "polarity_flip" and key["source"][i] == "B")
    judge_batches = _answer_all(root, drop={victim})
    result = judge_batches.ingest(root / "batches", root / "key.json", model="prova")
    assert result["kit_B"]["missing"] == [victim] and result["kit_B"]["unparsed"] == 1
    assert result["kit_B"]["metrics"]["per_defect_type"]["polarity_flip"]["recall"] < 1.0


def test_ingest_scores_a_judge_that_calls_everything_clean_as_useless(exported):
    root, _ = exported
    key = json.loads((root / "key.json").read_text(encoding="utf-8"))
    judge_batches = _answer_all(root, wrong=set(key["order"]))
    result = judge_batches.ingest(root / "batches", root / "key.json", model="prova")
    assert result["result"]["metrics"]["macro_f1"] == 0.0
    assert result["result"]["metrics"]["false_alarms_on_clean"] == 0


def test_ingest_refuses_answers_for_unknown_ids_and_requires_a_model(exported, tmp_path):
    root, _ = exported
    _answer_all(root)
    with (root / "batches" / "answers_01.jsonl").open("w", encoding="utf-8") as handle:
        handle.write(json.dumps({"id": "X-999", "label": "clean"}))
    from evaluation import judge_batches

    with pytest.raises(ValueError, match="të panjohur"):
        judge_batches.ingest(root / "batches", root / "key.json", model="prova")
    (root / "batches" / "answers_01.jsonl").unlink()
    with pytest.raises(SystemExit):
        judge_batches.main(["ingest", str(root / "batches"), "--key", str(root / "key.json")])
