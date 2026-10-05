<!-- E gjeneruar nga scripts/build_tables.py. Mos e ndrysho me dorë: ndrysho burimin te resources/ ose te domain/policy.py. -->

### Tabela 4. Katalogu i rregullave të verifikimit

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
| R8 | B | `omitted_recommendation` | Çdo rekomandim i mjekut duhet të ruhet në dalje. | tërë dalja |
| R9 | B | `ungrounded_term_explanation` | Asnjë term jashtë tabelës terminologjike nuk guxon të shpjegohet. | fjalia |
| SP1-3 | B | `prohibited_claim` | Asnjë pohim diagnostik, trajtimi apo prognoze. | fjalia |

Fushëveprimi ndan rregullat që vendosen nga një fjali e vetme nga ato që
kërkojnë shikim mbi tërë daljen. Vetëm të parat mund të përbëjnë detyrë
klasifikimi në nivel fjalie, prandaj kjo kolonë përcakton edhe se cilat
shkelje mund të mësohen nga klasifikuesi i Fazës 7 dhe cilat jo.
