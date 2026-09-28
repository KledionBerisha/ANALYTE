# 0009 — Rregulla përpara klasifikuesit në verifikim

**Gjendja:** i zbatuar; E11 pret trajnimin në Colab dhe grupin B

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
