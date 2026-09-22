"""
Matrica e eksperimenteve (§8.1 e specifikimit).

Regjistri ekziston që numrat e Kapitullit 6 të kenë secili një adresë. Një
qelizë e tabelës që nuk u mat nuk fshihet dhe nuk lihet bosh: ajo shtypet
`[TO BE MEASURED]`, sepse ndryshimi mes "nuk u mat ende" dhe "doli zero"
është ndryshimi mes një boshllëku të njohur dhe një gabimi të fshehur.

`status` thotë pse një eksperiment nuk mund të ekzekutohet ende. Kjo e bën
listën e mbetur të punës të lexueshme nga vetë harness-i në vend që të
mbahet mend.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

RUNNABLE = "runnable"
NEEDS_CORRUPTION_SET = "needs_corruption_set"
NEEDS_REAL_DATA = "needs_real_data"
NEEDS_USER_STUDY = "needs_user_study"
NEEDS_SECOND_PROVIDER = "needs_second_provider"

PENDING_REASONS: dict[str, str] = {
    NEEDS_CORRUPTION_SET: "korpusi i korruptuar ndërtohet në Fazën 7",
    NEEDS_REAL_DATA: "varet nga miratimi etik dhe nga dokumentet reale",
    NEEDS_USER_STUDY: "kërkon pjesëmarrës njerëz (Faza 10)",
    NEEDS_SECOND_PROVIDER: "kërkon një model të dytë gjuhësor",
}


@dataclass(frozen=True, slots=True)
class Experiment:
    """Një rresht i matricës së eksperimenteve."""

    id: str
    title: str
    condition: str
    dataset: str
    metric: str
    """Cili modul metrikash e llogarit: emri nën `evaluation.metrics`."""
    answers: str
    """Cila pyetje kërkimore — PK1..PK7 — merr përgjigje prej tij."""
    channel: str | None = None
    """Kufizimi te kanali dixhital ose i skanuar, kur eksperimenti e kërkon."""
    status: str = RUNNABLE

    @property
    def runnable(self) -> bool:
        return self.status == RUNNABLE

    @property
    def pending_reason(self) -> str | None:
        return None if self.runnable else PENDING_REASONS[self.status]

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "condition": self.condition,
            "dataset": self.dataset,
            "metric": self.metric,
            "answers": self.answers,
            "channel": self.channel,
            "status": self.status,
        }


EXPERIMENTS: tuple[Experiment, ...] = (
    Experiment("E1", "Saktësia e nxjerrjes", "dixhital", "synthetic-v1",
               "extraction", "PK1", channel="digital"),
    Experiment("E2", "Saktësia e nxjerrjes", "i skanuar", "synthetic-v1",
               "extraction", "PK1", channel="scanned"),
    Experiment("E3", "Klasifikimi i statusit", "—", "synthetic-v1",
               "classification", "PK2"),
    Experiment("E4", "Besnikëria e thjeshtimit", "—", "synthetic-v1",
               "prose", "PK3"),
    Experiment("E5", "Krahasimi i kryqëzuar", "—", "synthetic-v1",
               "crossref", "PK4"),
    Experiment("E6", "Ablacion A", "pa bazim", "synthetic-v1",
               "violations", "PK5"),
    Experiment("E7", "Ablacion B", "vetëm bazim", "synthetic-v1",
               "violations", "PK5"),
    Experiment("E8", "Ablacion C", "+ verifikim me rregulla", "synthetic-v1",
               "violations", "PK5"),
    Experiment("E9", "Ablacion D", "+ klasifikues", "synthetic-v1",
               "violations", "PK5"),
    Experiment("E10", "Zbuluesi: rregulla", "—", "corruption-test",
               "detector", "PK6", status=NEEDS_CORRUPTION_SET),
    Experiment("E11", "Zbuluesi: klasifikues", "—", "corruption-test",
               "detector", "PK6", status=NEEDS_CORRUPTION_SET),
    Experiment("E12", "Zbuluesi: gjykatës LLM", "—", "corruption-test",
               "detector", "PK6", status=NEEDS_CORRUPTION_SET),
    Experiment("E13", "Vlefshmëria mbi të dhëna reale", "—", "real-subset",
               "extraction", "vlefshmëri e jashtme", status=NEEDS_REAL_DATA),
    Experiment("E14", "Kuptueshmëria te përdoruesit", "me / pa sistem", "n=12-20",
               "comprehension", "PK7", status=NEEDS_USER_STUDY),
    Experiment("E15", "Model lokal kundrejt në re", "opsional", "synthetic-v1",
               "violations", "diskutim", status=NEEDS_SECOND_PROVIDER),
)

BY_ID: dict[str, Experiment] = {e.id: e for e in EXPERIMENTS}


def get(experiment_id: str) -> Experiment:
    try:
        return BY_ID[experiment_id]
    except KeyError:
        known = ", ".join(BY_ID)
        raise KeyError(f"eksperiment i panjohur '{experiment_id}'; njihen: {known}") from None


def runnable() -> tuple[Experiment, ...]:
    return tuple(e for e in EXPERIMENTS if e.runnable)
