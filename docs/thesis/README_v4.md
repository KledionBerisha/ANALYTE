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
- Kolona «Burimi» e tabelës terminologjike dhe e rregullave të kombinimit u hoq më 2026-10-06 sepse burimet
  mungonin. Më 2026-10-07 burimet u plotësuan te `resources/terminology.csv` dhe `resources/patterns.csv`
  (të lexuara më 2026-10-06; evidenca te `worksheets/burimet_e_gjetura.md`), kolona u rikthye te Tabela 2,
  Shtojca A dhe Tabela B.3, §6.6 dhe prejardhja (§6.1) u përditësuan, dhe `teza_v4.md` u rigjenerua me
  `restructure.py` (tani lexon `../teza_v3.md` dhe shkruan `../teza_v4.md`). Korpusi `data/v1` u rigjenerua
  (PDF-të identike; JSON-et ndryshojnë vetëm te `source_ref`; id-ja e re `gen-1.0/s42/n500/3fede455`).
  **Dokumenti .docx/.pdf nuk është rindërtuar** (pandoc dhe LibreOffice mungojnë në këtë makinë): ekzekuto
  `build_docx.py` dhe `update_toc.py` para dorëzimit.
- Abstrakti është shkurtuar në një faqe.

Ndërtimi (nga `build/`): `python restructure.py` (teza_v3.md → teza_v4.md), `python build_docx.py`
(pandoc + python-docx: Times New Roman 12/14, justify, 1.5, kapitujt në faqe të re, numrat e faqeve poshtë
djathtas, TOC/listat si fusha Word), `python update_toc.py in.docx out.docx out.pdf` (LibreOffice përditëson
tabelat e përmbajtjes dhe eksporton PDF; ekzekutohet dy herë që numrat e faqeve të konvergojnë).

Për t'u plotësuar nga autori para dorëzimit: emri i mentorit dhe viti akademik te kopertina; mirënjohja.
