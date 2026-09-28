# 0013 — Shtresa e shërbimit: baza, radha, siguria

**Gjendja:** i zbatuar (pa bisedë dhe pa pikat e administrimit)

## Konteksti

Specifikimi (§2-§5) e përcakton shërbimin: FastAPI, PostgreSQL, radhë
punësh me arq, JWT, log auditimi, dhe një kontratë API ku çdo tekst i
gjeneruar mban verifikimin e vet. Zbatimi kërkoi vendime që specifikimi
nuk i merr.

## Vendimi

**Tabelat pasqyrojnë domenin fushë për fushë**, me identifikuesit e
domenit dhe një kolonë rendi. Një test kthimi kërkon që konteksti i lexuar
nga baza të jetë i barabartë me origjinalin. Numrat dhjetorë ruhen si
tekst i saktë (`ExactDecimal`): R1 krahason me barazi të saktë, dhe SQLite
— ku ekzekutohen testet — e kthen `Numeric`-un në numër lundrues.

**Terminologjia dhe intervalet referente nuk hyjnë në bazë**, edhe pse §4
i rendit. `resources/` është burimi i vetëm; një kopje në bazë do të
largohej prej tij. Fjalori i secilit dokument ruhet i plotë, që shpjegimi
që pa pacienti të mbetet i gjurmueshëm edhe kur tabela ndryshon.

**Çdo përpjekje gjenerimi është një rresht** me `raw_output` dhe, vetëm te
ai i dorëzuari, `final_output`; shablloni rezervë është rresht më vete.
Tekstet e refuzuara nuk shfaqen kurrë si shpjegim, por gjurma e tyre është
e hapur për pronarin te `/verification`.

**Kalimet shkruhen ndërsa ndodhin**, përmes një dëgjuesi te `StateLog`, që
`/status` të tregojë "ocr_running" gjatë OCR-së. **Gjendja përfundimtare
shkruhet bashkë me rezultatet**, në një transaksion: përndryshe një klient
mund të shihte "delivered" para se shpjegimi të ekzistonte.

**Radha e punëve pas një ndërfaqeje.** `InlineRunner` për testet, `ArqRunner`
për shërbimin. Testet e API-së ekzekutojnë gjithë rrugën brenda një
kërkese, pa Redis; një test i veçantë e provon të njëjtën rrugë mbi
PostgreSQL të vërtetë, me skemën e ndërtuar nga migrimet.

**Siguria dhe privatësia (NFR5):**

- PDF-të ruhen të koduara me Fernet, me emër të rastësishëm; emri i
  skedarit — shpesh emri i pacientit — ruhet i koduar.
- Log-u i auditimit nuk ka funksion të përgjithshëm shkrimi: çdo lloj
  ngjarjeje ka funksionin e vet, dhe asnjëri nuk pranon emër, email, vlerë
  apo tekst. Gabimet e papritura regjistrohen vetëm me llojin e tyre.
- Argon2id për fjalëkalimet. JWT aksesi dhe rifreskimi dallohen nga fusha
  `typ`, dhe njëri refuzohet në vend të tjetrit. Tokeni nuk mban email.
- Hyrja e dështuar ka një përgjigje dhe një kohë të vetme, qoftë email-i i
  panjohur apo fjalëkalimi i gabuar.
- Dokumenti i tjetrit kthehet 404, jo 403.
- Sekreti i JWT-së dhe çelësi i kodimit nuk kanë vlerë parazgjedhëse:
  shërbimi nuk nis pa to.

**Kufizimet shkojnë me tekstin (NFR7).** Përgjigja e shpjegimit mban
`notices` të shkruara nga sistemi: leximi me OCR, vlerat pa interval,
termat e pashpjeguar, kalimi te shablloni. Njoftimi i OCR-së është masa
minimale deri sa të merret vendimi i hapur i ADR 0012.

## Alternativat e refuzuara

**Konteksti si një kolonë JSON.** Më i thjeshtë, por do ta bënte bazën të
pakërkueshme dhe diagramin ER (F6) të pakuptimtë.

**SQLAlchemy asinkron.** Puna e përpunimit është sinkrone gjithsesi —
PyMuPDF, Tesseract, rregullat — dhe shtresa asinkrone do të shtonte
kompleksitet pa fitim.

**Kontroll i formatit gjatë ngarkimit.** Do ta linte degën UPLOADED →
REJECTED të Figurës 6 pa u ushtruar kurrë nga shërbimi i vërtetë.

**Kodimi i gjithë bazës në nivel kolone.** Vlerat laboratorike janë të
dhëna shëndetësore; kodimi i tyre në kolonë do ta bënte bazën të
pakërkueshme. Kodimi i diskut të bazës është detyrë e vendosjes, jo e
kodit, dhe shënohet si kufizim.

## Pasojat

Mbeten pa u ndërtuar: biseda (kërkon modelin gjuhësor; kthen 501),
pikat e administrimit të vlerësimit (eksperimentet ekzekutohen nga
harness-i), kufizimi i shpeshtësisë së hyrjeve, dhe revokimi i tokenëve —
një token rifreskimi i vjedhur mbetet i vlefshëm deri në skadim.

Instalimi i paketës në mënyrë të redaktueshme (`pip install -e`) ishte i
prishur që përpara këtij ndryshimi; u ndreq më vonë me konfigurimin e
paketave namespace te `pyproject.toml`.
