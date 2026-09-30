# 0014 — Seancat e revokueshme, rrotullimi i tokenëve dhe kufizimi i hyrjeve

**Gjendja:** i zbatuar

## Konteksti

ADR 0013 la dy boshllëqe të shënuara: hyrja nuk kishte kufi provash, dhe
një token rifreskimi i vjedhur mbetej i vlefshëm deri në skadim — shtatë
ditë. Të dyja kanë të njëjtën rrënjë: tokenët ishin vetëm nënshkrime, dhe
shërbimi nuk kishte asnjë gjendje për t'i pyetur ose për t'i hequr.

Të dhënat që mbrohen janë shëndetësore, dhe një llogari e hyrë nga dikush
tjetër sheh dokumentet, vlerat dhe shpjegimet e pacientit.

## Vendimi

**Seancë e revokueshme.** Çdo hyrje hap një rresht `auth_sessions`. Të dy
tokenët mbajnë `sid`-in e saj. `current_login` kontrollon në çdo kërkesë që
seanca ekziston, i përket përdoruesit të tokenit dhe nuk është revokuar.
Kostoja është një lexim për kërkesë me çelës primar; fitimi është që
revokimi vlen menjëherë, jo pas 30 minutash.

**Tokeni i rifreskimit vlen një herë.** Mban `jti`, që ka rresht në
`refresh_tokens`. Rifreskimi e shpenzon me një `UPDATE … WHERE used_at IS
NULL` dhe jep një të ri në të njëjtën seancë. Nëse një token i shpenzuar
paraqitet sërish, dikush ka dy kopje — përdoruesi dhe dikush tjetër — dhe
shërbimi nuk ka si të dijë cili është cili. Revokon gjithë seancën: të dy
humbasin aksesin, përdoruesi hyn sërish, vjedhësi jo. Vjedhja që para
ishte e padukshme tani ka një pasojë të dukshme.

**Dritarja e hirit (10 s).** Dy rifreskime paralele të të njëjtit klient
do të dukeshin si ripërdorim. Brenda dritares, tokeni i shpenzuar
refuzohet me 401 pa u revokuar seanca. Një vjedhësi kjo nuk i jep asgjë:
merr 401 njësoj, jo token të ri. Klienti e heq shkakun nga ana e vet:
rifreskimi bëhet një herë për të gjitha kërkesat paralele, dhe një kërkesë
që merr 401 pasi tokeni ndryshoi e përsërit pa rifreskuar (`client.ts`).

**Dalja revokon.** `POST /auth/logout` revokon seancën; ndërfaqja e thërret
para se të fshijë tokenët lokalë.

**Kufizimi i hyrjeve me tri kova**, secila me dritare 15 minutash:

| Kova | Çelësi | Kufiri | Ndalon |
|---|---|---|---|
| çifti | (email, IP) | 5 | provën e një llogarie nga një vend |
| IP | IP | 20 | provën e shumë llogarive nga një vend |
| email | email | 20 | provën e shpërndarë të një llogarie nga shumë vende |

Kufiri i ngushtë është te çifti, jo te email-i, me qëllim: një sulmues nga
një IP tjetër nuk i mbush dështimet e çiftit të viktimës, prandaj nuk e
mbyll dot llogarinë e saj. Kova e email-it është kompromisi i pranuar dhe
ka kufi më të lartë. Një hyrje e suksesshme fshin dështimet e çiftit të vet.

Katër pohime mbi sjelljen, secili i qëllimshëm:

- Kufizimi vlen njësoj për email të panjohur dhe të njohur. Përgjigjja 429
  nuk tregon nëse llogaria ekziston, e njëjta veti që ka mesazhi 401.
- Një çift i bllokuar refuzohet edhe me fjalëkalimin e saktë; përndryshe
  provat do të vazhdonin derisa një të kishte sukses.
- Një kërkesë e refuzuar nuk numërohet si dështim; përndryshe një sulmues
  do ta mbante llogarinë e mbyllur pafundësisht.
- **Privatësia.** Email-i dhe IP-ja ruhen vetëm si HMAC-SHA256 me çelës
  (`security.keyed_hash`), me etiketë që i ndan, dhe rreshtat fshihen sapo
  dalin nga dritarja. Log-u i auditimit shënon që një kovë u mbush — një
  herë për mbushje, jo për kërkesë — dhe asnjë identifikues.

**IP-ja e klientit.** Pa konfigurim, adresa e lidhjes. Pas një proxy, me
`ANALYTE_TRUSTED_PROXY_HOPS=n`, e n-ta nga e djathta te `X-Forwarded-For`.
Nëse koka është më e shkurtër se pritej, adresa e lidhjes.

## Alternativat e refuzuara

**Numërues në Redis.** Është e zakonshme, por API-ja sot nuk ka lidhje me
Redis-in — vetëm punëtori — dhe testet e API-së ekzekutohen pa të. Një
varësi e re vetëm për këtë do t'i dobësonte provat.

**Kufizim vetëm sipas email-it.** I thjeshtë, dhe ia jep çdokujt që njeh
email-in e dikujt mundësinë ta mbyllë llogarinë e tij.

**Kufizim vetëm sipas IP-së.** Një sulmues me disa adresa e anashkalon, dhe
pas NAT-it një IP e përbashkët do të ndëshkonte përdorues të pafajshëm.

**Listë e zezë e `jti`-ve pa seancë.** Revokon një token, jo gjithë kopjet
e një hyrjeje; s'ka ku të regjistrohet ripërdorimi si sinjal vjedhjeje.

**Vetëm tokenë aksesi më të shkurtër.** Zvogëlon dritaren, por nuk e mbyll,
dhe e ndëshkon përdoruesin me rifreskime më të shpeshta.

## Pasojat

- **Tokenët e lëshuar para këtij ndryshimi nuk pranohen** (s'kanë `sid` as
  `jti`). Çdo përdorues hyn sërish një herë.
- **Një lexim më shumë për kërkesë të autentikuar**, dhe një shkrim për
  çdo hyrje të dështuar. Të dyja janë të kufizuara nga vetë kufizimi.
- **Dalja me token aksesi të skaduar nuk revokon te shërbimi.** Tokenët
  fshihen lokalisht gjithsesi (ruhen në `sessionStorage`), prandaj rreziku
  ka të bëjë vetëm me tokenë të kopjuar, dhe seanca skadon vetë.
- **Regjistrimi ende e tregon nëse një email ka llogari** (409). Kjo është
  e vërtetë dhe e hapur: hyrja e fsheh, regjistrimi jo, dhe kufizimi nuk e
  mbulon regjistrimin. Një ndryshim që e mbyll kërkon konfirmim me email,
  që sistemi s'e ka.
- **IPv6.** Një sulmues me një bllok /64 ndryshon adresën lirisht; kova e
  IP-së dhe e çiftit anashkalohen, dhe mbetet vetëm ajo e email-it.
- **Çelësi i HMAC-it është sekreti i JWT-së.** Ndryshimi i tij pastron
  praktikisht numëruesit; nuk ka pasojë tjetër, sepse rreshtat jetojnë
  vetëm 15 minuta.
- **Nuk ka "dil kudo"** (revokim i të gjitha seancave të një përdoruesi).
  Shtohet lehtë mbi `auth_sessions`, por s'ka ende pikë fundore.

## Çfarë u provua

`tests/integration/test_auth_hardening.py`: secila kovë ndalon atë që duhet
dhe jo më shumë; një sulmues nga një IP tjetër nuk e mbyll viktimën;
email-i i panjohur dhe i njohur kufizohen njësoj; tabela dhe auditimi nuk
mbajnë email apo IP; `Retry-After` llogaritet nga dështimi që po bllokon;
tokeni vlen një herë; ripërdorimi pas dritares revokon seancën, edhe aksesin
e saj, dhe lë seancat e tjera; dalja revokon menjëherë; tokenët pa seancë,
me seancë të panjohur ose të një përdoruesi tjetër refuzohen.

Pesë nga pohimet më të rëndësishme u provuan edhe duke i prishur: heqja e
`commit`-it te dështimi i regjistruar, heqja e `commit`-it te revokimi i
ripërdorimit, mosnderimi i revokimit te `current_login`, `Retry-After` nga
dështimi i gabuar, dhe shpenzimi i tokenit pa kusht. Secila prishje rrëzon
të paktën një test. Dy nga këto janë gabime që sesioni i kërkesës i
fshihte pa zhurmë: ai kthen prapa çdo gjë kur kërkesa përfundon me
përjashtim, dhe si 401 ashtu edhe 429 janë përjashtime.
