# 0004 — Infrastruktura e matjes përpara komponentëve

**Gjendja:** i zbatuar

## Konteksti

Kontributi i punimit është një mekanizëm verifikimi, dhe vlera e tij
shprehet vetëm me numra krahasues. Infrastruktura që i prodhon ata mund
të ndërtohej pasi të ekzistonin komponentët, ose përpara tyre.

## Vendimi

Harness-i i vlerësimit u ndërtua i treti, përpara çdo shtrese nxjerrjeje.
Ai ekzekuton matricën e eksperimenteve E1-E15, llogarit metrikat PK1-PK6
dhe shkruan rezultatin bashkë me prejardhjen: farën e korpusit, versionin
e tij me shumë kontrolluese të tabelave burimore, sha-në e git-it,
gjendjen e papastër të pemës së punës dhe versionin e katalogut të
rregullave.

Dy vendime të vogla brenda tij bartin peshë:

**Metrikat kthejnë `None` kur emëruesi është zero, kurrë zero.** "U matëm
dhe doli zero" dhe "nuk kishte çfarë të matej" janë pohime të ndryshme.
Tabela i shtyp ndryshe: `n/a` kundrejt një vlere, dhe `[TO BE MEASURED]`
për eksperimentet që presin komponentin e vet.

**Dy pipeline-a shërbejnë si kufij të njohur.** Orakulli kthen vetë të
vërtetën dhe duhet të arrijë 1.0 kudo; sistemi bosh nuk nxjerr asgjë dhe
nuk duhet të marrë kurrë notë të mirë.

## Alternativat e refuzuara

**Metrika ad-hoc për çdo komponent.** Do të kishin qenë më të shpejta dhe
do të kishin bërë të pamundur krahasimin e kushteve të ablacionit, të
cilat janë vetë argumenti i punimit.

**Zero në vend të `None`.** Më e thjeshtë për tabelat, por fsheh
ndryshimin mes dështimit dhe mungesës së matjes — pikërisht ndryshimi që
një lexues i punimit duhet ta shohë.

## Pasojat

Kufiri i poshtëm e vërtetoi vlerën e vet menjëherë: pipeline-i bosh
prodhoi *ruajtje mohimi 1.000*, sepse emëruesi numëronte edhe dokumentet
pa dalje fare. Një sistem që nuk shkruan asnjë fjali nuk përmbys asnjë
mohim; kjo nuk është besnikëri. Gabimi u gjet ditën e parë dhe jo pasi të
ishte raportuar.

Rezultatet mbajnë shënim nëse pema e punës ishte e papastër. Një numër i
prodhuar mbi kod të pakommit-uar nuk është i rindërtueshëm, dhe kjo duhet
të duket në skedar e jo të kujtohet.
