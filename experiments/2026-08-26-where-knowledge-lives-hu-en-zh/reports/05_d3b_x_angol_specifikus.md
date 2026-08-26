# D3b kiegészítés — angol-specifikus a vonzás? (Qwen3.5-9B-Base)

Páros különbség fogalmanként: J(forrás, ANGOL közelítő) − J(forrás, HARMADIK nyelvű közelítő); kontroll-pár: ugyanez a kontrollszó-promptokkal. ⚠️ Feltáró (a protokoll kiegészítése az elsődleges eredmény után). SESOI = +0,02.

## kérdés · 10. réteg **(ELSŐDLEGES)**

| fogalom | forrás | harmadik | token en/3. | J(en közelítő) | J(3. nyelvű közelítő) | Δ közelítő | Δ kontrollszó | Δ−Δ |
|---|---|---|---|---|---|---|---|---|
| kaláka | hu | zh | 11/6 | 0.140 | 0.116 | **+0,024** | +0,044 | -0,020 |
| szeretet / szerelem | hu | zh | 9/6 | 0.137 | 0.121 | **+0,015** | +0,026 | -0,011 |
| magázás / tegezés | hu | zh | 13/11 | 0.147 | 0.108 | **+0,040** | +0,037 | +0,002 |
| puszi / csók | hu | zh | 10/6 | 0.151 | 0.124 | **+0,027** | +0,035 | -0,008 |
| honfoglalás | hu | zh | 10/6 | 0.172 | 0.123 | **+0,049** | +0,044 | +0,005 |
| sógor | hu | zh | 12/6 | 0.135 | 0.095 | **+0,041** | +0,049 | -0,008 |
| névnap | hu | zh | 10/7 | 0.107 | 0.117 | **-0,011** | +0,010 | -0,021 |
| ráér | hu | zh | 11/6 | 0.118 | 0.108 | **+0,010** | +0,023 | -0,013 |
| 关系 (guanxi) | zh | hu | 9/10 | 0.193 | 0.140 | **+0,052** | +0,035 | +0,018 |
| 面子 (mianzi) | zh | hu | 9/8 | 0.184 | 0.137 | **+0,047** | +0,038 | +0,009 |
| 缘分 (yuanfen) | zh | hu | 10/9 | 0.198 | 0.146 | **+0,051** | +0,047 | +0,004 |
| 热闹 (renao) | zh | hu | 10/9 | 0.195 | 0.143 | **+0,052** | +0,053 | -0,002 |
| 江湖 (jianghu) | zh | hu | 10/10 | 0.198 | 0.129 | **+0,070** | +0,026 | +0,044 |
| 撒娇 (sajiao) | zh | hu | 11/12 | 0.175 | 0.145 | **+0,030** | +0,034 | -0,004 |
| 上火 (shanghuo) | zh | hu | 12/13 | 0.136 | 0.096 | **+0,040** | +0,013 | +0,027 |
| 加油 (jiayou) | zh | hu | 11/9 | 0.169 | 0.110 | **+0,058** | +0,060 | -0,002 |

- Δ közelítő (angol − harmadik): átlag **+0,037** [+0,028; +0,046], előjel 15/1, p = 0.001, Wilcoxon p = 0.000.
- Δ kontrollszó (angol − harmadik, meglévő `-ctrl` promptok): átlag +0,036, előjel 16/0, p = 0.000 (ez a nyelv/hossz miatti alap-eltolódás).
- **Különbség a különbségben:** átlag **+0,001** [-0,006; +0,009], előjel 7/9, p = 0.804.
- A HARMADIK nyelvű közelítőn belül a „saját − a többi (azonos nyelvű, n = 7) közelítő” többlet: átlag **+0,015** [+0,008; +0,022], előjel 14/2, p = 0.004 (ha ez is pozitív, a fogalom a saját közelítője felé húz a harmadik nyelven is).
- **Olvasat: a vonzás NEM angol-specifikus (a különbség-a-különbségben a SESOI alatt).**

## kérdés · 16. réteg

| fogalom | forrás | harmadik | token en/3. | J(en közelítő) | J(3. nyelvű közelítő) | Δ közelítő | Δ kontrollszó | Δ−Δ |
|---|---|---|---|---|---|---|---|---|
| kaláka | hu | zh | 11/6 | 0.158 | 0.118 | **+0,040** | +0,047 | -0,008 |
| szeretet / szerelem | hu | zh | 9/6 | 0.128 | 0.105 | **+0,023** | +0,038 | -0,015 |
| magázás / tegezés | hu | zh | 13/11 | 0.163 | 0.112 | **+0,051** | +0,043 | +0,008 |
| puszi / csók | hu | zh | 10/6 | 0.147 | 0.101 | **+0,046** | +0,066 | -0,020 |
| honfoglalás | hu | zh | 10/6 | 0.170 | 0.112 | **+0,057** | +0,042 | +0,016 |
| sógor | hu | zh | 12/6 | 0.130 | 0.094 | **+0,035** | +0,051 | -0,016 |
| névnap | hu | zh | 10/7 | 0.108 | 0.098 | **+0,010** | +0,016 | -0,006 |
| ráér | hu | zh | 11/6 | 0.145 | 0.100 | **+0,045** | +0,039 | +0,006 |
| 关系 (guanxi) | zh | hu | 9/10 | 0.174 | 0.117 | **+0,057** | +0,030 | +0,028 |
| 面子 (mianzi) | zh | hu | 9/8 | 0.155 | 0.125 | **+0,030** | +0,029 | +0,001 |
| 缘分 (yuanfen) | zh | hu | 10/9 | 0.169 | 0.131 | **+0,038** | +0,048 | -0,010 |
| 热闹 (renao) | zh | hu | 10/9 | 0.173 | 0.127 | **+0,046** | +0,043 | +0,003 |
| 江湖 (jianghu) | zh | hu | 10/10 | 0.167 | 0.144 | **+0,022** | +0,044 | -0,022 |
| 撒娇 (sajiao) | zh | hu | 11/12 | 0.146 | 0.134 | **+0,013** | +0,038 | -0,026 |
| 上火 (shanghuo) | zh | hu | 12/13 | 0.133 | 0.102 | **+0,031** | -0,000 | +0,032 |
| 加油 (jiayou) | zh | hu | 11/9 | 0.137 | 0.102 | **+0,036** | +0,034 | +0,001 |

- Δ közelítő (angol − harmadik): átlag **+0,036** [+0,029; +0,043], előjel 16/0, p = 0.000, Wilcoxon p = 0.000.
- Δ kontrollszó (angol − harmadik, meglévő `-ctrl` promptok): átlag +0,038, előjel 15/1, p = 0.001 (ez a nyelv/hossz miatti alap-eltolódás).
- **Különbség a különbségben:** átlag **-0,002** [-0,010; +0,006], előjel 8/8, p = 1.000.
- A HARMADIK nyelvű közelítőn belül a „saját − a többi (azonos nyelvű, n = 7) közelítő” többlet: átlag **+0,013** [+0,006; +0,019], előjel 14/2, p = 0.004 (ha ez is pozitív, a fogalom a saját közelítője felé húz a harmadik nyelven is).
- **Olvasat: a vonzás NEM angol-specifikus (a különbség-a-különbségben a SESOI alatt).**

## teljes prompt · 10. réteg

| fogalom | forrás | harmadik | token en/3. | J(en közelítő) | J(3. nyelvű közelítő) | Δ közelítő | Δ kontrollszó | Δ−Δ |
|---|---|---|---|---|---|---|---|---|
| kaláka | hu | zh | 16/10 | 0.179 | 0.183 | **-0,004** | +0,006 | -0,010 |
| szeretet / szerelem | hu | zh | 14/10 | 0.172 | 0.172 | **+0,000** | +0,013 | -0,013 |
| magázás / tegezés | hu | zh | 18/15 | 0.179 | 0.159 | **+0,020** | +0,005 | +0,015 |
| puszi / csók | hu | zh | 15/10 | 0.183 | 0.175 | **+0,007** | +0,008 | -0,001 |
| honfoglalás | hu | zh | 15/10 | 0.197 | 0.182 | **+0,015** | +0,005 | +0,010 |
| sógor | hu | zh | 17/10 | 0.162 | 0.166 | **-0,004** | +0,010 | -0,013 |
| névnap | hu | zh | 15/11 | 0.144 | 0.169 | **-0,026** | -0,006 | -0,020 |
| ráér | hu | zh | 16/10 | 0.147 | 0.153 | **-0,006** | +0,008 | -0,014 |
| 关系 (guanxi) | zh | hu | 14/20 | 0.229 | 0.192 | **+0,037** | +0,025 | +0,012 |
| 面子 (mianzi) | zh | hu | 14/18 | 0.221 | 0.197 | **+0,024** | +0,027 | -0,002 |
| 缘分 (yuanfen) | zh | hu | 15/19 | 0.229 | 0.200 | **+0,029** | +0,021 | +0,008 |
| 热闹 (renao) | zh | hu | 15/19 | 0.235 | 0.196 | **+0,040** | +0,035 | +0,005 |
| 江湖 (jianghu) | zh | hu | 15/20 | 0.226 | 0.194 | **+0,033** | +0,009 | +0,024 |
| 撒娇 (sajiao) | zh | hu | 16/22 | 0.212 | 0.197 | **+0,015** | +0,022 | -0,007 |
| 上火 (shanghuo) | zh | hu | 17/23 | 0.181 | 0.153 | **+0,028** | +0,006 | +0,022 |
| 加油 (jiayou) | zh | hu | 16/19 | 0.202 | 0.172 | **+0,030** | +0,033 | -0,003 |

- Δ közelítő (angol − harmadik): átlag **+0,015** [+0,006; +0,024], előjel 12/4, p = 0.077, Wilcoxon p = 0.009.
- Δ kontrollszó (angol − harmadik, meglévő `-ctrl` promptok): átlag +0,014, előjel 15/1, p = 0.001 (ez a nyelv/hossz miatti alap-eltolódás).
- **Különbség a különbségben:** átlag **+0,001** [-0,006; +0,007], előjel 7/9, p = 0.804.
- A HARMADIK nyelvű közelítőn belül a „saját − a többi (azonos nyelvű, n = 7) közelítő” többlet: átlag **+0,011** [+0,004; +0,017], előjel 15/1, p = 0.001 (ha ez is pozitív, a fogalom a saját közelítője felé húz a harmadik nyelven is).
- **Olvasat: a vonzás NEM angol-specifikus (a különbség-a-különbségben a SESOI alatt).**

## teljes prompt · 16. réteg

| fogalom | forrás | harmadik | token en/3. | J(en közelítő) | J(3. nyelvű közelítő) | Δ közelítő | Δ kontrollszó | Δ−Δ |
|---|---|---|---|---|---|---|---|---|
| kaláka | hu | zh | 16/10 | 0.166 | 0.176 | **-0,010** | +0,012 | -0,022 |
| szeretet / szerelem | hu | zh | 14/10 | 0.158 | 0.166 | **-0,009** | -0,005 | -0,004 |
| magázás / tegezés | hu | zh | 18/15 | 0.180 | 0.166 | **+0,014** | +0,007 | +0,008 |
| puszi / csók | hu | zh | 15/10 | 0.159 | 0.162 | **-0,003** | +0,013 | -0,016 |
| honfoglalás | hu | zh | 15/10 | 0.183 | 0.170 | **+0,014** | -0,012 | +0,026 |
| sógor | hu | zh | 17/10 | 0.151 | 0.166 | **-0,015** | +0,003 | -0,018 |
| névnap | hu | zh | 15/11 | 0.131 | 0.157 | **-0,026** | -0,021 | -0,005 |
| ráér | hu | zh | 16/10 | 0.155 | 0.152 | **+0,003** | +0,005 | -0,002 |
| 关系 (guanxi) | zh | hu | 14/20 | 0.207 | 0.177 | **+0,030** | +0,022 | +0,008 |
| 面子 (mianzi) | zh | hu | 14/18 | 0.188 | 0.176 | **+0,012** | +0,015 | -0,002 |
| 缘分 (yuanfen) | zh | hu | 15/19 | 0.202 | 0.179 | **+0,023** | +0,027 | -0,004 |
| 热闹 (renao) | zh | hu | 15/19 | 0.202 | 0.179 | **+0,022** | +0,020 | +0,002 |
| 江湖 (jianghu) | zh | hu | 15/20 | 0.201 | 0.189 | **+0,013** | +0,020 | -0,008 |
| 撒娇 (sajiao) | zh | hu | 16/22 | 0.185 | 0.181 | **+0,003** | +0,028 | -0,025 |
| 上火 (shanghuo) | zh | hu | 17/23 | 0.172 | 0.150 | **+0,022** | -0,013 | +0,034 |
| 加油 (jiayou) | zh | hu | 16/19 | 0.175 | 0.167 | **+0,008** | +0,020 | -0,013 |

- Δ közelítő (angol − harmadik): átlag **+0,006** [-0,001; +0,014], előjel 11/5, p = 0.210, Wilcoxon p = 0.130.
- Δ kontrollszó (angol − harmadik, meglévő `-ctrl` promptok): átlag +0,009, előjel 12/4, p = 0.077 (ez a nyelv/hossz miatti alap-eltolódás).
- **Különbség a különbségben:** átlag **-0,003** [-0,010; +0,005], előjel 5/11, p = 0.210.
- A HARMADIK nyelvű közelítőn belül a „saját − a többi (azonos nyelvű, n = 7) közelítő” többlet: átlag **+0,009** [+0,002; +0,014], előjel 13/3, p = 0.021 (ha ez is pozitív, a fogalom a saját közelítője felé húz a harmadik nyelven is).
- **Olvasat: a vonzás NEM angol-specifikus (a különbség-a-különbségben a SESOI alatt).**

## Összegzés

Harmadik nyelvű saját-többlet (kérdés, 10. réteg): +0,015 [+0,008; +0,022], p = 0.004.

Elsődleges (kérdés, 10. réteg): Δ közelítő +0,037 [+0,028; +0,046] (p = 0.001); a kontrollszó-pár alap-eltolódása +0,036; különbség a különbségben +0,001 [-0,006; +0,009] (p = 0.804) → **a vonzás NEM angol-specifikus (a különbség-a-különbségben a SESOI alatt)**.
