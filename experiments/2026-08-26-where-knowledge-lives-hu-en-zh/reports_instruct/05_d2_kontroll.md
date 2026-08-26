# D2 kontroll — mennyit ér a null-eredmény?

Kör: `results_instruct` · középső tartomány: 0–23. sík · matcher: az `analyze_d.py` eredetije + írásjel-tisztított változat.

## naiv lens

### eredeti matcher

- **Elérhetőség:** 4/16 fogalom jelöltszava fordul elő egyáltalán a korpusz top-20 olvasataiban — a többinél (UNT-HU01, UNT-HU03, UNT-HU04, UNT-HU05, UNT-HU06, UNT-HU07, UNT-HU08, UNT-ZH01, UNT-ZH04, UNT-ZH06, UNT-ZH07, UNT-ZH08) a találat szerkezetileg lehetetlen.
- **Pozitív kontroll (ANGOL prompt):** középső síkon 0/16 (—) · bármely síkon 2/16.
- **Null-eredmény (hu+zh prompt, középső sík):** 0/32 találat.

### tisztított matcher

- **Elérhetőség:** 5/16 fogalom jelöltszava fordul elő egyáltalán a korpusz top-20 olvasataiban — a többinél (UNT-HU01, UNT-HU04, UNT-HU05, UNT-HU06, UNT-HU07, UNT-HU08, UNT-ZH01, UNT-ZH04, UNT-ZH06, UNT-ZH07, UNT-ZH08) a találat szerkezetileg lehetetlen.
- **Pozitív kontroll (ANGOL prompt):** középső síkon 0/16 (—) · bármely síkon 2/16.
- **Null-eredmény (hu+zh prompt, középső sík):** 0/32 találat.

## tuned lens

### eredeti matcher

- **Elérhetőség:** 5/16 fogalom jelöltszava fordul elő egyáltalán a korpusz top-20 olvasataiban — a többinél (UNT-HU01, UNT-HU03, UNT-HU04, UNT-HU05, UNT-HU06, UNT-HU07, UNT-ZH01, UNT-ZH03, UNT-ZH04, UNT-ZH06, UNT-ZH08) a találat szerkezetileg lehetetlen.
- **Pozitív kontroll (ANGOL prompt):** középső síkon 0/16 (—) · bármely síkon 1/16.
- **Null-eredmény (hu+zh prompt, középső sík):** 0/32 találat.

### tisztított matcher

- **Elérhetőség:** 6/16 fogalom jelöltszava fordul elő egyáltalán a korpusz top-20 olvasataiban — a többinél (UNT-HU01, UNT-HU04, UNT-HU05, UNT-HU06, UNT-HU07, UNT-ZH01, UNT-ZH03, UNT-ZH04, UNT-ZH06, UNT-ZH08) a találat szerkezetileg lehetetlen.
- **Pozitív kontroll (ANGOL prompt):** középső síkon 0/16 (—) · bármely síkon 1/16.
- **Null-eredmény (hu+zh prompt, középső sík):** 0/32 találat.

## Következtetés

A pozitív kontroll szerint a műszer érzékenysége alacsony: az angol prompton is csak kevés fogalomnál jelenik meg a közelítőszó a középső síkokon. A nem-angol promptok nullája ezért **gyenge evidencia** a fordítási útvonal ellen — a dolgozat 7. fejezete ennek megfelelően fogalmaz.
