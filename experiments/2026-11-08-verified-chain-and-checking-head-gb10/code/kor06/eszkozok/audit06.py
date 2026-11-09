"""06-os kör — a címkeaudit (D14) vak felülete és összesítése, az `eszkozok/atnezes.py` mintájára.

  html      — önálló, offline átnéző felület a `kor06/adat/f2/audit/minta.jsonl`-ből (családonként 100 item): a szöveg,
              a kérdés és az opciók a tárolt (kanonikus) sorrendben. Dani választ: egy opciót, vagy X (egyik sem illik,
              NO_MATCH), M (hiányzik a döntő adat, MISSING_DATA), O (nem ehhez a feladathoz tartozik, OUT_OF_SCOPE);
              K kétértelmű, N nem tudom. Ha a választás eltér a konstrukciótól, a felület megmutatja a konstrukció
              címkéjét és a terv tényeit, és második ítéletet kér (a konstrukció hibás / én tévedtem / kétértelmű).
              Az item-id kimondja az állapotot, ezért a felület átlátszatlan kulcsot lát (a001…); a leképezés a
              `audit/atnezo_kulcsok.json`-ben. A család, a nyelv és a szelet sem látszik. localStorage + JSON-export.
  osszesit  — a döntések a kulccsal szemben: egyezés családonként és állapotonként, a hibák listája, a kapu (a
              címkehiba egyoldali 95%-os Clopper–Pearson felső korlátja ≤ 2%; 300 példán legfeljebb 1 hiba). Hibának
              számít a „konstrukció hibás” és a „kétértelmű” második ítélet.

  python3 kor06/eszkozok/audit06.py html
  python3 kor06/eszkozok/audit06.py osszesit --dontesek kor06/adat/f2/audit/dontesek.json

Második kör (D18–D19 után; friss minta csak a javított családokra): `--kor 2`. Az összesítés `--elozo`-val az 1. kör
döntéseit is beveszi azokra a családokra, amelyek a 2. körben nem szerepelnek, így a kapu ismét 300 itemre szól.
  python3 kor06/eszkozok/audit06.py html --kor 2
  python3 kor06/eszkozok/audit06.py osszesit --kor 2 --dontesek …/kor2/dontesek.json --elozo …/audit/dontesek_kor1.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(EXP / "eszkozok")]
from atnezes import cp_interval  # noqa: E402
from common import labels_for, permutation  # noqa: E402

D = EXP / "kor06/adat/f2"
OUT = EXP / "kor06/eredmenyek/F2/audit"
KOD = {"NO_MATCH": "X", "MISSING_DATA": "M", "OUT_OF_SCOPE": "O"}
KAPU = 0.02


def jl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def gold_code(it: dict, key: dict) -> str:
    """A konstrukció címkéje a felület kódjaival: MATCH-nél az opció betűje a kanonikus sorrendben, egyébként X/M/O."""
    if key["content_state"] != "MATCH":
        return KOD[key["content_state"]]
    order = permutation(it, 0)
    return next(lab for oid, lab in zip(order, labels_for(order)) if oid == key["gold"])


def adir(kor: int) -> Path:
    return D / "audit" if kor == 1 else D / f"audit/kor{kor}"


def cmd_html(a) -> None:
    A = adir(a.kor)
    minta, kulcs = jl(A / "minta.jsonl"), {k["id"]: k for k in jl(A / "kulcs.jsonl")}
    terv = {r["group_id"]: r["terv"] for f in {it["family"] for it in minta} for r in jl(D / f"raw/{f}.jsonl")}
    items, kulcsok = [], {}
    for n, it in enumerate(minta, 1):
        k = f"a{n:03d}" if a.kor == 1 else f"{chr(ord('a') + a.kor - 1)}{n:03d}"
        kulcsok[k] = it["id"]
        order = permutation(it, 0)
        by = {o["id"]: o["text"] for o in it["options"]}
        items.append({"k": k, "szoveg": it["state"], "kerdes": it["question"],
                      "opts": [{"l": lab, "t": "Egyik sem" if oid is None else by[oid]} for oid, lab in zip(order, labels_for(order))],
                      "gold": gold_code(it, kulcs[it["id"]]), "allapot": kulcs[it["id"]]["content_state"],
                      "tenyek": terv[it["id"]]["tenyek"]})
    sig = f"{len(items)}-{hashlib.sha256('|'.join(kulcsok.values()).encode()).hexdigest()[:10]}"
    (A / "atnezo_kulcsok.json").write_text(json.dumps({"sig": sig, "kulcsok": kulcsok}, ensure_ascii=False, indent=1) + "\n",
                                                 encoding="utf-8")
    out = A / "atnezo.html"
    out.write_text(HTML.replace("__DATA__", json.dumps({"sig": sig, "items": items}, ensure_ascii=False)), encoding="utf-8")
    print(f"{out}: {len(items)} item (sig {sig})")


def kor_rekordok(kor: int, dontesek: str, csak: set[str] | None = None) -> tuple[dict, list[tuple]]:
    A = adir(kor)
    km = json.loads((A / "atnezo_kulcsok.json").read_text())
    dec = json.loads(Path(dontesek).read_text())
    if dec.get("sig") != km["sig"]:
        raise SystemExit(f"a döntésfájl más mintához tartozik ({dec.get('sig')} ≠ {km['sig']})")
    minta = {it["id"]: it for it in jl(A / "minta.jsonl")}
    kulcs = {k["id"]: k for k in jl(A / "kulcs.jsonl")}
    km["kulcsok"] = {k: i for k, i in km["kulcsok"].items() if csak is None or minta[i]["family"] in csak}
    return km, [(k, iid, minta[iid], kulcs[iid], dec["dontesek"].get(k)) for k, iid in km["kulcsok"].items()]


def cmd_osszesit(a) -> None:
    km, recs = kor_rekordok(a.kor, a.dontesek)
    if a.elozo:
        most = {r[2]["family"] for r in recs}
        elozo_km, elozo = kor_rekordok(1, a.elozo, csak={f for f in ("penzugy.bankparositas", "muszaki.hibaelharitas",
                                                                      "szabaly.koltsegelszamolas") if f not in most})
        recs += elozo
        km["kulcsok"] |= elozo_km["kulcsok"]
    hianyzik = [r[0] for r in recs if r[4] is None]
    tabla, hibak, nyitott = defaultdict(Counter), [], []
    for k, iid, it, ky, d in recs:
        if d is None:
            continue
        g = gold_code(it, ky)
        cell = tabla[(it["family"], ky["content_state"])]
        cell["n"] += 1
        if d["valasz"] == g:
            cell["egyezik"] += 1
            continue
        m = d.get("masodik")
        cell[m or "nyitott"] += 1
        rec = {"kulcs": k, "id": iid, "family": it["family"], "lang": it["lang"], "allapot": ky["content_state"],
               "konstrukcio": g, "dani": d["valasz"], "masodik": m, "megjegyzes": d.get("megj", "")}
        (hibak if m in ("gold_hibas", "ketertelmu") else nyitott if m is None else []).append(rec)
    n = sum(c["n"] for c in tabla.values())
    _, hi = cp_interval(len(hibak), n, alpha=0.10) if n else (0.0, 1.0)  # kétoldali 90% → egyoldali 95% felső korlát
    rep = {"sig": km["sig"], "atnezve": n, "hianyzik": len(hianyzik), "nyitott_masodik_itelet": len(nyitott),
           "hiba": len(hibak), "felso_korlat_95": hi, "kapu": KAPU,
           "kapu_atment": bool(n == len(km["kulcsok"]) and not nyitott and hi <= KAPU),
           "cellak": {f"{f}|{s}": dict(c) for (f, s), c in sorted(tabla.items())}, "hibak": hibak, "nyitott": nyitott}
    out = OUT if a.kor == 1 else OUT / f"kor{a.kor}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "osszesito.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    L = ["# 06 F2 — címkeaudit (D14)", "",
         f"Átnézve {n} / {len(km['kulcsok'])}; nyitott második ítélet {len(nyitott)}; címkehiba {len(hibak)}; "
         f"az egyoldali 95%-os felső korlát {100 * hi:.2f}% (kapu ≤ {100 * KAPU:.0f}%): "
         f"**{'átment' if rep['kapu_atment'] else 'nem ment át' if n == len(km['kulcsok']) and not nyitott else 'még nem dönthető el'}**.", "",
         "| család | állapot | n | egyezik | konstrukció hibás | én tévedtem | kétértelmű |", "|---|---|---|---|---|---|---|"]
    L += [f"| {f} | {s} | {c['n']} | {c['egyezik']} | {c['gold_hibas']} | {c['en_tevedtem']} | {c['ketertelmu']} |"
          for (f, s), c in sorted(tabla.items())]
    if hibak:
        L += ["", "## Címkehibák", ""] + [f"- `{h['id']}` ({h['kulcs']}): konstrukció {h['konstrukcio']}, Dani {h['dani']}, "
                                          f"{h['masodik']}{'; ' + h['megjegyzes'] if h['megjegyzes'] else ''}" for h in hibak]
    (out / "osszesito.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


HTML = """<!doctype html><html lang="hu"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Címkeaudit 06</title>
<style>
:root{--bg:#f7f7f5;--fg:#1d1d1b;--mut:#6b6b66;--card:#fff;--bd:#dcdcd6;--acc:#2f5bd3;--warn:#a6461b}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#161615;--fg:#ececea;--mut:#9a9a94;--card:#21211f;--bd:#3a3a36;--acc:#7c9cff;--warn:#f0956a}}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.45 system-ui,sans-serif}
main{max-width:860px;margin:0 auto;padding:16px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:16px;margin:12px 0}
.mut{color:var(--mut);font-size:14px}.szoveg{white-space:pre-wrap;word-break:break-word}
button{font:inherit;padding:8px 12px;margin:4px 6px 4px 0;border:1px solid var(--bd);border-radius:8px;background:var(--card);color:var(--fg);cursor:pointer;text-align:left}
button:hover{border-color:var(--acc)}.opt{display:block;width:100%}.bar{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.rev{border-left:4px solid var(--warn);padding-left:12px}.prog{height:6px;background:var(--bd);border-radius:3px}.prog>div{height:6px;background:var(--acc);border-radius:3px}
kbd{border:1px solid var(--bd);border-radius:4px;padding:0 4px;font-size:13px}textarea{width:100%;box-sizing:border-box;font:inherit;background:var(--card);color:var(--fg);border:1px solid var(--bd);border-radius:8px}
pre{white-space:pre-wrap;word-break:break-word;font-size:13px}
</style></head><body><main>
<h1 style="font-size:20px">Címkeaudit <span class="mut" id="cnt"></span></h1>
<div class="prog"><div id="pb" style="width:0"></div></div>
<p class="mut">Melyik válasz helyes a szöveg alapján? Billentyű: az opció betűje; <kbd>X</kbd> egyik sem illik; <kbd>M</kbd> hiányzik a
döntő adat; <kbd>O</kbd> nem ehhez a feladathoz tartozik; <kbd>K</kbd> kétértelmű; <kbd>N</kbd> nem tudom. Az állapot a böngészőben
mentődik; a végén <b>Exportálás</b>.</p>
<div id="app"></div>
<div class="bar"><button id="back">← Előző</button><button id="exp">Exportálás (JSON)</button><span class="mut" id="saved"></span></div>
</main><script>
const DATA = __DATA__;
const KEY = "ldh-audit06-" + DATA.sig;
const ALL = {X:"X — egyik sem illik (a helyes válasz nincs a listán)", M:"M — hiányzik a döntő adat", O:"O — nem ehhez a feladathoz tartozik"};
const NEV = {X:"egyik sem illik (NO_MATCH)", M:"hiányzik a döntő adat (MISSING_DATA)", O:"nem ehhez a feladathoz tartozik (OUT_OF_SCOPE)"};
let st = {i:0, d:{}};
try { st = JSON.parse(localStorage.getItem(KEY)) || st; } catch(e) {}
function save(){ try{ localStorage.setItem(KEY, JSON.stringify(st)); document.getElementById('saved').textContent='mentve'; }catch(e){} }
function esc(s){ return String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
function cimke(it, c){ const o = it.opts.find(o=>o.l===c); return o ? `${c}) ${o.t}` : (NEV[c] || c); }
function render(){
  const n = DATA.items.length;
  document.getElementById('cnt').textContent = `${Math.min(st.i+1,n)} / ${n}`;
  document.getElementById('pb').style.width = (100*Object.keys(st.d).length/n)+'%';
  const app = document.getElementById('app');
  if (st.i >= n){ app.innerHTML = '<div class="card"><b>Kész.</b> Exportáld a döntéseket.</div>'; return; }
  const it = DATA.items[st.i], d = st.d[it.k] || {};
  let h = `<div class="card"><div class="mut">${esc(it.k)}</div><div class="szoveg">${esc(it.szoveg)}</div></div>
    <div class="card"><b>${esc(it.kerdes)}</b><div style="margin-top:8px">`;
  for (const o of it.opts) if (o.l !== 'X') h += `<button class="opt" data-c="${o.l}"><b>${o.l})</b> ${esc(o.t)}</button>`;
  for (const c in ALL) h += `<button class="opt" data-c="${c}">${esc(ALL[c])}</button>`;
  h += `</div><div class="bar"><button data-c="K">Kétértelmű</button><button data-c="N">Nem tudom</button></div>
    <textarea id="megj" rows="2" placeholder="Megjegyzés (nem kötelező)">${esc(d.megj||'')}</textarea></div>`;
  if (d.valasz && d.valasz !== it.gold && !d.masodik){
    h += `<div class="card rev"><b>A konstrukció: ${esc(cimke(it, it.gold))}</b> <span class="mut">(állapot: ${esc(it.allapot)})</span>
      <div class="mut">A te választásod: ${esc(cimke(it, d.valasz))}</div><pre>${esc(JSON.stringify(it.tenyek, null, 1))}</pre>
      <div class="bar"><button data-m="gold_hibas">A konstrukció hibás</button><button data-m="en_tevedtem">Én tévedtem</button>
      <button data-m="ketertelmu">Kétértelmű</button></div></div>`;
  }
  app.innerHTML = h;
  app.querySelectorAll('button[data-c]').forEach(b=>b.onclick=()=>choose(b.dataset.c));
  app.querySelectorAll('button[data-m]').forEach(b=>b.onclick=()=>second(b.dataset.m));
}
function megj(){ const t = document.getElementById('megj'); return t ? t.value.trim() : ''; }
function choose(c){
  const it = DATA.items[st.i]; st.d[it.k] = {valasz:c, megj:megj(), t:Date.now()};
  if (c === it.gold) st.i++;
  save(); render();
}
function second(m){ const it = DATA.items[st.i]; st.d[it.k].masodik = m; st.d[it.k].megj = megj(); st.i++; save(); render(); }
document.getElementById('back').onclick=()=>{ if (st.i > 0){ st.i--; delete st.d[DATA.items[st.i].k]; save(); render(); } };
document.getElementById('exp').onclick=()=>{
  const blob = new Blob([JSON.stringify({sig:DATA.sig, dontesek:st.d}, null, 1)], {type:'application/json'});
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'dontesek.json'; a.click();
};
document.addEventListener('keydown', e=>{
  if (e.target.tagName === 'TEXTAREA' || st.i >= DATA.items.length) return;
  const k = e.key.toUpperCase(), it = DATA.items[st.i], d = st.d[it.k] || {};
  if (d.valasz && d.valasz !== it.gold && !d.masodik) return;
  if (it.opts.some(o=>o.l===k && k!=='X') || k in ALL || k==='K' || k==='N') choose(k);
});
render();
</script></body></html>"""


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("html").add_argument("--kor", type=int, default=1)
    o = sub.add_parser("osszesit")
    o.add_argument("--kor", type=int, default=1)
    o.add_argument("--dontesek", required=True)
    o.add_argument("--elozo", help="az 1. kör döntései a 2. körben nem szereplő családokra")
    a = ap.parse_args()
    {"html": cmd_html, "osszesit": cmd_osszesit}[a.cmd](a)


if __name__ == "__main__":
    main()
