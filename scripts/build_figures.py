"""
Ndërtimi i figurave të punimit nga burimet e vërteta.

    python scripts/build_figures.py                # të gjitha
    python scripts/build_figures.py 6 11           # vetëm Figura 6 dhe 11
    python scripts/build_figures.py --out /tmp/f   # dosje tjetër

Dalja shkon te `docs/thesis/figures/`, PNG (300 dpi, për Word) dhe SVG (për
rishikim). Numrat janë ato të listës së figurave të `teza_v2.md`.

Nevojitet matplotlib: `pip install -e ".[figures]"`.
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
    from scripts.figures import erd, evaluation_chain, modules, state_machine

    return {
        6: ("figura_06_makina_e_gjendjeve", state_machine.build),
        7: ("figura_07_erd", erd.build),
        8: ("figura_08_struktura_modulare", modules.build),
        11: ("figura_11_tubacioni_i_vleresimit", evaluation_chain.build),
    }


def main(argv: list[str] | None = None) -> int:
    from scripts.figures import style

    parser = argparse.ArgumentParser(prog="build_figures")
    parser.add_argument("numbers", nargs="*", type=int, help="numrat e figurave (parazgjedhje: të gjitha)")
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
