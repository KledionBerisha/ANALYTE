# 0003 — Ndarja e përkufizimeve me gjeneruesin

**Gjendja:** i zbatuar

## Konteksti

Gjeneruesi i korpusit prodhon etiketat e së vërtetës bazë; sistemi
prodhon daljen që krahasohet me to. Disa veprime shfaqen në të dyja
anët: klasifikimi i një vlere kundrejt intervalit, kthimi i njësive,
kërkimi i një termi në tabelë dhe vendimi nëse një pohim përputhet me
një gjetje.

## Vendimi

Aty ku veprimi është **rregull i dhënë**, ai zbatohet një herë dhe ndahet
nga të dyja anët:

- `grounding/branch_a/classify.py` — statusi dhe ashpërsia
- `catalog.py` — faktorët e kthimit të njësive
- `grounding/branch_b/terminology.py::detect_terms` — kërkimi në tabelë
- `grounding/branch_b/crossref.py` — gjendja e krahasimit të kryqëzuar

Aty ku veprimi është **heuristikë**, ai NUK ndahet. Njohja e termave të
panjohur nga morfologjia mbetet vetëm te sistemi; e vërteta bazë e
termave të pashpjeguar vjen nga ajo që gjeneruesi vendosi të fusë.

## Arsyetimi

Rregulli i klasifikimit nuk mësohet dhe nuk hamendësohet: ai përkufizon
se çfarë do të thotë "e lartë". Nëse do të kishim dy zbatime të tij,
ndryshimi mes tyre do të shfaqej në rezultate si gabim i sistemit, dhe
PK2 do të matte mospërputhjen e dy kopjeve të një rregulli në vend që të
matte nxjerrjen.

Përkundrazi, po ta ndanim heuristikën e termave të panjohur, SP6 do të
dukej gjithmonë i plotësuar: sistemi do të krahasohej me vetveten.

## Pasojat

PK2 mat nëse u nxorën vlera dhe interval i duhur, jo nëse rregulli u
mësua. Kjo duhet thënë shprehimisht kur raportohet, përndryshe një lexues
mund ta marrë saktësinë e lartë si dëshmi për diçka që nuk u mat.

Fusha e intervalit te PK1 mbetet pjesërisht tautologjike për rreshtat me
njësi alternative, sepse të dyja anët përdorin të njëjtin faktor kthimi.
Ky është kufizim i njohur dhe i shënuar.
