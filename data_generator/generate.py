"""
Pika hyrëse e gjeneruesit të korpusit sintetik.

    python -m data_generator.generate --seed 42 --n 500 --out data/v1

Dy ekzekutime me të njëjtin seed japin bajt për bajt të njëjtat skedarë.
Kjo nuk është hollësi zbatimi por kërkesë e vlerësimit (NFR3): një
rezultat eksperimenti ka kuptim vetëm nëse korpusi mbi të cilin u mat
mund të rindërtohet.

Prandaj:
  - asnjë vulë kohore dhe asnjë identifikues i rastësishëm nuk hyn në dalje,
  - çdo dokument merr farën e vet të prejardhur nga seed-i dhe indeksi i tij,
    çka e bën dokumentin i-të të pavarur nga numri i përgjithshëm i
    dokumenteve dhe gjenerimin e ndashëm në procese,
  - manifesti mban shumat kontrolluese të skedarëve burimorë: nëse tabela e
    analiteve ndryshon, kjo duket menjëherë dhe korpusi nuk ngatërrohet me
    një të mëparshëm.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any

from analyte.catalog import RESOURCES_DIR
from .degrade import degrade_pdf, sample_profile
from .ground_truth import SCANNED_SHARE, DocumentTruth, build_document
from .ids import IdFactory
from .render import render_document

GENERATOR_VERSION = "gen-1.0"

RESOURCE_FILES: tuple[str, ...] = (
    "analytes.csv",
    "analytes_extra.csv",
    "units.csv",
    "terminology.csv",
)


def document_seed(seed: int, index: int) -> str:
    """Fara e një dokumenti të vetëm.

    Varet vetëm nga seed-i dhe indeksi, kurrë nga gjendja e mëparshme e
    gjeneratorit. Dokumenti 17 është i njëjti pavarësisht nëse u kërkuan
    20 apo 5000 dokumente.
    """
    return f"analyte/{GENERATOR_VERSION}/{seed}/{index}"


def build_corpus(
    seed: int, count: int, scanned_share: float = SCANNED_SHARE
) -> list[DocumentTruth]:
    documents = []
    for index in range(count):
        rng = random.Random(document_seed(seed, index))
        documents.append(
            build_document(rng, IdFactory(rng), scanned_share=scanned_share)
        )
    return documents


def render(document: DocumentTruth, seed: int, index: int) -> tuple[bytes, DocumentTruth]:
    """Vizaton dokumentin dhe kthen PDF-në bashkë me të vërtetën e plotësuar.

    Kutitë kufizuese dhe animi i skanimit dihen vetëm pasi faqja të jetë
    vizatuar, prandaj e vërteta bazë përfundon këtu dhe jo te
    `build_document`. Fara e skanerit rrjedh nga e njëjta farë dokumenti:
    dy ekzekutime japin të njëjtën kopje të prishur.
    """
    rng = random.Random(document_seed(seed, index) + "/scan")
    pdf, boxes = render_document(document)
    if document.is_scanned:
        profile = sample_profile(rng)
        pdf, boxes = degrade_pdf(pdf, boxes, profile, rng.getrandbits(63))
    return pdf, document.with_boxes(boxes)


def summarize(documents: list[DocumentTruth]) -> dict[str, Any]:
    """Përbërja e korpusit — burimi i tabelës përshkruese të Kapitullit 6."""
    statuses: Counter[str] = Counter()
    sources: Counter[str] = Counter()
    states: Counter[str] = Counter()
    kinds: Counter[str] = Counter()
    certainties: Counter[str] = Counter()
    polarities: Counter[str] = Counter()
    findings = assertions = unexplained = 0
    with_critical = 0

    for document in documents:
        context = document.context
        findings += len(context.findings)
        assertions += len(context.assertions)
        unexplained += len(context.unexplained_terms)
        if context.critical_findings():
            with_critical += 1
        for finding in context.findings:
            statuses[finding.status.value] += 1
            sources[finding.ref_source.value] += 1
        for assertion in context.assertions:
            kinds[assertion.kind.value] += 1
            certainties[assertion.certainty.value] += 1
            polarities[assertion.polarity.value] += 1
        for ref in context.cross_refs:
            states[ref.state.value] += 1

    return {
        "documents": len(documents),
        "findings": findings,
        "assertions": assertions,
        "unexplained_terms": unexplained,
        "documents_with_critical_value": with_critical,
        "scanned_documents": sum(1 for d in documents if d.is_scanned),
        "pages": sum(d.page_count for d in documents),
        "status": dict(sorted(statuses.items())),
        "reference_source": dict(sorted(sources.items())),
        "cross_reference_state": dict(sorted(states.items())),
        "assertion_kind": dict(sorted(kinds.items())),
        "certainty": dict(sorted(certainties.items())),
        "polarity": dict(sorted(polarities.items())),
    }


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _dump(payload: Any) -> bytes:
    """JSON i qëndrueshëm: gjithmonë të njëjtët bajt për të njëjtën përmbajtje."""
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False)
    return (text + "\n").encode("utf-8")


def write_corpus(
    documents: list[DocumentTruth], seed: int, out_dir: Path, scanned_share: float = SCANNED_SHARE
) -> tuple[Path, list[DocumentTruth]]:
    """Vizaton dhe shkruan korpusin; kthen manifestin dhe të vërtetën e plotësuar."""
    docs_dir = out_dir / "documents"
    docs_dir.mkdir(parents=True, exist_ok=True)

    entries = []
    rendered: list[DocumentTruth] = []
    for index, document in enumerate(documents):
        pdf, document = render(document, seed, index)
        rendered.append(document)

        stem = f"doc_{index:05d}"
        payload = _dump(document.to_json_dict())
        (docs_dir / f"{stem}.json").write_bytes(payload)
        (docs_dir / f"{stem}.pdf").write_bytes(pdf)
        entries.append(
            {
                "index": index,
                "file": f"documents/{stem}.json",
                "pdf": f"documents/{stem}.pdf",
                "document_id": str(document.document_id),
                "seed": document_seed(seed, index),
                "is_scanned": document.is_scanned,
                "sha256": _sha256(payload),
                "pdf_sha256": _sha256(pdf),
            }
        )
    documents = rendered

    manifest = {
        "generator_version": GENERATOR_VERSION,
        "seed": seed,
        "count": len(documents),
        "scanned_share": scanned_share,
        "resources": {
            name: _sha256((RESOURCES_DIR / name).read_bytes()) for name in RESOURCE_FILES
        },
        "summary": summarize(documents),
        "documents": entries,
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_bytes(_dump(manifest))
    return manifest_path, documents


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="data_generator.generate",
        description="Gjeneron korpusin sintetik me të vërtetën bazë.",
    )
    parser.add_argument("--seed", type=int, default=42, help="fara e korpusit")
    parser.add_argument("--n", type=int, default=500, help="numri i dokumenteve")
    parser.add_argument("--out", type=Path, default=Path("data/v1"), help="dosja e daljes")
    parser.add_argument(
        "--scanned-share",
        type=float,
        default=SCANNED_SHARE,
        help="përpjesa e dokumenteve që kalojnë nëpër simulimin e skanimit",
    )
    args = parser.parse_args(argv)

    if args.n < 1:
        parser.error("--n duhet të jetë të paktën 1")
    if not 0.0 <= args.scanned_share <= 1.0:
        parser.error("--scanned-share duhet të jetë ndërmjet 0 dhe 1")

    documents = build_corpus(args.seed, args.n, args.scanned_share)
    manifest_path, documents = write_corpus(documents, args.seed, args.out)

    summary = summarize(documents)
    print(f"U shkruan {summary['documents']} dokumente në {args.out}")
    print(f"  gjetje: {summary['findings']}, pohime: {summary['assertions']}")
    print(f"  faqe: {summary['pages']}, të skanuara: {summary['scanned_documents']}")
    print(f"  dokumente me vlerë kritike: {summary['documents_with_critical_value']}")
    print(f"  manifesti: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
