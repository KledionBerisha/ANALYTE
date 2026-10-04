# 0017 — Modeli gjuhësor te aplikacioni i uebit

**Gjendja:** i zbatuar; i fikur si parazgjedhje. Provuar me një ofrues të simuluar (13 teste) dhe një herë me Mistral të vërtetë mbi një dokument sintetik.

## Konteksti

Deri më 2026-10-05 aplikacioni i uebit gjeneronte gjithmonë me shabllonin determinist: `build_services` ndërtonte `TemplateGenerator`, dhe modeli gjuhësor (ADR 0015) përdorej vetëm nga harness-i i vlerësimit, mbi dokumente sintetike. Dokumentacioni thoshte të kundërtën («shërbimi mund ta përdorë modelin»); u korrigjua kur u pa se `ANALYTE_LLM_PROVIDER` nuk lexohej fare nga shërbimi.

Autori vendosi ta lidhë modelin me aplikacionin. Kjo e ndryshon një gjë që nuk ndryshon asnjë metrikë: te eksperimentet konteksti që i dërgohet ofruesit vjen nga dokumente të shpikura, ndërsa te aplikacioni mund të vijë nga pacientë të vërtetë.

## Vendimi

**Zgjedhja është e shprehur dhe e ndarë nga ofruesi.** `ANALYTE_SERVICE_GENERATOR` merr `template` (parazgjedhja) ose `model`. `ANALYTE_LLM_PROVIDER`, `_MODEL` dhe `_API_KEY` duhet të jenë te `.env` edhe për eksperimentet; po të ndizte modelin vetëm ofruesi, kushdo që ekzekuton një eksperiment do t'u dërgonte një ofruesi të jashtëm ngarkimet e vërteta pa e vendosur këtë. Me `model` dhe konfigurim të paplotë (pa ofrues, model ose çelës) shërbimi nuk nis (`ProviderError`), jo në mes të një dokumenti.

**Pa cache në disk.** Harness-i i ruan përgjigjet e modelit te depoja (`evaluation/cache/llm`) që eksperimentet të përsëriten. Aplikacioni e ndërton klientin pa `cache_dir`: kërkesat dhe përgjigjet e pacientëve të vërtetë nuk shkruhen në disk (përveç tekstit që shkon te tabela `explanations`, si me shabllonin).

**Çfarë i dërgohet ofruesit.** Vetëm `GroundingContext` përmes `build_prompt` (ADR 0015): vlerat, intervalet, statusi, termat dhe citimet e mjekut. Kurrë emri i pacientit, mosha, gjinia, emri i skedarit apo dokumenti i papërpunuar (një test e provon duke kërkuar emrin e pacientit dhe emrin e skedarit te çdo kërkesë). Citimet e mjekut kalojnë fjalë për fjalë; nëse një citim ka emër ose detaj identifikues, ai shkon te ofruesi, dhe nuk ka hap që ta heq.

**Cikli i njëjtë si te eksperimentet.** Gjenerim, verifikim me rregulla (dhe klasifikuesin kur është i ngarkuar), një rigjenerim me shkeljet e para, pastaj shablloni rezervë (SP8). Një ofrues që dështon (rrjeti, kuota, përjashtim) është një përpjekje e dështuar; pas dy përpjekjeve dokumenti dorëzohet me shabllonin dhe nuk humbet.

**Pacienti e di.** Një tekst i dorëzuar nga modeli mban njoftimin `model` (te `notices`), që thotë se u shkrua nga një model gjuhësor dhe se kontrolli kap vetëm një pjesë të gabimeve. Shablloni dhe shablloni rezervë nuk e kanë. Njoftimi është i shkruar nga sistemi, jo nga gjeneruesi (NFR7).

## Alternativat e refuzuara

**Të ndizet modeli sapo `ANALYTE_LLM_PROVIDER` është i vendosur.** Ofruesi është te `.env` për eksperimentet; ndezja e padukshme e dërgimit të të dhënave të pacientëve nuk duhet të varet nga një ndryshore që ka një qëllim tjetër.

**Cache e përgjigjeve edhe te aplikacioni.** Do t'i ruante te disku, e nga aty te depoja nëse dosja përputhet, kërkesat me të dhëna të pacientëve të vërtetë.

**Të mbahet vetëm shablloni.** Aplikacioni do të tregonte vetëm bazën e sigurt, jo shtegun që punimi mat. Autori e zgjodhi lidhjen.

## Pasojat

- **Me modelin, shumë dokumente dalin me shabllon rezervë.** Chapter 6 mat 25% (E8); në provën e vërtetë me Mistral dokumenti i provuar (një i korpusit sintetik) e refuzoi verifikimi dy herë, me 4 dhe 1 shkelje, dhe doli shablloni rezervë.
- **Verifikimi nuk është garanci.** Auditi i pavarur i E8 gjeti problem të llojeve që rregullat synojnë te 36% e teksteve që kaluan; njoftimi i thotë këtë pacientit, por problemi mbetet.
- **Të dhënat dalin nga sistemi** kur `ANALYTE_SERVICE_GENERATOR=model`. Kjo është pikërisht ajo që skica etike (`docs/ethics`) pyet: kushtet e ofruesit (plani falas) për ruajtjen dhe përdorimin e të dhënave, pëlqimi i pacientit, dhe nëse dokumentet reale duhet çidentifikuar para ngarkimit. Asnjë prej tyre nuk është vendosur.
- **Koha.** Një thirrje zgjat sekonda dhe plani falas ka kufi në minutë; me radhën arq punëtori e merr këtë, me `inline` kërkesa e ngarkimit pret.
- **Çelësi është te `.env` i shërbimit.** Si çdo sekret, nuk shkruhet te kodi, te depoja apo te biseda.

## Çfarë u provua

`tests/integration/test_model_in_service.py` (13 teste), me një klient të simuluar:

- pa çelësin e ndarë aplikacioni gjeneron me shabllon, edhe kur `.env` ka ofruesin, çelësin dhe modelin; me të, gjeneron me modelin, me `client.cache is None`;
- konfigurimi i paplotë (pa çelës, pa model, ofrues i panjohur, ose `model` pa ofrues) e ndalon shërbimin kur nis;
- teksti i modelit që kalon verifikimin dorëzohet me njoftimin `model`; përpjekja e parë e refuzuar rigjenerohet një herë me shkeljet te kërkesa e dytë (shkelja shfaqet atje) dhe dorëzohet;
- dy përpjekje të refuzuara dorëzojnë shabllonin pa njoftimin `model` dhe me atë `fallback`; një ofrues që hedh gabim nuk e humb dokumentin: gjendja `delivered`, teksti i shabllonit, dy thirrje;
- kërkesa që i dërgohet ofruesit nuk përmban emrin e pacientit as emrin e skedarit; shablloni vetëm nuk mban njoftim modeli.

Gjashtë nga këto pohime u provuan edhe duke i prishur (modeli nuk ndizet kurrë; ofruesi i eksperimenteve e ndez modelin; cache në disk; pa njoftim për modelin; pa njoftim për shablloni rezervë; rigjenerim pa shkeljet); secila prishje rrëzoi një test.

**Prova e vërtetë (2026-10-05).** Me ofruesin, modelin dhe çelësin nga `.env` dhe aplikacionin e ndërtuar nga `build_services`: një dokument sintetik, dy thirrje (4123 token hyrës, 1205 dalës, pa cache, pa rifreskime), përpjekja 1 me 4 shkelje, përpjekja 2 me 1, dorëzim me shabllon rezervë, njoftimi `fallback` dhe pa `model`. Kjo provon lidhjen nga fillimi te fundi me një ofrues të vërtetë; nuk provon cilësinë e tekstit të modelit mbi dokumente reale.
