# E9 — Ablacion D

**Kushti:** + klasifikues  
**Përgjigjet:** PK5  
**Rezultati kryesor:** 0.515 shkelje/100 fjali [95%: 0.373–0.665]

| Prejardhja | Vlera |
|---|---|
| Korpusi | `gen-1.0/s42/n500/37d8b080` |
| Dokumente | 500 (all) |
| Fara | 42 |
| Pipeline | `e9[template]+ocr+xlm-roberta-base/sentence/sentence@0.85` v1 |
| Git | `37b5be45b34b` |
| Rregullat | `r1.3` |
| Kur | 2026-10-02T19:49:24+00:00 |

```json
{
  "documents": 500,
  "documents_with_output": 500,
  "sentences": 15328,
  "violations_produced": 158,
  "violations_reaching_user": 79,
  "rate_produced_per_100_sentences": 1.0308,
  "rate_reaching_user_per_100_sentences": 0.5154,
  "ci95_produced": {
    "estimate": 1.0308,
    "low": 0.7454,
    "high": 1.3292,
    "level": 0.95,
    "resamples": 2000,
    "unit": "document",
    "units": 500
  },
  "ci95_reaching_user": {
    "estimate": 0.5154,
    "low": 0.3727,
    "high": 0.6646,
    "level": 0.95,
    "resamples": 2000,
    "unit": "document",
    "units": 500
  },
  "by_type_produced": {
    "direction_mismatch": 0,
    "fabricated_finding": 0,
    "hedge_removed": 0,
    "missing_critical": 0,
    "omitted_recommendation": 0,
    "polarity_flip": 0,
    "prohibited_claim": 0,
    "ungrounded_analyte": 158,
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
    "ungrounded_analyte": 79,
    "ungrounded_number": 0,
    "ungrounded_term_explanation": 0
  },
  "by_detector": {
    "classifier": 158,
    "llm_judge": 0,
    "rule": 0
  },
  "documents_with_violation": 51,
  "clean_deliveries": 449,
  "template_fallbacks": 51,
  "fallback_share": 0.102
}
```
