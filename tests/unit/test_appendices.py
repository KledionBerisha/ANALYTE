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


def test_appendix_a_reports_the_state_of_the_sources_honestly():
    """Kur burimet mungojnë, numri i vendmbajtësve shfaqet; kur janë plotësuar (2026-10-06),
    teksti e thotë dhe asnjë vendmbajtës nuk mbetet në tabelë."""
    text = appendices.appendix_a()
    terminology_table = text.split("Tabela A.2")[0]  # Tabela A.2 (këshillat) ka vendmbajtësit e vet
    unsourced = terminology_table.count("[BURIMI")
    if unsourced:
        assert f"{unsourced} prej tyre" in text
    else:
        assert "Secili zë mban në kolonën e burimit" in text
        assert "plotësohet" not in terminology_table


def test_appendix_a_lists_the_advice_table_with_its_source_state():
    """ADR 0023: Tabela A.2 radhit çdo rresht të `advice.csv` dhe thotë sa kanë fjali dhe burim."""
    with (ROOT / "resources" / "advice.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    text = appendices.appendix_a()
    filled = sum(1 for r in rows if r["advice_sq"].strip() and "plotësohet" not in r["source_ref"])
    assert "*Tabela A.2. Këshillat me burim sipas analitit dhe drejtimit*" in text
    assert f"{filled} nga {len(rows)} rreshta kanë fjali" in text
    assert text.count("| mbi intervalin |") + text.count("| nën intervalin |") == len(rows)


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
    for build in (appendices.appendix_e, appendices.appendix_f):
        assert "Nuk aplikohet" in build()


def test_appendix_d_shows_the_real_prompts_not_copies():
    from analyte.generation.prompt import PROMPT_VERSION, SYSTEM
    from evaluation import llm_judge, ungrounded

    text = appendices.appendix_d()
    assert SYSTEM in text and ungrounded.SYSTEM in text and llm_judge.SYSTEM in text
    assert f"`{PROMPT_VERSION}`" in text
    assert "KONTEKSTI" in text  # kërkesa e vërtetë për një dokument
    assert "987654" in text and "Shpjegimi i mëparshëm u refuzua" in text  # blloku i rigjenerimit
    assert "Nuk ka kërkesa" not in text


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


# --------------------------------------------------------------------
# Shtojcat te teksti i plotë
# --------------------------------------------------------------------


def _write_appendix(directory: Path, letter: str, body: str) -> None:
    (directory / f"{letter}_test.md").write_text(
        f"<!-- koment -->\n\n## Shtojca {letter} — Titull\n\n{body}\n", encoding="utf-8"
    )


def test_sync_replaces_only_the_sections_that_differ_and_keeps_the_rest_of_the_thesis(tmp_path):
    for letter, body in (("A", "tekst i ri"), ("B", "i pandryshuar")):
        _write_appendix(tmp_path, letter, body)
    thesis = tmp_path / "teza.md"
    thesis.write_text(
        "# Kapitulli\n\nteksti kryesor\n\n---\n\n"
        "## Shtojca A — Titull\n\ntekst i vjetër\n\n---\n\n"
        "## Shtojca B — Titull\n\ni pandryshuar\n",
        encoding="utf-8",
    )
    assert appendices.sync_into_thesis(thesis, tmp_path) == ["A"]
    text = thesis.read_text(encoding="utf-8")
    assert "tekst i ri" in text and "tekst i vjetër" not in text
    assert text.startswith("# Kapitulli\n\nteksti kryesor\n\n---\n\n")
    assert "\n---\n\n## Shtojca B — Titull" in text  # ndarësi mes shtojcave mbetet
    # një ekzekutim i dytë nuk ndryshon asgjë
    assert appendices.sync_into_thesis(thesis, tmp_path) == []


def test_the_thesis_appendices_are_the_generated_files():
    """Teksti i plotë dhe skedarët e shtojcave nuk duhet të largohen: pas çdo ndërtimi,
    `python scripts/build_appendices.py --thesis docs/thesis/teza_v3.md`."""
    thesis = ROOT / "docs" / "thesis" / "teza_v3.md"
    copy = thesis.read_text(encoding="utf-8")
    scratch = thesis.parent / "_sync_check.md"
    try:
        scratch.write_text(copy, encoding="utf-8", newline="\n")
        assert appendices.sync_into_thesis(scratch) == []
    finally:
        scratch.unlink(missing_ok=True)


def test_result_files_are_listed_by_experiment_number_with_the_model_runs_last(tmp_path, monkeypatch):
    """Tabela H.3 liston edhe E10, E11 (një rezultat për hyrje) dhe rezultatet me modelin te `llm/`."""
    (tmp_path / "E10").mkdir()
    (tmp_path / "E10" / "result.json").write_text(
        '{"metadata": {"code": {"git_sha": "abcdef1234567890", "working_tree_dirty": false}, '
        '"dataset": {"version": "v1"}}}',
        encoding="utf-8",
    )
    (tmp_path / "E11" / "sentence").mkdir(parents=True)
    (tmp_path / "E11" / "sentence" / "result.json").write_text("{}", encoding="utf-8")
    (tmp_path / "llm" / "E8").mkdir(parents=True)
    (tmp_path / "llm" / "E8" / "result.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(appendices, "RESULTS", tmp_path)
    labels = [p.parent.relative_to(tmp_path).as_posix() for p in appendices.result_files()]
    assert labels == ["E10", "E11/sentence", "llm/E8"]
