"""
Politika e sigurisë dhe katalogu i rregullave — konstante normative.

Ky modul nuk përmban logjikë. Ai përmban vendimet normative të punimit
të shprehura si të dhëna, në një vend të vetëm, që:

  - shtresa e gjenerimit t'i shkruajë në prompt,
  - shtresa e verifikimit t'i zbatojë,
  - gjeneruesi i korpusit të korruptuar të dijë çfarë të prishë,
  - dhe vlerësimi t'i indeksojë tabelat me të njëjtat identifikues.

Nëse një rregull ndryshon, ai ndryshon këtu dhe RULES_VERSION rritet.
Çdo VerificationResult e ruan atë version, prandaj rezultatet e vjetra
mbeten të lexueshme edhe pasi katalogu ndryshon (NFR2, NFR3).

Ashtu si `models.py`, ky modul nuk importon asgjë jashtë `domain/`.
"""

from __future__ import annotations

from enum import Enum
from typing import NamedTuple

from .enums import ViolationType

# --------------------------------------------------------------------
# Versionimi
# --------------------------------------------------------------------

RULES_VERSION = "r1.0"
"""Versioni i katalogut R1-R9. Ruhet në çdo VerificationResult."""

POLICY_VERSION = "sp1.0"
"""Versioni i politikës SP1-SP8."""


# --------------------------------------------------------------------
# Politika e sigurisë (§1.4 e specifikimit)
# --------------------------------------------------------------------


class SafetyPolicy(str, Enum):
    """Tetë politikat normative.

    Këto nuk janë udhëzime por kërkesa: secila ka një test përkatës.
    Vlera e enum-it është identifikuesi që shfaqet në log-un e auditimit
    dhe në tabelat e vlerësimit.
    """

    NO_DIAGNOSIS = "SP1"
    NO_TREATMENT = "SP2"
    NO_PROGNOSIS = "SP3"
    CRITICAL_ESCALATION = "SP4"
    NO_INTERVAL_NO_INTERPRETATION = "SP5"
    NO_TABLE_NO_EXPLANATION = "SP6"
    DISCLAIMER_REQUIRED = "SP7"
    TEMPLATE_ON_REPEATED_FAILURE = "SP8"

    @property
    def description_sq(self) -> str:
        return SAFETY_POLICY_TEXT[self]

    @property
    def is_prohibition(self) -> bool:
        """A e ndalon kjo politikë përmbajtje të caktuar në dalje?

        Politikat ndaluese zbatohen nga rregulli i vetëm PROHIBITED_CLAIM;
        të tjerat zbatohen strukturalisht — nga modelet e domenit, nga
        makina e gjendjeve ose nga shtresa e prezantimit.
        """
        return self in PROHIBITIVE_POLICIES


SAFETY_POLICY_TEXT: dict[SafetyPolicy, str] = {
    SafetyPolicy.NO_DIAGNOSIS: "Asnjë pohim diagnostik nuk lëshohet kurrë.",
    SafetyPolicy.NO_TREATMENT: "Asnjë këshillë trajtimi apo medikamenti nuk lëshohet kurrë.",
    SafetyPolicy.NO_PROGNOSIS: "Asnjë pohim prognostik nuk lëshohet kurrë.",
    SafetyPolicy.CRITICAL_ESCALATION: (
        "Gjetjet kritike shkaktojnë njoftim përpara çdo teksti shpjegues."
    ),
    SafetyPolicy.NO_INTERVAL_NO_INTERPRETATION: (
        "Vlera pa interval referent të zgjidhshëm shënohet e painterpretueshme, "
        "nuk hamendësohet."
    ),
    SafetyPolicy.NO_TABLE_NO_EXPLANATION: (
        "Termi që mungon në tabelën terminologjike shënohet i pashpjeguar, "
        "nuk përkufizohet."
    ),
    SafetyPolicy.DISCLAIMER_REQUIRED: (
        "Çdo dalje shoqërohet me shënimin për konsultim me profesionistin shëndetësor."
    ),
    SafetyPolicy.TEMPLATE_ON_REPEATED_FAILURE: (
        "Pas dështimit të përsëritur të verifikimit shfaqet shabllon determinist."
    ),
}

PROHIBITIVE_POLICIES: frozenset[SafetyPolicy] = frozenset(
    {
        SafetyPolicy.NO_DIAGNOSIS,
        SafetyPolicy.NO_TREATMENT,
        SafetyPolicy.NO_PROGNOSIS,
    }
)
"""SP1-SP3: të vetmet politika që zbatohen duke shqyrtuar tekstin e gjeneruar."""


# --------------------------------------------------------------------
# Katalogu i rregullave (Kapitulli 5)
# --------------------------------------------------------------------


class Rule(NamedTuple):
    """Një rregull verifikimi i katalogut.

    `requires_context` shënon rregullat që nuk mund të vendosen nga një
    fjali e vetme: ato kërkojnë shikim mbi tërë daljen (p.sh. R4 thotë se
    diçka mungon, çka nuk shihet duke lexuar një fjali). Kjo ndarje
    përcakton edhe cilat shkelje mund të mësohen nga një klasifikues
    fjalie dhe cilat jo — dallim që hyn drejtpërdrejt në diskutimin e PK6.
    """

    id: str
    violation: ViolationType
    branch: str
    description_sq: str
    requires_context: bool


RULE_CATALOG: tuple[Rule, ...] = (
    # --- Dega A: verifikim i saktë, determinist ---
    Rule(
        "R1",
        ViolationType.UNGROUNDED_NUMBER,
        "A",
        "Çdo numër në tekst duhet të gjendet ndër numrat e mbështetur të kontekstit.",
        requires_context=False,
    ),
    Rule(
        "R2",
        ViolationType.UNGROUNDED_ANALYTE,
        "A",
        "Çdo analit i përmendur duhet të jetë ndër analitet e matura.",
        requires_context=False,
    ),
    Rule(
        "R3",
        ViolationType.DIRECTION_MISMATCH,
        "A",
        "Drejtimi i pohuar duhet të përputhet me statusin e klasifikuar.",
        requires_context=False,
    ),
    Rule(
        "R4",
        ViolationType.MISSING_CRITICAL,
        "A",
        "Çdo gjetje kritike duhet të shfaqet në dalje.",
        requires_context=True,
    ),
    # --- Dega B: verifikim semantik ---
    Rule(
        "R5",
        ViolationType.POLARITY_FLIP,
        "B",
        "Polariteti i pohimit të mjekut nuk guxon të përmbyset.",
        requires_context=False,
    ),
    Rule(
        "R6",
        ViolationType.HEDGE_REMOVED,
        "B",
        "Pasiguria e shprehur nga mjeku nuk guxon të hiqet.",
        requires_context=False,
    ),
    Rule(
        "R7",
        ViolationType.FABRICATED_FINDING,
        "B",
        "Asnjë gjetje që mungon në kontekst nuk guxon të shtohet.",
        requires_context=False,
    ),
    Rule(
        "R8",
        ViolationType.OMITTED_RECOMMENDATION,
        "B",
        "Çdo rekomandim i mjekut duhet të ruhet në dalje.",
        requires_context=True,
    ),
    Rule(
        "R9",
        ViolationType.UNGROUNDED_TERM_EXPLANATION,
        "B",
        "Asnjë term jashtë tabelës terminologjike nuk guxon të shpjegohet.",
        requires_context=False,
    ),
    # --- Politika e sigurisë si rregull i vetëm ---
    Rule(
        "SP1-3",
        ViolationType.PROHIBITED_CLAIM,
        "B",
        "Asnjë pohim diagnostik, trajtimi apo prognoze.",
        requires_context=False,
    ),
)

RULE_BY_VIOLATION: dict[ViolationType, Rule] = {r.violation: r for r in RULE_CATALOG}
"""Kërkim i shpejtë: lloji i shkeljes → rregulli që e zbulon."""

RULE_BY_ID: dict[str, Rule] = {r.id: r for r in RULE_CATALOG}


def sentence_local_violations() -> frozenset[ViolationType]:
    """Shkeljet e vendosshme nga një fjali e vetme.

    Vetëm këto mund të përbëjnë detyrë klasifikimi në nivel fjalie; pjesa
    tjetër kërkon shikim mbi tërë daljen. Korpusi i korruptuar i Fazës 7
    ndërtohet mbi këtë bashkësi.
    """
    return frozenset(r.violation for r in RULE_CATALOG if not r.requires_context)


# --------------------------------------------------------------------
# Kufijtë e ciklit gjenerim → verifikim (Figura 6)
# --------------------------------------------------------------------

MAX_GENERATION_ATTEMPTS = 2
"""Përpjekja e dytë e merr listën e shkeljeve në prompt. Pas saj: shabllon (SP8)."""


# --------------------------------------------------------------------
# Tekste të detyrueshme për përdoruesin
# --------------------------------------------------------------------

DISCLAIMER_SQ = (
    "Ky shpjegim është automatik dhe nuk zëvendëson vlerësimin e profesionistit "
    "shëndetësor. Për çdo vendim mjekësor konsultohuni me mjekun tuaj."
)
"""SP7. Shfaqet në çdo dalje, përfshirë shabllonin e rezervës dhe bisedën."""

CRITICAL_BANNER_SQ = (
    "Kjo analizë përmban vlera dukshëm jashtë intervalit referent. "
    "Kontaktoni menjëherë mjekun tuaj."
)
"""SP4. Shfaqet përpara tekstit shpjegues, jo brenda tij."""

UNINTERPRETABLE_NOTICE_SQ = (
    "Për këtë vlerë nuk u gjet interval referent, prandaj nuk interpretohet."
)
"""SP5. Zëvendëson interpretimin, nuk e shoqëron atë."""

ATTRIBUTION_PREFIX_SQ = "Mjeku ka shënuar:"
"""Me çfarë e shënon dalja një fjali si citim të mjekut.

Dallimi ndërmjet asaj që thotë sistemi dhe asaj që citon ai nuk është
stilistik: pohimet e veta verifikohen kundrejt matjeve, citimet kundrejt
burimit. Pa këtë shenjë, një citim besnik i një mjeku që shprehet me
rezervë do të dukej si pohim i sistemit që ka humbur rezervën."""

UNEXPLAINED_TERM_NOTICE_SQ = (
    "Ky term nuk gjendet në fjalorin e sistemit, prandaj nuk shpjegohet."
)
"""SP6."""
