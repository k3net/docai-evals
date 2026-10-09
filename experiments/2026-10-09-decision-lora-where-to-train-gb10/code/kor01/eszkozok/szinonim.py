"""Szinonim-eszközszűrés (01-runbook 2. pont; a 00 F1F-leletének megfelelője): hamis X és hamis hiba ellen.

A gold-drop X csak akkor helyes, ha a listán maradt opciók egyike sem teljesíti a kérést. A közeli pár pedig hamis
hibát ad, ha a kérésre ő is helyes. Két független, nem-Qwen bíráló (Mistral Small 4, Llama-3.3-70B) dönt, egyetlen
kimeneti tokennel: P(igen) = igen / (igen + nem) a top-20 logprobból (a 00 `duplikatum_llm.py`-ja szerint).

  parok  — (item, opció) párok:
           * `xdrop`: minden gold-drop item minden opciója („teljesíti-e ez az eszköz a kérést?”);
           * `kozeli`: a nem-X MASSIVE- és T-katalógus-itemeken a gold `felulvizsgal`-párjai, ha a listán vannak.
           A BFCL és a When2Call nem kerül bele: azok gold-ja a benchmarké.
  biral  — egy bíráló a párokon (újraindítható, a kérdés elöl áll a prefix-cache miatt).
  dontes — kizárja az azonos nevű opciót tartalmazó itemeket (az xLAM-forrás egy listán két azonos nevű eszközt is
           ad: az opció-id ütközik, a gold-drop hamis X lehet). `xdrop`: ha BÁRMELYIK bíráló P(igen) ≥ P_MIN, az opció kicserélődik egy nem rokon eszközre (a felidézés a
           cél: a téves találat csak egy zavaró opciót cserél); `kozeli`: ha a két bíráló átlaga ≥ P_MIN, az item
           kétértelmű (soft = {gold, pár}); ha csak az egyiké, jelzést kap a címke-átnézésre.
           Az itemfájlokat helyben írja át (mentés: `*.pre_szinonim`); riport: eredmenyek/F1S/szinonim_riport.json.

  python3 kor01/eszkozok/szinonim.py parok
  python3 kor01/eszkozok/szinonim.py biral --tag mistral --url http://127.0.0.1:8430/v1 --model mistral-small-4 \\
      --extra-body '{"reasoning_effort": "none"}'
  python3 kor01/eszkozok/szinonim.py dontes --tags mistral,llama
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kozos01 import A, F1S, R, catalog, chat, massive_map, opt_line, p_yes, read_jsonl, write_json, write_jsonl  # noqa: E402
from osszeallit import cat_opt  # noqa: E402

SEED = 20261008
P_MIN = 0.5
D = F1S / "szinonim"
SYSTEM = {"hu": "Eszközválasztást ellenőrzöl. Egyetlen szóval válaszolj: igen vagy nem.",
          "en": "You are checking tool selection. Answer with a single word: yes or no."}
# a kérdés elöl, a változó rész a végén: a közös eleje a prefix-cache-ben marad
PROMPT = {
    "hu": ("Döntsd el, hogy az alábbi eszköz meghívásával teljesíthető-e a felhasználó kérése. Ha az eszköz a kérést "
           "csak részben, más célra vagy kerülőúton szolgálja ki, a válasz: nem.\n\nKérés: \"{req}\"\nEszköz: {opt}\n\n"
           "Válasz (igen/nem):"),
    "en": ("Decide whether calling the tool below fulfils the user's request. If the tool serves the request only "
           "partly, for a different purpose or in a roundabout way, the answer is no.\n\nRequest: \"{req}\"\n"
           "Tool: {opt}\n\nAnswer (yes/no):"),
}


def item_files() -> dict[str, Path]:
    fs = {s: A / f"items_{s}.jsonl" for s in ("train", "val", "teszt")}
    fs["katalogus"] = F1S / "items_katalogus.jsonl"
    miss = [str(f) for f in fs.values() if not f.exists()]
    if miss:
        raise SystemExit(f"hiányzik: {miss}")
    return fs


def dropped_gold(it: dict, mm: dict) -> str | None:
    m = it["meta"]
    if m.get("kivett_gold"):
        return m["kivett_gold"]
    if it["forras"] == "massive_hu":
        return mm.get(m.get("intent"))
    return None


def cmd_parok(args) -> None:
    cat = catalog()
    out, stat = [], Counter()
    for name, f in item_files().items():
        for it in read_jsonl(f):
            if it["forras"].startswith(("bfcl", "w2c")):
                continue
            if it["meta"].get("x_fajta") == "gold-drop":
                for o in it["options"]:
                    out.append({"fajta": "xdrop", "fajl": name, "id": it["id"], "opcio": o["id"], "lang": it["lang"],
                                "prompt": PROMPT[it["lang"]].format(req=it["request"], opt=opt_line(o, it["lang"]))})
                    stat[f"xdrop:{name}"] += 1
            elif it["gold"] in cat:
                for o in it["options"]:
                    if o["id"] in cat[it["gold"]]["felulvizsgal"]:
                        out.append({"fajta": "kozeli", "fajl": name, "id": it["id"], "opcio": o["id"], "lang": it["lang"],
                                    "prompt": PROMPT[it["lang"]].format(req=it["request"], opt=opt_line(o, it["lang"]))})
                        stat[f"kozeli:{name}"] += 1
    write_jsonl(D / "parok.jsonl", out)
    write_json(D / "parok_riport.json", {"n": len(out), **dict(stat)})
    print(len(out), dict(stat))


def cmd_biral(args) -> None:
    extra = {"max_tokens": 1, "temperature": 0, "logprobs": True, "top_logprobs": 20, **json.loads(args.extra_body)}
    tasks = read_jsonl(D / "parok.jsonl")
    if args.limit:
        tasks = tasks[: args.limit]
    out = D / f"biral_{args.tag}.jsonl"
    key = lambda t: f"{t['fajl']}|{t['id']}|{t['opcio']}"  # noqa: E731
    done = {key(r): r for r in read_jsonl(out)} if out.exists() else {}
    todo = [t for t in tasks if key(t) not in done or done[key(t)].get("p") is None]

    def run(t):
        base = {"fajta": t["fajta"], "fajl": t["fajl"], "id": t["id"], "opcio": t["opcio"]}
        try:
            r = chat(args.url, args.model, [{"role": "system", "content": SYSTEM[t["lang"]]},
                                            {"role": "user", "content": t["prompt"]}], extra, None)
            p, mass = p_yes(r)
            return {**base, "p": p, "tomeg": round(mass, 4)}
        except Exception as e:  # egy kérés hibája ne állítsa le a kört; az újrafuttatás pótolja
            return {**base, "p": None, "hiba": str(e)[:200]}

    with ThreadPoolExecutor(args.concurrency) as ex:
        for k, res in enumerate(ex.map(run, todo)):
            done[key(res)] = res
            if k % 2000 == 1999:
                write_jsonl(out, done.values())
                print(f"{k + 1}/{len(todo)}", flush=True)
    write_jsonl(out, done.values())
    rows = list(done.values())
    write_json(out.with_suffix(".summary.json"), {"n": len(rows), "valaszolt": sum(r.get("p") is not None for r in rows),
                                                  "igen": sum((r.get("p") or 0) >= P_MIN for r in rows), "model": args.model})
    print(f"{out}: {sum(r.get('p') is not None for r in rows)}/{len(rows)}")


def cmd_dontes(args) -> None:
    cat, mm = catalog(), massive_map()
    tags = args.tags.split(",")
    judg = {t: {(r["fajl"], r["id"], r["opcio"]): r.get("p") for r in read_jsonl(D / f"biral_{t}.jsonl")} for t in tags}
    pairs = read_jsonl(D / "parok.jsonl")
    miss = [p for p in pairs if any(judg[t].get((p["fajl"], p["id"], p["opcio"])) is None for t in tags)]
    if len(miss) > args.max_hiany:
        raise SystemExit(f"{len(miss)} pár bírálat nélkül (megengedett {args.max_hiany})")
    by_item = defaultdict(list)
    for p in pairs:
        ps = [judg[t].get((p["fajl"], p["id"], p["opcio"])) for t in tags]
        by_item[(p["fajl"], p["id"])].append((p["fajta"], p["opcio"], ps))
    files = item_files()
    src = {}
    for name, f in files.items():
        bak = f.with_suffix(".jsonl.pre_szinonim")
        if not bak.exists():  # idempotens: mindig a szűrés előtti állapotból indul
            shutil.copy(f, bak)
        src[name] = read_jsonl(bak)
    xlam_pool = {s: {} for s in ("train", "val")}
    for s in ("train", "val"):
        for it in src[s]:
            if it["forras"] == "xlam":
                for o in it["options"]:
                    xlam_pool[s].setdefault(o["id"], o)
    xlam_pool["val"] = {**xlam_pool["train"], **xlam_pool["val"]}
    rng = random.Random(SEED)
    rep: dict = {"p_min": P_MIN, "biralok": tags, "hianyzo_bíralat": len(miss)}
    for name, f in files.items():
        st = Counter()
        items = []
        for it in src[name]:  # a forrás azonos nevű eszközei (xLAM): az opció-id ütközik, a gold-drop pedig hamis X lehet
            ids = [o["id"] for o in it["options"]]
            if len(ids) != len(set(ids)) or it["meta"].get("kivett_gold") in ids:
                st[f"kizart_azonos_nevu_opcio:{it['forras']}"] += 1
                continue
            items.append(it)
        for it in items:
            dec = by_item.get((name, it["id"]))
            if not dec:
                continue
            have = {o["id"] for o in it["options"]}
            for fajta, oid, ps in dec:
                vals = [p for p in ps if p is not None]
                if fajta == "xdrop" and vals and max(vals) >= P_MIN:
                    g = dropped_gold(it, mm)
                    if it["forras"] == "xlam":
                        pool = [o for k, o in xlam_pool["val" if name == "val" else "train"].items() if k not in have | {g}]
                    else:
                        banned = have | ({g} | set(cat[g]["kozeli"]) | set(cat[g]["felulvizsgal"]) if g in cat else set())
                        pool = [cat_opt(cat[k]) for k in sorted(cat) if k not in banned]
                    new = rng.choice(pool)
                    k = next(i for i, o in enumerate(it["options"]) if o["id"] == oid)
                    it["options"][k] = new
                    have = (have - {oid}) | {new["id"]}
                    it["meta"].setdefault("szinonim_csere", []).append({"ki": oid, "be": new["id"], "p": [round(v, 3) for v in vals]})
                    st["xdrop_csere"] += 1
                elif fajta == "kozeli" and vals:
                    mean = sum(vals) / len(vals)
                    if mean >= P_MIN and len(vals) == len(tags):
                        it["meta"]["ketertelmu"] = True
                        it["meta"]["soft"] = sorted({it["gold"], oid})
                        st["kozeli_ketertelmu"] += 1
                    elif max(vals) >= P_MIN:
                        it["meta"].setdefault("szinonim_jelzes", []).append({"opcio": oid, "p": [round(v, 3) for v in vals]})
                        st["kozeli_jelzes"] += 1
            st["erintett_item"] += 1
        write_jsonl(f, items)
        rep[name] = dict(st)
    rep["xdrop_igen_bíralonkent"] = {t: sum(1 for p in pairs if p["fajta"] == "xdrop" and (judg[t].get((p["fajl"], p["id"], p["opcio"])) or 0) >= P_MIN)
                                     for t in tags}
    write_json(R / "F1S/szinonim_riport.json", rep)
    print(json.dumps(rep, ensure_ascii=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["parok", "biral", "dontes"])
    ap.add_argument("--tag", default="")
    ap.add_argument("--tags", default="mistral,llama")
    ap.add_argument("--url", default="")
    ap.add_argument("--model", default="")
    ap.add_argument("--concurrency", type=int, default=16)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--max-hiany", type=int, default=0)
    ap.add_argument("--extra-body", default="{}")
    args = ap.parse_args()
    {"parok": cmd_parok, "biral": cmd_biral, "dontes": cmd_dontes}[args.cmd](args)


if __name__ == "__main__":
    main()
