# Qwen3.8-Flash-Next NVFP4 determinisztikussági runbook – `spark-dev`

**Cél:** a jelenlegi, már validált `EXACT_TOPK=1` kiszolgáló megtartása mellett külön tesztpéldányban kipróbálni:

1. a determinisztikus QSA `persistent_topk` kernelt;
2. a FlashInfer CUTLASS NVFP4 MoE nemdeterminisztikus fused-finalize lépésének kikapcsolását;
3. ezek együttes hatását a reprodukálhatóságra és a teljesítményre.

> A runbook nem production inplace frissítés. Külön checkoutot, image-t, konténernevet, portot és cache-könyvtárat használ.

## 1. Kapcsolódó hibák és javítások

| Terület | Tünet | Javítás / kontroll |
| --- | --- | --- |
| QSA `persistent_topk` | `temperature=0` mellett már az első token jelöltjei és logprobjai eltérhetnek | [vLLM PR #55122](https://github.com/vllm-project/vllm/pull/55122), illetve a [standalone GB10 patch](https://github.com/jschmied/qwen38-flash-next-gb10/tree/main/patches/kernel-det) és `VLLM_QSA_DET_TOPK=1` |
| Candidate buffer | Érvényes jelöltek elveszhetnek | [vLLM issue #51782](https://github.com/vllm-project/vllm/issues/51782); ezt is célozza a #55122 |
| FlashInfer CUTLASS NVFP4 MoE | Azonos kérések decode közben eltérő logitokat adnak | [vLLM issue #54945](https://github.com/vllm-project/vllm/issues/54945), [PR #54948](https://github.com/vllm-project/vllm/pull/54948), `use_fused_finalize=False` |
| Mamba align / prefix cache | Blokkméret- és align-módhoz kapcsolódó reprodukálhatósági problémák | [PR #54076](https://github.com/vllm-project/vllm/pull/54076), [PR #53798](https://github.com/vllm-project/vllm/pull/53798) |
| Eredeti GB10 reprodukció | QSA nemdeterminizmus és exact Top-K kontroll | [blazux issue #3](https://github.com/blazux/qwen3.8-Flash-DGX/issues/3), [DocAI-kísérlet](https://github.com/k3net/docai-evals/tree/master/experiments/2026-08-28-qwen38-flash-next-nvfp4-topk-nondeterminism-gb10), [cikk](https://docai.hu/en/blog/qwen38-flash-next-nondeterministic-vllm-kernel) |

## 2. Elfogadási feltételek

A tesztváltozat csak akkor válthatja le a jelenlegi exact `torch.topk` megoldást, ha:

- a 6×10 elsőtokenes próba minden promptnál azonos tokeneket és top-20 logprob-signature-t ad;
- az 50 itemes suite legalább három teljes futása azonos eredményt ad;
- a teljes generálás tokenenkénti top-20 logprob-hash-e azonos;
- cold és prefix-cache-hit kérés azonos választ ad;
- MTP be- és kikapcsolása mellett külön-külön reprodukálható;
- nincs hosszú, üres vagy ismétlődő reasoning regresszió;
- a TTFT és decode lassulása dokumentált és elfogadható.

## 3. Előkészítés a `spark-dev` gépen

```bash
ssh spark-dev

mkdir -p /opt/vllm/qwen38-det-test/{src,results,logs,cache}
cd /opt/vllm/qwen38-det-test

date -Is | tee results/run-started-at.txt
nvidia-smi | tee results/nvidia-smi.txt
uname -a | tee results/uname.txt
docker version | tee results/docker-version.txt
```

Rögzítsük a jelenlegi stabil baseline-t. A konkrét konténernév eltérhet, ezért előbb listázzuk:

```bash
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}'
docker images --digests | grep -E 'qwen|vllm|blazux' | tee results/baseline-images.txt
```

Ha ismert a production konténer neve:

```bash
BASELINE_CONTAINER='<jelenlegi-kontener-neve>'
docker inspect "$BASELINE_CONTAINER" > results/baseline-container-inspect.json
docker logs "$BASELINE_CONTAINER" > logs/baseline.log 2>&1
```

Ne állítsuk le és ne írjuk felül ezt a konténert.

## 4. A patch-forrás rögzítése

```bash
cd /opt/vllm/qwen38-det-test/src

git clone https://github.com/jschmied/qwen38-flash-next-gb10.git
cd qwen38-flash-next-gb10
git rev-parse HEAD | tee /opt/vllm/qwen38-det-test/results/kernel-det-commit.txt

find patches/kernel-det -maxdepth 3 -type f -print | sort
python3 patches/kernel-det/build_det.py --help || true
python3 tools/determinism/qsadet_patch.py --help || true
```

> A standalone patch interfésze még változhat. A checkoutban található README és a két `--help` kimenete az irányadó; a használt commitot mindig rögzíteni kell.

## 5. Determinisztikus Top-K kernel felépítése

A patch készítője által megadott belépési pont:

```bash
cd /opt/vllm/qwen38-det-test/src/qwen38-flash-next-gb10
python3 patches/kernel-det/build_det.py
```

Ellenőrizzük, hogy készült-e betölthető modul:

```bash
find patches/kernel-det -type f \
  \( -name '*.so' -o -name '*.whl' -o -name '*.py' \) -print | sort
```

Ha a buildet a vLLM-konténerben kell futtatni, ugyanazt az image-et használjuk, amelyből a tesztkiszolgáló indul; így a CUDA-, PyTorch- és Python-ABI azonos marad. Ne másoljuk át vakon egy másik környezetben fordított `.so` fájlt.

## 6. Tesztkiszolgáló indítása

### 6.1 Kötelező izoláció

Használjunk külön:

- konténernevet;
- API-portot, például `8001`;
- FlashInfer autotune-cache-t;
- log- és eredménykönyvtárat.

```bash
export TEST_PORT=8001
export TEST_NAME=qwen38-det-topk-moe
export TEST_ROOT=/opt/vllm/qwen38-det-test
export VLLM_FLASHINFER_AUTOTUNE_CACHE_DIR="$TEST_ROOT/cache/flashinfer-nonfused"

mkdir -p "$VLLM_FLASHINFER_AUTOTUNE_CACHE_DIR" "$TEST_ROOT/logs" "$TEST_ROOT/results"
```

FlashInfer 0.6.17 vagy régebbi környezetben **ne** használjuk a fused móddal feltöltött korábbi autotune-cache-t. A #54945 szerint a régi cache hibás `gemm2` profile ID-t adhat a non-fused runnernek.

### 6.2 Kapcsolók

A tesztváltozat környezeti kapcsolói:

```bash
export VLLM_QSA_DET_TOPK=1
export VLLM_FLASHINFER_MOE_FUSED_FINALIZE=0
```

- Az első kapcsoló a standalone deterministic Top-K wiring része.
- A második csak akkor működik, ha a vLLM build tartalmazza a #54948 módosítását. Enélkül a hívási helyen explicit `use_fused_finalize=False` patch szükséges.

### 6.3 Indítás a blazux receptből

A meglévő recept pontos argumentumait tartsuk meg; csak az image/nevet, portot, cache-t és a fenti két kapcsolót változtassuk. Példa-váz:

```bash
cd /opt/vllm/qwen3.8-Flash-DGX

MODE=nvfp4 \
EXACT_TOPK=0 \
PREFIX_CACHE=1 \
VLLM_QSA_DET_TOPK=1 \
VLLM_FLASHINFER_MOE_FUSED_FINALIZE=0 \
VLLM_FLASHINFER_AUTOTUNE_CACHE_DIR=/opt/vllm/qwen38-det-test/cache/flashinfer-nonfused \
scripts/serve.sh 2>&1 | tee /opt/vllm/qwen38-det-test/logs/det-server.log
```

> A `serve.sh` által használt portot és konténernevet különítsük el a production példánytól. Ha a script ezeket nem engedi környezeti változóval felülírni, készítsünk külön tesztmásolatot a scriptből; a production fájlt ne módosítsuk.

Indítás után ellenőrizzük a logot:

```bash
grep -Ei 'QSA|TOPK|FLASHINFER|FUSED_FINALIZE|NVFP4|MTP|PREFIX|ERROR|WARNING' \
  /opt/vllm/qwen38-det-test/logs/det-server.log | tail -n 200
```

Elvárt:

- a deterministic QSA patch betöltődött;
- `EXACT_TOPK` nincs bekapcsolva;
- FlashInfer CUTLASS NVFP4 MoE fut;
- fused finalize ki van kapcsolva;
- nincs ABI-, symbol-, autotune- vagy CUDA-hiba.

## 7. A/B tesztmátrix

| Változat | Top-K | MoE finalize | Cél |
| --- | --- | --- | --- |
| A – baseline | `EXACT_TOPK=1` | jelenlegi alapérték | már validált referencia |
| B – Top-K izoláció | `VLLM_QSA_DET_TOPK=1` | fused | az új Top-K kernel önálló hatása |
| C – teljes javítás | `VLLM_QSA_DET_TOPK=1` | non-fused | teljes kérés-szintű reprodukálhatóság |
| D – MoE izoláció | `EXACT_TOPK=1` | non-fused | a MoE-javítás önálló hatása |

Egyszerre csak egy tesztváltozat fusson ugyanazon a GB10-en. Minden változatnál rögzítsük:

- image digest;
- vLLM és FlashInfer verzió;
- Git commitok;
- teljes indítóparancs és környezeti kapcsolók;
- cold-start és bemelegített mérés.

## 8. Gyors API-s reprodukálhatósági próba

Az alábbi próba háromszor elküldi ugyanazt a kérést, majd minden generált token top-20 logprob-listáját hash-eli:

```bash
export TEST_PORT=8001

python3 - <<'PY'
import hashlib
import json
import os
import urllib.request

port = os.environ.get("TEST_PORT", "8001")
url = f"http://127.0.0.1:{port}/v1/chat/completions"
prompt = (
    "Write a detailed technical explanation of how a copy-on-write page table "
    "works in a modern operating system kernel, covering fork(), page faults, "
    "reference counting, and the interaction with the TLB."
)

for run in range(10):
    body = json.dumps({
        "model": "flashnext",
        "temperature": 0,
        "max_tokens": 128,
        "logprobs": True,
        "top_logprobs": 20,
        "messages": [{"role": "user", "content": prompt}],
        "chat_template_kwargs": {"enable_thinking": False},
    }).encode()
    req = urllib.request.Request(url, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as response:
        data = json.loads(response.read())

    content = data["choices"][0]["logprobs"]["content"]
    token_hashes = []
    for token in content:
        canonical = "|".join(
            f"{x['token']!r}:{x['logprob']:.12g}"
            for x in token["top_logprobs"]
        )
        token_hashes.append(hashlib.sha256(canonical.encode()).hexdigest()[:12])

    whole = hashlib.sha256("|".join(token_hashes).encode()).hexdigest()
    print(run + 1, whole, token_hashes[:8])
PY
```

**PASS:** mind a tíz teljes hash azonos. Már egy eltérő hash is **FAIL**, akkor is, ha a látható válasz szövege azonos.

## 9. Saját evalok futtatása

```bash
cd /opt/vllm/qwen38-det-test/src
git clone https://github.com/k3net/docai-evals.git
cd docai-evals/experiments/2026-08-28-qwen38-flash-next-nvfp4-topk-nondeterminism-gb10
git rev-parse HEAD | tee /opt/vllm/qwen38-det-test/results/docai-evals-commit.txt
```

Futtatandó sorrend:

1. 6×10 elsőtokenes szonda;
2. 50 itemes teljes suite, legalább háromszor;
3. thinking be/ki;
4. MTP be/ki;
5. prefix cache kikapcsolva, majd cold/hit párral bekapcsolva;
6. rövid és hosszú kontextus: legalább 8K és 32K;
7. hosszú reasoning promptok, külön figyelve az üres vagy ismétlődő futásokra.

A repóban dokumentált eredeti parancsokat használjuk, de az API base URL-t a tesztportra állítsuk. Minden nyers JSON választ őrizzünk meg, ne csak az összesített PASS/FAIL eredményt.

## 10. Teljesítménymérés

Mindegyik A–D változatnál mérjük ugyanazzal a promptkészlettel:

- TTFT: 8K és 32K input;
- inter-token latency / decode ms/token;
- output token/s;
- peak memória;
- cold és warm eredmény;
- prefix cache miss és hit.

Legalább öt bemelegített ismétlés mediánját és p95 értékét rögzítsük. Ne hasonlítsunk össze eltérő MTP-, prefix-cache-, CUDA graph- vagy batch-konfigurációkat.

## 11. Hibakeresés

### `Invalid gemm2 profile id`

Valószínű ok: FlashInfer ≤0.6.17 alatt a fused és non-fused runner közös, inkompatibilis autotune-cache-t kapott.

Megoldás: állítsunk be új, üres könyvtárat anélkül, hogy a régi cache-t törölnénk:

```bash
export VLLM_FLASHINFER_AUTOTUNE_CACHE_DIR="/opt/vllm/qwen38-det-test/cache/flashinfer-nonfused-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$VLLM_FLASHINFER_AUTOTUNE_CACHE_DIR"
```

### Nem látszik a deterministic Top-K aktiválása

- ellenőrizzük a `VLLM_QSA_DET_TOPK=1` átadását a konténerbe;
- ellenőrizzük a patch Python-moduljának importját;
- ellenőrizzük a fordított `.so` Python-, PyTorch- és CUDA-ABI-ját;
- indításkor fail-closed módon álljunk le, ha a patch nem töltődött be; ne tekintsük a puszta env vart bizonyítéknak.

### Az első token stabil, de a későbbi logprobok eltérnek

Ez tipikusan arra utal, hogy a QSA Top-K javult, de a FlashInfer MoE fused finalize még aktív. Ellenőrizzük a #54948 bekötését és a szerverlogot.

### A szöveg azonos, a logprob-hash eltér

Ez továbbra is reprodukálhatósági hiba. A greedy argmax maradhat azonos úgy is, hogy a mögöttes logitok eltérnek.

## 12. Visszaállítás

A production baseline-hoz nem nyúltunk. A tesztpéldány leállítása:

```bash
docker ps --format '{{.Names}}' | grep -Fx qwen38-det-topk-moe
docker stop qwen38-det-topk-moe
```

Az első parancs csak ellenőriz, a második kizárólag a név szerint azonosított tesztkonténert állítja le. A tesztimage-et és cache-t a mérés dokumentálásáig ne töröljük.

## 13. Döntési szabály

- **Top-K PASS, teljes hash FAIL:** a deterministic Top-K kernel működik, de a MoE vagy align/prefix-cache út még eltér.
- **C változat teljes PASS:** jelölt az exact `torch.topk` kiváltására.
- **C PASS és érdemben gyorsabb A-nál:** készítsünk verziózott tesztimage-et, majd hosszabb staging soak tesztet.
- **B/C crash vagy eltérés:** maradjon a jelenlegi `EXACT_TOPK=1` baseline; az eredményt a pontos commitokkal és nyers hash-ekkel tegyük fel a #55122 PR-re.
- **Production váltás:** csak beolvadt vagy pontos commitra rögzített javításokkal, reprodukálható image builddel és teljes regressziós PASS után.

## 14. Eredményjegyzőkönyv

```markdown
### spark-dev Qwen3.8 determinism validation

- Date:
- GPU / driver:
- Image digest:
- vLLM commit:
- FlashInfer version:
- QSA deterministic kernel commit:
- MoE non-fused patch commit:
- mmap PLE commit:
- MTP:
- Prefix cache:
- CUDA graph mode:
- KV cache dtype:

| Variant | 6×10 | 50-item ×3 | Full logprob hash | 8K TTFT | 32K TTFT | Decode |
| --- | --- | --- | --- | ---: | ---: | ---: |
| A exact Top-K | | | | | | |
| B det kernel | | | | | | |
| C det + non-fused | | | | | | |
| D exact + non-fused | | | | | | |

Decision:
Observed regressions:
Raw-result path:
```

---

**Állapot a runbook készítésekor:** a #55122 és #54948 javításokat tesztágként kell kezelni, nem szabad automatikusan beolvadtnak vagy production-késznek tekinteni. A PR-ek aktuális státuszát az image építése előtt ismét ellenőrizni kell.
