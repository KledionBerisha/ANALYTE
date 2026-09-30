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

