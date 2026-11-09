# 07 F5 utáni feltáró elemzés: az állapotjelzés a bankon (gépi lap, `feltaro07.py`)

**Feltáró, nem megerősítő:** a CAL és a TESZT az F5-ben elköltve; az itt választott küszöb csak friss adaton igazolható. Temperature: a B1-4-é (D2).

## Döntések állapotonként (TESZT)

| család | állapot | SELECT | NONE | MISSING | OOS |
|---|---|---|---|---|---|
| penzugy.bankparositas | MATCH | 600 | 0 | 0 | 0 |
| penzugy.bankparositas | MISSING_DATA | 99 | 1 | 0 | 0 |
| penzugy.bankparositas | NO_MATCH | 66 | 132 | 2 | 0 |
| penzugy.bankparositas | OUT_OF_SCOPE | 0 | 100 | 0 | 0 |
| muszaki.hibaelharitas | MATCH | 598 | 2 | 0 | 0 |
| muszaki.hibaelharitas | MISSING_DATA | 15 | 18 | 67 | 0 |
| muszaki.hibaelharitas | NO_MATCH | 61 | 129 | 8 | 2 |
| muszaki.hibaelharitas | OUT_OF_SCOPE | 0 | 2 | 37 | 61 |
| szabaly.koltsegelszamolas | MATCH | 600 | 0 | 0 | 0 |
| szabaly.koltsegelszamolas | MISSING_DATA | 49 | 0 | 51 | 0 |
| szabaly.koltsegelszamolas | NO_MATCH | 51 | 149 | 0 | 0 |
| szabaly.koltsegelszamolas | OUT_OF_SCOPE | 0 | 80 | 4 | 16 |

## Szétválasztás (AUROC; CAL / TESZT)

| család | MISSING vs MATCH, SELECT-en: p(Y) | −gap | ikerarány r | OOS vs NO_MATCH, X-en: p(Z)/(p(X)+p(Z)) |
|---|---|---|---|---|
| penzugy.bankparositas | 0.963 / 0.959 | 0.998 / 0.998 | 0.998 / 0.998 | 0.205 / 0.227 |
| muszaki.hibaelharitas | 0.988 / 0.995 | 0.966 / 0.947 | – / – | 0.745 / 0.698 |
| szabaly.koltsegelszamolas | 0.987 / 0.998 | 0.942 / 0.934 | – / – | 0.804 / 0.832 |

## A bank ikerpárja (TESZT)

- MISSING_top1_ikres: 0.990
- MISSING_r_median: 0.677
- MATCH_goldikres_n: 253
- MATCH_goldikres_r_median: 0.023
- AUROC_r_MISSING_vs_MATCH_SELECT: 0.998
- AUROC_r_MISSING_vs_MATCHgoldikres_SELECT: 0.995
- MISSING p(Y) medián / p90: 0.028 / 0.114; MATCH: 0.002 / 0.008

## Szabályok: küszöb a CAL-on (a védett állapot ≤ 5%-a fordulhat), hatás a TESZT-en

| család | szabály | küszöb | cél: jelzett előtte → utána / n | védett átfordul / n | más állapot átfordul | szigorú helyes előtte → utána / n |
|---|---|---|---|---|---|---|
| penzugy.bankparositas | iker | 0.101 | 0 → 99 / 100 | 24 / 600 | – | 732 → 807 / 1000 |
| penzugy.bankparositas | py | 0.009 | 0 → 80 / 100 | 40 / 600 | {'NO_MATCH': 41} | 732 → 772 / 1000 |
| penzugy.bankparositas | oos | 0.155 | 0 → 3 / 100 | 19 / 200 | – | 732 → 716 / 1000 |
| muszaki.hibaelharitas | oos | 0.419 | 61 → 62 / 100 | 9 / 200 | – | 850 → 842 / 1000 |
| szabaly.koltsegelszamolas | oos | 0.339 | 16 → 49 / 100 | 7 / 200 | – | 805 → 831 / 1000 |

## Az ikerszabály hatása a banki K2-re (r* = 0.101, 2000 replika, TESZT)

| kar | változat | hasznos lefedettség [95%] | lezárási hiba [95%] | lezárt | helyes adatbekérés | τ alatt | munkapont nélküli replika |
|---|---|---|---|---|---|---|---|
| B1-4S | eredeti | 0.0 [0.0; 44.0] | nan [2.5; 6.1] | 0.0 | 0% | 99.8 | 90% |
| B1-4S | ikerszabaly | 0.0 [0.0; 44.0] | nan [2.5; 6.1] | 0.0 | 99% | 87.5 | 90% |
| B1-4S | Δ hasznos lef. | +0.0 [+0.0; +0.0] | | | | | |
| B1-4R | eredeti | 59.4 [0.0; 68.0] | 2.5 [0.7; 4.9] | 60.9 | 0% | 38.9 | 18% |
| B1-4R | ikerszabaly | 57.5 [0.0; 66.4] | 2.2 [0.7; 4.3] | 58.8 | 99% | 28.7 | 23% |
| B1-4R | Δ hasznos lef. | -1.9 [-23.4; +0.0] | | | | | |
