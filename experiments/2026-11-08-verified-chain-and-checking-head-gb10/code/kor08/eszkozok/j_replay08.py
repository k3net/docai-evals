"""08 javító kör (J; nem rögzített) — a `lanc08j` a meglévő kinyerési kimeneteken, GPU nélkül: a rögzített lánc és a javított lánc
ugyanazon a kinyerésen, az orákulum-úthoz mérve (a `g5_k2_08` definíciójával). Fejlesztési szám: ezek a szeletek már nyitottak, a
javítás rájuk készült. Előbb az ellenőrzés: a rögzített lánc itt pontosan a G3 tárolt kimenetét adja-e.

  python3 kor08/eszkozok/j_replay08.py --out kor08/eredmenyek/J/replay.md
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent)]
import lanc08 as L  # noqa: E402
import lanc08j as J  # noqa: E402

G3 = L.EXP / "kor08/adat/G3"
BLOKK = "v4"


def kulcs(it: dict, r: dict) -> tuple:
    if r["kimenet"] == "modell":
        u = L.uj_item(it, r)
        m = (u["state"], json.dumps(u["options"], ensure_ascii=False))
    else:
        m = None
    return (r["kimenet"], tuple(sorted(r["megmaradt"])), r["kotes"], m)


def szamol(parok: list, kin: dict, ora: dict, jav: bool) -> tuple[Counter, dict]:
    (J.aktival if jav else J.kikapcsol)()
    c, ki = Counter(), {}
    for p, it in parok:
        i, st, g = it["id"], it["content_state"], it["gold"]
        r = L.lanc(p["_fam"], it, kin.get(i), valtozat=BLOKK)
        o = ora[i]
        ki[i] = r
        c["n"] += 1
        c["kotes"] += r["kimenet"] == "kotes"
        c["emberhez"] += r["kimenet"] == "emberhez"
        c["elvetett tetel"] += bool(r.get("elvetett"))
        c["elvetett mezo"] += len(r.get("elvetett") or [])
        c["hamis kizaras"] += st == "MATCH" and g in r["kizart"]
        c["hamis kotes"] += r["kimenet"] == "kotes" and not (st == "MATCH" and r["kotes"] == g)
        if r["kimenet"] == "emberhez":
            continue
        c["atment"] += 1
        if kulcs(it, r) != kulcs(it, o):
            c["dbh"] += 1
            c["tobbet zar ki"] += bool(set(r["kizart"]) - set(o["kizart"]))
    return c, ki


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    sorok = ["# 08 javító kör — a lánc a meglévő kinyerésen (fejlesztési szám)", "",
             "Hamis átengedés a `g5_k2_08` definíciójával; R: a rögzített lánc, J: `lanc08j`. Ezek a szeletek nyitottak, a javítás rájuk készült.", "",
             "| forrás | család | n | hamis átengedés R | J | elvetett mező R | J | emberhez R | J | hamis kizárás R / J | hamis kötés R / J | többet zár ki R / J | új eltérés | kötés R / J |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    pelda = []
    for src in ("G2K3", "G2F", "G2T"):
        for fam in L.CSALADOK:
            parok = [({**p, "_fam": fam}, it) for p, it in L.betolt(src, fam)]
            kin = {r["id"]: r["mezok"] for r in L.jsonl(G3 / f"kinyeres/{src}_{fam}.jsonl")}
            J.kikapcsol()
            ora = {it["id"]: L.lanc(fam, it, L.orakulum(fam, p, it), valtozat=BLOKK) for p, it in parok}
            r, kr = szamol(parok, kin, ora, False)
            tarolt = {x["id"]: x for x in L.jsonl(G3 / f"kinyert_{src}/lanc_{fam}.jsonl")}
            elt = sum((kr[i]["kimenet"], sorted(kr[i]["megmaradt"]), kr[i]["kotes"]) != (t["kimenet"], sorted(t["megmaradt"]), t["kotes"])
                      for i, t in tarolt.items())
            if elt:
                raise SystemExit(f"a rögzített lánc nem a tárolt kimenetet adja: {src} {fam}: {elt}")
            j, kj = szamol(parok, kin, ora, True)
            J.kikapcsol()
            uj = 0
            for p, it in parok:
                i = it["id"]
                if kj[i]["kimenet"] == "emberhez":
                    continue
                if kulcs(it, kj[i]) != kulcs(it, ora[i]) and (kr[i]["kimenet"] == "emberhez" or kulcs(it, kr[i]) == kulcs(it, ora[i])):
                    uj += 1
                    pelda.append((src, i, kj[i]["kimenet"], ora[i]["kimenet"], kj[i]["kizart"], ora[i]["kizart"], kj[i]["szamitott"], ora[i]["szamitott"]))
            pc = lambda c: f"{c['dbh']}/{c['atment']} = {100 * c['dbh'] / max(c['atment'], 1):.1f}%".replace(".", ",")
            sorok.append(f"| {src} | {fam} | {r['n']} | {pc(r)} | {pc(j)} | {r['elvetett mezo']} | {j['elvetett mezo']} | {r['emberhez']} | {j['emberhez']} | "
                         f"{r['hamis kizaras']} / {j['hamis kizaras']} | {r['hamis kotes']} / {j['hamis kotes']} | {r['tobbet zar ki']} / {j['tobbet zar ki']} | {uj} | {r['kotes']} / {j['kotes']} |")
    J.aktival()
    zav = L.zavarasok()
    J.kikapcsol()
    zav0 = L.zavarasok()
    sorok += ["", "## Az ellenőrzés zavarópróbája (`lanc08.zavarasok`)", "", "| próba | R | J |", "|---|---|---|"]
    sorok += [f"| {k} | {zav0.get(k)} | {zav.get(k)} |" for k in zav0]
    sorok += ["", "## Új eltérések (a javítás hozta be)", ""] + [f"- `{x}`" for x in pelda[:30]]
    o = L.EXP / a.out
    o.parent.mkdir(parents=True, exist_ok=True)
    o.write_text("\n".join(sorok) + "\n", encoding="utf-8")
    print("\n".join(sorok))


if __name__ == "__main__":
    main()
