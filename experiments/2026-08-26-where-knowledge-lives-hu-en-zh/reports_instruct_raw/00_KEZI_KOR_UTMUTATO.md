# Ellenőrző kör — 3. kör — KONTROLL — **Qwen3.5-9B · nyers folytatásos prompt**

> ⚠️ **Terminológia (2026-08-26):** ahol ez a dokumentum „ellenőrző kör”-t vagy „ellenőrző bírálatt” ír, az a
> **GPT-5.6 Sol ellenőrző bírálata** (tételenként, a teljes válasszal és a rubrikával, a Qwen3.6-35B
> gépi bíráló ítélete mellé); emberi vak értékelés nem történt. A dolgozat ezt végig „ellenőrző kör”
> néven hozza.

> Generált fájl (`src/kezi_kor_utmutato.py`) — a benne lévő számok az aktuális
> `results_instruct_raw/` tartalmából jönnek. Ha újrafutott a bírálat, generáld újra.

## ⛔⛔ A LEGFONTOSABB szabály ebben a körben: azonos mérce

Ez a **kontroll-kör**. Ugyanaz a modell fut benne, mint a 2. körben (`Qwen3.5-9B` instruct), de a **base kör nyers, folytatásos promptjával** — chat-sablon nélkül. A cél egyetlen kérdés megválaszolása:

> A 2. körben mért javulás a **modellsúlyoktól** jön, vagy attól, hogy chat-sablonnal promptoztuk?

A gépi bíráló ítéletein már lefutott a felbontás, és azt adta, hogy **a javulást szinte teljes egészében a promptozás magyarázza** (a puszta súlycsere nettó +1 item, p = 1,000; a chat-sablonra váltás +10, p = 0,041). Ez a ellenőrző kör azt hivatott eldönteni, hogy **ez a következtetés a gépi bíráló műterméke-e** — különösen a `hallucinacio` kategóriában, amit a bíráló alig használ.

Ebből következik, hogy amit mérünk, **csak akkor a vizsgált hatás, ha a te mércéd változatlan.** Ha itt szigorúbb vagy, mint a korábbi körökben voltál, ez a kör rosszabbnak fog látszani, mint amilyen; ha elnézőbb, jobbnak. **Ez a kör legnagyobb kockázata, nem a rubrika.**

**Ezért mielőtt belekezdesz, olvasd át a saját korábbi döntéseidet:** `reports/kezi_validacio_naplo.md` · `reports_instruct/kezi_validacio_naplo.md` — különösen a *„Különösen fontos ellenőrző döntések”* és a *„D1 értelmezési elv”* szakaszt. Azok a precedenseid.

⚠️ **Amit ebben a körben NE csinálj:** ne igazítsd az ítéletet ahhoz, amit a 2. körben ugyanarra az itemre adtál. A két kör válaszszövege MÁS; itt is csak azt kell megítélned, ami a lapon van. Ha ugyanaz a tartalom, természetes, hogy ugyanaz az ítélet — de ez következmény legyen, ne cél.

## Hol tartok?

```bash
cd <experiment-dir>
SCOPE_RES=results_instruct_raw SCOPE_REPORTS=reports_instruct_raw python3 src/set_manual.py status
```

Jelenleg: **Mérés A 0/102** kötelező válasz · **D1 UNT 0/48**.

✅ A ellenőrző oszlopok túlélik a `judge.py` újrafuttatását — `(item_id, nyelv)` kulcson
átmentődnek. Nyugodtan félbehagyhatod.

---

## Fájltérkép

| Fájl | Szerep |
|---|---|
| `reports_instruct_raw/02_kezi_ellenorzes.md` | **Mérés A olvasnivalója** — 102 válasz kérdéssel, várt válasszal, a modell válaszával, a bíráló indoklásával |
| `reports_instruct_raw/05_kezi_ellenorzes_d1.md` | **D1 olvasnivalója** — 48 UNT-válasz komponensenkénti pipákkal |
| `results_instruct_raw/scores.csv` → `manual` | Mérés A beírnivalója (a `set_manual.py`-n keresztül) |
| `results_instruct_raw/d1_scores.csv` → `manual_native` / `manual_distortion` | D1 beírnivalója |
| `reports_instruct_raw/02_meres_a.md`, `reports_instruct_raw/05_meres_d.md` | a **kimenet**, amit utána újragenerálsz |

⛔ **A CSV-t soha ne szerkeszd kézzel.** A `answer` oszlop idézőjeleket, vesszőket és
sortöréseket tartalmaz; a 08-24-i kör pontosan így veszett el (6 törött sor + 46 sorban
kicserélt válaszszöveg). A `set_manual.py` validál: ismeretlen itemre, rossz nyelvre,
érvénytelen ítéletre és a nevezőt túllépő darabszámra hibát dob.

---

## Ennek a körnek a terepviszonyai

Amivel ebben a körben találkozni fogsz (a `gen.jsonl`-ből számolva):

| jelenség | magyar | angol | kínai | összesen |
|---|---|---|---|---|
| a token-keretbe ütközött (csonkolt) | 26 | 9 | 29 | **64/258** |
| ismétlési hurokba esett (degenerált) | 9 | 2 | 18 | **29/258** |

Összevetés a korábbi körökkel — ez segít ráhangolódni, mi lesz MÁS:

| | 1. kör | 2. kör | 3. kör — KONTROLL (ez) |
|---|---|---|---|
| csonkolt | 43/258 (hu 30, en 4, zh 9) | 86/258 (hu 47, en 17, zh 22) | 64/258 (hu 26, en 9, zh 29) |
| ismétlési hurok | 25/258 (hu 14, en 2, zh 9) | 13/258 (hu 0, en 1, zh 12) | 29/258 (hu 9, en 2, zh 18) |
| önértékelő toldalék levágva | 16/258 | 0/258 | 23/258 |

⚠️ **Lényegesen több a csonkolt válasz**, mint az 1. körben (64 vs. 43): a modell bőbeszédűbb. A keret minden körben ugyanaz (fact 200, UNT/kontroll 800 token), tehát ez nem mérési hiba — de **sok választ félbevágva fogsz látni**.
⛔ **Az önértékelő toldalék VISSZATÉRT** (16 → 23): a modell a válasz után gyakran saját feladatkiírást ír (*请判断回答是否正确…*, *A single-select problem…*). A `clean_answers.py` levágja, és az ív a levágott (`text_clean`) szöveget mutatja — **azt ítéld meg**, ne a nyerset. Ahol a vágás történt, az ív külön jelzi.
⛔ **Az ismétlési hurok is visszatért** (összesen 25 → 29; a legtöbb a kínai válaszoknál: 9 → 18). A beragadás dekódolási jelenség: a hurok ELŐTTI tartalom alapján ítélj, a hurkot magát ne rójuk fel.

---

# Mérés A — 102 válasz (kötelező)

## A négy ítélet

| ítélet | mikor |
|---|---|
| `helyes` | a válasz konkrétan megnevezi a várt információt (más megfogalmazás, más nyelv rendben) |
| `reszben` | konkrét és a jó irányba mutat, de nem pontosan a várt érték — „nagyjából stimmel”: jó kategória rossz elemmel, jó időszak rossz ablakkal, kettőből egy jó |
| `helytelen` | mást állít, kitér, felsorolja a lehetőségeket, vagy nem válaszol |
| `hallucinacio` | KONKRÉT kitalált tényt állít magabiztosan (nevet, helyet, dátumot, intézményt), és az téves |

### A `helytelen` / `hallucinacio` határ — ez a kör legfontosabb megkülönböztetése

Az 1. körben ez adta a korrekciók **43/45-ét**, és ebből lett a dolgozat egyik önálló
eredménye (a téves válaszok 50–86%-a magabiztos kitaláció). A gépi bíráló ezt a
kategóriát gyakorlatilag nem használja — ebben a körben is csak **1** hallucinációt és **0** `reszben`-t adott 102 válaszra.

A szabály, amit az 1. körben alkalmaztál (`kezi_validacio_naplo.md`):

> A `hallucinacio` címkét akkor használtam, amikor a hibás válasz konkrét kitalált
> szerzőt, helyet, dátumot, intézményt vagy részletes fabrikált tényt állított;
> egyszerű rossz kategória vagy nem-válasz `helytelen` maradt.

### Döntési fa

```
Válaszol egyáltalán a kérdésre?
├─ NEM (kitér, felsorol, kérdést ismétel) ──────────────► helytelen
└─ IGEN, konkrétumot állít
   ├─ pontosan a várt érték ──────────────────────────► helyes
   ├─ nem pontosan, de a jó irányba mutat ────────────► reszben
   └─ téves
      ├─ konkrét kitalált név/hely/dátum/intézmény ───► hallucinacio
      └─ csak rossz kategória, nincs kitalált adat ───► helytelen
```

## ⚠️ Amit NE rójunk fel

- **Bőbeszédűség és formázás.** Ez a modell markdownt használ (`**félkövér**`, felsorolás,
  fejezetcím). A forma nem számít, csak a tartalom.
- **A válasz nyelve.** Ha magyar kérdésre angolul felel, de a tartalom jó, az `helyes`.
- **A hiányzó rész csonkolt válaszban.** CSAK a meglévő szövegrészt értékeld. Ha a leírt
  rész alapján nem dönthető el, az `helytelen` — de nem `hallucinacio`, mert nem állított
  kitalált konkrétumot.
- **Az ismétlési hurok.** A beragadás dekódolási jelenség; a hurok ELŐTTI tartalom számít.

## Ha nem olvasol kínaiul

A kínai cellák (`*/zh`) a mátrix harmadát adják, ezért nem hagyhatók ki. Amit tehetsz:
a várt válasz kínai alakja ott van az ívben (`Várt:` sor), és a legtöbb ítélet eldönthető
azzal, hogy **szerepel-e a várt karaktersorozat a válaszban**. Ha igen és a mondat állítja
(nem tagadja, nem alternatívaként sorolja) → `helyes`. Ha nem szerepel, de a válasz
magabiztosan megnevez EGY MÁSIK konkrét helyet/nevet → `hallucinacio`. Ha csak körülír
vagy felsorol → `helytelen`. Kétes esetben jelöld meg és kérdezz rá.

## Beírás

```bash
SCOPE_RES=results_instruct_raw SCOPE_REPORTS=reports_instruct_raw python3 src/set_manual.py a HU04 en helytelen
SCOPE_RES=results_instruct_raw SCOPE_REPORTS=reports_instruct_raw python3 src/set_manual.py a ZH10 hu hallucinacio

# a bíráló ítéletének tömeges megerősítése (a ZH+HU csoportra):
SCOPE_RES=results_instruct_raw SCOPE_REPORTS=reports_instruct_raw python3 src/set_manual.py a --confirm-all
```

⚠️ A `--confirm-all` **minden** még üres sorra beírja a bíráló ítéletét. Csak akkor
használd, ha már végigolvastad az ívet, és a maradékkal tényleg egyetértesz.

## Kiértékelés

```bash
SCOPE_RES=results_instruct_raw SCOPE_REPORTS=reports_instruct_raw python3 src/analyze_a.py
```

→ `reports_instruct_raw/02_meres_a.md` (3×3 mátrix, hallucinációs tábla, megbízhatósági szakasz)

---

# Mérés D1 — 48 UNT-válasz (kötelező)

## Mit kell eldöntened

Fogalmanként előre rögzített **native** (a fogalom valódi jelentésmagjai) és **distortion**
(tipikus félreértések) komponenslista van. Minden válaszra két szám kell: hány native és
hány distortion komponens jelenik meg ténylegesen a szövegben.

Az 1. körben alkalmazott elved (`kezi_validacio_naplo.md`):

> Egy komponens csak akkor kapott találatot, ha a komponens tartalmi magja ténylegesen
> megjelent. Összetett komponensnél nem vettem automatikusan teljes találatnak egy
> részletet. A torzításokat is pozitív állításként kezeltem: csak akkor számoltam, ha a
> hibás keretezés a válaszban ténylegesen megjelent, puszta hiányból nem következtettem
> rá — kivéve ahol maga a torzítás definíciója kifejezetten egy jelentésárnyalat hiánya volt.

## Beírás

```bash
SCOPE_RES=results_instruct_raw SCOPE_REPORTS=reports_instruct_raw python3 src/set_manual.py d UNT-HU01 hu --native 2 --distortion 1
```

A `set_manual.py` ellenőrzi, hogy a szám belefér-e a fogalom komponenslistájába —
a nevezőt (`native_n`) a **befagyasztott** `items.jsonl` adja, azt nem lehet felülírni.

## Kiértékelés

```bash
SCOPE_RES=results_instruct_raw SCOPE_REPORTS=reports_instruct_raw python3 src/analyze_d.py
```

---

# Ellenőrző lista

- [ ] Mérés A: mind a 102 kötelező válasz kapott ellenőrző ítéletet (`set_manual.py status`)
- [ ] D1: mind a 48 UNT-válasz kapott `--native` és `--distortion` számot
- [ ] `analyze_a.py` és `analyze_d.py` újrafuttatva
- [ ] a riportok fejlécében nincs már „a ellenőrző kör hátravan” figyelmeztetés
- [ ] **a mércéd egyezik az 1. körével** — kétes eseteknél visszanéztél a `kezi_validacio_naplo.md`-be
- [ ] a kör eltéréseit ugyanúgy naplóztad, mint az 1. körnél

# Gyakori hibák

| hiba | miért baj |
|---|---|
| a CSV kézi szerkesztése | idézőjel-/vesszőtörés → némán elromlik egy cella (megtörtént) |
| a nyers válaszra ítélni a tisztított helyett | a bíráló a `text_clean`-t látta; az ív is azt mutatja |
| a csonkolt válasz hiányát felróni | a keret a mérés korlátja, nem a modell hibája |
| a formázást (markdown) hibának venni | a tartalom számít |
| a `hallucinacio` és a `helytelen` összemosása | ez adja a kör fő eredményét |
| más mércével ítélni, mint az 1. körben | a base↔instruct különbség a SZERZŐ elmozdulását mérné |
