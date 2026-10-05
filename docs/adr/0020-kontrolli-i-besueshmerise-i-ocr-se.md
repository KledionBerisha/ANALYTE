# 0020 — Kontrolli i besueshmërisë për vlerat e lexuara nga OCR-ja

**Gjendja:** i zbatuar. I ndezur te shërbimi; i fikur te eksperimentet e ngrira (E7–E9, E6), që rezultatet dhe cache-i i modelit të mbeten të vlefshme.
**Kujdes:** pragjet u zgjodhën pasi u panë gabimet e E3 mbi të njëjtat dokumente mbi të cilat matet kontrolli.

## Konteksti

E3 mati 62 vlera të skanuara me status të interpretuar dhe të gabuar, 11 prej tyre të shënuara "kritike të larta" pa qenë. Një vlerë e lexuar gabim interpretohet me
siguri të plotë dhe pacienti e lexon si të tijën (ADR 0012). Analiza e atyre 62 rasteve (`evaluation/ocr_guard_report.py`) tregoi një shkak të vetëm,
presjen dhjetore që OCR-ja e humb, në dy vende:

- **42 raste: te INTERVALI i shtypur.** "2,5 – 4,5" lexohet "25 – 45"; vlera e saktë 3,9 del "e ulët".
- **20 raste: te VLERA.** "46,6" lexohet "466"; një vlerë normale del "e lartë" ose "kritike e lartë".

OCR-ja e dokumenteve është për pacientët me skanime, ndërsa shtresa e tekstit të PDF-së nuk humb presje; prandaj kontrolli vlen vetëm për faqet e OCR-së
(`PageText.ocr`).

## Vendimi

Dy kontrolle te `grounding/branch_a/ocr_guard.py`, të aplikuara nga `extract` mbi faqet e OCR-së:

1. **Intervali i dëmtuar.** Nëse secili kufi i intervalit të shtypur është afërsisht 10, 100 ose 1000 herë ai i tabelës së brendshme për të njëjtin analit (tolerancë 15%, krahasim me të
   dyja gjinitë), presja ka humbur. Intervali i shtypur hidhet dhe përdoret ai i tabelës, rruga që ekziston tashmë kur intervali nuk shtypet; pa tabelë ose pa gjini gjetja mbetet e
   painterpretueshme (SP5). Zëvendësimi regjistrohet te `Extraction.corrections`.
2. **Vlera e dyshimtë.** Vlera e shtypur pa presje te një analit që laboratori e shtyp me presje, që del MBI intervalin, dhe pjesëtimi me 10 ose 100 e fut brenda tij, nuk merret:
   rreshti refuzohet me arsyen "vlerë e dyshimtë (OCR): presja dhjetore mungon". Një rresht i humbur është më i mirë se një vlerë e gabuar që pacienti e lexon si të vetën (po ai arsyetim si
   te "njësi e palexueshme").

**Pse rreshti hidhet dhe nuk interpretohet si "pa interval".** Njoftimi i SP5 thotë "nuk u gjet interval referent", gjë që te kjo vlerë nuk është e vërtetë; një njoftim i ri do të kërkonte ndryshim të politikës,
të rregullave dhe të kërkesës së modelit. Hedhja përdor mekanizmin që ekziston dhe e ruan arsyen.

**Fikur te eksperimentet.** `build(..., ocr_guard=...)` ka parazgjedhje `True` (shërbimi); pipeline-t e harness-it e kalojnë `False` dhe `--ocr-guard` e ndez. Ndryshe kontekstet e dokumenteve të skanuara do të ndryshonin,
e bashkë me to kërkesat e modelit që cache-i i ka çelës.

## Çfarë u mat

`python -m evaluation.ocr_guard_report` (168 dokumente të skanuara; OCR-ja një herë, nxjerrja pa kontroll dhe me kontroll mbi të njëjtat faqe; `evaluation/results/supplementary/ocr_guard.json`):

| | pa kontroll | me kontroll |
|---|---|---|
| Statuse të interpretuara dhe të gabuara | **62** | **2** |
| Prej tyre kritike të larta pa qenë | 11 | 2 |
| Rreshta të krahasueshëm me të vërtetën | 2 360 | 2 342 |
| Vlera të lexuara gabim ndër ta | 64 | 46 |
| Të interpretueshme që u bënë të painterpretueshme | 986 | 1 009 |

18 rreshta u refuzuan nga kontrolli i vlerës; **të 18 kishin vlerë të lexuar gabim, asnjë e saktë**. 46 intervale u zëvendësuan nga tabela. Dy gabimet e mbetura janë Ht 598 për 59,8 (kritike e lartë në vend
të të lartës; zhvendosja e nxjerr vlerën jashtë intervalit, prandaj kontrolli nuk e kap) dhe Ht 166 për 16,6.
Në harness (E1/E2/E3/E5 me `--ocr --ocr-guard`, ekzekutim zhvillimi nga pema e punës): F1 i nxjerrjes 0.670 → 0.669, saktësia e statusit 0.881 → 0.885, E5 (krahasimi i kryqëzuar) 0.863 → 0.862.

## Çfarë nuk kapet dhe çmimi

- Vlerat e tjera të lexuara gabim (4,35 për 4,3; shifra e zëvendësuar; njësia): ato kalojnë, dhe ato që shënojnë status të gabuar mbeten.
- Një vlerë që ka humbur presjen por del brenda intervalit pas zhvendosjes ("13" për "1,3" kur edhe 13 është brenda), nuk kapet.
- **Një vlerë e vërtetë e shtypur pa presje që plotëson kushtin humbet si rresht.** Shembull hipotetik: kreatininë 8 mg/dL e shtypur "8" në vend të "8,00", interval 0,7–1,3; pjesëtuar me 10 është 0,8, brenda intervalit.
  Te korpusi sintetik kjo nuk ndodh asnjëherë (0 nga 18), sepse gjeneruesi i shtyp vlerat me presjet e analitit; te dokumentet reale formati i laboratorëve të ndryshëm është i panjohur.
  Kjo është pikërisht klasa e rrezikshme (një kritike e vërtetë që nuk shfaqet), prandaj kontrolli duhet testuar mbi skanime reale para se të pretendohet siguri (E13).
- Nuk u shtua kontroll me kufij fiziologjikë absolutë: ata kërkojnë burime të lexuara që nuk ekzistojnë te depoja, dhe asnjë kufi nuk shpiket.

## Pasojat

- E7–E9 dhe auditi mbeten të matura pa kontrollin; ato përshkruajnë sistemin pa të. Shërbimi e ka të ndezur, prandaj matja e E3 me kontroll është ajo që përshkruan atë.
- Rezultatet e kontrollit janë të një ekzekutimi zhvillimi nga pema e punës; duhen rimatur nga një kopje e pastër pasi të commit-ohet kodi.
