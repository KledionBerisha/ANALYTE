"""
Kthimi i kontekstit dhe i shpjegimit përmes bazës.

Çdo gjë që shkruhet duhet të lexohet si i njëjti objekt domeni —
identifikuesit, numrat dhjetorë, rendi. Rregulli R1 krahason numrat me
barazi të saktë; një kontekst që humb një shifër dhjetore gjatë ruajtjes
do ta bënte verifikimin mbi kontekstin e ruajtur të ndryshëm nga ai mbi
kontekstin origjinal.
"""

from __future__ import annotations

import random
from decimal import Decimal
from uuid import uuid4

import pytest

from analyte.domain.models import GroundingContext
from analyte.generation.templates import TemplateGenerator
from analyte.orchestration.process import explain
from analyte.persistence import repository
from analyte.persistence.database import create_schema, make_engine, make_session_factory
from analyte.persistence.tables import DocumentRow, UserRow
from tests.fixtures.grounding_context import build_reference_context


@pytest.fixture
def sessions(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'r.db'}")
    create_schema(engine)
    return make_session_factory(engine)


def _document(session, document_id):
    user = UserRow(email=f"{uuid4().hex}@shembull.al", password_hash="x")
    session.add(user)
    session.flush()
    session.add(
        DocumentRow(
            id=document_id,
            user_id=user.id,
            filename_encrypted=b"x",
            mime="application/pdf",
            sha256="0" * 64,
            size_bytes=1,
            storage_path="x.bin",
            state="grounded",
        )
    )
    session.flush()


def _generated_context() -> GroundingContext:
    from data_generator.ground_truth import build_document
    from data_generator.ids import IdFactory

    for index in range(40):
        rng = random.Random(f"repo/{index}")
        context = build_document(rng, IdFactory(rng), scanned_share=0.0).context
        if context.patterns and context.glossary and context.unexplained_terms:
            return context
    raise AssertionError("asnjë kontekst me të gjitha pjesët")  # pragma: no cover


@pytest.mark.parametrize("builder", [build_reference_context, _generated_context])
def test_context_round_trips_field_for_field(sessions, builder):
    context = builder()
    with sessions() as session:
        _document(session, context.document_id)
        repository.save_context(session, context)
        session.commit()
    with sessions() as session:
        loaded = repository.load_context(session, context.document_id)
    assert loaded == context


def test_decimals_keep_every_digit(sessions):
    context = build_reference_context()
    finding = context.findings[0].model_copy(
        update={"value": Decimal("13.40"), "value_raw": "13,40"}
    )
    context = context.model_copy(update={"findings": (finding, *context.findings[1:])})
    with sessions() as session:
        _document(session, context.document_id)
        repository.save_context(session, context)
        session.commit()
    with sessions() as session:
        value = repository.load_context(session, context.document_id).findings[0].value
    assert str(value) == "13.40"


def test_saving_twice_replaces_rather_than_duplicates(sessions):
    context = build_reference_context()
    with sessions() as session:
        _document(session, context.document_id)
        repository.save_context(session, context)
        repository.save_context(session, context)
        session.commit()
    with sessions() as session:
        assert repository.load_context(session, context.document_id) == context


def test_delivered_explanation_and_its_verification_round_trip(sessions):
    context = build_reference_context()
    explanation = explain(context, TemplateGenerator())
    with sessions() as session:
        _document(session, context.document_id)
        repository.save_explanation(session, context.document_id, explanation)
        session.commit()
    with sessions() as session:
        row = repository.load_delivered(session, context.document_id)
        assert row.final_output == explanation.text
        restored = repository.to_verification(row.verification)
    assert restored.violations == explanation.verification.violations
    assert restored.rules_version == explanation.verification.rules_version


def test_advice_entries_round_trip_with_their_source(sessions):
    """ADR 0023: këshilla ruhet e plotë, si fjalori, bashkë me burimin dhe gjetjen e saj."""
    from analyte.catalog import Advice
    from analyte.grounding.branch_a.advice import attach

    context = build_reference_context()
    high = next(f for f in context.findings if f.status.direction.value == "increased")
    table = (Advice(high.analyte_code, "increased", "Flisni me mjekun tuaj për këtë vlerë.", "Burim i lexuar (provë)"),)
    context = context.model_copy(update={"advice": attach(context.findings, table)})
    assert len(context.advice) == 1
    with sessions() as session:
        _document(session, context.document_id)
        repository.save_context(session, context)
        session.commit()
    with sessions() as session:
        loaded = repository.load_context(session, context.document_id)
    assert loaded == context and loaded.advice[0].source_ref == "Burim i lexuar (provë)"

