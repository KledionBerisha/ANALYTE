# ANALYTE — progress so far

*State as of 2026-10-04, on top of commit `289cac5`. **Uncommitted:** email confirmation, registration that no longer reveals accounts, IPv6 /64 throttling and sign-out-everywhere (ADR 0016, migration `0003`, backend + frontend + tests); the thesis text rewritten to what was built (§5.7 classifier, §5.10, §5.12, §6.1, §7.6, Table 1); Figures 1–5, 9, 10 and 18–21 (`scripts/figures/concepts.py`, `scripts/figures/results.py`) and their wiring into the thesis; provenance metadata for E10/E11 (`evaluation/provenance.py`); tests for both; corrections to this file and to `docs/thesis/README.md`. Everything else is committed: the model path (ADR 0015), the real-model experiments E4/E6–E9, the E12 judges, the audit of E8, set C, Chapters 6–7, the Abstract and Appendix D.*

ANALYTE extracts laboratory values and physician statements from Albanian
medical PDFs, interprets them deterministically, writes a patient-facing
explanation that may use only that interpretation (`GroundingContext`), and
verifies the explanation automatically before anyone sees it.

**Tests:** 628 pass, 1 skipped (`python -m pytest`, 2026-10-04), plus the PostgreSQL integration test (`make test-postgres`: all 94 integration tests passed on PostgreSQL 16 against migration `0003` on 2026-10-05; the migration also checked on PostgreSQL: old accounts grandfathered as confirmed, downgrade and re-upgrade clean).
**Architecture decisions:** 17 ADRs in `docs/adr/` (0015: the language model, prompt, cache and judges; 0016: email confirmation and the closed ADR 0014 gaps; 0017: the model in the web app).

## Where we stand

| | |
|---|---|
| **Done and verified** | The whole system (extraction incl. OCR, interpretation, patterns, narrative branch, verification rules, state machine, API with hardened auth, frontend) and the **language-model path** (in the evaluation harness, and in the web service when `ANALYTE_SERVICE_GENERATOR=model`: ADR 0017, off by default, no disk cache, a `model` notice for the patient): client with response cache (`ministral-14b-2512`, Mistral free plan), versioned prompt `p1`, E6 baseline, Claude-judge batches, independent audit. Experiments E1–E12 and set B measured, all re-runnable; the model experiments were re-run from a clean checkout of `4f5ea17` with no new calls (E6: 2, for two documents that had no valid response the first time). |
| **Measured, with the honest reading** | The rules reach macro F1 **0.993** on the synthetic corpus but **0.795** on the author's natural-sentence set B (weak spots: diagnosis/treatment/prognosis, short direction phrases, unexplained-term explanations). The trained classifier is **close to useless on natural text** (0.015–0.177) and false-alarms on OCR text (E9: 10.2% of documents). OCR reads 125 of 2 370 values wrong and accepts them. |
| **Main result (PK5)** | Violations reaching the user, per 100 sentences, with the real model: **54.4** without grounding (E6), **9.5** grounded (E7), **0.000** (95% ≤ 0.034) grounded + rules + one retry (E8) — at the price of **25%** of documents falling back to the template; the sentence classifier (E9) raises that to 60% for no measured gain. **The 0.000 counts only what the rules see**: the independent audit of 90 delivered texts finds a rule-type problem in **36% (26–46%)**, direction errors in 23%, and some problem of any kind in 58%. H1 holds in the measured form, not as a guarantee; H2 is not confirmed. |
| **Not done** | Real documents (E13, no ethics approval), user study (E14/PK7), local model (E15), expert review, Chapter 3 and 40–60 references, sources for the 82 terms and 11 combination rules, **handwritten set A** (the author is rewriting it), the OCR plausibility check, chat (figure 17 would be its screenshot), a second judge independent of the system's builder. |

---

## Resuming in a new session

- **Working conventions** (memory notes in `~/.claude/projects/.../memory/`): never commit or push (the author does; give a one-sentence English commit message); no `Co-Authored-By`/"Generated with" lines; chat in English, code comments and thesis text in Albanian; **never invent citations** (leave `[REFERENCË — plotësohet]`); report every metric with its caveat and say when a method changed after a result was seen; state authorship exactly as the evidence supports (set B overlap, set C declared by the author); experiments for the thesis are re-run from a **clean git worktree** (`git worktree add --detach <dir> HEAD`, with `data/` and `ml/artifacts/` linked and `.env` copied), `--out` outside it.
- **LLM:** `.env` holds `ANALYTE_LLM_PROVIDER=mistral`, `ANALYTE_LLM_MODEL=ministral-14b-2512`, `ANALYTE_LLM_API_KEY` (never print or paste it). Free-plan facts: gemini-3.8-flash = 20 requests/day; Mistral small/medium/large have a 0 limit on the free plan; ministral-14b-2512 = 30 requests/min. Every model answer is cached in `evaluation/cache/llm/` (committed), so reruns need no calls. E12 and the audit use Claude subagents (`evaluation/judge_batches.py`, `evaluation/audit_batches.py`); no API.
- **Where things are:** thesis `docs/thesis/teza_v3.md` (Chapter 6 tables from `python scripts/build_chapter6_tables.py`; Appendices by `python scripts/build_appendices.py`); decisions `docs/adr/` (0015 = the model path); results `evaluation/results/` (`llm/` for the real-model runs, `supplementary/kit_C.json` for set C); handwritten sets `evaluation/handwritten/` (B and C installed, A empty).
- **Editing tip:** long Python in Bash heredocs mangles backslashes — write patch scripts with the file tool; keep LF line endings in `teza_v3.md`.

---

## 1. Phase status

| Phase (spec §6) | State |
|---|---|
| Domain contract | ✅ done |
| 2 — Synthetic corpus generator | ✅ done — 38 analytes, 3 layouts, scan simulation, reproducible from a seed |
| 3 — Evaluation infrastructure | ✅ done — harness, E1–E15 matrix, provenance, bootstrap 95% CIs |
| 4 — Branch A (lab values) | ✅ done — digital + **OCR** (Tesseract), combination patterns P01–P11 |
| 5 — Branch B (physician narrative) | ✅ done — terms, negation, hedging, cross-reference |
| 6 — Generation + verification | ✅ rules R1–R9 + SP1-3, state machine, regeneration, template fallback, **and the model path** (ADR 0015); the audit shows the rules miss a large share of real model errors |
| 7 — ML classifier | ✅ trained on Colab and measured on 2026-09-30 (E11) — far weaker than the rules; both threshold rules are reported (author's decision, 5% false-alarm budget) |
| 8 — Ablation | ✅ E6–E9 measured with the real model (54.4 → 9.5 → 0.000 → 0.40); E7–E9 with the template kept as boundary checks (`evaluation/results/E7`–`E9`) |
| 9 — Web application | ✅ backend + frontend done; it generates with the deterministic template by default and with the model when `ANALYTE_SERVICE_GENERATOR=model` (ADR 0017); chat is not built |
| 10 — User study (PK7) | ⛔ not started |
| 11 — Analysis / discussion | ⛔ not started |
| 12 — Thesis writing | ⚠️ `docs/thesis/teza_v3.md`: Chapters 5, 6 and 7 written from the code and the result files (H1 confirmed in the measured form only, H2 not confirmed), Abstract, §7.1/§7.3/§7.6/§7.8 and Appendices A–I done; Chapter 3 incomplete, 4 references verified; Figures 1–16 and 18–21 all made (1–11 and 18–21 from code, 12–16 by `scripts/export_screenshots.py`); only 17 (the chat) is not |
| 0 / 1 — ethics, mentor, Chapter 3 | author's side |

---

## 2. Measured results

Every number is from `evaluation/results/<experiment>/result.json` on the
corpus `gen-1.0/s42/n500/37d8b080` (500 documents, 168 scanned) unless noted.

| Experiment | Question | Result | How to read it |
|---|---|---|---|
| E1 | PK1 extraction, digital (332 documents) | **F1 1.000** | Measures wiring, not difficulty: the generator draws clean text at known coordinates. Stated as a limitation; external validity rests on E13. |
| E2 | PK1 extraction, scanned (OCR) | **F1 0.670** | Value precision 0.947 — **125 of 2 370 values read from scans are wrong and accepted**. |
| E3 | PK2 status classification, all docs, OCR | **0.881** | 62 values get the wrong direction, **11 are falsely "critical"** — all from lost decimal separators ("15,7" → "157"). |
| E5 | PK4 cross-reference | 1.000 digital · **0.656** whole corpus without OCR · **0.863** with OCR | The old draft value 0.563 had no recorded corpus and was replaced. |
| E7, E8 (template) | PK5 conditions B and C with the **template** as generator, OCR on, 500 docs | **0.000 violations/100 sentences** each (95% ≤ 0.021) | Boundary checks, not results: the template never errs, so verification has nothing to remove. They prove the loop and metric work end to end. Superseded by the model runs below. |
| E9 (template) | same, plus the sentence classifier at threshold 0.85 (rule 2), template as generator | **0.515 violations/100 sentences reaching the user** (95% CI 0.37–0.66); 158 sentences flagged in 51 documents (10.2%) → template fallback | **All are false alarms** (the generator is the template). They come from scanned documents: OCR-garbled units are flagged (12 of 40 scanned documents vs 0 of 120 digital sampled). The 5% budget chosen on clean digital text does not transfer to OCR text. |
| E10 | PK6 rules detector, 192 test samples | **macro F1 0.993**, 0 false alarms | Rules were fixed (r1.1–r1.3) after the test split was first measured (0.979). The fixes came from hand-built contexts and the UI, not from test errors — but this must be said. |
| E11 | PK6 classifier, same 192 texts as E10 | **Rule 1** (max macro F1): sentence **0.481**, sentence + context **0.538**, but it blocks **30/30 and 29/30 clean texts**. **Rule 2** (≤5% of clean validation texts blocked): sentence **0.385** (0/30 clean blocked), context **0.326** (2/30 blocked — 6.7%, above the 5% budget on the test set). | Far below the rules (0.993). Within the budget it catches nothing for `polarity_flip` and `direction_mismatch` (F1 0.00). Its perfect class, `fabricated_finding`, is a template artifact (leakage report). Measured after a metric correction, and rule 2 was added after the test split had been seen — both disclosed in ADR 0009. E9 uses rule 2. |
| **Set B** (105 natural sentences, submitted by the author) | PK6 on prose the generator did not produce | **Rules: macro F1 0.795**, 1/30 clean flagged. Classifier: sentence 0.053 (rule 1) / 0.015 (rule 2); sentence + context 0.177 / 0.104 | The real test: rules fall from 0.993 (synthetic) to 0.795; the classifier is close to useless. Rules per type — `polarity_flip`, `hedge_removed`, `ungrounded_analyte` 1.00; `ungrounded_number`, `fabricated_finding` 0.95; `direction_mismatch` 0.67; `prohibited_claim` 0.46; `ungrounded_term_explanation` **0.33 (1 of 5)**. **12 of 105 rows (doctor quotes only) are identical to rows of an earlier model-drafted version** — disclosed in `evaluation/handwritten/README.md` and ADR 0009; no duplicate rows. The evaluator was changed after a first 0/20 reading on quote rows (ADR 0009). 9 of 105 share a shape with training sentences; 0 verbatim in the template. |
| **E6, E7, E8, E9** (model) | PK5 with `ministral-14b-2512`, OCR on, 500 docs, clean checkout `4f5ea17` | per 100 sentences: **54.38** [51.55–57.18] → **9.55** [8.12–11.22] → **0.000** (≤ 0.034) → **0.40** [0.25–0.56]; fallbacks: E8 126 (25.2%), E9 302 (60.4%) | E8 produced 906 violations over both attempts, 0 reached the user; 121 of 247 first-attempt failures were fixed by the retry. E6 counts any number outside the measured values (dates too) and its texts are 4× longer. In E9 the 41 delivered violations are false alarms on template text; the classifier was not audited on model text. |
| **E4** (model) | PK3 on E8 drafts (5 935 sentences) | negation preserved **0.994** (327/329), hedges **1.000** (114/114), recommendations lost **4.9%** (30/612), invented findings **0.51/100 sentences** | Measures obedience to the "copy the doctor's words" instruction, not simplification; numerator comes from the rules. |
| **E12** (judges) | PK6 with an LLM judge, same 192 + 105 samples | **Claude Sonnet macro F1 1.000 / 1.000**, 0 clean blocked; **Claude Haiku 0.625 / 0.514**, 5 and 9 clean blocked | Not independent of the system (the same assistant built it), no fixed temperature, label-file access not technically audited (transcripts empty; Sonnet used 5–7 tool calls per batch, Haiku 5–47). Haiku agrees with Sonnet on 53% of items, so 1.000 is not a ceiling of the task. |
| **Set C** (60 author-written narrative sentences) | Branch B assertion extraction outside the generator's vocabulary | all five fields correct on **32/60**; on the **41 rows not identical to a generator sentence only 13/41**; simple negations 0/15, pseudo-negations 0/10, hedged 10/10, recommendations 7/10, direct statements 15/15 | 19 of 60 rows coincide with generator sentences (and all 19 pass). Failures: direction written as a noun ("rritja e TSH-së") is not recognised, "nuk mund të mohohet" is read as a plain negation, "nuk nevojitet"/"nevoja për" are not recognised. Same root cause as the audit's direction errors. Rules were not changed afterwards. |
| **Audit of E8** | independent look at 90 delivered generated texts (+10 template controls) | any problem **58%**; rule-type problem **36%** [26–46%]; clinical-type **27%** [19–37%]; direction **23%**; **0/10 template controls** | Lower bound of what the rules miss, from a fallible judge; some findings are borderline (spelled-out counts, harmless glosses). Real examples: a value of 37.4 called "within 32–36"; "TSH (hormone of liver stimulation)". |
| E13, E14 | external validity, PK7 | not measured | Need ethics approval / user study. |

---

## 3. Findings worth putting in the thesis

1. **The pre-registered expectation for PK6 was wrong.** Rules were predicted
   to lose on negation and hedging; they scored perfectly because they see
   the full context. The classifier sees less information, so PK6 compares
   two methods on *different* inputs (ADR 0009).
2. **Classifier leakage.** 100% of validation defect sentences share their
   exact shape (numbers and names removed) with a training sentence, and
   every invented finding starts with "Vërehet gjithashtu". E11 on synthetic
   data will measure recognition of the generator's templates, not defect
   detection. The handwritten set B is the only real test (ADR 0009).
3. **OCR is a safety problem, not just an accuracy problem.** A value read
   wrong is interpreted with full confidence; a value not read is safely
   refused (SP5). F1 alone hides this (ADR 0012).
4. **The UI found bugs the metrics did not.** Running scanned documents
   through the interface exposed (a) an interval read as "value + unit" and
   shown to the patient as their measured value, and (b) a rule bug where an
   OCR unit "." split every decimal number — which made the template itself
   fail verification, the NFR1 conflict ADR 0011 predicted. Both fixed.
5. **Several rule bugs were found by hand-built and generated edge cases**,
   not by the corpus: R1 on numbers inside physician quotes, R7 on the SP4
   banner's own vocabulary, R2 on glossary explanations, R5/R6 judging the
   wrong quote (rules r1.1 → r1.3).

6. **A metric defect hid a weak classifier, and a threshold rule hides a useless one.** `PRF.f1` returned `None` for a class the detector missed entirely, and the class average skipped it: a classifier catching nothing in five of seven defect types scored macro F1 0.96. Corrected to 2TP/(2TP+FP+FN); E10 is unchanged. Separately, the threshold rule (max macro F1 over defect types, chosen on validation) ignores false alarms on clean text, so it picks points that block ~98% of clean texts. Both were found after the test split had been seen. The original rule was kept and reported; a second rule (≤5% of clean validation texts blocked, chosen on validation, author's decision) was added beside it, and E9 uses that one. The table in ADR 0009 names both and says the second was added after the test was seen.

7. **The PK5 metric is circular, and the audit shows how much that matters.** Violations are counted with the same rules that block the text, so "0 reach the user" means "0 the rules see". On real model output the rules miss a large share of errors (36% of passed texts have a rule-type problem), mostly direction errors expressed as blanket claims or mis-assigned values, and invented glosses no rule checks. The rules' 0.993 describes the corrupted corpus.
8. **The judge's capability decides E12.** Claude Sonnet is perfect on both samples; Haiku, same protocol, scores 0.625 and 0.514 and agrees with Sonnet on 53% of items. An LLM judge is not automatically better than the rules.
9. **A small free model does a lot with grounding and little without it.** Grounding alone cuts violations from 54 to 9.5 per 100 sentences; the retry fixes about half of the remaining failing documents; the other half pay the template price.

---

## 4. What exists, by area

### Core pipeline — `backend/src/analyte/`
- `domain/` — frozen Pydantic models, enums, safety policy SP1–SP8, rule catalogue (version `r1.3`).
- `ingestion/` — format check, text-layer router, PDF reader, **OCR** (`ocr.py`: deskew, Tesseract `eng/psm6/200dpi`, chosen on a separate tuning corpus).
- `grounding/branch_a/` — extraction, units, LOINC, reference intervals, classification, **combination patterns** (`patterns.py`, table in `resources/patterns.csv`).
- `grounding/branch_b/` — terminology, negation, hedging, assertions, cross-reference.
- `generation/` — `Generator` protocol, deterministic template (the fallback), **`prompt.py`** (`build_prompt(context, feedback)`, version `p1`), **`llm.py`** (`ChatClient` with disk cache, throttling and retry; `GeminiClient`, `OpenAIChatClient` for Mistral/Groq/Cerebras/OpenRouter; `LlmGenerator`).
- `verification/` — rules R1–R9 + SP1-3; `classifier.py` runs a trained model after the rules.
- `orchestration/` — the state machine (Figure 6 as a transition table), regeneration loop, template fallback, job runner, arq worker.

### Service layer
- `api/` — FastAPI: auth (JWT + Argon2, equal-time login failure, **login throttling with IPv6 counted by /64, revocable sessions, single-use refresh tokens with reuse detection, logout and sign-out-everywhere** — ADR 0014; **email confirmation: registration always answers 202 with the same body, the mail is sent after the response, links are single-use, expire, and are stored only as HMAC; registration/resend have their own throttle** — ADR 0016; `mail.py`: SMTP (Mailtrap in development), console, in-memory), upload, history, status, findings, assertions, cross-references, explanation (always with its verification summary), verification details, page images, terminology. Errors as RFC 7807. Chat returns 501.
- `persistence/` — SQLAlchemy tables mirroring the domain (exact decimals), repository with round-trip tests, Alembic migrations `0001`–`0003`, encrypted file storage (Fernet; the filename is encrypted too).
- `audit/` — audit log that structurally cannot record names, emails or lab values.
- Infrastructure: `docker-compose.yml` (PostgreSQL on 5433, Redis), `.env.example`, `Makefile`.

### Frontend — `frontend/`
Next.js 16, Albanian UI: sign-in, upload, history, live processing steps,
critical-value banner (SP4), OCR warning at the top, explanation with a
verification badge, physician quotes set apart, findings table where clicking
a value outlines its source row on the original page, "discuss with your
doctor" contradictions, a full "how this was checked" panel, registration that asks you to check your
email, a `/confirm` page for the link, and "Dil kudo". API types are generated from OpenAPI.

### Evaluation and ML
- `evaluation/` — harness, metrics PK1–PK6, bootstrap CIs (document-level, rule of three at 0 events), ablation pipelines E6–E9 (`ungrounded.py` is the E6 baseline and the only code that shows a model the document text), `llm_judge.py` (API judge), `judge_batches.py` (E12 with Claude subagents), `audit_batches.py` (audit of E8), the response cache `evaluation/cache/`, a guard that refuses to file one ablation under another's ID.
- `evaluation/kits.py` + `evaluation/handwritten/` — the three handwritten sets (A, B, C) with loaders and evaluators ready.
- `ml/` — classifier dataset builder, Colab training script and notebook (`ml/colab/train_xlmr.ipynb`), evaluator (threshold chosen on validation only), leakage report.

### Documentation
- ADRs 0001–0015 (`docs/adr/`).
- `docs/thesis/teza_v3.md`: the full thesis text with the Chapter 5 drafts merged (5.2.1, 5.3, 5.4, 5.8.1, 5.11.2) and corrected against the code; the original `teza_v2.md` is untouched. Appendices A–I in `docs/thesis/appendices/` (`python scripts/build_appendices.py`).
- Tables T1–T5 generated from source (`scripts/build_tables.py`).
- Figures 6, 7, 8 and 11 generated from code (`python scripts/build_figures.py` → `docs/thesis/figures/`, PNG + SVG): the state machine from `TRANSITIONS`, the ER diagram from the table metadata, the module dependency matrix from real imports, and the evaluation pipeline with each experiment's status taken from the result files that exist. Figures 1–5, 9 and 10 (concept diagrams, `scripts/figures/concepts.py`) take the numbers and names in their boxes from the catalogue (rules, defect types, cross-reference states, attempt limit, analyte/term/pattern counts) and tests check them; Figures 18–21 (`scripts/figures/results.py`) read the result files and fail if one is missing. They are drawings of measured values, not measurements; the layout is by hand and was checked by eye.

---

## 5. Decisions the author made

| Date | Decision |
|---|---|
| 2026-09-27 | Do not harden the synthetic corpus; state the PK1 limitation and rely on E13. |
| 2026-09-27 | Train XLM-R on Colab. |
| 2026-09-27 | Skip the LLM for now (the template is the generator). |
| 2026-09-28 | No `.claude/` folder in the repository. |
| 2026-09-30 | Report both E11 threshold rules: best macro F1, and a 5% false-alarm budget chosen on validation. |
| 2026-10-02 | Write set B themselves (replacing a model-drafted version), and finish the thesis "tonight" — scoped to what does not need an LLM, ethics or a user study. |
| 2026-10-03 | Use a free provider only: Gemini (20 requests/day) and Cerebras/OpenAI/Anthropic were ruled out; generator is Mistral `ministral-14b-2512` on the free plan (ADR 0015). |
| 2026-10-03 | Use Claude (Sonnet, with Haiku as a check) as the E12 judge through Claude Code subagents instead of an API; add an independent audit of E8. |
| 2026-10-04 | Set C (60 narrative sentences) accepted as the author's own (declared). A second narrative set (C2) was drafted and then **dropped by the author — do not use or suggest it**; it was deleted from the repository. |
| 2026-10-05 | **The model is wired into the web app** (ADR 0017): opt-in `ANALYTE_SERVICE_GENERATOR=model`, no disk cache, same verify/retry/fallback cycle, a `model` notice in the UI. Off by default because `.env` already holds the provider for the experiments and that alone must not send real uploads to a provider. |
| 2026-10-04 | The chat stays "not built" (future work). Registration gets email confirmation through Mailtrap; the other ADR 0014 gaps (IPv6 /64, sign-out-everywhere) are fixed after it; the thesis is changed to say what was actually built (§5.7 classifier: defect type, not NLI; §5.12: audit log vs processing trace, account system). |
| 2026-10-04 | Set A: the author will rewrite it. Two submitted versions were not installed (a verbatim reformatting of the contexts; then templated prose with five rotating openers and meta-sentences about the conversion). |

---

## 6. Waiting on the author

| # | Item | Unblocks |
|---|---|---|
| 1 | **Decide how the thesis describes how set B was prepared**, given that 12 of its 105 rows (doctor quotes only) coincide with an earlier model-drafted version (disclosed in `evaluation/handwritten/README.md` and ADR 0009) | the PK6 section of Chapter 6 |
| 2 | **Handwritten set A** (`evaluation/handwritten/A_shpjegimet.md`, currently empty). Write in your own words from `A_kontekstet.md` only, one section per context (`## A01`…). About **10 genuinely different explanations are worth more than 25 templated ones** (the evaluator accepts any number). Each: critical-value notice first when there is one (SP4); only numbers, analytes and terms present in the context; no diagnosis/treatment/prognosis; a value without an interval is said to be uninterpreted (SP5); a term marked "does not explain" is named but not explained (SP6); **each doctor statement as its own sentence in the form `Mjeku ka shënuar: “…”.`** (not a bullet list without periods), with negation, hedge and recommendation intact; a closing note for the health professional in your own words. Then run `python -m evaluation.kits check` and look at every flag. | the rules' false-alarm rate on natural prose; an Albanian baseline for the model |
| 3 | **OCR plausibility check** — add sourced physiological limits, or declare the scanned channel unsafe to interpret | the 62 wrong-direction / 11 false-critical cases |
| 4 | **Sources for the 11 combination rules** (`resources/patterns.csv`, column `source_ref`, all `[REFERENCË — plotësohet]`): P01 Hb↓+ferritin↓, P02 Hb↓+MCV↓, P03 Hb↓+B12↓, P04 glucose↑+HbA1c↑, P05 creatinine↑+urea↑, P06 ALT↑+AST↑, P07 ALP↑+GGT↑, P08 TSH↑+fT4↓, P09 TSH↓+fT4↑, P10 WBC↑+CRP↑, P11 LDL↑+HDL↓. For each, a guideline or standard laboratory-medicine reference **you have read** (society guidelines for anaemia, diabetes, thyroid, kidney, liver, lipids are the kinds to look in); confirm the arrow directions; have your mentor or a clinician review; remove any rule you cannot source. Never cite what you have not read. | patterns in the thesis |
| 5 | **Sources for the 82 terminology entries** (`resources/terminology.csv`, column `source_ref`, all `[BURIMI — plotësohet…]`; 46 conditions, 17 measurements, 7 processes, 12 others): one source per term that supports the Albanian lay explanation in `explanation_sq` (kinds to look in: MeSH descriptors, MedlinePlus, NHS patient pages for plain-language definitions; LOINC documentation for what a test measures; say when the Albanian wording is your own translation). A term you cannot source should be **deleted** — it then becomes an "unexplained term" (SP6). Check that no explanation contains a number or a diagnostic claim. | T3, SP6 credibility |
| 6 | A **second judge independent of the system's builder** (or a human) for E12 and the audit; a human Albanian speaker's reading of ~20 generated explanations | PK3, the independence caveats in §6.7.2 |
| 7 | Ethics submission | E13 |
| ~~7b~~ | ~~Mailtrap credentials~~ **done 2026-10-05**: a real registration went through the Mailtrap sandbox, the message arrived, the link confirmed the account (ADR 0016). Not tested: a production SMTP provider or delivery to a real mailbox. | — |
| 7c | **Decide the data-protection side before turning the model on for real documents**: the provider's free-plan terms on storing and training on inputs, patient consent, whether doctor quotes must be de-identified first (ADR 0017, `docs/ethics/skica_e_paraqitjes.md`). The switch is off by default. | E13, using the model on real uploads |
| 8 | Chapter 3 and the reference list, review of `teza_v3.md` (Chapters 6–7 and the Abstract are written from the result files and need your reading), the cover page, and the thesis **title**: it says the explanations are "generated by large language models", which is accurate now (`ministral-14b-2512` was used) — confirm it is the title you want and that it promises no more than the thesis shows (no real documents, no user study) | the thesis |

---

## 7. Possible next steps without the author

1. ~~Draw Figures 18–21 and 1–5, 9, 10~~ **done 2026-10-04** (see §4); look at them and say what to change.
2. ~~Screenshots (Figures 12–16)~~ **done 2026-10-05**: `python scripts/export_screenshots.py` (`pip install -e ".[screenshots]"`; Playwright with the bundled Chromium or an installed Edge/Chrome, `--channel msedge`). It starts the API in-process (throwaway SQLite, in-memory mailer, the deterministic template) and the Next dev server, registers and confirms a test user, signs in through the form, uploads a synthetic digital document with a critical value and a report–lab contradiction (`doc_00335.pdf`, chosen from the corpus truth), and saves five PNGs. They show the template's explanation: the script builds its own services with the template so the images do not depend on an outside provider.
3. ~~ADR 0014 gaps~~ **done 2026-10-04** (ADR 0016). What the account system still does not have: password reset, two-factor login, automatic resend of a mail lost after the token was saved, a `Referrer-Policy` header on the confirm page; all listed in ADR 0016 and §7.6 item 11.
4. Audit E9's delivered texts the same way as E8's, to see whether the classifier catches real errors the rules miss; add a rules + LLM-judge combination condition; re-run E10/E11 from a clean checkout (they now record the git state, §7b).

---

## 7b. Traceability

Re-run on 2026-10-02 from a clean checkout of `37b5be4` (`working_tree_dirty: false`), results written outside the checkout so no run taints the next:

- **E1, E2, E3, E5, E7, E8, E9 now have `result.json` with a real git sha.** E2, E3 and E5 reproduce the earlier values exactly (0.670, 0.881, 0.863); the only differences from the committed files are one last-digit float and `None` → `0.0` for classes with false positives and no support (the F1 correction, ADR 0009).
- Supplementary numbers quoted in Chapter 5 (E3 and E5 on the digital subset, E5 without OCR) are in `evaluation/results/supplementary/ch5_digital_and_no_ocr.json`.
- **Model experiments (2026-10-04):** E4, E6, E7, E8 and E9 re-run from a clean checkout of `4f5ea17` (`working_tree_dirty: false`), reading the committed response cache; results in `evaluation/results/llm/`. E7, E8, E9 and E4 reproduce the development run exactly with 0 new calls. E6 made 2 new calls (two documents without a valid response in the first run; failed calls are never cached) and differs from the development run by 0.05/100 (54.385 vs 54.439): the two added documents and, probably, a few documents generated twice concurrently while the cache was filled in parallel (cause not isolated); the clean-checkout number is the one reported.
- **E12 and the audit have no git sha:** they are scored by `judge_batches.py`/`audit_batches.py` from the saved `answers_*.jsonl` and the key files in `evaluation/cache/`; the judge is not deterministic.
- **E10 and E11 provenance: done 2026-10-05.** Re-run from a clean worktree of `34fa710` (`working_tree_dirty: false`); metrics identical to the committed ones for E10 and both E11 inputs; `evaluation/results/E10/result.json` and `E11/{sentence,context}/result.json` now carry the git sha and a dataset id (E10: generator version, seed, size and a line-ending-independent checksum of the source tables; E11: a checksum of the Colab predictions it read). Figure 11 shows them `e plotë`; E4/E6 also show `e plotë` now that the figure reads `results/llm/`, and E12 shows `pjesore` (a judge result has no git sha). Still without metadata: `kit_B.json` (classifier and judge results on set B), the rules' set-B result (recomputed by `python -m evaluation.kits check`), E12 and the audit. Procedure for a future re-run: `git worktree add --detach <dir> HEAD`, junction `data/` and `ml/artifacts/`, `PYTHONPATH=<dir>/backend/src;<dir>`, `python -m ml.evaluate_rule_detector --n 200 --split test --out <out>/E10` and `python -m ml.evaluate_classifier --run ml/artifacts/runs/{sentence,context} --out <out>/E11`, then copy only the three `result.json` files.
- **The corpus manifest's resource checksums are tied to the author's working copy, not to git.** `data/v1/manifest.json` records SHA-256 of the raw bytes of `resources/*.csv`. For `terminology.csv` and `patterns.csv` (mixed line endings in the working copy, converted by `core.autocrlf=true`) a fresh checkout has different bytes and does not match the manifest; the other three tables match. The harness reads the version from the manifest and never re-hashes, so no result is affected, but the corpus version `gen-1.0/s42/n500/37d8b080` cannot be re-derived from a fresh checkout on this machine. Changing the generator's hash to ignore line endings would change the corpus version (and every result's `dataset.version`), so it was **not done**; the decision (leave, or normalise and re-stamp) is the author's.
- **Package-level cycle `audit ↔ orchestration ↔ persistence`** (Figure 8): `audit.logger` imports `orchestration.states.Transition`, and `persistence.repository` imports `Delivery`/`Explanation` from `orchestration.process`, while `orchestration.tasks` imports both. There is no cycle at module level. Moving those three types into `domain/` would remove it; §5.9 of `teza_v3.md` now states the cycle.

---

## 8. Running it

```bash
pip install -e ".[dev,generate,api]"
python -m pytest

cp .env.example .env                # fill in the two secrets
docker compose up -d --wait         # PostgreSQL (5433) + Redis
cd backend && alembic upgrade head && cd ..
uvicorn analyte.main:app --reload --app-dir backend/src
arq analyte.orchestration.worker.WorkerSettings          # second terminal
cd frontend && npm install && npm run dev                # http://localhost:3000

python -m evaluation.harness --dataset data/v1 --pipeline grounding --ocr
python -m evaluation.harness --dataset data/v1 --generator llm --ocr --pipeline e8 --experiment E8   # needs ANALYTE_LLM_* in .env
python scripts/build_chapter6_tables.py
python -m ml.evaluate_rule_detector --n 200 --split test
python -m evaluation.kits check
```
