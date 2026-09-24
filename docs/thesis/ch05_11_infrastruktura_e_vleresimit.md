# 5.11 Infrastruktura e vlerësimit

*Seksion i ri, i shkruar pas zbatimit.*

Kontributi kryesor i punimit është një mekanizëm verifikimi, dhe vlera e
tij shprehet vetëm me numra krahasues. Prandaj infrastruktura që i
prodhon ata u ndërtua përpara komponentëve që ajo mat — vendim
metodologjik i shpjeguar në seksionin 5.1 dhe i zbatuar në rendin e
fazave.

## 5.11.1 Ç'është një "sistem" për vlerësimin

Vlerësimi nuk njeh shtresa. Ai njeh diçka që merr një dokument dhe kthen
atë që mendon për të: kontekstin e nxjerrë, tekstin e gjeneruar dhe
vendimin e verifikimit. Kushtet e ablacionit të planit të eksperimenteve
bëhen kështu zbatime të ndryshme të së njëjtës ndërfaqe, në vend që degë
kushtëzimi brenda kodit të prodhimit.

Hyrja që i jepet sistemit mban vetëm identifikuesin e dokumentit dhe
shtegun e skedarit. E vërteta bazë nuk kalon kurrë prej andej, dhe kjo ka
test të vetin: prej saj varet vlefshmëria e çdo numri që del nga
harness-i, dhe një rrjedhje e tillë nuk do të linte asnjë shenjë të
dukshme në rezultate.

## 5.11.2 Metrikat

Të gjashtë pyetjet e para kërkimore kanë modulin e vet, dhe të gjitha
janë funksione të pastra mbi çiftet e vërtetë–parashikim.

**Nxjerrja (PK1)** matet për fushë, me çiftim të rreshtave sipas kodit
LOINC. Një rresht i humbur nuk është neutral për fushat e tij: ai
llogaritet si mungesë për secilën prej tyre. Përndryshe një sistem që
nxjerr vetëm rreshtat e lehtë do të dilte i përsosur.

**Klasifikimi (PK2)** raportohet edhe i ndarë sipas burimit të intervalit,
sepse një status i gabuar do të thotë gjithmonë njëra nga dy gjëra: vlera
u lexua gabim, ose intervali u zgjodh gabim. Veçmas raportohet edhe
mbulimi i vlerave të painterpretueshme — SP5 i shprehur si numër, sepse
rastet janë të pakta dhe saktësia e përgjithshme do t'i fshihte.

**Shkeljet (PK5)** ndajnë shkeljet e prodhuara nga ato që mbërrijnë te
përdoruesi. Ky dallim është tërë argumenti i ablacionit: verifikimi nuk e
bën modelin më të mirë, ai vendos çfarë del jashtë. Raportohet edhe
përpjesa e daljeve që përfunduan në shabllonin determinist — çmimi i
verifikimit, pa të cilin një sistem që refuzon gjithçka do të dukej i
përkryer.

**Zbuluesit (PK6)** maten sipas llojit të defektit dhe jo vetëm në
tërësi. Pritshmëria e formuluar përpara matjes është se rregullat do të
mbizotërojnë te defektet numerike dhe do të humbasin te mohimi dhe
pasiguria; një F1 i vetëm i përgjithshëm do ta fshihte plotësisht këtë.

## 5.11.3 Dy vendime të vogla me pasojë

**Metrikat kthejnë vlerë të papërcaktuar kur emëruesi është zero, kurrë
zero.** "U mat dhe doli zero" dhe "nuk kishte çfarë të matej" janë pohime
të ndryshme, dhe tabelat i shtypin ndryshe. Qelizat që presin një
komponent të paekzistuar shënohen veçmas dhe nuk lihen bosh.

**Dy sisteme shërbejnë si kufij të njohur.** Orakulli kthen vetë të
vërtetën dhe duhet të arrijë vlerën e përsosur kudo; një metrikë që nuk e
arrin dot është e prishur në vetvete, dhe pa këtë kontroll gabimi i saj
do të dukej më vonë si dobësi e sistemit të matur. Sistemi bosh nuk
nxjerr asgjë dhe nuk duhet të marrë kurrë notë të mirë.

Kufiri i poshtëm e vërtetoi vlerën e vet menjëherë. Sistemi bosh prodhoi
ruajtje mohimi 1.000, sepse emëruesi numëronte edhe dokumentet që nuk
kishin prodhuar asnjë fjali. Një sistem që nuk shkruan asgjë nuk përmbys
asnjë mohim; kjo nuk është besnikëri. Gabimi u gjet përpara se të ishte
raportuar ndonjë numër.

## 5.11.4 Prejardhja e rezultateve

Çdo rezultat shkruhet bashkë me farën e korpusit, versionin e tij me
shumat kontrolluese të tabelave burimore, sha-në e git-it, gjendjen e
pastër ose të papastër të pemës së punës dhe versionin e katalogut të
rregullave.

Gjendja e pemës së punës shënohet posaçërisht. Një numër i prodhuar mbi
kod të pakommit-uar nuk është i rindërtueshëm, dhe kjo duhet të duket në
skedar e jo të kujtohet nga ai që e ekzekutoi.

## 5.11.5 Gjendja e matjeve

| Pyetja | Gjendja |
|---|---|
| PK1 — nxjerrja | e matur për kanalin dixhital; kanali i skanuar pret OCR-në |
| PK2 — klasifikimi | e matur për kanalin dixhital |
| PK3 — besnikëria | pret shtresën e gjenerimit |
| PK4 — krahasimi i kryqëzuar | e matur |
| PK5 — shkeljet | pret gjenerimin dhe verifikimin |
| PK6 — zbuluesit | pret korpusin e korruptuar |
| PK7 — kuptueshmëria | pret studimin me përdorues |

Metrikat e PK3, PK5 dhe PK6 janë të zbatuara dhe të testuara; atyre u
mungon sistemi që i ushqen, jo mjeti që i mat. Ky dallim ka rëndësi për
planifikimin: kur shtresa e gjenerimit të ekzistojë, rruga nga korpusi te
qeliza e tabelës është tashmë e provuar.
