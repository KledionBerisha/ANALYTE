"""
Klasifikuesi i fjalive në shtresën e verifikimit (ADR 0009).

Rregullat vijnë të parat dhe janë të vetmet që ndalin daljen pa kusht.
Klasifikuesi gjykon vetëm fjalitë ku rregullat nuk gjetën asgjë, dhe çdo
shkelje e tij mban `detected_by=CLASSIFIER` dhe një `confidence` — ajo që
rregullat nuk e kanë dhe modeli i domenit ua ndalon.

Moduli nuk varet nga torch. Parashikuesi është protokoll; zbatimi me
transformers ngarkohet vetëm kur kërkohet, që shërbimi dhe testet të
punojnë pa të.

**Serializimi i kontekstit jeton këtu** dhe jo te skripti i trajnimit:
modeli i trajnuar me hyrjen `context` pret saktësisht këtë varg, dhe një
kopje e dytë do të largohej nga e para pa u vënë re.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Protocol

from analyte.domain.enums import AnalyteStatus, DetectedBy, ViolationType
from analyte.domain.models import GroundingContext, VerificationResult, Violation

from .base import sentences
from .pipeline import verify

CLEAN = "clean"

STATUS_WORD = {
    AnalyteStatus.CRITICAL_LOW: "shumë e ulët",
    AnalyteStatus.LOW: "e ulët",
    AnalyteStatus.NORMAL: "normale",
    AnalyteStatus.HIGH: "e lartë",
    AnalyteStatus.CRITICAL_HIGH: "shumë e lartë",
    AnalyteStatus.UNINTERPRETABLE: "pa interval",
}


def serialize_context(context: GroundingContext) -> str:
    """Konteksti si tekst i shkurtër për hyrjen `context` të klasifikuesit.

    Mban atë që rregullat përdorin: vlerat me statusin e tyre, pohimet e
    mjekut, termat e lejuar dhe të pashpjeguar. Rendi është i qëndrueshëm,
    që i njëjti kontekst të japë gjithmonë të njëjtin varg.
    """
    parts = [
        f"{f.analyte_name_canonical} {f.value_canonical} {f.unit_canonical} "
        f"{STATUS_WORD[f.status]}"
        for f in context.findings
    ]
    parts += [f"mjeku: {a.text_span}" for a in context.assertions]
    parts += [f"term: {e.term}" for e in context.glossary]
    parts += [f"pa shpjegim: {t}" for t in context.unexplained_terms]
    return " ; ".join(parts)


class SentencePredictor(Protocol):
    """Çdo gjë që i jep probabilitete një liste fjalish."""

    version: str
    labels: tuple[str, ...]
    mode: str
    """`sentence` ose `context` — cilën hyrje pret modeli."""

    def __call__(self, sentences: list[str], context: str) -> list[list[float]]:
        ...


def check(
    context: GroundingContext,
    text: str,
    predictor: SentencePredictor,
    threshold: float,
    *,
    skip: frozenset[str] = frozenset(),
) -> Iterator[Violation]:
    """Shkeljet që klasifikuesi sheh mbi fjalitë që nuk janë në `skip`."""
    candidates = [s.text for s in sentences(text) if s.text not in skip]
    if not candidates:
        return
    serialized = serialize_context(context) if predictor.mode == "context" else ""
    clean = predictor.labels.index(CLEAN)

    for sentence, row in zip(candidates, predictor(candidates, serialized)):
        best, p = max(
            ((index, value) for index, value in enumerate(row) if index != clean),
            key=lambda pair: pair[1],
        )
        if p >= threshold:
            yield Violation(
                type=ViolationType(predictor.labels[best]),
                detected_by=DetectedBy.CLASSIFIER,
                sentence=sentence,
                evidence=f"klasifikuesi: {predictor.labels[best]} me besueshmëri {p:.2f}",
                confidence=round(p, 4),
            )


def verify_with_classifier(
    context: GroundingContext,
    text: str,
    predictor: SentencePredictor,
    threshold: float,
    *,
    rules: str | None = None,
) -> VerificationResult:
    """Rregullat, pastaj klasifikuesi mbi fjalitë që rregullat i lanë të pastra."""
    ruled = verify(context, text, rules=rules)
    flagged = frozenset(v.sentence for v in ruled.violations)
    extra = tuple(check(context, text, predictor, threshold, skip=flagged))
    return ruled.model_copy(
        update={
            "violations": ruled.violations + extra,
            "classifier_version": predictor.version,
        }
    )


class TransformersPredictor:
    """Modeli i trajnuar në Colab, i ngarkuar nga dosja e ekzekutimit.

    Dosja është ajo që prodhon `ml/train_classifier.py`: `run.json` dhe
    nëndosja `model/`. Torch dhe transformers importohen vetëm këtu.
    """

    def __init__(self, run_dir: Path, device: str | None = None) -> None:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        self.mode = run["input"]
        self.labels = tuple(run["labels"])
        self.max_length = run["max_length"]
        self.version = f"{Path(run['model']).name}/{self.mode}/{run_dir.name}"
        self._torch = torch
        self._device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._tokenizer = AutoTokenizer.from_pretrained(run_dir / "model")
        self._model = AutoModelForSequenceClassification.from_pretrained(run_dir / "model")
        self._model.to(self._device).eval()

    def __call__(self, sentences: list[str], context: str) -> list[list[float]]:
        second = [context] * len(sentences) if self.mode == "context" else None
        encoded = self._tokenizer(
            sentences,
            second,
            truncation="only_second" if second else True,
            max_length=self.max_length,
            padding=True,
            return_tensors="pt",
        ).to(self._device)
        with self._torch.no_grad():
            logits = self._model(**encoded).logits
        return self._torch.softmax(logits, dim=-1).cpu().tolist()
