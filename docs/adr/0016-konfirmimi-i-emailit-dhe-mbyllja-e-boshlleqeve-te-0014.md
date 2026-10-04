# 0016 — Konfirmimi i email-it, regjistrimi që nuk zbulon llogari, dhe mbyllja e boshllëqeve të ADR 0014

**Gjendja:** i zbatuar. Dërgimi i vërtetë u provua më 2026-10-05 kundrejt kutisë së provës të Mailtrap (shih «Çfarë u provua»).

## Konteksti

ADR 0014 la tre boshllëqe të shënuara:

1. regjistrimi kthente 409 për një email që ka llogari, dhe kjo zbulonte kush ka llogari, ndërsa hyrja e fshihte;
2. kufizimi i hyrjeve numëronte adresat IPv6 një nga një, kështu që një sulmues me një bllok /64 ndryshonte adresën lirisht dhe i anashkalonte kovat e IP-së dhe të çiftit;
3. nuk kishte «dil kudo», revokim i të gjitha seancave të një përdoruesi.

ADR 0014 e kishte thënë shprehimisht se i pari nuk mbyllet pa konfirmim me email, që sistemi s'e kishte. Autori vendosi ta shtojë (kutia e provës e Mailtrap në zhvillim) dhe t'i mbyllë dhe dy të tjerat.

## Vendimi

**Llogaria nuk hyn pa konfirmim.** `users.email_confirmed_at` është bosh deri sa zotëruesi i kutisë të hapë lidhjen. Hyrja me fjalëkalim të saktë por pa konfirmim kthen 403 me udhëzim; me fjalëkalim të gabuar mbetet 401 i zakonshëm, i njëjtë me atë të email-it të panjohur, dhe 403-ja nuk numërohet si dështim.

**Regjistrimi kthen gjithmonë të njëjtën 202**, me të njëjtin trup, për tri rastet: email i ri, email i konfirmuar dhe email i regjistruar e ende i pakonfirmuar. Ndryshon vetëm mesazhi që merr kutia postare:

| Rasti | Veprimi | Mesazhi |
|---|---|---|
| i ri | krijohet llogaria e pakonfirmuar | lidhja e konfirmimit |
| i regjistruar, i pakonfirmuar | fjalëkalimi zëvendësohet me të rejën; lidhjet e vjetra shfuqizohen | lidhje e re |
| i konfirmuar | asgjë nuk ndryshon | «ky email ka tashmë llogari» |

**Dërgimi bëhet pas përgjigjes**, nga një detyrë në sfond, dhe pas `commit`-it: mesazhi nuk duhet të mbërrijë përpara tokenit që e verifikon, dhe koha e SMTP-së nuk duhet të tregojë cili rast ndodhi. Argon2 shpenzohet në të tria rastet për të njëjtën arsye (`ridërgimi` shpenzon një hash të rremë). Një dështim dërgimi nuk arrin te klienti (përgjigja ka dalë) dhe lë një ngjarje auditimi me vetëm llojin e gabimit.

**Tokeni.** 32 bajt të rastësishëm (`secrets.token_urlsafe`), i ruajtur vetëm si HMAC me çelës (`email_confirmations.token_key`), kështu që një kopje e bazës nuk jep lidhje të përdorshme. Vlen një herë (`UPDATE … WHERE used_at IS NULL`, si te tokenët e rifreskimit), skadon pas 24 orësh, dhe një i ri shfuqizon të papërdorurit e mëparshëm. Një token i panjohur, i përdorur ose i skaduar kthen të njëjtën 400.

**Kufizimi i email-eve që nis shërbimi.** Çdo kërkesë regjistrimi ose ridërgimi numërohet në `registration_attempts` (HMAC i email-it dhe i IP-së, si te `login_failures`): 10 për IP dhe 3 për email në orë. Numërohen të gjitha kërkesat, jo vetëm ato me email të ri, kështu që 429 nuk tregon nëse email-i ka llogari.

**Posta.** Një ndërfaqe `Mailer` me tre realizime: `SmtpMailer` (STARTTLS dhe hyrje me kredenciale nga mjedisi; në zhvillim `sandbox.smtp.mailtrap.io`), `ConsoleMailer` (vetëm zhvillim pa SMTP, shkruan mesazhin te log-u) dhe `OutboxMailer` (testet). Shërbimi nuk nis me `mail_backend=smtp` pa `ANALYTE_SMTP_HOST`: regjistrimi pa email do të dështonte në heshtje. Adresa e pranuesit kontrollohet me një shprehje të rreptë që refuzon çdo hapësirë, kontroll dhe shenjë që mund të ndërtojë një kokë tjetër mesazhi.

**IPv6 sipas prefiksit.** `network_of` e zvogëlon adresën IPv6 te prefiksi /64 (`ipv6_prefix_bits`) para se të hash-ohet; IPv4 dhe IPv4-të-mapuara numërohen të plota. Vlen për të dyja kovat, të hyrjes dhe të regjistrimit.

**Dil kudo.** `POST /auth/logout-all` revokon çdo seancë të hapur të përdoruesit (arsyeja `logout_all`), edhe atë që e kërkoi, dhe shkruan një ngjarje auditimi me numrin e seancave. Ndërfaqja pret përgjigjen e shërbimit përpara se të dalë, dhe e thotë nëse dështoi.

**Migrimi `0003`.** Shton `email_confirmed_at` dhe dy tabelat. Llogaritë që ekzistonin shënohen të konfirmuara në çastin e krijimit të tyre: ato u regjistruan kur shërbimi nuk dërgonte email, dhe të kërkohej konfirmim prej tyre do t'i mbyllte jashtë pa asnjë mënyrë për ta bërë atë.

## Alternativat e refuzuara

**Të mbahet 409.** Zbulon cilat email-e kanë llogari, çka ADR 0014 e quante boshllëk.

**Fjalëkalimi të vendoset te konfirmimi, jo te regjistrimi.** Mbyll plotësisht rrezikun më poshtë (dikush që regjistron email-in e tjetrit), por e ndryshon kontratën e API-së dhe rrjedhën e përdoruesit; refuzuar për thjeshtësi, dhe rreziku i mbetur është shkruar si pasojë.

**Dërgim brenda kërkesës.** Koha e SMTP-së (qindra milisekonda) do të tregonte cili rast ndodhi, dhe një SMTP i ngadalshëm do ta mbante kërkesën.

**Dërgim përmes radhës arq.** API-ja nuk ka lidhje me Redis-in (ADR 0014), dhe testet e saj ekzekutohen pa të; një varësi e re vetëm për këtë do t'i dobësonte provat.

**API e Mailtrap në vend të SMTP-së.** Kërkon një varësi dhe një token API; SMTP-ja është standarde dhe e njëjta kod funksionon me çdo ofrues.

## Pasojat

- **Regjistrimi i email-it të tjetrit mbetet i mundshëm deri në konfirmim.** Llogaria nuk hyn pa lidhjen te kutia e zotëruesit, dhe fjalëkalimin e mban ai që regjistroi i fundit; por nëse zotëruesi hap një lidhje që nuk e kërkoi, ai e konfirmon llogarinë me fjalëkalimin e sulmuesit. Mesazhi e paralajmëron («mos e hapni lidhjen»), por nuk e pengon.
- **Kufiri për email (3 në orë) mund të përdoret nga një tjetër** për ta vonuar regjistrimin e dikujt deri në një orë.
- **Koha nuk është e barabartë tërësisht.** Dega e re shkruan rreshta, e konfirmuara jo; Argon2 (dhjetëra milisekonda) i dominon të dyja, por dallimi nuk u mat.
- **Pa rindërgim automatik.** Nëse procesi ndalet pasi ruajti tokenin dhe para se ta dërgojë mesazhin, përdoruesi kërkon lidhje të re (ndërfaqja e ofron).
- **`ConsoleMailer` shkruan adresën dhe lidhjen te log-u.** Vetëm për zhvillim; prodhimi përdor `smtp`.
- **Tokeni është te adresa e lidhjes.** Faqja `/confirm` e lexon dhe e heq menjëherë nga adresa (`replaceState`) që të mos mbetet te historiku, por nuk vendos kokë `Referrer-Policy`.
- **Nuk ka rivendosje fjalëkalimi.** Një përdorues i pakonfirmuar që e harron fjalëkalimin regjistrohet sërish (zëvendësohet); një i konfirmuar nuk ka rrugë.
- **Mailtrap në mënyrën e provës nuk dërgon te kutia e vërtetë**; është vetëm për zhvillim.

## Çfarë u provua

`tests/integration/test_email_confirmation.py` (22 teste) dhe shtesat te `test_auth_hardening.py`:

- tri rastet e regjistrimit japin të njëjtin status, trup dhe `content-type`; pronari merr mesazhin që i përket rastit; llogaria ekzistuese nuk ndryshon;
- Argon2 thirret një herë në secilin rast;
- llogaria e pakonfirmuar nuk hyn, 403-ja nuk numërohet dështim, lidhja vlen një herë, e skaduara dhe e panjohura japin të njëjtën gabim, një token konfirmon vetëm llogarinë e vet;
- tokeni nuk ruhet i pastër; tabela e provave dhe auditimi nuk mbajnë email apo adresë;
- regjistrimi i dytë para konfirmimit zëvendëson fjalëkalimin dhe shfuqizon lidhjen e vjetër;
- ridërgimi: llogaria e pakonfirmuar merr lidhje të re, të tjerët marrin të njëjtën përgjigje dhe asgjë në kuti;
- kufizimi sipas email-it dhe IP-së, i pavarur nga ekzistenca e llogarisë;
- dështimi i dërgimit nuk e ndryshon përgjigjen dhe lë gjurmë pa adresë;
- `SmtpMailer` kundër një `smtplib` të simuluar: STARTTLS, hyrja, mesazhi; mënyrat `ssl` dhe `none`; shërbimi nuk nis pa konfigurim;
- migrimi: llogaritë e vjetra shënohen të konfirmuara (në SQLite dhe në PostgreSQL 16; po aty u provuan edhe `downgrade` dhe rinisja e `upgrade`); tërë paketa e integrimit kaloi mbi PostgreSQL (`make test-postgres`, 94 teste);
- IPv6: adresat e së njëjtës /64 ndajnë kovat, një /64 tjetër jo; dil kudo revokon çdo seancë të përdoruesit dhe vetëm të tij, edhe tokenët e rifreskimit, dhe numëron vetëm seancat e hapura.

Pesë nga pohimet u provuan edhe duke i prishur: heqja e kontrollit të konfirmimit te hyrja, IPv6 pa prefiks, dil kudo pa filtër përdoruesi, regjistrimi i dytë pa zëvendësim fjalëkalimi, dhe heqja e `commit`-it para dërgimit. Secila prishje rrëzoi të paktën një test. Prishja e fundit zbuloi dhe një gabim të vërtetë gjatë ndërtimit: pa `commit`, detyra në sfond hapte një sesion që prisnte një shkrim të pambaruar (SQLite «database is locked»), dhe në PostgreSQL mesazhi mund të mbërrinte para tokenit.

Prova nga fillimi te fundi, në zhvillim (SQLite, `mail_backend=console`, ndërfaqja në shfletues): regjistrimi tregon mesazhin e njëjtë, lidhja nga log-u konfirmon llogarinë dhe hiqet nga adresa, hyrja funksionon, «Dil kudo» revokon seancën te shërbimi (ngjarje auditimi me numrin 1) dhe kthen te hyrja.

**Dërgimi i vërtetë (2026-10-05).** Me kredencialet e kutisë së provës te `.env` (`sandbox.smtp.mailtrap.io:2525`, STARTTLS), një regjistrim i vërtetë kaloi nga API-ja e ndezur me bazë të përkohshme: përgjigjja ishte 202 e zakonshme, asnjë dështim dërgimi nuk u regjistrua (as te log-u, as te auditimi), autori e gjeti mesazhin te kutia, e hapi lidhjen te ndërfaqja, dhe llogaria u konfirmua (`user.email_confirmed` te auditimi, lidhja e shpenzuar, hyrja me 200). Kjo provon transportin SMTP dhe lidhjen nga fillimi te fundi me një ofrues të vërtetë; nuk provon dërgimin te një kuti e vërtetë (kutia e provës nuk dërgon te adresa të jashtme), as sjelljen e një ofruesi tjetër SMTP.

**Çfarë nuk u provua:** dërgimi te një kuti e vërtetë dhe një ofrues SMTP i prodhimit.
