# 0011 — Makina e gjendjeve dhe dështimet që Figura 6 nuk i emërton

**Gjendja:** i zbatuar

## Konteksti

Specifikimi (§2.2) e përcakton makinën e përpunimit si normative, dhe
Figura 6 e vizaton atë. Figura njeh një lloj dështimi në ciklin e
gjenerimit: verifikimi gjen shkelje. Zbatimi has në të tjera që figura
nuk i emërton — gjeneruesi hedh përjashtim, motori OCR mungon ose
dështon, shablloni vetë nuk kalon verifikimin — dhe secila duhej t'i
caktohej një gjendjeje.

## Vendimi

**Tabela e kalimeve është e dhënë, jo logjikë.** `orchestration/states.py`
mban Figurën 6 si fjalor, dhe regjistri refuzon çdo kalim që nuk është aty.
Testet kontrollojnë që çdo gjendje është e arritshme, që gjendjet
përfundimtare nuk kanë dalje, dhe që skenarët e integrimit e mbulojnë çdo
kalim të tabelës. Kriteri i Fazës 6 — çdo rrugë me test integrimi — kështu
kontrollohet dhe nuk deklarohet.

**Përjashtimi i gjeneruesit është përpjekje e dështuar.** Dy kalime u
shtuan: `GENERATING → GENERATING` dhe `GENERATING → TEMPLATE_FALLBACK`.
Përpjekja e dytë pas një përjashtimi nis pa shkelje në kërkesë, sepse nuk
ka tekst për të korrigjuar.

**Shablloni verifikohet, rezultati ruhet, dorëzimi nuk ndalet.**

**Gabimet e verifikuesit dhe të bazimit nuk kapen.** Ato janë defekte të
sistemit dhe ngrihen deri te thirrësi.

**Pa OCR, dokumenti i skanuar përfundon në `FAILED_INGESTION`** me arsyen
e shkruar në regjistër. Kontrolli i formatit (`ingestion/format.py`)
refuzon skedarët që nuk hapen si PDF, PDF-të me fjalëkalim dhe ata pa
faqe. Kontrolli për viruse nuk është ndërtuar dhe nuk simulohet.

## Alternativat e refuzuara

**Ta lejonim përjashtimin të ngrihej.** Dokumenti do të mbetej në
`GENERATING`, gjendje jopërfundimtare, pa shpjegim për pacientin — lloji
i dështimit të heshtur që `NO_FINDINGS` u shpik për ta shmangur.
Riprovimi mund t'i lihej radhës së punëve, por atëherë numri i
përpjekjeve do të varej nga konfigurimi i radhës dhe jo nga
`MAX_GENERATION_ATTEMPTS`, dhe SP8 do të kishte dy kufij.

**Ta regjistronim përjashtimin si dështim verifikimi.** Rruga do të
dukej si në figurë, por regjistri do të gënjente: asnjë tekst nuk u
verifikua. Një tabelë e analizës së gabimeve e ndërtuar mbi të do të
numëronte shkelje që nuk ndodhën.

**Ta ndalnim dorëzimin kur shablloni dështon.** NFR1 thotë se vetëm
teksti pa shkelje i shfaqet përdoruesit, dhe në këtë rast të dyja
kërkesat nuk plotësohen dot njëkohësisht. Shablloni është dalja më e
bazuar që sistemi di të prodhojë; pa të, pacienti nuk merr asgjë, as
njoftimin kritik të SP4. U zgjodh dorëzimi, me verifikimin e ruajtur që
konflikti të mbetet i dukshëm në rezultate.

**Ta kapnim gabimin e verifikuesit dhe të shkonim te shablloni.** Kjo do
ta fshihte një verifikues të prishur pas daljeve që duken korrekte —
sistemi do të dukej i sigurt pikërisht kur mekanizmi i sigurisë nuk
punon.

## Pasojat

Figura 6 duhet të vizatojë dy kalimet e shtuara; përndryshe figura dhe
kodi ndahen, dhe testi i mbulimit mbron vetëm kodin.

Konflikti me NFR1 është i vërtetë. Ai shfaqet vetëm nëse shablloni dështon
në verifikim, gjë që testet e shabllonit e ndalojnë mbi korpusin dhe mbi
kontekstin referues — por jo mbi dokumente reale, që nuk janë parë ende.

Ekzekutimi i parë i makinës gjeti dy defekte rregullash që korpusi nuk i
kishte zbuluar. Shablloni dështoi mbi kontekstin referues të shkruar me
dorë: R1 e raportonte numrin e një rekomandimi të cituar ("kontroll pas 3
muajsh"), dhe R7 e raportonte si gjetje të shpikur "interval referent" —
fjalorin e vetë njoftimit të SP4. Korpusi nuk prodhon rekomandime me
numra, dhe fjalorët e tij rastisnin ta përmbanin termin. Katalogu kaloi në
`r1.1`, dhe E10 ndryshoi: macro F1 nga 0,979 në 0,993, alarmet e rreme mbi
tekst të pastër nga 2 në 0. Ndryshimi u motivua nga konteksti referues dhe
jo nga gabimet e grupit të testimit, por rregullat tani janë ndryshuar pasi
grupi i testimit ishte matur, dhe kjo duhet thënë kur raportohet shifra.
