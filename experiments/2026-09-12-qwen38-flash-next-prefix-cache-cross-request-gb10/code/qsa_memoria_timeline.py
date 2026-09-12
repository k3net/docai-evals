#!/usr/bin/env python3
"""QSA workspace memória-validáció (runbook §9) — növekvő chunked prefill lépcsők.

A #56500 állítása: a QSA prefill-logits workspace ELŐRE foglalt és újrahasznált,
így a lefoglalt (reserved) memória nem nő lépcsőzetesen minden új kontextushossznál.
A szonda a 8K→16K→24K→32K→48K→64K sorozatot futtatja EGY szerverindításon belül,
és minden lépcső előtt/után rögzíti a GPU-memóriát (nvidia-smi a hoston, ssh-n) és
a vLLM /metrics pillanatképét.

⛔ A GB10 unified memóriáján az `nvidia-smi` used_memory mezője [N/A] lehet — ezért
   a hoston a `free -m` (used) és a konténer RSS-e is rögzítésre kerül, és a döntést
   a vLLM saját metrikái (kv-cache usage) + a host-memória trendje adja.
"""
from __future__ import annotations
import argparse, json, re, subprocess, time, urllib.request
from pathlib import Path

RENDSZERPROMPT = "Válaszolj magyarul, tömören."

def host_pillanatkep(ssh_host, konteneris_nev):
    out = {}
    def sh(cmd):
        try:
            return subprocess.run(["ssh", ssh_host, cmd], capture_output=True,
                                  text=True, timeout=60).stdout.strip()
        except Exception as e:
            return f"ERR {e}"
    out["ts"] = sh("date -Ins")
    out["nvidia_smi_apps"] = sh("nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader")
    out["free_m"] = sh("free -m | awk '/^Mem:/{print $2,$3,$4,$6}'")  # total used free buff/cache
    out["docker_stats"] = sh(f"docker stats --no-stream --format '{{{{.MemUsage}}}} {{{{.CPUPerc}}}}' {konteneris_nev}")
    return out

def metrics_pillanatkep(url):
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/metrics", timeout=30) as r:
            szoveg = r.read().decode()
    except Exception as e:
        return {"hiba": str(e)}
    erdekes = {}
    for sor in szoveg.splitlines():
        if sor.startswith("#") or not sor.strip():
            continue
        if re.match(r"vllm:(kv_cache_usage_perc|prefix_cache_(queries|hits)_total|num_preemptions"
                    r"|prompt_tokens_total|generation_tokens_total|num_requests_(running|waiting)"
                    r"|spec_decode_num_(draft|accepted)_tokens_total)", sor):
            kulcs, _, ertek = sor.rpartition(" ")
            erdekes[kulcs] = ertek
    return erdekes

def keres(url, model, prompt, max_tokens, timeout):
    payload = {"model": model, "temperature": 0.0, "top_p": 1, "max_tokens": max_tokens,
               "messages": [{"role": "system", "content": RENDSZERPROMPT},
                            {"role": "user", "content": prompt}],
               "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request(url.rstrip("/") + "/v1/chat/completions",
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json", "Connection": "close"})
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = json.load(r)
    return body, (time.monotonic() - t0) * 1000

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--url", required=True)
    a.add_argument("--model", required=True)
    a.add_argument("--ssh-host", default="spark-dev")
    a.add_argument("--kontener", required=True)
    a.add_argument("--lepcsok", default="8000,16000,24000,32000,48000,64000",
                   help="promptok hossza TOKENBEN (közelítés: 1 token ~ 1 szó-token a kitöltő szövegben)")
    a.add_argument("--max-tokens", type=int, default=32)
    a.add_argument("--timeout", type=int, default=1800)
    a.add_argument("--cimke", required=True)
    a.add_argument("--out", required=True)
    args = a.parse_args()

    # Kitöltő szöveg: determinisztikus, lépcsőnként EGYEDI magvú token-folyam, hogy a
    # prefix-cache ne hitteljen a lépcsők között. A hosszt a szerver /tokenize endpointjával
    # kalibráljuk (a becslés token/elem aránya modellenként más) — a cél ±2 % pontosság.
    def tokenizal(szoveg):
        req = urllib.request.Request(args.url.rstrip("/") + "/tokenize",
                                     data=json.dumps({"model": args.model, "prompt": szoveg}).encode(),
                                     headers={"Content-Type": "application/json", "Connection": "close"})
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.load(r)["count"]

    def kitolto(cel_token, mag):
        # 1) arány mérése 200 elemen, 2) skálázás, 3) egy korrekciós kör
        minta = " ".join(f"{mag}{i:06d}" for i in range(200))
        per_elem = tokenizal(minta) / 200
        db = max(1, int(cel_token / per_elem))
        for _ in range(3):
            szoveg = " ".join(f"{mag}{i:06d}" for i in range(db))
            n = tokenizal(szoveg)
            if abs(n - cel_token) / cel_token <= 0.02:
                return szoveg, n
            db = max(1, int(db * cel_token / n))
        return szoveg, n

    ki = {"cimke": args.cimke, "args": vars(args), "kezdet": time.strftime("%Y-%m-%dT%H:%M:%S"),
          "lepcsok": []}
    print(f"[i] {args.cimke} — {args.url} · lépcsők: {args.lepcsok}", flush=True)

    for lep in [int(x) for x in args.lepcsok.split(",")]:
        elotte_host = host_pillanatkep(args.ssh_host, args.kontener)
        elotte_met = metrics_pillanatkep(args.url)
        kitoltott, kit_tok = kitolto(lep - 40, f"az{lep}x")
        prompt = ("Az alábbi azonosítólista egy naplófájl kivonata.\n\n" + kitoltott
                  + "\n\nHány darab azonosító szerepel a listában? Csak a számot add vissza.")
        body, ms = keres(args.url, args.model, prompt, args.max_tokens, args.timeout)
        usage = body.get("usage", {})
        utana_host = host_pillanatkep(args.ssh_host, args.kontener)
        utana_met = metrics_pillanatkep(args.url)
        rek = {"cel_token": lep, "kitolto_tok": kit_tok, "prompt_tok": usage.get("prompt_tokens"),
               "cached_tok": (usage.get("prompt_tokens_details") or {}).get("cached_tokens"),
               "completion_tok": usage.get("completion_tokens"), "ms": round(ms, 1),
               "elotte_host": elotte_host, "utana_host": utana_host,
               "elotte_metrics": elotte_met, "utana_metrics": utana_met}
        ki["lepcsok"].append(rek)
        print(f"  {lep:>6} cél → prompt_tok={rek['prompt_tok']} cached={rek['cached_tok']} "
              f"{ms:.0f} ms | free(used MB) {elotte_host['free_m']} → {utana_host['free_m']}", flush=True)

    Path(args.out).write_text(json.dumps(ki, ensure_ascii=False, indent=2))
    print(f"\n[>] {args.out}")

if __name__ == "__main__":
    main()
