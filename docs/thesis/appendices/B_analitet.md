<!-- E gjeneruar nga scripts/build_appendices.py. Mos e ndrysho me dorë: ndrysho burimin dhe rigjenero. -->

## Shtojca B — Paneli i plotë i analiteve

Tabelat dalin nga `resources/` me `scripts/build_tables.py`, po ata skedarë që lexon sistemi. Intervalet janë ato të tabelës së brendshme, që përdoren vetëm kur dokumenti nuk e shtyp vetë intervalin.

### Tabela B.1. Paneli i analiteve dhe hartëzimi LOINC

Intervalet janë ato të tabelës së brendshme, e cila përdoret vetëm kur
dokumenti nuk e shtyp vetë intervalin. Aty ku kufijtë ndryshojnë sipas
gjinisë, jepen të dy.

| Kodi LOINC | Analiti | Njësia | Paneli | Interval (M) | Interval (F) |
|---|---|---|---|---|---|
| 718-7 | Hemoglobinë në gjak | g/dL | hematologji | 13.5 – 17.5 | 12.0 – 16.0 |
| 4544-3 | Hematokrit | % | hematologji | 40.0 – 52.0 | 36.0 – 48.0 |
| 789-8 | Eritrocite | 10^12/L | hematologji | 4.50 – 5.90 | 4.00 – 5.20 |
| 6690-2 | Leukocite | 10^9/L | hematologji | 4.0 – 10.0 | — |
| 777-3 | Trombocite | 10^9/L | hematologji | 150 – 400 | — |
| 787-2 | Volumi mesatar eritrocitar | fL | hematologji | 80.0 – 100.0 | — |
| 785-6 | Hemoglobina mesatare eritrocitare | pg | hematologji | 27.0 – 33.0 | — |
| 786-4 | Përqendrimi mesatar i hemoglobinës | g/dL | hematologji | 32.0 – 36.0 | — |
| 2345-7 | Glukozë në serum | mg/dL | biokimi | 70 – 99 | — |
| 4548-4 | Hemoglobinë e glikuar | % | biokimi | 4.0 – 5.6 | — |
| 2160-0 | Kreatininë në serum | mg/dL | veshkat | 0.70 – 1.30 | 0.60 – 1.10 |
| 3094-0 | Ure në serum | mg/dL | veshkat | 15 – 45 | — |
| 3084-1 | Acid urik në serum | mg/dL | veshkat | 3.4 – 7.0 | 2.4 – 6.0 |
| 2951-2 | Natrium në serum | mmol/L | elektrolite | 135 – 145 | — |
| 2823-3 | Kalium në serum | mmol/L | elektrolite | 3.5 – 5.1 | — |
| 2075-0 | Klor në serum | mmol/L | elektrolite | 98 – 107 | — |
| 17861-6 | Kalcium në serum | mg/dL | elektrolite | 8.6 – 10.2 | — |
| 2777-1 | Fosfor në serum | mg/dL | elektrolite | 2.5 – 4.5 | — |
| 2601-3 | Magnez në serum | mg/dL | elektrolite | 1.7 – 2.4 | — |
| 1742-6 | Alanin aminotransferazë | U/L | melcia | 10 – 40 | 7 – 35 |
| 1920-8 | Aspartat aminotransferazë | U/L | melcia | 10 – 40 | — |
| 6768-6 | Fosfatazë alkaline | U/L | melcia | 40 – 130 | — |
| 2324-2 | Gama-glutamil transferazë | U/L | melcia | 10 – 71 | 6 – 42 |
| 1975-2 | Bilirubinë totale | mg/dL | melcia | 0.20 – 1.20 | — |
| 1751-7 | Albuminë në serum | g/dL | melcia | 3.5 – 5.2 | — |
| 2885-2 | Proteina totale | g/dL | melcia | 6.4 – 8.3 | — |
| 2093-3 | Kolesterol total | mg/dL | lipide | 120 – 200 | — |
| 2085-9 | Kolesterol HDL | mg/dL | lipide | 40 – 70 | 50 – 85 |
| 13457-7 | Kolesterol LDL | mg/dL | lipide | 50 – 130 | — |
| 2571-8 | Trigliceride | mg/dL | lipide | 50 – 150 | — |
| 3016-3 | Hormoni stimulues i tiroides | mIU/L | tiroide | 0.40 – 4.00 | — |
| 3024-7 | Tiroksinë e lirë | ng/dL | tiroide | 0.80 – 1.80 | — |
| 3051-0 | Triiodotironinë e lirë | pg/mL | tiroide | 2.3 – 4.2 | — |
| 2276-4 | Ferritinë në serum | ng/mL | hekuri | 30 – 400 | 15 – 150 |
| 2498-4 | Hekur në serum | ug/dL | hekuri | 65 – 175 | 50 – 170 |
| 1988-5 | Proteina C-reaktive | mg/L | inflamacion | 0.0 – 5.0 | — |
| 2132-9 | Vitaminë B12 | pg/mL | vitamina | 200 – 900 | — |
| 1989-3 | Vitaminë D 25-OH | ng/mL | vitamina | 30.0 – 100.0 | — |

Tabela përmban 38 analite me interval referent.

Krahas tyre, sistemi njeh me emër edhe 8 analite për të cilat
tabela e brendshme nuk përmban interval. Këto nuk janë mangësi e tabelës
por rasti që rregullon politika SP5: vlera matet, emri njihet, dhe
interpretimi refuzohet.

| Kodi LOINC | Analiti | Njësia |
|---|---|---|
| 13965-9 | Homocisteinë në serum | umol/L |
| 33959-8 | Prokalcitoninë | ng/mL |
| 3040-3 | Lipazë në serum | U/L |
| 1798-8 | Amilazë në serum | U/L |
| 10839-9 | Troponinë I | ng/mL |
| 2857-1 | Antigjen specifik i prostatës | ng/mL |
| 1834-1 | Alfa-fetoproteinë | ng/mL |
| 2532-0 | Laktat dehidrogjenazë | U/L |


### Tabela B.2. Faktorët e konvertimit të njësive

Faktori shumëzon vlerën e shtypur në njësinë e parë për ta kthyer në
njësinë kanonike. Konvertimi varet nga analiti kudo ku në të hyn masa
molare, prandaj shumica e rreshtave janë specifikë për një kod LOINC.

| Nga | Në | Faktori | Analiti |
|---|---|---|---|
| g/L | g/dL | 0.1 | çdo analit |
| mmol/L | mg/dL | 18.0182 | 2345-7 |
| umol/L | mg/dL | 0.0113122 | 2160-0 |
| mmol/L | mg/dL | 6.006 | 3094-0 |
| umol/L | mg/dL | 0.0584795 | 1975-2 |
| mmol/L | mg/dL | 38.67 | 2093-3 |
| mmol/L | mg/dL | 38.67 | 2085-9 |
| mmol/L | mg/dL | 38.67 | 13457-7 |
| mmol/L | mg/dL | 88.57 | 2571-8 |


### Tabela B.3. Rregullat e kombinimit ndërmjet analiteve

Një rregull ndizet kur të gjitha kushtet plotësohen njëkohësisht.
Vlera kritike numërohet sipas drejtimit të saj; vlera pa interval
referent nuk merr pjesë (SP5). Rregulli nuk emërton gjendje: dalja thotë
vetëm se kombinimi kërkon vlerësim nga profesionisti shëndetësor.

| ID | Kushtet | Burimi |
|---|---|---|
| P01 | Hemoglobinë në gjak ↓ + Ferritinë në serum ↓ | J. Snook, N. Bhala, I. L. P. Beales, et al., "British Society of Gastroenterology guidelines for the management of iron deficiency anaemia in adults," *Gut*, vol. 70, no. 11, pp. 2030–2051, 2021, doi: 10.1136/gutjnl-2021-324757. https://gut.bmj.com/content/70/11/2030 |
| P02 | Hemoglobinë në gjak ↓ + Volumi mesatar eritrocitar ↓ | H. S. Chaudhry and M. R. Kasarla, "Microcytic Hypochromic Anemia," in *StatPearls* [Internet], Treasure Island, FL: StatPearls Publishing, updated Feb. 2026. https://www.ncbi.nlm.nih.gov/books/NBK470252/ |
| P03 | Hemoglobinë në gjak ↓ + Vitaminë B12 ↓ | R. C. Langan and A. J. Goodbred, "Vitamin B12 Deficiency: Recognition and Management," *American Family Physician*, vol. 96, no. 6, pp. 384–389, 2017. https://www.aafp.org/pubs/afp/issues/2017/0915/p384.html |
| P04 | Glukozë në serum ↑ + Hemoglobinë e glikuar ↑ | American Diabetes Association Professional Practice Committee, "2. Diagnosis and Classification of Diabetes: Standards of Care in Diabetes—2025," *Diabetes Care*, vol. 48, suppl. 1, pp. S27–S49, 2025, doi: 10.2337/dc25-S002. https://diabetesjournals.org/care/article/48/Supplement_1/S27/157566 |
| P05 | Kreatininë në serum ↑ + Ure në serum ↑ | A. O. Hosten, "BUN and Creatinine," in *Clinical Methods: The History, Physical, and Laboratory Examinations*, 3rd ed., H. K. Walker, W. D. Hall, J. W. Hurst, Eds. Boston, MA: Butterworths, 1990, ch. 193. https://www.ncbi.nlm.nih.gov/books/NBK305/ |
| P06 | Alanin aminotransferazë ↑ + Aspartat aminotransferazë ↑ | P. N. Newsome, R. Cramb, S. M. Davison, et al., "Guidelines on the management of abnormal liver blood tests," *Gut*, vol. 67, no. 1, pp. 6–19, 2018, doi: 10.1136/gutjnl-2017-315541. https://gut.bmj.com/content/67/1/6 |
| P07 | Fosfatazë alkaline ↑ + Gama-glutamil transferazë ↑ | P. N. Newsome, R. Cramb, S. M. Davison, et al., "Guidelines on the management of abnormal liver blood tests," *Gut*, vol. 67, no. 1, pp. 6–19, 2018, doi: 10.1136/gutjnl-2017-315541. https://gut.bmj.com/content/67/1/6 |
| P08 | Hormoni stimulues i tiroides ↑ + Tiroksinë e lirë ↓ | S. A. Wilson, L. A. Stem, and R. D. Bruehlman, "Hypothyroidism: Diagnosis and Treatment," *American Family Physician*, vol. 103, no. 10, pp. 605–613, 2021. https://www.aafp.org/pubs/afp/issues/2021/0515/p605.html |
| P09 | Hormoni stimulues i tiroides ↓ + Tiroksinë e lirë ↑ | D. S. Ross, H. B. Burch, D. S. Cooper, et al., "2016 American Thyroid Association Guidelines for Diagnosis and Management of Hyperthyroidism and Other Causes of Thyrotoxicosis," *Thyroid*, vol. 26, no. 10, pp. 1343–1421, 2016, doi: 10.1089/thy.2016.0229. https://journals.sagepub.com/doi/10.1089/thy.2016.0229 |
| P10 | Leukocite ↑ + Proteina C-reaktive ↑ | L. K. Riley and J. Rupert, "Evaluation of Patients with Leukocytosis," *American Family Physician*, vol. 92, no. 11, pp. 1004–1011, 2015. https://www.aafp.org/pubs/afp/issues/2015/1201/p1004.html |
| P11 | Kolesterol LDL ↑ + Kolesterol HDL ↓ | F. Mach, C. Baigent, A. L. Catapano, et al., "2019 ESC/EAS Guidelines for the management of dyslipidaemias: lipid modification to reduce cardiovascular risk," *European Heart Journal*, vol. 41, no. 1, pp. 111–188, 2020, doi: 10.1093/eurheartj/ehz455. https://academic.oup.com/eurheartj/article/41/1/111/5556353 |

> Burimi i secilit kombinim u lexua më 2026-10-06; citimi i evidencës dhe
> shkalla e mbështetjes (e plotë ose e pjesshme) për secilin jepen te
> `docs/thesis/worksheets/burimet_e_gjetura.md`. Kombinimet duhen konfirmuar
> nga mentori ose nga një mjek përpara dorëzimit.

