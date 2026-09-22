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
| Nxjerrja, gjenerimi, verifikimi, ndërfaqja | ende jo |

## Struktura

```
backend/src/analyte/domain/     modelet, enum-et dhe politika — pa I/O, pa varësi
backend/src/analyte/grounding/  interpretimi i vlerave (Dega A) dhe i tekstit (Dega B)
data_generator/                 korpusi sintetik: të dhënat, faqet dhe simulimi i skanimit
evaluation/                     harness-i i eksperimenteve dhe metrikat PK1-PK6
resources/                      tabelat burimore: analitet, njësitë, terminologjia
tests/                          njësi, fixture referues
```

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

Dy pipeline-a shërbejnë si kufij: `empty` nuk nxjerr asgjë dhe asnjë
metrikë nuk duhet ta shpërblejë, `oracle` kthen vetë të vërtetën dhe çdo
metrikë duhet të arrijë vlerën e përsosur mbi të. Të dy përdoren në teste;
`oracle` nuk është sistem por provë e metrikave.

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
