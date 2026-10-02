"""
Shtojcat e ndërtuara nga kodi.

Një shtojcë është e vlefshme vetëm për aq sa përputhet me burimin që e prodhon.
Këto teste nuk kontrollojnë pamjen por lidhjen: çdo term, çdo tabelë e bazës dhe
çdo rregull që sistemi ka shfaqet në shtojcën përkatëse, dhe shtojcat që s'mund
të plotësohen e thonë këtë shprehimisht në vend që të mbeten bosh.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

pytest.importorskip("sqlalchemy")

from analyte.domain.policy import RULE_CATALOG  # noqa: E402
from analyte.persistence.tables import Base  # noqa: E402
from scripts import build_appendices as appendices  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
needs_corpus = pytest.mark.skipif(
    not (ROOT / "data" / "v1" / "manifest.json").exists(), reason="korpusi data/v1 mungon"
)


def test_every_terminology_entry_is_in_appendix_a():
    with (ROOT / "resources" / "terminology.csv").open(encoding="utf-8", newline="") as handle:
        terms = [row["term"] for row in csv.DictReader(handle)]
    text = appendices.appendix_a()
    assert all(f"| {term} |" in text for term in terms)
    assert f"Tabela mban {len(terms)} terma" in text


def test_appendix_a_says_how_many_entries_have_no_source():
    """Burimet mungojnë dhe teksti nuk e fsheh: numri shfaqet te shtojca."""
    text = appendices.appendix_a()
    unsourced = text.count("[BURIMI")
    assert unsourced > 0 and f"{unsourced} prej tyre" in text


def test_the_schema_appendix_has_every_table_and_index():
    text = appendices.appendix_g()
    for table in Base.metadata.sorted_tables:
        assert f"CREATE TABLE {table.name} " in text, table.name
        for index in table.indexes:
            assert f"CREATE INDEX {index.name} " in text or f"CREATE UNIQUE INDEX {index.name} " in text
    assert f"{len(Base.metadata.tables)} tabela" in text


def test_every_rule_of_the_catalog_is_in_appendix_c():
    text = appendices.appendix_c()
    for rule in RULE_CATALOG:
        assert f"| {rule.id} |" in text, rule.id


def test_appendix_c_examples_show_the_rule_actually_firing():
    """Prova në çdo rresht vjen nga rregulli mbi fjalinë, jo nga një shembull i shkruar me dorë."""
    rows = [r for r in appendices.appendix_c().split("\n") if r.startswith("| R") and "`" in r]
    assert len(rows) >= 7
    assert not any("rregulli nuk e kapi" in r for r in rows)


def test_appendices_that_cannot_be_filled_say_so_explicitly():
    for build in (appendices.appendix_d, appendices.appendix_e, appendices.appendix_f):
        text = build()
        assert "Nuk aplikohet" in text or "Nuk ka kërkesa" in text


def test_table_labels_carry_the_appendix_letter():
    assert "Tabela B.1." in appendices.appendix_b()
    assert "Tabela C.1." in appendices.appendix_c()
    # asnjë tabelë e shtojcës nuk mban numër të thjeshtë: ai do të ngatërrohej me tabelat e trupit
    for number in range(1, 6):
        assert f"Tabela {number}." not in appendices.appendix_b()
        assert f"Tabela {number}." not in appendices.appendix_c()


@needs_corpus
def test_configuration_appendix_reports_real_versions():
    from analyte.domain.policy import POLICY_VERSION, RULES_VERSION

    text = appendices.appendix_h()
    assert RULES_VERSION in text and POLICY_VERSION in text
    assert "Fara | 42" in text


@needs_corpus
def test_example_appendix_renders_one_digital_and_one_scanned_document(tmp_path, monkeypatch):
    monkeypatch.setattr(appendices, "OUT", tmp_path)
    text = appendices.appendix_i()
    assert "dokument_dixhital.png" in text and "dokument_skanuar.png" in text
    assert (tmp_path / "images" / "dokument_dixhital.png").stat().st_size > 10_000
    assert (tmp_path / "images" / "dokument_skanuar.png").stat().st_size > 10_000
