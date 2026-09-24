# 5.4 Dega e raportit mjekësor

*Rishikim i shkruar pas zbatimit.*

*Figura 4. Tubacioni i përpunimit të raportit mjekësor*

Dega e dytë merret me tekstin e lirë të mjekut. Ndryshe nga vlerat
laboratorike, ku e vërteta është numër dhe krahasimi është i saktë, këtu
e vërteta është kuptimi i një fjalie — dhe pikërisht ai kuptim është ai
që humbet më lehtë kur teksti thjeshtohet.

## 5.4.1 Gjetja e tekstit dhe ndarja në fjali

Narrativa gjendet në dokument nën titullin e vet dhe mbyllet te
nënshkrimi i mjekut. Rreshtat e mbështjellë bashkohen sërish me një
hapësirë të vetme — veprimi i kundërt i atij që i mbështolli — që teksti
i rindërtuar të jetë varg për varg i njëjtë me atë që u shtyp. Kjo nuk
është kozmetikë: pozicionet e pohimeve maten mbi këtë varg dhe duhet të
mbeten të krahasueshme me anotimin manual.

Ndarja në fjali është e thjeshtë me qëllim. Narrativa e raporteve është
prozë e shkurtër pa shkurtime me pikë, dhe një ndarës më i ndërlikuar do
të fshihte se nga vjen secili pohim.

## 5.4.2 Njohja e termave

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

*Tabela 3. Ekstrakt i tabelës terminologjike*

Tabela përmban 82 zëra. Kolona e burimit mbetet vendmbajtëse dhe duhet
plotësuar përpara dorëzimit: pa referencë të verifikueshme, tabela bëhet
vetë burim informacioni të paverifikuar — pikërisht ajo që SP6 synon të
pengojë.

## 5.4.3 Mohimi dhe pasiguria

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

## 5.4.4 Pohimet dhe krahasimi i kryqëzuar

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

## 5.4.5 Matja

PK4 u mat mbi korpusin sintetik me dy vlera që duhen raportuar të dyja:

- **1.000** mbi dokumentet dixhitale, me mbulim të plotë për të katër
  gjendjet;
- **0.563** mbi tërë korpusin.

I gjithë ndryshimi është kanali i skanuar. Pa njohje optike, ato
dokumente nuk lexohen fare, prandaj çdo gjendje e tyre llogaritet si e
munguar. Eksperimenti E5 nuk ka kufizim kanali në planin e vlerësimit,
prandaj 0.563 është numri që ai prodhon sot dhe do të lëvizë vetëm kur
rruga e OCR-së të ekzistojë.

Mbi gjysmën dixhitale, të gjitha pohimet e burimit u rikthyen me
polaritet, siguri dhe lloj të saktë, dhe termat e pashpjeguar u
identifikuan saktësisht në çdo dokument.

Vlen i njëjti kufizim si te Dega A, dhe këtu ai peshon më shumë: narrativa
sintetike ndërtohet nga fjali të shkruara me dorë, dhe detektorët u
shkruan duke i pasur ato parasysh. Prandaj testet e mohimit dhe të
pasigurisë përdorin fjali të tjera, të shkruara posaçërisht si provë —
një provë mbi shabllonet e gjeneruesit do të tregonte vetëm se kodi
kujton veten. Prova e vërtetë mbetet teksti i mjekëve realë.
