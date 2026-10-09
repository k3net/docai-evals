"""Címke-átnézés a 01-es körben (a 00 runbook 4.8 és a 00 `atnezes.py` protokollja, eszközválasztásra igazítva).

Csak a saját címkéjű rétegek kerülnek a mintába; a BFCL és a When2Call gold-ja a benchmarké (2. és 4. pont):
  val-xlam      — az xLAM kitartott eszközei, saját gold-droppal;
  val-massive   — a MASSIVE hu dev a katalógusra képezve (saját leképezés);
  T-hu          — a MASSIVE hu teszt ugyanígy;
  T-katalogus   — a Mistral által írt kérések (a Mistral itt bíráló is, ezért nagyobb véletlen minta);
  eu180k        — a train-kiegészítő EU-180k itemek, csak a hívásosak (a 9. pont 3. szerint csak átnézés után kerülhetnek
                  be; az X-itemek kimaradnak, mert a forrás „hívás nélkül” / „udvarias elutasítás” címkéje a beszélgetés
                  stílusát jelöli, nem azt, hogy nincs illő eszköz — Napló 2026-10-07).

  minta    — három szint: (1) „konszenzus”: minden bíráló ugyanazt a nem-gold címkét adja, mind ≥ FLAG_CONF-fal,
             rétegenként legfeljebb CAP_KONSZ; (2) „jelzes”: a szinonim-szűrő jelzése (csak az egyik bíráló szerint
             helyes a közeli pár is), rétegenként legfeljebb CAP_JELZES; (3) „tobbi”: rétegenként N_TOBBI[réteg]
             arányos véletlen minta X / nem-X szerint. A bekerülési valószínűség cellánként rögzül.
  html     — önálló, offline átnéző felület (vak: a gold és a szavazatok rejtve, amíg Dani nem választ).
  osszesit — Horvitz–Thompson-szerű cellabecslés és a javítás utáni maradék zaj (Jeffreys-Beta + Monte Carlo, a 00
             szerint); kapu: a T-hu + T-katalogus maradék zajának felső 95%-os korlátja ≤ KAPU.
  alkalmaz — javítások az itemfájlokba (mentés: *.pre_atnezes), a „rossz kérés” itemek kizárva (naplózva).
  szuro    — emberi vak szúrópróba a gépi átnézésre (Napló 2026-10-07: mindkét adagot gépi ágens töltötte ki):
             (1) minden gépi címkejavítás és a trainbe kerülő EU-180k gépi döntései; (2) SZURO_N egyszerű véletlen
             item a teljesen átnézett tesztrétegek gépileg változatlanul hagyott itemjeiből. Felület: atnezo_szuro.html
             (a tárolt címke a gépi javítás utáni; csak Dani vak válasza után látszik).
  szuro_osszesit — a gépi átnéző mért tévedése, a végleges javításlista (javitasok_vegleges.jsonl, `forras`:
             gepi / gepi+dani / dani) és a teszt maradék zaja; kapu: felső95 ≤ KAPU.

  python3 kor01/eszkozok/atnezes01.py minta
  python3 kor01/eszkozok/atnezes01.py html
  python3 kor01/eszkozok/atnezes01.py osszesit --dontesek kor01/adat/f1s/atnezes/dontesek.json
  python3 kor01/eszkozok/atnezes01.py szuro
  python3 kor01/eszkozok/atnezes01.py szuro_osszesit --dontesek kor01/adat/f1s/atnezes/dontesek_szuro.json
  python3 kor01/eszkozok/atnezes01.py alkalmaz --javitasok kor01/adat/f1s/atnezes/javitasok_vegleges.jsonl
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import random
import shutil
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from keret import LABELS, NONE_LABEL  # noqa: E402
from kozos01 import A, F1S, R, read_jsonl, write_json, write_jsonl  # noqa: E402

FLAG_CONF = 0.8
CAP_KONSZ = 25
CAP_JELZES = 15
N_TOBBI = {"val-xlam": 40, "val-massive": 40, "T-hu": 60, "T-katalogus": 80, "eu180k": 30}
STRATA = list(N_TOBBI)
TESZT = ["T-hu", "T-katalogus"]
VAL = ["val-xlam", "val-massive"]
KAPU = 0.02
SZURO_N = 150
CELLS = ["konszenzus", "jelzes", "tobbi_x", "tobbi_nemx"]
OUT = F1S / "atnezes"
BIRALO = R / "F1S/biralo"


def layer_files() -> dict[str, tuple[Path, str | None]]:
    """réteg → (itemfájl, forrás-szűrő)."""
    return {"val-xlam": (A / "items_val.jsonl", "xlam"), "val-massive": (A / "items_val.jsonl", "massive_hu"),
            "T-hu": (A / "items_teszt.jsonl", "massive_hu"), "T-katalogus": (F1S / "items_katalogus.jsonl", None),
            "eu180k": (F1S / "items_eu180k.jsonl", None)}


def order_of(it: dict) -> list[str | None]:
    return [o["id"] for o in it["options"]] + [None]


def labels_of(it: dict) -> list[str]:
    return LABELS[: len(it["options"])] + [NONE_LABEL]


def gold_label(it: dict) -> str:
    return dict(zip(order_of(it), labels_of(it)))[it["gold"]]


def cp_interval(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    from scipy.stats import beta

    if n == 0:
        return (0.0, 1.0)
    lo = beta.ppf(alpha / 2, k, n - k + 1) if k > 0 else 0.0
    hi = beta.ppf(1 - alpha / 2, k + 1, n - k) if k < n else 1.0
    return (float(lo), float(hi))


def cell(e: dict) -> str:
    return e["tier"] if e["tier"] != "tobbi" else ("tobbi_x" if e["x"] else "tobbi_nemx")


def build_pool() -> list[dict]:
    reviews = defaultdict(dict)
    for f in glob.glob(str(BIRALO / "*.jsonl")):
        for r in read_jsonl(Path(f)):
            reviews[r["id"]][r.get("model", Path(f).stem)] = r
    pool = []
    for sp, (f, src) in layer_files().items():
        for it in read_jsonl(f):
            if (src and it["forras"] != src) or it["meta"].get("ketertelmu"):
                continue
            if sp == "eu180k" and it["gold"] is None:  # a forrás X-e beszélgetési stílus, nem „nincs illő eszköz” (Napló)
                continue
            g = gold_label(it)
            votes = {m: (r.get("pred"), r.get("conf")) for m, r in reviews.get(it["id"], {}).items()}
            ans = [(p, c) for p, c in votes.values() if p]
            konsz = (len(ans) >= 2 and len({p for p, _ in ans}) == 1 and ans[0][0] != g
                     and all((c or 0) >= FLAG_CONF for _, c in ans))
            tier = "konszenzus" if konsz else "jelzes" if it["meta"].get("szinonim_jelzes") else "tobbi"
            pool.append({"item": it, "gold_label": g, "tier": tier, "votes": votes, "stratum": sp, "x": it["gold"] is None,
                         "flag": bool(ans) and any(p != g for p, _ in ans)})
    return pool


def pool_counts(pool: list[dict]) -> dict:
    return {sp: {"n": sum(e["stratum"] == sp for e in pool),
                 **{c: sum(e["stratum"] == sp and cell(e) == c for e in pool) for c in CELLS}} for sp in STRATA}


def cmd_minta(args) -> None:
    rng = random.Random(args.seed)
    pool = build_pool()
    sample, incl = [], {}
    for sp in STRATA:
        for tier, cap in (("konszenzus", CAP_KONSZ), ("jelzes", CAP_JELZES)):
            es = [e for e in pool if e["stratum"] == sp and e["tier"] == tier]
            rng.shuffle(es)
            for e in es[:cap]:
                incl[e["item"]["id"]] = min(cap, len(es)) / len(es)
            sample += es[:cap]
        rest = [e for e in pool if e["stratum"] == sp and e["tier"] == "tobbi"]
        for x in (True, False):
            es = [e for e in rest if e["x"] == x]
            k = max(2, round(N_TOBBI[sp] * len(es) / max(1, len(rest))))
            rng.shuffle(es)
            for e in es[:k]:
                incl[e["item"]["id"]] = min(k, len(es)) / len(es)
            sample += es[:k]
    rng.shuffle(sample)
    recs = [{"id": e["item"]["id"], "stratum": e["stratum"], "tier": e["tier"], "x": e["x"], "flag": e["flag"],
             "incl_prob": incl[e["item"]["id"]], "votes": e["votes"], "gold_label": e["gold_label"], "item": e["item"]}
            for e in sample]
    counts = pool_counts(pool)
    write_json(OUT / "minta.json", {"records": recs, "pool_counts": counts, "flag_conf": FLAG_CONF, "cap_konsz": CAP_KONSZ,
                                    "cap_jelzes": CAP_JELZES, "n_tobbi": N_TOBBI, "seed": args.seed})
    print(json.dumps({"minta": len(recs), "retegenkent": {sp: sum(r["stratum"] == sp for r in recs) for sp in STRATA},
                      "szintek": {t: sum(r["tier"] == t for r in recs) for t in ("konszenzus", "jelzes", "tobbi")},
                      "pool": counts}, ensure_ascii=False))


HTML = """<!doctype html><html lang="hu"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Címke-átnézés 01</title>
<style>
:root{--bg:#f7f7f5;--fg:#1d1d1b;--mut:#6b6b66;--card:#fff;--bd:#dcdcd6;--acc:#2f5bd3;--warn:#a6461b}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#161615;--fg:#ececea;--mut:#9a9a94;--card:#21211f;--bd:#3a3a36;--acc:#7c9cff;--warn:#f0956a}}
:root[data-theme=dark]{--bg:#161615;--fg:#ececea;--mut:#9a9a94;--card:#21211f;--bd:#3a3a36;--acc:#7c9cff;--warn:#f0956a}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.45 system-ui,sans-serif}
main{max-width:860px;margin:0 auto;padding:16px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:16px;margin:12px 0}
.mut{color:var(--mut);font-size:14px}.req{font:600 18px/1.4 system-ui,sans-serif;word-break:break-word}
button{font:inherit;padding:8px 12px;margin:4px 6px 4px 0;border:1px solid var(--bd);border-radius:8px;background:var(--card);color:var(--fg);cursor:pointer;text-align:left}
button:hover{border-color:var(--acc)}.opt{display:block;width:100%}.bar{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.rev{border-left:4px solid var(--warn);padding-left:12px}.prog{height:6px;background:var(--bd);border-radius:3px}.prog>div{height:6px;background:var(--acc);border-radius:3px}
kbd{border:1px solid var(--bd);border-radius:4px;padding:0 4px;font-size:13px}code{font-size:14px}
</style></head><body><main>
<h1 style="font-size:20px">Címke-átnézés — eszközválasztás <span class="mut" id="cnt"></span></h1>
<div class="prog"><div id="pb" style="width:0"></div></div>
<p class="mut">Melyik eszközt kell meghívni a kérésre (vagy X = egyik sem)? Billentyű: a betűk, <kbd>K</kbd> kétértelmű,
<kbd>N</kbd> nem tudom, <kbd>R</kbd> rossz / valószerűtlen kérés. Az állapot a böngészőben mentődik; a végén <b>Exportálás</b>.</p>
<div id="app"></div>
<div class="bar"><button id="back">← Előző</button><button id="exp">Exportálás (JSON)</button><span class="mut" id="saved"></span></div>
</main><script>
const DATA = __DATA__;
const KEY = "ldh01-atnezes-" + DATA.sig;
let st = {i:0, d:{}};
try { st = JSON.parse(localStorage.getItem(KEY)) || st; } catch(e) {}
function save(){ try{ localStorage.setItem(KEY, JSON.stringify(st)); document.getElementById('saved').textContent='mentve'; }catch(e){} }
function esc(s){ return String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
function render(){
  const n = DATA.items.length;
  document.getElementById('cnt').textContent = `${Math.min(st.i+1,n)} / ${n}`;
  document.getElementById('pb').style.width = (100*Object.keys(st.d).length/n)+'%';
  const app = document.getElementById('app');
  if (st.i >= n){ app.innerHTML = '<div class="card"><b>Kész.</b> Exportáld a döntéseket.</div>'; return; }
  const it = DATA.items[st.i], d = st.d[it.id] || {};
  let h = `<div class="card"><div class="mut">Kérés (${esc(it.lang)})</div><div class="req">${esc(it.req)}</div>`;
  if (it.hist) h += `<div class="mut" style="margin-top:6px">Előzmény: ${esc(it.hist)}</div>`;
  h += `</div><div class="card">`;
  for (const o of it.opts) h += `<button class="opt" data-c="${o.l}"><b>${o.l})</b> <code>${esc(o.n)}</code> ${esc(o.t)} <span class="mut">${esc(o.r)}</span></button>`;
  h += `<div class="bar"><button data-c="K">Kétértelmű</button><button data-c="N">Nem tudom</button><button data-c="R">Rossz kérés</button></div></div>`;
  if (d.valasz && d.valasz !== it.gold && d.valasz !== 'R' && !d.masodik){
    const g = it.opts.find(o=>o.l===it.gold);
    h += `<div class="card rev"><b>A tárolt címke: ${esc(it.gold)}) ${esc(g?g.n:'')}</b>
      <div class="mut">${esc(it.nyom)}</div>
      <div class="bar"><button data-m="gold_hibas">A tárolt címke hibás (az én választásom a jó)</button>
      <button data-m="en_tevedtem">Én tévedtem</button><button data-m="ketertelmu">Kétértelmű</button></div></div>`;
  }
  app.innerHTML = h;
  app.querySelectorAll('button[data-c]').forEach(b=>b.onclick=()=>choose(b.dataset.c));
  app.querySelectorAll('button[data-m]').forEach(b=>b.onclick=()=>second(b.dataset.m));
}
function choose(c){
  const it = DATA.items[st.i]; st.d[it.id] = {valasz:c, t:Date.now()};
  if (c === it.gold || c === 'R') st.i++;
  save(); render();
}
function second(m){ const it = DATA.items[st.i]; st.d[it.id].masodik = m; st.i++; save(); render(); }
document.getElementById('back').onclick=()=>{ if (st.i <= 0) return; st.i--; delete st.d[DATA.items[st.i].id]; save(); render(); };
document.getElementById('exp').onclick=()=>{
  const blob = new Blob([JSON.stringify({sig:DATA.sig, dontesek:st.d}, null, 1)], {type:'application/json'});
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'dontesek.json'; a.click();
};
document.addEventListener('keydown', e=>{
  if (st.i >= DATA.items.length) return;
  const k = e.key.toUpperCase(), it = DATA.items[st.i], d = st.d[it.id] || {};
  if (d.valasz && d.valasz !== it.gold && !d.masodik) return;
  if (it.opts.some(o=>o.l===k) || k==='K' || k==='N' || k==='R') choose(k);
});
render();
</script></body></html>"""


def nyom(it: dict) -> str:
    m = it["meta"]
    parts = [f"forrás: {it['forras']}"]
    for k in ("x_fajta", "kivett_gold", "potlas", "intent", "eszkoz"):
        if m.get(k):
            parts.append(f"{k}: {m[k]}")
    if m.get("szinonim_csere"):
        parts.append(f"szinonim-csere: {m['szinonim_csere']}")
    if m.get("szinonim_jelzes"):
        parts.append(f"szinonim-jelzés: {m['szinonim_jelzes']}")
    return " · ".join(parts)


def html_item(it: dict, gold: str, hint: str) -> dict:
    opts = []
    for oid, lab in zip(order_of(it), labels_of(it)):
        if oid is None:
            opts.append({"l": lab, "n": "", "t": "Egyik sem" if it["lang"] == "hu" else "None of these", "r": ""})
            continue
        o = next(x for x in it["options"] if x["id"] == oid)
        req = f"(kötelező: {', '.join(o['required'])})" if o.get("required") else ""
        opts.append({"l": lab, "n": o["name"], "t": o.get("description") or "", "r": req})
    hist = " / ".join(h.get("content") or "" for h in it.get("history") or [] if (h.get("content") or "").strip())
    return {"id": it["id"], "lang": it["lang"], "req": it["request"], "hist": hist, "opts": opts, "gold": gold, "nyom": hint}


def write_html(items: list[dict], name: str, download: str = "dontesek.json") -> None:
    sig = f"{len(items)}-{hashlib.sha256('|'.join(i['id'] for i in items).encode()).hexdigest()[:10]}"
    html = HTML.replace("__DATA__", json.dumps({"sig": sig, "items": items}, ensure_ascii=False))
    (OUT / name).write_text(html.replace("a.download = 'dontesek.json'", f"a.download = '{download}'"), encoding="utf-8")
    print(f"{OUT / name}: {len(items)} item, sig {sig}")


def cmd_html(args) -> None:
    m = json.load(open(OUT / "minta.json"))
    items = [html_item(r["item"], r["gold_label"], nyom(r["item"])) for r in m["records"]
             if not args.adag or r.get("adag", 1) == args.adag]
    write_html(items, f"atnezo_adag{args.adag}.html" if args.adag else "atnezo.html")


def cmd_potadag(args) -> None:
    """2. adag (Dani döntése, 2026-10-07): az 1. adag szerint a T-hu (MASSIVE-teszt) zaja ~10%, a T-katalógusé ~5%.
    A T-hu-ból egyszerű véletlen minta (`--t-hu` item a pontozott populációból), a T-katalógusból minden item, mindet
    Dani nézi át; a H2 T-hu rétege ez a részhalmaz lesz. Az 1. adagban már eldöntött itemek döntése átjön (nem
    kerülnek újra a felületre). A részhalmaz id-listája a minta.json `t_hu_reszhalmaz` mezőjébe kerül."""
    m = json.load(open(OUT / "minta.json"))
    have = {r["id"] for r in m["records"]}
    pool = build_pool()
    rng = random.Random(args.seed + 2)
    thu = sorted((e for e in pool if e["stratum"] == "T-hu"), key=lambda e: e["item"]["id"])
    rng.shuffle(thu)
    sub = thu[: args.t_hu]
    kat = [e for e in pool if e["stratum"] == "T-katalogus"]
    new = [e for e in sub + kat if e["item"]["id"] not in have]
    rng.shuffle(new)
    m["records"] += [{"id": e["item"]["id"], "stratum": e["stratum"], "tier": "teljes", "x": e["x"], "flag": e["flag"],
                      "incl_prob": None, "votes": e["votes"], "gold_label": e["gold_label"], "item": e["item"], "adag": 2}
                     for e in new]
    m["t_hu_reszhalmaz"] = sorted(e["item"]["id"] for e in sub)
    m["teljes_atnezes"] = {"T-hu": len(sub), "T-katalogus": len(kat), "seed": args.seed + 2}
    write_json(OUT / "minta.json", m)
    print(json.dumps({"uj": len(new), "T-hu_reszhalmaz": len(sub), "ebbol_korabban_atnezett": len(sub) - sum(
        e["stratum"] == "T-hu" for e in new), "T-katalogus": len(kat)}, ensure_ascii=False))


def maradek_bayes(rep: dict, retegek: list[str], draws: int = 20000, seed: int = 7) -> dict:
    """A javítás utáni maradék zaj a rétegek együttesén (a 00 `atnezes.py`-ja szerint): cellánként Jeffreys-Beta
    poszterior, a nem átnézett itemek várható hibái Monte Carlóval; a „többi” cellák egy egyszerű véletlen mintaként."""
    import numpy as np

    rng = np.random.default_rng(seed)
    n_tot = sum(rep[sp]["n"] for sp in retegek)
    cellak = [rep[sp]["cellak"][c] for sp in retegek for c in ("konszenzus", "jelzes")]
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


def load_dec(spec: str) -> dict:
    dec = {}
    for f in spec.split(","):
        dec.update(json.load(open(f))["dontesek"])
    return dec


def cmd_osszesit(args) -> None:
    m = json.load(open(OUT / "minta.json"))
    dec = load_dec(args.dontesek)
    rep, fixes = {}, []
    for sp in STRATA:
        pc = m["pool_counts"][sp]
        recs = [r for r in m["records"] if r["stratum"] == sp and r["id"] in dec and r.get("adag", 1) == 1]
        res, e_tot, fixed = {}, 0.0, 0
        for c in CELLS:
            rr = [r for r in recs if cell(r) == c]
            err = [r for r in rr if dec[r["id"]].get("masodik") == "gold_hibas"]
            amb = [r for r in rr if dec[r["id"]].get("masodik") == "ketertelmu" or dec[r["id"]].get("valasz") == "K"]
            bad = [r for r in rr if dec[r["id"]].get("valasz") == "R"]
            zaj = {r["id"] for r in err} | {r["id"] for r in amb}
            rate = len(zaj) / len(rr) if rr else None
            res[c] = {"pool": pc[c], "atnezett": len(rr), "gold_hibas": len(err), "ketertelmu": len(amb), "rossz_keres": len(bad),
                      "zaj": len(zaj), "zajarany": rate, "cp95": cp_interval(len(zaj), len(rr))}
            if pc[c]:
                e_tot += (rate if rate is not None else 0.0) * pc[c]
                fixed += len(zaj)
        rep[sp] = {"cellak": res, "n": pc["n"], "becsult_hiba_osszes": e_tot / max(1, pc["n"]),
                   "becsult_maradek_javitas_utan": max(0.0, e_tot - fixed) / max(1, pc["n"])}
    full = set(m.get("t_hu_reszhalmaz", [])) | {r["id"] for r in m["records"] if r["stratum"] == "T-katalogus"}
    for r in m["records"]:
        d = dec.get(r["id"])
        if not d:
            continue
        if d.get("valasz") == "N" and r["id"] in full:  # teljesen átnézett rétegben az eldöntetlen item nem pontozható
            fixes.append({"id": r["id"], "stratum": r["stratum"], "muvelet": "ketertelmu", "valasz": "N"})
        elif d.get("valasz") == "R":
            fixes.append({"id": r["id"], "stratum": r["stratum"], "muvelet": "kizar"})
        elif d.get("masodik") == "gold_hibas" and d["valasz"] not in ("K", "N"):
            fixes.append({"id": r["id"], "stratum": r["stratum"], "muvelet": "javit", "uj_cimke": d["valasz"], "regi": r["gold_label"]})
        elif d.get("masodik") in ("ketertelmu", "gold_hibas") or d.get("valasz") == "K":
            fixes.append({"id": r["id"], "stratum": r["stratum"], "muvelet": "ketertelmu", "valasz": d.get("valasz")})
    osszes = {"teszt": maradek_bayes(rep, TESZT), "val": maradek_bayes(rep, VAL), "eu180k": maradek_bayes(rep, ["eu180k"]),
              "kapu_max": KAPU}
    osszes["kapu_ok"] = osszes["teszt"]["felso95"] <= KAPU
    if full:
        tel = {}
        for name, ids in (("T-hu_reszhalmaz", set(m.get("t_hu_reszhalmaz", []))),
                          ("T-katalogus", {r["id"] for r in m["records"] if r["stratum"] == "T-katalogus"})):
            ds = [dec[i] for i in ids if i in dec]
            tel[name] = {"n": len(ids), "eldontve": len(ds),
                         "gold_hibas": sum(d.get("masodik") == "gold_hibas" for d in ds),
                         "ketertelmu": sum(d.get("masodik") == "ketertelmu" or d.get("valasz") in ("K", "N") for d in ds),
                         "rossz_keres": sum(d.get("valasz") == "R" for d in ds)}
            tel[name]["zajarany_javitas_elott"] = (tel[name]["gold_hibas"] + tel[name]["ketertelmu"]) / max(1, len(ds))
        osszes["teljes_atnezes"] = tel
        # teljes átnézés után a maradék zaj csak az átnéző tévedése: a kapu akkor áll, ha minden item el van döntve
        osszes["kapu_ok_teljes"] = all(v["eldontve"] == v["n"] for v in tel.values())
    write_json(OUT / "osszesites.json", {"retegek": rep, "osszes": osszes, "javitasok": len(fixes)})
    write_jsonl(OUT / "javitasok.jsonl", fixes)
    print(json.dumps({"retegek": {k: {"teljes": round(v["becsult_hiba_osszes"], 4), "maradek": round(v["becsult_maradek_javitas_utan"], 4)}
                                  for k, v in rep.items()}, "osszes": osszes, "javitasok": len(fixes)}, ensure_ascii=False))


def cmd_alkalmaz(args) -> None:
    """„javit”: a gold az átnéző választása (címke → opció-id; X → None), a régi gold a meta.atnezes-be; „ketertelmu”:
    meta.ketertelmu = True, soft = régi gold + az átnéző választása; „kizar”: az item kikerül (naplózva a javításlistában
    és a meta nélkül a FAGYASZTVA.json-ban). A meta.atnezes.forras: gepi / gepi+dani / dani. Az EU-180k forrás-X itemjei
    (a javítás előtti gold = X) kimaradnak a train-extra fájlból. Az eredeti fájlok *.pre_atnezes néven megmaradnak."""
    fixes = {f["id"]: f for f in read_jsonl(Path(args.javitasok))}
    sub = set(json.load(open(OUT / "minta.json")).get("t_hu_reszhalmaz", []))
    stat = defaultdict(int)
    files = sorted({f for f, _ in layer_files().values()})
    for f in files:
        bak = f.with_suffix(".jsonl.pre_atnezes")
        if not bak.exists():
            shutil.copy(f, bak)
        out = []
        for it in read_jsonl(bak):
            if f == F1S / "items_eu180k.jsonl" and it["gold"] is None:
                stat["eu180k_forras_x_kihagyva"] += 1  # a forrás X-e beszélgetési stílus (Napló 2026-10-07)
                continue
            if it["id"] in sub:
                it["meta"]["t_hu_atnezett"] = True  # a H2 T-hu rétege: a teljesen átnézett véletlen részhalmaz
                stat["t_hu_reszhalmaz"] += 1
            fx = fixes.get(it["id"])
            if fx is None:
                out.append(it)
                continue
            lab2id = dict(zip(labels_of(it), order_of(it)))
            if fx["muvelet"] == "kizar":
                stat["kizarva"] += 1
                continue
            if fx["muvelet"] == "javit":
                if fx["uj_cimke"] not in lab2id:
                    stat["ismeretlen_cimke"] += 1
                    out.append(it)
                    continue
                new = lab2id[fx["uj_cimke"]]
                it["meta"]["atnezes"] = {"muvelet": "javit", "regi_gold": it["gold"], "uj_gold": new,
                                         "forras": fx.get("forras")}
                it["gold"] = new
                stat["javitva"] += 1
            else:
                v = fx.get("valasz")
                chosen = [lab2id[v]] if v in lab2id else []
                it["meta"]["atnezes"] = {"muvelet": "ketertelmu", "valasztas": v, "forras": fx.get("forras")}
                it["meta"]["ketertelmu"] = True
                it["meta"]["soft"] = sorted({x for x in [it["gold"], *chosen] + (it["meta"].get("soft") or [])}, key=str)
                stat["ketertelmure"] += 1
            out.append(it)
        write_jsonl(f, out)
    lines = [f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.relative_to(A)}" for f in
             [A / "items_train.jsonl", *files]]
    (OUT / "fagyasztas.sha256").write_text("\n".join(lines) + "\n")
    write_json(OUT / "FAGYASZTVA.json", {**stat, "fajlok": len(lines)})
    print(json.dumps({**stat, "hash": str(OUT / "fagyasztas.sha256")}, ensure_ascii=False))


def cmd_szuro(args) -> None:
    """Emberi vak szúrópróba a gépi átnézésre (Dani döntése, 2026-10-07). A `javitasok.jsonl` az `osszesit` gépi
    javításlistája. (1) „gepi_javitas”: minden „javit” művelet, és az EU-180k minden gépi művelete (trainbe kerül, ott
    zárt modell döntése nem maradhat); (2) „valtozatlan”: SZURO_N egyszerű véletlen item a teljesen átnézett
    tesztrétegek (T-hu-részhalmaz + T-katalógus) azon itemjeiből, amelyekhez nincs gépi művelet. A felületen a tárolt
    címke a gépi javítás utáni címke; a gépi javításnál a nyomban az eredeti is látszik (csak Dani válasza után)."""
    m = json.load(open(OUT / "minta.json"))
    recs = {r["id"]: r for r in m["records"]}
    fixes = {f["id"]: f for f in read_jsonl(OUT / "javitasok.jsonl")}
    full = set(m["t_hu_reszhalmaz"]) | {i for i, r in recs.items() if r["stratum"] == "T-katalogus"}
    jav = sorted(i for i, f in fixes.items() if f["muvelet"] == "javit" or f["stratum"] == "eu180k")
    rng = random.Random(args.seed + 3)
    valt = sorted(i for i in full if i not in fixes)
    rng.shuffle(valt)
    valt = valt[:SZURO_N]
    out, items = [], []
    for csop, ids in (("gepi_javitas", jav), ("valtozatlan", valt)):
        for i in ids:
            r, f = recs[i], fixes.get(i)
            cur = f["uj_cimke"] if f and f["muvelet"] == "javit" else r["gold_label"]
            hint = nyom(r["item"])
            if f and f["muvelet"] == "javit":
                hint = f"gépi javítás, az eredeti címke: {r['gold_label']} · " + hint
            out.append({"id": i, "csoport": csop, "stratum": r["stratum"], "tarolt": cur, "eredeti": r["gold_label"],
                        "gepi": f, "teljes_reteg": i in full})
            items.append(html_item(r["item"], cur, hint))
    perm = list(range(len(items)))
    rng.shuffle(perm)
    write_json(OUT / "szuro.json", {"records": [out[k] for k in perm], "seed": args.seed + 3, "szuro_n": SZURO_N,
                                    "valtozatlan_pool": len([i for i in full if i not in fixes])})
    write_html([items[k] for k in perm], "atnezo_szuro.html", download="dontesek-szuro.json")
    print(json.dumps({"gepi_javitas": len(jav), "valtozatlan": len(valt),
                      "retegenkent": {sp: sum(o["stratum"] == sp for o in out) for sp in STRATA}}, ensure_ascii=False))


def dani_verdict(d: dict | None, tarolt: str) -> str | None:
    """megerosit / hibas / ketertelmu / rossz; None = nincs döntés."""
    if not d:
        return None
    v = d.get("valasz")
    if v == "R":
        return "rossz"
    if v == tarolt or d.get("masodik") == "en_tevedtem":
        return "megerosit"
    if d.get("masodik") == "gold_hibas" and v not in ("K", "N"):
        return "hibas"
    return "ketertelmu"


def cmd_szuro_osszesit(args) -> None:
    """A gépi átnéző mért tévedése és a végleges javításlista. A szúrópróbán Dani a referencia: a gépi javítás
    megerősítve → marad („gepi+dani”); hibás → Dani címkéje („dani”; ha az az eredeti, a javítás elmarad);
    kétértelmű / rossz kérés → Dani döntése. A változatlan cellában talált hiba javítva („dani”). A teszt maradék zaja:
    a szúrópróbán kívüli változatlan itemek várható hibája (Jeffreys-Beta + Monte Carlo); zaj = hibás + kétértelmű +
    rossz kérés (szigorúbb, mint az `osszesit`, ahol a rossz kérés nem zaj)."""
    import numpy as np

    sz = json.load(open(OUT / "szuro.json"))
    m = json.load(open(OUT / "minta.json"))
    dec = load_dec(args.dontesek)
    fixes = {f["id"]: {**f, "forras": "gepi"} for f in read_jsonl(OUT / "javitasok.jsonl")}
    stat = defaultdict(lambda: defaultdict(int))
    for r in sz["records"]:
        v = dani_verdict(dec.get(r["id"]), r["tarolt"])
        stat[r["csoport"]][v or "nincs_dontes"] += 1
        if v is None:
            continue
        d, i = dec[r["id"]], r["id"]
        if v == "megerosit":
            if i in fixes and fixes[i]["muvelet"] == "javit":
                fixes[i]["forras"] = "gepi+dani"
            elif i in fixes:  # a gépi kétértelmű / kizár ítélet, de Dani a tárolt (eredeti) címkét választotta
                fixes.pop(i)
                stat[r["csoport"]]["gepi_itelet_elvetve"] += 1
        elif v == "hibas":
            if d["valasz"] == r["eredeti"]:
                fixes.pop(i, None)
                stat[r["csoport"]]["visszaallitva"] += 1
            else:
                fixes[i] = {"id": i, "stratum": r["stratum"], "muvelet": "javit", "uj_cimke": d["valasz"],
                            "regi": r["eredeti"], "forras": "dani"}
        elif v == "ketertelmu":
            fixes[i] = {"id": i, "stratum": r["stratum"], "muvelet": "ketertelmu", "valasz": d.get("valasz"), "forras": "dani"}
        else:
            fixes[i] = {"id": i, "stratum": r["stratum"], "muvelet": "kizar", "forras": "dani"}
    full = set(m["t_hu_reszhalmaz"]) | {r["id"] for r in m["records"] if r["stratum"] == "T-katalogus"}
    scored = {i for i in full if fixes.get(i, {}).get("muvelet") not in ("kizar", "ketertelmu")}
    v_recs = [r for r in sz["records"] if r["csoport"] == "valtozatlan" and dec.get(r["id"])]
    k = sum(dani_verdict(dec[r["id"]], r["tarolt"]) != "megerosit" for r in v_recs)
    n = len(v_recs)
    rest = sz["valtozatlan_pool"] - n
    rng = np.random.default_rng(7)
    p = rng.beta(k + 0.5, n - k + 0.5, size=20000)
    resid = rng.binomial(rest, p) / max(1, len(scored))
    j_recs = [r for r in sz["records"] if r["csoport"] == "gepi_javitas" and r["gepi"]["muvelet"] == "javit"
              and dec.get(r["id"])]
    j_ok = sum(dani_verdict(dec[r["id"]], r["tarolt"]) == "megerosit" for r in j_recs)
    rep = {
        "csoportok": {c: dict(v) for c, v in stat.items()},
        "gepi_javitas_pontossaga": {"n": len(j_recs), "megerositve": j_ok, "arany": j_ok / max(1, len(j_recs)),
                                    "cp95": cp_interval(j_ok, len(j_recs))},
        "valtozatlan_hibaarany": {"n": n, "zaj": k, "arany": k / max(1, n), "cp95": cp_interval(k, n),
                                  "pool": sz["valtozatlan_pool"]},
        "teszt_maradek": {"pontozott": len(scored), "pont": float(np.median(resid)),
                          "felso95": float(np.quantile(resid, 0.95)), "kapu_max": KAPU},
        "javitasok_forras": {f: sum(x["forras"] == f for x in fixes.values()) for f in ("gepi", "gepi+dani", "dani")},
        "eu180k_gepi_maradt": sum(x["stratum"] == "eu180k" and x["forras"] == "gepi" for x in fixes.values()),
    }
    rep["kapu_ok"] = rep["teszt_maradek"]["felso95"] <= KAPU and all(dec.get(r["id"]) for r in sz["records"])
    write_json(OUT / "szuro_osszesites.json", rep)
    write_jsonl(OUT / "javitasok_vegleges.jsonl", sorted(fixes.values(), key=lambda x: x["id"]))
    print(json.dumps(rep, ensure_ascii=False))


def cmd_szuro_potminta(args) -> None:
    """+SZURO_N item a változatlan cellából, ha a kapu az első mintán bukik (Napló 2026-10-07). Ugyanannak a keverésnek
    a folytatása, mint a `szuro`-é, így az első és a pótminta együtt egyetlen egyszerű véletlen minta. Csak az új
    itemek kerülnek a felületre (atnezo_szuro2.html); a `szuro_osszesit` mindkét adag döntését együtt kapja."""
    sz = json.load(open(OUT / "szuro.json"))
    m = json.load(open(OUT / "minta.json"))
    recs = {r["id"]: r for r in m["records"]}
    fixes = {f["id"] for f in read_jsonl(OUT / "javitasok.jsonl")}
    full = set(m["t_hu_reszhalmaz"]) | {i for i, r in recs.items() if r["stratum"] == "T-katalogus"}
    valt = sorted(i for i in full if i not in fixes)
    rng = random.Random(sz["seed"])  # a `szuro`-ban ez a generátor első használata
    rng.shuffle(valt)
    have = [r["id"] for r in sz["records"] if r["csoport"] == "valtozatlan"]
    k = len(have)
    if set(valt[:k]) != set(have):
        raise SystemExit("a keverés nem reprodukálja az első mintát")
    new_ids = valt[k:k + SZURO_N]
    items, out = [], []
    for i in new_ids:
        r = recs[i]
        out.append({"id": i, "csoport": "valtozatlan", "stratum": r["stratum"], "tarolt": r["gold_label"],
                    "eredeti": r["gold_label"], "gepi": None, "teljes_reteg": True, "potminta": 1})
        items.append(html_item(r["item"], r["gold_label"], nyom(r["item"])))
    sz["records"] += out
    sz["potminta"] = {"n": len(out), "seed": sz["seed"]}
    write_json(OUT / "szuro.json", sz)
    write_html(items, "atnezo_szuro2.html", download="dontesek-szuro2.json")
    print(json.dumps({"potminta": len(out), "valtozatlan_osszesen": k + len(out),
                      "retegenkent": {sp: sum(o["stratum"] == sp for o in out) for sp in TESZT}}, ensure_ascii=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["minta", "potadag", "html", "osszesit", "alkalmaz", "szuro", "szuro_osszesit",
                                       "szuro_potminta"])
    ap.add_argument("--adag", type=int, default=0, help="html: csak ennek az adagnak az itemjei (0 = mind)")
    ap.add_argument("--t-hu", type=int, default=600, help="potadag: a teljesen átnézett T-hu részhalmaz mérete")
    ap.add_argument("--dontesek", default=str(OUT / "dontesek.json"))
    ap.add_argument("--javitasok", default=str(OUT / "javitasok.jsonl"), help="alkalmaz: a javításlista")
    ap.add_argument("--seed", type=int, default=20261008)
    args = ap.parse_args()
    {"minta": cmd_minta, "potadag": cmd_potadag, "html": cmd_html, "osszesit": cmd_osszesit,
     "alkalmaz": cmd_alkalmaz, "szuro": cmd_szuro, "szuro_osszesit": cmd_szuro_osszesit,
     "szuro_potminta": cmd_szuro_potminta}[args.cmd](args)


if __name__ == "__main__":
    main()
