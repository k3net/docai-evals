"""05-ös kör — JEV-35B: promptépítő, kiolvasás, smoke (05-runbook 3.4, 8.3; 04-runbook 3.1).

A JEV saját csupasz formátuma, a repó `serve_decide.py` `s1_pass`-ának megfelelően, bájtra:

  [kind] choice
  [state] <az item state-je, változatlanul>
  [question] <az item question-je>
  [options]
  A) <opció>                      (opció: text, és ha van, " — " + use_when, mint a 03 generikus keretében)
  …
  [decision]:

  JEV-a  a valódi opciók után utolsóként az „egyik sem” (GENERIC[lang]["none"]: „Egyik sem” / „None of these”);
         ennek a betűje a mi X-ünk
  JEV-b  csak a valódi opciók; az X sosem top-1 (egyopciós item nem olvasható ki, kimarad)

Címkék: a `single_token_labels("x\\n{}) y")` sorrendje (A, B, …), az első 256-nak egyeznie kell a
`decision_head.json` choice-verbalizereivel. Kiolvasás a `kiolvaso03` ids-módjával: offline tokenizálás,
`/v1/completions` `max_tokens=1`, `logprob_token_ids` = a jelen lévő címkék. A logprobokhoz a fej bias-a adódik, a
`probs` erre a szűkített softmax (T = 1; a mi kalibrációnk később), a `probs_jev` a JEV `calibration.json`-jának
choice-temperature-ével (leíró). A kimenet csak eval: címke, soft target vagy szűrő nem lehet (12. pont).

  python3 kor05/eszkozok/jev05.py smoke --url http://127.0.0.1:8410 --out kor05/eredmenyek/F0/jev_smoke
  python3 kor05/eszkozok/jev05.py kiolvas --url http://127.0.0.1:8410 --feladat D_dev --perms 0,1,2,3 \\
      --out cache/k05/jev/D_dev.jsonl
"""

from __future__ import annotations

import argparse
import json
import math
import string
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE), str(EXP / "kor03/eszkozok"), str(EXP / "eszkozok")]
from allapot05 import content_state  # noqa: E402
from common import labels_for, permutation  # noqa: E402
from kozos03 import GENERIC  # noqa: E402

JEV_REPO = "autotrust/JEV-35B"
JEV_REV = "a5d0d580bb9324f0f4c07dcba5c5ca91e813e7c9"
import os  # noqa: E402

# a konténerben a ~/hf-cache-jev a /hfjev alatt (a snapshot symlinkjei a blobs/-ra mutatnak, ezért az egész cache kell)
JEV_DIR = Path(os.environ.get("LDH_JEV", f"/hfjev/hub/models--autotrust--JEV-35B/snapshots/{JEV_REV}"))
SERVED = "autotrust/JEV-35B"
MAX_OPTIONS = 256
README_PELDA = {"kind": "choice", "state": "Customer message: my card was charged twice for the same order.",
                "question": "Which team should handle this ticket?",
                "options": ["billing", "shipping", "technical support", "account security"]}


# --- prompt és címkék ------------------------------------------------------------------------------------------------

def option_text(o: dict) -> str:
    return o["text"] + (f" — {o['use_when']}" if o.get("use_when") else "")


def jev_options(item: dict, order: list[str | None], arm: str) -> tuple[list[str], list[str]]:
    """(opciószövegek, a mi címkéink) a JEV-sorrendben; az X (None) a JEV-a utolsó opciója, a JEV-b-ből kimarad."""
    opts = {o["id"]: o for o in item["options"]}
    ours = labels_for(order)
    texts, labs = [], []
    for oid, lab in zip(order, ours):
        if oid is None:
            if arm == "a":
                texts.append(GENERIC[item["lang"]]["none"])
                labs.append(lab)
            continue
        texts.append(option_text(opts[oid]))
        labs.append(lab)
    if arm == "a" and labs[-1] != "X":
        raise ValueError(f"{item['id']}: a JEV-a utolsó opciója nem az X")
    return texts, labs


def bare_prompt(kind: str, state: str, question: str, lines: list[str]) -> str:
    """A serve_decide s1_pass szövege (Qwen-profil: üres prefix), szöveges state-tel."""
    return f"[kind] {kind}\n[state] " + state + f"\n[question] {question}\n[options]\n" + "\n".join(lines) + "\n[decision]:"


class Jev:
    def __init__(self, path: Path = JEV_DIR):
        from transformers import AutoTokenizer  # noqa: PLC0415

        self.tok = AutoTokenizer.from_pretrained(str(path))
        self.head = json.loads((path / "adapter_vllm/decision_head.json").read_text())
        self.temps = json.loads((path / "calibration.json").read_text())["per_kind"]
        self.lo, self.hi = self.head["slots"]["ranges"]["choice"]
        self.labels, self.label_ids = self._single_token_labels("x\n{}) y")
        if self.label_ids[: self.hi - self.lo] != self.head["verbalizer_ids"][self.lo:self.hi]:
            raise SystemExit("a címketokenek nem egyeznek a fej choice-verbalizereivel")

    def _single_token_labels(self, context: str) -> tuple[list[str], list[int]]:
        out = []
        for lab in list(string.ascii_uppercase) + [a + b for a in string.ascii_uppercase for b in string.ascii_uppercase]:
            t = self.tok.encode(lab, add_special_tokens=False)
            if len(t) == 1 and t[0] in self.tok.encode(context.format(lab), add_special_tokens=False):
                out.append((lab, t[0]))
            if len(out) == MAX_OPTIONS:
                break
        return [lab for lab, _ in out], [t for _, t in out]

    def build(self, state: str, question: str, texts: list[str]) -> tuple[str, list[int], list[int], list[float]]:
        n = len(texts)
        if not 2 <= n <= MAX_OPTIONS:
            raise ValueError(f"a choice 2–{MAX_OPTIONS} opciót kér, itt {n}")
        lines = [f"{self.labels[i]}) {o}" for i, o in enumerate(texts)]
        text = bare_prompt("choice", state, question, lines)
        bias = [self.head["bias"][self.lo + i] if self.lo + i < self.hi else 0.0 for i in range(n)]
        return text, self.tok.encode(text, add_special_tokens=False), self.label_ids[:n], bias


def post(url: str, body: dict, timeout: float = 600, tries: int = 5) -> dict:
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except Exception:  # noqa: BLE001
            if attempt == tries - 1:
                raise
            time.sleep(3 * 2 ** attempt)
    raise RuntimeError("unreachable")


def softmax(z: list[float]) -> list[float]:
    m = max(z)
    e = [math.exp(x - m) for x in z]
    s = sum(e)
    return [x / s for x in e]


def readout(url: str, ids: list[int], label_ids: list[int], path: str = "ids") -> list[float]:
    """A címketokenek logprobjai. `ids`: logprob_token_ids (a kiolvaso03 útja); `allowed`: allowed_token_ids + top-n.
    A mintavételi paraméterek a serve_decide READ-jéé: a `--logprobs-mode processed_logprobs` mellett így a logprob a
    nyers eloszlás (T = 1, top-k/top-p nélkül), a címkékre szűkített softmax mindkét úton ugyanaz."""
    body = {"model": SERVED, "prompt": ids, "max_tokens": 1, "temperature": 1.0, "top_p": 1.0, "top_k": 0, "min_p": 0.0,
            "repetition_penalty": 1.0, "return_tokens_as_token_ids": True}
    if path == "ids":
        body |= {"logprobs": 1, "logprob_token_ids": label_ids}
    else:
        body |= {"logprobs": len(label_ids), "allowed_token_ids": label_ids}
    r = post(url + "/v1/completions", body)
    top = {int(k.split(":", 1)[1]): v for k, v in r["choices"][0]["logprobs"]["top_logprobs"][0].items()}
    return [top.get(t, -1e9) for t in label_ids]


def score(jev: Jev, lp: list[float], bias: list[float]) -> tuple[list[float], list[float]]:
    z = [v + b for v, b in zip(lp, bias)]
    return softmax(z), softmax([x / jev.temps["choice"] for x in z])


# --- itemek ----------------------------------------------------------------------------------------------------------

def load_items(names: list[str]) -> list[dict]:
    from hf_jellemzo05 import load_items as _load  # noqa: PLC0415

    return _load(names)


def item_row(jev: Jev, url: str, it: dict, perm: int, arm: str) -> dict:
    order = permutation(it, perm)
    texts, labs = jev_options(it, order, arm)
    text, ids, lids, bias = jev.build(it.get("state") or "", it["question"], texts)
    t0 = time.perf_counter()
    lp = readout(url, ids, lids)
    p, pj = score(jev, lp, bias)
    probs = dict(zip(labs, p))
    pred = max(probs, key=probs.get)
    gold = it.get("gold")
    return {"id": it["id"], "family": it["family"], "split": it["split"], "perm": perm, "arm": f"JEV-{arm}",
            "order": order, "labels": labs, "jev_labels": jev.labels[: len(labs)],
            "gold_label": next((lab for oid, lab in zip(order, labels_for(order)) if oid == gold), "X"),
            "content_state": content_state(it), "ketertelmu": bool(it.get("ketertelmu")), "pred": pred,
            "conf": probs[pred], "probs": probs, "probs_jev": dict(zip(labs, pj)), "label_logprobs": dict(zip(labs, lp)),
            "bias": dict(zip(labs, bias)), "n_prompt_tokens": len(ids), "latency_s": round(time.perf_counter() - t0, 4),
            "model": f"{JEV_REPO}@{JEV_REV}", "engine": "vllm"}


# --- alparancsok -----------------------------------------------------------------------------------------------------

def smoke(a) -> None:
    """(1) a címketokenek a fej verbalizereivel; (2) a repó /v1/decide-ja és a mi kiolvasásunk ugyanazt adja a README
    példáján és 30 D_dev-itemen, mindkét karral; (3) a két kiolvasási út egyezik; (4) áteresztés 32 párhuzamos kéréssel."""
    jev = Jev()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    res = {"revision": JEV_REV, "cimkek_egyeznek_a_fejjel": True, "elso_cimkek": jev.labels[:12],
           "temperature_choice": jev.temps["choice"]}
    info = None
    try:
        with urllib.request.urlopen(a.url + "/v1/decide/info", timeout=30) as r:
            info = json.loads(r.read())
    except Exception as e:  # noqa: BLE001
        res["decide_info_hiba"] = str(e)[:200]
    res["decide_info"] = info
    cases = [("README", README_PELDA["state"], README_PELDA["question"], README_PELDA["options"])]
    items = load_items(["D_dev"])[: a.n]
    for it in items:
        for arm in ("a", "b"):
            order = permutation(it, 0)
            texts, _ = jev_options(it, order, arm)
            if len(texts) >= 2:
                cases.append((f"{it['id']}|JEV-{arm}", it.get("state") or "", it["question"], texts))
    rows, maxd_decide, maxd_path = [], 0.0, 0.0
    for name, state, q, texts in cases:
        _, ids, lids, bias = jev.build(state, q, texts)
        lp = readout(a.url, ids, lids)
        lp2 = readout(a.url, ids, lids, path="allowed")
        p, pj = score(jev, lp, bias)
        p2, _ = score(jev, lp2, bias)
        maxd_path = max(maxd_path, max(abs(x - y) for x, y in zip(p, p2)))
        row = {"eset": name, "n_opcio": len(texts), "probs_jev": [round(x, 6) for x in pj], "valasztas": texts[pj.index(max(pj))]}
        if info is not None:
            d = post(a.url + "/v1/decide", {"kind": "choice", "state": state, "question": q, "options": texts,
                                            "strategy": "single", "thinking": "off"})
            dd = max(abs(x - y) for x, y in zip(pj, d["probabilities"]))
            maxd_decide = max(maxd_decide, dd)
            row |= {"decide_probs": [round(x, 6) for x in d["probabilities"]], "max_elteres": dd,
                    "decide_prompt_tokens": d["usage"]["prompt_tokens"], "sajat_prompt_tokens": len(ids)}
        rows.append(row)
    res["esetek"] = len(rows)
    res["readme_pelda"] = rows[0]
    res["max_elteres_decide_vs_sajat"] = maxd_decide if info is not None else None
    res["prompt_tokenszam_egyezik"] = all(r.get("decide_prompt_tokens") == r.get("sajat_prompt_tokens") for r in rows) \
        if info is not None else None
    res["max_elteres_ket_kiolvasasi_ut"] = maxd_path
    t0 = time.time()
    many = load_items(["D_dev"])[: 400]
    with ThreadPoolExecutor(32) as ex:
        acc = list(ex.map(lambda it: item_row(jev, a.url, it, 0, "a"), many))
    el = time.time() - t0
    res["ateresztes_keres_per_s"] = round(len(acc) / el, 1)
    res["d_dev_400_jev_a_pontossag_tajekoztato"] = round(sum(r["pred"] == r["gold_label"] for r in acc) / len(acc), 4)
    ok = res["max_elteres_ket_kiolvasasi_ut"] < 1e-4 and (info is None or (maxd_decide < 1e-4 and res["prompt_tokenszam_egyezik"]))
    res["atment"] = bool(ok)
    (out / "smoke.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out / "esetek.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k not in ("decide_info",)}, ensure_ascii=False, indent=1))
    sys.exit(0 if ok else 1)


def kiolvas(a) -> None:
    jev = Jev()
    items = load_items(a.feladat)
    if a.limit:
        items = items[: a.limit]
    perms = [int(p) for p in a.perms.split(",")]
    arms = a.karok.split(",")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        done = {(r["id"], r["perm"], r["arm"]) for r in map(json.loads, out.read_text(encoding="utf-8").splitlines())}
    jobs, skipped = [], 0
    for it in items:
        for p in perms:
            for arm in arms:
                if (it["id"], p, f"JEV-{arm}") in done:
                    continue
                if arm == "b" and len(it["options"]) < 2:
                    skipped += 1
                    continue
                jobs.append((it, p, arm))
    print(f"{len(items)} item × {len(perms)} perm × {len(arms)} kar; kész {len(done)}, hátra {len(jobs)}, "
          f"egyopciós JEV-b kimarad {skipped}", flush=True)

    def safe(job):
        try:
            return item_row(jev, a.url, *job), None
        except Exception as e:  # noqa: BLE001
            return None, {"id": job[0]["id"], "perm": job[1], "arm": job[2], "hiba": str(e)[:300]}

    t0, n_err = time.time(), 0
    status = Path(a.status) if a.status else None
    with open(out, "a", encoding="utf-8") as fh, open(out.with_suffix(".hibak.jsonl"), "a", encoding="utf-8") as eh, \
            ThreadPoolExecutor(a.concurrency) as ex:
        for i, (r, err) in enumerate(ex.map(safe, jobs), 1):
            if err:
                n_err += 1
                eh.write(json.dumps(err, ensure_ascii=False) + "\n")
            else:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            if i % 2000 == 0 or i == len(jobs):
                fh.flush()
                el = time.time() - t0
                left = (len(jobs) - i) / (i / el)
                msg = (f"{out.name}: {i}/{len(jobs)} · {i / el:.1f}/s · hiba {n_err} · hátra ~{left / 60:.0f} perc · "
                       f"várható vége {time.strftime('%H:%M', time.localtime(time.time() + left))}")
                print("  " + msg, flush=True)
                if status:
                    status.write_text(msg + "\n")
    print(f"kész: {len(jobs)} kiolvasás, ebből hiba {n_err}, {time.time() - t0:.0f} s", flush=True)
    if n_err > 0.01 * max(1, len(jobs)):
        raise SystemExit(f"a hibaarány {n_err / len(jobs):.1%} > 1%")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("smoke")
    s.add_argument("--url", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--n", type=int, default=30)
    k = sub.add_parser("kiolvas")
    k.add_argument("--url", required=True)
    k.add_argument("--feladat", action="append", required=True, help="szeletnév a szeletek05.json-ból; ismételhető")
    k.add_argument("--perms", default="0,1,2,3")
    k.add_argument("--karok", default="a,b")
    k.add_argument("--out", required=True)
    k.add_argument("--status", default="")
    k.add_argument("--concurrency", type=int, default=32)
    k.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    {"smoke": smoke, "kiolvas": kiolvas}[a.cmd](a)


if __name__ == "__main__":
    main()
