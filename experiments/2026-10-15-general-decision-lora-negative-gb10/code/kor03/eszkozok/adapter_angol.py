"""03-as kör — az angol tipizált döntési gerinc a közös sémára (03-runbook 3.3, F0; arány: a train 25%-a, Dani,
2026-10-09).

Források (a letöltés már szűrt, ld. letolt03.PATTERNS):
  tasksource-jev-typed-decisions, `full`   a címke a forrásadatkészletből jön, determinisztikus átírással. A `default`
                                           keveréket Jev-ítéletek súlyozták, ezért nem azt használjuk; a `full`-ban a
                                           Jev csak a forrásonkénti sorplafont befolyásolta. Itt forrásonként legfeljebb
                                           TS_CAP sor, saját, hash-alapú mintavétellel.
  procedural-typed-decisions (9 feladat)   procedurálisan generált, a gold számolt. Feladatonként legfeljebb PROC_CAP
                                           állapot, állapotonként minden choice/noul kérdés.
  Open-Jev (7 kontroll-konfiguráció, CC0)  kontrollált szintetikus feladatok, referenciacímkével. Konfigurációnként
                                           legfeljebb OJ_CAP sor.

Szűrés (a kitartás-lista és a licenc, 5. és 9. pont):
  - kitartott csoportokkal rokon források (EXCLUDE): routing (intent, eszköz- és ügynökdöntés), termék (ESCI),
    KIE/validáció-rokon (számtan, matematika, időbeli következtetés, táblázat), eval-szivárgás (COPA/XCOPA: a HuCoPA
    forrása; WinoWhy: a HuWNLI forrása), zárt modell címkéje (UltraFeedback: GPT-4 pontozás; WildGuardMix: GPT-4
    címkék), nem angol (multilingual/*), és a tasksource-ba csomagolt procedural (azt külön, saját szűréssel vesszük);
  - csak `license_use == commercial`, és a sor minden licence a megengedő vagy SA körből (LICENSE_MAP); GPL, AGPL, MPL,
    ODbL, „Custom”, „other” és ismeretlen: kimarad. Több licencnél a legszigorúbb lesz a `source_license`;
  - csak choice és noul, 2–10 opció („none of the other options” → X, természetes; „all of the other options” →
    kimarad), legfeljebb 4000 karakteres állapot.

Puha forráscél (szavazatarány, valószínűség): kétértelmű item a `soft` eloszlással, nem pontozott (2. pont).
Split: train, és a group_id hash-e szerint 10% val; a teszt-ID-t az angol gerinc nem kap (a H4 a magyar rétegeken mér).

  kor01/.venv/bin/python kor03/eszkozok/adapter_angol.py   # → kor03/adat/f0/en.*.jsonl + adapter_angol_riport.json
"""

from __future__ import annotations

import ast
import glob
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kozos03 import MAX_OPTIONS, noul_options, validate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
HF = ROOT / "forras/hf"
OUT = ROOT / "adat/f0"
SEED = "20261009"
TS_CAP, PROC_CAP, OJ_CAP = 60, 400, 600
MAX_STATE = 4000

EXCLUDE = {
    "routing": r"clinc|banking77|massive|mtop|snips|intent|taxonomy_routing|it-support|agent_action|shell-safety|tool|function|api\b",
    "termek": r"esci|product|glami",
    "kie": r"arithmetic|record_aggregation|table_lookup|math|numer|equate|temporal|tracie|time-reasoning|counting|prm800k|webinstruct|autotnli",
    "eval-szivargas": r"copa|winowhy",
    "zart-modell-cimke": r"ultrafeedback|wildguard",
    "nem-angol": r"^multilingual/",
    "procedural-kulon": r"^procedural-typed-decisions/",
}

# tasksource-licencjelölés → (SPDX a LICENSES-ből, szigorúsági rang); ami nincs itt, az kizáró
LICENSE_MAP = {
    "cc0-1.0": ("CC0-1.0", 0), "cc0 1.0 (dpi)": ("CC0-1.0", 0),
    "apache-2.0": ("Apache-2.0", 1), "apache license 2.0 (dpi)": ("Apache-2.0", 1),
    "mit": ("MIT", 1), "mit license (dpi)": ("MIT", 1),
    "bsd": ("BSD-3-Clause", 2), "bsd 2-clause license (dpi)": ("BSD-2-Clause", 2),
    "odc-by": ("ODC-BY-1.0", 3), "cc-by-3.0": ("CC-BY-3.0", 3), "cc-by-4.0": ("CC-BY-4.0", 3),
    "cc by 4.0 (dpi)": ("CC-BY-4.0", 3),
    "cc-by-sa-3.0": ("CC-BY-SA-3.0", 4), "cc by-sa 3.0 (dpi)": ("CC-BY-SA-3.0", 4),
    "cc-by-sa-4.0": ("CC-BY-SA-4.0", 5), "cc by-sa 4.0 (dpi)": ("CC-BY-SA-4.0", 5),
}
NONE_OPT = re.compile(r"^none of the (other )?options\.?$", re.I)
ALL_OPT = re.compile(r"^all of the (other )?options\.?$", re.I)


def hkey(s: str) -> str:
    return hashlib.sha256(f"{SEED}:{s}".encode()).hexdigest()


def excluded(source: str) -> str | None:
    for why, rx in EXCLUDE.items():
        if re.search(rx, source, re.I):
            return why
    return None


def effective_license(lic: str) -> str | None:
    parts = [p.strip().lower() for p in (lic or "").split(",") if p.strip()]
    mapped = [LICENSE_MAP.get(p) for p in parts]
    if not parts or any(m is None for m in mapped):
        return None
    return max(mapped, key=lambda m: m[1])[0]


def split_of(gid: str) -> str:
    return "val" if int(hkey("split:" + gid)[:8], 16) % 100 < 10 else "train"


def item(family: str, source: str, lic: str, ref: str, gid: str, state: str, question: str, kind: str,
         texts: list[str], probs: list[float], none_idx: int | None = None) -> tuple[dict | None, str]:
    """Közös átalakító: choice (texts + probs) vagy noul (probs = [p_igen]). A none_idx opció X-re képződik le."""
    if len(state) > MAX_STATE:
        return None, "kimarad: hosszú állapot"
    base = {"id": f"{family}:{ref}", "family": family, "group": "angol_gerinc", "source": source,
            "source_license": lic, "source_ref": ref, "split": split_of(gid), "group_id": f"{family}:{gid}",
            "lang": "en", "kind": kind, "state": state, "question": question, "x_type": None, "ketertelmu": False,
            "soft": None, "meta": {}}
    if kind == "noul":
        p = probs[0]
        gold = "igen" if p >= 0.999 else "nem" if p <= 0.001 else None
        it = {**base, "options": noul_options("en"), "gold": gold}
        if gold is None:
            it |= {"gold": "igen" if p >= 0.5 else "nem", "ketertelmu": True, "soft": {"igen": p, "nem": 1 - p}}
        return it, "noul" + (" puha" if it["ketertelmu"] else "")
    x_mass = 0.0
    if none_idx is not None:
        x_mass = probs[none_idx]
        texts = [t for i, t in enumerate(texts) if i != none_idx]
        probs = [q for i, q in enumerate(probs) if i != none_idx]
    if not 2 <= len(texts) <= MAX_OPTIONS:
        return None, "kimarad: opciószám"
    opts = [{"id": f"o{i + 1}", "text": t} for i, t in enumerate(texts)]
    if x_mass >= 0.999:
        return {**base, "options": opts, "gold": None, "x_type": "natural"}, "choice X"
    s = sum(probs) + x_mass
    if s <= 0:
        return None, "kimarad: üres cél"
    dist = {o["id"]: q / s for o, q in zip(opts, probs)}
    top = max(dist, key=lambda k: dist[k])
    if dist[top] >= 0.999:
        return {**base, "options": opts, "gold": top}, "choice"
    soft = dist | ({"X": x_mass / s} if x_mass else {})
    return {**base, "options": opts, "gold": top, "ketertelmu": True, "soft": soft}, "choice puha"


# --- tasksource ------------------------------------------------------------------------------------------------------

def tasksource() -> tuple[list[dict], Counter, dict]:
    keep: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    why, src_why = Counter(), {}
    cols = ["state", "kind", "id", "options", "target", "question", "source", "split", "group_id", "license", "license_use"]
    for f in sorted(glob.glob(str(HF / "tasksource/tasksource-jev-typed-decisions/full/*.parquet"))):
        t = pq.read_table(f, columns=cols)
        mask = pc.and_(pc.and_(pc.equal(t["license_use"], "commercial"), pc.equal(t["split"], "train")),
                       pc.is_in(t["kind"], value_set=pa.array(["choice", "noul"])))
        for r in t.filter(mask).to_pylist():
            src = r["source"]
            ex = excluded(src)
            if ex:
                src_why[src] = ex
                continue
            k = hkey(r["id"])
            lst = keep[src]
            if len(lst) < TS_CAP * 3 or k < lst[-1][0]:
                lst.append((k, r))
                lst.sort(key=lambda x: x[0])
                del lst[TS_CAP * 3:]
    rows = []
    for src, lst in sorted(keep.items()):
        n = 0
        for _, r in lst:
            if n >= TS_CAP:
                break
            lic = effective_license(r["license"])
            if lic is None:
                why["kimarad: licenc"] += 1
                src_why.setdefault(src, "licenc")
                continue
            texts = list(r["options"] or [])
            if any(ALL_OPT.match(x.strip()) for x in texts):
                why["kimarad: all of the other options"] += 1
                continue
            none_idx = next((i for i, x in enumerate(texts) if NONE_OPT.match(x.strip())), None)
            fam = "en.ts." + re.sub(r"[^a-z0-9]+", "_", src.lower()).strip("_")
            it, w = item(fam, f"tasksource:{src}", lic, r["id"], r["group_id"] or r["id"], r["state"], r["question"],
                         r["kind"], texts, list(r["target"]), none_idx)
            why[w] += 1
            if it:
                it["meta"] = {"ts_source": src}
                rows.append(it)
                n += 1
    return rows, why, src_why


# --- procedural ------------------------------------------------------------------------------------------------------

def procedural() -> tuple[list[dict], Counter]:
    rows, why = [], Counter()
    for d in sorted(glob.glob(str(HF / "tasksource/procedural-typed-decisions/*/"))):
        task = Path(d).name
        recs = [r for f in sorted(glob.glob(f"{d}/train-*.parquet")) for r in pq.read_table(f).to_pylist()]
        recs.sort(key=lambda r: hkey(r["id"]))
        for r in recs[:PROC_CAP]:
            qs, ans = json.loads(r["questions"]), json.loads(r["answers"])
            for qn, q in qs.items():
                a = ans.get(qn) or {}
                if q["type"] == "noul":
                    it, w = item(f"en.proc.{task}", "procedural-typed-decisions", "Apache-2.0", f"{r['id']}:{qn}",
                                 r["id"], r["state"], q["instructions"], "noul", [], [float(a["noul"])])
                elif q["type"] == "choice":
                    keys = list(q["criteria"])
                    texts = [q["criteria"][k] for k in keys]
                    probs = [float(a["probabilities"].get(k, 0.0)) for k in keys]
                    none_idx = keys.index("none") if "none" in keys else None
                    it, w = item(f"en.proc.{task}", "procedural-typed-decisions", "Apache-2.0", f"{r['id']}:{qn}",
                                 r["id"], r["state"], q["instructions"], "choice", texts, probs, none_idx)
                else:
                    why["kimarad: score"] += 1
                    continue
                why[w] += 1
                if it:
                    it["meta"] = {"proc_level": r["level"]}
                    rows.append(it)
    return rows, why


# --- Open-Jev --------------------------------------------------------------------------------------------------------

def open_jev() -> tuple[list[dict], Counter]:
    rows, why = [], Counter()
    for d in sorted(glob.glob(str(HF / "ZefanCai/Open-Jev/data/*/"))):
        cfg = Path(d).name
        recs = [r for f in sorted(glob.glob(f"{d}/train-*.parquet"))
                for r in pq.read_table(f, columns=["id", "group_id", "kind", "question", "options", "target",
                                                   "state_json"]).to_pylist()]
        recs.sort(key=lambda r: hkey(r["id"]))
        n = 0
        for r in recs:
            if n >= OJ_CAP:
                break
            if r["kind"] not in ("choice", "noul"):
                why["kimarad: " + r["kind"]] += 1
                continue
            st = json.loads(r["state_json"])
            state = st if isinstance(st, str) else json.dumps(st, ensure_ascii=False, indent=1)
            texts = ast.literal_eval(r["options"]) if isinstance(r["options"], str) else list(r["options"])
            probs = ast.literal_eval(r["target"]) if isinstance(r["target"], str) else list(r["target"])
            fam = "en.oj." + cfg.removesuffix("-v1").replace("-", "_")
            if r["kind"] == "noul":
                if [t.lower() for t in texts] != ["no", "yes"]:
                    why["kimarad: noul ismeretlen opciókkal"] += 1
                    continue
                it, w = item(fam, "Open-Jev", "CC0-1.0", r["id"], r["group_id"], state, r["question"], "noul", [],
                             [float(probs[1])])
            else:
                it, w = item(fam, "Open-Jev", "CC0-1.0", r["id"], r["group_id"], state, r["question"], "choice",
                             texts, [float(x) for x in probs])
            why[w] += 1
            if it:
                rows.append(it)
                n += 1
    return rows, why


def report(rows: list[dict], why: Counter) -> dict:
    return {"n": len(rows), "csalad": len({r["family"] for r in rows}), "ok": dict(why),
            "split": dict(Counter(r["split"] for r in rows)), "kind": dict(Counter(r["kind"] for r in rows)),
            "puha": sum(r["ketertelmu"] for r in rows), "x_arany": sum(r["gold"] is None for r in rows) / max(1, len(rows)),
            "licenc": dict(Counter(r["source_license"] for r in rows))}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rep = {}
    ts_rows, ts_why, src_why = tasksource()
    for name, (rows, why) in (("en.tasksource", (ts_rows, ts_why)), ("en.procedural", procedural()),
                              ("en.openjev", open_jev())):
        bad = [(r["id"], e) for r in rows if (e := validate(r))]
        if bad:
            raise SystemExit(f"{name}: {len(bad)} sémahiba, pl. {bad[:3]}")
        dup = Counter(r["id"] for r in rows).most_common(1)
        if dup and dup[0][1] > 1:
            raise SystemExit(f"{name}: ismétlődő id {dup}")
        (OUT / f"{name}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                                           encoding="utf-8")
        rep[name] = report(rows, why)
        print(name, json.dumps(rep[name], ensure_ascii=False)[:700])
    rep["kitartas_lista"] = {"szabaly": EXCLUDE, "kizart_forrasok": dict(sorted(src_why.items()))}
    print("kizárt tasksource-források:", Counter(src_why.values()))
    (OUT / "adapter_angol_riport.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
