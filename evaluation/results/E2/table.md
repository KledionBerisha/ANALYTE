# E2 — Saktësia e nxjerrjes

**Kushti:** i skanuar  
**Përgjigjet:** PK1  
**Rezultati kryesor:** 0.670 F1

| Prejardhja | Vlera |
|---|---|
| Korpusi | `gen-1.0/s42/n500/37d8b080` |
| Dokumente | 168 (scanned) |
| Fara | 42 |
| Pipeline | `grounding+ocr` v1 |
| Git | `37b5be45b34b` |
| Rregullat | `r1.3` |
| Kur | 2026-10-02T19:22:15+00:00 |

```json
{
  "per_field": {
    "analyte": {
      "tp": 2360,
      "fp": 10,
      "fn": 1028,
      "precision": 0.9958,
      "recall": 0.6966,
      "f1": 0.8197,
      "support": 3388
    },
    "value": {
      "tp": 2245,
      "fp": 125,
      "fn": 1143,
      "precision": 0.9473,
      "recall": 0.6626,
      "f1": 0.7798,
      "support": 3388
    },
    "unit": {
      "tp": 1852,
      "fp": 518,
      "fn": 1536,
      "precision": 0.7814,
      "recall": 0.5466,
      "f1": 0.6433,
      "support": 3388
    },
    "interval": {
      "tp": 1262,
      "fp": 1108,
      "fn": 2126,
      "precision": 0.5325,
      "recall": 0.3725,
      "f1": 0.4383,
      "support": 3388
    }
  },
  "micro": {
    "tp": 7719,
    "fp": 1761,
    "fn": 5833,
    "precision": 0.8142,
    "recall": 0.5696,
    "f1": 0.6703,
    "support": 13552
  },
  "macro_f1": 0.6702848211184439,
  "documents": 168
}
```
