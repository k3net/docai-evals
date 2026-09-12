# Round3 — Qwen3.8-Flash-Next GB10 vLLM stabilitási validáció, összefoglaló (2026-09-12)

> A `2026-09-12-qwen38-gb10-vllm-stabilitas-validacios-runbook.md` végrehajtása a **SPARK-DEV-en**.
> A prod (SPARK-BETA `night`-slot, `:8358`) végig **érintetlen** maradt.
>
> **Fejezetek:** `01-A-kar-prodkontroll.md` · `02-partial-hit-kiserlet.md` ·
> `03-C-kar-pr-kompatibilitas.md` · `04-upstream-pr-kommentek.md` · `05-B-kar-v029.md` ·
> nyers adat: `eredmenyek/` · szondák: `eszkozok/` · publikálható csomag: `publikalhato/`

## 1. Mi lett a fő eredmény?

A validáció **nem** a tervezett B/C kar összehasonlításával ért véget, hanem egy addig
félreértelmezett jelenség felderítésével:

⭐⭐⭐ **A prefix cache-en keresztül visszaolvasott állapot megváltoztatja a greedy logitokat, ha a
közös előtagot egy MÁS HOSSZÚSÁGÚ kérés írta be.** A hatás determinisztikus és reprodukálható; egy
addig nem használt dokumentumon (D6) **előre megjósolva sikerült előidézni** azzal, hogy a két kérés
eltérő számú teljes cache-blokkot zárjon le. ⚠️ Ugyanez a recept egy másik dokumentumon (D1) **nem**
hozta elő — a blokkszám-eltérés tehát **szükségesnek látszik, de nem elégséges**; a pontos mechanizmus
feltárása külön munka.

A round1 (08-28) és round2 (09-03) is látta a tünetet (mindig ugyanaz az egy item bukott az
50-ből), de a magyarázat fordított volt: a „hideg" futást gyanúsítottuk. A round3 megmutatta,
hogy a hideg/részleges út a **helyes**, és a **teljes cache-hit** tér el.

## 2. A bizonyítási lánc

| # | kísérlet | felállás | eredmény |
|---|---|---|---|
| 1 | determinizmus-szonda (§5.3) | 4 item × 10, `EXACT_TOPK=1` | 3/4 PASS, a T2-01 FAIL — a round2 mintázata bájtra |
| 2 | tiszta kar | T2-01 × 10, friss szerver, más kérés nélkül | **PASS** (10/10 azonos) |
| 3 | szennyezett kar | T3-01 × 1 → T2-01 × 10, friss szerver | **FAIL** — a **#1** egyezik a tiszta karral, a **#2–10** tér el |
| 4 | negatív kontroll | ugyanaz, `--no-enable-prefix-caching` | **PASS** (10/10) → a prefix cache okozza |
| 5 | ismétlés | szennyezett kar újabb friss szerveren | **FAIL**, azonos mintázat (más abszolút hash) |
| 6 | más itempárok | D3 (T5-01→T5-02), D5 (T9-01→T10-01) | **PASS** — nem minden páron jelentkezik |
| 7 | hipotézis: **blokkszám-eltérés** | log: „attention block size **1600** tokens"; a bukó pár az egyetlen, ahol a két kérés eltérő számú teljes blokkot zár le (3169→1, 3227→2; a passzolóknál 1/1 és 15/15) | — |
| 8 | szintetikus teszt | ismétlődő kitöltő prefix, A 1 blokk / B 2 blokk | **PASS** — a hipotézis szintetikus tartalommal **nem** igazolódik |
| 9 | **valódi dokumentum** (D6, addig érintetlen) | prefix 3002 tok, A 3086 (1 blokk) / B 3267 (2 blokk) | ⭐ **FAIL** — a jelenség **megjósolva, új dokumentumon előidézve** |
| 10 | döntő kontroll | ugyanaz a D6 prefix, A és B **azonos** blokkszámmal (2/2) | **PASS** (6/6) |
| 11 | általánosítási próba | D1 prefix (3 696 tok), A 4 689 (2 blokk) / B 4 870 (3 blokk) — **ugyanazon a szerverindításon**, mint a 10. | **PASS** → a blokkszám-eltérés **nem elégséges** feltétel |
| 12 | **B kar: másik image, másik vLLM, másik top-k út** (v0.29.0 + det-kernel) | determinizmus-szonda 4 item × 10 | ⛔ **3/4 PASS, a T2-01 ugyanúgy FAIL** |
| 13 | B kar, blokkhatár-szonda **egy indításon belül** | D6 1 vs 2 blokk / D3 2 vs 2 blokk | ⛔ **FAIL** / ✅ **PASS** |

## 3. Amit ebből állítani lehet — és amit nem

**Állítható:**

- a jelenség létezik, `temperature=0` mellett, **három** független friss szerverindításon;
- a prefix cache kikapcsolása megszünteti;
- a hatás a **kérések közti** blokk-újrafelhasználáshoz kötődik, nem a „hideg vs. meleg" tengelyhez;
- valódi dokumentum-tartalom mellett a blokkhatár-átlépés különbsége **elég volt** a kiváltásához két
  független dokumentumon (D2 természetes párral, D6 méretezett suffixekkel);
- a QSA top-k kernel **nincs** benne: az A karon az egzakt `torch.topk`, a B karon a determinisztikus
  CUDA-kernel futott — a jelenség **mindkettőn azonos**;
- a jelenség **nem** az általunk használt preview image sajátja: a hivatalos `vllm/vllm-openai:v0.29.0`
  alapon épült candidate-en (más vLLM-verzió, más modellcsomag-név) bájtra ugyanúgy előjön.

**Nem állítható:**

- hogy a [#54076](https://github.com/vllm-project/vllm/pull/54076) / [#53798](https://github.com/vllm-project/vllm/pull/53798)
  align-mode javítások megoldják — patchelt kart nem tudtunk építeni (ld. `03-…`);
- hogy a mechanizmus pontosan a Mamba-állapot elcsúszása; a log és a PR-ek erre mutatnak, de
  a kernel-szintű ok feltárása külön munka;
- hogy szintetikus (alacsony entrópiájú, ismétlődő) tartalommal is előjön — a 8. sor szerint **nem**;
- hogy a blokkszám-eltérés **elégséges** feltétel — a 11. sor szerint **nem** (D1: 2 vs 3 blokk, PASS,
  ugyanazon a szerverindításon, ahol a D6-kontroll futott). A jelenség tehát a prompt hosszától vagy
  tartalmától is függ; a QSA ritkafigyelem blokk-választása itt a legvalószínűbb további tényező.

⚠️ **Új mellék-lelet:** a teljes logprob-hash **szerverindítások között nem stabil** — még a
legelső, teljesen hideg kérésnél sem (a T3-01 előkészítő hash a 3., 4. és 5. indításon:
`a11bda…`, `4851c3…`, `4851c3…`). A **mintázat** viszont minden indításon reprodukálódott.
A determinizmus tehát **egy szerverindításon belül** értelmezhető; ez a round1 óta használt
„3 friss indításon ugyanaz" elfogadási feltételt is pontosítja: a mintázatra igaz, az abszolút
értékre nem.

## 4. A runbook karjainak állása

| kar | terv | mi történt |
|---|---|---|
| **A — prod kontroll** | ✅ teljes | 6 friss szerverindítás, determinizmus + prefix-cache + memória-timeline + a fenti kísérletsor |
| **B — blazux v0.29 bundle** | ✅ **teljes** | checkout `c578815`, image `cc6a1af569eb` (`vllm/vllm-openai:v0.29.0`, `VLLM_BUILD_COMMIT=98dff2a…`), `QSADET active` bizonyítékkal. Smoke ✅, determinizmus-szonda **3/4 PASS (T2-01 ugyanúgy FAIL)**, blokkhatár-szonda FAIL/PASS egy indításon, prefill **+21…28 %** az A karhoz képest, 0 hibajel. Részletek: `05-B-kar-v029.md` |
| **C — nyitott PR-ek** | ⛔ **kapun elakadt (dokumentáltan)** | a #56500 fő hunkja olyan fájlt módosít, ami sem a pinelt preview image-ben, sem a v0.29.0-ban nem létezik; a célzott memória-tünet a mi águnkon nem reprodukálható |

**Nem futott továbbá:** a runbook §11 többórás soak, a 128K/262K kontextus-lépcső, és az 50 elemű
KIE-suite a B karon — ez utóbbi a `night`-slot élesítésének feltétele (`docai-0061`), mert a det-kernel
más szöveget adhat (round2 §3.5).

⛔ **Egy szükségszerű eltérés a B karon:** a `-cc.splitting_ops` **nem** lehetett bájtra azonos az A
karéval, mert a csomagátnevezéssel az op-nevek is megváltoztak; a régi listával a motor CUDA-graph
hibával elhasalt (`05-…` §4). A funkcionálisan azonos v0.29-es listát használtuk.

## 5. Elfogadási feltételek (runbook §14) — az A karra

| feltétel | állás |
|---|---|
| 0 eltérő greedy output a determinizmussági szondán | ⚠️ 3/4 item; a 4. eltérése **azonosított mechanizmus**, nem zaj |
| 0/50 instabil KIE-elem | ⏸ nem futott ebben a körben (round2: 0/50 a det-kernellel) |
| cold/partial/full cache-út konzisztens | ⚠️ tiszta felállásban igen; **kérések közti** újrafelhasználásnál nem |
| nincs üres reasoning vagy kontextusmásolás | ✅ nem fordult elő |
| nincs monoton memória- vagy állapotnövekedés | ✅ 8K→64K sík plató |
| nincs OOM / CUDA illegal access / worker restart | ✅ 0 találat mind a 6 futás logjában |
| TTFT/prefill regresszió dokumentált | ✅ prefill 1 736–1 884 tok/s, nem romlik a hosszal |
| ≥ 3 friss szerverindításon ugyanaz | ✅ a **mintázatra**; ⚠️ az abszolút hashre **nem** (§3) |
| minden image-, repo- és PR-SHA rögzítve | ✅ `01-…` §1, `03-…` §1 |

## 6. Üzemi következmény

A `night`-slot konfigurációján **nem változtatunk** ennek alapján: a prefix cache marad
bekapcsolva (a kikapcsolása a hosszú, közös dokumentum-prefixeknél nagyságrendi lassulás volna),
a hatás pedig a logitokban jelentkezik, a meglévő védelmek mellett — KIE-nél háromszori futtatás
és egyezés-ellenőrzés, chatnél külön ellenőrző lépés.

⛔ A mérés **nem** ad okot arra, hogy a `VLLM_QSA_EXACT_TOPK=1` beállításon lazítsunk: az
végig aktív volt, és a jelenséghez semmi köze.
