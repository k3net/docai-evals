# Round2 / 3. fázis — determinisztikus `persistent_topk` kernel (vllm#55122) A/B (spark-dev, 2026-09-03)

> **A tét:** a round1 óta éles `VLLM_QSA_EXACT_TOPK=1` (python-szintű `torch.topk` a QSA-indexer
> block-selectjében) determinisztikus, de **1,35× prefill-árat** fizetünk érte (round1 §3.1e:
> 2 350 → 1 756 tok/s). A #55122 ugyanezt kernel-szinten oldja meg; a PR becslése ≈ +1,8 % TTFT.
> Ha ez a mi terhelésünkön is igaz, a `night`-slot prefillje ~26 %-ot nyer vissza.

## 1. Változatok

| jel | QSA block-select | image | env |
|---|---|---|---|
| **A** | python `torch.topk` (blazux `patch_qsa_exact_topk.py`, mód 1) | `qwen38-flash-dgx-up:e655b7d` | `VLLM_QSA_EXACT_TOPK=1` |
| **C** | **determinisztikus CUDA-kernel** (`_C_det.persistent_topk`, #55122) | `qwen38-flash-dgx-det:local` | `VLLM_QSA_EXACT_TOPK=0`, `VLLM_QSA_DET_TOPK=1`, `VLLM_QSA_DET_LIB=/gb10/…/_C_det.so` |

Minden más bájtra azonos (262 144 ctx, `--max-num-seqs 4`, prefix cache be, chunked prefill 8192,
PIECEWISE + 12 splitting op, MTP=2, `--kv-cache-dtype auto`).

A két patch **komponálható**: a blazux-patch a *hívást* cseréli le (`topk_op(...)` → if/elif/else),
a jschmied-patch a `topk_op = (...)` *értékadást* — `EXACT_TOPK=0` mellett az `else` ág fut, és a
`topk_op` ekkor már a determinisztikus kernel.

## 2. Build és korrektségi teszt a mi image-ünkben

Forrás: `jschmied/qwen38-flash-next-gb10` @ `0c5598782b33bbfc9acb46acd57b495ca0eb01b7`
(git clone a spark-devre, `~/round2/`).

```
docker run --rm --gpus all -v ~/round2/qwen38-flash-next-gb10/patches/kernel-det:/kd \
  -e DET_BUILD_DIR=/kd/build -e TORCH_EXTENSIONS_DIR=/kd/build \
  --entrypoint python3 qwen38-flash-dgx-up:e655b7d /kd/build_det.py
```

- ✅ Lefordult a saját image-ünkben (torch 2.13+cu130, nvcc sm_121a): `build/_C_det.so`, 1,42 MB.
- ✅ `test_det.py build/_C_det.so` → **`FAILS: 0`**.
- ⭐ Minden tesztsorban `stock identical x3=False` **és** `stock set==ref=False`: a **stock
  `persistent_topk` a mi GB10-ünkön sem reprodukálja önmagát, és a kiválasztott HALMAZ is eltér**
  az egzakt referenciától. Ez a round1 root cause-unk (§3.1c–d) független, kernel-szintű
  megerősítése — ugyanaz, amit mi a suite-on 13/50 instabil itemként láttunk.

⚠️ A `docker commit` az entrypointot a patch-konténerből örökli; `--change 'ENTRYPOINT
["vllm","serve"]'` nélkül a szerver `python3 <snapshot-path>`-t próbál futtatni és azonnal elhasal.

## 3. Mérés

A C-szerver aktivációja logból igazolva (nem csak env-változóból):
`QSADET active: /gb10/patches/kernel-det/build/_C_det.so`.
A mérési szekvencia bájtra azonos az A-ágéval (ugyanaz a smoke, ugyanazok az itemek, ugyanabban a
sorrendben) — a prefix-cache állapot különben eltolná a hideg prefill-időket.

### 3.1 Determinizmus — azonos

| kör | A | C |
|---|---|---|
| 4 item × 10 × 48 tok, thinking OFF | 3/4 PASS | **3/4 PASS** |
| 4 item × 5 × 512 tok, thinking ON | 4/4 PASS | **4/4 PASS** |

⭐ Mindkét ágon **ugyanaz a T2-01 bukik, ugyanazzal a mintázattal** (az 1. futás eltér, a 2–10.
egymással azonos). Ez megerősíti, hogy a §3.1-ben leírt részleges-vs-teljes cache-hit jelenség
külön, determinisztikus mechanizmus, és **nem** a top-k kernel zaja.

### 3.2 Prefill-sebesség (48 tokenes kör, azonos generált tokenszám mindkét ágon)

`prefill_ms = hideg futás − a meleg futások mediánja` (a meleg futás prefillje cache-hit):

| item | prompt tok | A prefill | C prefill | nyereség |
|---|---:|---:|---:|---:|
| T6-02 | 6 082 | 1 952 tok/s | **2 253 tok/s** | **+15,4 %** |
| T10-05 | 24 416 | 1 756 tok/s | **1 932 tok/s** | **+10,1 %** |
| T2-01 | 3 227 | 2 417 tok/s | 3 049 tok/s | +26,2 % ⚠️ |
| ~~T3-01~~ | 3 169 | — | — | ⛔ kizárva: a smoke felmelegítette, a hideg-meleg különbség 153 ms |

⚠️ A T2-01 hideg futása részlegesen cache-elt volt (közös `D2.md` prefix a T3-01-gyel), ezért a
számított prefill-sebessége felfelé torzít mindkét ágon. **A két tiszta cella a T6-02 és a T10-05:
+10…+15 %.** Viszonyítás: a round1 §3.1e szerint az exact `torch.topk` a stock kernelhez képest
1,35× lassulás (2 350 → 1 756 tok/s) — a B-kontroll adja meg, ebből mennyit hoz vissza a C.

### 3.3 Decode — nincs érdemi különbség

A 48 tokenes körben látott 8–10 %-os „meleg" időelőny **nem decode-nyereség**: a meleg futás is
tartalmaz maradék-prefillt (a prompt utolsó, részleges blokkja), és az megy át a QSA
block-selecten. Az 512 tokenes gondolkodó körben a tiszta decode kiegyenlített (T3-01: A 16 805–
17 125 ms vs C 17 074 ms azonos 512 tokenre; T10-05: A 29,1 tok/s vs C 30,2 tok/s). Ez egyezik a
round1 leletével (decode 26,4 vs 27,3 tok/s — a top-k ára a prefillben van).

### 3.4 B-kontroll (stock kernel) — a szonda érzékenysége és a sebesség-viszonyítás

Azonos image (`qwen38-flash-dgx-det:local`), egyetlen változó: sem `EXACT_TOPK`, sem `DET_TOPK`
(a log `QSADET` sorainak száma 0 — az arm a saját aktivációs sorával igazolva).

- ⭐⭐ **Determinizmus: 0/4 PASS — mind a négy itemen 10 különböző hash 10 futásból**, az eltérés
  már a 0. tokennél. Ez egyszerre (a) **negatív kontroll**: a szonda érzékeny, tehát az A/C ágak
  PASS-ai valódiak, és (b) a round1 root cause (§3.1c) független megerősítése — most **prod-konfigban,
  prefix cache-sel** is.
- ⚠️ `szövegváltozat: 1` itt is: a látható válasz mind a 10 futáson azonos maradt. **A
  szövegazonosság nem bizonyíték** — a round1-ben ugyanez a kernel 13/50 itemen adott ingadozó
  kimenetet, 5-nél a kinyert dátummal/összeggel együtt.

**Prefill-sebesség, ugyanaz a szekvencia mindhárom ágon:**

| item | prompt tok | B stock | A exact `torch.topk` | C det-kernel | A/B | **C/B** |
|---|---:|---:|---:|---:|---:|---:|
| T6-02 | 6 082 | 2 246 tok/s | 1 952 | **2 253** | 0,87 | **1,00** |
| T10-05 | 24 416 | 1 943 tok/s | 1 756 | **1 932** | 0,90 | **0,99** |
| T2-01 | 3 227 | 3 163 tok/s | 2 417 | **3 049** | 0,76 | **0,96** |
| ~~T3-01~~ | 3 169 | ⛔ smoke-szennyezett cella, kizárva | | | | |

⭐⭐⭐ **A determinizmus ára a det-kernellel gyakorlatilag eltűnik**: a C a stock sebesség
**96–100 %-át** hozza, míg a jelenlegi éles A-megoldás 76–90 %-on van. Ez egybevág a PR saját
becslésével (≈ +1,8 % TTFT), és a round1-ben mért 1,35× árat (0,74) magyarázza: az a python-szintű
`torch.topk` ára volt, nem a determinizmusé.

### 3.5 ⛔ A váltás megváltoztatja a kimenetet

Az A és a C **más szöveget** ad ugyanarra a promptra: T2-01 gondolkodása 273 (A) vs 294 (C) token,
T10-05 376 (A) vs 501 (C). Ez várható — két különböző, egyaránt determinisztikus block-select más
halmazt/sorrendet választ, tehát más logitokat ad —, de azt jelenti, hogy **a váltás nem
minőség-semleges: a magyar KIE-suite pontszámát (round1: 98/100) újra kell mérni a C-vel**,
mielőtt élesbe kerül.

### 3.6 F4 — magyar KIE fő suite 50×3 a det-kernellel: **95,00/100, 0/50 instabil, 0 formátumhiba**

`eredmenyek/meres-flash-nvfp4-detkernel.json` (a deven: `~/eval/magyar-kie-eval/reports/`), a
round1 harness és pontozó, mind a 150 kérés `finish=stop`, mind az 50 item 3/3 azonos kimenet.

| rendszer | pont | instabil | futás |
|---|---:|---:|---:|
| stock `persistent_topk` (round1) | 97,00 | 13/50 | 3 |
| round1 topk3-image (`torch.topk` + kanonikus rendezés) | 98,00 | 0/50 | 3 |
| **prod-image `e655b7d`, `EXACT_TOPK=1` (A)** | 96,00 | 0/50 | **1** |
| **C det-kernel** | **95,00** | **0/50** | 3 |

Pontosan két itemen tér el:
- **T5-03 (0/2):** a `tetelek` tömb JSON-kódolt **stringként** jön vissza (dupla szerializálás), a
  szigorú pontozó elutasítja — a tartalom (4 tétel, összegek, áfakulcsok) HELYES. ⛔ **A prod-image
  (A) ugyanezt csinálja (0/2)**; a round1 topk3-image listát adott. Image-tulajdonság, nem a kernelé.
- **T3-04 (1/2):** valódi értékhiba — a munkanapos határidő `2026-12-30` a helyes `2027-01-05`
  helyett; a gondolkodás egy near-tie-nál másfelé ágazik. A és a topk3-image is 2/2.

→ **A mostani éleshez képest −1 pont, egyetlen reasoning-itemen**, miközben a prod-referencia maga
1 futásos. Egy item egy futássorozatban nem „rosszabb kernel"-bizonyíték (két különböző egzakt
kiválasztás a holtversenyeknél máshova esik — ez így néz ki 50 itemen), de nem is a `docai-0061`
AC#1-ben kért „nem romlik 98 alá". A nehéz suite + challenge + ismételt futássorozat dönt.

## 4. Ítélet és a hátralévő lépések

**A C változat marad a jelölt az `EXACT_TOPK=1` leváltására**: azonos determinizmus, a stock
sebesség 96–100 %-a, a kernel a mi image-ünkben lefordul (0 FAIL), a fő suite-on 0/50 instabil és
95/100 a prod 96-jával szemben (egy near-tie item). A váltás **nem minőség-semleges** (§3.5, §3.6),
a patch **nyitott upstream PR** — production-váltás előtt:

| # | teendő | miért |
|---|---|---|
| ~~F4~~ | ~~fő suite 50×3~~ | **KÉSZ (§3.6): 95/100, 0/50** — hátra: nehéz 10×3 + challenge + egy ismételt fő futássorozat, hogy a T3-04 tie-e vagy szisztematikus |
| F5 | 3 külön szerverindítás, azonos szonda (a „no call from three runs" szabály) | most 1 indítás van ágakként |
| F6 | a hurok-őr viselkedése a C-vel (round1 §3.6: greedy+thinking ismétlési hurok) | a hurok a determinisztikus prefill mellékhatása volt |
| F7 | vendorozás a `spark/servers/vllm-qwen38-flash/` receptbe (Dockerfile-lépés + `.so` build), commit-pin | ⛔ a mostani C-image `docker commit`-tel készült a deven — **így nem élesíthető** |

⛔⛔ A `qwen38-flash-dgx-det:local` image a spark-deven `docker commit`-tel jött létre (patch-elt
`qsa.py` + mountolt `.so`). Ez mérésre jó, **élesbe így nem mehet**: a recept a repóba tartozik
(Dockerfile-lépés, a kernel forrásának pinelt commitja, a `.so` build a képbe), és a deploy a user
git-útján megy.

## 5. Reprodukálás

```
# spark-dev, a repó klónja: ~/round2/qwen38-flash-next-gb10 @ 0c5598782b33bbfc9acb46acd57b495ca0eb01b7
docker run --rm --gpus all -v ~/round2/qwen38-flash-next-gb10/patches/kernel-det:/kd \
  -e DET_BUILD_DIR=/kd/build -e TORCH_EXTENSIONS_DIR=/kd/build \
  --entrypoint python3 qwen38-flash-dgx-up:e655b7d /kd/build_det.py
docker run --rm --gpus all -v ~/round2/qwen38-flash-next-gb10/patches/kernel-det:/kd -w /kd \
  --entrypoint python3 qwen38-flash-dgx-up:e655b7d test_det.py build/_C_det.so     # FAILS: 0

docker run --name det-patch -v ~/round2/qwen38-flash-next-gb10:/gb10 \
  --entrypoint python3 qwen38-flash-dgx-up:e655b7d /gb10/tools/determinism/qsadet_patch.py
docker commit --change 'ENTRYPOINT ["vllm","serve"]' --change 'WORKDIR /vllm-workspace' \
  det-patch qwen38-flash-dgx-det:local && docker rm det-patch

# szerver: a compose paraméterei + VLLM_QSA_EXACT_TOPK=0, VLLM_QSA_DET_TOPK=1,
#          VLLM_QSA_DET_LIB=/gb10/patches/kernel-det/build/_C_det.so
# ellenőrzés (fail-closed): docker logs <konténer> | grep 'QSADET active'
```

Szonda a laptopról: `eszkozok/logprob_szonda.py --url http://10.10.0.5:<port> --model
qwen38-flash-next-nvfp4 --korpusz <items.jsonl + corpus/>`. Nyers adatok: `eredmenyek/szonda-{A,B,C}-*.json`.
