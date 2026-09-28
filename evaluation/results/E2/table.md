# E2 — Saktësia e nxjerrjes

**Kushti:** i skanuar  
**Përgjigjet:** PK1  
**Rezultati kryesor:** 0.666 F1

| Prejardhja | Vlera |
|---|---|
| Korpusi | `gen-1.0/s42/n500/37d8b080` |
| Dokumente | 168 (scanned) |
| Fara | 42 |
| Pipeline | `grounding+ocr` v1 |
| Git | `d8839e240cfe` (e papastër) |
| Rregullat | `r1.2` |
| Kur | 2026-09-27T22:01:36+00:00 |

```json
{
  "per_field": {
    "analyte": {
      "tp": 2509,
      "fp": 11,
      "fn": 879,
      "precision": 0.9956,
      "recall": 0.7406,
      "f1": 0.8494,
      "support": 3388
    },
    "value": {
      "tp": 2249,
      "fp": 271,
      "fn": 1139,
      "precision": 0.8925,
      "recall": 0.6638,
      "f1": 0.7613,
      "support": 3388
    },
    "unit": {
      "tp": 1852,
      "fp": 668,
      "fn": 1536,
      "precision": 0.7349,
      "recall": 0.5466,
      "f1": 0.6269,
      "support": 3388
    },
    "interval": {
      "tp": 1263,
      "fp": 1257,
      "fn": 2125,
      "precision": 0.5012,
      "recall": 0.3728,
      "f1": 0.4276,
      "support": 3388
    }
  },
  "micro": {
    "tp": 7873,
    "fp": 2207,
    "fn": 5679,
    "precision": 0.7811,
    "recall": 0.5809,
    "f1": 0.6663,
    "support": 13552
  },
  "macro_f1": 0.666299932295193,
  "documents": 168
}
```
