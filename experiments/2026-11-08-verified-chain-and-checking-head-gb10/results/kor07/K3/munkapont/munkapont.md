# Munkapont a változatlan τ-val (rögzítés utáni, feltáró kiegészítés)

Forrás: `cache/k07/k3`. A τ az F5 CAL-on kapott értéke karonként és családonként; lezárva a SELECT vagy X javaslat, ha a pontszám ≥ τ. Minden item MATCH, ezért az X-lezárás is hiba. A seedes karoknál (B1-4R, B1-R) a három seed átlaga, zárójelben a tartomány. Viszonyításul az F5 TESZT lezárási hibaaránya (a természetes összetételű friss mintán). „Nincs munkapont”: a CAL-on nem volt τ a CP-feltétellel, a kar semmit nem zár le.

## penzugy.bankparositas

| keret | kar | lezárt / n | ebből hibás | hibás arány a lezártakon | ebből csali | ebből X | F5 TESZT lezárási hiba |
|---|---|---|---|---|---|---|---|
| keret4 | B1-4S | nincs munkapont | – | – | – | – | – |
| keret4 | B1-4R | 11 (8–14) / 186 | 11 (8–14) | 100% | 6 | 5 | 2,5% |
| keret4 | B1-4LR | nincs munkapont | – | – | – | – | – |
| keret2 | B1-S | nincs munkapont | – | – | – | – | – |
| keret2 | B1-R | 19 (13–24) / 186 | 17,7 (12–22) | 93% | 14,7 | 3 | 2,8% |
| keret2 | B1-LR | 14 / 186 | 11 | 79% | 9 | 2 | 3,4% |

Bontás (négyállapotú keret, lezárt / n, ebből hibás):

| bontás | B1-4S | B1-4R | B1-4LR |
|---|---|---|---|
| változat B3a-reszfizetes | nincs munkapont | 11 / 186, hibás 11 | nincs munkapont |
| nyelv hu | nincs munkapont | 6,3 / 100, hibás 6,3 | nincs munkapont |
| nyelv en | nincs munkapont | 4,7 / 86, hibás 4,7 | nincs munkapont |

## muszaki.hibaelharitas

| keret | kar | lezárt / n | ebből hibás | hibás arány a lezártakon | ebből csali | ebből X | F5 TESZT lezárási hiba |
|---|---|---|---|---|---|---|---|
| keret4 | B1-4S | 116 / 182 | 46 | 40% | 46 | 0 | 4,7% |
| keret4 | B1-4R | 60,3 (53–69) / 182 | 16 (11–21) | 27% | 11,7 | 4,3 | 1,3% |
| keret4 | B1-4LR | 78 / 182 | 35 | 45% | 32 | 3 | 2,7% |
| keret2 | B1-S | nincs munkapont | – | – | – | – | – |
| keret2 | B1-R | 50,7 (48–55) / 182 | 11,7 (10–13) | 23% | 8,7 | 3 | 2,6% |
| keret2 | B1-LR | 109 / 182 | 43 | 39% | 43 | 0 | 2,4% |

Bontás (négyállapotú keret, lezárt / n, ebből hibás):

| bontás | B1-4S | B1-4R | B1-4LR |
|---|---|---|---|
| változat H3-valtas | 116 / 182, hibás 46 | 60,3 / 182, hibás 16 | 78 / 182, hibás 35 |
| nyelv hu | 50 / 86, hibás 19 | 29 / 86, hibás 6,7 | 40 / 86, hibás 20 |
| nyelv en | 66 / 96, hibás 27 | 31,3 / 96, hibás 9,3 | 38 / 96, hibás 15 |

## szabaly.koltsegelszamolas

| keret | kar | lezárt / n | ebből hibás | hibás arány a lezártakon | ebből csali | ebből X | F5 TESZT lezárási hiba |
|---|---|---|---|---|---|---|---|
| keret4 | B1-4S | 36 / 199 | 36 | 100% | 36 | 0 | 2,8% |
| keret4 | B1-4R | 151 (143–155) / 199 | 122,3 (116–127) | 81% | 119,3 | 3 | 3,8% |
| keret4 | B1-4LR | 138 / 199 | 107 | 78% | 104 | 3 | 3,2% |
| keret2 | B1-S | nincs munkapont | – | – | – | – | – |
| keret2 | B1-R | 132,3 (128–139) / 199 | 107,3 (103–113) | 81% | 105,3 | 2 | 3,2% |
| keret2 | B1-LR | 21 / 199 | 21 | 100% | 19 | 2 | 3,3% |

Bontás (négyállapotú keret, lezárt / n, ebből hibás):

| bontás | B1-4S | B1-4R | B1-4LR |
|---|---|---|---|
| változat S3a-netto | 3 / 100, hibás 3 | 75 / 100, hibás 60,7 | 54 / 100, hibás 38 |
| változat S3b-deviza | 33 / 99, hibás 33 | 76 / 99, hibás 61,7 | 84 / 99, hibás 69 |
| nyelv hu | 1 / 100, hibás 1 | 66,7 / 100, hibás 39 | 67 / 100, hibás 38 |
| nyelv en | 35 / 99, hibás 35 | 84,3 / 99, hibás 83,3 | 71 / 99, hibás 69 |
