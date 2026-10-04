# E6 — Ablacion A

**Kushti:** pa bazim  
**Përgjigjet:** PK5  
**Rezultati kryesor:** 54.385 shkelje/100 fjali [95%: 51.551–57.181]

| Prejardhja | Vlera |
|---|---|
| Korpusi | `gen-1.0/s42/n500/37d8b080` |
| Dokumente | 500 (all) |
| Fara | 42 |
| Pipeline | `e6[mistral:ministral-14b-2512:u1]+ocr` v1 |
| Git | `4f5ea177c675` |
| Rregullat | `r1.3` |
| Kur | 2026-10-04T19:51:23+00:00 |

```json
{
  "documents": 500,
  "documents_with_output": 500,
  "sentences": 37823,
  "violations_produced": 20570,
  "violations_reaching_user": 20570,
  "rate_produced_per_100_sentences": 54.3849,
  "rate_reaching_user_per_100_sentences": 54.3849,
  "ci95_produced": {
    "estimate": 54.3849,
    "low": 51.551,
    "high": 57.1812,
    "level": 0.95,
    "resamples": 2000,
    "unit": "document",
    "units": 500
  },
  "ci95_reaching_user": {
    "estimate": 54.3849,
    "low": 51.551,
    "high": 57.1812,
    "level": 0.95,
    "resamples": 2000,
    "unit": "document",
    "units": 500
  },
  "by_type_produced": {
    "direction_mismatch": 1508,
    "fabricated_finding": 4580,
    "hedge_removed": 0,
    "missing_critical": 3,
    "omitted_recommendation": 357,
    "polarity_flip": 0,
    "prohibited_claim": 131,
    "ungrounded_analyte": 2854,
    "ungrounded_number": 11075,
    "ungrounded_term_explanation": 62
  },
  "by_type_reaching_user": {
    "direction_mismatch": 1508,
    "fabricated_finding": 4580,
    "hedge_removed": 0,
    "missing_critical": 3,
    "omitted_recommendation": 357,
    "polarity_flip": 0,
    "prohibited_claim": 131,
    "ungrounded_analyte": 2854,
    "ungrounded_number": 11075,
    "ungrounded_term_explanation": 62
  },
  "by_detector": {
    "classifier": 0,
    "llm_judge": 0,
    "rule": 20570
  },
  "documents_with_violation": 500,
  "clean_deliveries": 0,
  "template_fallbacks": 0,
  "fallback_share": 0.0
}
```
