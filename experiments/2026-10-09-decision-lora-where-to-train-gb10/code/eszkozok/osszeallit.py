"""Szintetikus BA-adat — S7–S8 + a végső itemek (runbook 4.2–4.5).

- Opciólista: BM25 top-5 ∪ vektor top-5 (egyesítve, duplikátum nélkül). A gyűjtőcikkek
  a visszakeresésben helyet foglalnak (mint prodban), de az opciók közül kikerülnek;
  a lista a tartalék (6–8. rangú) jelöltekkel töltődik fel, így a listahossz nem
  árulkodik. Gyűjtőcikk soha nem gold: új termékre az X a helyes válasz.
- S7 „egyik sem” (~25% splitenként): X(b) = katalógusban nem szereplő cikk; X(a)
  természetes = a gold nincs a listán; X(a) kényszerített = a gold kiesik, a helyére a
  következő tartalék-jelölt kerül (azonos listahossz).
- S8 kétértelműség az attribútumokon: ha a sor a goldot (X-nél a valódi cikket) egy
  családtag-jelölttől nem különbözteti meg → „kétértelmű” (soft címke). Ha a sor a
  testvér értékét hordozza a gold helyett → „ellentmondó” generálási hiba → kiesik.
- Az opciók tárolt sorrendje seedelt keverés (a visszakeresési rang nem szivárog).
- S8 v2 (2026-10-05): kétértelmű a családon kívüli, csak méretben eltérő változat, ha a sor nem hordozza a valódi
  cikk méretét, és a semmitmondó sor (csak kód + márka; duplikatum.size_ambiguous / uninformative).
- Katalógus-duplikátumok (F1F, 2026-10-04; duplikatum_llm.py → dedup/duplikatumok.json, ha létezik): a valódi
  cikk duplikátuma soha nem opció — a gyűjtőcikkhez hasonlóan kikerül, a lista a tartalékkal töltődik fel —, és az
  értelmetlen nevű valódi cikk sorai kiesnek. Dani átnézésében a hibás címkék zöme ilyen duplikátum volt.

Futtatás: python3 eszkozok/osszeallit.py --out adat/pilot --seed 101
"""

from __future__ import annotations

import argparse
import json
import random
import re
import statistics
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from duplikatum import indistinguishable, size_ambiguous, uninformative  # noqa: E402
from common import EXP, MAX_OPTIONS, read_jsonl, write_json, write_jsonl  # noqa: E402

X_TARGET = 0.25
SPLITS = ["train", "val-belso", "val-szallito", "T-belso", "T-szallito", "T-kozeli", "T-tavoli"]


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace(",", ".")
    s = re.sub(r"(\d)\s+(?=[a-z%])", r"\1", s)  # "0.5 l" → "0.5l"
    return s


def present(value: str, text_n: str) -> bool:
    """Felismerhető-e az attribútum-érték a (normalizált) sorban — rövidítést is elfogadva."""
    v = norm(value)
    if not v.strip():
        return False
    if v in text_n:
        return True
    nums = re.findall(r"\d+(?:\.\d+)?", v)
    if nums:  # számos érték: minden szám szerepeljen önálló számként
        tn = set(re.findall(r"\d+(?:\.\d+)?", text_n))
        return all(n in tn or n.lstrip("0") in tn for n in nums)
    toks = re.findall(r"[a-z]{3,}", text_n)
    for w in re.findall(r"[a-z]{3,}", v):
        ok = False
        for t in toks:
            if w.startswith(t) or t.startswith(w[:4]):
                ok = True
            else:  # rövidítés: a token a szó betűinek részsorozata, azonos kezdőbetűvel
                it = iter(w)
                ok = t[0] == w[0] and len(t) >= 3 and all(c in it for c in t)
            if ok:
                break
        if not ok:
            return False
    return True


def distinguish(text: str, gold: dict, cand: dict) -> str:
    """'igen' — a sor megkülönbözteti a goldot a jelölttől; 'nem' — nem; 'ellentmond' — a jelöltre utal."""
    tn = norm(text)
    diff = [k for k in set(gold["attrs"]) | set(cand["attrs"]) if gold["attrs"].get(k) != cand["attrs"].get(k)]
    if not diff:
        return "nem"
    g_hits = [k for k in diff if gold["attrs"].get(k) and present(gold["attrs"][k], tn)]
    c_hits = [k for k in diff if cand["attrs"].get(k) and present(cand["attrs"][k], tn)]
    if any(k not in c_hits for k in g_hits):
        return "igen"
    if c_hits and not g_hits:
        return "ellentmond"
    # a különbség hiányzó attribútumban van (pl. a jelöltnek nincs márkája): a gold értéke dönt
    if any(gold["attrs"].get(k) and not cand["attrs"].get(k) and k in g_hits for k in diff):
        return "igen"
    return "nem"


def fmt_ft(x: float) -> str:
    return f"{x:,.0f}".replace(",", " ") if x >= 100 else f"{x:.2f}".replace(".", ",")


def fmt_qty(x: float) -> str:
    return str(int(x)) if float(x).is_integer() else f"{x:g}".replace(".", ",")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, required=True)
    args = ap.parse_args()
    out = Path(args.out)
    if not out.is_absolute():
        out = EXP / out
    rng = random.Random(args.seed + 7)
    arts = {a["id"]: a for a in read_jsonl(out / "s1_katalogus.jsonl")}
    sups = {s["id"]: s for s in json.load(open(out / "s2_szallitok.json"))}
    rows = {r["row"]: r for r in read_jsonl(out / "s4_sorok.jsonl")}
    cands = read_jsonl(out / "s6_jeloltek.jsonl")
    fam = defaultdict(list)
    for a in arts.values():
        fam[a["family"]].append(a["id"])
    dups, rossz_nev = defaultdict(set), set()
    dpath = out / "dedup" / "duplikatumok.json"
    if dpath.exists():
        dd = json.load(open(dpath))
        for a, b in dd["parok"]:
            dups[a].add(b)
            dups[b].add(a)
        rossz_nev = set(dd["ertelmetlen_nev"])

    stats = Counter()
    drafts = []
    for c in cands:
        r = rows[c["row"]]
        gold = r["article"]
        if gold in rossz_nev:
            stats["ertelmetlen_nev_kiesett"] += 1
            continue
        b_ids = [i for i, _ in c["bm25"]]
        v_ids = [i for i, _ in c["vector"]]
        merged = list(dict.fromkeys(b_ids[:5] + v_ids[:5]))
        reserve = [i for i in dict.fromkeys(b_ids[5:] + v_ids[5:]) if i not in merged]
        n_slots = len(merged)
        dup = dups.get(gold, set())
        n_dup = sum(i in dup for i in merged + reserve)
        if n_dup:
            stats["duplikatum_kizarva_item"] += 1
            stats["duplikatum_kizarva_opcio"] += n_dup
        # gyűjtő / duplikátum helyett tartalék → azonos listahossz. Legalább EGY tartalék minden itemnél marad: a
        # kényszerített X(a) a kiejtett gold helyére tartalékot tesz, és ha a duplikátum-kizárás kimeríti a
        # tartalékot, a rövid listák mind nem-X-ek maradnak → az opciószám elárulja az X-et (F1F első
        # shortcut-auditja: AUC 0,574, ebből az opciószám egyedül 0,573; 2026-10-04)
        avail = [i for i in merged + reserve if not arts[i]["catchall"] and i not in dup]
        n_eff = min(n_slots, MAX_OPTIONS, len(avail) - 1)
        opts, reserve = avail[:n_eff], avail[n_eff:]
        b_rank = b_ids.index(gold) + 1 if gold in b_ids else None
        v_rank = v_ids.index(gold) + 1 if gold in v_ids else None
        if r["xb"]:
            xf = "b"
        elif gold not in opts:
            xf = "a-termeszetes"
        else:
            xf = None
        drafts.append({"r": r, "opts": opts, "reserve": reserve, "x": xf, "b_rank": b_rank, "v_rank": v_rank,
                       "b_top1": b_ids[0] if b_ids else None,
                       "margin": (c["bm25"][0][1] - c["bm25"][1][1]) / c["bm25"][0][1] if len(c["bm25"]) > 1 and c["bm25"][0][1] > 0 else None})

    # S7: kényszerített X(a) splitenként ÉS metaadat-rétegenként a ~25%-os célig. A réteg a lista szórtsága és a
    # sor írásmódja: a természetes X(a) (visszakeresési hiba) a csupa nagybetűs, szórt listás soroknál sűrűsödik,
    # és a splitenkénti kényszerítéssel a metaadat elárulta az X-et (F1 shortcut-audit, CV AUC 0,584; 2026-10-04).
    # Az opciószám is réteg (F1F: a duplikátum-kizárás után a listahossz árulkodott).
    def stratum(d):
        paths = {arts[i]["path"] for i in d["opts"]}
        roots = {arts[i]["root"] for i in d["opts"]}
        return (d["r"]["text"].isupper(), min(len(paths), 5), min(len(roots), 3), len(d["opts"]))

    by_cell = defaultdict(list)
    for d in drafts:
        by_cell[(d["r"]["split"], stratum(d))].append(d)
    for (sp, _st), ds in sorted(by_cell.items(), key=lambda kv: str(kv[0])):
        need = round(X_TARGET * len(ds) - sum(d["x"] is not None for d in ds))
        if need < 0:
            stats[f"telitett_reteg_{sp}"] += 1
            stats[f"telitett_tobblet_{sp}"] += -need
        pool = [d for d in ds if d["x"] is None and d["reserve"]]
        rng.shuffle(pool)
        for d in pool[: max(0, need)]:
            d["opts"] = [i for i in d["opts"] if i != d["r"]["article"]] + [d["reserve"].pop(0)]
            d["x"] = "a"
        stats[f"x_hiany_{sp}"] += max(0, need - len(pool))

    items = defaultdict(list)
    for d in drafts:
        r, opts = d["r"], d["opts"]
        if len(opts) < 2:
            stats["kevés_opció"] += 1
            continue
        true_a = arts[r["article"]]
        sib = [arts[i] for i in opts if i != true_a["id"] and arts[i]["family"] == true_a["family"]]
        verdicts = {o["id"]: distinguish(r["text"], true_a, o) for o in sib}
        if "ellentmond" in verdicts.values() and d["x"] is None:
            stats["ellentmondo_kiesett"] += 1
            continue
        amb = [i for i, v in verdicts.items() if v != "igen"]
        # S8 kiterjesztés (2026-10-04): családon KÍVÜLI, azonos alkategóriájú, a sor alapján megkülönböztethetetlen
        # opció (szórend-/ragozás-duplikátum; a runbook S1-dedupja a generátorból kimaradt) — duplikatum.py
        dup = [i for i in opts if i != true_a["id"] and arts[i]["family"] != true_a["family"]
               and arts[i]["path"] == true_a["path"] and indistinguishable(r["text"], true_a["name"], arts[i]["name"])]
        if dup:
            stats["duplikatum_ketertelmu"] += 1
        amb += [i for i in dup if i not in amb]
        # S8 v2 (2026-10-05): családon kívüli méretváltozat méret nélküli sorral; semmitmondó sor (csak kód + márka)
        meret = [i for i in opts if i != true_a["id"] and arts[i]["family"] != true_a["family"]
                 and size_ambiguous(r["text"], true_a["name"], arts[i]["name"])]
        if meret:
            stats["meret_ketertelmu"] += 1
        amb += [i for i in meret if i not in amb]
        semmit = uninformative(r["text"], true_a["name"], true_a["attrs"].get("marka"))
        if semmit:  # bármelyik azonos alkategóriájú opció lehet a termék
            stats["semmitmondo_ketertelmu"] += 1
            amb += [i for i in opts if i != true_a["id"] and arts[i]["path"] == true_a["path"] and i not in amb]
        gold = None if d["x"] else true_a["id"]
        soft = None
        if amb or semmit:  # a soft céleloszlás tagjai; None = az X opció
            soft = [None if d["x"] else true_a["id"]] + amb
        order = list(opts)
        rng.shuffle(order)
        s = sups[r["supplier"]]
        items[r["split"]].append({
            "id": r["row"], "split": r["split"], "task": "ba_cikk",
            "context": {"sor": r["text"], "szallito": s["name"], "mennyiseg": fmt_qty(r["qty"]), "egyseg": r["unit"],
                        "egysegar": fmt_ft(r["unit_price"])},
            "options": [{"id": i, "text": arts[i]["name"], "path": arts[i]["path"]} for i in order],
            "gold": gold,
            "meta": {"article": true_a["id"], "supplier": s["id"], "family": true_a["family"], "root": true_a["root"],
                     "x_fajta": d["x"], "ketertelmu": bool(amb) or semmit, "soft": soft, "bm25_rank": d["b_rank"],
                     "vec_rank": d["v_rank"], "bm25_top1_gold": d["b_top1"] == true_a["id"], "bm25_margin": d["margin"],
                     "n_options": len(order), "value": round(r["qty"] * r["unit_price"], 2),
                     "siblings_in_list": len(sib), "duplikatum_opcio": len(dup), "meret_valtozat_opcio": len(meret),
                     "semmitmondo": semmit},
        })

    # a 00b kiegészítés (runbook 15. pont) új splitje is kiíródik; az F1 splitjei mindig (üresen is)
    splits = SPLITS + sorted(sp for sp in items if sp not in SPLITS)
    for sp in splits:
        write_jsonl(out / f"items_{sp}.jsonl", items.get(sp, []))

    def split_rep(its):
        if not its:
            return {}
        ne = [i for i in its if not i["meta"]["x_fajta"]]
        return {
            "n": len(its), "x_arany": round(1 - len(ne) / len(its), 3),
            "x_fajtak": dict(Counter(i["meta"]["x_fajta"] for i in its if i["meta"]["x_fajta"])),
            "ketertelmu_arany": round(sum(i["meta"]["ketertelmu"] for i in its) / len(its), 3),
            "bm25_top1_gold_arany_nem_x": round(sum(i["meta"]["bm25_top1_gold"] for i in ne) / max(1, len(ne)), 3),
            "testver_a_listan_arany_nem_x": round(sum(i["meta"]["siblings_in_list"] > 0 for i in ne) / max(1, len(ne)), 3),
            "bm25_margo_median": round(statistics.median([i["meta"]["bm25_margin"] for i in ne if i["meta"]["bm25_margin"] is not None] or [0]), 3),
            "opcioszam": dict(sorted(Counter(i["meta"]["n_options"] for i in its).items())),
            "opcioszam_x_vs_nem_x": [round(statistics.mean([i["meta"]["n_options"] for i in its if i["meta"]["x_fajta"]] or [0]), 2),
                                     round(statistics.mean([i["meta"]["n_options"] for i in ne] or [0]), 2)],
        }

    rep = {"seed": args.seed, "splitek": {sp: split_rep(items.get(sp, [])) for sp in splits}, "esemenyek": dict(stats)}
    write_json(out / "osszeallit_riport.json", rep)
    print(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
