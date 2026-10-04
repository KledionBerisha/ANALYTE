# E8 — Ablacion C

**Kushti:** + verifikim me rregulla  
**Përgjigjet:** PK5  
**Rezultati kryesor:** 0.000 shkelje/100 fjali [95%: ≤ 0.034]

| Prejardhja | Vlera |
|---|---|
| Korpusi | `gen-1.0/s42/n500/37d8b080` |
| Dokumente | 500 (all) |
| Fara | 42 |
| Pipeline | `e8[mistral:ministral-14b-2512:p1]+ocr` v1 |
| Git | `4f5ea177c675` |
| Rregullat | `r1.3` |
| Kur | 2026-10-04T19:23:52+00:00 |

```json
{
  "documents": 500,
  "documents_with_output": 500,
  "sentences": 8892,
  "violations_produced": 906,
  "violations_reaching_user": 0,
  "rate_produced_per_100_sentences": 10.1889,
  "rate_reaching_user_per_100_sentences": 0.0,
  "ci95_produced": {
    "estimate": 10.1889,
    "low": 8.5472,
    "high": 12.0115,
    "level": 0.95,
    "resamples": 2000,
    "unit": "document",
    "units": 500
  },
  "ci95_reaching_user": {
    "estimate": 0.0,
    "low": 0.0,
    "high": 0.0,
    "level": 0.95,
    "resamples": 2000,
    "unit": "document",
    "units": 500,
    "rule_of_three_high": 0.0337
  },
  "by_type_produced": {
    "direction_mismatch": 432,
    "fabricated_finding": 143,
    "hedge_removed": 0,
    "missing_critical": 11,
    "omitted_recommendation": 134,
    "polarity_flip": 5,
    "prohibited_claim": 0,
    "ungrounded_analyte": 31,
    "ungrounded_number": 150,
    "ungrounded_term_explanation": 0
  },
  "by_type_reaching_user": {
    "direction_mismatch": 0,
    "fabricated_finding": 0,
    "hedge_removed": 0,
    "missing_critical": 0,
    "omitted_recommendation": 0,
    "polarity_flip": 0,
    "prohibited_claim": 0,
    "ungrounded_analyte": 0,
    "ungrounded_number": 0,
    "ungrounded_term_explanation": 0
  },
  "by_detector": {
    "classifier": 0,
    "llm_judge": 0,
    "rule": 906
  },
  "documents_with_violation": 247,
  "clean_deliveries": 500,
  "template_fallbacks": 126,
  "fallback_share": 0.252
}
```
