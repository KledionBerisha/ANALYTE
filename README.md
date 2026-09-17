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
| Gjeneruesi i korpusit sintetik (`data_generator/`) | të dhënat e strukturuara dhe narrativa; vizatimi i PDF-së mbetet |
| Nxjerrja, gjenerimi, verifikimi, ndërfaqja | ende jo |

## Struktura

```
backend/src/analyte/domain/     modelet, enum-et dhe politika — pa I/O, pa varësi
backend/src/analyte/grounding/  interpretimi i vlerave (Dega A) dhe i tekstit (Dega B)
data_generator/                 korpusi sintetik me të vërtetën bazë
resources/                      tabelat burimore: analitet, njësitë, terminologjia
tests/                          njësi, fixture referues
```

## Përdorimi

Instalimi për zhvillim:

```bash
pip install -e ".[dev]"
```

Testet:

```bash
python -m pytest
```

Gjenerimi i korpusit sintetik:

```bash
python -m data_generator.generate --seed 42 --n 500 --out data/v1
```

Dy ekzekutime me të njëjtin seed japin bajt për bajt të njëjtat skedarë;
kjo kontrollohet me test. Korpuset nuk versionohen — ato rindërtohen nga
seed-i dhe nga shumat kontrolluese të tabelave burimore që ruhen në
`manifest.json`.

## Konventat

- `domain/` nuk importon asgjë nga pjesa tjetër e sistemit. Kjo zbatohet
  me test, jo me disiplinë.
- Vlerat numerike janë `Decimal` kudo. Verifikimi krahason numra për
  barazi të saktë, prandaj `float` do të prodhonte shkelje fantazmë.
- Objektet e domenit janë të pandryshueshme; çdo transformim prodhon
  objekt të ri, çka e mban gjurmën e auditimit të plotë.
- Komentet dhe emrat në dokumentim janë shqip; vlerat e enum-eve dhe
  identifikuesit janë anglisht, sepse ruhen në bazën e të dhënave.
