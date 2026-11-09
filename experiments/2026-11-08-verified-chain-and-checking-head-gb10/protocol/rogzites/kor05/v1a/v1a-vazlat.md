# 05a v1a — rögzítési vázlat (tervezet, Dani jóváhagyására)

**Állapot:** vázlat, 2026-10-29. Nincs rögzítve: a `ROGZITES.json` hiányzik, a pecsét zárva (`pecset05.kapu`). A
HO-rétegek kiolvasásait senki nem látta. **A D1–D5 ajánlásait Dani 2026-10-29-én elfogadta** („D1-D5 ok”); az
önellenőrzés (5. pont) után a döntésfüggő kód készül. A rögzítés a manifesttel válik érvényessé.

**Mit rögzít a v1a:** a 05a kitartott rétegein (HO-termék, HO-routing, HO-új; leíróként a HO-routing-hu és a
T-hu-maradék) a karokat, a kalibrációt, a döntési szabályt, a végpontokat és az ítéletszabályt, a 05-runbook 8.2
szerint. A rögzítés után nyílik a pecsét.

---

## 1. Ami a D_dev, a D_meta és a D_cal alapján eldőlt (nem HO-adat)

| tétel | érték | forrás |
|---|---|---|
| tartalmi fej | 128-as vetítés, 128 GELU, 0,1 dropout; LR 1e-4 mindhárom karon; seed 17/42/73 | `kor05/eredmenyek/F3/fejek/*/fej.json` |
| **K\*** | **H** (a D_dev makro tartalmi NLL-je 0,499; A: 0,503; C: 1,725 — a 3. pont szabálya) | ugyanott |
| megbízhatósági fej | a `megbizhatosag05.py` felépítése; LR: C 3e-4, H 1e-4, A 1e-4 (a belső val-BCE szerint) | `F3/megbizhatosag/*/rel.json` |
| kalibráció | a címkekarokon temperature (B0/B1: T = 1,946), a fejeken Platt, mind a D_cal_prob-on | `F3/kalib/kalib_proba.json` |
| τ | a D_cal_policy-n, alapesetenként egy item (2140 alapeset), CP-alsó ≥ 0,95, ≥ 200 elfogadott döntés | ugyanott |

**A megbízhatósági fej részletei** (a runbook nem írta elő, a v1a rögzíti):
- Csak a SELECT- és NONE-javaslatokon tanul; a MISSING_DATA- és OUT_OF_SCOPE-javaslat DEFER, nem kap pontszámot.
- Bemenet: a javaslat típusa, a tartalmi kimenet 11 összegzője, a javasolt jelölt jellemzői (NONE-nál az X-soré),
  karonként a megengedett jellemzőkkel.
- A korai megállás a D_meta belső, 20%-os validációs részén történik. A rész alapesetenként hash-elve készül, seed:
  `k05-meta-val:20261029`.
- A belső validáció AUROC-ja: C ~0,81, H ~0,86, A ~0,86.

**A D_cal_policy munkapontjai (pontbecslés, a végleges `kor05/eredmenyek/F3/kalib/kalib.json`):**

| kar | temperature | lefedettség (S+N) a munkaponton, (pontosság) |
|---|---|---|
| B0, B1 (HF) | 1,946 | **nincs igazolt munkapont** |
| L1v (a 03 vLLM-es L1★-ja) | 1,935 | **nincs igazolt munkapont** |
| G3 s1 / s2 / s3 (a 03 F4-kiolvasásai) | seedenként | 0,147 (0,971) / 0,182 (0,969) / nincs |
| JEV-a / JEV-b | 1,446 / 1,489 | 0,172 (0,970) / 0,200 (0,970) |
| C s17 / s42 / s73 | Platt | nincs / nincs / nincs |
| H s17 / s42 / s73 | Platt | 0,423 (0,962) / 0,426 (0,963) / 0,346 (0,964) |
| A s17 / s42 / s73 | Platt | 0,395 (0,963) / 0,373 (0,964) / 0,352 (0,964) |
| HX s17 / s42 / s73 (K\*-X) | Platt | 0,436 (0,963) / 0,436 (0,962) / 0,404 (0,963) |

A B1 200 legmagabiztosabb döntése közül 8 hibás. A CP-alsó ≥ 0,95-höz 200 elfogadott döntésnél legfeljebb 4 hiba
férne bele.

---

## 2. Döntések a rögzítés előtt

### D1. A 05a elsődleges végpontja — **elfogadva: az AURC (S+N) az elsődleges a 05a szűrőjében**

**A probléma.** A próbaelemzés a D_dev-en (`F3/proba_ddev`, 2000 replika) azt mutatja, hogy a 8.2 elsődleges
végpontja (Δ SELECT-lef@95) ezzel a τ-szabállyal bimodális. A H és a B0 is a CP-határ közvetlen közelében áll:

- a H a replikák egy részében munkapont nélkül marad, ott a lefedettsége 0;
- a B0, amelynek a pontbecslés szerint nincs munkapontja, a replikák több mint felében mégis kap egyet;
- a Δ H − B0 lefedettség CI-je így [−0,08; +0,55], p = 0,27, pedig a különbség a görbéken jól látszik.

Az AURC (SELECT + NONE) ugyanezen a mintán éles:

| kontraszt | ΔAURC (S+N), v1a-definíció | 95% CI | p | (03-konvenció) |
|---|---|---|---|---|
| H − B0 | −0,024 | [−0,041; −0,008] | 0,002 | −0,030 |
| H − C | −0,010 | [−0,022; −0,001] | 0,023 | −0,016 |
| A − H | −0,002 | [−0,008; +0,005] | 0,56 | −0,002 |

**Az AURC definíciója (v1a):** a risk–coverage görbe alatti terület a réteg minden pontozott itemjén; a SELECT- és
NONE-döntések a kalibrált q szerint csökkenő sorban, a nem döntött (DEFER) itemek a rangsor végén, hibaként. Így a
tartózkodás nem javítja a területet: a csupa-DEFER kar AURC-ja 1,0. (A 03 `mer()` konvenciójával, ahol a nem döntött
item kimarad, egy csupa-DEFER kar 0,0-t kapna; ez leíróként marad, `aurc_sn_03`.) A DEFER hányadát külön közöljük.

A B1-nek a D_cal_policy-n nincs munkapontja. Így az S3 (K\* − B1) lefedettségi kontrasztja a HO-n gyakorlatilag
annyit mér, hogy a K\* τ-ja átvisz-e. A különbséget a B1-hez képest nem méri.

**Lehetőségek:**
- **(a) Marad a 8.2.** Várható ítélet: „nem eldönthető” vagy „nem lép tovább” a τ-zaj miatt, a görbék minőségétől
  függetlenül.
- **(b) — ajánlott, elfogadva.** Az S3 és az S5 továbblép, ha a három HO-rétegből legalább kettőn:
  - a ΔAURC (S+N) negatív, és a CI-je nem tartalmazza a 0-t;
  - a K\* precizitásának pontbecslése a saját τ-jánál ≥ 0,93, ha van munkapontja;
  - az MTX nem szignifikánsan nagyobb.

  A Δ SELECT-lef@95 és a lef@p95 leíró. Ez a 8.4 05b-javaslatának (AURC társ-elsődleges) előrehozása.
- **(c) τ-szabály-csere a 05a-ra** (pl. a 200-as minimum elhagyása, vagy pontbecslés ≥ 0,95). A hibahatárt lazítja;
  nem ajánlom, mert a 05b-ben úgyis a szigorú szabály kell.

### D2. Mikor helyes a NONE — **elfogadva: szigorúan (csak a NO_MATCH-en)**

- **Szigorú:** a NONE csak gold `NO_MATCH`-en helyes. A `MISSING_DATA` és az `OUT_OF_SCOPE` végrehajtható eredménye
  más (forrásterv 3.1: adatbekérés, illetve továbbítás).
- **Enyhe (leíró):** a NONE minden nem-`MATCH` állapoton helyes; ez a régi L1★ X-értelmezése.
- A D_cal_policy-n a kettő azonos τ-t ad. A HO-routingon viszont 2183 OUT_OF_SCOPE item van, ott a B1 X-e a szigorú
  változatban hibás döntés. Ez a 05 tézisének a lényege, de a B1-et a 03-hoz képest szigorúbban méri. Mindkét
  változatot közöljük; az ítélet a szigorún áll.

### D3. A T-meta felépítése — **elfogadva: finomhangolás a D_meta-fejből, 5-szörös csoportos cross-fittinggel**

- A célcsalád-minta 500 alapesete (~1000 item) egy 950 ezer paraméteres fejhez kevés a nulláról tanításhoz. A D_meta-n
  tanult megbízhatósági fejet finomhangoljuk.
- Foldonként az 5-ből 4 fold tanít, az ötödik kapja a cross-fittelt pontszámot. A τ ezeken választódik, a 7. pont
  szabályával.
- A teszten az 5 fold-modell logitjainak átlaga adja a pontszámot. A tanítási beállítások azonosak a D_meta-fejéivel,
  a LR a D_meta-n választott.
- **Kész:** `megbizhatosag05.py tmeta`; csereszeleteken (D_cal_prob → D_cal_policy) végigpróbálva: öt fold, foldonként
  tanító, belső validációs és kihagyott rész, a korai megállás a 4–5. epochnál.

### D4. A K\*-X abláció (S4, H4) — **elfogadva: a H tartalmi feje egyetlen X-állapottal, minden más azonos**

Kész: `fej05.py --kar HX` (a megbízhatósági fej és a kalibráció is), a HX X-e NONE-javaslat. A D_dev makro NLL-je a
HX-nél nem vethető össze a H-éval (két kimeneti osztály a négy helyett).

### D5. A JEV kalibrációja — **elfogadva: mint a B1-é (temperature a D_cal_prob-on, τ a D_cal_policy-n)**

- A 04 3.1 a val-on kalibrált volna. A 05-ben minden kar a D_cal-on kalibrál, így a JEV − L1★ összevetés azonos
  eljárású.
- A H6 ítéletszabálya a 04 5.1-é, a HO-rétegek maradékán (8.3). **Feloldás (a D1 elfogadása után, az
  önellenőrzésben):** a H6 is a D1 (b) végpontját kapja, hogy a JEV-a − B1 és a K\* − B1 ugyanazzal a mércével
  mérjen: ΔAURC (S+N) elsődleges, a Δlef@95 leíró; a 04 ítéletkategóriái („JEV jobb” / „nem teljesíti” / „JEV
  rosszabb” / „nem eldönthető”) maradnak, a feltételek (precizitás ≥ 0,93, MTX, AURC) változatlanok. Ha Dani a 04
  eredeti lef@95-ös végpontját akarja a H6-ra, szóljon a rögzítés előtt.

---

## 3. Statisztika (a 8.1 szerint, a próbán ellenőrizve)

- 10 000 replika, seed 20261029.
- A réteg és a D_cal_policy klaszteres újramintázása, két szinten: család, azon belül alapeset.
- A fejeknél a seed visszatevéssel, karonként.
- A τ minden replikában újra; a temperature és a Platt a pontbecslésből rögzítve (a 03 módszere).
- Páros Δ ugyanazon a rétegmintán, kétoldali p. Holm a három réteg p-értékein (leíró; az ítéletszabály a „legalább
  kettő a háromból”).
- A kétértelmű itemek nem pontozódnak. Ha egy kar egy itemet nem tud kiolvasni (a JEV-b az egyopciós natív itemeket),
  az a karnál DEFER.

---

## 4. Ami a v1a-ban fut (`kor05/eszkozok/k05a_elemzes_lanc.sh`)

**Előfeltétel:** a `befagyaszt05.py ellenoriz` átmegy: a `ROGZITES.json`, a `MANIFEST.sha256` és a két pecsétmanifest
egyezik.

**Rétegek:**
- **szűrőrétegek:** HO-termék, HO-routing, HO-új;
- **leíró:** a HO-routing-hu és a T-hu-maradék. Az utóbbi külön fut, JEV nélkül, mert a JEV-et ott nem olvastuk ki.

**Karok (13):**
- **címkekarok:** B0, B1 (HF); L1v, G3 s1–s3 (a 03 vLLM-kiolvasásai); JEV-a, JEV-b;
- **fejek:** C, H (= K\*), A, HX (= K\*-X);
- **célcsalád-karok:** B1-T, H-T-kal, H-T-meta. A τ és a Platt a réteg célcsalád-mintáján (500 alapeset); a
  HO-routing-hu és a T-hu-maradék a HO-routing mintáját kapja.

**Kontrasztok:**

| név | kontraszt | szerep |
|---|---|---|
| S3 | H − B1 | szűrő, ítélet |
| S5 | H-T-meta − B1-T, H-T-kal − B1-T | szűrő, ítélet (külön: „csak T-vel továbblép”) |
| S1 | H − C | leíró |
| S2 | A − H | leíró |
| S4 | H − HX | leíró |
| H6 | JEV-a − L1v, JEV-a − G3 | megerősítő, Holm a 2 × 3-ra; motor-azonos referenciák (mind vLLM) |
| — | JEV-a − B1, JEV-b − L1v | leíró |

**Ítélet (D1 b):** a kontraszt egy rétegen teljesül, ha:
- a ΔAURC (S+N) CI-je 0 alatt van;
- az X kar S+N precizitása a saját τ-jánál ≥ 0,93, ha van munkapontja;
- az MTX nem szignifikánsan nagyobb.

Továbblép, ha ez a három szűrőrétegből legalább kettőn teljesül. Mellette: szigorú helyesség (az ítélet) és enyhe
(leíró), 10 000 replika.

**Két tudott gyengeség, amelyet a rögzítés változatlanul hagy, az eredménylap kiír:**
- **Az MTX-őr gyenge.** Az MTX a τ-nál mérődik, így a τ-zajt örökli: egy replikában munkapont nélkül 0. Ezért ritkán
  bukik. A τ-tól független kiegészítés leíró: az elfogadott SELECT-ek nem-MATCH aránya az AURC-görbe mentén, a
  családonkénti bontásban.
- **Az S5 T-kal változata az AURC-ban azonos az S3-mal.** A Platt monoton, a τ pedig nem hat az AURC-ra. A T-kal saját
  hozzájárulása csak a precizitás- és a munkapont-feltételben jelenik meg; az érdemi T-változat a T-meta.

**A rögzítés lépései (a feloldás előtt, Dani „mehet”-jére):**
1. a runbook 8.2 és 8.3 a D1 és a D5 szerint (kész, a Naplóban);
2. `befagyaszt05.py manifest`: a pillanatképek és a `MANIFEST.sha256`;
3. `befagyaszt05.py rogzit --jovahagyas "Dani, 2026-10-29: …"`: ettől nyílik a pecsét;
4. a `k05a_elemzes_lanc.sh`: a döntési sorok a kitartott szeleteken (GPU, ~10 perc), a T-meta, a három elemzés.

---

## 5. Önellenőrzés (2026-10-29, a döntésfüggő kód előtt)

**Vakság és adat — rendben.**
- A HO-rétegek és a célcsalád-minták kiolvasása a pecsét alatt (root, 700); a `fej05`, a `megbizhatosag05`, a
  `kalib05` és az `elemzes05` betöltője a `ROGZITES.json` nélkül megáll. Semmilyen napló, státuszfájl vagy
  összegzés nem tartalmaz HO-kimenetet, csak darabszámot és időt.
- A célcsalád-minták és a tesztek csoportszinten diszjunktak (0 közös `group_id` mindhárom rétegen).
- Minden eddigi szám (fejek, kalibráció, τ, a próba-elemzés) a D_fit / D_dev / D_meta / D_cal szeleteken készült.
- A 03 v1-ét is így rögzítettük: a kiolvasás pecsételve futott a rögzítés alatt (`kor03/rogzites/v1/ROGZITES.txt`).

**Három javítás a kódban (a rögzítés előtt, HO-adat nélkül):**
1. **AURC:** a 03 konvenciójával a DEFER javította a területet (csupa-DEFER → 0,0). Új definíció fent (D1); a
   D_dev-próbán a H − B0 kontraszt −0,030-ról −0,024-re gyengül, de éles marad (p = 0,002).
2. **Clopper–Pearson-tábla:** a családszintű visszatevés miatt a replika nagyobb lehet az eredeti rétegnél, a fix
   méretű tábla kifutott (IndexError). Igény szerint bővülő tábla.
3. **JEV-b temperature:** az X-gold itemeken a gold nem érhető el, a tag a T-tól független; kimarad az illesztésből.

**Tudott aszimmetria, nem hiba (D2 következménye):** a szigorú helyesség a B1 X-ét az OUT_OF_SCOPE itemeken hibának
veszi; a HO-routingon ez 2183 item a 6659 pontozottból. A K\* ugyanitt DEFER-t adhat, amely a lefedettségbe nem
számít, az AURC-ba a rangsor végén hibaként. Az enyhe helyesség leíró változata ezért kötelező melléklet, és az
eredménylap a HO-routingon a kettőt egymás mellett mutatja.

**Egy módszertani megjegyzés, nyíltan:** a D1 (az AURC társ-elsődlegessé tétele) a D_dev-próba láttán született,
tehát adatfüggő tervváltoztatás; a HO-rétegeket nem érinti, a 8.4 a 05b-re már javasolta, és a rögzítés előtt
történik. A runbook 8.2 és 8.3 szövegét a rögzítéskor ennek megfelelően írjuk át, a pillanatképpel együtt.

**Ami nem készült el, és a rögzítésig kell:** a T-meta, a K\*-X, a célcsalád-mintás kalibráció (B1-T, T-kal), a
`befagyaszt05.py`; a K\*-X tanítása CPU-n fut (a GPU-n a JEV), ~2–3 óra.
