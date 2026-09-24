# 5.2.1 Kontrata e të dhënave

*Rishikim i seksionit 5.2, i shkruar pas zbatimit.*

Garancia qendrore e arkitekturës nuk zbatohet përmes udhëzimeve në
kërkesën drejtuar modelit gjuhësor por përmes kontratës së të dhënave.
Kjo është arsyeja pse kontrata u shkrua e para, përpara çdo shtrese
tjetër, dhe pse ajo nuk ndryshoi gjatë zbatimit të komponentëve që e
përdorin.

## Objekti i vetëm i kalimit

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

## Tri vendime që e bëjnë kontratën të zbatueshme

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

## Pastërtia e paketës së domenit

Paketa e modeleve nuk importon asgjë nga pjesa tjetër e sistemit. Kjo nuk
mbetet konventë: një test lexon pemën sintaksore të çdo moduli të saj dhe
dështon nëse ndonjë import del jashtë listës së lejuar.

Arsyeja është e thjeshtë. Kontrata mban formën e të dhënave për pesë
shtresa dhe për gjeneruesin e korpusit njëkohësisht. Sapo ajo të fillojë
të varet nga persistenca ose nga gjenerimi, ndryshimi i atyre shtresave e
prish atë në heshtje, dhe etiketat e korpusit ndalojnë së përputhuri me
daljen e sistemit pa asnjë shenjë të dukshme.
