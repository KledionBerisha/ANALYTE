# ANALYTE — progress so far

*State as of 2026-10-02, on top of commit `37b5be4`. Everything described below that is newer than that commit — set B, the clean-checkout re-runs, the appendix builder, `teza_v3.md`, the classifier-on-B evaluator — is in the working tree and not yet committed.*

ANALYTE extracts laboratory values and physician statements from Albanian
medical PDFs, interprets them deterministically, writes a patient-facing
explanation that may use only that interpretation (`GroundingContext`), and
verifies the explanation automatically before anyone sees it.

**Tests:** all pass (`python -m pytest`), plus 1 PostgreSQL integration test (`make test-postgres`, run against migration 0002 on 2026-09-30).
**Architecture decisions:** 14 ADRs in `docs/adr/`.

## Where we stand

| | |
|---|---|
| **Done and verified** | The whole system (extraction incl. OCR, interpretation, patterns, narrative branch, verification rules, state machine, API with hardened auth, frontend). Evaluation infrastructure with provenance. XLM-R trained and measured. Experiments E1, E2, E3, E5, E7, E8, E9, E10, E11 and set B measured, all re-runnable. Figures 6, 7, 8, 11 and Appendices A–I generated from code. `teza_v3.md` = Chapter 5 merged and corrected. |
| **Measured, with the honest reading** | The rules reach macro F1 **0.993** on the synthetic corpus but **0.795** on the author's natural-sentence set B (weak spots: diagnosis/treatment/prognosis, short direction phrases, unexplained-term explanations). The trained classifier is **close to useless on natural text** (0.015–0.177) and false-alarms on OCR text (E9: 10.2% of documents). OCR reads 125 of 2 370 values wrong and accepts them. |
| **Blocked on an LLM** | The central experiment (does verification lower the rate of unsupported claims, PK5: E6–E9), E4, E12, the chat feature. With the template as generator E7/E8 are boundary checks only. |
| **Not done** | Real documents (E13, no ethics approval), user study (E14/PK7), Chapters 6 and 7 (skeletons), Abstract and §7.6 not adapted to what was really done, Chapter 3 and 40–60 references, sources for the 82 terms and 11 combination rules, handwritten sets A and C, figures 1–5, 9, 10, 12–21. |

---

## 1. Phase status

| Phase (spec §6) | State |
|---|---|
| Domain contract | ✅ done |
| 2 — Synthetic corpus generator | ✅ done — 38 analytes, 3 layouts, scan simulation, reproducible from a seed |
| 3 — Evaluation infrastructure | ✅ done — harness, E1–E15 matrix, provenance, bootstrap 95% CIs |
| 4 — Branch A (lab values) | ✅ done — digital + **OCR** (Tesseract), combination patterns P01–P11 |
| 5 — Branch B (physician narrative) | ✅ done — terms, negation, hedging, cross-reference |
| 6 — Generation + verification | ⚠️ rules R1–R9 + SP1-3, state machine, regeneration, template fallback done — **no LLM yet** (by decision) |
| 7 — ML classifier | ✅ trained on Colab and measured on 2026-09-30 (E11) — far weaker than the rules; both threshold rules are reported (author's decision, 5% false-alarm budget) |
| 8 — Ablation | ⚠️ E7/E8/E9 run with the template as generator (boundary checks); the real ablation (E6–E9) **needs an LLM** |
| 9 — Web application | ✅ backend + frontend done (chat not built — needs LLM) |
| 10 — User study (PK7) | ⛔ not started |
| 11 — Analysis / discussion | ⛔ not started |
| 12 — Thesis writing | ⚠️ `docs/thesis/teza_v3.md`: Chapter 5 merged and corrected against the code, Appendices A–I generated; Chapters 6–7 still skeletons, Abstract and §7.6 not yet adapted, Chapter 3 incomplete |
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
| E7, E8 | PK5 conditions B and C with the template as generator, OCR on, 500 docs | **0.000 violations/100 sentences** each (95% ≤ 0.021) | Boundary checks, not results: the template never errs, so verification has nothing to remove. They prove the loop and metric work end to end. |
| E9 | same, plus the sentence classifier at threshold 0.85 (rule 2) | **0.515 violations/100 sentences reaching the user** (95% CI 0.37–0.66); 158 sentences flagged in 51 documents (10.2%) → template fallback | **All are false alarms** (the generator is the template), all `ungrounded_analyte`. They come from scanned documents: OCR-garbled units ("midi", "ugidl", "umolL") get flagged. Probe: 12 of 40 scanned documents flagged vs 0 of the digital ones sampled. The 5% budget chosen on clean digital validation text (0% blocked) does **not** transfer to the OCR channel. |
| E10 | PK6 rules detector, 192 test samples | **macro F1 0.993**, 0 false alarms | Rules were fixed (r1.1–r1.3) after the test split was first measured (0.979). The fixes came from hand-built contexts and the UI, not from test errors — but this must be said. |
| E11 | PK6 classifier, same 192 texts as E10 | **Rule 1** (max macro F1): sentence **0.481**, sentence + context **0.538**, but it blocks **30/30 and 29/30 clean texts**. **Rule 2** (≤5% of clean validation texts blocked): sentence **0.385** (0/30 clean blocked), context **0.326** (2/30 blocked — 6.7%, above the 5% budget on the test set). | Far below the rules (0.993). Within the budget it catches nothing for `polarity_flip` and `direction_mismatch` (F1 0.00). Its perfect class, `fabricated_finding`, is a template artifact (leakage report). Measured after a metric correction, and rule 2 was added after the test split had been seen — both disclosed in ADR 0009. E9 uses rule 2. |
| **Set B** (105 natural sentences, submitted by the author) | PK6 on prose the generator did not produce | **Rules: macro F1 0.795**, 1/30 clean flagged. Classifier: sentence 0.053 (rule 1) / 0.015 (rule 2); sentence + context 0.177 / 0.104 | The real test: rules fall from 0.993 (synthetic) to 0.795; the classifier is close to useless. Rules per type — `polarity_flip`, `hedge_removed`, `ungrounded_analyte` 1.00; `ungrounded_number`, `fabricated_finding` 0.95; `direction_mismatch` 0.67; `prohibited_claim` 0.46; `ungrounded_term_explanation` **0.33 (1 of 5)**. **12 of 105 rows (doctor quotes only) are identical to rows of an earlier model-drafted version** — disclosed in `evaluation/handwritten/README.md` and ADR 0009; no duplicate rows. The evaluator was changed after a first 0/20 reading on quote rows (ADR 0009). 9 of 105 share a shape with training sentences; 0 verbatim in the template. |
| E4, E6, E12 | PK3, PK5, PK6 | not measured | Need the LLM. Pipelines and metrics exist and are tested. |
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

---

## 4. What exists, by area

### Core pipeline — `backend/src/analyte/`
- `domain/` — frozen Pydantic models, enums, safety policy SP1–SP8, rule catalogue (version `r1.3`).
- `ingestion/` — format check, text-layer router, PDF reader, **OCR** (`ocr.py`: deskew, Tesseract `eng/psm6/200dpi`, chosen on a separate tuning corpus).
- `grounding/branch_a/` — extraction, units, LOINC, reference intervals, classification, **combination patterns** (`patterns.py`, table in `resources/patterns.csv`).
- `grounding/branch_b/` — terminology, negation, hedging, assertions, cross-reference.
- `generation/` — `Generator` protocol, deterministic template (the fallback and the current generator).
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
- `evaluation/` — harness, metrics PK1–PK6, bootstrap CIs (document-level, rule of three at 0 events), E7/E8/E9 pipelines, a guard that refuses to file one ablation under another's ID.
- `evaluation/kits.py` + `evaluation/handwritten/` — the three handwritten sets (A, B, C) with loaders and evaluators ready.
- `ml/` — classifier dataset builder, Colab training script and notebook (`ml/colab/train_xlmr.ipynb`), evaluator (threshold chosen on validation only), leakage report.

### Documentation
- ADRs 0001–0014 (`docs/adr/`).
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

---

## 6. Waiting on the author

| # | Item | Unblocks |
|---|---|---|
| 1 | **Decide how the thesis describes how set B was prepared**, given that 12 of its 105 rows (doctor quotes only) coincide with an earlier model-drafted version (disclosed in `evaluation/handwritten/README.md` and ADR 0009) | the PK6 section of Chapter 6 |
| 2 | Handwritten set **A** — 25 explanations (`A_shpjegimet.md`, currently empty) | false-alarm rate on natural text; LLM quality baseline |
| 4 | Handwritten set **C** — ~60 physician sentences (`C_narrativa.csv`, empty) | Branch B outside the generator's vocabulary |
| 5 | **OCR plausibility check** — add sourced physiological limits, or declare the scanned channel unsafe to interpret | the 62 wrong-direction / 11 false-critical cases |
| 6 | Confirm the 11 combinations in T5 and give each a source | patterns in the thesis |
| 7 | Sources for the 82 terminology entries | T3, SP6 credibility |
| 8 | LLM provider (when ready) and the Albanian LLM quality test | PK3, PK5, chat |
| 9 | Ethics submission | E13 |
| 10 | Chapter 3, Abstract and §7.6 (adapt to what was really done), review of `teza_v3.md`, remaining figures | the thesis |

---

## 7. Possible next steps without the author

1. Figures still to draw by hand or by script: 1 (phases), 2–5 (architecture and pipelines), 9–10 (corpus generation, corrupted corpus).
2. A reproducible script that exports the six thesis screenshots (Figures 12–17) from the running UI.
3. Remaining gaps recorded in ADR 0014: registration still reveals whether an email has an account (409), no "sign out everywhere", and IPv6 /64 rotation weakens the per-address limits.
4. Chapter 5/6 drafts for the service layer, the interface, OCR, and a results section generated from `evaluation/results/`.

---

## 7b. Traceability

Re-run on 2026-10-02 from a clean checkout of `37b5be4` (`working_tree_dirty: false`), results written outside the checkout so no run taints the next:

- **E1, E2, E3, E5, E7, E8, E9 now have `result.json` with a real git sha.** E2, E3 and E5 reproduce the earlier values exactly (0.670, 0.881, 0.863); the only differences from the committed files are one last-digit float and `None` → `0.0` for classes with false positives and no support (the F1 correction, ADR 0009).
- Supplementary numbers quoted in Chapter 5 (E3 and E5 on the digital subset, E5 without OCR) are in `evaluation/results/supplementary/ch5_digital_and_no_ocr.json`.
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
python -m ml.evaluate_rule_detector --n 200 --split test
python -m evaluation.kits check
```
