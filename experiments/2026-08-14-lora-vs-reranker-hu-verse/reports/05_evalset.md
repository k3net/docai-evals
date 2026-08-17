# F1.5 — Rögzített értékelő szett

| szerző | generálási prompt | extraction próba (train/holdout) | few-shot példa |
|---|---:|---:|---:|
| Arany János | 50 | 50 / 37 | 4 |
| Petőfi Sándor | 50 | 50 / 50 | 4 |

A generálási promptok a **holdout** versek címéből és mért formai jellemzőiből épülnek — a modell soha nem látott verset ír, de az elvárás gépileg ellenőrizhető. A few-shot példák kizárólag a **train** szeletből jönnek: holdout-példa a B1 baseline-ban szivárgás lenne.

