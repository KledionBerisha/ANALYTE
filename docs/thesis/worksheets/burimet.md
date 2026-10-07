# Fletë pune: burimet që mungojnë

*Gjeneruar nga `python scripts/build_source_worksheets.py`; mos e redaktoni këtu. Burimin e shkruani te kolona `source_ref` e `resources/terminology.csv` ose `resources/patterns.csv`, pastaj ekzekutoni skriptin sërish.*

**Rregulla.** Shkruani vetëm burim që e keni lexuar dhe që e mbështet pohimin e kolonës «Pohimi». Nëse shpjegimi shqip është përkthimi juaj, thoni këtë te `source_ref`. Zërin që nuk e gjeni, fshijeni: termi bëhet «i pashpjeguar» (SP6), kombinimi hiqet. Asnjë citim nuk është shkruar këtu: rreshti «Ku të kërkohet» tregon lloje burimesh, jo burime.

Mbeten: **0** terma dhe **0** kombinime.

Asnjë zë nuk mbetet pa burim. Burimet e lexuara dhe evidenca e secilit janë te `docs/thesis/worksheets/burimet_e_gjetura.md`.

## Kombinimet e analiteve

Për secilin: një udhëzues ose standard i mjekësisë laboratorike që e lidh këtë kombinim me kërkesën që mjeku ta shohë (jo me diagnozë: SP1). Konfirmoni edhe shigjetat. Mentori ose një mjek duhet t'i rishikojë.

| Kodi | Pohimi (kombinimi) | Fusha | Burimi i lexuar | Faqja ose seksioni |
|---|---|---|---|---|

## Termat

## Pas leximit

1. Kontrolloni që asnjë shpjegim nuk përmban numër ose pohim diagnostik.
2. Shkruani burimin te `source_ref`; ekzekutoni `python scripts/build_tables.py` dhe `python scripts/build_appendices.py` që T3, T5 dhe Shtojca A të pasqyrojnë burimet.
3. Ekzekutoni `python -m pytest`: testet e terminologjisë dhe të kombinimeve do t'ju tregojnë nëse fshirja e një zëri prish diçka.
