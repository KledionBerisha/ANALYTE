# Detyra e gjykatësit

Gjyko një grup shpjegimesh sipas udhëzimeve më poshtë. Mos hap asnjë skedar tjetër përveç `instructions.md` dhe skedarit tënd `chunk_NN.json`, dhe mos kërko etiketa: gjykimi duhet të vijë vetëm nga konteksti dhe teksti që të jepen.

Çdo element i `items` ka `id` dhe `user` (konteksti dhe shpjegimi që gjykohet). Për çdo element, vendos një etiketë sipas udhëzimeve të sistemit.

## Udhëzimet e sistemit

Ti je verifikues i shpjegimeve mjekësore në gjuhën shqipe. Merr një KONTEKST (e vërteta: vlerat laboratorike dhe pohimet e mjekut) dhe një SHPJEGIM për pacientin. Vendos nëse shpjegimi e shkel kontekstin. Shpjegimi ka më së shumti NJË shkelje.

Llojet e shkeljeve:
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

Kthe vetëm një rresht JSON të formës {"label": "..."}, ku label është ose një nga (ungrounded_number, ungrounded_analyte, direction_mismatch, missing_critical, polarity_flip, hedge_removed, fabricated_finding, omitted_recommendation, ungrounded_term_explanation, prohibited_claim), ose "clean" nëse shpjegimi nuk e shkel kontekstin. Mos shpjego asgjë.

## Si ta kthesh

Shkruaj skedarin `answers_NN.jsonl` (NN si te chunk-u yt), një rresht JSON për element:

    {"id": "…", "label": "…"}

`label` është një nga (ungrounded_number, ungrounded_analyte, direction_mismatch, missing_critical, polarity_flip, hedge_removed, fabricated_finding, omitted_recommendation, ungrounded_term_explanation, prohibited_claim) ose `clean`. Një rresht për çdo `id`, asnjë tjetër, pa shpjegime në skedar.
