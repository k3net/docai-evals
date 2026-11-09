"""08 — a valós kinyerés (G1, G3): az alany a vLLM-példányán (`lib.sh` `subject_start`, LORA=0), kötött JSON-sémával
(`lanc08.kinyero_sema`), thinking nélkül, temperature 0. Csak a tétel szövegét látja (a hibacsaládon a szabályok
mérésneveit is), a jelölteket nem (`lanc08.kinyero_prompt`). Csak a standard könyvtár: a spark-dev gazdagépén fut.

Kimenet soronként: {"id", "family", "sema", "mezok" (a lánc mezőlistája, vagy null, ha a válasz nem értelmezhető),
"nyers", "hiba", "ido_s"}. `--sema 1`: a G1 első menete (egy közös mezőlista); `--sema 2`: szerepenkénti mezők
(`lanc08.kinyero_sema2`, Dani 11-02). `--idk`: csak a fájlban felsorolt item-id-k (soronként egy).
  python3 kor08/eszkozok/kinyer08.py --forras K3diag --out kor08/adat/G1/kinyeres [--sema 2] [--idk F] [--limit 20]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lanc08 as L  # noqa: E402

URL = "http://127.0.0.1:8400/v1/chat/completions"
MODEL = "Qwen/Qwen3.6-35B-A3B-FP8"


def hivas(fam: str, it: dict, sema: int) -> dict:
    jel = L.jeloltek(fam, it["options"], it["lang"])[0]
    schema = L.kinyero_sema(fam, jel) if sema == 1 else L.kinyero_sema2(fam, jel)
    body = {"model": MODEL, "messages": L.kinyero_prompt(fam, it, jel, sema), "temperature": 0, "max_tokens": 1024,
            "seed": 0, "chat_template_kwargs": {"enable_thinking": False},
            "response_format": {"type": "json_schema", "json_schema": {"name": "kinyeres", "schema": schema, "strict": True}}}
    t0 = time.time()
    out = {"id": it["id"], "family": fam, "sema": sema, "mezok": None, "nyers": None, "hiba": None}
    for k in range(4):
        try:
            req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=300) as r:
                txt = json.loads(r.read())["choices"][0]["message"]["content"] or ""
            out["nyers"] = txt
            obj = json.loads(txt)
            out["mezok"] = L.lapit(fam, obj, sema) if isinstance(obj, dict) else None
            out["hiba"] = None if out["mezok"] is not None else "nem értelmezhető szerkezet"
            break
        except urllib.error.HTTPError as e:
            out["hiba"] = f"http {e.code}"
            time.sleep(2 ** k)
        except (urllib.error.URLError, TimeoutError) as e:
            out["hiba"] = f"hálózat: {e}"
            time.sleep(2 ** k)
        except json.JSONDecodeError:
            out["hiba"] = "JSON"
            break
    out["ido_s"] = round(time.time() - t0, 2)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forras", required=True, choices=list(L.FORRASOK))
    ap.add_argument("--csalad", choices=L.CSALADOK)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--szalak", type=int, default=64)
    ap.add_argument("--sema", type=int, default=2, choices=(1, 2))
    ap.add_argument("--idk")
    a = ap.parse_args()
    idk = set(Path(a.idk).read_text(encoding="utf-8").split()) if a.idk else None
    out = Path(a.out) if Path(a.out).is_absolute() else L.EXP / a.out
    out.mkdir(parents=True, exist_ok=True)
    for fam in (a.csalad,) if a.csalad else L.CSALADOK:
        items = [it for _, it in L.betolt(a.forras, fam) if idk is None or it["id"] in idk][:a.limit]
        if not items:
            continue
        p = out / f"{a.forras}_{fam}.jsonl"
        t0, n = time.time(), 0
        with p.open("w", encoding="utf-8") as f, ThreadPoolExecutor(a.szalak) as ex:
            for r in ex.map(lambda it: hivas(fam, it, a.sema), items):
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
                n += 1
                if n % 500 == 0 or n == len(items):
                    el = time.time() - t0
                    vege = time.strftime("%H:%M", time.localtime(time.time() + el / n * (len(items) - n)))
                    print(f"  {a.forras}:{fam} {n}/{len(items)} · {n / el:.1f} item/s · várható vége {vege}", flush=True)
        hibak = sum(1 for x in L.jsonl(p) if x["mezok"] is None)
        print(f"{a.forras}:{fam}: {n} item, értelmezhetetlen válasz {hibak} → {p.relative_to(L.EXP) if p.is_relative_to(L.EXP) else p}")


if __name__ == "__main__":
    main()
