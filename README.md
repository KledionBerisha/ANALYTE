# ANALYTE

Nxjerrje, interpretim determinist dhe shpjegim i verifikuar i analizave
laboratorike në gjuhën shqipe.

Sistemi nxjerr vlerat laboratorike dhe pohimet klinike nga dokumente
mjekësore shqip, i interpreton ato me rregulla deterministe, gjeneron
shpjegim për pacientin me model gjuhësor të kufizuar rreptësisht në atë
interpretim, dhe verifikon automatikisht se teksti i gjeneruar nuk shton
asgjë të pambështetur.

Garancia qendrore është e shprehur si nënshkrim tipi: shtresa e
gjenerimit merr vetëm një `GroundingContext` dhe asgjë tjetër — as
dokumentin e papërpunuar, as tekstin e nxjerrë prej tij.

## Gjendja

| Pjesa | Gjendja |
|---|---|
| Kontrata e domenit (`domain/`) | e plotë |
| Politika e sigurisë dhe katalogu i rregullave (`domain/policy.py`) | e plotë |
| Klasifikimi determinist (`grounding/branch_a/classify.py`) | i plotë |
| Gjeneruesi i korpusit sintetik (`data_generator/`) | i plotë: të dhëna, narrativë, PDF në tri formate, simulim skanimi |
| Infrastruktura e vlerësimit (`evaluation/`) | e plotë: PK1-PK6, matrica E1-E15, prejardhja e rezultateve |
| Dega A — vlerat nga tabela (`ingestion/`, `grounding/branch_a/`) | kanali dixhital dhe OCR (Tesseract, ADR 0012); kombinimet ndërmjet analiteve |
| Dega B — pohimet nga narrativa (`grounding/branch_b/`) | e plotë: terma, mohim, pasiguri, krahasim i kryqëzuar |
| Verifikimi (`verification/`) | rregullat R1-R9 dhe SP1-3; klasifikuesi XLM-R i trajnuar në Colab dhe i matur (ADR 0009) |
| Makina e gjendjeve (`orchestration/`) | e plotë, me rigjenerim dhe shabllon rezervë (ADR 0011) |
| Gjenerimi (`generation/`) | shablloni determinist (rezervë) dhe modeli gjuhësor përmes klientit me cache (`ministral-14b-2512`, ADR 0015); biseda jo |
| Shërbimi (`api/`, `persistence/`, `audit/`) | API, PostgreSQL, radha arq, auditim, skedarë të koduar (ADR 0013); biseda jo |
| Ndërfaqja web (`frontend/`) | Next.js: ngarkimi, hapat e përpunimit, shpjegimi me verifikim, vlerat me burimin në dokument; biseda jo |

## Struktura

```
backend/src/analyte/domain/     modelet, enum-et dhe politika — pa I/O, pa varësi
backend/src/analyte/catalog.py  tabelat burimore: analitet, njësitë, terminologjia
backend/src/analyte/ingestion/  leximi i PDF-së dhe vendimi tekst/OCR
backend/src/analyte/grounding/  interpretimi i vlerave (Dega A) dhe i tekstit (Dega B)
data_generator/                 korpusi sintetik: të dhënat, faqet dhe simulimi i skanimit
evaluation/                     harness-i i eksperimenteve dhe metrikat PK1-PK6
resources/                      tabelat burimore: analitet, njësitë, terminologjia
tests/                          njësi, fixture referues
```

## Shërbimi

```bash
cp .env.example .env              # plotësoni dy sekretet dhe postën (shih më poshtë)
docker compose up -d --wait       # PostgreSQL (5433) dhe Redis
cd backend && alembic upgrade head && cd ..
uvicorn analyte.main:app --reload --app-dir backend/src
arq analyte.orchestration.worker.WorkerSettings    # në terminal tjetër
```

**Posta.** Llogaria aktivizohet me një lidhje të dërguar me email (ADR 0016), prandaj shërbimi nuk nis pa
konfigurim posta. Në zhvillim, vendosni te `.env` kredencialet SMTP të një kutie prove të Mailtrap
(`ANALYTE_SMTP_HOST`, `_PORT`, `_USERNAME`, `_PASSWORD`; shih `.env.example`), ose `ANALYTE_MAIL_BACKEND=console`
për të parë lidhjen te log-u i shërbimit pa SMTP.

Ndërfaqja: `cd frontend && npm install && npm run dev`, pastaj
`http://localhost:3000`. Dokumentimi i API-së: `http://localhost:8000/docs`. Testi mbi PostgreSQL
të vërtetë: `make test-postgres`.

## Përdorimi

Instalimi për zhvillim:

```bash
pip install -e ".[dev,generate]"
```

Grupi `generate` nevojitet vetëm për vizatimin e korpusit. Shërbimi nuk
varet prej tij: ai nuk shtyp kurrë PDF, ai vetëm i lexon.

Testet:

```bash
python -m pytest
```

Gjenerimi i korpusit sintetik:

```bash
python -m data_generator.generate --seed 42 --n 500 --out data/v1
```

Për çdo dokument shkruhen dy skedarë: PDF-ja që sheh sistemi dhe JSON-i
me të vërtetën bazë që nuk e sheh kurrë. Rreth 35% e dokumenteve kalojnë
nëpër simulimin e skanimit — anim, turbullim, zhurmë dhe artefakte
kompresimi — dhe dalin pa shtresë teksti, sepse PK1 dhe PK2 raportohen
veçmas për dixhitale dhe për të skanuara. Përpjesa rregullohet me
`--scanned-share`.

Vizatimi kushton rreth një sekondë për dokument të skanuar, prandaj një
korpus prej 500 dokumentesh merr disa minuta.

Dy ekzekutime me të njëjtin seed japin bajt për bajt të njëjtat skedarë,
PDF-të e përfshira; kjo kontrollohet me test. Korpuset nuk versionohen —
ato rindërtohen nga seed-i dhe nga shumat kontrolluese të tabelave
burimore që ruhen në `manifest.json`.

Ekzekutimi i eksperimenteve mbi një korpus:

```bash
python -m evaluation.harness --dataset data/v1 --pipeline empty
```

Shkruan `evaluation/results/{ID}/` për secilin nga E1-E15 dhe një
`summary.md` me matricën e plotë. Qelizat që presin një komponent të
paekzistuar shtypen `[TO BE MEASURED]`; ato nuk lihen bosh dhe nuk
ngatërrohen me zero.

Katër pipeline-a pa gjenerim njihen (`e6`–`e9` janë kushtet e ablacionit, më sipër). Dy prej tyre janë kufij dhe jo sisteme: `empty`
nuk nxjerr asgjë dhe asnjë metrikë nuk duhet ta shpërblejë, `oracle` kthen
vetë të vërtetën dhe çdo metrikë duhet të arrijë vlerën e përsosur mbi të.
Dy të tjerët janë sistemi: `branch_a` nxjerr vlerat nga tabela, `grounding`
shton pohimet e narrativës dhe krahasimin e kryqëzuar.

Të dhënat e vërteta nuk i kalojnë kurrë sistemit: hyrja e tij mban vetëm
identifikuesin e dokumentit dhe shtegun e PDF-së.

### Modeli gjuhësor

Pa konfigurim, gjeneruesi është shablloni. Për të përdorur një model, te `.env`
(shih `.env.example`; çelësi nuk shkruhet kurrë në kod):

```
ANALYTE_LLM_PROVIDER=mistral         # gemini | mistral | groq | cerebras | openrouter | openai_compatible
ANALYTE_LLM_MODEL=ministral-14b-2512 # emër me version, jo `-latest`
ANALYTE_LLM_API_KEY=
```

Kushtet e ablacionit me modelin (nga rrënja, me `--ocr` për të skanuarat):

```bash
python -m evaluation.harness --dataset data/v1 --generator llm --ocr --pipeline e6 --experiment E6   # pa bazim
python -m evaluation.harness --dataset data/v1 --generator llm --ocr --pipeline e7 --experiment E7   # vetëm bazim
python -m evaluation.harness --dataset data/v1 --generator llm --ocr --pipeline e8 --experiment E8   # + rregulla
python -m evaluation.harness --dataset data/v1 --generator llm --ocr --pipeline e9 --experiment E9 --classifier ml/artifacts/runs/sentence
python -m evaluation.harness --dataset data/v1 --generator llm --ocr --pipeline e8 --experiment E4   # PK3
```

Çdo përgjigje e modelit ruhet te `evaluation/cache/llm/` (një skedar për kërkesë, çelës
hash-i i kërkesës së plotë) dhe versionohet në git: një ekzekutim i dytë nuk bën asnjë thirrje dhe jep
po atë tekst. Nëse ofruesi bie ose kuota mbaron, ekzekutimi ndalet (jo numërohet si gabim i modelit)
dhe e njëjta komandë vazhdon aty ku u ndal. Numrat e Kapitullit 6 merren nga një kopje e pastër e git-it
(`git worktree add --detach <dosja> HEAD`, me `data/` dhe `ml/artifacts/` të lidhura), jo nga pema e punës.

Gjykatësit (E12) dhe auditi i E8 përdorin modele Claude si subagjentë, pa API: `python -m evaluation.judge_batches`
dhe `python -m evaluation.audit_batches` shkruajnë batch-e pa etiketa dhe rillogarisin rezultatin nga
përgjigjet e ruajtura; shih ADR 0015 për kufizimet. Tabelat e Kapitullit 6 dalin nga
`python scripts/build_chapter6_tables.py`.

## Konventat

- `domain/` nuk importon asgjë nga pjesa tjetër e sistemit. Kjo zbatohet
  me test, jo me disiplinë.
- Vlerat numerike janë `Decimal` kudo. Verifikimi krahason numra për
  barazi të saktë, prandaj `float` do të prodhonte shkelje fantazmë.
- Objektet e domenit janë të pandryshueshme; çdo transformim prodhon
  objekt të ri, çka e mban gjurmën e auditimit të plotë.
- Komentet dhe emrat në dokumentim janë shqip; vlerat e enum-eve dhe
  identifikuesit janë anglisht, sepse ruhen në bazën e të dhënave.
- Kutitë kufizuese kanë origjinën në këndin e sipërm-majtas, ashtu si i
  raportojnë bibliotekat që lexojnë PDF. Kthimi nga sistemi i PDF-së
  bëhet një herë, te vizatuesi.
- Metrikat kthejnë `None` kur nuk kishte çfarë të matej dhe kurrë zero.
  Zeroja është pohim; `None` është mungesë matjeje.
- Sistemit nuk i kalon kurrë e vërteta bazë: ajo hyrje mban vetëm
  identifikuesin e dokumentit dhe shtegun e PDF-së, dhe kjo zbatohet me
  test.
