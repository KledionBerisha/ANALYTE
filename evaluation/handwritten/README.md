# Shembujt e shkruar me dorë

Tri grupe që i shkruan autori, me fjalët e veta. Janë e vetmja lëndë e
punimit që nuk ka kaluar nëpër gjeneruesin sintetik, prandaj janë e vetmja
provë se rregullat dhe detektorët nuk mbajnë mend thjesht shabllonet e
sistemit.

```bash
python -m evaluation.kits build   # rishkruan vetëm A_kontekstet.md
python -m evaluation.kits check   # mat gjithçka që është plotësuar
```

`build` nuk mbishkruan asnjë skedar që plotësoni ju. `check` mund të
ekzekutohet në çdo moment: rreshtat bosh anashkalohen, dhe rreshtat me
gabim formati raportohen me arsyen në vend që të ndalin matjen.

**Rregulli i vetëm i përbashkët:** mos i shikoni shabllonet e sistemit
(`generation/templates.py`) as tekstet e gjeneruesit përpara se të
shkruani. Shkruani ashtu si do të shkruanit për një pacient, ose ashtu si
do të gabonte një model gjuhësor.

---

## A — Shpjegime referuese (25)

**Skedari:** `A_shpjegimet.md`, nën titullin `## A01` … `## A25`.
**Konteksti:** `A_kontekstet.md` — lexoni vetëm atë që është aty.

Për çdo kontekst, shkruani shpjegimin që do t'i jepnit pacientit. Kushtet:

- Asnjë numër që nuk është në kontekst (vlera ose kufijtë e intervalit).
- Asnjë analit, gjendje ose term që nuk është në kontekst.
- Pa diagnozë, pa trajtim, pa prognozë (SP1-SP3).
- Nëse ka vlerë kritike, njoftimi për ta vjen **para** çdo shpjegimi
  (SP4).
- Vlera pa interval nuk interpretohet; thuhet vetëm se nuk interpretohet
  (SP5).
- Termi që nuk shpjegohet (SP6) përmendet, por nuk shpjegohet.
- Çdo gjë që thotë mjeku citohet me parashtesën `Mjeku ka shënuar:` —
  mohimi, rezerva dhe rekomandimi duhet të mbijetojnë.
- Shënimi përmbyllës për profesionistin shëndetësor (SP7) — me fjalët
  tuaja.

**Për çfarë përdoren.** Sot: rregullat ekzekutohen mbi to, dhe çdo shkelje
është ose alarm i rremë i rregullit ose gabim i shpjegimit — të dyja duhen
parë me sy. Kjo është e vetmja matje e alarmeve të rreme mbi prozë të
natyrshme. Kur të ketë model gjuhësor: pikë krahasimi për testin e
cilësisë në shqip, mbi të njëjtat kontekste.

---

## B — Fjali me defekt (rreth 100)

**Skedari:** `B_fjalite.csv`

| Kolona | Përmbajtja |
|---|---|
| `id` | B001, B002, … |
| `konteksti` | A01 … A25 — fjalia i përket atij konteksti |
| `fjalia` | Një fjali e vetme e daljes |
| `etiketa` | Njëra nga vlerat më poshtë |
| `shenim` | Opsionale — çfarë keni prishur |

Etiketat dhe sa të shkruhen:

| Etiketa | Sa | Çfarë është |
|---|---|---|
| `clean` | 30 | Fjali e saktë, e shkruar ndryshe nga shablloni |
| `ungrounded_number` | 10 | Numër që nuk është në kontekst |
| `ungrounded_analyte` | 10 | Analit që nuk është matur dhe mjeku nuk e përmend |
| `direction_mismatch` | 10 | Vlera e lartë thuhet e ulët, ose anasjelltas |
| `polarity_flip` | 10 | Citim i mjekut me mohimin të përmbysur |
| `hedge_removed` | 10 | Citim i mjekut me rezervën të hequr |
| `fabricated_finding` | 10 | Gjendje që nuk përmendet askund në kontekst |
| `ungrounded_term_explanation` | 5 | Shpjegim i një termi që nuk shpjegohet (SP6) |
| `prohibited_claim` | 10 | Diagnozë, trajtim ose prognozë |

Dy kushte që i kërkon mënyra si maten rregullat:

- `polarity_flip` dhe `hedge_removed` duhet të fillojnë me
  `Mjeku ka shënuar:` — rregullat R5 dhe R6 gjykojnë vetëm citimet.
- Një fjali, një defekt. Nëse fjalia prish dy gjëra, rezultati do të
  numërojë vetëm të parën sipas rendit të katalogut.

Mostrat më të vlefshme janë ato që **nuk** duken si shablloni: parafrazime,
rend tjetër fjalësh, sinonime, fjali të gjata. Një model gjuhësor nuk do
të gabojë në formën e shabllonit.

---

## C — Narrativë mjeku (rreth 60)

**Skedari:** `C_narrativa.csv`

| Kolona | Vlerat |
|---|---|
| `id` | C001, C002, … |
| `fjalia` | Një fjali raporti, ashtu si do ta shkruante një mjek |
| `lloji` | `finding` · `recommendation` · `term_mention` |
| `polariteti` | `affirmed` · `negated` |
| `siguria` | `confirmed` · `hedged` |
| `analiti` | Emri i analitit nëse fjalia përmend një (p.sh. `Hemoglobina`), përndryshe bosh |
| `drejtimi` | `increased` · `decreased` · `normal` · `unspecified` |
| `shenim` | Opsionale |

Shpërndarja e synuar:

- 15 mohime të thjeshta ("nuk ka", "mungojnë shenjat e")
- 10 pseudo-mohime — mohim që pohon me rezervë ("nuk përjashtohet",
  "nuk mund të mohohet")
- 10 me rezervë ("e mundshme", "sugjeron", "dyshohet")
- 10 rekomandime, disa të mohuara ("nuk nevojitet kontroll")
- 15 pohime të drejtpërdrejta me drejtim, me emra analitesh në forma të
  ndryshme (shkurtesa, trajta të shquara)

Këto mbushin boshllëkun më të madh të Degës B: detektorët e mohimit dhe
të rezervës janë testuar vetëm mbi fjali të shkruara gjatë zhvillimit,
nga e njëjta dorë që shkroi detektorët.
