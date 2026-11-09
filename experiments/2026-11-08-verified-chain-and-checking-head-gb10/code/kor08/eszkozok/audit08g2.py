"""08 G2 — az értelmezési teszt egységenkénti címkeauditja (G1-rögzítés 5.4; Dani 11-03). Az alany döntése és
bizonyossága nem kerül a lapra; az audit a kiolvasás előtt van.

  minta     a három minta (átfedhetnek; a lapra egységenként egyszer kerül, a tagság a kulcsfájlban):
              lefedési  szabálycsalád: minden forgatókönyv mindkét nyelven egy teljes egység (1 (a) + 3 (b)); bank és
                        hiba: sablononként (= forgatókönyv, egy nyelvű) egy egység, (a) + egy (b)
              véletlen  családonként 30 egység, nyelvenként 15, a lefedésivel azonos terjedelemben; a címkehibaarány
                        csak ebből becsülhető
              jelzett   a Gemma eltérő (b) itemjei (`kor08/adat/G2/<rész>/gemma/eltero.jsonl`), a teljes egységgel; az
                        (a) eltérése nem jelöl (Dani 11-04: a Gemma kerete az (a) Y-címkéjét nem tudja kifejezni, a
                        próbában az (a) 92%-a „eltérő”; az (a)-n a Gemma választása leíró, `gemma08`)
            → `kor08/adat/G2/<rész>/audit/{lap,kulcs}.json` (a lap adatában nincs id, gold, állapot és tény; a kulcsban van)
  html      a lap (`atnezo.html`): egységenként a kérdés és az opciók egyszer, a változatok egymás mellett (az (a) és a
            (b)-k; a (b)-ben kiemelve, ami az (a)-ban nincs), változatonként zárolt vak választás; eltérésnél a
            konstrukció és a felülvizsgálat (külön mező); egységszinten a hiba fajtája (konstrukciós / egyedi). Utána
            szivárgás-ellenőrzés.
  osszesit  Dani exportja a kulccsal szemben → `kor08/eredmenyek/G2/audit/osszesito.{json,md}` és a kezelés
            (`kor08/adat/G2/<rész>/audit/kezeles.json`: javított címkék, kizárt egységek, felülvizsgálandó cellák) az 5.4
            szabálya szerint: javítható, ha a hiba csak a goldban van és a vak választás egyértelmű; egyébként az egység
            kimarad; két független hibás alapeset egy forgatókönyv–nyelv cellában felülvizsgálat; konstrukciós hiba
            egyetlen esetből is a forgatókönyv felülvizsgálata. A 80 alapeset és a 320 item külön sorban (nem függetlenek).

  python3 kor08/eszkozok/audit08g2.py minta [--resz ert_teszt]
  python3 kor08/eszkozok/audit08g2.py html [--resz ert_teszt]
  python3 kor08/eszkozok/audit08g2.py osszesit --dontesek kor08/adat/G2/ert_teszt/audit/dontesek.json
  python3 kor08/eszkozok/audit08g2.py alkalmaz [--felulvizsgalat F]
            a kezelés az itemeken (a kiolvasás előtt): a javított gold, a kizárt egységek kimaradnak; a felülvizsgálandó
            cellák és forgatókönyvek döntése (`--felulvizsgalat`: {"cella": {"<család>|<klaszter>|<nyelv>": "marad" |
            "kizar"}, "forgatokonyv": {"<család>|<klaszter>": …}}) nélkül nem fut. Az eredeti az `items_audit_elott/` alá.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import random
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
BANK, HIBA, SZAB = "penzugy.bankparositas", "muszaki.hibaelharitas", "szabaly.koltsegelszamolas"
CSALADOK = (BANK, HIBA, SZAB)
SEED = "audit08g2:2026-11-03"
VELETLEN = 30
NEM_OPCIO = {"X": "Egyik sem felel meg", "M": "Hiányzik a döntő adat", "Z": "Nem a hatáskör"}
ALLAPOT_KOD = {"NO_MATCH": "X", "MISSING_DATA": "M", "OUT_OF_SCOPE": "Z"}


GYOKER = {"d": EXP / "kor08/adat/G2", "e": EXP / "kor08/eredmenyek/G2/audit"}  # `--gyoker`: a kódpróba a scratch alá


def d(resz: str) -> Path:
    return GYOKER["d"] / resz


def jl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def h(s: str) -> int:
    return int(hashlib.sha256(f"{SEED}|{s}".encode()).hexdigest(), 16)


def egysegek(resz: str, fam: str) -> dict[str, dict]:
    """Egység-id → {klaszter, nyelv, változatok: {(a), b1, b2, b3}: item}."""
    out: dict[str, dict] = {}
    for it in jl(d(resz) / "items" / f"{fam}.jsonl"):
        e = it["meta"]["ertelmezes"]
        u = out.setdefault(e["egyseg"], {"klaszter": it["template_group_id"], "lang": it["lang"], "v": {}})
        u["v"]["a" if e["alt"] == "a" else f"b{e['valtozat']}"] = it
    return {k: u for k, u in out.items() if len(u["v"]) == 4}


def cmd_minta(a) -> None:
    lap, kulcs = [], {"resz": a.resz, "seed": SEED, "keszult": datetime.now().isoformat(timespec="seconds"), "egysegek": {}}
    tag: dict[tuple[str, str], dict] = {}  # (család, egység) → {minta: set, változatok: set}

    def jelol(fam: str, eid: str, minta: str, valt: set[str]) -> None:
        x = tag.setdefault((fam, eid), {"minta": set(), "v": set()})
        x["minta"].add(minta)
        x["v"] |= valt
    for fam in CSALADOK:
        U = egysegek(a.resz, fam)
        if not U:
            continue
        teljes = fam == SZAB
        rnd = random.Random(f"{SEED}:{fam}")

        def terj(eid: str) -> set[str]:
            return {"a", "b1", "b2", "b3"} if teljes else {"a", f"b{1 + h(f'b:{eid}') % 3}"}
        cella = defaultdict(list)  # lefedési: szabálycsalád forgatókönyv × nyelv; bank és hiba sablon (egy nyelvű)
        for eid, u in U.items():
            cella[(u["klaszter"], u["lang"]) if teljes else (u["klaszter"],)].append(eid)
        for k in sorted(cella):
            eid = sorted(cella[k], key=lambda e: h(f"lef:{e}"))[0]
            jelol(fam, eid, "lefedesi", terj(eid))
        for lang in ("hu", "en"):
            pool = sorted((e for e, u in U.items() if u["lang"] == lang), key=lambda e: h(f"vel:{e}"))
            for eid in rnd.sample(pool, min(VELETLEN // 2, len(pool))):
                jelol(fam, eid, "veletlen", terj(eid))
        eltero = {r["id"] for r in jl(d(a.resz) / "gemma" / "eltero.jsonl")}
        for eid, u in U.items():
            if any(it["id"] in eltero for v, it in u["v"].items() if v != "a"):
                jelol(fam, eid, "jelzett", {"a", "b1", "b2", "b3"})
    sor = sorted(tag, key=lambda k: h(f"sor:{k[1]}"))
    for n, (fam, eid) in enumerate(sor, 1):
        U = egysegek(a.resz, fam)[eid]
        x, k = tag[(fam, eid)], f"u{n:03d}"
        its = {v: U["v"][v] for v in ("a", "b1", "b2", "b3") if v in x["v"]}
        base = next(iter(its.values()))
        betuk = [chr(65 + i) for i in range(len(base["options"]))]
        lap.append({"k": k, "kerdes": base["question"], "opts": [{"l": l, "t": o["text"]} for l, o in zip(betuk, base["options"])],
                    "valt": [{"v": v, "szoveg": it["state"],
                              "r": base64.b64encode(json.dumps({"gold": _kod(it, betuk), "allapot": it["content_state"]},
                                                                ensure_ascii=False).encode()).decode()} for v, it in its.items()]})
        kulcs["egysegek"][k] = {"csalad": fam, "egyseg": eid, "klaszter": U["klaszter"], "lang": U["lang"],
                                "minta": sorted(x["minta"]), "itemek": {v: it["id"] for v, it in its.items()},
                                "gold": {v: _kod(it, betuk) for v, it in its.items()}}
    o = d(a.resz) / "audit"
    o.mkdir(parents=True, exist_ok=True)
    sig = hashlib.sha256(json.dumps(lap, ensure_ascii=False).encode()).hexdigest()[:12]
    kulcs["sig"] = sig
    (o / "lap.json").write_text(json.dumps({"sig": sig, "egysegek": lap}, ensure_ascii=False) + "\n", encoding="utf-8")
    (o / "kulcs.json").write_text(json.dumps(kulcs, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    c = Counter(m for v in kulcs["egysegek"].values() for m in v["minta"])
    n_it = sum(len(v["itemek"]) for v in kulcs["egysegek"].values())
    print(f"{len(lap)} egység, {n_it} item a lapon; mintánként (átfedéssel): {dict(c)}; sig {sig}")


def _kod(it: dict, betuk: list[str]) -> str:
    if it["gold"] is not None:
        return betuk[[o["id"] for o in it["options"]].index(it["gold"])]
    return ALLAPOT_KOD[it["content_state"]]


HTML = """<!doctype html><html lang="hu"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Címkeaudit 08 G2</title><style>
:root{--bg:#f6f5f2;--card:#fff;--fg:#1d1d1b;--mut:#6b6b66;--acc:#2f5d8a;--hl:#fff1a8;--rev:#fdecea;--ok:#e7f4ea;--bd:#dddad3}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--card:#22221f;--fg:#ecebe6;--mut:#a3a29c;--acc:#8db6e0;--hl:#5a4d10;--rev:#4a2422;--ok:#1f3a26;--bd:#3a3935}}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}
header{position:sticky;top:0;background:var(--bg);padding:10px 16px;border-bottom:1px solid var(--bd);display:flex;gap:12px;align-items:center;flex-wrap:wrap}
#pbw{flex:1;min-width:120px;height:6px;background:var(--bd);border-radius:3px}#pb{height:6px;background:var(--acc);border-radius:3px;width:0}
main{max-width:1500px;margin:0 auto;padding:12px 16px}.card{background:var(--card);border:1px solid var(--bd);border-radius:8px;padding:12px;margin:10px 0}
.grid{display:grid;gap:10px;grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}.mut{color:var(--mut);font-size:13px}
.szoveg{white-space:pre-wrap}mark{background:var(--hl);color:inherit}.rev{background:var(--rev)}.ok{background:var(--ok)}
button{font:inherit;border:1px solid var(--bd);background:var(--card);color:var(--fg);border-radius:6px;padding:5px 9px;margin:3px;cursor:pointer}
button:hover{border-color:var(--acc)}textarea{width:100%;box-sizing:border-box;font:inherit;background:var(--card);color:var(--fg);border:1px solid var(--bd);border-radius:6px}
h3{margin:0 0 6px;font-size:15px}</style></head><body>
<header><b>Címkeaudit 08 G2</b><span id="cnt"></span><div id="pbw"><div id="pb"></div></div><span id="saved" class="mut"></span>
<button id="back">← Előző</button><button id="next">Következő →</button><button id="exp">Export</button></header>
<main><div class="card mut">Egységenként: a kérdés és az opciók egyszer; a változatok egymás mellett. Minden változatnál válaszd
ki, mi a helyes válasz <b>csak a szöveg és az opciók alapján</b>; a választás rögzül. Ha mind megvan, eltérésnél megjelenik a
konstrukció címkéje, és külön rögzítheted a felülvizsgálatot. A kiemelés: a (b) szövegében az, ami az (a)-ban nincs.</div>
<div id="app"></div></main><script>
const DATA = __DATA__;
const KEY = "ldh-audit08g2-" + DATA.sig;
const NEM = __NEM__;
const MAS = {gold_hibas:"a konstrukció hibás, a vak választásom a helyes", en_tevedtem:"én tévedtem, a konstrukció a helyes",
             ketertelmu:"kétértelmű"};
const FAJTA = {konstrukcios:"konstrukciós (a terv / a forgatókönyv hibás)", egyedi:"egyedi megvalósítási (ez az alapeset: elírás, kimaradt mondat, fordítás)"};
let st = {i:0, d:{}};
try { st = JSON.parse(localStorage.getItem(KEY)) || st; } catch(e) {}
function save(){ try{ localStorage.setItem(KEY, JSON.stringify(st)); document.getElementById('saved').textContent='mentve'; }catch(e){} }
function esc(s){ return String(s).replace(/[&<>"]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
function R(v){ return JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(v.r), c=>c.charCodeAt(0)))); }
function szavak(s){ return new Set(s.toLowerCase().match(/[\\p{L}\\p{N}]+/gu) || []); }
function kiemel(s, ref){
  if (!ref) return esc(s);
  return s.split(/(\\s+)/).map(w=>{ const t = (w.toLowerCase().match(/[\\p{L}\\p{N}]+/gu)||[]);
    return t.length && t.some(x=>!ref.has(x)) ? `<mark>${esc(w)}</mark>` : esc(w); }).join('');
}
function cimke(u, c){ const o = u.opts.find(o=>o.l===c); return o ? `${c}) ${o.t}` : (NEM[c] || (c==='K'?'Kétértelmű':c==='N'?'Nem tudom':c)); }
function rec(u){ return st.d[u.k] = st.d[u.k] || {v:{}}; }
function mindvak(u){ const r = st.d[u.k]; return !!r && u.valt.every(v=>r.v[v.v] && r.v[v.v].valasz); }
function kesz(u){ const r = st.d[u.k]; if (!mindvak(u)) return false;
  const hibas = u.valt.filter(v=>r.v[v.v].valasz !== R(v).gold);
  if (hibas.some(v=>!r.v[v.v].masodik)) return false;
  const kell = hibas.some(v=>r.v[v.v].masodik !== 'en_tevedtem'); return !kell || !!r.fajta; }
function render(){
  const n = DATA.egysegek.length;
  document.getElementById('cnt').textContent = `${Math.min(st.i+1,n)} / ${n}`;
  document.getElementById('pb').style.width = (100*DATA.egysegek.filter(kesz).length/n)+'%';
  const app = document.getElementById('app');
  if (st.i >= n){ app.innerHTML = '<div class="card"><b>Kész.</b> Exportáld a döntéseket.</div>'; return; }
  const u = DATA.egysegek[st.i], r = st.d[u.k] || {v:{}}, vak = mindvak(u);
  const a = u.valt.find(v=>v.v==='a'), ref = a ? szavak(a.szoveg) : null;
  let h = `<div class="card"><div class="mut">${esc(u.k)}</div><b>${esc(u.kerdes)}</b><div>` +
    u.opts.map(o=>`<div><b>${o.l})</b> ${esc(o.t)}</div>`).join('') + `</div></div><div class="grid">`;
  for (const v of u.valt){
    const x = r.v[v.v], nev = v.v==='a' ? '(a)' : `(${v.v})`;
    h += `<div class="card"><h3>${nev}</h3><div class="szoveg">${v.v==='a' ? esc(v.szoveg) : kiemel(v.szoveg, ref)}</div><div style="margin-top:8px">`;
    if (!x || !x.valasz){
      h += u.opts.map(o=>`<button data-v="${v.v}" data-c="${o.l}">${o.l}</button>`).join('') +
        Object.keys(NEM).map(c=>`<button data-v="${v.v}" data-c="${c}" title="${esc(NEM[c])}">${c}</button>`).join('') +
        `<button data-v="${v.v}" data-c="K">Kétértelmű</button><button data-v="${v.v}" data-c="N">Nem tudom</button>`;
    } else {
      h += `<div class="mut">Vak választás (rögzítve): <b>${esc(cimke(u, x.valasz))}</b></div>`;
      if (vak){ const g = R(v).gold;
        if (x.valasz === g) h += `<div class="ok">Egyezik a konstrukcióval.</div>`;
        else { h += `<div class="rev"><b>A konstrukció: ${esc(cimke(u, g))}</b>`;
          h += x.masodik ? `<div>Felülvizsgálat: <b>${esc(MAS[x.masodik])}</b></div>` :
            Object.keys(MAS).map(m=>`<button data-v="${v.v}" data-m="${m}">${esc(MAS[m])}</button>`).join('');
          h += `</div>`; } }
    }
    h += `</div></div>`;
  }
  h += `</div>`;
  if (vak){
    const hibas = u.valt.filter(v=>r.v[v.v].masodik && r.v[v.v].masodik !== 'en_tevedtem');
    if (hibas.length){ h += `<div class="card"><b>A hiba fajtája:</b> ` + Object.keys(FAJTA).map(f=>
      `<button data-f="${f}" ${r.fajta===f?'style="border-color:var(--acc);font-weight:600"':''}>${esc(FAJTA[f])}</button>`).join('') + `</div>`; }
  }
  h += `<div class="card"><textarea id="megj" rows="2" placeholder="Megjegyzés az egységhez (nem kötelező)">${esc(r.megj||'')}</textarea></div>`;
  app.innerHTML = h;
  app.querySelectorAll('button[data-c]').forEach(b=>b.onclick=()=>choose(b.dataset.v, b.dataset.c));
  app.querySelectorAll('button[data-m]').forEach(b=>b.onclick=()=>second(b.dataset.v, b.dataset.m));
  app.querySelectorAll('button[data-f]').forEach(b=>b.onclick=()=>{ rec(u).fajta = b.dataset.f; save(); render(); });
  const t = document.getElementById('megj'); t.onchange=()=>{ rec(u).megj = t.value.trim(); save(); };
}
function choose(v, c){ const u = DATA.egysegek[st.i], r = rec(u); if (r.v[v] && r.v[v].valasz) return;  // a vak választás egyszer rögzül
  r.v[v] = {valasz:c, t:Date.now()}; save(); render(); }
function second(v, m){ const u = DATA.egysegek[st.i], x = rec(u).v[v]; if (!x || x.masodik) return;
  const g = R(u.valt.find(z=>z.v===v)).gold;
  x.masodik = m; x.felulvizsgalt = m === 'en_tevedtem' ? g : m === 'gold_hibas' ? x.valasz : 'K'; x.t2 = Date.now(); save(); render(); }
document.getElementById('back').onclick=()=>{ if (st.i > 0){ st.i--; save(); render(); window.scrollTo(0,0); } };
document.getElementById('next').onclick=()=>{ if (st.i < DATA.egysegek.length){ st.i++; save(); render(); window.scrollTo(0,0); } };
document.getElementById('exp').onclick=()=>{
  const blob = new Blob([JSON.stringify({sig:DATA.sig, dontesek:st.d}, null, 1)], {type:'application/json'});
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'dontesek.json'; a.click(); };
render();
</script></body></html>
"""


def cmd_html(a) -> None:
    o = d(a.resz) / "audit"
    lap = json.loads((o / "lap.json").read_text(encoding="utf-8"))
    html = HTML.replace("__DATA__", json.dumps(lap, ensure_ascii=False)).replace("__NEM__", json.dumps(NEM_OPCIO, ensure_ascii=False))
    (o / "atnezo.html").write_text(html, encoding="utf-8")
    kulcs = json.loads((o / "kulcs.json").read_text(encoding="utf-8"))
    tilos = {i for u in kulcs["egysegek"].values() for i in u["itemek"].values()} | {u["egyseg"] for u in kulcs["egysegek"].values()} \
        | {u["klaszter"] for u in kulcs["egysegek"].values()} | set(CSALADOK) | {"G2T", "G2N", "MATCH", "MISSING_DATA", "(z)"}
    nyilt = re.sub(r'"r":\s*"[A-Za-z0-9+/=]*"', '"r":""', html)  # a kódolt mezőben a véletlen egyezés nem szivárgás
    sziv = sorted(x for x in tilos if x in nyilt)
    if sziv:
        raise SystemExit(f"szivárgás a lapon: {sziv[:10]}")
    if re.search(r'"gold"\s*:', html):
        raise SystemExit("a gold nyíltan a lapon")
    print(f"→ {o / 'atnezo.html'}; {len(lap['egysegek'])} egység; szivárgás nincs")


def wilson(k: int, n: int, z: float = 1.96) -> list[float]:
    if not n:
        return [math.nan, math.nan]
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    w = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [max(0.0, c - w), min(1.0, c + w)]


def cmd_osszesit(a) -> None:
    o = d(a.resz) / "audit"
    kulcs = json.loads((o / "kulcs.json").read_text(encoding="utf-8"))
    ex = json.loads(Path(a.dontesek).read_text(encoding="utf-8"))
    if ex["sig"] != kulcs["sig"]:
        raise SystemExit(f"az export más laphoz tartozik ({ex['sig']} ≠ {kulcs['sig']})")
    D = ex["dontesek"]
    egys, hianyos, kezeles = {}, [], {"javitott": {}, "kizart_egyseg": [], "felulvizsgalando_cella": [], "felulvizsgalando_forgatokonyv": []}
    for k, U in kulcs["egysegek"].items():
        r = D.get(k)
        if not r or any(v not in r.get("v", {}) or "valasz" not in r["v"][v] for v in U["itemek"]):
            hianyos.append(k)
            continue
        hibak = {}
        for v, g in U["gold"].items():
            x = r["v"][v]
            if x["valasz"] == g:
                continue
            m = x.get("masodik")
            if m is None:
                hianyos.append(k)
                break
            if m != "en_tevedtem":
                hibak[v] = {"konstrukcio": g, "vak": x["valasz"], "masodik": m}
        else:
            # 5.4: javítható, ha a hiba csak a goldban van, a vak választás egyértelmű, és az egység a javítás után is a
            # konstrukciónak felel meg: a (b) helyes válasza egy opció (döntő jel), az (a)-é M; ezért az (a) hibája és a (b)
            # X / M / Z-re javítása nem javítható (az egység kimarad)
            javithato = all(h["masodik"] == "gold_hibas" and v != "a" and h["vak"] not in (*NEM_OPCIO, "K", "N")
                            for v, h in hibak.items())
            allapot = "rendben" if not hibak else "javitva" if javithato else "kizarva"
            egys[k] = {**U, "hibak": hibak, "fajta": r.get("fajta"), "allapot": allapot, "megj": r.get("megj", "")}
            if allapot == "javitva":
                for v, hh in hibak.items():
                    kezeles["javitott"][U["itemek"][v]] = hh["vak"]
            elif allapot == "kizarva":
                kezeles["kizart_egyseg"].append(U["egyseg"])
    # cellák: két független hibás alapeset → felülvizsgálat; konstrukciós hiba → a forgatókönyv felülvizsgálata
    cella = defaultdict(list)
    for k, e in egys.items():
        if e["hibak"]:
            cella[(e["csalad"], e["klaszter"], e["lang"])].append(e["egyseg"])
            if e["fajta"] == "konstrukcios":
                kezeles["felulvizsgalando_forgatokonyv"].append([e["csalad"], e["klaszter"]])
    kezeles["felulvizsgalando_cella"] = [[f, kl, lang, len(v)] for (f, kl, lang), v in sorted(cella.items()) if len(v) >= 2]
    rep = {"sig": kulcs["sig"], "hianyos": hianyos, "csaladok": {}}
    for fam in CSALADOK:
        E = [e for e in egys.values() if e["csalad"] == fam]
        if not E:
            continue
        F = {}
        for minta in ("lefedesi", "veletlen", "jelzett"):
            M = [e for e in E if minta in e["minta"]]
            ki = sum(bool(e["hibak"]) for e in M)
            it = sum(len(e["itemek"]) for e in M)
            ih = sum(len(e["hibak"]) for e in M)
            F[minta] = {"alapeset": len(M), "item": it, "hibas_alapeset": ki, "hibas_item": ih,
                        "kizart": sum(e["allapot"] == "kizarva" for e in M), "javitott": sum(e["allapot"] == "javitva" for e in M)}
        v = F["veletlen"]
        F["cimkehibaarany_veletlen"] = {"alapeset": v["hibas_alapeset"] / v["alapeset"] if v["alapeset"] else None,
                                        "ci95": wilson(v["hibas_alapeset"], v["alapeset"])}
        rep["csaladok"][fam] = F
    rep["kezeles"] = {k: len(x) for k, x in kezeles.items()}
    out = GYOKER["e"] / a.resz
    out.mkdir(parents=True, exist_ok=True)
    (out / "osszesito.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (o / "kezeles.json").write_text(json.dumps(kezeles, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    md = [f"# 08 G2 — címkeaudit ({a.resz})", "", f"Lap {kulcs['sig']}; hiányos egység: {len(hianyos)}. Az alapesetek és az "
          "itemek külön sorban: egy alapeset változatai nem függetlenek. A címkehibaarány csak a véletlen mintából.", "",
          "| család | minta | alapeset | item | hibás alapeset | hibás item | javítva | kizárva |", "|---|---|---|---|---|---|---|---|"]
    for fam, F in rep["csaladok"].items():
        for minta in ("lefedesi", "veletlen", "jelzett"):
            x = F[minta]
            md.append(f"| {fam} | {minta} | {x['alapeset']} | {x['item']} | {x['hibas_alapeset']} | {x['hibas_item']} | {x['javitott']} | {x['kizart']} |")
    md += ["", "A címkehibaarány (véletlen minta, alapesetenként, 95% Wilson): " + "; ".join(
        f"{fam}: {F['cimkehibaarany_veletlen']['alapeset']:.1%} [{F['cimkehibaarany_veletlen']['ci95'][0]:.1%}; "
        f"{F['cimkehibaarany_veletlen']['ci95'][1]:.1%}]" for fam, F in rep["csaladok"].items() if F["cimkehibaarany_veletlen"]["alapeset"] is not None),
           "", f"Kezelés: {rep['kezeles']}. A felülvizsgálandó cellák és forgatókönyvek a `kezeles.json`-ban; a felülvizsgálat "
           "eredményéig az érintett cella nem kerül a kiolvasásba."]
    (out / "osszesito.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


def cmd_alkalmaz(a) -> None:
    o = d(a.resz) / "audit"
    kez = json.loads((o / "kezeles.json").read_text(encoding="utf-8"))
    fv = json.loads(Path(a.felulvizsgalat).read_text(encoding="utf-8")) if a.felulvizsgalat else {"cella": {}, "forgatokonyv": {}}
    nyitott = [c for c in kez["felulvizsgalando_cella"] if "|".join(map(str, c[:3])) not in fv["cella"]] + \
              [f for f in kez["felulvizsgalando_forgatokonyv"] if "|".join(f) not in fv["forgatokonyv"]]
    if nyitott:
        raise SystemExit(f"felülvizsgálandó cella vagy forgatókönyv döntés nélkül: {nyitott[:5]}")
    kizart = set(kez["kizart_egyseg"])
    rep_ = {}
    for fam in CSALADOK:
        p = d(a.resz) / "items" / f"{fam}.jsonl"
        if not p.exists():
            continue
        arch = d(a.resz) / "items_audit_elott" / f"{fam}.jsonl"
        arch.parent.mkdir(parents=True, exist_ok=True)
        if not arch.exists():
            arch.write_bytes(p.read_bytes())
        out, c = [], Counter()
        for it in jl(arch):
            e = it["meta"]["ertelmezes"]
            cel = f"{fam}|{it['template_group_id']}|{it['lang']}"
            if e["egyseg"] in kizart or fv["cella"].get(cel) == "kizar" or \
                    fv["forgatokonyv"].get(f"{fam}|{it['template_group_id']}") == "kizar":
                c["kimarad"] += 1
                continue
            if it["id"] in kez["javitott"]:
                betu = kez["javitott"][it["id"]]
                it = {**it, "gold": it["options"][ord(betu) - 65]["id"], "meta": {**it["meta"], "audit_javitva": True}}
                c["javitott"] += 1
            out.append(it)
        p.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in out), encoding="utf-8")
        rep_[fam] = {"item": len(out), **c}
    (o / "ALKALMAZVA.json").write_text(json.dumps({"ido": datetime.now().isoformat(timespec="seconds"), "csaladok": rep_},
                                                  ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(rep_, ensure_ascii=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("minta")
    ht = sub.add_parser("html")
    o = sub.add_parser("osszesit")
    o.add_argument("--dontesek", required=True)
    al = sub.add_parser("alkalmaz")
    al.add_argument("--felulvizsgalat")
    for x in (m, ht, o, al):
        x.add_argument("--resz", default="ert_teszt", choices=("ert_teszt", "ert_tanito"))
        x.add_argument("--gyoker", help="kódpróba: a G2 adat és az eredmény gyökere")
    a = ap.parse_args()
    if a.gyoker:
        GYOKER["d"], GYOKER["e"] = Path(a.gyoker), Path(a.gyoker) / "eredmenyek"
    {"minta": cmd_minta, "html": cmd_html, "osszesit": cmd_osszesit, "alkalmaz": cmd_alkalmaz}[a.cmd](a)


if __name__ == "__main__":
    main()
