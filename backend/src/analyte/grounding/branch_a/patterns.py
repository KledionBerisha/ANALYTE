"""
Zbulimi i kombinimeve ndërmjet analiteve.

Disa rezultate thonë më shumë bashkë se veç e veç. Rregullat këtu janë të
shkruara me dorë në `resources/patterns.csv`, një rresht për rregull, dhe
secili rresht mban burimin e vet — ashtu si tabela terminologjike, dhe
për të njëjtën arsye: rregulli pa burim është pohim mjekësor i
paverifikuar.

**Rregullat nuk emërtojnë gjendje.** Ato thonë se një kombinim meriton
vlerësim profesional, jo çfarë është ai. Emri i kombinimit është diagnozë
dhe SP1 e ndalon atë pavarësisht nga burimi.

**Vlera pa interval nuk merr pjesë.** Statusi `UNINTERPRETABLE` nuk ka
drejtim, prandaj asnjë kusht nuk plotësohet prej tij. Një rregull që
ndizet mbi një vlerë që sistemi refuzoi ta interpretojë do ta
interpretonte atë tërthorazi — pikërisht ajo që SP5 ndalon.

**Analiti i dyfishtë nuk zgjidhet me hamendje.** Nëse i njëjti analit
shfaqet dy herë në dokument — dy matje, dy data — rregulli që e kërkon
nuk ndizet. Zgjedhja e njërës do të ishte vendim klinik që sistemi nuk
ka mjete ta marrë.
"""

from __future__ import annotations

from collections import Counter

from analyte.catalog import Pattern, load_patterns
from analyte.domain.models import AnalyteFinding, PatternObservation


def detect(
    findings: tuple[AnalyteFinding, ...],
    patterns: tuple[Pattern, ...] | None = None,
) -> tuple[PatternObservation, ...]:
    """Kombinimet e plotësuara nga gjetjet e një dokumenti, në rendin e tabelës."""
    patterns = load_patterns() if patterns is None else patterns
    counts = Counter(f.analyte_code for f in findings)
    by_code = {f.analyte_code: f for f in findings if counts[f.analyte_code] == 1}

    observed: list[PatternObservation] = []
    for pattern in patterns:
        matched = [
            by_code[code]
            for code, direction in pattern.conditions
            if code in by_code and by_code[code].status.direction.value == direction
        ]
        if len(matched) == len(pattern.conditions):
            observed.append(
                PatternObservation(
                    pattern_id=pattern.pattern_id,
                    finding_ids=tuple(f.id for f in matched),
                    source_ref=pattern.source_ref,
                )
            )
    return tuple(observed)
