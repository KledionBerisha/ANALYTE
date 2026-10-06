# E6 — Ablacion A

**Kushti:** pa bazim  
**Përgjigjet:** PK5  
**Rezultati kryesor:** 73.926 shkelje/100 fjali [95%: 70.690–77.028]

| Prejardhja | Vlera |
|---|---|
| Korpusi | `gen-1.0/s42/n500/37d8b080` |
| Dokumente | 500 (all) |
| Fara | 42 |
| Pipeline | `e6[mistral:ministral-14b-2512:u1]+ocr` v1 |
| Git | `2d93c52201b3` (e papastër) |
| Rregullat | `r1.4` |
| Kur | 2026-10-05T21:35:51+00:00 |

```json
{
  "documents": 500,
  "documents_with_output": 500,
  "sentences": 37823,
  "violations_produced": 27961,
  "violations_reaching_user": 27961,
  "rate_produced_per_100_sentences": 73.9259,
  "rate_reaching_user_per_100_sentences": 73.9259,
  "ci95_produced": {
    "estimate": 73.9259,
    "low": 70.6899,
    "high": 77.0281,
    "level": 0.95,
    "resamples": 2000,
    "unit": "document",
    "units": 500
  },
  "ci95_reaching_user": {
    "estimate": 73.9259,
    "low": 70.6899,
    "high": 77.0281,
    "level": 0.95,
    "resamples": 2000,
    "unit": "document",
    "units": 500
  },
  "by_type_produced": {
    "direction_mismatch": 2340,
    "fabricated_finding": 4583,
    "hedge_removed": 0,
    "missing_critical": 2,
    "omitted_recommendation": 357,
    "polarity_flip": 0,
    "prohibited_claim": 2657,
    "ungrounded_analyte": 3262,
    "ungrounded_number": 11547,
    "ungrounded_term_explanation": 3213
  },
  "by_type_reaching_user": {
    "direction_mismatch": 2340,
    "fabricated_finding": 4583,
    "hedge_removed": 0,
    "missing_critical": 2,
    "omitted_recommendation": 357,
    "polarity_flip": 0,
    "prohibited_claim": 2657,
    "ungrounded_analyte": 3262,
    "ungrounded_number": 11547,
    "ungrounded_term_explanation": 3213
  },
  "by_detector": {
    "classifier": 0,
    "llm_judge": 0,
    "rule": 27961
  },
  "documents_with_violation": 500,
  "clean_deliveries": 0,
  "template_fallbacks": 0,
  "fallback_share": 0.0
}
```
