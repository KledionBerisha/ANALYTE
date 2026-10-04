# ANALYTE — progress so far

*State as of 2026-10-04, on top of commit `4f5ea17` (LLM generation, E4/E6–E9 with the real model, E12 judges and the batch tooling are committed there). Newer and not yet committed: the independent audit of E8 (`evaluation/audit_batches.py`, `evaluation/results/llm/AUDIT_E8/`, `evaluation/cache/audit_e8/`), ADR 0015, the LLM section of the README, Chapter 6/7 rewritten around the model results (Abstract, §6.4, §6.6, §6.7, §6.10, §7.1, §7.3, §7.6, §7.8, Appendix D regenerated from the real prompts), and `scripts/build_chapter6_tables.py` extended to the LLM results.*

ANALYTE extracts laboratory values and physician statements from Albanian
medical PDFs, interprets them deterministically, writes a patient-facing
explanation that may use only that interpretation (`GroundingContext`), and
verifies the explanation automatically before anyone sees it.

**Tests:** 539 pass, 1 skipped (`python -m pytest`, 2026-10-04), plus 1 PostgreSQL integration test (`make test-postgres`, run against migration 0002 on 2026-09-30).
**Architecture decisions:** 15 ADRs in `docs/adr/` (0015: the language model, prompt, cache and judges).

## Where we stand

| | |
|---|---|
| **Done and verified** | The whole system (extraction incl. OCR, interpretation, patterns, narrative branch, verification rules, state machine, API with hardened auth, frontend) and the **language-model path**: client with response cache (`ministral-14b-2512`, Mistral free plan), versioned prompt `p1`, E6 baseline, Claude-judge batches, independent audit. Experiments E1–E12 and set B measured, all re-runnable; the model experiments were re-run from a clean checkout of `4f5ea17` with no new calls (E6: 2, for two documents that had no valid response the first time). |
| **Measured, with the honest reading** | The rules reach macro F1 **0.993** on the synthetic corpus but **0.795** on the author's natural-sentence set B (weak spots: diagnosis/treatment/prognosis, short direction phrases, unexplained-term explanations). The trained classifier is **close to useless on natural text** (0.015–0.177) and false-alarms on OCR text (E9: 10.2% of documents). OCR reads 125 of 2 370 values wrong and accepts them. |
| **Main result (PK5)** | Violations reaching the user, per 100 sentences, with the real model: **54.4** without grounding (E6), **9.5** grounded (E7), **0.000** (95% ≤ 0.034) grounded + rules + one retry (E8) — at the price of **25%** of documents falling back to the template; the sentence classifier (E9) raises that to 60% for no measured gain. **The 0.000 counts only what the rules see**: the independent audit of 90 delivered texts finds a rule-type problem in **36% (26–46%)**, direction errors in 23%, and some problem of any kind in 58%. H1 holds in the measured form, not as a guarantee; H2 is not confirmed. |
| **Not done** | Real documents (E13, no ethics approval), user study (E14/PK7), local model (E15), expert review, Chapter 3 and 40–60 references, sources for the 82 terms and 11 combination rules, handwritten sets A and C, the OCR plausibility check, chat, figures 1–5, 9, 10, 12–21 (18–21 can now be drawn from the results), a second judge independent of the system's builder. |

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
| 9 — Web application | ✅ backend + frontend done (the service can use the model, but chat is not built) |
| 10 — User study (PK7) | ⛔ not started |
| 11 — Analysis / discussion | ⛔ not started |
| 12 — Thesis writing | ⚠️ `docs/thesis/teza_v3.md`: Chapters 5, 6 and 7 written from the code and the result files (H1 confirmed in the measured form only, H2 not confirmed), Abstract, §7.1/§7.3/§7.6/§7.8 and Appendices A–I done; Chapter 3 incomplete, 4 references verified, Figures 12–21 not drawn |
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
- `api/` — FastAPI: auth (JWT + Argon2, equal-time login failure, **login throttling, revocable sessions, single-use refresh tokens with reuse detection, logout** — ADR 0014), upload, history, status, findings, assertions, cross-references, explanation (always with its verification summary), verification details, page images, terminology. Errors as RFC 7807. Chat returns 501.
- `persistence/` — SQLAlchemy tables mirroring the domain (exact decimals), repository with round-trip tests, Alembic migration `0001`, encrypted file storage (Fernet; the filename is encrypted too).
- `audit/` — audit log that structurally cannot record names, emails or lab values.
- Infrastructure: `docker-compose.yml` (PostgreSQL on 5433, Redis), `.env.example`, `Makefile`.

### Frontend — `frontend/`
Next.js 16, Albanian UI: sign-in, upload, history, live processing steps,
critical-value banner (SP4), OCR warning at the top, explanation with a
verification badge, physician quotes set apart, findings table where clicking
a value outlines its source row on the original page, "discuss with your
doctor" contradictions, and a full "how this was checked" panel. API types
are generated from OpenAPI.

### Evaluation and ML
- `evaluation/` — harness, metrics PK1–PK6, bootstrap CIs (document-level, rule of three at 0 events), ablation pipelines E6–E9 (`ungrounded.py` is the E6 baseline and the only code that shows a model the document text), `llm_judge.py` (API judge), `judge_batches.py` (E12 with Claude subagents), `audit_batches.py` (audit of E8), the response cache `evaluation/cache/`, a guard that refuses to file one ablation under another's ID.
- `evaluation/kits.py` + `evaluation/handwritten/` — the three handwritten sets (A, B, C) with loaders and evaluators ready.
- `ml/` — classifier dataset builder, Colab training script and notebook (`ml/colab/train_xlmr.ipynb`), evaluator (threshold chosen on validation only), leakage report.

### Documentation
- ADRs 0001–0015 (`docs/adr/`).
- `docs/thesis/teza_v3.md`: the full thesis text with the Chapter 5 drafts merged (5.2.1, 5.3, 5.4, 5.8.1, 5.11.2) and corrected against the code; the original `teza_v2.md` is untouched. Appendices A–I in `docs/thesis/appendices/` (`python scripts/build_appendices.py`).
- Tables T1–T5 generated from source (`scripts/build_tables.py`).
- Figures 6, 7, 8 and 11 generated from code (`python scripts/build_figures.py` → `docs/thesis/figures/`, PNG + SVG): the state machine from `TRANSITIONS`, the ER diagram from the table metadata, the module dependency matrix from real imports, and the evaluation pipeline with each experiment's status taken from the result files that exist.

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

---

## 6. Waiting on the author

| # | Item | Unblocks |
|---|---|---|
| 1 | **Decide how the thesis describes how set B was prepared**, given that 12 of its 105 rows (doctor quotes only) coincide with an earlier model-drafted version (disclosed in `evaluation/handwritten/README.md` and ADR 0009) | the PK6 section of Chapter 6 |
| 2 | Handwritten set **A** — 25 explanations (`A_shpjegimet.md`, currently empty) | false-alarm rate on natural text; LLM quality baseline |
| 4 | ~~Handwritten set C~~ **done 2026-10-04** (60 rows, author's declaration); handwritten set **A** is still empty — a file submitted the same day was a reformatting of the contexts and was not installed | false-alarm rate on natural prose; LLM quality baseline |
| 5 | **OCR plausibility check** — add sourced physiological limits, or declare the scanned channel unsafe to interpret | the 62 wrong-direction / 11 false-critical cases |
| 6 | Confirm the 11 combinations in T5 and give each a source | patterns in the thesis |
| 7 | Sources for the 82 terminology entries | T3, SP6 credibility |
| 8 | A **second judge independent of the system's builder** (or a human) for E12 and the audit; a human Albanian speaker's reading of ~20 generated explanations | PK3, the independence caveats in §6.7.2 |
| 9 | Ethics submission | E13 |
| 10 | Chapter 3, §7.1/§7.3/§7.8, review of `teza_v3.md` (Chapter 6 and the new Abstract/§7.6 are written from the result files and need your reading), remaining figures, and the thesis **title**, which still says the explanations are "generated by large language models" although no LLM was used | the thesis |

---

## 7. Possible next steps without the author

1. Figures still to draw by hand or by script: 1 (phases), 2–5 (architecture and pipelines), 9–10 (corpus generation, corrupted corpus), and now 18–21 (ablation, confusion matrices, violation types) from `evaluation/results/`.
2. A reproducible script that exports the six thesis screenshots (Figures 12–17) from the running UI.
3. Remaining gaps recorded in ADR 0014: registration still reveals whether an email has an account (409), no "sign out everywhere", and IPv6 /64 rotation weakens the per-address limits.
4. Audit E9's delivered texts the same way as E8's, to see whether the classifier catches real errors the rules miss; add a rules + LLM-judge combination condition; re-run E10/E11 from a clean checkout with git state recorded.

---

## 7b. Traceability

Re-run on 2026-10-02 from a clean checkout of `37b5be4` (`working_tree_dirty: false`), results written outside the checkout so no run taints the next:

- **E1, E2, E3, E5, E7, E8, E9 now have `result.json` with a real git sha.** E2, E3 and E5 reproduce the earlier values exactly (0.670, 0.881, 0.863); the only differences from the committed files are one last-digit float and `None` → `0.0` for classes with false positives and no support (the F1 correction, ADR 0009).
- Supplementary numbers quoted in Chapter 5 (E3 and E5 on the digital subset, E5 without OCR) are in `evaluation/results/supplementary/ch5_digital_and_no_ocr.json`.
- **Model experiments (2026-10-04):** E4, E6, E7, E8 and E9 re-run from a clean checkout of `4f5ea17` (`working_tree_dirty: false`), reading the committed response cache; results in `evaluation/results/llm/`. E7, E8, E9 and E4 reproduce the development run exactly with 0 new calls. E6 made 2 new calls (two documents without a valid response in the first run; failed calls are never cached) and differs from the development run by 0.05/100 (54.385 vs 54.439): the two added documents and, probably, a few documents generated twice concurrently while the cache was filled in parallel (cause not isolated); the clean-checkout number is the one reported.
- **E12 and the audit have no git sha:** they are scored by `judge_batches.py`/`audit_batches.py` from the saved `answers_*.jsonl` and the key files in `evaluation/cache/`; the judge is not deterministic.
- **Still open:** E10's result has no provenance metadata (no git sha, no corpus version), and E11's was computed from Colab predictions with evaluation code that was uncommitted when it ran. Re-run `python -m ml.evaluate_rule_detector --n 200 --split test` and the two `ml.evaluate_classifier` commands after committing, and add the git state to their output.
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
