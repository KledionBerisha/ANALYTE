# 0019 — Mbrojtja e të dhënave: pëlqimi për modelin, porta e çidentifikimit, fshirja, eksporti dhe afati i ruajtjes

**Gjendja:** i zbatuar teknikisht; vendimet ligjore dhe etike mbeten të autorit (shih "Çfarë mbetet vendim i autorit"). Modeli mbetet i fikur si parazgjedhje (ADR 0017).

## Konteksti

ADR 0017 e lidhi modelin gjuhësor me aplikacionin si zgjedhje e shprehur e shërbimit (`ANALYTE_SERVICE_GENERATOR=model`) dhe la hapur tre pyetje të dokumentuara te skica etike (`docs/ethics`): kushtet e ofruesit për ruajtjen dhe përdorimin e të dhënave, pëlqimi i pacientit, dhe nëse citimet e mjekut duhet të çidentifikohen para dërgimit. ADR 0017 thoshte gjithashtu se "nëse një citim ka emër ose detaj identifikues, ai shkon te ofruesi, dhe nuk ka hap që ta heq". Zgjedhja e shërbimit nuk ishte pëlqim i pacientit: kur shërbimi ishte në `model`, çdo dokument shkonte te ofruesi.

Ky ADR ndërton kontrollet teknike që i bëjnë ato vendime të zbatueshme, dhe nuk i merr vetë. Kodi nuk pohon asgjë për kushtet e një ofruesi, as për bazën ligjore të përpunimit; ato janë të autorit dhe renditen më poshtë.

## Vendimi

### 1. Pëlqim për çdo ngarkim

Forma e ngarkimit ka fushën `model_consent` (parazgjedhja `false`). Ruhet për çdo dokument, me kohën (`documents.model_consent`, `model_consent_at`), dhe regjistrohet te auditimi si ngjarja `document.model_consent` me ngarkesë `{"given": true|false}` (asnjë e dhënë personale). Pëlqimi pyetet vetëm kur shërbimi e ka modelin të ndezur: kur është `template`, fusha ruhet `false` edhe nëse klienti dërgoi `true`, dhe nuk shkruhet ngjarje (nuk u pyet asgjë).

Kur gjeneruesi dërgon kontekstin jashtë sistemit (`LlmGenerator.sends_data_off_system`), për çdo dokument vendoset me radhë (`orchestration/model_gate.py`):

1. **pa pëlqim** → shablloni determinist; nuk ndërtohet kërkesë dhe nuk bëhet asnjë thirrje në rrjet; njoftimi `model_declined` i thotë pacientit pse;
2. **me pëlqim, por porta e çidentifikimit shënon diçka** → shablloni, me njoftimin `model_withheld` që emërton kategoritë (jo vargjet);
3. **me pëlqim dhe pa shënime** → modeli, si te ADR 0017 (verifikim, një rigjenerim, shabllon rezervë).

Pëlqimi nuk e anashkalon portën: ai është leje për të dërguar atë që porta lejon. Vendimi ruhet te `documents.model_use` (`used`, `no_consent`, `identifying_content`) dhe te ngjarja `document.model_use`; kategoritë e portës ruhen si kode (`name_like,date`), kurrë si tekst.

**Çfarë i dërgohet ofruesit, nga kërkesa e vërtetë** (`generation/prompt.py`): emrat kanonikë të analiteve; vlera e matur me njësinë kanonike; pozicioni ndaj intervalit (fraza fikse) dhe numrat e intervalit; emrat e analiteve në kombinime; termat që përmend raporti me shpjegimet e fjalorit; fjalët e termave të pashpjeguar; fjalitë e mjekut fjalë për fjalë; teksti fiks i politikës; dhe, në përpjekjen e dytë, fjalitë e daljes së refuzuar të modelit me arsyen e rregullit. **Nuk dërgohet:** emri i pacientit, mosha, gjinia, emri i skedarit, PDF-ja, data e matjes, laboratori, faqja, flamujt e shtypur. **Një rrjedhje e tërthortë që duhet ditur:** intervalet referente të disa analiteve ndryshojnë sipas gjinisë (`resources/analytes.csv`); gjinia nuk dërgohet, por numrat e intervalit mund ta lënë të kuptohet. Teksti i pëlqimit te ndërfaqja e thotë këtë.

### 2. Porta e çidentifikimit (`generation/deidentify.py`)

Vetëm dy pjesë të kërkesës vijnë nga teksti i lirë i dokumentit: citimet e mjekut (`ReportAssertion.text_span`) dhe termat e pashpjeguar. Gjithçka tjetër vjen nga katalogu ose nga matjet. Një test e ruan këtë ndarje: vendos shenja te çdo fushë tjetër e tekstit të lirë (emri i papërpunuar, njësia e shtypur, flamuri, burimi i termit) dhe provon që asnjë nuk del te kërkesa; dhe provon që vargjet e skanuara vërtet dalin. Kush e fut një fushë të re te kërkesa e rrëzon testin.

**Lejo-listë së pari.** Vlerat e strukturuara kalojnë vetëm nëse janë pikërisht ato të katalogut (emri kanonik, njësia kanonike, termi dhe shpjegimi i fjalorit); përndryshe `uncatalogued`. Teksti i lirë skanohet për: email, adresë interneti, telefon, datë (me numra ose me emër muaji pranë numrit), moshë dhe datëlindje, numra me katër shifra e më shumë, identifikues me shkronja e shifra, tituj (`Dr`, `Prof`, `Znj`, `Zoti`), shenja adrese e kontakti, dhe **çdo fjalë me shkronjë të madhe që nuk është te fjalori** (analitet dhe variantet e tyre, termat me lakimet e shqipes, fjalët e shpjegimeve dhe të teksteve të politikës, dhe një listë e mbyllur fjalësh të zakonshme klinike). Fjala e parë e një fjalie shkruhet me shkronjë të madhe, prandaj edhe ajo duhet të jetë te fjalori: "Krasniqi ka hemoglobinë të ulët" shënohet.

**Dështimi është i mbyllur, dhe nuk redaktohet.** Kur diçka shënohet, dokumenti nuk dërgohet fare. Alternativa, të zëvendësohet emri me një shenjë fikse, u refuzua për katër arsye: (a) modeli do të kopjonte një citim të ndryshëm nga ai që ruhet, dhe rregullat R5, R6 dhe R8 e krahasojnë daljen me citimin origjinal (R8 kërkon që rekomandimi të gjendet fjalë për fjalë në dalje, prandaj një rekomandim i redaktuar do të refuzohej dy herë); (b) pacienti duhet të shohë citimin e mjekut të pandryshuar, dhe një shenjë te teksti i tij është ndryshim; (c) zëvendësimi mbrapsht pas gjenerimit do të kërkonte të besohej se modeli e ka kopjuar shenjën pa e riformuluar fjalinë; (d) zbulimi i emrave është i pasaktë në të dy drejtimet, dhe një emër i mbetur pas "redaktimit" do të dukej i mbrojtur. Çmimi i dështimit të mbyllur është se shpjegimi del me shabllon për më shumë dokumente se sa duhet; ai nuk humbet dokumentin dhe pacienti merr njoftim.

**Gjetjet nuk mbajnë vargun e shënuar**, vetëm llojin, fushën dhe indeksin: ato shkruhen te auditimi dhe te baza, që nuk guxojnë të mbajnë të dhëna personale (NFR5).

**Matja e vetme:** 0 nga 400 dokumente sintetike u shënuan. Është kontroll për mbi-bllokim mbi narrativat e gjeneruesit, dhe fjalori u formësua mbi të njëjtat fjali, prandaj nuk provon asgjë për tekst real; nuk ka asnjë matje mbi tekst real.

### 3. Fshirja (`erasure.py`, `api/privacy.py`, `api/documents.py`)

Tri rrugë, një funksion: `erase_documents`.

- `DELETE /documents/{id}` (ekzistonte; tani kalon nga funksioni i përbashkët). Dokumenti i një përdoruesi tjetër kthen 404, jo 403.
- `DELETE /me/data` fshin llogarinë: dokumentet, skedarët e koduar, çdo rresht të derivuar, seancat, tokenët e rifreskimit, lidhjet e konfirmimit, numëruesit e kufizimit që mbajnë HMAC të email-it, dhe përdoruesin. Kërkon **fjalëkalimin aktual në trup**: një token aksesi i vjedhur nuk mjafton. Fjalëkalimi i gabuar kthen 403 (jo 401, që klienti të mos nisë një rifreskim) dhe numërohet te kovat e hyrjes (`throttle`), që pika të mos bëhet një rrugë tjetër për të provuar fjalëkalimin; kufizimi kontrollohet para fjalëkalimit, si te hyrja.
- Afati i ruajtjes (më poshtë) përdor të njëjtin funksion.

**Çfarë mbetet pas fshirjes, dhe pse nuk mban të dhëna personale.** Rreshtat e `audit_events`: lloji i ngjarjes, koha, numërime dhe arsye teknike, dhe `document_id` (identifikues i rastësishëm, pa lidhje me person pas fshirjes; pa të, gjurma "u fshi" nuk do t'i përgjigjej asgjëje). Dy gjëra hiqen: `user_id` bëhet bosh në çdo ngjarje të llogarisë së fshirë, dhe `sha256` hiqet nga ngjarja `document.uploaded` e dokumentit të fshirë (hash-i i një PDF-je shëndetësore do të lejonte dikë që e ka skedarin ta provojë se kaloi këtu). Ngjarja `user.erased` mban vetëm numrin e dokumenteve. **Ky është vendim dizajni që autori duhet ta rishikojë**: një gjurmë që mbetet mbas fshirjes është pikërisht ajo që një autoritet mbrojtjeje do të pyeste, dhe ky ADR nuk pohon që është e mjaftueshme ligjërisht.

**Rendi dhe përsëritja.** Rreshtat fshihen, pastaj skedarët, dhe transaksioni ruhet vetëm pasi skedarët u hoqën: nëse fshirja e skedarit dështon, kthehet prapa dhe kërkesa përsëritet; nuk mbetet skedar pa rresht. Fshirja është e përsëritshme (`DELETE … WHERE id IN`, `missing_ok`). Dy fshirje njëkohësisht të së njëjtës llogari ose të të njëjtit dokument provohen mbi PostgreSQL: asnjë nuk del në gabim. Një punë që po përfundon ndërsa dokumenti fshihet nuk shkruan asgjë pas vetes (kontrolli para shkrimit dhe `IntegrityError` e çelësit të huaj trajtohen te `run_document`). Ngarkimi që dështon pas shkrimit të skedarit e fshin skedarin.

**Çfarë nuk mbulon.** Një ngarkim që shkruhet pikërisht kur fshihet llogaria mund të lërë një skedar të koduar pa rresht (rreshti shkon me kaskadë, skedari jo; fshirja rilexon dokumentet tri herë për ta zvogëluar këtë, jo për ta zhdukur). Kopjet rezervë të bazës dhe të dosjes së ruajtjes, nëse ekzistojnë, nuk preken. Tekstet që ofruesi i modelit mund të ketë ruajtur nuk fshihen nga këtu: sistemi nuk ka asnjë mënyrë për t'i kërkuar ofruesit fshirjen.

### 4. Eksporti (`GET /me/export`)

JSON me të dhënat e llogarisë (email, datat), çdo dokument të pronarit (emri i skedarit të dekoduar, metadatat, pëlqimi dhe përdorimi i modelit), gjetjet, pohimet e mjekut, shpjegimin e dorëzuar dhe çdo përpjekje, dhe ngjarjet e auditimit që i përkasin (me `user_id` të tij ose dokumentet e tij). Çdo pyetje filtrohet me pronarin; një test që krijon një përdorues tjetër provon që asgjë e tij nuk del. Asnjë hash fjalëkalimi, token ose seancë nuk përfshihet kurrë. **PDF-ja origjinale nuk përfshihet** (e ka ngarkuar vetë përdoruesi). Përgjigja ka `Cache-Control: no-store`.

### 5. Afati i ruajtjes

`ANALYTE_DOCUMENT_RETENTION_DAYS` (parazgjedhja `0` = pa afat). Me vlerë pozitive, punëtori arq e ekzekuton çdo orë (minuta 7) `purge_expired`, që fshin çdo dokument të ngarkuar para `tani − afati` me `erase_documents` dhe regjistron `document.expired`. Çdo dokument ka transaksionin e vet: një skedar që nuk fshihet nuk bllokon të tjerët, numërohet te `PurgeResult.failed` dhe provohet sërish ditën tjetër. Koha jepet si parametër, që testet të përdorin një orë të rreme. **Gjatësia e afatit është vendim i autorit**; kodi nuk propozon asnjë vlerë.

### Migrimi

`0005` shton katër kolona te `documents`. **Supozon që `0004` ekziston** (shkruhet nga një punë tjetër); testet e ndërtimit të zinxhirit u ekzekutuan me një stub të përkohshëm `0004`, që nuk është pjesë e dorëzimit. Dokumentet e vjetra shënohen pa pëlqim: u ngarkuan kur nuk kishte pyetje.

## Çfarë mbetet vendim i autorit

Asnjë nga këto nuk zgjidhet nga kodi, dhe asnjë nuk është shkruar si e vërtetë te dokumentet:

- **Kushtet e ofruesit** për ruajtjen dhe përdorimin e të dhënave të dërguara (përfshirë trajnimin) në planin që përdoret **[REFERENCË — plotësohet nga kushtet e ofruesit; mos supozo]**.
- **Baza ligjore** e përpunimit të të dhënave shëndetësore dhe nëse një kuti pëlqimi në ndërfaqe e plotëson **[REFERENCË — plotësohet]**.
- **Marrëveshja e përpunimit të të dhënave** me ofruesin, nëse kërkohet **[REFERENCË — plotësohet]**.
- **Transferimi jashtë BE-së**: ku ndodhet përpunimi i ofruesit **[REFERENCË — plotësohet]**.
- **Miratimi etik** (E13, E14) dhe nëse modeli ndizet fare mbi dokumente reale; alternativa është modeli lokal (E15).
- **Afati i ruajtjes** dhe nëse gjurma e auditimit që mbetet pas fshirjes (document_id, kohë, lloj) është e pranueshme.
- **Teksti i pëlqimit**: formulimi te `frontend/src/components/ModelConsent.tsx` është i shkruar nga sistemi dhe nuk është këshillë ligjore.
- **Çidentifikimi në burim**: porta e kap vetëm atë që kap; nëse dokumentet reale duhet çidentifikuar para ngarkimit (skica etike §5) është vendim i veçantë.

## Kufijtë e portës së çidentifikimit

Porta është heuristikë mbi shqipen e lirë, jo çidentifikim i provuar. **Nuk kap:**

- emra të shkruar me shkronja të vogla, ose emra që rastisin me një fjalë të fjalorit (testi përdor një listë prej 120 emrash e vendesh shembull, jo një listë të plotë);
- pothuajse-identifikues pa trajtë: një profesion i rrallë, një ngjarje e veçantë, një vend i përshkruar me fjalë, një lidhje familjare;
- identifikues të shkruar në mënyra që nuk njihen (shifra të shkruara me fjalë, një numër i ndarë me shkronja);
- çdo gjë që qëndron në fusha që nuk hyjnë te kërkesa (nuk skanohen, sepse nuk dërgohen);
- tekst të përkthyer a të transliteruar (shkronja jo-shqipe), përveç normalizimit të përgjithshëm Unicode.

**Mbi-bllokon (dështim i mbyllur):** një fjali që hapet me një fjalë të zakonshme që mungon te lista (shënohet `name_like`), një vit apo numër me katër shifra (vlerë laboratorike e madhe, e shënuar `long_number`), një term i pashpjeguar me shkronjë të madhe, çdo përmendje e moshës. Pasoja është shablloni, jo humbja e dokumentit.

Dhe porta nuk është kontroll ligjor: një dokument që kalon portën mund të mbajë ende të dhëna personale.

## Alternativat e refuzuara

**Redaktim në vend të refuzimit** (shih më lart). **Të dërgohet vetëm teksti pa citimet e mjekut**: do ta bënte modelin të shkruante pa pohimet që rregullat R5, R6, R8 kërkojnë t'i ruajë, dhe do të ndryshonte atë që mat punimi. **Pëlqim si cilësim i llogarisë**: një pëlqim i dhënë njëherë nuk është pëlqim për dokumentin që po ngarkohet sot. **Fshirje e plotë e gjurmës së auditimit**: do ta zhdukte dëshminë se një dokument u përpunua e u fshi (NFR2).

## Pasojat

- Me modelin e ndezur, pjesa e dokumenteve që shkojnë te ofruesi është më e vogël se më parë: ato pa pëlqim dhe ato që porta i shënon dalin me shabllon. Matjet e modelit te Kapitulli 6 janë mbi dokumente sintetike pa këto filtra, dhe nuk përshkruajnë më atë që sheh një përdorues real.
- Porta shton një rrugë shtesë që duhet mbajtur: fjalori `COMMON_WORDS` dhe lista e kategorive te njoftimi.
- Ngarkimet e reja pyesin një pyetje të re; ndërfaqja nuk e shfaq kur modeli është i fikur.
- Gjurma e auditimit tani ka pesë lloje ngjarjesh të reja (`document.model_consent`, `document.model_use`, `document.expired`, `user.erased`, `user.exported`), të gjitha pa të dhëna personale.

## Çfarë u provua

`tests/unit/test_deidentify.py` (174 teste): citime të pastra shkruar me dorë (jo shabllonet e gjeneruesit) që kalojnë, përfshirë një term të fjalorit me shkronjë të madhe dhe një muaj pa numër; 26 fjali me emra, tituj, data, telefona, email, identifikues, moshë dhe adresa; 120 emra e vende shembull të zakonshëm, të provuar si fjalë e parë dhe në mes të fjalisë; karaktere të padukshme dhe shifra me gjerësi të plotë; gjetjet nuk mbajnë vargun; vlerat e strukturuara jashtë katalogut; testet strukturore (fushat që porta nuk i skanon nuk dalin te kërkesa).

`tests/integration/test_data_protection.py` (22 teste, SQLite): pa pëlqim ofruesi nuk thirret kurrë dhe pacienti merr njoftimin; pëlqimi ruhet me kohë dhe auditohet pa të dhëna personale; një emër te citimi e ndalon dërgimin me pëlqim dhe pacienti sheh citimin origjinal; shërbimi pa model e injoron pëlqimin; fshirja e dokumentit dhe e llogarisë (skedarët largohen nga depoja, çdo tabelë e derivuar zbrazet, përdoruesi tjetër nuk preket, gjurma pa `user_id` dhe pa hash); 401, 404 dhe 403/429; eksporti pa kredenciale dhe pa të dhëna të të tjerëve; afati me orë të rreme, me një skedar që nuk fshihet; puna që përfundon pasi dokumenti u fshi. Tetë prishje të qëllimshme (pa kontroll pëlqimi, pa portë, pa fshirje skedari, pa heqje të `user_id`, pa heqje të hash-it, pa kufizim, pa kontroll të emrave, pa kontroll të afatit 0) rrëzuan secila një test.

`tests/integration/test_data_protection_postgres.py` (6 teste, PostgreSQL 16 nga migrimet, `make test-postgres`): pëlqimi dhe porta, kaskadat e çelësave të huaj, dy fshirje njëkohësisht të së njëjtës llogari dhe të të njëjtit dokument, afati, eksporti.

**Nuk u provua:** asnjë thirrje e vërtetë te ofruesi me këtë rrugë të re; asnjë matje mbi tekst real të mjekut; ndërfaqja u kontrollua me `tsc`, `eslint` dhe `next build` (webpack), jo me një përdorues; fshirja e llogarisë nuk ka ndërfaqe, vetëm API.
