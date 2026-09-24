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
mbi dokumente reale. E para pret zbatimin e njohjes optike; e dyta pret
miratimin etik. Deri atëherë, PK1 raportohet me këtë kufizim të shprehur.

Faza e zbulimit të kombinimeve ndërmjet analiteve, e përshkruar në
planifikim, nuk është zbatuar ende.
