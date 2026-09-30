"""
Figurat e ndërtuara nga kodi.

Figura është e vlefshme vetëm për aq sa përputhet me burimin që e përcakton.
Këto teste nuk kontrollojnë pamjen — atë e shikon njeriu — por lidhjen: çdo
gjendje, tabelë dhe eksperiment ka vend, çdo skaj vjen nga burimi, dhe një
burim që ndryshon pa e prekur figurën bën testin të dështojë me një mesazh që
thotë çfarë mungon.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.figures import layout

# --------------------------------------------------------------------
# Vendosja në shtresa (pa matplotlib)
# --------------------------------------------------------------------


def test_every_forward_edge_points_to_a_later_layer():
    nodes = list("abcdef")
    edges = [("a", "b"), ("b", "c"), ("a", "c"), ("c", "d"), ("a", "e"), ("e", "d"), ("d", "f")]
    depth = layout.layers(nodes, edges)
    assert all(depth[a] < depth[b] for a, b in edges)
    assert depth["a"] == 0 and depth["f"] == max(depth.values())


def test_a_cycle_is_reported_not_hidden():
    nodes = ["a", "b", "c"]
    edges = [("a", "b"), ("b", "c"), ("c", "b")]
    forward, back = layout.split_back_edges(nodes, edges)
    assert back == [("c", "b")] and ("b", "c") in forward
    assert [sorted(group) for group in layout.strongly_connected(nodes, edges)] == [["b", "c"]]


def test_a_self_loop_is_a_back_edge_but_not_a_cycle_between_nodes():
    forward, back = layout.split_back_edges(["a"], [("a", "a")])
    assert forward == [] and back == [("a", "a")]
    assert layout.strongly_connected(["a"], [("a", "a")]) == []


def test_ordering_within_layers_is_repeatable_and_complete():
    nodes = ["r", "x", "y", "z"]
    edges = [("r", "x"), ("r", "y"), ("r", "z")]
    depth = layout.layers(nodes, edges)
    first = layout.order_within_layers(depth, edges, nodes)
    assert first == layout.order_within_layers(depth, edges, nodes)
    assert sorted(n for column in first.values() for n in column) == sorted(nodes)


# --------------------------------------------------------------------
# Figurat
# --------------------------------------------------------------------

pytest.importorskip("matplotlib")

from analyte.domain.enums import ProcessingState  # noqa: E402
from analyte.orchestration.states import TRANSITIONS  # noqa: E402
from analyte.persistence.tables import Base  # noqa: E402
from scripts.figures import erd, evaluation_chain, modules, state_machine  # noqa: E402


def test_state_machine_draws_exactly_the_transition_table():
    fig, drawn = state_machine.build()
    assert sorted((a.value, b.value) for a, b in drawn) == sorted(
        (a.value, b.value) for a, targets in TRANSITIONS.items() for b in targets
    )
    assert len(drawn) == sum(len(targets) for targets in TRANSITIONS.values())
    assert set(state_machine.POSITIONS) == set(ProcessingState)
    state_machine.style.plt.close(fig)


def test_state_machine_refuses_a_state_without_a_place(monkeypatch):
    trimmed = dict(state_machine.POSITIONS)
    del trimmed[ProcessingState.NO_FINDINGS]
    monkeypatch.setattr(state_machine, "POSITIONS", trimmed)
    with pytest.raises(ValueError, match="no_findings"):
        state_machine.build()


def test_erd_has_every_table_and_every_foreign_key():
    fig, relations = erd.build()
    drawn_tables = {*erd.POSITIONS, *erd.CHILDREN, "verification_results", "violations"}
    assert drawn_tables == {t.name for t in Base.metadata.sorted_tables}
    foreign = {
        (fk.column.table.name, t.name, fk.parent.name)
        for t in Base.metadata.sorted_tables
        for fk in t.foreign_keys
    }
    enforced = {(p, c, col) for p, c, col, _one, logical in relations if not logical}
    assert enforced == foreign
    erd.style.plt.close(fig)


def test_erd_marks_the_unique_foreign_key_as_one_to_one():
    one_to_one = {(p, c) for p, c, _col, one, _logical in erd.relations() if one}
    assert one_to_one == {("explanations", "verification_results")}


def test_erd_logical_links_name_real_columns():
    for (table, column), parent in erd.LOGICAL_LINKS.items():
        assert column in Base.metadata.tables[table].c
        assert parent in Base.metadata.tables
        assert not any(fk.parent.name == column for fk in Base.metadata.tables[table].foreign_keys)


def test_erd_refuses_a_table_without_a_place(monkeypatch):
    monkeypatch.setattr(erd, "CHILDREN", erd.CHILDREN[:-1])
    with pytest.raises(ValueError, match="explanations"):
        erd.build()


def test_the_domain_module_depends_on_nothing_else_in_the_application():
    """Pohimi i §5.9: moduli i domenit nuk varet nga asnjë modul tjetër."""
    assert not [edge for edge in modules.import_graph() if edge[0] == "domain"]


def _package(tmp_path: Path, files: dict[str, str]) -> Path:
    root = tmp_path / "analyte"
    for name, source in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
    return root


def test_import_scanner_resolves_absolute_and_relative_imports(tmp_path):
    root = _package(
        tmp_path,
        {
            "api/auth.py": "from analyte.domain.models import X\nfrom . import deps\nfrom .sub import y\n",
            "api/deps.py": "from ..persistence.tables import T\nfrom .. import config\n",
            "main.py": "from .api import auth\nimport analyte.verification.base\n",
            "config.py": "import os\n",
            "domain/models.py": "from pydantic import BaseModel\n",
            "persistence/tables.py": "",
            "verification/base.py": "",
        },
    )
    edges = set(modules.import_graph(root))
    assert edges == {
        ("api", "domain"),
        ("api", "persistence"),
        ("api", "config"),
        ("main", "api"),
        ("main", "verification"),
    }


def test_import_scanner_counts_each_statement_and_ignores_self_edges(tmp_path):
    root = _package(
        tmp_path,
        {
            "grounding/a.py": "from analyte.domain import x\nfrom analyte.domain.models import y\n"
            "from analyte.grounding.b import z\n",
            "grounding/b.py": "",
            "domain/models.py": "",
        },
    )
    assert dict(modules.import_graph(root)) == {("grounding", "domain"): 2}


# --------------------------------------------------------------------
# Figura 11
# --------------------------------------------------------------------


def _experiment(runnable: bool):
    return evaluation_chain.registry.Experiment(
        "EX", "t", "—", "d", "m", "PK",
        status=evaluation_chain.registry.RUNNABLE
        if runnable
        else evaluation_chain.registry.NEEDS_USER_STUDY,
    )


def test_measured_means_a_result_file_exists_not_that_a_number_was_cited():
    status = evaluation_chain.status_of
    assert status(_experiment(True), {}) == evaluation_chain.READY
    assert status(_experiment(False), {}) == evaluation_chain.BLOCKED
    assert status(_experiment(False), {"EX": {"metrics": {}}}) == evaluation_chain.MEASURED
    # një rezultat që vetë thotë se pret diçka nuk është i matur
    assert status(_experiment(True), {"EX": {"pending_reason": "pret"}}) == evaluation_chain.READY


@pytest.mark.parametrize(
    ("result", "expected"),
    [
        (None, ""),
        ({"metrics": {}}, "pjesore"),
        ({"metadata": {"code": {"git_sha": "abc"}, "dataset": {}}}, "pjesore"),
        (
            {"metadata": {"code": {"git_sha": "abc", "working_tree_dirty": True},
                          "dataset": {"version": "v"}}},
            "pa commit",
        ),
        (
            {"metadata": {"code": {"git_sha": "abc", "working_tree_dirty": False},
                          "dataset": {"version": "v"}}},
            "e plotë",
        ),
    ],
)
def test_trace_says_how_traceable_a_measurement_is(result, expected):
    assert evaluation_chain.trace_of(result) == expected


def test_provenance_fields_are_read_from_a_real_result():
    fields = evaluation_chain.provenance_fields(
        {"E2": {"metadata": {"experiment_id": "E2", "dataset": {"seed": 1, "version": "v"},
                             "created_at": "x"}}}
    )
    assert fields == ["experiment_id, created_at", "dataset: seed, version"]
    assert evaluation_chain.provenance_fields({}) == []


def test_results_kept_in_subfolders_count_as_measured(tmp_path):
    """E11 ruan një rezultat për çdo hyrje, te `E11/sentence/result.json`."""
    (tmp_path / "E11" / "sentence").mkdir(parents=True)
    (tmp_path / "E11" / "sentence" / "result.json").write_text('{"metrics": {}}', encoding="utf-8")
    (tmp_path / "E11" / "leakage.json").write_text("{}", encoding="utf-8")  # nuk është rezultat
    (tmp_path / "E2").mkdir()
    (tmp_path / "E2" / "result.json").write_text('{"metrics": {}}', encoding="utf-8")
    assert sorted(evaluation_chain.load_results(tmp_path)) == ["E11", "E2"]


def test_figure_11_covers_every_registered_experiment():
    fig, statuses = evaluation_chain.build()
    assert list(statuses) == [e.id for e in evaluation_chain.registry.EXPERIMENTS]
    assert set(statuses.values()) <= {
        evaluation_chain.MEASURED, evaluation_chain.READY, evaluation_chain.BLOCKED,
    }
    evaluation_chain.style.plt.close(fig)


def test_every_blocked_experiment_says_what_it_waits_for():
    for experiment in evaluation_chain.registry.EXPERIMENTS:
        if not experiment.runnable:
            assert experiment.waiting_for or experiment.pending_reason


# --------------------------------------------------------------------
# Komanda
# --------------------------------------------------------------------


def test_the_command_writes_png_and_svg_for_each_figure(tmp_path):
    from scripts import build_figures

    assert build_figures.main(["6", "8", "--out", str(tmp_path)]) == 0
    names = sorted(p.name for p in tmp_path.iterdir())
    assert names == [
        "figura_06_makina_e_gjendjeve.png",
        "figura_06_makina_e_gjendjeve.svg",
        "figura_08_struktura_modulare.png",
        "figura_08_struktura_modulare.svg",
    ]
    assert all(p.stat().st_size > 10_000 for p in tmp_path.iterdir())


def test_the_command_rejects_an_unknown_figure(tmp_path):
    from scripts import build_figures

    with pytest.raises(SystemExit, match="999"):
        build_figures.main(["999", "--out", str(tmp_path)])
