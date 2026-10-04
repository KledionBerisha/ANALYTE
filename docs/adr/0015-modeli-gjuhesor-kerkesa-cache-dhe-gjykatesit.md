# 0015 — Modeli gjuhësor: ofruesi, kërkesa, cache dhe gjykatësit

**Gjendja:** i zbatuar; rezultatet janë te Kapitulli 6 (§6.4, §6.6, §6.7)

## Konteksti

Deri më 2026-10-03 gjeneruesi i vetëm ishte shablloni, dhe eksperimentet E4, E6 dhe E12 ishin të
pamatura, ndërsa E7–E9 ishin vetëm kontrolle kufiri (një shabllon që nuk gabon nuk ka çfarë t'i
heqë verifikimi). Pa model gjuhësor, hipoteza e parë nuk provohej. Kufizimi i vendosur nga autori:
**asnjë shpenzim**; çdo ofrues duhej të ishte falas.

## Vendimi

**Ofruesi dhe modeli.** Mistral, modeli `ministral-14b-2512` (emër me version, jo pseudonim
`-latest`), në planin falas. Kuota e planit u lexua nga faqja e kufizimeve të llogarisë së autorit, jo
nga burime të dyta: modelet `mistral-small`, `mistral-medium` dhe `mistral-large` kishin kufi 0 kërkesa
në këtë plan (përgjigje 429 dhe 403), ndërsa `ministral-14b` jep 30 kërkesa/minutë. Kjo është një
zgjedhje e detyruar nga kuota, jo nga cilësia: është model 14 miliardë parametrash, shqipja nuk është
verifikuar si gjuhë e mbështetur zyrtarisht prej tij, dhe plani falas mund t'i përdorë thirrjet për
trajnim (pa pasojë: dërgohen vetëm dokumente sintetike). Ky model është gjeneruesi i çdo kushti
(E4, E6–E9); rezultatet nuk thonë asgjë për modele të tjera.

**Kërkesa `p1`** (`generation/prompt.py`). Funksioni merr vetëm `GroundingContext` dhe shkeljet e
përpjekjes së mëparshme; nënshkrimi kontrollohet nga test. Tekstet e detyrueshme (SP4–SP7) dhe citimet
e mjekut kopjohen fjalë për fjalë. **Vendim që duhet deklaruar:** kërkesa e drejton modelin te shprehjet e
pozicionit që R3 i njeh ("mbi/nën intervalin referent"), sepse një model që shkruan "i lartë" do ta
kalonte R3 pa u parë. Kushtet B–D maten pra me një kërkesë që i përshtatet kontratës së verifikuesit.
Temperatura 0. **`p1` nuk u ndryshua pasi u pa ndonjë rezultat.** Rregullat u mbetën `r1.3`; asnjë rregull
nuk u ndryshua pas matjes së grupit B ose të E7–E9.

**Cache e përgjigjeve në depo** (`evaluation/cache/llm/`). Çelësi është hash-i i kërkesës së plotë (ofruesi,
modeli, temperatura, kufiri, udhëzimet, konteksti). Një ekzekutim i dytë nuk bën asnjë thirrje dhe jep po
atë tekst; kërkesa që ndryshon edhe me një shkronjë nuk gjen asgjë. Thirrjet e dështuara nuk ruhen kurrë.
Arsyeja: një ofrues falas e tërheq ose e ndryshon një model pa paralajmërim, dhe pa cache një rezultat
nuk rikrijohet. Çmimi: rreth 1 500 skedarë, 18 MB, në git.

**Gabimi i ofruesit nuk është gabim i modelit.** `ProviderUnavailable` (kuotë, rrjet) ndalon ekzekutimin
(`RunAborted`, një `BaseException`), që cikli gjenerim → verifikim → shabllon të mos e numërojë një
ofrues të rënë si dështim të modelit. Një përgjigje e refuzuar ose e cunguar numërohet si përpjekje e
dështuar.

**Klienti i përgjithshëm.** `ChatClient` ka cache-in, kufizimin e shpejtësisë dhe rifreskimin; `GeminiClient`
dhe `OpenAIChatClient` (Mistral, Groq, Cerebras, OpenRouter) plotësojnë vetëm adresën, kokat, trupin dhe
leximin e përgjigjes. Gjykatësi mund të jetë ofrues tjetër (`ANALYTE_LLM_JUDGE_*`).

**Kushti A (E6)** (`evaluation/ungrounded.py`). Modeli sheh tekstin e dokumentit me një kërkesë naive, pa
udhëzime sigurie. Nuk është `Generator` dhe nuk hyn në shërbim: garancia që gjeneruesi nuk sheh dokumentin
mbetet e paprekur. Teksti verifikohet nga të njëjtat rregulla kundrejt kontekstit që nxorri sistemi, dhe
çdo numër jashtë vlerave të matura (përfshirë një datë) numërohet si `ungrounded_number`.

**Gjykatësi i E12.** Një model Claude (`sonnet`) i thirrur si subagjent i Claude Code në 15 batch-e me 20
elemente (`evaluation/judge_batches.py`), si gjykatësi kryesor; Haiku si kontroll i dytë. Batch-et nuk
përmbajnë etiketat; çelësi qëndron jashtë dosjes që lexojnë gjykatësit, dhe bashkohet vetëm te `ingest`. Të
gjitha përgjigjet ruhen në depo. Të njëjtat 192 mostra të E10 dhe 105 rreshta të B si për rregullat dhe
klasifikuesin.

**Audit i pavarur i E8** (`evaluation/audit_batches.py`). Metrika e PK5 numëron shkeljet me të njëjtat
rregulla që e bllokojnë tekstin; "0 shkelje arrijnë te përdoruesi" do të thotë "asnjë që rregullat e
shohin". Gjykatësi Claude lexon një mostër të tekstit të dorëzuar dhe liston çdo problem, përfshirë
`other_unsupported` (pohim që asnjë rregull nuk e kontrollon).

## Alternativat e refuzuara

- **Gemini, shtresa falas:** `gemini-3.8-flash` ka 20 kërkesa në ditë (e matur); modelet më të vogla kishin
  kufij për minutë, por kuotë ditore të panjohur, dhe studimi duhet një gjenerues i vetëm.
- **OpenAI, Anthropic API:** pa shtresë falas (parapagim).
- **Cerebras:** kërkonte pagesë te llogaria e autorit. **Groq:** i ngadaltë (kuota ditore e tokenëve).
  **OpenRouter:** 50 kërkesa/ditë pa blerje, dhe modele që rrotullohen.
- **Model lokal:** nuk u provua; pajisja e autorit nuk u deklarua.
- **Gjykatës me API:** asnjë ofrues falas nuk e mbulonte E12 mirë; modeli i vogël i Mistral si gjykatës do ta
  kishte bërë gjykatësin më të dobët se gjeneruesi dhe nga e njëjta kompani.

## Pasojat, përfshirë të padëshiruarat

- **Gjykatësi Claude nuk është i pavarur nga sistemi:** është asistenti që ndihmoi ta ndërtojë. Temperatura
  dhe mostrimi nuk fiksohen, prandaj një ekzekutim i ri nuk garantohet të japë të njëjtat etiketa; vlerësimi
  rillogaritet nga `answers_*.jsonl`.
- **Qasja te skedarët nuk u audituan teknikisht.** Etiketat vërtetë ishin në një skedar jashtë dosjes së
  batch-eve; mbrohej nga udhëzimi. Transkriptet e subagjentëve ishin bosh. Provë indirekte: çdo subagjent
  Sonnet përdori 5–7 thirrje mjetesh (lexim i udhëzimeve, i batch-it në pjesë, shkrim i përgjigjeve), pa
  hapësirë për kërkim; Haiku përdori 5 deri 47 (tetë nga 15 mbi 25) dhe pati saktësi shumë më të ulët.
- **Perfeksioni i Sonnet (macro F1 1.000) nuk është ceiling i detyrës:** Haiku mori 0.625 dhe 0.514, dhe
  pajtohet me Sonnet në 53% të rasteve. Aftësia e gjykatësit e përcakton rezultatin.
- **E gjithë vlefshmëria e jashtme mbetet e pamatur** (korpus sintetik, asnjë dokument real, asnjë përdorues).
