# F4/3 — Szerző-klasszifikátor

TF-IDF (szó 1–2-gram + karakter 3–5-gram) + logisztikus regresszió. Tanítva 7195 blokkon a **train** szeletből, validálva 432 **holdout** blokkon.

| | érték |
|---|---:|
| holdout pontosság | **91.0%** |
| többségi alaplap | 59.0% |
| Arany János F1 | 0.888 |
| Petőfi Sándor F1 | 0.924 |

## A generált szövegek osztályozása

| feltétel | célszerző | n | eltalálva (`author_clf_acc`) |
|---|---|---:|---:|
| B0 | Arany János | 150 | 38.7% |
| B1 | Arany János | 149 | 56.4% |
| B2 | Arany János | 50 | 56.0% |
| C | Arany János | 150 | 77.3% |
| C2 | Arany János | 50 | 92.0% |
| C_ep1 | Arany János | 150 | 68.0% |
