"""08 G1 — a lánc pontossága a megismert szeleteken: ugyanaz a lánc a valós kinyeréssel (`kinyer08`) és az
orákulum-mezőkkel (08-runbook 2.2, 3.4). Tervezési számok. Csak a standard könyvtár.

  döntést befolyásoló kinyerési hiba   a lánc kimenete (kimenet, megmaradt jelöltek, automatikus kötés, a modellnek
                                       mutatott ellenőrzött adatok) a két úton eltér
  hamis átengedés                      a döntést befolyásoló hiba aránya azokon, ahol az ellenőrzés átment
  hamis kizárás / hamis kötés          a gold kizárva, illetve az automatikus kötés nem a goldra
  mezőszintű pontosság                 szerepenként (és a mérésnél kapcsolatonként) helyes / rossz érték / hiányzó / többlet

  python3 kor08/eszkozok/g1_lanc08.py --kinyeres kor08/adat/G1/kinyeres --out kor08/eredmenyek/G1
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lanc08 as L  # noqa: E402


def kulcs(res: dict) -> tuple:
    return (res["kimenet"], tuple(sorted(res["megmaradt"])), res["kotes"], res["blokk"])


def mezok_osszevetese(kin: list[dict], ora: list[dict], c: Counter) -> None:
    def k(f):
        return (f["szerep"], L.norm(str(f.get("kapcsolat") or "")) if f["szerep"] == "meres" else "")
    ok = defaultdict(list)
    for f in ora:
        ok[k(f)].append(f)
    kk = defaultdict(list)
    for f in kin:
        if isinstance(f, dict) and "szerep" in f:
            kk[k(f)].append(f)
    for key in set(ok) | set(kk):
        sz = key[0]
        a, b = ok.get(key, []), kk.get(key, [])
        for i in range(max(len(a), len(b))):
            if i >= len(b):
                c[(sz, "hiányzó")] += 1
            elif i >= len(a):
                c[(sz, "többlet")] += 1
            else:
                x, y = a[i]["ertek"], b[i]["ertek"]
                if sz in L.SZOVEGES:
                    same = L.norm_ref(str(x)) == L.norm_ref(str(y)) if sz == "hivatkozas" else L.norm(str(x)) == L.norm(str(y))
                else:
                    vx, vy = L._ertek(x, "en" if "." in str(x) else "hu"), L._ertek(y, "hu" if "," in str(y) else "en")
                    same = vx is not None and vy is not None and L.egyezik(abs(vx), abs(vy), 1e-6)
                c[(sz, "helyes" if same else "rossz érték")] += 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kinyeres", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--blokk", default="v0", choices=L.BLOKK_VALTOZAT)  # a szabálycsalád blokkjának változata
    a = ap.parse_args()
    kd = Path(a.kinyeres) if Path(a.kinyeres).is_absolute() else L.EXP / a.kinyeres
    res: dict = {}
    for src in L.FORRASOK:
        for fam in L.CSALADOK:
            p = kd / f"{src}_{fam}.jsonl"
            if not p.exists():
                continue
            kin = {r["id"]: r for r in L.jsonl(p)}
            c = Counter()
            ki, ok_, bukas, mez, elv = Counter(), Counter(), Counter(), Counter(), Counter()
            for terv, it in L.betolt(src, fam):
                if it["id"] not in kin:
                    continue
                r_k = L.lanc(fam, it, kin[it["id"]]["mezok"], valtozat=a.blokk)
                ora = L.orakulum(fam, terv, it)
                r_o = L.lanc(fam, it, ora, valtozat=a.blokk)
                st, g = it["content_state"], it["gold"]
                c["n"] += 1
                ki[f"{st}|{r_k['kimenet']}"] += 1
                ok_[f"{st}|{r_o['kimenet']}"] += 1
                for f in r_k["bukott"]:
                    bukas[f.get("ok", "?")] += 1
                for f in r_k.get("elvetett", []):
                    elv[f"{f.get('szerep')}: {f.get('ok', '?')}"] += 1
                if r_k.get("elvetett"):
                    c["elvetett mezős tétel"] += 1
                if kin[it["id"]]["mezok"] is None:
                    c["értelmezhetetlen kinyerés"] += 1
                if r_k["kimenet"] == "emberhez":
                    c["emberhez"] += 1
                else:
                    c["ellenőrzés átment"] += 1
                    if kulcs(r_k) != kulcs(r_o):
                        c["döntést befolyásoló kinyerési hiba (átment)"] += 1
                if kulcs(r_k) != kulcs(r_o):
                    c["a két út kimenete eltér"] += 1
                if st == "MATCH" and g in r_k["kizart"]:
                    c["hamis kizárás (a gold)"] += 1
                if r_k["kimenet"] == "kotes" and (st != "MATCH" or r_k["kotes"] != g):
                    c["hamis automatikus kötés"] += 1
                if r_k["kimenet"] == "kotes":
                    c["automatikus kötés"] += 1
                if r_o["kimenet"] == "kotes":
                    c["automatikus kötés (orákulum)"] += 1
                if isinstance(kin[it["id"]]["mezok"], list):
                    mezok_osszevetese(kin[it["id"]]["mezok"], ora, mez)
            atment = c["ellenőrzés átment"]
            c_: dict = dict(c)
            c_["hamis átengedés"] = round(c["döntést befolyásoló kinyerési hiba (átment)"] / atment, 4) if atment else None
            c_["emberhez arány"] = round(c["emberhez"] / c["n"], 4) if c["n"] else None
            res[f"{src}|{fam}"] = {"szamok": c_, "kimenet_kinyert": dict(sorted(ki.items())),
                                   "kimenet_orakulum": dict(sorted(ok_.items())), "bukasok": dict(bukas.most_common()),
                                   "elvetett": dict(elv.most_common()), "mezok": {f"{k[0]}|{k[1]}": v for k, v in sorted(mez.items())}}
    out = Path(a.out) if Path(a.out).is_absolute() else L.EXP / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "lanc_pontossag.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out / "lanc_pontossag.md").write_text(lap(res), encoding="utf-8")
    print(lap(res))


def lap(res: dict) -> str:
    L_ = ["# G1 — a lánc pontossága valós és orákulum-kinyeréssel (tervezési számok, megismert adat)", "",
          "| forrás | család | n | emberhez | ellenőrzés átment | döntést befolyásoló hiba (átment) | hamis átengedés | "
          "hamis kizárás | hamis kötés | automatikus kötés: valós / orákulum |", "|---|---|---|---|---|---|---|---|---|---|"]
    for k, R in res.items():
        s = R["szamok"]
        src, fam = k.split("|")
        ha = "–" if s["hamis átengedés"] is None else f"{100 * s['hamis átengedés']:.1f}%".replace(".", ",")
        L_.append(f"| {src} | {fam} | {s['n']} | {s.get('emberhez', 0)} | {s.get('ellenőrzés átment', 0)} | "
                  f"{s.get('döntést befolyásoló kinyerési hiba (átment)', 0)} | {ha} | "
                  f"{s.get('hamis kizárás (a gold)', 0)} | {s.get('hamis automatikus kötés', 0)} | "
                  f"{s.get('automatikus kötés', 0)} / {s.get('automatikus kötés (orákulum)', 0)} |")
    L_ += ["", "## Az emberhez küldés okai", ""]
    for k, R in res.items():
        if R["bukasok"]:
            L_.append(f"- **{k}:** " + "; ".join(f"{o} {n}" for o, n in list(R["bukasok"].items())[:6]))
    L_ += ["", "## Elvetett mezők (az ellenőrzésen bukott, a tétel ettől még a láncban marad)", ""]
    for k, R in res.items():
        if R["elvetett"]:
            L_.append(f"- **{k}:** " + "; ".join(f"{o} {n}" for o, n in list(R["elvetett"].items())[:6]))
    L_ += ["", "## Mezőszintű pontosság (az orákulumhoz mérve)", ""]
    for k, R in res.items():
        L_.append(f"- **{k}:** " + "; ".join(f"{m} {n}" for m, n in R["mezok"].items()))
    return "\n".join(L_) + "\n"


if __name__ == "__main__":
    main()
