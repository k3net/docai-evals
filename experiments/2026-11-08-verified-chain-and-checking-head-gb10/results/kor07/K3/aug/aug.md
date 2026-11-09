# Páros diagnosztikai próba: eredeti szöveg vs. a géppel kiszámított sorral kiegészítve (feltáró)

A K3 végső mintája (K07K3), ugyanazok az itemek és jelöltek; a kiegészített változatban a szöveg végén egy sor a hiányzó lépés eredményével (`kor07/eszkozok/aug07.py`). Feltáró elemzés a már megismert K3-mintán, nem megerősítő. Helyes = SELECT a gold opción; a nem-SELECT is hiba (minden item MATCH). A különbség intervalluma sabloncsoportos klaszteres bootstrap (2000 ismétlés). McNemar: egzakt, kétoldali.

## Négyállapotú keret

| család | bontás | n | helyes: eredeti → kiegészített | rossz opció | nem-SELECT | javult / romlott | McNemar p |
|---|---|---|---|---|---|---|---|
| penzugy.bankparositas | összes | 186 | 54 (29%) → 186 (100%) | 127 → 0 | 5 → 0 | 132 / 0 | 0,0000 |
| penzugy.bankparositas | változat B3a-reszfizetes | 186 | 54 (29%) → 186 (100%) | 127 → 0 | 5 → 0 | 132 / 0 | 0,0000 |
| penzugy.bankparositas | nyelv hu | 100 | 24 (24%) → 100 (100%) | 74 → 0 | 2 → 0 | 76 / 0 | 0,0000 |
| penzugy.bankparositas | nyelv en | 86 | 30 (35%) → 86 (100%) | 53 → 0 | 3 → 0 | 56 / 0 | 0,0000 |
| muszaki.hibaelharitas | összes | 182 | 95 (52%) → 171 (94%) | 80 → 9 | 7 → 2 | 78 / 2 | 0,0000 |
| muszaki.hibaelharitas | változat H3-valtas | 182 | 95 (52%) → 171 (94%) | 80 → 9 | 7 → 2 | 78 / 2 | 0,0000 |
| muszaki.hibaelharitas | nyelv hu | 86 | 48 (56%) → 80 (93%) | 35 → 5 | 3 → 1 | 33 / 1 | 0,0000 |
| muszaki.hibaelharitas | nyelv en | 96 | 47 (49%) → 91 (95%) | 45 → 4 | 4 → 1 | 45 / 1 | 0,0000 |
| szabaly.koltsegelszamolas | összes | 199 | 48 (24%) → 134 (67%) | 148 → 65 | 3 → 0 | 86 / 0 | 0,0000 |
| szabaly.koltsegelszamolas | változat S3a-netto | 100 | 30 (30%) → 67 (67%) | 70 → 33 | 0 → 0 | 37 / 0 | 0,0000 |
| szabaly.koltsegelszamolas | változat S3b-deviza | 99 | 18 (18%) → 67 (68%) | 78 → 32 | 3 → 0 | 49 / 0 | 0,0000 |
| szabaly.koltsegelszamolas | nyelv hu | 100 | 42 (42%) → 90 (90%) | 55 → 10 | 3 → 0 | 48 / 0 | 0,0000 |
| szabaly.koltsegelszamolas | nyelv en | 99 | 6 (6%) → 44 (44%) | 93 → 55 | 0 → 0 | 38 / 0 | 0,0000 |

| család | Δ helyes arány [95%] | B1-4S AUROC: eredeti → kieg. | B1-4R AUROC: eredeti → kieg. | B1-4LR AUROC: eredeti → kieg. | B1-4R0 AUROC: eredeti → kieg. |
|---|---|---|---|---|---|
| penzugy.bankparositas | 0,710 [0,646; 0,771] | 0,310 → – | 0,211 → – | 0,345 → – | 0,314 → – |
| muszaki.hibaelharitas | 0,418 [0,328; 0,505] | 0,612 → 0,857 | 0,696 → 0,919 | 0,594 → 0,818 | 0,641 → 0,715 |
| szabaly.koltsegelszamolas | 0,432 [0,365; 0,500] | 0,316 → 0,535 | 0,447 → 0,547 | 0,375 → 0,476 | 0,514 → 0,633 |

Munkapont a változatlan τ-val (lezárt, ebből hibás; seedes karon a seedek átlaga):

| család | kar | eredeti | kiegészített |
|---|---|---|---|
| penzugy.bankparositas | B1-4S | nincs munkapont | nincs munkapont |
| penzugy.bankparositas | B1-4R | 11,0, hibás 11,0 | 42,3, hibás 0,0 |
| penzugy.bankparositas | B1-4LR | nincs munkapont | nincs munkapont |
| muszaki.hibaelharitas | B1-4S | 116,0, hibás 46,0 | 164,0, hibás 7,0 |
| muszaki.hibaelharitas | B1-4R | 60,3, hibás 16,0 | 165,7, hibás 4,0 |
| muszaki.hibaelharitas | B1-4LR | 78,0, hibás 35,0 | 140,0, hibás 6,0 |
| szabaly.koltsegelszamolas | B1-4S | 36,0, hibás 36,0 | 67,0, hibás 17,0 |
| szabaly.koltsegelszamolas | B1-4R | 151,0, hibás 122,3 | 188,0, hibás 63,3 |
| szabaly.koltsegelszamolas | B1-4LR | 138,0, hibás 107,0 | 196,0, hibás 65,0 |

## 06-os keret (leíró)

| család | bontás | n | helyes: eredeti → kiegészített | rossz opció | nem-SELECT | javult / romlott | McNemar p |
|---|---|---|---|---|---|---|---|
| penzugy.bankparositas | összes | 186 | 59 (32%) → 186 (100%) | 124 → 0 | 3 → 0 | 127 / 0 | 0,0000 |
| penzugy.bankparositas | változat B3a-reszfizetes | 186 | 59 (32%) → 186 (100%) | 124 → 0 | 3 → 0 | 127 / 0 | 0,0000 |
| penzugy.bankparositas | nyelv hu | 100 | 26 (26%) → 100 (100%) | 73 → 0 | 1 → 0 | 74 / 0 | 0,0000 |
| penzugy.bankparositas | nyelv en | 86 | 33 (38%) → 86 (100%) | 51 → 0 | 2 → 0 | 53 / 0 | 0,0000 |
| muszaki.hibaelharitas | összes | 182 | 95 (52%) → 168 (92%) | 80 → 10 | 7 → 4 | 73 / 0 | 0,0000 |
| muszaki.hibaelharitas | változat H3-valtas | 182 | 95 (52%) → 168 (92%) | 80 → 10 | 7 → 4 | 73 / 0 | 0,0000 |
| muszaki.hibaelharitas | nyelv hu | 86 | 44 (51%) → 78 (91%) | 38 → 7 | 4 → 1 | 34 / 0 | 0,0000 |
| muszaki.hibaelharitas | nyelv en | 96 | 51 (53%) → 90 (94%) | 42 → 3 | 3 → 3 | 39 / 0 | 0,0000 |
| szabaly.koltsegelszamolas | összes | 199 | 51 (26%) → 133 (67%) | 146 → 66 | 2 → 0 | 83 / 1 | 0,0000 |
| szabaly.koltsegelszamolas | változat S3a-netto | 100 | 31 (31%) → 66 (66%) | 69 → 34 | 0 → 0 | 36 / 1 | 0,0000 |
| szabaly.koltsegelszamolas | változat S3b-deviza | 99 | 20 (20%) → 67 (68%) | 77 → 32 | 2 → 0 | 47 / 0 | 0,0000 |
| szabaly.koltsegelszamolas | nyelv hu | 100 | 45 (45%) → 90 (90%) | 53 → 10 | 2 → 0 | 46 / 1 | 0,0000 |
| szabaly.koltsegelszamolas | nyelv en | 99 | 6 (6%) → 43 (43%) | 93 → 56 | 0 → 0 | 37 / 0 | 0,0000 |

| család | Δ helyes arány [95%] | B1-S AUROC: eredeti → kieg. | B1-R AUROC: eredeti → kieg. | B1-LR AUROC: eredeti → kieg. | B1-R0 AUROC: eredeti → kieg. |
|---|---|---|---|---|---|
| penzugy.bankparositas | 0,683 [0,614; 0,750] | 0,323 → – | 0,203 → – | 0,331 → – | 0,323 → – |
| muszaki.hibaelharitas | 0,401 [0,319; 0,486] | 0,603 → 0,923 | 0,699 → 0,938 | 0,588 → 0,820 | 0,629 → 0,646 |
| szabaly.koltsegelszamolas | 0,412 [0,342; 0,477] | 0,309 → 0,535 | 0,372 → 0,433 | 0,420 → 0,560 | 0,615 → 0,656 |

Munkapont a változatlan τ-val (lezárt, ebből hibás; seedes karon a seedek átlaga):

| család | kar | eredeti | kiegészített |
|---|---|---|---|
| penzugy.bankparositas | B1-S | nincs munkapont | nincs munkapont |
| penzugy.bankparositas | B1-R | 19,0, hibás 17,7 | 50,7, hibás 0,0 |
| penzugy.bankparositas | B1-LR | 14,0, hibás 11,0 | 80,0, hibás 0,0 |
| muszaki.hibaelharitas | B1-S | nincs munkapont | nincs munkapont |
| muszaki.hibaelharitas | B1-R | 50,7, hibás 11,7 | 168,3, hibás 7,7 |
| muszaki.hibaelharitas | B1-LR | 109,0, hibás 43,0 | 139,0, hibás 4,0 |
| szabaly.koltsegelszamolas | B1-S | nincs munkapont | nincs munkapont |
| szabaly.koltsegelszamolas | B1-R | 132,3, hibás 107,3 | 171,7, hibás 62,0 |
| szabaly.koltsegelszamolas | B1-LR | 21,0, hibás 21,0 | 35,0, hibás 8,0 |
