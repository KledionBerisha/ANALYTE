"""
Identifikues të përsëritshëm.

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
