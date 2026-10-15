"""03-as kör — az F4 technikai lezárása (03-runbook 7., v1: „Az F4 technikai lezárása”; Dani, 2026-10-14).

Minden, az elemzéshez szükséges kiolvasáson az elvárt (item_id, perm) párok pontos egyezése: hiány, ismétlődés és
érvénytelen sor nélkül (a puszta sorszám nem elég). Érvénytelen a sor, ha
  - a címkék / opció-sorrend nem az itemből és a permutációból számolt (`common.permutation`, `labels_for`);
  - a valószínűségek nem pontosan a jelen lévő címkékre szólnak, nem végesek, vagy az összegük nem 1;
  - hiányzó címke van (`missing`), a címketömeg nem véges pozitív szám, a `pred` nem címke;
  - a modell neve nem a karé (az adapter vagy a bázis).
A lepecsételt F4-fájloknál a `PECSET.sha256` útvonalankénti utolsó hash-e a jelenlegi fájlé, a korábbi hash-ek pedig a
fájl egy-egy sor-előtagjáé (append-only: az eredeti sorok érintetlenek, a pótlás csak hozzáfűzött). Az előtag
utáni sorok a pótoltak: `potolt_parok.jsonl` (kar, id, perm). A pótlás futásazonosítója az `olvas.log` jelölőjéből.

Eredményt nem ír ki és nem összegez: csak kulcsokat, sorszámot, érvényességet, hash-t, és a címketömeg technikai
mediánját / minimumát (a smoke-próbák épségmutatója).

  python3 kor03/eszkozok/f4_teljesseg03.py [--karok a,b]   → eredmenyek/F4/teljesseg.json, potolt_parok.jsonl,
      V1-MANIFEST-kiolvasasok.sha256; kilépési kód 1, ha bármely kar nincs rendben
Csak standard könyvtár (a Spark gazdagépén is fut).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[0]
EXP = HERE.parents[1]
sys.path.insert(0, str(EXP / "eszkozok"))
from common import labels_for, permutation  # noqa: E402

F4R = ROOT / "eredmenyek/F4"
BASE = "Qwen/Qwen3.6-35B-A3B-FP8"
P4 = (0, 1, 2, 3)
I03 = {"eval": "kor03/adat/f2/items_eval.jsonl", "val": "kor03/adat/f2/items_val.jsonl",
       "termek": "kor03/adat/f4/items_ho_termek.jsonl", "routing": "kor03/adat/f4/items_ho_routing.jsonl"}
G3K = ["k03v2_g3_s1", "k03v2_g3_s2", "k03v2_g3_s3", "k03v2_g3kemeny_s1", "k03v2_g3hu_s1"]


def karok() -> list[dict]:
    """név, kiolvasás, itemek, permutációk, elvárt modellnév, lepecsételt-e, többlet-id megengedett-e."""
    k = []
    for a in G3K:
        k.append({"nev": f"F4:{a}", "kar": a, "ut": f"kor03/eredmenyek/F4/{a}/vllm_eval.jsonl", "items": I03["eval"], "perms": P4,
                  "model": a, "pecset": True})
    k.append({"nev": "F4:l0r", "kar": "l0r", "ut": "kor03/eredmenyek/F4/l0r/vllm_eval.jsonl", "items": I03["eval"], "perms": P4,
              "model": BASE, "pecset": True})
    for n in (1, 2, 3):
        k.append({"nev": f"F4:l3mixse_h2_s{n}", "kar": f"l3mixse_h2_s{n}", "ut": f"kor03/eredmenyek/F4/l3mixse_h2_s{n}/vllm_eval.jsonl",
                  "items": I03["termek"], "perms": P4, "model": f"l3mixse_h2_s{n}", "pecset": True})
        k.append({"nev": f"F4:k01_l3mixse_p30_s{n}", "kar": f"k01_l3mixse_p30_s{n}",
                  "ut": f"kor03/eredmenyek/F4/k01_l3mixse_p30_s{n}/vllm_eval.jsonl", "items": I03["routing"], "perms": P4,
                  "model": f"k01_l3mixse_p30_s{n}", "pecset": True})
    # a nem lepecsételt, de az elemzéshez szükséges kiolvasások (val, L1★ eval, az L3-spec saját val-ja)
    k.append({"nev": "F2:L1★ eval", "kar": "L1", "ut": "kor03/eredmenyek/F2/qwen_eval.jsonl", "items": I03["eval"], "perms": P4,
              "model": BASE, "tobblet_ok": True})
    k.append({"nev": "F2:L1★ val", "kar": "L1", "ut": "kor03/eredmenyek/F2/qwen_val.jsonl", "items": I03["val"], "perms": P4,
              "model": BASE, "tobblet_ok": True})
    for a in G3K:
        k.append({"nev": f"F3:{a} val", "kar": a, "ut": f"kor03/eredmenyek/F3/{a}/vllm_val.jsonl", "items": I03["val"], "perms": P4,
                  "model": a})
    for n in (1, 2, 3):
        k.append({"nev": f"00:l3_s{n} val", "kar": f"l3mixse_h2_s{n}", "ut": f"eredmenyek/F4/vllm/l3_s{n}_val.jsonl",
                  "items": ["adat/f1/items_val-belso.jsonl", "adat/f1/items_val-szallito.jsonl"], "perms": P4, "regi": True,
                  "model": f"l3mixse_h2_s{n}"})
        k.append({"nev": f"01:l3_s{n} val", "kar": f"k01_l3mixse_p30_s{n}", "ut": f"kor01/eredmenyek/F4/vllm/l3_s{n}_val.jsonl",
                  "items": ["kor01/adat/items_val.jsonl"], "perms": P4 if n == 1 else (0,), "regi": True,
                  "model": f"k01_l3mixse_p30_s{n}"})
    return k


def load_items(paths) -> dict[str, dict]:
    out = {}
    for p in [paths] if isinstance(paths, str) else paths:
        with open(EXP / p, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    it = json.loads(line)
                    out[it["id"]] = it
    return out


PILLANATKEP = ROOT / "rogzites/v1/PECSET-pillanatkep.sha256"


def pecset_pillanatkep() -> bool | None:
    """Az élő PECSET a rögzítéskori pillanatképpel kezdődik-e (append-only); None, ha nincs pillanatkép."""
    if not PILLANATKEP.exists():
        return None
    return (F4R / "PECSET.sha256").read_bytes().startswith(PILLANATKEP.read_bytes())


def pecset() -> dict[str, list[str]]:
    by = defaultdict(list)
    p = F4R / "PECSET.sha256"
    if p.exists():
        for line in p.read_text().splitlines():
            if line.strip():
                h, path = line.split(None, 1)
                by[path.strip()].append(h)
    return by


def prefix_lines(path: Path, hashes: list[str]) -> dict[str, int | None]:
    """Melyik korábbi hash melyik sor-előtagé (sorok száma); None, ha egyiké sem."""
    want = set(hashes)
    found: dict[str, int | None] = {h: None for h in hashes}
    h = hashlib.sha256()
    if hashlib.sha256(b"").hexdigest() in want:
        found[hashlib.sha256(b"").hexdigest()] = 0
    with open(path, "rb") as fh:
        for n, line in enumerate(fh, 1):
            h.update(line)
            d = h.copy().hexdigest()
            if d in want and found[d] is None:
                found[d] = n
    return found


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def finite(x) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(x)


def row_problem(r: dict, it: dict, k: dict) -> str | None:
    order = permutation(it, r["perm"])
    if r.get("order") != order:
        return "opció-sorrend"
    labs = labels_for(order)
    if r.get("labels") != labs:
        return "címkék"
    if k.get("model") and r.get("model") != k["model"]:
        return "modellnév"
    if k.get("regi"):
        lp = r.get("label_logprobs") or {}
        if set(lp) != set(labs):
            return "címke-logprob kulcsok"
        if not all(finite(v) and v > -9999.0 for v in lp.values()):
            return "nem véges / hiányzó logprob"
        return None
    pr = r.get("probs") or {}
    if set(pr) != set(labs):
        return "valószínűség-kulcsok"
    if not all(finite(v) and v >= 0 for v in pr.values()) or abs(sum(pr.values()) - 1) > 1e-6:
        return "valószínűség-értékek"
    if r.get("missing"):
        return "hiányzó címke"
    if not (finite(r.get("label_mass")) and r["label_mass"] > 0):
        return "címketömeg"
    if r.get("pred") not in labs or not finite(r.get("conf")):
        return "pred/conf"
    return None


def check(k: dict, items: dict, seals: dict) -> tuple[dict, list[dict]]:
    path = EXP / k["ut"]
    res: dict = {"ut": k["ut"], "items": k["items"], "perms": list(k["perms"])}
    if not path.exists():
        return res | {"rendben": False, "hiba": "nincs ilyen fájl"}, []
    expected = {(i, p) for i in items for p in k["perms"]}
    seen = Counter()
    bad = Counter()
    extra = 0
    masses = []
    models, frames = Counter(), Counter()
    order_rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            r = json.loads(line)
            key = (r["id"], r["perm"])
            order_rows.append(key)
            if r["id"] not in items:
                extra += 1
                continue
            if key not in expected:
                bad["váratlan permutáció"] += 1
                continue
            seen[key] += 1
            prob = row_problem(r, items[r["id"]], k)
            if prob:
                bad[prob] += 1
            if not k.get("regi"):
                masses.append(r.get("label_mass", float("nan")))
                models[r.get("model")] += 1
                frames[r.get("frame")] += 1
    missing = expected - set(seen)
    dup = sum(c - 1 for c in seen.values() if c > 1)
    res |= {"elvart_par": len(expected), "jelen": len(seen), "hianyzik": len(missing), "ismetlodo": dup,
            "ervenytelen": dict(bad), "tobblet_sor_kikerult_itemre": extra,
            "pelda_hianyzo": sorted(missing)[:5]}
    if masses:
        ms = sorted(m for m in masses if finite(m))
        res["cimketomeg_median_min"] = [ms[len(ms) // 2], ms[0]] if ms else None
        res["cimketomeg_05_alatt"] = sum(m < 0.5 for m in ms)
        res["modellnev"] = dict(models)
        res["keret"] = dict(frames)
    hib = path.with_suffix(".hibak.jsonl")
    hib_parok = set()
    if hib.exists():
        with open(hib, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    e = json.loads(line)
                    hib_parok.add((e["id"], e["perm"]))
    res["hibanaplo_sorok"] = sum(1 for _ in open(hib, encoding="utf-8")) if hib.exists() else 0
    res["hibanaplo_parok"] = len(hib_parok)
    res["sha256"] = sha256(path)
    ok = bool(not missing and dup == 0 and not bad and (extra == 0 or k.get("tobblet_ok")))
    potolt: list[dict] = []
    if k.get("pecset"):
        hs = seals.get(k["ut"], [])
        res["pecset_hashek"] = len(hs)
        res["pecset_utolso_egyezik"] = bool(hs) and hs[-1] == res["sha256"]
        ok &= res["pecset_utolso_egyezik"]
        if hib_parok and len(hs) < 2:
            res["hiba_pecset"] = "a hibanapló nem üres, de nincs pótlás-pecsét"
            ok = False
        if len(hs) > 1:
            pre = prefix_lines(path, hs[:-1])
            res["pecset_elotagok"] = pre
            ok &= all(v is not None for v in pre.values())
            first = pre[hs[0]]
            if first is not None:
                potolt = [{"kar": k["kar"], "id": i, "perm": p} for i, p in order_rows[first:]]
                res["eredeti_sorok"] = first
                res["potolt_sorok"] = len(potolt)
                res["potolt_itemek"] = len({x["id"] for x in potolt})
                res["potolt_egyezik_a_hibanaploval"] = {(x["id"], x["perm"]) for x in potolt} == hib_parok
                ok &= res["potolt_egyezik_a_hibanaploval"]
        log = path.parent / "olvas.log"
        if log.exists():
            res["potlas_futasazonosito"] = [f"K03F4-potlas {ln[len('--- pótlás '):].strip()} ({k['kar']}, vLLM-napló: "
                                            f"{k['ut'].rsplit('/', 1)[0]}/potlas)"
                                            for ln in log.read_text(encoding="utf-8").splitlines() if ln.startswith("--- pótlás ")]
    res["rendben"] = bool(ok)
    return res, potolt


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--karok", default="", help="vesszővel elválasztott kar-nevek (alap: mind)")
    ap.add_argument("--out", default=str(F4R))
    a = ap.parse_args()
    if a.karok and Path(a.out).resolve() == F4R.resolve():
        raise SystemExit("részfuttatás (--karok) csak külön --out könyvtárba írhat")
    seals = pecset()
    cache: dict = {}
    out: dict = {"karok": {}}
    potolt: list[dict] = []
    want = set(a.karok.split(",")) if a.karok else None
    for k in karok():
        if want and k["nev"] not in want:
            continue
        key = json.dumps(k["items"])
        if key not in cache:
            cache = {key: load_items(k["items"])}  # egyszerre egy itemkészlet a memóriában
        res, pot = check(k, cache[key], seals)
        out["karok"][k["nev"]] = res
        potolt += pot
        print(f"{k['nev']:28s} {'rendben' if res['rendben'] else 'HIBÁS'}  "
              f"hiányzik {res.get('hianyzik')}, ismétlődő {res.get('ismetlodo')}, érvénytelen {sum(res.get('ervenytelen', {}).values())}"
              + (f", pótolt {res['potolt_sorok']}" if "potolt_sorok" in res else ""), flush=True)
    out["pecset_pillanatkep_egyezik"] = pecset_pillanatkep()
    out["rendben"] = (all(v["rendben"] for v in out["karok"].values()) and not want
                      and out["pecset_pillanatkep_egyezik"] is True)
    od = Path(a.out)
    od.mkdir(parents=True, exist_ok=True)
    (od / "teljesseg.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(od / "potolt_parok.jsonl", "w", encoding="utf-8") as fh:
        for p in potolt:
            fh.write(json.dumps(p, ensure_ascii=False) + "\n")
    with open(od / "V1-MANIFEST-kiolvasasok.sha256", "w", encoding="utf-8") as fh:
        for v in out["karok"].values():
            if "sha256" in v:
                fh.write(f"{v['sha256']}  {v['ut']}\n")
    print("ÖSSZESEN:", "rendben" if out["rendben"] else "NINCS RENDBEN")
    sys.exit(0 if out["rendben"] else 1)


if __name__ == "__main__":
    main()
