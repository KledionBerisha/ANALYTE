"""
Ruajtja e skedarëve të ngarkuar, të koduar (NFR5).

PDF-ja e pacientit është e dhënë shëndetësore dhe mban emrin e tij. Ajo
ruhet në disk e koduar me Fernet (AES-128-CBC me HMAC), me emër që është
identifikues i rastësishëm dhe jo emri i skedarit. Çelësi vjen nga
konfigurimi dhe nuk ka vlerë parazgjedhëse: një shërbim pa çelës nuk nis.

Përpunimi ka nevojë për një shteg skedari — PyMuPDF dhe Tesseract lexojnë
nga disku — prandaj `decrypted` e shkruan përmbajtjen në një skedar të
përkohshëm dhe e fshin sapo blloku mbaron, edhe kur përpunimi dështon.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from cryptography.fernet import Fernet


class EncryptedStore:
    def __init__(self, root: Path, key: str) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._fernet = Fernet(key.encode() if isinstance(key, str) else key)

    def encrypt_text(self, value: str) -> bytes:
        return self._fernet.encrypt(value.encode("utf-8"))

    def decrypt_text(self, token: bytes) -> str:
        return self._fernet.decrypt(token).decode("utf-8")

    def put(self, content: bytes) -> str:
        """Ruan përmbajtjen dhe kthen emrin e brendshëm të skedarit."""
        name = f"{uuid4().hex}.bin"
        (self.root / name).write_bytes(self._fernet.encrypt(content))
        return name

    def get(self, name: str) -> bytes:
        return self._fernet.decrypt(self._path(name).read_bytes())

    def delete(self, name: str) -> None:
        self._path(name).unlink(missing_ok=True)

    @contextmanager
    def decrypted(self, name: str, suffix: str = ".pdf") -> Iterator[Path]:
        handle, raw = tempfile.mkstemp(suffix=suffix)
        path = Path(raw)
        try:
            with os.fdopen(handle, "wb") as out:
                out.write(self.get(name))
            yield path
        finally:
            path.unlink(missing_ok=True)

    def _path(self, name: str) -> Path:
        """Emri vjen nga baza, por kontrollohet gjithsesi: një emër me
        ndarës shtegu do të dilte jashtë dosjes së ruajtjes."""
        if Path(name).name != name or not name.endswith(".bin"):
            raise ValueError("emër i pavlefshëm skedari të ruajtur")
        return self.root / name
