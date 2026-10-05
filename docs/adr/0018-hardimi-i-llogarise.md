# 0018 — Hardimi i llogarisë: rivendosja e fjalëkalimit, hapi i dytë (TOTP), rindërgimi i mesazheve dhe kokat e sigurisë

**Gjendja:** i zbatuar. I provuar me teste mbi SQLite dhe mbi PostgreSQL 16 (shih «Çfarë u provua» dhe «Çfarë nuk u provua»).

## Konteksti

ADR 0016 (te «Pasojat») la tre boshllëqe të shënuara në sistemin e llogarive, dhe një i katërt shtohet këtu:

1. **nuk kishte rivendosje fjalëkalimi**: një përdorues i konfirmuar që e harron fjalëkalimin nuk kishte asnjë rrugë;
2. **nuk kishte rindërgim automatik**: lidhja ruhej para se mesazhi të nisej, dhe nëse transporti dështonte ose procesi ndalej midis të dyjave, tokeni ekzistonte por mesazhi nuk mbërrinte kurrë;
3. **nuk kishte kokë `Referrer-Policy`**: lidhjet `/confirm?token=…` mbajnë një token te adresa, dhe e vetmja mbrojtje ishte që faqja e heq vetë nga adresa;
4. **nuk kishte hap të dytë hyrjeje** (nuk ishte i shënuar te ADR 0016, por i përket të njëjtit sistem): një fjalëkalim i vjedhur mjaftonte për të hapur llogarinë dhe, me të, dokumentet shëndetësore të përdoruesit.

Parimet e ADR 0014 dhe 0016 mbeten të detyrueshme për çdo pikë të re: **asnjë përgjigje nuk tregon nëse një email ka llogari**, Argon2 shpenzohet në çdo degë, tokenët ruhen vetëm si HMAC, çdo shpenzim është një UPDATE i kushtëzuar (vlen një herë), dhe kufizimi vjen para se të kontrollohet ndonjë sekret.

## Vendimi

### 1. Rivendosja e fjalëkalimit

**`POST /auth/forgot-password`** kthen gjithmonë të njëjtën 202 me të njëjtin trup, për email të konfirmuar, të pakonfirmuar dhe të panjohur. Mesazhi dërgohet pas përgjigjes, nga detyra në sfond, si te regjistrimi; Argon2 shpenzohet (hash i rremë) në çdo degë, kështu që koha nuk tregon cila ndodhi.

| Rasti | Veprimi | Mesazhi |
|---|---|---|
| i konfirmuar | lëshohet një token rivendosjeje; të papërdorurit e mëparshëm shfuqizohen | lidhja e rivendosjes |
| i pakonfirmuar | lëshohet një token konfirmimi (si te «ridërgo») | lidhja e **konfirmimit**, jo e rivendosjes |
| i panjohur | asgjë | asgjë |

**Rivendosja nuk është rrugë anash konfirmimit.** Një llogari e pakonfirmuar nuk merr kurrë lidhje rivendosjeje. Edhe nëse një token rivendosjeje ekzistonte për të (mbrojtje në thellësi, e provuar me një token të vendosur me dorë), `reset-password` e refuzon me të njëjtën 400 dhe nuk e ndryshon as fjalëkalimin, as `email_confirmed_at`. Një rivendosje e suksesshme nuk e prek `email_confirmed_at` të një llogarie të konfirmuar.

**`POST /auth/reset-password`** (token + fjalëkalim i ri). Tokeni është 32 bajt të rastësishëm, i ruajtur vetëm si HMAC me etiketë të veten (`password-reset`, e ndryshme nga `email-confirm`), vlen një herë (UPDATE i kushtëzuar mbi `used_at`) dhe skadon pas 60 minutash (`ANALYTE_RESET_TOKEN_MINUTES`; më shkurt se konfirmimi, sepse një lidhje e tillë hap llogarinë, jo vetëm e aktivizon). Rregulla e gjatësisë së fjalëkalimit është ajo e regjistrimit; një fjalëkalim shumë i shkurtër kthen 422 **pa shpenzuar lidhjen**. Fjalëkalimi i ri hash-ohet para se tokeni të kontrollohet, kështu që koha nuk tregon nëse tokeni ishte i vlefshëm. Një token i panjohur, i përdorur ose i skaduar kthen të njëjtën 400.

Pas suksesit: fjalëkalimi i ri vendoset, **çdo seancë e përdoruesit revokohet** (arsyeja `password_reset`; tokenët e aksesit dhe të rifreskimit pushojnë menjëherë), lidhjet e tjera të papërdorura të rivendosjes fshihen dhe shkruhet një ngjarje auditimi (`auth.password_reset`, pa asnjë të dhënë). **Hapi i dytë, nëse ka, mbetet aktiv**: dikush që ka vetëm kutinë postare nuk e kalon.

**Kufizimi.** Kërkesat `forgot-password` numërohen te `registration_attempts` me etiketa të veta (`reset-email`, `reset-ip`), pra kova të ndara nga ato të regjistrimit (një kërkesë rivendosjeje nuk e mbush kufirin e regjistrimit, dhe anasjelltas) me të njëjtat kufij (10 për IP, 3 për email në orë). Numërohen të gjitha kërkesat, jo vetëm ato me email me llogari, që 429 të mos tregojë nëse email-i ka llogari. Dorëzimet e `reset-password` kufizohen sipas IP-së (`ANALYTE_RESET_SUBMIT_MAX_PER_IP`, parazgjedhja 20 në orë, të suksesshme ose jo), **para** se tokeni të kontrollohet: një IP e bllokuar refuzohet edhe me tokenin e saktë.

### 2. Hapi i dytë i hyrjes (TOTP)

**Algoritmi.** TOTP sipas RFC 6238 mbi HOTP të RFC 4226: SHA-1, hap 30 sekondash, gjashtë shifra, dritare ±1 hap. Realizohet me bibliotekën standarde (`hmac`, `hashlib`, `struct`, `base64`; `analyte/twofactor.py`), pa varësi të re. SHA-1 zgjidhet sepse e pranojnë të gjitha aplikacionet e zakonshme të vërtetimit; në HMAC ai nuk ka dobësinë e përplasjeve që e ka bërë të papërshtatshëm gjetkë. Vektorët e shtojcës B të RFC 6238 (SHA-1) dhe ato të shtojcës D të RFC 4226 ekzekutohen te testet.

**Regjistrimi** (përdorues i hyrë):

  - `POST /auth/2fa/enroll` nxjerr një sekret të ri (160 bit) dhe e kthen **një herë**, bashkë me adresën `otpauth://`. Sekreti ruhet **i koduar** (`users.totp_secret_encrypted`) me të njëjtin çelës Fernet që kodon skedarët (`EncryptedStore.encrypt_text`). Nuk ka çelës të dytë: një çelës i ri do të donte një rrugë të re për t'u ruajtur e rrotulluar, dhe ky çelës ruan tashmë të dhëna më të ndjeshme se sekreti. Kostoja është te «Pasojat». Thirrja e dytë para konfirmimit e zëvendëson sekretin; pasi hapi aktivizohet kthen 409 dhe sekreti nuk lexohet më nga asnjë pikë.
  - `POST /auth/2fa/confirm` aktivizon me kodin e parë të vlefshëm dhe kthen **8 kode rimëkëmbjes**, një herë. Kodi që konfirmoi regjistrimin shënohet i përdorur: nuk hap hyrjen e parë.
  - `POST /auth/2fa/disable` kërkon **fjalëkalimin e tanishëm dhe një kod** (aplikacioni ose rimëkëmbjeje): një token aksesi i vjedhur vetëm nuk e çaktivizon. Fjalëkalimi kontrollohet i pari, që një fjalëkalim i gabuar të mos shpenzojë një kod rimëkëmbjeje të saktë.
  - `GET /auth/2fa` kthen vetëm `{enabled, recovery_codes_remaining}`.
  - Aktivizimi **revokon seancat e tjera** të hapura (jo atë që e aktivizoi): ato u hapën vetëm me fjalëkalim dhe nuk duhet të mbeten të vlefshme pa hapin e dytë. Gabimet e këtyre pikave janë 400, jo 401: klienti e merr 401-ën si seancë të humbur dhe provon rifreskim.

**Kodet e rimëkëmbjes**: 10 shenja nga një alfabet 32-shenjësh (50 bit), të shfaqura si `xxxxx-xxxxx`. Ruhen vetëm si HMAC me çelës, të lidhur me përdoruesin (`recovery_codes.code_key`), dhe vlejnë një herë (UPDATE i kushtëzuar). HMAC i thjeshtë, jo Argon2, sepse kodi ka 50 bit rastësie (një fjalëkalim njerëzor nuk ka) dhe sepse kontrollohet vetëm pas kufizimit.

**Hyrja.** Me hap të dytë aktiv, fjalëkalimi i saktë nuk kthen tokenë por `{"mfa_required": true, "challenge": …}`: një token i nënshkruar, **jo token aksesi** (`typ` tjetër, pa seancë), me jetë 5 minuta. Sfida mban vetëm `sub`, një gjurmë lidhëse `cv` dhe kohët: asnjë email. Gjurma `cv` është HMAC i hash-it të fjalëkalimit dhe i kohës së aktivizimit të hapit të dytë; prandaj një sfidë **pushon** nëse fjalëkalimi ndryshon (çdo rivendosje ka kripë të re) ose hapi i dytë çaktivizohet, edhe nëse riaktivizohet. `POST /auth/login/verify` merr sfidën dhe një kod dhe hap seancën. Çdo gabim (sfidë e pavlefshme, e skaduar, e vjetruar ose kod i gabuar) kthen të njëjtën 401.

**Asgjë nuk tregohet para fjalëkalimit të saktë.** Email-i i panjohur dhe fjalëkalimi i gabuar japin të njëjtën 401 me trup të njëjtë, me ose pa hap të dytë; sfida del vetëm pasi fjalëkalimi është i saktë dhe email-i i konfirmuar (403-ja e llogarisë së pakonfirmuar mbetet para sfidës).

**Rilojimi.** Një kod TOTP pranohet vetëm për një hap kohe **më të madh** se i fundit i pranuari (`users.totp_last_step`), i shkruar me UPDATE të kushtëzuar: i njëjti kod nuk përdoret dy herë, as nën kërkesa paralele. Kjo ka një kosto të qëllimshme: një telefon me orë që vonon mund të refuzohet derisa të kalojë hapi i pranuar.

**Kufizimi i kodeve të gabuara**, para se kodi të kontrollohet. Numërohen te `login_failures` me etiketa të veta (`mfa-user`, `mfa-ip`), pra nuk e mbushin kovën e fjalëkalimit dhe anasjelltas: për çiftin (përdorues, IP) 5, për një IP 20, për një përdorues nga çdo IP 10, brenda dritares së hyrjes (15 minuta). Kufiri për përdorues është më i ulët se ai i fjalëkalimit, sepse hapësira e një kodi është vetëm një milion. Një kod i saktë pas kufirit refuzohet 429. Kodi i saktë pastron numëruesin e çiftit. Të njëjtat kova vlejnë për konfirmimin e regjistrimit dhe për çaktivizimin.

### 3. Rishikimi dhe rindërgimi i mesazheve

**Regjistri i dërgimit** (`mail_deliveries`): një rresht për çdo mesazh me lidhje (konfirmim ose rivendosje) me llojin, identifikuesin e tokenit që mbart (pa çelës të huaj: tregon një nga dy tabelat), origjinën (`request` ose `sweep`), gjendjen (`pending`, `sent`, `superseded`, `expired`, `skipped`), numrin e provave dhe **vetëm llojin** e gabimit të fundit. Nuk mban adresë, lidhje apo tekst; adresa nxirret nga `users` kur duhet.

**Rishikimi në sfond.** Dërgimi provohet deri në 3 herë (`ANALYTE_MAIL_SEND_ATTEMPTS`) me pritje që dyfishohet (2 s, 4 s: `ANALYTE_MAIL_RETRY_BACKOFF_SECONDS`). Pas dështimit përfundimtar rreshti mbetet `pending` dhe shkruhet **një** ngjarje auditimi `mail.failed` me vetëm llojin e gabimit. Njoftimet pa token («ky email ka tashmë llogari») rishikohen njëlloj por nuk kanë regjistër: s'ka çfarë të rindërgohet.

**Kalimi periodik** (`outbox.resend_unsent`, thirret nga punëtori arq çdo 10 minuta). **Tokeni i vjetër nuk rikthehet**: ruhet vetëm si HMAC, prandaj lidhja e plotë nuk mund të ndërtohet sërish; të ruhej e pastër (ose e koduar) do ta prishte vetinë që një kopje e bazës nuk jep lidhje të përdorshme, dhe ADR 0016 e ka vendosur këtë me qëllim. Prandaj kalimi **lëshon një token të ri**, që shfuqizon të vjetrin të papërdorur, dërgon lidhjen e re dhe e shënon rreshtin e vjetër `superseded`. Rregullat:

  - merr vetëm mesazhet `pending` që kanë pritur `ANALYTE_MAIL_RESEND_AFTER_MINUTES` (10), që mos të ndërhyjë te rishikimi që është ende në punë;
  - vetëm nëse tokeni është i papërdorur dhe i pa skaduar, dhe llogaria ende e do (konfirmimi: ende e pakonfirmuar; rivendosja: e konfirmuar). Përndryshe rreshti shënohet `expired` dhe asgjë nuk dërgohet;
  - **jo më shumë se 2 rilëshime automatike për përdorues në 24 orë** (`ANALYTE_MAIL_AUTO_REISSUE_PER_DAY`); tejkalimi shënohet `skipped` dhe nuk provohet më, që kalimi të mos përdoret për të mbushur një kuti postare. Përdoruesi mbetet me të drejtën të kërkojë vetë (e kufizuar nga kufizimi i zakonshëm);
  - marrja e rreshtit është një UPDATE i kushtëzuar: dy kalime paralele nuk rilëshojnë dy herë të njëjtin mesazh;
  - `limit` mesazhe për kalim (50); regjistrimet më të vjetra se 30 ditë fshihen.

Ngjarjet e auditimit mbajnë vetëm llojin e dështimit (`mail.failed`) dhe llojin e mesazhit të rilëshuar (`mail.reissued`).

### 4. Kokat bazë të sigurisë

**API:** një middleware ASGI i vogël (`api/headers.py`, i regjistruar te `main.py`) vendos në çdo përgjigje `Referrer-Policy: no-referrer`, `X-Content-Type-Options: nosniff` dhe `X-Frame-Options: DENY`, dhe `Cache-Control: no-store` për `/auth/*`. Është ASGI i pastër, jo `BaseHTTPMiddleware`: nuk e lexon trupin, prandaj nuk ndërhyn te figurat e faqeve dhe te detyrat në sfond. Përgjigjet 500 i nxjerr middleware-i më i jashtëm i Starlette-it, përtej atij tonit; prandaj trajtuesi i gabimeve të papritura i shton vetë të njëjtat koka.

**Ndërfaqja:** `next.config.ts` vendos të tri kokat e para për çdo faqe (`headers()`). `no-referrer` ka rëndësi të veçantë për `/confirm` dhe `/reset-password`, ku një token ndodhet te adresa: faqja e heq tokenin nga adresa pas leximit (`replaceState`), por kjo është shtresa e dytë.

### 5. Migrimi `0004`

Shton `users.totp_secret_encrypted`, `totp_enabled_at`, `totp_last_step` (të gjitha bosh: llogaritë ekzistuese mbeten pa hap të dytë) dhe tre tabelat `password_resets`, `recovery_codes`, `mail_deliveries`. Testi i migrimeve provon `upgrade`, `downgrade` dhe barazinë me modelet.

### Ndërfaqja

`/forgot-password`, `/reset-password` (merr tokenin nga adresa dhe e heq menjëherë; tokeni nuk shpenzohet kur faqja hapet por kur dërgohet formulari), lidhja «Harrova fjalëkalimin» te hyrja, hapi i dytë te faqja e hyrjes (fusha e kodit dhe «përdor një kod rimëkëmbjeje»), dhe `/security` (regjistrim, shfaqje një herë e kodeve të rimëkëmbjes, çaktivizim). **Nuk shtohet kod QR**: s'ka varësi të re; ndërfaqja shfaq çelësin dhe adresën `otpauth://` si tekst, që aplikacionet e pranojnë me shkrim me dorë.

## Alternativat e refuzuara

**Ruajtja e lidhjes (e koduar) për ta rindërguar të njëjtën.** Do ta kishte bërë rindërgimin të thjeshtë, por një kopje e bazës plus çelësi i ruajtjes do të jepte lidhje të përdorshme. Refuzuar; në vend të saj, një token i ri me kufi ditor.

**Rivendosja që konfirmon email-in** («pasi e hapi lidhjen nga kutia, kutia është e tij»). Është e vërtetë, por e bën rivendosjen rrugë anash konfirmimit dhe e hap derën që ADR 0016 e mbylli: dikush që regjistron email-in e tjetrit më pas do ta konfirmonte me një rivendosje. Refuzuar nga kërkesa.

**Rivendosja që mbyll vetëm seancat e vjetra, jo të gjitha.** Nuk ka mënyrë të besueshme për të ditur cilat janë «të vjetrat»: dikush që e ka fjalëkalimin e vjetër mund të ketë hapur seancë para ose pas. Revokohen të gjitha.

**Biblioteka TOTP (`pyotp`).** Algoritmi është pak dhjetëra rreshta, specifikimi ka vektorë provash, dhe një varësi e re për siguri kërkon të besohet edhe ajo. Refuzuar.

**SMS si hap i dytë.** Kërkon një ofrues, numra telefoni (të dhënë personale) dhe është më i dobët (SIM swap). Refuzuar.

**WebAuthn.** Më i fortë se TOTP, por kërkon HTTPS, një origjinë të qëndrueshme dhe më shumë kod e ndërfaqe nga ç'mban ky punim. Nuk zbatohet.

**Çelës i veçantë për sekretet TOTP.** Do të ndante rrezikun, por shton një sekret tjetër për t'u gjeneruar, ruajtur e rrotulluar, pa e ndryshuar rrezikun real (të dy çelësat ndodhen te e njëjta `.env`).

**Sfidë njëpërdorimshe.** Do të kërkonte ruajtje shtesë; sfida jeton 5 minuta dhe çdo përdorim i saj kërkon kod të vlefshëm e të pa përdorur, kështu që ripërdorimi i saj nuk jep asgjë pa kodin.

## Pasojat

- **Çelësi i ruajtjes mbron edhe sekretet TOTP.** Kush e merr `ANALYTE_STORAGE_KEY` dhe bazën, lexon dhe sekretet TOTP, jo vetëm emrat e skedarëve. Dhe anasjelltas: **ndërrimi i çelësit pa rikodim e prish hyrjen për çdo përdorues me hap të dytë** (kodi s'mund të kontrollohet; dështimi duket te log-u si gabim, jo si kod i gabuar).
- **Humbja e aplikacionit dhe e kodeve të rimëkëmbjes e mbyll llogarinë.** Nuk ka rrugë rimëkëmbjeje tjetër (as administrator, as email): një rrugë e tillë do të ishte pikërisht ajo që sulmuesi do të shfrytëzonte. Rivendosja e fjalëkalimit nuk e heq hapin e dytë.
- **Nuk ka rigjenerim kodesh rimëkëmbjeje.** Kur mbeten pak, përdoruesi çaktivizon e aktivizon sërish (kërkon një kod të vlefshëm). Ndërfaqja e paralajmëron.
- **Aktivizimi i hapit të dytë mbyll seancat e tjera të përdoruesit** (pajisjet e tjera duhet të hyjnë sërish).
- **Kufizimet janë te baza e të dhënave**, jo te kujtesa e procesit: ndahen midis proceseve dhe rinisjeve, por çdo përpjekje shkruan një rresht, dhe përpjekjet e refuzuara nuk shkruajnë asgjë. Një sulmues që di fjalëkalimin e dikujt mund t'ia mbushë kovën e kodeve (10 në 15 minuta) dhe ta mbyllë një kohë nga hapi i dytë, njëlloj si te kova e email-it të hyrjes (ADR 0014).
- **Koha nuk është e barabartë tërësisht.** Argon2 shpenzohet në çdo degë të `forgot-password`, por dega me llogari shkruan rreshta dhe e tjera jo; Argon2 dominon, por dallimi **nuk u mat**. Të njëjtën kufizim e ka dhe `reset-password` (hash i të njëjtit fjalëkalim para kontrollit të tokenit).
- **Mesazhi i rivendosjes mund të mbërrijë dikujt që nuk e kërkoi** (kushdo mund të shkruajë email-in e tjetrit). Teksti e thotë, fjalëkalimi nuk ndryshon pa e hapur lidhjen, dhe kufizimi (3 në orë për email) e kufizon bezdinë.
- **Lidhja e rivendosjes është te adresa e faqes.** Mbrojtjet: faqja e heq nga adresa, `no-referrer`, vlen një herë, 60 minuta. Nuk mbrohet nga një zgjerim i shfletuesit që lexon adresën para se faqja ta heqë.
- **Rilëshimi automatik dërgon një email që përdoruesi nuk e kërkoi në atë çast** (por e kishte kërkuar më parë, dhe mesazhi i parë nuk mbërriti). Kufiri është 2 në ditë për përdorues.
- **Rindërgimi varet nga punëtori arq.** Pa të (ose pa Redis), mesazhet e humbura mbeten `pending`; përdoruesi vazhdon të kërkojë vetë. API-ja nuk e ekzekuton kalimin.
- **Rishikimi në sfond bllokon një fije** gjatë pritjes (6 sekonda në rastin më të keq me parazgjedhjet). Është fije e grupit të detyrave të FastAPI-t, jo cikli kryesor, por një SMTP që dështon gjatë mund t'i mbushë fijet.
- **Kokat:** nuk vendoset `Content-Security-Policy` as `Strict-Transport-Security` (HSTS i përket ndërprerësit TLS, ku ka domenin dhe certifikatën; CSP kërkon një provë të veçantë me Next.js dhe nuk u mat). `X-Frame-Options` është kokë e vjetër; shfletuesit e rinj lexojnë `frame-ancestors` te CSP.
- **SHA-1 te TOTP** është zgjedhja e standardit dhe e aplikacioneve; nuk ndryshohet pa humbur përputhshmërinë.
- **Kodet e rimëkëmbjes ruhen si HMAC pa Argon2**: me 50 bit dhe kufizim; një kopje e bazës pa `ANALYTE_JWT_SECRET` nuk lejon të provohen kodet jashtë linje.

## Çfarë u provua

Teste të reja: `tests/unit/test_twofactor.py` (20), `tests/integration/test_password_reset.py` (24), `test_two_factor.py` (34), `test_mail_resend.py` (22), `test_security_headers.py` (6), një test migrimi te `test_migrations.py`, dhe `test_postgres_accounts.py` (4, vetëm kur `ANALYTE_TEST_DATABASE_URL` është vënë).

- **TOTP:** vektorët e RFC 6238 (SHA-1, 8 shifra, gjashtë kohë) dhe të RFC 4226 (HOTP, 5 numërues); dritarja ±1 pranon tre hapa dhe refuzon ata përtej; kodet me hapësira; formati dhe normalizimi i kodeve të rimëkëmbjes.
- **Rivendosja:** rruga e zakonshme; një përdorim; një kërkesë e re shfuqizon të mëparshmen; skadimi; i panjohur, i përdorur dhe i skaduar japin të njëjtën gabim; fjalëkalimi i shkurtër nuk shpenzon lidhjen; tokeni nuk ruhet i pastër dhe etiketa e HMAC-ut ndryshon nga ajo e konfirmimit; një token konfirmimi nuk rivendos fjalëkalim; tri llojet e email-it japin të njëjtin status, trup dhe `content-type`, dhe Argon2 thirret një herë në secilën degë; revokimi i çdo seance (aksesi dhe rifreskimi, vetëm të përdoruesit); llogaria e pakonfirmuar merr lidhje konfirmimi, jo rivendosjeje; një token rivendosjeje i vendosur me dorë për një llogari të pakonfirmuar nuk e ndryshon, nuk e konfirmon, dhe hyrja mbetet 403; kufizimi sipas email-it, IP-së dhe dorëzimeve, i pavarur nga ekzistenca e llogarisë dhe nga kufiri i regjistrimit; auditimi pa email.
- **Hapi i dytë:** regjistrimi, konfirmimi, 409 për regjistrim të dytë; sekreti i koduar në bazë dhe kodet vetëm si HMAC; hyrja jep sfidë, jo tokenë; 401 e njëjtë para fjalëkalimit; rilojimi refuzohet (edhe kodi që konfirmoi regjistrimin); kodet e rimëkëmbjes vlejnë një herë, nuk vlejnë te llogaria tjetër; kufizimi sipas çiftit, përdoruesit dhe IP-së, para kontrollit të kodit (kodi i saktë pas kufirit merr 429), pa përzierje me kovat e fjalëkalimit, dhe pastrimi pas suksesit; sfida pushon pas rivendosjes së fjalëkalimit, çaktivizimit, çaktivizimit e riaktivizimit, dhe skadimit; sfida nuk është token aksesi dhe anasjelltas; sfida e nënshkruar me çelës tjetër refuzohet; çaktivizimi kërkon fjalëkalimin dhe kodin dhe kufizohet; «dil kudo» dhe rivendosja mbeten të sakta; auditimi nuk mban email as kod.
- **Rindërgimi:** numri i provave dhe pritja që dyfishohet; një gabim kalimtar rishikohet dhe mesazhi mbërrin; regjistri nuk mban adresë; kalimi lëshon token të ri dhe lidhja e vjetër pushon; nuk vepron para kohës së pritjes; nuk prek mesazhe të dërguara, të përdorura, të skaduara, të zëvendësuara nga përdoruesi, apo të një llogarie tashmë të konfirmuar; kufiri ditor për përdorues (jo global); `limit` për kalim; kalimi për rivendosje; regjistrimet e vjetra fshihen; planifikimi i punëtorit.
- **Kokat:** të tri te çdo lloj përgjigjeje (200, 404, 401, 422, përgjigjet e CORS, 500 me përjashtim të papritur), `no-store` vetëm te `/auth/*` (jo te `/authors`), dhe kokat e vetë endpoint-it (`Retry-After`) mbijetojnë.
- **PostgreSQL 16:** migrimi `0004` (`upgrade`, `downgrade`, barazia me modelet) dhe provat e reja mbi bazë të ndërtuar nga migrimet; një token rivendosjeje, një kod TOTP dhe një kod rimëkëmbjes shpenzohen nga **saktësisht një** nga tetë kërkesa paralele; kalimi periodik mbi `timestamptz`.
- **Ndërfaqja:** `npm run lint` pa gabime; `next build --webpack` (TypeScript dhe faqet e reja kompilohen: `/forgot-password`, `/reset-password`, `/security`); `next start` kthen të tri kokat në `/login`, `/reset-password` dhe te një 404; në shfletues, mbi një API të ndezur me bazë të përkohshme: «Harrova fjalëkalimin» te hyrja, kërkesa, lidhja nga email-i hapet dhe tokeni hiqet nga adresa, fjalëkalimi ndryshon; regjistrimi i hapit të dytë me kod të llogaritur nga sekreti i shfaqur, kodet e rimëkëmbjes shfaqen, hyrja kërkon kodin, një kod i përdorur refuzohet me mesazh, kodi i radhës hap seancën.
- **Prova e prishjes.** Njëmbëdhjetë prishje të njëpasnjëshme të kodit u ekzekutuan kundër testeve përkatëse, dhe secila rrëzoi të paktën një test: heqja e kushtit të rilojimit, e kufizimit para kodit, e lidhjes së sfidës me fjalëkalimin, e kushtit `used_at` të kodit të rimëkëmbjes, e kontrollit të konfirmimit te rivendosja, e revokimit të seancave, e hash-it para kontrollit të tokenit, e kufizimit të dorëzimeve, e kufirit ditor të kalimit, e kontrollit të tokenit të skaduar te kalimi, dhe e `no-store`.

## Çfarë nuk u provua

- **Dërgimi i vërtetë me rishikim:** provat përdorin transporte të simuluara; rishikimi dhe kalimi nuk u ekzekutuan kundër një SMTP të vërtetë (Mailtrap) dhe vonesat e vërteta të rrjetit nuk u matën.
- **Punëtori arq me Redis:** u provua që kalimi është i regjistruar si punë me orar (çdo 10 minuta) dhe që funksioni i punës nuk bën asgjë pa postë; **nuk** u nis punëtori kundër një Redis të vërtetë, kështu që nuk është parë vetë ekzekutimi i planifikuar.
- **Aplikacione të vërteta vërtetimi:** kodet u kontrolluan kundër vektorëve të RFC-ve dhe kundër një llogaritjeje të pavarur në JavaScript (WebCrypto) te shfletuesi, jo kundër Google Authenticator apo aplikacioneve të tjera.
- **Koha e barabartë** e degëve të `forgot-password` dhe `reset-password`: provohet vetëm që Argon2 shpenzohet në secilën; nuk u matën kohët.
- **Kokat e ndërfaqes pas një proxy** ose në një hostim të vërtetë: u parë vetëm me `next start` lokal.
- **Pa CSP, pa HSTS, pa QR, pa WebAuthn, pa rigjenerim kodesh rimëkëmbjeje, pa rrugë rimëkëmbjeje të një autentikuesi të humbur përtej kodeve, pa SMS, pa pajisje «të besuara».**
