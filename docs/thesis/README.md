# Draftet e kapitujve

Skedarët këtu janë rishikime të seksioneve të `teza_v2.md`, të shkruara
pasi komponenti përkatës u zbatua dhe u mat. Drafti ekzistues i Kapitullit
5 u shkrua përpara zbatimit dhe përshkruan qëllimin; këto seksione
përshkruajnë atë që ekziston, bashkë me atë që nuk ekziston ende.

Ato nuk e zëvendësojnë tekstin kryesor automatikisht. Secili mban numrin
e seksionit të cilit i përket, që bashkimi të bëhet me dorë dhe me
vetëdije.

| Skedari | Seksioni | Mbulon |
|---|---|---|
| `ch05_02_kontrata_e_te_dhenave.md` | 5.2 | Kontrata e të dhënave si garanci e zbatuar |
| `ch05_03_dega_laboratorike.md` | 5.3 | Dega A ashtu si u zbatua |
| `ch05_04_dega_e_raportit.md` | 5.4 | Dega B ashtu si u zbatua |
| `ch05_08_strategjia_e_te_dhenave.md` | 5.8 | Korpusi sintetik ashtu si u ndërtua |
| `ch05_11_infrastruktura_e_vleresimit.md` | i ri | Harness-i dhe metrikat |

## Versioni 3 (2026-10-02)

`teza_v3.md` është `teza_v2.md` me drafte e Kapitullit 5 të bashkuara (5.2.1, 5.3, 5.4,
5.8.1, 5.11.2), gabimet e gjetura kundrejt kodit të ndrequra, dhe Shtojcat A–I në fund.
Origjinali `teza_v2.md` nuk u ndryshua.

| Skedari | Çfarë është |
|---|---|
| `teza_v3.md` | Teksti i plotë me figurat dhe shtojcat |
| `appendices/` | Shtojcat A–I, të gjeneruara nga kodi: `python scripts/build_appendices.py` |
| `figures/` | Figurat 1–11 dhe 18–21, të gjeneruara nga kodi (numrat në kuti vijnë nga katalogu, ata të rezultateve nga skedarët e rezultateve): `python scripts/build_figures.py` |
| `tables/` | Tabelat e shtojcave B dhe C, nga `python scripts/build_tables.py` |

Çfarë ndryshoi nga v2, e verifikuar kundrejt kodit: fazat e Degës A janë gjashtë (jo shtatë);
krahasimi i tri detektorëve nuk bëhet mbi të njëjtën hyrje (ADR 0009); Tabela 1 nuk liston spaCy
dhe pdfplumber që nuk përdoren; Tabela 6 ka E15; baza nuk ka tabela ekzekutimesh dhe terminologjia
nuk është në të (ADR 0013); ndarja e korpusit sipas dokumentit nuk e ndalon rrjedhjen e shabllonit
(seksioni 5.11.1); llojet e defekteve të korpusit të korruptuar emërtohen siç janë në kod.

**Ç'mbetet e hapur:** Kapitujt 6 dhe 7, Abstrakti dhe Shtojcat janë shkruar nga skedarët e
rezultateve (përfshirë modelin gjuhësor `ministral-14b-2512`, gjykatësit dhe auditin); punimi nuk ka
dokumente reale dhe nuk ka studim me përdorues. Kapitulli 3 ka vende të pashkruara dhe 4
referenca; figurat 12–16 (pamje të ndërfaqes) nuk janë bërë dhe 17 nuk prodhohet (chat-i nuk është
ndërtuar); burimet e terminologjisë dhe të kombinimeve mungojnë; grupi A i fjalive me dorë është bosh.

## Tabelat

`tables/` gjenerohet nga `scripts/build_tables.py` dhe nuk shkruhet me
dorë. Tabelat T1-T5 dalin nga po ata skedarë dhe po ai katalog që përdor
sistemi, sepse një tabelë e shtypur me dorë fillon të largohet nga kodi
që ditën e dytë.

```bash
python scripts/build_tables.py
```

## Çfarë mbetet për t'u plotësuar nga autori

- **Referencat.** Asnjë citim nuk është shkruar në këto draftë. Aty ku
  nevojitet burim, qëndron `[REFERENCË — plotësohet]`.
- **Kolona e burimit te tabela terminologjike.** Të 82 zërat mbajnë
  vendmbajtëse. Pa referencë të verifikueshme, tabela bëhet vetë burim
  informacioni të paverifikuar — pikërisht ajo që SP6 synon të pengojë.
- **Rregullat e kombinimit (Tabela 5).** Njëmbëdhjetë kombinime, secili me
  burim vendmbajtës. Kombinimet duhen konfirmuar nga mentori ose nga një
  mjek, jo vetëm burimi i tyre.
- **Figurat.** Thirrjet e figurave janë shënuar; vizatimi i tyre mbetet.
