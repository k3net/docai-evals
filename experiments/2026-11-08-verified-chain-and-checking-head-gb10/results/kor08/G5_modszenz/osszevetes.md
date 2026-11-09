# 08 G5 utólag — módérzékenység (leíró)

Ugyanazok a fejek (R-módon tanítva), a pontozás és a rögzített elemzők, csak a zárt kiolvasás módja más. A τ és a temperature a mód saját CAL-ján áll be. A fő eredmény az R-módú G5.

## A két fő próba (L-RN − L-S, szabálycsalád)

| mód | ág | ΔAUROC | 95% | olvasat | L-RN | L-S | esemény |
|---|---|---|---|---|---|---|---|
| R | K1a | 0,186 | [0,121; 0,258] | javít érdemben | 0,924 | 0,738 | 453 / 1567 |
| R | K1b | 0,036 | [-0,047; 0,086] | nem eldönthető | 0,927 | 0,890 | 74 / 1567 |
| A | K1a | 0,188 | [0,121; 0,258] | javít érdemben | 0,924 | 0,736 | 444 / 1564 |
| A | K1b | 0,030 | [-0,061; 0,077] | nem eldönthető | 0,927 | 0,897 | 75 / 1564 |
| B | K1a | 0,190 | [0,121; 0,262] | javít érdemben | 0,922 | 0,732 | 448 / 1570 |
| B | K1b | 0,040 | [-0,052; 0,090] | nem eldönthető | 0,921 | 0,881 | 69 / 1570 |

## K2: a helyes arány a kinyert úton

| mód | penzugy.bankparositas | muszaki.hibaelharitas | szabaly.koltsegelszamolas |
|---|---|---|---|
| R | 97,8% (lánc nélkül 44,4%) | 98,9% (lánc nélkül 59,3%) | 97,5% (lánc nélkül 28,0%) |
| A | 97,8% (lánc nélkül 44,4%) | 98,9% (lánc nélkül 60,4%) | 97,5% (lánc nélkül 27,0%) |
| B | 97,8% (lánc nélkül 44,4%) | 98,9% (lánc nélkül 60,4%) | 97,5% (lánc nélkül 28,5%) |

## K3: hasznos lefedettség és lezárási hiba

| család | mód | L-RN | L-RN hiba | L-S | L-S hiba | B1-4R | B1-4R hiba | L-RN − L-S | 95% | L-RN − B1-4R | 95% | hibafeltétel (L-RN) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| penzugy.bankparositas | R | 36,3% | 0,0% | 36,3% | 0,0% | 53,2% | 1,2% | 0,0% | [-0,0%; 0,0%] | -16,9% | [-25,0%; 21,0%] | teljesül |
| penzugy.bankparositas | A | 36,3% | 0,0% | 36,3% | 0,0% | 53,8% | 2,0% | 0,0% | [-0,0%; 0,0%] | -17,5% | [-25,2%; 6,0%] | teljesül |
| penzugy.bankparositas | B | 36,3% | 0,0% | 36,3% | 0,0% | 54,6% | 2,3% | 0,0% | [-0,0%; 0,0%] | -18,3% | [-26,0%; 19,3%] | teljesül |
| muszaki.hibaelharitas | R | 67,6% | 3,6% | 62,9% | 4,1% | 71,2% | 5,5% | 4,7% | [0,2%; 9,2%] | -3,5% | [-6,1%; 11,3%] | bizonytalan |
| muszaki.hibaelharitas | A | 67,8% | 4,1% | 62,8% | 4,4% | 71,3% | 5,3% | 5,0% | [0,0%; 9,8%] | -3,4% | [-5,9%; 9,2%] | bizonytalan |
| muszaki.hibaelharitas | B | 67,8% | 5,5% | 63,1% | 4,4% | 70,5% | 5,9% | 4,7% | [0,0%; 10,1%] | -2,7% | [-5,1%; 9,0%] | nem teljesül |
| szabaly.koltsegelszamolas | R | 71,9% | 3,1% | 62,6% | 4,7% | 71,9% | 2,7% | 9,3% | [7,4%; 18,1%] | -0,0% | [-2,9%; 4,7%] | bizonytalan |
| szabaly.koltsegelszamolas | A | 72,3% | 3,8% | 62,5% | 4,4% | 72,5% | 2,9% | 9,8% | [7,5%; 19,1%] | -0,2% | [-2,8%; 4,6%] | bizonytalan |
| szabaly.koltsegelszamolas | B | 71,9% | 3,7% | 61,8% | 4,0% | 72,4% | 3,2% | 10,1% | [6,9%; 18,3%] | -0,5% | [-3,2%; 5,1%] | bizonytalan |

## Az (a)-ból τ fölött lezárt arány

| család | mód | L-RN | L-S |
|---|---|---|---|
| penzugy.bankparositas | R | 0,0% | 0,0% |
| penzugy.bankparositas | A | 0,0% | 0,0% |
| penzugy.bankparositas | B | 0,0% | 0,0% |
| muszaki.hibaelharitas | R | 11,3% | 80,6% |
| muszaki.hibaelharitas | A | 12,9% | 87,1% |
| muszaki.hibaelharitas | B | 18,8% | 83,9% |
| szabaly.koltsegelszamolas | R | 43,5% | 43,0% |
| szabaly.koltsegelszamolas | A | 46,6% | 42,2% |
| szabaly.koltsegelszamolas | B | 47,9% | 41,4% |

## Döntésfordulás R-hez képest (a modell döntése: fajta és jelölt)

| szelet | n | A: eltér | A: helyesség eltér | B: eltér | B: helyesség eltér |
|---|---|---|---|---|---|
| lG2F_penzugy.bankparositas_TESZT | 637 | 40 | 17 | 30 | 12 |
| nG2F_penzugy.bankparositas_TESZT | 1000 | 11 | 5 | 14 | 8 |
| lG2K3_penzugy.bankparositas_G2K3 | 90 | 0 | 0 | 0 | 0 |
| lG2T_penzugy.bankparositas_G2T | 256 | 12 | 4 | 9 | 3 |
| lG2F_muszaki.hibaelharitas_TESZT | 999 | 21 | 17 | 18 | 14 |
| nG2F_muszaki.hibaelharitas_TESZT | 1000 | 29 | 24 | 18 | 15 |
| lG2K3_muszaki.hibaelharitas_G2K3 | 91 | 0 | 0 | 0 | 0 |
| lG2T_muszaki.hibaelharitas_G2T | 248 | 2 | 0 | 2 | 0 |
| lG2F_szabaly.koltsegelszamolas_TESZT | 995 | 16 | 15 | 14 | 14 |
| nG2F_szabaly.koltsegelszamolas_TESZT | 1000 | 16 | 15 | 16 | 16 |
| lG2K3_szabaly.koltsegelszamolas_G2K3 | 199 | 0 | 0 | 0 | 0 |
| lG2T_szabaly.koltsegelszamolas_G2T | 2204 | 39 | 26 | 35 | 22 |
| **összesen** | 8719 | 186 | 123 | 156 | 104 |
