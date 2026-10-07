"""
Ndërtimi i figurave të punimit nga burimet e vërteta.

    python scripts/build_figures.py                # të gjitha
    python scripts/build_figures.py 6 11           # vetëm Figura 6 dhe 11
    python scripts/build_figures.py --out /tmp/f   # dosje tjetër
    
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "src"))
sys.path.insert(0, str(ROOT))

DEFAULT_OUT = ROOT / "docs" / "thesis" / "figures"


def _figures():
    from scripts.figures import concepts, erd, evaluation_chain, modules, results, state_machine

    return {
        1: ("figura_01_fazat", concepts.figure_01),
        2: ("figura_02_arkitektura", concepts.figure_02),
        3: ("figura_03_dega_laboratorike", concepts.figure_03),
        4: ("figura_04_dega_e_raportit", concepts.figure_04),
        5: ("figura_05_shtresa_e_verifikimit", concepts.figure_05),
        6: ("figura_06_makina_e_gjendjeve", state_machine.build),
        7: ("figura_07_erd", erd.build),
        8: ("figura_08_struktura_modulare", modules.build),
        9: ("figura_09_korpusi_sintetik", concepts.figure_09),
        10: ("figura_10_korpusi_i_korruptuar", concepts.figure_10),
        11: ("figura_11_tubacioni_i_vleresimit", evaluation_chain.build),
        18: ("figura_18_ablacioni", results.figure_18),
        19: ("figura_19_matrica_e_statusit", results.figure_19),
        20: ("figura_20_matricat_e_detektoreve", results.figure_20),
        21: ("figura_21_llojet_e_shkeljeve", results.figure_21),
    }


def main(argv: list[str] | None = None) -> int:
    from scripts.figures import style

    parser = argparse.ArgumentParser(prog="build_figures")
    parser.add_argument(
        "numbers", nargs="*", type=int, help="numrat e figurave (parazgjedhje: të gjitha)"
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    available = _figures()
    unknown = [n for n in args.numbers if n not in available]
    if unknown:
        raise SystemExit(f"figura të panjohura: {unknown}; njihen: {sorted(available)}")

    for number in args.numbers or sorted(available):
        name, build = available[number]
        fig, *_ = build()
        for path in style.save(fig, args.out, name):
            print(f"Figura {number}: {path.relative_to(ROOT) if ROOT in path.parents else path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
