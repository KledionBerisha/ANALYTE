# Protokolli i propozuar për E13 dhe E14

*Draft pune për paraqitjen etike. **Nuk është kryer asnjë matje** dhe asnjë numër këtu nuk është rezultat. Çdo gjë e shënuar
**[konfirmo]** është vendim i autorit, i mentorit ose i bordit; çdo burim që duhet është **[REFERENCË — plotësohet]**.
Skica e faktave për sistemin është te `skica_e_paraqitjes.md`; ky skedar thotë çfarë do të matej dhe si, që bordi të ketë çfarë të miratojë.*

## 0. Dy vendime që e ndryshojnë gjithçka

1. **E14 nuk ka nevojë për dokumente reale të pacientëve.** Pjesëmarrësit mund të lexojnë raporte *sintetike* (nga gjeneruesi i korpusit,
   me gjetje, vlera kritike dhe pohime mjeku të njohura), kështu që nuk futet asnjë e dhënë shëndetësore e vërtetë. Studimi mbetet studim me njerëz
   (pëlqim, privatësi e pjesëmarrësve), por pa kategori të veçantë të dhënash. Kjo e bën E14 shumë më të lehtë për t'u miratuar se E13.
2. **E13 me modelin të fikur.** Me dokumente reale, shërbimi duhet të gjenerojë vetëm me shabllon (`ANALYTE_SERVICE_GENERATOR=template`, parazgjedhja).
   Kështu asnjë e dhënë nuk del nga sistemi (ADR 0017, 0019). Ndezja e modelit mbi dokumente reale kërkon vendimet ligjore të hapura (kushtet e
   ofruesit, baza ligjore, marrëveshja e përpunimit, transferimi jashtë BE-së) dhe nuk duhet të hyjë te kjo kërkesë **[konfirmo]**.

## 1. E13 — vlefshmëria e jashtme mbi dokumente reale

**Pyetja.** A mbajnë përfundimet e Kapitullit 6 (nxjerrja, statusi, kundërshtimet raport–laborator, verifikimi) kur dokumentet nuk janë sintetike?
Sot asnjë numër nuk është matur mbi dokumente reale; 1.000 mbi dixhitalet mat lidhjen e tubacionit, jo vështirësinë.

**Mostra.** Dokumente laboratorike shqip, dixhitale dhe të skanuara, të dhëna nga laboratorë ose pacientë me pëlqim **[konfirmo]**. Madhësia nuk
është caktuar këtu: duhet të mjaftojë që intervali i besimit i F1-së së nxjerrjes të jetë më i ngushtë se diferenca që kërkohet të zbulohet, dhe të ketë
të paktën disa dhjetëra dokumente të skanuara, sepse OCR-ja është kanali më i dobët **[konfirmo numrin]**. Dokumentet nga laboratorë të ndryshëm janë
më të vlefshme se shumë nga i njëjti formular.

**Çidentifikimi në burim.** Para se një dokument të hyjë te depoja: heqja e emrit, datëlindjes, numrave të identifikimit dhe adresës nga PDF-ja
(ose nga fotokopja), nga një person që nuk është anotuesi **[konfirmo kush dhe si]**. Sistemi nuk e bën këtë; porta e çidentifikimit (ADR 0019) është heuristikë
për citimet e dërguara te modeli, jo për PDF-të.

**Anotimi (e vërteta bazë).** Çdo dokument anotohet nga dy persona të pavarur; mospërputhjet zgjidhen nga i treti. Anotuesit shënojnë, për çdo rresht:
analitin, vlerën, njësinë, intervalin e shtypur, statusin (normale, e lartë, e ulët, kritike, e painterpretueshme), dhe për narrativën pohimet (analiti, drejtimi,
mohimi, rezerva, rekomandimi). Udhëzimet janë ato që do të futen te Shtojca E; ato duhet të përdorin përkufizimet e Shtojcës A/C, jo të shpiken përsëri.
Raportohet pajtimi mes anotuesve (p.sh. koeficienti kappa i Cohen-it), që e vërteta bazë të mos merret si e pagabueshme [REFERENCË — plotësohet].

**Çfarë matet** (të njëjtat metrika si te Kapitulli 6, kështu që krahasimi me korpusin sintetik është i drejtpërdrejtë): F1 i nxjerrjes (PK1) dhe saktësia e statusit
(PK2) të ndara dixhital/skanuar; sa vlera të gabuara pranohen dhe sa statuse janë të interpretuara gabim (sidomos kritike të rreme dhe kritike të humbura); saktësia e
krahasimit të kryqëzuar (PK4); sa dokumente përfundojnë te shablloni dhe pse; kontrolli i OCR-së (ADR 0020) mbi skanime reale (sa rreshta refuzon, sa prej tyre ishin të sakta).
**Rezultati i pritur nuk shkruhet para matjes**: korpusi sintetik është shumë më i pastër, prandaj rënie është e mundshme dhe duhet raportuar si e tillë.

**Çfarë nuk mat E13.** Kuptueshmërinë për pacientin (kjo është E14) dhe cilësinë e gjuhës së modelit (modeli është i fikur).

**Harness.** Dokumentet e anotuara futen si korpus me të njëjtin format (`data/<emri>/`, me `truth` për çdo dokument) dhe ekzekutohen me
`python -m evaluation.harness --dataset data/<emri> --pipeline grounding --ocr --ocr-guard`; deri tani formati ekziston vetëm për korpusin sintetik, kështu që
një shndërrues nga anotimet te ky format duhet shkruar **[konfirmo]**.

## 2. E14 — kuptueshmëria te përdoruesit (PK7)

**Pyetja.** A i kuptojnë pjesëmarrësit më mirë rezultatet kur lexojnë shpjegimin e sistemit sesa kur lexojnë vetë raportin laboratorik?

**Dizajni.** Brenda subjekteve, dy kushte: (A) raporti origjinal, (B) raporti plus shpjegimi i sistemit. Çdo pjesëmarrës lexon dy raporte *të ndryshme* sintetike
me vështirësi të krahasueshme, një për kusht; renditja e kushteve dhe cili raport i shkon cilit kusht ndërrohen midis pjesëmarrësve (kundërpeshim) që të mos
përzihen efektet e renditjes dhe të raportit. Specifikimi mban n=12–20; kjo është e vogël, prandaj rezultati është eksplorues **[konfirmo]**.

**Pjesëmarrësit.** Të rritur që nuk janë profesionistë shëndetësorë, shqipfolës, me pëlqim të informuar; përjashtohen studentët e mjekësisë dhe farmacisë
(do ta ndryshonin pyetjen). Përzgjedhja nuk është përfaqësuese dhe kjo thuhet **[konfirmo si rekrutohen]**.

**Instrumenti** (Shtojca F). Për çdo raport, pyetje me përgjigje të vërtetueshme nga raporti, të shkruara para studimit:
1. *Ç'është jashtë intervalit?* Pjesëmarrësi emërton vlerat jashtë intervalit (saktësi/recall kundrejt gjetjeve të njohura).
2. *Drejtimi:* për dy vlera të dhëna, të larta apo të ulëta.
3. *Urgjenca:* a ka diçka që kërkon kontakt të shpejtë me mjekun? (raportet me vlerë kritike dhe pa të, përzier.)
4. *Çfarë tha mjeku:* një pohim me mohim ose rezervë ("nuk përjashtohet…") — a e kuptoi pjesëmarrësi saktë?
5. *Vlera pa interval:* a e kuptoi pjesëmarrësi se ajo nuk interpretohet?
Pas çdo raporti: besimi në përgjigje (shkallë 1–5), vështirësia e perceptuar (1–5), dhe një pyetje e hapur. Në fund: qëndrimi ndaj shpjegimit (a do ta përdorte; a ka
diçka që e ngatërroi) dhe pyetje për përvojën me raportet. Shkallët e pranuara për kuptueshmëri ose përdorshmëri, nëse përdoren, duhen cituar [REFERENCË — plotësohet].

**Çfarë matet.** Pjesa e përgjigjeve të sakta për kusht (kryesorja), koha për raport, besimi dhe vështirësia e raportuar, dhe, më e rëndësishmja për sigurinë, a i
humb pjesëmarrësit më shumë vlera kritike me shpjegimin sesa pa të (një shpjegim që qetëson gabim është dëmi që sistemi duhet të shmangë). Analiza: dallimet e çiftuara për
pjesëmarrës me intervale besimi (jo vetëm vlera p), sepse me n të vogël një vlerë p nuk është provë; rezultatet raportohen edhe kur dalin kundër sistemit.

**Çfarë shpjegimi shihet.** Shablloni determinist (garancia më e fortë) dhe, veçmas dhe vetëm nëse vendimet ligjore e lejojnë për tekst sintetik (që nuk është i dhënë
personal), teksti i modelit. Dy grupe pjesëmarrësish të ndara ose një studim i dytë; nuk përzihen në një krahasim të vetëm.

**Etika.** Pëlqim me shkrim: qëllimi, ajo që kërkohet, pa dëm të pritshëm përtej lodhjes, e drejta për t'u tërhequr në çdo kohë pa pasoja dhe fshirja e të dhënave, ku
ruhen përgjigjet (të pa emrave, me kod). Raportet janë sintetike dhe pjesëmarrësit informohen se nuk janë të vërteta dhe nuk zëvendësojnë këshillën mjekësore.
Përgjigjet nuk kombinohen me të dhëna identifikuese **[konfirmo me bordin]**.

## 3. Çfarë duhet para se të nisë

| Hap | Kush |
|---|---|
| Formulari i bordit të UBT-së dhe mentori | autori |
| Vendimi: E14 me raporte sintetike (rekomandohet), E13 me model të fikur | autori, mentori |
| Burimi i dokumenteve reale dhe pëlqimi i tyre (vetëm E13) | autori, laboratori **[konfirmo]** |
| Anotuesit dhe çidentifikuesi (vetëm E13) | autori **[konfirmo]** |
| Shndërruesi i anotimeve te formati i harness-it (vetëm E13) | mund ta shkruaj kur formati i anotimit të jetë i caktuar |
| Pilot me 2–3 vetë para studimit, për të gjetur pyetje të paqarta | autori |

## 4. Çfarë NUK u bë

Nuk u mblodh asnjë dokument real, nuk u rekrutua asnjë pjesëmarrës, nuk u përgjigj asnjë pyetësor, dhe nuk u fabrikua asnjë rezultat. Seksionet 6.8 dhe 6.9 të punimit mbeten
«nuk u krye» derisa këto të ekzekutohen nga autori.
