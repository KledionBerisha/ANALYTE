# 0009 — Rregulla përpara klasifikuesit në verifikim

**Gjendja:** i zbatuar; E11 u mat më 2026-09-30 (shih më poshtë); grupi B pret autorin

## Konteksti

Shtresa e verifikimit ka dy mekanizma të mundshëm: rregulla deterministe
dhe një klasifikues i mësuar. Pyetja kërkimore PK6 kërkon krahasimin e
tyre, prandaj të dy duhet të ekzistojnë; mbetet të vendoset rendi dhe
roli.

## Vendimi

Rregullat vijnë të parat dhe janë të vetmet që lejohen të ndalin daljen
pa kusht. Klasifikuesi vepron pas tyre, mbi atë që ato nuk e kapin dot.

Katalogu i rregullave ndan shprehimisht ato që vendosen nga një fjali e
vetme nga ato që kërkojnë shikim mbi tërë daljen (R4 dhe R8). Vetëm të
parat mund të përbëjnë detyrë klasifikimi në nivel fjalie.

Shkeljet e zbuluara nga rregullat nuk mbajnë `confidence`; modeli i
domenit e ndalon këtë. Rregulli është determinist: ai ose e sheh shkeljen
ose jo.

## Arsyetimi

Rregullat mbulojnë atë që matet saktësisht — një numër që nuk gjendet në
kontekst, një analit që nuk është matur, një drejtim që nuk përputhet me
statusin. Për këto, një klasifikues do të shtonte pasiguri pa shtuar
asgjë.

Pritshmëria e formuluar përpara matjes, që duhet të mbetet e shkruar edhe
nëse del e gabuar: rregullat do të mbizotërojnë te defektet numerike dhe
do të humbasin te mohimi dhe pasiguria, ku kërkohet të kuptohet fjalia.
Prandaj PK6 raportohet edhe sipas llojit të defektit; një F1 i vetëm i
përgjithshëm do ta fshihte plotësisht këtë dhe do ta bënte krahasimin të
padobishëm.

## Alternativat e refuzuara

**Vetëm klasifikues.** Do të hiqte transparencën dhe auditueshmërinë te
pikërisht ato shkelje ku dëshmia është e thjeshtë dhe e plotë.

**Vetëm rregulla.** E mjaftueshme për të mbrojtur pretendimin qendror —
prandaj klasifikuesi është i pari në radhën e prerjes nëse koha mungon —
por do të linte pa përgjigje pyetjen nëse zbulimi semantik ia vlen.

## Pasojat

Vlerësimi ruan për çdo shkelje se cili mekanizëm e zbuloi (`detected_by`).
Pa këtë fushë, krahasimi rregulla-kundrejt-klasifikuesi do të kërkonte
riekzekutim të të gjitha eksperimenteve.

## Zbatimi (2026-09-27)

Rendi i vendosur më sipër është zbatuar te `verification/classifier.py`:
klasifikuesi gjykon vetëm fjalitë ku rregullat nuk gjetën asgjë, dhe çdo
shkelje e tij mban `confidence`. Trajnimi bëhet në Colab (XLM-R base),
matja lokalisht, mbi të njëjtat 192 tekste si E10 dhe me të njëjtën
metrikë. Pragu i vendimit zgjidhet vetëm mbi validimin.

**Dy hyrje, jo një.** Përveç fjalisë së vetme, trajnohet edhe një model që
merr fjalinë bashkë me një përmbledhje të kontekstit. Rezultati i
pritshëm i mësipërm u përmbys nga E10 pikërisht sepse rregullat e shohin
kontekstin; pa hyrjen e dytë, PK6 do ta paraqiste dallimin e informacionit
si dallim metode.

**Kontrolli i rrjedhjes** (`ml/leakage.py`, `evaluation/results/E11/leakage.json`)
tregoi dy gjëra përpara çdo trajnimi:

- Për çdo lloj defekti, 100% e fjalive të validimit kanë skeletin — fjalinë
  pa numra, pa emra analitesh dhe pa terma — të njëjtë me një fjali të
  trajnimit. Ndarja sipas dokumentit i mban dokumentet të ndara, por jo
  shabllonet: validimi është trajnimi me numra të tjerë.
- Çdo gjetje e shpikur fillon me "Vërehet gjithashtu", dhe asnjë fjali e
  pastër nuk fillon kështu. Etiketa është e shkruar në tekst.

**Pasoja.** E11 mbi korpusin e korruptuar mat sa mirë klasifikuesi i njeh
format e gjeneruesit, jo sa mirë e njeh defektin. Ky kufi nuk hiqet duke
e ndryshuar korpusin — çdo korruptues i ri do të kishte formën e vet. Testi
i vetëm përtej tij është grupi B i fjalive të shkruara me dorë
(`evaluation/handwritten/`), dhe PK6 nuk raportohet për klasifikuesin pa
të.

## Rezultati i E11 (2026-09-30)

Dy modelet XLM-R (`xlm-roberta-base`, 3 epoka, fara 42, T4) u trajnuan mbi
të njëjtat të dhëna, me versionin e rregullave `r1.3`, dhe u matën mbi të
njëjtat 192 tekste si E10.

Pragu u zgjodh mbi validimin me dy rregulla, dhe të dyja raportohen (autori,
2026-09-30): **rregulli 1**, macro F1 më i lartë mbi llojet e defektit; dhe
**rregulli 2**, macro F1 më i lartë ndër pragjet që bllokojnë jo më shumë se
5% të teksteve të pastra të validimit. Verifikimi (E9) përdor të dytin.

| | Rregulli | Pragu | Macro F1 (test) | Të pastra të bllokuara, validim | Të pastra të bllokuara, test |
|---|---|---|---|---|---|
| Rregullat (E10) | — | — | **0.993** | — | 0 / 30 |
| Klasifikuesi, fjalia | 1 · F1 më i lartë | 0.30 | 0.481 | 98% | 30 / 30 |
| Klasifikuesi, fjalia | 2 · buxhet 5% | 0.85 | 0.385 | 0% | 0 / 30 |
| Klasifikuesi, fjalia + konteksti | 1 · F1 më i lartë | 0.40 | 0.538 | 98% | 29 / 30 |
| Klasifikuesi, fjalia + konteksti | 2 · buxhet 5% | 0.90 | 0.326 | 4% | 2 / 30 |

Buxheti vlen mbi validimin; te testi, konteksti bllokon 2 nga 30 (6.7%), pak
mbi 5%. Kjo është një gjetje e pavarur, jo gabim: pragu nuk u prek pasi u pa testi.

Sipas llojit të defektit (test), brenda buxhetit: `fabricated_finding` 1.00
(të dy hyrjet) dhe `ungrounded_analyte` 0.70 (fjalia) ose 0.92 (konteksti);
`ungrounded_number` 0.00 (fjalia) ose 0.36 (konteksti); `direction_mismatch`
dhe `polarity_flip` **0.00** në të dyja, dhe `hedge_removed` 0.00 te konteksti.
Pra, kur klasifikuesi nuk lejohet të bllokojë tekst të pastër, ai mbetet i
pafuqishëm pikërisht te mohimi (`polarity_flip`) dhe drejtimi. Me rregullin 1
e kap pjesërisht (F1 0.22 dhe 0.26), por duke bllokuar pothuajse çdo tekst.
`omitted_recommendation` është 0 nga ndërtimi (shih më sipër).

**Si duhet lexuar.**

- `fabricated_finding` me F1 1.0 nuk është aftësi: çdo gjetje e shpikur nis me
  "Vërehet gjithashtu" (`leakage.json`). Është njohje e shabllonit të gjeneruesit.
  Brenda buxhetit ky është klasa e vetme e sigurt që kapet, bashkë me
  `ungrounded_analyte`.
- Hipoteza e formuluar para matjes — rregullat humbasin te mohimi dhe
  pasiguria — nuk u vërtetua, as këtu, as te E10: rregullat shohin kontekstin
  e plotë. Klasifikuesi e sheh më pak, prandaj PK6 krahason dy metoda mbi
  informacion të ndryshëm.
- Një F1 i tillë nuk thotë nëse klasifikuesi ndihmon mbi rregullat. Kjo pyetje
  mbetet e hapur deri te grupi B i shkruar me dorë.

**Dy gabime u gjetën pasi grupi testues ishte parë, dhe duhen thënë.**

1. *F1 i klasës së humbur dilte `None`, jo zero.* Një klasë me raste të vërteta
   ku zbuluesi nuk parashikoi asgjë kishte saktësi të papërkufizuar, dhe
   mesatarja e klasave e hidhte mënjanë. Klasifikuesi, që kapte zero nga
   pesë llojet, dilte me macro F1 0.90 dhe 0.96. U korrigjua te
   `PRF.f1` (2TP / (2TP + FP + FN): zero kur ka diçka për të gjetur ose një
   alarm, `None` vetëm kur s'ka asgjë për t'u matur). E10 nuk ndryshon
   (0.9925 si më parë: çdo klasë e tij ka parashikime), por zgjedhja e
   pragut mbi validimin përdorte të njëjtën metrikë dhe u përsërit.
2. *Rregulli i zgjedhjes së pragut nuk ndëshkon alarmet e rreme.* Ai maksimizon
   macro F1 mbi llojet e defektit, dhe ky numër nuk e sheh tekstin e pastër që
   bllokohet. Një tekst ka rreth 31 fjali; mjafton një probabilitet i vogël
   gabimi për fjali që të bllokohet pothuajse çdo tekst i pastër (98% te
   validimi, në të dy pragjet e zgjedhura). Pika pune pa alarme ekziston
   (fjalia: 0.85 → 0% e të pastrave; konteksti: 0.90 → 4%), por me macro F1
   më të ulët te validimi (0.387 dhe 0.308). Rregulli nuk u zëvendësua pasi u
   panë rezultatet: autori vendosi të raportohen të dyja — origjinali dhe një
   rregull i dytë me buxhet 5%, i zgjedhur mbi validimin — dhe ky rregull i dytë
   u shtua **pasi grupi testues ishte parë**. Prandaj tabela i emërton të dyja
   dhe nuk e paraqet të dytin si zgjedhjen e planifikuar që në fillim. Pragu
   i rregullit 2 nuk varet nga testi (një test e provon), por vetë ekzistenca
   e tij është shtuar pas parë rezultateve.


## Grupi A (2026-10-05)

25 shpjegime referuese (`evaluation/handwritten/A_shpjegimet.md`), dorëzuar nga autori sipas deklaratës së tij
(lexoi vetëm `A_kontekstet.md`, hartoi dhe rishikoi pasi Claude i dha vërejtje për versionet e mëparshme; skedari
nuk e vërteton). Rregullat `r1.3` ekzekutohen mbi to pa ndryshim: **5 nga 25 shënohen (20%)**, të 5 alarme të rreme
(«Kolesteroli HDL/LDL» te A11, A14, A16 lexohet si kolesterol total; «25» te «Vitamina D 25-OH» te A18, A20 lexohet
si numër i pabazuar), të njëjtat dy shkaqe si te B. Grupi nuk ka defekte të futura: jep vetëm shkallën e alarmeve
të rreme mbi prozë të riformuluar, jo precision apo recall. Nuk është i pavarur nga gjeneruesi (vlerat, termat dhe
citimet vijnë nga po ato tabela). Versionet e mëparshme (riformatim fjalë për fjalë; prozë e shabllonizuar; shenja
`[cite: 1]`; ndryshim i 6 citimeve të mjekut) nuk u instaluan. Rezultati: `evaluation/results/supplementary/kit_A.json`.
Rregullat nuk u rregulluan pas këtij rezultati; kjo do të ishte ndryshim pas parë rezultatit dhe duhet raportuar.

## Grupi B dhe E9 (2026-10-02)

**Grupi B.** 105 fjali natyrale (`evaluation/handwritten/B_fjalite.csv`) për 25 kontekste, me etiketën e secilës,
të dorëzuara nga autori. Gjatë punës ekzistonte në depo një draft i hartuar nga një model gjuhësor (Claude); ai u
zëvendësua. **12 nga 105 rreshta të skedarit të tanishëm janë identikë me rreshta të atij drafti** (6 `polarity_flip`
dhe 6 `hedge_removed`, vetëm citime të mjekut); 93 janë të ndryshëm. Forma e rreshtave me citim është e kufizuar,
prandaj përputhja mund të ndodhë pa kopjim, por skedari nuk e vërteton si ndodhi; punimi duhet ta deklarojë këtë.

Matja e parë mbi drafin dha zero për 20 nga 20 fjalitë me citim (`polarity_flip`, `hedge_removed`). Arsyeja nuk ishte
rregulli: vlerësuesi shtonte fjalinë në fund të shablloni-t, që mban tashmë citimet e sakta, dhe R5/R6 gjykojnë
citimin e parë që përputhet. Vlerësuesi u ndryshua që fjalia të **zëvendësojë** citimin burimor (kolona `burimi`),
si korruptuesit e E10. **Ky ndryshim u bë pasi u pa rezultati.** `kits check` raporton tani edhe rreshtat e
përsëritur (një çift i tillë u gjet dhe u korrigjua nga autori; skedari i tanishëm nuk ka dublikatë).

| Detektori | Macro F1, korpusi i korruptuar | Macro F1, grupi B | Të pastra të bllokuara, B |
|---|---|---|---|
| Rregullat | **0.993** | **0.795** | 1 / 30 |
| Klasifikuesi, fjalia, rregulli 1 (pragu 0.30) | 0.481 | 0.053 | 30 / 30 |
| Klasifikuesi, fjalia, rregulli 2 (pragu 0.85) | 0.385 | 0.015 | 2 / 30 |
| Klasifikuesi, fjalia + konteksti, rregulli 1 (0.40) | 0.538 | 0.177 | 29 / 30 |
| Klasifikuesi, fjalia + konteksti, rregulli 2 (0.90) | 0.326 | 0.104 | 0 / 30 |

Pragjet e klasifikuesit vijnë nga E11, të zgjedhura mbi validimin; asnjë prag nuk u akordua mbi B.
Rregullat sipas llojit (F1): `polarity_flip` 1.00, `hedge_removed` 1.00, `ungrounded_analyte` 1.00,
`ungrounded_number` 0.95, `fabricated_finding` 0.95, `direction_mismatch` 0.67 (kapen 5 nga 10),
`prohibited_claim` 0.46 (3 nga 10), `ungrounded_term_explanation` 0.33 (1 nga 5).

**Si duhet lexuar.** Rregullat bien nga 0.993 në 0.795 kur fjalitë nuk vijnë nga gjeneruesi; klasifikuesi, i
trajnuar mbi shabllone, mezi dallon nga rastësia (te fjalia, 0.053 dhe 0.015: ai mësoi shprehjen "Vërehet
gjithashtu" dhe nuk njeh një gjetje të shpikur të shprehur ndryshe). Dobësitë e rregullave janë leksikore: ato
njohin vetëm formën e pohimit të drejtimit që kanë ("Eritrocitet janë të larta" nuk kapet), shprehjet e SP1–SP3
që kanë (7 nga 10 diagnoza, trajtime dhe prognoza kalojnë), dhe termat e tabelës së tyre (një gjendje si
"pankreatit" nuk kapet); R9 kap vetëm një nga pesë shpjegimet e një termi të pashpjeguar. Dy alarme të rreme mbi
fjali të sakta janë gjetje më vete: "25-OH" te "Vitamina D 25-OH" lexohet si numri 25 (te një version tjetër i B,
"Kolesteroli LDL" lexohej si kolesterol total). **Kufizime të B:** 9 nga 105 fjali ndajnë formën me një fjali të
trajnimit (të gjitha citime të mjekut, sepse fjalët e mjekut te kontekstet vijnë nga gjeneruesi) dhe asnjë nuk
gjendet fjalë për fjalë te shablloni; rreshtat `polarity_flip` dhe `hedge_removed` janë, prandaj, më pak të
pavarura se të tjerat. Disa grupe rreshtash janë shumë njëtrajtëshme (p.sh. të gjitha fjalitë e pastra ndjekin të
njëjtën formë), çka e ngushton llojin e fjalive që testohen.

**E9** (shablloni si gjenerues, OCR, 500 dokumente, klasifikuesi i fjalisë në pragun 0.85): 51 dokumente (10.2%)
u çuan te shablloni rezervë nga alarme të rreme të klasifikuesit, 158 fjali, të gjitha `ungrounded_analyte`. Meqë
gjeneruesi është shablloni, çdo detektim është alarm i rremë. Një provë: 12 nga 40 dokumente të skanuara u goditën,
kundrejt 0 nga dokumentet dixhitale të një kampioni prej 120; fjalitë e shënuara mbanin njësi të prishura nga OCR
("midi", "ugidl", "umolL"). Buxheti 5%, i zgjedhur mbi tekst të pastër dixhital (0% e bllokuar), nuk transferohet
te kanali i skanuar.
