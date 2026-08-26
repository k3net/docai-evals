# D2 kontroll — mennyit ér a null-eredmény?

Kör: `results` · középső tartomány: 0–23. sík · matcher: az `analyze_d.py` eredetije + írásjel-tisztított változat.

## naiv lens

### eredeti matcher

- **Elérhetőség:** 10/16 fogalom jelöltszava fordul elő egyáltalán a korpusz top-20 olvasataiban — a többinél (UNT-HU03, UNT-HU04, UNT-HU06, UNT-HU07, UNT-ZH06, UNT-ZH08) a találat szerkezetileg lehetetlen.
- **Pozitív kontroll (ANGOL prompt):** középső síkon 3/16 (UNT-ZH01, UNT-ZH02, UNT-ZH04) · bármely síkon 7/16.
- **Null-eredmény (hu+zh prompt, középső sík):** 0/32 találat.

### tisztított matcher

- **Elérhetőség:** 12/16 fogalom jelöltszava fordul elő egyáltalán a korpusz top-20 olvasataiban — a többinél (UNT-HU04, UNT-HU07, UNT-ZH06, UNT-ZH08) a találat szerkezetileg lehetetlen.
- **Pozitív kontroll (ANGOL prompt):** középső síkon 3/16 (UNT-ZH01, UNT-ZH02, UNT-ZH04) · bármely síkon 8/16.
- **Null-eredmény (hu+zh prompt, középső sík):** 1/32 találat — [('UNT-HU03', 'hu', {20: ['distinction'], 21: ['distinction']})].

## tuned lens

### eredeti matcher

- **Elérhetőség:** 9/16 fogalom jelöltszava fordul elő egyáltalán a korpusz top-20 olvasataiban — a többinél (UNT-HU03, UNT-HU04, UNT-HU05, UNT-HU06, UNT-HU07, UNT-ZH06, UNT-ZH08) a találat szerkezetileg lehetetlen.
- **Pozitív kontroll (ANGOL prompt):** középső síkon 1/16 (UNT-ZH05) · bármely síkon 7/16.
- **Null-eredmény (hu+zh prompt, középső sík):** 0/32 találat.

### tisztított matcher

- **Elérhetőség:** 10/16 fogalom jelöltszava fordul elő egyáltalán a korpusz top-20 olvasataiban — a többinél (UNT-HU03, UNT-HU04, UNT-HU05, UNT-HU07, UNT-ZH06, UNT-ZH08) a találat szerkezetileg lehetetlen.
- **Pozitív kontroll (ANGOL prompt):** középső síkon 1/16 (UNT-ZH05) · bármely síkon 8/16.
- **Null-eredmény (hu+zh prompt, középső sík):** 0/32 találat.

## Következtetés

A pozitív kontroll szerint a műszer érzékenysége alacsony: az angol prompton is csak kevés fogalomnál jelenik meg a közelítőszó a középső síkokon. A nem-angol promptok nullája ezért **gyenge evidencia** a fordítási útvonal ellen — a dolgozat 7. fejezete ennek megfelelően fogalmaz.
