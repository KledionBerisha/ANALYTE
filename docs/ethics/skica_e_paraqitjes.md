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
- **Gjurma e auditimit:** ngjarje (ngarkim, kalime gjendjesh, fshirje) pa përmbajtje.

## 3. Masat që janë zbatuar (me vendin në kod)

| Masa | Ku |
|---|---|
| PDF-ja ruhet e koduar (Fernet), me emër të rastësishëm; çelësi nuk ka vlerë parazgjedhëse dhe shërbimi nuk nis pa të | `persistence/storage.py` |
| Përpunimi lexon një kopje të përkohshme që fshihet sapo mbaron blloku, edhe kur përpunimi dështon | `persistence/storage.py` (`decrypted`) |
| Gjurma e auditimit nuk mund të regjistrojë emra, email-e ose vlera laboratorike (funksionet pranojnë vetëm identifikues dhe llojin e ngjarjes) | `audit/logger.py` |
| Përdoruesi mund ta fshijë dokumentin: fshihen rreshti në bazë dhe skedari i koduar; fshirja regjistrohet | `api/documents.py` (`DELETE /documents/{id}`) |
| Modeli gjuhësor merr vetëm `GroundingContext`; emri, mosha dhe gjinia nuk hyjnë në të (gjinia përdoret vetëm për zgjidhjen e intervalit, para formimit të kontekstit) | `generation/prompt.py`, §5.2.1 |
| Hyrja me kufizim, seanca të revokueshme, token rifreskimi me përdorim të vetëm | ADR 0014 |
| Teksti i paverifikuar nuk i shfaqet përdoruesit; kur verifikimi dështon dy herë del shablloni | `orchestration/process.py`, ADR 0011 |

## 4. Çfarë do të pyeste një bord (boshllëqe të njohura, pa e zbutur)

1. **Dërgimi te një ofrues i jashtëm.** Sot asnjë e dhënë e vërtetë nuk del nga sistemi: modeli gjuhësor (Mistral, plan falas)
   thirret vetëm nga harness-i i vlerësimit, mbi dokumente sintetike, dhe aplikacioni i uebit gjeneron me shabllon.
   Nëse modeli lidhet me aplikacionin, ose përdoret te E13/E14, konteksti (vlera laboratorike dhe citime të mjekut)
   do të dërgohej te ofruesi. Nëse një citim përmban emër ose detaj identifikues, ai do të dilte jashtë sistemit. Punimi nuk
   ka një hap që ta heq. Kushtet e planit falas për ruajtjen dhe përdorimin e të dhënave për trajnim **[konfirmo
   nga kushtet e ofruesit; mos supozo]**. Alternativa e përmendur te §3.7.3 është një model lokal (E15), i pamatur.
2. **Citimet e mjekut nuk çidentifikohen.** Rregullat kontrollojnë që citimi të ruhet, jo që të mos përmbajë identifikues.
3. **Regjistrimi tregon nëse një email ka llogari** (ADR 0014); mbyllja kërkon konfirmim me email, që sistemi s'e ka.
4. **Gabimet e OCR-së pranohen me besim:** 125 nga 2 370 vlera të skanuara janë të gabuara dhe interpretohen (§6.2).
   Për dokumente reale kjo do të thoshte shpjegim i gabuar për një pacient. **Propozim (vendimi është i autorit
   dhe i bordit):** matja reale të bëhet pa u dhënë shpjegimet pacientëve.
5. **Asnjë rishikim klinik.** Rregullat e kombinimit dhe tabela terminologjike nuk kanë burim të lexuar nga mjek
   (kolonat `source_ref`); audit i pavarur i tekstit të gjeneruar gjeti problem te 58% e teksteve (§6.6.1).
6. **Statusi rregullator.** Punimi pozicionohet jashtë pajisjes mjekësore dhe vetë thotë që kjo nuk është e
   garantuar (§3.7.1).

## 5. Çfarë duhet nga autori dhe institucioni

- Formulari dhe afatet e bordit etik të UBT-së (ose i mentorit) **[konfirmo]**.
- Mentori si përgjegjës; kontakt me një mjek ose laborator që jep dokumente të çidentifikuara **[konfirmo]**.
- Vendimi: E13 vetëm me dokumente të çidentifikuara nga burimi (autori nuk i sheh emrat), apo me pëlqim të pacientit.
- Teksti i pëlqimit për E14 dhe protokolli i anotimit (Shtojca E, F) — të shkruhen nga autori; asnjë përgjigje
  pjesëmarrësi nuk fabrikohet (§6.9).
- Vendim për ofruesin e modelit gjuhësor gjatë E13/E14: e njëjta, tjetër, ose model lokal.

## 6. Çfarë mbetet e pavërtetuar këtu

Gjithçka e shënuar **[konfirmo]**, dhe çdo pohim ligjor (baza ligjore sipas GDPR Neni 9, transferimi
ndërkombëtar): skica nuk e vendos. Të dyja kërkojnë burimin ligjor që e lexon vetë autori dhe konfirmimin e
mentorit.
