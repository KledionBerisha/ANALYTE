"""
Identifikues të përsëritshëm.

`uuid4()` merr entropi nga sistemi operativ dhe do ta prishte kërkesën
NFR3: i njëjti seed duhet të japë të njëjtin korpus bajt për bajt.
Prandaj gjeneruesi nuk e thërret kurrë atë; të gjithë identifikuesit
dalin nga i njëjti burim i mbjellë si vlerat.
"""

from __future__ import annotations

import random
from uuid import UUID


class IdFactory:
    """Prodhon UUID-4 nga një gjenerator pseudo-rastësor i mbjellë."""

    def __init__(self, rng: random.Random) -> None:
        self._rng = rng

    def __call__(self) -> UUID:
        return UUID(int=self._rng.getrandbits(128), version=4)
