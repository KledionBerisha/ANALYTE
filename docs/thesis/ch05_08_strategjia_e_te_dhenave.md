# 5.8 Strategjia e të dhënave

*Rishikim i seksionit 5.8.1, i shkruar pas ndërtimit të gjeneruesit.*

## 5.8.1 Korpusi sintetik

Korpusi sintetik është burimi parësor i vlerësimit. Ai prodhon
njëkohësisht dy gjëra që mbahen rreptësisht të ndara: dokumentin PDF që
sheh sistemi, dhe skedarin me të vërtetën bazë që sistemi nuk e sheh
kurrë.

### Rendi i veprimeve

Rendi me të cilin ndërtohet një dokument nuk është i rastësishëm.
Zgjidhet i pari statusi i synuar, pastaj kampionohet një vlerë që e
plotëson atë, pastaj vendoset mënyra e shtypjes — njësia, prania e
intervalit, presja dhjetore — dhe vetëm në fund rillogaritet statusi i
vërtetë mbi vlerën dhe intervalin ashtu si dalin të shtypura.

Nëse do të ruhej statusi i synuar, një dokument që shtyp interval paksa
të ndryshëm nga tabela e brendshme do të mbante etiketë të rreme. Kjo
është forma më e rrezikshme e gabimit në një korpus me etiketa: ai nuk
dështon, ai mat diçka tjetër nga ajo që mendon se mat.

### Variacioni i shtypjes

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

### Narrativa

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

### Simulimi i skanimit

Rreth 35% e dokumenteve kthehen në fotografi letre: anim, turbullim,
zhurmë, njolla dhe artefakte kompresimi, pa asnjë shtresë teksti.

Dokumenti i skanuar nuk vizatohet ndryshe. Ai vizatohet njësoj dhe pastaj
prishet, prandaj përmbajtja e të dy kanaleve është identike dhe çdo
ndryshim në rezultatet e PK1 dhe PK2 i atribuohet kanalit e jo tekstit.
Kutitë kufizuese rrotullohen bashkë me faqen; përndryshe e vërteta bazë
do të tregonte vende ku nuk ka më asgjë.

### Përsëritshmëria

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

### Çfarë mat dhe çfarë nuk mat ky korpus

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
