"""
Leximi i një korpusi të gjeneruar.

"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

from analyte.domain.models import GroundingContext

from .pipeline import DocumentInput


@dataclass(frozen=True, slots=True)
class DatasetCase:
    """Një dokument i korpusit, me të dy anët e tij të ndara."""

    document_input: DocumentInput
    truth: GroundingContext
    is_scanned: bool
    layout: str
    page_count: int

    @property
    def document_id(self) -> UUID:
        return self.document_input.document_id

    @property
    def channel(self) -> str:
        """Kanali i dokumentit. PK1 dhe PK2 raportohen veçmas për të dy."""
        return "scanned" if self.is_scanned else "digital"


@dataclass(frozen=True, slots=True)
class Dataset:
    """Korpusi bashkë me identitetin e tij.

    `version` është ajo që shkruhet në metadata e çdo rezultati. Ajo
    përmban shumën kontrolluese të tabelave burimore, prandaj dy korpuse
    me të njëjtin seed por me tabela analitesh të ndryshme nuk kanë të
    njëjtin version dhe nuk ngatërrohen dot në asnjë tabelë.
    """

    name: str
    version: str
    seed: int
    cases: tuple[DatasetCase, ...]
    manifest: dict[str, Any]

    def __len__(self) -> int:
        return len(self.cases)

    def filter(self, *, channel: str | None = None) -> Dataset:
        if channel is None:
            return self
        cases = tuple(case for case in self.cases if case.channel == channel)
        return Dataset(
            name=f"{self.name}[{channel}]",
            version=self.version,
            seed=self.seed,
            cases=cases,
            manifest=self.manifest,
        )

    def truth_by_id(self) -> dict[UUID, GroundingContext]:
        return {case.document_id: case.truth for case in self.cases}


def load(directory: Path, *, limit: int | None = None) -> Dataset:
    """Lexon korpusin nga dosja ku e shkroi gjeneruesi."""
    directory = Path(directory)
    manifest_path = directory / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"mungon manifesti te {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = manifest["documents"][: limit if limit is not None else None]

    cases = []
    for entry in entries:
        payload = json.loads((directory / entry["file"]).read_text(encoding="utf-8"))
        cases.append(
            DatasetCase(
                document_input=DocumentInput(
                    document_id=UUID(payload["document_id"]),
                    pdf_path=directory / entry["pdf"],
                ),
                truth=GroundingContext.model_validate(payload["context"]),
                is_scanned=payload["is_scanned"],
                layout=payload["lab"]["layout"],
                page_count=payload["page_count"],
            )
        )

    return Dataset(
        name=directory.name,
        version=dataset_version(manifest),
        seed=manifest["seed"],
        cases=tuple(cases),
        manifest=manifest,
    )


def dataset_version(manifest: dict[str, Any]) -> str:
    """Identiteti i shkurtër i korpusit, i shtypshëm në një qelizë tabele.

    Formati `gjenerues/seed/numër/shumë-kontrolluese` mban gjithçka që
    duhet për ta rindërtuar atë, përveç kodit — për të cilin shërben sha-ja
    e git-it e ruajtur krahas.
    """
    resources = manifest.get("resources", {})
    joined = "".join(value for _, value in sorted(resources.items()))
    fingerprint = hashlib.sha256(joined.encode()).hexdigest()[:8] if resources else "00000000"
    return f"{manifest['generator_version']}/s{manifest['seed']}/n{manifest['count']}/{fingerprint}"
