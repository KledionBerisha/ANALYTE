"""
Figurat e ndërtuara nga kodi.

"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.figures import layout

# Vendosja në shtresa (pa matplotlib)


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


# Figurat

pytest.importorskip("matplotlib")

from analyte.domain.enums import ProcessingState
from analyte.orchestration.states import TRANSITIONS
from analyte.persistence.tables import Base
from scripts.figures import erd, evaluation_chain, modules, state_machine


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


# Figura 11


def _experiment(runnable: bool):
    return evaluation_chain.registry.Experiment(
        "EX",
        "t",
        "—",
        "d",
        "m",
        "PK",
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
            {
                "metadata": {
                    "code": {"git_sha": "abc", "working_tree_dirty": True},
                    "dataset": {"version": "v"},
                }
            },
            "pa commit",
        ),
        (
            {
                "metadata": {
                    "code": {"git_sha": "abc", "working_tree_dirty": False},
                    "dataset": {"version": "v"},
                }
            },
            "e plotë",
        ),
    ],
)
def test_trace_says_how_traceable_a_measurement_is(result, expected):
    assert evaluation_chain.trace_of(result) == expected


def test_provenance_fields_are_read_from_a_real_result():
    fields = evaluation_chain.provenance_fields(
        {
            "E2": {
                "metadata": {
                    "experiment_id": "E2",
                    "dataset": {"seed": 1, "version": "v"},
                    "created_at": "x",
                }
            }
        }
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
        evaluation_chain.MEASURED,
        evaluation_chain.READY,
        evaluation_chain.BLOCKED,
    }
    evaluation_chain.style.plt.close(fig)


def test_every_blocked_experiment_says_what_it_waits_for():
    for experiment in evaluation_chain.registry.EXPERIMENTS:
        if not experiment.runnable:
            assert experiment.waiting_for or experiment.pending_reason


# Komanda


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


# Figurat 18–21: numrat vijnë nga skedarët e rezultateve


def _results_module():
    pytest.importorskip("matplotlib")
    from scripts.figures import results

    return results


def test_ablation_reads_the_four_conditions_from_the_result_files():
    results = _results_module()
    rows = results.ablation()
    assert [r["letter"] for r in rows] == ["A", "B", "C", "D"]
    assert [r["experiment"] for r in rows] == ["E6", "E7", "E8", "E9"]
    # kushti C nuk ka asnjë shkelje te përdoruesi; vetëm ai mban kufirin e sipërm të rregullës së tre
    assert rows[2]["rate"] == 0 and rows[2]["upper_bound"] is not None
    assert all(r["upper_bound"] is None for r in rows if r["experiment"] != "E8")
    # kampioni është i njëjti në të katër kushtet; shkeljet ulen nga A në B
    assert rows[0]["rate"] > rows[1]["rate"] > rows[3]["rate"] > rows[2]["rate"]


def test_status_matrix_adds_up_to_the_values_E3_matched():
    results = _results_module()
    classes, counts = results.status_matrix()
    assert classes == results.STATUS_ORDER
    per_class = results._load(results.RESULTS / "E3" / "result.json")["metrics"]["overall"][
        "per_class"
    ]
    assert [sum(row) for row in counts] == [per_class[c]["support"] for c in classes]
    assert (
        sum(map(sum, counts))
        == results._load(results.RESULTS / "E3" / "result.json")["metrics"]["overall"]["total"]
    )


def test_present_classes_keeps_a_fixed_order_and_refuses_unknown_ones():
    results = _results_module()
    matrix = {"polarity_flip->clean": 1, "clean->clean": 2, "hedge_removed->hedge_removed": 3}
    assert results.present_classes(matrix) == ["clean", "polarity_flip", "hedge_removed"]
    with pytest.raises(results.MissingResult, match="klasa pa vend"):
        results.present_classes({"clean->invented_type": 1})


def test_confusion_counts_fills_missing_cells_with_zero():
    results = _results_module()
    counts = results.confusion_counts({"a->a": 2, "a->b": 1}, ["a", "b"])
    assert counts == [[2, 1], [0, 0]]


def test_shares_are_percentages_of_the_condition_total():
    results = _results_module()
    shares = results.shares({"x": 1, "y": 3, "z": 0})
    assert shares == {"x": 25.0, "y": 75.0, "z": 0.0}
    assert results.shares({"x": 0}) == {}


def test_a_missing_result_stops_the_figure_with_a_message(tmp_path):
    results = _results_module()
    with pytest.raises(results.MissingResult, match="mungon"):
        results.ablation(tmp_path)


def test_detector_figures_read_the_same_numbers_as_chapter_6():
    results = _results_module()
    data = results.detectors()
    # vlerat e Tabelës 12: rregullat 0.993 / 0.795, klasifikuesi 0.385 / 0.015, Sonnet 1.000 / 1.000
    assert round(data["Rregullat"]["synthetic"]["macro_f1"], 3) == 0.993
    assert round(data["Rregullat"]["natural"]["macro_f1"], 3) == 0.795
    assert round(data["Klasifikuesi XLM-R"]["synthetic"]["macro_f1"], 3) == 0.385
    assert round(data["Klasifikuesi XLM-R"]["natural"]["macro_f1"], 3) == 0.015
    assert data["Gjykatësi Claude Sonnet"]["natural"]["macro_f1"] == 1.0


# Figurat 1–5, 9, 10: ç'është shkruar në kuti vjen nga burimi


def _concepts_module():
    pytest.importorskip("matplotlib")
    from scripts.figures import concepts

    return concepts


def _texts(fig) -> str:
    """Çdo tekst i vizatuar në figurë, si një varg."""
    return "\n".join(t.get_text() for ax in fig.axes for t in ax.texts)


def test_rule_ranges_come_from_the_rule_catalogue():
    concepts = _concepts_module()
    assert concepts.rule_ranges() == {"A": "R1–R4", "B": "R5–R9"}


def test_figure_5_names_the_rules_and_the_attempt_limit_from_the_code():
    concepts = _concepts_module()
    fig, ranges = concepts.figure_05()
    text = _texts(fig)
    assert ranges["A"] in text and ranges["B"] in text
    assert f"pas {concepts.MAX_GENERATION_ATTEMPTS} përpjekjesh" in text


def test_figure_4_draws_every_cross_reference_state_and_no_other():
    concepts = _concepts_module()
    from analyte.domain.enums import CrossReferenceState

    fig, info = concepts.figure_04()
    assert len(info["states"]) == len(CrossReferenceState)
    assert set(concepts.CROSS_LABELS) == set(CrossReferenceState)
    text = _texts(fig)
    assert all(label in text for label in info["states"])


def test_figure_3_and_4_quote_the_real_sizes_of_the_tables():
    concepts = _concepts_module()
    from analyte.catalog import load_patterns, load_terminology

    text3 = _texts(concepts.figure_03()[0])
    text4 = _texts(concepts.figure_04()[0])
    assert f"{len(load_patterns())} rregulla" in text3
    assert f"({len(load_terminology())} terma)" in text4


def test_figure_9_quotes_the_number_of_analytes_in_the_catalogue():
    concepts = _concepts_module()
    from analyte.catalog import load_analytes

    fig, info = concepts.figure_09()
    assert info["analytes"] == len(load_analytes())
    assert f"{info['analytes']} analite" in _texts(fig)


def test_figure_10_draws_one_box_per_corruptor_and_the_real_split():
    concepts = _concepts_module()
    from ml.data.build_corruption_set import CORRUPTORS, SPLIT_WEIGHTS

    fig, info = concepts.figure_10()
    assert len(info["defects"]) == len(CORRUPTORS) == 7
    assert abs(sum(SPLIT_WEIGHTS) - 1.0) < 1e-9
    text = "\n".join(t.get_text() for t in fig.axes[0].texts)
    for defect in info["defects"]:
        assert defect in text
    assert "train 70%" in text and "val 15%" in text and "test 15%" in text


def test_corruption_split_really_is_the_one_the_figure_states():
    """Figura 10 thotë 70/15/15; `_split_for` duhet ta bëjë këtë mbi çdo 20 dokumente."""
    pytest.importorskip("matplotlib")
    from ml.data.build_corruption_set import _split_for

    counts = {"train": 0, "val": 0, "test": 0}
    for index in range(200):
        counts[_split_for(index)] += 1
    assert counts == {"train": 140, "val": 30, "test": 30}


def test_figure_11_accepts_results_whose_metadata_has_no_pipeline(monkeypatch):
    """E10 dhe E11 shkruajnë metadata me kodin dhe të dhënat, por pa `pipeline` (ato s'kalojnë nga harness-i)."""
    pytest.importorskip("matplotlib")
    from scripts.figures import evaluation_chain as chain

    results = {
        "E10": {
            "metadata": {
                "code": {"git_sha": "a" * 40, "working_tree_dirty": False},
                "dataset": {"version": "v", "seed": 1},
            }
        },
        "E3": {
            "metadata": {
                "pipeline": {"name": "grounding"},
                "code": {"git_sha": "a" * 40, "working_tree_dirty": False},
                "dataset": {"version": "v", "seed": 1},
            }
        },
    }
    monkeypatch.setattr(chain, "load_results", lambda *a, **k: results)
    fig, *_ = chain.build()
    assert "grounding" in "\n".join(t.get_text() for ax in fig.axes for t in ax.texts)


def test_results_of_the_language_model_runs_count_as_measured_without_replacing_template_ones(
    tmp_path,
):
    """E4, E6 dhe E12 kanë rezultat vetëm te `llm/`; E7 ka të dyja dhe mban atë me shabllon."""
    for relative, marker in (
        ("E7/result.json", "shabllon"),
        ("llm/E7/result.json", "model"),
        ("llm/E4/result.json", "model"),
        ("llm/E12/result.json", "model"),
        ("llm/E12_haiku/result.json", "kontroll"),
        ("llm/AUDIT_E8/result.json", "audit"),  # nuk është eksperiment i regjistrit
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"marker": "%s"}' % marker, encoding="utf-8")
    found = evaluation_chain.load_results(tmp_path)
    assert sorted(found) == ["E12", "E4", "E7"]
    assert found["E7"]["marker"] == "shabllon" and found["E12"]["marker"] == "model"
