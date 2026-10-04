# E9 — Ablacion D

**Kushti:** + klasifikues  
**Përgjigjet:** PK5  
**Rezultati kryesor:** 0.396 shkelje/100 fjali [95%: 0.247–0.562]

| Prejardhja | Vlera |
|---|---|
| Korpusi | `gen-1.0/s42/n500/37d8b080` |
| Dokumente | 500 (all) |
| Fara | 42 |
| Pipeline | `e9[mistral:ministral-14b-2512:p1]+ocr+xlm-roberta-base/sentence/sentence@0.85` v1 |
| Git | `4f5ea177c675` |
| Rregullat | `r1.3` |
| Kur | 2026-10-04T19:31:03+00:00 |

```json
{
  "documents": 500,
  "documents_with_output": 500,
  "sentences": 10359,
  "violations_produced": 1930,
  "violations_reaching_user": 41,
  "rate_produced_per_100_sentences": 18.6311,
  "rate_reaching_user_per_100_sentences": 0.3958,
  "ci95_produced": {
    "estimate": 18.6311,
    "low": 17.0372,
    "high": 20.4045,
    "level": 0.95,
    "resamples": 2000,
    "unit": "document",
    "units": 500
  },
  "ci95_reaching_user": {
    "estimate": 0.3958,
    "low": 0.2471,
    "high": 0.562,
    "level": 0.95,
    "resamples": 2000,
    "unit": "document",
    "units": 500
  },
  "by_type_produced": {
    "direction_mismatch": 445,
    "fabricated_finding": 226,
    "hedge_removed": 0,
    "missing_critical": 13,
    "omitted_recommendation": 146,
    "polarity_flip": 4,
    "prohibited_claim": 0,
    "ungrounded_analyte": 948,
    "ungrounded_number": 148,
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
    "ungrounded_analyte": 41,
    "ungrounded_number": 0,
    "ungrounded_term_explanation": 0
  },
  "by_detector": {
    "classifier": 982,
    "llm_judge": 0,
    "rule": 948
  },
  "documents_with_violation": 380,
  "clean_deliveries": 470,
  "template_fallbacks": 302,
  "fallback_share": 0.604
}
```
