"""
Këshillat me burim për gjetjet jashtë intervalit (ADR 0023).

Pacienti kërkon të dijë jo vetëm se një vlerë është jashtë intervalit, por
edhe çfarë mund të bëjë. Sistemi nuk e lejon modelin gjuhësor ta shkruajë
këtë: një këshillë e shpikur është pohim mjekësor pa burim, dhe SP1–SP3 e
ndalojnë. Këshilla vjen vetëm nga `resources/advice.csv`, një rresht për
çdo analit dhe drejtim, me burimin e vet si te tabela terminologjike, dhe
shtypet fjalë për fjalë.

**Rreshti pa fjali ose pa burim të lexuar nuk hyn në kontekst.** Tabela
dërgohet me rreshta bosh, që autori t'i plotësojë nga burime që i ka hapur;
një rresht i paplotësuar nuk i shfaqet kurrë pacientit.

**Vlera pa interval nuk merr këshillë.** Statusi `UNINTERPRETABLE` nuk ka
drejtim (SP5), dhe një këshillë mbi të do ta interpretonte tërthorazi.
Vlera normale nuk merr këshillë: nuk ka çfarë të ndryshojë.

**Analiti i dyfishtë nuk zgjidhet me hamendje**, si te kombinimet: dy
matje të të njëjtit analit me drejtime të ndryshme do të kërkonin një
vendim klinik që sistemi nuk e merr.
"""

from __future__ import annotations

from collections import Counter

from analyte.catalog import Advice, advice_by_key
from analyte.domain.enums import Direction
from analyte.domain.models import AdviceEntry, AnalyteFinding

ADVISED_DIRECTIONS = (Direction.INCREASED, Direction.DECREASED)


def attach(
    findings: tuple[AnalyteFinding, ...],
    advice: tuple[Advice, ...] | None = None,
) -> tuple[AdviceEntry, ...]:
    """Këshillat e tabelës për gjetjet e një dokumenti, në rendin e gjetjeve."""
    table = advice_by_key() if advice is None else {(a.loinc_code, a.direction): a for a in advice}
    counts = Counter(f.analyte_code for f in findings)

    out: list[AdviceEntry] = []
    for finding in findings:
        direction = finding.status.direction
        if direction not in ADVISED_DIRECTIONS or counts[finding.analyte_code] != 1:
            continue
        row = table.get((finding.analyte_code, direction.value))
        if row is None or not row.is_filled:
            continue
        out.append(
            AdviceEntry(
                finding_id=finding.id,
                analyte_code=finding.analyte_code,
                direction=direction,
                advice_sq=row.advice_sq,
                source_ref=row.source_ref,
            )
        )
    return tuple(out)
