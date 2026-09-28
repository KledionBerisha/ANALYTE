# 5.3 Dega e rezultateve laboratorike

*Rishikim i shkruar pas zbatimit. Kanali dixhital është i plotë; rruga e
njohjes optike të karaktereve nuk është zbatuar ende.*

*Figura 3. Tubacioni i përpunimit të rezultateve laboratorike*

## 5.3.1 Rrugëzimi i dokumentit

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

## 5.3.2 Rindërtimi i rreshtave

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

## 5.3.3 Normalizimi

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

*Tabela 2. Faktorët e konvertimit të njësive*

## 5.3.4 Zgjidhja e intervalit referent

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

## 5.3.5 Klasifikimi dhe refuzimi i interpretimit

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

*Tabela 1. Paneli i analiteve dhe hartëzimi LOINC*

Tabela e brendshme përmban 38 analite me interval referent dhe njeh me
emër edhe 8 të tjera për të cilat interval nuk ekziston. Këto të fundit
nuk janë mangësi e tabelës por materiali me të cilin matet politika SP5.

## 5.3.6 Rreshtat e hedhur

Çdo rresht që njihet si të dhëna por nuk prodhon gjetje ruhet bashkë me
arsyen: analit i panjohur, vlerë e palexueshme, dublikatë. Kjo listë nuk
hyn në kontekst — ajo është material auditimi dhe analize gabimesh.

Pa të, një saktësi e ulët e nxjerrjes nuk do të tregonte nëse faji është
i segmentimit, i hartës së emrave apo i njësive, dhe analiza e gabimeve e
Kapitullit 7 do të mbështetej te ndjesia.

## 5.3.7 Gjendja e zbatimit dhe matja

Kanali dixhital u mat mbi 33 dokumente dixhitale të korpusit sintetik.
Saktësia, mbulimi dhe F1 dolën 1.000 për të katër fushat — analiti,
vlera, njësia dhe intervali — dhe saktësia e klasifikimit gjithashtu
1.000, pa asnjë rresht të hedhur.

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

E3 me OCR mbi tërë korpusin: saktësia e statusit 0.881. Pjesa më e madhe e
gabimeve janë të sigurta — vlerat u bënë "pa interval" sepse intervali
nuk u lexua, dhe SP5 refuzoi interpretimin. Por 62 vlera morën drejtim të
gabuar, ndër to 9 vlera normale të shënuara kritike të larta dhe 1 vlerë
kritike e ulët e shënuar kritike e lartë. Këta janë rastet që kontrolli i
besueshmërisë do t'i ndalte.

Vendimi për të mos e vështirësuar korpusin sintetik, dhe arsyeja e tij,
jepen te seksioni 5.8.

## 5.3.8 Kombinimet ndërmjet analiteve

Rregullat e kombinimit janë të shkruara me dorë në një tabelë burimore
(Tabela 5), një rresht për rregull: një listë kushtesh — analiti dhe
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
