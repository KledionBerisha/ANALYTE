# Kapitulli 3 — plan leximi (pa citime)

*Plan pune, jo tekst për punimin. Nuk përmban asnjë citim të ri: emrat që shfaqen janë ata që autori i ka
shkruar vetë te `teza_v3.md` (§8, lista «burime që duhen lexuar»), dhe secili duhet lexuar para se të citohet.
Referencat [1]–[4] janë ato të verifikuara.*

## 1. Çfarë ka tashmë dhe çfarë i mungon

| Seksioni | Gjendja | Çfarë i duhet literaturës (pohimi që duhet mbështetur) |
|---|---|---|
| 3.1.1 intervali referent, 3.1.2 LOINC | shkruar pa burim | një burim për variacionin e intervaleve ndërmjet laboratorëve; dokumentacioni zyrtar i LOINC (ka në listën e autorit) |
| 3.1.3 komunikimi me pacientin | vetëm hyrja; vendmbajtës | 2–3 studime që thonë se qasja në rezultate nuk sjell kuptim automatikisht (portale pacientësh; PubMed, JAMIA) |
| 3.2.1 nxjerrja e informacionit klinik | vendmbajtës | burime që thonë se sistemet me rregulla mbeten konkurruese në fushë të ngushtë |
| 3.2.2 mohimi | shkruar mbi [1], [2] | gati |
| 3.2.3 thjeshtimi i teksteve mjekësore | vendmbajtës | literatura e thjeshtimit mjekësor (ACL Anthology, PubMed) dhe si matet; lidhet me PK3 (§6.4), që mat vetëm besnikërinë ndaj udhëzimit të kopjimit |
| 3.2.4 gjuhët me burime të pakta | pohim pa burim («nuk ka model klinik për shqipen») | burim ose kërkim i dokumentuar që e mbështet (data dhe fjalë kyçe të kërkimit) |
| 3.3.1–3.3.2 halucinacioni | shkruar mbi [3] | kontrolloni që «shqyrtimi i parë gjithëpërfshirës» është formuluar ashtu si thotë vetë burimi |
| 3.3.3 bazimi | pa burim | RAG dhe bazimi në burim (një ose dy burime) |
| 3.4.1 NLI | shkruar mbi [4] | gati; shih shënimin e §3 |
| 3.4.2 metoda të tjera | vendmbajtës | SelfCheckGPT, FActScore, HaluEval, Maynez et al. (nga lista e autorit), me një rresht të vetin për secilën |
| 3.5 XLM-RoBERTa | vendmbajtës | Conneau et al. (2020), nga lista e autorit |
| 3.7.1–3.7.3 rregullatore | shkruar pa burim zyrtar; vetë teksti e quan «në lëvizje» | teksti zyrtar i çdo rregulloreje të emëruar te §8; statusin e Rregullores (BE) 2026/1744 e konfirmon autori nga Gazeta Zyrtare |

Qëllimi i listës së autorit është 40–60 burime; sot janë 4. Përpjesëtim i propozuar (jo i detyrueshëm): 3.1 rreth
6–8, 3.2 rreth 8–10, 3.3 rreth 8–10, 3.4 rreth 8–10, 3.5 rreth 3–4, 3.7 rreth 6–8. Rregullat e Kapitullit 6 kërkojnë
më pak burime sesa kjo listë; mos shtoni burim vetëm për të mbushur numrin.

## 2. Si kërkohet (recetë, jo rezultat)

- **PubMed / JAMIA:** `patient portal` AND (`comprehension` OR `understanding`) AND `laboratory results`.
- **ACL Anthology:** `medical text simplification`, `lay summary`, `faithfulness`, `factual consistency`,
  `hallucination detection`.
- **Gjuhë me burime të pakta:** `Albanian` AND (`clinical` OR `biomedical`) AND (`NLP` OR `corpus`). Shënoni datën
  e kërkimit dhe çfarë gjetët, që «nuk ekziston» të jetë pohim i dokumentuar, jo supozim.
- Për çdo burim të lexuar: shkruani një rresht me çfarë pohon, dhe vendin e punimit ku e përdorni.

## 3. Formulimi i klasifikuesit (vendosur 2026-10-04)

§5.7 dhe §3.4.3 u ndryshuan që të thonë ç'u ndërtua: klasifikuesi parashikon një nga tetë llojet e shkeljes ose `clean`
(ADR 0009), jo marrëdhënien NLI me tre klasa. Kapitulli 3 mund ta mbajë NLI-në si motivim dhe terren literature [4];
§3.4.1 nuk pretendon më që ajo është detyra e zbatuar. Kur ta shkruani 3.4, mos e rikthejeni formulimin NLI si detyrë të punimit.

## 4. Çfarë nuk bën kjo fletë

Nuk zgjedh burime, nuk jep numra dhe nuk shkruan fjalinë e Kapitullit 3. Çdo pohim që del prej tij duhet të ketë
burimin e lexuar nga autori.
