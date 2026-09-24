# 0006 — Përputhje e saktë e emrave, jo e afërt

**Gjendja:** i zbatuar

## Konteksti

Laboratorët e shtypin të njëjtin analit në shumë mënyra: "Hemoglobina",
"HGB", "Hb", "Hemoglobinë". Hartëzimi te kodi LOINC duhet t'i njohë të
gjitha, dhe tundimi i dukshëm është përputhja e afërt me distancë
vargjesh.

## Vendimi

Përputhja është e saktë pas normalizimit. Normalizimi heq shkronjat e
mëdha, pikësimin dhe theksin; përtej kësaj nuk ka tolerancë. Emri që nuk
njihet mbetet i panjohur dhe rreshti regjistrohet si i hedhur, me arsyen.

Kur dy analite pretendojnë të njëjtën formë të shkruar, asnjëri nuk e
fiton. Zgjedhja e "të parit" do të varej nga rendi i rreshtave në një CSV.

## Arsyetimi

"Kaliumi" dhe "Kalciumi" ndryshojnë për një shkronjë dhe kanë intervale
krejt të ndryshme. Një përputhje e afërt do t'i ngatërronte herët a vonë,
dhe ngatërrimi do të hynte i heshtur në një shpjegim për pacientin — i
mbështetur nga çdo shtresë e mëpasme, sepse për to gjetja do të dukej e
rregullt.

Heqja e theksit është lëshim i vetëdijshëm në drejtim të kundërt: OCR-ja
i ngatërron rregullisht `ë` me `e` dhe `ç` me `c`, dhe një krahasim që i
dallon do të dështonte pikërisht te kanali ku ndihma nevojitet më shumë.
Në shqip nuk ka çift termash mjekësorë që dallohen vetëm nga theksi.

## Pasojat

Mbulimi varet drejtpërdrejt nga plotësia e listës së varianteve në
`resources/analytes.csv`. Kjo është e matshme dhe e zgjerueshme; një
distancë vargjesh, përkundrazi, do të kishte fshehur të njëjtin problem
pas një pragu të zgjedhur me dorë.

Rreshtat e hedhur ruhen me arsyen e tyre, që një PK1 i ulët të tregojë ku
prishet puna — te segmentimi, te harta e emrave apo te njësitë — dhe jo
vetëm se prishet.
