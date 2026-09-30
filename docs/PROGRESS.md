# ANALYTE — progress so far

*State as of 2026-09-30, on top of commit `3ab94e7`. The security hardening (ADR 0014) and the generated figures are in the working tree, not yet committed.*

ANALYTE extracts laboratory values and physician statements from Albanian
medical PDFs, interprets them deterministically, writes a patient-facing
explanation that may use only that interpretation (`GroundingContext`), and
verifies the explanation automatically before anyone sees it.

**Tests:** 438 pass, plus 1 PostgreSQL integration test (`make test-postgres`, run against migration 0002 on 2026-09-30).
**Architecture decisions:** 14 ADRs in `docs/adr/`.

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
| 7 — ML classifier | ⚠️ data, Colab notebook, evaluator, leakage report, runtime integration done — **training not run yet** |
| 8 — Ablation | ⚠️ E7/E8/E9 pipelines ready — needs LLM + trained classifier |
| 9 — Web application | ✅ backend + frontend done (chat not built — needs LLM) |
| 10 — User study (PK7) | ⛔ not started |
| 11 — Analysis / discussion | ⛔ not started |
| 12 — Thesis writing | ⚠️ Chapter 5 section drafts in `docs/thesis/`, not merged into `teza_v2.md` |
| 0 / 1 — ethics, mentor, Chapter 3 | author's side |

---

## 2. Measured results

Every number is from `evaluation/results/<experiment>/result.json` on the
corpus `gen-1.0/s42/n500/37d8b080` (500 documents, 168 scanned) unless noted.

| Experiment | Question | Result | How to read it |
|---|---|---|---|
| E1 | PK1 extraction, digital | **F1 1.000** | Measures wiring, not difficulty: the generator draws clean text at known coordinates. Stated as a limitation; external validity rests on E13. |
| E2 | PK1 extraction, scanned (OCR) | **F1 0.670** | Value precision 0.947 — **125 of 2 370 values read from scans are wrong and accepted**. |
| E3 | PK2 status classification, all docs, OCR | **0.881** | 62 values get the wrong direction, **11 are falsely "critical"** — all from lost decimal separators ("15,7" → "157"). |
| E5 | PK4 cross-reference | 1.000 digital · **0.656** whole corpus without OCR · **0.863** with OCR | The old draft value 0.563 had no recorded corpus and was replaced. |
| E8 | PK5 with the template as generator | **0.000 violations/100 sentences** (95% ≤ 0.136) | A boundary check, not a result: proves the loop and metric work end to end. |
| E10 | PK6 rules detector, 192 test samples | **macro F1 0.993**, 0 false alarms | Rules were fixed (r1.1–r1.3) after the test split was first measured (0.979). The fixes came from hand-built contexts and the UI, not from test errors — but this must be said. |
| E4, E6, E7, E9, E11, E12 | PK3, PK5, PK6 | not measured | Need the LLM or the trained classifier. Pipelines and metrics exist and are tested. |
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
- ADRs 0001–0013 (`docs/adr/`).
- Chapter 5 drafts: 5.2, 5.3 (incl. patterns and OCR), 5.4, 5.8 (incl. the decision not to harden the corpus), 5.11 (incl. CIs and the ablation guard).
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

---

## 6. Waiting on the author

| # | Item | Unblocks |
|---|---|---|
| 1 | Run `ml/colab/train_xlmr.ipynb` and return `results.zip` | E11, then E9 |
| 2 | Handwritten set **A** — 25 explanations (`A_shpjegimet.md`, currently empty) | false-alarm rate on natural text; LLM quality baseline |
| 3 | Handwritten set **B** — ~105 sentences (`B_fjalite.csv`, empty) | the only non-template PK6 test |
| 4 | Handwritten set **C** — ~60 physician sentences (`C_narrativa.csv`, empty) | Branch B outside the generator's vocabulary |
| 5 | **OCR plausibility check** — add sourced physiological limits, or declare the scanned channel unsafe to interpret | the 62 wrong-direction / 11 false-critical cases |
| 6 | Confirm the 11 combinations in T5 and give each a source | patterns in the thesis |
| 7 | Sources for the 82 terminology entries | T3, SP6 credibility |
| 8 | LLM provider (when ready) and the Albanian LLM quality test | PK3, PK5, chat |
| 9 | Ethics submission | E13 |
| 10 | Chapter 3, figures, merging `ch05_*.md` into `teza_v2.md` | the thesis |

---

## 7. Possible next steps without the author

1. Figures still to draw by hand or by script: 1 (phases), 2–5 (architecture and pipelines), 9–10 (corpus generation, corrupted corpus).
2. A reproducible script that exports the six thesis screenshots (Figures 12–17) from the running UI.
3. Remaining gaps recorded in ADR 0014: registration still reveals whether an email has an account (409), no "sign out everywhere", and IPv6 /64 rotation weakens the per-address limits.
4. Chapter 5/6 drafts for the service layer, the interface, OCR, and a results section generated from `evaluation/results/`.

---

## 7b. Traceability gaps the generated figures exposed

- **E1 and E8 have no `result.json`** in `evaluation/results/`, although §2 cites their values. Figure 11 shows them as "gati", not "i matur". Re-run them (`python -m evaluation.harness …`) so the numbers have a file behind them.
- **E2, E3 and E5 were produced with uncommitted changes** (`working_tree_dirty: true` at `ba2c96b`), so the recorded git sha does not identify the code that made them. Re-run from a clean commit before quoting them in the thesis.
- **E10's result has no provenance metadata** (no git sha, no corpus version), unlike the harness results.
- **Package-level cycle `audit ↔ orchestration ↔ persistence`** (Figure 8): `audit.logger` imports `orchestration.states.Transition`, and `persistence.repository` imports `Delivery`/`Explanation` from `orchestration.process`, while `orchestration.tasks` imports both. There is no cycle at module level. Moving those three types into `domain/` would remove it; §5.9 of the thesis should either say so or be changed once it is fixed.

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
