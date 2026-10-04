"""
Klienti i modelit gjuhësor (Gemini) dhe gjeneruesi që e përdor atë.

Dy gjëra që një eksperiment me model të jashtëm kërkon dhe një thirrje e
zakonshme nuk i ka:

**Cache e përgjigjeve (`ResponseCache`).** Çdo përgjigje ruhet në disk me
çelës hash-in e kërkesës së plotë (modeli, temperatura, niveli i arsyetimit,
udhëzimet dhe konteksti). Një ekzekutim i përsëritur — pas një ndërprerjeje,
pas ndryshimit të një metrike, apo nga një person tjetër — nuk bën asnjë
thirrje të re dhe jep saktësisht të njëjtin tekst. Pa të, një rezultat
shpjegohet me "modeli tha diçka tjetër sot", dhe një ofrues që e tërheq një
model nuk e bën të pamundur rishikimin e punimit. Kërkesa që ndryshon, edhe
me një shkronjë, nuk gjen asgjë në cache: nuk ka rrezik të përdoret një
përgjigje e vjetër për një prompt të ri.

**Kufizim shpejtësie dhe rifreskim (`GeminiClient`).** Shtresa falas ka kufij
për minutë dhe për ditë. Thirrjet ndahen me një interval minimal; gabimet e
përkohshme (429, 5xx, rrjeti) rifreskohen me pritje në rritje dhe me
`Retry-After` kur jepet. Kur rifreskimet mbarojnë, hidhet `ProviderUnavailable`.
Ai është ndryshe nga `ProviderError` (kërkesa u refuzua, ose përgjigja nuk
ka tekst të plotë): i pari nuk është gabim i modelit dhe eksperimenti nuk duhet
ta numërojë si të tillë (shih `evaluation.harness`).

Çelësi dërgohet vetëm te kokat (`x-goog-api-key`), kurrë në adresë, dhe hiqet
nga çdo mesazh gabimi para se të shkruhet.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from analyte.domain.models import GroundingContext, Violation

from .prompt import PROMPT_VERSION, build_prompt

API_ROOT = "https://generativelanguage.googleapis.com/v1beta"
TRANSIENT_STATUS = frozenset({429, 500, 502, 503, 504})


class ProviderError(Exception):
    """Kërkesa u refuzua ose përgjigja nuk është e përdorshme (e përhershme)."""


class ProviderUnavailable(ProviderError):
    """Ofruesi nuk u arrit pas rifreskimeve: kuotë, rrjet apo ndërprerje."""


@dataclass(frozen=True, slots=True)
class Completion:
    text: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    thought_tokens: int = 0
    cached: bool = False


@dataclass(slots=True)
class Usage:
    """Çfarë kushtoi një ekzekutim, për raportin e eksperimentit."""

    calls: int = 0
    cache_hits: int = 0
    retries: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    thought_tokens: int = 0

    def to_json(self) -> dict[str, int]:
        return {
            "calls": self.calls,
            "cache_hits": self.cache_hits,
            "retries": self.retries,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "thought_tokens": self.thought_tokens,
        }


class ResponseCache:
    """Përgjigjet e ruajtura, një skedar JSON për çdo kërkesë."""

    def __init__(self, directory: Path) -> None:
        self.directory = Path(directory)

    @staticmethod
    def key(parameters: dict[str, Any]) -> str:
        canonical = json.dumps(parameters, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _path(self, key: str) -> Path:
        return self.directory / key[:2] / f"{key}.json"

    def get(self, key: str) -> Completion | None:
        path = self._path(key)
        if not path.exists():
            return None
        record = json.loads(path.read_text(encoding="utf-8"))
        usage = record.get("usage", {})
        return Completion(
            text=record["text"],
            model=record["model"],
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            thought_tokens=usage.get("thought_tokens", 0),
            cached=True,
        )

    def put(self, key: str, parameters: dict[str, Any], completion: Completion) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "key": key,
            "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "model": completion.model,
            "request": parameters,
            "text": completion.text,
            "usage": {
                "input_tokens": completion.input_tokens,
                "output_tokens": completion.output_tokens,
                "thought_tokens": completion.thought_tokens,
            },
        }
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
        temporary.replace(path)


@dataclass
class ChatClient:
    """Pjesa e përbashkët e çdo ofruesi: cache, kufizimi, rifreskimi, kostot.

    Çdo ofrues e plotëson me pesë gjëra që ndryshojnë: adresën, kokat, trupin e
    kërkesës, leximin e përgjigjes dhe leximin e sinjalit të kuotës (`_hint`).
    Pjesa tjetër — dhe vetë rregullat që një eksperiment kërkon nga një klient —
    nuk varet nga ofruesi, prandaj ndërrimi i ofruesit nuk ndryshon asnjë metrikë.
    """

    api_key: str = field(repr=False)
    model: str
    temperature: float = 0.0
    thinking: str = "low"
    max_output_tokens: int = 4096
    requests_per_minute: int = 10
    timeout_seconds: float = 120.0
    max_retries: int = 6
    cache: ResponseCache | None = None
    transport: httpx.BaseTransport | None = None
    sleep: Callable[[float], None] = time.sleep
    clock: Callable[[], float] = time.monotonic
    provider: str = ""
    base_url: str = ""
    usage: Usage = field(default_factory=Usage)
    _last_request: float | None = field(default=None, init=False, repr=False)

    def complete(self, system: str, user: str) -> Completion:
        parameters = self._parameters(system, user)
        key = ResponseCache.key(parameters)
        if self.cache is not None:
            hit = self.cache.get(key)
            if hit is not None:
                self.usage.cache_hits += 1
                return hit

        completion = self._request(system, user)
        self.usage.calls += 1
        self.usage.input_tokens += completion.input_tokens
        self.usage.output_tokens += completion.output_tokens
        self.usage.thought_tokens += completion.thought_tokens
        if self.cache is not None:
            self.cache.put(key, parameters, completion)
        return completion

    # ------------------------------------------------------------------
    # Ajo që ndryshon sipas ofruesit
    # ------------------------------------------------------------------

    def _url(self) -> str:
        raise NotImplementedError

    def _headers(self) -> dict[str, str]:
        raise NotImplementedError

    def _body(self, system: str, user: str) -> dict[str, Any]:
        raise NotImplementedError

    def _parse(self, payload: dict[str, Any]) -> Completion:
        raise NotImplementedError

    @staticmethod
    def _hint(response: httpx.Response) -> tuple[float | None, bool]:
        """(sa të pritet sipas ofruesit, a është kuota ditore ose mujore e shteruar)."""
        delay: float | None = None
        retry_after = response.headers.get("retry-after", "")
        if retry_after.isdigit():
            delay = float(retry_after)
        return delay, False

    # ------------------------------------------------------------------

    def _parameters(self, system: str, user: str) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "thinking": self.thinking,
            "max_output_tokens": self.max_output_tokens,
            "system": system,
            "user": user,
        }

    def _throttle(self) -> None:
        if self.requests_per_minute <= 0 or self._last_request is None:
            return
        wait = 60.0 / self.requests_per_minute - (self.clock() - self._last_request)
        if wait > 0:
            self.sleep(wait)

    def _request(self, system: str, user: str) -> Completion:
        url, headers, body = self._url(), self._headers(), self._body(system, user)
        reason = ""

        for attempt in range(self.max_retries + 1):
            self._throttle()
            self._last_request = self.clock()
            delay = min(2.0 ** (attempt + 1), 60.0)
            try:
                with httpx.Client(transport=self.transport, timeout=self.timeout_seconds) as http:
                    response = http.post(url, headers=headers, json=body)
            except httpx.TransportError as error:
                reason = f"rrjeti: {type(error).__name__}"
            else:
                if response.status_code == 200:
                    return self._parse(response.json())
                if response.status_code not in TRANSIENT_STATUS:
                    raise ProviderError(self._describe(response))
                reason = self._describe(response)
                hinted, exhausted = self._hint(response)
                if exhausted:
                    # Kuota ditore nuk rikthehet brenda orës: rifreskimi do të humbiste
                    # vetëm kohë. Ekzekutimi ndalet dhe vazhdon nga cache pas rivendosjes.
                    raise ProviderUnavailable(f"kuota e ofruesit u shteru: {reason}")
                if hinted is not None:
                    delay = max(delay, min(hinted, 300.0))

            if attempt < self.max_retries:
                self.usage.retries += 1
                self.sleep(delay)

        raise ProviderUnavailable(f"ofruesi nuk u arrit pas {self.max_retries + 1} përpjekjesh: {reason}")

    def _describe(self, response: httpx.Response) -> str:
        try:
            payload = response.json()
            error = payload.get("error", payload)
            message = error.get("message", "") if isinstance(error, dict) else str(error)
        except ValueError:
            message = response.text[:200]
        return f"HTTP {response.status_code}: {message}".replace(self.api_key, "<çelësi>")[:400]


@dataclass
class GeminiClient(ChatClient):
    """Gemini (`generateContent`)."""

    provider: str = "gemini"

    def _url(self) -> str:
        return f"{API_ROOT}/models/{self.model}:generateContent"

    def _headers(self) -> dict[str, str]:
        return {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}

    def _body(self, system: str, user: str) -> dict[str, Any]:
        config: dict[str, Any] = {
            "temperature": self.temperature,
            "maxOutputTokens": self.max_output_tokens,
        }
        if self.thinking:
            config["thinkingConfig"] = {"thinkingLevel": self.thinking}
        return {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": config,
        }

    @staticmethod
    def _hint(response: httpx.Response) -> tuple[float | None, bool]:
        """Gemini e jep te `error.details`: `RetryInfo.retryDelay` ("8s") dhe
        `QuotaFailure.violations[].quotaId` ("...PerDay..." ose "...PerMinute...")."""
        delay, _ = ChatClient._hint(response)
        daily = False
        try:
            details = response.json().get("error", {}).get("details", [])
        except ValueError:
            return delay, daily
        for detail in details:
            kind = str(detail.get("@type", ""))
            if kind.endswith("RetryInfo"):
                match = re.fullmatch(r"([0-9.]+)s", str(detail.get("retryDelay", "")))
                if match:
                    delay = max(delay or 0.0, float(match.group(1)))
            if kind.endswith("QuotaFailure"):
                daily = daily or any(
                    "PerDay" in str(v.get("quotaId", "")) for v in detail.get("violations", [])
                )
        return delay, daily

    def _parse(self, payload: dict[str, Any]) -> Completion:
        candidates = payload.get("candidates") or []
        if not candidates:
            feedback = payload.get("promptFeedback", {})
            raise ProviderError(f"përgjigje pa kandidat (promptFeedback={feedback})")
        candidate = candidates[0]
        parts = (candidate.get("content") or {}).get("parts") or []
        text = "".join(part.get("text", "") for part in parts if not part.get("thought")).strip()
        finish = candidate.get("finishReason", "")
        if finish not in {"STOP", ""}:
            raise ProviderError(f"përgjigja nuk është e plotë: finishReason={finish}")
        if not text:
            raise ProviderError("përgjigje pa tekst")
        usage = payload.get("usageMetadata", {})
        return Completion(
            text=text,
            model=payload.get("modelVersion", self.model),
            input_tokens=usage.get("promptTokenCount", 0),
            output_tokens=usage.get("candidatesTokenCount", 0),
            thought_tokens=usage.get("thoughtsTokenCount", 0),
        )


OPENAI_BASE_URLS = {
    "mistral": "https://api.mistral.ai/v1",
    "groq": "https://api.groq.com/openai/v1",
    "cerebras": "https://api.cerebras.ai/v1",
    "openrouter": "https://openrouter.ai/api/v1",
}
"""Ofruesit që flasin API-n `chat/completions`; çdo tjetër jepet me `base_url`."""

_EXHAUSTED = re.compile(r"per day|daily|\bTPD\b|\bRPD\b|per month|monthly|credits", re.IGNORECASE)


@dataclass
class OpenAIChatClient(ChatClient):
    """Çdo ofrues me API `POST {base_url}/chat/completions` (Mistral, Groq, Cerebras, OpenRouter…).

    `thinking` nuk dërgohet: parametrat e arsyetimit ndryshojnë nga ofruesi, dhe një
    parametër i panjohur do ta refuzonte kërkesën. Mbetet te çelësi i cache-it."""

    provider: str = "openai_compatible"

    def _url(self) -> str:
        return f"{self.base_url.rstrip('/')}/chat/completions"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _body(self, system: str, user: str) -> dict[str, Any]:
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_output_tokens,
        }

    @staticmethod
    def _hint(response: httpx.Response) -> tuple[float | None, bool]:
        """Këta ofrues nuk kanë format të përbashkët për kuotën: lexohet `Retry-After`,
        dhe një 429 që e quan kufirin "ditor", "mujor" ose të kreditit konsiderohet i shteruar."""
        delay, _ = ChatClient._hint(response)
        if response.status_code != 429:
            return delay, False
        if response.headers.get("x-ratelimit-limit-req-minute") == "0":
            # Mistral: modeli nuk është në planin e çelësit (limit 0 kërkesa/minutë).
            return delay, True
        try:
            payload = response.json()
            error = payload.get("error", payload)
            message = error.get("message", "") if isinstance(error, dict) else str(error)
        except ValueError:
            message = response.text[:300]
        return delay, bool(_EXHAUSTED.search(str(message)))

    def _parse(self, payload: dict[str, Any]) -> Completion:
        choices = payload.get("choices") or []
        if not choices:
            raise ProviderError("përgjigje pa zgjedhje")
        choice = choices[0]
        content = (choice.get("message") or {}).get("content") or ""
        if isinstance(content, list):  # modelet me arsyetim e japin si copëza
            content = "".join(
                chunk.get("text", "") for chunk in content if chunk.get("type", "text") == "text"
            )
        text = str(content).strip()
        finish = choice.get("finish_reason") or "stop"
        if finish != "stop":
            raise ProviderError(f"përgjigja nuk është e plotë: finish_reason={finish}")
        if not text:
            raise ProviderError("përgjigje pa tekst")
        usage = payload.get("usage", {})
        return Completion(
            text=text,
            model=payload.get("model", self.model),
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
        )


class LlmGenerator:
    """`Generator` mbi një klient: konteksti dhe shkeljet bëhen kërkesë, teksti kthehet.

    Emri mban modelin dhe versionin e kërkesës: ruhet me çdo përpjekje, dhe
    pa të një rezultat nuk atribuohet dot te konfigurimi që e prodhoi.
    """

    def __init__(self, client: ChatClient) -> None:
        self.client = client
        self.name = f"{client.provider}:{client.model}:{PROMPT_VERSION}"

    def __call__(self, context: GroundingContext, feedback: tuple[Violation, ...] = ()) -> str:
        prompt = build_prompt(context, feedback)
        return self.client.complete(prompt.system, prompt.user).text


def build_client(
    settings: Any, *, role: str = "generator", model: str | None = None, cache_dir: Path | None = None
) -> ChatClient:
    """Klienti nga konfigurimi, për gjeneruesin ose për gjykatësin (`role="judge"`).

    Gjykatësi trashëgon ofruesin, çelësin dhe adresën e gjeneruesit, përveç
    kur `llm_judge_*` jepen: kështu gjykatësi mund të jetë ofrues tjetër.

    Hedh `ProviderError` me arsyen kur mungon ofruesi, modeli ose çelësi, që një
    ekzekutim të ndalet para se të niset, jo në mes të 500 dokumenteve.
    """
    judge = role == "judge"
    provider = (settings.llm_judge_provider if judge else "") or settings.llm_provider
    key = (settings.llm_judge_api_key if judge else None) or settings.llm_api_key
    base_url = (settings.llm_judge_base_url if judge else "") or settings.llm_base_url
    chosen = model or (settings.llm_judge_model if judge else "") or settings.llm_model

    if provider not in {"gemini", "openai_compatible", *OPENAI_BASE_URLS}:
        raise ProviderError(f"ofrues i panjohur ose i paplotësuar: '{provider}'")
    if not chosen:
        raise ProviderError("mungon ANALYTE_LLM_MODEL")
    if key is None or not key.get_secret_value():
        raise ProviderError("mungon ANALYTE_LLM_API_KEY")

    common: dict[str, Any] = {
        "api_key": key.get_secret_value(),
        "model": chosen,
        "temperature": settings.llm_temperature,
        "thinking": settings.llm_thinking,
        "max_output_tokens": settings.llm_max_output_tokens,
        "requests_per_minute": settings.llm_requests_per_minute,
        "timeout_seconds": settings.llm_timeout_seconds,
        "cache": ResponseCache(cache_dir) if cache_dir is not None else None,
    }
    if provider == "gemini":
        return GeminiClient(**common)
    url = base_url or OPENAI_BASE_URLS.get(provider, "")
    if not url:
        raise ProviderError("ofruesi `openai_compatible` kërkon ANALYTE_LLM_BASE_URL")
    return OpenAIChatClient(**common, provider=provider, base_url=url)
