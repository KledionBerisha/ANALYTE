# 0001 — Kontrata e domenit përpara çdo shtrese

**Gjendja:** i zbatuar

## Konteksti

Sistemi ka pesë shtresa që shkëmbejnë të njëjtat të dhëna: nxjerrja,
bazimi, gjenerimi, verifikimi dhe persistenca. Gjeneruesi i korpusit
duhet të prodhojë etiketa pikërisht në atë formë; vlerësimi duhet t'i
krahasojë me daljen e sistemit.

## Vendimi

Modelet e domenit u shkruan të parat, përpara çdo shtrese tjetër, si
modele Pydantic të pandryshueshme (`frozen=True`, `extra="forbid"`), me
`Decimal` për çdo vlerë numerike dhe pa asnjë import nga pjesa tjetër e
sistemit. Objekti qendror `GroundingContext` është i vetmi input i
shtresës së gjenerimit.

Pastërtia e paketës `domain/` nuk mbetet konventë: një test lexon
importet e çdo moduli dhe dështon nëse ndonjë prej tyre del jashtë
listës së lejuar.

## Alternativat e refuzuara

**Modele që rriten bashkë me kodin.** Do të kishte qenë më e shpejtë në
javët e para. Por gjeneruesi duhet të emetojë të vërtetën bazë në
saktësisht këtë formë; çdo ndryshim i mëvonshëm do të kërkonte një
shtresë përkthimi ndërmjet etiketave dhe daljes, dhe çdo metrikë do të
matej përmes saj.

**`float` në vend të `Decimal`.** Rregulli R1 krahason numrat për barazi
të saktë. Me `float`, një vlerë e lexuar `0.1 + 0.2` nuk do të përputhej
me `0.3` dhe verifikimi do të raportonte shkelje fantazmë që askush nuk
do t'i shpjegonte dot.

**Objekte të ndryshueshme.** Një gjetje e nxjerrë që modifikohet nga një
shtresë e mëpasme e prish gjurmën e auditimit (NFR2): nuk dihet më cila
shtresë e vendosi vlerën përfundimtare.

## Pasojat

Garancia qendrore e punimit shprehet si nënshkrim tipi:
`build_prompt(ctx: GroundingContext) -> str`. Modeli gjuhësor nuk ka
parametër për dokumentin e papërpunuar, prandaj mungesa e qasjes nuk
është premtim por veti e kodit.

Çmimi është ashpërsia: një fushë e re kërkon ndryshim në modelin,
gjeneruesin dhe testet njëkohësisht. Kjo është e qëllimshme.
