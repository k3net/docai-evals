# F3 jegyzőkönyv — a mérés igazolása és az `S07` megerősítése · 2026-09-20

> Az F3 A) és B) fázisa 2026-09-19 22:35 és 2026-09-20 07:46 között futott; a C) (S08,
> S09, S06) még megy. A fázisok tartalma és a döntési szabály **az adat előtt** a runbook
> Naplójában (2026-09-19). Nyers kimenetek: `eredmenyek/f3/`.

---

## 1. A) A kockázatmérés igazolása a TÉNYLEGES tartón

A kiszolgáló `--logprobs-mode processed_logprobs` módban: a rögzített top-20 a
büntetések + hőmérséklet + `top_k` + `top_p` *utáni* eloszlás. `han_kockazat.py
--feldolgozott`: E[Han] = Σ exp(lp), lánc nélkül. Válasz-szegmens, /M, válaszonkénti
bootstrap CI; „megfigyelt" = ténylegesen generált Han-token a válaszban.

| profil | `K0` E[Han] (tényleges tartó) | `K0` megfigyelt | `S07` E[Han] | `S07` megfigyelt |
|---|---|---|---|---|
| alap `t=0,6` (a cél) | **73,4/M** [14,9; 148,1] | 0 / 7 325 | **exact 0** [0; 0] | 0 / 8 983 |
| alap `t=0,3` (a mai éles) | **392,4/M** [0; 870,9] | **4 / 7 869** | **exact 0** [0; 0] | 0 / 7 678 |
| újrapróbálkozás `t=0,9 / top_p 1 / pp 1,8` | **306,1/M** [103,3; 600,3] | **3 / 6 650** | **0,45/M** [0,04; 1,17] | 0 / 7 136 |
| csapda 150 irat, prod-profil (nem ügyféladat) | exact 0 (válasz 9 338 poz.) · gondolkodás: 2 Han / 223 476 | 0 | **exact 0** (válasz 8 674) · gondolkodás: **0 / 213 361** | 0 |

### ⛔ Két korrekció, amit ez a mérés kikényszerít

**1. A nyers-top-20-as módszer a kontroll kockázatát ~10-szeresen alulbecsülte.**
`K0 @ 0,6`: az F1 kontrafaktuális becslése 5,5/M volt, a tényleges tartón **73,4/M**. Az
ok pontosan az, amit a felhasználó mondott: a `presence_penalty=1,5` a már látott tokeneket
a top-k *előtt* nyomja le, és a nyersen 21+. helyezett Han-tokenek bejutnak a tartóba. Az
F1/F2 eredménylap `K0`-számai tehát **alsó korlátok**; a foltok exact nullái viszont a
tényleges tartón is állnak (`S07 @ 0,6` és `@ 0,3`), egy kivétellel (lent).

**2. A `t=0,3`-as tűzoltás nem szünteti meg a kockázatot.** A mai éles állapot (`K0 @
0,3`) a tényleges tartón **392/M**, és 7 869 válaszpozíción **4 valódi Han-token** —
több, mint `0,6`-on. Mechanizmus: a vLLM a büntetéseket a logitokra teszi, *mielőtt* a
hőmérséklettel oszt (`sampler.forward` → `apply_penalties`, majd `sample` →
`apply_temperature` → top-k/p), tehát alacsony hőmérsékleten a büntetés **erősebben**
hat (1,5/0,3 = 5 a skálázott térben), és több helyet nyit a top-20-ban. ⚠️ n kicsi (3
eset × 5 seed), a CI a nullát is tartalmazza — de a 4 megfigyelt esemény valódi.

**Az egy kivétel:** `S07` az újrapróbálkozási úton (`t=0,9`, `pp=1,8`) **nem exact
nulla**: 0,45/M [0,04; 1,17], megfigyelt esemény nincs. Ez ≈ egy Han-token 2,2 millió
újrapróbálkozási pozíciónként, és az újrapróbálkozás maga ritka (legfeljebb 1×, csak
hurok-gyanú esetén). A döntési szabály szó szerinti feltétele („nem nagyobb, mint `K0 @
0,3`") így is bőven teljesül; a gyakorlati megfogalmazás („exact nulla") a `0,9`-es úton
nem.

---

## 2. B) `S07`–`K0` megerősítés a sima (prod-azonos) motoron

Három friss `S07`-példány és egy friss `K0`-példány; 3 profil × 5 seed, egy 3-szálas
párhuzamos köteg, és a csapda a prod-profilon (`parallel=6`, 3×). A kockázatszámítás itt a
korábbi (nyers) módszerrel — az összevethetőség kedvéért —, de a lényeg a **megfigyelt**
esemény:

| | `K0-p1` | `S07-p1` | `S07-p2` | `S07-p3` |
|---|---|---|---|---|
| `t=0,6` — Han a gondolkodásban / válaszban | **63 / 2** (12 992 poz.) | 0 / 0 | 0 / 0 | 0 / 0 |
| `t=0,3` | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| `t=0,9` újrapróbálkozás — *végső válasszal záruló* rekordok | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| `t=0,9` — **minden** rekord (⛔ javítás, §6) | **6 593 Han** egy elszabadult, 35 952 tokenes generálásban | 0 (de ugyanott 65 536 tokenes elszabadulás, Han nélkül) | 0 (ua.) | 0 (ua.) |
| `t=0,6`, 3-szálas köteg | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| csapda 150 irat, prod-profil: gondolkodás / válasz | **7 / 0** (250 663 poz.) | **0 / 0** (248 996 poz.) | — | — |

⭐ **Az `S07` három példányon, 15 seeden, három profilon, párhuzamos köteg alatt és a 150
irat ~249 000 pozícióján egyetlen Han-tokent sem generált** — sem a gondolkodásban, sem a
válaszban. A `K0` ugyanezeken a seedeken `0,6`-on 65-öt.

**Trajektória-azonosság (a mechanizmus bizonyítéka, ismét):** `K0-p1` és `S07-p1`
mintavételezett útja `t=0,3`-on **15/15** azonos, `t=0,6`-on és `0,9`-en **13/15** — a két
eltérő éppen az, ahol a `K0` Han-tokent húzott. A folt tehát *pontosan* a billenési
pontokon hat, máshol a modell viselkedése változatlan.

⚠️ **Korlát:** a három `S07`-példány trajektóriája egymással **15/15 azonos** — mindhárom
ugyanabba a numerika-módba esett, tehát a példányok közti függetlenség itt kisebb, mint
terveztük (viszont három független indítás ugyanabba a módba: a gyakori mód tényleg
gyakori).

### A csapda a prod-profilon (költség mintavételezés alatt)

| kar | pass | pont | régi 50 | formátumsértés |
|---|---|---|---|---|
| `K0-fd` (feldolgozott példány) | 146/150 | 191,00 | 47/50 | 2 |
| `S07-fd` | 146/150 | **194,50** | **50/50** | 0 |
| `K0-p1` (sima példány) | 144/150 | 184,00 | 47/50 | 1 |
| `S07-p1` | 146/150 | **195,00** | **50/50** | 0 |

Párosítva a `K0-fd` ellen: `S07` Δ = 0,00 pp [−3,2; +3,2] (b=3, c=3), tehát „felbontás
alatt" — de a pontszámon és a régi 50-en az `S07` **jobb**, és formátumsértése nincs.
Mintavételezés alatt a `K0` gondolkodásbeli Han-kisiklásai láthatóan a válaszminőségbe is
belekerülnek; a folt ezt is elviszi.

---

## 3. A döntési szabály kiértékelése (runbook Napló, 2026-09-19, az adat előtt)

| feltétel | mért | |
|---|---|---|
| (1) E[Han] `S07 @ 0,6` ≤ `K0 @ 0,3` a tényleges tartón | exact 0 ≤ 392/M; `@ 0,9`: 0,45/M ≤ 306/M | ✅ (a `0,9`-es út nem exact nulla — kimondva) |
| (2) csapda prod-profilon `S07 @ 0,6` nem rosszabb `K0 @ 0,6`-nál | 146/150 vs 146/150 (Δ 0), pont 194,5 vs 191,0 | ✅ |
| (3) három friss `S07`-példány, 0 valódi Han a válaszban | 0 Han bárhol, ~300 000 pozíción | ✅ (korlát: azonos numerika-mód) |

**Az `S07` a prod-próbára javasolható** — szigorúbb bizonyítékkal, mint amit a runbook
kért, és egy őszinte kivétellel (az újrapróbálkozási út 0,45/M-je). A prod-próba maga a
felhasználó döntése.

---

## 4. C) Az ablak két széle: `S09`, `S08`, `S06` · kész 13:02

Sima motor, F2-protokoll, Han-szonda 5× (nyers-top-20-as módszer — tehát a `K0`-hoz
hasonlóan **alsó korlát**; a `t=0,6`/`0,8`/`1,0` oszlop a tényleges futás beállítása).

| kar | kínai | Han nélküli | Han `t=0,6` | `t=0,8` | `t=1,0` | csapda | példány-mód |
|---|---|---|---|---|---|---|---|
| `S09` | **36/36** | 0 | exact 0 | **16,9/M** [2,1; 37,9] | 3,3/M [0; 8,7] | 145/150 (≡ `K0` bájtra) | inst1 |
| `S08` | **36/36** | 0 | exact 0 | exact 0 | **1,6/M** [0; 4,8] | 143/150 | *új mód (5.)* |
| `S07` | **36/36** | 0 | exact 0 | exact 0 | exact 0 | 145/150 (≡ `K0`) | inst1 |
| `S06` | **20/36 = 55,6 %** | 16/36 | exact 0 | exact 0 | exact 0 | 143/150 | ugyanaz, mint `S08` |
| `S05` | 1/36 | 35/36 | exact 0 | exact 0 | exact 0 | 145/150 | inst1 |

Megfigyelt Han-esemény egyik új karon sincs (0 / ~7 600–9 800 válaszpozíció karonként).

**A két lépcső helye — most már mindkét oldalról bemérve:**

- **Haszon-lépcső (magyar):** az exact nulla a prod-úton (`t=0,6` és `0,8`) **S = 0,8-ig**
  tart; `S09` már `0,8`-on szivárog (16,9/M), `S08` csak `t=1,0`-n (1,6/M). Ez a nyers
  módszer alsó korlátja — a tényleges tartón (F3 A) az `S07` is 0,45/M-et mutatott az
  újrapróbálkozási úton, tehát az `S08` ott várhatóan több.
- **Költség-lépcső (kínai):** **S = 0,7-ig ép** (36/36), `0,6`-on már **55,6 %** és a válaszok
  44 %-a Han-mentes, `0,5`-en 2,8 %. A szakadék tehát 0,7 és 0,6 között van, nem
  0,7 és 0,5 között — az `S07` **közvetlenül a szakadék szélén** ül, tartalék nélkül lefelé.

**Válasz a felhasználó három kérdésére:**

| kar | kérdés | válasz |
|---|---|---|
| `S08` | elég-e kisebb beavatkozás ugyanahhoz a csillapításhoz? | a prod-úton (`0,6`, `0,8`) **igen**, `t=1,0`-n már nem exact nulla; a tényleges tartón nem mértük — ha jelölt lenne, egy `processed_logprobs` menet (~1 óra) kell hozzá |
| `S09` | még közelebb maradhatunk-e az eredeti modellhez? | **nem**: `t=0,8`-on 16,9/M, tehát a prod-úton is szivárog |
| `S06` | hol kezd összeomlani a kínai; mekkora a tartalék S07 alatt? | **0,6-nál már omlik** (55,6 %); az S07 alatt **nincs** tartalék |

**Következtetés:** `S* = S07` marad — a legkisebb dózis, amely a nyers módszerrel minden
hőmérsékleten exact nulla ÉS a kínait érintetlenül hagyja; az `S08` a haszonoldalon
majdnem egyenértékű (prod-úton exact nulla), de a tényleges tartón nincs igazolva, és a
kínai oldalon nem ad többet (mindkettő 36/36). A választás tehát nem költség/haszon,
hanem **biztonsági tartalék**: az `S07` a haszon-lépcsőtől egy lépéssel beljebb van, a
költség-lépcső szélén; az `S08` fordítva.

⚠️ **Példány-mód, ötödször:** az `S08` és az `S06` példánya egy eddig nem látott módba
esett (6 item billen a `K0`-hoz képest, köztük két új: `T2-02`, `T7-09`), és a két kar
csapdája egymással azonos mintázatú; a belső KIE mindkettőn 0,970 (a `K0` 1,000) —
ugyanaz a mód, nem a folt. 16 példányból 5 mód.

---

## 5. A dózis-hatás végső képe (12 kar)

```
S:      0,9     0,8     0,7  |  0,6     0,5     0,3     0,1
kínai:  100 %   100 %   100 % |  55,6 %  2,8 %   0 %     0 %       ← költség-lépcső 0,7/0,6
Han:    szivárog ~0*    0     |  0       0       0       0         ← haszon-lépcső 0,9/0,8
```
`*` = exact nulla a prod-úton, 1,6/M `t=1,0`-n (nyers módszer). Az irány-forma (`A050`,
`A200`) és a finomított maszk (`S05F`, `A200F`) a táblán kívül: mind rosszabb mindkét
tengelyen. A teljes eredménylap: `eredmenyek/eredmenylap.txt`.

---

## 6. ⛔ Önellenőrzés a lezárás után · 2026-09-20

Független újraszámolás a nyers rekordokból (`eszkozok/han_ujraszamol_mind.py`, kimenet:
`eredmenyek/f3/ujraszamolas-minden-rekord.txt`), a csapda és a kínai próba pass-számainak,
bájt-azonossági csoportjainak és McNemar-értékeinek újraszámolásával együtt. **A táblák
számai egyeznek**; a következtetés (`S* = S07`, a prod-próba javasolható) áll. Négy dolgot
viszont a mérőeszköz eltakart vagy a szöveg túlállított:

**1. A `han_kockazat.py` kihagyja a végső válasz nélküli rekordokat — gondolkodásostul.**
A szondarekordok ~fele eszközhívással zárul (`finish_reason = tool_calls`), ezek és az
elszabadult generálások nem kerültek sem az E[Han]-ba, sem a „megfigyelt" számlálóba. Minden
rekordot számolva:
- **`S07`: továbbra is 0 generált Han-token, mindenhol** — 4 példány, ~1,09 M *különböző*
  pozíció (a p2/p3 soros útja a p1-gyel azonos, azt egyszer számolva). Poisson 95 % felső
  korlát a teljes megfigyelt folyamra: **< 2,8/M**. Ez erősebb állítás, mint a korábbi ~300 000.
- **`K0-p1`, újrapróbálkozási profil, seed 5: egy rekord 6 593 Han-tokent generált** egy
  35 952 tokenes, végső válasz nélküli szósalátában. A §2 tábla „0 / 0"-ja tehát csak a
  végső válasszal záruló rekordokra igaz. A `K0` „65 Han"-ja így **65 + 6 593**.
- `S09 @ t=1,0`: 2 generált Han egy eszközhívásos körben (az eredménylap 0-t mutat) — az
  `S09` szivárgását erősíti. `A200`/`A200F`: a gondolkodásbeli Han-tokenek (1–7 / futás)
  ismertek voltak (F2 §5), a kihagyott rekordokban is van belőlük.

**2. Az újrapróbálkozási profil a folttól függetlenül elszabadulhat.** Ugyanazon a seeden
(5) a `K0-p1` két esete 35–36 ezer tokenes szósalátába futott; az `S07-p1/p2/p3` ugyanott
**szintén** (egyszer a 65 536-os plafonig, `finish_reason = length`) — Han nélkül. A folt a
Han-t veszi el, **a degenerációt nem**. A feldolgozott-logprobos példányokon (`-fd`)
ugyanezek a seedek nem szabadultak el (más numerika-mód). `S05 @ t=1,0`-n is volt egy ilyen.
Ez a `t=0,9 / top_p=1,0` profil tulajdonsága, és a prod-döntéshez önálló adat: 15 futásból 2.

**3. A `0,45/M` (`S07 @ 0,9`) alsó korlát.** `top_p = 1,0` mellett az FP8-logitok
holtversenyei a top-k határán bent maradnak (a vLLM minden, a k-adikkal egyenlő értéket
megtart), így a pozíciók ~4 %-án a tényleges tartó 20-nál nagyobb, és a rögzített top-20
összege < 1 (legrosszabb pozíció: 0,952). A `0,6`-os és `0,3`-as profilon (`top_p = 0,95`)
a normálási hiba ~10⁻⁷ — ott a tartó teljes, az exact nulla valóban exact.

**4. A „~10×" pontbecslések hányadosa, nem mért szorzó.** `K0 @ 0,6`: nyers módszer 5,5/M
[0; 10,8] (F1) és 12,0/M [0; 29,4] (F3 `K0-p1`), tényleges tartó 73,4/M [14,9; 148,1] —
három ügyfél-eset, különböző példányok, széles CI-k. Helyesen: „nagyságrendileg
alulbecsült (pontbecslésben 6–13×)". A mechanizmus (büntetés a top-k előtt) ettől
függetlenül strukturális, és a `K0-p1` megfigyelt 2 Han / 7 159 válaszpozíciója (279/M) is
a nyers becslés fölött van. A publikus 150 iraton a `K0` kockázata kicsi (válasz: exact 0;
gondolkodás: 2–7 Han / ~230 000) — a nagy `K0`-számok a három ügynök-esetből jönnek.

**Két módszertani megjegyzés, ami a szövegekben pontosítandó volt:**
- *Nullműszer:* a bájt-azonosság a `K0`-val **8 karon igazolt** (6 az inst1-módban, `S01` és
  `S05F` a `K0-ujpeldany` módjában). Az `S08`/`S06` és az `A050` módjában nincs `K0`-mérés:
  ott a tulajdonság levezetett, nem mért (az `S08` ≡ `S06` egymással bájtra azonos).
- *A §7/1 szabály (Σp bootstrap felső korlát < 1/M)* nullánál degenerált: ha minden
  válaszban Σp = 0, a bootstrap [0; 0], a mintanagyságtól függetlenül. Az „exact nulla"
  ezért **strukturális** állítás a bejárt pozíciókra (nincs Han a tartóban), a statisztikai
  korlátot a megfigyelt folyam Poisson-korlátja adja (fent: < 2,8/M). A 12 karos tábla
  Han-oszlopai 3 ügyfél-esetből, 3–5 seedeletlen ismétlésből állnak, és az azonos módú karok
  **ugyanazt a mintavételezett utat** járják (a kiszolgáló RNG-je azonos sorrendben fogy) —
  az S-karok nullái nem független minták.
