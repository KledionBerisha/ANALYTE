# E5 — Krahasimi i kryqëzuar

**Kushti:** —  
**Përgjigjet:** PK4  
**Rezultati kryesor:** 0.877 saktësi

| Prejardhja | Vlera |
|---|---|
| Korpusi | `gen-1.0/s42/n500/37d8b080` |
| Dokumente | 500 (all) |
| Fara | 42 |
| Pipeline | `grounding+ocr` v1 |
| Git | `d8839e240cfe` (e papastër) |
| Rregullat | `r1.2` |
| Kur | 2026-09-27T22:06:26+00:00 |

```json
{
  "overall": {
    "total": 10009,
    "accuracy": 0.8766,
    "matrix": {
      "agreement->agreement": 790,
      "agreement->measured_not_mentioned": 279,
      "agreement->missing": 94,
      "contradiction->contradiction": 59,
      "contradiction->measured_not_mentioned": 20,
      "contradiction->missing": 8,
      "measured_not_mentioned->measured_not_mentioned": 7833,
      "measured_not_mentioned->missing": 777,
      "mentioned_not_measured->mentioned_not_measured": 92,
      "mentioned_not_measured->missing": 57
    },
    "per_class": {
      "agreement": {
        "tp": 790,
        "fp": 0,
        "fn": 373,
        "precision": 1.0,
        "recall": 0.6793,
        "f1": 0.809,
        "support": 1163
      },
      "contradiction": {
        "tp": 59,
        "fp": 0,
        "fn": 28,
        "precision": 1.0,
        "recall": 0.6782,
        "f1": 0.8082,
        "support": 87
      },
      "measured_not_mentioned": {
        "tp": 7833,
        "fp": 299,
        "fn": 777,
        "precision": 0.9632,
        "recall": 0.9098,
        "f1": 0.9357,
        "support": 8610
      },
      "mentioned_not_measured": {
        "tp": 92,
        "fp": 0,
        "fn": 57,
        "precision": 1.0,
        "recall": 0.6174,
        "f1": 0.7635,
        "support": 149
      },
      "missing": {
        "tp": 0,
        "fp": 936,
        "fn": 0,
        "precision": 0.0,
        "recall": null,
        "f1": null,
        "support": 0
      }
    }
  },
  "spurious_cross_references": 11,
  "recall_by_state": {
    "agreement": 0.6793,
    "contradiction": 0.6782,
    "mentioned_not_measured": 0.6174,
    "measured_not_mentioned": 0.9098
  }
}
```
