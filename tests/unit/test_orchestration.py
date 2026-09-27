"""
Testet e makinës së përpunimit (Figura 6).

Kriteri i Fazës 6 kërkon që çdo rrugë e makinës të ketë test integrimi,
përfshirë dështimin e dyfishtë që çon te shablloni. Ky kriter këtu nuk
lihet si premtim: skenarët drejtohen të gjithë nga skedari PDF deri te
gjendja përfundimtare, dhe testi i fundit kontrollon që bashkimi i
kalimeve të tyre mbulon çdo kalim të tabelës. Një kalim i shtuar pa
skenar e rrëzon atë test.

Modeli gjuhësor nuk ekziston ende, prandaj gjeneruesit janë të rremë:
njëri kthen shabllonin (tekst i saktë i garantuar), tjetri shabllonin me
një numër të shpikur (shkelje e garantuar e R1), i treti hedh përjashtim.
Këto mjaftojnë për makinën — ajo nuk di dhe nuk duhet të dijë kush e
shkroi tekstin.
"""

from __future__ import annotations

import inspect
import random
from uuid import uuid4

import pymupdf
import pytest

from analyte.domain.enums import ProcessingState as S
from analyte.domain.enums import ViolationType
from analyte.domain.policy import DISCLAIMER_SQ, MAX_GENERATION_ATTEMPTS
from analyte.generation import templates
from analyte.generation.base import Generator
from analyte.ingestion.format import rejection_reason
from analyte.ingestion.pdf_text import read_pdf
from analyte.orchestration.process import Delivery, explain, process
from analyte.orchestration.states import TRANSITIONS, IllegalTransition, StateLog
from tests.fixtures.grounding_context import build_reference_context

INVENTED_NUMBER = "Vlera e matur është 987654."


def perfect(context) -> str:
    return templates.build(context)


def defective(context) -> str:
    return templates.build(context).replace(DISCLAIMER_SQ, f"{INVENTED_NUMBER} {DISCLAIMER_SQ}")


class Scripted:
    """Gjenerues që ndjek një skenar: një hap për çdo përpjekje.

    Hapi është funksion i kontekstit ose përjashtim. Gjeneruesi ruan
    shkeljet që i janë dhënë, që testet të shohin çfarë mori përpjekja e
    dytë.
    """

    name = "scripted"

    def __init__(self, *steps):
        self.steps = list(steps)
        self.feedback = []

    def __call__(self, context, feedback):
        self.feedback.append(feedback)
        step = self.steps.pop(0)
        if isinstance(step, Exception):
            raise step
        return step(context)


# --------------------------------------------------------------------
# Dokumentet
# --------------------------------------------------------------------


def _render(scanned: bool, seed: str) -> bytes:
    from data_generator.generate import render
    from data_generator.ground_truth import build_document
    from data_generator.ids import IdFactory

    for index in range(20):
        rng = random.Random(f"{seed}/{index}")
        document = build_document(rng, IdFactory(rng), scanned_share=1.0 if scanned else 0.0)
        if document.context.findings:
            return render(document, seed=7, index=index)[0]
    raise AssertionError("asnjë dokument me gjetje")  # pragma: no cover


def _blank_report() -> bytes:
    """PDF dixhital me tekst të mjaftueshëm, por pa analite dhe pa narrativë.

    Kalon router-in si shtresë teksti, prandaj rruga e tij mbaron te
    `NO_FINDINGS` dhe jo te OCR-ja.
    """
    document = pymupdf.open()
    page = document.new_page()
    for line in range(12):
        page.insert_text(
            (72, 72 + 20 * line), f"Rreshti {line + 1}: njoftim administrativ i qendres."
        )
    data = document.tobytes()
    document.close()
    return data


@pytest.fixture(scope="module")
def files(tmp_path_factory):
    directory = tmp_path_factory.mktemp("orchestration")
    paths = {
        "digital": _render(scanned=False, seed="orch-digital"),
        "scanned": _render(scanned=True, seed="orch-scanned"),
        "blank": _blank_report(),
        "not_pdf": b"Ky eshte skedar teksti, jo PDF.\n",
    }
    out = {}
    for name, data in paths.items():
        out[name] = directory / f"{name}.pdf"
        out[name].write_bytes(data)
    return out


def _ocr_from(path):
    """OCR i rremë: kthen faqet e një dokumenti dixhital.

    Makina nuk varet nga cilësia e OCR-së, vetëm nga fakti nëse ajo
    ktheu faqe apo dështoi.
    """
    return lambda _: read_pdf(path)


def _ocr_broken(_):
    raise RuntimeError("tesseract mungon")


# --------------------------------------------------------------------
# Skenarët — një për çdo rrugë të Figurës 6
# --------------------------------------------------------------------


@pytest.fixture(scope="module")
def outcomes(files):
    boom = ConnectionError("API nuk u përgjigj")
    scenarios = {
        "rejected": (files["not_pdf"], Scripted(), None),
        "first_pass": (files["digital"], Scripted(perfect), None),
        "second_pass": (files["digital"], Scripted(defective, perfect), None),
        "double_failure": (files["digital"], Scripted(defective, defective), None),
        "error_then_pass": (files["digital"], Scripted(boom, perfect), None),
        "double_error": (files["digital"], Scripted(boom, boom), None),
        "no_ocr": (files["scanned"], Scripted(), None),
        "ocr_fails": (files["scanned"], Scripted(), _ocr_broken),
        "ocr_reads": (files["scanned"], Scripted(perfect), _ocr_from(files["digital"])),
        "no_findings": (files["blank"], Scripted(), None),
    }
    out = {}
    for name, (path, generator, ocr) in scenarios.items():
        out[name] = (process(uuid4(), path, generator, ocr=ocr), generator)
    return out


def _path(outcome):
    return [t.target for t in outcome.transitions]


def test_non_pdf_is_rejected(outcomes):
    outcome, _ = outcomes["rejected"]
    assert _path(outcome) == [S.REJECTED]
    assert "nuk është PDF" in outcome.reason


def test_verified_text_is_delivered_on_first_attempt(outcomes):
    outcome, _ = outcomes["first_pass"]
    assert outcome.state is S.DELIVERED
    assert outcome.explanation.delivery is Delivery.GENERATED
    assert len(outcome.explanation.attempts) == 1
    assert _path(outcome)[-3:] == [S.GENERATING, S.VERIFYING, S.DELIVERED]


def test_second_attempt_receives_the_first_attempts_violations(outcomes):
    """Rigjenerimi me shkeljet në kërkesë — dhe me të gjitha, jo me të parën."""
    outcome, generator = outcomes["second_pass"]
    first, second = outcome.explanation.attempts

    assert generator.feedback[0] == ()
    assert generator.feedback[1] == first.violations
    assert any(v.type is ViolationType.UNGROUNDED_NUMBER for v in first.violations)
    assert second.passed
    assert outcome.explanation.delivery is Delivery.GENERATED
    assert outcome.explanation.text == second.text


def test_double_failure_falls_back_to_the_template(outcomes):
    """SP8 — pas dy dështimeve pacienti sheh shabllonin, jo tekstin e dytë."""
    outcome, _ = outcomes["double_failure"]
    explanation = outcome.explanation

    assert _path(outcome)[-6:] == [
        S.GENERATING,
        S.VERIFYING,
        S.GENERATING,
        S.VERIFYING,
        S.TEMPLATE_FALLBACK,
        S.DELIVERED,
    ]
    assert explanation.delivery is Delivery.TEMPLATE
    assert len(explanation.attempts) == MAX_GENERATION_ATTEMPTS
    assert INVENTED_NUMBER not in explanation.text
    assert explanation.text == templates.build(outcome.context)
    assert explanation.verification.passed


def test_generator_error_counts_as_an_attempt(outcomes):
    """Përjashtimi nuk e ngec dokumentin; përpjekja e dytë nis pa shkelje."""
    outcome, generator = outcomes["error_then_pass"]
    first, second = outcome.explanation.attempts

    assert first.error.startswith("ConnectionError")
    assert first.text is None and first.verification is None
    assert generator.feedback[1] == ()
    assert second.passed
    assert _path(outcome)[-4:] == [S.GENERATING, S.GENERATING, S.VERIFYING, S.DELIVERED]


def test_repeated_generator_error_falls_back_to_the_template(outcomes):
    outcome, _ = outcomes["double_error"]
    assert _path(outcome)[-4:] == [S.GENERATING, S.GENERATING, S.TEMPLATE_FALLBACK, S.DELIVERED]
    assert outcome.explanation.delivery is Delivery.TEMPLATE
    assert "ConnectionError" in outcome.transitions[-2].reason


def test_scanned_document_without_ocr_fails_explicitly(outcomes):
    """"Nuk u lexua" nuk është "nuk kishte asgjë"."""
    outcome, _ = outcomes["no_ocr"]
    assert _path(outcome) == [S.INGESTING, S.OCR_RUNNING, S.FAILED_INGESTION]
    assert "OCR" in outcome.reason
    assert outcome.context is None


def test_ocr_failure_is_recorded(outcomes):
    outcome, _ = outcomes["ocr_fails"]
    assert outcome.state is S.FAILED_INGESTION
    assert "tesseract mungon" in outcome.reason


def test_ocr_pages_continue_down_the_same_path(outcomes):
    outcome, _ = outcomes["ocr_reads"]
    assert _path(outcome)[:4] == [S.INGESTING, S.OCR_RUNNING, S.TEXT_EXTRACTED, S.PARSING]
    assert outcome.state is S.DELIVERED


def test_document_without_content_stops_before_generation(outcomes):
    outcome, generator = outcomes["no_findings"]
    assert _path(outcome) == [S.INGESTING, S.TEXT_EXTRACTED, S.PARSING, S.NO_FINDINGS]
    assert generator.feedback == []
    assert outcome.explanation is None


def test_every_outcome_ends_in_a_terminal_state(outcomes):
    for name, (outcome, _) in outcomes.items():
        assert outcome.state.is_terminal, name


def test_generated_text_is_never_delivered_unverified(outcomes):
    """NFR1 — dalja e gjeneruesit arrin te pacienti vetëm pa shkelje."""
    for name, (outcome, _) in outcomes.items():
        explanation = outcome.explanation
        if explanation is not None and explanation.delivery is Delivery.GENERATED:
            assert explanation.verification.passed, name


def test_scenarios_cover_every_transition_of_the_figure(outcomes):
    """Kriteri i Fazës 6, i kontrolluar dhe jo i deklaruar."""
    covered = {
        (t.source, t.target) for outcome, _ in outcomes.values() for t in outcome.transitions
    }
    expected = {(source, target) for source, targets in TRANSITIONS.items() for target in targets}
    assert expected - covered == set()


# --------------------------------------------------------------------
# Cikli pa dokument
# --------------------------------------------------------------------


def test_loop_runs_on_a_given_context():
    """Ablacioni e drejton ciklin mbi kontekstin e vërtetë, pa nxjerrje."""
    context = build_reference_context()
    log = StateLog(start=S.GROUNDED)
    explanation = explain(context, Scripted(defective, defective), log=log)

    assert explanation.delivery is Delivery.TEMPLATE
    assert log.state is S.DELIVERED
    assert explanation.verification.passed


def test_verifier_errors_are_not_swallowed():
    """Një verifikues i prishur nuk duhet të kthehet në shabllon të heshtur."""

    def broken(context, text):
        raise RuntimeError("rregulli R3 u rrëzua")

    with pytest.raises(RuntimeError, match="R3"):
        explain(build_reference_context(), Scripted(perfect), verifier=broken)


def test_generator_sees_only_context_and_feedback():
    """E njëjta garanci si `build_prompt`: asnjë rrugë drejt dokumentit."""
    parameters = list(inspect.signature(Generator.__call__).parameters)
    assert parameters == ["self", "context", "feedback"]


# --------------------------------------------------------------------
# Tabela e kalimeve
# --------------------------------------------------------------------


def test_table_names_every_state():
    assert set(TRANSITIONS) == set(S)


def test_terminal_states_have_no_exit():
    for state, targets in TRANSITIONS.items():
        assert (not targets) == state.is_terminal, state


def test_every_state_is_reachable_from_upload():
    reached, frontier = {S.UPLOADED}, [S.UPLOADED]
    while frontier:
        for target in TRANSITIONS[frontier.pop()]:
            if target not in reached:
                reached.add(target)
                frontier.append(target)
    assert reached == set(S)


def test_illegal_transition_is_refused():
    log = StateLog()
    with pytest.raises(IllegalTransition):
        log.advance(S.DELIVERED)
    assert log.state is S.UPLOADED
    assert log.transitions == ()


# --------------------------------------------------------------------
# Kontrolli i formatit
# --------------------------------------------------------------------


def test_truncated_pdf_is_rejected(tmp_path):
    path = tmp_path / "broken.pdf"
    path.write_bytes(b"%PDF-1.7\n1 0 obj << /Type /Catalog")
    assert "dëmtuar" in rejection_reason(path) or "faqe" in rejection_reason(path)


def test_encrypted_pdf_is_rejected(tmp_path):
    document = pymupdf.open()
    document.new_page()
    path = tmp_path / "locked.pdf"
    document.save(
        path, encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="sekret", owner_pw="sekret"
    )
    document.close()
    assert "fjalëkalim" in rejection_reason(path)


def test_missing_file_is_rejected(tmp_path):
    assert "nuk lexohet" in rejection_reason(tmp_path / "mungon.pdf")


def test_valid_pdf_is_accepted(files):
    assert rejection_reason(files["digital"]) is None
    assert rejection_reason(files["scanned"]) is None
