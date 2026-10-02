# E5 — Krahasimi i kryqëzuar

**Kushti:** —  
**Përgjigjet:** PK4  
**Rezultati kryesor:** 0.863 saktësi

| Prejardhja | Vlera |
|---|---|
| Korpusi | `gen-1.0/s42/n500/37d8b080` |
| Dokumente | 500 (all) |
| Fara | 42 |
| Pipeline | `grounding+ocr` v1 |
| Git | `37b5be45b34b` |
| Rregullat | `r1.3` |
| Kur | 2026-10-02T19:32:13+00:00 |

```json
{
  "overall": {
    "total": 10009,
    "accuracy": 0.8634,
    "matrix": {
      "agreement->agreement": 790,
      "agreement->measured_not_mentioned": 263,
      "agreement->missing": 110,
      "contradiction->contradiction": 59,
      "contradiction->measured_not_mentioned": 19,
      "contradiction->missing": 9,
      "measured_not_mentioned->measured_not_mentioned": 7701,
      "measured_not_mentioned->missing": 909,
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
        "tp": 7701,
        "fp": 282,
        "fn": 909,
        "precision": 0.9647,
        "recall": 0.8944,
        "f1": 0.9282,
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
        "fp": 1085,
        "fn": 0,
        "precision": 0.0,
        "recall": null,
        "f1": 0.0,
        "support": 0
      }
    }
  },
  "spurious_cross_references": 10,
  "recall_by_state": {
    "agreement": 0.6793,
    "contradiction": 0.6782,
    "mentioned_not_measured": 0.6174,
    "measured_not_mentioned": 0.8944
  }
}
```
