"""E irány — a számítási csapdák (calc_traps) vak auditja (Dani 2026-11-20: „60 tételes vak audit”).

  lap       60 tétel: csapdatípus × nyelv szerint rétegezve (5 × 2 × 6), seedelt mintával → publikacio/E/audit/audit_cimkezo.html
            (átlátszatlan kulcsok; a lapon nincs azonosító, család, csapdatípus és helyes válasz), kulcs: audit_kulcs.json
  ertekel   Dani exportja (audit_dontesek.json) a konstrukció válaszával szemben → audit_eredmeny.json

A lapon a kiadásra kerülő (névcserélt) szöveg áll. Dani opciót választ, vagy „egyik sem / nem dönthető el”.
Előre rögzített szabály: a hibásnak talált tétel kikerül a kiadásból; legfeljebb 2 eltérés esetén (60-ból) a konfiguráció
az audit számával megy ki, 3 vagy több eltérésnél Dani dönt a folytatásról.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from collections import Counter
from pathlib import Path

EXP = Path(__file__).resolve().parents[2]
E = EXP / "publikacio/E"
A = E / "audit"
SEED = "e-audit:calc_traps:20261120"
LETTERS = "ABCDEFGH"


def jsonl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def lap(_a) -> None:
    its = jsonl(E / "data/calc_traps/test.jsonl")
    cella = {}
    for it in its:
        cella.setdefault((it["trap_type"], it["lang"]), []).append(it)
    rng = random.Random(SEED)
    minta = [it for k in sorted(cella) for it in rng.sample(sorted(cella[k], key=lambda r: r["id"]), 6)]
    rng.shuffle(minta)
    kulcs = {f"a{i + 1:03d}": it["id"] for i, it in enumerate(minta)}
    sig = hashlib.sha256("|".join(kulcs.values()).encode()).hexdigest()[:12]
    lapok = [{"k": k, "text": it["text"], "question": it["question"], "options": [o["text"] for o in it["options"]]} for k, it in zip(kulcs, minta)]
    A.mkdir(parents=True, exist_ok=True)
    (A / "audit_kulcs.json").write_text(json.dumps({"sig": sig, "kulcsok": kulcs}, indent=1) + "\n", encoding="utf-8")
    html = HTML.replace("__DATA__", json.dumps({"sig": sig, "items": lapok}, ensure_ascii=False))
    for tilos in ("dti-", "trap_type", "partial_payment", "unit_conversion", "net_vs_gross", "calc_traps"):
        if tilos in html:
            raise SystemExit(f"szivárgás a lapon: {tilos}")
    (A / "audit_cimkezo.html").write_text(html, encoding="utf-8")
    print(f"{A / 'audit_cimkezo.html'}: {len(lapok)} tétel, sig {sig}; cellák: {dict(Counter(f'{it['trap_type']}:{it['lang']}' for it in minta))}")


def cp_felso(k: int, n: int, alfa: float = 0.05) -> float:
    """Egyoldali Clopper–Pearson felső korlát, felezéssel."""
    if k >= n:
        return 1.0
    lo, hi = k / n, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if sum(math.comb(n, i) * mid**i * (1 - mid) ** (n - i) for i in range(k + 1)) > alfa:
            lo = mid
        else:
            hi = mid
    return hi


def ertekel(a) -> None:
    km = json.loads((A / "audit_kulcs.json").read_text())
    dec = json.loads(Path(a.dontesek).read_text())
    if dec.get("sig") != km["sig"]:
        raise SystemExit(f"a döntésfájl más laphoz tartozik ({dec.get('sig')} ≠ {km['sig']})")
    its = {it["id"]: it for it in jsonl(E / "data/calc_traps/test.jsonl")}
    sorok, c = [], Counter()
    for k, iid in km["kulcsok"].items():
        it, d = its[iid], dec["dontesek"].get(k)
        gold = LETTERS[[o["id"] for o in it["options"]].index(it["answer"])]
        e = "hianyzik" if d is None else "egyezik" if d == gold else "nem_donthato" if d == "N" else "elter"
        c[e] += 1
        sorok.append({"kulcs": k, "id": iid, "trap_type": it["trap_type"], "lang": it["lang"], "konstrukcio": gold, "dani": d, "eredmeny": e})
    n, hiba = len(sorok) - c["hianyzik"], c["elter"] + c["nem_donthato"]
    rep = {"sig": km["sig"], "atnezve": n, **c, "elteres": hiba, "felso_korlat_95": cp_felso(hiba, n) if n else None,
           "kapu": "kimegy az audit számával" if hiba <= 2 and not c["hianyzik"] else "Dani dönt",
           "elteresek": [s for s in sorok if s["eredmeny"] in ("elter", "nem_donthato")], "kizarando": [s["id"] for s in sorok if s["eredmeny"] in ("elter", "nem_donthato")],
           "cellak": {f"{t}:{e}": v for (t, e), v in sorted(Counter((s["trap_type"], s["eredmeny"]) for s in sorok).items())}}
    (A / "audit_eredmeny.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in rep.items() if k != "kizarando"}, ensure_ascii=False, indent=1))


HTML = """<!doctype html><html lang="hu"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Vak audit – számítási tételek</title><style>
:root{--bg:#f6f6f3;--fg:#1c1c1a;--mut:#666;--card:#fff;--line:#d8d8d2;--acc:#1f5fbf}
@media (prefers-color-scheme:dark){:root{--bg:#161614;--fg:#eaeae4;--mut:#9a9a92;--card:#20201d;--line:#3a3a35;--acc:#7fb0ff}}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif}main{max-width:860px;margin:0 auto;padding:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:16px;margin:12px 0}
pre{white-space:pre-wrap;font:15px/1.5 ui-monospace,monospace;margin:0}.q{font-weight:600;margin:12px 0 8px}
label{display:block;padding:8px 10px;border:1px solid var(--line);border-radius:6px;margin:6px 0;cursor:pointer}
label.sel{border-color:var(--acc);outline:2px solid var(--acc)}input{margin-right:8px}
.bar{display:flex;gap:8px;align-items:center;flex-wrap:wrap}button{font:inherit;padding:8px 14px;border-radius:6px;border:1px solid var(--line);background:var(--card);color:var(--fg);cursor:pointer}
.mut{color:var(--mut);font-size:14px}</style></head><body><main>
<h1>Vak audit</h1><p class="mut">Melyik opció a helyes válasz a kérdésre? Ha egyik sem, vagy a szövegből nem dönthető el, azt jelöld. A döntések a böngészőben mentődnek; a végén exportáld.</p>
<div class="bar"><button id="prev">← előző</button><span id="pos"></span><button id="next">következő →</button><span class="mut" id="done"></span><button id="exp">Export (JSON)</button></div>
<div class="card"><pre id="text"></pre><div class="q" id="q"></div><div id="opts"></div></div>
<script>
const DATA = __DATA__;
const KEY = "ldh-e-audit-" + DATA.sig; let st = {i:0, d:{}};
try { st = JSON.parse(localStorage.getItem(KEY)) || st; } catch(e) {}
function save(){ try{ localStorage.setItem(KEY, JSON.stringify(st)); }catch(e){} }
const L = "ABCDEFGH";
function show(){ const it = DATA.items[st.i]; document.getElementById('text').textContent = it.text; document.getElementById('q').textContent = it.question;
  const o = document.getElementById('opts'); o.innerHTML = '';
  [...it.options.map((t,j)=>[L[j], L[j]+') '+t]), ['N','Egyik sem / nem dönthető el']].forEach(([v,t])=>{ const l = document.createElement('label');
    const r = document.createElement('input'); r.type='radio'; r.name='o'; r.checked = st.d[it.k]===v; if(r.checked) l.className='sel';
    r.onchange = ()=>{ st.d[it.k]=v; save(); show(); }; l.appendChild(r); l.appendChild(document.createTextNode(t)); o.appendChild(l); });
  document.getElementById('pos').textContent = (st.i+1)+' / '+DATA.items.length;
  document.getElementById('done').textContent = 'kész: '+Object.keys(st.d).length+' / '+DATA.items.length; }
document.getElementById('prev').onclick = ()=>{ st.i = Math.max(0, st.i-1); save(); show(); };
document.getElementById('next').onclick = ()=>{ st.i = Math.min(DATA.items.length-1, st.i+1); save(); show(); };
document.getElementById('exp').onclick = ()=>{ const b = new Blob([JSON.stringify({sig:DATA.sig, dontesek:st.d}, null, 1)], {type:'application/json'});
  const a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = 'audit_dontesek.json'; a.click(); };
show();
</script></main></body></html>"""


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("lap")
    e = sub.add_parser("ertekel")
    e.add_argument("--dontesek", default=str(A / "audit_dontesek.json"))
    a = ap.parse_args()
    {"lap": lap, "ertekel": ertekel}[a.cmd](a)


if __name__ == "__main__":
    main()
