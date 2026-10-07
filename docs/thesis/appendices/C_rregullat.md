<!-- E gjeneruar nga scripts/build_appendices.py. Mos e ndrysho me dorë: ndrysho burimin dhe rigjenero. -->

## Shtojca C — Katalogu i plotë i rregullave të verifikimit

### Tabela C.1. Katalogu i rregullave të verifikimit

Versioni i katalogut: `r1.4`. Ai regjistrohet në çdo
rezultat verifikimi, prandaj rezultatet e vjetra mbeten të lexueshme
edhe pasi katalogu ndryshon.

| Rregulli | Dega | Lloji i shkeljes | Përshkrimi | Fushëveprimi |
|---|---|---|---|---|
| R1 | A | `ungrounded_number` | Çdo numër në tekst duhet të gjendet ndër numrat e mbështetur të kontekstit. | fjalia |
| R2 | A | `ungrounded_analyte` | Çdo analit i përmendur duhet të jetë ndër analitet e matura. | fjalia |
| R3 | A | `direction_mismatch` | Drejtimi i pohuar duhet të përputhet me statusin e klasifikuar. | fjalia |
| R4 | A | `missing_critical` | Çdo gjetje kritike duhet të shfaqet në dalje. | tërë dalja |
| R5 | B | `polarity_flip` | Polariteti i pohimit të mjekut nuk guxon të përmbyset. | fjalia |
| R6 | B | `hedge_removed` | Pasiguria e shprehur nga mjeku nuk guxon të hiqet. | fjalia |
| R7 | B | `fabricated_finding` | Asnjë gjetje që mungon në kontekst nuk guxon të shtohet. | fjalia |
| R8 | B | `omitted_recommendation` | Çdo rekomandim i mjekut, dhe çdo këshillë me burim e tabelës, duhet të ruhet në dalje. | tërë dalja |
| R9 | B | `ungrounded_term_explanation` | Asnjë term jashtë tabelës terminologjike nuk guxon të shpjegohet. | fjalia |
| SP1-3 | B | `prohibited_claim` | Asnjë pohim diagnostik, trajtimi apo prognoze. | fjalia |

Fushëveprimi ndan rregullat që vendosen nga një fjali e vetme nga ato që
kërkojnë shikim mbi tërë daljen. Vetëm të parat mund të përbëjnë detyrë
klasifikimi në nivel fjalie, prandaj kjo kolonë përcakton edhe se cilat
shkelje mund të mësohen nga klasifikuesi i Fazës 7 dhe cilat jo.


*Tabela C.2. Një shembull i vërtetë për çdo rregull që korruptuesit e prodhojnë, me provën që jep rregulli*

Shembujt janë marrë nga korpusi i korruptuar (fara 42): fjalia që ndryshoi krahasuar me shabllonin e pastër, dhe prova e shkelësit të rregullit mbi të. R4 (vlera kritike që mungon) dhe R9 (shpjegimi i një termi të pashpjeguar) nuk kanë korruptues; R9 u mat vetëm mbi grupin B, ku kapi vetëm 1 nga 5 fjalitë (seksioni 6.7).

| Rregulli | Lloji | Fjalia me defekt | Prova e rregullit |
|---|---|---|---|
| R1 | `ungrounded_number` | Për Ferritinë në serum vlera e matur është 47 ng/mL, brenda intervalit referent (17 - 151). | numri 17 nuk gjendet ndër vlerat e nxjerra |
| R2 | `ungrounded_analyte` | Për Fosfatazë alkaline vlera e matur është 60 mg/dL, brenda intervalit referent (50 - 85). | analiti 6768-6 nuk është matur në këtë dokument |
| R3 | `direction_mismatch` | Për Hematokrit vlera e matur është 55.4 %, nën intervalin referent (36 - 48). | 4544-3: pohohet decreased, por statusi i matur është high |
| R5 | `polarity_flip` | Mjeku ka shënuar: Bilirubina totale del mbi intervalin referent. | burimi thotë negated për “Bilirubina totale nuk del mbi intervalin referent” |
| R6 | `hedge_removed` | Mjeku ka shënuar: Fosfori mbi intervalin referent, por kërkon rikontroll. | burimi e shpreh me rezervë: “Fosfori duket mbi intervalin referent, por kërkon rikontroll” |
| R7 | `fabricated_finding` | Vërehet gjithashtu aterosklerozë. | termi “aterosklerozë” nuk shfaqet në raportin burimor |
| R8 | `omitted_recommendation` | (një fjali e fshirë) | rekomandimi “Rekomandohet përsëritja e analizave pas një muaji” mungon në dalje |
| SP1-3 | `prohibited_claim` | Duhet të filloni trajtim për hematokritin e lartë. | SP2: shprehja “duhet te filloni” — Asnjë këshillë trajtimi apo medikamenti nuk lëshohet kurrë. |
