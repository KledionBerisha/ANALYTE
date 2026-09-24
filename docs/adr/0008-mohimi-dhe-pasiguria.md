# 0008 — Mohimi dhe pasiguria me rregulla leksikore

**Gjendja:** i zbatuar

## Konteksti

Rregullat R5 dhe R6 ndalojnë përmbysjen e polaritetit dhe heqjen e
pasigurisë. Që ato të maten, të dyja duhen njohur së pari në burim.
Shqipja nuk ka model të gatshëm për këtë detyrë.

## Vendimi

Zbulimi bëhet me rregulla leksikore në frymën e NegEx-it: një listë e
shkurtër shenjash, një fushë veprimi që mbyllet te kundërvënia ("por",
"ndërsa", pikëpresja), dhe një listë pseudo-mohimesh që kontrollohet e
para.

Pasiguria zbulohet njësoj, me shenja të ndara në katër grupe: foljet
modale, ndajfoljet, foljet e dukjes dhe mohimi i përjashtimit.

Polariteti dhe drejtimi mbahen fusha të ndara. "Nuk rezulton mbi
intervalin" ka drejtim `INCREASED` dhe polaritet `NEGATED`.

## Arsyetimi

"Nuk përjashtohet sideropeni" përmban shenjën "nuk" dhe nuk mohon asgjë —
ajo pohon me rezervë. Po ta lexonim si mohim, do të përmbysnim mjekun
pikërisht ashtu si druhet R5 se do ta bëjë modeli gjuhësor. Prandaj
pseudo-mohimet fitojnë mbi shenjat e thjeshta.

Bashkimi i polaritetit me drejtimin do ta bënte të pamundur dallimin mes
"është i ulët" dhe "nuk është i lartë", të cilat nuk janë e njëjta gjë:
e dyta përputhet me çdo status që nuk është i rritur.

Gabimi i parazgjedhur është pohimi. Një mohim i humbur prodhon tekst më
të fortë se burimi dhe kapet nga verifikimi; një mohim i shpikur prodhon
tekst që kundërshton burimin pa lënë gjurmë se nga erdhi.

## Alternativat e refuzuara

**Model i mësuar.** Nuk ka korpus shqip me anotim mohimi. Ndërtimi i tij
do të ishte punim më vete.

**Rrënjëzim i plotë i shqipes.** Përputhja e termave duron prapashtesat me
përputhje parashtese mbi çdo fjalë. Një rrënjëzues i gjysmuar do të
fshihte se ku gabon sistemi, pas një shtrese tjetër gabimi.

## Pasojat

Detektorët provohen me fjali të shkruara me dorë, të ndryshme nga
shabllonet e gjeneruesit. Kjo është e domosdoshme: detektorët u shkruan
duke i pasur ato shabllone parasysh, prandaj një provë mbi to do të
tregonte vetëm se kodi kujton veten.

Një kufizim mbetet i hapur dhe i fiksuar me test: mohimi në gjymtyrën e
dytë ("Natriumi është i lartë, por kaliumi nuk është i rritur") lexohet
si pohim. Zgjidhja e vërtetë është ndarja e fjalisë në dy pohime, jo
zbutja e fushës së veprimit.
