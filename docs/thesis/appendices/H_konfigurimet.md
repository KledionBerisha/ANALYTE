<!-- E gjeneruar nga scripts/build_appendices.py. Mos e ndrysho me dorë: ndrysho burimin dhe rigjenero. -->

## Shtojca H — Konfigurimet e eksperimenteve dhe farat fillestare

*Tabela H.1. Korpusi sintetik*

| Parametri | Vlera |
|---|---|
| Versioni i gjeneruesit | `gen-1.0` |
| Fara | 42 |
| Dokumente | 500 (168 të skanuara, pjesa e synuar 35%) |
| Faqe | 556 |
| Gjetje laboratorike | 9860 |
| Pohime të mjekut | 2749 |
| Terma të pashpjeguar | 236 |
| Dokumente me vlerë kritike | 36 |

*Tabela H.2. Versionet dhe parametrat fiks të sistemit*

| Parametri | Vlera |
|---|---|
| Katalogu i rregullave | `r1.3` |
| Politika e sigurisë | `sp1.0` |
| OCR | Tesseract, gjuha `eng`, `--psm 6`, 200 dpi |
| Rimostrimi bootstrap | 2000 rimostrime, fara 20260928, njësia është dokumenti |

*Tabela H.3. Rezultatet që ekzistojnë dhe prejardhja e tyre*

| Eksperimenti | Pipeline | Kodi (git) | Pema e punës | Korpusi |
|---|---|---|---|---|
| E1 | `grounding` | `37b5be45b3` | e pastër | `gen-1.0/s42/n500/37d8b080` |
| E2 | `grounding+ocr` | `37b5be45b3` | e pastër | `gen-1.0/s42/n500/37d8b080` |
| E3 | `grounding+ocr` | `37b5be45b3` | e pastër | `gen-1.0/s42/n500/37d8b080` |
| E5 | `grounding+ocr` | `37b5be45b3` | e pastër | `gen-1.0/s42/n500/37d8b080` |
| E7 | `e7[template]+ocr` | `37b5be45b3` | e pastër | `gen-1.0/s42/n500/37d8b080` |
| E8 | `e8[template]+ocr` | `37b5be45b3` | e pastër | `gen-1.0/s42/n500/37d8b080` |
| E9 | `e9[template]+ocr+xlm-roberta-base/sentence/sentence@0.85` | `37b5be45b3` | e pastër | `gen-1.0/s42/n500/37d8b080` |
| E10 | — | — | — | — (pa metadata) |

*Tabela H.4. Klasifikuesi XLM-RoBERTa (trajnuar në Colab) dhe pragjet e zgjedhura mbi validimin*

| Hyrja | Modeli | Epoka | Shkalla e të nxënit | Batch | Gjatësia | Fara | Pajisja | Pragu 1 | Pragu 2 |
|---|---|---|---|---|---|---|---|---|---|
| context | `xlm-roberta-base` | 3 | 2e-05 | 16 | 384 | 42 | Tesla T4 | 0.4 | 0.9 |
| sentence | `xlm-roberta-base` | 3 | 2e-05 | 16 | 128 | 42 | Tesla T4 | 0.3 | 0.85 |

Pragu 1 është ai me macro F1 më të lartë mbi validimin; pragu 2 është ai me macro F1 më të lartë ndër ata që bllokojnë jo më shumë se 5% të teksteve të pastra të validimit (seksioni 6.7).
