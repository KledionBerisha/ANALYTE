# 0022 — Klasifikuesi i fjalive mbetet alternativë e vlerësuar, jo pjesë e verifikimit të vendosur

**Gjendja:** vendim i marrë më 2026-10-05, me atë që u mat. Klasifikuesi **nuk u rihartua**: nuk kishte të dhëna për ta përmirësuar.

## Konteksti

Klasifikuesi XLM-RoBERTa (ADR 0009) u trajnua për të njohur tetë llojet e shkeljes mbi fjali të korpusit të korruptuar. Kur u
mat mbi tekst që gjeneruesi sintetik nuk e prodhoi, rezultati ishte i dobët:

| Matje | Rezultat |
|---|---|
| E11, korpusi i korruptuar (192 tekste) | macro F1 0.326–0.538, por te rregulli 1 bllokon 29–30 nga 30 tekste të pastra |
| Grupi B (105 fjali të shkruara nga autori) | macro F1 **0.015–0.177** |
| E9 me modelin (OCR, 500 dokumente) | 302 dokumente (60.4%) përfundojnë te shablloni, kundrejt 126 (25.2%) pa klasifikues; të 41 shkeljet që arrijnë te përdoruesi janë alarme të rreme mbi shabllon |
| Rrjedhje (`ml/leakage.py`) | 100% e formave të fjalive me defekt të validimit kanë një formë identike në trajnim |

Aplikacioni i uebit nuk e ngarkon klasifikuesin: `orchestration.tasks.build_services` ndërton vetëm gjeneruesin dhe verifikuesin
me rregulla. Klasifikuesi ekziston te `verification/classifier.py` dhe përdoret vetëm nga harness-i (E9, E11).

## Vendimi

1. **Verifikimi i vendosur është ai me rregulla** (`r1.4`, ADR 0021). Klasifikuesi nuk futet te shërbimi.
2. **Klasifikuesi mbetet në depo si alternativë e vlerësuar**: kodi, rezultatet E9 dhe E11, dhe fakti që ai nuk e kap atë që rregullat
   e humbin (te E9 nuk u audituan tekstet e tij) mbeten si rezultat i punimit, jo si komponent që pretendohet se punon.
3. **Nuk u trajnua një version i ri.** Arsyet janë të dukshme dhe nuk varen nga përpjekja:
   - Problemi është të dhënat: çdo fjali trajnimi vjen nga shabllonet e gjeneruesit, dhe klasifikuesi mëson ato forma. Një model më i
     madh ose më shumë epoka mbi të njëjtin korpus e përforcon këtë, jo e zgjidh.
   - Të dhënat që do ta ndryshonin rezultatin janë fjali natyrale me etiketë të pavarur nga rregullat (të vërteta ose të shkruara nga një
     njeri që nuk ka parë rregullat). Grupet A, B dhe C janë të vetmet dhe janë të rezervuara si provë; rrjedhimisht nuk mund të përdoren për trajnim.
     Tekstet e modelit me etiketa nga vetë rregullat do ta bënin klasifikuesin një kopje të rregullave (qarkullim), dhe nuk do të kapte asgjë që ato e humbin.
   - Trajnimi i XLM-RoBERTa kërkon GPU; kjo makinë ka vetëm CPU, dhe trajnimi kryhet te Colab (vendim i 2026-09-27).

## Çfarë do të duhej për ta ndryshuar këtë vendim

- Një mostër e madhe fjalish natyrale shqip me defekte të etiketuara nga njerëz të pavarur (dokumente reale ose tekst i shkruar me dorë
  në masë), të ndarë që asnjë formë të mos kalojë nga trajnimi te testi.
- Një gjykatës i pavarur ose njerëzor për të matur nëse klasifikuesi kap diçka që `r1.4` nuk e kap, mbi tekstin e modelit (auditi i E9 nuk u krye).
- Gjenerimi i atyre të dhënave është pikërisht E13 (dokumente reale) dhe nuk mund të bëhet pa miratim etik.

## Pasojat

- Hipoteza H2 dhe krahasimi i tre detektorëve (PK6) mbeten si u raportuan; rezultati i klasifikuesit nuk ndryshon.
- Pretendimi i punimit për verifikim me mësim makinerik bëhet më i ngushtë: klasifikuesi u ndërtua, u mat dhe u gjet i pamjaftueshëm mbi tekst
  natyral; verifikimi i vendosur është me rregulla. Kjo thuhet te §7.3 dhe §7.6.
- E9 mbetet me `r1.3` dhe me pragun 0.85 (rregulli 2); nuk u rimat me `r1.4`.
