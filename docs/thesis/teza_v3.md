# Programi për Shkenca Kompjuterike dhe Inxhinierisë

**Bazimi determinist dhe verifikimi i automatizuar i shpjegimeve mjekësore të gjeneruara nga modelet e mëdha gjuhësore**

Shkalla Bachelor

Denis [Mbiemri]

[Muaji] / [Viti]
Prishtinë

---

# Programi për Shkenca Kompjuterike dhe Inxhinierisë

Punim Diplome

Viti akademik [XXXX] – [YYYY]

Denis [Mbiemri]

**Bazimi determinist dhe verifikimi i automatizuar i shpjegimeve mjekësore të gjeneruara nga modelet e mëdha gjuhësore**

Mentori: [Titulli. Emri dhe Mbiemri]

[Muaji] / [Viti]

Ky punim është përpiluar dhe dorëzuar në përmbushjen e kërkesave të pjesshme për Shkallën Bachelor

---

> **SHËNIM PËR STATUSIN** *(hiqet para dorëzimit)*
>
> Versioni 3, ndërtuar më 2026-10-02. Kapitujt 2, 4 dhe 5 janë të shkruar; Kapitulli 5 u rishikua kundrejt zbatimit të vërtetë (seksionet 5.2.1, 5.3, 5.4, 5.8.1 dhe 5.11.2 vijnë nga `docs/thesis/ch05_*.md`). Kapitulli 3 ka ende vende të pashkruara dhe 4 referenca të verifikuara. Kapitujt 6 dhe 7 janë ende skelet; çdo vlerë e pamatur është shënuar **[MATET]**. Shtojcat A–I gjenerohen nga kodi (`scripts/build_appendices.py`) dhe jepen në fund.
>
> **Ç'nuk është bërë, dhe teksti nuk duhet të pretendojë të kundërtën:** nuk ka model gjuhësor (shablloni është gjeneruesi i vetëm, ndaj E4, E6 dhe E12 janë të pamatura dhe E7–E9 janë vetëm kufij të njohur); nuk ka dokumente reale (E13); nuk ka studim me përdorues (E14). Grupi B i fjalive (`evaluation/handwritten/B_fjalite.csv`) e dorëzoi autori; një draft i mëparshëm i hartuar nga një model gjuhësor ekzistonte në depo dhe 12 nga 105 rreshta (vetëm citime të mjekut) janë identikë me të — kjo duhet deklaruar te punimi (shih `evaluation/handwritten/README.md`).

---

# ABSTRAKT

Rezultatet e analizave laboratorike dhe raportet mjekësore u dorëzohen pacientëve në një formë të hartuar për profesionistin shëndetësor dhe jo për vetë pacientin. Dokumenti përmban shkurtesa latine, njësi që ndryshojnë sipas laboratorit dhe intervale referente që nuk janë të vetëkuptueshme, me pasojë që pacienti ka qasje në informacionin e vet pa pasur qasje në kuptimin e tij. Modelet e mëdha gjuhësore e bëjnë teknikisht të mundur riformulimin e këtij informacioni në gjuhë të thjeshtë, por ato prodhojnë me rrjedhshmëri edhe pohime që nuk mbështeten nga dokumenti burimor, dukuri e njohur në literaturë si halucinacion. Në kontekst mjekësor, një pohim i tillë nuk është thjesht gabim cilësie por rrezik i drejtpërdrejtë për pacientin.

Ky punim propozon, implementon dhe vlerëson ANALYTE, një sistem i ndërtuar mbi parimin se modeli gjuhësor nuk duhet të ketë autoritet mbi faktet. Informacioni nxirret nga dokumenti dhe interpretohet nga një shtresë deterministe; modeli gjuhësor merr vetëm këtë përfaqësim të strukturuar dhe merret ekskluzivisht me formulimin gjuhësor; një shtresë e automatizuar verifikimi kontrollon daljen e gjeneruar kundrejt burimit përpara se ajo t'i shfaqet përdoruesit. Asnjë tekst i paverifikuar nuk arrin te përdoruesi.

Arkitektura testohet njëkohësisht në dy fusha me natyrë thelbësisht të ndryshme: rezultate laboratorike numerike të strukturuara dhe raporte mjekësore në tekst të lirë. Për të dhënat numerike verifikimi është mekanikisht i vendosshëm, ndërsa për prozën klinike ai është semantik dhe rrjedhimisht më pak i sigurt. Kjo asimetri matet dhe raportohet si gjetje e pavarur e punimit.

Vlerësimi kryhet mbi një korpus sintetik dokumentesh laboratorike shqip, i gjeneruar posaçërisht për këtë punim dhe i pajisur me të vërtetë bazë të plotë, si dhe validohet mbi një grup të vogël dokumentesh reale të anonimizuara. Eksperimenti kryesor krahason normën e pohimeve të pambështetura në katër kushte: pa bazim, me bazim, me verifikim me rregulla dhe me verifikim të plotë.

**[REZULTATET KRYESORE — KAPITULLI 6]**

Punimi trajton gjithashtu zbatueshmërinë e qasjes në gjuhën shqipe, për të cilën nuk ekziston asnjë model klinik i paratrajnuar i përpunimit të gjuhës natyrore, dhe dokumenton pasojat arkitekturore të kësaj mungese.

**Fjalë kyçe:** halucinacion, bazim, verifikim i automatizuar, përpunim i gjuhës natyrore në mjekësi, modele të mëdha gjuhësore, rezultate laboratorike, gjuhë me burime të pakta

---

# MIRËNJOHJE/FALENDERIME

*[Shkruhet në fund. Mentori, stafi akademik i UBT-së, familja, si dhe çdo institucion ose laborator që ka kontribuar me të dhëna ose me miratim etik.]*

---

# PËRMBAJTJA

*[Gjenerohet automatikisht në Word pas formatimit përfundimtar. Abstrakti dhe mirënjohja nuk paraqiten këtu.]*

---

# LISTA E FIGURAVE

Figura 1. Fazat kryesore të zhvillimit të sistemit ANALYTE

Figura 2. Arkitektura e përgjithshme e sistemit

Figura 3. Tubacioni i përpunimit të rezultateve laboratorike

Figura 4. Tubacioni i përpunimit të raportit mjekësor

Figura 5. Arkitektura e shtresës së verifikimit

Figura 6. Makina e gjendjeve e përpunimit të dokumentit

Figura 7. Entity Relationship Diagram (ERD) i databazës

Figura 8. Struktura modulare e aplikacionit

Figura 9. Procesi i gjenerimit të korpusit sintetik

Figura 10. Ndërtimi i korpusit të korruptuar për trajnimin e klasifikuesit

Figura 11. Tubacioni i vlerësimit dhe gjurmueshmëria e eksperimenteve

Figura 12. Faqja e autentikimit të sistemit

Figura 13. Ngarkimi i dokumentit dhe statusi i përpunimit

Figura 14. Paraqitja e gjetjeve laboratorike të strukturuara

Figura 15. Shpjegimi në gjuhë të thjeshtë me treguesin e verifikimit

Figura 16. Krahasimi i raportit mjekësor me rezultatet laboratorike

Figura 17. Chat-i i lidhur me dokumentin

Figura 18. Rezultatet e ablacionit të shtresës së verifikimit

Figura 19. Matrica e konfuzionit për klasifikimin e statusit

Figura 20. Matricat e konfuzionit për tre qasjet e detektimit

Figura 21. Shpërndarja e llojeve të shkeljeve të zbuluara

---

# LISTA E TABELAVE

Tabela 1. Teknologjitë kryesore të përdorura në sistem

Tabela 2. Paneli i analiteve dhe hartëzimi me kodet LOINC

Tabela 3. Faktorët e konvertimit të njësive

Tabela 4. Ekstrakt nga tabela terminologjike shqip

Tabela 5. Katalogu i rregullave të verifikimit

Tabela 6. Matrica e eksperimenteve

Tabela 7. Saktësia e nxjerrjes së të dhënave laboratorike

Tabela 8. Saktësia e klasifikimit kundrejt intervaleve referente

Tabela 9. Besnikëria e thjeshtimit të tekstit mjekësor

Tabela 10. Saktësia e krahasimit të kryqëzuar

Tabela 11. Rezultatet e ablacionit të verifikimit

Tabela 12. Krahasimi i tre qasjeve të detektimit

Tabela 13. Performanca e detektorëve sipas llojit të defektit

Tabela 14. Rezultatet e studimit me përdorues

Tabela 15. Taksonomia e gabimeve të vërejtura

---

# FJALORI I TERMAVE

**ALT** – Alanine Aminotransferase

**API** – Application Programming Interface

**AST** – Aspartate Aminotransferase

**CDSS** – Clinical Decision Support System

**ERD** – Entity Relationship Diagram

**F1-Score** – Mesatarja harmonike e precision-it dhe recall-it

**GDPR** – General Data Protection Regulation

**Grounding** – Bazimi i daljes së gjeneruar në një burim të verifikueshëm

**HbA1c** – Hemoglobina e glikuar

**Hallucination** – Përmbajtje e gjeneruar që nuk mbështetet nga burimi

**Hedging** – Shprehje gjuhësore e pasigurisë klinike

**JWT** – JSON Web Token

**LLM** – Large Language Model

**LOINC** – Logical Observation Identifiers Names and Codes

**MDR** – Medical Device Regulation

**NER** – Named Entity Recognition

**NLI** – Natural Language Inference

**NLP** – Natural Language Processing

**OCR** – Optical Character Recognition

**PK1–PK7** – Pyetjet kërkimore të këtij punimi

**REST** – Representational State Transfer

**XLM-RoBERTa** – Model enkoder shumëgjuhësh i paratrajnuar

---

# 2 HYRJE

Zhvillimi i shërbimeve elektronike shëndetësore ka ndryshuar rrënjësisht mënyrën se si pacientët kanë qasje në informacionin e tyre mjekësor. Rezultatet e analizave laboratorike, që dikur komunikoheshin ekskluzivisht përmes mjekut, sot i dorëzohen pacientit drejtpërdrejt në formë elektronike, shpesh brenda pak orësh nga kryerja e analizës dhe përpara se ai të ketë mundësi të flasë me një profesionist shëndetësor. Kjo qasje e drejtpërdrejtë konsiderohet përgjithësisht si përparim, sepse e vendos pacientin në qendër të procesit dhe e pajis atë me informacionin që i përket.

Megjithatë, qasja në informacion nuk është e njëjta gjë me qasjen në kuptim. Një raport laboratorik është dokument teknik i hartuar për profesionistin shëndetësor. Ai përmban shkurtesa latine ose angleze, njësi matëse që ndryshojnë nga një laborator në tjetrin, dhe intervale referente të shtypura në mënyrë të tillë që marrëdhënia e tyre me vlerën e matur nuk është gjithmonë e qartë për një lexues jo profesionist. Për pacientin, rezultati praktik është një dokument që e zotëron por nuk e kupton.

Pasojat e kësaj situate nuk janë neutrale. Pacienti që nuk e kupton dokumentin e vet ose pret takimin e radhës me mjekun, duke shtyrë kuptimin për javë të tëra, ose kërkon shpjegim në burime të painformuara në internet, ku informacioni nuk është i përshtatur për rastin e tij konkret dhe shpesh është i pasaktë. Të dyja rrugët janë të dobëta: e para vonon informimin, e dyta e zëvendëson atë me përmbajtje të paverifikuar që mund të shkaktojë ankth të panevojshëm ose, në drejtimin e kundërt, qetësi të pajustifikuar që e shtyn pacientin të mos kërkojë ndihmë kur duhet.

Zhvillimi i shpejtë i modeleve të mëdha gjuhësore gjatë viteve të fundit e ka bërë teknikisht të mundur zgjidhjen e këtij problemi. Këto modele janë jashtëzakonisht të afta në riformulimin e tekstit teknik në gjuhë të thjeshtë dhe në përshtatjen e nivelit të shpjegimit sipas lexuesit. Në parim, një sistem që merr një raport laboratorik dhe prodhon një shpjegim të kuptueshëm për pacientin është një aplikim i drejtpërdrejtë i teknologjisë ekzistuese.

Problemi qëndron në një veti të këtyre modeleve që në kontekstin mjekësor bëhet vendimtare. Modelet gjuhësore gjenerojnë tekst të rrjedhshëm edhe kur përmbajtja e tij nuk mbështetet nga burimi. Kjo dukuri, e njohur në literaturë si halucinacion, është përshkruar në mënyrë sistematike nga Ji et al. [3], të cilët dallojnë ndërmjet halucinacionit intrinsik, ku përmbajtja e gjeneruar kundërshton burimin, dhe halucinacionit ekstrinsik, ku përmbajtja nuk mund të verifikohet nga burimi. Në shumicën e aplikimeve, një halucinacion përbën shqetësim për cilësinë e produktit. Në kontekstin e shpjegimit të një rezultati mjekësor, ai përbën rrezik.

Skenarët konkretë janë të thjeshtë për t'u imagjinuar dhe të rëndë për nga pasojat. Një sistem mund t'i thotë pacientit se një vlerë është brenda normës kur në fakt nuk është. Mund të përmendë një analizë që nuk është kryer fare, duke krijuar përshtypjen se një aspekt i shëndetit është kontrolluar kur nuk është. Mund ta kthejë një mohim të shprehur nga mjeku në pohim, duke e shndërruar një gjetje të përjashtuar në një gjetje të konfirmuar. Secili prej këtyre rasteve mund të ndikojë drejtpërdrejt në vendimin e pacientit për të kërkuar ose për të mos kërkuar ndihmë mjekësore.

Qasja më e zakonshme ndaj këtij problemi në praktikë është udhëzimi i modelit që të mos shpikë informacion. Ky punim niset nga premisa se një udhëzim i tillë nuk përbën mekanizëm sigurie. Ai mund ta ulë frekuencën e problemit, por nuk e eliminon dhe, më e rëndësishmja, nuk ofron asnjë mënyrë për të matur nëse është zbatuar. Nëse siguria e një sistemi mjekësor varet nga bindja e një modeli statistikor, ajo nuk është siguri por shpresë.

Punimi propozon një zgjidhje arkitekturore. Modeli gjuhësor nuk e sheh kurrë dokumentin e papërpunuar. Informacioni nxirret dhe interpretohet nga një shtresë deterministe që punon me rregulla të verifikueshme dhe jo me modele probabilistike. Modeli gjuhësor merr vetëm përfaqësimin e strukturuar që rezulton nga kjo shtresë dhe ngarkohet ekskluzivisht me formulimin gjuhësor. Pas gjenerimit, një shtresë e automatizuar verifikimi kontrollon në mënyrë mekanike nëse çdo pohim i tekstit të gjeneruar mbështetet nga përfaqësimi i strukturuar. Vetëm teksti që kalon këtë kontroll i shfaqet përdoruesit.

Parimi organizues i të gjithë sistemit mund të përmblidhet në një fjali: modeli gjuhësor formulon gjuhën, por nuk përcakton faktet.

Kontributi kryesor i punimit nuk është ndërtimi i një aplikacioni web mjekësor, sepse sisteme të tilla ekzistojnë në numër të konsiderueshëm. Kontributi është shtresa e verifikimit dhe vlerësimi i saj sasior. Punimi mat sa shpesh modeli prodhon përmbajtje të pambështetur, sa e ul këtë verifikimi, dhe sa saktë e zbulon vetë verifikimi përmbajtjen problematike.

Një element i dytë, po aq i rëndësishëm, është krahasimi i drejtpërdrejtë i dy niveleve të bazimit. Arkitektura zbatohet njëkohësisht mbi të dhëna numerike të strukturuara, ku verifikimi mund të jetë i saktë, dhe mbi tekst klinik të lirë, ku ai mund të jetë vetëm semantik dhe rrjedhimisht i pasigurt. Ky ndryshim nuk fshihet por matet dhe raportohet, sepse ai përcakton se çfarë lloj garancie mund të japë realisht një sistem i tillë.

Së fundi, punimi zhvillohet për gjuhën shqipe. Për shqipen nuk ekziston asnjë model klinik i paratrajnuar i përpunimit të gjuhës natyrore i krahasueshëm me modelet e disponueshme për anglishten. Kjo mungesë nuk është detaj teknik por kufizim që përcakton arkitekturën e sistemit, dhe dokumentimi i pasojave të saj përbën kontribut më vete në një fushë ku literatura ekzistuese është pothuajse inekzistente.

Punimi organizohet si vijon. Kapitulli 3 shqyrton literaturën përkatëse mbi diagnostikën laboratorike, përpunimin e gjuhës natyrore në mjekësi, halucinacionet e modeleve gjuhësore dhe metodat e verifikimit. Kapitulli 4 formulon problemin dhe paraqet pyetjet kërkimore. Kapitulli 5 përshkruan metodologjinë, arkitekturën, implementimin dhe planin e vlerësimit. Kapitulli 6 paraqet rezultatet e matura. Kapitulli 7 i diskuton ato dhe nxjerr përfundimet e punimit.

---

# 3 SHQYRTIMI I LITERATURËS (HISTORIKU)

## 3.1 Diagnostika laboratorike dhe interpretimi i rezultateve

### 3.1.1 Natyra e intervalit referent

Interpretimi i një vlere laboratorike nuk është veti e vetë vlerës por e marrëdhënies së saj me një interval referent. Ky interval përcaktohet nga secili laborator mbi bazën e metodës analitike që përdor dhe të popullatës referente që ka matur, dhe varet gjithashtu nga mosha dhe gjinia e personit. Rrjedhimisht, i njëjti rezultat numerik mund të klasifikohet si normal në një laborator dhe si jashtë normës në një tjetër, pa asnjë gabim nga ana e asnjërit.

Kjo veti ka pasoja të drejtpërdrejta për dizajnin e çdo sistemi që synon të interpretojë automatikisht rezultate laboratorike. Një tabelë e ngurtë intervalesh të shkruar në kod prodhon në mënyrë të pashmangshme klasifikime të gabuara për dokumente që vijnë nga laboratorë me metoda të ndryshme. Zgjidhja e vetme e qëndrueshme është nxjerrja e intervalit nga vetë dokumenti sa herë që ai është i shtypur atje, dhe përdorimi i një tabele rezervë vetëm si zgjidhje e fundit, me regjistrim të qartë se cili burim është përdorur për secilën vlerë.

### 3.1.2 Standardizimi terminologjik dhe LOINC

Një pengesë e dytë në përpunimin automatik të dokumenteve laboratorike është mungesa e uniformitetit në emërtimin e testeve. I njëjti analit mund të shfaqet si shkurtesë latine, si emërtim i plotë anglisht, si emërtim shqip, ose në një variant lokal specifik për laboratorin.

LOINC, sistemi ndërkombëtar i identifikuesve për observimet laboratorike dhe klinike, është përgjigjja standarde ndaj kësaj situate. Ai cakton një identifikues të qëndrueshëm për çdo test, pavarësisht emërtimit që përdor institucioni konkret. Për sistemet automatike, LOINC funksionon si shtresë normalizimi që e zëvendëson një fjalor sinonimesh të improvizuar me një standard të dokumentuar dhe të citueshëm.

### 3.1.3 Komunikimi i rezultateve me pacientin

Rritja e qasjes së drejtpërdrejtë të pacientëve në rezultatet e tyre përmes portaleve elektronike ka krijuar një fushë të re problemesh që lidhen me kuptueshmërinë. Literatura mjekësore ka dokumentuar se disponueshmëria e informacionit nuk përkthehet automatikisht në kuptim, dhe se interpretimi i pasaktë nga vetë pacienti mund të prodhojë reagime emocionale të papërshtatshme me gjendjen reale klinike.

*[Zgjerohet me 2–3 studime nga PubMed ose JAMIA mbi patient portal comprehension. Mos cito para se t'i lexosh.]*

## 3.2 Përpunimi i gjuhës natyrore në kontekst mjekësor

### 3.2.1 Nxjerrja e informacionit klinik

Nxjerrja e informacionit të strukturuar nga tekstet klinike është një nga drejtimet më të vjetra të përpunimit të gjuhës natyrore në mjekësi. Sistemet e hershme bazoheshin tërësisht në fjalorë terminologjikë dhe rregulla të shkruara manualisht, ndërsa qasjet e mëvonshme kanë përdorur modele statistikore dhe, së fundmi, modele neuronale të paratrajnuara mbi korpuse klinike.

Rëndësia e kësaj literature për punimin aktual qëndron në një vërejtje metodologjike: sistemet e bazuara në rregulla mbeten konkurruese kur fusha e problemit është e ngushtë dhe e përcaktuar mirë, dhe kanë përparësinë e vendimtare se janë plotësisht të shpjegueshme dhe të auditueshme.

*[Zgjerohet me 2–3 burime.]*

### 3.2.2 Zbulimi i mohimit

Mohimi përbën një problem qendror në përpunimin e teksteve klinike, sepse një gjetje e pohuar dhe një gjetje e mohuar kanë kuptime krejtësisht të kundërta ndërsa ndajnë pothuajse të njëjtat fjalë përmbajtësore. Një sistem që injoron mohimin nuk prodhon një gabim të vogël por një gabim të përmbysur.

Chapman et al. [1] propozuan algoritmin NegEx, i cili identifikon frazat mohuese përmes shprehjeve të rregullta, filtron rastet ku një frazë duket mohuese pa qenë e tillë, dhe kufizon fushëveprimin e mohimit brenda një distance të caktuar nga fraza. Në një test me 1235 gjetje dhe sëmundje të shpërndara në 1000 fjali nga epikriza, algoritmi arriti specificitet prej 94.5 përqind dhe vlerë parashikuese pozitive prej 84.5 përqind, duke ruajtur një ndjeshmëri prej 77.8 përqind [1].

Harkema et al. [2] e zgjeruan këtë qasje me algoritmin ConText, i cili përcakton jo vetëm nëse një gjetje është e mohuar, por edhe kush është përjetuesi i saj dhe cili është statusi i saj kohor.

Rëndësia e këtyre dy punimeve për ANALYTE është e dyfishtë. Së pari, ato tregojnë se një qasje e bazuar në rregulla, relativisht e thjeshtë dhe e vlerësuar mirë, është e mjaftueshme për zbulimin e mohimit në tekste klinike. Së dyti, dhe më rëndësishëm për kontekstin e këtij punimi, kjo qasje nuk varet nga ekzistenca e një modeli neuronal të paratrajnuar për gjuhën konkrete, gjë që e bën atë të zbatueshme për shqipen.

### 3.2.3 Thjeshtimi i teksteve mjekësore

Thjeshtimi i tekstit mjekësor për lexues jo profesionistë është fushë e veçantë kërkimore me metrika dhe sfida të vetat. Problemi qendror i saj është se thjeshtimi dhe besnikëria janë në tension: sa më shumë të thjeshtohet një tekst, aq më i madh bëhet rreziku që të humbasë nuanca klinike thelbësore.

*[Zgjerohet me literaturë nga ACL Anthology dhe PubMed mbi medical text simplification.]*

### 3.2.4 Gjuhët me burime të pakta

Modelet klinike të paratrajnuara ekzistojnë praktikisht vetëm për anglishten. Për shqipen nuk ekziston asnjë model i krahasueshëm, dhe as korpuse klinike të anotuara publikisht.

Kjo mungesë ka pasojë të drejtpërdrejtë arkitekturore. Komponentët që në një sistem anglisht do të realizoheshin me një model klinik të specializuar duhet të realizohen ndryshe: me fjalorë dhe rregulla aty ku problemi është i vendosshëm, dhe me enkoderë shumëgjuhësh të përgjithshëm aty ku nuk është. Ky punim e trajton këtë kufizim jo si mangësi që duhet fshehur, por si kusht i projektimit që duhet dokumentuar.

## 3.3 Modelet e mëdha gjuhësore dhe halucinacionet

### 3.3.1 Përkufizimi dhe tipologjia

Ji et al. [3] ofrojnë shqyrtimin e parë gjithëpërfshirës të problemit të halucinacionit në gjenerimin e gjuhës natyrore, duke mbuluar përkufizimin, kategorizimin, shkaktarët, metrikat e matjes dhe metodat e zbutjes. Dallimi që ata vendosin ndërmjet halucinacionit intrinsik dhe atij ekstrinsik hartëzohet drejtpërdrejt në kategoritë e shkeljeve që ky punim përcakton dhe mat. Një pohim që kundërshton statusin e strukturuar të një analiti është halucinacion intrinsik; përmendja e një analiti që nuk është matur fare është halucinacion ekstrinsik.

### 3.3.2 Shkaqet

Literatura identifikon disa burime të dallueshme të halucinacionit, që shtrihen nga cilësia e të dhënave të trajnimit deri te vetë procesi i dekodimit gjatë gjenerimit [3]. Për qëllimet e këtij punimi, vërejtja thelbësore është se asnjë nga këto shkaqe nuk eliminohet përmes udhëzimit në prompt. Halucinacioni është veti strukturore e mënyrës si funksionojnë këto modele dhe jo dështim i rastësishëm që mund të korrigjohet me formulim më të mirë të kërkesës.

Ky konstatim është arsyeja pse punimi trajton verifikimin si mekanizëm të veçantë dhe të pavarur nga gjenerimi, dhe jo si përmirësim të tij.

### 3.3.3 Bazimi

Bazimi është praktika e kufizimit të gjenerimit në një burim të verifikueshëm. Format e tij janë të ndryshme, nga futja e dokumentit burimor në kontekst deri te arkitekturat që kombinojnë kërkimin me gjenerimin.

Ky punim zbaton një formë të rreptë të bazimit, ku modeli nuk merr fare dokumentin burimor por vetëm një objekt të strukturuar të prodhuar nga shtresa deterministe. Dallimi është thelbësor: në bazimin e zakonshëm, modeli mund të interpretojë gabim burimin; në bazimin e rreptë, interpretimi është kryer tashmë përpara se modeli të përfshihet.

## 3.4 Verifikimi i daljes së modeleve gjuhësore

### 3.4.1 Natural Language Inference si bazë verifikimi

Natural Language Inference, detyra e klasifikimit të marrëdhënies ndërmjet një premise dhe një hipoteze si entailment, kundërshti ose neutralitet, është korniza e natyrshme formale për pyetjen nëse një pohim mbështetet nga një burim.

Laban et al. [4] rishikojnë përdorimin e modeleve NLI për zbulimin e mospërputhjeve faktike dhe konstatojnë se punimet e mëparshme kishin dështuar për shkak të një mospërputhjeje granulariteti: dataset-et NLI janë ndërtuar në nivel fjalie, ndërsa zbulimi i mospërputhjeve zbatohet në nivel dokumenti. Ata propozojnë metodën SummaCConv, e cila e zgjidh këtë duke segmentuar dokumentin në njësi fjalie dhe duke agreguar rezultatet ndërmjet çifteve të fjalive [4]. Mbi benchmark-un SummaC, të përbërë nga gjashtë dataset-e zbulimi mospërputhjeje, metoda arrin saktësi të balancuar prej 74.4 përqind [4].

Ky rezultat ka rëndësi të dyfishtë për punimin aktual. Së pari, ai konfirmon se qasja e bazuar në NLI për verifikimin e mbështetjes është e vlefshme dhe e vlerësuar. Së dyti, dhe më rëndësishëm, shifra prej rreth 74 përqind saktësi të balancuar tregon se verifikimi semantik mbi tekst të lirë mbetet dukshëm larg përsosmërisë edhe në gjendjen aktuale të teknikës. Ky është pikërisht kufizimi që ky punim e mat drejtpërdrejt përmes krahasimit të dy degëve të sistemit.

### 3.4.2 Metoda të tjera detektimi

Literatura përmban gjithashtu qasje që nuk mbështeten në një burim të jashtëm por në qëndrueshmërinë e brendshme të gjenerimeve të shumta, si dhe metrika që e zbërthejnë tekstin e gjeneruar në pohime atomike dhe i verifikojnë ato veçmas.

*[Zgjerohet me SelfCheckGPT, FActScore, HaluEval dhe punime të ngjashme pas leximit.]*

### 3.4.3 Pozicionimi i këtij punimi

Dallimi kryesor i ANALYTE nga literatura e mësipërme qëndron në natyrën e premisës. Në punimet e cituara, premisa është tekst dhe verifikimi është rrjedhimisht detyrë semantike me normë gabimi të pashmangshme. Në degën e rezultateve laboratorike të ANALYTE, premisa nuk është tekst por një objekt i strukturuar me vlera numerike të njohura dhe statuse të përcaktuara në mënyrë deterministe. Pyetja nëse një numër mbështetet nga burimi ka përgjigje të vendosshme, dhe verifikimi bëhet krahasim dhe jo gjykim.

Modeli NLI mbetet i nevojshëm vetëm për degën e tekstit të lirë. Ky ndarje i qëllimshëm i dy regjimeve, dhe matja e ndryshimit ndërmjet tyre, është ajo që punimi e paraqet si kontribut.

## 3.5 Modelet shumëgjuhëshe

Meqë modelet klinike të specializuara mbulojnë vetëm anglishten, komponenti neuronal i këtij sistemi duhet të mbështetet në një enkoder shumëgjuhësh të përgjithshëm. XLM-RoBERTa është paratrajnuar mbi një korpus të gjerë shumëgjuhësh që përfshin edhe gjuhë me burime relativisht të pakta, dhe përdoret gjerësisht si bazë për detyra klasifikimi në gjuhë për të cilat nuk ekzistojnë modele të dedikuara.

*[Verifiko citimin e plotë të Conneau et al. (2020) përpara përdorimit.]*

## 3.6 Teknologjitë e përdorura

Sistemi është ndërtuar me teknologji të hapura të zakonshme, të zgjedhura që çdo hap të jetë i riprodhueshëm dhe i testueshëm; përdorimi i tyre përmblidhet te Tabela 1. Shërbimi është shkruar në Python me FastAPI. Modelet e domenit janë objekte të pandryshueshme Pydantic, dhe numrat dhjetorë ruhen si `Decimal`, që krahasimi i saktë i verifikimit të mos ndikohet nga rrumbullakimi binar. Të dhënat ruhen në PostgreSQL përmes SQLAlchemy me migrime Alembic, dhe punët e përpunimit ekzekutohen në sfond me arq mbi Redis. Teksti dhe koordinatat e fjalëve nga PDF-të lexohen me PyMuPDF, dhe dokumentet e skanuara kalojnë përmes Tesseract. Komponenti neuronal është XLM-RoBERTa, i trajnuar me PyTorch dhe Transformers në Google Colab. Ndërfaqja është aplikacion Next.js me React dhe TypeScript, me tipe të gjeneruara nga skema OpenAPI e shërbimit. Hyrja përdor Argon2id për fjalëkalimet dhe tokenë JWT me seanca të revokueshme. Nuk përdoret spaCy: njohja e termave, e mohimit dhe e pasigurisë bëhet me fjalorë dhe rregulla leksikore të shkruara për këtë punim (seksioni 5.4). Figurat strukturore të punimit gjenerohen nga kodi me matplotlib.

## 3.7 Aspektet rregullatore dhe etike

### 3.7.1 Kualifikimi si pajisje mjekësore

Sipas Rregullores së Bashkimit Evropian për Pajisjet Mjekësore, softueri i destinuar të japë informacion që përdoret për vendime diagnostike ose terapeutike mund të kualifikohet si pajisje mjekësore, me klasifikim të përcaktuar nga Rregulli 11 i Aneksit VIII. Dokumenti udhëzues MDCG 2019-11 trajton në detaje kualifikimin dhe klasifikimin e softuerit në këtë kuadër.

ANALYTE pozicionohet qëllimisht jashtë kësaj kategorie. Sistemi shpjegon në gjuhë të thjeshtë rezultatet e vetë pacientit dhe refuzon në mënyrë sistematike çdo pohim diagnostik, terapeutik ose prognostik. Ky punim megjithatë nuk pretendon se ky pozicionim e vendos sistemin përfundimisht jashtë fushës së rregullores, sepse kufiri ndërmjet informacionit shpjegues dhe informacionit që përdoret për vendimmarrje klinike nuk është i mprehtë dhe varet nga përdorimi real.

### 3.7.2 Akti Evropian për Inteligjencën Artificiale

Kuadri rregullator evropian për inteligjencën artificiale ka pësuar ndryshime të rëndësishme së fundmi. Digital Omnibus on AI, i miratuar si Rregullorja (BE) 2026/1744, u publikua në Gazetën Zyrtare më 24 korrik 2026 dhe hyri në fuqi më 27 korrik 2026. Ky akt shtyn zbatimin e detyrimeve për sistemet me rrezik të lartë të pavarura sipas Aneksit III deri më 2 dhjetor 2027, ndërsa për sistemet e integruara në produkte të rregulluara sipas Aneksit I afati shtyhet deri më 2 gusht 2028. Detyrimet e transparencës sipas Nenit 50 nuk u shtynë dhe zbatohen që nga 2 gushti 2026.

Pasoja praktike për një sistem si ANALYTE është se detyrimet e transparencës, përfshirë shpalosjen se përmbajtja është gjeneruar nga inteligjenca artificiale, janë tashmë të zbatueshme, ndërsa regjimi më i rëndë për sistemet me rrezik të lartë hyn në fuqi më vonë.

*[Kjo fushë është ende në lëvizje. Verifiko statusin aktual përpara dorëzimit përfundimtar.]*

### 3.7.3 Mbrojtja e të dhënave

Të dhënat shëndetësore klasifikohen si kategori e veçantë e të dhënave personale sipas Nenit 9 të Rregullores së Përgjithshme për Mbrojtjen e të Dhënave. Përpunimi i tyre kërkon bazë ligjore specifike dhe masa mbrojtëse shtesë.

Për një sistem që dërgon përmbajtjen e dokumenteve mjekësore te një ofrues i jashtëm i modeleve gjuhësore, ky ofrues merr statusin e përpunuesit dhe transferimi mund të përbëjë transferim ndërkombëtar të të dhënave shëndetësore. Një alternativë që e shmang plotësisht këtë problem është vendosja lokale e një modeli me peshë të hapur, e cila vlerësohet si opsion në kuadër të këtij punimi.

---

# 4 DEKLARIMI I PROBLEMIT

Në kujdesin shëndetësor bashkëkohor, pacienti ka gjithnjë e më shumë qasje të drejtpërdrejtë në dokumentet e veta mjekësore, por kjo qasje nuk shoqërohet me mjete që e bëjnë informacionin të kuptueshëm. Një raport laboratorik i dorëzuar elektronikisht përmban të dhëna të sakta dhe të plota, të hartuara sipas konventave profesionale, por i drejtohet një lexuesi me formim mjekësor. Pacienti që e merr këtë dokument ndodhet në pozitën e pazakontë të zotërimit të informacionit pa mundësinë e përdorimit të tij.

Problemi nuk zgjidhet me rritjen e mëtejshme të transparencës apo me qasje më të gjerë në të dhëna, sepse pengesa nuk është disponueshmëria por interpretueshmëria. Zgjidhja kërkon një shtresë ndërmjetëse që e përkthen informacionin teknik në gjuhë të kuptueshme pa e ndryshuar përmbajtjen e tij.

Modelet e mëdha gjuhësore e ofrojnë këtë aftësi përkthimi në një nivel që deri para pak vitesh nuk ishte i mundur. Megjithatë, përdorimi i tyre në këtë rol krijon një problem të dytë, i cili në kontekstin mjekësor është më i rëndë se problemi fillestar. Këto modele prodhojnë tekst të rrjedhshëm dhe bindës edhe kur përmbajtja e tij nuk mbështetet nga dokumenti burimor. Rrjedhshmëria e daljes nuk lidhet me saktësinë e saj, dhe pikërisht kjo mospërputhje e bën problemin të rrezikshëm: një pohim i gabuar nuk duket i gabuar.

Mënyrat kritike të dështimit ndryshojnë në varësi të llojit të burimit, dhe ky dallim është themelor për strukturën e punimit.

Kur burimi është një tabelë vlerash laboratorike, dështimet kryesore janë shpikja e një vlere që nuk gjendet në dokument, përmendja e një analiti që nuk është matur, kthimi i drejtimit të një gjetjeje, dhe humbja e heshtur e një vlere kritike nga shpjegimi përfundimtar. I fundit është më i rrezikshmi dhe njëkohësisht më pak i vërejturi, sepse nuk prodhon asnjë gabim të dukshëm në tekst por thjesht një mungesë.

Kur burimi është tekst narrativ i shkruar nga mjeku, dështimet janë të një natyre tjetër. Mohimi mund të kthehet, duke e shndërruar një gjetje të përjashtuar në një gjetje të konfirmuar. Shprehjet e pasigurisë mund të hiqen, duke e paraqitur një hipotezë si fakt. Mund të shtohen gjetje që mjeku nuk i ka shkruar. Mund të humbasin rekomandime konkrete si kontrolli i përsëritur pas një periudhe të caktuar. Dhe mund të shpiket një përkufizim për një term që sistemi nuk e njeh.

Ndër këto, kthimi i mohimit është shkelja më e rëndë e mundshme, sepse ndryshon kuptimin klinik në të kundërtën e tij duke ruajtur plotësisht rrjedhshmërinë gjuhësore, dhe rrjedhimisht nuk sinjalizohet në asnjë mënyrë te lexuesi.

Zgjidhjet ekzistuese ndaj këtyre problemeve janë të pamjaftueshme për tri arsye.

Së pari, udhëzimi i modelit që të mos shpikë informacion trajtohet gjerësisht si masë mbrojtëse, por nuk është e tillë. Ai mund ta zvogëlojë frekuencën e problemit, por nuk ofron asnjë garanci dhe, çka është më e rëndësishme për një punim shkencor, nuk ofron asnjë mënyrë matjeje. Një sistem, siguria e të cilit nuk mund të matet, nuk mund të vlerësohet.

Së dyti, metodat ekzistuese të verifikimit semantik nuk e shfrytëzojnë strukturën kur ajo është e pranishme. Kur burimi është një objekt i strukturuar me vlera numerike të njohura, trajtimi i verifikimit si detyrë probabilistike e humb pa nevojë saktësinë që struktura e bën të mundur.

Së treti, literatura nuk ofron një krahasim të drejtpërdrejtë të së njëjtës arkitekturë verifikimi të zbatuar njëkohësisht mbi burim të strukturuar dhe mbi tekst të lirë. Pa këtë krahasim, nuk dihet sa ndryshon siguria e garancisë ndërmjet dy rasteve, dhe rrjedhimisht nuk dihet çfarë lloj premtimi mund t'i bëhet ndershmërisht përdoruesit.

Një problem i katërt, specifik për kontekstin e këtij punimi, është mungesa e plotë e infrastrukturës gjuhësore për shqipen. Modelet klinike të paratrajnuara, korpuset e anotuara dhe fjalorët terminologjikë për pacientë ekzistojnë për anglishten dhe mungojnë për shqipen. Kjo do të thotë se zgjidhjet e gatshme nuk mund të transferohen drejtpërdrejt, dhe se çdo komponent gjuhësor duhet ose të ndërtohet nga fillimi ose të zëvendësohet me një qasje që nuk varet nga burime specifike për gjuhën.

Problemi kryesor që trajton ky punim është, pra, mungesa e një arkitekture ku modeli gjuhësor mund të përdoret për të shpjeguar informacion mjekësor pa i dhënë atij autoritet mbi faktet, dhe ku efektiviteti i këtij kufizimi mund të matet në mënyrë sasiore, si për të dhëna të strukturuara ashtu edhe për tekst klinik të lirë, në një gjuhë për të cilën mjetet e specializuara nuk ekzistojnë.

## 4.1 Pyetjet kërkimore

Pyetja kryesore kërkimore e punimit formulohet si vijon:

*Deri në ç'masë mund të gjenerojë një sistem i automatizuar shpjegime të kuptueshme për pacientin nga rezultate laboratorike dhe raporte mjekësore, pa futur përmbajtje të pambështetur nga burimi, dhe si ndryshon siguria e kësaj garancie ndërmjet të dhënave të strukturuara dhe tekstit të lirë?*

Kjo pyetje zbërthehet në shtatë nënpyetje, secila e lidhur me një metrikë të përcaktuar.

Për degën e rezultateve laboratorike, **PK1** pyet sa saktë nxirren emri i testit, vlera, njësia dhe intervali referent nga dokumentet, e matur me precision, recall dhe F1-Score, me raportim të ndarë për dokumentet digjitale dhe ato të skanuara. **PK2** pyet sa saktë klasifikohen vlerat kundrejt intervaleve referente, e matur me saktësi dhe matricë konfuzioni, e kushtëzuar nga nxjerrja e suksesshme që gabimet e fazës së mëparshme të mos e ndotin rezultatin.

Për degën e raportit mjekësor, **PK3** pyet sa besueshëm mund të thjeshtohet terminologjia mjekësore pa ndryshuar kuptimin klinik, e matur me normën e ruajtjes së mohimit, normën e ruajtjes së shprehjeve të pasigurisë, normën e gjetjeve të shpikura dhe rishikim ekspertësh mbi një mostër. **PK4** pyet sa besueshëm përputhen pohimet e raportit narrativ me vlerat laboratorike, e matur përmes një klasifikimi katërshe kundrejt anotimit manual.

Për të dyja degët bashkë, **PK5** pyet sa shpesh gjeneron modeli përmbajtje të pambështetur dhe sa e ul këtë shtresa e verifikimit; ky është eksperimenti kryesor i punimit. **PK6** pyet sa saktë e zbulon vetë shtresa e verifikimit përmbajtjen e pambështetur, duke krahasuar rregullat deterministe, klasifikuesin e finetunuar dhe modelin gjuhësor të përdorur si gjykatës. **PK7** pyet nëse përdoruesit joprofesionistë i kuptojnë më mirë rezultatet e tyre me ndihmën e sistemit.

## 4.2 Hipotezat

Punimi formulon dy hipoteza. Hipoteza e parë parashikon se shtimi i verifikimit të automatizuar e ul ndjeshëm normën e pohimeve të pambështetura që arrijnë te përdoruesi, krahasuar me bazimin pa verifikim. Hipoteza e dytë parashikon se precision-i dhe recall-i i detektorit janë më të lartë për degën e të dhënave laboratorike sesa për degën e tekstit narrativ, si pasojë e drejtpërdrejtë e asimetrisë së bazimit.

## 4.3 Shtrirja dhe kufizimet

Brenda shtrirjes së punimit hyjnë dokumentet laboratorike në gjuhën shqipe, në formë digjitale dhe të skanuar, seksionet narrative të raporteve mjekësore, një panel prej tridhjetë deri në dyzet analitesh me hartëzim LOINC, dhe një tabelë terminologjike me tetëdhjetë deri në njëqind e pesëdhjetë terma.

Jashtë shtrirjes mbeten qëllimisht diagnoza, rekomandimi i trajtimit dhe prognoza, të cilat janë të përjashtuara me politikë të shkruar dhe të testuar; modelet parashikuese të rrezikut; arkitekturat që kombinojnë kërkimin me gjenerimin mbi korpuse të jashtme mjekësore; nxjerrja e plotë e entiteteve klinike; rezultatet laboratorike jonumerike; dhe gjuhët e tjera përveç shqipes.

---

# 5 METODOLOGJIA

## 5.1 Qasja e zhvillimit të sistemit

Zhvillimi i sistemit ANALYTE është organizuar sipas një qasjeje iterative në të cilën infrastruktura e vlerësimit ndërtohet përpara komponentëve që ajo mat. Ky rend është i qëllimshëm dhe përbën vendim metodologjik: në një punim ku kontributi kryesor është një mekanizëm verifikimi, aftësia për të matur duhet të ekzistojë përpara asaj që matet.

Procesi është ndarë në faza me kritere të përcaktuara përfundimi. Asnjë komponent nuk konsiderohet i përfunduar derisa metrika përkatëse të jetë matur mbi një dataset të versionuar dhe rezultati të jetë i gjurmueshëm deri te konfigurimi që e ka prodhuar.

*Figura 1. Fazat kryesore të zhvillimit të sistemit ANALYTE*

Diagrami paraqet rrjedhën e nëntë fazave kryesore: përcaktimi i shtrirjes dhe shqyrtimi i literaturës, ndërtimi i gjeneruesit të të dhënave sintetike, ndërtimi i infrastrukturës së vlerësimit, zhvillimi i degës laboratorike, zhvillimi i degës së raportit mjekësor, gjenerimi dhe verifikimi me rregulla, trajnimi i klasifikuesit të verifikimit, eksperimentet dhe ablacioni, dhe së fundi zhvillimi i aplikacionit web. Shigjetat tregojnë varësitë ndërmjet fazave, ku fazat e dyta dhe të treta paraprijnë të gjitha fazat e mëpasme sepse prodhojnë përkatësisht të dhënat dhe mjetet matëse.

## 5.2 Arkitektura e sistemit

Arkitektura e ANALYTE ndjek një model të vetëm, i cili zbatohet në mënyrë identike në të dyja degët e sistemit. Burimi përpunohet nga një shtresë deterministe bazimi që prodhon një përfaqësim të strukturuar; ky përfaqësim i jepet modelit gjuhësor, i cili prodhon tekstin; teksti i prodhuar kalon përmes një shtrese verifikimi; dhe vetëm teksti i verifikuar i shfaqet përdoruesit.

*Figura 2. Arkitektura e përgjithshme e sistemit*

Figura paraqet pesë shtresat e sistemit dhe rrjedhën e të dhënave ndërmjet tyre. Shtresa e prezantimit, e realizuar me Next.js dhe React, komunikon përmes një ndërfaqeje REST me shtresën e API-së të ndërtuar me FastAPI. Kjo e fundit delegon përpunimin e dokumenteve te shtresa e orkestrimit, e cila menaxhon punët asinkrone dhe makinën e gjendjeve. Shtresa e bazimit përmban dy degët e përpunimit, ndërsa shtresa e verifikimit vendoset ndërmjet gjenerimit dhe dorëzimit. Të gjitha të dhënat dhe gjurmët e auditimit ruhen në PostgreSQL.

Garancia qendrore e arkitekturës nuk zbatohet përmes udhëzimeve por përmes kontratës së të dhënave. Funksioni që ndërton kërkesën për modelin gjuhësor pranon si parametër vetëm objektin e kontekstit të strukturuar dhe asgjë tjetër. Modeli nuk ka qasje programatike te dokumenti i papërpunuar, te teksti i nxjerrë prej tij, apo te ndonjë burim tjetër informacioni. Ky kufizim është i verifikueshëm nga vetë nënshkrimi i funksionit dhe testohet automatikisht.

*Tabela 1. Teknologjitë kryesore të përdorura në sistem*

| Komponenti | Teknologjia | Roli |
|---|---|---|
| Ndërfaqja e përdoruesit | Next.js, React, TypeScript | Aplikacioni web dhe paraqitja e rezultateve |
| Shërbimi i aplikacionit | Python, FastAPI | API REST, validim, autentikim |
| Baza e të dhënave | PostgreSQL | Ruajtja e të dhënave dhe gjurmëve të auditimit |
| Autentikimi | Argon2id, JWT | Hyrja, seancat e revokueshme dhe kufizimi i provave |
| Nxjerrja e tekstit | PyMuPDF | Leximi i PDF-ve me ruajtje të koordinatave |
| Njohja optike e karaktereve | Tesseract | Përpunimi i dokumenteve të skanuara |
| Terminologjia standarde | Nënbashkësi LOINC | Normalizimi i emrave të analiteve |
| Përpunimi gjuhësor | Fjalorë dhe rregulla leksikore | Segmentimi, zbulimi i termave, i mohimit dhe i pasigurisë |
| Klasifikuesi i verifikimit | XLM-RoBERTa | Zbulimi semantik i përmbajtjes së pambështetur |
| Gjenerimi i gjuhës | Shabllon determinist (adaptori i modelit gjuhësor nuk është zbatuar) | Formulimi i shpjegimeve |
| Përpunimi në sfond | arq, Redis | Punët asinkrone të përpunimit të dokumenteve |
| Paketimi | Docker, docker-compose | Mjedisi i riprodhueshëm i ekzekutimit |
| Testimi | pytest | Teste njësie, integrimi dhe golden-file |

### 5.2.1 Kontrata e të dhënave

Garancia qendrore e arkitekturës nuk zbatohet përmes udhëzimeve në
kërkesën drejtuar modelit gjuhësor por përmes kontratës së të dhënave.
Kjo është arsyeja pse kontrata u shkrua e para, përpara çdo shtrese
tjetër, dhe pse ajo nuk ndryshoi gjatë zbatimit të komponentëve që e
përdorin.

#### Objekti i vetëm i kalimit

Shtresa e gjenerimit ka nënshkrimin:

```python
def build_prompt(ctx: GroundingContext) -> str
```

Nuk ka parametër për dokumentin e papërpunuar, për tekstin e nxjerrë prej
tij, apo për ndonjë burim tjetër. Modeli nuk mund të shohë asgjë që nuk
ndodhet brenda kontekstit, sepse nuk ka nga ku ta marrë. Kufizimi është i
verifikueshëm nga vetë nënshkrimi dhe nuk mbështetet te disiplina e
zhvilluesit.

`GroundingContext` përmban gjetjet e strukturuara, pohimet e nxjerra nga
narrativa, gjendjet e krahasimit të kryqëzuar, zërat e fjalorit për
termat e përmendur dhe listën e termave që sistemi nuk i shpjegon. Ai nuk
përmban të dhëna të pacientit: emri, mosha dhe gjinia mbeten jashtë, dhe
gjinia përdoret vetëm gjatë zgjidhjes së intervalit referent, përpara se
konteksti të formohet (NFR5).

#### Tri vendime që e bëjnë kontratën të zbatueshme

**Objektet janë të pandryshueshme.** Një gjetje e nxjerrë nuk modifikohet
nga shtresat e mëpasme; çdo transformim prodhon objekt të ri. Kjo e mban
gjurmën e auditimit të plotë: dihet gjithmonë cila shtresë e prodhoi një
vlerë (NFR2).

**Vlerat numerike janë `Decimal`.** Verifikimi krahason numrat për barazi
të saktë, prandaj përfaqësimi me presje lëvizëse do të prodhonte shkelje
fantazmë — një numër i mbështetur do të dukej i pambështetur për shkak të
rrumbullakimit binar, dhe shkaku do të ishte pothuajse i pazbulueshëm.

**Gjendjet e pamundura nuk ndërtohen dot.** Validimi i modelit refuzon një
gjetje pa interval referent që mban status tjetër nga *e
painterpretueshme*, një gjetje normale që mban masë ashpërsie, ose një
shkelje të zbuluar nga një rregull që mban vlerë besueshmërie. Politika
SP5 dhe natyra deterministe e rregullave nuk janë kështu kërkesa që
kontrollohen diku më vonë; ato janë kushte ndërtimi.

#### Pastërtia e paketës së domenit

Paketa e modeleve nuk importon asgjë nga pjesa tjetër e sistemit. Kjo nuk
mbetet konventë: një test lexon pemën sintaksore të çdo moduli të saj dhe
dështon nëse ndonjë import del jashtë listës së lejuar.

Arsyeja është e thjeshtë. Kontrata mban formën e të dhënave për pesë
shtresa dhe për gjeneruesin e korpusit njëkohësisht. Sapo ajo të fillojë
të varet nga persistenca ose nga gjenerimi, ndryshimi i atyre shtresave e
prish atë në heshtje, dhe etiketat e korpusit ndalojnë së përputhuri me
daljen e sistemit pa asnjë shenjë të dukshme.

## 5.3 Dega e rezultateve laboratorike

*Figura 3. Tubacioni i përpunimit të rezultateve laboratorike*

### 5.3.1 Rrugëzimi i dokumentit

Faza e parë vendos nëse dokumenti ka shtresë teksti të përdorshme. Pragu
nuk është zero dhe kjo është pjesë e vendimit: një faqe e skanuar mund të
mbajë pak tekst — numër faqeje, vulë të shtypur dixhitalisht, mbetje nga
një njohje optike e mëparshme — dhe po ta pranonim atë si shtresë të
vlefshme, sistemi do të nxirrte disa rreshta dhe do ta quante dokumentin
të lexuar. Prandaj kërkohen njëkohësisht një numër minimal karakteresh
dhe një numër minimal rreshtash për faqe.

Dokumenti që nuk e kalon këtë provë kalon në gjendjen e dështimit të
leximit dhe jo në atë të mungesës së gjetjeve. Dallimi mes "nuk u lexua
dot" dhe "nuk kishte asgjë brenda" është gjendje e veçantë e makinës së
gjendjeve, sepse të dyja prodhojnë dalje bosh dhe vetëm njëra prej tyre
është gabim i sistemit.

### 5.3.2 Rindërtimi i rreshtave

Raportet laboratorike janë tabela, por PDF-ja nuk ruan tabela: ajo ruan
vargje teksti të vendosura në koordinata. Biblioteka e leximit kthen një
rresht për çdo varg të vizatuar veçmas, prandaj "rreshti i tabelës" nuk
ekziston derisa të ndërtohet.

Sistemi i grupon fragmentet sipas vijës bazë me tolerancë të vogël dhe i
rendit horizontalisht brenda grupit. Kjo e heq hamendjen nga segmentimi:
vargu i vetëm "Hb 13,0 g/dL 13,5 - 17,5" kërkon të gjendet ku mbaron emri
dhe ku fillon vlera, ndërsa tre fragmente me kolona të veta nuk kërkojnë
asgjë.

Njohja e një rreshti si rresht të dhënash mbetet e ngushtë me qëllim:
kërkohen të paktën dy fragmente, fragmenti i parë të mos jetë numër, dhe
një nga fragmentet e mëpasme të fillojë me numër. Blloku i pacientit,
titujt e paneleve dhe koka e kolonave bien jashtë kësaj prove.

### 5.3.3 Normalizimi

Emrat e analiteve hartëzohen te kodet LOINC me përputhje të saktë pas
normalizimit; përputhja e afërt refuzohet. Arsyeja jepet në vendimin
arkitekturor 0006: "Kaliumi" dhe "Kalciumi" ndryshojnë për një shkronjë
dhe kanë intervale krejt të ndryshme, dhe ngatërrimi i tyre do të hynte i
heshtur në një shpjegim për pacientin.

Numrat lexohen si me presje ashtu edhe me pikë dhjetore, por ndarësi i
mijësheve refuzohet. Kjo është zgjedhje e vetëdijshme: refuzimi është
gabim i dukshëm, ndërsa hamendja është gabim i heshtur me faktor një mijë.

Njësitë kthehen në njësinë kanonike të analitit. Faktori varet nga
substanca kudo ku në të hyn masa molare, prandaj kthimi merr analitin dhe
jo vetëm dy emra njësish. Vlera në njësi që nuk njihet nuk kthehet dhe as
nuk pranohet ashtu siç është: ajo nuk krahasohet dot me asnjë interval,
prandaj gjetja mbetet e painterpretueshme.

*Tabela 3. Faktorët e konvertimit të njësive*

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

### 5.3.4 Zgjidhja e intervalit referent

Përparësia është e përcaktuar. Intervali i shtypur në dokument fiton
gjithmonë, sepse laboratori e di me çfarë metode ka matur dhe tabela jonë
jo. Kur ai mungon, merret intervali i tabelës së brendshme, i përputhur
sipas analitit dhe gjinisë. Kur asnjëra nuk jep përgjigje, gjetja mbetet
pa interval.

Gjinia lexohet nga blloku i kokës së dokumentit. Kur ajo nuk gjendet dhe
analiti ka kufij të ndryshëm sipas saj, intervali mbetet i pazgjidhur:
zgjedhja e njërit prej dy intervaleve do të ishte short i maskuar si
mbulim.

Burimi i intervalit regjistrohet për çdo gjetje dhe raportohet veçmas në
rezultate. Pa të, një gabim klasifikimi nuk mund t'i atribuohet as
leximit të intervalit nga faqja, as zgjedhjes së tij nga tabela.

### 5.3.5 Klasifikimi dhe refuzimi i interpretimit

Klasifikimi është rregull determinist mbi vlerën e normalizuar dhe
kufijtë e zgjidhur, me gjashtë statuse. Masa e ashpërsisë llogaritet si
largësia nga kufiri i kaluar pjesëtuar me gjerësinë e intervalit. Për
intervale njëanëshe, të zakonshme te lipidet, gjerësia nuk ekziston dhe
shkalla bëhet vetë kufiri i kaluar; ky dallim është i dokumentuar te
funksioni, sepse ashpërsitë e dy llojeve nuk janë të krahasueshme mes
tyre.

Vlera pa interval mbahet dhe nuk hidhet. Pacienti e ka atë të shtypur në
dokument dhe ka të drejtë ta shohë të renditur, me shënimin se nuk
interpretohet. Heqja e saj do të fshihte një matje që laboratori e bëri
vërtet — mungesë e heshtur në vend të një refuzimi të shprehur.

*Tabela 2. Paneli i analiteve dhe hartëzimi me kodet LOINC (ekstrakt)*

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

*Ekstrakt i 10 analiteve të para; paneli i plotë është te Shtojca B (Tabela B.1).*

Tabela e brendshme përmban 38 analite me interval referent dhe njeh me
emër edhe 8 të tjera për të cilat interval nuk ekziston. Këto të fundit
nuk janë mangësi e tabelës por materiali me të cilin matet politika SP5.

### 5.3.6 Rreshtat e hedhur

Çdo rresht që njihet si të dhëna por nuk prodhon gjetje ruhet bashkë me
arsyen: analit i panjohur, vlerë e palexueshme, dublikatë. Kjo listë nuk
hyn në kontekst — ajo është material auditimi dhe analize gabimesh.

Pa të, një saktësi e ulët e nxjerrjes nuk do të tregonte nëse faji është
i segmentimit, i hartës së emrave apo i njësive, dhe analiza e gabimeve e
Kapitullit 7 do të mbështetej te ndjesia.

### 5.3.7 Gjendja e zbatimit dhe matja

Kanali dixhital u mat mbi 332 dokumente dixhitale të korpusit sintetik (E1). Saktësia, mbulimi dhe F1 dolën 1.000 për të katër fushat — analiti, vlera, njësia dhe intervali. Saktësia e klasifikimit mbi të njëjtat dokumente është 1.000.

Ky rezultat nuk duhet lexuar si dëshmi se nxjerrja është e zgjidhur. Ai
thotë se tubacioni është i lidhur saktë mbi një korpus që nuk dallon:
gjeneruesi vizaton tekst të pastër në koordinata të njohura dhe nxjerrësi
lexon koordinata. Mungojnë rreziqet e një dokumenti real — emrat e
mbështjellë në dy rreshta, shenjat e fusnotave pranë vlerës, qelizat e
bashkuara, kolonat e komenteve dhe analitet jashtë tabelës. Për më tepër,
nxjerrësi dhe gjeneruesi ndajnë tabelën e kthimit të njësive, çka e bën
fushën e intervalit pjesërisht tautologjike te rreshtat me njësi
alternative.

Matja që do të kishte vlerë dalluese është ajo mbi kanalin e skanuar dhe
mbi dokumente reale. E dyta pret miratimin etik; e para u bë me Tesseract 5
(ADR 0012), me konfigurim të zgjedhur mbi një korpus të veçantë akordimi.
Mbi 168 dokumentet e skanuara të korpusit të vlerësimit
(`gen-1.0/s42/n500/37d8b080`), F1 doli 0.670:

| Fusha | Saktësia | Mbulimi | F1 |
|---|---|---|---|
| Analiti | 0.996 | 0.697 | 0.820 |
| Vlera | 0.947 | 0.663 | 0.780 |
| Njësia | 0.781 | 0.547 | 0.643 |
| Intervali | 0.533 | 0.373 | 0.438 |

Numri që ka rëndësi nuk është F1 por saktësia e vlerës. Nga 2 370 vlera të
nxjerra nga dokumentet e skanuara, 125 ishin të gabuara dhe u pranuan — më
shpesh sepse OCR-ja humbi ndarësin dhjetor dhe "15,7" u lexua "157". Në
matjen e parë ishin 271; gjysma tjetër — intervale të lexuara si vlerë me
njësi numerike — refuzohen tani nga nxjerrësi (ADR 0012). Një
vlerë e humbur nuk interpretohet; një vlerë e gabuar interpretohet me
siguri, dhe asgjë më poshtë në rrjedhë nuk e vë re. Kontrolli i
besueshmërisë që do ta ndalte kërkon kufij fiziologjikë me burim për çdo
analit dhe mbetet vendim i hapur. [REFERENCË — plotësohet]

E3 me OCR mbi tërë korpusin: saktësia e statusit 0.881. Pjesa më e madhe e gabimeve janë të sigurta — vlerat u bënë "pa interval" sepse intervali nuk u lexua, dhe SP5 refuzoi interpretimin. Por 62 vlera morën një status të interpretuar dhe të gabuar, ndër to 11 të shënuara kritike të larta pa qenë të tilla (9 normale, 1 e lartë dhe 1 kritike e ulët). Këta janë rastet që kontrolli i besueshmërisë do t'i ndalte.

Vendimi për të mos e vështirësuar korpusin sintetik, dhe arsyeja e tij,
jepen te seksioni 5.8.

### 5.3.8 Kombinimet ndërmjet analiteve

Rregullat e kombinimit janë të shkruara me dorë në një tabelë burimore
(Tabela B.3, Shtojca B), një rresht për rregull: një listë kushtesh — analiti dhe
drejtimi i statusit të tij — që duhet të plotësohen njëkohësisht, dhe
burimi i rregullit. Njëmbëdhjetë rregulla mbulojnë kombinime të njohura
gjerësisht, si hemoglobina e ulët me ferritinë të ulët apo hormoni
stimulues i tiroides i lartë me tiroksinë të lirë të ulët.
[REFERENCË — plotësohet]

Rregulli nuk emërton gjendjen. Emri i një kombinimi është diagnozë, dhe
SP1 e ndalon pavarësisht nga burimi; dalja thotë vetëm se këto vlera,
bashkë, kërkojnë vlerësim nga profesionisti shëndetësor. Tri veti e
kufizojnë rregullin më tej. Vlera kritike numërohet sipas drejtimit të
saj, që rregulli të mos heshtë pikërisht te vlerat më të rënda. Vlera pa
interval referent nuk merr pjesë, sepse përndryshe rregulli do ta
interpretonte tërthorazi atë që SP5 ndalon të interpretohet. Dhe një
analit që shfaqet dy herë në dokument nuk zgjidhet me hamendje: rregulli
që e kërkon nuk ndizet.

Kombinimet hyjnë në `GroundingContext` si vëzhgime që tregojnë gjetjet që
i formuan, prandaj edhe modeli gjuhësor i sheh vetëm si pjesë të
kontekstit. Ashtu si klasifikimi, ato janë rregull i dhënë (ADR 0003): e
vërteta bazë e korpusit i llogarit me të njëjtin funksion.

Korpusi prodhon vlera të pavarura për çdo analit, prandaj kombinimet aty
janë të rralla — rreth 15 në 400 dokumente. Rregullat testohen mbi gjetje
të ndërtuara me dorë, jo mbi korpusin, dhe asnjë PK nuk mat saktësinë e
tyre klinike; ajo varet nga burimi i secilit rregull dhe nga shqyrtimi i
mentorit.

*[Figura — plotësohet: shembull i një kombinimi nga gjetjet te fjalia e
daljes]*

## 5.4 Dega e raportit mjekësor

*Figura 4. Tubacioni i përpunimit të raportit mjekësor*

Dega e dytë merret me tekstin e lirë të mjekut. Ndryshe nga vlerat
laboratorike, ku e vërteta është numër dhe krahasimi është i saktë, këtu
e vërteta është kuptimi i një fjalie — dhe pikërisht ai kuptim është ai
që humbet më lehtë kur teksti thjeshtohet.

### 5.4.1 Gjetja e tekstit dhe ndarja në fjali

Narrativa gjendet në dokument nën titullin e vet dhe mbyllet te
nënshkrimi i mjekut. Rreshtat e mbështjellë bashkohen sërish me një
hapësirë të vetme — veprimi i kundërt i atij që i mbështolli — që teksti
i rindërtuar të jetë varg për varg i njëjtë me atë që u shtyp. Kjo nuk
është kozmetikë: pozicionet e pohimeve maten mbi këtë varg dhe duhet të
mbeten të krahasueshme me anotimin manual.

Ndarja në fjali është e thjeshtë me qëllim. Narrativa e raporteve është
prozë e shkurtër pa shkurtime me pikë, dhe një ndarës më i ndërlikuar do
të fshihte se nga vjen secili pohim.

### 5.4.2 Njohja e termave

Kërkimi në tabelën terminologjike është rregull: termi gjendet ose nuk
gjendet. Përputhja duron lakimin e shqipes me përputhje parashtese mbi
çdo fjalë të termit, prandaj "anemisë", "anemia" dhe "anemi" janë i
njëjti zë, dhe "intervalin referent" gjendet si "interval referent".
Toleranca vlen për çdo fjalë e jo vetëm për të fundit, sepse shqipja e
lakon edhe kryefjalën e një termi dyfjalësh.

Termat që nuk gjenden në tabelë njihen me morfologji: prapashtesat
mjekësore si -ozë, -emi, -peni dhe -uri. Kjo është heuristikë dhe jo
rregull, dhe kjo ndarje ka pasojë metodologjike: heuristika nuk ndahet me
gjeneruesin e korpusit. E vërteta bazë e termave të pashpjeguar vjen nga
ajo që gjeneruesi vendosi të fusë; po ta nxirrnim me të njëjtën
heuristikë, sistemi do të krahasohej me vetveten dhe SP6 do të dukej
gjithmonë i plotësuar.

Heuristika ka çmimin e vet dhe ai u pa gjatë zbatimit: prapashtesa -itet
kapte foljen "paraqitet" dhe prodhonte një term të pashpjeguar në
pothuajse çdo dokument. Ajo u hoq, dhe fjalët e zakonshme që mbarojnë si
terma mjekësorë mbahen në një listë të shkurtër përjashtimesh. Kur ajo
listë të rritet përtej disa dhjetësh, kjo do të thotë se qasja
morfologjike ka dalë nga fuqia e vet.

*Tabela 4. Ekstrakt nga tabela terminologjike shqip*

| Termi | Shpjegimi | Kategoria | Burimi |
|---|---|---|---|
| anemi | nivel i ulët i hemoglobinës në gjak | gjendje | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| eritropoezë | prodhimi i qelizave të kuqe të gjakut në palcën kockore | proces | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| leukocitozë | numër i rritur i qelizave të bardha të gjakut | gjendje | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| leukopeni | numër i ulët i qelizave të bardha të gjakut | gjendje | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| trombocitopeni | numër i ulët i pllakëzave të gjakut | gjendje | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| trombocitozë | numër i rritur i pllakëzave të gjakut | gjendje | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hiperglicemi | nivel i rritur i sheqerit në gjak | gjendje | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hipoglicemi | nivel i ulët i sheqerit në gjak | gjendje | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hiperkalemi | nivel i rritur i kaliumit në gjak | gjendje | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hipokalemi | nivel i ulët i kaliumit në gjak | gjendje | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |

*Ekstrakt i 10 zërave të parë; tabela e plotë është te Shtojca A (Tabela A.1).*

Tabela përmban 82 zëra. Kolona e burimit mbetet vendmbajtëse dhe duhet
plotësuar përpara dorëzimit: pa referencë të verifikueshme, tabela bëhet
vetë burim informacioni të paverifikuar — pikërisht ajo që SP6 synon të
pengojë.

### 5.4.3 Mohimi dhe pasiguria

Zbulimi i mohimit ndjek frymën e NegEx-it: një listë e shkurtër shenjash
dhe një fushë veprimi që mbyllet te kundërvënia. Tri hollësi e bëjnë
problemin real.

**Pseudo-mohimi kontrollohet i pari.** "Nuk përjashtohet sideropeni"
përmban shenjën "nuk" dhe nuk mohon asgjë — ajo pohon me rezervë. Po ta
lexonim si mohim, do të përmbysnim mjekun pikërisht ashtu si druhet
rregulli R5 se do ta bëjë modeli gjuhësor.

**Polariteti dhe drejtimi mbahen të ndarë.** "Nuk rezulton mbi intervalin
referent" ka drejtim *i rritur* dhe polaritet *i mohuar*. Bashkimi i tyre
në një fushë do ta bënte të pamundur dallimin mes "është i ulët" dhe "nuk
është i lartë", të cilat nuk janë e njëjta gjë: e dyta përputhet me çdo
status që nuk është i rritur.

**Gabimi i parazgjedhur është pohimi.** Një mohim i humbur prodhon tekst
më të fortë se burimi dhe kapet nga verifikimi; një mohim i shpikur
prodhon tekst që kundërshton burimin pa lënë gjurmë se nga erdhi.

Pasiguria zbulohet njësoj, me shenja të ndara në katër grupe: foljet
modale, ndajfoljet, foljet e dukjes dhe mohimi i përjashtimit. Ky i fundit
është njëkohësisht pseudo-mohim, dhe të dy modulet e trajtojnë njësoj:
pohim, por me rezervë.

Një kufizim mbetet i hapur dhe është fiksuar me test që ndryshimi i tij
të jetë i vetëdijshëm: mohimi në gjymtyrën e dytë të fjalisë lexohet si
pohim. Zgjidhja e duhur është ndarja e fjalisë në dy pohime, jo zbutja e
fushës së veprimit.

### 5.4.4 Pohimet dhe krahasimi i kryqëzuar

Çdo fjali që pretendon diçka kthehet në një pohim me llojin e vet:
gjetje, rekomandim ose përmendje termi. Fjalitë që nuk pretendojnë asgjë
nuk prodhojnë pohim; një pohim i shpikur do të kërkonte më vonë
mbështetje që nuk ekziston.

Fjalia me term të panjohur prodhon pohim njësoj si ajo me term të njohur.
Kjo është ana e dytë e SP6: sistemi duhet ta vërejë fjalinë për ta shënuar
termin si të pashpjeguar. Po ta linim pa pohim, "nuk e shpjegojmë" do të
bëhej "nuk e pamë fare" — dy gjendje që duken njësoj në dalje dhe janë
krejt të ndryshme në auditim.

Krahasimi i kryqëzuar prodhon një gjendje për analit. Rregulli i
përputhjes është përkufizim dhe jo hamendje, prandaj i njëjti funksion
përdoret nga gjeneruesi për të ndërtuar të vërtetën bazë; PK4 mat
nxjerrjen e gjetjeve dhe të pohimeve, jo rregullin.

### 5.4.5 Matja

PK4 u mat mbi korpusin sintetik me dy vlera që duhen raportuar të dyja:

- **1.000** mbi dokumentet dixhitale, me mbulim të plotë për të katër
  gjendjet;
- **0.656** mbi tërë korpusin pa OCR, dhe **0.863** me OCR
  (`gen-1.0/s42/n500/37d8b080`, 500 dokumente, 168 të skanuar).

I gjithë ndryshimi është kanali i skanuar. Pa njohje optike ato dokumente
nuk lexohen fare dhe çdo gjendje e tyre llogaritet si e munguar; me OCR
lexohen pjesërisht. Një vlerë e mëparshme prej 0.563 u raportua në një
draft më të hershëm pa u shënuar korpusi mbi të cilin u mat, prandaj nuk
riprodhohet dhe nuk përdoret.

Mbi gjysmën dixhitale, të gjitha pohimet e burimit u rikthyen me
polaritet, siguri dhe lloj të saktë, dhe termat e pashpjeguar u
identifikuan saktësisht në çdo dokument.

Vlen i njëjti kufizim si te Dega A, dhe këtu ai peshon më shumë: narrativa
sintetike ndërtohet nga fjali të shkruara me dorë, dhe detektorët u
shkruan duke i pasur ato parasysh. Prandaj testet e mohimit dhe të
pasigurisë përdorin fjali të tjera, të shkruara posaçërisht si provë —
një provë mbi shabllonet e gjeneruesit do të tregonte vetëm se kodi
kujton veten. Prova e vërtetë mbetet teksti i mjekëve realë.

## 5.5 Shtresa e verifikimit

*Figura 5. Arkitektura e shtresës së verifikimit*

Shtresa e verifikimit është kontributi qendror i punimit. Ajo vepron mbi tekstin e gjeneruar nga modeli gjuhësor dhe mbi kontekstin e strukturuar që i është dhënë atij, dhe vendos nëse teksti mund t'i shfaqet përdoruesit.

Verifikimi funksionon në dy mënyra, që i përgjigjen dy degëve të sistemit.

Për të dhënat laboratorike, verifikimi është i saktë. Çdo numër që shfaqet në tekstin e gjeneruar duhet të përputhet me një vlerë, me një kufi intervali ose me një datë të pranishme në gjetjet e strukturuara, brenda një tolerance të përcaktuar rrumbullakimi; një numër i papërputhur përbën shkelje. Çdo analit i përmendur duhet të ekzistojë në gjetjet; përmendja e një analiti të pamatur përbën shkelje. Çdo pohim mbi drejtimin duhet të përputhet me statusin e strukturuar të analitit përkatës. Dhe çdo gjetje e klasifikuar si kritike duhet të shfaqet diku në tekstin përfundimtar.

Për tekstin narrativ, verifikimi është semantik. Polariteti i çdo pohimi burimor duhet të ruhet në dalje; kthimi i një mohimi përbën shkeljen më të rëndë të mundshme. Niveli i sigurisë i shprehur në burim duhet gjithashtu të ruhet. Asnjë gjetje e re nuk lejohet të shfaqet. Çdo rekomandim i pranishëm në burim duhet të mbijetojë në dalje. Dhe çdo term i shpjeguar duhet të gjendet në tabelën terminologjike.

*Tabela 5. Katalogu i rregullave të verifikimit*

| Kodi | Dega | Kontrolli |
|---|---|---|
| R1 | A | Përputhja numerike me tolerancë të përcaktuar |
| R2 | A | Ekzistenca e analitit në gjetjet e strukturuara |
| R3 | A | Përputhja e drejtimit me statusin |
| R4 | A | Mbulimi i gjetjeve kritike |
| R5 | B | Ruajtja e polaritetit |
| R6 | B | Ruajtja e nivelit të sigurisë |
| R7 | B | Mosshfaqja e gjetjeve të reja |
| R8 | B | Mbijetesa e rekomandimeve |
| R9 | B | Bazueshmëria e shpjegimeve terminologjike |

Katalogu i zbatuar (versioni `r1.3`) përmban edhe një rregull politike, SP1–SP3, që refuzon pohimet diagnostike, të trajtimit dhe prognostike; versioni i katalogut regjistrohet te çdo rezultat verifikimi. Katalogu i plotë me një shembull për çdo rregull është te Shtojca C.

Renditja e ekzekutimit është e përcaktuar: rregullat deterministe ekzekutohen të parat dhe kanë përparësi kudo ku verifikimi është mekanikisht i vendosshëm, ndërsa klasifikuesi ekzekutohet i dyti dhe mbulon zhvendosjet semantike që rregullat nuk i kapin. Vendimi përfundimtar është bashkimi i flamujve nga të dyja qasjet.

## 5.6 Trajtimi i dështimit

*Figura 6. Makina e gjendjeve e përpunimit të dokumentit*

![Figura 6](figures/figura_06_makina_e_gjendjeve.png)

Sjellja e sistemit në rast shkeljeje është e përcaktuar si makinë gjendjesh dhe çdo kalim regjistrohet në gjurmën e auditimit.

Kur verifikimi zbulon një ose më shumë shkelje, sistemi rigjeneron tekstin një herë, duke e përfshirë shprehimisht përshkrimin e shkeljes në kërkesën drejtuar modelit. Teksti i ri verifikohet përsëri. Nëse edhe ky dështon, sistemi nuk bën përpjekje të mëtejshme por kalon te një shpjegim i gjeneruar nga një shabllon determinist, i cili ndërtohet drejtpërdrejt nga gjetjet e strukturuara pa përfshirjen e modelit gjuhësor. Ky shpjegim është më i thatë gjuhësisht por i garantuar i saktë.

Makina e gjendjeve përmban gjithashtu një gjendje të veçantë për dokumentet që përpunohen me sukses por nuk japin asnjë gjetje. Pa këtë gjendje, një dokument i palexueshëm do të prodhonte një dalje bosh pa asnjë shpjegim për përdoruesin, gjë që përbën dështim të heshtur.

Parimi që përshkon të gjithë këtë mekanizëm është se tekst i paverifikuar nuk i shfaqet asnjëherë përdoruesit, në asnjë rrethanë.

## 5.7 Komponenti i mësimit makinerik

Verifikimi semantik formulohet si detyrë klasifikimi kontekstual. Jepet premisa, e cila është konteksti i nxjerrë nga burimi, dhe hipoteza, e cila është një fjali e vetme nga teksti i gjeneruar, dhe kërkohet klasifikimi i marrëdhënies si e mbështetur, e kundërshtuar ose e pambështetur.

Ky formulim është i njëjtë me atë të natural language inference, i cili është përdorur me sukses për zbulimin e mospërputhjeve faktike [4].

Modeli bazë i zgjedhur është XLM-RoBERTa. Zgjedhja diktohet nga konteksti gjuhësor: modelet klinike të paratrajnuara mbulojnë vetëm anglishten, ndërsa një enkoder shumëgjuhësh i përgjithshëm mbulon edhe shqipen. Kjo zgjedhje justifikohet gjithashtu eksperimentalisht përmes krahasimit me alternativat.

*Figura 10. Ndërtimi i korpusit të korruptuar për trajnimin e klasifikuesit*

Të dhënat e trajnimit prodhohen automatikisht. Duke nisur nga një dalje e verifikuar si e saktë, futet saktësisht një defekt i kontrolluar nga shtatë lloje të mundshme: ndryshim i një numri, përmendje e një analiti që nuk është matur, kthim i drejtimit të një gjetjeje, kthim i mohimit, heqje e një shprehjeje pasigurie, shtim i një gjetjeje të shpikur, ose fshirje e një rekomandimi (llojet `ungrounded_number`, `ungrounded_analyte`, `direction_mismatch`, `polarity_flip`, `hedge_removed`, `fabricated_finding` dhe `omitted_recommendation`). Etiketa caktohet automatikisht nga vetë procesi i korruptimit, gjë që eliminon nevojën për anotim manual dhe garanton etiketim të përsosur.

Krahasimi eksperimental përfshin tri qasje mbi të njëjtat mostra testuese, por jo mbi të njëjtën informacion: rregullat deterministe të përshkruara në nënkapitullin 5.5 shohin kontekstin e plotë të strukturuar; klasifikuesi i finetunuar sheh vetëm fjalinë (një variant i dytë merr edhe një përmbledhje të shkurtër të kontekstit); dhe një model i madh gjuhësor i përdorur si gjykatës do të merrte kontekstin dhe një rubrikë vlerësimi të përcaktuar rreptësisht. Prandaj dallimet mes tyre janë dallime të hyrjes po aq sa të metodës (ADR 0009). Klasifikuesi vlerësohet në dy pika pune, të dyja të zgjedhura mbi validimin dhe vetëm atje: ajo me macro F1 më të lartë mbi llojet e defektit, dhe ajo me macro F1 më të lartë ndër pragjet që bllokojnë jo më shumë se 5% të teksteve të pastra të validimit.

## 5.8 Strategjia e të dhënave

### 5.8.1 Korpusi sintetik

*Figura 9. Procesi i gjenerimit të korpusit sintetik*

Korpusi sintetik është burimi parësor i vlerësimit. Ai prodhon
njëkohësisht dy gjëra që mbahen rreptësisht të ndara: dokumentin PDF që
sheh sistemi, dhe skedarin me të vërtetën bazë që sistemi nuk e sheh
kurrë.

#### Rendi i veprimeve

Rendi me të cilin ndërtohet një dokument nuk është i rastësishëm.
Zgjidhet i pari statusi i synuar, pastaj kampionohet një vlerë që e
plotëson atë, pastaj vendoset mënyra e shtypjes — njësia, prania e
intervalit, presja dhjetore — dhe vetëm në fund rillogaritet statusi i
vërtetë mbi vlerën dhe intervalin ashtu si dalin të shtypura.

Nëse do të ruhej statusi i synuar, një dokument që shtyp interval paksa
të ndryshëm nga tabela e brendshme do të mbante etiketë të rreme. Kjo
është forma më e rrezikshme e gabimit në një korpus me etiketa: ai nuk
dështon, ai mat diçka tjetër nga ajo që mendon se mat.

#### Variacioni i shtypjes

Ndryshimet mes laboratorëve janë pjesë e korpusit dhe jo zbukurim: presje
apo pikë dhjetore, interval i shtypur për të gjitha rreshtat, për disa
ose për asnjë, flamur `H`/`L`, shigjetë apo yll, njësi tradicionale apo
SI. Tri formate faqeje ndryshojnë gjerësinë e kolonave, vendosjen e
njësisë në qelizë të veçantë ose ngjitur pas vlerës, dhe praninë e vijave
ndarëse.

Intervali i shtypur ndryshon paksa nga tabela e brendshme në rreth një të
dhjetën e rreshtave. Pa këtë, nxjerrja e intervalit nga dokumenti nuk do
të matej kurrë vërtet: sistemi do të dilte i saktë edhe po ta injoronte
fare atë që shtypet.

#### Narrativa

Teksti i mjekut ndërtohet nga fjali të plota të shkruara me dorë dhe jo
nga fragmente të bashkuara. Shqipja ka rasa dhe përshtatje numri; një
shabllon i tipit "Vlerat e {emri} janë të rritura" prodhon trajtë të
gabuar për gjysmën e analiteve. Prandaj çdo shabllon ekziston në njëjës
dhe në shumës, dhe emri i analitit qëndron gjithmonë kryefjalë në emërore.

Fjalitë me terma mjekësorë janë të kushtëzuara nga matja: një narrativë
që përmend leukocitozë kur leukocitet janë normale do të ishte korpus i
pakujdesshëm, jo korpus i vështirë.

Numrat nuk hyjnë në narrativë — shkruhet "pas tre muajsh" dhe jo "pas 3
muajsh". Një vlerë e shtypur në tekstin e mjekut do të zgjeronte heshtazi
bashkësinë e numrave që teksti i gjeneruar mund t'i përmendë, dhe do ta
zbuste rregullin R1 pikërisht aty ku ai duhet të jetë i ashpër.

#### Simulimi i skanimit

Rreth 35% e dokumenteve kthehen në fotografi letre: anim, turbullim,
zhurmë, njolla dhe artefakte kompresimi, pa asnjë shtresë teksti.

Dokumenti i skanuar nuk vizatohet ndryshe. Ai vizatohet njësoj dhe pastaj
prishet, prandaj përmbajtja e të dy kanaleve është identike dhe çdo
ndryshim në rezultatet e PK1 dhe PK2 i atribuohet kanalit e jo tekstit.
Kutitë kufizuese rrotullohen bashkë me faqen; përndryshe e vërteta bazë
do të tregonte vende ku nuk ka më asgjë.

#### Përsëritshmëria

Dy ekzekutime me të njëjtën farë japin bajt për bajt të njëjtët skedarë,
PDF-të e përfshira. Kjo kërkonte tri gjëra: asnjë identifikues nga burim
i rastësishëm i sistemit, asnjë vulë kohore në dalje, dhe çrrënjosjen e
vulës së kohës që biblioteka e vizatimit e shkruan në PDF si
parazgjedhje.

Çdo dokument merr farën e vet të prejardhur nga fara e korpusit dhe
indeksi i tij. Prandaj dokumenti i njëqindtë është i njëjti pavarësisht
nëse u kërkuan njëqind e një apo pesëqind dokumente, dhe gjenerimi është
i ndashëm në procese.

Manifesti ruan shumat kontrolluese të tabelave burimore. Dy korpuse me të
njëjtën farë por me tabelë analitesh të ndryshme nuk kanë të njëjtin
version dhe nuk ngatërrohen dot në asnjë tabelë rezultatesh.

#### Çfarë mat dhe çfarë nuk mat ky korpus

Korpusi mbulon me qëllim rastet që punimi pretendon se i trajton — vlera
kritike, vlera pa interval referent, pohime të mohuara, pasiguri të
shprehur, rekomandime, terma jashtë tabelës dhe të katër gjendjet e
krahasimit të kryqëzuar — dhe ky mbulim kontrollohet me test.

Ai nuk mat vështirësinë e nxjerrjes nga dokumente reale. Kjo duhet thënë
hapur dhe jo si formulë modestie: kanali dixhital sintetik nuk dallon,
sepse gjeneruesi vizaton tekst të pastër në koordinata të njohura dhe
nxjerrësi lexon koordinata. Vlefshmëria e jashtme varet nga eksperimenti
E13 mbi dokumente reale, dhe nëse ai nuk realizohet, kufizimi mbetet i
shprehur në përfundime.

Korpusi nuk u vështirësua për ta mbyllur këtë boshllëk. Emra të
mbështjellë në dy rreshta, shenja fusnotash dhe kolona komentesh mund t'i
shtoheshin gjeneruesit, por atëherë i njëjti autor do ta projektonte
vështirësinë dhe zgjidhjen e saj, dhe një rezultat i lartë mbi të nuk do
të provonte asgjë përtej asaj që autori priste. Kanali i skanuar është
përjashtimi: zhurma e skanimit prodhohet nga një proces i rastësishëm dhe
jo nga një listë rreziqesh, prandaj E2 është matja e vetme brenda
korpusit që e sfidon nxjerrësin.

Shkalla e jonormalitetit është rreth 20% për analit, më e lartë se te një
depistim rutinë. Pasurimi është i qëllimshëm — një korpus ku pothuajse çdo
vlerë është normale nuk ka mbi çfarë të matë as klasifikimin, as
përshkallëzimin kritik — dhe raportohet si i tillë. Ai nuk duhet
ngatërruar me prevalencë.

### 5.8.2 Të dhënat reale

Nëse miratimi etik jepet, një grup prej tridhjetë deri në pesëdhjetë dokumentesh reale të anonimizuara përdoret ekskluzivisht si validim i jashtëm, për të kontrolluar nëse performanca e matur mbi dokumentet sintetike transferohet te faqosje reale të papara.

Për këtë grup, udhëzimet e anotimit përcaktohen paraprakisht me shkrim, një nënbashkësi anotohet në mënyrë të pavarur nga një anotues i dytë, dhe pajtueshmëria ndër-anotuese raportohet përmes koeficientit Cohen's kappa.

Nëse miratimi etik nuk jepet ose vonohet përtej afatit, punimi vazhdon mbi korpusin sintetik dhe kufizimi deklarohet shprehimisht në kapitullin e diskutimit.

## 5.9 Organizimi i komponentëve të aplikacionit

*Figura 8. Struktura modulare e aplikacionit*

![Figura 8](figures/figura_08_struktura_modulare.png)

Aplikacioni është organizuar në module me përgjegjësi të ndara qartë. Moduli i domenit përmban modelet e të dhënave dhe nuk varet nga asnjë modul tjetër, gjë që e mban kontratën e të dhënave të qëndrueshme ndërsa pjesa tjetër e sistemit evoluon. Moduli i ngarkimit merret me leximin e dokumenteve dhe njohjen optike. Moduli i bazimit përmban të dyja degët e përpunimit. Moduli i gjenerimit përmban përshtatësin e modelit gjuhësor dhe kërkesat e versionuara. Moduli i verifikimit përmban rregullat dhe klasifikuesin. Moduli i orkestrimit menaxhon makinën e gjendjeve dhe punët asinkrone. Moduli i qëndrueshmërisë menaxhon bazën e të dhënave, ndërsa moduli i auditimit regjistron çdo hap të përpunimit.

Kjo ndarje u kontrollua kundrejt importeve të vërteta. Figura 8 është matricë varësish e ndërtuar nga kodi (`scripts/build_figures.py`), dhe tregon se moduli i domenit nuk importon asnjë modul tjetër të aplikacionit, siç pretendohet më sipër. Ajo tregon edhe një devijim: ekziston një varësi rrethore në nivel paketash mes auditimit, orkestrimit dhe qëndrueshmërisë (`audit.logger` importon `orchestration.states`, `persistence.repository` importon `orchestration.process`, dhe `orchestration.tasks` importon të dyja). Nuk ka cikël në nivel moduli, por ndarja e pastër e përgjegjësive nuk është plotësisht e vërtetë; zgjidhja është zhvendosja e tri llojeve të përbashkëta në paketën e domenit, dhe nuk është bërë.

Ndarja e gjeneruesit të të dhënave dhe e infrastrukturës së vlerësimit në module të veçanta jashtë aplikacionit kryesor pasqyron faktin se ato i shërbejnë kërkimit dhe jo produktit.

## 5.10 Struktura e databazës

*Figura 7. Entity Relationship Diagram (ERD) i databazës*

![Figura 7](figures/figura_07_erd.png)

Baza e të dhënave është projektuar në formë të normalizuar dhe pasqyron rrjedhën e përpunimit. Tabela e përdoruesve lidhet me tabelën e dokumenteve, e cila nga ana e saj lidhet me tabelën e punëve të përpunimit që regjistron gjendjen aktuale të çdo dokumenti në makinën e gjendjeve.

Tabela e gjetjeve laboratorike ruan për çdo analit vlerën e papërpunuar dhe atë të normalizuar, njësinë origjinale dhe atë kanonike, intervalin referent bashkë me burimin e tij, statusin, ashpërsinë dhe pozicionin në dokument. Ruajtja e pozicionit lejon theksimin e zonës burimore në ndërfaqen e përdoruesit.

Terminologjia dhe intervalet referente nuk ruhen në bazë: `resources/` është burimi i vetëm, dhe një kopje në bazë do të largohej prej tij. Ruhet vetëm fjalori i secilit dokument, i plotë, që shpjegimi që pa pacienti të mbetet i gjurmueshëm edhe kur tabela ndryshon, bashkë me termat e pashpjeguar dhe kombinimet e vërejtura. Tabela e pohimeve ruan pohimet e nxjerra nga raporti narrativ, ndërsa tabela e krahasimeve të kryqëzuara lidh pohimet me gjetjet përkatëse.

Tabela e shpjegimeve ruan veçmas daljen e papërpunuar të modelit dhe daljen përfundimtare të shfaqur, bashkë me versionin e kërkesës, modelin e përdorur dhe parametrat e tij. Diferenca ndërmjet dy fushave përbën gjurmën që dëshmon se asnjë tekst i paverifikuar nuk është shfaqur.

Tabela e rezultateve të verifikimit dhe ajo e shkeljeve ruajnë vendimet e shtresës së verifikimit. Kolona që tregon nëse një shkelje është zbuluar nga rregullat apo nga klasifikuesi është burimi i drejtpërdrejtë i të dhënave për krahasimin e tre qasjeve.

Prejardhja e eksperimenteve nuk ruhet në bazën e aplikacionit. Eksperimentet ekzekutohen nga harness-i në linjë komande, dhe çdo rezultat shkruhet si skedar `result.json` me farën e korpusit, versionin e tij, git sha dhe gjendjen e pemës së punës (seksioni 5.11.2.4), që të jetë i rindërtueshëm pa ndërmjetës. Tri tabela të tjera i shërbejnë hyrjes: `auth_sessions`, `refresh_tokens` dhe `login_failures`; e fundit mban email-in dhe adresën IP vetëm si hash me çelës (ADR 0014). Skema e plotë është te Shtojca G.

## 5.11 Metodologjia e vlerësimit

*Figura 11. Tubacioni i vlerësimit dhe gjurmueshmëria e eksperimenteve*

![Figura 11](figures/figura_11_tubacioni_i_vleresimit.png)

Variablat e pavarura të studimit janë kushti i verifikimit, i cili merr katër vlera nga mungesa e plotë e bazimit deri te verifikimi i plotë; lloji i dokumentit, digjital ose i skanuar; dhe dega e sistemit, laboratorike ose narrative.

Variablat e varura janë F1-Score i nxjerrjes, saktësia e klasifikimit të statusit, norma e pohimeve të pambështetura, precision-i, recall-i dhe F1-Score i detektorit, normat e ruajtjes së mohimit dhe të shprehjeve të pasigurisë, dhe rezultati i kuptueshmërisë në studimin me përdorues.

Bazat krahasuese janë kërkesa naive pa bazim, verifikimi vetëm me rregulla, dhe modeli gjuhësor i përdorur si gjykatës.

### 5.11.1 Kontrolli i rrjedhjes së të dhënave

Korpusi i korruptuar rrjedh nga dalje të gjeneruara që nga ana e tyre rrjedhin nga një numër i vogël shabllonesh dokumentesh. Një ndarje e rastësishme e këtij korpusi në nivel fjalie do të vendoste fjali pothuajse identike njëkohësisht në grupin e trajnimit dhe në atë të testimit, duke e fryrë artificialisht performancën e matur të klasifikuesit dhe duke e bërë rezultatin e PK6 të pabesueshëm.

Prandaj ndarja bëhet në nivel dokumenti burimor, jo në nivel fjalie: asnjë dokument nuk ndodhet në dy grupe, dhe një test e kontrollon këtë. Kjo mbron nga rrjedhja e një dokumenti të vetëm, por nuk mbron nga rrjedhja e shabllonit, dhe matja tregoi se ndarja nuk e ndalon atë: forma e fjalisë (me numrat dhe emrat e hequr) e çdo fjalie me defekt të grupit të validimit gjendet te një fjali e trajnimit (100% për secilin lloj defekti, 99.9% për fjalitë e pastra), dhe çdo gjetje e shpikur nis me të njëjtën shprehje, "Vërehet gjithashtu". Pasoja është se rezultati i klasifikuesit mbi korpusin sintetik mat sa i njeh shabllonet e gjeneruesit, jo sa zbulon defekte. Prandaj PK6 raportohet edhe mbi grupin B, fjali jashtë gjeneruesit, dhe rezultati sintetik nuk paraqitet si provë e aftësisë së klasifikuesit.

*Tabela 6. Matrica e eksperimenteve*

| ID | Eksperimenti | Kushti | Metrika kryesore | Pyetja |
|---|---|---|---|---|
| E1 | Nxjerrja e të dhënave | dokumente digjitale | Precision, Recall, F1 | PK1 |
| E2 | Nxjerrja e të dhënave | dokumente të skanuara | Precision, Recall, F1 | PK1 |
| E3 | Klasifikimi i statusit | — | Saktësi, matricë konfuzioni | PK2 |
| E4 | Besnikëria e thjeshtimit | — | Ruajtja e mohimit dhe e pasigurisë | PK3 |
| E5 | Krahasimi i kryqëzuar | — | Saktësi katërshe | PK4 |
| E6 | Ablacion, kushti A | pa bazim | Normë shkeljesh | PK5 |
| E7 | Ablacion, kushti B | vetëm bazim | Normë shkeljesh | PK5 |
| E8 | Ablacion, kushti C | bazim dhe rregulla | Normë që arrin përdoruesin | PK5 |
| E9 | Ablacion, kushti D | bazim, rregulla, klasifikues | Normë që arrin përdoruesin | PK5 |
| E10 | Detektori me rregulla | — | Precision, Recall, F1 | PK6 |
| E11 | Detektori me klasifikues | — | Precision, Recall, F1 | PK6 |
| E12 | Detektori me LLM gjykatës | — | Precision, Recall, F1 | PK6 |
| E13 | Validimi mbi të dhëna reale | — | F1, hendeku i transferimit | — |
| E14 | Kuptueshmëria e përdoruesit | me dhe pa sistem | Rezultat kuptueshmërie | PK7 |
| E15 | Modeli lokal kundrejt atij në re | opsional | Normë shkeljesh | diskutim |

### 5.11.2 Infrastruktura e vlerësimit

Kontributi kryesor i punimit është një mekanizëm verifikimi, dhe vlera e
tij shprehet vetëm me numra krahasues. Prandaj infrastruktura që i
prodhon ata u ndërtua përpara komponentëve që ajo mat — vendim
metodologjik i shpjeguar në seksionin 5.1 dhe i zbatuar në rendin e
fazave.

#### 5.11.2.1 Ç'është një "sistem" për vlerësimin

Vlerësimi nuk njeh shtresa. Ai njeh diçka që merr një dokument dhe kthen
atë që mendon për të: kontekstin e nxjerrë, tekstin e gjeneruar dhe
vendimin e verifikimit. Kushtet e ablacionit të planit të eksperimenteve
bëhen kështu zbatime të ndryshme të së njëjtës ndërfaqe, në vend që degë
kushtëzimi brenda kodit të prodhimit.

Hyrja që i jepet sistemit mban vetëm identifikuesin e dokumentit dhe
shtegun e skedarit. E vërteta bazë nuk kalon kurrë prej andej, dhe kjo ka
test të vetin: prej saj varet vlefshmëria e çdo numri që del nga
harness-i, dhe një rrjedhje e tillë nuk do të linte asnjë shenjë të
dukshme në rezultate.

Çdo kusht ablacioni është sistem më vete, dhe harness-i refuzon ta
regjistrojë rezultatin e njërit nën identifikuesin e një tjetri. Pa këtë,
një ekzekutim i vetëm i sistemit të plotë do t'i mbushte E6-E9 me të
njëjtat numra, dhe matrica do të tregonte një ablacion që nuk ndodhi.
Qeliza e një kushti që sistemi nuk e zbaton mbetet `[TO BE MEASURED]`,
bashkë me arsyen.

Shablloni determinist luan për gjenerimin rolin që orakulli luan për
nxjerrjen: i veshur si gjenerues, ai duhet të japë zero shkelje dhe zero
kalime te shablloni rezervë. Mbi 80 dokumente ai jep pikërisht këtë, dhe
kështu rruga nga gjeneruesi te qeliza e PK5 është e provuar përpara se të
ekzistojë modeli gjuhësor.

Kur kushti rigjeneron, çdo draft i modelit numërohet ndër shkeljet e
prodhuara, ndërsa te përdoruesi numërohen vetëm shkeljet e tekstit që ai
mori — drafti i pranuar ose shablloni. Po të numërohej vetëm drafti i
fundit, shkeljet e përpjekjes së parë, ato që verifikimi i ndali, do të
zhdukeshin nga numri i të prodhuarave, dhe verifikimi do të dukej sikur e
bën modelin më të mirë në vend që të vendosë çfarë del jashtë.

#### 5.11.2.2 Metrikat

Të gjashtë pyetjet e para kërkimore kanë modulin e vet, dhe të gjitha
janë funksione të pastra mbi çiftet e vërtetë–parashikim.

**Nxjerrja (PK1)** matet për fushë, me çiftim të rreshtave sipas kodit
LOINC. Një rresht i humbur nuk është neutral për fushat e tij: ai
llogaritet si mungesë për secilën prej tyre. Përndryshe një sistem që
nxjerr vetëm rreshtat e lehtë do të dilte i përsosur.

**Klasifikimi (PK2)** raportohet edhe i ndarë sipas burimit të intervalit,
sepse një status i gabuar do të thotë gjithmonë njëra nga dy gjëra: vlera
u lexua gabim, ose intervali u zgjodh gabim. Veçmas raportohet edhe
mbulimi i vlerave të painterpretueshme — SP5 i shprehur si numër, sepse
rastet janë të pakta dhe saktësia e përgjithshme do t'i fshihte.

**Shkeljet (PK5)** ndajnë shkeljet e prodhuara nga ato që mbërrijnë te
përdoruesi. Ky dallim është tërë argumenti i ablacionit: verifikimi nuk e
bën modelin më të mirë, ai vendos çfarë del jashtë. Raportohet edhe
përpjesa e daljeve që përfunduan në shabllonin determinist — çmimi i
verifikimit, pa të cilin një sistem që refuzon gjithçka do të dukej i
përkryer.

**Zbuluesit (PK6)** maten sipas llojit të defektit dhe jo vetëm në
tërësi. Pritshmëria e formuluar përpara matjes është se rregullat do të
mbizotërojnë te defektet numerike dhe do të humbasin te mohimi dhe
pasiguria; një F1 i vetëm i përgjithshëm do ta fshihte plotësisht këtë.

### Intervalet e besimit

Shkallët e PK5 dhe ruajtjet e PK3 raportohen me interval besimi 95% me
rimostrim bootstrap (2 000 rimostrime, farë e fiksuar). Njësia e
rimostrimit është dokumenti dhe jo fjalia, sepse fjalitë e një dokumenti
ndajnë kontekstin dhe gabimet e tyre nuk janë të pavarura; rimostrimi
sipas fjalisë do ta ngushtonte intervalin pa të drejtë.

Kur mostra nuk ka asnjë ngjarje — zero shkelje, ose ruajtje e plotë —
intervali përqindor del me gjerësi zero. Në atë rast raportohet kufiri i
rregullit të treshit (3/n): mbi 80 dokumente, shablloni jep 0 shkelje për
100 fjali, me kufi të sipërm 0.191. Kjo nuk është kujdes formal: "zero
shkelje" mbi një mostër të vogël nuk do të thotë se sistemi nuk shkel kurrë.

#### 5.11.2.3 Dy vendime të vogla me pasojë

**Metrikat kthejnë vlerë të papërcaktuar kur emëruesi është zero, kurrë
zero.** "U mat dhe doli zero" dhe "nuk kishte çfarë të matej" janë pohime
të ndryshme, dhe tabelat i shtypin ndryshe. Qelizat që presin një
komponent të paekzistuar shënohen veçmas dhe nuk lihen bosh.

**Dy sisteme shërbejnë si kufij të njohur.** Orakulli kthen vetë të
vërtetën dhe duhet të arrijë vlerën e përsosur kudo; një metrikë që nuk e
arrin dot është e prishur në vetvete, dhe pa këtë kontroll gabimi i saj
do të dukej më vonë si dobësi e sistemit të matur. Sistemi bosh nuk
nxjerr asgjë dhe nuk duhet të marrë kurrë notë të mirë.

Kufiri i poshtëm e vërtetoi vlerën e vet menjëherë. Sistemi bosh prodhoi
ruajtje mohimi 1.000, sepse emëruesi numëronte edhe dokumentet që nuk
kishin prodhuar asnjë fjali. Një sistem që nuk shkruan asgjë nuk përmbys
asnjë mohim; kjo nuk është besnikëri. Gabimi u gjet përpara se të ishte
raportuar ndonjë numër.

#### 5.11.2.4 Prejardhja e rezultateve

Çdo rezultat shkruhet bashkë me farën e korpusit, versionin e tij me
shumat kontrolluese të tabelave burimore, sha-në e git-it, gjendjen e
pastër ose të papastër të pemës së punës dhe versionin e katalogut të
rregullave.

Gjendja e pemës së punës shënohet posaçërisht. Një numër i prodhuar mbi
kod të pakommit-uar nuk është i rindërtueshëm, dhe kjo duhet të duket në
skedar e jo të kujtohet nga ai që e ekzekutoi.

Rezultatet e matura me këtë infrastrukturë jepen te Kapitulli 6; gjendja e secilit eksperiment është përmbledhur te Figura 11.

## 5.12 Politika e sigurisë

Sistemi zbaton një grup politikash sigurie që janë kërkesa formale të implementimit dhe jo rekomandime. Secila prej tyre shoqërohet me një test automatik.

Sistemi nuk emeton asnjë pohim diagnostik, asnjë këshillë trajtimi ose medikamenti, dhe asnjë pohim prognostik. Gjetjet e klasifikuara si kritike shkaktojnë një njoftim eskalimi që shfaqet përpara çdo shpjegimi tjetër. Vlerat për të cilat nuk ekziston interval referent shënohen si të painterpretueshme dhe nuk klasifikohen. Termat që nuk gjenden në tabelën terminologjike shënohen si të pashpjeguar dhe nuk përkufizohen. Çdo dalje e sistemit përmban shënimin se sistemi nuk zëvendëson vlerësimin e profesionistit shëndetësor. Dhe në rast dështimi të përsëritur të verifikimit, shfaqet shpjegimi i gjeneruar nga shablloni determinist.

Përveç këtyre, sistemi mban një regjistër të plotë auditimi që përmban dokumentin origjinal, të dhënat e nxjerra, të dhënat e normalizuara, kontekstin e strukturuar, hyrjen dhe daljen e modelit gjuhësor, rezultatin e verifikimit, shkeljet e zbuluara, rigjenerimet e kryera dhe daljen përfundimtare.

---

# 6 REZULTATET

> **Ky kapitull është skelet.** Struktura e paraqitjes, tabelat dhe teksti i pavarur nga matjet janë të shkruara. Çdo vlerë numerike është shënuar **[MATET]** dhe plotësohet vetëm nga ekzekutime reale eksperimentesh, sipas parimit se asnjë rezultat nuk shpiket.

## 6.1 Rezultatet e implementimit të sistemit

*Figura 12–17. Pamje të ndërfaqes së përdoruesit*

*[Përshkrim i sistemit të përfunduar: komponentët e implementuar, numri i analiteve të mbështetura, madhësia e tabelës terminologjike, numri i dokumenteve në korpusin sintetik, mbulimi i testeve.]*

**[MATET]**

## 6.2 Saktësia e nxjerrjes së të dhënave laboratorike

*Tabela 7. Saktësia e nxjerrjes së të dhënave laboratorike*

| Fusha | Precision (dig.) | Recall (dig.) | F1 (dig.) | Precision (skan.) | Recall (skan.) | F1 (skan.) |
|---|---|---|---|---|---|---|
| Emri i analitit | [MATET] | [MATET] | [MATET] | [MATET] | [MATET] | [MATET] |
| Vlera numerike | [MATET] | [MATET] | [MATET] | [MATET] | [MATET] | [MATET] |
| Njësia | [MATET] | [MATET] | [MATET] | [MATET] | [MATET] | [MATET] |
| Intervali referent | [MATET] | [MATET] | [MATET] | [MATET] | [MATET] | [MATET] |
| Mikro-mesatarja | [MATET] | [MATET] | [MATET] | [MATET] | [MATET] | [MATET] |

## 6.3 Saktësia e klasifikimit kundrejt intervaleve referente

*Tabela 8* dhe *Figura 19.* **[MATET]**

*[Raportohet gjithashtu përpjesa e vlerave për të cilat intervali u nxor nga dokumenti kundrejt tabelës së brendshme, si dhe përpjesa e shënuar si e painterpretueshme.]*

## 6.4 Besnikëria e thjeshtimit të tekstit mjekësor

*Tabela 9. Besnikëria e thjeshtimit*

| Metrika | Vlera |
|---|---|
| Norma e ruajtjes së mohimit | [MATET] |
| Norma e ruajtjes së shprehjeve të pasigurisë | [MATET] |
| Norma e gjetjeve të shpikura | [MATET] |
| Norma e rekomandimeve të humbura | [MATET] |
| Gjatësia mesatare e fjalisë, burim kundrejt dalje | [MATET] |
| Raporti i termave mjekësorë, burim kundrejt dalje | [MATET] |
| Vlerësimi i ekspertëve, shkallë Likert | [MATET] |

## 6.5 Saktësia e krahasimit të kryqëzuar

*Tabela 10.* **[MATET]**

## 6.6 Efekti i shtresës së verifikimit

Ky është eksperimenti kryesor i punimit dhe rezultati i tij përbën përgjigjen e drejtpërdrejtë ndaj hipotezës së parë.

*Tabela 11. Rezultatet e ablacionit të verifikimit*

| Kushti | Norma e shkeljeve, dega A | Norma e shkeljeve, dega B |
|---|---|---|
| A — pa bazim | [MATET] | [MATET] |
| B — vetëm bazim | [MATET] | [MATET] |
| C — bazim dhe rregulla | [MATET] | [MATET] |
| D — bazim, rregulla dhe klasifikues | [MATET] | [MATET] |

*Figura 18.* **[MATET]**

## 6.7 Saktësia e vetë shtresës së verifikimit

*Tabela 12. Krahasimi i tre qasjeve të detektimit*

| Qasja | Precision | Recall | F1 |
|---|---|---|---|
| Rregullat deterministe | [MATET] | [MATET] | [MATET] |
| Klasifikuesi i finetunuar | [MATET] | [MATET] | [MATET] |
| Modeli gjuhësor si gjykatës | [MATET] | [MATET] | [MATET] |

*Tabela 13. Performanca sipas llojit të defektit* — **[MATET]**

Kjo tabelë është më informuese se ajo e përgjithshme. Pritshmëria e formuluar para matjes ishte që rregullat të ishin të plota për defektet numerike dhe të pafuqishme për ato semantike, ndërsa klasifikuesi të sillej në mënyrën e kundërt. Matja e kundërshtoi pjesën e parë: rregullat arritën macro F1 0.993 mbi korpusin e korruptuar edhe te mohimi dhe pasiguria, sepse ato shohin kontekstin e plotë të strukturuar, ndërsa klasifikuesi sheh më pak (ADR 0009).

*Figura 20* dhe *Figura 21.* **[MATET]**

## 6.8 Validimi mbi të dhëna reale

*[Vetëm nëse miratimi etik jepet. Përndryshe zëvendësohet me deklaratën përkatëse të kufizimit.]*

**[MATET OSE NUK APLIKOHET]**

## 6.9 Rezultatet e studimit me përdorues

*Tabela 14.* **[MATET]**

*[Nuk fabrikohen përgjigje pjesëmarrësish. Nëse studimi nuk kryhet, seksioni zëvendësohet me rishikim ekspertësh mbi një mostër dhe kjo deklarohet shprehimisht.]*

## 6.10 Analiza e gabimeve

*Tabela 15. Taksonomia e gabimeve* — ndërtohet nga shkeljet reale të vërejtura gjatë eksperimenteve.

**[MATET]**

---

# 7 DISKUTIME DHE PËRFUNDIME

> **Ky kapitull është skelet.** Argumentet strukturore që nuk varen nga madhësia e efektit janë të shkruara. Çdo pohim që varet nga rezultatet është shënuar.

## 7.1 Diskutimi i rezultateve

*[Interpretimi i PK1 deri PK7 në dritën e hipotezave të parashtruara në nënkapitullin 4.2.]*

**[VARET NGA REZULTATET]**

## 7.2 Asimetria e bazimit ndërmjet të dhënave të strukturuara dhe tekstit të lirë

Kjo është gjetja konceptuale kryesore e punimit dhe mund të artikulohet pavarësisht nga madhësia e efektit të matur.

Kur burimi është një objekt i strukturuar me vlera numerike të njohura, pyetja nëse një pohim mbështetet nga burimi ka përgjigje të vendosshme. Verifikimi është krahasim dhe jo gjykim, dhe norma e gabimit të tij kufizohet vetëm nga saktësia e fazës së nxjerrjes.

Kur burimi është prozë klinike, ekuivalenca semantike nuk reduktohet në krahasim të saktë. Pyetja nëse një fjali e ruan kuptimin e burimit kërkon gjykim, dhe çdo mekanizëm automatik gjykimi ka normë gabimi të pashmangshme. Rezultati i raportuar nga Laban et al. [4], një saktësi e balancuar prej afërsisht 74 përqind për zbulimin e mospërputhjeve me metoda të bazuara në natural language inference, ilustron se ky nuk është kufizim i implementimit konkret të këtij punimi por i qasjes në përgjithësi në gjendjen aktuale të teknikës.

Pasoja praktike është se garancia që sistemi mund t'i japë përdoruesit nuk është uniforme. Për vlerat laboratorike, pohimi se asnjë numër i pambështetur nuk arrin te përdoruesi është i fortë dhe i verifikueshëm. Për tekstin narrativ, pohimi i barasvlershëm është probabilistik dhe duhet formuluar si i tillë.

Ky punim argumenton se kjo asimetri duhet deklaruar hapur në çdo sistem të ngjashëm. Paraqitja e të dy rasteve pas një treguesi të vetëm që thotë thjesht se dalja është verifikuar do të ishte mashtruese për përdoruesin, sepse do t'i jepte të njëjtin nivel besimi dy pohimeve me forcë të ndryshme evidence.

## 7.3 Rregullat kundrejt mësimit makinerik në verifikim

*[Krahasim i bazuar në Tabelat 12 dhe 13.]*

Pavarësisht rezultatit konkret, argumenti strukturor qëndron: rregullat dhe klasifikuesi kanë fusha të ndryshme zbatimi dhe nuk janë konkurrentë të drejtpërdrejtë. Rregullat janë të plota dhe të sigurta aty ku problemi është i vendosshëm, ndërsa klasifikuesi është i domosdoshëm aty ku nuk është.

Nëse klasifikuesi nuk i tejkalon rregullat në metrikat e përgjithshme, ky rezultat nuk e zhvlerëson atë. Ai tregon se klasat e gabimeve të pranishme në korpusin e përdorur janë kryesisht të vendosshme me mjete deterministe, dhe kjo në vetvete përbën gjetje me vlerë për projektimin e sistemeve të ngjashme.

**[VARET NGA REZULTATET]**

## 7.4 Përpunimi i gjuhës natyrore mjekësore për shqipen

Mungesa e modeleve klinike të paratrajnuara për shqipen e detyroi dizajnin drejt fjalorëve dhe rregullave për komponentët e vendosshëm, dhe drejt enkoderëve shumëgjuhësh të përgjithshëm për ata semantikë.

Tabela terminologjike e ndërtuar në kuadër të këtij punimi është artefakt i ripërdorshëm që mund të shërbejë si bazë për punime të ardhshme në këtë fushë.

*[Vlerësim i cilësisë së gjenerimit në shqip bazuar në rezultatet e PK3 dhe rishikimin e ekspertëve.]*

## 7.5 Konsideratat e sigurisë dhe rregullatore

Sistemi është projektuar si mjet shpjegues dhe refuzon në mënyrë sistematike pohimet diagnostike, terapeutike dhe prognostike. Punimi nuk pretendon se ky pozicionim e vendos sistemin përfundimisht jashtë fushës së rregullores për pajisjet mjekësore, sepse kufiri ndërmjet informacionit shpjegues dhe informacionit që përdoret për vendimmarrje klinike varet nga përdorimi real dhe jo vetëm nga qëllimi i deklaruar.

Për sa i përket Aktit Evropian për Inteligjencën Artificiale, detyrimet e transparencës janë tashmë të zbatueshme, ndërsa regjimi për sistemet me rrezik të lartë hyn në fuqi më vonë. Sistemi i zbaton detyrimet e transparencës përmes shënimit të përhershëm dhe treguesit të verifikimit të pranishëm në çdo dalje.

## 7.6 Kufizimet e punimit

Vlerësimi kryesor është kryer mbi të dhëna sintetike, dhe performanca mbi faqosje reale të papara mbetet ose e pamatur ose e matur vetëm mbi një mostër të vogël. Ky është kufizimi më i rëndësishëm i punimit dhe ndikon në përgjithësueshmërinë e rezultateve të PK1 dhe PK2.

Verifikimi semantik i degës narrative nuk ofron garanci por vetëm ulje të matshme të rrezikut, dhe norma e tij e gabimit nuk është zero.

Tabela terminologjike është e kufizuar në numër dhe nuk mbulon çdo term të mundshëm mjekësor, gjë që nënkupton se një pjesë e termave do të mbeten të pashpjeguar.

Studimi me përdorues, nëse kryhet, është i vogël dhe lejon vetëm përshkrim dhe jo përgjithësim statistikor.

Rezultatet laboratorike jonumerike nuk mbulohen fare nga sistemi.

Së fundi, cilësia e modelit gjuhësor në gjuhën shqipe është matur vetëm në kontekstin e këtij sistemi dhe nuk përbën vlerësim të përgjithshëm të aftësisë së modelit në këtë gjuhë.

## 7.7 Mundësitë për zhvillime të mëtejshme

Validimi mbi një grup më të gjerë dokumentesh reale nga laboratorë të ndryshëm do të ishte hapi i parë dhe më i rëndësishëm për të konfirmuar përgjithësueshmërinë e rezultateve.

Zgjerimi i tabelës terminologjike dhe i panelit të analiteve do ta rriste mbulimin praktik të sistemit pa ndryshuar arkitekturën.

Zhvillimi i modeleve të specializuara të përpunimit të gjuhës natyrore për shqipen mjekësore do ta hiqte kufizimin themelor që ka formësuar dizajnin e këtij sistemi.

Metoda më të sofistikuara të verifikimit semantik mund ta ngushtojnë hendekun ndërmjet dy degëve, megjithëse argumenti i nënkapitullit 7.2 sugjeron se ai nuk mund të mbyllet plotësisht.

Vendosja lokale e një modeli gjuhësor me peshë të hapur do ta eliminonte transferimin e të dhënave shëndetësore te palë të treta dhe do të thjeshtonte ndjeshëm pozicionin e sistemit në raport me mbrojtjen e të dhënave.

Së fundi, validimi klinik me pjesëmarrjen e profesionistëve shëndetësorë do të ishte parakusht për çdo përdorim real të sistemit përtej kontekstit kërkimor.

## 7.8 Përfundimet

*[Shkruhet në fund, i bazuar ekskluzivisht në rezultatet e matura. Struktura: përgjigjja e pyetjes kryesore kërkimore, statusi i të dyja hipotezave, kontributet e konfirmuara nga rezultatet, dhe ajo që mbetet e paprovuar.]*

**[VARET NGA REZULTATET]**

---

# 8 REFERENCAT

*Referencat [1]–[4] janë verifikuar kundrejt burimeve origjinale. Lista duhet zgjeruar në dyzet deri gjashtëdhjetë burime gjatë fazës së shqyrtimit të literaturës. Asnjë punim nuk duhet cituar pa u lexuar.*

[1] W. W. Chapman, W. Bridewell, P. Hanbury, G. F. Cooper, and B. G. Buchanan, "A simple algorithm for identifying negated findings and diseases in discharge summaries," *Journal of Biomedical Informatics*, vol. 34, no. 5, pp. 301–310, 2001, doi: 10.1006/jbin.2001.1029.

[2] H. Harkema, J. N. Dowling, T. Thornblade, and W. W. Chapman, "ConText: An algorithm for determining negation, experiencer, and temporal status from clinical reports," *Journal of Biomedical Informatics*, vol. 42, no. 5, pp. 839–851, 2009.

[3] Z. Ji, N. Lee, R. Frieske, T. Yu, D. Su, Y. Xu, E. Ishii, Y. J. Bang, A. Madotto, and P. Fung, "Survey of Hallucination in Natural Language Generation," *ACM Computing Surveys*, vol. 55, no. 12, Article 248, 2023, doi: 10.1145/3571730.

[4] P. Laban, T. Schnabel, P. N. Bennett, and M. A. Hearst, "SummaC: Re-Visiting NLI-based Models for Inconsistency Detection in Summarization," *Transactions of the Association for Computational Linguistics*, vol. 10, pp. 163–177, 2022, doi: 10.1162/tacl_a_00453.

*Burime që duhen lexuar dhe shtuar gjatë fazës së shqyrtimit të literaturës:*

Conneau et al. (2020) mbi XLM-RoBERTa; Maynez et al. (2020) mbi besnikërinë në përmbledhjen abstraktive; Manakul et al. (2023) mbi SelfCheckGPT; Min et al. (2023) mbi FActScore; Li et al. (2023) mbi HaluEval; literatura mbi thjeshtimin e teksteve mjekësore nga ACL Anthology; literatura mbi kuptueshmërinë e portaleve të pacientëve nga PubMed dhe JAMIA; dokumentacioni zyrtar i LOINC; udhëzuesi MDCG 2019-11; Rregullorja (BE) 2017/745; Rregullorja (BE) 2024/1689 dhe Rregullorja (BE) 2026/1744; Rregullorja (BE) 2016/679.

---

# 9 APPENDIXES

**Shtojca A** — Tabela e plotë terminologjike shqip me shpjegimet, burimet dhe kategoritë

**Shtojca B** — Paneli i plotë i analiteve me kodet LOINC dhe intervalet referente rezervë

**Shtojca C** — Katalogu i plotë i rregullave të verifikimit me shembuj

**Shtojca D** — Kërkesat e përdorura për modelin gjuhësor, me versionim

**Shtojca E** — Udhëzimet e anotimit për dokumentet reale

**Shtojca F** — Instrumenti i studimit me përdorues

**Shtojca G** — Skema SQL e bazës së të dhënave

**Shtojca H** — Konfigurimet e eksperimenteve dhe farat fillestare

**Shtojca I** — Shembuj dokumentesh nga korpusi sintetik

---

## Shtojca A — Tabela e plotë terminologjike shqip

Tabela mban 82 terma. **82 prej tyre mbajnë ende vendmbajtës në kolonën e burimit**: shpjegimet janë përkufizime pune të autorit dhe nuk janë referuar te një burim i verifikueshëm. Pa referencë, tabela vetë është burim informacioni të paverifikuar; kjo është kufizim i shprehur te seksioni 7.6, jo detaj i fshehur këtu.

*Tabela A.1. Termat, shpjegimet, kategoritë dhe sinonimet*

| Termi | Shpjegimi | Kategoria | Sinonimet | Burimi |
|---|---|---|---|---|
| anemi | nivel i ulët i hemoglobinës në gjak | gjendje | anemia, anemik | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| eritropoezë | prodhimi i qelizave të kuqe të gjakut në palcën kockore | proces | eritropoeza | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| leukocitozë | numër i rritur i qelizave të bardha të gjakut | gjendje | leukocitoza | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| leukopeni | numër i ulët i qelizave të bardha të gjakut | gjendje | leukopenia | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| trombocitopeni | numër i ulët i pllakëzave të gjakut | gjendje | trombocitopenia | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| trombocitozë | numër i rritur i pllakëzave të gjakut | gjendje | trombocitoza | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hiperglicemi | nivel i rritur i sheqerit në gjak | gjendje | hiperglicemia | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hipoglicemi | nivel i ulët i sheqerit në gjak | gjendje | hipoglicemia | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hiperkalemi | nivel i rritur i kaliumit në gjak | gjendje | hiperkalemia | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hipokalemi | nivel i ulët i kaliumit në gjak | gjendje | hipokalemia | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hipernatremi | nivel i rritur i natriumit në gjak | gjendje | hipernatremia | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hiponatremi | nivel i ulët i natriumit në gjak | gjendje | hiponatremia | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hiperkalcemi | nivel i rritur i kalciumit në gjak | gjendje | hiperkalcemia | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hipokalcemi | nivel i ulët i kalciumit në gjak | gjendje | hipokalcemia | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| transaminaza | enzima që lidhen me funksionin e mëlçisë | enzima | transaminazat, ALT, AST | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| kolestazë | rrjedhje e penguar e biliarit nga mëlçia | gjendje | kolestaza | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hiperbilirubinemi | nivel i rritur i bilirubinës në gjak | gjendje | hiperbilirubinemia | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| ikter | ngjyrim i verdhë i lëkurës dhe i syve | shenjë | ikteri, verdhëz | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| dislipidemi | vlera të çrregulluara të yndyrnave në gjak | gjendje | dislipidemia | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hiperkolesterolemi | nivel i rritur i kolesterolit në gjak | gjendje | hiperkolesterolemia | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hipertrigliceridemi | nivel i rritur i trigliceridëve në gjak | gjendje | hipertrigliceridemia | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hipotiroidizëm | veprimtari e ulët e gjëndrës tiroide | gjendje | hipotiroidizmi, hipotiroidi | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hipertiroidizëm | veprimtari e shtuar e gjëndrës tiroide | gjendje | hipertiroidizmi, hipertiroidi | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| azotemi | nivel i rritur i mbetjeve azotike në gjak | gjendje | azotemia | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| proteinuri | prani e proteinave në urinë | gjendje | proteinuria | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| inflamacion | përgjigje mbrojtëse e organizmit ndaj dëmtimit ose infeksionit | proces | inflamacioni, inflamator | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| sideropeni | rezerva të ulëta të hekurit në organizëm | gjendje | sideropenia | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hemolizë | shkatërrim i parakohshëm i qelizave të kuqe | proces | hemoliza, hemolitik | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hipoalbuminemi | nivel i ulët i albuminës në gjak | gjendje | hipoalbuminemia | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hiperurikemi | nivel i rritur i acidit urik në gjak | gjendje | hiperurikemia | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| nefropati | sëmundje e veshkave | gjendje | nefropatia | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hepatopati | sëmundje e mëlçisë | gjendje | hepatopatia | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| steatozë | grumbullim i yndyrës në mëlçi | gjendje | steatoza | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| glikemi | niveli i sheqerit në gjak | matje | glikemia | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| elektrolit | minerale në gjak që mbajnë ekuilibrin e ujit dhe punën e qelizave | matje | elektrolitet, elektrolitike | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hemogram | analiza e plotë e qelizave të gjakut | analize | hemograma, analiza e plotë e gjakut | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| interval referent | kufijtë brenda të cilëve vlera konsiderohet e zakonshme | metodologji | vlera referente, intervali referent | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| analit | substanca e matur në analizë | metodologji | analiti, analitet | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| funksioni renal | mënyra si punojnë veshkat | matje | funksioni i veshkave, renal | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| funksioni hepatik | mënyra si punon mëlçia | matje | funksioni i mëlçisë, hepatik | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| metabolizëm | tërësia e proceseve kimike që mbajnë gjallë organizmin | proces | metabolizmi, metabolik | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| ferritinë | proteina që ruan hekurin në organizëm | matje | ferritina | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hemoglobinë | proteina që bart oksigjenin në qelizat e kuqe | matje | hemoglobina | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| kreatininë | mbetje e punës së muskujve që largohet nga veshkat | matje | kreatinina | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| albuminë | proteina kryesore e gjakut e prodhuar nga mëlçia | matje | albumina | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| tiroide | gjëndra që rregullon shpejtësinë e metabolizmit | organ | tiroidja, tiroidea | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| neutropeni | numër i ulët i një lloji të qelizave të bardha | gjendje | neutropenia | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| neutrofili | numër i rritur i një lloji të qelizave të bardha | gjendje |  | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| limfocitozë | numër i rritur i limfociteve në gjak | gjendje | limfocitoza | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| limfopeni | numër i ulët i limfociteve në gjak | gjendje | limfopenia | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| policitemi | numër i rritur i qelizave të kuqe në gjak | gjendje | policitemia | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hemostazë | procesi i ndalimit të gjakderdhjes | proces | hemostaza | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| koagulim | mpiksja e gjakut | proces | koagulimi, koagulues | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| filtrim glomerular | shpejtësia me të cilën veshkat pastrojnë gjakun | matje | filtrimi glomerular, GFR | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| klirens | masa e pastrimit të një substance nga gjaku | matje | klirensi | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hematuri | prani e gjakut në urinë | gjendje | hematuria | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| glikozuri | prani e sheqerit në urinë | gjendje | glikozuria | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| ketonuri | prani e trupave ketonikë në urinë | gjendje | ketonuria | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| urobilinogjen | produkt i zbërthimit të bilirubinës | matje | urobilinogjeni | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| lipoproteinë | grimcë që bart yndyrnat në gjak | matje | lipoproteina, lipoproteinat | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| aterosklerozë | ngurtësim dhe ngushtim i enëve të gjakut | gjendje | ateroskleroza | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| sindrom metabolik | bashkësi çrregullimesh të metabolizmit | gjendje | sindromi metabolik | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| rezistencë ndaj insulinës | përgjigje e dobësuar e qelizave ndaj insulinës | gjendje | rezistenca ndaj insulinës | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| insulinë | hormoni që ul nivelin e sheqerit në gjak | matje | insulina | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| kortizol | hormon i gjëndrave mbiveshkore | matje | kortizoli | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| paratiroide | gjëndra që rregullojnë kalciumin | organ | paratiroidet | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| osteoporozë | humbje e dendësisë së kockave | gjendje | osteoporoza | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hiperfosfatemi | nivel i rritur i fosforit në gjak | gjendje | hiperfosfatemia | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hipofosfatemi | nivel i ulët i fosforit në gjak | gjendje | hipofosfatemia | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hipomagnezemi | nivel i ulët i magnezit në gjak | gjendje | hipomagnezemia | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hipokloremi | nivel i ulët i klorit në gjak | gjendje | hipokloremia | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| hiperkloremi | nivel i rritur i klorit në gjak | gjendje | hiperkloremia | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| serum | pjesa e lëngshme e gjakut pa faktorët e mpiksjes | material | serumi | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| plazmë | pjesa e lëngshme e gjakut me faktorët e mpiksjes | material | plazma | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| gjëndër | organ që prodhon dhe lëshon substanca në trup | organ | gjëndra, gjëndrat | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| enzimë | proteinë që përshpejton reaksionet kimike në trup | matje | enzima, enzimat | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| antitrup | proteinë mbrojtëse e prodhuar nga sistemi imunitar | matje | antitrupa, antitrupat | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| antigjen | substancë që nxit përgjigje të sistemit imunitar | matje | antigjeni | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| biomarkues | tregues i matshëm i një gjendjeje në trup | metodologji | biomarkuesi | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| depistim | kontroll i rregullt për zbulim të hershëm | metodologji | depistimi | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| gjakderdhje | humbje gjaku nga enët e gjakut | gjendje | gjakderdhja | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |
| imunitet | aftësia e trupit për t'u mbrojtur nga infeksionet | proces | imuniteti, imunitar | [BURIMI — plotësohet gjatë ndërtimit të tabelës] |

---

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
| P01 | Hemoglobinë në gjak ↓ + Ferritinë në serum ↓ | [REFERENCË — plotësohet] |
| P02 | Hemoglobinë në gjak ↓ + Volumi mesatar eritrocitar ↓ | [REFERENCË — plotësohet] |
| P03 | Hemoglobinë në gjak ↓ + Vitaminë B12 ↓ | [REFERENCË — plotësohet] |
| P04 | Glukozë në serum ↑ + Hemoglobinë e glikuar ↑ | [REFERENCË — plotësohet] |
| P05 | Kreatininë në serum ↑ + Ure në serum ↑ | [REFERENCË — plotësohet] |
| P06 | Alanin aminotransferazë ↑ + Aspartat aminotransferazë ↑ | [REFERENCË — plotësohet] |
| P07 | Fosfatazë alkaline ↑ + Gama-glutamil transferazë ↑ | [REFERENCË — plotësohet] |
| P08 | Hormoni stimulues i tiroides ↑ + Tiroksinë e lirë ↓ | [REFERENCË — plotësohet] |
| P09 | Hormoni stimulues i tiroides ↓ + Tiroksinë e lirë ↑ | [REFERENCË — plotësohet] |
| P10 | Leukocite ↑ + Proteina C-reaktive ↑ | [REFERENCË — plotësohet] |
| P11 | Kolesterol LDL ↑ + Kolesterol HDL ↓ | [REFERENCË — plotësohet] |

> Kombinimet u zgjodhën si të njohura gjerësisht dhe duhen konfirmuar nga
> mentori ose nga një mjek, bashkë me burimin e secilit, përpara
> dorëzimit.

---

## Shtojca C — Katalogu i plotë i rregullave të verifikimit

### Tabela C.1. Katalogu i rregullave të verifikimit

Versioni i katalogut: `r1.3`. Ai regjistrohet në çdo
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


*Tabela C.2. Një shembull i vërtetë për çdo rregull që korruptuesit e prodhojnë, me provën që jep rregulli*

Shembujt janë marrë nga korpusi i korruptuar (fara 42): fjalia që ndryshoi krahasuar me shabllonin e pastër, dhe prova e shkelësit të rregullit mbi të. R4 (vlera kritike që mungon) dhe R9 (shpjegimi i një termi të pashpjeguar) nuk kanë korruptues; R9 u mat vetëm mbi grupin B, ku nuk kapi asnjë nga 5 fjalitë (seksioni 6.7).

| Rregulli | Lloji | Fjalia me defekt | Prova e rregullit |
|---|---|---|---|
| R1 | `ungrounded_number` | Për Ferritinë në serum vlera e matur është 47 ng/mL, brenda intervalit referent (17 - 151). | numri 17 nuk gjendet ndër vlerat e nxjerra |
| R2 | `ungrounded_analyte` | Për Fosfatazë alkaline vlera e matur është 60 mg/dL, brenda intervalit referent (50 - 85). | analiti 6768-6 nuk është matur në këtë dokument |
| R3 | `direction_mismatch` | Për Hematokrit vlera e matur është 55.4 %, nën intervalin referent (36 - 48). | 4544-3: pohohet decreased, por statusi i matur është high |
| R5 | `polarity_flip` | Mjeku ka shënuar: Bilirubina totale del mbi intervalin referent. | burimi thotë negated për “Bilirubina totale nuk del mbi intervalin referent” |
| R6 | `hedge_removed` | Mjeku ka shënuar: Fosfori mbi intervalin referent, por kërkon rikontroll. | burimi e shpreh me rezervë: “Fosfori duket mbi intervalin referent, por kërkon rikontroll” |
| R7 | `fabricated_finding` | Vërehet gjithashtu aterosklerozë. | termi “aterosklerozë” nuk shfaqet në raportin burimor |
| R8 | `omitted_recommendation` | (një fjali e fshirë) | rekomandimi “Rekomandohet përsëritja e analizave pas një muaji” mungon në dalje |
| SP1-3 | `prohibited_claim` | Duhet të merrni ilaçe për yndyrnat në gjak. | SP2: shprehja “merrni” — Asnjë këshillë trajtimi apo medikamenti nuk lëshohet kurrë. |

---

## Shtojca D — Kërkesat për modelin gjuhësor

**Nuk ka kërkesa për t'u treguar.** Sistemi nuk përdor ende model gjuhësor: gjeneruesi i vetëm i zbatuar është shablloni determinist (`generation/templates.py`), që ndërton tekstin drejtpërdrejt nga `GroundingContext`. Ndërfaqja ekziston (protokolli `Generator`, dhe kontrata që funksioni i kërkesës merr vetëm kontekstin; shih seksionin 5.2.1), por adaptori i një ofruesi dhe kërkesat e versionuara nuk janë shkruar. Kjo shtojcë plotësohet kur të ekzistojnë; deri atëherë eksperimentet E4, E6, E7 dhe E12 mbeten të pamatura ose maten vetëm me shabllonin si kufi i njohur.

---

## Shtojca E — Udhëzimet e anotimit për dokumentet reale

**Nuk aplikohet.** Nuk u përdorën dokumente reale: miratimi etik nuk është marrë. Eksperimenti E13 (vlefshmëria e jashtme) mbetet i pamatur, dhe kjo deklarohet si kufizimi kryesor te seksioni 7.6. Grupet e shkruara C dhe B (`evaluation/handwritten/`) nuk janë dokumente reale dhe nuk e zëvendësojnë E13.

---

## Shtojca F — Instrumenti i studimit me përdorues

**Nuk aplikohet.** Studimi me përdorues (PK7, E14) nuk u krye, kështu që nuk ka instrument për t'u paraqitur dhe nuk raportohen rezultate kuptueshmërie. Seksioni 6.9 e thotë këtë shprehimisht.

---

## Shtojca G — Skema SQL e bazës së të dhënave

Skema PostgreSQL e ndërtuar nga modelet (`persistence/tables.py`): 16 tabela. Migrimet Alembic (`backend/alembic/versions/`) e prodhojnë të njëjtën skemë; një test krahason rezultatin e tyre me modelet. Terminologjia dhe intervalet referente nuk janë në bazë (`resources/` është burimi i vetëm).

```sql
CREATE TABLE audit_events (
	id SERIAL NOT NULL, 
	document_id UUID, 
	user_id UUID, 
	event_type VARCHAR(60) NOT NULL, 
	payload JSON NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_audit_events_document_created ON audit_events (document_id, created_at);

CREATE TABLE login_failures (
	id SERIAL NOT NULL, 
	email_key VARCHAR(64) NOT NULL, 
	ip_key VARCHAR(64) NOT NULL, 
	at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_login_failures_email_at ON login_failures (email_key, at);

CREATE INDEX ix_login_failures_ip_at ON login_failures (ip_key, at);

CREATE TABLE users (
	id UUID NOT NULL, 
	email VARCHAR(320) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE TABLE auth_sessions (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	revoked_at TIMESTAMP WITH TIME ZONE, 
	revoked_reason VARCHAR(30), 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_auth_sessions_user_id ON auth_sessions (user_id);

CREATE TABLE documents (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	filename_encrypted BYTEA NOT NULL, 
	mime VARCHAR(100) NOT NULL, 
	sha256 VARCHAR(64) NOT NULL, 
	size_bytes INTEGER NOT NULL, 
	storage_path VARCHAR(255) NOT NULL, 
	uploaded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	channel VARCHAR(20), 
	state VARCHAR(30) NOT NULL, 
	state_reason TEXT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_documents_user_id ON documents (user_id);

CREATE TABLE cross_references (
	id UUID NOT NULL, 
	document_id UUID NOT NULL, 
	position INTEGER NOT NULL, 
	analyte_code VARCHAR(20) NOT NULL, 
	state VARCHAR(30) NOT NULL, 
	assertion_id UUID, 
	finding_id UUID, 
	PRIMARY KEY (id), 
	FOREIGN KEY(document_id) REFERENCES documents (id) ON DELETE CASCADE
);

CREATE INDEX ix_cross_references_document_id ON cross_references (document_id);

CREATE TABLE document_glossary (
	id SERIAL NOT NULL, 
	document_id UUID NOT NULL, 
	position INTEGER NOT NULL, 
	term VARCHAR(200) NOT NULL, 
	explanation_sq TEXT NOT NULL, 
	source_ref TEXT NOT NULL, 
	category VARCHAR(100), 
	synonyms JSON NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(document_id) REFERENCES documents (id) ON DELETE CASCADE
);

CREATE INDEX ix_document_glossary_document_id ON document_glossary (document_id);

CREATE TABLE document_unexplained_terms (
	id SERIAL NOT NULL, 
	document_id UUID NOT NULL, 
	position INTEGER NOT NULL, 
	term VARCHAR(200) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(document_id) REFERENCES documents (id) ON DELETE CASCADE
);

CREATE INDEX ix_document_unexplained_terms_document_id ON document_unexplained_terms (document_id);

CREATE TABLE explanations (
	id UUID NOT NULL, 
	document_id UUID NOT NULL, 
	attempt INTEGER NOT NULL, 
	generator VARCHAR(200) NOT NULL, 
	prompt_version VARCHAR(50), 
	raw_output TEXT, 
	final_output TEXT, 
	is_fallback BOOLEAN NOT NULL, 
	delivered BOOLEAN NOT NULL, 
	error TEXT, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(document_id) REFERENCES documents (id) ON DELETE CASCADE
);

CREATE INDEX ix_explanations_document_id ON explanations (document_id);

CREATE TABLE lab_findings (
	id UUID NOT NULL, 
	document_id UUID NOT NULL, 
	position INTEGER NOT NULL, 
	analyte_code VARCHAR(20) NOT NULL, 
	analyte_name_raw VARCHAR(200) NOT NULL, 
	analyte_name_canonical VARCHAR(200) NOT NULL, 
	value_raw VARCHAR(64) NOT NULL, 
	value VARCHAR(64) NOT NULL, 
	unit_raw VARCHAR(40), 
	unit_canonical VARCHAR(40) NOT NULL, 
	value_canonical VARCHAR(64) NOT NULL, 
	ref_low VARCHAR(64), 
	ref_high VARCHAR(64), 
	ref_source VARCHAR(20) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	severity VARCHAR(64), 
	page INTEGER NOT NULL, 
	bbox JSON, 
	measured_at DATE, 
	flag_in_document VARCHAR(10), 
	PRIMARY KEY (id), 
	FOREIGN KEY(document_id) REFERENCES documents (id) ON DELETE CASCADE
);

CREATE INDEX ix_lab_findings_document_analyte ON lab_findings (document_id, analyte_code);

CREATE TABLE pattern_observations (
	id SERIAL NOT NULL, 
	document_id UUID NOT NULL, 
	position INTEGER NOT NULL, 
	pattern_id VARCHAR(20) NOT NULL, 
	finding_ids JSON NOT NULL, 
	source_ref TEXT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(document_id) REFERENCES documents (id) ON DELETE CASCADE
);

CREATE INDEX ix_pattern_observations_document_id ON pattern_observations (document_id);

CREATE TABLE processing_jobs (
	id UUID NOT NULL, 
	document_id UUID NOT NULL, 
	state VARCHAR(30) NOT NULL, 
	attempt INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	started_at TIMESTAMP WITH TIME ZONE, 
	finished_at TIMESTAMP WITH TIME ZONE, 
	error TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(document_id) REFERENCES documents (id) ON DELETE CASCADE
);

CREATE INDEX ix_processing_jobs_document_id ON processing_jobs (document_id);

CREATE TABLE refresh_tokens (
	id UUID NOT NULL, 
	session_id UUID NOT NULL, 
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	used_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(session_id) REFERENCES auth_sessions (id) ON DELETE CASCADE
);

CREATE INDEX ix_refresh_tokens_session_id ON refresh_tokens (session_id);

CREATE TABLE report_assertions (
	id UUID NOT NULL, 
	document_id UUID NOT NULL, 
	position INTEGER NOT NULL, 
	text_span TEXT NOT NULL, 
	analyte_code VARCHAR(20), 
	direction VARCHAR(20) NOT NULL, 
	polarity VARCHAR(20) NOT NULL, 
	certainty VARCHAR(20) NOT NULL, 
	kind VARCHAR(20) NOT NULL, 
	char_start INTEGER NOT NULL, 
	char_end INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(document_id) REFERENCES documents (id) ON DELETE CASCADE
);

CREATE INDEX ix_report_assertions_document_id ON report_assertions (document_id);

CREATE TABLE verification_results (
	id UUID NOT NULL, 
	explanation_id UUID NOT NULL, 
	mode VARCHAR(30) NOT NULL, 
	passed BOOLEAN NOT NULL, 
	rules_version VARCHAR(20) NOT NULL, 
	classifier_version VARCHAR(200), 
	duration_ms INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (explanation_id), 
	FOREIGN KEY(explanation_id) REFERENCES explanations (id) ON DELETE CASCADE
);

CREATE TABLE violations (
	id UUID NOT NULL, 
	verification_result_id UUID NOT NULL, 
	position INTEGER NOT NULL, 
	type VARCHAR(40) NOT NULL, 
	detected_by VARCHAR(20) NOT NULL, 
	sentence TEXT NOT NULL, 
	evidence TEXT NOT NULL, 
	confidence FLOAT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(verification_result_id) REFERENCES verification_results (id) ON DELETE CASCADE
);

CREATE INDEX ix_violations_verification_result_id ON violations (verification_result_id);
```

---

## Shtojca H — Konfigurimet e eksperimenteve dhe farat fillestare

*Tabela H.1. Korpusi sintetik*

| Parametri | Vlera |
|---|---|
| Versioni i gjeneruesit | `gen-1.0` |
| Fara | 42 |
| Dokumente | 500 (168 të skanuara, pjesa e synuar 35%) |
| Faqe | 556 |
| Gjetje laboratorike | 9860 |
| Pohime të mjekut | 2749 |
| Terma të pashpjeguar | 236 |
| Dokumente me vlerë kritike | 36 |

*Tabela H.2. Versionet dhe parametrat fiks të sistemit*

| Parametri | Vlera |
|---|---|
| Katalogu i rregullave | `r1.3` |
| Politika e sigurisë | `sp1.0` |
| OCR | Tesseract, gjuha `eng`, `--psm 6`, 200 dpi |
| Rimostrimi bootstrap | 2000 rimostrime, fara 20260928, njësia është dokumenti |

*Tabela H.3. Rezultatet që ekzistojnë dhe prejardhja e tyre*

| Eksperimenti | Pipeline | Kodi (git) | Pema e punës | Korpusi |
|---|---|---|---|---|
| E1 | `grounding` | `37b5be45b3` | e pastër | `gen-1.0/s42/n500/37d8b080` |
| E2 | `grounding+ocr` | `37b5be45b3` | e pastër | `gen-1.0/s42/n500/37d8b080` |
| E3 | `grounding+ocr` | `37b5be45b3` | e pastër | `gen-1.0/s42/n500/37d8b080` |
| E5 | `grounding+ocr` | `37b5be45b3` | e pastër | `gen-1.0/s42/n500/37d8b080` |
| E7 | `e7[template]+ocr` | `37b5be45b3` | e pastër | `gen-1.0/s42/n500/37d8b080` |
| E8 | `e8[template]+ocr` | `37b5be45b3` | e pastër | `gen-1.0/s42/n500/37d8b080` |
| E9 | `e9[template]+ocr+xlm-roberta-base/sentence/sentence@0.85` | `37b5be45b3` | e pastër | `gen-1.0/s42/n500/37d8b080` |
| E10 | — | — | — | — (pa metadata) |

*Tabela H.4. Klasifikuesi XLM-RoBERTa (trajnuar në Colab) dhe pragjet e zgjedhura mbi validimin*

| Hyrja | Modeli | Epoka | Shkalla e të nxënit | Batch | Gjatësia | Fara | Pajisja | Pragu 1 | Pragu 2 |
|---|---|---|---|---|---|---|---|---|---|
| context | `xlm-roberta-base` | 3 | 2e-05 | 16 | 384 | 42 | Tesla T4 | 0.4 | 0.9 |
| sentence | `xlm-roberta-base` | 3 | 2e-05 | 16 | 128 | 42 | Tesla T4 | 0.3 | 0.85 |

Pragu 1 është ai me macro F1 më të lartë mbi validimin; pragu 2 është ai me macro F1 më të lartë ndër ata që bllokojnë jo më shumë se 5% të teksteve të pastra të validimit (seksioni 6.7).

---

## Shtojca I — Shembuj dokumentesh nga korpusi sintetik

Dy dokumente të korpusit: njëri dixhital dhe njëri i skanuar, që kanë të njëjtën përmbajtje të prodhuar nga i njëjti gjenerues. Emrat e pacientëve në to janë të shpikur nga gjeneruesi.

### Dokument dixhital (`doc_00001.pdf`)

![Faqja e parë e dokumentit dixhital](appendices/images/dokument_dixhital.png)

*Figura I.1. Faqja e parë e një dokumenti dixhital të korpusit sintetik*

E vërteta bazë për gjashtë gjetjet e para:

| Analiti | Vlera | Njësia | Intervali | Statusi |
|---|---|---|---|---|
| Hemoglobinë në gjak | 13.0 | g/dL | 13.5 – 17.5 | low |
| Hematokrit | 33.8 | % | 40.0 – 52.0 | low |
| Eritrocite | 3.48 | 10^12/L | 4.50 – 5.90 | low |
| Leukocite | 8.1 | 10^9/L | 4.0 – 10.0 | normal |
| Trombocite | 66 | 10^9/L | 150 – 399 | low |
| Volumi mesatar eritrocitar | 92.7 | fL | 79.9 – 100.1 | normal |

Narrativa e mjekut (fillimi):

> Analizat janë kryer me kërkesë të mjekut familjar. Kaliumi është nën intervalin referent. Trombocitet rezultojnë nën intervalin referent. Gama GT del mbi intervalin referent. Eritrocitet rezultojnë mbi intervalin referent. Klori nuk rezulton nën intervalin referent. Funksioni renal është vlerësuar në tërësi. Vërehet eozinofili e lehtë. Rekomandohet konsultë me mjekun specialist.…

### Dokument i skanuar (`doc_00000.pdf`)

![Faqja e parë e dokumentit i skanuar](appendices/images/dokument_skanuar.png)

*Figura I.2. Faqja e parë e një dokumenti i skanuar të korpusit sintetik*

E vërteta bazë për gjashtë gjetjet e para:

| Analiti | Vlera | Njësia | Intervali | Statusi |
|---|---|---|---|---|
| Hemoglobinë në gjak | 15.7 | g/dL | 13.5 – 17.5 | normal |
| Hematokrit | 44.6 | % | 40.0 – 52.0 | normal |
| Eritrocite | 5.22 | 10^12/L | 4.50 – 5.90 | normal |
| Leukocite | 7.1 | 10^9/L | 4.0 – 10.0 | normal |
| Trombocite | 336 | 10^9/L | 150 – 400 | normal |
| Volumi mesatar eritrocitar | 102.5 | fL | 80.0 – 100.0 | high |

Narrativa e mjekut (fillimi):

> Vlerësim laboratorik në kuadër të ndjekjes së rregullt. Fosfori është nën intervalin referent. Kaliumi del mbi intervalin referent. Glukoza mund të jetë nën intervalin referent. Vërehet hiperkalemi. Rekomandohet vlerësim klinik i mëtejshëm.…
