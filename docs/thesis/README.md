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

## Tabelat

`tables/` gjenerohet nga `scripts/build_tables.py` dhe nuk shkruhet me
dorë. Tabelat T1-T4 dalin nga po ata skedarë dhe po ai katalog që përdor
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
- **Figurat.** Thirrjet e figurave janë shënuar; vizatimi i tyre mbetet.
