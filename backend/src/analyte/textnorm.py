"""
Normalizimi i tekstit, i përbashkët për të dyja degët.

Dega A krahason emra analitesh; Dega B krahason terma mjekësorë. Të dyja
kanë nevojë për të njëjtën gjë: një formë të krahasueshme e cila nuk
varet nga shkronjat e mëdha, nga pikësimi dhe as nga theksi.

Heqja e theksit është vendim me pasojë. "Hemoglobinë" dhe "Hemoglobine"
bëhen e njëjta gjë, çka do të thotë se një dallim i vërtetë drejtshkrimor
humbet. Kjo pranohet me vetëdije: OCR-ja i ngatërron rregullisht ë me e
dhe ç me c, dhe një krahasim që i dallon ato do të dështonte pikërisht te
kanali ku ndihma nevojitet më shumë. Në shqip nuk ka çift fjalësh
mjekësore që dallohen vetëm nga theksi.
"""

from __future__ import annotations

import re
import unicodedata

_PUNCTUATION = re.compile(r"[^\w\s]", re.UNICODE)
_WHITESPACE = re.compile(r"\s+")
_WORD = re.compile(r"\w+", re.UNICODE)


def fold(text: str) -> str:
    """Forma e krahasueshme e një vargu."""
    lowered = unicodedata.normalize("NFKD", text.casefold())
    stripped = "".join(ch for ch in lowered if not unicodedata.combining(ch))
    return _WHITESPACE.sub(" ", _PUNCTUATION.sub(" ", stripped)).strip()


def fold_token(token: str) -> str:
    """Si `fold`, por për një fjalë të vetme dhe pa ndarës."""
    return fold(token).replace(" ", "")


def words(text: str) -> list[tuple[str, int, int]]:
    """Fjalët e tekstit me pozicionet e tyre në vargun origjinal.

    Pozicionet ruhen sepse pohimet e Degës B mbajnë `char_start` dhe
    `char_end` në tekstin e papërpunuar; një token pa adresë nuk kthehet
    dot në pohim të gjurmueshëm.
    """
    return [(match.group(), match.start(), match.end()) for match in _WORD.finditer(text)]
