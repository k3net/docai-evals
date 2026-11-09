# 07 — K1 és K2 elemzés: F5, friss CAL / TESZT

Sabloncsoportos klaszteres bootstrap (10000 replika, seed 20261101), a τ replikánként újra a CAL-on, a futások (seedek) átlaga replikánként (D24). Szigorú helyesség (négyállapotú keret: négyosztályos). K2: τ a lezárható javaslatokon (SELECT és X / NONE), CP-alsó ≥ 0.95, ≥ 200 lezárt ügy; hibafeltétel: lezárási hibaarány ≤ 0.05 a TESZT-en; „behozza”: a hasznos lefedettség különbségének alsó határa > -0.03.

## K1 — AURC a TESZT-en

| család | B1-4S | B1-4R | B1-4LR | B1-4R0 | B1-S | B1-N | B1-R | B1-LR | B1-R0 |
|---|---|---|---|---|---|---|---|---|---|
| penzugy.bankparositas | 0,0952 | 0,0491 | 0,0707 | 0,1072 | 0,1397 | 0,1002 | 0,0503 | 0,0643 | 0,1259 |
| muszaki.hibaelharitas | 0,0406 | 0,0229 | 0,0374 | 0,1049 | 0,2277 | 0,0841 | 0,0427 | 0,0555 | 0,1052 |
| szabaly.koltsegelszamolas | 0,0629 | 0,0287 | 0,0326 | 0,0643 | 0,3044 | 0,1126 | 0,0438 | 0,0675 | 0,1307 |
| **átlag** | 0,0662 | 0,0336 | 0,0469 | 0,0921 | 0,2239 | 0,0990 | 0,0456 | 0,0624 | 0,1206 |

**K1: B1-4R − B1-4S:** bankparositas Δ -0,0460 [-0,0546; -0,0380] p=0,000; hibaelharitas Δ -0,0177 [-0,0259; -0,0091] p=0,000; koltsegelszamolas Δ -0,0343 [-0,0421; -0,0257] p=0,000. Átlag arány **0,507** [0,459; 0,562]; 8.3: javul 3/3, arány ≤ 0,90: igen, D4: igen → **teljesül**. Holm-p: bankparositas 0,000, hibaelharitas 0,000, koltsegelszamolas 0,000

**B1-4LR − B1-4S:** bankparositas Δ -0,0244 [-0,0306; -0,0180] p=0,000; hibaelharitas Δ -0,0032 [-0,0182; 0,0150] p=0,637; koltsegelszamolas Δ -0,0303 [-0,0407; -0,0151] p=0,001. Átlag arány **0,708** [0,608; 0,826]; 8.3: javul 3/3, arány ≤ 0,90: igen, D4: igen → **teljesül**. Holm-p: bankparositas 0,000, koltsegelszamolas 0,001, hibaelharitas 0,637

**B1-4R − B1-4LR:** bankparositas Δ -0,0216 [-0,0325; -0,0121] p=0,000; hibaelharitas Δ -0,0144 [-0,0291; -0,0017] p=0,018; koltsegelszamolas Δ -0,0040 [-0,0138; 0,0032] p=0,390. Átlag arány **0,716** [0,630; 0,823]; 8.3: javul 3/3, arány ≤ 0,90: igen, D4: igen → **teljesül**. Holm-p: bankparositas 0,000, hibaelharitas 0,036, koltsegelszamolas 0,390

**06: B1-R − B1-S:** bankparositas Δ -0,0895 [-0,1051; -0,0755] p=0,000; hibaelharitas Δ -0,1850 [-0,2116; -0,1585] p=0,000; koltsegelszamolas Δ -0,2606 [-0,2849; -0,2367] p=0,000. Átlag arány **0,204** [0,186; 0,222]; 8.3: javul 3/3, arány ≤ 0,90: igen, D4: igen → **teljesül**. Holm-p: bankparositas 0,000, hibaelharitas 0,000, koltsegelszamolas 0,000

**kereszt (leíró): B1-4S − B1-R:** bankparositas Δ 0,0449 [0,0362; 0,0542] p=0,000; hibaelharitas Δ -0,0021 [-0,0096; 0,0054] p=0,552; koltsegelszamolas Δ 0,0191 [0,0123; 0,0259] p=0,000. Átlag arány **1,453** [1,341; 1,565]; 8.3: javul 1/3, arány ≤ 0,90: nem, D4: nem → **nem teljesül**. Holm-p: bankparositas 0,000, koltsegelszamolas 0,000, hibaelharitas 0,552

**kereszt (leíró): B1-4R − B1-R:** bankparositas Δ -0,0011 [-0,0057; 0,0030] p=0,637; hibaelharitas Δ -0,0198 [-0,0270; -0,0123] p=0,000; koltsegelszamolas Δ -0,0151 [-0,0221; -0,0076] p=0,000. Átlag arány **0,737** [0,665; 0,814]; 8.3: javul 3/3, arány ≤ 0,90: igen, D4: igen → **teljesül**. Holm-p: hibaelharitas 0,000, koltsegelszamolas 0,000, bankparositas 0,637

### E-AURC (leíró, D13; promptok között nem összevethető)

| család | B1-4S | B1-4R | B1-4LR | B1-4R0 | B1-S | B1-N | B1-R | B1-LR | B1-R0 |
|---|---|---|---|---|---|---|---|---|---|
| penzugy.bankparositas | 0,0554 | 0,0094 | 0,0309 | 0,0674 | 0,0980 | 0,0585 | 0,0086 | 0,0226 | 0,0842 |
| muszaki.hibaelharitas | 0,0286 | 0,0110 | 0,0254 | 0,0930 | 0,1922 | 0,0486 | 0,0072 | 0,0199 | 0,0697 |
| szabaly.koltsegelszamolas | 0,0424 | 0,0082 | 0,0122 | 0,0438 | 0,2668 | 0,0750 | 0,0062 | 0,0299 | 0,0931 |

### D20 — AURC a SELECT- és a nem-SELECT javaslatokon (B1-4R vs B1-4S; B1-R vs B1-S)

| család | B1-4S sel / nem-sel | B1-4R sel / nem-sel | B1-S sel / nem-sel | B1-R sel / nem-sel |
|---|---|---|---|---|
| penzugy.bankparositas | 0,0520 / 0,7311 | 0,0347 / 0,1180 | 0,0474 / 0,7772 | 0,0358 / 0,1347 |
| muszaki.hibaelharitas | 0,0156 / 0,1698 | 0,0119 / 0,0914 | 0,0160 / 0,7289 | 0,0091 / 0,2167 |
| szabaly.koltsegelszamolas | 0,0210 / 0,4364 | 0,0201 / 0,0568 | 0,0600 / 0,7640 | 0,0344 / 0,0956 |

### A döntések helyessége és a tévesztési mátrix (prompttulajdonság)

**penzugy.bankparositas:** helyes döntés négyállapotú 0,732, 06-os 0,726; lezárható javaslat 0,998 / 1,000; felső korlát 0,800.

| gold | 4: SELECT | X | Y | Z | · | 06: SELECT | NONE |
|---|---|---|---|---|---|---|---|
| MATCH | 600 | 0 | 0 | 0 | · | 600 | 0 |
| NO_MATCH | 66 | 132 | 2 | 0 | · | 74 | 126 |
| MISSING_DATA | 99 | 1 | 0 | 0 | · | 98 | 2 |
| OUT_OF_SCOPE | 0 | 100 | 0 | 0 | · | 0 | 100 |

**muszaki.hibaelharitas:** helyes döntés négyállapotú 0,850, 06-os 0,746; lezárható javaslat 0,825 / 1,000; felső korlát 0,800.

| gold | 4: SELECT | X | Y | Z | · | 06: SELECT | NONE |
|---|---|---|---|---|---|---|---|
| MATCH | 598 | 2 | 0 | 0 | · | 586 | 14 |
| NO_MATCH | 61 | 129 | 8 | 2 | · | 37 | 163 |
| MISSING_DATA | 15 | 18 | 67 | 0 | · | 30 | 70 |
| OUT_OF_SCOPE | 0 | 2 | 37 | 61 | · | 1 | 99 |

**szabaly.koltsegelszamolas:** helyes döntés négyállapotú 0,805, 06-os 0,739; lezárható javaslat 0,929 / 1,000; felső korlát 0,800.

| gold | 4: SELECT | X | Y | Z | · | 06: SELECT | NONE |
|---|---|---|---|---|---|---|---|
| MATCH | 600 | 0 | 0 | 0 | · | 600 | 0 |
| NO_MATCH | 51 | 149 | 0 | 0 | · | 53 | 147 |
| MISSING_DATA | 49 | 0 | 51 | 0 | · | 100 | 0 |
| OUT_OF_SCOPE | 0 | 80 | 4 | 16 | · | 1 | 99 |

## K2 — hasznos lefedettség és lezárási hibaarány a TESZT-en (τ a CAL-on)

| kar | család | lezárt | hasznos lefedettség [95%] | lezárási hibaarány [95%] | helyes adatbekérés | helyes továbbítás | nem lezárt: adatbekérés / továbbítás / τ alatt | nincs munkapont (pont / replika) |
|---|---|---|---|---|---|---|---|---|
| B1-4S | bankparositas | 0,0% | 0,0% [0,0%; 44,3%] | – [2,4%; 6,3%] | 0,0% | 0,0% | 0,2% / 0,0% / 99,8% | 1,00 / 0,902 |
| B1-4S | hibaelharitas | 62,1% | 59,2% [44,6%; 69,7%] | 4,7% [0,8%; 9,6%] | 67,0% | 61,0% | 11,2% / 6,3% / 20,4% | 0,00 / 0,013 |
| B1-4S | koltsegelszamolas | 53,1% | 51,6% [46,0%; 55,0%] | 2,8% [1,1%; 5,1%] | 51,0% | 16,0% | 5,5% / 1,6% / 39,8% | 0,00 / 0,000 |
| **B1-4S** | **átlag** | | **36,9%** [31,6%; 52,4%] | **–** [2,3%; 5,7%] | | | | – / 0,305 |
| B1-4R | bankparositas | 60,9% | 59,4% [0,0%; 68,0%] | 2,5% [0,6%; 4,7%] | 0,0% | 0,0% | 0,2% / 0,0% / 38,9% | 0,00 / 0,178 |
| B1-4R | hibaelharitas | 63,7% | 62,9% [55,3%; 72,8%] | 1,3% [0,5%; 4,7%] | 67,0% | 61,0% | 11,2% / 6,3% / 18,8% | 0,00 / 0,000 |
| B1-4R | koltsegelszamolas | 75,0% | 72,2% [69,5%; 74,6%] | 3,8% [2,1%; 5,9%] | 51,0% | 16,0% | 5,5% / 1,6% / 17,9% | 0,00 / 0,000 |
| **B1-4R** | **átlag** | | **64,8%** [44,4%; 69,8%] | **2,5%** [1,7%; 4,1%] | | | | – / 0,059 |
| B1-4LR | bankparositas | 0,0% | 0,0% [0,0%; 55,2%] | – [2,4%; 5,9%] | 0,0% | 0,0% | 0,2% / 0,0% / 99,8% | 1,00 / 0,654 |
| B1-4LR | hibaelharitas | 62,3% | 60,6% [0,0%; 70,5%] | 2,7% [0,6%; 6,1%] | 67,0% | 61,0% | 11,2% / 6,3% / 20,2% | 0,00 / 0,042 |
| B1-4LR | koltsegelszamolas | 72,2% | 69,9% [65,4%; 72,8%] | 3,2% [1,9%; 5,6%] | 51,0% | 16,0% | 5,5% / 1,6% / 20,7% | 0,00 / 0,000 |
| **B1-4LR** | **átlag** | | **43,5%** [23,8%; 63,4%] | **–** [2,4%; 4,8%] | | | | – / 0,232 |
| B1-4R0 | bankparositas | 0,0% | 0,0% [0,0%; 0,0%] | – [4,0%; 8,1%] | 0,0% | 0,0% | 0,2% / 0,0% / 99,8% | 1,00 / 1,000 |
| B1-4R0 | hibaelharitas | 36,1% | 34,7% [29,8%; 61,0%] | 3,8% [1,5%; 7,3%] | 67,0% | 61,0% | 11,2% / 6,3% / 46,4% | 0,33 / 0,227 |
| B1-4R0 | koltsegelszamolas | 48,9% | 47,0% [0,0%; 55,0%] | 3,9% [2,3%; 6,4%] | 51,0% | 16,0% | 5,5% / 1,6% / 44,0% | 0,00 / 0,250 |
| **B1-4R0** | **átlag** | | **27,2%** [11,1%; 36,6%] | **–** [3,1%; 5,4%] | | | | – / 0,492 |
| B1-S | bankparositas | 0,0% | 0,0% [0,0%; 0,0%] | – [–; –] | 0,0% | 0,0% | 0,0% / 0,0% / 100,0% | 1,00 / 1,000 |
| B1-S | hibaelharitas | 0,0% | 0,0% [0,0%; 0,0%] | – [–; –] | 0,0% | 0,0% | 0,0% / 0,0% / 100,0% | 1,00 / 1,000 |
| B1-S | koltsegelszamolas | 0,0% | 0,0% [0,0%; 0,0%] | – [–; –] | 0,0% | 0,0% | 0,0% / 0,0% / 100,0% | 1,00 / 1,000 |
| **B1-S** | **átlag** | | **0,0%** [0,0%; 0,0%] | **–** [–; –] | | | | – / 1,000 |
| B1-N | bankparositas | 0,0% | 0,0% [0,0%; 55,7%] | – [2,0%; 6,0%] | 0,0% | 0,0% | 0,0% / 0,0% / 100,0% | 1,00 / 0,624 |
| B1-N | hibaelharitas | 46,4% | 45,7% [0,0%; 57,7%] | 1,5% [0,0%; 8,4%] | 0,0% | 0,0% | 0,0% / 0,0% / 53,6% | 0,00 / 0,145 |
| B1-N | koltsegelszamolas | 0,0% | 0,0% [0,0%; 47,4%] | – [2,5%; 6,8%] | 0,0% | 0,0% | 0,0% / 0,0% / 100,0% | 1,00 / 0,543 |
| **B1-N** | **átlag** | | **15,2%** [0,0%; 46,8%] | **–** [2,4%; 5,9%] | | | | – / 0,437 |
| B1-R | bankparositas | 66,1% | 64,2% [58,9%; 68,5%] | 2,8% [1,6%; 4,7%] | 0,0% | 0,0% | 0,0% / 0,0% / 33,9% | 0,00 / 0,000 |
| B1-R | hibaelharitas | 67,9% | 66,1% [60,2%; 72,5%] | 2,6% [1,1%; 5,7%] | 0,0% | 0,0% | 0,0% / 0,0% / 32,1% | 0,00 / 0,000 |
| B1-R | koltsegelszamolas | 71,6% | 69,3% [65,0%; 72,8%] | 3,2% [1,7%; 6,0%] | 0,0% | 0,0% | 0,0% / 0,0% / 28,4% | 0,00 / 0,000 |
| **B1-R** | **átlag** | | **66,6%** [63,7%; 69,5%] | **2,9%** [2,1%; 4,4%] | | | | – / 0,000 |
| B1-LR | bankparositas | 55,6% | 53,7% [0,0%; 60,8%] | 3,4% [1,9%; 5,5%] | 0,0% | 0,0% | 0,0% / 0,0% / 44,4% | 0,00 / 0,231 |
| B1-LR | hibaelharitas | 50,6% | 49,4% [0,0%; 62,4%] | 2,4% [0,5%; 6,0%] | 0,0% | 0,0% | 0,0% / 0,0% / 49,4% | 0,00 / 0,120 |
| B1-LR | koltsegelszamolas | 52,3% | 50,6% [45,3%; 64,6%] | 3,3% [2,0%; 7,4%] | 0,0% | 0,0% | 0,0% / 0,0% / 47,7% | 0,00 / 0,007 |
| **B1-LR** | **átlag** | | **51,2%** [19,1%; 58,0%] | **3,0%** [2,2%; 5,0%] | | | | – / 0,119 |
| B1-R0 | bankparositas | 0,0% | 0,0% [0,0%; 0,0%] | – [4,5%; 7,3%] | 0,0% | 0,0% | 0,0% / 0,0% / 100,0% | 1,00 / 1,000 |
| B1-R0 | hibaelharitas | 16,0% | 15,5% [13,5%; 31,2%] | 2,9% [1,3%; 7,1%] | 0,0% | 0,0% | 0,0% / 0,0% / 84,0% | 0,67 / 0,640 |
| B1-R0 | koltsegelszamolas | 0,0% | 0,0% [0,0%; 0,0%] | – [4,5%; 10,8%] | 0,0% | 0,0% | 0,0% / 0,0% / 100,0% | 1,00 / 0,995 |
| **B1-R0** | **átlag** | | **5,2%** [4,5%; 10,5%] | **–** [–; –] | | | | – / 0,878 |

### Következtetés (D10, a három család egyenlő súlyú átlagán)

- **behozza (B1-4S − B1-R):** Δ hasznos lefedettség -29,6% [-34,2%; -15,2%], p=0,000 → **nem hozza be**; családonként bankparositas -64,2% [-68,1%; -22,1%], hibaelharitas -6,9% [-18,5%; 2,1%], koltsegelszamolas -17,7% [-23,0%; -13,4%].
- **javít mellette (B1-4R − B1-4S):** Δ hasznos lefedettség 27,9% [7,8%; 33,5%], p=0,001 → **javít mellette**; családonként bankparositas 59,4% [0,0%; 67,4%], hibaelharitas 3,7% [-5,5%; 16,3%], koltsegelszamolas 20,6% [17,2%; 25,8%].
- **B1-4R − B1-R (leíró):** Δ hasznos lefedettség -1,7% [-21,4%; 2,0%], p=0,380; családonként bankparositas -4,8% [-63,8%; 1,5%], hibaelharitas -3,2% [-9,8%; 4,7%], koltsegelszamolas 2,8% [0,6%; 5,9%].
- **B1-R − B1-S (06):** Δ hasznos lefedettség 66,6% [63,7%; 69,5%], p=0,000; családonként bankparositas 64,2% [58,9%; 68,5%], hibaelharitas 66,1% [60,2%; 72,5%], koltsegelszamolas 69,3% [65,0%; 72,8%].

Hibafeltétel karonként (átlag; pont ≤ 5% / bizonytalan): B1-S – (nem), B1-R 2,9% (igen), B1-4S – (nem), B1-4R 2,5% (igen).
