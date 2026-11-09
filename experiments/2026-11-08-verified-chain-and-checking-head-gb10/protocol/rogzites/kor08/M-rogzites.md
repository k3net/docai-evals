# 08 illesztett kontroll (M) — a rögzítés

- **Verzió:** v0.1, 2026-11-06. Dani jóváhagyásával rögzítve („1. indulhat”; `kor08/rogzites/M/manifest.json`); a kiolvasás csak a rögzítés után indult.
- **Alapja:** az eredménylap E függeléke: a K1(a) nyeresége felszíni jeggyel magyarázható, mert az (a) a rövid, jel nélküli szöveg. Dani 11-06: „kezd a kontrollal”.
- **Viszony a D12-höz:** a G1-rögzítés és a G5 eredményei nem változnak. A rögzített fájlokhoz nem nyúl, minden burkolóként készül. Fej nem tanul.

## 1. Kérdés

**A befagyasztott L-RN megtartja-e a nyereségét az L-S-hez képest, ha az (a) nem rövid, hanem ugyanolyan hosszú, és ugyanúgy kimond egy konkrét tényt, mint a (b), csak az nem dönt?**

## 2. Minta (kész, a rögzítés előtt generálva)

- **Illesztett (a):** a G2 értelmezési tesztjének (a)-tervei változatlanul, a generátor utasításában a (b) jelének helyén egy nem döntő mondat (`illeszt08m.py`): szabálycsalád 551, bank 64, hiba 62 item. A címke Y. Szelet: `M1T`.
- **A (b):** a G2 itemjei és a G3 R-módú kiolvasása, változatlanul.
- **Modellkimenet a generálásig és az illesztés ellenőrzéséig nem készült.** A mondatok egy körben készültek, javítás nem volt.

## 3. Az illesztés ellenőrzése: nem érte el a küszöböt

A küszöbök a generálás előtt rögzítve (`felszin08m.py`, szabálycsalád). Eredmény (`kor08/eredmenyek/M/felszin/illesztes.md`):

| próba | küszöb | eredeti (a) | illesztett (a) | teljesül |
|---|---|---|---|---|
| hossz | ≤ 0,60 | 0,731 | 0,582 | igen |
| a régi szöveges modell | ≤ 0,70 | 1,000 | 0,841 | nem |
| friss szöveges modell, sabloncsoportos CV | ≤ 0,80 | – | 0,998 | nem |

A friss modell a nem döntő mondatok témáját ismeri fel (számla, átutalás, érkezett), a (b)-ben pedig a használatot és a célt (használja, éves, saját). A bankon és a hibán a régi modell is 1,000 / 0,997, ezért ott a kontroll nem illesztett.

## 4. Végrehajtás

`k08m.sh`, egy futással: kinyerés az alannyal a rögzített `kinyer08`-cal; a rögzített lánc (`lanc08`, a J nélkül, ahogy a G3-ban) kinyert és orákulum-úton; kiolvasás R-módban a `k08j.sh` `kiolvas_r`-jével, a determinizmus-őrrel; pontozás a befagyasztott fejekkel (`cache/k08/fejek08`, 07 fejek); az (a') és a meglévő (b) egyesítése; a rögzített `g5_k1_08` a G5 argumentumaival, 10 000 replikával.

## 5. Végpont és olvasat

**Végpont:** a szabálycsaládon a K1(a) az illesztett (a)-val: az L-RN − L-S AUROC-különbség, a 95%-os intervallummal (egy próba, Holm nincs), a G1-rögzítés 8. pontjának párokra vonatkozó táblájával.

**Az olvasat aszimmetrikus,** mert az illesztés nem teljesült, és a megmaradt szöveges jegyek a fejnek kedveznek:

- **Nem „javít érdemben”** (az intervallum tartalmazza a 0-t, vagy a pontbecslés < 0,05): a G5 nyeresége úgy tűnik el, hogy a szöveges jegyek egy része még elérhető. **A fejről szóló állítás elvetve, a fej a D9 szerint parkol,** további kontroll nincs. A 08B 4. lépcsője leíró.
- **„Javít érdemben”:** **nem bizonyíték,** mert a megmaradt jegyek ezt is magyarázhatják. A kérdés nyitva marad, és csak erősebb kontroll döntheti el: az (a) és a (b) is tartalmaz jel jellegű mondatot, és csak az különbözik, hogy az a kért összegre vonatkozik-e. Erről Dani dönt.

**Mindig közölve:** az L-RN és az L-S AUROC-ja, az L-R, L-R07, L-LRN, a nyelvenkénti bontás, az (a') SELECT-aránya az (a)-hoz képest, a τ fölött lezárt (a') aránya, a diagnózis kiesései. A bank és a hiba leíró, következtetés nélkül.

## 6. Ami nem része

A G5 számai nem változnak. Ha a fej így is tart, az nem igazolja a G5 állítását. Ha elbukik, az csak ezekre a fejekre és erre a tanítómintára vonatkozik: az illesztett tanítóminta külön kérdés.

## 7. Idő

Kb. 1 óra GPU (az alany indítása és kinyerés kb. 20 perc, kiolvasás kb. 30 perc, pontozás és elemzés kb. 10 perc), próbánként +10 perc.
