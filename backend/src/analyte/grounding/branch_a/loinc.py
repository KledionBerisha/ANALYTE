"""
Nga emri i shtypur te kodi LOINC.

Laboratorët e shkruajnë të njëjtin analit në shumë mënyra: "Hemoglobina",
"HGB", "Hb". Tabela e analiteve i mban këto forma, dhe ky modul i kthen
në një indeks kërkimi.

Përputhja është e saktë pas normalizimit dhe jo e afërt. Një përputhje e
afërt — distancë vargjesh, nënvargje — do ta ngatërronte "Kalciumi" me
"Kaliumi" herët a vonë, dhe ngatërrimi do të hynte i heshtur në një
shpjegim për pacientin. Emri i panjohur kthehet si i panjohur; kjo e ul
mbulimin e PK1 në mënyrë të dukshme, e cila është pikërisht sjellja e
dëshiruar.

Rasti i dykuptimësisë trajtohet shprehimisht: nëse dy analite pretendojnë
të njëjtën formë, asnjëri nuk e fiton. Zgjedhja e "të parit" do të
varej nga rendi i rreshtave në një CSV.
"""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache

from analyte.catalog import Analyte, analytes_by_code

_PUNCTUATION = re.compile(r"[^\w\s]", re.UNICODE)
_WHITESPACE = re.compile(r"\s+")

AMBIGUOUS = "<ambiguous>"
"""Shënues i brendshëm për forma që i përkasin më shumë se një analiti."""


def normalize_name(name: str) -> str:
    """Forma e krahasueshme e një emri.

    Hiqen shenjat e pikësimit dhe theksi i shkronjave, sepse "ALT (GPT)",
    "ALT/GPT" dhe "alt gpt" janë i njëjti analit i shtypur ndryshe.
    Shkronjat shqipe ë dhe ç normalizohen bashkë me të tjerat: OCR-ja i
    ngatërron rregullisht me e dhe c, dhe një hartë që i dallon ato do të
    dështonte pikërisht te kanali ku ndihma nevojitet më shumë.
    """
    folded = unicodedata.normalize("NFKD", name.casefold())
    stripped = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return _WHITESPACE.sub(" ", _PUNCTUATION.sub(" ", stripped)).strip()


@lru_cache(maxsize=1)
def _index() -> dict[str, str]:
    """Harta formë e normalizuar → kod, me dykuptimësitë e shënuara."""
    index: dict[str, str] = {}
    for code, analyte in analytes_by_code().items():
        for form in _forms(analyte):
            key = normalize_name(form)
            if not key:
                continue
            current = index.get(key)
            if current is None:
                index[key] = code
            elif current != code:
                index[key] = AMBIGUOUS
    return index


def _forms(analyte: Analyte) -> tuple[str, ...]:
    return (analyte.name_canonical_sq, analyte.narrative_name, *analyte.variants)


def resolve(name: str) -> str | None:
    """Kodi LOINC i një emri të shtypur, ose None nëse nuk njihet."""
    code = _index().get(normalize_name(name))
    return None if code in (None, AMBIGUOUS) else code


MIN_INFLECTED_LENGTH = 5
"""Fjala e parë duhet të ketë të paktën kaq shkronja para se të provohet trajta e shquar: shkurtesat (K, P, Na, Ca, Pt) nuk
lakohen, dhe heqja e një mbaresë prej tyre do të përputhej rastësisht me një shkurtesë tjetër."""


def _token_variants(token: str) -> list[str]:
    """Trajtat e pashquara të mundshme të një fjale (pas normalizimit ë → e)."""
    if len(token) < MIN_INFLECTED_LENGTH:
        return []
    out: list[str] = []
    if token.endswith("a"):
        out.append(token[:-1] + "e")  # Hemoglobina → Hemoglobine(ë)
    if token.endswith("ja"):
        out.append(token[:-2] + "e")  # Ureja → Ure(a)
    for ending in ("ve", "it", "ut", "in", "un"):  # leukociteve, klorit, kalciumit, natriumin
        if token.endswith(ending):
            out.append(token[: -len(ending)])
    for ending in ("es", "en"):  # hemoglobinës, hemoglobinën → hemoglobine
        if token.endswith(ending):
            out.append(token[:-1])
    for ending in ("i", "u", "t"):  # Kolesteroli, Natriumi, Leukocitet
        if token.endswith(ending):
            out.append(token[: -len(ending)])
    return [variant for variant in dict.fromkeys(out) if len(variant) >= 4]


def inflected_candidates(name: str) -> tuple[str, ...]:
    """Trajtat e pashquara të mundshme të një emri të lakuar ("Kolesteroli HDL" → "Kolesterol HDL").

    Lakimi prek fjalën e parë dhe të fundit (emri kryesor, ose emri i gjinisë së dytë si te "alanin aminotransferazës"). Tabela
    mban emrin si "Hemoglobinë në gjak" ose "Kolesterol HDL"; teksti i gjeneruar e shkruan "Hemoglobina në gjak",
    "hemoglobinës", "leukociteve", "klorit", "Kolesteroli HDL". Mbaresat që i lidhin janë në `_token_variants`.
    """
    original_tokens = normalize_name(name).split(" ")
    # "të" e lidh emrin në rasën gjinore ("përqendrimit mesatar të hemoglobinës") ku tabela ka "i": të dyja trajtat provohen.
    versions = [original_tokens]
    if "te" in original_tokens[1:]:
        versions.append(["i" if token == "te" else token for token in original_tokens])
    candidates: list[str] = []
    for tokens in versions:
        first = [tokens[0], *_token_variants(tokens[0])]
        last = [tokens[-1], *_token_variants(tokens[-1])] if len(tokens) > 1 else [tokens[-1]]
        for head in first:
            for tail in last:
                if len(tokens) == 1:
                    candidates.append(head)
                else:
                    candidates.append(" ".join([head, *tokens[1:-1], tail]))
    original = " ".join(original_tokens)
    return tuple(c for c in dict.fromkeys(candidates) if c != original)


def resolve_inflected(name: str) -> str | None:
    """Si `resolve`, por pranon edhe trajtën e shquar të emrit (`r1.4`).

    Përputhja mbetet e saktë: një trajtë e lakuar pranohet vetëm kur ajo e pashquara është një formë e njohur dhe vetëm një
    analit e pretendon. "Kaliumi" dhe "Kalciumi" nuk ngatërrohen, sepse asnjëra nuk bëhet tjetra me heqjen e një mbarese.
    """
    code = resolve(name)
    if code is not None:
        return code
    hits = {_index().get(candidate) for candidate in inflected_candidates(name)} - {None, AMBIGUOUS}
    return hits.pop() if len(hits) == 1 else None


def is_known(name: str) -> bool:
    return resolve(name) is not None


def known_forms() -> int:
    """Sa forma të shkruara njihen. Shifër përshkruese për Tabelën T1."""
    return sum(1 for value in _index().values() if value != AMBIGUOUS)
