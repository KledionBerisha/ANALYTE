"""
Paketa për Colab: të dhënat e klasifikuesit dhe skripti i trajnimit.

    python -m ml.colab.make_bundle

"""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "ml" / "artifacts" / "classifier_data"
SCRIPT = ROOT / "ml" / "train_classifier.py"
BUNDLE = ROOT / "ml" / "artifacts" / "classifier_bundle.zip"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ml.colab.make_bundle")
    parser.add_argument("--n", type=int, default=1500)
    parser.add_argument("--rebuild", action="store_true", help="rindërto të dhënat")
    args = parser.parse_args(argv)

    if args.rebuild or not (DATA / "meta.json").exists():
        from ml.data import build_classifier_set

        build_classifier_set.main(["--n", str(args.n), "--out", str(DATA)])

    BUNDLE.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(BUNDLE, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(SCRIPT, "train_classifier.py")
        for path in sorted(DATA.iterdir()):
            archive.write(path, f"classifier_data/{path.name}")

    print(f"shkruar {BUNDLE} ({BUNDLE.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
