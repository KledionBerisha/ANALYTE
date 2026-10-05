# 0021 — Katalogu i rregullave `r1.4`: katër rregulla përmirësohen, `r1.3` mbetet i ngrirë

**Gjendja:** i zbatuar. `r1.4` është versioni i parazgjedhur i shërbimit; `r1.3` mbetet versioni me të cilin u matën E4, E6–E11 dhe grupet A, B, C.
**Kujdes:** `r1.4` u hartua pasi u panë gabimet e grupeve A, B, të auditit të E8 dhe të E10. Ato mostra nuk janë më të pastra si provë e tij.

## Konteksti

Rregullat `r1.3` arritën macro F1 0.993 mbi korpusin e korruptuar dhe 0.795 mbi grupin B; auditi i pavarur i E8 gjeti problem të llojeve që
rregullat synojnë te 36% e teksteve që kaluan verifikimin, kryesisht drejtim të gabuar (23%). Grupet A dhe B treguan edhe alarme të rreme
nga trajta e shquar e emrave: "Kolesteroli HDL" lexohej si kolesterol total, dhe "25" te "Vitamina D 25-OH" si numër i pabazuar.
Të gjitha janë të kufizuara në leksik dhe në njohjen e emrave, jo në arkitekturë.

## Vendimi

**Katalogu nuk ndryshon: R1–R9 dhe SP1–SP3.** Katër rregulla përmirësohen brenda të njëjtave lloje shkeljesh (kështu Shtojca C e gjeneruar dhe
`RULE_BY_VIOLATION` mbeten të vlefshme):

1. **R1 dhe R2, njohja e emrave.** Pranohet trajta e shquar dhe e lakuar: `Hemoglobina në gjak`, `Kolesteroli HDL`, `hemoglobinës`,
   `leukociteve`, `klorit`, `përqendrimit mesatar të hemoglobinës` (me "të" në vend të "i"). Emri deri në katër fjalë. Përputhja mbetet e saktë:
   një trajtë e lakuar pranohet vetëm kur e pashquara është formë e njohur dhe vetëm një analit e pretendon; shkurtesat nuk lakohen.
   Emrat e njohur maskohen para kërkimit të numrave (shifrat te "25-OH").
2. **R1, numri i përket analitit.** Te një fjali me një analit të vetëm, një numër që është vlerë ose kufi i një analiti TJETËR shënohet
   (`ungrounded_number`). Fjalitë me dy analite nuk gjykohen për përkatësi.
3. **R3, sipas klauzolës.** Një drejtim për analit, jo një për fjali: fjalia ndahet te kundërvënia (`;`, "ndërsa", "por") dhe te "dhe"; një klauzolë pa analit
   trashëgon analitin e klauzolës paraprake. Fjalori i drejtimit zgjerohet ("e lartë", "të ulta", "rritja e", "u ul") me fjalë të plota.
   Pohimi i përgjithshëm shënohet: "të gjitha vlerat e tjera janë brenda intervalit" kur një gjetje jashtë intervalit nuk është përmendur.
   Kërkohet sasior TOTAL; "në analizat e tjera, natriumi është…" nuk është pohim i përgjithshëm.
4. **R9, shpjegim i shpikur në kllapa.** Një kllapë me dy fjalë ose më shumë, pa shifra, pas një analiti, shkurtese ose termi ("TSH (hormoni i stimulimit
   të mëlçisë)") shënohet (`ungrounded_term_explanation`), përveç kur përputhet me fjalorin (edhe në trajtë tjetër gramatikore), është emër tjetër i të njëjtit
   analit, ose flet për intervalin.

Shpjegimet e fjalorit që shfaqen fjalë për fjalë në tekst hiqen para njohjes së analiteve te R1 dhe R3: shpjegimi i hemoglobinës ("proteina që bart
oksigjenin në qelizat e kuqe") përmban "qelizat e kuqe", emër i eritrociteve, dhe fjalia që e jep nuk flet për eritrocitet.

**Dega B (nxjerrja e pohimeve).** Shtohen pseudo-mohimet "nuk mund të mohohet" dhe "nuk është e pamundur", shenjat e rekomandimit "nevojitet", "nevoja për",
"është e nevojshme", "kërkohet", "indikohet", dhe fjalori i zgjeruar i drejtimit. Ndryshimi nuk ndryshoi asnjë pohim të nxjerrë nga 332 narrativat dixhitale
të korpusit (shuma kontrolluese e pohimeve para dhe pas e njëjtë), kështu që konteksti, kërkesa dhe cache-i i modelit mbeten të pandryshuara.

**Versionimi.** `verify(context, text, rules=...)` zgjedh versionin; `verification/ruleset.py` e mban zgjedhjen në një `ContextVar`. Çdo
`VerificationResult` ruan versionin që e ekzekutoi. Harness-i dhe vlerësuesit e kalojnë `r1.3` si parazgjedhje (`--rules r1.4` për ta ndryshuar);
shërbimi përdor `r1.4`. Kështu çdo numër i raportuar me `r1.3` riprodhohet, dhe cache-i i modelit, që varet nga cilat drafte i ndalonte katalogu, mbetet i vlefshëm.

## Çfarë u mat

Mostrat janë të njëjta për të dy versionet (`python -m evaluation.compare_rules`, rezultati te `evaluation/results/supplementary/rules_r14.json`):

| Matje | `r1.3` | `r1.4` |
|---|---|---|
| Shablloni mbi 500 kontekstet | 0 shkelje | 0 shkelje |
| E10, macro F1 (192 tekste testi) | 0.9925 | 1.000 |
| Grupi B, macro F1 (105 fjali) | 0.795 | 0.843 |
| Grupi B, `direction_mismatch` / `ungrounded_number` F1 | 0.67 / 0.95 | 1.00 / 1.00 |
| Grupi B, tekste të pastra të shënuara | 1 nga 30 | 0 nga 30 |
| Grupi A, shpjegime të shënuara | 5 nga 25 | 0 nga 25 |
| Auditi i E8: tekste të dorëzuara të shënuara (nga 90) | 0 | 25 |
| Prej 40 teksteve me problem të llojeve të rregullave sipas auditit: të shënuara | 0 | 17 (14 me lloj që auditori e ka emërtuar) |
| Prej 38 teksteve që auditori i gjeti të pastra: të shënuara | 0 | 2 |

Të dyja tekstet e shënuara që auditori i kishte gjetur të pastra janë pohime të përgjithshme ku një gjetje jashtë intervalit nuk përmendet (acidi urik; fosfori);
sipas dëshmisë duken gabime të vërteta që auditori i humbi, por kjo nuk u verifikua nga një gjykatës i pavarur.

## Çfarë NUK u përmirësua

- `prohibited_claim` (SP1–SP3) mbetet F1 0.46 mbi B (3 nga 10), dhe `ungrounded_term_explanation` 0.33 (1 nga 5): fjalori i diagnozës, trajtimit dhe prognozës dhe zbulimi i
  shpjegimeve të termave jashtë kllapave nuk u zgjeruan. Shtimi i shprehjeve sipas B do ta kishte kontaminuar edhe më shumë grupin.
- Gjykimi është leksikor dhe sipas klauzolës, jo semantik: një drejtim i shprehur me fjalë që nuk janë te fjalori, ose një vlerë e atribuuar gabim te fjali me dy analite, nuk kapet.
- Tekstet e modelit me 25 shënime nga r1.4 nuk u rigjeneruan: E8, E9 dhe auditi mbeten të matura me `r1.3`. Një E8 me `r1.4` do të ndalonte më shumë drafte, do të kërkonte
  thirrje të reja ndaj modelit dhe do të ngrinte pjesën që përfundon te shablloni (25.2% me `r1.3`); nuk u ekzekutua.

## Kontaminimi

Çdo rregull i ri u hartua duke parë gabime të sakta: shembujt e auditit të E8, alarmet e rreme të A dhe B, dhe vetë grupi B. Prandaj A, B dhe auditi nuk janë më mostra të reja për `r1.4`;
numrat e tabelës më sipër tregojnë sa kap ai defektet e njohura dhe sa e mban pastërtinë e shabllonit, jo si do të sillej mbi tekst të ri. Vlera e tij mbi tekst të pa parë është e pamatur.
Alarmet e rreme që hoqi (trajtat e shquara, pohimi i kllapave) janë, megjithatë, defekte të nxjerrjes së emrave dhe jo përshtatje me një mostër të veçantë.
