"""
Struktura e paketave kontrollohet kundrejt importeve të vërteta (§5.9, Figura 8).

"""

from __future__ import annotations

from scripts.figures import layout, modules


def test_the_domain_depends_on_no_other_module():
    graph = modules.import_graph()
    assert [edge for edge in graph if edge[0] == "domain"] == []


def test_there_is_no_package_cycle():
    graph = modules.import_graph()
    nodes = sorted(modules.top_level_modules() | {n for edge in graph for n in edge})
    assert layout.strongly_connected(nodes, list(graph)) == []


def test_the_shared_result_types_live_in_the_domain_and_are_re_exported():
    from analyte.domain import processing
    from analyte.orchestration import process, states

    assert process.Delivery is processing.Delivery
    assert process.Attempt is processing.Attempt
    assert process.Explanation is processing.Explanation
    assert states.Transition is processing.Transition
