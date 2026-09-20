# F2 jegyzőkönyv — a teljes dózis-sor · 2026-09-19

> Kilenc kar, mind a hat műszeren. A sima motoron, sorosan, ismétlés nélkül (a döntés és
> az okai: [F1-naplo.md](F1-naplo.md) §8–9, runbook Napló 2026-09-19). Az F2 13:00-kor
> indult és 22:12-kor zárult; karonként ~1 óra 20 perc. A §10 eredménylap:
> `eredmenyek/eredmenylap.txt` (+ `.json`).

---

## 1. A kilenc kar egy táblában

> ⛔ **Utólag (2026-09-20, F3 A):** a Han-kockázat oszlopai a NYERS top-20-ra épülő
> becslések. A tényleges tartón mérve a `K0` kockázata ~10× nagyobb (`@ 0,6`: 73/M;
> `@ 1,0` nem mérve újra), a foltok exact nullái pedig állnak (`S07 @ 0,6/0,3`), kivéve az
> újrapróbálkozási utat (`S07 @ 0,9`: 0,45/M). Részletek: [F3-naplo.md](F3-naplo.md).

| kar | forma · S/α · maszk | kínai pontszám | Han **nélküli** válasz | magyar Han-kockázat, prod-út (`pp1,5 t0,6`) | `t=1,0` kontrafaktuális | csapda vs. azonos módú `K0` |
|---|---|---|---|---|---|---|
| `K0` | — | **36/36 = 100 %** | 0/36 | 5,5/M [0; 10,8] | **219,9/M** [48; 289] | — |
| **`S07`** | szorzás · 0,7 · nyers | **36/36 = 100 %** | 0/36 | **exact 0** | **exact 0** | 150/150 azonos |
| `S05` | szorzás · 0,5 · nyers | 1/36 = 2,8 % | 35/36 | exact 0 | exact 0 | 150/150 azonos |
| `S03` | szorzás · 0,3 · nyers | 0/36 | 36/36 | exact 0 | exact 0 | 150/150 azonos |
| `S01` | szorzás · 0,1 · nyers | 0/36 | 36/36 | exact 0 | exact 0 | 150/150 azonos |
| `A200` | irány · 2,0 · nyers | 0/36 | 36/36 | exact 0 | exact 0 | 150/150 azonos |
| `A050` | irány · 0,5 · nyers | 0/36 | 35/36 | exact 0 | exact 0 | *(új példány-mód; ld. §4)* |
| `S05F` | szorzás · 0,5 · **finomított** | 7/36 = 19,4 % | 16/36 | exact 0 | **11,3/M** [0; 22,0] | 150/150 azonos |
| `A200F` | irány · 2,0 · **finomított** | 1/36 = 2,8 % | 31/36 | **4,3/M** [0; 10,2] · `t=0,8`-on **1 valódi Han a válaszban** | 2,6/M [0; 7,3] | 150/150 azonos |

A kínai próba kontroll-ellenes McNemar p < 10⁻⁴ minden folton, Holm után is — kivéve az
`S07`-et, ahol **nincs diszkordáns pár**. A magyar csapda mind a kilenc karon **bájtra**
azonos a saját példány-módjának `K0`-jával (nullműszer, ld. §4).

**Belső, megerősítő műszerek** (ügyféladat, nem publikálható; §7/3):

| kar | KIE F1 | contract F1 / acc |
|---|---|---|
| `K0` | 1,000 | 0,923 / 0,926 |
| `S07` | 1,000 | 0,917 / 0,921 |
| `S05` | 1,000 | 0,919 / 0,923 |
| `S03` | 1,000 | 0,915 / 0,924 |
| `S01` | 0,982 (fp=4, mm=2) | 0,931 / 0,936 |
| `A200` | 1,000 | 0,915 / 0,921 |
| `A050` | 0,986 (fp=2, mm=2) | 0,921 / 0,926 |
| `S05F` | 0,982 (fp=4, mm=2) | 0,931 / 0,936 |
| `A200F` | 1,000 | 0,923 / 0,926 |

⭐ Az `S01` és az `S05F` KIE- és contract-száma **számjegyre azonos** (0,982 / fp=4 / mm=2;
0,931 / 0,936 / fp=9 / fn=57 / wrong=72) — ez a két kar ugyanabba a példány-módba esett
(a csapdán is 150/150 azonosak egymással). A belső műszerek eltérései tehát nem a
folt hatásai, hanem a példányé; a §7/3 „nem mutat romlást" feltétel teljesül abban az
értelemben, hogy az azonos módú karok azonos számot adnak, a módok közti ±0,02 pedig a
példányzaj.

---

## 2. Kapu F2 — azonosítható-e `S*`?

**Igen: `S* = S07`.** Az egyetlen kar, ahol a magyar Han-kockázat a termelési úton *és*
`t=1,0`-n is exact nulla, **és** a kínai próba a kontrollal azonos (36/36, 0 diszkordáns
pár). Minden más folt vagy a kínait öli le (S ≤ 0,5, mindkét irány-dózis), vagy a
kockázatot nem nullázza (finomított maszk), vagy mindkettő (`A200F`).

A dózis-hatás alakja **nem görbe, hanem két lépcső**:

- **haszonoldal (magyar):** a nyers maszk minden dózisa exact nullát ad már S = 0,7-nél
  — a lépcső 0,7 fölött van, és ez a kör nem mérte, hol (S08, S09 nem volt kar);
- **költségoldal (kínai):** S = 0,7-nél ép, S = 0,5-nél halott — a lépcső 0,5 és 0,7 között.

A két lépcső közti ablak létezik, és `S07` benne van. Hogy mennyire széles (S06?
S065?), az F3 kérdése.

---

## 3. A hipotézisek verdiktje (előzetes; F3 után végleges)

| | állítás | verdikt | alap |
|---|---|---|---|
| **H1** | erős dózisnál fizetünk magyarul | **cáfolva minden dózisra** — a magyar greedy kimenet bájtra érintetlen S = 0,1-nél is; a költség *teljes egészében* a kínain jelenik meg | §4 nullműszer-levezetés + 9 kar |
| **H2** | az irány-csere mechanizmusa más, és olcsóbb | mechanizmusa **igazolt** (nyers tömeg exact 0, F0), de **nem olcsóbb**: `A050` is 0/36 kínai | kínai próba |
| **H3** | a finomított maszk megtartja a kínait | **cáfolva**: `S05F` 19,4 %, a válaszok fele Han-mentes; `A200F` 2,8 % | kínai próba |
| **H4** | a finomított maszk is nullázza a kockázatot | **cáfolva**: `S05F` `t=1,0`-n 11,3/M; `A200F` már a prod-úton is 4,3/M és valódi Han a válaszban | Han-szonda |
| **H5** | a kockázat a hőmérséklettel nő | **igazolt a kontrollon** (5,5 → 16,7 → 61–220/M `t=0,6→0,8→1,0`), a foltoknál lépcső | Han-szonda |
| **H6** | a folt hatása a mintavételi profiltól függ | **igazolt**: S-karok nyers Han-tömege *nő* (10,5 → 13,4 → 16,1 %), a nulla a `top_k` csonkolás terméke; `A200F` `t=0,8`-on tényleges Han | előjel-csapda (F0) + szonda |

---

## 4. Ami a mérésről derült ki (a tanulmány „amit elrontottunk" szakaszába)

1. **A magyar csapda nullműszer.** A folt csak Han-sorok logitját változtatja, azok
   magyar szövegen soha nem argmaxok → greedy kimenet bitre azonos; mintavételnél csak a
   csonkolt tartóban lévő Han-nál térhet el → *a nem-célnyelvi költség felülről korlátos a
   nem-célnyelvi kockázattal.* Ezt mind a nyolc folt bájtra igazolta. A csapda így
   **negatív kontroll** lett: azt bizonyítja, hogy a mérés nem lát fantomhatást.
2. **A példány-módok.** A kiszolgáló-példány indításkor egy diszkrét numerika-módba
   esik; a késélen ülő itemek (`T3-02`, `T3-03`, `T3-05`, `T7-08`, `C9-09`, `C4-10`,
   `C9-02`, `T4-04`) módonként más oldalra billennek. 13 példányból **legalább 4 mód**;
   az azonos módú példányok **bájtra** reprodukálják egymást (`S01` ≡ `S05F` ≡ `K0`-inst2;
   `S07` ≡ `S03` ≡ `S05` ≡ `A200` ≡ `A200F` ≡ `K0`-inst1; `A050` egy negyedik). A
   nullműszer-tulajdonság miatt minden kar csapdája azonosítja a saját módját, és a kart a
   *vele azonos módú* `K0`-hoz lehet hasonlítani. A `VLLM_BATCH_INVARIANT=1` +
   `TRITON_ATTN` út példányok és kötegméretek között is reprodukálható (mért), de
   motorváltás — a döntés szerint a kör a sima motoron maradt.
3. **A Han-szonda az S-karokon ugyanazt a trajektóriát adja.** `S07` ≡ `S03` (27/27),
   `S05F` ≡ `S01` (27/27) — azonos mód + `seed=0` + sehol Han a top-20-ban = azonos
   mintavételezett út. Az „exact nulla" igaz, de az S-karok közti különbség a
   haszonoldalon ezen a műszeren definíció szerint nem létezik.
4. **Az F1 3× → F2 3× helyett 5×.** A Han-szonda az F2 karjain 3× futott (F1-en 5×), így
   a pozíciószám karonként 3–10 ezer. Az exact nulla nem függ ettől; a Poisson-korlát
   igen (500–1 100/M). Az `S*` megerősítése F3-ban 5×.

---

## 5. Amit az F3-nak kell

- **`S07` megerősítése** 5× Han-szondával, **több példányon** (legalább 3 mód), és `t=0,6`-os
  csapda-futással (a költség a termelési mintavételi profilon, nem greedy-n).
- **Az ablak szélessége:** `S06` (és ha él, `S065`) — hol a kínai lépcső pontosan.
- **A haszon-lépcső helye:** `S08`, `S09` — hol szűnik meg az exact nulla. (Ha S09 is
  nulla, a folt még enyhébb is lehet.)
- `A200` gondolkodásbeli Han-tokenjei: melyik tokenek, a nyers maszkban vannak-e.
