# Runbook: döntési LoRA a kiszolgált chat-modellen

**Kalibrált, típusos döntés egy változatlan, FP8-ban kiszolgált hibrid MoE chat-modell
ugyanazon vLLM-példányán — első feladat: a BA-bíráló, szintetikus adaton.**

- Verzió: **v2** (2026-10-03, házon belüli terv-review után) · státusz: **terv, mérés még nem futott**
- Gép: measurement-host (<remote-host>), a kutatásra 100%-ban szabad · minden hosszú futás
  **leválasztva** (`setsid nohup`), STATUS-fájllal és újraindulás utáni folytatással; a
  laptop a futás alatt altatható; az eredmények ebbe a mappába jönnek vissza (`rsync`)
- Alanymodell: `Qwen/Qwen3.6-35B-A3B-FP8` (snapshot `95a723d0…`), **MTP nélkül** —
  szándékosan: a kör célja kutatás és tanulás, nem azonnal bevezethető prod-megoldás
- Háttér: [compass_artifact_…md](compass_artifact_wf-26f3c25c-fe45-5fbe-886f-91f31df5a350_text_markdown.md)
  (irodalmi áttekintés, 2026-10)
- Végtermékek: (1) publikálható szintetikus magyar döntési adatkészlet, (2) HF döntési
  adapter, ha a 10. pont szabálya engedi, (3) tanulmány, (4) belső jegyzet a docai-0122
  C fokához (LLM-bíráló)

> ⚠️ Ez a runbook **a mérés előtt** rögzíti a hipotéziseket, az elsődleges végpontot, a
> statisztikai eljárást és a publikálási szabályt. Ha menet közben bármelyik változik, a
> változás **dátummal és okkal** a Naplóba kerül, nem csendben.

---

## 0. Kiindulás

### Amit tudunk

| megállapítás | erősség | forrás |
|---|---|---|
| tréning nélküli logit-kiolvasás + kalibráció más modelleken használható döntést ad | irodalom, nálunk nem mért | compass-anyag (a) |
| 2026-05-ben a vLLM `--enable-lora` Qwen3.6-FP8-on **bitre azonos kimenetet** adott adapterrel és nélküle | mért, régi build | [`lora_business_law`](<internal: lora_business_law>) |
| a v0.30.0 kódja szerint a LoRA **modulonként** aktiválódik, globális „MoE miatti” kihagyás nincs; a hiányzó modul csak DEBUG-szinten látszik (`vllm/lora/model_manager.py:339-362`). A 2026-05-ös tünet **legvalószínűbb oka az adapter-kulcsprefix**: a PEFT `base_model.model.model.layers.…`-t ment, a vLLM leképezője csak a `model.language_model.` → `language_model.model.` prefixet ismeri (`model_executor/models/qwen3_vl.py:1821-1827`) | kódolvasás (2026-10-03), nem mért | K0c igazolja |
| **v0.30.0-n a batch-invariáns (BI) mód GDN-es modellen nem indul** (`v1/attention/selector.py:235-239`); a 2026-09-es „BI+TRITON_ATTN reprodukálható” mérés a 0.19.1rc1-en készült | kódolvasás | K0a rögzíti |
| a vLLM példányok közt a kimenet billen (CJK: hosszú generálásokon ±2–5/150 PASS/FAIL, 0.19.1rc1, MTP-vel); **példányon belül, soros kéréssel bitre stabil** | mért, más buildon | memória: vllm-peldany-nemdeterminizmus-spark |
| Qwen3.6: 40 réteg, `full_attention_interval=4` → 10 attention + 30 GatedDeltaNet. Modulok: `self_attn.{q,k,v,o}_proj`; `linear_attn.in_proj_qkv`/`in_proj_z` (FP8), `in_proj_a`/`in_proj_b` (BF16), `out_proj`; `mlp.shared_expert.{gate,up,down}_proj`; routed expertek **expertenként külön kulcson**. A vLLM a GDN-vetítőket `in_proj_qkvz`/`in_proj_ba` csomagba olvasztja, a LoRA ezt kezeli | config + kód | `config.json`, `qwen3_5.py:481-484` |
| a HF-osztály (transformers 5.6) a routed experteket 3D paraméterként várja, és a `qwen3_5_moe_text` típushoz nincs expert-összefésülő konverter → **az FP8 checkpoint expertjei nem töltődnek be, véletlen inicializálással maradnak, csak figyelmeztetéssel** | kódolvasás | K0f kemény kapu |
| GB10-tréning: gradient checkpointing nélkül **a node indul újra**; a **`lora-train:3`** image `causal-conv1d`-je az első lépésnél SIGSEGV → **`lora-train:2`** kell (torch-fallback, lassabb, stabil); nincs `flash_attn`; a TRL completion-maszk **2 tokennel elcsúszik** | mért | [`LoRA_Arany-János`](../../2026-08-14-lora-vs-reranker-hu-verse/README.md) 6. fej., `~/lora-study/src/run_mag.sh:18-22` |
| a 35B LoRA-tréning eddigi egyetlen GB10-mérése ~190 token/s (1,85 M token / 9844 s) | mért | `lora_business_law` eredmények |
| a címkék egytokenesek: `A`…`J` = 32–41, `X` = 55; a kikapcsolt-thinking előtag tokenizálása nem változik a címke előtt. **De** a mondatkezdő névelő „A” azonos az `A` címkével, és az „Egyik” = `E|gy|ik` → az „egyik sem” szándék az `E` címkére folyhat | tokenizer-audit | K0b méri |
| a chat template alapból **bekapcsolt** thinkinget ad; `enable_thinking=False` minden hívásnál kötelező | `chat_template.jinja:147-153` | — |
| vLLM v0.30.0 API: a `/v1/chat/completions/render` csak `--enable-scale-out`-tal él; a `logprob_token_ids` (≤128 id) pontosan a megadott tokenek logprobját adja; a prefix caching **alapból be** van kapcsolva; CUDA-n a Model Runner V2 az alapértelmezett | kód | `scale_out/factories.py:73-83`, `sampling_params.py:296`, `config/cache.py:130` |
| measurement-host üres, 121 GB; képek: `vllm/vllm-openai:v0.30.0` (`sha256:8a69ffad…`), `lora-train:2/3`, `qwen38-flash-dgx:v030-bb661c4`; HF-cache: Qwen3.6-FP8, Qwen3.8-Flash-Next-NVFP4, `bge-m3`; **családban független LLM egyetlen: `nvidia/Llama-3.3-70B-Instruct-FP8`** (`~/hf-cache-llama33`; csak a `boot-llama33.sh` v2 receptjével bootol, a v1 megbénította a gépet) | mért, 2026-10-03 | `ssh measurement-host` |
| a generátor (Qwen3.8-Flash) **ugyanaz a szótár és 3:1 hibrid felépítés**, mint az alanyé — „generátor ≠ alany”, de egy családon belül | config | — |
| prod jelöltgenerálás: OpenSearch `multi_match` `best_fields` (`aliases^3`, `name^2`, `category`), `fuzziness: AUTO`, `hu_item_text` analyzer (standard tokenizer, lowercase, magyar stop, asciifolding `preserve_original`, **stemmelés nélkül**) + Qdrant `bge-m3` a „név · aliasok · kategória” szövegen; **5+5 jelölt, két külön listában** | kód | `<product-code> `; `<product-code>` |

**A <tenant> BA-adat (2026-10-03, lokális tükör, aggregátum):**
- 4109 cikk, ebből 158 catch-all. 72 kategória két szinten: 11 gyökér + 61 alkategória.
- A bejövő sorok közül 101 123 tételsor (`item`). Mellettük 5048 betét, 1946 kedvezmény, 831 egyéb, 157 kerekítés, 32 szállítás.
- A tételszöveg átlagosan ~33 karakter.
- **Emberi besorolási döntés gyakorlatilag nincs:**
  - a besorolás `auto` 100 306 (ebből `alias_global` 99 206, `partner_code` 1100), `manual` 3;
  - besorolatlan 8828 sor, ebből tételsor 814;
  - az aliasok forrása 15 671 `import`, 2 `manual`.

A meglévő címkék tehát determinisztikus eredetűek, és a könnyű eseteket fedik.

### Amit nem tudunk, és ezért van ez a kör

1. Mennyit ér nálunk, magyar BA-adaton a **tréning nélküli** kalibrált logit-kiolvasás?
2. Hoz-e ehhez képest mérhető javulást egy **kis döntési LoRA**, és általánosít-e új
   szállítói írásmódra és új kategóriára, vagy csak a katalógust tanulja meg?
3. **Kiszolgálható-e** a LoRA ugyanazon a vLLM-példányon, ahol a változatlan chat-modell
   fut (v0.30.0, hibrid MoE, FP8)?
4. Elég-e a rejtett állapotra tett olcsó probe LoRA nélkül?

### Ami a publikálhatóságot eldönti

- **A <tenant>-adat ügyféladat.** A laptopot csak **mintázat-típusokból és eloszlásokból álló
  profil** hagyja el. Nyers szöveg, n-gram, név, kód és egyedi ár nem.
- **Minden publikált adat generált.** A címke **konstrukcióból** adódik: a sor egy ismert
  cikkből készül.
- **A tenant neve sehol nem szerepel.** Hogy a profil ilyen másodlagos felhasználása
  belefér-e az ügyfélszerződésbe, azt F0-ban **írásban** rögzíteni kell.
- **Licencek, F0-kapu:**
  - a Qwen-alap,
  - a harmadik féltől származó generátor-kvant (`RadixArk/Qwen3.8-Flash-Next-NVFP4`),
  - a Llama 3.3 Community License,
  - a külső bíráló API-feltételei.

  Mindegyiknél azt kell rögzíteni, mire használható a kimenet tréning- és publikációs
  célra.

---

## 1. Kutatási kérdés

**Tanítható-e egy kis LoRA úgy, hogy egy változatlan, FP8-ban kiszolgált hibrid MoE
chat-modell ugyanazon vLLM-példányán kalibrált, típusos döntést adjon? És mennyit hoz ez
a tréning nélküli, kalibrált logit-kiolvasáshoz képest?**

A BA-bíráló ennek az első, konkrét esete. A kérdésforma szándékosan általános (választás
opciók közül + „egyik sem”), hogy egy későbbi, általános célú döntési adapter ugyanezt a
felületet használja. Az állítások a **szintetikus feladatra** szólnak, és **relatívak**
(kar a kar ellen). Valós adatra csak a docai-0122 arany-halmaza ad majd igazolást.

---

## 2. Definíciók — a saját mérőszámok, első használat előtt

- **Döntési pozíció:** az asszisztens-előtag (`enable_thinking=False`, azaz
  `<think>\n\n</think>\n\n`) utáni első generált pozíció.
- **Címke-token:** az opciók betűjele (`A`…`J`, „egyik sem” = `X`).
- **Szűkített softmax:** a jelen lévő opciók címke-tokenjeinek logprobjaira vett softmax. Ez
  a döntés eloszlása, a **bizalom** a maximuma.
- **Címketömeg:** a teljes szótárra normált valószínűség-tömeg a jelen lévő címkéken. Ez
  diagnosztika: ha alacsony, a modell nem betűvel akar válaszolni.
- **Besorolás:** nem-`X` döntés, amelynek bizalma ≥ τ. Az `X` és a küszöb alatti döntés
  **tartózkodás**: prodban az ilyen sor gyűjtőcikkre vagy emberhez megy, nem
  automatikus besorolás.
- **τ-szabály (előre rögzítve):** τ a val-on (val-belső + val-szállító együtt) az a
  legkisebb küszöb, amely fölött a besorolások precizitásának egyoldali 95%-os
  Clopper–Pearson alsó korlátja ≥ 95%. A teszten τ változatlan.
- **Besorolási lefedettség@95** *(elsődleges végpont)*: a réteg itemjeinek az a hányada,
  amely τ fölötti besorolást kap. Mellé mindig jelentjük a besorolások **elért teszt-
  precizitását** is. **Precizitás-bukás:** ha egy kar teszt-precizitása egy rétegen
  < 93%, akkor az a kar azon a rétegen bukik, és a lefedettsége nem számít győzelemnek.
- **Besorolási lefedettség@90** *(előre rögzített másodlagos végpont; user-döntés,
  2026-10-05)*: ugyanez 90%-os célprecizitással és saját τ90-nel (CP-alsó ≥ 90%).
  Precizitás-bukás, ha a teszt-precizitás < 88%. Azért került be, mert a pilot alapján a
  @95 az alapvonalakra ~0, és egy 0-ról induló elsődleges végpont mellett kell egy
  felbontóbb, előre rögzített mérce.
- **AURC** *(küszöbmentes; a H1-ben társ-elsődleges, user-döntés 2026-10-05)*: a kockázat–lefedettség görbe alatti terület
  (kockázat = a besorolások hibaaránya).
- **Döntési lefedettség@95** *(másodlagos)*: ugyanez, de az `X` döntést is automatikusnak
  számítja.
- **X-precizitás / X-fedés:** az `X` címke precizitása és fedése.
- **ECE:** expected calibration error, 15 **egyenlő tömegű** bin, top-címke.
- **Pozíció-billenés:** a jelöltsorrend 4 permutációja között a döntés megváltozásának
  aránya. A diagnosztikai részhalmazban az `X` is mozog.
- **Példány-billenés:** friss vLLM-példányok közt a top-címke eltérésének aránya. Mellette
  jelentjük az elkülönülő numerika-módok számát.
- **Kétértelmű-átlépés:** a kétértelmű réteg itemjeinek az a hányada, amely τ fölötti
  besorolást kap (itt az **alacsony** érték a jó).
- **Érték-súlyozott lefedettség:** a besorolási lefedettség a sor (szintetikus) nettó
  értékével súlyozva, az értéket a 99. percentilisnél winsorizálva.

---

## 3. Hipotézisek — előre kimondva, cáfolati kritériummal

A karokat **mindig motoron belül** hasonlítjuk össze (vLLM a vLLM-mel, HF a HF-fel).

### H1 — A döntési LoRA veri a kalibrált logitot *(elsődleges)*
**Két társ-elsődleges végpont (user-döntés, 2026-10-05, az MDE-számítás után, L3-eredmény
előtt):**
- (a) L3 > L1★ a besorolási lefedettség@95-ben;
- (b) L3 < L1★ az AURC-ben,

mindkettő a teljes teszten. **Holm-korrekció** (családi α = 0,05). A kisebbik bootstrap
p-értékű végpont p ≤ 0,025 mellett szignifikáns. Ha az, a másik p ≤ 0,05 mellett az. **A H1
teljesül, ha legalább az egyik szignifikáns az L3 javára.**

*Miért:* a @95 MDE-je ~11–12 pont, mert a szórás >90%-a a val-on választott τ-ból jön. Az
AURC küszöbmentes, MDE-je ~0,004–0,005 (Napló, MDE).

**Másodlagos:** a besorolási lefedettség@90, ugyanazzal a bootstrappal, ugyanazokon az
újramintákon. A jelentésben mindig szerepel.

- Motor: vLLM, ha a K0c átment, különben HF.
- A CI-t és a kétoldali bootstrap p-értéket hierarchikus, klaszterezett bootstrap adja, a
  val-küszöb újraválasztásával (ld. 8. pont).

**Cáfolat végpontonként**, bármelyik elég:
- a Holm-korrigált küszöbön nem szignifikáns, vagy az L1★ javára az;
- (@95-nél) az L3 precizitás-bukott a teljes teszten;
- bármelyik seed pontbecslése ≤ L1★ (@95), illetve ≥ L1★ (AURC).

Ha mindkét végpont cáfolt, a H1 cáfolt.

### H2 — A javulás általánosít *(elsődleges, háromértékű)*
Külön a T-szállító és a T-kategória rétegen (ez utóbbin a „közeli” és a „távoli” gyökér
együtt; külön is jelentve):

- CI alsó határa > 0 → **általánosít**;
- CI felső határa < 2 százalékpont → **nem általánosít**;
- egyébként → **nem eldönthető**.

A rétegenkénti MDE-t (minimálisan kimutatható hatás) az F1 végén, a pilot varianciából
számoljuk, és a Naplóba írjuk **az F3 előtt**.

### H3 — Ugyanazon a példányon kiszolgálható *(a „közös gerinc” állítás)*
Négy feltétel, mindnek teljesülnie kell:

- **(a) Aktiválás:** a K0c-ben minden célmodul-csoport aktiválódik. A DEBUG-logban a
  „Successfully loaded LoRA weights” sorok száma egyezik a várt modulszámmal, és
  csoportonként (csak attention / csak GDN / csak shared expert) a logitok mérhetően
  elmozdulnak.
- **(b) A LoRA-hatás egyezése:** a címke-logitok elmozdulása (L3 − L0) a HF-ben és a vLLM-ben
  korrelál, Pearson r ≥ 0,9.
- **(c) Egyezés a motorok közt:** [L3 HF↔vLLM top-címke egyezés] − [L0 HF↔vLLM egyezés]
  egyoldali 95%-os alsó korlátja > −2 százalékpont.
- **(d) A LoRA nélküli kérések nem sérülnek:** egy `--enable-lora`-s példányon a LoRA-t nem
  kérő kérések top-címke egyezése egy LoRA nélküli példánnyal ≥ (a LoRA nélküli friss
  példányok egymás közti egyezése) − 1 százalékpont.

Bitazonosságot **nem** követelünk: az `--enable-lora` a kernelutat is megváltoztathatja,
és a példányzaj külön forrás.

**Cáfolat:** bármelyik feltétel bukik.

### H4 — Az olcsó probe is ér valamit
L2a > L1★ a HF-motoron, a besorolási lefedettség@95-ben.
**Cáfolat:** a CI alsó határa ≤ 0.

### H5 — Jobb kalibráció
L3 ECE < L1★ ECE, ugyanazon a motoron.
**Cáfolat:** a különbség CI-jának felső határa ≥ 0.

### H6 — Külön fej *(stretch, elhagyható)*
L4 > L3 a besorolási lefedettség@95-ben. Csak akkor fut, ha az F5 elindul.

**Többszörös tesztelés:**
- H1 és H2 együtt adja a fő állítást; mindkettőnek teljesülnie kell, ezért korrekció nem kell.
- H4 és H5 egy Holm-családot alkot.
- H6 külön, feltáró.

---

## 4. A szintetikus adat — „<tenant> alapon”

### 4.1. Ami a <tenant>ből kimegy, és ami nem

A laptopon, a `<tenant-db>` tükörből egy aggregáló szkript készíti a
`_belso/tenant_profil.json` fájlt. Csak ez megy tovább, és ez is csak a measurement-hostre.

**Ami benne van:**
- gyökér- és alkategóriánkénti cikkarány;
- tételszöveg-hossz hisztogram;
- egységek eloszlása;
- sortípus-arányok;
- kategóriánkénti **kerekített, zajosított** egységár-kvantilisek;
- **mintázat-típusok gyakorisága**: CSUPA NAGYBETŰ, rövidítés-sűrűség, kiszerelés-jelölés,
  kódelőtag, csonkolás.

**Ami nem kerül bele:** szöveg, n-gram, cikknév, alias, szállítónév, belső kód,
partner-cikkkód, egyedi ár.

**A feladatból kimaradó gyökerek:**
- a „Besorolandó” (666 cikk) gyűjtővödör, nem szemantikus kategória;
- az „Értékesítés” a kimenő oldal.

Marad 9 gyökér.

### 4.2. Generálási lánc (measurement-host)

- **Generátor:** `Qwen3.8-Flash-Next-NVFP4`. A mért alany a Qwen3.6, a kettő ugyanabból a
  családból való; ennek kezelése a T-gen réteg (4.4).
- **Struktúra:** minden LLM-hívás **strukturált JSON-t** ad vissza, attribútum-nyommal. Így a
  szűrők nem szövegre, hanem attribútumokra épülnek.

| lépés | mit csinál |
|---|---|
| S1 katalógus | 9 gyökér a <tenant>-arányokkal, ~5 000 kitalált cikk; a két kitartott gyökér külön cikkszámmal (~460–460). **Ár:** a generátor-LLM változatonkénti becsült nettó egységára, a profil q10/3 – q90·3 sávjára csonkolva (a profil kvantilisei egységeket kevernek, a pilotban így lett 103 Ft/kg-os krémes); a testvérek aránya méret^0,85. Kiszerelést tartalmazó névnél az egység nem kg/l. **Két séma:** <br>• *termék*: márka (kitalált), változat, méret, alapegység, **cikk-szintű ár**, így a méretváltozatok ára eltér; <br>• *szolgáltatás/közüzem/ingatlan/jármű*: típus, időszak, helyszín, szerződés-jelleg (a tükörben ezek a 9 gyökér cikkeinek ~22%-a). <br>Gyökerenként **gyűjtőcikk** („Egyéb …”). A termék-gyökerekben a cikkek ≥ 40%-ának van testvére, amely egy attribútumban tér el. **Dedup:** normalizált név. A családon kívüli szemantikus duplikátumokat (ugyanaz a termék más néven, más szórenddel, más nyelven vagy kevesebb részlettel, akár más alkategóriában) nem a katalógusban, hanem az S7-ben kezeljük, LLM-bírálattal (lásd ott). Az eredetileg tervezett `bge-m3` > 0,95-ös szűrő Dani 9 duplikátum-esetéből egyet sem fogott volna meg (Napló, 2026-10-04). |
| S2 szállítók | 48 kitalált szállító, mindegyik 1–3 gyökérre szakosodva, saját **írásmód-profillal**: kis-/nagybetű, rövidítési szint 0–3, kódelőtag, kiszerelés-jelölés, szórend, mezőhossz-csonkolás, elírási ráta. **Névütközés-szűrő:** a lokális partner-törzsek ellen, a laptopon; a generátor utasítása szerint nyilvánvalóan kitalált nevekkel. |
| S3 szállítói megnevezés | (szállító, cikk) páronként egy LLM-hívás: „így írná ez a szállító”. A kimenet a megnevezés **és** a megtartott, átírt vagy elhagyott attribútumok listája. `temperature=0.7`, seed. |
| S4 tételsor | a megnevezésre determinisztikus zaj (kiszerelés-utótag, csonkolás, elírás), plusz mennyiség, egység és egységár a cikk árából. |
| S5 aliasok | a katalógus alias-mezője **csak train-párok** megnevezéseiből épül, ahogy prodban is a korábban besorolt sorokból. **A train-sorok a saját párjukat sem látják aliasként:** a train-párok két foldra oszlanak, és egy train-sor a másik fold aliasaiból épült indexben keres. A val/teszt-sorok a teljes train-alias-készletet látják. A gyűjtőcikkek aliasai a train-beli „új termékek” (X(b)) szövegei, mint prodban a be nem sorolt soroké. |
| S6 jelöltek | saját OpenSearch-konténer a **prod mappingjével és lekérdezésével** (`multi_match` `best_fields`, `aliases^3`, `name^2`, `category` = levélkategória neve, `fuzziness: AUTO`, `active`-szűrő), plusz `bge-m3` (CLS + L2) **pontos kNN** (nem HNSW) a „név · ≤50 alias · kategória” szövegen. 5+5, utána egyesítve és duplikátummentesítve. Ez saját döntés: a prod két listát ad, a bíráló egyesítve kapja. **A gyűjtőcikkek** a visszakeresésben helyet foglalnak, mint prodban, de az opciólistából kikerülnek, és a lista a 6–8. rangú tartalékkal töltődik fel. Gyűjtőcikk soha nem gold: új termékre az `X` a helyes válasz, a gyűjtőre a prod lánca sorol. **A train-itemek visszakeresése a kitartott gyökerek nélküli katalóguson fut.** A jelöltlisták fagyasztott artefaktként tárolódnak. |
| S7 „egyik sem” | **Duplikátum-kizárás** (`duplikatum_llm.py`, F1F): a jelölt párok minden sor valódi cikke × a teljes S6-jelöltlistája, családon kívül, számkompatibilisen, `bge-m3` koszinusz ≥ 0,60 vagy közös szótő mellett. A két nem-Qwen bíráló (Llama-3.3-70B, Mistral Small 4) páronként, mindkét sorrendben dönt: jelölheti-e a két tétel ugyanazt a terméket. Duplikátum, ha bármelyik bíráló sorrendekre átlagolt P(igen) ≥ 0,5. A valódi cikk duplikátuma soha nem opció, a gyűjtőcikkhez hasonlóan tartalékkal pótolva. Ugyanez a kör kiszűri az értelmetlen cikkneveket (mindkét bíráló P(igen) < 0,5): az ilyen valódi cikk sorai kiesnek. **Kalibrációs kapu:** Dani 9 ismert duplikátum-párjából ≥ 7 megfogva. <br>Utána ~25% „egyik sem” splitenként, két fajta: <br>(a) a gold nincs a listán: *természetes* visszakeresési hiba, vagy *kényszerített* kiejtés a következő tartalék-jelölttel pótolva, így a listahossz-eloszlás nem árulkodik; <br>(b) a gold egy katalógusból kihagyott cikk (új termék). A kihagyott cikkek **splitenként diszjunktak**. |
| S8 kétértelműség | **minden** itemre, az `X`-ekre is, az attribútum-nyomból és normalizált egyezésből. Ha a sor nem különbözteti meg a goldot (`X`-nél: egyik jelen lévő jelölttől sem különbözik), az item a **kétértelmű** rétegbe kerül. A teszten nem pontozott, de a kétértelmű-átlépés mérőszámmal jelentett. A train-ben **soft címkével** marad: a gold és a tőle megkülönböztethetetlen jelöltek közt oszlik meg. |

### 4.3. A kérdésforma

Általános, SystemOne-szerű „choice” séma (`task`, `context{…}`, `options[]`,
`none_option`). A BA ennek egy példánya:

```
<|im_start|>system
Döntési modell vagy. Egyetlen betűvel válaszolj: a választott opció betűjével.<|im_end|>
<|im_start|>user
Feladat: melyik cikktörzs-tételhez tartozik a számlasor?
Számlasor: "COLA ZERO 0,5L PET 12/KRT"
Szállító: Délibáb Ital Kft. · Mennyiség: 24 db · Nettó egységár: 289 Ft
Opciók:
A) Kóla Zero 0,5 l PET [Ital › Üdítő]
B) Kóla 0,5 l PET [Ital › Üdítő]
…
X) Egyik sem
<|im_end|>
<|im_start|>assistant
<think>

</think>

```

- **Tokenizálás:** offline, a HF-tokenizerrel (`enable_thinking=False`). A vLLM a token-id-ket
  kapja. A K0b ezt a render-végponttal keresztellenőrzi.
- **Az `X` helye:** a fő designban mindig az utolsó és mindig jelen van. A jelöltek sorrendje
  véletlen (seed), a tréningben epochonként újrakeverve. A val/teszt **10%-ában** az `X` is
  mozog, ez a pozíció-diagnosztika.
- **Címke-ütközés:** az „A” névelő és az „Egyik” → `E` szivárgást a K0b méri, az eldobható
  pilot-adaton. A mérés: címketömeg, `E`-tömeg az `X`-itemeken, kontrollként „Nincs illő”
  `X`-szöveggel, és egy `(` prefill-változat. A választott forma a Naplóba kerül, **F1
  előtt**.

### 4.4. Splitek és rétegek — előre rögzítve

**A split egysége a (szállító, cikk) pár.** Egy pár sorai csak egy splitben szerepelnek.

| réteg | mi van benne | méret (cél) |
|---|---|---|
| train | 24 train-szállító × nem kitartott gyökerek, train-párok (2 sor/pár) | ~8 300 |
| val-belső | látott szállító × látott cikk, **nem látott pár** | ~450 |
| val-szállító | 8 csak-val szállító | ~1 150 |
| **T-belső** | látott szállító × látott cikk, nem látott pár (val-tól diszjunkt) | ~900 |
| **T-szállító** | 16 csak-teszt szállító | ~1 750 |
| **T-kategória** | két kitartott gyökér: **„Élelmiszer – hús, hal”** (*közeli*: rokon élelmiszer-domén) és **„Konyhaüzemi anyag”** (*távoli*), gyökerenként ~460 cikk | ~1 100 + ~850 |
| T-gen *(opcionális)* | ~800 item, **Llama-3.3-mal generálva** — a generátor-stílus érzékenységi próbája | ~800 |
| kétértelmű | S8-ból, minden splitből külön | jelentve, nem pontozva |

- A méretek a pilot után, a `meretezes_szim.py` szimulációjával rögzítve (a generátor valódi
  split-kódja, álcikkekkel). A teszt összesen ~4 600 item; a két H2-réteg (T-szállító,
  T-kategória) ~1 750 és ~1 950. A train a pilot előtti ~16 000-es tervnél kisebb: a K0e
  szerint ~4 óra/epoch, így az F3 karjai egy-egy éjszakába férnek.
- **Szállító/cikk:** cikkenként 1–4 szállító (0,25/0,35/0,25/0,15), és ha egy cikknek ≥ 2
  train-szállítója van, egy párja mindig kitartott (val:T = 1:2). A <tenant>-ben a cikkek 84,5%-a
  egy szállítós; a pár-szintű rétegekhez ez szándékos eltérés.
- Minden tesztrétegben ~25% az „egyik sem”.
- A kitartott gyökerek a train és a val katalógusából is hiányoznak.
- A szállító-hozzárendelés és minden seed F1 előtt rögzül a jegyzőkönyvben.

### 4.5. Nehézség — alanyfüggetlen mércével

A nehézséget **nem** a mért modellhez hangoljuk. A célsávok a szintetikus adatra, az
eldobható pilot-generáláson (seed P, F0) állítandók be, előre rögzítve.

**Rögzítve a pilot után, az F1 előtt (2026-10-03),** a train kivételével minden rétegre:
- a gold a BM25 top-1-en 40–85%-ban (a pilot rétegei: 44–82%);
- a gold testvére a listán: ≥ 40% (pilot: 40–67%);
- a BM25-margó mediánja ≤ 0,40 (pilot: 0,13–0,45).

Az eredeti, pilot előtti sávot (50–75%; ≥ 40%; < 0,15) a pilot a margón minden rétegben
átlépte. A K0b-2 szerint az alany döntési nehézsége szinte teljesen az `X`-en van, a nem-`X`
pontosság a lexikai nehézségtől alig függ (a T-közeliben BM25 top-1 44%, alany 94%). A sávok
ezért sodródásőrök a pilot és a végleges generálás közt, nem nehézségi célértékek.

A végleges split **friss seeddel** készül. Rá nem futtatunk újabb nehezítési kört.

### 4.6. Shortcut-audit (F1, a befagyasztás előtt)

Egy csak metaadatokon tanított osztályozó (listahossz, betűkészlet, a jelöltek
kategória-útjai, a gold-kategóriájú jelölt pozíciója) próbálja megjósolni az `X` / nem-`X`
címkét és a gold pozícióját. **Kapu:** CV AUC ≤ 0,55. Ha nem teljesül, a generálást javítani
kell, és újragenerálunk.

### 4.7. Valószerűség (belső, a laptopon)

2000 valós <tenant>-sor és 2000 szintetikus sor között karakter 3–5-gram logisztikus
kétmintás osztályozó, CV AUC.

- Nem kemény kapu, mert a szintetikus adat mindig megkülönböztethető.
- Ha az AUC > 0,95, a leginkább elkülönítő n-gramokat **csak megnézzük**, és
  **mintázat-típusra absztrahálva** egy kör stílusprofil-javítás jön.
- N-gram soha nem kerül a profilba vagy az adatba.
- A valós sorok nem hagyják el a laptopot.

### 4.8. Címke-átnézés — független modellek, utána Dani

A cél a címkezaj mérése és javítása **szelekciós torzítás nélkül**.

1. **Időzítés.** A 4.5–4.7 iterációk után, a befagyasztás előtt. **A val/teszt ezután
   befagy**, a hash a jegyzőkönyvbe kerül. **Alany ezelőtt nem fut a val/teszten.**
2. **Bírálók.** Legalább kettő, egyik sem Qwen-családú (az alany és a generátor is az):
   - **Llama-3.3-70B-Instruct-FP8** lokálisan;
   - **Mistral Small 4 119B-A6B NVFP4** (`mistralai/Mistral-Small-4-119B-2603-NVFP4`,
     Apache-2.0) lokálisan a measurement-hosten (user-döntés, 2026-10-04; az eredetileg tervezett
     GPT-6 Astra helyett). A chat-integrációból (OpenRouter, `mistral-small-2603`) már van
     vele tapasztalat. Lokálisan logprobot ad, és az adat nem hagyja el a gépet.
     - Indítás: `lib.sh: mistral_start` (v0.30.0, `--tokenizer-mode/--config-format/--load-format mistral`,
       `TRITON_MLA`), kéréseknél `reasoning_effort: none`.
     - Ha a 3 itemes próbán a címketömeg nem elég, verbális bizalommal fut (`f1d_vezenylo.sh`).

   A bírálók **gold nélkül** kapják a feladat-promptot, és választást + bizalmat adnak.
3. **Triage, nem szűrő.** A modellszavazat alapján egyetlen item sem esik ki és nem kap új
   címkét. A bírálói kimenet csak jelöl. A modell-egyet-nem-értés szerinti szűrés a tesztet az
   LLM-eknek könnyű itemekre szűkítené.
4. **Dani mintája** (a populáció a *pontozott*, nem kétértelmű val/teszt itemek) két szintből áll
   (user-döntés, 2026-10-04):
   - (a) **konszenzusos ellentmondás:** minden bíráló ugyanazt a nem-gold címkét adja, mind
     ≥ 0,8 bizalommal. Rétegenként legfeljebb 40, ismert bekerülési valószínűséggel.
   - (b) **minden más item egy arányos véletlen mintából**, ~240, réteg × `X`/nem-`X`
     szerint. A vitatott és a nem vitatott itemek így azonos valószínűséggel kerülnek be.

   Miért két szint? A bírálók erős pozíciós torzítást mutatnak (A: 24–30% vs gold 10%), és
   szinte sosem választanak `X`-et (1–2% vs 25%), így a sima flag főleg bírálói hibát jelöl.
   Ha a flag-poolt a véletlentől külön kvótával mintáznánk, a maradék-zaj korlátja még
   hibátlan átnézéssel is 4% fölött maradna.
   **Becslés** (`atnezes.py osszesit`): cellánként Jeffreys-Beta poszterior; a (b) szint cellái
   egy egyszerű véletlen mintaként, a konszenzusos szint rétegenként. A javítás utáni maradék
   zaj a teszten Monte Carlóval adódik, pont és 95. percentilis. **Zaj = hibás gold VAGY
   kétértelmű:** az át nem nézett kétértelmű itemet a teszt egyetlen golddal pontozná.
   **Újragenerálás után új minta:** a korábbi döntések csak a természetes átfedésre jönnek át
   (azonos kontextus, opcióhalmaz és gold; a betűk opció-id szerint átfordítva). A változatlan
   itemekkel a minta nem bővíthető, mert épp a duplikátum-mentesek, és lefelé torzítanák a
   becslést.
5. **Vakság.** Dani egy egyszerű lokális átnéző felületen dolgozik, és nem látja a goldot, a
   szavazatokat és a minta eredetét. Eltéréskor második kör jön a gold és a generálási nyom
   megmutatásával. A kimenet egyike: *gold hibás* / *én tévedtem* / *kétértelmű*.
6. **Döntés.** A hibás gold javul, vagy a kétértelmű rétegbe kerül; **csendes törlés
   nincs**. A hibát okozó generátor-ok a Naplóba kerül. Ugyanez a protokoll a val-on is lefut.
7. **Jelentés.** Rétegenként:
   - flag-arány;
   - megerősített hibaarány a flaggelt és a véletlen poolban;
   - a reziduális zaj CI-vel.

   Az elsődleges eredmény a **javítatlan** teszten is megjelenik, érzékenységvizsgálatként.
8. **Train.** Legfeljebb a ≥ 2 bíráló által magabiztosan vitatott itemek hagyhatók el,
   dokumentálva. A tesztből soha.

### 4.9. Valós adat — csak belső, nem publikált

- **R-det** *(F4, opcionális)*: ~1000 valós <tenant>-sor, csak **szabály-eredetű,
  ≥ 0,90-es bizalmú** címkével. A kezdő cikktörzs alacsony bizalmú partner-profil tippjei
  kimaradnak.
  - A jelöltek a valós katalóguson készülnek.
  - Könnyű-torzított, ezért csak épségi próba.
  - Kimenete **kizárólag a `_belso/`-be** kerül, az `eredmenyek/`-be soha.
  - A measurement-hostről a futás után törlendő.
- **docai-0122 arany-halmaz** (~150 vak ellenőrzés), amikor elkészül: ez lesz az első
  valódi, emberi címkés valós mérés. Nem ennek a körnek a része.

---

## 5. A létra

| fok | mi ez | motor |
|---|---|---|
| **L0** | nyers szűkített softmax a döntési pozíción | vLLM **és** HF |
| **L1** | L0 + kalibráció, négy kar: <br>(a) temperature scaling; <br>(b) contextual calibration (tartalom nélküli bemenet); <br>(c) **streaming** batch calibration, rögzített sorrendben, a val-on befagyasztott statisztikával; <br>(d) 4-permutációs átlagolás. <br>A val-on legjobb kar = **L1★**. | vLLM és HF |
| **L2a** | **tanult címkesorok:** ridge vagy logisztikus fej a döntési pozíció rejtett állapotán → pozícióosztályok (`A`…`J`, `X`), a hiányzó opciók maszkolva. Lényegében az `lm_head` címkesorainak újratanulása, gerinc-változtatás nélkül. | HF |
| L2b | pointer-probe: opciónkénti pontszám a döntési pozíció és az opció-szakaszok rejtett állapotából (Kev-stílus). Minden token rejtett állapota kell → **csak kutatási**. | HF |
| **L3** | **döntési LoRA**, kiolvasás a fagyasztott `lm_head` címkesoraiból + a val-on illesztett temperature | HF és vLLM |
| L4 | LoRA + külön fej a vLLM-ből visszakapott rejtett állapoton | vLLM, stretch |

Az L2a és az output-head runbook EXP-005-je ([magyar-llm-output-head-kutatasi-runbook.md](../output-head/magyar-llm-output-head-kutatasi-runbook.md))
ugyanazt az infrastruktúrát használja (rejtett állapot-cache, `lm_head`-sorok). Közösen
érdemes építeni.

### Az L3 tréningje

**Bázis — „FP8-hű BF16 checkpoint”, offline konverzióval (K0f).**
- Az FP8 súlyok blokkonként (128×128) BF16-ra dekvantálva.
- A routed expertek a HF 3D elrendezésébe fésülve.
- A kulcskészlet a hivatalos BF16 checkpoint indexével azonos (csak az index-fájl töltendő
  le).

A LoRA így ugyanazokat a súlyértékeket látja, amelyeket a vLLM kiszolgál; csak az
aktiváció-kvantálás marad eltérés. Ez a konverzió a betöltéskori dekvantálás memóriacsúcsát
is kiváltja. Kemény kapu: a betöltés után a `missing_keys` és az `unexpected_keys` üres.
Fallback: a hivatalos BF16 checkpoint (~70 GB), ugyanezzel a kapuval.

**A tréning beállításai:**
- **Image:** `lora-train:2`.
- **Célmodulok, két kar** (a pontos nevek a K0f-ben a betöltött modellből listázva, a
  `visual.*` kizárva):
  - `L3-mix` = `self_attn.{q,k,v,o}_proj` (10 réteg) + `linear_attn.{in_proj_qkv,in_proj_z,in_proj_a,in_proj_b,out_proj}` (30 réteg);
  - `L3-mix+se` = ugyanez + `mlp.shared_expert.{gate,up,down}_proj`.
  - A routed experteken nincs LoRA.
- **Hiperparaméterek:** `r=16`, `α=32`, dropout 0,05, lr 1e-4 (cosine, 3% warmup), 1 epoch,
  bf16, **gradient checkpointing kötelező**, `max_length=1024`, packing **ki**.
- **Veszteség — saját kód, nem TRL SFT:**
  - a döntési pozíció logitjaiból a jelen lévő címkékre szűkített softmax;
  - **CE (ε=0) + 0,5 · Brier**;
  - kétértelmű itemeknél soft céleloszlás.

  A label smoothing ismerten rontja a szelektív osztályozást, ezért csak hangolási opció. A
  pozíciót kézzel indexeljük, egységteszttel (K0e).
- **Adapter-export:** a kulcsok átnevezése `base_model.model.model.language_model.layers.…`
  alakra. A K0c igazolja, hogy a vLLM minden modult betölt.
- Checkpoint 200 lépésenként, folytatás újraindulás után (7. pont).

**Hangolási keret — előre, szimmetrikusan:**
- az L1 a négy rögzített kalibrációs kart kapja;
- az L3 a két pilot-kart, plusz **egy** hangolási kört legfeljebb 3 konfiggal (lr, ε ∈ {0;
  0,05}, epoch ∈ {1; 2}).

A hangolási kör **a pilot eredményétől függetlenül** lefut, a választás a val-on történik.

**Seedek:**
- a győztes kar 3 seeddel fut;
- a publikált adapter a **val-medián** seed;
- H1-hez mindhárom seed kell (3. pont).

**Fake-quant kar (a K0d 90–95%-os sávja miatt, ld. 9. pont):** a tréning forwardjába FP8
per-token-group aktiváció-fake-quant kerül (`fakequant.py`), abban a változatban, amelyet a
K0d-2 a pilot-itemeken kiválasztott: **`fp32`** (minden FP8-modul előtt fp32-skálás
tokenenkénti csoportos kvantálás). Az F3 pilotjában ez egy harmadik kar: `L3-mix`
fake-quanttal. Ha a val-on, vLLM-ben legalább olyan jó, mint fake-quant nélkül, a
megerősítő seedek is fake-quanttal futnak.

A K0d-2 szerint a fake-quant hatása kicsi: +0,7 pont a zajon belül, a HF saját
expert-implementációinak egymás közti eltérése (eager vs grouped_mm: 96,3%) ugyanekkora
nagyságrendű. A fake-quant expert-útja eager, a kiolvasásban ~3× lassabb. Az F3 előtt egy
smoke méri a tréning időköltségét. Ha egy epoch > 12 óra, a kar csak a lineárisokon
kvantál, és az expertek a grouped_mm-úton maradnak (ezt a változatot is a pilot-itemeken
kell előbb lemérni).

---

## 6. Műszerek és kiszolgálás

### Az alany-példány (vLLM)

```bash
docker run -d --name ldh-subject --gpus all --ipc host -p 8400:8000 \
  -v ~/.cache/huggingface:<hf-cache> \
  -v ~/experiments/2026-10-03-lora-decision-head/adapters:/adapters \
  -e VLLM_ALLOW_RUNTIME_LORA_UPDATING=True \
  vllm/vllm-openai:v0.30.0 Qwen/Qwen3.6-35B-A3B-FP8 \
  --max-model-len 8192 --gpu-memory-utilization 0.5 \
  --no-enable-prefix-caching --max-logprobs 64 \
  --enable-lora --max-loras 2 --max-lora-rank 32 \
  --lora-target-modules q_proj k_proj v_proj o_proj in_proj_qkv in_proj_z in_proj_a in_proj_b out_proj gate_proj up_proj down_proj
# NINCS --speculative-config (MTP ki). K0b-hez: + --enable-scale-out (render).
# K0c-hez: + -e VLLM_LOGGING_LEVEL=DEBUG. A LoRA nélküli összehasonlító példány
# ugyanez --enable-lora és a --lora-* kapcsolók nélkül.
```

- **Kiolvasás:** offline token-id-k → `/v1/completions`, `max_tokens=1`, `temperature=0`,
  `logprob_token_ids` = a jelen lévő címkék id-jai. Ez pontosan a címkék (teljes szótárra
  normált) logprobját adja, top-k levágás és padlóérték nélkül. A szűkített softmax és a
  címketömeg ebből számolódik. Az adaptert a `lora_request` / modellnév választja ki,
  futásidőben betöltve.
- **Az elsődleges mérés soros (concurrency 1)**, és **egy motor összes kara ugyanazon a
  példányon fut**: L0/L1 `lora_request` nélkül, L3 vele. Így a páros különbségekből kiesik a
  példányzaj. Minden futás rögzíti a példány **ujjlenyomatát**: egy fix 50 itemes próbahalmaz
  logitjainak hash-ét.
- **Robusztusság:** legalább 5 friss példány, LoRA-val és nélküle, 1000 itemes részhalmazon
  L0 + L3. Jelentjük a példány-billenést és az elkülönülő módok számát. Opcionális kar: a
  `boot-llama33.sh` v2-ben használt `enable_flashinfer_autotune=false` beállítással
  összeolvadnak-e a módok.
- **Tilalom:** a measurement-hosten **soha** nem fut `mode-switch.sh`, `worker-mode.sh` vagy
  `docker compose up` az `/opt/docai` alól, mert a `worker-mode.env` a prod alphára mutat.
  Minden konténer saját `docker run`, `ldh-` névelőtaggal.

### Teljesítmény-mérés (F4, a tanulmányba)

Döntés/s és p50/p95 késleltetés, concurrency 1/8/32 mellett:
- (a) LoRA nélküli példányon;
- (b) `--enable-lora`-s példányon, LoRA-t nem kérő kéréssel;
- (c) `lora_request`-tel.

Mellé a chat decode tok/s MTP nélkül, a prod MTP=2 konfiggal összevetve, hogy a „lassabb
chat” ára számmal szerepeljen.

---

## 7. Futtatási rend a measurement-hosten

**Munkakönyvtár:** `~/experiments/2026-10-03-lora-decision-head/`, benne `eszkozok/`,
`adat/`, `adapters/`, `cache/`, `ckpt/`, `logs/` és `eredmenyek/`.
- **A measurement-hosten marad:** az adapterek, a checkpointok, a konvertált bázis és a rejtett
  állapot-cache.
- **Ide jön vissza:** az `eredmenyek/` (riportok, metrikák, item-szintű predikciók) és a
  publikálható `adat/`.

```bash
# laptop → measurement-host: kód és profil
rsync -az --delete eszkozok/ measurement-host:~/experiments/2026-10-03-lora-decision-head/eszkozok/
scp _belso/tenant_profil.json measurement-host:~/experiments/2026-10-03-lora-decision-head/adat/

# indítás leválasztva — utána a laptop altatható
ssh measurement-host 'cd ~/experiments/2026-10-03-lora-decision-head && \
  setsid nohup ./eszkozok/f1_vezenylo.sh > logs/f1.log 2>&1 < /dev/null & echo elindult'

# állapot (bármikor, ébredés után)
ssh measurement-host 'cat ~/experiments/2026-10-03-lora-decision-head/STATUS-F1'

# eredmény vissza ide
./eszkozok/sync_back.sh   # rsync: eredmenyek/, adat/ (publikálható rész), logs/*.log
```

**A vezénylők szabályai:**
- **Idempotencia:** minden lépés kihagyja magát, ha a kimenete `OK`-jelölővel megvan. A
  tréning a legutolsó checkpointból folytat.
- **Heartbeat:** a `STATUS-Fx`-ben időbélyeg, lépés, haladás és **várható befejezés
  óra:percben**, legalább 5 percenként frissítve. Ha 15 percnél régebbi, a futás halott.
- **Újraindulás utáni folytatás:** F0-ban a <user> crontabjába egy `@reboot` sor kerül, amely
  a futó fázis vezénylőjét újraindítja (idempotensen). A kör végén ez eltávolítandó, a
  Naplóba bejegyezve.
- **Lezárás:** a végén `DONE-Fx` vagy `FAILED-Fx` (okkal), és a vezénylő leállítja a saját
  konténereit.
- **Egyszerre egy nagy folyamat:** generátor-vLLM **vagy** alany-vLLM **vagy** Llama-bíráló
  **vagy** tréning. A Llama csak a `boot-llama33.sh` v2 receptjével indul.
- **Jegyzőkönyv:** minden futás rögzíti az image digestet, a modell-snapshotot, a seedet, a
  parancssort, a példány-ujjlenyomatot és az adat-hash-t.

---

## 8. Statisztikai protokoll — előre rögzítve

- Minden összevetés **párosított**, ugyanazokon az itemeken, motoron belül, és (vLLM-ben)
  ugyanazon a példányon.
- **Ismétlési zaj (példányon belül):** BI nélkül ugyanaz a kérés ugyanazon a példányon sem
  bájtazonos (K0a). Ezért az F4-ben a sor végén az L0 kar még egyszer lefut (L0′), és az
  L0↔L0′ eltérés (top-címke billenés, |Δp|) külön zajforrásként kerül a tanulmányba. Ha a
  karok közti különbség ennek nagyságrendjébe esik, az eredmény nem értelmezhető.
- **CI: klaszterezett bootstrap.**
  - Klaszter = cikk; a T-szállító rétegen a szállító. A T-szállítón ehhez jön még egy
    **szállító-szintű permutációs teszt** H2-höz.
  - Minden replikában a **val is újramintavételeződik, és τ újraválasztódik**, így a
    küszöb-bizonytalanság benne van a CI-ben.
  - H1-nél hierarchikus: seed × klaszter.
  - 10 000 ismétlés, 95% CI.
- **Val/teszt-higiénia:** küszöb, temperature, kalibrációs kar és a batch calibration
  statisztikája **csak a val-on** rögzül. A teszt egyszer fut, az F4-ben, az előre rögzített
  beállításokkal.
- **Bontások:** rétegenként, `X` / nem-`X`, listahossz (6–11 opció) és az `X` mozgó
  részhalmaza szerint.
- **Felbontás:**
  - a teljes teszten (~4600 pontozott item, a T-gen nélkül) klaszterezés nélkül ~±1,5 százalékpont;
  - a ~1500-as rétegeken ~±2,5–3, klaszterezve tágabb.

  A tényleges MDE-t a pilot alapján az F1 végén számoljuk.
- McNemar a pontosságra, másodlagosként.
- **Holm-korrekció a H1 két társ-elsődleges végpontjára** (@95, AURC; családi α = 0,05). A
  bootstrap kétoldali p = 2 · min(P(Δ ≤ 0), P(Δ ≥ 0)) a replikákból (`elemzes.bootstrap_diff`,
  `holm`).

---

## 9. Fázisterv, kapukkal

### F0 — Előkészítés és környezet-kapuk (~2–3 nap, ~6–8 óra GPU)

**Laptop:**
1. `_belso/tenant_profil.json` (4.1).
2. Licenc- és szerződés-jegyzet (0. pont); a külső bíráló kiválasztása.
3. Az eszközök: generátor-lánc, OpenSearch + `bge-m3` jelöltgenerátor, kiolvasó kliens,
   kalibráció, offline konverter, tréning, átnéző felület, vezénylők, `sync_back.sh`.

**measurement-host (`f0_vezenylo.sh`, leválasztva, `@reboot`-tal):**
- **F0.1 — eldobható pilot-generálás** (seed P, ~1000 item). Erre épül a K0b, K0d, K0e és a
  4.5 célsávjainak beállítása. A pilot soha nem kerül a val/tesztbe.
- **K0a — indulás.** A v0.30.0 a 6. pont kapcsolóival elindítja a Qwen3.6-FP8-at GB10-en.
  - Egy BI-próba, várhatóan `RuntimeError`, a Naplóba.
  - **Ismétlési zaj ugyanazon a példányon:** 3 bemelegítő kérés után három soros futás
    50 itemen × 2 permutáción, három konfigurációban (LoRA nélkül; `--enable-lora`
    async scheduling nélkül; `--enable-lora`). Bájtazonosság BI nélkül nem várható.
    Kapu: a példányon belül a top-címke 100%-ban egyezik; a valószínűség-szintű
    zajpadló (max |Δp|, átlagos |Δp(gold)|) a Naplóba és a tanulmányba kerül.
- **K0b — tokenizálás és kiolvasás:**
  - az offline token-id-k egyeznek a render-végpontéval (50 item);
  - a `logprob_token_ids` minden címkét visszaad;
  - címketömeg és `E`-tömeg az `X`-itemeken, kontrollként „Nincs illő” és `(` prefill;
  - a kérdésforma rögzítése.
- **K0f — FP8-hű bázis:**
  - offline konverzió;
  - a betöltés után `missing_keys` és `unexpected_keys` üres;
  - a modulnevek kilistázása;
  - perplexitás-épség néhány szövegen a vLLM-hez képest.
- **K0c — LoRA-aktiválás.** Valódi PEFT-mentésű adapter egy 5 lépéses pilot-tréningből
  (`lora-train:2`), átnevezett kulcsokkal, csoportonként nem nulla `B`-vel (csak attention /
  csak GDN / csak shared expert), DEBUG-loggal.
  - Kapu: a betöltött modulok száma egyezik a vártal; csoportonként elmozdulnak a logitok;
    expert-3D wrapper nem jön létre.
  - **Negatív kontroll:** ugyanez **átnevezés nélkül** → 0 betöltött modul. Ez a 2026-05-ös
    diagnózist is igazolja vagy cáfolja.
- **K0d — HF↔vLLM L0-egyezés** a pilot-itemeken.
  - ≥ 95% → rendben.
  - 90–95% → az F3-ban fake-quant kar, előtte **K0d-2** (`f0c_vezenylo.sh`):
    - a `fakequant.fq` bitre egyezik a vLLM `per_token_group_quant_fp8` kerneljével
      (fp32 és UE8M0 skála);
    - eager alapvonal és három változat (`vllm`: lineáris fp32 + MoE UE8M0; `fp32`;
      `pow2`) a pilot-itemeken, mind vs vLLM;
    - a legmagasabb top-címke egyezésű változat lesz az F3 fake-quant karja.
  - < 90% → **STOP**, a konverziót vagy a kiolvasást kell vizsgálni.
- **K0e — tréning-smoke:**
  - 20 lépés `lora-train:2`-vel;
  - csúcsmemória, token/s → az F3 időbecslése és a train-méret;
  - a döntési pozíció egységtesztje;
  - **folytatás-próba** (kilövés, újraindulás checkpointból).
- **K0g — Llama-bíráló** boot-próbája (v2 recept). Kimarad, ha a licenc-jegyzet kizárja.

**Kapu F0:**
- **K0a, K0b vagy K0f bukik** → javítás, nem továbblépés.
- **K0c bukik** a negatív kontroll és az átnevezés után is → döntési pont, a Naplóba. Az
  L0–L3 HF-ben továbbmegy, H3 „nem tesztelhető”. A fallbackek:
  - HF+peft kiszolgálás a méréshez;
  - vLLM-patch, amely maga is upstream-hozzájárulás;
  - merge + FP8 újrakvantálás (adapter-csere nélkül).
- **K0e szerint az F3 egy epochja > 12 óra** → kisebb train-méret vagy `max_length`; döntés
  a Naplóba.

### F1 — Szintetikus adatkészlet (1–2 éjszaka GPU + átnézési napok)

Szigorú sorrend:
1. végleges generálás friss seeddel;
2. nehézség-ellenőrzés (4.5), shortcut-audit (4.6), valószerűség (4.7) — legfeljebb egy
   javító iteráció, utána újragenerálás friss seeddel;
3. **befagyasztás**;
4. címke-átnézés (4.8): bírálók, majd Dani;
5. javítások;
6. **hash a jegyzőkönyvbe**;
7. MDE-számítás a pilotból.

Alany a val/teszten csak ezután fut.

**Kapu F1:**
- a javítás utáni reziduális címkezaj (hibás gold vagy kétértelmű) 95%-os felső határa a
  pontozott teszten ≤ 2% (`atnezes.py osszesit`, 4.8/4);
- szivárgás 0: <tenant>-szállítónév, kód vagy partner-cikkkód nincs; a névütközés-szűrő átment;
- shortcut AUC ≤ 0,55;
- a nehézségi célsávok teljesülnek.

### F2 — Tréning nélküli alapvonal (~1 éjszaka)

- L0 és az L1-karok vLLM-ben (soros, egy példány) és HF-ben, **csak a val-on** (a kar- és
  küszöbválasztáshoz). **L1★:** a val-on a legnagyobb lefedettség@95, holtversenyben a
  lefedettség@90, majd a kisebb ECE.
- Rejtett állapotok kinyerése HF-ben a döntési pozíción (27. réteg ≈ ⅔ mélység, és a 40.):
  train és val az F2-ben; a teszté az F4-ben, a HF-karokkal együtt. Így az F2-ben egyetlen
  teszt-predikció sem keletkezik (`f2_vezenylo.sh`).
- L2a és L2b fittelése a train-en, választás a val-on.

**Kapu F2 (a val-on döntve):** ha az L1★ besorolási lefedettség@95-je a val-on ≥ 90%, a
LoRA-nak kevés tere marad. Ilyenkor az F3 csak a pilotot futtatja, és a tanulmány fő
állítása a kalibrált logit lesz.

### F3 — Döntési LoRA (4–6 éjszaka)

1. **Pilot:** `L3-mix`, `L3-mix+se` és `L3-mix` fp32 fake-quanttal, 1 seed, 1 epoch
   (`f3_vezenylo.sh pilot`). Karonként: tréning → HF- és vLLM-kiolvasás a val-on, 4 permutációval
   → elemzés.
2. **Hangolási kör:** a pilot eredményétől függetlenül lefut, a pilot-győztes célmodul-készletén.
   **Előre rögzítve (2026-10-05, a pilot előtt):**
   - (h1) lr 2e-4;
   - (h2) ε = 0,05;
   - (h3) 2 epoch.

   Mind 1 seed. A fake-quant a pilot szerint (lásd lent).
3. **Megerősítés:** a val-on győztes konfig +2 seeddel (seed 2, 3).

**Győztes-választás (előre rögzítve):** az L3 `temp` karja (egyetlen forward + val-temperature),
a vLLM val-on. Sorrend: lefedettség@95, holtversenyben (< 2 pont) a lefedettség@90, majd a
kisebb AURC. **A fake-quant** (user-döntés 2026-10-05, a 3. pilot-kar eredménye előtt) csak akkor
megy tovább a hangolásra és a megerősítő seedekre, ha a fake-quantos `L3-mix` ugyanezzel a
sorrenddel a vLLM val-on **egyértelműen jobb**, mint a fake-quant nélküli. Az AURC-ben itt csak a
0,001-nél nagyobb eltérés számít. Holtversenyben az olcsóbb, fake-quant nélküli ág marad, mert az
fp32 fake-quant ~5× lassabban tanul. A választást az `f3_dontes.py` végzi gépiesen.

Közben a választás csak a val-on értékelve, HF-ben és vLLM-ben.

### F4 — Végső teszt és „ugyanazon a példányon” (~1 éjszaka)

- **A végső teszt egyetlen vLLM-példányon fut, sorosan:** L0, L1★, mindhárom L3-seed, végül
  L0′ (az L0 ismétlése, a 8. pont ismétlési zajához). Ugyanez a HF-motoron is.
- **H3 (b)–(d):** legalább 5 friss példány LoRA-val és nélküle.
- Teljesítmény-mérés (6. pont).
- Opcionális: R-det (4.9), T-gen.

### F5 — Stretch: külön fej (L4)

A #59543 backportja a v0.30.0-ra. Model Runner V2 kell hozzá, ami a v0.30.0-n CUDA-n az
alapértelmezett, és spekulatív dekódolás nélkül fut. Alternatíva: a v0.30.0 saját
`extract_hidden_states` spekulatív módszere — ennek használhatóságát előbb meg kell nézni.
Ha egyik sem indul el, az is eredmény: bekerül a tanulmányba.

### F6 — Termékek (~2 nap, GPU nélkül)

- dataset card;
- adapter card, ha a 10. pont engedi;
- tanulmány;
- belső jegyzet a docai-0122-höz: a T-szállító és az `X`-réteg súlyozásával, és azzal, hogy
  a prod C fok ma kötegelt JSON-kimenetre van tervezve, az egytokenes forma tehát
  javaslat, nem másolat.

---

## 10. Publikálási döntési szabály — előre, nem utólag

| eredmény | adatkészlet | adapter | tanulmány |
|---|---|---|---|
| H1 igaz, H2 mindkét rétegen „általánosít”, H3 igaz | publikus | publikus (vLLM-ben igazolt) | teljes |
| H1 igaz, H2 „általánosít”, H3 bukik | publikus | publikus, **„csak HF/peft, vLLM-kiszolgálás nem igazolt”** megjegyzéssel | a kiszolgálási negatív eredmény a tanulmány része |
| H1 igaz, H2 bármelyik rétegen „nem általánosít” | publikus | **nem** (katalógus-memorizálás) | „a szintetikus javulás nem általánosít” |
| H1 igaz, H2 „nem eldönthető” | publikus | nem | a tanulmány a nagyobb tesztréteg igényét mondja ki |
| H1 bukik | publikus | nem | „a kalibrált logit elég” — publikálható negatív eredmény |
| F1-kapu bukik, vagy a licenc-/szerződés-jegyzet tiltja | nem | nem | nincs; belső jegyzőkönyv |

Ügyféladat egyik esetben sem kerül publikálásra. A `_belso/` mappa tartalma soha nem megy
HF-re, blogba vagy a `docai-evals`-ba.

---

## 11. Kockázatok

| kockázat | jel | kezelés |
|---|---|---|
| a LoRA kulcs-prefix miatt némán kimarad | K0c negatív kontroll | átnevezés exportkor; DEBUG-számlálás minden adapter-betöltésnél |
| a GDN-csomagolt modulokra (`in_proj_qkvz`/`in_proj_ba`, vegyes FP8/BF16) nem jut LoRA | K0c csoportonként | ha csak a GDN-csoport néma: `attn+se` kar, a különbség a tanulmányba |
| az FP8 expertek HF-ben nem töltődnek be | K0f | offline konverzió, kemény kulcs-kapu |
| nincs példányok közt reprodukálható mód (BI nem indul) | K0a | soros mérés, minden kar egy példányon, ujjlenyomat, ≥5 példányos robusztusság |
| HF↔vLLM numerikai eltérés | K0d | motoron belüli összevetés; fake-quant kar |
| tréningidő (~190 token/s) | K0e | train-méret a mérés szerint; F3 4–6 éjszaka |
| node-restart hosszú futás közben | heartbeat | `@reboot` + idempotens folytatás checkpointból |
| a memória kifut | — | `--gpu-memory-utilization 0.5`; egyszerre egy nagy folyamat |
| szintetikus–valós rés | 4.7 AUC | stílusprofil-iteráció; relatív állítások; a valós igazolás a docai-0122 arany-halmazán |
| a generátor-család stílusa szivárog | T-gen réteg | Llama-generált érzékenységi réteg; determinisztikus zaj |
| a címke-betűk ütköznek magyar szavakkal | K0b | címketömeg-diagnosztika; kérdésforma-választás az F1 előtt |
| a prodra mutató `worker-mode.env` | — | `mode-switch`/`worker-mode`/compose tilos, saját `docker run` |

---

## 12. Ami ebben a körben nem cél

- **Általános célú döntési adapter** (több feladat, bool/choice/score típusok,
  SystemOne-kompatibilis végpont). A kérdésforma már erre készül, de a tréningje a következő
  kör. A 100+ opciós feladat ott sem cél: a kevés, kezelhető opció a gyakorlati problémák
  nagy részére elég.
- Tenant-specifikus finomhangolás védett, valós adaton: csak ha ez a kör jó eredményt ad.
- Prod-integráció (docai-0122 árnyék-mód), együttélés az MTP-vel.

---

## 13. Mappaszerkezet (laptop, ez a mappa)

```
LoRA-decision-head/
  00-runbook.md            ez a fájl
  compass_artifact_…md     irodalmi háttér
  eszkozok/                F0-ban készül
  _belso/                  <tenant>-profil, valós minták, R-det kimenet — SOHA nem publikálható
  adat/                    a befagyasztott szintetikus adatkészlet + hash — publikálható jelölt
  eredmenyek/F0…F5/        visszahúzott riportok, metrikák, item-szintű predikciók
  jegyzokonyv/             futásnapló: digest, snapshot, seed, ujjlenyomat, döntések
  publikacio/  hf-release/ F6
```

---

## 14. Eredménylap — a váz, amit ki kell tölteni

Motoronként egy tábla (vLLM / HF), rétegenként (T-belső, T-szállító, T-közeli, T-távoli,
pool):

| fok / kar | besorolási lef@95 | elért precizitás | AURC | döntési lef@95 | X-prec / X-fedés | ECE | kétértelmű-átlépés | pozíció-billenés | címketömeg | döntés/s |
|---|---|---|---|---|---|---|---|---|---|---|
| L0 | | | | | | | | | | |
| L1★ (kar: …) | | | | | | | | | | |
| L2a (HF) | | | | | | | | | — | — |
| L2b (HF) | | | | | | | | | — | — |
| L3 (kar: …, 3 seed) | | | | | | | | | | |
| L4 (stretch) | | | | | | | | | | |

- H1 … H6: igaz / cáfolt / nem eldönthető / nem tesztelhető — CI-vel együtt.
- Javítatlan teszten (érzékenység): …
- Címkezaj rétegenként: …
- K0c: betöltött modulok / várt modulok: … · példány-billenés (≥5 példány), elkülönülő
  módok száma: …
- MTP nélküli chat decode: … tok/s (prod MTP=2: …).

---

## 15. 00b kiegészítés — valóban kitartott szállítós réteg (előre rögzítve, 2026-10-07)

**Miért.** Az önellenőrzés szerint az F1 T-szállító rétegének mind a 14 szállítója a train-ben is szerepel
(generátorhiba, Napló 2026-10-07), így a H2 új szállítóra vonatkozó része nem tesztelhető. Dani döntése: új,
valóban kitartott réteg készül, a **meglévő** adapterekkel mérve. Ez a pont a generálás előtt rögzül; a
mérés előtt (Dani címke-átnézése után) csak a Naplóban dokumentált, indokolt módosítás lehet.

**A réteg: `T-ujszallito`.**
- 16 új, csak-teszt szállító (`s048`–`s063`, `role = test`), az S2 receptjével és a v2 stílusprofillal, új
  seeddel (20261007). Az S2-vel húzott 48 jelöltből az első 16, amely legalább egy nem kitartott gyökeret is
  kiszolgál; a csak kitartott gyökeres szállító nem kaphat látott cikket (az F1-ben így lett 16-ból 14). Nevük
  nem ütközik a meglévőkkel.
- Cikkek: a nem kitartott gyökerek valódi (nem gyűjtő) cikkei közül csak azok, amelyeknek az F1-ben van
  train-párja (látott cikk). A párok sűrűsége az F1 szabálya szerint (cikkenként 1–4 szállító a gyökér
  train + val + új teszt szállítóiból; csak az új szállítók párjai kerülnek a rétegbe).
- X(b): a kivezetett F1 T-szállító X(b)-cikkei, mindegyik egy, a gyökerét kiszolgáló új szállítóval. Ezek
  a train-ben és a val-ban nem szerepelnek.
- Az S3–S8 lánc az F1-é (S1 katalógus, train-aliasok, OpenSearch + bge-m3 jelöltek, a duplikátum-kizárás,
  az S7–S8 seed 20261005). Az item-id-k a meglévő sorok után folytatódnak, nem ütköznek az F1-gyel.
- Az F1 adat (`adat/f1`) érintetlen; a kiegészítés az `adat/k00b` alatt épül.

**Kapuk a fagyasztás előtt:**
1. **Split-átfedés (kemény kapu):**
   - a réteg szállítói nem szerepelnek a train-ben, a val-ban és a többi tesztrétegben;
   - a (szállító, cikk) párjai nem szerepelnek az F1 párjai közt;
   - minden nem-X(b) cikkének van train-párja;
   - az X(b)-cikkek a train-ben és a val-ban nem szerepelnek;
   - a train-nel azonos (normalizált sorszöveg, gold) duplikátum száma jelentve.
2. **Shortcut-audit** az F1 kapujával (CV AUC ≤ 0,55). Bukás esetén egy javító kör (S7–S8 új seeddel),
   naplózva.
3. **Címke-átnézés** az F1 protokolljával (4.8 és az `atnezes.py`): a két bíráló (Llama-3.3-70B, Mistral
   Small 4) csak előszűr, Dani átnézi a konszenzus-flageket (≤ 40) és egy rétegzett véletlen mintát
   (~120). A javítások után a becsült maradék zaj felső 95%-os korlátja ≤ 2%.
4. SHA-256 fagyasztás.

**Mérés (a fagyasztás után):**
- Ugyanaz az alany-image, modell és a három F3/F4-adapter (`l3mixse_h2_s1..s3`). Újratanítás nincs.
- **vLLM:** egyetlen friss példány (`LORA=1`) olvassa a próbahalmazt, a val-t (`f2_val.jsonl`) és a
  `T-ujszallito`-t: az L0-t 4 permutáción (az L1★ permutáció-átlagához), az L3 × 3-at perm 0-n (a `temp` kar
  csak ezt használja; a többi permutáció csak a pozíció-billenés diagnosztikája volt), végül az L0′-t
  (perm 0). Mint az F4-ben, a τ és a temperature ugyanabból a példányból jön, mint a teszt.
- **HF:** a `T-ujszallito`-n az L0 (4 perm.) és az L3 × 3 (perm 0); a HF val az F2/F3-ból.
- Eszközök: `eszkozok/k00bb_vezenylo.sh` (mérés), `eszkozok/k00b_elemzes.py` (elemzés; az F4 T-szállító
  rétegén validálva: pont-Δ +0,1736 és permutációs p 0,00012, mint az F4-ben).

**Hipotézis — H2-szállító′ (elsődleges motor: vLLM, a HF is jelentve).**
- Mérőszám: Δ = L3 (3 seed átlaga) − L1★ besorolási lefedettség@95 a `T-ujszallito`-n. A közölt Δ a
  pontkülönbség, a CI a bootstrap percentilise.
- A karok és a kalibráció pontosan az F4-ét követik: L1★ = permutáció-átlag + a perm-0-ra illesztett
  val-temperature, L3 `temp` kar, τ@95 a val-on. Érzékenységként jelentjük a permutáció-átlagra illesztett
  temperature-t is.
- Bootstrap: 10 000 ismétlés, klaszter = szállító, a val újramintavételezésével és τ újraválasztásával.
- Ítélet (mint a H2): CI alsó határa > 0 → **általánosít**; CI felső határa < 2 pont → **nem
  általánosít**; egyébként → **nem eldönthető**.
- Mellékes: egzakt szállító-permutációs próba (2¹⁶ előjelcsere, rögzített val-τ), az AURC a saját
  görbéig és közös lefedettségen, a nem-X arány (plafon), a kockázat rögzített lefedettségen, X-fedés.
- **Erőbecslés:** a feltáró adat (a valóban nem látott szállítók itemjei) +9 pont körüli hatást mutat. A
  CI fél-szélessége a τ-bizonytalanság miatt a réteg méretétől kevéssé függ; az F4-ben egy hasonló méretű
  rétegen ~±7–9 pont volt. A „nem eldönthető” ítéletnek tehát reális esélye van; ezt előre kimondjuk.

**Publikálás (a 10. pont kiegészítése).** A 10. pont soraiban a „H2 T-szállító” helyére a H2-szállító′
lép; a T-kategória ítélete az F4-ből marad (általánosít). Ha a H2-szállító′ „általánosít”, az adapter a
„H1 igaz, H2 általánosít, H3 bukik” sor szerint publikus a 4.4. pont megjegyzésével. Ha „nem általánosít”
vagy „nem eldönthető”, az adapter nem publikus (a 10. pont megfelelő sorai).

---

## Napló

- **2026-10-03 — v1.** Döntések a megbeszélésből:
  - az MTP elengedhető (kutatási kör);
  - ~97%-os példányegyezés elfogadható;
  - első feladat a BA-bíráló, **szintetikus**, <tenant>-alapú adattal (publikálhatóság);
  - FP8 elsőként, BF16 a kutatási fallback;
  - az általános célú döntési modell hosszú távú cél, 100+ opció nem cél;
  - a <tenant>-ben nincs emberi besorolási döntés;
  - a measurement-host a kutatásra 100%-ban szabad.
- **2026-10-03 — v2, házon belüli terv-review után** (devils-advocate + kód-ellenőrzés;
  a kulcsállítások szúrópróbával a measurement-host image-eiben igazolva).
  - **User-döntés:** az F1 végén a címkéket független modellek nézik át, utána Dani is (4.8).
  - **Környezet:**
    - A BI-mód v0.30.0-n GDN-en nem indul → soros, egy-példányos páros design.
    - A 2026-05-ös LoRA-tünet valószínű oka az adapter-kulcsprefix → átnevezés + negatív
      kontroll a K0c-ben.
    - A HF az FP8 experteket nem tölti be → offline FP8-hű konverzió (K0f).
    - `lora-train:2` a `:3` helyett.
    - A docker-parancs bővült: `--enable-scale-out` (csak K0b), `--no-enable-prefix-caching`,
      `--gpu-memory-utilization 0.5`, `--lora-target-modules`,
      `VLLM_ALLOW_RUNTIME_LORA_UPDATING`.
    - Kiolvasás `logprob_token_ids`-szel.
  - **Design:**
    - A split egysége a (szállító, cikk) pár; alias csak train-párokból.
    - A kitartott gyökér a train-katalógusból is kimarad.
    - `X(a)` 6. rangú pótlással; az `X(b)` cikkek splitenként diszjunktak.
    - Két kitartott gyökér (közeli/távoli), 12+8 kitartott szállító, val-szállító réteg.
    - Shortcut-audit; alanyfüggetlen nehézség, eldobható pilottal.
    - S8 attribútum-alapú kétértelműség, soft címkével.
    - Szolgáltatás-séma, gyűjtőcikk, cikk-szintű ár.
  - **Statisztika:**
    - Elsődleges végpont: **besorolási** lefedettség@95 (az `X` tartózkodás),
      Clopper–Pearson τ-szabállyal és precizitás-bukással.
    - Klaszterezett, val-újraküszöbölő bootstrap; H2 háromértékű, MDE-vel.
    - H3 bitazonosság helyett LoRA-hatás-egyezés.
    - Szimmetrikus hangolási keret; ε=0 alapból; streaming batch calibration.
  - **Adat és jog:**
    - n-gram nem kerül a profilba;
    - az R-det kimenete `_belso/`;
    - a tenant neve nem szerepel;
    - licenc- és szerződés-kapu F0-ban.
  - **Idő:** az F3 4–6 éjszakára tervezve (~190 token/s).
- **2026-10-03 — F0 indul** (user: „indulhat az F0”; a második bíráló a GPT-6 Astra).
  - **Megvalósítási döntések (a mérés előtt):**
    - Generátor: `qwen38-flash-dgx:v030-bb661c4` a round8 receptjével (`--max-model-len 32768`).
      CJK-szűrő a kimeneten (docai-0117): a CJK-t tartalmazó választ eldobjuk, és új seeddel
      újrakérjük.
    - Gyűjtőcikk az opciólistán nem szerepel, tartalékkal pótolva (4.2 S6).
    - A train-aliasok két foldban épülnek (4.2 S5).
    - Szállító/cikk eloszlás: a <tenant>-ben a cikkek 84,5%-ának egy szállítója van. A
      szintetikusban ez 55%, mert a pár-szintű splithez (T-belső) több szállítós cikk kell.
      Ez szándékos eltérés.
    - Egy ügyfél-azonosító alkategória a szintetikus katalógusban általánosabb néven szerepel.
  - **K0a — BI-próba:** a v0.30.0-n `VLLM_BATCH_INVARIANT=1` mellett az alany nem indul
    (RuntimeError) — a review-ban előre jelzett módon.
  - **K0f — konverzió:** 693 várt kulcs, 0 hiányzó forrás, 79 s, 65 GB.
  - **Licenc-jegyzet:** [jegyzokonyv/2026-10-03-licenc-szerzodes.md](jegyzokonyv/2026-10-03-licenc-szerzodes.md).
    A generátor forrásmodellje Qwen Community License 1.0 alatt áll („Model as a Service /
    AI Work Assistant” záradékkal). Az ügyfélszerződés-pont nyitott; amíg nincs döntés, a
    szintetikus adat csak belső.
  - **Újraindulás utáni folytatás:** a `@reboot` crontab-sor telepítve 06:59-kor
    (`# ldh-folytat`). A kör végén eltávolítandó.
  - **K0a — ismétlési zaj (F0A, majd a K0a-2 mátrix az F0B elején).** Az F0A-ban ugyanazon a
    példányon két soros futás nem volt bájtazonos: a probe-00 az első kérésnél, a probe-13 a
    futás közepén tért el. Ezért a kiolvasó 3 bemelegítő kérést kapott, és három
    konfigurációt mértünk, mindegyiket egy friss példányon, 3 soros futással, 50 item × 2
    permutációval:

    | konfiguráció | bájtazonos sor (1↔2, 1↔3) | top-címke | max \|Δp\| | átl. \|Δp(gold)\| |
    |---|---|---|---|---|
    | LoRA nélkül | 99%, 99% | 100% | 0,013 | ≤ 0,0001 |
    | `--enable-lora`, async nélkül | 94%, 96% | 100% | 0,014 | ≤ 0,0002 |
    | `--enable-lora` | 92%, 94% | 100% | 0,029 | ≤ 0,0006 |

    Konfigurációk közt, az 1. futások párjain (0% bájtazonos):

    | pár | top-címke | átl. \|Δp(gold)\| |
    |---|---|---|
    | `--enable-lora` ↔ `--enable-lora`, async nélkül | 98% | 0,016 |
    | LoRA nélkül ↔ `--enable-lora` | 96% | 0,023 |
    | LoRA nélkül ↔ `--enable-lora`, async nélkül | 97% | 0,026 |

    **Következtetések:**
    - A példányon belüli zaj nem LoRA-specifikus. Az async scheduling kikapcsolása nem
      szünteti meg. Az `--enable-lora` növeli, de a top-címkét egyik konfigurációban sem
      billenti (3 × 3 futás).
    - A nagy log-prob eltérések (max 1,6 nat) a kis valószínűségű címkéken vannak, a
      döntést nem érintik.
    - A példányok közti eltérés (2–4 billenés / 100) egy nagyságrenddel nagyobb a
      példányon belülinél. Ez megerősíti a páros, egy-példányos designt, és azt, hogy a
      H3(d) bázisa a LoRA nélküli friss példányok egymás közti egyezése legyen (F4,
      ≥ 5 példány). Ez a 100 párosított soron nem dönthető el.
    - A K0a kapu ennek megfelelően: példányon belül top-címke 100% → **teljesül**. A
      bájtazonosság nem kapu (9. pont, K0a). Az F4-be bekerült az L0′ ismétlés (8. pont).
- **2026-10-03 — F0 kapuk** (F0A 07:25, F0B 09:40, F0C a K0d-2-vel; részletek:
  [pilot-megfigyelések](jegyzokonyv/2026-10-03-pilot-megfigyelesek.md), a nyers kimenet az
  `eredmenyek/F0/`-ban).

  | kapu | eredmény | ítélet |
  |---|---|---|
  | K0a | BI nem indul; példányon belül a top-címke 100%-ban stabil (3 konfig × 3 futás) | ✓ |
  | K0b | render 50/50; minden címke egy token (A–J: 32–41, X: 55); címketömeg medián 0,999; „(” prefill a tömeget ~0-ra viszi → nincs prefill; „Nincs illő” rosszabb X-recallt ad → „Egyik sem” marad | ✓ |
  | K0f | 693/693 kulcs, 0 hiányzó; betöltési kapu üres; perplexitás HF 5,23 / 6,07 / 11,39 vs vLLM 5,14 / 5,90 / 10,75 | ✓ |
  | K0c | betöltött modul attn 20/20, GDN 90/90, shared expert 80/80, mind 190/190; routed expertre 0; átl. \|Δp(gold)\| 0,026–0,048 a negatív kontroll 0,004-ével szemben; **átnevezés nélkül 0 modul** | ✓ |
  | K0d | HF↔vLLM top-címke 553/588 = 94,0% (X-itemeken 86%) | 90–95% sáv → fake-quant kar, K0d-2 |
  | K0e | selftest; 20 lépés `mix+se`; kilövés az 5. lépés után, folytatás „lépés 5”-ről; ~215 token/s, 70 GB | ✓ |
  | K0g | Llama-3.3-70B-FP8 boot 181 s, helyes válasz | ✓ |

  - **K0c — a negatív kontroll igazolja a 2026-05-ös diagnózist:** átnevezés nélkül a vLLM
    egyetlen modult sem tölt be, és ezt csak DEBUG-szinten jelzi („No LoRA weights found”).
  - **K0c — a kritérium javítása az adat után, átláthatóan:** az első elemző „elmozdult”, ha
    a címke-log-prob max eltérése > 1e-3. Ezt a kis valószínűségű címkék példányzaja (K0a-2:
    max 0,87 nat) önmagában átlépi, ezért a 0 modult betöltő negatív kontroll hamisan
    „mozdult”, és a kapu bukott (`K0c_ok: false`). Az új kritérium valószínűség-szintű:
    átl. |Δp(gold)| ≥ 0,01 (a K0a-2 példányon belüli zajának ~16-szorosa) és ≥ 3 × a
    negatív kontrollé; a kontroll < 0,01. Az ítélet nem a küszöbön múlik: a kontroll
    0,004, a valódi csoportok 0,026–0,048, és a kontroll 44/50 sora bájtazonos az alappal.
  - **K0e — a selftest kritériumának javítása:** a `logits_to_keep=1` és a teljes forward
    utolsó pozíciója a bf16 GEMM-alak miatt ≤ 0,03-mal tér el (egy bf16-ulp alatt), az
    eredeti 1e-2-es tűrés ezt bukatta. Új kritérium: < 0,25, és az utolsó előtti pozíciótól
    > 1,0 (a rossz pozíció kizárására).
  - **K0d — eltérés-szerkezet:** csak alacsony margón (vLLM top1 − top2 ≥ 0,6 → 100%
    egyezés), és szisztematikus X-eltolódás (log P(X) HF − vLLM medián −0,37). Az ok az
    aktiváció-kvantálás: a vLLM a GB10-en a FP8-lineárisok előtt tokenenként, 128-as
    csoportban fp32 skálával, a Triton MoE előtt UE8M0 skálával kvantál. Ez a vLLM-ben
    ellentmondásos: a DeepGEMM-et erre a modellre éppen az E8M0 pontosságromlása miatt
    kapcsolja ki, a Triton MoE mégis E8M0 skálát kap. Upstream-jelentésre érdemes.
  - **K0d-2 — `fakequant.py`:** a `fq` a vLLM `per_token_group_quant_fp8` C++ kernelével
    bitre egyezik (551 424 elem, fp32 és UE8M0). Az első változat az fp32-skálánál az
    elemek 0,8%-án tért el, mert a `tensor / skalár` a PyTorch-ban CUDA-n reciprokkal szoroz;
    javítva tenzor/tenzor osztásra. A kikapcsolt mód az eredeti expert-forwardot hívja
    (kontroll: 50/50 bájtazonos).
  - **Pilot → F1 döntések:**
    - méretezés `meretezes_szim.py` alapján (4.4);
    - nehézségi célsávok rögzítve (4.5);
    - LLM-ár a profil durva sávjára csonkolva, kiszerelés–egység összhang, gyökérenként
      rétegzett X(b), gyűjtőnév-javítás (4.2 S1);
    - a T-belső/T-szállító lexikai könnyebbsége a trainhez képest (teljes vs 2-foldos
      alias-index) **elfogadva**: a prod is a teljes alias-készlettel keres, és a K0b-2 szerint
      a nem-`X` döntési pontosság a lexikai nehézségtől alig függ.
  - **A pilot generátorkódja** a 2026-10-03 délelőtti változat; az F1 előtti módosítások
    (ár a promptban is) a pilotot már nem reprodukálják bitre. A pilot eldobható, a kimenete
    `eredmenyek/F0/pilot`-ban és `adat/pilot`-ban marad.
  - **K0d-2 — eredmény (F0C, 19:53):** 588 pilot-item, mind vs vLLM (`pilot_vllm`):

    | HF-változat | top-címke | X-itemeken | log P(X) HF−vLLM medián | átl. \|Δ log-prob\| | idő |
    |---|---|---|---|---|---|
    | grouped_mm, fake-quant nélkül (K0d) | 94,0% | 86,0% | −0,37 | 0,40 | ~4 perc |
    | eager, fake-quant nélkül | 94,4% | 87,3% | −0,37 | — | — |
    | `vllm` (lineáris fp32, MoE UE8M0) | 94,0% | 86,0% | −0,32 | 0,45 | 13 perc |
    | **`fp32`** | **95,1%** | 86,7% | −0,25 | 0,43 | 13 perc |
    | `pow2` | 93,7% | 86,0% | −0,34 | 0,49 | 13 perc |

    - A szabály szerint a legjobb (`fp32`) lesz az F3 fake-quant karja.
    - **A különbségek a zajon belül vannak.** ±1 pont ~6 item, és mind a < 0,3 margójú ~95
      itemen billen. A HF két saját expert-implementációja (eager vs grouped_mm) egymással
      csak 96,3%-ban egyezik.
    - **A vLLM-hű (`vllm`) változat nem javít.** Vagy a Triton MoE a valóságban nem UE8M0
      skálát kap, vagy az eltérést más források uralják: a HF a GDN-t a torch-fallbackkel
      számolja (az `fla` nincs a `lora-train:2`-ben), a vLLM FlashInfer GDN-kernellel; ehhez
      jön a fuzionált RMSNorm+kvantálás és a súlyok bf16-kerekítése.
    - **Következmény a mérésekre:**
      - a HF↔vLLM egyezés felső korlátja ezen az adaton ~95–96%;
      - a H3(c) a karok *különbségét* hasonlítja, ez a közös zajt kiejti;
      - a motorok közti szisztematikus X-eltolódást (−0,25 … −0,37) a motoronkénti τ elnyeli.
- **2026-10-03/04 — F1: generálás, auditok, egy javító iteráció.**
  - **F1A** (19:56–22:53; S1 seed 20261003; `f1a_vezenylo.sh`) lefutott.
    - **S1-hozam:** 3514 cikk a tervezett ~5000 helyett. Az alkategóriánkénti több
      LLM-hívás sok azonos nevet ad (pl. „Tej 2,8% 1 l”), ezeket a dedup kiszűri.
    - **Rétegek:** train 5685, val-belső 238, val-szállító 479, T-belső 473, T-szállító
      1527, T-közeli 751, T-távoli 709. A teszt összesen ~3460 (terv ~4600); a két
      H2-réteg 1527 és 1460. **Elfogadva:** a teljes teszt felbontása ~±1,7 pont ±1,5
      helyett, és a val-ből (~720) a τ konzervatívabb lesz, de minden karra egyformán.
  - **Nehézség (4.5):** a val/teszt minden rétege sávban. A train a BM25 top-1-en 0,34 (nem
    kapu): a 2-foldos alias-index miatt nehezebb.
  - **Shortcut (4.6) — bukott:** CV AUC 0,584.
    - **Ok:** a *természetes* X(a), vagyis a visszakeresési hiba (nem-X vs természetes X(a):
      AUC 0,703; nélkülük 0,504). Ezek 60%-a csupa nagybetűs sor, és a jelöltlistájuk szórtabb
      (3,6 vs 2,8 kategóriaút).
  - **Valószerűség (4.7, laptop):** CV AUC 0,974 > 0,95 → stílusprofil-kör.
    - **Mintázatok, valós vs szintetikus:** csupa nagybetű 15% vs 30%, zárójel 18% vs 6%,
      pontos rövidítés 48% vs 33%, számjegy 64% vs 49%, kódelőtag 5% vs 2,5%.
    - **A nagybetű-többlet forrása:** az S3-prompt csupa nagybetűs rövidítés-példái
      („CS.MELL”). Rövidítési szint ≥ 1-nél az LLM a nevek 23–67%-át csupa nagybetűvel írta,
      holott a nagybetűs stílusú szállító csak 5/48.
  - **Az egyetlen javító iteráció** (runbook F1 2. lépés), mindkét auditra:
    - **S7:** a kényszerített X(a) splitenként *és* metaadat-rétegenként (nagybetűs sor ×
      kategóriaút-szám × gyökérszám) a 25%-os célig; a telített rétegek többletét a riport
      számolja.
      - **F1B** (S7 seed 20261004, a v1 S1–S6-on): shortcut AUC 0,530, a kapu teljesül.
      - Az F1B-t a Llama-körben kézzel leállítottam, mert az F1C az itemeket úgyis lecseréli.
    - **Stílus v2:**
      - S3-prompt vegyes betűs példákkal és kis-/nagybetű-utasítással;
      - S2: zárójel-stílus 35%, rövidítési szint 0,25/0,30/0,25/0,20, kiszerelés 40%,
        kódelőtag 12%;
      - S4: zárójelbe a kiszerelés vagy a százalék.
    - **F1C** (06:17-től): S1 megtartva, S2–S8 friss seeddel (20261005), utána auditok,
      előzetes hash, Llama. A v1 adat `adat/f1_v1`, az eredmény `eredmenyek/F1_v1` (benne az
      F1B auditja).
  - **Archiválási hiba:** az F1B `adat/f1/v1` mentése csendben elmaradt. A mappa root
    tulajdonú (a generátor-konténer hozta létre), és a `2>/dev/null` elnyelte a hibát. Így
    az F1A rétegzés nélküli itemjei felülíródtak. Az S1–S6 és a régi `osszeallit.py`
    (seed 20261003) determinisztikusan újraelőállítja őket. Az F1C az archívumot `mv`-vel
    készíti.
  - **F1C — S3-hiba (07:08):** az S3 ~45 perc után elhasalt. Egy LLM-válaszban a `tetelek`
    egyik eleme lista volt objektum helyett, és a futásnak nem volt részleges mentése.
    - **Javítás:**
      - típusőr az S1/S3 válaszfeldolgozásban;
      - a hiányzó megnevezések egyszeri újrakérése más seeddel (eddig csendben kiestek);
      - egy végleg sikertelen hívás nem állítja le a futást;
      - hívásonkénti cache (`s3_cache.jsonl`), amelyből egy újabb hiba után a futás folytatódik.
    - Ál-LLM-mel tesztelve. Újraindítás 07:09-kor; a seed és a párkiosztás változatlan.
  - **F1C eredménye (08:51):**
    - **Rétegek (S2–S8 seed 20261005):** train 5740, val-belső 248, val-szállító 785, T-belső
      489, T-szállító 1675, T-közeli 740, T-távoli 697. A teszt összesen 3601, a val 1033.
    - **Shortcut:** CV AUC **0,520** (foldok 0,50–0,56); a gold pozíciója egyenletes (p = 0,79).
      A természetes X(a) a csupa nagybetűs sorok csökkenésével sokkal ritkább lett (train 580
      → 280).
    - **Nehézség:** minden val/teszt réteg sávban; a train BM25 top-1 0,38 (nem kapu).
    - **Valószerűség:** CV AUC **0,978** (v1: 0,974). A mintázatok vegyesen alakultak, a
      runbook egy stílus-kört engedett, ezért nincs további iteráció:

      | mintázat | valós | v1 | v2 |
      |---|---|---|---|
      | nagybetű | 15% | 30% | 23% |
      | zárójel | 18% | 6% | 23% |
      | pontos rövidítés | 48% | 33% | 27% |
      | kódelőtag | 5% | 2,5% | 13% |
      | számjegy | 64% | 49% | 52% |

      A szintetikus sor karakter-n-gram szinten továbbra is jól elkülöníthető. Ez a
      tanulmány korlátja: a T-gen réteg (Llama-generált stílus) és a belső R-det (4.9) méri a
      stílusérzékenységet.
    - **Llama-bíráló (val/teszt, 4634 item):** gold-egyezés 58–67%, nem-X itemeken 76–87%,
      **X-recall 4–10%**; magabiztos (≥ 0,8) ellentmondás 25–30%. A Llama szinte sosem
      választ X-et, így a flagek többsége az X-itemeken a bíráló hibája. Ezek közt vannak
      viszont a valódi X-zajjelöltek is: egy listán maradt egyenértékű cikk. A
      rétegenkénti 60-as korlát és a bekerülési súlyok miatt a becslés torzítatlan marad.
  - **Második bíráló:** Mistral Small 4 119B-A6B NVFP4 lokálisan (user, 2026-10-04; a GPT-6
    Astra helyett). Snapshot `45331841b631`, 66 GiB, `~/hf-cache-mistral4`. F1D: 08:51-től.
  - **Bírálók és triage (2026-10-04):**
    - **Mistral Small 4 NVFP4 lokálisan:** a v0.30.0 image transformers 5.17-ével a
      `PixtralForConditionalGeneration` importja bukott (`PixtralRotaryEmbedding` átnevezve,
      `position_ids_in_meshgrid` megszűnt). Javítás: `vllm_shim/sitecustomize.py`, csak a
      Mistral-konténerbe. Boot 9,5 perc, logprob-mód, címketömeg a top-20-ban 0,85–0,98.
    - **Pontosság a val/teszten:** gold-egyezés Llama 58–67%, Mistral 41–50%. Nem-X itemeken
      Llama 76–87%, Mistral 54–67%. **X-recall:** Llama 4–10%, Mistral 1–3%.
    - **Pozíciós torzítás:** A-választás Llama 24%, Mistral 30%, a gold 10%. Mindkét bíráló
      jóval gyengébb az alanynál (pilot, nem-X ~94%).
  - **S8-kiterjesztés: családon kívüli duplikátumok (2026-10-04).**
    - **Felfedezés:** az átnéző felület első itemje hat szinte azonos „Jégsaláta” cikket
      mutatott. A runbook S1-dedupja (bge-m3 koszinusz > 0,95) a generátorból kimaradt,
      csak a pontos névegyezés-szűrés volt meg.
    - **Mérés** (`duplikatum_audit.py`): a gold mellett családon kívüli, koszinusz > 0,95
      opció a T-rétegekben 1,2–5,2%.
    - **Javítás:** az S8 kiterjesztése (`duplikatum.py`, lexikai, determinisztikus). Egy
      azonos alkategóriájú, más családú, azonos számú opció megkülönböztethetetlen, ha a
      különbség-szavak egyike sem szerepel a sorban. Kivétel, ha csak az opciónak van plusz
      minősítője; olyankor a sor a goldot írja le.
    - **Hatás:** +795 kétértelmű item; a kétértelmű arány 16–23% rétegenként. Az item-magok
      (id, gold, opciósorrend, kontextus) mind a 10 374 itemen bitre azonosak, így a
      bírálói eredmények érvényesek. A shortcut (0,52) és a nehézség változatlanul átmegy.
    - **A konszenzusos ellentmondás** a kétértelműek kiszűrésével 255-ről 170-re esett: a
      bírálói ellentmondások jó része a duplikátumokból jött.
    - **A következő generáláshoz** az S1-dedupot be kell építeni a generátorba.
  - **Átnézési minta:** 387 item (148 konszenzusos + 239 véletlen, ebből 74 vitatott); a
    populáció 3701 pontozott val/teszt item. Szimulált maradék-zaj a teszten:
    - hibátlan átnézésnél felső95 0,9%;
    - 30%-os konszenzus-hibánál 1,2%;
    - +1% zaj a többiben: 2,9% → ilyenkor egy második véletlen adag kell.
  - **Elemző lánc — próbafutás a pilot L0-n (2026-10-04, laptop):**
    - **Hiba javítva:** a `bootstrap_diff` csak a teszt-predikciókat kapta, a val-újraküszöbölés
      `KeyError`-ral bukott.
    - **Lelet az elsődleges végpontra:** a pilot L0 legmagabiztosabb besorolásai közt ott
      vannak az `X`-itemek 0,999-es téves választásai. A top-100 precizitása 94%, mind a 6
      hiba `X`-item; a top-200-é 95%. A CP-alsó ≥ 0,95-höz ~97–98% kellene több száz
      itemen, így a **besorolási lefedettség@95 az L0-ra és várhatóan minden L1-karra ~0**
      (alsó korlát). A temperature az ECE-t javítja (0,104 → 0,05), a lefedettséget nem.
    - Ugyanez @90-nel a pilotban ~40%. **Döntendő az F2 előtt (user):** marad-e egyedüli
      elsődleges végpontnak a @95, vagy előre rögzített másodlagos végpontként bekerül a
      @90 és az AURC.
  - **Train-bírálat (F1E, 2026-10-04):** mindkét bíráló lefutott az 5740 train-itemen.
    - **Konszenzusos magabiztos ellentmondás:** 226 item. Ebből 76 már kétértelmű, a maradék
      150 (2,6%) ~70%-a `X`-item (161/226).
    - **Döntés: a train-t nem szűrjük** (a 4.8/8 csak megengedi). Az ellentmondások zöme a
      bírálók `X`-vakságából jön. Az érintett `X`-itemek épp a nehéz negatívok: a jó cikk nincs
      a listán, és egy rokon cikk magabiztosan „illik”. A LoRA-nak ezeket kell megtanulnia, így
      az elhagyásuk a bírálói torzítást vinné át a tanítóadatba.
    - A train címkezaját a val/teszt átnézésből becsült zajszinttel jelentjük.
  - **F3-időmérés (F1E, 12 lépés `mix+se`, grad-accum 8, az F1 train-en).** A train 5740 item,
    átlagosan 385 token (p95 478), egy epoch ~2,21 M token.

    | fake-quant | token/s | epoch | expertek | memória |
    |---|---|---|---|---|
    | nincs | 178–214 | ~3,1 óra | grouped_mm | 70 GB |
    | `lin` | 172–206 | ~3,2 óra | grouped_mm | 70 GB |
    | `fp32` | 58–62 | ~10,2 óra | eager | 70 GB |

    - Az `fp32` a 12 órás szabály (5. pont) alatt marad → **az F3 fake-quant karja `fp32`**.
    - A `lin` gyakorlatilag ingyen van: tartalékként marad, ha az F3 időkerete szorít.
    - F3-becslés:
      - a két alap pilot-kar egyenként ~3 óra, a fake-quant kar ~10 óra;
      - a hangolás (≤ 3 konfig, 1–2 epoch) ~3–6 óra konfigonként;
      - a megerősítés +2 seed;
      - összesen ~2–3 éjszaka.
  - **Címke-átnézés, első 99 item (2026-10-04, Dani).** A felület kevert sorrendje miatt az
    első 99 a 387-es minta egyenletes részmintája (36 konszenzusos, 63 véletlen).
    - **Lelet:** 12 problémás címke: 7 hibás gold és 5 kétértelmű. A véletlen szint teszt-részén
      6/51, vagyis kb. minden tizedik pontozott itemnél gond van a címkével.
    - **Ok (generátor):**
      - 9/12 katalógus-duplikátum: ugyanaz a termék két cikkszámon, más néven, néha más
        alkategóriában („Mozzarella ball 125 g” / „Mozzarella golyó 125 g”, „UHT tej 1,5% 1 l” /
        „UHT tej 1,5%”, „Méz virágméz” / „Virágméz”). Az `X(a)`-nál a valódi cikk kiesik, de a
        duplikátuma a listán marad; nem-`X`-nél a sor a duplikátumra illik jobban.
      - 2/12 értelmetlen vagy rossz helyre tett katalógusnév („Kenyér” a húskészítmények közt).
      - 1/12 csonkolás miatti valódi kétértelműség.
    - **A 4.2 S1 dedup kimaradt, de nem is segített volna.** A generátor csak a normalizált
      nevet szűrte. A hibás párok `bge-m3` koszinusza 0,70–0,94, így a > 0,95-ös dedup 0/12-t
      fogna. Szám-kompatibilitással kiegészítve (`duplikatum_kalibral.py`) sem választ szét:
      a 12-ből 7 elfogásához 0,85 kell, ami az átnézett jó itemek 27/87-ét és a pontozott
      itemek 26%-át is jelölné.
    - **Kapu:** most felső95 10,9% (pont 5,0%). Ha a maradék 288 itemben már nem lenne hiba,
      akkor is 2,7% > 2%. A kétértelműt is zajnak számolva 6,0%. **Több átnézéssel a kapu nem
      teljesíthető; a forrást kell javítani.**
    - **Protokoll-hiba:** az `osszesit` csak a *gold hibás* döntést számolja maradék-zajnak. Az
      át nem nézett, de valójában kétértelmű item a teszten egyetlen golddal pontozódik, tehát
      ugyanúgy zaj.
  - **F1F — duplikátum-kizárás (user-döntés, 2026-10-04: a javítás mehet; az átnézés szünetel).**
    - Jelölt párok: 49 651 (sor valódi cikke × S6-lista, családon kívül). Szám-kompatibilis és
      koszinusz ≥ 0,60 vagy közös szótő: **25 651 bírálandó pár** (10 281 csak a szótő miatt).
      Dani 9 duplikátum-párjából 3 koszinusza 0,60–0,66, ezért kellett a szótő-ág.
    - A két bíráló mindkét sorrendben (bírálónként ~55 ezer kérés, 16 párhuzamos szekvencia),
      utána döntés + kalibrációs kapu.
    - Utána: archiválás (`adat/f1_v2`, `eredmenyek/F1_v2`), S7–S8 újra (S1–S6 változatlan, seed
      20261005), auditok kapuval, a két bíráló a val/teszten, új átnézési minta.
    - A 99 döntés megmarad (`dontesek_100.json`) kalibrációnak (`adat/f1/dedup/kalibracio.json`:
      9 duplikátum-pár, 631 nem-duplikátum pár a 87 rendben talált itemből, 2 értelmetlen név).
    - Az új zajdefinícióval (hibás gold vagy kétértelmű) az F1C-adat maradék-zaja a 99 döntésből
      pont 12,3%, felső95 20,3%.
    - Llama-próba (64 kérés): az igen/nem válasz-tömeg mediánja 1,0, a döntések józanok
      („UHT tej 1,5%” / „Tartós tej UHT 1,5%” → 1,0; „UHT tej 1,5%” / „Tehéntej 1,5% zsírtartalmú”
      → 0,001). A katalógusban egy-egy termékre akár 4–5 névváltozat is van.
  - **L2a-szonda kész (`l2a_szonda.py`, 2026-10-04), az F2 vezénylőjébe kötve.**
    - Multinomiális logisztikus fej L2-büntetéssel a 27. és a 40. réteg rejtett állapotán. A
      hiányzó címkék maszkolva, a cél az L3-mal azonos (gold, kétértelműnél egyenletes soft).
    - λ a val NLL-jén (pontozott itemek, 0. permutáció); a kimenet a HF-sorformátum, ezért az
      `elemzes.py` karjai rajta is futnak. A teszten `apply` az F4-ben.
    - Szintetikus próbán végigfut (fit → apply bájtazonos → elemzés).
  - **Javítás:** az `elemzes.py` `load_meta`-ja az `atnezes.py alkalmaz` után a
    `*.pre_atnezes.jsonl` mentést is beolvasta volna, és a régi gold felülírta volna a javítottat.
    Mostantól kihagyja. A measurement-host `elemzes.py`-ja régebbi volt (kötelező `--test`); szinkronizálva.
    - **Átírt prompt:** a kérdés elöl, a pár a végén. A prefix-cache ~80%-os, a Llama ~9,2 kérés/s
      (előtte 3,9), a Mistral ~9 kérés/s. Az első, fordított sorrendű 10 perc eldobva.
    - **Döntés:** a 25 651 párból 6950 duplikátum (Llama 4352, Mistral 5931; unió).
    - **Értelmetlen név:** 29 cikk, mindkét bíráló egyetért. Zömmel a távközlési szolgáltatás-sémák
      furcsa helyszín-kombinációi („Mobil internet adatkeret - Parkoló kamera”), illetve
      „Földimogyorókrém tojás”, „Üdítős ital kóla” az alkoholos italoknál. A „Facsart tálca”-t mindkét
      bíráló értelmesnek tartja.
    - **Kalibrációs kapu: 8/9 ✓.** Csak a „Kenyér” / „Kenyér fehér” pár marad ki (Llama 0,497,
      Mistral 0,026). A 87 rendben talált item opciói közül 154/631 párt jelöl, 66 itemnél. A
      példák zöme valódi duplikátum vagy általános–specifikus pár („Fokhagyma por 5 kg” /
      „Fokhagymapor”, „Sajtos felvágott 400 g” / „Felvágott 400 g”). Van köztük téves is, főleg
      a Mistraltól: „Joghurt vanília” / „Joghurt natúr” 0,907, színváltozatok 0,56–0,78. Ezek
      csak egy-egy zavaró opciót cserélnek.
    - **S7:**
      - 7569 itemnél 24 476 opció zárva ki;
      - 79 sor esett ki értelmetlen név miatt;
      - 162 item maradt 2-nél kevesebb opcióval.
    - **Első audit: shortcut-kapu ✗ (AUC 0,574).** Az opciószám árult el (egyváltozós AUC 0,530 →
      0,573; X-listák 7,71 vs. 7,25 opció). A duplikátum-kizárás kimerítette a tartalékot, és
      kényszerített X(a) csak tartalékos itemből lehet, így a rövid listák nem-X-ek maradtak.
      **Javítás:**
      - minden itemnél marad ≥ 1 tartalék;
      - az opciószám is réteg a kényszerítésben;
      - diagnosztika: `auditok.py shortcut-diag`, jellemzőnkénti és X-fajtánkénti AUC.
    - **Második audit ✓:**
      - shortcut AUC 0,520, gold-pozíció χ² p = 0,56;
      - opciószám X / nem-X rétegenként ±0,3;
      - nehézség a sávban;
      - X-arány 22–26%;
      - kétértelmű 11–17% (F1C: 16–23%);
      - val/teszt 4540 item (F1C: 4634).
    - **F1F kész (2026-10-04 22:39).** A val/teszten mindkét bíráló 4540/4540-re válaszolt. A
      laptopon az F1C-adat `adat/f1_v2`-ben, az eredményei `eredmenyek/F1_v2`-ben; az új adat
      hash-e egyezik a `fagyasztas_jelolt.sha256`-tal.
    - **Új átnézési minta (2026-10-05): 336 item** (98 konszenzusos + 238 véletlen, ebből 61
      vitatott). A konszenzusos ellentmondás 170-ről 98-ra esett (−42%), egy réteg sem éri el a
      40-es plafont. A korábbi döntésekből 1 jött át.
  - **Végpont-döntés (user, 2026-10-05):** az elsődleges marad a besorolási lefedettség@95.
    Előre rögzített másodlagos a besorolási lefedettség@90 (τ90, bukás < 88%) és az AURC.
    - `elemzes.py`: karonként `at90` blokk. A bootstrap ugyanazokon az újramintákon adja a Δ@95-öt,
      a Δ@90-et és a ΔAURC-t. L1★ holtversenyben (@95 ~0) a @90, majd az ECE szerint.
    - Próbafutás a pilot L0-n: a pilot val-on a @90 is 0 minden karon, a bootstrap Δ@90
      CI-ja ±0,52. A τ-szabály kis val-mintán ugrálva vált a végtelen és a véges érték
      között. Az F1 val (~850 pontozott item) jóval stabilabb lesz, de **az F2-ben ellenőrizni
      kell a Δ@90 CI-szélességét**, mielőtt az MDE-t rögzítjük.
  - **Második átnézés, első 100 item (2026-10-05):** 1 problémás (1 hibás gold, `T-szallito`, véletlen
    rész); a tegnapi körben 99-ből 12 volt. Teszt maradék-zaj: pont 2,3%, felső95 7,1%.
    Szimuláció a 336-os mintára:
    - nincs több probléma: felső95 1,9%, a kapu épp átmegy;
    - +1 probléma: 2,7%, bukik;
    - +2 probléma: 3,5%, bukik.

    ~1%-os valódi zajnál a ≤ 2% bizonyításához ~600 teszt-oldali véletlen item kell, vagyis
    valószínűleg második adag is. A kapu nem változik.
  - **F2T (2026-10-05 05:59):** az F2 train-része előre (HF-kiolvasás + rejtett állapot 27/40,
    `f2t_vezenylo.sh`). A train-t az átnézés nem érinti, a val/teszten alany nem fut. Az F2
    `hf_train` jelölőjét állítja be.
  - **Második átnézés, 200 item (2026-10-05):** 4 problémás itemet találtunk.
    - 2 családon kívüli méretváltozat: a sorban nincs méret, a listán ugyanaz a termék több
      méretben, külön családban („CheeseMaster trapipsta (” mellett Trappista 5 kg / 1 kg /
      500 g / 100 g).
    - 1 semmitmondó sor („209560 Pannon Sajtmanufaktúra”: a csonkolás után csak kód + márka).
    - 1 valódi emberi kétértelműség (az „R.fűsz.k.” rövidítés).

    Az első három generátor-ok.
    - **Pontosítás Daninak:** X = a termék nincs a listán. Kétértelmű = a termék a listán van,
      de nem dönthető el, melyik változat. A modell ezekre soft célt tanul, nem X-et.
  - **F1G — S8 v2 (2026-10-05):** két új kétértelműség-szabály (`duplikatum.size_ambiguous` és
    `uninformative`).
    - *Méretváltozat:* a két név szavai kölcsönösen ekvivalensek, a számértékek eltérnek, és a
      sor a valódi cikk egyetlen számértékét sem hordozza.
    - *Semmitmondó sor:* a sor egyetlen szava sem illik a valódi cikk nevére, és a márka, a kód
      meg a számok levétele után nem marad ≥ 3 betűs szó.
    - Az első, durvább változat elgépelt sorokat és márkanévbe ágyazott termékneveket
      („KÁRPÁT VODKA”) is jelölt, így a pontozásból épp a nehéz itemek estek volna ki. Javítva.
    - Eredmény:
      - 84 item lett újonnan kétértelmű (115 méret, 10 semmitmondó esemény, átfedéssel);
      - a 10 133 item kontextusa, opciói és goldja bájtazonos;
      - shortcut AUC 0,520, nehézség OK.

      A bírálatok és Dani döntései érvényesek maradnak. Régi itemek: `adat/f1_s8v1`.
    - **Minta szűkítve** (`atnezes.py szukit`): az újonnan kétértelmű itemek kiesnek a
      populációból és a mintából. A szűkítés a tartalom determinisztikus függvénye, így a
      maradék minta cellánként egyenletes marad. Eredmény: 336 → 329 item, a 4 problémából 3
      kiesett.
    - A 195 átnézett itemen 1 probléma maradt; teszt maradék-zaj: pont 1,1%, felső95 3,4%.
      Ha a hátralévő 134-ben nincs probléma, 1,94% (épp átmegy); +1 problémánál 2,77%.
    - ⚠️ **Torzítás:** a két szabályt a már átnézett itemekből terveztük, ezért ezeken a
      maradék-zaj optimista. A még át nem nézett 134 és egy esetleges második adag torzítatlan.
      A jelentésben az utóbbiakon számolt becslés is szerepel.
  - **Második átnézés, 300 item (2026-10-05):** 2 új probléma.
    - r000586 semmitmondó sor; az S8 v2 már kivette.
    - „Kenyér fehér (1000 g) 20x”: a gold „Kenyér fehér 1000 g”, a listán „Kenyér fehér 1 kg” is
      ott van. Mértékegység-duplikátum: a szabályok a számokat szövegként vetették össze.
  - **F1G-2 — S8 v3:** a mennyiségek alapegységben (kg/dkg → g, l/dl/cl → ml; `duplikatum.qtys`).
    Az `indistinguishable` és a `size_ambiguous` ezzel vet össze.
    - 54 item lett újonnan kétértelmű (val/teszt 13); a tartalom bájtazonos, a shortcut AUC 0,520,
      a nehézség OK.
    - A minta 329 → 325 itemre szűkült.
    - 288 számító átnézett itemen 1 probléma (r004979, rövidítés). Teszt maradék-zaj: pont 0,69%,
      felső95 2,25%. Ha a hátralévő 37-ben nincs probléma, 1,95%; +1 problémánál 2,78%.
    - Mivel a három szabályt az átnézett itemekből terveztük, a kapu után egy **friss megerősítő
      adag** kell (új véletlen „többi” itemek, a szabályokra nézve torzítatlan).
  - **Első adag lezárva (2026-10-05):** 325/325 számító item átnézve, 1 probléma (r004979, a
    rövidítés). **Teszt maradék-zaj: pont 0,60%, felső95 1,95% → a kapu (≤ 2%) teljesül.** Val:
    pont 0,36%, felső95 3,5%. Javítás: 1 item kétértelműre (`javitasok.jsonl`).
  - **Megerősítő pótadag** (`atnezes.py potadag`, `adag` = 2): 152 friss véletlen „többi” item
    (teszt 118), `atnezo_adag2.html`. Ezekre a S8 v2–v3 szabályokat nem hangoltuk. Két egyenletes
    húzás uniója cellán belül egyenletes, így a becslő változatlan. Az `osszesit` és az
    `alkalmaz` vesszővel elválasztott döntésfájlokat is fogad.
  - **Megerősítő adag, első 100 (2026-10-05):** 1 probléma (r000731). A sor „TEJFÖL 20% 2DL”, a
    gold „Savanyú Tejföl 20% 2 dl”, a listán „Tejföl 20% 200 g” is ott van: ugyanaz a
    kiszerelés.
  - **F1G-3 — S8 v4:** a térfogat 1-es sűrűséggel egyenértékű a tömeggel (l/dl/cl/ml → g).
    7 item lett újonnan kétértelmű (val/teszt 3); a tartalom bájtazonos, shortcut 0,520,
    nehézség OK. A minta 477 → 476.
  - **Kapu, két adaggal:** teszt pont 0,40%, felső95 1,36% ✓. Val: pont 0,24%, felső95 2,55%.
    - *Konzervatív becslés* (az S8 v4 nélkül, r000731 zajként): pont 0,73%, felső95 1,89% ✓.
    - A megerősítő adag 100 itemjéből 1 probléma volt, és az is új mértékegység-variáns. A
      szabálytervezés miatti optimizmus tehát kicsi.
  - **BEFAGYASZTVA (2026-10-05 08:28, user-döntés: a megerősítő adag 100 itemjénél megállunk).**
    - Javítás: 1 item kétértelműre (r004979). Hibás goldot javítani nem kellett: a második körben
      talált hibák mind a kétértelműség-szabályokba kerültek.
    - Hash: `eredmenyek/F1/atnezes/fagyasztas.sha256`; az átnézés előtti fájlok:
      `items_*.pre_atnezes.jsonl`.
    - **Végső maradék címkezaj a teszten:** pont 0,40%, felső95 1,36%; konzervatívan 0,73% /
      1,89%. Val: 0,24% / 2,55%.
    - Átnézve összesen: 1. adag 325, 2. adag 99 számító item. Az F1C-n az első 99-ből 12 volt
      problémás.
    - **Javítás az `alkalmaz`-ban:** „K” választásnál a soft halmazba tévesen az X (None) került,
      mert a `lab2id.get("K")` is None-t ad. Javítva, újrafuttatva. Mindig a `pre_atnezes`
      mentésből dolgozik, és csak az r004979 tér el tőle.
    - A train `kétértelmű`-jelölése az F2T indulása után változott (S8 v2–v4, 93 item). A HF-sorok
      és a rejtett állapotok ettől függetlenek, az L2a a soft célt a befagyasztott itemekből olvassa.
  - **F2 indítva (2026-10-05 08:29):** a fagyasztási hash-ellenőrzés OK; a `hf_train` lépés az
    F2T-ből kész.
  - **F2 kész (2026-10-05 08:29–09:28), val, 825 pontozott item (181 kétértelmű).**

    | fok / kar | motor | lef@95 | prec | lef@90 | AURC | ECE | pontosság | X-prec | X-fedés |
    |---|---|---|---|---|---|---|---|---|---|
    | L0 nyers | vLLM | 0,531 | 0,968 | 0,685 | 0,040 | 0,047 | 0,799 | 0,809 | 0,369 |
    | L1 temp (T = 1,37) | vLLM | 0,543 | 0,969 | 0,692 | 0,040 | 0,021 | 0,799 | 0,809 | 0,369 |
    | **L1★ = perm. átlag** | vLLM | **0,596** | 0,967 | 0,739 | 0,032 | 0,049 | 0,817 | 0,875 | 0,395 |
    | L1 contextual | vLLM | 0,377 | 0,971 | 0,549 | 0,096 | 0,170 | 0,686 | — | 0,000 |
    | L0 nyers | HF | 0,575 | 0,968 | 0,695 | 0,039 | 0,059 | 0,790 | 0,774 | 0,333 |
    | **L1★ = perm. átlag** | HF | **0,625** | 0,967 | 0,745 | 0,031 | 0,049 | 0,817 | 0,894 | 0,390 |
    | L2a 27. réteg, perm. átlag (λ = 0,01) | HF | 0,684 | 0,966 | 0,725 | 0,006 | 0,155 | 0,886 | 0,762 | 0,887 |
    | **L2a 40. réteg, perm. átlag** (λ = 0,03) | HF | **0,688** | 0,967 | 0,756 | 0,007 | 0,050 | 0,902 | 0,816 | 0,841 |
    | L2a 40. réteg, nyers | HF | 0,656 | 0,967 | 0,753 | 0,012 | 0,061 | 0,885 | 0,782 | 0,810 |

    - **F2-kapu:** az L1★ lef@95 a val-on 0,596 (vLLM) és 0,625 (HF), < 0,90 → a LoRA-nak van
      tere, az F3 teljes programmal fut.
    - **A pilot „@95 ≈ 0” lelete a címkezaj műterméke volt.** A legmagabiztosabb „téves”
      besorolások zöme duplikátum-gold volt. A tisztított adaton az L0 is ~53–58%-ot fed le.
    - **A batch- és a contextual kalibráció ront.** A contextual az X-et teljesen kiírtja
      (X-fedés 0). A temperature csak az ECE-n javít.
    - **L2a (H4 előzetes):** a lineáris fej az utolsó réteg rejtett állapotán az X-fedést
      0,33–0,39-ről 0,81–0,84-re emeli, a pontosságot ~0,80-ról 0,89–0,90-re, az AURC-t ~0,035-ről
      0,007–0,012-re viszi. A modell „tudja” az X-et, a címkesor-kiolvasás nem hozza felszínre.
    - **Az F3 mércéje gyakorlatilag az L2a.** A H1 előre rögzítetten L3 vs. L1★, ez marad; az
      eredménylapon az L2a mellette szerepel.
    - A λ-t az L2a ugyanazon a val-on választja (7 érték), mint a kart és a τ-t: enyhe optimizmus,
      a teszt (F4) dönt.
  - **MDE (F1 7. lépés; `mde.py`, 2026-10-05):** az F2 val-kiolvasásaiból, klaszterezett
    bootstrappal (500 ismétlés), a 3021 pontozott teszt-itemre vetítve. A szórás két része: a
    τ-választás (a val-on rögzül, a teszt méretével nem csökken) és a mintavétel (~1/n).

    | összevetés | Δ@95 MDE80 | ebből τ-rész | Δ@90 MDE80 | ΔAURC MDE80 |
    |---|---|---|---|---|
    | L1★ vs. L0 (vLLM) | 12,3 pont | 92% | 5,4 pont | 0,0039 |
    | L2a-40 vs. L1★ (HF) | 11,4 pont | 94% | 6,0 pont | 0,0054 |

    - **A @95-ös elsődleges végpont gyenge felbontású:** a szórás >90%-a a 825 pontozott
      val-itemen választott τ-ból jön. A @95-ös CP-szabály ugrálós.
    - Az L2a-40 val-on mért +6,3 pontja @95-ön nem lenne szignifikáns, a ΔAURC = −0,025 viszont
      ~5-szöröse az MDE-nek.
    - A seed-komponens (H1: 3 seed) nincs benne.
    - **Döntendő az F4 előtt (user):** marad-e egyedüli elsődleges a @95.
  - **F3 pilot indítva (2026-10-05 09:35):** `f3_vezenylo.sh pilot`.
    - Karok: `l3mix_s1`, `l3mixse_s1`, `l3mixfq_s1` (fp32).
    - Beállítások: r = 16, α = 32, dropout 0,05, lr 1e-4, grad-accum 16, 1 epoch, a train 5593 item.
    - Becsült idő: ~3 + 3 + 10 óra tréning, plusz karonként ~1 óra kiértékelés.
  - **H1-végpont (user-döntés, 2026-10-05, L3-eredmény előtt): a @95 és az AURC társ-elsődleges,
    Holm-korrekcióval** (családi α = 0,05). A H1 teljesül, ha legalább az egyik szignifikáns az
    L3 javára. A @90 másodlagos. `elemzes.py`: a bootstrap kétoldali p-t ad, a `holm()` dönt.
    Egységpróba: (p = 0,2; 0,001 AURC jó irányban) → H1 ✓; (0,03; 0,04) → egyik sem;
    (@95 p = 0,001, de az L1★ javára) → H1 ✗.
  - **F3 pilot, 1. kar: `l3mix_s1` (2026-10-05 12:39).** A tréning 350 lépés volt (09:35–11:44, ~285
    tok/s). A címke-CE átlaga az első 50 lépésben 0,571, az utolsó 50-ben 0,333. Val, 825
    pontozott item.

    | kar | motor | lef@95 | prec@95 | lef@90 | AURC | ECE | pontosság | X-prec | X-fedés | kétért.-átlépés |
    |---|---|---|---|---|---|---|---|---|---|---|
    | L0 nyers | vLLM | 0,531 | 0,968 | 0,685 | 0,040 | 0,047 | 0,799 | 0,809 | 0,369 | 0,276 |
    | L1★ perm. átlag | vLLM | 0,596 | 0,967 | 0,739 | 0,032 | 0,049 | 0,817 | 0,875 | 0,395 | 0,331 |
    | L2a-40 perm. átlag | HF | 0,688 | 0,967 | 0,756 | 0,007 | 0,050 | 0,902 | 0,816 | 0,841 | 0,453 |
    | **L3-mix `temp`** | vLLM | **0,756** | 0,965 | 0,761 | **0,0012** | 0,018 | 0,947 | 0,909 | 0,918 | 0,785 |
    | L3-mix perm. átlag | vLLM | 0,758 | 0,968 | 0,758 | 0,0012 | 0,019 | 0,954 | 0,910 | 0,933 | 0,823 |
    | L3-mix `temp` | HF | 0,756 | 0,965 | 0,758 | 0,0011 | 0,017 | 0,949 | 0,905 | 0,928 | 0,801 |

    - **A val-on a @95 a plafonon van.** A 825 pontozott itemből 195 gold-X, így helyes
      besorolással legfeljebb 0,764 érhető el. Az L3 ennek 99%-át fedi le. A @90 ezért alig
      nagyobb a @95-nél. A val-on a @95 és a @90 a további L3-karok között nem fog különbséget
      tenni, a pilot-győztest várhatóan az AURC dönti el (a 9. F3 sorrendje szerint).
    - Az L1★-hoz képest a @95 +16 pont, az AURC −0,031. Mindkettő többszöröse az MDE-nek
      (12,3 pont, illetve 0,004). Ez val-adat, egy seed, ugyanabból a generátorból, amelyből a
      train is jön. A H1-et a teszt dönti el, a T-közeli és a T-távoli réteggel együtt.
    - **A HF és a vLLM egyezik** (0,756 / 0,756; AURC 0,0011 / 0,0012). A BF16-on tanított,
      futásidőben betöltött adapter az FP8-as vLLM-alanyon hű maradt. A fake-quant kar a HF–vLLM
      eltérést aligha javíthatja; a kérdés az, hogy nem ront-e.
    - **Kétértelmű-átlépés 0,33 → 0,79 (itt a kisebb a jó).** Az L3 a kétértelmű sorokat is
      magabiztosan besorolja, részben azért, mert a τ alacsony (0,39). Ez nem kapu, de prodban
      az ilyen sor emberhez menne. Az F4-ben a választott címke soft-gold-találatát is
      megnézzük.
  - **F3 pilot, 2. kar: `l3mixse_s1` (2026-10-05 15:48).** A tanítható paraméterek száma
    21,2 M (310 modul), a `mix`-é 16,3 M. Sebesség ~275 tok/s, a címke-CE az utolsó 50 lépés
    átlagában 0,318. vLLM `temp`: @95 0,755, @90 0,755, AURC 0,0009, ECE 0,014, pontosság 0,952,
    X-fedés 0,933, kétért.-átlépés 0,856. HF `temp`: 0,755 / 0,755 / 0,0010. Az előre rögzített
    sorrend szerint a @95 és a @90 holtverseny (< 2 pont), az AURC 0,0009 < 0,0012, így a
    célmodul-győztes a `mix+se`. A különbség a zajszinten van, de a szabály ezt adja.
  - **A 3. kar (fp32 fake-quant) ~56 tok/s-mal tanul**, ötször lassabban, mint a fake-quant
    nélküli. Ha a fake-quant továbbmegy, a hangolás és a megerősítés ~3 nap a ~0,6 nap helyett.
  - `f3_dontes.py` (új): az előre rögzített győztes-választás gépiesen. Kimenete a
    `pilot_dontes.json` és a `hangolas_dontes.json`, valamint a következő szakasz karjai.
    Az `f3_vezenylo.sh` megkapta a `hangolas` és a `megerosites` szakaszt. A measurement-hostre csak a
    pilot vége után kerül, mert futó bash-szkriptet nem írunk felül.
  - **Fake-quant szabály pontosítva (user-döntés 2026-10-05 ~16:30, a 3. kar eredménye előtt):**
    a fake-quant csak akkor megy tovább, ha egyértelműen jobb; AURC-holtverseny < 0,001,
    holtversenyben a fake-quant nélküli ág (lásd 9. F3). A hangolás lánca indítva: a
    `lanc.sh F3-pilot F3-hangolas` a pilot DONE-jára indítja az `f3_vezenylo.sh hangolas`-t. A
    `folytat.sh` és a `lanc.sh` mostantól a szakaszos fázisneveket (F3-pilot) is kezeli; eddig
    egy reboot után az F3 nem folytatódott volna.
    A megerősítés is láncolva: `lanc.sh F3-hangolas F3-megerosites`. FAILED esetén nem indul.
    Várható menetrend: pilot DONE ~03:00, hangolás ~14:30 (10-06), megerősítés ~21:00 (10-06),
    ha a fake-quant nem megy tovább.
  - **F3 pilot kész (2026-10-06 02:08).** A 3. kar (`l3mixfq_s1`, fp32 fake-quant): ~60 tok/s, a
    címke-CE az utolsó 50 lépés átlagában 0,330. vLLM `temp`: @95 0,756, @90 0,756, AURC 0,0015,
    ECE 0,011, pontosság 0,953. HF: 0,761 / 0,761 / 0,0014. A fake-quant nélküli `l3mix`-hez
    képest a @95 azonos, az AURC 0,0003-mal rosszabb, ez a 0,001-es sávon belül van.
    → **holtverseny, a fake-quant nem megy tovább.** Az eredeti, sáv nélküli szabállyal is ez
    jött volna ki, mert ott a fake-quant AURC-je kisebb kellett volna legyen, és nagyobb lett.
    A pilot-döntés (`pilot_dontes.json`): `mix+se`, fake-quant nélkül.
  - **Hangolás indult (02:09).** Karok: `l3mixse_h1_s1` (lr 2e-4), `_h2_s1` (ε = 0,05),
    `_h3_s1` (2 epoch).
    - **h1 kész (05:15).** vLLM `temp`: @95 0,764, @90 0,764, AURC 0,0016, ECE 0,011,
      pontosság 0,960, X-fedés 0,933.
    - A h1 a @95-ben a plafonig ér (0,7636 = 630/825). A pilot-alaphoz (0,755) képest ez
      +0,8 pont, ami < 2 pont, tehát holtverseny. Az AURC-ben (0,0016 vs. 0,0009) az alap
      a jobb.
    - **h2 kész (08:22).** vLLM `temp`: @95 0,759, @90 0,759, AURC 0,00086, ECE 0,020,
      pontosság 0,958, X-fedés 0,944, kétért.-átlépés 0,812. A címke-CE az utolsó 50 lépésben
      0,544; az ε miatt ennek magasabb a padlója, ez nem romlás. Az alaphoz képest a @95 és a
      @90 holtverseny, az AURC 0,00086 < 0,00091, így **egyelőre a h2 vezet**. Az eltérés
      0,00005, tisztán zaj; a szabály szerint mégis ez dönt.
  - **`f4_elemzes.py` (új, 2026-10-06), az F4 elemzője.** Motoron belül számol: H1 (Holm, végpontonkénti
    cáfolattal), H2 (rétegenkénti háromértékű ítélet, a T-szállítón egzakt szállító-szintű
    előjelcserés permutációval; 14 szállító, 2^14 kombináció), H4 + H5 Holm-családban,
    L0↔L0′ ismétlési zaj, bontások, McNemar.
    - A bootstrap a 8. pont szerint 10 000 ismétléses és hierarchikus: seed × klaszter,
      rétegenkénti klaszterkulccsal, a val újramintavételezésével és τ újraválasztásával.
    - A vektorizált τ- és mérőszám-számítás bitre egyezik az `elemzes.py`-éval, valós F3/F2
      val-kiolvasásokon (`onteszt`).
    - Próbafutás: a val-kiolvasásokat tükröztem a teszt-rétegekre, 200 replikával ~6 s. A
      valódi teszten 10 000 replikára ~15–20 perc várható.
    - **Mellékes val-lelet (l3mixse_s1):** a magabiztosan besorolt kétértelmű sorok 95,5%-ában a
      választott opció a soft-gold egyike. Az L3 tehát a kétértelmű sorokon jellemzően az
      elfogadható változatok egyikét választja.
  - **F4 előkészítve és láncolva (user-döntés 2026-10-06, a megerősítés előtt).**
    - Döntések: (1) a val-t is az F4-es vLLM-példány olvassa újra, így τ és a temperature
      ugyanabból a példányból jön, mint a teszt; (2) az L2a a HF-ágon fut a teszten (H4); (3) a
      H3-hoz 5 friss `--enable-lora`-s és 5 LoRA nélküli példány fut egy 1000 itemes
      teszt-részhalmazon.
    - `f4_vezenylo.sh`: a vLLM fő példányon sorosan fut az L0 (val + teszt, 4 permutáció), az
      L3 seed 1–3 (adapterenként betöltés és eltávolítás), az L0′, a teljesítménymérés (b) és
      (c), és elején-végén a próba-ujjlenyomat. Ezt követi az elemzés, a HF-ág (L0 + 40. réteg,
      L3 × 3, L0′, L2a apply), az elemzés, a H3-példányok a teljesítménymérés (a) részével, végül
      az `f4_h3.py`.
    - Őr: ha bármelyik seed vLLM val-lefedettsége@95 ≤ L1★-é (0,596), a teszt nem nyílik meg.
      Ez a hibás tréning kiszűrésére szolgál, nem választási szabály.
    - A tükrözött val-adaton (valós HF- és vLLM-kiolvasásokkal) a próbafutás jelei: a top-címke
      HF↔vLLM egyezése L0-n 0,940, L3-mal 0,988, a LoRA-hatás korrelációja r = 0,971.
    - Lánc: `F3-hangolas → F3-megerosites → F4`. Várható befejezés: a vLLM-es H1 ~00:15
      (10-07), az F4 vége ~07:00 (10-07). Ha a 2 epochos h3 nyer, mindkettő ~4 órával később.
  - **Licenc- és szerződés-kapu feloldva (Dani, 2026-10-06):** „licensz aggályokat feloldom,
    használhatjuk”. A licenc-jegyzet három nyitott pontja lezárva. A 10. pont publikálási
    táblája ettől kezdve csak az eredménytől függ; az „F1-kapu bukik, vagy a licenc-jegyzet
    tiltja” sor licenc-ága nem áll fenn.
  - **F6 előkészítve (2026-10-06, GPU nélkül):**
    - `eszkozok/f4_riport.py`: az F4 JSON-jaiból kitölti a 14. pont eredménylapját
      (`eredmenyek/F4/eredmenylap.md`). Rétegenkénti táblák, a hipotézis-ítéletek CI-vel, az
      ismétlési zaj, a javítatlan teszten mért érzékenység, címkezaj, K0c, példány-billenés,
      teljesítmény.
    - Az F4 vezénylő 7., nem végzetes lépéseként fut. A tükrözött próbaadaton végigfutott.
    - `f4_elemzes.py`: a kimenetbe bekerülnek a bemenetek útvonalai is.
    - `hf-release/dataset/README.md` (dataset card) és `publikacio/tanulmany-vaz.md`
      (tanulmány-váz): az eddigi számokkal, `[kitöltendő]` helyekkel az F4-hez.
  - **F3 hangolás kész (2026-10-06 13:33), győztes: h2 (`--eps 0.05`).**
    - vLLM val, `temp` kar (lef@95 / lef@90 / AURC): alap 0,755 / 0,755 / 0,00091 · h1 (lr 2e-4)
      0,764 / 0,764 / 0,00156 · **h2 (eps 0,05) 0,759 / 0,759 / 0,00086** · h3 (2 epoch) 0,760 /
      0,760 / 0,00168.
    - A lefedettségek mind 2 ponton belül vannak (holtverseny), így a szabály szerint az AURC
      döntött. A h2 előnye az alaphoz képest 0,00005, ami zajszintű, de a szabály szerinti
      választás. Mind a négy kar a 0,764-es val-plafon közelében áll; a választás tétje kicsi.
    - A megerősítés automatikusan indult (13:34): `l3mixse_h2_s2`, `l3mixse_h2_s3`. Utána az F4.
      Mivel nem a 2 epochos h3 nyert, az F4 menetrendje marad (H1 ~00:15, F4 vége ~07:00, 10-07).
  - **F3 megerősítés kész (2026-10-06 19:50).** A h2-konfiguráció (`--eps 0.05`) három seeddel, vLLM val,
    `temp` kar (lef@95 / lef@90 / AURC / ECE / precízió@95):
    - s1: 0,759 / 0,759 / 0,00086 / 0,020 / 0,968
    - s2: 0,769 / 0,775 / 0,00184 / 0,021 / 0,965
    - s3: 0,749 / 0,749 / 0,00063 / 0,016 / 0,973
    - A seedek közti szórás (@95: 2 pont, AURC: háromszoros) jóval nagyobb, mint a hangolás karjai
      közti különbség (AURC 0,00005). A hangolás holtverseny-olvasata ezzel igazolva. Mindhárom seed
      messze az L1★ (0,596) fölött van, az F4 seed-őre átengedi őket.
  - **F4 indítási hiba és javítás (19:50 → 19:54).** A lánc a megerősítés után nem tudta elindítani az
    `f4_vezenylo.sh`-t („Permission denied”), mert a laptopon létrehozott fájl futtatási jog nélkül
    szinkronizálódott. Javítás: `chmod +x` mindkét helyen, `bash -n` ellenőrzés, újraindítás a lánccal
    (`lanc.sh F3-megerosites F4`). Az F4 19:54-kor indult. A késés 4 perc, mérést nem érint.
    Tanulság: új vezénylő-szkriptnél a szinkron előtt `chmod +x`, és a láncot egy szárazfuttatással
    (`test -x`) ellenőrizni.
  - **F4 kész (2026-10-07 05:52), eredmények a laptopon (`eredmenyek/F4/eredmenylap.md`).**
    ⚠ Az önellenőrzés (lent) felülírja: a T-szállító ítélete nem tesztelhető (szállító-szivárgás), a Δ-k
    bootstrap-mediánok (pont-Δ: H1 +13,7), a 97/112-es összevont előjelpróba elvetve.
    - **H1 igaz** (vLLM, pool): L3 lef@95 0,752 vs. L1★ 0,616, Δ = +12,8 pont, 95% CI [4,8; 21,0];
      AURC 0,0018 vs. 0,0273, Δ = −0,0255 [−0,0300; −0,0213]. A HF-motoron +10,4 pont [4,0; 18,5].
    - **H2 mind a négy rétegen „általánosít”:** T-szállító +16,3 pont (14 szállítós permutáció
      p = 0,0001), T-kategória +8,8, T-közeli +9,3, T-távoli +8,0 (vLLM).
    - **H4 igaz** (L2a, 40. réteg, HF: +6,4 pont), **H5 igaz** (ECE 0,043 → 0,010).
    - **H3 cáfolt, egyedül a (d) miatt.** (a) aktiválás ✓; (b) a LoRA-hatás HF↔vLLM r = 0,976 ✓;
      (c) alsó korlát +3,6 pont ✓. (d): egy `--enable-lora`-s példányon a LoRA nélküli kérések
      top-címke-egyezése egy LoRA nélküli példánnyal 0,937, míg a LoRA nélküli példányok egymás közt
      1,000 (küszöb −1 pont). A LoRA-s példányok egymás közt is billegnek (L0 4,3%, 5 numerika-mód 5
      példányon), a LoRA nélküliek nem. Utólagos, leíró elemzés (nem előre rögzített): a LoRA nélküli
      kérések pontossága 0,761–0,763 a LoRA-s és 0,765 a LoRA nélküli példányokon; a billenések a
      bizonytalan itemeken vannak (medián bizonyosság 0,43), irányuk kiegyenlített (97 jóra, 112
      rosszra, előjelpróba p = 0,33). A (d) bukása a kimenet változását jelzi, kimutatható
      pontosságromlás nélkül.
    - Ismétlési zaj (L0 ↔ L0′, ugyanazon a példányon): 0 billenés — a páros, egy-példányos design áll.
      Címkezaj a teszten 0,4% (felső 95%: 1,4%). Kétértelmű itemeken a soft-gold találat 97,5–98,3%.
    - Kiszolgálás (fő példány, 512 item): `lora_request` c = 1-nél 6,2 döntés/s, p50 161 ms (LoRA
      nélküli kérés ugyanott 6,4/s, 158 ms); c = 32-nél 15,2/s (16,9/s LoRA nélkül, −10%). Az (a)
      LoRA nélküli példány friss H3-példányon mért (4,7/s), a (b)-vel nem vethető össze közvetlenül.
    - A riport két javítása utólag (laptop, `f4_riport.py`): a HF-szakasz H3-sora „motorközi, lásd
      vLLM” lett a téves „h3.json hiányzik” helyett; a H3-sor kiírja a (d) számait, és bekerült az
      utólagos leíró elemzés. A `reboot_hook.sh` eltávolítva (10-07 06:22), a measurement-hosten nem fut semmi.
    - **Publikálási szabály (10. pont):** a „H1 igaz, H2 általánosít, H3 bukik” sor érvényes: adatkészlet
      publikus, adapter publikus megjegyzéssel, a kiszolgálási negatív eredmény a tanulmány része.
      Az előre rögzített megjegyzés („csak HF/peft, vLLM-kiszolgálás nem igazolt”) pontatlan a tényleges
      bukásra: az adapter vLLM-kiszolgálása (a)–(c) szerint igazolt, a (d) a közös példányon futó LoRA
      nélküli forgalom kimenetének változásáról szól. Döntés lent (10-07).
- **2026-10-07 — Publikálási megjegyzés: a valóságot írjuk le (Dani, „2-es legyen”).**
  - Az ítélet nem változik: **H3 cáfolt**, a 10. pont „H1 igaz, H2 általánosít, H3 bukik” sora érvényes
    (adatkészlet publikus, adapter publikus megjegyzéssel, a kiszolgálási negatív eredmény a tanulmány része).
  - **Eltérés az előre rögzített szövegtől:** a megjegyzés nem a „csak HF/peft, vLLM-kiszolgálás nem
    igazolt” lesz, hanem a tényleges bukás leírása (a végleges szöveg a lenti mélyfúrás után, a tanulmány
    4.4. pontjában és a dataset cardban). Ok: a rögzített szöveg azt az esetet írta le, amikor az adapter
    vLLM-ben nem működik; itt működik, és a (d) mást mér.
- **2026-10-07 — H3(d) mélyfúrás (utólagos, leíró; Dani kérése: „a ~6% gyanús”; az önellenőrzés után pontosítva).**
  Eszköz: `eszkozok/f4_h3_modok.py` → `eredmenyek/F4/h3_modok.json`; az eredménylapba bekerült.
  - **Mérési hibát nem találtunk.** A 10 friss példány soraiban a prompt, a jelöltsorrend, a tokenszám és
    a modellnév egyezik, egyik sorból sem hiányzik címke, és az L0 az adapter betöltése előtt futott.
  - **Az adapter nem szivárog át a LoRA nélküli kérésekre — soros forgalomban.** A fő példányon az L0 és az
    L0′ (három adapter be- és kitöltése után, a 3. még betöltve) közt 0 billenés, 98,9% bájtazonos sor.
    Vegyes köteget (LoRA-s és LoRA nélküli kérés egyszerre) nem mértünk.
  - **Az ok a számítási út váltása.** A megmaradt logok szerint `--enable-lora` mellett „Using fused MoE LoRA
    implementation” és `TRITON` Fp8 MoE backend fut (13 korábbi indítás, F0–F3), nélküle `DEEPGEMM` (az egyetlen
    megmaradt LoRA nélküli log, nolora_k5). A H3 LoRA-s példányainak logja felülíródott, rájuk ez következtetés.
    Az `--enable-lora` a lefordított gráfot is megváltoztatja (más torch.compile-kulcs, `PunicaWrapperGPU`), így
    nem bizonyított, hogy az eltérés a MoE-backendből jön. Döntő kontroll: LoRA nélküli példány kényszerített
    Triton MoE-backenddel (nem futott).
  - **Két összetevő:**
    - *Rendszeres eltolódás:* a LoRA-s módok a LoRA nélkülihez képest egy irányba tolódnak (átl. Δ log p(A)
      +0,21, entrópia 0,456 vs. 0,444), egymáshoz képest nem (±0,006). A HF félúton van (+0,10).
    - *Indításonkénti módsorsolás:* a LoRA nélküli példányok mind az öt indításkor 0 billenéssel egyeztek (nem
      bitazonosan: 991–996/1000 bájtazonos sor), a LoRA-sok három módba estek ({k1, k3, k4}, {k2}, {k5, fő
      F4-példány}; a fő példány és a k5 977/1000 bájtazonos). **Mód** itt: páronként ≤ 1% top-címke-billenés
      (utólagos definíció; 5 példányból alsó becslés). Az F4-bejegyzés „5 numerika-módja” a bitszintű
      próba-ujjlenyomat, az más mérce. A módok egymás közt 52–64, a LoRA nélkülitől 58–77 billenésre vannak
      1000 itemből. A módsorsolás oka nem azonosított.
  - **Kimutatható romlás nincs, kb. ±1,3 pontos felbontással.** A HF-referencia minden módtól egyformán messze
    van (50–63 billenés), a LoRA nélkülitől is. A pontozott itemeken (n = 875) a LoRA-s módok pontossága a LoRA
    nélkülitől −0,1…+0,1 pont (95% CI kb. ±1,3), a billenések módonként kiegyenlítettek (14/15, 17/16, 20/19).
    A korábbi „97 jóra, 112 rosszra” összesítés öt példányt vont össze (ebből három egy mód: ál-ismétlés), és a
    kétértelmű itemeket is számolta — elvetve.
  - **A H1 módfüggetlen.** A fő példány val-ján rögzített temperature és τ@95 mellett (perm 0, `temp` kar)
    az L0 lef@95 0,597–0,609 minden példányon, a LoRA nélkülieken is; az L3 − L0 +12,3…+13,7 pont.
  - **A (d) bázisa (tanulság), de a bukás nem ebből jön.** A bázist („LoRA nélküli példányok egymás közt”) a
    K0a-2 alapján abban a hitben terveztük, hogy azok is billegnek 2–4%-ot; a K0a-2 viszont konfigurációk közt
    mért. A bázis 1,000 lett. A bukás azonban bármely ésszerű bázissal megáll: a LoRA-s példányok egymás közti
    egyezése is csak 0,957, a keresztegyezés 0,937.
  - **Mellékmegfigyelés (teljesítmény):** a LoRA nélküli, DeepGEMM-es példány c = 1-nél 4,7 döntés/s
    (p50 212 ms), a Tritonos LoRA-s példány LoRA nélküli kéréssel 6,4/s (158 ms). Backend- és
    példánykülönbség együtt, egyetlen mérés; nem a LoRA-támogatás ára.
  - **Tanulságok a 01-es körre:** (1) a `subject_stop` minden példány logját ugyanabba a fájlba írja
    (`ldh-subject.log`), példányonkénti log kell; (2) a H3-példányok blokkosan futottak (előbb az 5 LoRA-s, aztán
    az 5 LoRA nélküli), legközelebb váltakozva.
- **2026-10-07 — Önellenőrzés a kör végén (Dani kérése).** Két független átnézés (kódhelyesség; tervezés és
  előregisztráció), a leleteket ellenőriztem. Eszköz: `eszkozok/f4_onellenorzes.py` →
  `eredmenyek/F4/onellenorzes.json`; az eredménylap új „Önellenőrzés” szakasza.
  - **Ami szilárd:**
    - a `vllm_f4.json` a mostani kódból bitre azonosan újraszámolható, az eredménylap bájtra;
    - a gyors bootstrap 15 valódi klaszter-húzáson egyezik a referenciával;
    - a τ, a temperature, a kar- és a seed-választás csak val-alapú, az F2/F3 kimeneteiben nincs teszt-sor;
    - a fagyasztási hash-t az F3 és az F4 is ellenőrizte;
    - a HF-ág sorrendje, címkéi és tokenszámai egyeznek a vLLM-ével;
    - a szállító-permutációban mind a 14 szállító nyeresége pozitív.
  - **[ÖLŐ] A T-szállító réteg szállítói nem kitartottak.** A terv (4. pont): „16 csak-teszt szállító”.
    - A tesztben 14 szállító van, és mind a 14 szerepel a train-ben is (900 sor, a train 16%-a). A (szállító,
      cikk) párok nem fednek át.
    - Ok: `eszkozok/generator.py:351-356`. Ha egy teszt- vagy val-pár cikkének nem volt train-párja, a kód magát
      a pár szállítóját tette a train-be, nem egy másik szállítóét.
    - Ugyanez a val-szállítónál is: 8 szállító, 910 train-sor.
    - Split-átfedés-audit nem volt (az `auditok.py` csak shortcutot, nehézséget és valószerűséget néz).
    - **Következmény:** a H2 T-szállító ítélete **nem tesztelhető** (a réteg nem a rögzített definíció szerint
      épült). A számolt Δ (+17,4 pont) leíró: látott szállító × látott cikk, új pár.
    - Feltáró: a valóban nem látott szállítókon (T-távoli, és a T-közeli fele) a nyereség +9,1 / +9,2 pont, a
      kategóriaváltással keveredve. A T-közelin belül a látott szállítókon +11,7.
    - A T-kategória ítélete érvényes: a gyökerek és a cikkek diszjunktak, szövegduplikátum 0.
    - A 10. pont táblája ezt az esetet nem fedi: az adapter publikálásáról Dani dönt.
  - **[KOMOLY] A @95-előny plafon és X-felismerés.**
    - A pontozott teszt nem-X aránya 0,756, az L3 lef@95-e 0,752: a plafonon van.
    - Az L1★ hibái @95-ön 42/46-ban X-gold itemek, amelyeket besorolt; @90-en 150/164.
    - A nyereség mérete a 25%-os X-arány függvénye: X 10% → +3,5 pont, 5% → +1,1 pont (ritkítással).
    - „+13 pont automatizálás” X-arány nélkül nem állítható.
  - **[KOMOLY] AURC-definíció.**
    - A görbe a kar saját nem-X döntéseinél ér véget, így a több X-et mondó kar kisebb AURC-t kap.
    - Közös lefedettségre (0,745) vágva: L1★ 0,0108, L3 0,0012–0,0019, tehát 6–9-szeres, nem 15-szörös.
    - Kockázat 0,7-es lefedettségen: 4,8% vs. 0,4%. A H1(b) minden változatban megáll.
  - **[KOMOLY] Az L1★ temperature-e a perm-0 kiolvasásra illesztett,** de a permutáció-átlagra alkalmazzuk.
    - Ezért az L1★ alulmagabiztos: ECE 0,043.
    - A permutáció-átlagra illesztve az ECE 0,026, a lef@95 0,607; T = 1 mellett az ECE 0,018.
    - A H5 megáll, de a hatás −0,016 körüli, nem −0,035.
  - **[KOMOLY] A közölt Δ a bootstrap-medián volt, nem a pontkülönbség.**
    - Pontkülönbség: H1 +13,7 (medián 12,8), T-kategória +9,8 (8,8), HF +11,0 (10,4).
    - Az eredménylap most mindkettőt mutatja, és p < 0,0001-et a 0,0000 helyett.
  - **[KOMOLY] A K0d-bejegyzés (10-03) állítása pontatlan.**
    - Ott: „a DeepGEMM-et erre a modellre … kikapcsolja”. A LoRA nélküli példány logja szerint a figyelmeztetés
      („Auto-disabled DeepGemm … Falling back to CUTLASS”) mellett a MoE mégis `DEEPGEMM`-mel fut, „DeepGEMM E8M0
      enabled” mellett.
    - A kikapcsolás tehát legfeljebb a lineáris rétegeket érinti.
  - **[KOMOLY] A valószerűség-rés kezelése elmaradt.**
    - A 0,978-as valószerűség-AUC ellensúlyaként tervezett T-gen réteg és R-det nem futott.
    - A teszt X-itemjeinek 77%-a (564/737) kényszerített X(a), természetes X(a) csak 74.
    - Egyetlen generátorcsalád adja a train-t és a tesztet.
  - **Nem naplózott eltérések a tervtől (most naplózva):**
    - a rétegenkénti MDE nem készült el, a `mde.py` csak a poolt számolja;
    - az MTP nélküli chat decode tok/s nem mérve;
    - az „X mozgó részhalmaz” bontás nem készült, mert az F4 `--move-none-frac 0`-val olvasott;
    - a társ-elsődleges AURC-döntés (10-05) az F2 L2a val-AURC-jének ismeretében született (az ítélet ettől
      független, mert a @95 egyedül is szignifikáns).
  - **[KISEBB]:**
    - az eredménylap L1★ döntés/s-e az L0-é volt; a permutáció-átlag 4 kérés, javítva negyedére;
    - a precizitás-bukás nem volt jelölve (vLLM L0 T-közeli 0,924 < 0,93), most ⚠;
    - a szállító-permutáció rögzített val-τ-val számol, p = 2/2¹⁴;
    - a vLLM-en a H5 egyelemű „Holm-család”;
    - a temperature-bizonytalanság nem kerül a CI-be;
    - sorszöveg + gold duplikátum a train-nel: T-szállító 47/1627, T-belső 10/474, T-kategória 0;
    - a pilot és az F1 közt 236 id ütközik (tartalom eltér, szivárgás nincs);
    - az F3 kar-választás zaj volt: a példányok közti L3-AURC-szórás 0,0006–0,0010, a döntő különbségek
      0,00005–0,0003.
  - **Javítva:** az eredménylap (pont-Δ, p-kiírás, T-szállító ítélet, döntés/s, ⚠, H3-szakasz, önellenőrzés),
    a tanulmány-váz, a dataset card (a cikkszám 3514, nem ~5000; a shortcut-audit leírása; nincs
    split-szivárgás-audit), az adapter-card váz és a docai-0122-jegyzet.
  - **A 01-es körre:** generátorjavítás (a kitartott szállító párja sosem kerülhet a train-be) és kötelező
    split-átfedés-audit a fagyasztás előtt (szállító, cikk, pár, normalizált szöveg).
  - **Nyitott (Dani döntése):** a T-szállító kezelése (nem tesztelhetőként marad, vagy új, valóban kitartott
    szállítós réteg készül előre rögzített kiegészítésként), és ettől függően az adapter publikálása.
- **2026-10-07 — Döntés az önellenőrzés után (Dani).**
  - **T-szállító:** új, valóban kitartott szállítós réteg készül, előre rögzített kiegészítésként (00b). Javított
    generátor, csak-teszt szállítók a már látott cikkekre, címke-triage és emberi átnézés, fagyasztás, majd a
    **meglévő** adapterek kiolvasása vLLM-en és HF-en. Újratanítás nincs. A kiegészítés protokollja a generálás
    előtt kerül a runbookba.
  - **Adapter:** nem megy ki, amíg az új réteg eredménye nincs meg. A 10. pont logikája marad: a szállítói
    általánosítás is kell.
- **2026-10-07 — 00b protokoll rögzítve (15. pont), K00b/A indult (07:32).**
  - Új eszközök:
    - `generator.py ujszallito`: az F1-ből épít, a régi T-szállító párjai és sorai nélkül; az új szállítók
      csak látott cikkeket kapnak;
    - `split_audit.py`: kemény kapu; az F1 T-szállítóján lefuttatva mind a 14 szállítót megfogja;
    - az `osszeallit.py` és az `auditok.py` (`--splits`) átengedi az új splitet;
    - `k00ba_vezenylo.sh`.
  - Lokális próbafutás LLM nélkül (álnevekkel):
    - 16 új szállító, 2156 pár, ebből 37 X(b), szállítónként 73–309 sor;
    - szállító- és pár-átfedés 0, nem látott cikk 0, X(b) a train/val-ban 0;
    - az új sor-id-k (`r010377`–) nem ütköznek az F1-gyel, a train-sorok bájtra azonosak.
  - Az első próbában a 16 új szállítóból csak 12 kapott sort, mert 4 csak kitartott gyökeret szolgált ki
    (az F1-ben ugyanezért lett 16-ból 14). Javítás: az S2-vel húzott 48 jelöltből az első 16, amely nem
    kitartott gyökeret is kiszolgál; a 15. pont ennek megfelelően pontosítva, a generálás előtt.
  - A measurement-hosten `chmod +x` + `bash -n` + `test -x` után indult. Az újraindulás utáni folytatás hookja
    újra telepítve (a K00b/A végén eltávolítandó). Várható vége ~11:30 (a két bíráló bootja a hosszú).
- **2026-10-07 — K00b/B (mérés) előkészítve, adat nélkül.**
  - `k00bb_vezenylo.sh`: hash-ellenőrzés (réteg + F1), egyetlen friss vLLM-példány, a vLLM-elemzés, majd HF
    és a HF-elemzés. A 15. pont pontosítva: az L3 a perm 0-t olvassa. Becsült idő ~3 óra (vLLM ~1 óra,
    HF ~2 óra).
  - `k00b_elemzes.py`: az F4 T-szállító rétegén validálva (pont-Δ +0,1736, permutációs p 0,00012, mint az
    F4-ben).
  - `atnezes.py`: `--strata` és `--n-tobbi` kapcsoló az egyrétegű átnézéshez.
  - **Sorrend a K00b/A után (laptop):**
    1. `sync.sh back`;
    2. `atnezes.py minta --gen adat/k00b --biralo eredmenyek/K00b/biralo --out adat/k00b/atnezes
       --strata T-ujszallito --n-tobbi 120`, majd `html`;
    3. Dani átnézése;
    4. `osszesit` és `alkalmaz`;
    5. fagyasztás: `adat/k00b/meres/items_T-ujszallito.jsonl`, `eredmenyek/K00b/fagyasztas.sha256`,
       `FAGYASZTVA.json`;
    6. `sync.sh to`, majd indulhat a K00b/B.
- **2026-10-07 — K00b/A kész (07:32–08:32), átnézés és fagyasztás (12:40).**
  - **Kapuk:**
    - split-átfedés 0: a 16 szállító máshol nem szerepel, pár- és X(b)-átfedés 0, minden cikk látott;
    - shortcut CV AUC 0,466 (≤ 0,55);
    - a nehézség a sávban: a BM25 top-1 gold 0,655, az F1 T-szállítón 0,708 volt.
  - **A réteg:** 2107 item, 25% X (441 kényszerített X(a), 50 természetes, 35 X(b)), 20,6% kétértelmű.
    Train-nel azonos sorszöveg + gold: 69 (3,3%; az F1 T-szállítón 47/1627, arányában ugyanannyi).
    *Pontosítva a K00b/B után:* ez a 00b-generátor saját train-fájljához mért szám volt; az F1-trainhez
    (amin az adapterek tanultak) mérve 65 (3,1%). A kapu az F1-train ellenében is átmegy.
  - **Bírálók:** Llama és Mistral, mind a 2107 itemre válaszoltak.
  - **Dani átnézése:**
    - a minta 150 item: mind a 30 konszenzus-flag + 120 rétegzett véletlen;
    - 149 egyezett a golddal, 1 konszenzus-flages item kétértelmű lett (K);
    - a becsült maradék zaj 0,18%, felső 95%-os korlátja 1,49% (kapu ≤ 2%) ✓.
  - **Fagyasztás:**
    - `adat/k00b/meres/items_T-ujszallito.jsonl`: 2107 item, 1673 pontozott, 16 szállító, 24,5% X;
    - `eredmenyek/K00b/fagyasztas.sha256`, `FAGYASZTVA.json`;
    - a measurement-hosten tartalom szerint ellenőrizve.
  - A K00b/B indul; az újraindulás utáni folytatás hookja újra telepítve.

- **2026-10-07 — K00b/B kész (12:40–16:07): H2-szállító′ = általánosít.**
  - **Futás:** vLLM 12:40–13:52 (egy friss `LORA=1` példány), HF 13:53–16:07. A próbahalmaz eleje és vége
    0,84 / 0,84; az ujjlenyomat a példányon belül eltér, ahogy az F4-ben is (687d… / 663b…). Hash-ellenőrzés
    (a réteg és az F1) OK. A hook eltávolítva.
  - **Elsődleges motor (vLLM), 1673 pontozott item, 16 szállító, nem-X arány 0,755:**

    | | L1★ | L3 (s1 / s2 / s3) |
    |---|---|---|
    | lef@95 (precizitás) | 0,568 (0,965) | 0,763 / 0,769 / 0,758 (0,962 / 0,957 / 0,968) |
    | X-fedés | 0,42 | 0,90 / 0,89 / 0,92 |
    | AURC közös 0,759-es lefedettségig | 0,0176 | 0,0019 / 0,0033 / 0,0019 |
    | kockázat 0,7-es lefedettségen | 6,0% | 1,2% / 1,8% / 1,3% |
    | ECE | 0,067 (perm-átlag-T: 0,045) | 0,017 / 0,019 / 0,015 |

    - **Δ lef@95 = +19,5 pont [10,2; 29,2] → általánosít.** Egzakt szállító-permutáció p = 3,1·10⁻⁵
      (2/2¹⁶, a legkisebb elérhető). Érzékenység (perm-átlagra illesztett T): +20,8.
    - @90: +4,6 [0,4; 10,1] (az F4-ben @90-en nem volt különbség).
  - **HF (jelentve):** L1★ 0,594, L3 0,760 / 0,772 / 0,755; Δ +16,8 [8,6; 26,4] → általánosít, p = 3,1·10⁻⁵;
    @90 +3,7 [−0,5; 9,3]; AURC közös 0,756-ig 0,0167 vs. 0,0014–0,0034; kockázat 0,7-nél 6,1% vs. 0,8–1,7%.
  - **Önellenőrzés (utólagos, leíró; `eszkozok/k00b_onellenorzes.py` → `eredmenyek/K00b/onellenorzes.json`):**
    - **Split a tényleges tanítóhalmaz ellenében.** A 00b-generátor `adat/k00b/items_train.jsonl`-je eltér az
      F1-étől (az S5–S8 újrafuttatása miatt), a split-audit a duplikátumot ehhez mérte. A train-párok
      azonosak (2871 pár, 2595 cikk), így a szállító-, pár-, látott-cikk- és X(b)-feltétel az F1-re is áll.
      Az F1-trainhez mért duplikátum 65 (nem 69). Az `split_audit.py` új `--train` kapcsolót kapott, az
      F1-train elleni futás: `eredmenyek/K00b/audit/split_f1train.json`, kapu OK.
    - **Mind a 16 szállítón pozitív a nyereség:** vLLM +9,4…+35,4, HF +6,4…+35,9 pont.
    - **A duplikátumok nem hordozzák:** a 65 sorszöveg+gold-duplikátum nélkül +19,5; a 104 azonos
      sorszövegű item nélkül +19,7; a 20 item nélkül, amelynek cikkéhez csak train-pár van (train-item
      nincs), +19,7.
    - **X-fajtánként** (vLLM): az L1★ X-fedése mindhárom fajtán ~0,40; az L3-é kényszerített X(a)-n 0,92
      (n = 344), természetesen 0,80 (n = 34), X(b)-n 0,81 (n = 32). A nyereség nagyobb része a
      generátor kényszerített X-ére esik.
    - **Miért kétszerese a feltáró becslésnek (~+9)?** A becslés a T-közeli nem látott szállítós itemjeiből
      jött, ahol a cikk sem látott. A `T-ujszallito` szerkezete (látott cikk, új szállító) a régi
      T-szállítóé, és a számai is azt követik:

      | réteg (vLLM) | L1★ | L3 | Δ | X(a)-arány az X-ek közt |
      |---|---|---|---|---|
      | T-belső | 0,639 | 0,775 | +13,6 | 0,68 |
      | T-szállító (szivárgott) | 0,572 | 0,746 | +17,4 | 0,86 |
      | T-közeli | 0,643 | 0,748 | +10,4 | 0,65 |
      | T-távoli | 0,666 | 0,757 | +9,1 | 0,73 |
      | **T-ujszallito** | 0,568 | 0,763 | +19,5 | 0,84 |

      Leíró megfigyelés, nem oksági állítás: ahol az alap gyengébb és több a kényszerített X, ott nagyobb a
      nyereség. A H2-szállító′ ítéletét ez nem érinti (a CI alsó határa +10,2).
  - **Következmény (15. és 10. pont):** H1 igaz, H2 mindkét rétegen „általánosít” (T-kategória az F4-ből,
    szállító′ a 00b-ből), H3 bukik → az adatkészlet publikus; az adapter publikus a 4.4. pont
    kiszolgálási megjegyzésével (a 2-es döntés szerinti, valóságot leíró szöveggel). A tényleges
    feltöltés Dani jóváhagyására vár; nyitott: a dataset licence, a kiadott seedek köre, a HF-azonosítók.
  - **Tanulság a 01-hez:** a split-audit referenciája mindig a ténylegesen használt tanítóhalmaz legyen,
    ne a generátor újraépített train-je.

- **2026-10-07 — Döntés (Dani): a HF-publikálás a 01-es kör után.** Az adatkészlet és az adapter a 10. és
  a 15. pont szerint publikus lehetne, de egyelőre nem kerül fel a HF-re. Előbb a 01-es kör fut le, a
  feltöltésről utána döntünk. Nyitott marad: a dataset licence, a kiadott seedek köre, a HF-azonosítók.
  *Felülírva még aznap este (lent).*

- **2026-10-07 — Döntés (Dani): a 00 kiadása most, a 01 előtt.** Indok: a JEV-27B és a Jev Decision Index
  (55 hasonló modell) mutatja, hogy a terület gyorsan mozog. A mi különbségünk (explicit „egyik sem”, lefedettség
  precizitás-célon valódi címkén, kitartott rétegek, előregisztráció, a vLLM `--enable-lora` kiszolgálási lelete)
  most friss. A 01 a 00 eredményein nem változtat. Döntések:
  - adatkészlet: CC-BY-4.0;
  - névtér: `k3dani`;
  - adapter: mindhárom seed (s1 a fő, s2/s3 mellette).
  - Sorrend: export és ellenőrzés, Dani végső jóváhagyása, feltöltés (előbb privátként, átnézés után publikus).
  - A teljes tanulmány később megy ki (`docai-evals` / blog).

- **2026-10-07 — 00 kiadás: privát feltöltés (19:15).** Az `eszkozok/hf_export.py` állította össze; a forrás a
  `hf-release/` kártyái és a `decision_prompt.py`. A kimenet a measurement-hosten: `hf-release-00/`.
  - **Adatkészlet:** `k3dani/hu-invoice-catalog-decisions` (CC-BY-4.0, privát).
    - Splitek: train 5593 / validation 1006 / test 3534 / test_new_suppliers 2107.
    - Ellenőrizve: a fagyasztott hash-ek, egyedi id-k, tiltott minta nincs, `meta.atnezes` kivéve.
  - **Adapter:** `k3dani/Qwen3.6-35B-A3B-invoice-decision-lora` (Apache-2.0, privát).
    - Tartalom: az s1 a gyökérben (peft) és a `vllm/` alatt; s2/s3 a `seed2/` és `seed3/` alatt; `calibration.json`
      (a val-on illesztett T és τ seedenként); `decision_prompt.py`; MANIFEST.sha256.
    - Az `adapter_config.json` helyi útvonala a publikus alapmodellre cserélve.
  - **Következő lépés:** Dani átnézi a HF-en, a szavára publikusra váltom. A tanulmány később megy ki.
- **2026-10-07 — 00 kiadás: publikus (Dani jóváhagyásával).** Egy javítás után: az `adapter_config.json`
  `task_type` mezője `null` helyett `CAUSAL_LM` (a HF kártyája figyelmeztetett, a betöltést nem érinti), az
  `hf_export.py`-ban is javítva. Mindkét repó publikus, névtelenül ellenőrizve: adatkészlet 7 fájl, adapter 17 fájl.
  - https://huggingface.co/datasets/k3dani/hu-invoice-catalog-decisions
  - https://huggingface.co/k3dani/Qwen3.6-35B-A3B-invoice-decision-lora
  - Hátra van: a tanulmány (`docai-evals` / blog).
