# Skicë për paraqitjen etike (E13 dhe E14)

*Skicë pune, jo formulari i institucionit. Formulari, afatet dhe pyetjet e bordit janë të UBT-së dhe i
plotëson autori me mentorin. Këtu janë vetëm faktet për sistemin, të marra nga kodi, dhe pyetjet që një bord
do t'i bënte pasi t'i lexojë. Çdo gjë e shënuar **[konfirmo]** nuk është verifikuar dhe nuk duhet shkruar si e
vërtetë pa u konfirmuar.*

## 1. Çfarë kërkohet të miratohet

Punimi nuk ka asnjë matje mbi dokumente reale dhe asnjë studim me përdorues (§6.8, §6.9). Dy matje varen nga
miratimi:

| Matja | Çfarë do të bëhej | Çfarë mungon për ta përshkruar |
|---|---|---|
| **E13** — vlefshmëria e jashtme | Sistemi përpunon dokumente laboratorike reale shqip dhe krahasohet me anotim të njeriut (Shtojca E, aktualisht «nuk aplikohet») | burimi i dokumenteve, numri, kush i anoton, si çidentifikohen **[konfirmo]** |
| **E14 / PK7** — studim me përdorues | Pjesëmarrësit lexojnë shpjegime dhe përgjigjen për kuptueshmërinë (Shtojca F, «nuk aplikohet») | instrumenti, përzgjedhja, pëlqimi, numri **[konfirmo]** |

## 2. Çfarë të dhënash prek sistemi

- **PDF-ja e ngarkuar.** Mban emrin e pacientit dhe të dhëna shëndetësore (kategori e veçantë sipas §3.7.3).
- **Gjetjet e nxjerra:** analiti, vlera, njësia, intervali, statusi, koordinatat në faqe.
- **Narrativa e mjekut** e ndarë në pohime (polaritet, siguri, lloj). Citimet e mjekut kalojnë fjalë për fjalë.
- **Llogaria e përdoruesit:** email dhe fjalëkalim i hashuar (Argon2id).
- **Gjurma e auditimit:** ngjarje (ngarkim, kalime gjendjesh, pëlqim dhe përdorim i modelit, fshirje, skadim, eksport) pa
  përmbajtje.
- **Pëlqimi për modelin gjuhësor,** për çdo ngarkim, me kohën (`documents.model_consent`, `model_consent_at`), kur
  shërbimi e ka modelin të ndezur (ADR 0019).

## 3. Masat që janë zbatuar (me vendin në kod)

| Masa | Ku |
|---|---|
| PDF-ja ruhet e koduar (Fernet), me emër të rastësishëm; çelësi nuk ka vlerë parazgjedhëse dhe shërbimi nuk nis pa të | `persistence/storage.py` |
| Përpunimi lexon një kopje të përkohshme që fshihet sapo mbaron blloku, edhe kur përpunimi dështon | `persistence/storage.py` (`decrypted`) |
| Gjurma e auditimit nuk mund të regjistrojë emra, email-e ose vlera laboratorike (funksionet pranojnë vetëm identifikues dhe llojin e ngjarjes) | `audit/logger.py` |
| Përdoruesi mund ta fshijë dokumentin: fshihen rreshti në bazë, gjithçka e derivuar prej tij dhe skedari i koduar; fshirja regjistrohet | `api/documents.py` (`DELETE /documents/{id}`), `erasure.py` |
| Përdoruesi mund ta fshijë llogarinë me gjithçka të saj (dokumente, skedarë, seanca, tokenë, numërues të kufizimit), duke dhënë fjalëkalimin aktual; në gjurmën e auditimit `user_id` bëhet bosh dhe hash-i i skedarit hiqet. Nuk ka ndërfaqe, vetëm API | `api/privacy.py` (`DELETE /me/data`), ADR 0019 |
| Përdoruesi mund t'i eksportojë të dhënat e veta si JSON, pa kredenciale e pa të dhëna të të tjerëve | `api/privacy.py` (`GET /me/export`) |
| Afati i ruajtjes, i konfigurueshëm; **i fikur si parazgjedhje** (`ANALYTE_DOCUMENT_RETENTION_DAYS=0`); me vlerë pozitive punëtori fshin çdo orë dokumentet më të vjetra me të njëjtën rrugë fshirjeje. Afati nuk është caktuar | `erasure.py` (`purge_expired`), `orchestration/worker.py` |
| Modeli gjuhësor përdoret vetëm për ngarkimet ku pacienti shënoi kutinë e pëlqimit (e pashënuar si parazgjedhje, vlen për një ngarkim); pa të, shpjegimi del nga shablloni dhe nuk bëhet asnjë thirrje te ofruesi; pacienti merr njoftimin përkatës | `orchestration/model_gate.py`, `api/documents.py`, `ModelConsent.tsx` |
| Para çdo dërgimi te ofruesi, citimet e mjekut dhe termat e pashpjeguar kalojnë një portë çidentifikimi (emra, tituj, data, telefona, email, numra të gjatë, identifikues, moshë, adresa) që **dështon e mbyllur**: nëse shënon diçka, dokumenti nuk dërgohet fare. Është heuristikë, jo çidentifikim i provuar (shih §4) | `generation/deidentify.py`, ADR 0019 |
| Modeli gjuhësor merr vetëm `GroundingContext`; emri, mosha dhe gjinia nuk hyjnë në të (gjinia përdoret vetëm për zgjidhjen e intervalit, para formimit të kontekstit) | `generation/prompt.py`, §5.2.1 |
| Hyrja me kufizim, seanca të revokueshme, token rifreskimi me përdorim të vetëm | ADR 0014 |
| Teksti i paverifikuar nuk i shfaqet përdoruesit; kur verifikimi dështon dy herë del shablloni | `orchestration/process.py`, ADR 0011 |

## 4. Çfarë do të pyeste një bord (boshllëqe të njohura, pa e zbutur)

1. **Dërgimi te një ofrues i jashtëm.** Modeli gjuhësor (Mistral, plan falas) u lidh me aplikacionin më 2026-10-05, por është
   i fikur si parazgjedhje (`ANALYTE_SERVICE_GENERATOR=template`; ADR 0017), dhe deri sot ka punuar vetëm mbi dokumente sintetike
   (eksperimentet dhe një provë). Kur ndizet (`=model`), konteksti i një dokumenti (vlera laboratorike, intervale, statuse,
   termat me shpjegimet e fjalorit, citime të mjekut; jo emri, mosha, gjinia, emri i skedarit apo PDF-ja; pa cache në disk) i
   dërgohet ofruesit **vetëm nëse pacienti ka shënuar kutinë e pëlqimit për atë ngarkim dhe porta e çidentifikimit nuk ka
   shënuar asgjë** (ADR 0019). Intervalet referente të disa analiteve varen nga gjinia dhe dërgohen si numra, prandaj gjinia
   mund të nxirret tërthorazi. Çfarë bën ofruesi me të dhënat: kushtet e planit falas për ruajtjen dhe përdorimin për
   trajnim **[konfirmo nga kushtet e ofruesit; mos supozo]**. Sistemi nuk ka asnjë mënyrë t'i kërkojë ofruesit fshirjen e
   asaj që ka marrë. Alternativa e përmendur te §3.7.3 është një model lokal (E15), i pamatur.
2. **Porta e çidentifikimit është heuristikë.** Citimet e mjekut kontrollohen për emra (fjalë me shkronjë të madhe jashtë
   fjalorit klinik), tituj, data, telefona, email, numra të gjatë, identifikues, moshë dhe adresa, dhe dokumenti nuk dërgohet
   nëse diçka shënohet; citimi nuk redaktohet kurrë, që pacienti ta shohë të pandryshuar dhe rregullat R5, R6, R8 të vlejnë.
   **Nuk kap** emra me shkronja të vogla, emra që rastisin me një fjalë të fjalorit, pothuajse-identifikues pa trajtë (një
   profesion i rrallë, një ngjarje e veçantë), as ç'nuk skanohet sepse nuk dërgohet. Mbi-bllokon (një fjali që hapet me fjalë
   të zakonshme jashtë listës, një numër me katër shifra). Është provuar vetëm me fjali të shkruara nga autori dhe me narrativat
   sintetike; **nuk është matur mbi tekst real të mjekut.** Një dokument që kalon portën mund të mbajë ende të dhëna personale.
3. **Pëlqimi me kuti në ndërfaqe nuk është vendosur si i vlefshëm ligjërisht.** Kuti e pashënuar, një tekst që thotë çfarë
   dërgohet dhe çfarë jo, pëlqim i ruajtur me kohë dhe i auditueshëm: kjo është mekanika. Nëse ajo e plotëson kërkesën e një
   pëlqimi për të dhëna shëndetësore është pyetje për autorin dhe mentorin **[REFERENCË — plotësohet]**.
4. **Regjistrimi tregon nëse një email ka llogari** (ADR 0014); mbyllja kërkon konfirmim me email, që sistemi s'e ka.
   (Kjo pikë u shkrua para ADR 0016: konfirmimi me email dhe përgjigja e njëjtë për çdo email tani ekzistojnë; rishikoje.)
5. **Gabimet e OCR-së pranohen me besim:** 125 nga 2 370 vlera të skanuara janë të gabuara dhe interpretohen (§6.2).
   Për dokumente reale kjo do të thoshte shpjegim i gabuar për një pacient. **Propozim (vendimi është i autorit
   dhe i bordit):** matja reale të bëhet pa u dhënë shpjegimet pacientëve.
6. **Asnjë rishikim klinik.** Rregullat e kombinimit dhe tabela terminologjike nuk kanë burim të lexuar nga mjek
   (kolonat `source_ref`); audit i pavarur i tekstit të gjeneruar gjeti problem te 58% e teksteve (§6.6.1).
7. **Statusi rregullator.** Punimi pozicionohet jashtë pajisjes mjekësore dhe vetë thotë që kjo nuk është e
   garantuar (§3.7.1).

## 5. Çfarë duhet nga autori dhe institucioni

- Formulari dhe afatet e bordit etik të UBT-së (ose i mentorit) **[konfirmo]**.
- Mentori si përgjegjës; kontakt me një mjek ose laborator që jep dokumente të çidentifikuara **[konfirmo]**.
- Vendimi: E13 vetëm me dokumente të çidentifikuara nga burimi (autori nuk i sheh emrat), apo me pëlqim të pacientit.
- Teksti i pëlqimit për E14 dhe protokolli i anotimit (Shtojca E, F) — të shkruhen nga autori; asnjë përgjigje
  pjesëmarrësi nuk fabrikohet (§6.9).
- Vendim për ofruesin e modelit gjuhësor gjatë E13/E14: e njëjta, tjetër, ose model lokal.
- Vendimet që ADR 0019 i lë të hapura dhe që kodi nuk i merr: kushtet e ofruesit për ruajtjen e trajnimin; baza ligjore e
  përpunimit të të dhënave shëndetësore; marrëveshja e përpunimit me ofruesin, nëse kërkohet; ku ndodhet përpunimi i ofruesit
  (transferimi jashtë BE-së); a plotësohet pëlqimi me kutinë e ndërfaqes; sa ditë ruhet një dokument
  (`ANALYTE_DOCUMENT_RETENTION_DAYS`, sot 0 = pa afat); dhe a pranohet gjurma e auditimit që mbetet pas fshirjes
  (identifikuesi i rastësishëm i dokumentit, koha, lloji i ngjarjes). Çdo gjë e ligjshme këtu të shkruhet me burimin e
  lexuar nga autori **[REFERENCË — plotësohet]**.

## 6. Çfarë mbetet e pavërtetuar këtu

Gjithçka e shënuar **[konfirmo]**, dhe çdo pohim ligjor (baza ligjore sipas GDPR Neni 9, transferimi
ndërkombëtar): skica nuk e vendos. Të dyja kërkojnë burimin ligjor që e lexon vetë autori dhe konfirmimin e
mentorit.
