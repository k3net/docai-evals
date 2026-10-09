"""Címke-átnézés (runbook 4.8): triage a bírálók alapján → Dani mintája → vak átnéző felület
→ összesítés (torzítatlan zajbecslés) → javítások. A bírálói kimenet SOHA nem címke.

  minta     — flag: legalább egy bíráló ≥ FLAG_CONF bizalommal mást választ, mint a gold, VAGY
              minden bíráló mást választ. Minta: (a) a flaggelt itemek rétegenként legfeljebb
              CAP-ig, (b) egyenletes véletlen minta a nem flaggeltekből (rétegezve: réteg × X/nem-X).
              Minden itemhez rögzül a bekerülési valószínűség.
  html      — önálló, offline átnéző felület (localStorage + JSON-export); a gold és a bírálói
              szavazat rejtve, a sorrend kevert, a minta eredete nem látszik.
  osszesit  — Dani döntéseiből: rétegenként flag-arány, megerősített hibaarány a flaggelt és a
              véletlen poolban, Horvitz–Thompson-becslés a teljes és a javítás utáni (reziduális)
              zajra, Clopper–Pearson CI-vel; javított item-fájlok + javítási napló.

Példa:
  python3 eszkozok/atnezes.py minta --gen adat/f1 --biralo eredmenyek/F1/biralo --out adat/f1/atnezes
  python3 eszkozok/atnezes.py html --out adat/f1/atnezes
  python3 eszkozok/atnezes.py osszesit --out adat/f1/atnezes --dontesek adat/f1/atnezes/dontesek.json
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import EXP, gold_label, labels_for, permutation, read_jsonl, write_json, write_jsonl  # noqa: E402

FLAG_CONF = 0.8
# Kétszintű triage (user-döntés, 2026-10-04): a bírálók erős A-torzítása és X-vaksága miatt a sima flag
# főleg bírálói hibát jelöl.
#   1. szint („konszenzus”): minden bíráló UGYANAZT a nem-gold címkét adja, mind ≥ FLAG_CONF-fal; rétegenként CAP_KONSZ.
#   2. szint („többi”): minden más item EGY arányos véletlen mintából (réteg × X/nem-X), N_TOBBI összesen. A flaggelt
#      és a nem flaggelt itemek így azonos valószínűséggel kerülnek be, és a zajbecslés ~240 itemre támaszkodik —
#      külön kvótákkal egy ~1150-es flag-cellából csak ~60 item jutott volna, és a 2%-os kapu hibátlan átnézéssel
#      sem lett volna elérhető (szimulálva: felső95 4,25%).
CAP_KONSZ = 40
N_TOBBI = 240
STRATA = ["val-belso", "val-szallito", "T-belso", "T-szallito", "T-kozeli", "T-tavoli"]


def _p(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else EXP / p


def cp_interval(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    from scipy.stats import beta

    if n == 0:
        return (0.0, 1.0)
    lo = beta.ppf(alpha / 2, k, n - k + 1) if k > 0 else 0.0
    hi = beta.ppf(1 - alpha / 2, k + 1, n - k) if k < n else 1.0
    return (float(lo), float(hi))


CELLS = ["konszenzus", "tobbi_x", "tobbi_nemx"]


def cell(e: dict) -> str:
    """A becslés cellája (a minta is így rétegzett): a konszenzusos szint, és a többi X / nem-X szerint."""
    return "konszenzus" if e["tier"] == "konszenzus" else ("tobbi_x" if e["x"] else "tobbi_nemx")


def build_pool(gen: Path, biralo: Path) -> list[dict]:
    """A pontozott (nem kétértelmű) val/teszt itemek a szintjükkel és X/nem-X jelölésükkel (cmd_minta, cmd_szukit)."""
    reviews = defaultdict(dict)  # item_id -> {model: row}
    for f in glob.glob(str(biralo / "*.jsonl")):
        for r in read_jsonl(Path(f)):
            reviews[r["id"]][r.get("model", Path(f).stem)] = r
    pool = []
    for sp in STRATA:
        for it in read_jsonl(gen / f"items_{sp}.jsonl"):
            if it["meta"].get("ketertelmu"):
                continue  # a kétértelmű réteg nem pontozott → a zajbecslés a pontozott itemekre szól
            order = permutation(it, 0)
            g = gold_label(it, order)
            rv = reviews.get(it["id"], {})
            votes = {m: (r.get("pred"), r.get("conf")) for m, r in rv.items()}
            answered = [(p, c) for p, c in votes.values() if p]
            flag = bool(answered) and (any(p != g and (c or 0) >= FLAG_CONF for p, c in answered)
                                       or all(p != g for p, _ in answered))
            konsz = (len(answered) >= 2 and len({p for p, _ in answered}) == 1 and answered[0][0] != g
                     and all((c or 0) >= FLAG_CONF for _, c in answered))
            tier = "konszenzus" if konsz else "tobbi"
            pool.append({"item": it, "gold_label": g, "flag": flag, "tier": tier, "votes": votes, "stratum": sp,
                         "x": it["gold"] is None})
    return pool


def pool_counts(pool: list[dict]) -> dict:
    return {sp: {"n": sum(e["stratum"] == sp for e in pool),
                 **{c: sum(e["stratum"] == sp and cell(e) == c for e in pool) for c in CELLS}} for sp in STRATA}


def cmd_minta(args) -> None:
    gen = _p(args.gen)
    out = _p(args.out)
    rng = random.Random(args.seed)
    arts = {a["id"]: a for a in read_jsonl(gen / "s1_katalogus.jsonl")}
    rows = {r["row"]: r for r in read_jsonl(gen / "s4_sorok.jsonl")}
    pool = build_pool(gen, _p(args.biralo))
    sample, incl = [], {}
    # (a) 1. szint: konszenzusos magabiztos ellentmondás, rétegenként CAP_KONSZ-ig
    for sp in STRATA:
        es = [e for e in pool if e["stratum"] == sp and e["tier"] == "konszenzus"]
        rng.shuffle(es)
        take = es[:CAP_KONSZ]
        for e in take:
            incl[e["item"]["id"]] = len(take) / len(es)
        sample += take
    # (b) 2. szint: a többi itemből egy arányos véletlen minta, réteg × X/nem-X cellánként
    rest = [e for e in pool if e["tier"] == "tobbi"]
    cells = defaultdict(list)
    for e in rest:
        cells[(e["stratum"], e["x"])].append(e)
    for _key, es in sorted(cells.items(), key=lambda kv: str(kv[0])):
        k = max(2, round(N_TOBBI * len(es) / max(1, len(rest))))
        rng.shuffle(es)
        for e in es[:k]:
            incl[e["item"]["id"]] = min(k, len(es)) / len(es)
        sample += es[:k]
    rng.shuffle(sample)
    records = [make_record(e, arts, rows, incl[e["item"]["id"]]) for e in sample]
    counts = pool_counts(pool)
    write_json(out / "minta.json", {"records": records, "pool_counts": counts, "flag_conf": FLAG_CONF, "cap_konsz": CAP_KONSZ,
                                    "n_tobbi": N_TOBBI, "seed": args.seed,
                                    "populacio": "a pontozott (nem kétértelmű) val/teszt itemek"})
    print(json.dumps({"minta": len(records), "szintek": {t: sum(r["tier"] == t for r in records) for t in ("konszenzus", "tobbi")},
                      "tobbi_flaggelt": sum(r["tier"] == "tobbi" and r["flag"] for r in records),
                      "pool": counts}, ensure_ascii=False))


def make_record(e: dict, arts: dict, rows: dict, incl: float, adag: int = 1) -> dict:
    it = e["item"]
    r = rows.get(it["id"], {})
    a = arts.get(it["meta"]["article"], {})
    return {
        "id": it["id"], "stratum": e["stratum"], "flag": e["flag"], "tier": e["tier"], "x": e["x"], "incl_prob": incl,
        "votes": e["votes"], "gold_label": e["gold_label"], "item": it, "adag": adag,
        "nyom": {"valodi_cikk": a.get("name"), "attrs": a.get("attrs"), "szallitoi_megnevezes": r.get("base_name"),
                 "x_fajta": it["meta"].get("x_fajta"), "ketertelmu_szabaly": it["meta"].get("ketertelmu")},
    }


def cmd_potadag(args) -> None:
    """Pótadag a „többi” szintből (2026-10-05): a mintában még nem szereplő itemekből egy újabb arányos véletlen minta
    (réteg × X/nem-X), a minta.json-hoz fűzve `adag` sorszámmal. Két egyenletes, visszatevés nélküli húzás uniója a
    cellán belül továbbra is egyenletes, így a becslő változatlan. Célja a megerősítés: a kétértelműség-szabályokat
    (S8 v2–v3) a korábbi adag itemjeiből terveztük, az új itemek erre nézve torzítatlanok."""
    gen, out = _p(args.gen), _p(args.out)
    m = json.load(open(out / "minta.json"))
    adag = max(r.get("adag", 1) for r in m["records"]) + 1
    rng = random.Random(args.seed + 1000 * adag)
    arts = {a["id"]: a for a in read_jsonl(gen / "s1_katalogus.jsonl")}
    rows = {r["row"]: r for r in read_jsonl(gen / "s4_sorok.jsonl")}
    have = {r["id"] for r in m["records"]}
    tobbi = [e for e in build_pool(gen, _p(args.biralo)) if e["tier"] == "tobbi"]
    cells = defaultdict(list)
    for e in tobbi:
        cells[(e["stratum"], e["x"])].append(e)
    new = []
    for _key, es in sorted(cells.items(), key=lambda kv: str(kv[0])):
        k = max(1, round(args.n * len(es) / len(tobbi)))
        free = [e for e in es if e["item"]["id"] not in have]
        rng.shuffle(free)
        new += free[:k]
    rng.shuffle(new)
    recs = [make_record(e, arts, rows, None, adag) for e in new]
    m["records"] += recs
    m.setdefault("potadagok", []).append({"adag": adag, "n": len(recs), "seed": args.seed + 1000 * adag})
    write_json(out / "minta.json", m)
    print(json.dumps({"adag": adag, "uj": len(recs), "teszt": sum(r["stratum"].startswith("T-") for r in recs),
                      "minta_osszes": len(m["records"])}, ensure_ascii=False))


def cmd_szukit(args) -> None:
    """A minta szűkítése egy csak a kétértelmű-jelölést változtató újragenerálás után (2026-10-05, S8 v2): az újonnan
    kétértelmű itemek kikerülnek a populációból ÉS a mintából. A szűkítés az item tartalmának determinisztikus
    függvénye, mintabeli és mintán kívüli itemre egyformán hat, ezért a megmaradt minta cellánként továbbra is
    egyenletes véletlen minta. Ellenőrzi, hogy a megmaradt itemek kontextusa, opciói és goldja változatlan; a régi
    minta minta_<címke>.json néven megmarad."""
    gen, out = _p(args.gen), _p(args.out)
    m = json.load(open(out / "minta.json"))
    pool = {e["item"]["id"]: e for e in build_pool(gen, _p(args.biralo))}
    keep, dropped = [], []
    for r in m["records"]:
        e = pool.get(r["id"])
        if e is None:
            dropped.append(r["id"])
            continue
        it, oi = e["item"], r["item"]
        if (it["context"], it["options"], it["gold"]) != (oi["context"], oi["options"], oi["gold"]) or e["tier"] != r["tier"]:
            raise SystemExit(f"{r['id']}: a tartalom vagy a szint megváltozott — a minta nem szűkíthető, újra kell húzni")
        keep.append({**r, "item": it})
    write_json(out / f"minta_{args.cimke}.json", m)
    m2 = {**m, "records": keep, "pool_counts": pool_counts(list(pool.values())),
          "szukites": {"cimke": args.cimke, "kiesett": dropped, "maradt": len(keep)}}
    write_json(out / "minta.json", m2)
    print(json.dumps({"maradt": len(keep), "kiesett": dropped}, ensure_ascii=False))


HTML = """<!doctype html><html lang="hu"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Címke-átnézés</title>
<style>
:root{--bg:#f7f7f5;--fg:#1d1d1b;--mut:#6b6b66;--card:#fff;--bd:#dcdcd6;--acc:#2f5bd3;--ok:#1f7a3f;--warn:#a6461b}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#161615;--fg:#ececea;--mut:#9a9a94;--card:#21211f;--bd:#3a3a36;--acc:#7c9cff;--ok:#5cc184;--warn:#f0956a}}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.45 system-ui,sans-serif}
main{max-width:860px;margin:0 auto;padding:16px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:16px;margin:12px 0}
.mut{color:var(--mut);font-size:14px}.sor{font:600 18px/1.4 ui-monospace,monospace;word-break:break-word}
button{font:inherit;padding:8px 12px;margin:4px 6px 4px 0;border:1px solid var(--bd);border-radius:8px;background:var(--card);color:var(--fg);cursor:pointer;text-align:left}
button:hover{border-color:var(--acc)}.opt{display:block;width:100%}.bar{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.rev{border-left:4px solid var(--warn);padding-left:12px}.prog{height:6px;background:var(--bd);border-radius:3px}.prog>div{height:6px;background:var(--acc);border-radius:3px}
kbd{border:1px solid var(--bd);border-radius:4px;padding:0 4px;font-size:13px}
</style></head><body><main>
<h1 style="font-size:20px">Címke-átnézés <span class="mut" id="cnt"></span></h1>
<div class="prog"><div id="pb" style="width:0"></div></div>
<p class="mut">Válaszd ki, melyik cikkhez tartozik a számlasor (vagy X = egyik sem). Billentyű: a betűk, <kbd>K</kbd> kétértelmű, <kbd>N</kbd> nem tudom.
Az állapot a böngészőben mentődik; a végén <b>Exportálás</b>.</p>
<div id="app"></div>
<div class="bar"><button id="back">← Előző</button><button id="exp">Exportálás (JSON)</button><span class="mut" id="saved"></span></div>
</main><script>
const DATA = __DATA__;
const KEY = "ldh-atnezes-" + DATA.sig;
let st = {i:0, d:{}};
try { st = JSON.parse(localStorage.getItem(KEY)) || st; } catch(e) {}
const ELOZO = DATA.elozo || {};
for (const id in ELOZO) if (!st.d[id]) st.d[id] = ELOZO[id];
function kesz(i){ return !!ELOZO[DATA.items[i].id]; }
function save(){ try{ localStorage.setItem(KEY, JSON.stringify(st)); document.getElementById('saved').textContent='mentve'; }catch(e){} }
function esc(s){ return String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
function render(){
  const n = DATA.items.length;
  while (st.i < n && kesz(st.i)) st.i++; document.getElementById('cnt').textContent = `${Math.min(st.i+1,n)} / ${n}`;
  document.getElementById('pb').style.width = (100*Object.keys(st.d).length/n)+'%';
  const app = document.getElementById('app');
  if (st.i >= n){ app.innerHTML = '<div class="card"><b>Kész.</b> Exportáld a döntéseket.</div>'; return; }
  const it = DATA.items[st.i], d = st.d[it.id] || {};
  let h = `<div class="card"><div class="mut">Számlasor</div><div class="sor">${esc(it.sor)}</div>
   <div class="mut" style="margin-top:6px">${esc(it.szallito)} · ${esc(it.menny)} · nettó egységár: ${esc(it.ar)} Ft</div></div><div class="card">`;
  for (const o of it.opts) h += `<button class="opt" data-c="${o.l}"><b>${o.l})</b> ${esc(o.t)} <span class="mut">${esc(o.p)}</span></button>`;
  h += `<div class="bar"><button data-c="K">Kétértelmű</button><button data-c="N">Nem tudom</button></div></div>`;
  if (d.valasz && d.valasz !== it.gold && !d.masodik){
    const g = it.opts.find(o=>o.l===it.gold);
    h += `<div class="card rev"><b>A generált címke: ${esc(it.gold)}) ${esc(g?g.t:'')}</b>
      <div class="mut">Valódi cikk: ${esc(it.nyom.valodi_cikk)} · szállítói megnevezés: ${esc(it.nyom.szallitoi_megnevezes)} ·
      tulajdonságok: ${esc(JSON.stringify(it.nyom.attrs))} · X-fajta: ${esc(it.nyom.x_fajta)}</div>
      <div class="bar"><button data-m="gold_hibas">A generált címke hibás (az én választásom a jó)</button>
      <button data-m="en_tevedtem">Én tévedtem</button><button data-m="ketertelmu">Kétértelmű</button></div></div>`;
  }
  app.innerHTML = h;
  app.querySelectorAll('button[data-c]').forEach(b=>b.onclick=()=>choose(b.dataset.c));
  app.querySelectorAll('button[data-m]').forEach(b=>b.onclick=()=>second(b.dataset.m));
}
function choose(c){
  const it = DATA.items[st.i]; st.d[it.id] = {valasz:c, t:Date.now()};
  if (c === it.gold) st.i++;
  save(); render();
}
function second(m){ const it = DATA.items[st.i]; st.d[it.id].masodik = m; st.i++; save(); render(); }
document.getElementById('back').onclick=()=>{
  let j = st.i - 1; while (j >= 0 && kesz(j)) j--;
  if (j < 0) return;
  st.i = j; delete st.d[DATA.items[j].id]; save(); render(); };
document.getElementById('exp').onclick=()=>{
  const blob = new Blob([JSON.stringify({sig:DATA.sig, dontesek:st.d}, null, 1)], {type:'application/json'});
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'dontesek.json'; a.click();
};
document.addEventListener('keydown', e=>{
  if (st.i >= DATA.items.length) return;
  const k = e.key.toUpperCase(), it = DATA.items[st.i], d = st.d[it.id] || {};
  if (d.valasz && d.valasz !== it.gold && !d.masodik) return;
  if (it.opts.some(o=>o.l===k) || k==='K' || k==='N') choose(k);
});
render();
</script></body></html>"""


def carry_over(records: list[dict], old_minta: Path, old_dec: Path) -> dict:
    """Korábbi döntések átvétele (2026-10-04, F1F): ha egy új mintabeli item kontextusa, opcióhalmaza és goldja
    azonos egy korábban eldöntött itemével, a döntés opció-id szerint átfordítva átjön (az újrakeverés miatt a
    betűk mások). A mintát NEM bővítjük a régi itemekkel: a változatlan itemek épp a duplikátum-mentesek, a
    hozzáadásuk lefelé torzítaná a zajbecslést."""
    old = {r["id"]: r for r in json.load(open(old_minta))["records"]}
    dec = json.load(open(old_dec))["dontesek"]
    res = {}
    for r in records:
        o, d = old.get(r["id"]), dec.get(r["id"])
        if not o or not d:
            continue
        it, oi = r["item"], o["item"]
        if (it["context"] != oi["context"] or it["gold"] != oi["gold"]
                or {x["id"] for x in it["options"]} != {x["id"] for x in oi["options"]}):
            continue
        oo, no = permutation(oi, 0), permutation(it, 0)
        lab_old = dict(zip(labels_for(oo), oo))
        lab_new = {v: k for k, v in zip(labels_for(no), no)}
        v = d["valasz"]
        if v not in ("K", "N"):
            v = lab_new[lab_old[v]]
        res[r["id"]] = {**d, "valasz": v, "atvett": True}
    return res


def cmd_html(args) -> None:
    out = _p(args.out)
    m = json.load(open(out / "minta.json"))
    recs = [r for r in m["records"] if not args.adag or r.get("adag", 1) == args.adag]
    elozo = carry_over(recs, _p(args.elozo_minta), _p(args.elozo_dontesek)) if args.elozo_minta else {}
    items = []
    for r in recs:
        it = r["item"]
        order = permutation(it, 0)
        opts_by = {o["id"]: o for o in it["options"]}
        opts = [{"l": lab, "t": ("Egyik sem" if oid is None else opts_by[oid]["text"]), "p": ("" if oid is None else opts_by[oid]["path"])}
                for oid, lab in zip(order, labels_for(order))]
        c = it["context"]
        items.append({"id": it["id"], "sor": c["sor"], "szallito": c["szallito"], "menny": f"{c['mennyiseg']} {c['egyseg']}",
                      "ar": c["egysegar"], "opts": opts, "gold": r["gold_label"], "nyom": r["nyom"]})
    sig = f"{len(items)}-{hashlib.sha256('|'.join(i['id'] for i in items).encode()).hexdigest()[:10]}"
    html = HTML.replace("__DATA__", json.dumps({"sig": sig, "items": items, "elozo": elozo}, ensure_ascii=False))
    name = f"atnezo_adag{args.adag}.html" if args.adag else "atnezo.html"
    (out / name).write_text(html, encoding="utf-8")
    print(f"{out / name}: {len(items)} item, ebből {len(elozo)} korábbi döntéssel")


def maradek_bayes(rep: dict, retegek: list[str], draws: int = 20000, seed: int = 7) -> dict:
    """A javítás utáni maradék címkezaj (hibás gold vagy kétértelmű) a rétegek együttesén: cellánként Jeffreys-Beta poszterior a hibaarányra,
    a nem átnézett itemek várható hibáinak összege Monte Carlóval → pont (medián) és 95. percentilis, arányban.
    A cellánkénti CP-felsők összeadása itt túl konzervatív (egy 0/15-ös cella egyedül ~20%-ot adna)."""
    import numpy as np

    rng = np.random.default_rng(seed)
    n_tot = sum(rep[sp]["n"] for sp in retegek)
    # a „többi” szint arányos mintájában a bekerülés minden cellában ~azonos → a rétegek többi-cellái EGY egyszerű
    # véletlen mintaként becsülendők (cellánként külön a Jeffreys-prior cellaszámszor adódna össze); a konszenzusos
    # szint bekerülése rétegenként eltér → rétegenként
    cellak = [rep[sp]["cellak"]["konszenzus"] for sp in retegek]
    tobbi = [rep[sp]["cellak"][c] for sp in retegek for c in ("tobbi_x", "tobbi_nemx")]
    cellak.append({k: sum(c[k] for c in tobbi) for k in ("pool", "atnezett", "zaj")})
    tot = np.zeros(draws)
    for c in cellak:
        rest = c["pool"] - c["atnezett"]
        if rest <= 0:
            continue
        p = rng.beta(c["zaj"] + 0.5, c["atnezett"] - c["zaj"] + 0.5, size=draws)
        tot += rng.binomial(rest, p)
    r = tot / max(1, n_tot)
    return {"n": n_tot, "pont": float(np.median(r)), "felso95": float(np.quantile(r, 0.95))}


def cmd_osszesit(args) -> None:
    out = _p(args.out)
    m = json.load(open(out / "minta.json"))
    dec = {}
    for f in args.dontesek.split(","):  # több adag döntései (vesszővel); ütközésnél a későbbi fájl nyer
        dec.update(json.load(open(_p(f)))["dontesek"])
    rep, fixes = {}, []
    for sp in STRATA:
        pc = m["pool_counts"][sp]
        recs = [r for r in m["records"] if r["stratum"] == sp and r["id"] in dec]
        res, e_tot, fixed = {}, 0.0, 0
        for c in CELLS:
            rr = [r for r in recs if cell(r) == c]
            err = [r for r in rr if dec[r["id"]].get("masodik") == "gold_hibas"]
            amb = [r for r in rr if dec[r["id"]].get("masodik") == "ketertelmu" or dec[r["id"]].get("valasz") == "K"]
            # zaj = hibás gold VAGY kétértelmű: a teszt a kétértelmű itemet is egyetlen golddal pontozná (2026-10-04)
            zaj = {r["id"] for r in err} | {r["id"] for r in amb}
            rate = len(zaj) / len(rr) if rr else None
            ci = cp_interval(len(zaj), len(rr))
            res[c] = {"pool": pc[c], "atnezett": len(rr), "gold_hibas": len(err), "ketertelmu": len(amb), "zaj": len(zaj),
                      "zajarany": rate, "cp95": ci}
            if pc[c]:
                # cella-arány × cellaméret (a cellán belül egyenletes a bekerülés); átnézés nélküli cellánál a CP-felső 1,0
                e_tot += (rate if rate is not None else 0.0) * pc[c]
                fixed += len(zaj)
        rep[sp] = {"cellak": res, "n": pc["n"], "becsult_hiba_osszes": e_tot / max(1, pc["n"]),
                   "becsult_maradek_javitas_utan": max(0.0, e_tot - fixed) / max(1, pc["n"])}
    for r in m["records"]:
        d = dec.get(r["id"])
        if not d:
            continue
        if d.get("masodik") == "gold_hibas" and d["valasz"] not in ("K", "N"):
            fixes.append({"id": r["id"], "stratum": r["stratum"], "muvelet": "javit", "uj_cimke": d["valasz"], "regi": r["gold_label"]})
        elif d.get("masodik") in ("ketertelmu", "gold_hibas") or d.get("valasz") == "K":
            # „gold hibás”, de a választás K / N: a helyes címke nem egyértelmű → kétértelmű
            fixes.append({"id": r["id"], "stratum": r["stratum"], "muvelet": "ketertelmu"})
    teszt = [sp for sp in STRATA if sp.startswith("T-")]
    osszes = {"teszt": maradek_bayes(rep, teszt), "val": maradek_bayes(rep, [sp for sp in STRATA if sp.startswith("val-")]),
              "kapu_max": 0.02}
    osszes["kapu_ok"] = osszes["teszt"]["felso95"] <= osszes["kapu_max"]
    write_json(out / "osszesites.json", {"retegek": rep, "teszt": osszes, "javitasok": len(fixes)})
    write_jsonl(out / "javitasok.jsonl", fixes)
    print(json.dumps({"retegek": {k: {"teljes": round(v["becsult_hiba_osszes"], 4), "maradek": round(v["becsult_maradek_javitas_utan"], 4)}
                                  for k, v in rep.items()}, "teszt": osszes, "javitasok": len(fixes)}, ensure_ascii=False))


def cmd_alkalmaz(args) -> None:
    """A javítások beírása az item-fájlokba (runbook F1 5–6.), majd végleges hash és befagyasztás-jelölő.

    - „javit”: a gold Dani választása lesz (a 0. permutáció címkéje → opció-id; X → None), a régi gold a
      meta.atnezes mezőbe kerül;
    - „ketertelmu”: meta.ketertelmu = True (a teszten nem pontozott), soft címke a régi gold + Dani választása.
    Csendes törlés nincs. Az eredeti fájlok *.pre_atnezes.jsonl néven megmaradnak."""
    import shutil

    gen = _p(args.gen)
    out = _p(args.out)
    fixes = {f["id"]: f for f in read_jsonl(out / "javitasok.jsonl")}
    dec = {}
    for f in args.dontesek.split(","):
        dec.update(json.load(open(_p(f)))["dontesek"])
    stat = defaultdict(int)
    for sp in STRATA:
        f = gen / f"items_{sp}.jsonl"
        bak = gen / f"items_{sp}.pre_atnezes.jsonl"
        if not bak.exists():
            shutil.copy(f, bak)
        items = read_jsonl(bak)
        for it in items:
            fx = fixes.get(it["id"])
            if not fx:
                continue
            order = permutation(it, 0)
            lab2id = dict(zip(labels_for(order), order))
            if fx["muvelet"] == "javit":
                new = lab2id.get(fx["uj_cimke"], "?")
                if new == "?":
                    stat["ismeretlen_cimke"] += 1
                    continue
                it["meta"]["atnezes"] = {"muvelet": "javit", "regi_gold": it["gold"], "uj_gold": new}
                it["gold"] = new
                stat["javitva"] += 1
            else:
                v = dec.get(it["id"], {}).get("valasz")
                # K / N nem opció: a soft halmazba csak valódi választás kerül (az X = None csak akkor, ha „X”-et választott)
                chosen = [lab2id[v]] if v in lab2id else []
                it["meta"]["atnezes"] = {"muvelet": "ketertelmu", "dani_valasztasa": v}
                it["meta"]["ketertelmu"] = True
                it["meta"]["soft"] = sorted({x for x in [it["gold"], *chosen] + (it["meta"].get("soft") or [])}, key=str)
                stat["ketertelmure"] += 1
        write_jsonl(f, items)
    import hashlib as _h
    lines = []
    for f in sorted(gen.glob("items_*.jsonl")):
        if ".pre_atnezes" in f.name:
            continue
        lines.append(f"{_h.sha256(f.read_bytes()).hexdigest()}  {f.name}")
    (out / "fagyasztas.sha256").write_text("\n".join(lines) + "\n")
    write_json(out / "FAGYASZTVA.json", {**stat, "fajlok": len(lines)})
    print(json.dumps({**stat, "hash": str(out / "fagyasztas.sha256")}, ensure_ascii=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["minta", "potadag", "szukit", "html", "osszesit", "alkalmaz"])
    ap.add_argument("--n", type=int, default=150, help="potadag: a pótadag mérete (a „többi” szintből)")
    ap.add_argument("--adag", type=int, default=0, help="html: csak ennek az adagnak az itemjei (0 = mind)")
    ap.add_argument("--cimke", default="s8v1", help="szukit: a régi minta mentésének címkéje")
    ap.add_argument("--gen", default="adat/f1")
    ap.add_argument("--biralo", default="eredmenyek/F1/biralo")
    ap.add_argument("--out", default="adat/f1/atnezes")
    ap.add_argument("--dontesek", default="adat/f1/atnezes/dontesek.json")
    ap.add_argument("--seed", type=int, default=404)
    ap.add_argument("--elozo-minta", default="", help="html: a korábbi minta.json (a döntések átvételéhez)")
    ap.add_argument("--elozo-dontesek", default="", help="html: a korábbi dontesek.json")
    ap.add_argument("--strata", default="", help="vesszős rétegnév-lista (üres = az F1 hat rétege; 00b: T-ujszallito)")
    ap.add_argument("--n-tobbi", type=int, default=0, help="minta: a „többi” szint mérete (0 = N_TOBBI)")
    args = ap.parse_args()
    global STRATA, N_TOBBI
    if args.strata:
        STRATA = args.strata.split(",")
    if args.n_tobbi:
        N_TOBBI = args.n_tobbi
    {"minta": cmd_minta, "potadag": cmd_potadag, "szukit": cmd_szukit, "html": cmd_html, "osszesit": cmd_osszesit, "alkalmaz": cmd_alkalmaz}[args.cmd](args)


if __name__ == "__main__":
    main()
