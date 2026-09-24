"""
Politika e sigurisë si rregull: SP1-SP3.

Tri ndalime — diagnoza, trajtimi, prognoza — zbatohen me një rregull të
vetëm, sepse të tria kanë të njëjtën pasojë: teksti ndalohet, pavarësisht
se cili prej tyre u shkel.

Shenjat janë leksikore dhe lista mbahet e shkurtër e lexueshme. Kjo e bën
rregullin të anashkalueshëm nga një formulim i zgjuar, dhe kjo pranohet:
ai është shtresa e fundit dhe jo e vetmja. Shpjegimi vjen nga një model i
udhëzuar shprehimisht të mos i lëshojë këto pohime, dhe konteksti që i
jepet nuk përmban asgjë diagnostike për të riprodhuar.

Alternativa — një klasifikues i trajnuar për qëllimin — do të kërkonte
korpus të anotuar që nuk ekziston për shqipen, dhe do ta zëvendësonte një
dobësi të dukshme me një të padukshme.
"""

from __future__ import annotations

from collections.abc import Iterator

from analyte.domain.enums import ViolationType
from analyte.domain.models import GroundingContext, Violation
from analyte.domain.policy import SafetyPolicy
from analyte.textnorm import fold

from .base import sentences, violation

DIAGNOSTIC_CUES: tuple[str, ...] = (
    "ju keni semundjen",
    "ju vuani nga",
    "diagnoza eshte",
    "diagnostikoheni",
    "kjo do te thote se keni",
    "jeni i semure me",
)

TREATMENT_CUES: tuple[str, ...] = (
    "merrni",
    "filloni terapine",
    "duhet te pini",
    "doza",
    "mjekimi",
    "ilaci",
    "tableta",
    "recete",
    "nderprisni mjekimin",
)

PROGNOSTIC_CUES: tuple[str, ...] = (
    "do te permiresohet",
    "do te perkeqesohet",
    "rreziku juaj eshte",
    "pritet te zhvilloni",
    "shanset per",
    "do te sherohet",
)

CUES: tuple[tuple[SafetyPolicy, tuple[str, ...]], ...] = (
    (SafetyPolicy.NO_DIAGNOSIS, DIAGNOSTIC_CUES),
    (SafetyPolicy.NO_TREATMENT, TREATMENT_CUES),
    (SafetyPolicy.NO_PROGNOSIS, PROGNOSTIC_CUES),
)


def check_prohibited_claims(context: GroundingContext, text: str) -> Iterator[Violation]:
    """SP1-SP3 — asnjë pohim diagnostik, trajtimi apo prognoze."""
    del context  # ndalimi nuk varet nga konteksti: ai vlen gjithmonë

    for sentence in sentences(text):
        folded = fold(sentence.text)
        for policy, cues in CUES:
            hit = next((cue for cue in cues if cue in folded), None)
            if hit is not None:
                yield violation(
                    ViolationType.PROHIBITED_CLAIM,
                    sentence.text,
                    f"{policy.value}: shprehja \u201c{hit}\u201d — {policy.description_sq}",
                )
                break
