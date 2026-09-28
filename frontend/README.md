# ANALYTE — ndërfaqja

Next.js 16, React 19, TypeScript, Tailwind 4. E gjitha logjika e
interpretimit dhe e verifikimit është te shërbimi; ndërfaqja vetëm e
paraqet atë, dhe nuk llogarit asnjë status, asnjë interval, asnjë tekst.

```bash
npm install
npm run dev          # http://localhost:3000 — kërkon API-në në :8000
npm run lint
npm run api:types    # pas `python scripts/export_openapi.py`
```

`NEXT_PUBLIC_API_URL` ndryshon adresën e API-së (parazgjedhja
`http://localhost:8000`).

## Çfarë tregon

- **Ngarkimi dhe historia** — `/documents`.
- **Hapat e përpunimit** ndërsa ndodhin, nga kalimet që regjistron shërbimi.
- **Njoftimi kritik (SP4)** para çdo teksti, dhe **njoftimi i OCR-së** në krye
  kur dokumenti u lexua nga një skanim.
- **Shpjegimi** me treguesin e verifikimit; citimet e mjekut të ndara nga
  fjalitë e sistemit; shënimi për profesionistin (SP7) në fund.
- **Vlerat**, dhe për secilën **rreshti në dokumentin origjinal** nga i cili
  u lexua.
- **Mospërputhjet** ndërmjet shënimit të mjekut dhe matjes.
- **Si u kontrollua shpjegimi** — çdo përpjekje, edhe ato të refuzuara, me
  shkeljet e tyre.

## Vendime

- **Tipat e API-së gjenerohen** nga skema OpenAPI (`src/lib/api/schema.d.ts`)
  dhe nuk shkruhen me dorë.
- **Tokenët në `sessionStorage`**: mbyllja e skedës e mbyll seancën — e
  arsyeshme për të dhëna shëndetësore në kompjuterë të përbashkët.
- **Faqet e dokumentit si figura**, të kërkuara me token dhe të shfaqura si
  URL objekti; PDF-ja origjinale nuk i jepet shfletuesit.
- **Teksti i verifikuar nuk ndryshohet.** Ndërfaqja e ndan në pjesë — njoftim,
  fjali, citime, shënim — por nuk shton, nuk heq dhe nuk riformulon asgjë.
