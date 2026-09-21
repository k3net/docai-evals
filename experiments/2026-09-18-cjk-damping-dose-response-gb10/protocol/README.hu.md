# CJK-csillapítás — dózis-hatás mérés

**Mennyit szabad elvenni egy tokenosztálytól?** Dózis-hatás mérés a CJK-csillapításra,
`Qwen3.6-35B-A3B-FP8`-on. A cél egy mért, publikált HF-modell és egy hivatkozható
tanulmány.

⛔ **A protokoll a [00-runbook.md](00-runbook.md)**, és az a mérés ELŐTT készült: a
hipotézisek, az elsődleges végpont, a statisztikai eljárás és a publikálási döntési
szabály előre rögzítve. Ami menet közben változik, az **dátummal és okkal** a runbook
Naplójába kerül. A mért leletek és az elrontott dolgok a
[jegyzokonyv/F0-naplo.md](jegyzokonyv/F0-naplo.md)-ban, a pilot menetéből fakadó
protokollváltozások a [jegyzokonyv/F1-naplo.md](jegyzokonyv/F1-naplo.md)-ban vannak.

## Hol mi van

| | |
|---|---|
| [00-runbook.md](00-runbook.md) | **a protokoll** — hipotézisek, karok, kapuk, döntési szabály, napló |
| [jegyzokonyv/F0-naplo.md](jegyzokonyv/F0-naplo.md) | az F0 mért leletei, beleértve az elrontott dolgokat |
| [jegyzokonyv/F1-naplo.md](jegyzokonyv/F1-naplo.md) | az F1 pilot — a megbukott párhuzamosság-kapu, a példány-módok, a nullműszer-lelet, az F2 futó naplója |
| [jegyzokonyv/F2-naplo.md](jegyzokonyv/F2-naplo.md) | **a kilenc kar egy táblában**, Kapu F2, H1–H6 verdikt, F3-terv |
| [eszkozok/](eszkozok/) | a mérőeszközök (lent részletezve) |
| [kinai-proba/](kinai-proba/) | a kínai képesség-próba: 36 item + futtató |
| [eredmenyek/](eredmenyek/) | minden kar minden műszere, eredménylap, F3, igazolások |
| [hf-release/](hf-release/) | a model card forrása (a csomag a mérőgépen épül: `eszkozok/hf_csomag.sh`) |
| [publikacio/](publikacio/) | a docai-evals experiment három dokumentumának forrása (`eszkozok/docai_evals_csomag.sh` másolja) |
| [article/](article/) | a blogcikk terve és ábrái — **a mérés lezárásáig nem publikálható** |
| `../magyar-kie-eval/` | a Csapda Korpusz; a bővítés: `src/gen_csapda.py`, `corpus/C*.md`, `gt/items-150.jsonl` |

Futó mérés: **measurement-host**, `~/experiments/2026-09-18-cjk-csillapitas/`.
Motor-image: `vllm-openai:beta-mirror-dev328` (vLLM `0.19.1rc1.dev328+g18013df6a`,
alap-image digest `sha256:10c361c5…`). **Címke szerinti image-hivatkozás tilos** —
a runbook §9 szerint a motorbuild önmagában többet mozdít, mint a folt.

## Az eszközök

### A beavatkozás
| | |
|---|---|
| `unihan_egyszerusitett.py` | a „csak-egyszerűsített" Han-karakterek listája a Unihanból (verziózott, a csomag része) |
| `celtokenek.py` | céltokenek KÉT maszkkal: `nyers` (a round5-é, 55 424 token) és `finomitott` (koreai mintájú, 54 939) |
| `mu_h_becslo.py` | a μ_h irányvektor magyar szövegen, vLLM `token_embed` poolinggal + tanári kényszerítéses önteszt |
| `patch_lm_head.py` | egytenzoros folt KÉT formában: `szorzas` (S) és `irany` (−α·μ_h/‖μ_h‖²) |
| `ellenoriz_kar.py` | a kar igazolása három szinten: fájl / tenzor / sor (507 ellenőrzés) |
| `karok_epit.sh` | mind a nyolc kar előállítása és igazolása |

### A mérés
| | |
|---|---|
| `kar_futtat.sh` | egy kar végigmérése: csapda + kínai + KIE + contract + Han-kockázat + eseménypróba |
| `f1_vezenylo.sh` | az F1 pilot (K0, S05, A200) + a soros determinizmus igazolása, **utána szándékosan megáll** |
| `f2_vezenylo.sh` | a maradék hat kar — **csak a Kapu F1 kiértékelése után** |
| `kapu_f0.py` | a Kapu F0 két feltételének formális kiértékelése |
| `han_kockazat.py` | pozíciónkénti Han-kockázat a felvett logprobokból, válaszonkénti bootstrap CI-vel |
| `kinai-proba/kinai_proba.py` | a kínai képesség-próba futtatója |

### A kiértékelés
| | |
|---|---|
| `statisztika.py` | a runbook §5 eljárásai, csak `math`-tal, öntesztelve (Wilson, Poisson, McNemar, Holm, párosított CI) |
| `csapda_riport.py` | az elsődleges költség-végpont: item-szintű pass-rate, rétegzett, párosított |
| `kinai_riport.py` | a model card kötelező kínai száma |
| `elojel_csapda.py` | az előjel-csapda mérése valószínűségben, nyersen és a mintavételezési lánc után |
| `parhuzam_ellenoriz.py` | befolyásolja-e a kötegméret a greedy kimenetet? — **igen, és emiatt állt át a mérés sorosra** |
| `determinizmus_ellenoriz.py` | az F1 kapuja: bájtra reprodukálható-e a soros mérés a teljes korpuszon? |
| `eredmenylap.py` | a runbook §10 eredménylapja — **minden** lefuttatott karral |

## Hol tartunk (2026-09-19)

| fázis | állapot |
|---|---|
| **F0 — előkészítés** | ✅ kész |
| **Kapu F0** | ✅ a soros `K0` **bájtra** a round5 (49/50, 0 diszkordáns); C9 osztály 7/11 |
| **F1 — pilot (K0, S05, A200)** | ✅ kész (2026-09-18 23:57), sorosan |
| **Kapu F1** | ✅ **teljesül** mind a három feltételen |
| ⭐ lelet | a magyar csapda greedy alatt **nullműszer** (K0 ≡ S05 ≡ A200 bájtra); a költség a **kínain**: 100 % → 2,8 % (S05) → 0 % (A200) |
| ⛔ lelet | a kiszolgáló-példány ±2–5 itemet billent (4 példány, 3 mintázat); a `VLLM_BATCH_INVARIANT`+Triton út reprodukálható, de motorváltás — **döntés: F2 a sima motoron** |
| **F2 — a maradék hat kar** | ✅ **kész** (2026-09-19 13:00–22:35) — [jegyzokonyv/F2-naplo.md](jegyzokonyv/F2-naplo.md) |
| **Kapu F2** | ✅ **`S* = S07`**: exact 0 kockázat + ép kínai (36/36); minden más folt vagy a kínait öli (S ≤ 0,5, A050, A200), vagy a kockázatot nem nullázza (S05F, A200F) |
| ⛔ lelet (felhasználó) | a Han-kockázat „exact nulla” a **nyers** top-20-ra bizonyított; a vLLM a büntetéseket a top-k **előtt** alkalmazza, a nyers 21+. helyezett bejuthat — a tényleges tartón külön igazolandó |
| **F3 A) mérés-igazolás** | ✅ (2026-09-20) a tényleges tartón `S07 @ 0,6` és `@ 0,3` **exact 0**, `@ 0,9` 0,45/M; `K0` **~10× alulbecsült** volt (73/M @ 0,6; **392/M + 4 valódi Han @ 0,3** — a tűzoltás nem véd) — [jegyzokonyv/F3-naplo.md](jegyzokonyv/F3-naplo.md) |
| **F3 B) `S07` megerősítés** | ✅ 3 friss példány, 15 seed, 3 profil, párhuzamos köteg, 150 irat: **0 Han bárhol**; csapda prod-profilon `S07` = `K0` (146/150), pontban jobb |
| **F3 C) S08 / S09 / S06** | ✅ (13:02) az ablak két széle: kínai **S ≥ 0,7-ig ép**, 0,6-on 55,6 %; Han exact 0 a prod-úton **S ≤ 0,8-ig**, S09 szivárog → **`S* = S07`** marad, a költség-lépcső szélén |
| prod-próba `S07 @ 0,6`-tal | ✅ **javasolható** — a döntési szabály mindhárom feltétele teljesül; a felhasználó dönt |
| ⛔ **önellenőrzés a lezárás után** | ✅ (2026-09-20) a táblák számai független újraszámolással egyeznek; négy javítás ([F3-naplo.md](jegyzokonyv/F3-naplo.md) §6): a számító kihagyta a végső válasz nélküli rekordokat (`S07` így is 0 Han ~1,09 M pozíción; a `K0`-nál egy **6 593 Han-tokenes** elszabadulás maradt rejtve), az újrapróbálkozási profil folttól függetlenül degenerál (2/15), a 0,45/M alsó korlát, a „~10×" pontbecslés-hányados |
| **F4 — HF-csomag, publikus mérési könyvtár, tanulmány, cikk** | ✅ **kész** (2026-09-20) — `hf-release/`, `docai-evals/experiments/2026-09-18-cjk-damping-dose-response-gb10/`, `/kutatas/cjk-csillapitas`, blog HU+EN; **a feltöltés és a commitok a felhasználóé** |

**Ami a felhasználóé:** (a) ✅ a HF-feltöltés kész (2026-09-21): <https://huggingface.co/k3dani/Qwen3.6-35B-A3B-FP8-cjk-damped-S07> — publikus, 69 fájl, az átírt shard sha256-a a HF oldalán egyezik a build-rekorddal.
(b) commit a `docai-evals` (új experiment-könyvtár + két index-sor) és a `docai_web` (controller, route, 3 nézet,
2 index, 6 kép) repóban, utána `php artisan sitemap:generate`; (c) a prod-próba `S07 @ 0,6`.

A mérés lezárult; a measurement-hosten nem fut semmi. A HF-csomag: `~/experiments/2026-09-18-cjk-csillapitas/hf-release/`.

## Ami eldőlt, és ami még nem

A részletek a jegyzőkönyvben; a három legfontosabb:

1. ⭐ **Az előjel-csapda aktív a szorzásos formánál.** A nyers eloszlásban a folt
   **megnöveli** a Han-tömeget (t=1,0: 10,5 % → 16,1 % S=0,5-nél), mert a célzott sorok
   96,4 %-ának negatív a logitja. A prod mintavételezés (`top_k=20`) levágja a farkat,
   ezért a termelési úton mégis nulla — de **a folt hatásossága a mintavételezési
   profiltól függ**, és ez a model cardba kötelező. Az irány-alapú csere ezt a
   tulajdonságot nem hordozza: nála a nyers tömeg is **pontosan nulla**.
2. **A μ_h nem a próbahalmaz műterméke:** két független, 30-itemes halmaz iránya
   `cos = 0,8893`.
3. **A Csapda Korpusz 150 itemre bővült**, 9 generált irattal és 385 konzisztencia-
   ellenőrzéssel. A kontroll rajta **144/150 = 96,0 %**; a legnehezebb osztály a C9
   („eldönthetetlen állításra határozott ítélet"), 7/11 — ez a `T7-08`-ból absztrahált
   hibaosztály, és az új iraton is él.
4. ⛔ **A kötegméret átbillenti a greedy kimenetet.** A párhuzamosított mérés a `T7-08`
   itemen a PASS/FAIL-t is megfordítja a sorossal szemben — akkora hatás, mint amit mérni
   akarunk, tehát **konfundál**. A mérőpad ezért sorosra állt, és mivel a soros dekódolás
   bitre reprodukálható, ez **nem került többe**: 450 kérés/kar helyett 150, ~108 perc
   helyett ~46. ⛔ Utólag: a soros mérés egy példányon belül bájtra reprodukálható, de
   **friss példányok között nem** (2–5 item / 150, diszkrét numerika-módok) — a zaj tehát
   nem csak a párhuzamosításé volt; ld. [F1-naplo.md](jegyzokonyv/F1-naplo.md) §8.

Ami azóta eldőlt: a dózis-hatás két lépcső, `S* = S07`, a H1–H6 verdiktje az
[F2-naplo.md](jegyzokonyv/F2-naplo.md) §3-ban, a prod-próba javasolható. Ami nyitva maradt:
az `S08` a tényleges tartón, egy pont S = 0,6 és 0,7 között, a kanji/hanja próba, és az
újrapróbálkozási profil (`t=0,9 / top_p=1,0`) degenerációja — ez utóbbi nem a folt kérdése.
