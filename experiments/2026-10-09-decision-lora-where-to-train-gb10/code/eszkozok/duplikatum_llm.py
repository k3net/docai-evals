"""Katalógus-duplikátumok és értelmetlen cikknevek LLM-bírálattal (F1F, 2026-10-04).

Dani első 99 átnézett itemjében a 12 problémás címkéből 9 katalógus-duplikátum: ugyanaz a termék két cikkszámon,
más néven („Mozzarella ball 125 g” / „Mozzarella golyó 125 g”), és 2 értelmetlen cikknév. Embedding-szabály ezt
nem választja szét a szándékos nehéz negatívoktól (duplikatum_kalibral.py), ezért a két nem-Qwen bíráló dönt:

  parok   — jelölt párok: minden sor valódi cikke × a teljes S6-jelöltlistája (a tartalékkal együtt, tehát minden,
            ami az S7-ben opció lehet), családon kívül, gyűjtőcikk nélkül, számkompatibilis (az egyik szám/mértékegység-
            halmaza része a másikénak), és bge-m3 koszinusz ≥ COS_MIN VAGY közös szótő; plusz a kalibrációs párok.
            (Dani 9 duplikátum-párjából 3 koszinusza 0,60–0,66: a koszinusz-küszöb egyedül nem elég.)
            A cikkek: minden valódi cikk (a névbírálathoz).
  biral   — egy bíráló (vLLM, OpenAI-kompatibilis): a párok MINDKÉT sorrendben (a pozíciós torzítás ellen) és a
            cikknevek; egyetlen kimeneti token, P(igen) = igen / (igen + nem) a top-20 logprobból.
  dontes  — duplikátum, ha bármelyik bíráló két sorrendre átlagolt P(igen)-je ≥ DUP_P (bírálónként a felidézés a
            cél: a téves duplikátum csak egy zavaró opciót cserél le); értelmetlen név, ha MINDKÉT bíráló P(igen)-je
            < NEV_P (a téves találat itemet ejt ki). Kalibráció Dani döntésein; kapu: a 9 ismert duplikátum-párból
            legalább KAPU_DUP megfogva.

  python3 eszkozok/duplikatum_llm.py parok --gen adat/f1 --dir adat/f1/dedup
  python3 eszkozok/duplikatum_llm.py biral --dir adat/f1/dedup --url http://127.0.0.1:8420/v1 --model llama33-70b-fp8
  python3 eszkozok/duplikatum_llm.py dontes --gen adat/f1 --dir adat/f1/dedup
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from biralo import chat  # noqa: E402
from common import EXP, read_jsonl, write_json, write_jsonl  # noqa: E402
from duplikatum import equiv, nums, words  # noqa: E402

COS_MIN = 0.60
DUP_P = 0.5
NEV_P = 0.5
KAPU_DUP = 7

SYSTEM = "Egy vendéglátó cég cikktörzsét tisztítod. Egyetlen szóval válaszolj: igen vagy nem."
# A kérdés áll elöl, a változó tétel(ek) a végén: így minden kérés ~150 tokenes eleje közös, és a vLLM
# prefix-cache-e csak a pár ~40 tokenjét számolja újra (a fordított sorrenddel a Llama ~3,9 kérés/s volt).
PAR_PROMPT = """Döntsd el, jelölheti-e az alábbi két cikktörzs-tétel ugyanazt a terméket vagy szolgáltatást (más néven, \
más szórenddel, más nyelven, vagy az egyik kevesebb részlettel), úgyhogy egy számlasort, amely az egyiket írja le, \
joggal a másikra is be lehetne sorolni. Ha valamely lényeges tulajdonságban biztosan eltérnek (fajta, íz, méret, \
zsírtartalom, kiszerelés, anyag, helyszín, időszak), a válasz: nem.

1) {a} [{pa}]
2) {b} [{pb}]

Válasz (igen/nem):"""
NEV_PROMPT = """Döntsd el, értelmes, valóságban is létező termék vagy szolgáltatás megnevezése-e az alábbi cikktörzs-tétel. \
A kategória-besorolás pontosságát most ne nézd, csak azt, hogy a megnevezés értelmes-e.

Cikktörzs-tétel: {a}
Kategória: {pa}

Válasz (igen/nem):"""


def _p(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else EXP / p


def compatible(a: str, b: str) -> bool:
    na, nb = set(nums(a)), set(nums(b))
    return na <= nb or nb <= na


def shared_stem(a: str, b: str) -> bool:
    """Van-e közös (ragozás-ekvivalens) ≥ 4 betűs szó, összetett szó végén is („Jégsaláta” / „Saláta”)."""
    wa, wb = [w for w in words(a) if len(w) >= 4], [w for w in words(b) if len(w) >= 4]
    return any(equiv(x, y) or x.endswith(y) or y.endswith(x) for x in wa for y in wb)


def cmd_parok(args) -> None:
    from jeloltek import Embedder

    gen, d = _p(args.gen), _p(args.dir)
    arts = {a["id"]: a for a in read_jsonl(gen / "s1_katalogus.jsonl")}
    rows = {r["row"]: r for r in read_jsonl(gen / "s4_sorok.jsonl")}
    kal = json.load(open(d / "kalibracio.json"))
    cand = set()
    for c in read_jsonl(gen / "s6_jeloltek.jsonl"):
        a = rows[c["row"]]["article"]
        for i, _ in c["bm25"] + c["vector"]:
            if i != a and not arts[i]["catchall"] and arts[i]["family"] != arts[a]["family"]:
                cand.add(tuple(sorted((a, i))))
    kal_pairs = {tuple(sorted((p["a"], p["b"]))) for p in kal["duplikatum_parok"] + kal["nem_duplikatum_parok"]}
    ids = sorted({i for p in cand | kal_pairs for i in p})
    pos = {i: k for k, i in enumerate(ids)}
    v = Embedder()([arts[i]["name"] for i in ids], max_len=64)
    out, stat = [], Counter()
    for a, b in sorted(cand | kal_pairs):
        s = float(v[pos[a]] @ v[pos[b]])
        kal_p = (a, b) in kal_pairs
        stat["jelolt"] += (a, b) in cand
        na, nb = arts[a]["name"], arts[b]["name"]
        if kal_p or (compatible(na, nb) and (s >= COS_MIN or shared_stem(na, nb))):
            out.append({"a": a, "b": b, "cos": round(s, 4), "kal": kal_p})
            stat["biralando"] += 1
            stat["csak_kozos_szo"] += s < COS_MIN and not kal_p
    write_jsonl(d / "parok.jsonl", out)
    cikkek = sorted(i for i, a in arts.items() if not a["catchall"])
    write_jsonl(d / "cikkek.jsonl", [{"a": i} for i in cikkek])
    stat["cikk"] = len(cikkek)
    write_json(d / "parok_riport.json", dict(stat))
    print(json.dumps(dict(stat), ensure_ascii=False))


def p_igen(r: dict) -> tuple[float | None, float]:
    """P(igen) a top-20 logprobból (igen/nem-szerű első tokenek tömegével), és a két válasz együttes tömege."""
    top = r["choices"][0]["logprobs"]["content"][0]["top_logprobs"]
    yes = no = 0.0
    for t in top:
        tok = t["token"].strip().lower()
        if tok in ("igen", "ig", "i"):
            yes += math.exp(t["logprob"])
        elif tok in ("nem", "ne", "n"):
            no += math.exp(t["logprob"])
    return (yes / (yes + no) if yes + no > 0 else None), yes + no


def cmd_biral(args) -> None:
    d = _p(args.dir)
    gen = _p(args.gen)
    arts = {a["id"]: a for a in read_jsonl(gen / "s1_katalogus.jsonl")}
    extra = {"max_tokens": 1, "temperature": 0, "logprobs": True, "top_logprobs": 20, **json.loads(args.extra_body)}
    tasks = []
    for p in read_jsonl(d / "parok.jsonl"):
        for x, y in ((p["a"], p["b"]), (p["b"], p["a"])):
            tasks.append(("par", f"{x}|{y}", PAR_PROMPT.format(a=arts[x]["name"], pa=arts[x]["path"], b=arts[y]["name"], pb=arts[y]["path"])))
    for c in read_jsonl(d / "cikkek.jsonl"):
        tasks.append(("nev", c["a"], NEV_PROMPT.format(a=arts[c["a"]]["name"], pa=arts[c["a"]]["path"])))
    if args.limit:
        tasks = tasks[: args.limit]
    out = d / f"biral_{args.tag}.jsonl"
    done = {(r["fajta"], r["kulcs"]): r for r in read_jsonl(out)} if out.exists() else {}
    todo = [t for t in tasks if (t[0], t[1]) not in done or done[(t[0], t[1])].get("p") is None]

    def run(t):
        fajta, kulcs, prompt = t
        try:
            r = chat(args.url, args.model, [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}], extra, None)
            p, mass = p_igen(r)
            return {"fajta": fajta, "kulcs": kulcs, "p": p, "tomeg": round(mass, 4)}
        except Exception as e:  # egy kérés hibája ne állítsa le a kört; az újrafuttatás pótolja
            return {"fajta": fajta, "kulcs": kulcs, "p": None, "hiba": str(e)[:200]}

    with ThreadPoolExecutor(args.concurrency) as ex:
        for k, res in enumerate(ex.map(run, todo)):
            done[(res["fajta"], res["kulcs"])] = res
            if k % 2000 == 1999:
                write_jsonl(out, done.values())
                print(f"{k + 1}/{len(todo)}", flush=True)
    write_jsonl(out, done.values())
    rows = list(done.values())
    summ = {"model": args.model, "n": len(rows), "valasz": sum(r.get("p") is not None for r in rows),
            "tomeg_median": sorted(r.get("tomeg", 0) for r in rows)[len(rows) // 2] if rows else None}
    write_json(d / f"biral_{args.tag}.summary.json", summ)
    print(json.dumps(summ, ensure_ascii=False))


def cmd_dontes(args) -> None:
    d = _p(args.dir)
    gen = _p(args.gen)
    arts = {a["id"]: a for a in read_jsonl(gen / "s1_katalogus.jsonl")}
    kal = json.load(open(d / "kalibracio.json"))
    tags = args.tags.split(",")
    par_p, nev_p = defaultdict(dict), defaultdict(dict)
    for tag in tags:
        acc = defaultdict(list)
        for r in read_jsonl(d / f"biral_{tag}.jsonl"):
            if r.get("p") is None:
                continue
            if r["fajta"] == "par":
                acc[tuple(sorted(r["kulcs"].split("|")))].append(r["p"])
            else:
                nev_p[r["kulcs"]][tag] = r["p"]
        for k, ps in acc.items():
            par_p[k][tag] = sum(ps) / len(ps)
    pairs = read_jsonl(d / "parok.jsonl")
    dup = [p for p in pairs if max(par_p.get((p["a"], p["b"]), {}).values(), default=0.0) >= DUP_P]
    rossz = sorted(i for i, ps in nev_p.items() if len(ps) == len(tags) and all(v < NEV_P for v in ps.values()))

    def pp(a, b):
        return {t: round(v, 3) for t, v in par_p.get(tuple(sorted((a, b))), {}).items()}

    kal_dup = [{**p, "nev_a": arts[p["a"]]["name"], "nev_b": arts[p["b"]]["name"], "p": pp(p["a"], p["b"]),
                "fogva": max(pp(p["a"], p["b"]).values(), default=0.0) >= DUP_P} for p in kal["duplikatum_parok"]]
    neg = kal["nem_duplikatum_parok"]
    neg_hit = [p for p in neg if max(pp(p["a"], p["b"]).values(), default=0.0) >= DUP_P]
    res = {
        "biralok": tags, "dup_p": DUP_P, "nev_p": NEV_P, "cos_min": COS_MIN,
        "birált_par": len(pairs), "duplikatum_par": len(dup),
        "duplikatum_par_biralonkent": {t: sum(par_p.get((p["a"], p["b"]), {}).get(t, 0.0) >= DUP_P for p in pairs) for t in tags},
        "ertelmetlen_nev": len(rossz), "cikk": len(nev_p),
        "kalibracio": {
            "duplikatum_fogva": sum(k["fogva"] for k in kal_dup), "duplikatum_n": len(kal_dup), "kapu_min": KAPU_DUP,
            "nem_duplikatum_jelolve": len(neg_hit), "nem_duplikatum_n": len(neg),
            "jo_itemek_opciovesztessel": len({p["item"] for p in neg_hit}), "jo_itemek_n": len({p["item"] for p in neg}),
            "ertelmetlen_fogva": [{"a": c["a"], "nev": arts[c["a"]]["name"], "p": nev_p.get(c["a"])} for c in kal["ertelmetlen_nev"]],
            "jo_cikk_kiejtve": sum(c["a"] in set(rossz) for c in kal["jo_cikk"]), "jo_cikk_n": len(kal["jo_cikk"]),
            "duplikatum_parok": kal_dup,
            "nem_duplikatum_jelolt_peldak": [[arts[p["a"]]["name"], arts[p["b"]]["name"], pp(p["a"], p["b"])] for p in neg_hit[:30]],
        },
        "ertelmetlen_peldak": [[arts[i]["name"], arts[i]["path"], nev_p[i]] for i in rossz[:40]],
    }
    res["kapu_ok"] = res["kalibracio"]["duplikatum_fogva"] >= KAPU_DUP
    write_json(d / "dontes_riport.json", res)
    write_json(d / "duplikatumok.json", {"parok": [[p["a"], p["b"]] for p in dup], "ertelmetlen_nev": rossz,
                                          "dup_p": DUP_P, "nev_p": NEV_P, "biralok": tags})
    print(json.dumps({k: v for k, v in res.items() if k not in ("ertelmetlen_peldak",)}, ensure_ascii=False, indent=1))
    if not res["kapu_ok"]:
        raise SystemExit(f"kalibrációs kapu: {res['kalibracio']['duplikatum_fogva']}/{len(kal_dup)} < {KAPU_DUP}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["parok", "biral", "dontes"])
    ap.add_argument("--gen", default="adat/f1")
    ap.add_argument("--dir", default="adat/f1/dedup")
    ap.add_argument("--url", default="")
    ap.add_argument("--model", default="")
    ap.add_argument("--tag", default="", help="a bíráló rövid neve a kimeneti fájlban (llama, mistral)")
    ap.add_argument("--tags", default="llama,mistral")
    ap.add_argument("--concurrency", type=int, default=16)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--extra-body", default="{}")
    args = ap.parse_args()
    {"parok": cmd_parok, "biral": cmd_biral, "dontes": cmd_dontes}[args.cmd](args)


if __name__ == "__main__":
    main()
