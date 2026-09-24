# 0005 — Refuzimi i interpretimit pa interval referent

**Gjendja:** i zbatuar

## Konteksti

Politika SP5 kërkon që një vlerë pa interval referent të zgjidhshëm të
shënohet e painterpretueshme dhe jo të hamendësohet. Kjo duhej kthyer nga
parim në sjellje të kodit, në disa vende njëherësh.

## Vendimi

Refuzimi zbatohet në tri pika, dhe në secilën prej tyre alternativa e
lehtë do të kishte qenë hamendja:

1. **Modeli i domenit e bën gjendjen e pamundur të pamundur.** Një
   `AnalyteFinding` pa kufij dhe me status tjetër nga `UNINTERPRETABLE`
   nuk ndërtohet dot; validimi dështon në ndërtim.
2. **Gjinia e panjohur nuk zëvendësohet.** Kur dokumenti nuk e shtyp
   gjininë dhe analiti ka kufij të ndryshëm sipas saj, intervali mbetet i
   pazgjidhur. Zgjedhja e njërit prej dy intervaleve do të ishte short.
3. **Njësia e panjohur ndal klasifikimin.** Një vlerë në njësi që nuk
   kthehet dot nuk krahasohet me asnjë interval, prandaj mbetet e
   painterpretueshme.

Gjetja e painterpretueshme **mbahet dhe nuk hidhet**. Pacienti e ka atë
vlerë të shtypur në dokument dhe ka të drejtë ta shohë të renditur, me
shënimin se nuk interpretohet.

## Alternativat e refuzuara

**Hedhja e rreshtit.** Do të kishte dhënë një dalje më të pastër dhe do
të fshihte një matje që laboratori e bëri vërtet. Mungesa e heshtur është
më e keqe se refuzimi i shprehur.

**Interval i parazgjedhur nga tabela pa e ditur gjininë.** Do të rriste
mbulimin e dukshëm të sistemit dhe do të prodhonte klasifikime që duken
të besueshme pa pasur bazë.

## Pasojat

Mbulimi i matur bie: analitet pa interval nuk hyjnë kurrë në statistikat
e klasifikimit si sukses. Kjo është e dëshiruar.

SP5 mat me numër. Vlerësimi raporton veçmas *uninterpretable recall* —
sa nga vlerat pa interval u njohën si të tilla — sepse rastet janë të
pakta dhe saktësia e përgjithshme do t'i fshihte plotësisht.
