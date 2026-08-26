# D3b újramérés — a fogalom a SAJÁT angol közelítőszava felé húz? (Qwen3.5-9B · chat-sablon)

Forrás-SAE: `results_instruct/sae/` · közelítőszó-SAE: `results_d3b_instruct/sae/` · protokoll: `d3b-protokoll.md` (a futtatás előtt rögzítve). Fogalmak: 16. SESOI = +0,02 Jaccard.

A 16 angol közelítőszó-prompt (a kontrollszó-prompt sablonjával):

- `UNT-HU01` kaláka → *<|im_start|>user*
- `UNT-HU02` szeretet / szerelem → *<|im_start|>user*
- `UNT-HU03` magázás / tegezés → *<|im_start|>user*
- `UNT-HU04` puszi / csók → *<|im_start|>user*
- `UNT-HU05` honfoglalás → *<|im_start|>user*
- `UNT-HU06` sógor → *<|im_start|>user*
- `UNT-HU07` névnap → *<|im_start|>user*
- `UNT-HU08` ráér → *<|im_start|>user*
- `UNT-ZH01` 关系 (guanxi) → *<|im_start|>user*
- `UNT-ZH02` 面子 (mianzi) → *<|im_start|>user*
- `UNT-ZH03` 缘分 (yuanfen) → *<|im_start|>user*
- `UNT-ZH04` 热闹 (renao) → *<|im_start|>user*
- `UNT-ZH05` 江湖 (jianghu) → *<|im_start|>user*
- `UNT-ZH06` 撒娇 (sajiao) → *<|im_start|>user*
- `UNT-ZH07` 上火 (shanghuo) → *<|im_start|>user*
- `UNT-ZH08` 加油 (jiayou) → *<|im_start|>user*

## kérdés · 10. réteg **(ELSŐDLEGES)**

| fogalom | forrás | kérdés-token | J(saját közelítő) | J(más közelítők, átlag) | többlet | hossz-illesztett többlet (n) | kontrollszavas többlet (régi D3b) |
|---|---|---|---|---|---|---|---|
| kaláka | hu | 11 | 0.196 | 0.189 | **+0,007** | +0,003 (11) | -0,002 |
| szeretet / szerelem | hu | 9 | 0.175 | 0.153 | **+0,021** | +0,011 (8) | +0,014 |
| magázás / tegezés | hu | 13 | 0.175 | 0.165 | **+0,010** | — (2) | +0,013 |
| puszi / csók | hu | 10 | 0.181 | 0.145 | **+0,036** | +0,035 (12) | +0,019 |
| honfoglalás | hu | 10 | 0.204 | 0.180 | **+0,024** | +0,021 (12) | +0,001 |
| sógor | hu | 12 | 0.148 | 0.122 | **+0,025** | +0,033 (6) | +0,022 |
| névnap | hu | 10 | 0.138 | 0.100 | **+0,038** | +0,037 (12) | +0,015 |
| ráér | hu | 11 | 0.163 | 0.165 | **-0,003** | -0,005 (11) | +0,013 |
| 关系 (guanxi) | zh | 9 | 0.244 | 0.200 | **+0,044** | +0,026 (8) | +0,006 |
| 面子 (mianzi) | zh | 9 | 0.213 | 0.186 | **+0,027** | +0,016 (8) | +0,004 |
| 缘分 (yuanfen) | zh | 10 | 0.223 | 0.176 | **+0,047** | +0,041 (12) | -0,008 |
| 热闹 (renao) | zh | 10 | 0.229 | 0.185 | **+0,044** | +0,037 (12) | +0,019 |
| 江湖 (jianghu) | zh | 10 | 0.212 | 0.176 | **+0,036** | +0,030 (12) | +0,023 |
| 撒娇 (sajiao) | zh | 11 | 0.200 | 0.181 | **+0,018** | +0,017 (11) | -0,001 |
| 上火 (shanghuo) | zh | 12 | 0.156 | 0.172 | **-0,016** | -0,002 (6) | -0,021 |
| 加油 (jiayou) | zh | 11 | 0.192 | 0.167 | **+0,025** | +0,027 (11) | +0,039 |

- **Átlagos többlet: +0,024**, fogalom-bootstrap 95% CI [+0,015; +0,032] · előjelteszt 14 pozitív / 2 negatív, p = 0.004 · Wilcoxon p = 0.000.
- Hossz-illesztett (|Δtoken| ≤ 1, ≥ 3 pár): n = 15 fogalom, átlag +0,022, előjelteszt 13/2, p = 0.007.
- Ugyanez a RÉGI, kontrollszavas változattal (szemantikai szomszéd): átlag +0,010, előjelteszt 12/4, p = 0.077.
- Műszer-referencia: J(forrás, saját angol KÉRDÉS) átlag 0.307 (szó szerinti egyezéssel), J(forrás, saját közelítő) átlag 0.190.
- **Döntés a protokoll szerint: POZITÍV eredmény a protokoll szabálya szerint (a jel angol-specifikussága külön: 05_d3b_x_angol_specifikus.md).**

## kérdés · 16. réteg

| fogalom | forrás | kérdés-token | J(saját közelítő) | J(más közelítők, átlag) | többlet | hossz-illesztett többlet (n) | kontrollszavas többlet (régi D3b) |
|---|---|---|---|---|---|---|---|
| kaláka | hu | 11 | 0.211 | 0.202 | **+0,010** | +0,005 (11) | -0,016 |
| szeretet / szerelem | hu | 9 | 0.168 | 0.158 | **+0,009** | +0,004 (8) | -0,000 |
| magázás / tegezés | hu | 13 | 0.198 | 0.160 | **+0,038** | — (2) | +0,007 |
| puszi / csók | hu | 10 | 0.193 | 0.158 | **+0,035** | +0,037 (12) | +0,025 |
| honfoglalás | hu | 10 | 0.194 | 0.180 | **+0,014** | +0,011 (12) | +0,001 |
| sógor | hu | 12 | 0.140 | 0.125 | **+0,014** | +0,023 (6) | +0,010 |
| névnap | hu | 10 | 0.140 | 0.106 | **+0,034** | +0,035 (12) | +0,015 |
| ráér | hu | 11 | 0.183 | 0.170 | **+0,013** | +0,010 (11) | +0,021 |
| 关系 (guanxi) | zh | 9 | 0.195 | 0.144 | **+0,050** | +0,039 (8) | +0,011 |
| 面子 (mianzi) | zh | 9 | 0.161 | 0.155 | **+0,007** | -0,002 (8) | +0,006 |
| 缘分 (yuanfen) | zh | 10 | 0.183 | 0.146 | **+0,037** | +0,034 (12) | -0,005 |
| 热闹 (renao) | zh | 10 | 0.202 | 0.156 | **+0,045** | +0,041 (12) | +0,011 |
| 江湖 (jianghu) | zh | 10 | 0.177 | 0.160 | **+0,016** | +0,013 (12) | +0,008 |
| 撒娇 (sajiao) | zh | 11 | 0.152 | 0.157 | **-0,005** | -0,005 (11) | +0,006 |
| 上火 (shanghuo) | zh | 12 | 0.146 | 0.144 | **+0,002** | +0,004 (6) | -0,018 |
| 加油 (jiayou) | zh | 11 | 0.162 | 0.140 | **+0,022** | +0,022 (11) | +0,020 |

- **Átlagos többlet: +0,021**, fogalom-bootstrap 95% CI [+0,013; +0,029] · előjelteszt 15 pozitív / 1 negatív, p = 0.001 · Wilcoxon p = 0.000.
- Hossz-illesztett (|Δtoken| ≤ 1, ≥ 3 pár): n = 15 fogalom, átlag +0,018, előjelteszt 13/2, p = 0.007.
- Ugyanez a RÉGI, kontrollszavas változattal (szemantikai szomszéd): átlag +0,006, előjelteszt 12/4, p = 0.077.
- Műszer-referencia: J(forrás, saját angol KÉRDÉS) átlag 0.272 (szó szerinti egyezéssel), J(forrás, saját közelítő) átlag 0.175.
- **Döntés a protokoll szerint: POZITÍV eredmény a protokoll szabálya szerint (a jel angol-specifikussága külön: 05_d3b_x_angol_specifikus.md).**

## teljes prompt · 10. réteg

| fogalom | forrás | kérdés-token | J(saját közelítő) | J(más közelítők, átlag) | többlet | hossz-illesztett többlet (n) | kontrollszavas többlet (régi D3b) |
|---|---|---|---|---|---|---|---|
| kaláka | hu | 23 | 0.364 | 0.366 | **-0,002** | -0,007 (11) | -0,004 |
| szeretet / szerelem | hu | 21 | 0.331 | 0.305 | **+0,026** | +0,018 (8) | +0,005 |
| magázás / tegezés | hu | 25 | 0.343 | 0.327 | **+0,016** | — (2) | +0,018 |
| puszi / csók | hu | 22 | 0.361 | 0.308 | **+0,052** | +0,051 (12) | +0,024 |
| honfoglalás | hu | 22 | 0.371 | 0.345 | **+0,026** | +0,023 (12) | +0,006 |
| sógor | hu | 24 | 0.326 | 0.297 | **+0,030** | +0,038 (6) | +0,027 |
| névnap | hu | 22 | 0.323 | 0.267 | **+0,055** | +0,054 (12) | +0,014 |
| ráér | hu | 23 | 0.348 | 0.326 | **+0,022** | +0,019 (11) | +0,022 |
| 关系 (guanxi) | zh | 21 | 0.445 | 0.389 | **+0,055** | +0,039 (8) | +0,028 |
| 面子 (mianzi) | zh | 21 | 0.415 | 0.387 | **+0,028** | +0,013 (8) | +0,011 |
| 缘分 (yuanfen) | zh | 22 | 0.428 | 0.378 | **+0,049** | +0,042 (12) | +0,002 |
| 热闹 (renao) | zh | 22 | 0.427 | 0.380 | **+0,048** | +0,040 (12) | +0,029 |
| 江湖 (jianghu) | zh | 22 | 0.414 | 0.373 | **+0,041** | +0,035 (12) | +0,020 |
| 撒娇 (sajiao) | zh | 23 | 0.416 | 0.382 | **+0,034** | +0,034 (11) | -0,001 |
| 上火 (shanghuo) | zh | 24 | 0.341 | 0.369 | **-0,028** | -0,014 (6) | -0,018 |
| 加油 (jiayou) | zh | 23 | 0.391 | 0.360 | **+0,030** | +0,031 (11) | +0,023 |

- **Átlagos többlet: +0,030**, fogalom-bootstrap 95% CI [+0,019; +0,040] · előjelteszt 14 pozitív / 2 negatív, p = 0.004 · Wilcoxon p = 0.001.
- Hossz-illesztett (|Δtoken| ≤ 1, ≥ 3 pár): n = 15 fogalom, átlag +0,028, előjelteszt 13/2, p = 0.007.
- Ugyanez a RÉGI, kontrollszavas változattal (szemantikai szomszéd): átlag +0,013, előjelteszt 13/3, p = 0.021.
- Műszer-referencia: J(forrás, saját angol KÉRDÉS) átlag 0.478 (szó szerinti egyezéssel), J(forrás, saját közelítő) átlag 0.378.
- **Döntés a protokoll szerint: POZITÍV eredmény a protokoll szabálya szerint (a jel angol-specifikussága külön: 05_d3b_x_angol_specifikus.md).**

## teljes prompt · 16. réteg

| fogalom | forrás | kérdés-token | J(saját közelítő) | J(más közelítők, átlag) | többlet | hossz-illesztett többlet (n) | kontrollszavas többlet (régi D3b) |
|---|---|---|---|---|---|---|---|
| kaláka | hu | 23 | 0.357 | 0.359 | **-0,002** | -0,009 (11) | -0,021 |
| szeretet / szerelem | hu | 21 | 0.315 | 0.289 | **+0,026** | +0,020 (8) | -0,007 |
| magázás / tegezés | hu | 25 | 0.345 | 0.306 | **+0,039** | — (2) | +0,007 |
| puszi / csók | hu | 22 | 0.342 | 0.299 | **+0,044** | +0,045 (12) | +0,023 |
| honfoglalás | hu | 22 | 0.367 | 0.341 | **+0,027** | +0,024 (12) | +0,006 |
| sógor | hu | 24 | 0.296 | 0.275 | **+0,022** | +0,028 (6) | +0,023 |
| névnap | hu | 22 | 0.293 | 0.250 | **+0,043** | +0,042 (12) | +0,012 |
| ráér | hu | 23 | 0.342 | 0.316 | **+0,026** | +0,023 (11) | +0,023 |
| 关系 (guanxi) | zh | 21 | 0.422 | 0.356 | **+0,066** | +0,053 (8) | +0,017 |
| 面子 (mianzi) | zh | 21 | 0.353 | 0.351 | **+0,003** | -0,010 (8) | +0,007 |
| 缘分 (yuanfen) | zh | 22 | 0.388 | 0.348 | **+0,039** | +0,034 (12) | +0,011 |
| 热闹 (renao) | zh | 22 | 0.415 | 0.364 | **+0,051** | +0,044 (12) | +0,010 |
| 江湖 (jianghu) | zh | 22 | 0.381 | 0.349 | **+0,032** | +0,027 (12) | +0,021 |
| 撒娇 (sajiao) | zh | 23 | 0.377 | 0.350 | **+0,027** | +0,025 (11) | +0,007 |
| 上火 (shanghuo) | zh | 24 | 0.341 | 0.345 | **-0,004** | +0,000 (6) | -0,020 |
| 加油 (jiayou) | zh | 23 | 0.342 | 0.326 | **+0,016** | +0,017 (11) | +0,013 |

- **Átlagos többlet: +0,028**, fogalom-bootstrap 95% CI [+0,019; +0,038] · előjelteszt 14 pozitív / 2 negatív, p = 0.004 · Wilcoxon p = 0.000.
- Hossz-illesztett (|Δtoken| ≤ 1, ≥ 3 pár): n = 15 fogalom, átlag +0,024, előjelteszt 13/2, p = 0.007.
- Ugyanez a RÉGI, kontrollszavas változattal (szemantikai szomszéd): átlag +0,008, előjelteszt 13/3, p = 0.021.
- Műszer-referencia: J(forrás, saját angol KÉRDÉS) átlag 0.433 (szó szerinti egyezéssel), J(forrás, saját közelítő) átlag 0.355.
- **Döntés a protokoll szerint: POZITÍV eredmény a protokoll szabálya szerint (a jel angol-specifikussága külön: 05_d3b_x_angol_specifikus.md).**

## Összegzés

Az elsődleges elemzésben (kérdés-tartomány, 10. réteg) az átlagos többlet +0,024 [+0,015; +0,032], előjelteszt p = 0.004 → **POZITÍV eredmény a protokoll szabálya szerint (a jel angol-specifikussága külön: 05_d3b_x_angol_specifikus.md)**. A többi (réteg × tartomány) változat fent; ha az irányuk eltér, az elsődleges dönt, a többi érzékenységi elemzés.

⛔ Amit ez a teszt sem mér: elosztott, nem lexikális angol pivotot. A közelítőszó-prompt egyetlen angol megfogalmazás; a „nincs pozitív evidencia” nem a pivot hiányának bizonyítéka.
