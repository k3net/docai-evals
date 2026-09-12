# Qwen3.8-Flash-Next GB10 vLLM stabilitási validációs runbook

**Célgép:** `spark-dev` — NVIDIA DGX Spark / GB10, Ubuntu 24.04, ARM64, 128 GB unified memory  
**Dátum:** 2026-09-12  
**Cél:** a jelenlegi működő konfiguráció érintetlenül hagyása mellett validálni az újabb vLLM-javításokat, különösen a QSA-memóriakezelést, a Mamba-state kezelést, a determinisztikus Top-K-t és a prefix cache helyességét.

## 1. Mit validálunk?

Három kart érdemes összehasonlítani:

| Kar | Tartalom | Szerep |
|---|---|---|
| A — PROD CONTROL | A jelenlegi pinelt, már validált spark-dev image | Referencia, nem módosítjuk |
| B — v0.29 BUNDLE | A `blazux/qwen3.8-Flash-DGX` aktuális `v0.29` profilja | Hivatalos vLLM release + GB10 patchkészlet |
| C — EXPERIMENTAL | B vagy friss vLLM `main`, kiegészítve a még nyitott PR-ekkel | Upstream-validáció, külön image-ben |

Kiemelt változások:

- [vLLM #55450](https://github.com/vllm-project/vllm/pull/55450) — beolvadt Mamba-state retirement javítás;
- [vLLM #56500](https://github.com/vllm-project/vllm/pull/56500) — bounded, újrahasznált QSA prefill-logits workspace;
- [vLLM #55122](https://github.com/vllm-project/vllm/pull/55122) — determinisztikus `persistent_topk`;
- [vLLM #54948](https://github.com/vllm-project/vllm/pull/54948) — FlashInfer MoE fused-finalize kikapcsolhatósága;
- [vLLM #53798](https://github.com/vllm-project/vllm/pull/53798) és [#54076](https://github.com/vllm-project/vllm/pull/54076) — align-mode prefix-cache resume javítások;
- [vLLM #54129](https://github.com/vllm-project/vllm/pull/54129) — mmap PLE;
- [blazux/qwen3.8-Flash-DGX](https://github.com/blazux/qwen3.8-Flash-DGX) — single-Spark recept és patchkészlet;
- [saját reprodukció](https://github.com/k3net/docai-evals/tree/master/experiments/2026-08-28-qwen38-flash-next-nvfp4-topk-nondeterminism-gb10).

## 2. Biztonsági szabályok

1. A működő production image-et ne buildeld újra és ne taggeld át.
2. Minden candidate image kapjon új, dátumozott taget.
3. Egyszerre csak egy Qwen3.8 konténer fusson: a GB10 unified memóriája miatt két modell egyidejű indítása nem reális kontroll.
4. A kontroll eredményeit előbb mentsd el, csak utána állítsd le.
5. Nyitott PR-t mindig konkrét commit SHA-val rögzíts; a mozgó PR-head nem reprodukálható.
6. Ha bármely patch nem alkalmazható tisztán, állj meg annál a karnál. Ne javíts konfliktust dokumentálatlanul.
7. A teszt végén a production image-et indítsd vissza, és futtasd le újra a smoke tesztet.

## 3. Munkakönyvtár és eredménykönyvtár

```bash
ssh spark-dev

export RUN_DATE="$(date -u +%Y%m%dT%H%M%SZ)"
export RUN_ROOT="/opt/vllm/qwen38-validation-${RUN_DATE}"
export RESULT_ROOT="${RUN_ROOT}/results"

sudo mkdir -p "${RESULT_ROOT}"
sudo chown -R "$(id -u):$(id -g)" "${RUN_ROOT}"
```

Ellenőrzés:

```bash
printf 'RUN_ROOT=%s\nRESULT_ROOT=%s\n' "${RUN_ROOT}" "${RESULT_ROOT}"
test -d "${RESULT_ROOT}"
```

## 4. Kiindulási állapot rögzítése

```bash
{
  date -Ins
  uname -a
  uname -m
  nvidia-smi
  docker version
  docker info
  docker ps --no-trunc
  docker images --digests
  df -h
  free -h
} > "${RESULT_ROOT}/00-host-inventory.txt" 2>&1
```

A jelenlegi Qwen-konténer és image azonosítása:

```bash
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Ports}}' | tee "${RESULT_ROOT}/01-running-containers.tsv"
```

Állítsd be a tényleges neveket:

```bash
export PROD_CONTAINER="qwen38-flash"
export PROD_IMAGE="$(docker inspect -f '{{.Config.Image}}' "${PROD_CONTAINER}")"
export PROD_IMAGE_ID="$(docker inspect -f '{{.Image}}' "${PROD_CONTAINER}")"

printf 'PROD_CONTAINER=%s\nPROD_IMAGE=%s\nPROD_IMAGE_ID=%s\n' \
  "${PROD_CONTAINER}" "${PROD_IMAGE}" "${PROD_IMAGE_ID}" \
  | tee "${RESULT_ROOT}/02-prod-pins.env"
```

Ne folytasd, ha a pin üres:

```bash
test -n "${PROD_IMAGE_ID}"
docker image inspect "${PROD_IMAGE_ID}" >/dev/null
```

## 5. A kar — production kontrollmérés

### 5.1 Smoke teszt

A production checkout könyvtárában:

```bash
cd /opt/vllm/qwen3.8-Flash-DGX
./flash status | tee "${RESULT_ROOT}/A-status.txt"
./flash test 2>&1 | tee "${RESULT_ROOT}/A-smoke-test.txt"
docker logs "${PROD_CONTAINER}" > "${RESULT_ROOT}/A-container.log" 2>&1
```

Ha a checkout máshol található, előbb keresd meg:

```bash
find /opt/vllm -maxdepth 3 -type f -name flash -path '*qwen3.8-Flash-DGX*' -print
```

### 5.2 Konfiguráció és aktív patchek

```bash
docker inspect "${PROD_CONTAINER}" > "${RESULT_ROOT}/A-docker-inspect.json"
docker exec "${PROD_CONTAINER}" python3 -m pip freeze > "${RESULT_ROOT}/A-pip-freeze.txt"
docker exec "${PROD_CONTAINER}" python3 - <<'PY' > "${RESULT_ROOT}/A-runtime.txt"
import os, platform, torch, vllm
print("platform", platform.platform())
print("vllm", getattr(vllm, "__version__", "unknown"))
print("torch", torch.__version__)
print("cuda", torch.version.cuda)
for key in sorted(os.environ):
    if key.startswith(("VLLM_", "NCCL_", "CUDA_")):
        print(f"{key}={os.environ[key]}")
PY
```

### 5.3 Saját determinisztikussági kontroll

Futtasd le a korábbi, változatlan tesztet ugyanazzal a promptkészlettel és paraméterekkel:

```bash
cd /opt/vllm/docai-evals/experiments/2026-08-28-qwen38-flash-next-nvfp4-topk-nondeterminism-gb10
find . -maxdepth 2 -type f -print | sort > "${RESULT_ROOT}/A-experiment-files.txt"
```

Ezután a korábban használt futtatóparancsot indítsd el, és minden stdout/stderr kimenetet ments az alábbi fájlba:

```bash
# IDE másold be a korábban validált parancsot.
# <KORABBI_DETERMINIZMUS_PARANCS> 2>&1 | tee "${RESULT_ROOT}/A-determinism.txt"
```

Kötelező invariánsok:

- azonos első token és elsőtokenes top-logprobok;
- azonos teljes válasz-hash;
- legalább 6 szerverindítás × 10 ismétlés a legerősebb szondán;
- 0/50 instabil elem a KIE suite-ban;
- ne legyen hosszú üres reasoning vagy prompt-visszamondás.

### 5.4 Kontroll leállítása

```bash
cd /opt/vllm/qwen3.8-Flash-DGX
./flash stop
docker ps --format '{{.Names}}' | grep -Fx "${PROD_CONTAINER}" || true
```

Az image-et ne töröld.

## 6. B kar — aktuális blazux v0.29 bundle

Ez a legkisebb kockázatú, azonnal elvégezhető validáció. A v0.29 profil a hivatalos `vllm/vllm-openai:v0.29.0` alapot használja, és erre rétegzi a GB10-specifikus javításokat.

### 6.1 Reprodukálható checkout

```bash
cd "${RUN_ROOT}"
git clone https://github.com/blazux/qwen3.8-Flash-DGX.git candidate-blazux
cd candidate-blazux

git rev-parse HEAD | tee "${RESULT_ROOT}/B-blazux-head.txt"
git status --short | tee "${RESULT_ROOT}/B-git-status.txt"
```

A fájlban szereplő SHA legyen később a publikáció része.

### 6.2 Előellenőrzés

```bash
./flash doctor v0.29 2>&1 | tee "${RESULT_ROOT}/B-doctor.txt"
```

Csak akkor folytasd, ha:

- ARM64 és GB10 felismerve;
- Docker NVIDIA runtime működik;
- nincs más nagy GPU-memóriás konténer;
- van elég szabad lemez;
- a port szabad;
- a checkpoint elérhető.

Ha a production checkpoint más könyvtárban van, ne töltsd le újra. A `./flash doctor v0.29` által jelzett változóval vagy a `profiles/v0.29.env` másolatában add meg a meglévő abszolút elérési utat. A production profilt ne szerkeszd.

### 6.3 Image build

```bash
export CANDIDATE_IMAGE="qwen38-flash-dgx:v029-validation-${RUN_DATE}"

docker build \
  --pull \
  --progress=plain \
  -f Dockerfile.v0.29 \
  -t "${CANDIDATE_IMAGE}" \
  . 2>&1 | tee "${RESULT_ROOT}/B-docker-build.log"

docker image inspect "${CANDIDATE_IMAGE}" > "${RESULT_ROOT}/B-image-inspect.json"
```

### 6.4 Indítás külön porton

```bash
./flash serve v0.29 \
  IMAGE="${CANDIDATE_IMAGE}" \
  PORT=18301 \
  DET_TOPK=1 \
  EXACT_TOPK=0 \
  PREFIX_CACHE=1 \
  MTP=2

./flash wait 2>&1 | tee "${RESULT_ROOT}/B-wait.txt"
./flash status 2>&1 | tee "${RESULT_ROOT}/B-status.txt"
./flash test 2>&1 | tee "${RESULT_ROOT}/B-smoke-test.txt"
```

Elvárt aktív útvonal:

- `VLLM_QSA_DET_TOPK=1`;
- exact `torch.topk` fallback kikapcsolva;
- prefix cache bekapcsolva;
- mmap PLE aktív;
- MTP=2;
- modell API: `http://127.0.0.1:18301/v1`.

## 7. C kar — új javításokkal bővített kísérleti image

### 7.1 Fontos kompatibilitási kapu

A `#56500` PR a mozgó vLLM `main` kódbázisára készült. Ne tekintsd automatikusan kompatibilisnek a v0.29 csomaggal.

Rögzítsd a PR aktuális commitját:

```bash
cd "${RUN_ROOT}"
git clone https://github.com/vllm-project/vllm.git vllm-pr-work
cd vllm-pr-work

git fetch origin pull/56500/head:pr-56500
git rev-parse pr-56500 | tee "${RESULT_ROOT}/C-pr-56500-head.txt"
git log -1 --oneline pr-56500 | tee -a "${RESULT_ROOT}/C-pr-56500-head.txt"
git diff --stat origin/main...pr-56500 | tee "${RESULT_ROOT}/C-pr-56500-stat.txt"
git diff --name-only origin/main...pr-56500 | tee "${RESULT_ROOT}/C-pr-56500-files.txt"
```

Ha a PR olyan fájlokat módosít, amelyek a v0.29 image-ben nem léteznek vagy lényegesen eltérnek, ne erőltesd rá a release image-re. Ilyenkor friss `main`-ből kell teljes candidate image-et építeni.

### 7.2 Ajánlott PR-sorrend friss `main` esetén

Kezdj a `main` olyan commitjáról, amely már tartalmazza a beolvadt `#55450` javítást:

```bash
cd "${RUN_ROOT}/vllm-pr-work"
git fetch origin main
git checkout -b gb10-qwen38-validation origin/main

git log --oneline --all --grep='Retire Mamba states across null gaps' -n 3 \
  | tee "${RESULT_ROOT}/C-55450-presence.txt"
test -s "${RESULT_ROOT}/C-55450-presence.txt"
```

Az egyes nyitott PR-eket külön branchként töltsd le:

```bash
for pr in 56500 55122 54948 53798 54076 54129 55334; do
  git fetch origin "pull/${pr}/head:pr-${pr}"
  git rev-parse "pr-${pr}"
done | tee "${RESULT_ROOT}/C-open-pr-heads.txt"
```

Ne vond össze őket vakon. Ajánlott sorrend:

1. `#56500` — QSA workspace;
2. `#55122` — determinisztikus Top-K;
3. `#54948` — MoE fused-finalize kapcsoló;
4. `#53798`, majd `#54076` — worker- és scheduleroldali align fix;
5. `#55334` — RadixArk mixed FP8-PLE loader;
6. `#54129` — mmap PLE, utoljára, mert gyakran konfliktusos.

Minden PR előtt készíts összevonási próbát:

```bash
git status --short
git merge --no-commit --no-ff pr-56500
```

Ha tiszta:

```bash
git commit -m "validation: merge vLLM PR 56500"
```

Ha konfliktusos:

```bash
git merge --abort
```

Ekkor dokumentáld a konfliktust, és hagyd ki a PR-t vagy készíts külön kart. Ugyanezt ismételd a következő PR-rel. Minden sikeres merge után:

```bash
git rev-parse HEAD | tee -a "${RESULT_ROOT}/C-merged-heads.txt"
git status --short
```

### 7.3 Source image build

A pontos Dockerfile és build argumentumok változhatnak a vLLM `main` ágon, ezért előbb ellenőrizd őket:

```bash
cd "${RUN_ROOT}/vllm-pr-work"
test -f docker/Dockerfile
docker buildx inspect
```

Candidate build:

```bash
export MAIN_IMAGE="qwen38-vllm-main-gb10-${RUN_DATE}"

docker build \
  --progress=plain \
  -f docker/Dockerfile \
  -t "${MAIN_IMAGE}" \
  . 2>&1 | tee "${RESULT_ROOT}/C-vllm-main-build.log"
```

Ez több órás build is lehet. Ha az ARM64 build vagy a modellindítás nem működik, az eredmény továbbra is publikálható, ha tartalmazza a pontos SHA-kat, buildlogot és a reprodukálható hibát.

### 7.4 Indítási feltételek

A C kart csak akkor indítsd, ha a build tartalmazza a single-GB10 modellbetöltéshez szükséges loader- és PLE-megoldást. A RadixArk checkpoint tiszta upstream `main` alatt `#55334` nélkül nem feltétlenül tölthető be, a nagy FP8 PLE pedig `#54129` vagy más offload nélkül nem fér el megfelelő KV-cache mellett.

Kötelező runtime-kapcsolók:

```text
VLLM_QSA_DET_TOPK=1
VLLM_FLASHINFER_MOE_FUSED_FINALIZE=0
VLLM_PLE_MMAP=1
```

A változóneveket indítás előtt ellenőrizd a tényleges PR-headeken; nyitott PR-eknél változhatnak.

## 8. Egységes tesztmátrix minden karhoz

| Dimenzió | Értékek |
|---|---|
| Kontextus | 8K, 32K, 64K; ha stabil, 128K |
| MTP | 0, 2, 3 |
| Prefix cache | cold, partial hit, full hit |
| Indítás | legalább 3 friss szerverindítás/kombináció |
| Ismétlés | legalább 10 azonos kérés/indítás |
| Sampling | `temperature=0`, fix minden további paraméter |
| Top-K út | determinisztikus kernel; külön negatív kontrollként stock |
| Minőségi suite | 50 DocAI/KIE elem |

Ne futtasd az összes kombinációt rögtön. Kapuzás:

1. smoke és koherencia;
2. 8K determinisztikusság;
3. cold/partial/full cache;
4. 32K és 64K;
5. 50-es suite;
6. csak ezután 128K és többórás soak.

## 9. QSA workspace memória-validáció (`#56500`)

### 9.1 Cél

Bizonyítani, hogy növekvő chunked prefill mellett a CUDA allocator által lefoglalt memória nem nő lépcsőzetesen minden új kontextushossznál.

### 9.2 Mérési eljárás

Minden karon friss szerverindítás után futtasd ugyanazokat a kontextusokat ebben a sorrendben:

```text
8K → 16K → 24K → 32K → 48K → 64K
```

Minden kérés előtt és után mentsd:

```bash
date -Ins
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
docker stats --no-stream "${PROD_CONTAINER}"
curl -fsS http://127.0.0.1:18301/metrics
```

Példa gyűjtés:

```bash
{
  date -Ins
  nvidia-smi
  docker stats --no-stream
  curl -fsS http://127.0.0.1:18301/metrics || true
} >> "${RESULT_ROOT}/C-memory-timeline.txt" 2>&1
```

Azonosítsd és mentsd külön a következőket, ha a metrics endpoint tartalmazza őket:

- GPU cache usage;
- prefix-cache hit és request számlálók;
- prompt tokenek;
- TTFT;
- preemption;
- MTP drafted/accepted tokenek.

Sikerfeltétel:

- a reserved memória a workspace előfoglalása után stabil platón marad;
- nincs új device-allokáció minden növekvő kontextuslépcsőn;
- nincs OOM, preemption-vihar vagy worker restart;
- az output és a kiválasztott Top-K eredmény nem változik a workspace patch miatt.

## 10. Prefix-cache helyességi teszt

Minden szerverindításon:

1. **Cold:** új, hosszú prefix + suffix A.
2. **Partial hit:** ugyanaz a prefix + suffix B.
3. **Full hit:** pontosan ismételd meg a második kérést.
4. Ismételd meg legalább tízszer.

Rögzítsd kérésenként:

- request ID;
- prompt token count;
- cache-hit token count;
- TTFT;
- első token ID;
- elsőtokenes top-logprobok;
- teljes válasz SHA-256;
- reasoning és final tokenhossz;
- MTP acceptance length.

Sikerfeltétel:

- cold, partial és full útvonalon az elsőtokenes logprobok az elvárt numerikus tolerancián belül egyeznek;
- greedy output hash egyezik;
- a partial hit nem tér el úgy, hogy az utána következő full hitek már egyeznek;
- nincs nullázott vagy stale Mamba-state-re utaló eltérés.

## 11. Hosszú reasoning és Mamba soak teszt

Legalább 2–4 órán át ismételj:

- hosszú közös prefixet használó multi-turn/tool-loop kéréseket;
- 32K–128K közötti promptokat;
- cold és cache-hit útvonalakat;
- MTP=2 és MTP=3 konfigurációt.

Figyeld:

```bash
docker logs -f qwen38-flash 2>&1 | tee "${RESULT_ROOT}/soak-container.log"
```

Külön keress rá:

```bash
rg -i 'oom|out of memory|preempt|engine.*dead|illegal memory|timeout|mamba|state|guard|nan|inf' \
  "${RESULT_ROOT}" || true
```

Hibának minősül:

- üres reasoning a tokenlimitig;
- prompt vagy hosszú kontextusrész szó szerinti visszamondása;
- 0,8 feletti, gyanúsan magas prose MTP acceptance kontextusmásolással együtt;
- TTFT fokozatos romlása azonos cache-állapot mellett;
- computed-token progress visszalépés;
- állapotpool vagy GPU-memória monoton növekedése;
- eltérő greedy kimenet azonos bemenetre.

## 12. Negatív kontrollok

A hibadiagnózis hitelesítéséhez külön, rövid futásokban:

1. `DET_TOPK=0`, stock Top-K — várhatóan reprodukálhatja a nemdeterminizmust.
2. `EXACT_TOPK=1`, `DET_TOPK=0` — determinisztikus, de lassabb referencia.
3. `PREFIX_CACHE=0` — elválasztja a cache-hibát a Top-K/MoE hibától.
4. `MTP=0` — elválasztja a speculative decode útvonalat.
5. `--enforce-eager` vagy PIECEWISE graph — CUDA graph eredetű hibák kizárására.
6. Fused finalize bekapcsolva/kikapcsolva — MoE nemdeterminizmus izolálására.

Ezeket ne production terhelés mellett futtasd.

## 13. Eredménytábla

Másold ki és töltsd ki minden karhoz:

| Kar | Image ID | vLLM SHA | Patch SHA-k | Context | MTP | Cache út | Stabil ismétlés | TTFT | Prefill tok/s | Decode tok/s | Peak/reserved memória | Megjegyzés |
|---|---|---|---|---:|---:|---|---:|---:|---:|---:|---:|---|
| A | | | | 8K | 2 | cold | /10 | | | | | |
| A | | | | 32K | 2 | partial | /10 | | | | | |
| B | | | | 8K | 2 | cold | /10 | | | | | |
| B | | | | 32K | 2 | partial | /10 | | | | | |
| C | | | | 8K | 2 | cold | /10 | | | | | |
| C | | | | 32K | 2 | partial | /10 | | | | | |

## 14. Elfogadási feltételek

A candidate csak akkor tekinthető jobbnak a jelenlegi image-nél, ha mind teljesül:

- 0 eltérő greedy output a determinisztikussági szondán;
- 0/50 instabil KIE-elem;
- cold/partial/full cache-útvonal konzisztens;
- nincs üres reasoning vagy kontextusmásolás;
- nincs monoton memória- vagy Mamba-state növekedés;
- nincs OOM, CUDA illegal access vagy worker restart;
- TTFT/prefill/decode regresszió dokumentált és elfogadható;
- legalább három friss szerverindításon ugyanaz az eredmény;
- minden image-, repo- és PR-SHA rögzítve van.

## 15. Rollback

Állítsd le és távolítsd el csak a candidate konténert:

```bash
cd "${RUN_ROOT}/candidate-blazux"
./flash stop || true
./flash rm || true
```

Ellenőrizd a production image pinjét:

```bash
docker image inspect "${PROD_IMAGE_ID}" >/dev/null
```

Indítsd vissza a production receptet az eredeti checkoutból és eredeti változókkal:

```bash
cd /opt/vllm/qwen3.8-Flash-DGX
IMAGE="${PROD_IMAGE}" ./flash serve default
./flash wait
./flash test 2>&1 | tee "${RESULT_ROOT}/ROLLBACK-smoke-test.txt"
```

Csak akkor zárd le a munkát, ha az API egészséges és a production smoke teszt sikeres.

## 16. Publikálható bizonyítékcsomag

Készíts az eredményekből egy külön, személyes adatot vagy tokent nem tartalmazó könyvtárat:

```bash
export PUBLIC_ROOT="${RUN_ROOT}/public-results"
mkdir -p "${PUBLIC_ROOT}"

cp "${RESULT_ROOT}"/*-head*.txt "${PUBLIC_ROOT}/" 2>/dev/null || true
cp "${RESULT_ROOT}"/*smoke-test*.txt "${PUBLIC_ROOT}/" 2>/dev/null || true
cp "${RESULT_ROOT}"/*determinism*.txt "${PUBLIC_ROOT}/" 2>/dev/null || true
cp "${RESULT_ROOT}"/*memory*.txt "${PUBLIC_ROOT}/" 2>/dev/null || true
```

Publikálás előtt:

```bash
rg -n -i 'token|authorization|bearer|password|secret|hf_[A-Za-z0-9]+' "${PUBLIC_ROOT}" || true
```

A PR-komment tartalmazza:

- GB10 / `sm_121`, ARM64;
- driver, CUDA, Torch és vLLM verzió;
- minden commit SHA;
- modell/checkpoint pontos neve;
- runtime flag-ek;
- kontroll és patch eredmények ugyanabban a táblázatban;
- nyers mérési fájlokra mutató permanens link;
- pozitív és negatív eredmények egyaránt;
- egyértelmű korlátok: single node, single GB10, konkrét workload.

## 17. Javasolt végrehajtási sorrend

1. Inventory és production pin.
2. A kar kontrollmérés.
3. Production konténer leállítása, image megtartása.
4. B kar: aktuális blazux `v0.29` build és smoke.
5. B kar: 8K determinisztikusság, cache-szonda, 32K/64K, 50-es suite.
6. Ha B stabil: többórás soak.
7. C kar: először csak `#56500` kompatibilitási vizsgálat.
8. Ezután a további nyitott PR-ek egyenként, külön mérési ponttal.
9. Candidate leállítása.
10. Production rollback és smoke teszt.
11. Nyers adatok tisztítása, publikálható csomag és PR-komment.

## 18. Döntési pont

Az első, reálisan publikálható mérföldkő nem feltétlenül a teljes hét-PR-es stack. Már önmagában értékes eredmény:

- a blazux v0.29 bundle független GB10-validációja;
- a `#56500` memória-platójának reprodukciója vagy cáfolata;
- a beolvadt `#55450` hosszú prefill/TTFT hatásának saját mérése;
- a teljes determinisztikussághoz szükséges Top-K + MoE + PLE kombináció ismételt igazolása.

A legjobb eredmény az, amelyben minden változó pinelt, a kontroll ugyanazon a gépen futott, és a nyers adatokból más is újra tudja számolni a következtetést.
