# Magyar KIE-eval — mérés-részletek (generált)

> Forrás: `magyar-kie-eval/reports/*.json` · generátor `src/reszletek.py` · minden szám számolt. Mérce: greedy, minden item 3× (hosszú 1×, izoláció 5×), a többségi kimenet pontozva. A kalibrációs kör (`kalibracio-flash.json`, 76/100) a pontozó-javítás ELŐTTI, nem összevethető — kihagyva. A hosszú suite-ból a T22 GT-je az iratból visszaparszolt; az LLM-bírói mezők (T1-01 `ertelmezes`, T7-09 `indoklas`) 2 pontja minden modellre elérhetetlen.

## Fő suite (T1–T10, 50 item × 3 futás, 100 pont)

### `Flash IQ4_XS · llama.cpp · 4k keret` — meres-flash-next.json

- **futtatott esetek:** 50 item, 150 sikeres futás, 0 hibás

| Metrika | Medián | Min | Max |
|---|---|---|---|
| Prompt tokenek | **6 052** | 1 844 | 24 440 |
| Kimeneti tokenek | **307** | 139 | 3 703 |
| Decode tok/s (motor-mérés, llama.cpp `timings`) | **25,3** | 21,5 | 27,1 |
| Kimeneti tok/s (válaszidőre, TTFT-vel — mindkét motoron azonos képlet) | **24,5** | 9,1 | 26,6 |
| Teljes válaszidő (ms) | **15 440** | 5 753 | 149 899 |

- **JSON-validitás:** 150/150 (100 %)
- **Csonkolt (finish_reason=length):** 0/150
- **Instabil item (eltérő kimenet azonos greedy kérésre):** 0/50
- **Pontszám (többségi kimenet):** **98,00 / 100** (LLM-bírói 2 pont elérhetetlen, elérhető max 98)

| Teszt | Pont | Max | Instabil item |
|---|---|---|---|
| **T1** | 9,00 | 10 | — |
| **T2** | 10,00 | 10 | — |
| **T3** | 10,00 | 10 | — |
| **T4** | 10,00 | 10 | — |
| **T5** | 10,00 | 10 | — |
| **T6** | 10,00 | 10 | — |
| **T7** | 9,00 | 10 | — |
| **T8** | 10,00 | 10 | — |
| **T9** | 10,00 | 10 | — |
| **T10** | 10,00 | 10 | — |

| Mező | Egyezés | Eltérések (első 2) |
|---|---|---|
| `index_tipusa` | 1/1 (100 %) | — |
| `bazis_idoszak` | 1/1 (100 %) | — |
| `elso_indexalas` | 1/1 (100 %) | — |
| `plafon_szazalek` | 2/2 (100 %) | — |
| `negativ_index_kezelese` | 1/1 (100 %) | — |
| `kerekites` | 1/1 (100 %) | — |
| `kotber_szazalek` | 5/5 (100 %) | — |
| `kotber_osszeg_ft` | 5/5 (100 %) | — |
| `alkalmazott_plafon` | 5/5 (100 %) | — |
| `hatarido` | 5/5 (100 %) | — |
| `szamitas_alapja` | 6/6 (100 %) | — |
| `szemelyek` | 1/1 (100 %) | — |
| `cegek` | 1/1 (100 %) | — |
| `atado` | 1/1 (100 %) | — |
| `atvevo` | 1/1 (100 %) | — |
| `szerepel` | 1/1 (100 %) | — |
| `vezeteknev_teljes_alak` | 1/1 (100 %) | — |
| `vegosszeg_egyezik` | 1/1 (100 %) | — |
| `elteres_ft` | 1/1 (100 %) | — |
| `iranya` | 1/1 (100 %) | — |
| `jogcim` | 1/1 (100 %) | — |
| `alanyi_adomentes` | 1/1 (100 %) | — |
| `tetelek` | 1/1 (100 %) | — |
| `egysegar` | 1/1 (100 %) | — |
| `mennyiseg` | 1/1 (100 %) | — |
| `eloleg_brutto_ft` | 1/1 (100 %) | — |
| `eloleg_szazalek` | 1/1 (100 %) | — |
| `ertek_ft` | 8/8 (100 %) | — |
| `hivatkozasi_lanc` | 1/1 (100 %) | — |
| `kamat_alapja` | 1/1 (100 %) | — |
| `tovabb_hivatkozott_pont` | 1/1 (100 %) | — |
| `hivatkozott_pont` | 2/2 (100 %) | — |
| `letezik` | 1/1 (100 %) | — |
| `forras` | 1/1 (100 %) | — |
| `itelet` | 8/8 (100 %) | — |
| `hatalyos_forras` | 5/5 (100 %) | — |
| `valasz` | 2/2 (100 %) | — |
| `valasz_ft` | 2/2 (100 %) | — |
| `emeles_szazalek` | 1/1 (100 %) | — |
| `idopont` | 2/2 (100 %) | — |
| `osszeg_ft` | 2/2 (100 %) | — |
| `megnevezes` | 1/1 (100 %) | — |
| `forras_szakasz` | 1/1 (100 %) | — |

### `Flash NVFP4 · vLLM+mmap-PLE · MTP=2 · 16k keret` — meres-flash-nvfp4.json

- **futtatott esetek:** 50 item, 150 sikeres futás, 0 hibás

| Metrika | Medián | Min | Max |
|---|---|---|---|
| Prompt tokenek | **6 064** | 1 856 | 24 452 |
| Kimeneti tokenek | **368** | 123 | 16 384 |
| Kimeneti tok/s (válaszidőre, TTFT-vel — mindkét motoron azonos képlet) | **26,4** | 8,6 | 36,1 |
| Teljes válaszidő (ms) | **17 021** | 6 944 | 454 409 |

- **JSON-validitás:** 149/150 (99 %)
- **Csonkolt (finish_reason=length):** 1/150 — ebből ÜRES tartalom: 1
- **Instabil item (eltérő kimenet azonos greedy kérésre):** 13/50
- **Pontszám (többségi kimenet):** **97,00 / 100** (LLM-bírói 2 pont elérhetetlen, elérhető max 98)

| Teszt | Pont | Max | Instabil item |
|---|---|---|---|
| **T1** | 9,00 | 10 | 1 |
| **T2** | 10,00 | 10 | — |
| **T3** | 9,00 | 10 | 3 |
| **T4** | 10,00 | 10 | 1 |
| **T5** | 10,00 | 10 | 1 |
| **T6** | 10,00 | 10 | 5 |
| **T7** | 9,00 | 10 | 1 |
| **T8** | 10,00 | 10 | — |
| **T9** | 10,00 | 10 | — |
| **T10** | 10,00 | 10 | 1 |

| Mező | Egyezés | Eltérések (első 2) |
|---|---|---|
| `hatarido` | 4/5 (80 %) | `T3-05`: GT `"2026-11-23"` → `"2026-11-20"` |
| `index_tipusa` | 1/1 (100 %) | — |
| `bazis_idoszak` | 1/1 (100 %) | — |
| `elso_indexalas` | 1/1 (100 %) | — |
| `plafon_szazalek` | 2/2 (100 %) | — |
| `negativ_index_kezelese` | 1/1 (100 %) | — |
| `kerekites` | 1/1 (100 %) | — |
| `kotber_szazalek` | 5/5 (100 %) | — |
| `kotber_osszeg_ft` | 5/5 (100 %) | — |
| `alkalmazott_plafon` | 5/5 (100 %) | — |
| `szamitas_alapja` | 6/6 (100 %) | — |
| `szemelyek` | 1/1 (100 %) | — |
| `cegek` | 1/1 (100 %) | — |
| `atado` | 1/1 (100 %) | — |
| `atvevo` | 1/1 (100 %) | — |
| `szerepel` | 1/1 (100 %) | — |
| `vezeteknev_teljes_alak` | 1/1 (100 %) | — |
| `vegosszeg_egyezik` | 1/1 (100 %) | — |
| `elteres_ft` | 1/1 (100 %) | — |
| `iranya` | 1/1 (100 %) | — |
| `jogcim` | 1/1 (100 %) | — |
| `alanyi_adomentes` | 1/1 (100 %) | — |
| `tetelek` | 1/1 (100 %) | — |
| `egysegar` | 1/1 (100 %) | — |
| `mennyiseg` | 1/1 (100 %) | — |
| `eloleg_brutto_ft` | 1/1 (100 %) | — |
| `eloleg_szazalek` | 1/1 (100 %) | — |
| `ertek_ft` | 8/8 (100 %) | — |
| `hivatkozasi_lanc` | 1/1 (100 %) | — |
| `kamat_alapja` | 1/1 (100 %) | — |
| `tovabb_hivatkozott_pont` | 1/1 (100 %) | — |
| `hivatkozott_pont` | 2/2 (100 %) | — |
| `letezik` | 1/1 (100 %) | — |
| `forras` | 1/1 (100 %) | — |
| `itelet` | 8/8 (100 %) | — |
| `hatalyos_forras` | 5/5 (100 %) | — |
| `valasz` | 2/2 (100 %) | — |
| `valasz_ft` | 2/2 (100 %) | — |
| `emeles_szazalek` | 1/1 (100 %) | — |
| `idopont` | 2/2 (100 %) | — |
| `osszeg_ft` | 2/2 (100 %) | — |
| `megnevezes` | 1/1 (100 %) | — |
| `forras_szakasz` | 1/1 (100 %) | — |

### `35B FP8 · vLLM · MTP=2 · 4k keret` — meres-qwen36.json

- **futtatott esetek:** 50 item, 150 sikeres futás, 0 hibás

| Metrika | Medián | Min | Max |
|---|---|---|---|
| Prompt tokenek | **6 026** | 1 818 | 24 414 |
| Kimeneti tokenek | **1 608** | 317 | 4 096 |
| Kimeneti tok/s (válaszidőre, TTFT-vel — mindkét motoron azonos képlet) | **61,2** | 50,1 | 64,6 |
| Teljes válaszidő (ms) | **26 170** | 6 237 | 66 201 |

- **JSON-validitás:** 144/150 (96 %)
- **Csonkolt (finish_reason=length):** 6/150 — ebből ÜRES tartalom: 6
- **Instabil item (eltérő kimenet azonos greedy kérésre):** 0/50
- **Pontszám (többségi kimenet):** **92,00 / 100** (LLM-bírói 2 pont elérhetetlen, elérhető max 98)

| Teszt | Pont | Max | Instabil item |
|---|---|---|---|
| **T1** | 9,00 | 10 | — |
| **T2** | 10,00 | 10 | — |
| **T3** | 7,00 | 10 | — |
| **T4** | 8,00 | 10 | — |
| **T5** | 10,00 | 10 | — |
| **T6** | 10,00 | 10 | — |
| **T7** | 8,00 | 10 | — |
| **T8** | 10,00 | 10 | — |
| **T9** | 10,00 | 10 | — |
| **T10** | 10,00 | 10 | — |

| Mező | Egyezés | Eltérések (első 2) |
|---|---|---|
| `hatarido` | 3/4 (75 %) | `T3-02`: GT `"2026-08-24"` → `"2026-08-21"` |
| `itelet` | 7/8 (88 %) | `T7-08`: GT `"NEM DÖNTHETŐ EL"` → `"HAMIS"` |
| `index_tipusa` | 1/1 (100 %) | — |
| `bazis_idoszak` | 1/1 (100 %) | — |
| `elso_indexalas` | 1/1 (100 %) | — |
| `plafon_szazalek` | 2/2 (100 %) | — |
| `negativ_index_kezelese` | 1/1 (100 %) | — |
| `kerekites` | 1/1 (100 %) | — |
| `kotber_szazalek` | 5/5 (100 %) | — |
| `kotber_osszeg_ft` | 5/5 (100 %) | — |
| `alkalmazott_plafon` | 5/5 (100 %) | — |
| `szamitas_alapja` | 5/5 (100 %) | — |
| `szemelyek` | 1/1 (100 %) | — |
| `cegek` | 1/1 (100 %) | — |
| `atado` | 1/1 (100 %) | — |
| `atvevo` | 1/1 (100 %) | — |
| `vezeteknev_teljes_alak` | 1/1 (100 %) | — |
| `vegosszeg_egyezik` | 1/1 (100 %) | — |
| `elteres_ft` | 1/1 (100 %) | — |
| `iranya` | 1/1 (100 %) | — |
| `jogcim` | 1/1 (100 %) | — |
| `alanyi_adomentes` | 1/1 (100 %) | — |
| `tetelek` | 1/1 (100 %) | — |
| `egysegar` | 1/1 (100 %) | — |
| `mennyiseg` | 1/1 (100 %) | — |
| `eloleg_brutto_ft` | 1/1 (100 %) | — |
| `eloleg_szazalek` | 1/1 (100 %) | — |
| `ertek_ft` | 8/8 (100 %) | — |
| `hivatkozasi_lanc` | 1/1 (100 %) | — |
| `kamat_alapja` | 1/1 (100 %) | — |
| `tovabb_hivatkozott_pont` | 1/1 (100 %) | — |
| `hivatkozott_pont` | 2/2 (100 %) | — |
| `letezik` | 1/1 (100 %) | — |
| `forras` | 1/1 (100 %) | — |
| `hatalyos_forras` | 5/5 (100 %) | — |
| `valasz` | 2/2 (100 %) | — |
| `valasz_ft` | 2/2 (100 %) | — |
| `emeles_szazalek` | 1/1 (100 %) | — |
| `idopont` | 2/2 (100 %) | — |
| `osszeg_ft` | 2/2 (100 %) | — |
| `megnevezes` | 1/1 (100 %) | — |
| `forras_szakasz` | 1/1 (100 %) | — |

### `35B FP8 · vLLM · MTP=2 · 16k keret` — meres-qwen36-16k.json

- **futtatott esetek:** 50 item, 150 sikeres futás, 0 hibás

| Metrika | Medián | Min | Max |
|---|---|---|---|
| Prompt tokenek | **6 026** | 1 818 | 24 414 |
| Kimeneti tokenek | **1 608** | 317 | 7 045 |
| Kimeneti tok/s (válaszidőre, TTFT-vel — mindkét motoron azonos képlet) | **60,4** | 49,8 | 62,9 |
| Teljes válaszidő (ms) | **26 723** | 6 129 | 114 375 |

- **JSON-validitás:** 150/150 (100 %)
- **Csonkolt (finish_reason=length):** 0/150
- **Instabil item (eltérő kimenet azonos greedy kérésre):** 0/50
- **Pontszám (többségi kimenet):** **96,00 / 100** (LLM-bírói 2 pont elérhetetlen, elérhető max 98)

| Teszt | Pont | Max | Instabil item |
|---|---|---|---|
| **T1** | 9,00 | 10 | — |
| **T2** | 10,00 | 10 | — |
| **T3** | 9,00 | 10 | — |
| **T4** | 10,00 | 10 | — |
| **T5** | 10,00 | 10 | — |
| **T6** | 10,00 | 10 | — |
| **T7** | 8,00 | 10 | — |
| **T8** | 10,00 | 10 | — |
| **T9** | 10,00 | 10 | — |
| **T10** | 10,00 | 10 | — |

| Mező | Egyezés | Eltérések (első 2) |
|---|---|---|
| `hatarido` | 4/5 (80 %) | `T3-02`: GT `"2026-08-24"` → `"2026-08-21"` |
| `itelet` | 7/8 (88 %) | `T7-08`: GT `"NEM DÖNTHETŐ EL"` → `"HAMIS"` |
| `index_tipusa` | 1/1 (100 %) | — |
| `bazis_idoszak` | 1/1 (100 %) | — |
| `elso_indexalas` | 1/1 (100 %) | — |
| `plafon_szazalek` | 2/2 (100 %) | — |
| `negativ_index_kezelese` | 1/1 (100 %) | — |
| `kerekites` | 1/1 (100 %) | — |
| `kotber_szazalek` | 5/5 (100 %) | — |
| `kotber_osszeg_ft` | 5/5 (100 %) | — |
| `alkalmazott_plafon` | 5/5 (100 %) | — |
| `szamitas_alapja` | 6/6 (100 %) | — |
| `szemelyek` | 1/1 (100 %) | — |
| `cegek` | 1/1 (100 %) | — |
| `atado` | 1/1 (100 %) | — |
| `atvevo` | 1/1 (100 %) | — |
| `szerepel` | 1/1 (100 %) | — |
| `vezeteknev_teljes_alak` | 1/1 (100 %) | — |
| `vegosszeg_egyezik` | 1/1 (100 %) | — |
| `elteres_ft` | 1/1 (100 %) | — |
| `iranya` | 1/1 (100 %) | — |
| `jogcim` | 1/1 (100 %) | — |
| `alanyi_adomentes` | 1/1 (100 %) | — |
| `tetelek` | 1/1 (100 %) | — |
| `egysegar` | 1/1 (100 %) | — |
| `mennyiseg` | 1/1 (100 %) | — |
| `eloleg_brutto_ft` | 1/1 (100 %) | — |
| `eloleg_szazalek` | 1/1 (100 %) | — |
| `ertek_ft` | 8/8 (100 %) | — |
| `hivatkozasi_lanc` | 1/1 (100 %) | — |
| `kamat_alapja` | 1/1 (100 %) | — |
| `tovabb_hivatkozott_pont` | 1/1 (100 %) | — |
| `hivatkozott_pont` | 2/2 (100 %) | — |
| `letezik` | 1/1 (100 %) | — |
| `forras` | 1/1 (100 %) | — |
| `hatalyos_forras` | 5/5 (100 %) | — |
| `valasz` | 2/2 (100 %) | — |
| `valasz_ft` | 2/2 (100 %) | — |
| `emeles_szazalek` | 1/1 (100 %) | — |
| `idopont` | 2/2 (100 %) | — |
| `osszeg_ft` | 2/2 (100 %) | — |
| `megnevezes` | 1/1 (100 %) | — |
| `forras_szakasz` | 1/1 (100 %) | — |

### `122B NVFP4 · vLLM · 16k keret` — meres-122b.json

- **futtatott esetek:** 50 item, 150 sikeres futás, 0 hibás

| Metrika | Medián | Min | Max |
|---|---|---|---|
| Prompt tokenek | **6 026** | 1 818 | 24 414 |
| Kimeneti tokenek | **992** | 381 | 4 715 |
| Kimeneti tok/s (válaszidőre, TTFT-vel — mindkét motoron azonos képlet) | **25,3** | 16,5 | 27,3 |
| Teljes válaszidő (ms) | **40 317** | 16 444 | 183 599 |

- **JSON-validitás:** 150/150 (100 %)
- **Csonkolt (finish_reason=length):** 0/150
- **Instabil item (eltérő kimenet azonos greedy kérésre):** 0/50
- **Pontszám (többségi kimenet):** **97,00 / 100** (LLM-bírói 2 pont elérhetetlen, elérhető max 98)

| Teszt | Pont | Max | Instabil item |
|---|---|---|---|
| **T1** | 9,00 | 10 | — |
| **T2** | 10,00 | 10 | — |
| **T3** | 9,00 | 10 | — |
| **T4** | 10,00 | 10 | — |
| **T5** | 10,00 | 10 | — |
| **T6** | 10,00 | 10 | — |
| **T7** | 9,00 | 10 | — |
| **T8** | 10,00 | 10 | — |
| **T9** | 10,00 | 10 | — |
| **T10** | 10,00 | 10 | — |

| Mező | Egyezés | Eltérések (első 2) |
|---|---|---|
| `hatarido` | 4/5 (80 %) | `T3-02`: GT `"2026-08-24"` → `"2026-08-21"` |
| `index_tipusa` | 1/1 (100 %) | — |
| `bazis_idoszak` | 1/1 (100 %) | — |
| `elso_indexalas` | 1/1 (100 %) | — |
| `plafon_szazalek` | 2/2 (100 %) | — |
| `negativ_index_kezelese` | 1/1 (100 %) | — |
| `kerekites` | 1/1 (100 %) | — |
| `kotber_szazalek` | 5/5 (100 %) | — |
| `kotber_osszeg_ft` | 5/5 (100 %) | — |
| `alkalmazott_plafon` | 5/5 (100 %) | — |
| `szamitas_alapja` | 6/6 (100 %) | — |
| `szemelyek` | 1/1 (100 %) | — |
| `cegek` | 1/1 (100 %) | — |
| `atado` | 1/1 (100 %) | — |
| `atvevo` | 1/1 (100 %) | — |
| `szerepel` | 1/1 (100 %) | — |
| `vezeteknev_teljes_alak` | 1/1 (100 %) | — |
| `vegosszeg_egyezik` | 1/1 (100 %) | — |
| `elteres_ft` | 1/1 (100 %) | — |
| `iranya` | 1/1 (100 %) | — |
| `jogcim` | 1/1 (100 %) | — |
| `alanyi_adomentes` | 1/1 (100 %) | — |
| `tetelek` | 1/1 (100 %) | — |
| `egysegar` | 1/1 (100 %) | — |
| `mennyiseg` | 1/1 (100 %) | — |
| `eloleg_brutto_ft` | 1/1 (100 %) | — |
| `eloleg_szazalek` | 1/1 (100 %) | — |
| `ertek_ft` | 8/8 (100 %) | — |
| `hivatkozasi_lanc` | 1/1 (100 %) | — |
| `kamat_alapja` | 1/1 (100 %) | — |
| `tovabb_hivatkozott_pont` | 1/1 (100 %) | — |
| `hivatkozott_pont` | 2/2 (100 %) | — |
| `letezik` | 1/1 (100 %) | — |
| `forras` | 1/1 (100 %) | — |
| `itelet` | 8/8 (100 %) | — |
| `hatalyos_forras` | 5/5 (100 %) | — |
| `valasz` | 2/2 (100 %) | — |
| `valasz_ft` | 2/2 (100 %) | — |
| `emeles_szazalek` | 1/1 (100 %) | — |
| `idopont` | 2/2 (100 %) | — |
| `osszeg_ft` | 2/2 (100 %) | — |
| `megnevezes` | 1/1 (100 %) | — |
| `forras_szakasz` | 1/1 (100 %) | — |

## Nehéz suite (T11–T20, 10 item × 3 futás, 100 pont)

### `Flash IQ4_XS · llama.cpp` — nehez-flash.json

- **futtatott esetek:** 10 item, 30 sikeres futás, 0 hibás

| Metrika | Medián | Min | Max |
|---|---|---|---|
| Prompt tokenek | **3 339** | 3 263 | 9 182 |
| Kimeneti tokenek | **634** | 186 | 2 352 |
| Decode tok/s (motor-mérés, llama.cpp `timings`) | **25,9** | 24,2 | 26,2 |
| Kimeneti tok/s (válaszidőre, TTFT-vel — mindkét motoron azonos képlet) | **25,0** | 14,9 | 26,0 |
| Teljes válaszidő (ms) | **26 493** | 7 368 | 104 144 |

- **JSON-validitás:** 30/30 (100 %)
- **Csonkolt (finish_reason=length):** 0/30
- **Instabil item (eltérő kimenet azonos greedy kérésre):** 0/10
- **Pontszám (többségi kimenet):** **91,33 / 100**

| Teszt | Pont | Max | Instabil item |
|---|---|---|---|
| **T11** | 8,00 | 10 | — |
| **T12** | 10,00 | 10 | — |
| **T13** | 10,00 | 10 | — |
| **T14** | 10,00 | 10 | — |
| **T15** | 10,00 | 10 | — |
| **T16** | 10,00 | 10 | — |
| **T17** | 10,00 | 10 | — |
| **T18** | 10,00 | 10 | — |
| **T19** | 3,33 | 10 | — |
| **T20** | 10,00 | 10 | — |

| Mező | Egyezés | Eltérések (első 2) |
|---|---|---|
| `dij_2027_01_01_ft` | 0/1 (0 %) | `T11-01`: GT `2230000` → `2226000` |
| `dij_2026_09_15_ft` | 0/1 (0 %) | `T19-01`: GT `2100000` → `1850000` |
| `m2_hatalyat_erinti_e` | 0/1 (0 %) | `T19-01`: GT `false` → `true` |
| `dij_2028_01_01_ft` | 1/1 (100 %) | — |
| `dij_2029_01_01_ft` | 1/1 (100 %) | — |
| `plafonozott_ev` | 1/1 (100 %) | — |
| `kerekites_modja` | 1/1 (100 %) | — |
| `felmondasi_ido_nap` | 1/1 (100 %) | — |
| `donto_irat` | 1/1 (100 %) | — |
| `alapszerzodes_megallapit_e` | 1/1 (100 %) | — |
| `fizetendo_ft` | 1/1 (100 %) | — |
| `szammal_kiirt_ft` | 1/1 (100 %) | — |
| `elter_e` | 1/1 (100 %) | — |
| `iranyado` | 1/1 (100 %) | — |
| `koltseget_viseli` | 1/1 (100 %) | — |
| `donto_pont` | 1/1 (100 %) | — |
| `engedely_datuma` | 1/1 (100 %) | — |
| `eves_osszeg_ft` | 1/1 (100 %) | — |
| `alkalmazott_arfolyam` | 1/1 (100 %) | — |
| `uzemeltetesi_alapdij_ft_ho` | 1/1 (100 %) | — |
| `hatarido` | 1/1 (100 %) | — |
| `munkanapban_szamolva` | 1/1 (100 %) | — |
| `elteres_oka` | 1/1 (100 %) | — |
| `fel_neve` | 1/1 (100 %) | — |
| `szerepe` | 1/1 (100 %) | — |
| `kiallitja` | 1/1 (100 %) | — |
| `cimzettje` | 1/1 (100 %) | — |
| `berbeado_eszrevetel_cimzettje` | 1/1 (100 %) | — |
| `dij_2026_08_31_ft` | 1/1 (100 %) | — |
| `szemelyi_serules_plafon` | 1/1 (100 %) | — |
| `vagyoni_karra_van_plafon` | 1/1 (100 %) | — |
| `vagyoni_plafon_ft` | 1/1 (100 %) | — |

### `Flash NVFP4 · vLLM+mmap-PLE · MTP=2` — nehez-flash-nvfp4.json

- **futtatott esetek:** 10 item, 30 sikeres futás, 0 hibás

| Metrika | Medián | Min | Max |
|---|---|---|---|
| Prompt tokenek | **3 351** | 3 275 | 9 194 |
| Kimeneti tokenek | **688** | 227 | 10 178 |
| Kimeneti tok/s (válaszidőre, TTFT-vel — mindkét motoron azonos képlet) | **28,3** | 25,0 | 31,0 |
| Teljes válaszidő (ms) | **24 866** | 8 593 | 350 840 |

- **JSON-validitás:** 30/30 (100 %)
- **Csonkolt (finish_reason=length):** 0/30
- **Instabil item (eltérő kimenet azonos greedy kérésre):** 0/10
- **Pontszám (többségi kimenet):** **100,00 / 100**

| Teszt | Pont | Max | Instabil item |
|---|---|---|---|
| **T11** | 10,00 | 10 | — |
| **T12** | 10,00 | 10 | — |
| **T13** | 10,00 | 10 | — |
| **T14** | 10,00 | 10 | — |
| **T15** | 10,00 | 10 | — |
| **T16** | 10,00 | 10 | — |
| **T17** | 10,00 | 10 | — |
| **T18** | 10,00 | 10 | — |
| **T19** | 10,00 | 10 | — |
| **T20** | 10,00 | 10 | — |

| Mező | Egyezés | Eltérések (első 2) |
|---|---|---|
| `dij_2027_01_01_ft` | 1/1 (100 %) | — |
| `dij_2028_01_01_ft` | 1/1 (100 %) | — |
| `dij_2029_01_01_ft` | 1/1 (100 %) | — |
| `plafonozott_ev` | 1/1 (100 %) | — |
| `kerekites_modja` | 1/1 (100 %) | — |
| `felmondasi_ido_nap` | 1/1 (100 %) | — |
| `donto_irat` | 1/1 (100 %) | — |
| `alapszerzodes_megallapit_e` | 1/1 (100 %) | — |
| `fizetendo_ft` | 1/1 (100 %) | — |
| `szammal_kiirt_ft` | 1/1 (100 %) | — |
| `elter_e` | 1/1 (100 %) | — |
| `iranyado` | 1/1 (100 %) | — |
| `koltseget_viseli` | 1/1 (100 %) | — |
| `donto_pont` | 1/1 (100 %) | — |
| `engedely_datuma` | 1/1 (100 %) | — |
| `eves_osszeg_ft` | 1/1 (100 %) | — |
| `alkalmazott_arfolyam` | 1/1 (100 %) | — |
| `uzemeltetesi_alapdij_ft_ho` | 1/1 (100 %) | — |
| `hatarido` | 1/1 (100 %) | — |
| `munkanapban_szamolva` | 1/1 (100 %) | — |
| `elteres_oka` | 1/1 (100 %) | — |
| `fel_neve` | 1/1 (100 %) | — |
| `szerepe` | 1/1 (100 %) | — |
| `kiallitja` | 1/1 (100 %) | — |
| `cimzettje` | 1/1 (100 %) | — |
| `berbeado_eszrevetel_cimzettje` | 1/1 (100 %) | — |
| `dij_2026_08_31_ft` | 1/1 (100 %) | — |
| `dij_2026_09_15_ft` | 1/1 (100 %) | — |
| `m2_hatalyat_erinti_e` | 1/1 (100 %) | — |
| `szemelyi_serules_plafon` | 1/1 (100 %) | — |
| `vagyoni_karra_van_plafon` | 1/1 (100 %) | — |
| `vagyoni_plafon_ft` | 1/1 (100 %) | — |

### `35B FP8 · vLLM` — nehez-qwen36.json

- **futtatott esetek:** 10 item, 30 sikeres futás, 0 hibás

| Metrika | Medián | Min | Max |
|---|---|---|---|
| Prompt tokenek | **3 313** | 3 237 | 9 156 |
| Kimeneti tokenek | **2 382** | 1 358 | 4 496 |
| Kimeneti tok/s (válaszidőre, TTFT-vel — mindkét motoron azonos képlet) | **62,3** | 60,5 | 63,7 |
| Teljes válaszidő (ms) | **38 244** | 22 340 | 72 054 |

- **JSON-validitás:** 30/30 (100 %)
- **Csonkolt (finish_reason=length):** 0/30
- **Instabil item (eltérő kimenet azonos greedy kérésre):** 0/10
- **Pontszám (többségi kimenet):** **98,00 / 100**

| Teszt | Pont | Max | Instabil item |
|---|---|---|---|
| **T11** | 8,00 | 10 | — |
| **T12** | 10,00 | 10 | — |
| **T13** | 10,00 | 10 | — |
| **T14** | 10,00 | 10 | — |
| **T15** | 10,00 | 10 | — |
| **T16** | 10,00 | 10 | — |
| **T17** | 10,00 | 10 | — |
| **T18** | 10,00 | 10 | — |
| **T19** | 10,00 | 10 | — |
| **T20** | 10,00 | 10 | — |

| Mező | Egyezés | Eltérések (első 2) |
|---|---|---|
| `dij_2027_01_01_ft` | 0/1 (0 %) | `T11-01`: GT `2230000` → `2226000` |
| `dij_2028_01_01_ft` | 1/1 (100 %) | — |
| `dij_2029_01_01_ft` | 1/1 (100 %) | — |
| `plafonozott_ev` | 1/1 (100 %) | — |
| `kerekites_modja` | 1/1 (100 %) | — |
| `felmondasi_ido_nap` | 1/1 (100 %) | — |
| `donto_irat` | 1/1 (100 %) | — |
| `alapszerzodes_megallapit_e` | 1/1 (100 %) | — |
| `fizetendo_ft` | 1/1 (100 %) | — |
| `szammal_kiirt_ft` | 1/1 (100 %) | — |
| `elter_e` | 1/1 (100 %) | — |
| `iranyado` | 1/1 (100 %) | — |
| `koltseget_viseli` | 1/1 (100 %) | — |
| `donto_pont` | 1/1 (100 %) | — |
| `engedely_datuma` | 1/1 (100 %) | — |
| `eves_osszeg_ft` | 1/1 (100 %) | — |
| `alkalmazott_arfolyam` | 1/1 (100 %) | — |
| `uzemeltetesi_alapdij_ft_ho` | 1/1 (100 %) | — |
| `hatarido` | 1/1 (100 %) | — |
| `munkanapban_szamolva` | 1/1 (100 %) | — |
| `elteres_oka` | 1/1 (100 %) | — |
| `fel_neve` | 1/1 (100 %) | — |
| `szerepe` | 1/1 (100 %) | — |
| `kiallitja` | 1/1 (100 %) | — |
| `cimzettje` | 1/1 (100 %) | — |
| `berbeado_eszrevetel_cimzettje` | 1/1 (100 %) | — |
| `dij_2026_08_31_ft` | 1/1 (100 %) | — |
| `dij_2026_09_15_ft` | 1/1 (100 %) | — |
| `m2_hatalyat_erinti_e` | 1/1 (100 %) | — |
| `szemelyi_serules_plafon` | 1/1 (100 %) | — |
| `vagyoni_karra_van_plafon` | 1/1 (100 %) | — |
| `vagyoni_plafon_ft` | 1/1 (100 %) | — |

### `122B NVFP4 · vLLM` — nehez-122b.json

- **futtatott esetek:** 10 item, 30 sikeres futás, 0 hibás

| Metrika | Medián | Min | Max |
|---|---|---|---|
| Prompt tokenek | **3 313** | 3 237 | 9 156 |
| Kimeneti tokenek | **1 911** | 467 | 5 608 |
| Kimeneti tok/s (válaszidőre, TTFT-vel — mindkét motoron azonos képlet) | **26,3** | 24,6 | 27,0 |
| Teljes válaszidő (ms) | **71 754** | 18 268 | 213 614 |

- **JSON-validitás:** 30/30 (100 %)
- **Csonkolt (finish_reason=length):** 0/30
- **Instabil item (eltérő kimenet azonos greedy kérésre):** 0/10
- **Pontszám (többségi kimenet):** **98,00 / 100**

| Teszt | Pont | Max | Instabil item |
|---|---|---|---|
| **T11** | 8,00 | 10 | — |
| **T12** | 10,00 | 10 | — |
| **T13** | 10,00 | 10 | — |
| **T14** | 10,00 | 10 | — |
| **T15** | 10,00 | 10 | — |
| **T16** | 10,00 | 10 | — |
| **T17** | 10,00 | 10 | — |
| **T18** | 10,00 | 10 | — |
| **T19** | 10,00 | 10 | — |
| **T20** | 10,00 | 10 | — |

| Mező | Egyezés | Eltérések (első 2) |
|---|---|---|
| `dij_2027_01_01_ft` | 0/1 (0 %) | `T11-01`: GT `2230000` → `2226000` |
| `dij_2028_01_01_ft` | 1/1 (100 %) | — |
| `dij_2029_01_01_ft` | 1/1 (100 %) | — |
| `plafonozott_ev` | 1/1 (100 %) | — |
| `kerekites_modja` | 1/1 (100 %) | — |
| `felmondasi_ido_nap` | 1/1 (100 %) | — |
| `donto_irat` | 1/1 (100 %) | — |
| `alapszerzodes_megallapit_e` | 1/1 (100 %) | — |
| `fizetendo_ft` | 1/1 (100 %) | — |
| `szammal_kiirt_ft` | 1/1 (100 %) | — |
| `elter_e` | 1/1 (100 %) | — |
| `iranyado` | 1/1 (100 %) | — |
| `koltseget_viseli` | 1/1 (100 %) | — |
| `donto_pont` | 1/1 (100 %) | — |
| `engedely_datuma` | 1/1 (100 %) | — |
| `eves_osszeg_ft` | 1/1 (100 %) | — |
| `alkalmazott_arfolyam` | 1/1 (100 %) | — |
| `uzemeltetesi_alapdij_ft_ho` | 1/1 (100 %) | — |
| `hatarido` | 1/1 (100 %) | — |
| `munkanapban_szamolva` | 1/1 (100 %) | — |
| `elteres_oka` | 1/1 (100 %) | — |
| `fel_neve` | 1/1 (100 %) | — |
| `szerepe` | 1/1 (100 %) | — |
| `kiallitja` | 1/1 (100 %) | — |
| `cimzettje` | 1/1 (100 %) | — |
| `berbeado_eszrevetel_cimzettje` | 1/1 (100 %) | — |
| `dij_2026_08_31_ft` | 1/1 (100 %) | — |
| `dij_2026_09_15_ft` | 1/1 (100 %) | — |
| `m2_hatalyat_erinti_e` | 1/1 (100 %) | — |
| `szemelyi_serules_plafon` | 1/1 (100 %) | — |
| `vagyoni_karra_van_plafon` | 1/1 (100 %) | — |
| `vagyoni_plafon_ft` | 1/1 (100 %) | — |

## Hosszú kontextus suite (T21–T25, 5 item × 1 futás, 217k token, 100 pont)

### `Flash IQ4_XS · llama.cpp · cache_prompt=false` — hosszu-flash.json

- **futtatott esetek:** 5 item, 5 sikeres futás, 0 hibás

| Metrika | Medián | Min | Max |
|---|---|---|---|
| Prompt tokenek | **217 351** | 217 332 | 217 426 |
| Kimeneti tokenek | **675** | 215 | 5 736 |
| Decode tok/s (motor-mérés, llama.cpp `timings`) | **7,7** | 7,7 | 7,8 |
| Kimeneti tok/s (válaszidőre, TTFT-vel — mindkét motoron azonos képlet) | **0,6** | 0,2 | 3,2 |
| Teljes válaszidő (ms) | **1 121 462** | 1 009 193 | 1 794 654 |

- **JSON-validitás:** 5/5 (100 %)
- **Csonkolt (finish_reason=length):** 0/5
- **Instabil item (eltérő kimenet azonos greedy kérésre):** 0/5
- **Pontszám (többségi kimenet):** **100,00 / 100**

| Teszt | Pont | Max | Instabil item |
|---|---|---|---|
| **T21** | 20,00 | 20 | — |
| **T22** | 20,00 | 20 | — |
| **T23** | 20,00 | 20 | — |
| **T24** | 20,00 | 20 | — |
| **T25** | 20,00 | 20 | — |

| Mező | Egyezés | Eltérések (első 2) |
|---|---|---|
| `oradij_2024_ft` | 1/1 (100 %) | — |
| `oradij_2025_ft` | 1/1 (100 %) | — |
| `oradij_2026_ft` | 1/1 (100 %) | — |
| `munkadij_2026_ft` | 1/1 (100 %) | — |
| `esemenyek_szama` | 1/1 (100 %) | — |
| `osszkoltseg_ft` | 1/1 (100 %) | — |
| `hatalyos_munkanap` | 1/1 (100 %) | — |
| `eredeti_munkanap` | 1/1 (100 %) | — |
| `feluliro_pont` | 1/1 (100 %) | — |
| `azonosito` | 1/1 (100 %) | — |
| `terulet` | 1/1 (100 %) | — |
| `bejelentve` | 1/1 (100 %) | — |
| `tetoszigeteles_garancia_lejar` | 1/1 (100 %) | — |
| `aggregat_tipusjel` | 1/1 (100 %) | — |
| `vizora_gyari_szam` | 1/1 (100 %) | — |
| `liftkarbantarto_szerzodesszam` | 1/1 (100 %) | — |
| `tuzjelzo_felulvizsgalat` | 1/1 (100 %) | — |

### `Flash IQ4_XS · llama.cpp · prompt-cache MELEG` — hosszu-flash-cache.json

- **futtatott esetek:** 5 item, 5 sikeres futás, 0 hibás

| Metrika | Medián | Min | Max |
|---|---|---|---|
| Prompt tokenek | **217 351** | 217 332 | 217 426 |
| Kimeneti tokenek | **738** | 215 | 5 300 |
| Decode tok/s (motor-mérés, llama.cpp `timings`) | **7,7** | 7,7 | 7,8 |
| Kimeneti tok/s (válaszidőre, TTFT-vel — mindkét motoron azonos képlet) | **7,3** | 6,6 | 7,6 |
| Teljes válaszidő (ms) | **100 716** | 32 652 | 694 245 |

- **JSON-validitás:** 5/5 (100 %)
- **Csonkolt (finish_reason=length):** 0/5
- **Instabil item (eltérő kimenet azonos greedy kérésre):** 0/5
- **Pontszám (többségi kimenet):** **100,00 / 100**

| Teszt | Pont | Max | Instabil item |
|---|---|---|---|
| **T21** | 20,00 | 20 | — |
| **T22** | 20,00 | 20 | — |
| **T23** | 20,00 | 20 | — |
| **T24** | 20,00 | 20 | — |
| **T25** | 20,00 | 20 | — |

| Mező | Egyezés | Eltérések (első 2) |
|---|---|---|
| `oradij_2024_ft` | 1/1 (100 %) | — |
| `oradij_2025_ft` | 1/1 (100 %) | — |
| `oradij_2026_ft` | 1/1 (100 %) | — |
| `munkadij_2026_ft` | 1/1 (100 %) | — |
| `esemenyek_szama` | 1/1 (100 %) | — |
| `osszkoltseg_ft` | 1/1 (100 %) | — |
| `hatalyos_munkanap` | 1/1 (100 %) | — |
| `eredeti_munkanap` | 1/1 (100 %) | — |
| `feluliro_pont` | 1/1 (100 %) | — |
| `azonosito` | 1/1 (100 %) | — |
| `terulet` | 1/1 (100 %) | — |
| `bejelentve` | 1/1 (100 %) | — |
| `tetoszigeteles_garancia_lejar` | 1/1 (100 %) | — |
| `aggregat_tipusjel` | 1/1 (100 %) | — |
| `vizora_gyari_szam` | 1/1 (100 %) | — |
| `liftkarbantarto_szerzodesszam` | 1/1 (100 %) | — |
| `tuzjelzo_felulvizsgalat` | 1/1 (100 %) | — |

### `Flash NVFP4 · vLLM+mmap-PLE · MTP=2` — hosszu-flash-nvfp4.json

- **futtatott esetek:** 5 item, 5 sikeres futás, 0 hibás

| Metrika | Medián | Min | Max |
|---|---|---|---|
| Prompt tokenek | **217 363** | 217 344 | 217 438 |
| Kimeneti tokenek | **1 831** | 497 | 9 617 |
| Kimeneti tok/s (válaszidőre, TTFT-vel — mindkét motoron azonos képlet) | **10,9** | 4,0 | 24,5 |
| Teljes válaszidő (ms) | **157 295** | 122 604 | 392 613 |

- **JSON-validitás:** 5/5 (100 %)
- **Csonkolt (finish_reason=length):** 0/5
- **Instabil item (eltérő kimenet azonos greedy kérésre):** 0/5
- **Pontszám (többségi kimenet):** **100,00 / 100**

| Teszt | Pont | Max | Instabil item |
|---|---|---|---|
| **T21** | 20,00 | 20 | — |
| **T22** | 20,00 | 20 | — |
| **T23** | 20,00 | 20 | — |
| **T24** | 20,00 | 20 | — |
| **T25** | 20,00 | 20 | — |

| Mező | Egyezés | Eltérések (első 2) |
|---|---|---|
| `oradij_2024_ft` | 1/1 (100 %) | — |
| `oradij_2025_ft` | 1/1 (100 %) | — |
| `oradij_2026_ft` | 1/1 (100 %) | — |
| `munkadij_2026_ft` | 1/1 (100 %) | — |
| `esemenyek_szama` | 1/1 (100 %) | — |
| `osszkoltseg_ft` | 1/1 (100 %) | — |
| `hatalyos_munkanap` | 1/1 (100 %) | — |
| `eredeti_munkanap` | 1/1 (100 %) | — |
| `feluliro_pont` | 1/1 (100 %) | — |
| `azonosito` | 1/1 (100 %) | — |
| `terulet` | 1/1 (100 %) | — |
| `bejelentve` | 1/1 (100 %) | — |
| `tetoszigeteles_garancia_lejar` | 1/1 (100 %) | — |
| `aggregat_tipusjel` | 1/1 (100 %) | — |
| `vizora_gyari_szam` | 1/1 (100 %) | — |
| `liftkarbantarto_szerzodesszam` | 1/1 (100 %) | — |
| `tuzjelzo_felulvizsgalat` | 1/1 (100 %) | — |

### `35B FP8 · vLLM` — hosszu-qwen36.json

- **futtatott esetek:** 5 item, 5 sikeres futás, 0 hibás

| Metrika | Medián | Min | Max |
|---|---|---|---|
| Prompt tokenek | **217 325** | 217 306 | 217 400 |
| Kimeneti tokenek | **2 331** | 1 376 | 11 912 |
| Kimeneti tok/s (válaszidőre, TTFT-vel — mindkét motoron azonos képlet) | **46,5** | 14,9 | 52,0 |
| Teljes válaszidő (ms) | **69 352** | 29 948 | 228 885 |

- **JSON-validitás:** 5/5 (100 %)
- **Csonkolt (finish_reason=length):** 0/5
- **Instabil item (eltérő kimenet azonos greedy kérésre):** 0/5
- **Pontszám (többségi kimenet):** **100,00 / 100**

| Teszt | Pont | Max | Instabil item |
|---|---|---|---|
| **T21** | 20,00 | 20 | — |
| **T22** | 20,00 | 20 | — |
| **T23** | 20,00 | 20 | — |
| **T24** | 20,00 | 20 | — |
| **T25** | 20,00 | 20 | — |

| Mező | Egyezés | Eltérések (első 2) |
|---|---|---|
| `oradij_2024_ft` | 1/1 (100 %) | — |
| `oradij_2025_ft` | 1/1 (100 %) | — |
| `oradij_2026_ft` | 1/1 (100 %) | — |
| `munkadij_2026_ft` | 1/1 (100 %) | — |
| `esemenyek_szama` | 1/1 (100 %) | — |
| `osszkoltseg_ft` | 1/1 (100 %) | — |
| `hatalyos_munkanap` | 1/1 (100 %) | — |
| `eredeti_munkanap` | 1/1 (100 %) | — |
| `feluliro_pont` | 1/1 (100 %) | — |
| `azonosito` | 1/1 (100 %) | — |
| `terulet` | 1/1 (100 %) | — |
| `bejelentve` | 1/1 (100 %) | — |
| `tetoszigeteles_garancia_lejar` | 1/1 (100 %) | — |
| `aggregat_tipusjel` | 1/1 (100 %) | — |
| `vizora_gyari_szam` | 1/1 (100 %) | — |
| `liftkarbantarto_szerzodesszam` | 1/1 (100 %) | — |
| `tuzjelzo_felulvizsgalat` | 1/1 (100 %) | — |

### `122B NVFP4 · vLLM` — hosszu-122b.json

- **futtatott esetek:** 5 item, 5 sikeres futás, 0 hibás

| Metrika | Medián | Min | Max |
|---|---|---|---|
| Prompt tokenek | **217 325** | 217 306 | 217 400 |
| Kimeneti tokenek | **4 310** | 1 409 | 14 550 |
| Kimeneti tok/s (válaszidőre, TTFT-vel — mindkét motoron azonos képlet) | **22,3** | 9,6 | 24,0 |
| Teljes válaszidő (ms) | **207 292** | 76 171 | 606 728 |

- **JSON-validitás:** 5/5 (100 %)
- **Csonkolt (finish_reason=length):** 0/5
- **Instabil item (eltérő kimenet azonos greedy kérésre):** 0/5
- **Pontszám (többségi kimenet):** **80,00 / 100**

| Teszt | Pont | Max | Instabil item |
|---|---|---|---|
| **T21** | 20,00 | 20 | — |
| **T22** | 0,00 | 20 | — |
| **T23** | 20,00 | 20 | — |
| **T24** | 20,00 | 20 | — |
| **T25** | 20,00 | 20 | — |

| Mező | Egyezés | Eltérések (első 2) |
|---|---|---|
| `esemenyek_szama` | 0/1 (0 %) | `T22-01`: GT `43` → `42` |
| `osszkoltseg_ft` | 0/1 (0 %) | `T22-01`: GT `7141000` → `7177000` |
| `oradij_2024_ft` | 1/1 (100 %) | — |
| `oradij_2025_ft` | 1/1 (100 %) | — |
| `oradij_2026_ft` | 1/1 (100 %) | — |
| `munkadij_2026_ft` | 1/1 (100 %) | — |
| `hatalyos_munkanap` | 1/1 (100 %) | — |
| `eredeti_munkanap` | 1/1 (100 %) | — |
| `feluliro_pont` | 1/1 (100 %) | — |
| `azonosito` | 1/1 (100 %) | — |
| `terulet` | 1/1 (100 %) | — |
| `bejelentve` | 1/1 (100 %) | — |
| `tetoszigeteles_garancia_lejar` | 1/1 (100 %) | — |
| `aggregat_tipusjel` | 1/1 (100 %) | — |
| `vizora_gyari_szam` | 1/1 (100 %) | — |
| `liftkarbantarto_szerzodesszam` | 1/1 (100 %) | — |
| `tuzjelzo_felulvizsgalat` | 1/1 (100 %) | — |

## Izoláció — a 13 instabil item × 5 futás, Flash NVFP4 (egyszerre egy kapcsoló)

### `MTP=0 (spekulatív dekódolás KI)` — izo-mtp0.json

- **futtatott esetek:** 13 item, 65 sikeres futás, 0 hibás

| Metrika | Medián | Min | Max |
|---|---|---|---|
| Prompt tokenek | **6 038** | 1 858 | 24 452 |
| Kimeneti tokenek | **748** | 165 | 6 941 |
| Kimeneti tok/s (válaszidőre, TTFT-vel — mindkét motoron azonos képlet) | **16,1** | 7,1 | 16,8 |
| Teljes válaszidő (ms) | **46 038** | 12 176 | 416 108 |

- **JSON-validitás:** 65/65 (100 %)
- **Csonkolt (finish_reason=length):** 0/65
- **Instabil item (eltérő kimenet azonos greedy kérésre):** 11/13
- **Pontszám (többségi kimenet):** **32,00 / 34** (LLM-bírói 2 pont elérhetetlen, elérhető max 32)

| Teszt | Pont | Max | Instabil item |
|---|---|---|---|
| **T1** | 9,00 | 10 | 1 |
| **T3** | 6,00 | 6 | 2 |
| **T4** | 2,00 | 2 | — |
| **T5** | 2,00 | 2 | 1 |
| **T6** | 10,00 | 10 | 5 |
| **T7** | 1,00 | 2 | 1 |
| **T10** | 2,00 | 2 | 1 |

| Mező | Egyezés | Eltérések (első 2) |
|---|---|---|
| `index_tipusa` | 1/1 (100 %) | — |
| `bazis_idoszak` | 1/1 (100 %) | — |
| `elso_indexalas` | 1/1 (100 %) | — |
| `plafon_szazalek` | 1/1 (100 %) | — |
| `negativ_index_kezelese` | 1/1 (100 %) | — |
| `kerekites` | 1/1 (100 %) | — |
| `hatarido` | 3/3 (100 %) | — |
| `szamitas_alapja` | 4/4 (100 %) | — |
| `szerepel` | 1/1 (100 %) | — |
| `tetelek` | 1/1 (100 %) | — |
| `ertek_ft` | 3/3 (100 %) | — |
| `hivatkozasi_lanc` | 1/1 (100 %) | — |
| `kamat_alapja` | 1/1 (100 %) | — |
| `tovabb_hivatkozott_pont` | 1/1 (100 %) | — |
| `hivatkozott_pont` | 2/2 (100 %) | — |
| `letezik` | 1/1 (100 %) | — |
| `forras` | 1/1 (100 %) | — |
| `forras_szakasz` | 1/1 (100 %) | — |

### `cudagraph_mode=NONE` — izo-cgnone.json

- **futtatott esetek:** 13 item, 65 sikeres futás, 0 hibás

| Metrika | Medián | Min | Max |
|---|---|---|---|
| Prompt tokenek | **6 038** | 1 858 | 24 452 |
| Kimeneti tokenek | **675** | 167 | 16 384 |
| Kimeneti tok/s (válaszidőre, TTFT-vel — mindkét motoron azonos képlet) | **27,4** | 9,9 | 29,8 |
| Teljes válaszidő (ms) | **25 550** | 7 709 | 587 345 |

- **JSON-validitás:** 64/65 (98 %)
- **Csonkolt (finish_reason=length):** 1/65 — ebből ÜRES tartalom: 1
- **Instabil item (eltérő kimenet azonos greedy kérésre):** 13/13
- **Pontszám (többségi kimenet):** **32,00 / 34** (LLM-bírói 2 pont elérhetetlen, elérhető max 32)

| Teszt | Pont | Max | Instabil item |
|---|---|---|---|
| **T1** | 9,00 | 10 | 1 |
| **T3** | 6,00 | 6 | 3 |
| **T4** | 2,00 | 2 | 1 |
| **T5** | 2,00 | 2 | 1 |
| **T6** | 10,00 | 10 | 5 |
| **T7** | 1,00 | 2 | 1 |
| **T10** | 2,00 | 2 | 1 |

| Mező | Egyezés | Eltérések (első 2) |
|---|---|---|
| `index_tipusa` | 1/1 (100 %) | — |
| `bazis_idoszak` | 1/1 (100 %) | — |
| `elso_indexalas` | 1/1 (100 %) | — |
| `plafon_szazalek` | 1/1 (100 %) | — |
| `negativ_index_kezelese` | 1/1 (100 %) | — |
| `kerekites` | 1/1 (100 %) | — |
| `hatarido` | 3/3 (100 %) | — |
| `szamitas_alapja` | 4/4 (100 %) | — |
| `szerepel` | 1/1 (100 %) | — |
| `tetelek` | 1/1 (100 %) | — |
| `ertek_ft` | 3/3 (100 %) | — |
| `hivatkozasi_lanc` | 1/1 (100 %) | — |
| `kamat_alapja` | 1/1 (100 %) | — |
| `tovabb_hivatkozott_pont` | 1/1 (100 %) | — |
| `hivatkozott_pont` | 2/2 (100 %) | — |
| `letezik` | 1/1 (100 %) | — |
| `forras` | 1/1 (100 %) | — |
| `forras_szakasz` | 1/1 (100 %) | — |

### `VLLM_PLE_MMAP_WORKERS=1` — izo-w1.json

- ⏳ még nincs adat

### `⭐ egzakt kanonikus top-k a QSA persistent_topk helyett (MTP=2 marad)` — izo-topk.json

- **futtatott esetek:** 13 item, 65 sikeres futás, 0 hibás

| Metrika | Medián | Min | Max |
|---|---|---|---|
| Prompt tokenek | **6 038** | 1 858 | 24 452 |
| Kimeneti tokenek | **751** | 196 | 4 317 |
| Kimeneti tok/s (válaszidőre, TTFT-vel — mindkét motoron azonos képlet) | **23,4** | 7,1 | 28,9 |
| Teljes válaszidő (ms) | **32 004** | 9 254 | 163 625 |

- **JSON-validitás:** 65/65 (100 %)
- **Csonkolt (finish_reason=length):** 0/65
- **Instabil item (eltérő kimenet azonos greedy kérésre):** 0/13
- **Pontszám (többségi kimenet):** **32,00 / 34** (LLM-bírói 2 pont elérhetetlen, elérhető max 32)

| Teszt | Pont | Max | Instabil item |
|---|---|---|---|
| **T1** | 9,00 | 10 | — |
| **T3** | 6,00 | 6 | — |
| **T4** | 2,00 | 2 | — |
| **T5** | 2,00 | 2 | — |
| **T6** | 10,00 | 10 | — |
| **T7** | 1,00 | 2 | — |
| **T10** | 2,00 | 2 | — |

| Mező | Egyezés | Eltérések (első 2) |
|---|---|---|
| `index_tipusa` | 1/1 (100 %) | — |
| `bazis_idoszak` | 1/1 (100 %) | — |
| `elso_indexalas` | 1/1 (100 %) | — |
| `plafon_szazalek` | 1/1 (100 %) | — |
| `negativ_index_kezelese` | 1/1 (100 %) | — |
| `kerekites` | 1/1 (100 %) | — |
| `hatarido` | 3/3 (100 %) | — |
| `szamitas_alapja` | 4/4 (100 %) | — |
| `szerepel` | 1/1 (100 %) | — |
| `tetelek` | 1/1 (100 %) | — |
| `ertek_ft` | 3/3 (100 %) | — |
| `hivatkozasi_lanc` | 1/1 (100 %) | — |
| `kamat_alapja` | 1/1 (100 %) | — |
| `tovabb_hivatkozott_pont` | 1/1 (100 %) | — |
| `hivatkozott_pont` | 2/2 (100 %) | — |
| `letezik` | 1/1 (100 %) | — |
| `forras` | 1/1 (100 %) | — |
| `forras_szakasz` | 1/1 (100 %) | — |

## HU-CH magyar nyelvértés-challenge (10 tétel × 1 futás, friss kontextus, a szerző protokollja)

> Nincs gépi pontszám: a szerző integritási megjegyzése szerint LLM-bíró nélkül, a vak `reports/challenge-pontozolap.md`-n kézzel pontozandó. Itt csak a futás-metrikák.

### `Flash IQ4_XS · llama.cpp` — challenge__flash.json

| Metrika | Medián | Min | Max |
|---|---|---|---|
| Kimeneti tokenek | **570** | 208 | 972 |
| Válasz hossza (karakter) | **430** | 18 | 877 |
| Teljes válaszidő (ms) | **21 582** | 8 806 | 36 866 |

- **Csonkolt:** 0/10 · **Üres válasz:** 0/10

| Tétel | finish | ki-token | válasz (első 60 kar.) |
|---|---|---|---|
| HU-CH-01 | stop | 208 | Mari Jánost Péternek nézte. |
| HU-CH-02 | stop | 418 | (a) **Az igazgató** kezdeményezte a visszahívást (ő az alany |
| HU-CH-03 | stop | 586 | ## Válasz  **A várakozás végét a beszélő visszatérése jelöli |
| HU-CH-04 | stop | 555 | **(1) Következik.** A „hacsak… nem" szerkezet Anna jóváhagyá |
| HU-CH-05 | stop | 524 | A vezető azt kéri, hogy **semmiképpen se írd alá** a szerződ |
| HU-CH-06 | stop | 669 | **Nem következik biztosan**, hogy Anna saját kezűleg festett |
| HU-CH-07 | stop | 972 | ## Két értelmezés  1. **A megszólított (Ön) tenné meg:** „Me |
| HU-CH-08 | stop | 405 | 1–c, 2–a, 3–b, 4–d |
| HU-CH-09 | stop | 634 | ## A) „Anna jobban szereti Bélát, mint Csaba."  **Kihagyás k |
| HU-CH-10 | stop | 643 | ## A) „Nem kellett elmenned."  Ez az állítás azt fejezi ki,  |

### `Flash NVFP4 · vLLM` — challenge__flash-nvfp4.json

| Metrika | Medián | Min | Max |
|---|---|---|---|
| Kimeneti tokenek | **2 840** | 936 | 16 384 |
| Válasz hossza (karakter) | **237** | 0 | 913 |
| Teljes válaszidő (ms) | **103 604** | 35 636 | 458 475 |

- **Csonkolt:** 1/10 · **Üres válasz:** 1/10 ⛔

| Tétel | finish | ki-token | válasz (első 60 kar.) |
|---|---|---|---|
| HU-CH-01 | stop | 1 421 | Mari Jánost Péternek nézte. |
| HU-CH-02 | length | 16 384 | ⛔ ÜRES |
| HU-CH-03 | stop | 3 603 | A várakozás végét a beszélő visszatérése jelöli ki.  A „nem” |
| HU-CH-04 | stop | 10 288 | (1) Következik.   (2) Nem következik. A mondat csak Anna jóv |
| HU-CH-05 | stop | 1 141 | A mondat azt kéri, hogy **semiképpen se írd alá** a szerződé |
| HU-CH-06 | stop | 1 338 | Nem, nem következik biztosan.  Két lehetséges értelmezés: 1. |
| HU-CH-07 | stop | 3 052 | Két értelmezés:  1. A megszólított lenne a cselekvő: „Ön néz |
| HU-CH-08 | stop | 936 | 1–c, 2–a, 3–b, 4–d |
| HU-CH-09 | stop | 2 628 | **A)** „Anna jobban szereti Bélát, mint Csaba.”   Kibontva:  |
| HU-CH-10 | stop | 8 014 | **A)** „Nem kellett elmenned.”   - **Jelentés:** a múltban n |

### `35B FP8 · vLLM` — challenge__qwen36.json

| Metrika | Medián | Min | Max |
|---|---|---|---|
| Kimeneti tokenek | **1 742** | 776 | 4 610 |
| Válasz hossza (karakter) | **253** | 18 | 1 317 |
| Teljes válaszidő (ms) | **29 861** | 13 324 | 76 430 |

- **Csonkolt:** 0/10 · **Üres válasz:** 0/10

| Tétel | finish | ki-token | válasz (első 60 kar.) |
|---|---|---|---|
| HU-CH-01 | stop | 776 | Mari Jánost Péternek nézte. |
| HU-CH-02 | stop | 947 | (a) Az igazgató kezdeményezte.   (b) A titkár hajtotta végre |
| HU-CH-03 | stop | 1 476 | A várakozás végét a **beszélő visszatérése** jelöli ki.  A * |
| HU-CH-04 | stop | 3 285 | (1) következik   (2) nem következik |
| HU-CH-05 | stop | 2 007 | A mondat kizárólag azt kéri, hogy **semmiképpen se írd alá** |
| HU-CH-06 | stop | 1 274 | Nem következik biztosan, hogy Anna saját kezűleg festett.  A |
| HU-CH-07 | stop | 2 557 | Két értelmezés: 1. 2. személy egyes szám (udvarias megszólít |
| HU-CH-08 | stop | 889 | 1–c, 2–a, 3–b, 4–d |
| HU-CH-09 | stop | 3 301 | **A) „Anna jobban szereti Bélát, mint Csaba.”** - Teljes jel |
| HU-CH-10 | stop | 4 610 | **A) „Nem kellett elmenned.”** - **Jelentés:** A múltban nem |

### `122B NVFP4 · vLLM` — challenge__122b.json

| Metrika | Medián | Min | Max |
|---|---|---|---|
| Kimeneti tokenek | **4 924** | 1 870 | 7 485 |
| Válasz hossza (karakter) | **264** | 18 | 858 |
| Teljes válaszidő (ms) | **195 457** | 71 938 | 303 302 |

- **Csonkolt:** 0/10 · **Üres válasz:** 0/10

| Tétel | finish | ki-token | válasz (első 60 kar.) |
|---|---|---|---|
| HU-CH-01 | stop | 1 870 | „Mari Jánost Péternek nézte.” |
| HU-CH-02 | stop | 7 485 | (a) Az igazgató. (b) A titkár (a mondat nyelvtani szerkezete |
| HU-CH-03 | stop | 4 679 | A várakozás végét a beszélő visszatérése jelöli ki.  A „nem” |
| HU-CH-04 | stop | 5 349 | (1) Következik. (2) Nem következik. A mondat csak azt rögzít |
| HU-CH-05 | stop | 7 094 | A szöveg alapján azt kéri, hogy semmiképpen se írd alá. Az,  |
| HU-CH-06 | stop | 5 168 | Nem következik biztosan.  1. Értelmezés: Anna fizikailag mag |
| HU-CH-07 | stop | 3 321 | 1. Értelmezés: A megszólított személy (tiszteletteljes „Ön”  |
| HU-CH-08 | stop | 2 834 | 1–c, 2–a, 3–b, 4–d |
| HU-CH-09 | stop | 4 573 | **A) „Anna jobban szereti Bélát, mint Csaba."** *   **Teljes |
| HU-CH-10 | stop | 6 131 | **Különbség:** Az A mondat egyszerű múltban áll (a szükséges |

