# D3b újramérés — a fogalom a SAJÁT angol közelítőszava felé húz? (Qwen3.5-9B-Base)

Forrás-SAE: `results/sae/` · közelítőszó-SAE: `results_d3b/sae/` · protokoll: `d3b-protokoll.md` (a futtatás előtt rögzítve). Fogalmak: 16. SESOI = +0,02 Jaccard.

A 16 angol közelítőszó-prompt (a kontrollszó-prompt sablonjával):

- `UNT-HU01` kaláka → *Question: What does the expression 'mutual aid' mean?*
- `UNT-HU02` szeretet / szerelem → *Question: What does the word 'love' mean?*
- `UNT-HU03` magázás / tegezés → *Question: What does the expression 'formal vs informal you' mean?*
- `UNT-HU04` puszi / csók → *Question: What does the word 'kiss' mean?*
- `UNT-HU05` honfoglalás → *Question: What does the word 'conquest' mean?*
- `UNT-HU06` sógor → *Question: What does the word 'brother-in-law' mean?*
- `UNT-HU07` névnap → *Question: What does the expression 'name day' mean?*
- `UNT-HU08` ráér → *Question: What does the expression 'to have time' mean?*
- `UNT-ZH01` 关系 (guanxi) → *Question: What does the word 'connections' mean?*
- `UNT-ZH02` 面子 (mianzi) → *Question: What does the word 'face' mean?*
- `UNT-ZH03` 缘分 (yuanfen) → *Question: What does the word 'fate' mean?*
- `UNT-ZH04` 热闹 (renao) → *Question: What does the word 'lively' mean?*
- `UNT-ZH05` 江湖 (jianghu) → *Question: What does the word 'underworld' mean?*
- `UNT-ZH06` 撒娇 (sajiao) → *Question: What does the expression 'to act cute' mean?*
- `UNT-ZH07` 上火 (shanghuo) → *Question: What does the expression 'to have internal heat' mean?*
- `UNT-ZH08` 加油 (jiayou) → *Question: What does the expression 'go for it' mean?*

## kérdés · 10. réteg **(ELSŐDLEGES)**

| fogalom | forrás | kérdés-token | J(saját közelítő) | J(más közelítők, átlag) | többlet | hossz-illesztett többlet (n) | kontrollszavas többlet (régi D3b) |
|---|---|---|---|---|---|---|---|
| kaláka | hu | 11 | 0.140 | 0.148 | **-0,008** | -0,010 (11) | -0,002 |
| szeretet / szerelem | hu | 9 | 0.137 | 0.118 | **+0,018** | +0,011 (8) | +0,011 |
| magázás / tegezés | hu | 13 | 0.147 | 0.128 | **+0,019** | — (2) | +0,011 |
| puszi / csók | hu | 10 | 0.151 | 0.115 | **+0,036** | +0,037 (12) | +0,026 |
| honfoglalás | hu | 10 | 0.172 | 0.143 | **+0,029** | +0,026 (12) | +0,002 |
| sógor | hu | 12 | 0.135 | 0.103 | **+0,033** | +0,040 (6) | +0,018 |
| névnap | hu | 10 | 0.107 | 0.083 | **+0,024** | +0,024 (12) | +0,011 |
| ráér | hu | 11 | 0.118 | 0.125 | **-0,007** | -0,006 (11) | +0,007 |
| 关系 (guanxi) | zh | 9 | 0.193 | 0.164 | **+0,029** | +0,017 (8) | -0,001 |
| 面子 (mianzi) | zh | 9 | 0.184 | 0.158 | **+0,026** | +0,019 (8) | -0,000 |
| 缘分 (yuanfen) | zh | 10 | 0.198 | 0.165 | **+0,032** | +0,029 (12) | -0,006 |
| 热闹 (renao) | zh | 10 | 0.195 | 0.159 | **+0,036** | +0,032 (12) | +0,018 |
| 江湖 (jianghu) | zh | 10 | 0.198 | 0.158 | **+0,041** | +0,037 (12) | +0,004 |
| 撒娇 (sajiao) | zh | 11 | 0.175 | 0.160 | **+0,016** | +0,014 (11) | -0,002 |
| 上火 (shanghuo) | zh | 12 | 0.136 | 0.156 | **-0,020** | -0,015 (6) | -0,008 |
| 加油 (jiayou) | zh | 11 | 0.169 | 0.149 | **+0,020** | +0,020 (11) | +0,026 |

- **Átlagos többlet: +0,020**, fogalom-bootstrap 95% CI [+0,011; +0,028] · előjelteszt 13 pozitív / 3 negatív, p = 0.021 · Wilcoxon p = 0.001.
- Hossz-illesztett (|Δtoken| ≤ 1, ≥ 3 pár): n = 15 fogalom, átlag +0,018, előjelteszt 12/3, p = 0.035.
- Ugyanez a RÉGI, kontrollszavas változattal (szemantikai szomszéd): átlag +0,007, előjelteszt 10/6, p = 0.454.
- Műszer-referencia: J(forrás, saját angol KÉRDÉS) átlag 0.254 (szó szerinti egyezéssel), J(forrás, saját közelítő) átlag 0.160.
- **Döntés a protokoll szerint: POZITÍV eredmény a protokoll szabálya szerint (a jel angol-specifikussága külön: 05_d3b_x_angol_specifikus.md).**

## kérdés · 16. réteg

| fogalom | forrás | kérdés-token | J(saját közelítő) | J(más közelítők, átlag) | többlet | hossz-illesztett többlet (n) | kontrollszavas többlet (régi D3b) |
|---|---|---|---|---|---|---|---|
| kaláka | hu | 11 | 0.158 | 0.159 | **-0,001** | -0,005 (11) | -0,005 |
| szeretet / szerelem | hu | 9 | 0.128 | 0.123 | **+0,005** | +0,004 (8) | +0,010 |
| magázás / tegezés | hu | 13 | 0.163 | 0.126 | **+0,037** | — (2) | +0,006 |
| puszi / csók | hu | 10 | 0.147 | 0.123 | **+0,024** | +0,026 (12) | +0,026 |
| honfoglalás | hu | 10 | 0.170 | 0.152 | **+0,018** | +0,017 (12) | -0,000 |
| sógor | hu | 12 | 0.130 | 0.113 | **+0,017** | +0,021 (6) | +0,019 |
| névnap | hu | 10 | 0.108 | 0.079 | **+0,028** | +0,029 (12) | +0,011 |
| ráér | hu | 11 | 0.145 | 0.134 | **+0,011** | +0,009 (11) | +0,015 |
| 关系 (guanxi) | zh | 9 | 0.174 | 0.151 | **+0,023** | +0,013 (8) | +0,014 |
| 面子 (mianzi) | zh | 9 | 0.155 | 0.143 | **+0,012** | +0,005 (8) | +0,006 |
| 缘分 (yuanfen) | zh | 10 | 0.169 | 0.141 | **+0,028** | +0,026 (12) | +0,003 |
| 热闹 (renao) | zh | 10 | 0.173 | 0.145 | **+0,028** | +0,025 (12) | +0,006 |
| 江湖 (jianghu) | zh | 10 | 0.167 | 0.144 | **+0,022** | +0,020 (12) | +0,024 |
| 撒娇 (sajiao) | zh | 11 | 0.146 | 0.141 | **+0,005** | +0,006 (11) | +0,006 |
| 上火 (shanghuo) | zh | 12 | 0.133 | 0.142 | **-0,009** | -0,005 (6) | -0,013 |
| 加油 (jiayou) | zh | 11 | 0.137 | 0.122 | **+0,016** | +0,014 (11) | +0,017 |

- **Átlagos többlet: +0,017**, fogalom-bootstrap 95% CI [+0,011; +0,022] · előjelteszt 14 pozitív / 2 negatív, p = 0.004 · Wilcoxon p = 0.000.
- Hossz-illesztett (|Δtoken| ≤ 1, ≥ 3 pár): n = 15 fogalom, átlag +0,014, előjelteszt 13/2, p = 0.007.
- Ugyanez a RÉGI, kontrollszavas változattal (szemantikai szomszéd): átlag +0,009, előjelteszt 13/3, p = 0.021.
- Műszer-referencia: J(forrás, saját angol KÉRDÉS) átlag 0.233 (szó szerinti egyezéssel), J(forrás, saját közelítő) átlag 0.150.
- **Döntés a protokoll szerint: nincs pozitív evidencia (a CI a SESOI-t is tartalmazza).**

## teljes prompt · 10. réteg

| fogalom | forrás | kérdés-token | J(saját közelítő) | J(más közelítők, átlag) | többlet | hossz-illesztett többlet (n) | kontrollszavas többlet (régi D3b) |
|---|---|---|---|---|---|---|---|
| kaláka | hu | 16 | 0.179 | 0.179 | **-0,000** | -0,001 (11) | -0,006 |
| szeretet / szerelem | hu | 14 | 0.172 | 0.156 | **+0,016** | +0,009 (8) | +0,012 |
| magázás / tegezés | hu | 18 | 0.179 | 0.162 | **+0,017** | — (2) | +0,008 |
| puszi / csók | hu | 15 | 0.183 | 0.150 | **+0,032** | +0,032 (12) | +0,018 |
| honfoglalás | hu | 15 | 0.197 | 0.174 | **+0,023** | +0,021 (12) | -0,002 |
| sógor | hu | 17 | 0.162 | 0.144 | **+0,018** | +0,024 (6) | +0,011 |
| névnap | hu | 15 | 0.144 | 0.126 | **+0,018** | +0,016 (12) | +0,008 |
| ráér | hu | 16 | 0.147 | 0.153 | **-0,006** | -0,006 (11) | +0,007 |
| 关系 (guanxi) | zh | 14 | 0.229 | 0.205 | **+0,023** | +0,012 (8) | +0,003 |
| 面子 (mianzi) | zh | 14 | 0.221 | 0.199 | **+0,022** | +0,015 (8) | -0,001 |
| 缘分 (yuanfen) | zh | 15 | 0.229 | 0.204 | **+0,025** | +0,022 (12) | -0,006 |
| 热闹 (renao) | zh | 15 | 0.235 | 0.203 | **+0,033** | +0,029 (12) | +0,011 |
| 江湖 (jianghu) | zh | 15 | 0.226 | 0.199 | **+0,027** | +0,023 (12) | -0,000 |
| 撒娇 (sajiao) | zh | 16 | 0.212 | 0.202 | **+0,010** | +0,010 (11) | -0,001 |
| 上火 (shanghuo) | zh | 17 | 0.181 | 0.200 | **-0,019** | -0,014 (6) | -0,013 |
| 加油 (jiayou) | zh | 16 | 0.202 | 0.192 | **+0,010** | +0,011 (11) | +0,019 |

- **Átlagos többlet: +0,016**, fogalom-bootstrap 95% CI [+0,008; +0,022] · előjelteszt 13 pozitív / 3 negatív, p = 0.021 · Wilcoxon p = 0.002.
- Hossz-illesztett (|Δtoken| ≤ 1, ≥ 3 pár): n = 15 fogalom, átlag +0,014, előjelteszt 12/3, p = 0.035.
- Ugyanez a RÉGI, kontrollszavas változattal (szemantikai szomszéd): átlag +0,004, előjelteszt 9/7, p = 0.804.
- Műszer-referencia: J(forrás, saját angol KÉRDÉS) átlag 0.254 (szó szerinti egyezéssel), J(forrás, saját közelítő) átlag 0.194.
- **Döntés a protokoll szerint: nincs pozitív evidencia (a CI a SESOI-t is tartalmazza).**

## teljes prompt · 16. réteg

| fogalom | forrás | kérdés-token | J(saját közelítő) | J(más közelítők, átlag) | többlet | hossz-illesztett többlet (n) | kontrollszavas többlet (régi D3b) |
|---|---|---|---|---|---|---|---|
| kaláka | hu | 16 | 0.166 | 0.170 | **-0,004** | -0,006 (11) | -0,001 |
| szeretet / szerelem | hu | 14 | 0.158 | 0.146 | **+0,012** | +0,010 (8) | +0,005 |
| magázás / tegezés | hu | 18 | 0.180 | 0.149 | **+0,031** | — (2) | +0,003 |
| puszi / csók | hu | 15 | 0.159 | 0.145 | **+0,014** | +0,015 (12) | +0,015 |
| honfoglalás | hu | 15 | 0.183 | 0.168 | **+0,016** | +0,015 (12) | -0,007 |
| sógor | hu | 17 | 0.151 | 0.145 | **+0,006** | +0,008 (6) | +0,014 |
| névnap | hu | 15 | 0.131 | 0.113 | **+0,018** | +0,017 (12) | +0,007 |
| ráér | hu | 16 | 0.155 | 0.148 | **+0,007** | +0,006 (11) | +0,010 |
| 关系 (guanxi) | zh | 14 | 0.207 | 0.190 | **+0,017** | +0,008 (8) | +0,017 |
| 面子 (mianzi) | zh | 14 | 0.188 | 0.183 | **+0,006** | -0,001 (8) | +0,000 |
| 缘分 (yuanfen) | zh | 15 | 0.202 | 0.180 | **+0,022** | +0,020 (12) | +0,001 |
| 热闹 (renao) | zh | 15 | 0.202 | 0.181 | **+0,021** | +0,018 (12) | +0,001 |
| 江湖 (jianghu) | zh | 15 | 0.201 | 0.182 | **+0,020** | +0,018 (12) | +0,014 |
| 撒娇 (sajiao) | zh | 16 | 0.185 | 0.182 | **+0,002** | +0,003 (11) | +0,004 |
| 上火 (shanghuo) | zh | 17 | 0.172 | 0.183 | **-0,011** | -0,007 (6) | -0,021 |
| 加油 (jiayou) | zh | 16 | 0.175 | 0.163 | **+0,012** | +0,012 (11) | +0,021 |

- **Átlagos többlet: +0,012**, fogalom-bootstrap 95% CI [+0,007; +0,017] · előjelteszt 14 pozitív / 2 negatív, p = 0.004 · Wilcoxon p = 0.001.
- Hossz-illesztett (|Δtoken| ≤ 1, ≥ 3 pár): n = 15 fogalom, átlag +0,009, előjelteszt 12/3, p = 0.035.
- Ugyanez a RÉGI, kontrollszavas változattal (szemantikai szomszéd): átlag +0,005, előjelteszt 13/3, p = 0.021.
- Műszer-referencia: J(forrás, saját angol KÉRDÉS) átlag 0.231 (szó szerinti egyezéssel), J(forrás, saját közelítő) átlag 0.176.
- **Döntés a protokoll szerint: a mért pivot-hatás kisebb, mint a SESOI.**

## Összegzés

Az elsődleges elemzésben (kérdés-tartomány, 10. réteg) az átlagos többlet +0,020 [+0,011; +0,028], előjelteszt p = 0.021 → **POZITÍV eredmény a protokoll szabálya szerint (a jel angol-specifikussága külön: 05_d3b_x_angol_specifikus.md)**. A többi (réteg × tartomány) változat fent; ha az irányuk eltér, az elsődleges dönt, a többi érzékenységi elemzés.

⛔ Amit ez a teszt sem mér: elosztott, nem lexikális angol pivotot. A közelítőszó-prompt egyetlen angol megfogalmazás; a „nincs pozitív evidencia” nem a pivot hiányának bizonyítéka.
