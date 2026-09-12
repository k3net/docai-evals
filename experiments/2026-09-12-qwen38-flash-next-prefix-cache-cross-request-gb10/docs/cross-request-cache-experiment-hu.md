# Round3 / T2-01 — a prefix-cache-en átolvasott állapot izolálása (spark-dev, 2026-09-12)

> **A kiindulás:** a determinizmus-szondában a round1 (08-28), a round2 (09-03) és a round3 (09-12)
> mérésén **ugyanaz az egyetlen item (T2-01) bukik, ugyanazzal a mintázattal**: az 1. futás hash-e
> eltér, a 2–10. egymással azonos. A round2 ezt „részleges-vs-teljes cache-hit jelenségként" írta le,
> de nem döntötte el, **melyik ág a helyes**. Ez a kísérlet eldönti.

## 1. A felállás

A T2-01 és a T3-01 **ugyanazt a `D2.md`-t** kapja meg, csak a feladat + séma suffix tér el, és a
szonda a T3-01-et futtatja előbb. Két kar, **mindkettő teljesen friss szerverindításon** (a
`~/.cache/huggingface` és a torch.compile cache közös, a KV/prefix cache üres):

| kar | szekvencia | prefix cache | mit mér |
|---|---|---|---|
| **tiszta** | T2-01 × 10, más kérés nélkül | ON | a T2-01 önmagában determinisztikus-e |
| **szennyezett** | T3-01 × 1, majd T2-01 × 10 | ON | mit csinál a **másik kérés által írt** közös prefix-blokkokkal |
| **negatív kontroll** | ugyanaz a szennyezett szekvencia | **OFF** (`--no-enable-prefix-caching`) | tényleg a prefix cache okozza-e |

Eszköz: `eszkozok/t201_partial_hit.py` (`temperature=0`, `max_tokens=48`, top-20 logprob,
thinking OFF, szigorúan sorosan). A hash = a generálás **minden** tokenjének top-20 logprob-listájából
képzett SHA-256; a szövegazonosság nem számít bizonyítéknak.

## 2. Eredmény

| kar / futás | teljes logprob-hash | 1. token top-20 sig |
|---|---|---|
| **tiszta** (2. szerverindítás), #1–#10 | `fdc948fbf8f7698f` ×10 | `9dd8c8389070202a` ×10 |
| **szennyezett** (3. szerverindítás), előkészítés T3-01 | `a11bda4539ab9c88` | — |
| **szennyezett**, T2-01 **#1** | `fdc948fbf8f7698f` | `9dd8c8389070202a` |
| **szennyezett**, T2-01 #2–#10 | `dabe443eeea90df5` ×9 | `15fcdd5f2718a6c6` ×9 |
| **negatív kontroll** (4. indítás, cache OFF), T2-01 #1–#10 | `c1dc6688b1004f2f` ×10 | `125df9a862e0462e` ×10 |

⭐⭐⭐ **A hibás ág nem az, amelyiket a round2 gyanúsította.** A szennyezett kar **első** futása —
amelyik a D2 blokkjaira részleges hitet kap, de a saját suffixét frissen prefillezi — **bitre ugyanazt**
adja, mint a teljesen cache-mentes tiszta kar mind a tíz futása. A **2–10. futás**, vagyis a **teljes
prefix-cache hit** tér el, már a **0. tokennél**, és utána stabilan hozza a saját, eltérő értékét.

⭐⭐⭐ **A negatív kontroll zárja a láncot:** ugyanaz a szennyezett szekvencia
`--no-enable-prefix-caching` mellett **10/10 azonos** — az eltérés eltűnik. (Az abszolút hash itt
szükségszerűen más, `c1dc66…`: prefix cache nélkül a vLLM nem is kapcsol `align` Mamba-módra —
a log `Mamba cache mode is set to 'align'` sora ilyenkor **nem jelenik meg** —, tehát más numerikus
út fut. A mérőszám a **stabilitás**, nem az abszolút érték.)

⭐⭐ A tiszta karon a 2–10. futás **szintén teljes cache hit**, és ott **nincs** eltérés. A különbség
tehát nem a „cache-hit vs. hideg" tengely, hanem az, hogy a közös prefix blokkjait **melyik kérés írta**:
ha ugyanaz a kérés (tiszta kar), a visszaolvasás helyes; ha egy **másik, eltérő hosszú** kérés
(szennyezett kar), a visszaolvasott állapot más logitokat ad.

## 3. Mit jelent ez

A modell hibrid (Mamba/linear-attention + QSA sparse attention) architektúrájú, és a vLLM a prefix
caching mellett automatikusan `align` Mamba-cache módra vált:

```
INFO [config.py:605] Mamba cache mode is set to 'align' for Qwen4ExpForConditionalGeneration
                     by default when prefix caching is enabled
```

Align módban a Mamba-állapotot blokkhatárokon kell menteni/visszaolvasni, a chunk-felosztásnak pedig
együtt kell mozognia a cache-csoport blokkméretével. Ha a közös prefix blokkjait egy **más hosszúságú**
kérés írta, a visszaolvasott állapot és a kérés saját chunk-határai elcsúszhatnak — pontosan ezt célozza
két nyitott upstream PR:

- [#54076](https://github.com/vllm-project/vllm/pull/54076) — *Use the Mamba cache group's block size for align-mode chunk splitting*
- [#53798](https://github.com/vllm-project/vllm/pull/53798) — *Seed align-mode Mamba `state_idx` in Mamba blocks*

### ⭐⭐⭐ A két javítás lényege MÁR AKTÍV a mért image-ben — és a jelenség így is fennáll

A B kar checkoutjából (`blazux/qwen3.8-Flash-DGX` @ `c578815`) kiderült, hogy a recept egy
`src/patch_mamba_block_size.py` nevű, **két soros** javítást tesz az image-be, és ez pontosan a fenti
két PR **két fájlját** és szemantikáját érinti:

| javítás | fájl | mit tesz |
|---|---|---|
| ~#53798 | `v1/worker/gpu/model_states/mamba_hybrid.py` | a state-slot seed `block_size` helyett a **`mamba_block_size`**-szal osztja a `num_computed_tokens - 1`-et |
| ~#54076 | `v1/core/sched/scheduler.py` | a block-aligned prefill-split a **scheduler blokkméretét** (a csoportok LCM-jét) használja |

A patch fejléce a hibát is leírja: az `EngineCore` a `cache_config.block_size`-t a **legkisebb** csoport
blokkméretére írja felül (a QSA raw-key ring 8/16-os blokkja), miközben a seed és a split a **mamba**
blokkméretet (1600) várná; következmény: „a prefix hit a state-slotot rossz oszlopra ülteti → null blokk
→ **csupa nulla visszaolvasott állapot**".

⛔ **Ellenőriztük a mért image-ben** (`qwen38-flash-dgx-up:e655b7d`), és mindkét sor benne van:

```
mamba_hybrid.py:116-117   (new_req_data.num_computed_tokens - 1)
                          // (self.cache_config.mamba_block_size or self.cache_config.block_size)
scheduler.py:392          block_size = self.block_size  # scheduler block size (LCM of groups) == mamba block size
```

Vagyis a fenti kísérletsor **nem** a javítatlan hibát méri: a „csupa nulla állapot" eset már el van
hárítva, és **marad** egy finomabb, kérések közti eltérés. ⚠️ Ez nem jelenti, hogy a két upstream PR
felesleges volna: azok lényegesen többet tesznek a kétsoros patchnél (#54076: +287/−17 hat fájlban,
#53798: +64/−23), így nem zárható ki, hogy a maradék esetet is lefedik — ezt csak egy patchelt karon
lehetne eldönteni.

⚠️ **Amit ez a kísérlet NEM bizonyít:** hogy a fenti két PR megjavítja a maradékot. Amit bizonyít: a
jelenség **létezik, reprodukálható, determinisztikus**, a prefix-cache-en átolvasott állapothoz kötődik,
**nem** a top-k kernelhez (`VLLM_QSA_EXACT_TOPK=1` mindkét karon aktív volt), és **nem** az ismert,
már javított all-zero-state hibához.

## 3b. Blokkhatár-szonda — a mechanizmus-hipotézis tesztje (és korlátai)

A log elárulja a cache blokkméretét:

```
INFO [interface.py:915] Setting attention block size to 1600 tokens to ensure that
                        attention page size is >= mamba page size.
```

Megnézve a mért itempárokat, a bukó pár az **egyetlen**, ahol a két kérés eltérő számú **teljes**
blokkot zár le:

| pár | A prompt | B prompt | teljes blokkok (1600) | eredmény |
|---|---:|---:|---|---|
| D2: T3-01 → T2-01 | 3 169 | 3 227 | **1 vs 2** | ⛔ FAIL |
| D3: T5-01 → T5-02 | 2 155 | 2 182 | 1 vs 1 | ✅ PASS |
| D5: T9-01 → T10-01 | 24 384 | 24 404 | 15 vs 15 | ✅ PASS |

Ebből jött a hipotézis, és a `eszkozok/blokkhatar_szonda.py` ezt teszteli: a közös prefix után a két
suffixet a `/tokenize`-zal méretezi úgy, hogy a blokkszám eltérjen vagy egyezzen.

| # | felállás | prefix | A / B prompt | blokkok | eredmény |
|---|---|---|---:|---|---|
| 1 | szintetikus kitöltő | 1 680 tok, ismétlődő minta | 3 091 / 3 308 | 1 vs 2 | ✅ PASS |
| 2 | szintetikus kontroll | ugyanaz | 3 307 / 3 371 | 2 vs 2 | ✅ PASS |
| 3 | **valódi dokumentum (D6)** | 3 002 tok | 3 086 / 3 267 | **1 vs 2** | ⛔ **FAIL** |
| 4 | valódi kontroll (D6, más indítás) | 3 002 tok | 3 307 / 3 371 | 2 vs 2 | ✅ PASS |
| 5 | valódi általánosítás (D1, a 4-gyel **azonos** indításon) | 3 696 tok | 4 689 / 4 870 | 2 vs 3 | ✅ PASS |

⭐ A **3. sor a legerősebb eredmény az egész körben**: egy addig nem használt dokumentumon, méretezett
suffixekkel, **előre megjósolva** idéztük elő ugyanazt a mintázatot (B#1 eltér, B#2–6 azonos).

⚠️ Az **1. és az 5. sor viszont megcáfolja az egyszerű magyarázatot**: szintetikus, alacsony
entrópiájú prefixszel nem jön elő, és egy másik valódi dokumentumon (D1, 2 vs 3 blokk) sem — ráadásul
az 5. sor **ugyanazon a szerverindításon** futott, mint a 4. kontroll, tehát az indítás-hatás kizárva.
A blokkszám-eltérés tehát **szükségesnek látszik, de nem elégséges**; a prompt hossza vagy tartalma is
számít. A legvalószínűbb további tényező a QSA ritkafigyelem blokk-választása, amely a kontextus
hosszától és tartalmától is függ — ennek szétválasztása külön mérés.

## 4. Gyakorlati következmény a saját üzemünkre

A `night`-slot chat- és KIE-forgalmában **közös hosszú prefixek** vannak (ugyanaz a dokumentum több
kérdéssel, ugyanaz a rendszerprompt több feladattal) — tehát pontosan a szennyezett kar felállása.
A hatás a mért itemen a **logitokban** jelentkezett; a látható válasz szövege mind a 10 futáson azonos
maradt (`szoveg_valtozatok: 1`), de a round1 §3 szerint ugyanez a fajta eltérés 50-ből 5 itemen a
**kinyert dátumot vagy összeget** is elmozdította.

⛔ **A szövegazonosság tehát itt sem bizonyíték.** Az üzemi védelem változatlan: a KIE-nél háromszori
futtatás + egyezés-ellenőrzés, a chatnél a hallucináció-ellenőrző lépés.
