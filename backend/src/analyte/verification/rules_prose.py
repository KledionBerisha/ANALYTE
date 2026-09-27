"""
Dega B e verifikimit: rregullat R5-R9.

Këto rregulla krahasojnë kuptimin e daljes me kuptimin e burimit, dhe
prandaj janë më të brishta se ato të Degës A. Ato mbështeten te po ata
detektorë leksikorë që nxjerrin pohimet nga narrativa, çka do të thotë se
ato e shohin vetëm atë që ata detektorë shohin.

Kjo kufizë duhet mbajtur parasysh kur lexohen rezultatet e PK3: nëse një
mohim përmbyset dhe detektori nuk e kap, PK3 do të tregojë ruajtje të
përsosur. Prandaj PK3 nuk qëndron vetëm — ai lexohet bashkë me PK6, që mat
pikërisht aftësinë zbuluese.

Lidhja ndërmjet një pohimi të burimit dhe një fjalie të daljes bëhet me
analitin ose me termin e përmendur. Ky është krahasim i thjeshtë dhe i
dukshëm; një përafrim semantik do të fshihte se ku gabon rregulli.
"""

from __future__ import annotations

from collections.abc import Iterator

from analyte.domain.enums import (
    AssertionKind,
    Certainty,
    Polarity,
    ViolationType,
)
from analyte.domain.models import GroundingContext, ReportAssertion, Violation
from analyte.domain.policy import (
    CRITICAL_BANNER_SQ,
    DISCLAIMER_SQ,
    UNEXPLAINED_TERM_NOTICE_SQ,
    UNINTERPRETABLE_NOTICE_SQ,
)
from analyte.grounding.branch_b import terminology
from analyte.grounding.branch_b.assertions import find_direction
from analyte.grounding.branch_b.hedging import certainty_of
from analyte.grounding.branch_b.negation import polarity_of
from analyte.textnorm import fold

from .base import analytes_in, is_attributed, sentences, violation


def _sentence_for(
    assertion: ReportAssertion, text: str, context: GroundingContext
) -> str | None:
    """Fjalia e daljes që i përgjigjet një pohimi të burimit.

    Shqyrtohen vetëm fjalitë e atribuuara. Një përmbysje polariteti
    kërkon që pretendimi të jetë ripohuar; nëse dalja nuk e mbart fare
    atë, kemi heqje dhe jo përmbysje, dhe e para nuk i takon këtij
    rregulli.
    """
    quoted = [s.text for s in sentences(text) if is_attributed(s.text)]

    if assertion.analyte_code is not None:
        for sentence in quoted:
            if assertion.analyte_code in analytes_in(sentence, context):
                return sentence
        return None

    terms = {match.term.term for match in terminology.detect_terms(assertion.text_span)}
    if not terms:
        return None
    for sentence in quoted:
        found = {match.term.term for match in terminology.detect_terms(sentence)}
        if terms & found:
            return sentence
    return None


def check_polarity(context: GroundingContext, text: str) -> Iterator[Violation]:
    """R5 — polariteti i pohimit të mjekut nuk guxon të përmbyset.

    Shkelja kërkon që dalja ta ripohojë të njëjtin pretendim me polaritet
    të kundërt. Nëse dalja flet për të njëjtin analit por për diçka tjetër
    — p.sh. raporton pozicionin e matur aty ku mjeku mohoi një drejtim
    tjetër — kjo nuk është përmbysje por pohim i ri, dhe vlerësohet nga
    rregullat e Degës A. Pa këtë kusht, çdo fjali e shabllonit për një
    analit të përmendur me mohim do të dilte shkelje.
    """
    for assertion in context.assertions:
        if assertion.kind is AssertionKind.RECOMMENDATION:
            continue
        sentence = _sentence_for(assertion, text, context)
        if sentence is None:
            continue
        if find_direction(sentence) is not assertion.direction:
            continue
        if polarity_of(sentence) is not assertion.polarity:
            yield violation(
                ViolationType.POLARITY_FLIP,
                sentence,
                f"burimi thotë {assertion.polarity.value} për "
                f"“{assertion.text_span}”",
            )


def check_hedging(context: GroundingContext, text: str) -> Iterator[Violation]:
    """R6 — pasiguria e shprehur nga mjeku nuk guxon të hiqet.

    Kontrollohet vetëm drejtimi i humbjes. Shtimi i pasigurisë aty ku
    mjeku ishte i sigurt e dobëson tekstin por nuk e bën të pavërtetë;
    heqja e saj e kthen hamendjen në fakt.
    """
    for assertion in context.assertions:
        if assertion.certainty is not Certainty.HEDGED:
            continue
        sentence = _sentence_for(assertion, text, context)
        if sentence is None:
            continue
        if certainty_of(sentence) is not Certainty.HEDGED:
            yield violation(
                ViolationType.HEDGE_REMOVED,
                sentence,
                f"burimi e shpreh me rezervë: “{assertion.text_span}”",
            )


def check_fabrication(context: GroundingContext, text: str) -> Iterator[Violation]:
    """R7 — asnjë gjetje që mungon në kontekst nuk guxon të shtohet.

    Kontrolli bëhet mbi termat mjekësorë: një gjendje e përmendur në dalje
    duhet të vijë ose nga një pohim i mjekut, ose nga fjalori i termave që
    dalja ka të drejtë të shpjegojë. Termi që nuk vjen nga asnjëra është
    shtesë.

    Emrat e analiteve të matura hyjnë gjithashtu ndër burimet e lejuara:
    "Glukozë në serum" përmban termin "serum", dhe pa këtë përjashtim çdo
    përmendje e një analiti do të raportohej si gjetje e shpikur.
    """
    allowed = {entry.term for entry in context.glossary}
    # Shpjegimi i një termi përdor fjalë të tjera të tabelës — "enzimë"
    # brenda përkufizimit të transaminazave. Ato nuk janë gjetje të reja.
    for entry in context.glossary:
        allowed |= {m.term.term for m in terminology.detect_terms(entry.explanation_sq)}
    for assertion in context.assertions:
        allowed |= {m.term.term for m in terminology.detect_terms(assertion.text_span)}
    for finding in context.findings:
        allowed |= {m.term.term for m in terminology.detect_terms(finding.analyte_name_canonical)}
        allowed |= {m.term.term for m in terminology.detect_terms(finding.analyte_name_raw)}
    # Termi i pashpjeguar vjen nga raporti, dhe SP6 e detyron daljen ta
    # përmendë. Ai nuk shpjegohet — këtë e ruan R9 — por as nuk është shtesë.
    for term in context.unexplained_terms:
        allowed |= {m.term.term for m in terminology.detect_terms(term)}
    allowed |= _system_vocabulary()

    for sentence in sentences(text):
        for match in terminology.detect_terms(sentence.text):
            if match.term.term not in allowed:
                yield violation(
                    ViolationType.FABRICATED_FINDING,
                    sentence.text,
                    f"termi “{match.term.term}” nuk shfaqet në raportin burimor",
                )


def _system_vocabulary() -> set[str]:
    """Termat që përdorin tekstet e detyrueshme të politikës.

    "Interval referent" nuk është gjetje: është fjalori me të cilin sistemi
    flet për çdo matje, dhe njoftimi i SP4 e përmban vetë. Pa këtë
    përjashtim, R7 do ta raportonte si të shpikur tekstin që politika e
    kërkon — pikërisht në dokumentet ku termi nuk rastis të jetë edhe në
    fjalor.

    Bashkësia nxirret nga tekstet e politikës dhe nuk shkruhet me dorë, që
    një ndryshim i njoftimit të mos kërkojë ndryshim të dytë këtu.
    """
    notices = (
        CRITICAL_BANNER_SQ,
        DISCLAIMER_SQ,
        UNEXPLAINED_TERM_NOTICE_SQ,
        UNINTERPRETABLE_NOTICE_SQ,
    )
    return {m.term.term for notice in notices for m in terminology.detect_terms(notice)}


def check_recommendations(context: GroundingContext, text: str) -> Iterator[Violation]:
    """R8 — çdo rekomandim i mjekut duhet të ruhet në dalje.

    Si R4, ky rregull shqyrton tërë daljen: një rekomandim i hequr nuk
    shihet duke lexuar fjalitë që mbetën.

    Krahasimi bëhet mbi përmbajtjen kuptimplote të rekomandimit dhe jo mbi
    vargun e plotë, sepse dalja lejohet ta paraqesë atë me hyrje të vetën.
    """
    for assertion in context.assertions:
        if assertion.kind is not AssertionKind.RECOMMENDATION:
            continue
        if fold(assertion.text_span) not in fold(text):
            yield violation(
                ViolationType.OMITTED_RECOMMENDATION,
                "",
                f"rekomandimi “{assertion.text_span}” mungon në dalje",
            )


def check_term_explanations(context: GroundingContext, text: str) -> Iterator[Violation]:
    """R9 — asnjë term jashtë tabelës nuk guxon të shpjegohet (SP6).

    Termi i pashpjeguar lejohet të përmendet — dalja duhet ta thotë se ai
    u përmend dhe nuk shpjegohet. Shkelja ndodh kur ai shoqërohet me
    shpjegim.
    """
    explanatory = ("do te thote", "quhet", "eshte nje gjendje", "nenkupton", "tregon se")

    for term in context.unexplained_terms:
        folded_term = fold(term)
        for sentence in sentences(text):
            folded = fold(sentence.text)
            if folded_term not in folded:
                continue
            if any(cue in folded for cue in explanatory):
                yield violation(
                    ViolationType.UNGROUNDED_TERM_EXPLANATION,
                    sentence.text,
                    f"termi “{term}” nuk gjendet në tabelën terminologjike",
                )
