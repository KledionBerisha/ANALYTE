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


def is_known(name: str) -> bool:
    return resolve(name) is not None


def known_forms() -> int:
    """Sa forma të shkruara njihen. Shifër përshkruese për Tabelën T1."""
    return sum(1 for value in _index().values() if value != AMBIGUOUS)
