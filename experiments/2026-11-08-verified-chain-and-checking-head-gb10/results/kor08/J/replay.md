# 08 javító kör — a lánc a meglévő kinyerésen (fejlesztési szám)

Hamis átengedés a `g5_k2_08` definíciójával; R: a rögzített lánc, J: `lanc08j`. Ezek a szeletek nyitottak, a javítás rájuk készült.

| forrás | család | n | hamis átengedés R | J | elvetett mező R | J | emberhez R | J | hamis kizárás R / J | hamis kötés R / J | többet zár ki R / J | új eltérés | kötés R / J |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| G2K3 | penzugy.bankparositas | 90 | 1/90 = 1,1% | 1/90 = 1,1% | 3 | 3 | 0 | 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 |
| G2K3 | muszaki.hibaelharitas | 91 | 3/91 = 3,3% | 1/91 = 1,1% | 5 | 1 | 0 | 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 |
| G2K3 | szabaly.koltsegelszamolas | 200 | 0/199 = 0,0% | 0/199 = 0,0% | 1 | 1 | 1 | 1 | 0 / 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 |
| G2F | penzugy.bankparositas | 1500 | 49/1500 = 3,3% | 46/1500 = 3,1% | 63 | 59 | 0 | 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 | 545 / 545 |
| G2F | muszaki.hibaelharitas | 1500 | 13/1499 = 0,9% | 8/1499 = 0,5% | 27 | 11 | 1 | 1 | 0 / 0 | 0 / 0 | 2 / 2 | 0 | 0 / 0 |
| G2F | szabaly.koltsegelszamolas | 1500 | 39/1489 = 2,6% | 2/1489 = 0,1% | 38 | 1 | 11 | 11 | 0 / 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 |
| G2T | penzugy.bankparositas | 256 | 2/256 = 0,8% | 2/256 = 0,8% | 5 | 5 | 0 | 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 |
| G2T | muszaki.hibaelharitas | 248 | 0/248 = 0,0% | 0/248 = 0,0% | 2 | 0 | 0 | 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 |
| G2T | szabaly.koltsegelszamolas | 2204 | 47/2204 = 2,1% | 1/2204 = 0,0% | 47 | 1 | 0 | 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 | 0 / 0 |

## Az ellenőrzés zavarópróbája (`lanc08.zavarasok`)

| próba | R | J |
|---|---|---|
| részlet-arány más szereppel (áfakulcs-szerű szövegrész nélkül) | {'megfogta': 185} | {'megfogta': 185} |
| rossz érték, jó forrásrészlet | {'megfogta': 4613} | {'megfogta': 4613} |
| kitalált forrásrészlet | {'megfogta': 4614} | {'megfogta': 4614} |
| ugyanaz a szám két szerepben | {'megfogta': 4610, 'átengedte': 3} | {'megfogta': 4610, 'átengedte': 3} |
| rossz egység | {'megfogta': 1467} | {'megfogta': 1467} |
| áfakulcs → árfolyam | {'megfogta': 100} | {'megfogta': 100} |
| bruttó nettónak jelölve | {'megfogta': 100} | {'megfogta': 100} |
| 27% áfa részlet-aránynak (Dani példája) | {'megfogta': 1} | {'megfogta': 1} |

## Új eltérések (a javítás hozta be)

