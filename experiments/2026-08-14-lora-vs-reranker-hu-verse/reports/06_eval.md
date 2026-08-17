# F4 — Eval-gate


## Tengely A — stílus és forma (arany)

| feltétel | n | üres | strófaszám | strófaméret | szótag pontos | szótag ±1 | rímséma | rímarány | **rímminőség** | ebből ragrím | ismételt sor | szótáron kívüli | **kitalált szó** | distinct-2 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B0 | 150 | 0% | 0.440 | 0.805 | 0.153 | 0.465 | 0.064 | 0.134 | 0.111 | 0.122 | 0.092 | 0.021 | 0.015 | 0.832 |
| B1 | 150 | 0% | 0.567 | 0.802 | 0.206 | 0.532 | 0.043 | 0.114 | 0.093 | 0.094 | 0.103 | 0.023 | 0.019 | 0.822 |
| B2 | 50 | 0% | 0.700 | 0.938 | 0.409 | 0.750 | 0.141 | 0.236 | 0.203 | 0.120 | 0.122 | 0.019 | 0.013 | 0.810 |
| C | 150 | 0% | 0.573 | 0.735 | 0.203 | 0.562 | 0.087 | 0.177 | 0.139 | 0.147 | 0.118 | 0.067 | 0.044 | 0.828 |
| C2 | 50 | 0% | 0.640 | 0.941 | 0.471 | 0.817 | 0.120 | 0.255 | 0.206 | 0.165 | 0.113 | 0.057 | 0.041 | 0.814 |
| C_ep1 | 150 | 0% | 0.593 | 0.739 | 0.180 | 0.482 | 0.043 | 0.119 | 0.092 | 0.138 | 0.181 | 0.035 | 0.023 | 0.744 |
| GOLD | 50 | 0% | 1.000 | 0.982 | 0.800 | 0.974 | 0.892 | 0.577 | 0.400 | 0.286 | 0.007 | 0.079 | 0.000 | 0.980 |

## Tengely A — stílus és forma (petofi)

| feltétel | n | üres | strófaszám | strófaméret | szótag pontos | szótag ±1 | rímséma | rímarány | **rímminőség** | ebből ragrím | ismételt sor | szótáron kívüli | **kitalált szó** | distinct-2 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| GOLD | 50 | 0% | 1.000 | 1.000 | 0.809 | 1.000 | 0.813 | 0.624 | 0.439 | 0.282 | 0.021 | 0.079 | 0.000 | 0.961 |

A **GOLD** sor az eredeti Arany/Petőfi versek mért értéke ugyanezzel a mérőléccel — ez a feladat gyakorlati felső korlátja. (A `strófaszám` ott értelemszerűen 1,000: a specifikáció magából a versből készült.)


### Megérte-e? — C (LoRA) a baseline-okhoz mérve (arany)

| metrika | B1 (few-shot) | **B2 (few-shot+reranker)** | **C (LoRA)** | C − B2 | GOLD |
|---|---:|---:|---:|---:|---:|
| strófaszám | 0.567 | 0.700 | 0.573 | **-0.127** | 1.000 |
| strófaméret | 0.802 | 0.938 | 0.735 | **-0.203** | 0.982 |
| szótag pontos | 0.206 | 0.409 | 0.203 | **-0.207** | 0.800 |
| szótag ±1 | 0.532 | 0.750 | 0.562 | **-0.188** | 0.974 |
| rímséma | 0.043 | 0.141 | 0.087 | **-0.054** | 0.892 |
| rímarány | 0.114 | 0.236 | 0.177 | **-0.059** | 0.577 |
| **rímminőség** | 0.093 | 0.203 | 0.139 | **-0.064** | 0.400 |
| ebből ragrím | 0.094 | 0.120 | 0.147 | **+0.028** | 0.286 |
| ismételt sor | 0.103 | 0.122 | 0.118 | **-0.004** | 0.007 |
| szótáron kívüli | 0.023 | 0.019 | 0.067 | **+0.048** | 0.079 |
| **kitalált szó** | 0.019 | 0.013 | 0.044 | **+0.031** | 0.000 |
| distinct-2 | 0.822 | 0.810 | 0.828 | **+0.018** | 0.980 |

A **B2 a valódi ellenfél**: a determinisztikus reranker pontosan azokat a formai metrikákat optimalizálja, amelyeket mérünk. A `C − B2` oszlop mutatja, mit tesz hozzá a LoRA azon felül, amit egy jó prompt és egy olcsó utószűrő önmagában is tud. A **rímminőség** (ragrím nélküli rím) az a metrika, amit a reranker nem tud trükkel megnyerni.


## Tengely C — memorizáció (`extraction_gap`)

| feltétel | szerző | train n-gram | holdout n-gram | **gap** | train ≥8 szó | holdout ≥8 szó |
|---|---|---:|---:|---:|---:|---:|
| B0 | arany | 1.48 | 1.38 | **+0.10** | 0% | 0% |
| C | arany | 1.24 | 1.19 | **+0.05** | 0% | 0% |
| C_ep1 | arany | 1.24 | 1.22 | **+0.02** | 0% | 0% |

A **holdout** oszlop a kontroll: azt méri, mennyit reprodukál a modell olyan versből, amit MI nem tanítottunk — ez a pretrainingből jön. Csak a **gap** írható a LoRA számlájára.

