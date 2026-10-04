# Detyra e auditorit

Audito një grup shpjegimesh sipas udhëzimeve më poshtë. Mos hap asnjë skedar tjetër përveç `instructions.md` dhe skedarit tënd `chunk_NN.json`. Gjykimi duhet të vijë vetëm nga konteksti dhe teksti që të jepen.

Çdo element i `items` ka `id` dhe `user` (konteksti dhe shpjegimi që auditohet).

## Udhëzimet

Ti auditon shpjegime mjekësore në gjuhën shqipe që do t'i shfaqen pacientit. Merr një KONTEKST (e vërteta: vlerat laboratorike dhe pohimet e mjekut) dhe një SHPJEGIM. Gjej ÇDO problem në shpjegim kundrejt kontekstit. Mund të ketë zero, një ose disa.

Llojet e problemeve:
- ungrounded_number: Çdo numër në tekst duhet të gjendet ndër numrat e mbështetur të kontekstit.
- ungrounded_analyte: Çdo analit i përmendur duhet të jetë ndër analitet e matura.
- direction_mismatch: Drejtimi i pohuar duhet të përputhet me statusin e klasifikuar.
- missing_critical: Çdo gjetje kritike duhet të shfaqet në dalje.
- polarity_flip: Polariteti i pohimit të mjekut nuk guxon të përmbyset.
- hedge_removed: Pasiguria e shprehur nga mjeku nuk guxon të hiqet.
- fabricated_finding: Asnjë gjetje që mungon në kontekst nuk guxon të shtohet.
- omitted_recommendation: Çdo rekomandim i mjekut duhet të ruhet në dalje.
- ungrounded_term_explanation: Asnjë term jashtë tabelës terminologjike nuk guxon të shpjegohet.
- prohibited_claim: Asnjë pohim diagnostik, trajtimi apo prognoze.
- other_unsupported: një pohim që nuk jepet te konteksti dhe që nuk është një nga llojet e mësipërme — njohuri mjekësore e shtuar (p.sh. çfarë bën një test ose një qelizë), interpretim, qetësim ose alarmim ('nuk është e rrezikshme'), këshillë, krahasim me të tjerë, apo çdo informacion tjetër që pacienti nuk e merr nga konteksti.

Mos e quaj problem: tekstet e detyrueshme të sistemit (njoftimi për vlera kritike, shënimi përmbyllës, njoftimi që një term ose vlerë nuk shpjegohet), citimet e mjekut me parashtesën 'Mjeku ka shënuar:' kur përputhen me pohimet e dhëna, dhe shpjegimet e termave që jepen te konteksti (edhe riformuluar pa shtuar asgjë).

Për çdo element, kthe një rresht JSON: {"id": "...", "problems": [{"label": "...", "quote": "fjalët e shpjegimit që e shkaktojnë, deri në 15 fjalë"}]}. `problems` është [] kur shpjegimi nuk ka asnjë problem.

## Si ta kthesh

Shkruaj `answers_NN.jsonl` (NN si te chunk-u yt): një rresht JSON për çdo `id`, pa asnjë rresht tjetër. `label` është një nga (ungrounded_number, ungrounded_analyte, direction_mismatch, missing_critical, polarity_flip, hedge_removed, fabricated_finding, omitted_recommendation, ungrounded_term_explanation, prohibited_claim, other_unsupported).
