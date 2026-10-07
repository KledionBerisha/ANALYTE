# Versioni 4 (2026-10-06) — dorëzimi sipas udhëzimeve të UBT-së

`teza_v4.md` është `teza_v3.md` e ristrukturuar sipas «UBT Instruksione për punim diplome»:

- Rendi dhe numërimi i UBT-së: Abstrakt, Mirënjohje, Përmbajtja, Lista e figurave, Lista e tabelave, Fjalori
  (faqe me numra romakë), pastaj 1 Hyrje, 2 Shqyrtimi i literaturës, 3 Deklarimi i problemit, 4 Metodologjia,
  5 Rezultatet, 6 Diskutime dhe përfundime, 7 Referencat, 8 Appendixes (faqe me numra arabë nga 1).
  Të gjitha referencat e brendshme (§, Kapitulli, seksioni) janë rinumëruar.
- Kapitulli 2 (literatura) është shkruar i plotë; lista e referencave ka 64 zëra, secili i verifikuar
  më 2026-10-06 kundrejt DOI-së / faqes zyrtare (ACL Anthology, Crossref, EUR-Lex, gzk.rks-gov.net).
- Figurat janë rinumëruar sipas radhës së shfaqjes (1–20; Figura 17 e vjetër, chat-i, është hequr);
  tabelat janë numëruar sipas radhës së shfaqjes (1–27) dhe çdo tabelë ka titull.
- (e kapërcyer më 2026-10-07, shih më poshtë.)
- Abstrakti është shkurtuar në një faqe.
- **2026-10-07:** burimet e 82 termave dhe të 11 kombinimeve u shkruan te `resources/*.csv` (korpusi u rigjenerua:
  `gen-1.0/s42/n500/3fede455`, përmbajtje e njëjtë), dhe rregullat u rishikuan nga një mjek familjar. `build/apply_sources.py`
  (ekzekutohet pas `restructure.py`) fut Shtojcat A dhe B të rigjeneruara, kolonën «Burimi» te Tabela 5, referencat [65]–[77],
  dhe ndryshon §4.3.8, §4.4.2, §5 (hyrja), §5.1, §6.4, §6.6 pika 10, Shtojcën H dhe Mirënjohjen.

Ndërtimi (nga `build/`): `python restructure.py` (teza_v3.md → teza_v4.md), `python apply_sources.py`, `python apply_advice.py`, `python build_docx.py`
(pandoc + python-docx: Times New Roman 12/14, justify, 1.5, kapitujt në faqe të re, numrat e faqeve poshtë
djathtas, TOC/listat si fusha Word), `python update_toc.py in.docx out.docx out.pdf` (LibreOffice përditëson
tabelat e përmbajtjes dhe eksporton PDF; ekzekutohet dy herë që numrat e faqeve të konvergojnë).

Për t'u plotësuar nga autori para dorëzimit: emri i mentorit dhe viti akademik te kopertina; mirënjohja.
- **2026-10-07 (pasdite):** tabela e këshillave me burim (ADR 0023) u plotësua: 75 nga 76 rreshta te `resources/advice.csv`
  (CRP e ulët pa rresht), burimet dhe fjalitë angleze mbështetëse te `worksheets/keshillat_e_gjetura.csv`; `tests/unit/test_advice.py`
  kalon (21 teste). `build/apply_advice.py` (pas `apply_sources.py`) shton §4.3.9, fjalitë te §4.5, §4.10, §4.12, Tabelën 8, §6.6, §6.7
  dhe Tabelën B.4. Zinxhiri i plotë: restructure → apply_sources → apply_advice → build_docx → update_toc (dy herë).
