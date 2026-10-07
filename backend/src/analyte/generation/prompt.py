"""
Kërkesa për modelin gjuhësor, e ndërtuar vetëm nga `GroundingContext`.

    def build_prompt(context, feedback) -> Prompt

Nënshkrimi është garancia e punimit: ky modul nuk merr dokumentin, tekstin e
nxjerrë prej tij, as ndonjë burim tjetër. Çfarë di modeli është ajo që ka
vendosur shtresa e bazimit, dhe asgjë më shumë. Një test kontrollon që
nënshkrimi të mos zgjerohet.

**Çfarë e kufizon modelin.** Kërkesa i thotë modelit të mos shtojë asnjë
informacion mjekësor, asnjë numër tjetër, asnjë analit tjetër; të kopjojë
fjalë për fjalë tekstet e detyrueshme (SP4–SP7) dhe citimet e mjekut; dhe të
përshkruajë pozicionin e vlerës me shprehjet që verifikuesi i njeh. **Kjo e
fundit është vendim dizajni që duhet deklaruar:** rregulli R3 e njeh drejtimin
vetëm në ato forma (`assertions.INCREASE_MARKERS` etj.), dhe një model që
shkruan "i lartë" do ta kalonte R3 pa u parë. Kërkesa e drejton te format që
verifikuesi mat, jo te një formulim që do ta bënte verifikimin të verbër.

**Shkeljet e përpjekjes së mëparshme** futen në kërkesë si fjali të daljes dhe
arsye të rregullit (`Violation.sentence`, `Violation.evidence`); asgjë prej tyre
nuk vjen nga dokumenti.

`PROMPT_VERSION` ruhet me çdo përpjekje (te emri i gjeneruesit): një rezultat
nuk atribuohet dot te një kërkesë që ndryshon pa dije.
"""

from __future__ import annotations

from dataclasses import dataclass

from analyte.domain.enums import AnalyteStatus
from analyte.domain.models import AnalyteFinding, GroundingContext, Violation
from analyte.domain.policy import (
    ATTRIBUTION_PREFIX_SQ,
    CRITICAL_BANNER_SQ,
    DISCLAIMER_SQ,
    RULE_BY_VIOLATION,
    UNEXPLAINED_TERM_NOTICE_SQ,
    UNINTERPRETABLE_NOTICE_SQ,
)

from .templates import POSITION, _number, _pattern_sentences, _quoted_assertions, advice_by_finding

PROMPT_VERSION = "p1"


@dataclass(frozen=True, slots=True)
class Prompt:
    """Kërkesa e plotë: udhëzimet fikse dhe konteksti i këtij dokumenti."""

    system: str
    user: str
    version: str = PROMPT_VERSION


SYSTEM = f"""Ti shkruan një shpjegim në gjuhën shqipe për një pacient, nga rezultatet e tij laboratorike dhe nga pohimet e mjekut. Ti NUK je mjek dhe nuk ke asnjë njohuri mjekësore që nuk jepet më poshtë. Detyra jote është vetëm formulimi: e vërteta është ajo që të jepet te "KONTEKSTI", dhe asgjë tjetër.

Rregulla që nuk shkelen kurrë:

1. Përdor vetëm numrat që shfaqen te konteksti (vlera e matur dhe dy kufijtë e intervalit). Shkruaji me pikë dhjetore, ashtu si janë dhënë. Mos shkruaj asnjë numër tjetër: as numërim, as përqindje, as data, as "dy" ose "tre" me shifra.
2. Përmend vetëm analitet e listuara. Përdore emrin ashtu siç jepet. Mos përmend asnjë analit, sëmundje, gjendje apo term tjetër.
3. Pozicionin e vlerës ndaj intervalit përshkruaje vetëm me këto shprehje: "brenda intervalit referent", "nën intervalin referent", "mbi intervalin referent", "dukshëm nën intervalin referent", "dukshëm mbi intervalin referent". Mos përdor "i lartë", "e ulët", "normale" apo sinonime.
4. Mos jep diagnozë, mos këshillo trajtim apo ilaç, mos bëj parashikim për të ardhmen. Mos thuaj çfarë do të thotë një vlerë për shëndetin e pacientit.
5. Pohimet e mjekut kopjoji FJALË PËR FJALË, pa i ndryshuar, shkurtuar apo riformuluar, në formën e dhënë (që nis me "{ATTRIBUTION_PREFIX_SQ}"). Mohimi, rezerva ("mundësisht", "nuk përjashtohet") dhe rekomandimi duhet të mbeten saktësisht siç janë.
6. Tekstet e shënuara "KOPJOJE" i shkruan fjalë për fjalë.
7. Shpjegimin e një termi mjekësor merre vetëm nga shpjegimi i dhënë; mund ta thuash me fjalë më të thjeshta, pa shtuar asgjë. Termat e shënuar "PA SHPJEGIM" mos i shpjego.
8. Shkruaj në gjuhë të thjeshtë, me fjali të shkurtra, pa terma teknikë të panevojshëm. Mos përdor lista me shenja, tituj apo format Markdown: vetëm paragrafë të thjeshtë.

Struktura: njoftimi për vlera kritike (nëse jepet) del i pari; pastaj çdo vlerë laboratorike; pastaj kombinimet (nëse ka); pastaj termat; pastaj pohimet e mjekut; në fund shënimi përmbyllës fjalë për fjalë. Kthe vetëm tekstin e shpjegimit."""


def build_prompt(context: GroundingContext, feedback: tuple[Violation, ...] = ()) -> Prompt:
    """Kërkesa për një kontekst, dhe për shkeljet e përpjekjes së mëparshme."""
    return Prompt(system=SYSTEM, user=_user_message(context, feedback))


def _user_message(context: GroundingContext, feedback: tuple[Violation, ...]) -> str:
    blocks: list[str] = ["KONTEKSTI"]

    if context.critical_findings():
        blocks.append(
            "Njoftim për vlera kritike (KOPJOJE si fjalinë e parë të shpjegimit):\n"
            f"{CRITICAL_BANNER_SQ}"
        )

    blocks.append("Vlerat laboratorike:\n" + _findings(context))

    advice = _advice(context)
    if advice:
        # ADR 0023: blloku shfaqet vetëm kur konteksti ka këshilla; kërkesat pa këshilla mbeten `p1` bajt për bajt.
        blocks.append(
            "Këshilla me burim (KOPJOJE çdo fjali fjalë për fjalë, menjëherë pas vlerës përkatëse; "
            "mos shto asnjë këshillë tjetër):\n" + advice
        )

    patterns = _pattern_sentences(context)
    if patterns:
        blocks.append(
            "Kombinime rezultatesh (KOPJOJE çdo fjali fjalë për fjalë):\n" + "\n".join(patterns)
        )

    terms = _terms(context)
    if terms:
        blocks.append("Terma nga raporti i mjekut:\n" + terms)

    quotes = _quoted_assertions(context)
    if quotes:
        blocks.append(
            "Pohimet e mjekut (KOPJOJE çdo fjali fjalë për fjalë, njëra pas tjetrës):\n"
            + "\n".join(quotes)
        )

    blocks.append(f"Shënimi përmbyllës (KOPJOJE fjalë për fjalë në fund):\n{DISCLAIMER_SQ}")

    if feedback:
        blocks.append(_feedback(feedback))

    blocks.append("Shkruaje shpjegimin.")
    return "\n\n".join(blocks)


def _findings(context: GroundingContext) -> str:
    return "\n".join(f"- {_finding_line(finding)}" for finding in context.findings)


def _finding_line(finding: AnalyteFinding) -> str:
    name = finding.analyte_name_canonical
    value = f"{_number(finding.value_canonical)} {finding.unit_canonical}"
    if finding.status is AnalyteStatus.UNINTERPRETABLE:
        return (
            f"{name}: vlera e matur {value}; PA INTERVAL. "
            f"Pas vlerës KOPJOJE: {UNINTERPRETABLE_NOTICE_SQ}"
        )
    return (
        f"{name}: vlera e matur {value}; pozicioni: {POSITION[finding.status]}"
        f"{_interval(finding)}"
    )


def _interval(finding: AnalyteFinding) -> str:
    low, high = finding.ref_low, finding.ref_high
    if low is not None and high is not None:
        return f"; intervali referent {_number(low)} - {_number(high)}"
    if high is not None:
        return f"; intervali referent deri {_number(high)}"
    if low is not None:
        return f"; intervali referent nga {_number(low)}"
    return ""


def _advice(context: GroundingContext) -> str:
    names = {finding.id: finding.analyte_name_canonical for finding in context.findings}
    advice = advice_by_finding(context)
    return "\n".join(f"- pas {names[finding_id]}: {sentence}" for finding_id, sentence in advice.items())


def _terms(context: GroundingContext) -> str:
    lines = [
        f"- {entry.term}: shpjegimi i lejuar: {entry.explanation_sq}" for entry in context.glossary
    ]
    lines += [
        f"- {term}: PA SHPJEGIM. Thuaj vetëm: Raporti përmend termin “{term}”. "
        f"{UNEXPLAINED_TERM_NOTICE_SQ}"
        for term in context.unexplained_terms
    ]
    return "\n".join(lines)


def _feedback(violations: tuple[Violation, ...]) -> str:
    lines = [
        "Shpjegimi i mëparshëm u refuzua nga verifikimi. Rishkruaje të gjithë shpjegimin pa "
        "këto gabime:"
    ]
    for violation in violations:
        rule = RULE_BY_VIOLATION.get(violation.type)
        reason = rule.description_sq if rule else violation.type.value
        lines.append(f"- Fjalia: «{violation.sentence}» — {reason} ({violation.evidence})")
    return "\n".join(lines)
