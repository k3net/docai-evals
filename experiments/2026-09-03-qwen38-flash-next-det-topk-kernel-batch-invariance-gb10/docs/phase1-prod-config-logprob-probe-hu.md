# Round2 / 1. fázis — a prod-night konfig logprob-szintű reprodukálhatósága (spark-dev, 2026-09-03)

> **Egymondatos lelet:** a jelenlegi éles `night`-konfig (`e655b7d` image + `VLLM_QSA_EXACT_TOPK=1`
> + prefix cache + MTP=2) **azonos cache-állapot mellett tokenszinten bitre reprodukálható** —
> 92 kérésből 91 azonos hash-t adott; az egyetlen eltérés oka azonosítva: **részleges vs. teljes
> prefix-cache-hit** ugyanarra a promptra. A round2 runbook fő gyanúsítottja, a FlashInfer CUTLASS
> NVFP4 MoE fused finalize (vllm#54945), a **mi shape-jeinken nem aktiválódik**.

## 1. Miért kellett ez a mérés

A round1 (`../round1/eredmenyek/03-nvfp4-instabilitas.md`) determinizmus-bizonyítéka két ponton
nem fedi az éles üzemet:

| round1 mérés | éles `night`-konfig | a rés |
|---|---|---|
| `src/prefill_szonda.py`, **`max_tokens=1`** | teljes generálás (KIE 16k-ig) | csak a prefill 0. tokenjét néztük; a decode-lépések nem |
| `izolacio.sh`: **`--no-enable-prefix-caching`** | `--enable-prefix-caching` | a PC-kapcsoló a `mamba_cache_mode`-ot is `align`-ra állítja (két változó egy kapcsolón) |

Közben upstream két új, a mi buildünket érintő lelet született (mindkettő **nyitott** PR/issue,
2026-09-03-i ellenőrzés): a MoE fused finalize nemdeterminizmusa (vllm#54945 / PR #54948) és a
determinisztikus `persistent_topk` kernel (PR #55122). A szerverünk logja megerősíti, hogy az
érintett kernelen futunk: `Using 'FLASHINFER_CUTLASS' NvFp4 MoE backend` (`nvfp4.py:291`).

## 2. Mérési elrendezés

- **Szerver:** `spark-dev`, `qwen38-det-a` konténer, `qwen38-flash-dgx-up:e655b7d` image, port 18380.
  A paraméterek a `spark/servers/vllm-qwen38-flash/docker-compose.yml`-ből átvéve (a lokális és a
  devi compose md5-je azonos: `51abed25245c824e4f0689403245a937`) — 262 144 ctx, `--max-num-seqs 4`,
  `--gpu-memory-utilization 0.78`, `--enable-prefix-caching`, `--enable-chunked-prefill`,
  `--max-num-batched-tokens 8192`, PIECEWISE cudagraph a 12 splitting oppal, MTP=2,
  `VLLM_QSA_EXACT_TOPK=1`, `--kv-cache-dtype auto`, `--no-enable-flashinfer-autotune`.
  Logból ellenőrizve: `enable_prefix_caching: True`, `Mamba cache mode is set to 'align' … by
  default when prefix caching is enabled`, FLASHINFER_CUTLASS MoE, FlashInfer **0.6.17**.
- **Szonda:** `eszkozok/logprob_szonda.py`, a laptopról WireGuard-on (a spark-dev GPU-ját csak a
  vLLM terheli). Tokenenkénti top-20 logprob signature → teljes hash; a promptépítés bájtra a
  round1 `harness.py` `RENDSZERPROMPT` + `felhasznaloi_uzenet` szerint.
- **Soros kérések**, a szerverlog végig `Running: 1 reqs` — nincs köteg-keveredés.

## 3. Eredmények

| kör | mód | max_tokens | itemek | ismétlés | eredmény |
|---|---|---:|---|---:|---|
| P1 | thinking OFF | 48 | T3-01, T6-02, T10-05, T2-01 | 10 | **3/4 PASS** (T2-01 FAIL) |
| P2 | thinking OFF | 256 | T3-01, T2-01, T1-01, T8-01 | 8 | **4/4 PASS** |
| P3 | **thinking ON** | 512 | T3-01, T2-01, T6-02, T10-05 | 5 | **4/4 PASS** |

- **Melegen (2… n futás) 0 eltérés mind a három körben**, összesen 80 futáson.
- A P3-ban a 24 416 tokenes T10-05 és a 512 tokenes gondolkodó generálás is bitre azonos.
- Nyers adat: `eredmenyek/szonda-A-{48tok,256tok,thinking-512tok}.json`.

### 3.1 Az egyetlen FAIL mechanizmusa — részleges vs. teljes cache-hit

A P1-ben a T2-01 **1. futása** tért el a 2–10-től (azok egymással bitre azonosak), és **mind a 46
token** top-20 listája eltért, miközben a kiválasztott tokenek (a válasz szövege) azonosak voltak.
Tehát nem egy near-tie billent át: a teljes rejtett állapot más volt.

Az ok mérve: a T2-01 és a P1 első itemje, a T3-01 **ugyanazt a `D2.md` dokumentumot** kapja, és a
két prompt **6 982 karakteren (≈2 182 token, a T2-01 promptjának 68 %-a) azonos**. A T2-01 első
futása így egy teljes 1 616-os blokkra már hitet kapott (részleges hit), a 2–10. futás pedig a
teljes promptra (teljes hit) — **két különböző cache-út, két különböző logitvektor**.

⛔⛔ **Ez élesben rendszeresen előálló helyzet**, nem laborműtermék: a KIE-promptok közös
rendszerprompt-prefixe, az azonos dokumentumra adott több kérdés és a chat többfordulós
beszélgetése folyamatosan termel részleges hiteket. Ugyanaz a dokumentum ugyanazzal a kérdéssel más
cache-állapotban más logitokat kap — a szöveg itt nem változott, de a következő near-tie-nál
átbillenhet. Ez az a hibaosztály, amit upstream a #53798/#54076 páros céloz, és amit a #54173
(független bejelentő, azonos modell és GB10) is prefix cache mellett ír le.

### 3.2 Amit ez a mérés a runbook fő gyanúsítottjáról mond

A vllm#54945 reprodukciója (55 tokenes prompt, `--enforce-eager`, no spec, `--no-enable-prefix-caching`,
`--max-num-seqs 16`) 3 azonos kérésből **3 különböző** logprob-signature-t ad már a 2. tokennél.
A mi konfigunkban ez a mintázat **egyszer sem** jelent meg 92 kérésen. A különbség a shape-ekben van:
a finding 26 szerint a divergencia a MoE **small-M** útján ül, a mi termelési shape-jeink (3–24k
tokenes prefill 8192-es chunkokban, MTP=2 miatt 3 tokenes verify-shape) nem ezek.

⚠️ Ez **nem** cáfolja a #54945-öt: azt mondja, hogy a hiba shape-függő, és a mi üzemi pontunkon
nem aktiválódik. A PR #54948 (`use_fused_finalize=False`) így nálunk nem sürgős — de a mérés
korlátai (lásd lent) miatt nem is zárható ki véglegesen.

## 3.3 F2c — köteg-invariancia: a soros determinizmus élesre NEM fordítható át

`eszkozok/parhuzamos_szonda.py`, cél-item T3-01, 128 token, thinking OFF, minden prompt előre
bemelegítve (hogy az eltérés a kötegre és ne a cache-útra legyen visszavezethető):

| elrendezés | különböző hash | egyezik a soros referenciával |
|---|---:|---|
| soros (REF), 3× | 1 | — (ez a referencia) |
| 2 egyidejű **azonos** kérés, 3 kör | 2 | **0/6** |
| 4 egyidejű **azonos** kérés, 3 kör | 3 | **0/12** |
| vegyes köteg (cél + T6-02 + T10-05 + T1-01), 3 kör | 1 | **0/3** |

- ⛔⛔ **Két bitre azonos, egyszerre beküldött kérés egymástól is eltérő logitokat kap**, és a
  körök között az sem stabil, melyik kapja melyiket (a beérkezési sorrend dönt).
- A hatás **nem véletlenszerű zaj**: adott köteg-alakra determinisztikus (a vegyes köteg 3/3
  azonos), csak más, mint a soros eset. Ez a kernelek batch-invariancia-hiánya — a vLLM ezt nem is
  ígéri, és a mi modellünkön a hivatalos `VLLM_BATCH_INVARIANT` út zárva van (GDN_ATTN, vllm#42960).
- ✅ **A látható válasz mind a 21 futáson azonos** (`tartalom_sha` egységes, 39 token): a
  logit-eltolódás ezen az itemen nem billentette át a greedy argmaxot.

**Következmény:** az `EXACT_TOPK=1` ára (round1: 1,35× prefill) a *soros* bit-determinizmust
vásárolja meg. Élesben, ahol a `night`-slot cronjai és a chat párhuzamosan kérnek, bit-szintű
reprodukálhatóság nincs és nem is lehet — az `EXACT_TOPK` haszna ott az, hogy a round1-ben mért
**érték-szintű** ingadozást (13/50 item, ebből 5-nél a kinyert dátum/összeg is változott)
megszünteti. A kötegelt üzem érték-szintű stabilitása külön mérendő (lásd §5, F2d).

## 4. Mit NEM bizonyít ez a mérés

- **Egyetlen szerverindítás.** A jschmied-post-mortem szabálya (3 start) itt nincs betartva; az
  indítások közti eltérés (JIT, autotune, allokátor) nem mérve.
- **Csak a top-20 logprob.** A 20-on kívüli logitok eltérhetnek.
- **Legfeljebb 512 generált token.** Az éles KIE 16 384-es kerettel megy.
- ⛔ **Csak `Running: 1 reqs` mellett.** Élesben a `night`-slot cronjai párhuzamosan kérnek
  (`--max-num-seqs 4`), a kernelek pedig **nem batch-invariánsak** → a köteg-összetétel változása
  önmagában más logitokat ad. Ez a mérés erről semmit nem mond, és ez a legvalószínűbb élő
  eltérés-forrás.
- **A hideg út saját reprodukálhatósága nyitott:** két azonos, egyaránt teljesen hideg futást
  csak szerver-újraindítással (vagy PC=0-val) lehet összevetni.

## 5. Következő lépések (döntésre)

| # | mérés | mit dönt el |
|---|---|---|
| F2a | ugyanez a szonda `--no-enable-prefix-caching` szerveren | a hideg út saját reprodukálhatósága + a PC-gépezet hatása egy változóban |
| F2b | 3 külön szerverindítás, azonos szonda | a start-ok közti stabilitás (a „3 start" szabály) |
| ~~F2c~~ | ~~párhuzamos kérések~~ | **KÉSZ, ld. §3.3: a bit-determinizmus kötegben elvész, a szöveg stabil maradt** |
| F2d | a round1 13 instabil itemje **kötegelt** üzemben, 5 kör, szöveg- és érték-szintű összevetés | a köteg-hatás átbillenti-e a kinyert dátumot/összeget — ez az éles KIE-kockázat valódi mértéke |
| F3 | PR #55122 det-kernel standalone build + `VLLM_QSA_DET_TOPK=1` A/B a mi `EXACT_TOPK=1`-ünkkel | visszanyerhető-e a round1-ben mért **1,35× prefill-ár** (2 350 → 1 756 tok/s) azonos determinizmus mellett; a PR becslése +1,8 % TTFT |
| F4 | ha F3 zöld: magyar KIE fő suite 50×3 | a 98/100 pontszám nem romlik-e |

Az F3-hoz minden előfeltétel megvan az image-ünkben: a patch-pontok ott vannak, ahol a
`tools/determinism/*` toolok várják (`flashinfer_cutlass_moe.py:390`, `qsa.py:812`), és a
konténerben van `nvcc` + torch 2.13/cu130 stable shim, tehát a kernel a helyszínen fordítható.

## 6. Melléklelet — vllm#54173 az éles rendszeren

A #54173 (CUBLAS_STATUS_INTERNAL_ERROR / illegal memory access prefix caching mellett, azonos
modell és GB10) a mi éles konfigurációnkat írja le. Az éles `night`-slot 08-31 óta tartó
konténer-logjában (14 142 sor) **0 találat** a crash-mintázatokra — eddig nem érint minket.
