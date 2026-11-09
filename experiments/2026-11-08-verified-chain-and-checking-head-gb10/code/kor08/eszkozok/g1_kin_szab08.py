"""08 G1 — az alany kinyerése és a szabályalapú kinyerő (`szabkin08`) a láncon, ugyanazokon a megismert itemeken (D1: leíró
összevetés). Mindkettő ugyanazzal a lánccal (a G1 szabálycsaládi blokkjával) az orákulum-mezőkhöz mérve: a döntést
befolyásoló kinyerési hiba (`g1_lanc08.kulcs` eltér), emberhez küldés, hamis kizárás, hamis kötés, automatikus kötés;
itemszinten a kettő átfedése. Fejlesztési számok: a szabályalapú kinyerő egy hibajavító körét ezeken az adatokon
végeztem (11-03), és az alany sémája is itt fejlődött. Csak a standard könyvtár.
  python3 kor08/eszkozok/g1_kin_szab08.py --alany kor08/adat/G1/kinyeres_g1 --szabaly kor08/adat/G1/kinyeres_szabaly \
      --blokk v4 --out kor08/eredmenyek/G1
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import g1_lanc08 as GL  # noqa: E402
import lanc08 as L  # noqa: E402

UTAK = ("alany", "szabály")


def tetel(fam: str, it: dict, mezok: list | None, ora_k: tuple, blokk: str) -> dict:
    r = L.lanc(fam, it, mezok, valtozat=blokk)
    st, g = it["content_state"], it["gold"]
    emberhez = r["kimenet"] == "emberhez"  # az emberhez küldött tétel nem átengedés (mint a `g1_lanc08`-ban)
    return {"emberhez": emberhez, "hiba": not emberhez and GL.kulcs(r) != ora_k,
            "hamis_kizaras": st == "MATCH" and g in r["kizart"],
            "hamis_kotes": r["kimenet"] == "kotes" and (st != "MATCH" or r["kotes"] != g), "kotes": r["kimenet"] == "kotes"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--alany", required=True)
    ap.add_argument("--szabaly", required=True)
    ap.add_argument("--blokk", default="v4", choices=L.BLOKK_VALTOZAT)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    res: dict = {}
    for src in L.ONTESZT:
        for fam in L.CSALADOK:
            kin = {u: {r["id"]: r["mezok"] for r in L.jsonl(L.EXP / d / f"{src}_{fam}.jsonl")}
                   for u, d in zip(UTAK, (a.alany, a.szabaly))}
            c: dict[str, Counter] = {u: Counter() for u in UTAK}
            atfedes = Counter()
            for terv, it in L.betolt(src, fam):
                if not all(it["id"] in kin[u] for u in UTAK):
                    continue
                ora_k = GL.kulcs(L.lanc(fam, it, L.orakulum(fam, terv, it), valtozat=a.blokk))
                t = {u: tetel(fam, it, kin[u][it["id"]], ora_k, a.blokk) for u in UTAK}
                for u in UTAK:
                    c[u]["n"] += 1
                    c[u].update(k for k, v in t[u].items() if v)
                atfedes[f"alany {'hibás' if t['alany']['hiba'] else 'jó'} · szabály {'hibás' if t['szabály']['hiba'] else 'jó'}"] += 1
            res[f"{src}|{fam}"] = {"utak": {u: dict(c[u]) for u in UTAK}, "atfedes": dict(atfedes)}
    out = L.EXP / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "kinyero_osszevetes.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out / "kinyero_osszevetes.md").write_text(lap(res, a.blokk), encoding="utf-8")
    print(lap(res, a.blokk))


def lap(res: dict, blokk: str) -> str:
    def pc(x: int, n: int) -> str:
        return f"{x} ({100 * x / n:.1f}%)".replace(".", ",") if n else "–"
    L_ = [f"# G1 — az alany kinyerése és a szabályalapú kinyerő a láncon (D1, leíró; blokk {blokk})", "",
          "Mindkét kinyerés ugyanazzal a lánccal, az orákulum-mezőkhöz mérve. Döntést befolyásoló hiba: a lánc kimenete, "
          "a megmaradt jelöltek, az automatikus kötés vagy a modellnek mutatott ellenőrzött adat eltér az orákulum-útétól. "
          "Fejlesztési számok: a szabályalapú kinyerő egy hibajavító köre ezeken az adatokon készült.", "",
          "| forrás | család | n | döntést befolyásoló hiba (átment): alany / szabály | emberhez: alany / szabály | hamis kizárás: "
          "alany / szabály | hamis kötés: alany / szabály | automatikus kötés: alany / szabály | mindkettő hibás | csak az "
          "alany | csak a szabály |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, r in res.items():
        src, fam = k.split("|")
        u, s, at = r["utak"]["alany"], r["utak"]["szabály"], r["atfedes"]
        n = u.get("n", 0)
        # a nevező az átengedett tételek száma (hamis átengedés, 2.2), mint a `g1_lanc08`-ban
        L_.append(f"| {src} | {fam} | {n} | {pc(u.get('hiba', 0), n - u.get('emberhez', 0))} / "
                  f"{pc(s.get('hiba', 0), n - s.get('emberhez', 0))} | "
                  f"{u.get('emberhez', 0)} / {s.get('emberhez', 0)} | {u.get('hamis_kizaras', 0)} / {s.get('hamis_kizaras', 0)} | "
                  f"{u.get('hamis_kotes', 0)} / {s.get('hamis_kotes', 0)} | {u.get('kotes', 0)} / {s.get('kotes', 0)} | "
                  f"{at.get('alany hibás · szabály hibás', 0)} | {at.get('alany hibás · szabály jó', 0)} | "
                  f"{at.get('alany jó · szabály hibás', 0)} |")
    return "\n".join(L_) + "\n"


if __name__ == "__main__":
    main()
