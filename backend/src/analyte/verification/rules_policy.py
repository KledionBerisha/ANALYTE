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

from . import ruleset
from .base import is_attributed, sentences, violation

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

DIAGNOSTIC_CUES_R14: tuple[str, ...] = (
    "ju keni ",
    "ju vuani",
    "vuani nga",
    "jeni e semure",
    "jeni i semure",
    "diagnoza e",
    "diagnoza juaj",
    "diagnostikohet me",
    "konfirmon diagnozen",
    "konfirmon qe keni",
    "konfirmon se keni",
    "tregon qarte se keni",
    "shenje e qarte e",
    "tregues i qarte i",
    "provon se keni",
    "kjo eshte semundje",
    "keni nje semundje",
    "keni nje gjendje",
    "pacienti ka semundjen",
)

TREATMENT_CUES_R14: tuple[str, ...] = (
    "duhet te merrni",
    "duhet te filloni",
    "duhet te ndaloni",
    "filloni ",
    "ndaloni ",
    "reduktoni",
    "ulni marrjen",
    "rritni marrjen",
    "ndryshoni dieten",
    "dieten",
    "mos hani",
    "mos pini",
    "ilace",
    "ilaceve",
    "suplement",
    "terapi",
    "trajtim",
    "trajtoheni",
    "antibiotik",
    "insulin",
    "vitamina shtese",
    "dozen",
)

PROGNOSTIC_CUES_R14: tuple[str, ...] = (
    "do te zhvilloni",
    "do te keni",
    "do te rritet",
    "do te ulet",
    "do te kthehet ne normale",
    "ka rrezik",
    "keni rrezik",
    "rrezikoni",
    "rrezik per",
    "ne te ardhmen",
    "mund te coje ne",
    "mund te shkaktoje",
    "komplikacione",
    "perkeqesim",
    "permiresim",
    "prognoz",
    "jetegjatesi",
    "nese nuk trajtohet",
    "ka gjasa te zhvilloni",
    "gjasat per",
)
"""`r1.4`: shenja më të gjera, shkruara nga përkufizimi i SP1–SP3 dhe nga shqipja klinike e zakonshme, jo nga rreshtat e grupit B.
Fjalitë e atribuuara (citimet e mjekut) nuk gjykohen: fjala është e mjekut dhe kopjohet fjalë për fjalë. Rregulli është ende leksikor: një
formulim që nuk është në listë kalon, dhe një fjalë e listës te një fjali e pafajshme jep alarm."""

CUES_R14: tuple[tuple[SafetyPolicy, tuple[str, ...]], ...] = (
    (SafetyPolicy.NO_DIAGNOSIS, DIAGNOSTIC_CUES + DIAGNOSTIC_CUES_R14),
    (SafetyPolicy.NO_TREATMENT, TREATMENT_CUES + TREATMENT_CUES_R14),
    (SafetyPolicy.NO_PROGNOSIS, PROGNOSTIC_CUES + PROGNOSTIC_CUES_R14),
)


def check_prohibited_claims(context: GroundingContext, text: str) -> Iterator[Violation]:
    """SP1-SP3 — asnjë pohim diagnostik, trajtimi apo prognoze."""
    del context  # ndalimi nuk varet nga konteksti: ai vlen gjithmonë

    modern = ruleset.modern()
    for sentence in sentences(text):
        if modern and is_attributed(sentence.text):
            continue
        folded = f" {fold(sentence.text)} " if modern else fold(sentence.text)
        for policy, cues in CUES_R14 if modern else CUES:
            hit = next((cue for cue in cues if cue in folded), None)
            if hit is not None:
                yield violation(
                    ViolationType.PROHIBITED_CLAIM,
                    sentence.text,
                    f"{policy.value}: shprehja \u201c{hit}\u201d — {policy.description_sq}",
                )
                break
