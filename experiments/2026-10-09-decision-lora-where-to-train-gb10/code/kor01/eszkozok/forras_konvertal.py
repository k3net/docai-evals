"""01-es kör — a nyilvános források egységes item-formátumra (01-runbook 2–4. pont), GPU nélkül.

Item: {id, forras, split, lang, request, history, options: [{id, name, description, required}], gold (név | None = X),
       meta: {klaszter, …}}. Az opciók sorrendje itt a forrásé; a keverés és a címkézés (A–J) az F1 összeállítás dolga.
- BFCL (teszt): simple, multiple, irrelevance, live_simple, live_multiple, live_irrelevance. Gold a possible_answer
  első hívásának neve; az irrelevance-ben X. Kizárva: 0 vagy > 10 eszköz.
- When2Call teszt (MCQ): tool_call és request_for_info → gold = target_tool (nincs külön visszakérdezés-címke,
  user-döntés 2026-10-06); cannot_answer → X. A forrás a BFCL-live, ezért a klaszter a source_id: a BFCL-live
  itemmel közös, a bootstrapban egy klaszter.
- When2Call train (SFT): csak szöveges válaszok. „Nem tudom” + ≥ 1 eszköz → X; visszakérdezés + pontosan 1 eszköz →
  gold = az az eszköz. A többi (több eszközös visszakérdezés: a gold nem azonosítható) kimarad.
- xLAM-60k (train): azok a sorok, amelyekben minden hívás ugyanarra az eszközre szól → gold = az az eszköz
  (39 552 sor). A klaszter a normalizált kérés, hogy az xlam-irrelevance párja ugyanabba a splitbe kerüljön.
- xlam-irrelevance-7.5k (train): a gold eszköz kivéve → X; klaszter a normalizált kérés.
- MASSIVE hu-HU: mondat-szintű rekordok a katalógus-leképezéssel (katalogus/massive_lekepezes.json); a jelöltlista
  az F1-ben épül.
- EU-180k hu: a 29 240 sor 136 egyedi beszélgetés (mind 215×); dedup után gold = az első hívott eszköz, X ha nincs
  hívás. Az eszközleírások kinyerése az F1 LLM-lépése.

  python3 kor01/eszkozok/forras_konvertal.py   → kor01/adat/*.jsonl + forras_riport.json
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
F, OUT = ROOT / "forras", ROOT / "adat"
MAX_OPT = 10


def jl(path: Path) -> list[dict]:
    return [json.loads(line) for line in open(path) if line.strip()]


def write(name: str, rows: list[dict]) -> None:
    with open(OUT / name, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def opt(fn: dict | str) -> dict:
    d: dict = json.loads(fn) if isinstance(fn, str) else fn
    req = (d.get("parameters") or {}).get("required") or []
    return {"id": d["name"], "name": d["name"], "description": (d.get("description") or "").strip(), "required": req}


def split_question(q: list) -> tuple[str, list]:
    msgs = q[0] if q and isinstance(q[0], list) else q
    users = [i for i, m in enumerate(msgs) if m["role"] == "user"]
    last = users[-1]
    return msgs[last]["content"], msgs[:last]


def bfcl(rep: dict) -> list[dict]:
    items = []
    for cat in ("simple", "multiple", "irrelevance", "live_simple", "live_multiple", "live_irrelevance"):
        rows = jl(F / f"bfcl/BFCL_v3_{cat}.json")
        pa = {r["id"]: r for r in jl(F / f"bfcl/possible_answer_{cat}.json")} if "irrelevance" not in cat else {}
        c = Counter()
        for r in rows:
            opts = [opt(fn) for fn in r["function"]]
            if not opts or len(opts) > MAX_OPT:
                c[f"kizarva_{'0' if not opts else '>10'}_eszkoz"] += 1
                continue
            gold = None
            if pa:
                if r["id"] not in pa:
                    c["kizarva_nincs_possible_answer"] += 1
                    continue
                gt = pa[r["id"]]["ground_truth"]
                gold = next(iter(gt[0])) if gt else None
                if gold not in {o["id"] for o in opts}:
                    c["kizarva_gold_nincs_a_listan"] += 1
                    continue
            req, hist = split_question(r["question"])
            items.append({"id": f"bfcl-{r['id']}", "forras": f"bfcl_{cat}", "split": "teszt", "lang": "en", "request": req,
                          "history": hist, "options": opts, "gold": gold,
                          "meta": {"klaszter": r["id"], "n_tools": len(opts)}})
            c["item"] += 1
        rep[f"bfcl_{cat}"] = dict(c)
    return items


def when2call_test(rep: dict) -> list[dict]:
    items, c = [], Counter()
    for r in jl(F / "when2call/when2call_test_mcq.jsonl"):
        opts = [opt(t) for t in r["tools"]]
        if not opts or len(opts) > MAX_OPT:
            c[f"kizarva_{'0' if not opts else '>10'}_eszkoz"] += 1
            continue
        gold = json.loads(r["target_tool"])["name"] if r["correct_answer"] in ("tool_call", "request_for_info") else None
        if gold is not None and gold not in {o["id"] for o in opts}:
            c["kizarva_gold_nincs_a_listan"] += 1
            continue
        items.append({"id": f"w2c-{r['uuid']}", "forras": "w2c_teszt", "split": "teszt", "lang": "en", "request": r["question"],
                      "history": [], "options": opts, "gold": gold,
                      "meta": {"klaszter": r["source_id"], "w2c_valasz": r["correct_answer"], "n_tools": len(opts)}})
        c[r["correct_answer"]] += 1
    rep["w2c_teszt"] = dict(c)
    return items


CANNOT = re.compile(r"\b(unable|can't|cannot|don't have (the )?(capability|access|ability)|not able)\b", re.I)
ASK = re.compile(r"\b(could you|can you|please (provide|specify|tell)|i('ll| will)? need)\b", re.I)


def when2call_train(rep: dict) -> list[dict]:
    items, c = [], Counter()
    for k, r in enumerate(jl(F / "when2call/when2call_train_sft.jsonl")):
        opts = [opt(t) for t in r["tools"]]
        ans = r["messages"][-1]["content"].strip()
        if CANNOT.search(ans):
            kind = "cannot_answer"
        elif ans.endswith("?") or ASK.search(ans):
            kind = "request_for_info"
        else:
            c["kizarva_besorolatlan_valasz"] += 1
            continue
        if kind == "cannot_answer" and not opts:
            c["kizarva_0_eszkoz"] += 1
            continue
        if kind == "request_for_info" and len(opts) != 1:
            c["kizarva_visszakerdezes_tobb_eszkozzel"] += 1
            continue
        if len(opts) > MAX_OPT:
            c["kizarva_>10_eszkoz"] += 1
            continue
        gold = opts[0]["id"] if kind == "request_for_info" else None
        items.append({"id": f"w2ct-{k:05d}", "forras": "w2c_train", "split": "train", "lang": "en",
                      "request": r["messages"][0]["content"], "history": [], "options": opts, "gold": gold,
                      "meta": {"klaszter": f"w2ct-{k:05d}", "w2c_valasz": kind, "n_tools": len(opts)}})
        c[kind] += 1
    rep["w2c_train"] = dict(c)
    return items


def qkey(q: str) -> str:
    return re.sub(r"\W+", " ", q.lower()).strip()


def xlam(rep: dict) -> list[dict]:
    items, c = [], Counter()
    for r in json.load(open(F / "xlam/xlam_function_calling_60k.json")):
        opts = [opt(t) for t in json.loads(r["tools"])]
        called = {a["name"] for a in json.loads(r["answers"])}
        if len(called) != 1:
            c["kizarva_tobb_eszkozre_szolo_hivas"] += 1
            continue
        if len(opts) > MAX_OPT:
            c["kizarva_>10_eszkoz"] += 1
            continue
        gold = next(iter(called))
        if gold not in {o["id"] for o in opts}:
            c["kizarva_gold_nincs_a_listan"] += 1
            continue
        items.append({"id": f"xlam-{r['id']}", "forras": "xlam", "split": "train", "lang": "en", "request": r["query"],
                      "history": [], "options": opts, "gold": gold,
                      "meta": {"klaszter": f"q:{qkey(r['query'])}", "generator": "deepseek-v2" if r["id"] < 33659 else "mixtral-8x22b",
                               "n_tools": len(opts)}})
        c["item"] += 1
    rep["xlam"] = dict(c)
    return items


def xlam_irrel(rep: dict, xlam_keys: set[str]) -> list[dict]:
    items, c = [], Counter()
    for k, r in enumerate(json.load(open(F / "xlam_irrel/xlam-7.5k-irrelevancek.json"))):
        opts = [opt(t) for t in json.loads(r["tools"])]
        if not opts or len(opts) > MAX_OPT:
            c[f"kizarva_{'0' if not opts else '>10'}_eszkoz"] += 1
            continue
        key = f"q:{qkey(r['query'])}"
        items.append({"id": f"xlamir-{k:04d}", "forras": "xlam_irrel", "split": "train", "lang": "en", "request": r["query"],
                      "history": [], "options": opts, "gold": None, "meta": {"klaszter": key, "n_tools": len(opts)}})
        c["item"] += 1
        c["parja_az_xlam_itemek_kozt"] += key in xlam_keys
    rep["xlam_irrel"] = dict(c)
    return items


def massive(rep: dict) -> list[dict]:
    mp = json.loads((ROOT / "katalogus/massive_lekepezes.json").read_text())
    part = {"train": "train", "dev": "val", "test": "teszt"}
    items, c = [], Counter()
    for r in jl(F / "massive/1.1/data/hu-HU.jsonl"):
        m = mp[r["intent"]]
        items.append({"id": f"massive-hu-{r['id']}", "forras": "massive_hu", "split": part[r["partition"]], "lang": "hu",
                      "request": r["utt"], "gold_eszkoz": m["eszkoz"],
                      "meta": {"klaszter": f"massive-{r['id']}", "intent": r["intent"], "scenario": r["scenario"],
                               "felulvizsgal": m["felulvizsgal"]}})
        c[f"{part[r['partition']]}_{'X' if m['eszkoz'] is None else 'eszkoz'}"] += 1
        c[f"{part[r['partition']]}_felulvizsgalando"] += bool(m["felulvizsgal"])
    rep["massive_hu"] = dict(c)
    return items


def eu180k(rep: dict) -> list[dict]:
    rows = [json.loads(line) for line in open(F / "eu180k/eu-multilang-tool-calling-180k.jsonl") if '"language": "hu"' in line]
    groups = defaultdict(list)
    for r in rows:
        groups[json.dumps(r["conversation"], ensure_ascii=False, sort_keys=True)].append(r)
    called = Counter((c.get("function") or c)["name"] for r in rows for m in r["conversation"] for c in (m.get("tool_calls") or []))
    items, c = [], Counter()
    for k, (_, rs) in enumerate(sorted(groups.items())):
        r = rs[0]
        conv = r["conversation"]
        sysp = conv[0]["content"] if conv[0]["role"] == "system" else ""
        first_user = next(i for i, m in enumerate(conv) if m["role"] == "user")
        first_call = next((m for m in conv[first_user:] if m.get("tool_calls")), None)
        gold = (first_call["tool_calls"][0].get("function") or first_call["tool_calls"][0])["name"] if first_call else None
        tools = sorted({n for n in called if re.search(rf"(?<![\w]){re.escape(n)}(?![\w])", sysp)})
        flags = []
        if first_call and len(first_call["tool_calls"]) > 1:
            flags.append("parhuzamos_hivas")
        if gold and gold not in tools:
            flags.append("gold_nincs_a_system_promptban")
        if not tools:
            flags.append("eszkozlista_nem_nyerheto_ki")
        items.append({"id": f"eu180k-hu-{k:03d}", "forras": "eu180k_hu", "split": "train", "lang": "hu",
                      "request": conv[first_user]["content"], "history": [], "system_prompt": sysp,
                      "options_nevek": tools, "gold": gold,
                      "meta": {"klaszter": f"eu180k-{k:03d}", "ismetles": len(rs), **r["_axis_values"], "jelzok": flags}})
        c["egyedi"] += 1
        c["X" if gold is None else "eszkoz"] += 1
        for f in flags:
            c[f] += 1
    c["sorok_osszesen"] = len(rows)
    rep["eu180k_hu"] = dict(c)
    return items


def main() -> None:
    OUT.mkdir(exist_ok=True)
    rep = {}
    b, wt, wtr, ms, eu = bfcl(rep), when2call_test(rep), when2call_train(rep), massive(rep), eu180k(rep)
    xl = xlam(rep)
    xi = xlam_irrel(rep, {i["meta"]["klaszter"] for i in xl})
    write("xlam_train.jsonl", xl)
    write("xlam_irrel_train.jsonl", xi)
    # szivárgás (előzetes, név-szintű): BFCL-itemek, amelyek eszközneve a train-forrásokban is szerepel
    train_names = {o["id"] for i in xl + xi + wtr for o in i["options"]}
    hit = [i for i in b if any(o["id"] in train_names for o in i["options"])]
    rep["szivargas_nev_szinten"] = {"train_eszkoznevek": len(train_names), "bfcl_item_kozos_eszkoznevvel": len(hit),
                                   "bfcl_item_osszes": len(b)}
    for i in b:
        i["meta"]["train_eszkoznev_atfedes"] = any(o["id"] in train_names for o in i["options"])
    write("bfcl_teszt.jsonl", b)
    write("w2c_teszt.jsonl", wt)
    write("w2c_train.jsonl", wtr)
    write("massive_hu.jsonl", ms)
    write("eu180k_hu_egyedi.jsonl", eu)
    # átfedés: a When2Call-teszt forráskérdései a BFCL-live itemek közt
    bids = {i["meta"]["klaszter"] for i in b}
    rep["atfedes"] = {"w2c_teszt_klaszter_a_bfcl_ben": sum(i["meta"]["klaszter"] in bids for i in wt), "w2c_teszt_osszes": len(wt)}
    (OUT / "forras_riport.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1))
    print(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
