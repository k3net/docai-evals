# 08B fejlesztési próba: a lépcsők a 262 tételen

**Fejlesztési szám, nem megerősítő:** a minta és a címkék ismertek, a τ itt választott, ezért a modell-lépcsők hibaaránya optimista. Csak aggregátum.

Hatókör 255 / 262 tétel (K / N és több számlás nélkül). Címkék: {'MATCH': 139, 'MISSING_DATA': 62, 'OUT_OF_SCOPE': 47, 'NO_MATCH': 7}. A lánc kimenete: {'modell': 214, 'kotes': 23}.

Hivatkozás: a közleményben pontosan egy jelölt számlaszáma 93 tételen, a kinyerés ebből 30-et hozott; eldobott mező 1, kizárt jelölt 0.

| lépcső | lezárt | hibás | hibaarány [95%] | új a termékhez / ebből hibás | a hibák címkéje |
|---|---|---|---|---|---|
| lánc (csak kötés) | 22 | 0 | 0,0% [0,0; 0,0] | 1 / 0 | – |
| lánc + L-S | 101 | 2 | 2,0% [0,0; 5,3] | 2 / 0 | {'MISSING_DATA': 2} |
| lánc + L-S + iker-kapu | 101 | 2 | 2,0% [0,0; 5,3] | 2 / 0 | {'MISSING_DATA': 2} |
| lánc + L-R07 | 43 | 0 | 0,0% [0,0; 0,0] | 3 / 0 | – |
| lánc + L-R07 + iker-kapu | 77 | 1 | 1,3% [0,0; 4,3] | 3 / 0 | {'MISSING_DATA': 1} |
| lánc + L-R | 76 | 1 | 1,3% [0,0; 4,5] | 1 / 0 | {'MISSING_DATA': 1} |
| lánc + L-R + iker-kapu | 72 | 1 | 1,4% [0,0; 4,8] | 1 / 0 | {'MISSING_DATA': 1} |
| lánc + L-RN | 91 | 1 | 1,1% [0,0; 3,7] | 2 / 0 | {'MISSING_DATA': 1} |
| lánc + L-RN + iker-kapu | 94 | 1 | 1,1% [0,0; 3,7] | 2 / 0 | {'MISSING_DATA': 1} |
| lánc + L-LR | 81 | 1 | 1,2% [0,0; 4,1] | 2 / 0 | {'MISSING_DATA': 1} |
| lánc + L-LR + iker-kapu | 102 | 2 | 2,0% [0,0; 5,2] | 2 / 0 | {'MISSING_DATA': 2} |
| lánc + L-LRN | 70 | 1 | 1,4% [0,0; 5,1] | 2 / 0 | {'MISSING_DATA': 1} |
| lánc + L-LRN + iker-kapu | 70 | 1 | 1,4% [0,0; 4,8] | 2 / 0 | {'MISSING_DATA': 1} |

**A modell döntései a címkék szerint (a modellhez ment tételek):**

| címke | döntés | n |
|---|---|---|
| MATCH | SELECT | 117 |
| MISSING_DATA | SELECT | 33 |
| MISSING_DATA | X | 20 |
| NO_MATCH | X | 3 |
| OUT_OF_SCOPE | SELECT | 3 |
| OUT_OF_SCOPE | X | 32 |

**A SELECT-ek rangsora (helyes a nem helyes ellen):**

| kar | AUROC | helyes / nem helyes |
|---|---|---|
| L-S | 0,911 | 117 / 36 |
| L-R07 | 0,865 | 117 / 36 |
| L-R | 0,836 | 117 / 36 |
| L-RN | 0,910 | 117 / 36 |
| L-LR | 0,918 | 117 / 36 |
| L-LRN | 0,875 | 117 / 36 |
