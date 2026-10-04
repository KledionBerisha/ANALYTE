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
| `burimi` | Vetëm për `polarity_flip` dhe `hedge_removed`: fjala e saktë e pohimit të mjekut (nga lista "Mjeku ka shkruar" e kontekstit) që fjalia zëvendëson |

**Prejardhja.** Skedari i tanishëm i dorëzoi autori më 2026-10-02, si punën e vet.
Gjatë kësaj pune ekzistonte në depo një draft i mëparshëm i hartuar nga një model
gjuhësor (Claude); ai u zëvendësua dhe nuk është më pjesë e depove. **12 nga 105 rreshta të
skedarit të tanishëm janë identikë (kontekst dhe fjali) me rreshta të atij drafti**: 6
`polarity_flip` dhe 6 `hedge_removed`, pra vetëm rreshta me citim të mjekut; edhe 4 fjali të
tjera përputhen nëse nuk merret parasysh konteksti. 93 rreshtat e tjerë janë të ndryshëm.
Forma e rreshtave me citim është shumë e kufizuar (parashtesa dhe fjala e mjekut me një
ndryshim), prandaj përputhja mund të ndodhë pa kopjim, por skedari nuk e vërteton
se si ndodhi. Punimi duhet ta thotë hapur si u përgatit B dhe se kjo mbivendosje ekziston.

Matja ka një ndryshim të rëndësishëm nga përshkrimi fillestar: `polarity_flip`
dhe `hedge_removed` **zëvendësojnë** citimin burimor te shablloni, jo shtohen
në fund. Shablloni i mban tashmë citimet e sakta, dhe R5/R6 gjykojnë të parin;
një citim i dytë i shtuar nuk gjykohej kurrë dhe matja jepte zero për një arsye
që s'ka lidhje me rregullat (20 nga 20 të humbura në matjen e parë). Ky ndryshim
u bë pasi u pa ai rezultat, dhe duhet raportuar.

`python -m evaluation.kits check` raporton edhe rreshtat e përsëritur (`B_duplicates`):
një rresht me të njëjtin kontekst, fjali dhe burim numërohet dy herë dhe e fryn llojin e tij.

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

**Prejardhja e C.** Skedari i tanishëm (60 rreshta) e dorëzoi autori më 2026-10-04, si punë të vet (sipas deklaratës së tij). `python -m evaluation.kit_c_report` e mat ndarë sipas llojit dhe numëron rreshtat identikë me fjali që gjeneruesi i prodhon: 19 nga 60. Mbi 41 fjalitë e tjera, 13 dalin plotësisht saktë. Një version i mëparshëm i dorëzuar i C ishte i zbrazët; një tjetër kishte 26 nga 60 rreshta identikë me gjeneruesin dhe nuk u instalua.


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
