"""
Vendosja në shtresa e një grafi të drejtuar, pa varësi nga matplotlib.

"""

from __future__ import annotations

from collections.abc import Hashable, Iterable
from typing import TypeVar

N = TypeVar("N", bound=Hashable)


def split_back_edges(
    nodes: Iterable[N], edges: Iterable[tuple[N, N]]
) -> tuple[list[tuple[N, N]], list[tuple[N, N]]]:
    """Ndan skajet në ato përpara dhe ato që mbyllin një cikël (përfshirë sythat)."""
    nodes = list(nodes)
    out: dict[N, list[N]] = {n: [] for n in nodes}
    for a, b in edges:
        out[a].append(b)
    state: dict[N, int] = {}  # 1 = në rrugë, 2 = mbaruar
    back: set[tuple[N, N]] = set()

    def visit(node: N) -> None:
        state[node] = 1
        for target in out[node]:
            if state.get(target) == 1:
                back.add((node, target))
            elif target not in state:
                visit(target)
        state[node] = 2

    for node in nodes:
        if node not in state:
            visit(node)
    forward = [e for e in edges if e not in back]
    return forward, [e for e in edges if e in back]


def layers(nodes: Iterable[N], edges: Iterable[tuple[N, N]]) -> dict[N, int]:
    """Numri i shtresës për secilën nyje; 0 për ato pa skaj hyrës."""
    nodes = list(nodes)
    forward, _ = split_back_edges(nodes, list(edges))
    incoming: dict[N, list[N]] = {n: [] for n in nodes}
    for a, b in forward:
        incoming[b].append(a)
    depth: dict[N, int] = {}

    def of(node: N) -> int:
        if node not in depth:
            depth[node] = 1 + max((of(p) for p in incoming[node]), default=-1)
        return depth[node]

    for node in nodes:
        of(node)
    return depth


def order_within_layers(
    layer_of: dict[N, int], edges: Iterable[tuple[N, N]], nodes: list[N]
) -> dict[int, list[N]]:
    """Renditja brenda shtresës me mesataren e fqinjëve të shtresës së mëparshme,
    që skajet të kalojnë pak mbi njëri-tjetrin. Renditja fillestare është ajo e
    `nodes`, prandaj rezultati është i përsëritshëm."""
    columns: dict[int, list[N]] = {}
    for node in nodes:
        columns.setdefault(layer_of[node], []).append(node)
    parents: dict[N, list[N]] = {n: [] for n in nodes}
    for a, b in edges:
        if layer_of[a] < layer_of[b]:
            parents[b].append(a)
    position: dict[N, float] = {}
    for depth in sorted(columns):
        column = columns[depth]
        if depth > 0:
            column.sort(
                key=lambda n: (
                    sum(position[p] for p in parents[n]) / len(parents[n])
                    if parents[n]
                    else float("inf")
                )
            )
        for index, node in enumerate(column):
            position[node] = float(index)
    return columns


def strongly_connected(nodes: Iterable[N], edges: Iterable[tuple[N, N]]) -> list[list[N]]:
    """Grupet e nyjeve që varen rrethore nga njëra-tjetra (Tarjan); vetëm ato me më shumë se një."""
    nodes = list(nodes)
    out: dict[N, list[N]] = {n: [] for n in nodes}
    for a, b in edges:
        out[a].append(b)
    index: dict[N, int] = {}
    low: dict[N, int] = {}
    on_stack: set[N] = set()
    stack: list[N] = []
    found: list[list[N]] = []
    counter = 0

    def visit(node: N) -> None:
        nonlocal counter
        index[node] = low[node] = counter
        counter += 1
        stack.append(node)
        on_stack.add(node)
        for target in out[node]:
            if target not in index:
                visit(target)
                low[node] = min(low[node], low[target])
            elif target in on_stack:
                low[node] = min(low[node], index[target])
        if low[node] == index[node]:
            group = []
            while True:
                member = stack.pop()
                on_stack.discard(member)
                group.append(member)
                if member == node:
                    break
            if len(group) > 1:
                found.append(group)

    for node in nodes:
        if node not in index:
            visit(node)
    return found
