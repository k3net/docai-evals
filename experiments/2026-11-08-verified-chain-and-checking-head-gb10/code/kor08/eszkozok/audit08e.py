"""08 G1b — a javított 2. kör (szabálycsalád) vak címkeauditja (D7; Dani 11-02: a javított párok modellválasz és
bizonyossági pontszám nélkül, a párok együtt). A 06 `audit06` vak lapja és összesítője burkolva, 08-as útvonalakkal; a 06
kódja nem változik.

  minta      — a `kor2j` szabálycsaládjának minden itemje, sablonként egymás után: a (b) j=0, a párja, az (a), majd a
               sablon többi (b)-je; a sablonok sorrendje seedelt → `kor08/adat/ertelmezes/kor2j/audit/{minta,kulcs}.jsonl`.
               A mintafájlban nincs gold és nincs állapot; az a kulcsfájlban van.
  html       — a vak lap (`atnezo.html`, átlátszatlan kulcsok a001…), utána a szivárgás-ellenőrzés: item-id, sablon-id,
               szeletnév, családnév és „(z)” nem lehet a lapon. Az (a) helyes válasza a lapon „M” (hiányzik a döntő adat).
  osszesit   — Dani exportja (`dontesek.json`) a kulccsal szemben → `kor08/eredmenyek/G1b/audit/osszesito.{json,md}`.
  --kor 2    — második auditkör (az audit06 útvonalán: `kor2j/audit/kor2/`, kulcsok b001…, összesítés `…/audit/kor2/`);
               a `minta --csak-d7` csak a D7 audit után javított forgatókönyv itemjeit veszi (Dani 11-02: az angol 02.).

A lap csak az itemből és a tervből épül: az alany döntése és bizonyossága nem kerül rá. Az első, vak választás zárolva
rögzül (`valasz`); a konstrukció csak eltéréskor látszik, a felülvizsgálat külön mező (`masodik`, `felulvizsgalt`, `megj2`).
A gold, az állapot és a tények a lap forrásában kódolva.
  python3 kor08/eszkozok/audit08e.py minta
  python3 kor08/eszkozok/audit08e.py html
  python3 kor08/eszkozok/audit08e.py osszesit --dontesek kor08/adat/ertelmezes/kor2j/audit/dontesek.json
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(EXP / "kor06/eszkozok"), str(EXP / "eszkozok")]
import audit06 as A  # noqa: E402

SZAB = "szabaly.koltsegelszamolas"
K2J = EXP / "kor08/adat/ertelmezes/kor2j"


def aud(kor: int) -> Path:
    return A.adir(kor)  # 1: `kor2j/audit`, 2: `kor2j/audit/kor2`
SEED = "audit08e:2026-11-02"
A.D = K2J
A.OUT = EXP / "kor08/eredmenyek/G1b/audit"
A.HTML = A.HTML.replace("<title>Címkeaudit 06</title>", "<title>Címkeaudit 08 G1b</title>").replace(
    '"ldh-audit06-"', '"ldh-audit08e-"')

# Dani 11-02: az első, vak választás külön rögzül, és a konstrukció megmutatása után sem írható felül; a felülvizsgált
# címke külön mező. A 06-os lapon a felfedés után az opciógombok kattinthatók maradtak (a vak választás felülíródott),
# az „Előző” pedig törölte a rekordot. Itt: a rekord az első kattintás után zárolt, az „Előző” csak lapoz; a felülvizsgálat
# `masodik` + `felulvizsgalt` + `megj2`. A gold, az állapot és a tények kódolva (`r`), hogy a forrásban ne olvashatók.
_JS = r"""function R(it){ return JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(it.r), c=>c.charCodeAt(0)))); }
const MAS = {gold_hibas:"a konstrukció hibás, a vak választásom a helyes", en_tevedtem:"én tévedtem, a konstrukció a helyes",
             ketertelmu:"kétértelmű"};
function kesz(it, d){ return !!(d && d.valasz && (d.valasz === R(it).gold || d.masodik)); }
function render(){
  const n = DATA.items.length;
  document.getElementById('cnt').textContent = `${Math.min(st.i+1,n)} / ${n}`;
  document.getElementById('pb').style.width = (100*DATA.items.filter(it=>kesz(it, st.d[it.k])).length/n)+'%';
  const app = document.getElementById('app');
  if (st.i >= n){ app.innerHTML = '<div class="card"><b>Kész.</b> Exportáld a döntéseket.</div>'; return; }
  const it = DATA.items[st.i], d = st.d[it.k];
  let h = `<div class="card"><div class="mut">${esc(it.k)}</div><div class="szoveg">${esc(it.szoveg)}</div></div>`;
  if (!d){
    h += `<div class="card"><b>${esc(it.kerdes)}</b><div style="margin-top:8px">`;
    for (const o of it.opts) if (o.l !== 'X') h += `<button class="opt" data-c="${o.l}"><b>${o.l})</b> ${esc(o.t)}</button>`;
    for (const c in ALL) h += `<button class="opt" data-c="${c}">${esc(ALL[c])}</button>`;
    h += `</div><div class="bar"><button data-c="K">Kétértelmű</button><button data-c="N">Nem tudom</button></div>
      <textarea id="megj" rows="2" placeholder="Megjegyzés (nem kötelező)"></textarea></div>`;
  } else {
    const r = R(it);
    h += `<div class="card"><b>${esc(it.kerdes)}</b><div class="mut" style="margin-top:8px">A vak választásod (rögzítve, nem
      módosítható):</div><div>${esc(cimke(it, d.valasz))}</div>${d.megj ? `<div class="mut">Megjegyzés: ${esc(d.megj)}</div>` : ''}
      ${d.valasz === r.gold ? '<div class="mut">Egyezik a konstrukcióval.</div>' : ''}</div>`;
    if (d.valasz !== r.gold){
      h += `<div class="card rev"><b>A konstrukció: ${esc(cimke(it, r.gold))}</b> <span class="mut">(állapot: ${esc(r.allapot)})</span>
        <pre>${esc(JSON.stringify(r.tenyek, null, 1))}</pre>`;
      if (d.masodik) h += `<div>Felülvizsgálat: <b>${esc(MAS[d.masodik])}</b></div>${d.megj2 ? `<div class="mut">${esc(d.megj2)}</div>` : ''}`;
      else h += `<textarea id="megj" rows="2" placeholder="Megjegyzés a felülvizsgálathoz (nem kötelező)"></textarea>
        <div class="bar"><button data-m="gold_hibas">${esc(MAS.gold_hibas)}</button><button data-m="en_tevedtem">${esc(MAS.en_tevedtem)}</button>
        <button data-m="ketertelmu">Kétértelmű</button></div>`;
      h += `</div>`;
    }
    if (kesz(it, d)) h += `<div class="bar"><button id="tovabb">Tovább →</button></div>`;
  }
  app.innerHTML = h;
  app.querySelectorAll('button[data-c]').forEach(b=>b.onclick=()=>choose(b.dataset.c));
  app.querySelectorAll('button[data-m]').forEach(b=>b.onclick=()=>second(b.dataset.m));
  const tv = document.getElementById('tovabb'); if (tv) tv.onclick=()=>{ st.i++; save(); render(); };
}
function megj(){ const t = document.getElementById('megj'); return t ? t.value.trim() : ''; }
function choose(c){
  const it = DATA.items[st.i]; if (st.d[it.k]) return;  // a vak választás egyszer rögzül
  st.d[it.k] = {valasz:c, megj:megj(), t:Date.now()};
  if (c === R(it).gold) st.i++;
  save(); render();
}
function second(m){
  const it = DATA.items[st.i], d = st.d[it.k]; if (!d || d.masodik) return;
  d.masodik = m; d.felulvizsgalt = m === 'en_tevedtem' ? R(it).gold : m === 'gold_hibas' ? d.valasz : 'K';
  d.megj2 = megj(); d.t2 = Date.now(); st.i++; save(); render();
}
document.getElementById('back').onclick=()=>{ if (st.i > 0){ st.i--; save(); render(); } };
document.getElementById('exp').onclick=()=>{
  const blob = new Blob([JSON.stringify({sig:DATA.sig, dontesek:st.d}, null, 1)], {type:'application/json'});
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'dontesek.json'; a.click();
};
document.addEventListener('keydown', e=>{
  if (e.target.tagName === 'TEXTAREA' || st.i >= DATA.items.length) return;
  const k = e.key.toUpperCase(), it = DATA.items[st.i];
  if (st.d[it.k]) return;
  if (it.opts.some(o=>o.l===k && k!=='X') || k in ALL || k==='K' || k==='N') choose(k);
});
"""
_i, _j = A.HTML.index("function render(){"), A.HTML.index("render();\n</script>")
A.HTML = A.HTML[:_i] + _JS + A.HTML[_j:]


def kodol(lap: str) -> str:
    """A lap DATA-jában a gold, az állapot és a tények egy base64-mezőbe (`r`) kerülnek."""
    eleje, veg = "const DATA = ", ";\nconst KEY"
    i = lap.index(eleje) + len(eleje)
    j = lap.index(veg, i)
    data = json.loads(lap[i:j])
    for it in data["items"]:
        r = {k: it.pop(k) for k in ("gold", "allapot", "tenyek")}
        it["r"] = base64.b64encode(json.dumps(r, ensure_ascii=False).encode()).decode()
    return lap[:i] + json.dumps(data, ensure_ascii=False) + lap[j:]


def jl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def jl_write(p: Path, rows: list[dict]) -> None:
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def cmd_minta(a) -> None:
    terv = {p["group_id"]: p for p in jl(K2J / "terv" / f"{SZAB}.jsonl")}
    items = jl(K2J / "items" / f"{SZAB}.jsonl")
    if a.csak_d7:
        items = [it for it in items if terv[it["id"]]["ertelmezes"].get("d7")]
    sablon: dict[str, list[dict]] = {}
    for it in items:
        sablon.setdefault(terv[it["id"]]["sablon_id"], []).append(it)

    def hely(it: dict) -> tuple:  # a (b) j=0, a párja (a), majd a többi (b)
        e = terv[it["id"]]["ertelmezes"]
        return (int(e["par"].rsplit(":", 1)[1]), e["alt"] != "b")

    rows, keys = [], []
    for sid in sorted(sablon, key=lambda s: hashlib.sha256(f"{SEED}:{s}".encode()).hexdigest()):
        for it in sorted(sablon[sid], key=hely):
            rows.append({k: it[k] for k in ("id", "family", "lang", "kind", "state", "question", "options")})
            keys.append({"id": it["id"], "gold": it["gold"], "content_state": it["content_state"], "split": it["split"]})
    d = aud(a.kor)
    d.mkdir(parents=True, exist_ok=True)
    jl_write(d / "minta.jsonl", rows)
    jl_write(d / "kulcs.jsonl", keys)
    print(f"minta: {len(rows)} item, {len(sablon)} sablon; "
          f"{dict(Counter((terv[r['id']]['lang'], terv[r['id']]['ertelmezes']['alt']) for r in rows))}")


def cmd_html(a) -> None:
    A.cmd_html(a)  # az audit06 útvonala: `aud(a.kor)`
    lap = aud(a.kor) / "atnezo.html"
    lap.write_text(kodol(lap.read_text(encoding="utf-8")), encoding="utf-8")
    cmd_ellenoriz(a)


def cmd_ellenoriz(a) -> None:
    d = aud(a.kor)
    lap = (d / "atnezo.html").read_text(encoding="utf-8")
    km = json.loads((d / "atnezo_kulcsok.json").read_text(encoding="utf-8"))
    minta = jl(d / "minta.jsonl")
    hibak = []
    for nev, rx in (("item-id", r":ERT2J?:"), ("sablon-id", r":k07:"), ("szelet", r"\b(CAL|TESZT|T500|ERT2J?)\b"),
                    ("„(z)”", r"\(z\)"), ("nyílt gold / állapot / tények", r'"(gold|allapot|tenyek)":'),
                    ("állapotnév", r'"(MATCH|NO_MATCH|MISSING_DATA|OUT_OF_SCOPE)"')):
        n = len(re.findall(rx, lap))
        if n:
            hibak.append(f"{nev}: {n} előfordulás")
    if SZAB in lap:
        hibak.append(f"családnév a lapon: {SZAB}")
    if list(km["kulcsok"].values()) != [m["id"] for m in minta]:
        hibak.append("a kulcsleképezés nem a minta sorrendje")
    if hibak:
        raise SystemExit("szivárgás-ellenőrzés: " + "; ".join(hibak))
    print(f"szivárgás-ellenőrzés: rendben ({len(minta)} item, sig {km['sig']})")


def cmd_osszesit(a) -> None:
    # az audit06 összesítője a `valasz` (itt: a vak választás) és a `masodik` mezőt olvassa; a felülvizsgálat utáni
    # megjegyzés a vak megjegyzés mögé kerül, jelölve
    forras = Path(a.dontesek)
    dec = json.loads(forras.read_text(encoding="utf-8"))
    for d in dec["dontesek"].values():
        if d.get("megj2"):
            d["megj"] = "; ".join(x for x in (d.get("megj", ""), f"a felülvizsgálatkor: {d['megj2']}") if x)
    tmp = aud(a.kor) / "dontesek_osszesiteshez.json"
    tmp.write_text(json.dumps(dec, ensure_ascii=False, indent=1), encoding="utf-8")
    a.dontesek, a.elozo = str(tmp), None
    A.cmd_osszesit(a)
    out = A.OUT if a.kor == 1 else A.OUT / f"kor{a.kor}"
    # a döntésfájl eredete (tények, nem ítélet): a vak választások időbélyegei és a lapformátum; a zárolt lap a
    # felülvizsgált rekordba `felulvizsgalt`-at ír, a régi nem
    rek = list(dec["dontesek"].values())
    ts = sorted(r["t"] for r in rek if "t" in r)
    ido = lambda t: datetime.fromtimestamp(t / 1000).strftime("%H:%M:%S")  # noqa: E731
    masod = [r for r in rek if r.get("masodik")]
    formatum = ("a zárolt lapé (11-02 22:47 után)" if any("felulvizsgalt" in r for r in masod) else
                "a zárolás előtti lapé" if masod else "nem dönthető el (nincs második ítélet)")
    eredet = {"fajl": forras.name, "sha256": hashlib.sha256(forras.read_bytes()).hexdigest(), "rekord": len(rek),
              "kulonbozo_idobelyeg": len(set(ts)), "elso": ido(ts[0]) if ts else None, "utolso": ido(ts[-1]) if ts else None,
              "lapformatum": formatum}
    js = out / "osszesito.json"
    js.write_text(json.dumps(json.loads(js.read_text(encoding="utf-8")) | {"eredet": eredet}, ensure_ascii=False, indent=1)
                  + "\n", encoding="utf-8")
    sor = (out / "osszesito.md").read_text(encoding="utf-8").splitlines()
    sor[0] = "# 08 G1b — a javított 2. kör címkeauditja (D7, szabálycsalád)"
    sor = sor[:1] + ["", f"A döntésfájl: `{eredet['fajl']}` (sha256 {eredet['sha256'][:12]}…), {eredet['rekord']} rekord; a vak "
                          f"választások időbélyege: {eredet['kulonbozo_idobelyeg']} különböző ({eredet['elso']}–{eredet['utolso']}); "
                          f"a rekordformátum {formatum}. A 06 D14 2%-os kapuja a 08 D7-nek nem része (3.3: a tényleges "
                          "hibaszámot közöljük, újabb példát nem generálunk); az alábbi kapusor csak a 06-os összesítő öröksége."] + sor[1:]
    (out / "osszesito.md").write_text("\n".join(sor) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("minta")
    m.add_argument("--csak-d7", action="store_true")
    h = sub.add_parser("html")
    e = sub.add_parser("ellenoriz")
    o = sub.add_parser("osszesit")
    o.add_argument("--dontesek", required=True)
    for x in (m, h, e, o):
        x.add_argument("--kor", type=int, default=1, choices=(1, 2))
    a = ap.parse_args()
    {"minta": cmd_minta, "html": cmd_html, "ellenoriz": cmd_ellenoriz, "osszesit": cmd_osszesit}[a.cmd](a)


if __name__ == "__main__":
    main()
