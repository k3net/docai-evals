# 08 erősebb kontroll (N) — a rögzítés

- **Verzió:** v0.2, 2026-11-08. Dani jóváhagyásával rögzítve („elfogadom, mehet”; `kor08/rogzites/N/manifest.json`); a kiolvasás csak a rögzítés után indult. A v0.1-et Dani 11-08-án elfogadta, de az első címkeellenőrzés a kapun elbukott, ezért a minta és a 4. pont változott.
- **Alapja:** az M eredménye (eredménylap, F függelék): a fej nyeresége megmaradt, de a témabeli különbség miatt nem bizonyíték. Dani 11-06: „készítsd el, vigyük végig a fej kérdést”.
- **Viszony a D12-höz:** a G1-rögzítés, a G5 és az M eredményei nem változnak. A rögzített fájlokhoz nem nyúl, fej nem tanul. **Ez a fej utolsó kontrollja: a két kimenet mindegyike lezárja a kérdést.**

## 1. Kérdés

**A befagyasztott L-RN megkülönbözteti-e azt, hogy a döntő jellegű mondat a kért összegre vonatkozik-e, ha a szöveg szókincse, hossza és szerkezete azonos?**

## 2. Minta (kész, a rögzítés előtt generálva)

Minimális pár a szabálycsaládon (`szint08n.py`). Egy egységből két szöveg, ugyanazzal a tervvel és formával, mindkettőben egy döntő jellegű mondat (J, a forgatókönyv `jel2`-je), egy nem döntő mondat (L, az M mondata) és egy „korábbi, másik kérelem” jelölés:

- **(b''):** a kért összegről J(f), a korábbi kérelemről L(f'); a címke a gold.
- **(a''):** a kért összegről L(f), a korábbi kérelemről J(f'); a címke Y.

Az f' az f párja (azonos gold és csali), a korábbi kérelem helye egységenként hash, a két tagban azonos. Mindkét tag új szöveg, a (b) első változatának formájában. A bank és a hiba nem része.

**Kihozatal:** 1102 tervből 431 teljes egység (862 item), 34 forgatókönyv 40-ből, mindkét nyelven. Az elveszett 240 item nagy része a tényellenőrző hibája: ahol a pár két forgatókönyvének közös kulcsszava van, a „másik jel” tiltása mindig bukik, ezért 3 forgatókönyv-pár kiesett (F21–F22, F41–F42, F79–F80). A kiesés a kulcsszavakból következik, modellkimenet nem szól bele. A mintát nem pótoljuk.

**Szerkezeti szűrő (v0.2, `szures08n.py`, csak szöveg és terv):** a „korábbi kérelem” mondata a tartalmával együtt álljon, a kért összegről szóló mondat legyen meg a jelölő mondaton kívül, és a J a megfelelő helyen legyen. Egy egység csak mindkét tagjával marad meg. **Marad 348 egység (696 item), 33 forgatókönyv,** kiesik 83 egység (a jelölő mondat üres 74 szöveg, a kért összegről szóló mondat hiányzik 13, a J a kért összegről is szól 5).

## 3. Az illesztés ellenőrzése: teljesült

A küszöbök a generálás előtt rögzítve, az M-éi (`felszin08n.py`, `kor08/eredmenyek/N/felszin/illesztes.md`). Egy generálási kör, a szűrő után újraszámolva.

| próba | küszöb | M | N, szűrés előtt | N, szűrés után | teljesül |
|---|---|---|---|---|---|
| hossz | ≤ 0,60 | 0,582 | 0,505 | 0,506 | igen |
| a régi szöveges modell | ≤ 0,70 | 0,841 | 0,518 | 0,513 | igen |
| friss szöveges modell, forgatókönyv-páros CV | ≤ 0,80 | 0,998 | 0,714 | 0,695 | igen |

## 4. Címkeellenőrzés (a kiolvasás előtt)

**1. kör (`kor08/adat/N/audit/atnezo.html`, 11-08):** 30 vak item, a kapu legfeljebb 2 eltérés. **Eredmény: 3 eltérés, a kapu nem teljesült, a kiolvasás nem indult.** Mindhárom a generálás hibája, Dani válasza helyes: két (a'')-ben a „korábbi kérelem” mondat üres, és a J a kért összegről szól; egy (b'')-ből a J kimaradt, a tényellenőrzőn az aláírás kulcsszava vitte át. A szűrő mindhármat kiveszi, az ellenőrzött 30-ból 21 marad, azok mind egyeznek. A szűrő ezekből a hibákból készült, ezért ez a 21 nem bizonyíték rá.

**2. kör (`kor08/adat/N/audit/atnezo2.html`):** 30 friss vak item a szűrt mintából, az 1. kör egységeitől diszjunkt, id és címke nélkül (15 magyar, 15 angol; 14 (a''), 16 (b'')). Dani a szabálypontot vagy az M-et választja. **Kapu: legfeljebb 2 eltérés a 30-ból.** Ha több, a kiolvasás nem indul, és a fej a D9 szerint parkol, további generálási kör nincs. Egyedi hibás item a mintából nem kerül ki, a számot közöljük.

**A 2. kör eredménye (11-08 09:04, `dontesek2.json`, sha256 af0a72a7…): 0 eltérés a 30-ból, a kapu teljesült.** Az (a)-k mind M, a (b)-k mind a helyes szabálypont. Korlát: a lap összetétele (14 / 16) ebben a tervezetben szerepelt a kitöltés előtt, az egyes tételekről ez nem árul el semmit.

## 5. Végrehajtás

`k08n.sh`, egy futással: kinyerés az alannyal a rögzített `kinyer08`-cal; a rögzített lánc (`lanc08`, ahogy a G3-ban) kinyert és orákulum-úton; kiolvasás R-módban, a determinizmus-őrrel; pontozás a befagyasztott fejekkel; a rögzített `g5_k1_08` 10 000 replikával; a szöveges modellek ugyanazon a halmazon.

## 6. Végpont és olvasat

**Végpont:** a K1(a) a minimális párokon: az L-RN − L-S AUROC-különbség, a 95%-os intervallummal (egy próba, Holm nincs), a G1-rögzítés 8. pontjának táblájával.

- **A fej állítása áll, szűkített formában, ha mindkettő teljesül:** (1) az L-RN − L-S „javít érdemben” (alsó határ > 0 és pontbecslés ≥ 0,05); (2) az L-RN AUROC-ja nagyobb a legjobb szöveges modellénél ugyanazon a halmazon (pontbecslés). Az állítás hatóköre: a szabálycsalád, ez a konstrukció, ezek a fejek.
- **Minden más esetben az állítás elvetve,** a nem eldönthető eredmény is, és a fej a D9 szerint parkol.

**Mindkét kimenet után a fej kérdése lezárul, további kontroll nincs.** A munkaponti kép és a valódi banki eredmény (F függelék, K08V) egyik esetben sem változik: pozitív kimenet esetén sem következik belőle termékhasznosság.

**Mindig közölve:** az L-RN, L-S, L-R, L-R07, L-LRN AUROC-ja, a nyelvenkénti bontás, az (a'') és a (b'') SELECT-aránya, a τ fölött lezárt (a'') aránya, a diagnózis kiesései, a címkeellenőrzés eredménye.

## 7. Erő és idő

Az M intervallumának fél szélessége 40 klaszterrel kb. 0,06; 33 klaszterrel és kevesebb itemmel kb. 0,07–0,08-ra számítok (becslés, nem szimuláció). A G5 és az M nyeresége (0,186, illetve 0,144) ebben a méretben kimutatható, a 0,05 körüli hatás nem.

Kb. 1 óra GPU, próbánként +10 perc.
