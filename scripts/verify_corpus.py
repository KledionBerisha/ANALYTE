"""
Kontrollon që tabelat burimore në `resources/` janë bajt për bajt ato që u përdorën për të ndërtuar korpusin.

    python scripts/verify_corpus.py                      # data/v1
    python scripts/verify_corpus.py --dataset data/v1

"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compare(manifest: dict[str, str], resources: Path) -> list[dict[str, str]]:
    """Një rresht për secilën tabelë: `match`, `line_endings_only`, `changed_or_mixed_endings`, `changed` ose `missing`."""
    report = []
    for name, expected in sorted(manifest.items()):
        path = resources / name
        if not path.exists():
            report.append({"file": name, "status": "missing"})
            continue
        raw = path.read_bytes()
        if digest(raw) == expected:
            report.append({"file": name, "status": "match"})
            continue
        # A del ndryshimi vetëm nga mbarimet e rreshtave? Provohen të dyja trajtat e mundshme të origjinalit.
        lf = raw.replace(b"\r\n", b"\n")
        crlf = lf.replace(b"\n", b"\r\n")
        if expected in {digest(lf), digest(crlf)}:
            status = "line_endings_only"
        elif raw.count(b"\r\n") and raw.count(b"\n") > raw.count(b"\r\n"):
            # Mbarime të përziera (CRLF dhe LF në të njëjtin skedar): pa bajtet origjinale nuk dallohet nga ndryshimi i përmbajtjes.
            status = "changed_or_mixed_endings"
        else:
            status = "changed"
        report.append({"file": name, "status": status})
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--dataset", type=Path, default=ROOT / "data" / "v1")
    parser.add_argument("--resources", type=Path, default=ROOT / "resources")
    args = parser.parse_args(argv)

    manifest_path = args.dataset / "manifest.json"
    if not manifest_path.exists():
        print(f"mungon {manifest_path}", file=sys.stderr)
        return 2
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))["resources"]
    report = compare(manifest, args.resources)
    for row in report:
        print(f"{row['status']:>18}  {row['file']}")
    bad = [r for r in report if r["status"] != "match"]
    if bad:
        print(
            f"\n{len(bad)} nga {len(report)} tabela nuk përputhen me manifestin. "
            "`line_endings_only` do të thotë se përmbajtja është e njëjtë dhe ndryshojnë vetëm mbarimet e rreshtave "
            "(shih `.gitattributes`); `changed_or_mixed_endings` ndodh kur skedari ka mbarime të përziera dhe nuk dallohet nga ndryshimi i përmbajtjes; `changed` do të thotë se tabela ndryshoi pas ndërtimit të korpusit.",
            file=sys.stderr,
        )
        return 1
    print(f"\nTë {len(report)} tabelat përputhen me manifestin e {args.dataset}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
