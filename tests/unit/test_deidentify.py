"""
Porta e çidentifikimit (ADR 0019): çfarë teksti të dokumentit nuk guxon t'i dërgohet ofruesit të modelit.

Fjalitë janë shkruar me dorë dhe nuk janë shabllonet e gjeneruesit sintetik: një portë e provuar vetëm mbi fjalitë që e
ka formësuar fjalori i saj do të kalonte çdo gjë. Emrat janë shembuj të zakonshëm shqiptarë, të shpikur këtu për testin;
asnjëri nuk i përket një personi që ky punim njeh.

Ç'provohet:

  - **Citimet e pastra kalojnë**, përfshirë një term të fjalorit me shkronjë të madhe në mes të fjalisë (e lakuar) dhe
    një muaj pa numër pranë.
  - **Çdo lloj i të dhënave identifikuese shënohet**: emër, titull, datë (me numra ose me emër muaji), telefon, email,
    adresë interneti, numër i gjatë, identifikues, moshë dhe datëlindje, shenja adrese.
  - **Dështimi është i mbyllur**: një emër nuk kalon për shkak se rastis me një fjalë të zakonshme, dhe ai është i
    shënuar edhe kur është fjala e parë e fjalisë.
  - **Gjetjet nuk mbajnë vargun e shënuar**, kështu që nuk e rrjedhin atë te auditimi.
  - **Garancia strukturore**: çdo varg i tekstit të lirë që hyn te kërkesa shkon nga porta; një fushë që porta nuk e skanon
    nuk hyn te kërkesa.
"""

from __future__ import annotations

import pytest

from analyte.domain.enums import AssertionKind, Certainty, Direction, Polarity
from analyte.domain.models import GlossaryEntry, ReportAssertion
from analyte.generation import deidentify
from analyte.generation.deidentify import Kind, inspect, is_known_word, scan_text
from analyte.generation.prompt import build_prompt
from tests.fixtures.grounding_context import build_reference_context

# --------------------------------------------------------------------
# Citimet e pastra
# --------------------------------------------------------------------

CLEAN = [
    "Funksioni i veshkave duket i ruajtur, por vlerat kërkojnë vëmendje",
    "Mjeku sugjeron përsëritjen e analizës pas dy javësh",
    "Nuk vërehen shenja të inflamacionit akut",
    "Hemoglobina qëndron pak nën kufirin e poshtëm",
    "Rekomandohet konsultë me specialistin",
    "Vlerat tregojnë Anemi të lehtë",  # term i fjalorit, shkronjë e madhe në mes
    "Rritja e transaminazave është e mundshme",  # lakim ("rritje" -> "rritja")
    "Kontrolli i radhës të bëhet në shtator",  # emri i muajit pa numër pranë nuk identifikon
    "Glukoza 7.8 mmol/L është mbi intervalin referent",  # numër dhjetor dhe njësi me shkronjë të madhe
    "Nuk përjashtohet steatozë hepatike",
]


@pytest.mark.parametrize("quote", CLEAN)
def test_a_clean_clinical_quote_passes(quote):
    assert scan_text(quote) == ()


def test_a_glossary_term_that_looks_like_a_name_is_not_flagged_but_an_unknown_capitalised_word_is():
    """Një term mjekësor i fjalorit duket si emër (shkronjë e madhe, fjalë e panjohur në shqipen e përditshme) dhe kalon;
    një fjalë tjetër me shkronjë të madhe nuk kalon."""
    assert scan_text("Mjeku vëren Hepatopati") == ()
    assert scan_text("Mjeku vëren Hepatopati te Floriani") == (Kind.NAME_LIKE,)


# --------------------------------------------------------------------
# Çfarë shënohet
# --------------------------------------------------------------------

FLAGGED: list[tuple[str, set[Kind]]] = [
    ("Dr. Elira Gashi e ka vlerësuar rezultatin", {Kind.TITLE, Kind.NAME_LIKE}),
    ("Znj. Mirela Hoxha duhet ta përsërisë analizën", {Kind.TITLE, Kind.NAME_LIKE}),
    ("Prof. Dritan Berisha këshillon kontroll", {Kind.TITLE, Kind.NAME_LIKE}),
    ("Pacientja Valbona Shehu paraqet vlera të ulëta", {Kind.NAME_LIKE}),
    ("Pacienti Arben Krasniqi ka hemoglobinë të ulët", {Kind.NAME_LIKE}),
    ("Rezultati i takon Gentian Morina", {Kind.NAME_LIKE}),
    ("Zoti Ilir ka glukozë të rritur", {Kind.TITLE, Kind.NAME_LIKE}),
    ("Kontrolli i radhës është më 14.03.2026", {Kind.DATE}),
    ("Kontrolli i radhës është më 14/3/26", {Kind.DATE}),
    ("Rezultati u mor më 2026-03-14", {Kind.DATE}),
    ("Kontrolli i radhës është më 14 mars", {Kind.DATE}),
    ("Kontrolli i radhës është në mars 2026", {Kind.DATE, Kind.LONG_NUMBER}),
    ("Telefononi në 069 123 4567", {Kind.PHONE, Kind.CONTACT_CUE}),
    ("Telefononi në +355 4 222 3333", {Kind.PHONE}),
    ("Merreni në (04) 222-3333", {Kind.PHONE}),
    ("Dërgoni rezultatin në arben.krasniqi@shembull.al", {Kind.EMAIL}),
    ("Shihni www.klinika-shembull.al për rezultatet", {Kind.URL}),
    ("Numri personal i pacientit është I05101999A", {Kind.ID_TOKEN}),
    ("Dosja 884213 mban rezultatet e mëparshme", {Kind.LONG_NUMBER}),
    ("Kodi i mostrës AB123456 u përsërit", {Kind.ID_TOKEN, Kind.LONG_NUMBER}),
    ("Pacienti është 45 vjeç", {Kind.BIRTH_OR_AGE}),
    ("Mosha e pacientit ndikon në vlerësim", {Kind.BIRTH_OR_AGE}),
    ("Lindur më 3 maj", {Kind.BIRTH_OR_AGE, Kind.DATE}),
    ("Datëlindja është në dosje", {Kind.BIRTH_OR_AGE}),
    ("Banon në rrugën e Kavajës", {Kind.ADDRESS_CUE}),
    ("Vlerat u dërguan në adresën e pacientit", {Kind.ADDRESS_CUE}),
]


@pytest.mark.parametrize(("quote", "expected"), FLAGGED)
def test_identifying_forms_are_flagged(quote, expected):
    assert expected <= set(scan_text(quote)), (quote, scan_text(quote))


# Emra shembull të zakonshëm: asnjëri nuk duhet të kalojë, edhe kur rastis me një fjalë të fjalorit.
FIRST_NAMES = (
    "Arben Besnik Dritan Fatmir Genc Gentian Gezim Ilir Kujtim Lulzim Mentor Naim Petrit Sokol Valon Agim Altin Armend "
    "Artan Bashkim Burim Dashamir Edmond Elton Endrit Erion Fisnik Flamur Gazmend Hysen Jetmir Kastriot Klodian Leonard "
    "Luan Mimoza Ardita Besa Blerta Drita Elira Elona Fjolla Flora Jeta Lindita Majlinda Mirela Nora Rita Teuta Valbona "
    "Vjosa Zana Albana Aferdita Alma Anila"
).split()
SURNAMES = (
    "Krasniqi Berisha Hoxha Gashi Shehu Kola Dervishi Hasani Morina Rama Basha Bytyqi Dibra Elezi Gjoka Hysaj Islami "
    "Kelmendi Leka Meta Nika Osmani Prifti Qosja Rexhepi Sadiku Tafa Ujkani Vata Zogaj Kurti Mehmeti Selimi Aliu Ahmeti "
    "Bajrami Cani Deda Ndreu Marku Pjetri Lleshi Hajdari Mustafa Gjinaj Gjoni Spahiu"
).split()
PLACES = "Tiranë Prishtinë Durrës Shkodër Vlorë Elbasan Korçë Gjakovë Pejë Prizren Fier Berat Kukës Lezhë Sarandë".split()


@pytest.mark.parametrize("name", FIRST_NAMES + SURNAMES + PLACES)
def test_a_common_name_is_flagged_mid_sentence_and_as_the_first_word(name):
    assert Kind.NAME_LIKE in scan_text(f"Vlera e glukozës te {name} është mbi intervalin")
    assert Kind.NAME_LIKE in scan_text(f"{name} ka glukozë të rritur")
    assert not is_known_word(name)


def test_an_all_caps_name_is_flagged_but_a_catalogue_abbreviation_is_not():
    assert Kind.NAME_LIKE in scan_text("PACIENTI ARBEN KRASNIQI ka glukozë të rritur")
    assert scan_text("Vlerat e TSH dhe ALT janë brenda intervalit") == ()


def test_invisible_characters_do_not_hide_an_email_or_a_number():
    assert Kind.EMAIL in scan_text("arben​.krasniqi@shembull​.al")
    assert Kind.PHONE in scan_text("telefon ０６９１２３４５６７")


def test_a_month_name_next_to_a_number_is_a_date_but_a_month_alone_is_not():
    assert Kind.DATE in scan_text("Kontrolli bëhet më 5 shtator")
    assert Kind.DATE in scan_text("Në shtator 2025 duhet përsëritur")
    assert Kind.DATE not in scan_text("Kontrolli bëhet në shtator")


def test_flags_never_carry_the_flagged_string():
    context = build_reference_context()
    name = "Arben Krasniqi"
    leaked = context.assertions[0].model_copy(update={"text_span": f"Dr. {name} ka konfirmuar glukozë të rritur"})
    verdict = inspect(context.model_copy(update={"assertions": (leaked, *context.assertions[1:])}))
    assert not verdict.clean
    assert {flag.field for flag in verdict.flags} == {"assertion"}
    assert {flag.index for flag in verdict.flags} == {0}
    assert set(verdict.kinds) == {"name_like", "title"}
    rendered = repr(verdict) + str(verdict.kinds)
    assert "Arben" not in rendered and "Krasniqi" not in rendered


# --------------------------------------------------------------------
# Termat e pashpjeguar
# --------------------------------------------------------------------


def _with_unexplained(*terms: str):
    return build_reference_context().model_copy(update={"unexplained_terms": tuple(terms)})


def test_a_lowercase_medical_word_is_a_valid_unexplained_term():
    assert inspect(_with_unexplained("makrocitozë", "anizocitozë")).clean


@pytest.mark.parametrize("term", ["Kaduri", "Arbenuri", "makro-citozë", "anemi12", "hipo glicemi", "x"])
def test_an_unexplained_term_that_could_be_a_name_or_is_not_a_single_word_is_flagged(term):
    assert not inspect(_with_unexplained(term)).clean


# --------------------------------------------------------------------
# Vlerat e strukturuara: vetëm ato të katalogut
# --------------------------------------------------------------------


def test_the_reference_context_passes_the_gate():
    assert inspect(build_reference_context()).clean


def test_a_finding_whose_name_or_unit_is_not_the_catalogues_is_flagged():
    context = build_reference_context()
    renamed = context.findings[0].model_copy(update={"analyte_name_canonical": "Glukoza e Arben Krasniqit"})
    reunit = context.findings[1].model_copy(update={"unit_canonical": "g/dL (Arben)"})
    verdict = inspect(context.model_copy(update={"findings": (renamed, reunit, *context.findings[2:])}))
    assert [(f.kind, f.field, f.index) for f in verdict.flags] == [
        (Kind.UNCATALOGUED, "finding", 0),
        (Kind.UNCATALOGUED, "finding", 1),
    ]


def test_a_glossary_entry_that_is_not_the_catalogues_is_flagged():
    context = build_reference_context()
    altered = GlossaryEntry(
        term="anemi",
        explanation_sq="gjendja e pacientit Arben Krasniqi",
        source_ref="x",
    )
    verdict = inspect(context.model_copy(update={"glossary": (altered,)}))
    assert [(f.kind, f.field) for f in verdict.flags] == [(Kind.UNCATALOGUED, "glossary")]


# --------------------------------------------------------------------
# Garancia strukturore: çfarë del te kërkesa është ajo që porta shikon
# --------------------------------------------------------------------

SENTINEL = "SENTINELË"


def _prompt_text(context) -> str:
    prompt = build_prompt(context)
    return prompt.system + "\n" + prompt.user


def test_free_text_fields_that_the_gate_does_not_scan_never_reach_the_prompt():
    """Nëse dikush e fut një fushë të re të tekstit të lirë te kërkesa, ky test e rrëzon: porta e skanon vetëm atë që
    del nga dokumenti dhe hyn te kërkesa, dhe çdo fushë tjetër duhet të mbetet jashtë saj."""
    context = build_reference_context()
    findings = tuple(
        f.model_copy(
            update={
                "analyte_name_raw": f"{SENTINEL}-raw",
                "unit_raw": f"{SENTINEL}-unit",
                "value_raw": f"{SENTINEL}-vlera",
                "flag_in_document": f"{SENTINEL}-flamur",
            }
        )
        for f in context.findings
    )
    glossary = tuple(
        GlossaryEntry(
            term=g.term,
            explanation_sq=g.explanation_sq,
            source_ref=f"{SENTINEL}-burimi",
            category=f"{SENTINEL}-kategoria",
            synonyms=(f"{SENTINEL}-sinonim",),
        )
        for g in context.glossary
    )
    assertions = tuple(
        a.model_copy(update={"analyte_code": None if a.analyte_code is None else a.analyte_code}) for a in context.assertions
    )
    prompt = _prompt_text(context.model_copy(update={"findings": findings, "glossary": glossary, "assertions": assertions}))
    assert SENTINEL not in prompt
    # Provë që kontrolli nuk është bosh: vargjet e skanuara vërtet shfaqen te kërkesa.
    assert "Glukozë në serum" in prompt and "Rekomandohet kontroll pas 3 muajsh" in prompt


def test_the_two_free_text_fields_that_reach_the_prompt_are_exactly_the_ones_the_gate_scans():
    context = build_reference_context()
    quote = ReportAssertion(
        text_span=f"{SENTINEL} ka konfirmuar glukozë të rritur",
        analyte_code=None,
        direction=Direction.UNSPECIFIED,
        polarity=Polarity.AFFIRMED,
        certainty=Certainty.CONFIRMED,
        kind=AssertionKind.TERM_MENTION,
        char_start=0,
        char_end=30,
    )
    with_quote = context.model_copy(update={"assertions": (quote,)})
    assert SENTINEL in _prompt_text(with_quote)
    assert not inspect(with_quote).clean

    with_term = context.model_copy(update={"unexplained_terms": (f"{SENTINEL}uri",)})
    assert SENTINEL in _prompt_text(with_term)
    assert not inspect(with_term).clean


def test_the_vocabulary_comes_from_the_catalogue_and_the_policy_texts_not_from_a_general_dictionary():
    vocabulary = deidentify.vocabulary()
    for word in ("hemoglobine", "anemi", "ferritina", "mmol", "konsultohuni"):
        assert word in vocabulary, word
    for word in ("arben", "krasniqi", "berisha", "tirane"):
        assert word not in vocabulary, word
