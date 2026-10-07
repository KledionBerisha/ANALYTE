"""
Krahasimi i kryqëzuar: raporti kundrejt laboratorit.

"""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID, uuid4

from analyte.domain.enums import AnalyteStatus, CrossReferenceState, Direction, Polarity
from analyte.domain.models import AnalyteFinding, CrossReference, ReportAssertion


def build_cross_references(
    findings: tuple[AnalyteFinding, ...],
    assertions: tuple[ReportAssertion, ...],
    new_id: Callable[[], UUID] = uuid4,
) -> tuple[CrossReference, ...]:
    """Krahasimi raport ↔ laborator, një gjendje për analit.

    Pohimet pa analit (rekomandimet dhe përmendjet e termave) nuk hyjnë
    këtu: ato nuk pretendojnë asgjë për një vlerë të matur.

    Identifikuesi jepet nga fabrika e mbjellë dhe jo nga `uuid4()` i
    modelit: një identifikues i rastësishëm i vetëm mjafton që i njëjti
    seed të prodhojë dy korpuse të ndryshëm.
    """
    by_code = {f.analyte_code: f for f in findings}
    refs: list[CrossReference] = []
    mentioned: set[str] = set()

    for assertion in assertions:
        code = assertion.analyte_code
        if code is None or code in mentioned:
            continue
        mentioned.add(code)

        finding = by_code.get(code)
        if finding is None:
            refs.append(
                CrossReference(
                    id=new_id(),
                    analyte_code=code,
                    state=CrossReferenceState.MENTIONED_NOT_MEASURED,
                    assertion_id=assertion.id,
                )
            )
            continue

        refs.append(
            CrossReference(
                id=new_id(),
                analyte_code=code,
                state=(
                    CrossReferenceState.AGREEMENT
                    if _agrees(assertion, finding.status)
                    else CrossReferenceState.CONTRADICTION
                ),
                assertion_id=assertion.id,
                finding_id=finding.id,
            )
        )

    for finding in findings:
        if finding.analyte_code not in mentioned:
            refs.append(
                CrossReference(
                    id=new_id(),
                    analyte_code=finding.analyte_code,
                    state=CrossReferenceState.MEASURED_NOT_MENTIONED,
                    finding_id=finding.id,
                )
            )

    return tuple(refs)


def _agrees(assertion: ReportAssertion, status: AnalyteStatus) -> bool:
    """A përputhet pohimi me statusin e matur?

    Mohimi nuk është e kundërta e pohimit: "nuk rezulton mbi intervalin"
    përputhet me çdo status që nuk është i rritur, jo vetëm me atë të
    ulët. Prandaj polariteti trajtohet veçmas nga drejtimi.
    """
    claimed = assertion.direction
    if claimed is Direction.UNSPECIFIED:
        return True
    if assertion.polarity is Polarity.NEGATED:
        return status.direction is not claimed
    return status.direction is claimed


def _agrees(assertion: ReportAssertion, status: AnalyteStatus) -> bool:
    """A përputhet pohimi me statusin e matur?

    Mohimi nuk është e kundërta e pohimit: "nuk rezulton mbi intervalin"
    përputhet me çdo status që nuk është i rritur, jo vetëm me atë të
    ulët. Prandaj polariteti trajtohet veçmas nga drejtimi.
    """
    claimed = assertion.direction
    if claimed is Direction.UNSPECIFIED:
        return True
    if assertion.polarity is Polarity.NEGATED:
        return status.direction is not claimed
    return status.direction is claimed
