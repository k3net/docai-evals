> **Development numbers, aggregates only:** 262 real bank transactions of one contributing company, a known sample with known labels (one labeller, blind); the thresholds come from the synthetic calibration. Not a confirmatory result. `results/REAL-DATA-NOTICE.md`.

# 07B — végleges eredmény Dani vak címkéihez mérve

Tétel 262; K / N válasz miatt kimaradt 4; több számlát rendező (az egy-számlás elemzésből kimarad, a teljes folyamatban megoldatlan) 7. A címkék: {'MATCH': 142, 'MISSING_DATA': 62, 'OUT_OF_SCOPE': 47, 'NO_MATCH': 7}.

## 1. A jelöltválasztás lefedése

Ahol létezik helyes számla: 140; ebből a listán: 139.

## A termék a címkékhez mérve

| eset | n |
|---|---|
| kategorizált, címke O | 45 |
| kategorizált, címke más | 19 |
| kötött a listán kívül; címke: MISSING_DATA | 5 |
| kötött a listán kívül; címke: NO_MATCH | 3 |
| kötött a listán kívül; címke: OUT_OF_SCOPE | 1 |
| kötött, helyes | 134 |
| kötött, téves: a címke más számla | 2 |
| kötött; címke M (a látott adatból nem dönthető el) | 35 |
| nem oldotta meg, címke MATCH | 3 |
| nem oldotta meg, címke MISSING_DATA | 3 |
| nem oldotta meg, címke NO_MATCH | 4 |
| nem oldotta meg, címke OUT_OF_SCOPE | 1 |

## 2. A modell döntése a listán — négyállapotú keret

Helyes döntés (szigorú): 142 / 230.

| címke | modell | n |
|---|---|---|
| MATCH | SELECT=helyes | 139 |
| MISSING_DATA | SELECT | 38 |
| MISSING_DATA | X | 15 |
| NO_MATCH | X | 3 |
| OUT_OF_SCOPE | SELECT | 4 |
| OUT_OF_SCOPE | X | 31 |

### 3. Kiegészítő értékelés: a modell a termék mellett (Dani, 11-02)

A modell a meglévő kötést és kategóriát nem írja felül, csak a termék által megoldatlan tételre (se kötés, se kategória) tesz javaslatot. Megoldatlan 11 tétel, ebből a modellhez került 7; a címkéik: {'NO_MATCH': 4, 'OUT_OF_SCOPE': 1, 'MISSING_DATA': 3, 'MATCH': 3}. A modell döntései rajtuk (τ nélkül): MATCH → SELECT=helyes 3, MISSING_DATA → X 2, NO_MATCH → X 1, OUT_OF_SCOPE → SELECT 1. Ütközés: a termék a listán kötött, a modell a munkaponton mást mond (más számla vagy X); ez jelzés, nem hiba.

| kar | lezárt a megoldatlanokon | ebből helyes kötés / helyes X / hibás | helyes párosítás: termék → termék + modell | ütközésjelzés | ebből a címke a modellt / a terméket igazolja / M |
|---|---|---|---|---|---|
| B1-4S | nincs munkapont | – | – | – | – |
| B1-4R | 3 | 3 / 0 / 0 | 134 → 137 (/ 262) | 2,7 | 2 / 0 / 0,7 |
| B1-4LR | nincs munkapont | – | – | – | – |

### Felülíró változat (leíró): munkapont a változatlan τ-val, a termékhez viszonyított többlet

| kar | lezárt | ebből hibás | helyes kötés | többlet helyes kötés (a termék nem kötötte jól) | új hiba: a termék jó volt / nem kötött | részfizetés: lezárt / hibás | helyes párosítás a teljes folyamatban: termék → termék + modell |
|---|---|---|---|---|---|---|---|
| B1-4S | nincs munkapont | – | – | – | – | – | – |
| B1-4R | 129 | 9,7 | 119,3 | 5 | 0 / 0,3 | 3 / 0 | 134 → 139 (/ 262) |
| B1-4LR | nincs munkapont | – | – | – | – | – | – |

## 2. A modell döntése a listán — 06-os keret (leíró)

Helyes döntés (szigorú): 142 / 230.

| címke | modell | n |
|---|---|---|
| MATCH | SELECT=helyes | 139 |
| MISSING_DATA | SELECT | 35 |
| MISSING_DATA | X | 18 |
| NO_MATCH | X | 3 |
| OUT_OF_SCOPE | SELECT | 3 |
| OUT_OF_SCOPE | X | 32 |

### 3. Kiegészítő értékelés: a modell a termék mellett (Dani, 11-02)

A modell a meglévő kötést és kategóriát nem írja felül, csak a termék által megoldatlan tételre (se kötés, se kategória) tesz javaslatot. Megoldatlan 11 tétel, ebből a modellhez került 7; a címkéik: {'NO_MATCH': 4, 'OUT_OF_SCOPE': 1, 'MISSING_DATA': 3, 'MATCH': 3}. A modell döntései rajtuk (τ nélkül): MATCH → SELECT=helyes 3, MISSING_DATA → X 2, NO_MATCH → X 1, OUT_OF_SCOPE → X 1. Ütközés: a termék a listán kötött, a modell a munkaponton mást mond (más számla vagy X); ez jelzés, nem hiba.

| kar | lezárt a megoldatlanokon | ebből helyes kötés / helyes X / hibás | helyes párosítás: termék → termék + modell | ütközésjelzés | ebből a címke a modellt / a terméket igazolja / M |
|---|---|---|---|---|---|
| B1-S | nincs munkapont | – | – | – | – |
| B1-R | 3 | 3 / 0 / 0 | 134 → 137 (/ 262) | 5 | 2 / 0 / 3 |
| B1-LR | 2 | 2 / 0 / 0 | 134 → 136 (/ 262) | 3 | 2 / 0 / 1 |

### Felülíró változat (leíró): munkapont a változatlan τ-val, a termékhez viszonyított többlet

| kar | lezárt | ebből hibás | helyes kötés | többlet helyes kötés (a termék nem kötötte jól) | új hiba: a termék jó volt / nem kötött | részfizetés: lezárt / hibás | helyes párosítás a teljes folyamatban: termék → termék + modell |
|---|---|---|---|---|---|---|---|
| B1-S | nincs munkapont | – | – | – | – | – | – |
| B1-R | 138,3 | 19 | 119,3 | 5 | 0 / 9 | 3 / 0 | 134 → 139 (/ 262) |
| B1-LR | 140 | 12 | 128 | 4 | 0 / 6 | 2 / 0 | 134 → 138 (/ 262) |

A teljes folyamat nevezője: 262 tétel (az üres listájúak és a több számlát rendezők megoldatlanként).
