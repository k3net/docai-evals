"""03-as kör — szinonimaszűrés (03-runbook 4.3; a 00 S7 és a 01 `szinonim.py` receptje): hamis X és hamis hiba ellen.

Azokban a családokban, ahol a disztraktor a forrásszövegből jön (CELCSALADOK), minden nem-gold opcióra két független
bíráló (Mistral Small 4 és Gemma 4 26B-A4B; a 01-ben Mistral és Llama-3.3 volt, itt a Llama a 72 890 párra
4–6 órát adott volna) mondja meg egyetlen tokennel, hogy az opció
a helyzetre szintén helyes válasz lehet-e: P(igen) = igen / (igen + nem) a top-20 logprobból. Ha BÁRMELYIK bíráló
P(igen) ≥ P_MIN, az opció kikerül (a felidézés a cél: a téves találat csak egy disztraktort vesz el). Ha egy itemben
kettőnél kevesebb opció marad, vagy a gold-drop X-item egyetlen opciója sem marad, az item kiesik.

Célok: a keverő szinonim_celok.jsonl-je (a pool gold-drop X-ei, kiegyensúlyozás előtt) és a pool nem-X itemjei ezekből
a családokból.

  python3 kor03/eszkozok/szinonim03.py parok
  python3 kor03/eszkozok/szinonim03.py biral --tag mistral --url http://127.0.0.1:8430/v1 --model mistral-small-4 \\
      --extra '{"reasoning_effort": "none"}'
  python3 kor03/eszkozok/szinonim03.py dontes --tags mistral,gemma   → adat/f1/szinonim_dontes.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[0]
sys.path.append(str(ROOT.parent / "eszkozok"))
from biralo import chat  # noqa: E402

F0, F1 = ROOT / "adat/f0", ROOT / "adat/f1"
D = F1 / "szinonim"
P_MIN = 0.5
YES = {"igen", "ig", "i", "yes", "y"}
NO = {"nem", "ne", "n", "no"}
SYSTEM = "Ellenőrző vagy. Egyetlen szóval válaszolj: igen vagy nem."
# család → a bírálói kérdés; a helyzet elöl, az opció a végén (a prefix-cache miatt)
KERDES = {
    "qa.hurc": "Illik-e az alábbi kifejezés a ___ helyére, vagyis erre utalhat-e a kihagyott rész a szöveg alapján?",
    "qa.milqa": "Helyes válasz lehet-e az alábbi szövegrészlet a kérdésre a szöveg alapján?",
    "jogi.multieurlex": "Az alábbi EuroVoc-területhez is tartozhat-e ez a jogi aktus?",
    "kozbeszerzes.ted_cpv": "Ebbe a CPV-főcsoportba is tartozhat-e a beszerzés tárgya?",
    "konstrukcios.wiki_szakaszcim": "Illik-e ez a szakaszcím is a szövegrészhez?",
    "konstrukcios.wiki_folytatas": "Folytathatja-e ez a mondat is közvetlenül és értelmesen a szöveget?",
    "jogi.njt_torveny": "Származhat-e ez a rendelkezés ebből a törvényből is?",
    "jogi.njt_fejezet": "Tartozhat-e ez a rendelkezés ebbe a fejezetbe is?",
    "jogi.njt_cim": "Tartozhat-e ez a rendelkezés e cím alá is?",
}
CELCSALADOK = tuple(KERDES)


def items_by_id(ids: set[str]) -> dict[str, dict]:
    out = {}
    for fam in CELCSALADOK:
        for line in (F0 / f"{fam}.jsonl").read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r["id"] in ids:
                out[r["id"]] = r
    return out


def user_prompt(it: dict, opt_text: str) -> str:
    return (f"{KERDES[it['family']]}\n\nHelyzet:\n{it['state']}\n\nEredeti kérdés: {it['question']}\n\n"
            f"Opció: {opt_text}\n\nVálasz (igen/nem):")


def cmd_parok(a) -> None:
    # a keverő célhalmaza: a szűrendő családokban a kvóta 1,3-szereséig vett jelöltek (tartalékkal)
    ids = {json.loads(line)["id"] for line in (F1 / "szinonim_celok.jsonl").read_text(encoding="utf-8").splitlines()}
    items = items_by_id(ids)
    D.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(D / "parok.jsonl", "w", encoding="utf-8") as fh:
        for iid in sorted(items):
            it = items[iid]
            for o in it["options"]:
                if o["id"] == it["gold"]:
                    continue
                fh.write(json.dumps({"pid": f"{iid}|{o['id']}", "item": iid, "opt": o["id"], "family": it["family"],
                                     "prompt": user_prompt(it, o["text"])}, ensure_ascii=False) + "\n")
                n += 1
    print(f"{len(items)} item, {n} pár", dict(Counter(it["family"] for it in items.values())))


def p_yes(r: dict) -> tuple[float | None, float]:
    yes = no = 0.0
    for t in r["choices"][0]["logprobs"]["content"][0]["top_logprobs"]:
        tok = t["token"].strip().lower()
        if tok in YES:
            yes += math.exp(t["logprob"])
        elif tok in NO:
            no += math.exp(t["logprob"])
    return (yes / (yes + no) if yes + no > 0 else None), yes + no


def cmd_biral(a) -> None:
    extra = json.loads(a.extra) if a.extra else {}
    path = D / f"biral.{a.tag}.jsonl"
    done = {json.loads(line)["pid"] for line in path.read_text(encoding="utf-8").splitlines()} if path.exists() else set()
    pairs = [json.loads(line) for line in (D / "parok.jsonl").read_text(encoding="utf-8").splitlines()]
    todo = [p for p in pairs if p["pid"] not in done]
    print(f"{a.tag}: {len(done)} kész, {len(todo)} hátra", flush=True)

    def one(p: dict) -> dict:
        try:
            r = chat(a.url, a.model, [{"role": "system", "content": SYSTEM}, {"role": "user", "content": p["prompt"]}],
                     {"max_tokens": 1, "temperature": 0, "logprobs": True, "top_logprobs": 20, **extra}, None, timeout=600)
            py, mass = p_yes(r)
            return {"pid": p["pid"], "p_igen": py, "tomeg": mass}
        except Exception as e:  # noqa: BLE001
            return {"pid": p["pid"], "p_igen": None, "tomeg": 0.0, "hiba": str(e)[:200]}

    with open(path, "a", encoding="utf-8") as fh, ThreadPoolExecutor(a.workers) as ex:
        for i, r in enumerate(ex.map(one, todo), 1):
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            fh.flush()
            if i % 1000 == 0:
                print(f"  {i}/{len(todo)}", flush=True)


def cmd_dontes(a) -> None:
    pairs = [json.loads(line) for line in (D / "parok.jsonl").read_text(encoding="utf-8").splitlines()]
    votes: dict[str, list[float | None]] = defaultdict(list)
    for tag in a.tags.split(","):
        for line in (D / f"biral.{tag}.jsonl").read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            votes[r["pid"]].append(r["p_igen"])
    items = items_by_id({p["item"] for p in pairs})
    out, why, fam_rate = {}, Counter(), defaultdict(lambda: [0, 0])
    removed = defaultdict(list)
    for p in pairs:
        v = votes.get(p["pid"], [])
        flag = any(x is not None and x >= P_MIN for x in v) or not any(x is not None for x in v)
        fam_rate[p["family"]][0] += flag
        fam_rate[p["family"]][1] += 1
        if flag:
            removed[p["item"]].append(p["opt"])
    for iid, it in items.items():
        rest = [o for o in it["options"] if o["id"] not in removed.get(iid, [])]
        drop = len(rest) < (2 if it["gold"] is None else 2)
        out[iid] = {"kivett": removed.get(iid, []), "kizart": drop}
        why["kizárt item" if drop else ("opció kivéve" if removed.get(iid) else "érintetlen")] += 1
    rep = {"p_min": P_MIN, "biralok": a.tags, "item": dict(why),
           "kivett_arany": {f: round(k / n, 4) for f, (k, n) in sorted(fam_rate.items())}}
    (F1 / "szinonim_dontes.json").write_text(json.dumps({"riport": rep, "itemek": out}, ensure_ascii=False, indent=1),
                                             encoding="utf-8")
    print(json.dumps(rep, ensure_ascii=False, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["parok", "biral", "dontes"])
    ap.add_argument("--tag")
    ap.add_argument("--tags", default="mistral,gemma")
    ap.add_argument("--url")
    ap.add_argument("--model")
    ap.add_argument("--extra", default="")
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args()
    {"parok": cmd_parok, "biral": cmd_biral, "dontes": cmd_dontes}[a.cmd](a)


if __name__ == "__main__":
    main()
