# E4 — Besnikëria e thjeshtimit

**Kushti:** —  
**Përgjigjet:** PK3  
**Rezultati kryesor:** 0.997 ruajtje mohimi [95%: 0.991–1.000]

| Prejardhja | Vlera |
|---|---|
| Korpusi | `gen-1.0/s42/n500/37d8b080` |
| Dokumente | 500 (all) |
| Fara | 42 |
| Pipeline | `e8[mistral:ministral-14b-2512:p1]+ocr+guard` v1 |
| Git | `2d93c52201b3` (e papastër) |
| Rregullat | `r1.4` |
| Kur | 2026-10-05T21:27:01+00:00 |

```json
{
  "documents": 500,
  "documents_with_output": 500,
  "sentences": 5805,
  "negation_preservation": 0.997,
  "hedge_preservation": 1.0,
  "ci95_negation_preservation": {
    "estimate": 0.997,
    "low": 0.9907,
    "high": 1.0,
    "level": 0.95,
    "resamples": 2000,
    "unit": "document",
    "units": 275
  },
  "ci95_hedge_preservation": {
    "estimate": 1.0,
    "low": 1.0,
    "high": 1.0,
    "level": 0.95,
    "resamples": 2000,
    "unit": "document",
    "units": 113,
    "rule_of_three_low": 0.9737
  },
  "recommendation_preservation": 0.9461,
  "fabricated_findings_per_100_sentences": 0.5857,
  "counts": {
    "negated_assertions": 329,
    "hedged_assertions": 114,
    "recommendations": 612,
    "polarity_flips": 1,
    "hedges_removed": 0,
    "recommendations_omitted": 33,
    "fabricated_findings": 34
  }
}
```
