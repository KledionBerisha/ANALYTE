# E7 — Ablacion B

**Kushti:** vetëm bazim  
**Përgjigjet:** PK5  
**Rezultati kryesor:** 9.545 shkelje/100 fjali [95%: 8.118–11.224]

| Prejardhja | Vlera |
|---|---|
| Korpusi | `gen-1.0/s42/n500/37d8b080` |
| Dokumente | 500 (all) |
| Fara | 42 |
| Pipeline | `e7[mistral:ministral-14b-2512:p1]+ocr` v1 |
| Git | `4f5ea177c675` |
| Rregullat | `r1.3` |
| Kur | 2026-10-04T19:18:01+00:00 |

```json
{
  "documents": 500,
  "documents_with_output": 500,
  "sentences": 5804,
  "violations_produced": 554,
  "violations_reaching_user": 554,
  "rate_produced_per_100_sentences": 9.5451,
  "rate_reaching_user_per_100_sentences": 9.5451,
  "ci95_produced": {
    "estimate": 9.5451,
    "low": 8.1181,
    "high": 11.2241,
    "level": 0.95,
    "resamples": 2000,
    "unit": "document",
    "units": 500
  },
  "ci95_reaching_user": {
    "estimate": 9.5451,
    "low": 8.1181,
    "high": 11.2241,
    "level": 0.95,
    "resamples": 2000,
    "unit": "document",
    "units": 500
  },
  "by_type_produced": {
    "direction_mismatch": 235,
    "fabricated_finding": 113,
    "hedge_removed": 0,
    "missing_critical": 6,
    "omitted_recommendation": 104,
    "polarity_flip": 3,
    "prohibited_claim": 0,
    "ungrounded_analyte": 22,
    "ungrounded_number": 71,
    "ungrounded_term_explanation": 0
  },
  "by_type_reaching_user": {
    "direction_mismatch": 235,
    "fabricated_finding": 113,
    "hedge_removed": 0,
    "missing_critical": 6,
    "omitted_recommendation": 104,
    "polarity_flip": 3,
    "prohibited_claim": 0,
    "ungrounded_analyte": 22,
    "ungrounded_number": 71,
    "ungrounded_term_explanation": 0
  },
  "by_detector": {
    "classifier": 0,
    "llm_judge": 0,
    "rule": 554
  },
  "documents_with_violation": 247,
  "clean_deliveries": 253,
  "template_fallbacks": 0,
  "fallback_share": 0.0
}
```
