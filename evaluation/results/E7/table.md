# E7 — Ablacion B

**Kushti:** vetëm bazim  
**Përgjigjet:** PK5  
**Rezultati kryesor:** 0.000 shkelje/100 fjali [95%: ≤ 0.021]

| Prejardhja | Vlera |
|---|---|
| Korpusi | `gen-1.0/s42/n500/37d8b080` |
| Dokumente | 500 (all) |
| Fara | 42 |
| Pipeline | `e7[template]+ocr` v1 |
| Git | `37b5be45b34b` |
| Rregullat | `r1.3` |
| Kur | 2026-10-02T19:37:23+00:00 |

```json
{
  "documents": 500,
  "documents_with_output": 500,
  "sentences": 14016,
  "violations_produced": 0,
  "violations_reaching_user": 0,
  "rate_produced_per_100_sentences": 0.0,
  "rate_reaching_user_per_100_sentences": 0.0,
  "ci95_produced": {
    "estimate": 0.0,
    "low": 0.0,
    "high": 0.0,
    "level": 0.95,
    "resamples": 2000,
    "unit": "document",
    "units": 500,
    "rule_of_three_high": 0.0214
  },
  "ci95_reaching_user": {
    "estimate": 0.0,
    "low": 0.0,
    "high": 0.0,
    "level": 0.95,
    "resamples": 2000,
    "unit": "document",
    "units": 500,
    "rule_of_three_high": 0.0214
  },
  "by_type_produced": {
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
    "rule": 0
  },
  "documents_with_violation": 0,
  "clean_deliveries": 500,
  "template_fallbacks": 0,
  "fallback_share": 0.0
}
```
