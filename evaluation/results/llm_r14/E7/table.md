# E7 — Ablacion B

**Kushti:** vetëm bazim  
**Përgjigjet:** PK5  
**Rezultati kryesor:** 13.563 shkelje/100 fjali [95%: 11.857–15.538]

| Prejardhja | Vlera |
|---|---|
| Korpusi | `gen-1.0/s42/n500/37d8b080` |
| Dokumente | 500 (all) |
| Fara | 42 |
| Pipeline | `e7[mistral:ministral-14b-2512:p1]+ocr+guard` v1 |
| Git | `2d93c52201b3` (e papastër) |
| Rregullat | `r1.4` |
| Kur | 2026-10-05T20:50:36+00:00 |

```json
{
  "documents": 500,
  "documents_with_output": 500,
  "sentences": 5677,
  "violations_produced": 770,
  "violations_reaching_user": 770,
  "rate_produced_per_100_sentences": 13.5635,
  "rate_reaching_user_per_100_sentences": 13.5635,
  "ci95_produced": {
    "estimate": 13.5635,
    "low": 11.8567,
    "high": 15.5384,
    "level": 0.95,
    "resamples": 2000,
    "unit": "document",
    "units": 500
  },
  "ci95_reaching_user": {
    "estimate": 13.5635,
    "low": 11.8567,
    "high": 15.5384,
    "level": 0.95,
    "resamples": 2000,
    "unit": "document",
    "units": 500
  },
  "by_type_produced": {
    "direction_mismatch": 291,
    "fabricated_finding": 107,
    "hedge_removed": 0,
    "missing_critical": 3,
    "omitted_recommendation": 104,
    "polarity_flip": 3,
    "prohibited_claim": 6,
    "ungrounded_analyte": 41,
    "ungrounded_number": 106,
    "ungrounded_term_explanation": 109
  },
  "by_type_reaching_user": {
    "direction_mismatch": 291,
    "fabricated_finding": 107,
    "hedge_removed": 0,
    "missing_critical": 3,
    "omitted_recommendation": 104,
    "polarity_flip": 3,
    "prohibited_claim": 6,
    "ungrounded_analyte": 41,
    "ungrounded_number": 106,
    "ungrounded_term_explanation": 109
  },
  "by_detector": {
    "classifier": 0,
    "llm_judge": 0,
    "rule": 770
  },
  "documents_with_violation": 289,
  "clean_deliveries": 211,
  "template_fallbacks": 0,
  "fallback_share": 0.0
}
```
