# 0009 — Rregulla përpara klasifikuesit në verifikim

**Gjendja:** i planifikuar (Fazat 6 dhe 7)

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
