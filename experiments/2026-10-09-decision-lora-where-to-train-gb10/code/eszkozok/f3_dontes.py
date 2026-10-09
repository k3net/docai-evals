"""F3 — az előre rögzített győztes-választás (runbook 9. F3) és a következő szakasz karjai.

Szabály (2026-10-05, a pilot előtt rögzítve): az L3 `temp` karja a vLLM val-on. Sorrend: lefedettség@95,
holtversenyben (< 2 pont) a lefedettség@90, holtversenyben (< 2 pont) a kisebb AURC.
Fake-quant (user-döntés 2026-10-05, a 3. pilot-kar eredménye előtt): csak akkor megy tovább, ha a fake-quantos
`L3-mix` ugyanezzel a sorrenddel EGYÉRTELMŰEN jobb, és az AURC-ben is csak 0,001-nél nagyobb eltérés számít;
holtversenyben az olcsóbb, fake-quant nélküli ág marad (az fp32 fake-quant ~5× lassabban tanul).

  python3 eszkozok/f3_dontes.py karok hangolas      # → eredmenyek/F3/pilot_dontes.json + a hangolási karok
  python3 eszkozok/f3_dontes.py karok megerosites   # → eredmenyek/F3/hangolas_dontes.json + a seed 2, 3 karok
  python3 eszkozok/f3_dontes.py onteszt
A `karok` a stdout-ra a vezénylő KAROK-sorait írja: név|célmodulok|fake-quant|további tréning-kapcsolók.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import EXP, write_json  # noqa: E402

R = EXP / "eredmenyek/F3"
TIE = 0.02
FQ_AURC_TIE = 0.001  # csak a fake-quant-döntésben (user-döntés, 2026-10-05)
PILOT = {  # kar: (célmodulok, fake-quant, további kapcsolók)
    "l3mix_s1": ("mix", "none", ""),
    "l3mixse_s1": ("mix+se", "none", ""),
    "l3mixfq_s1": ("mix", "fp32", ""),
}
# előre rögzítve (2026-10-05, a pilot előtt): a pilot-győztes célmodul-készletén, 1 seed
TUNING = {"h1": "--lr 2e-4", "h2": "--eps 0.05", "h3": "--epochs 2"}


def score(arm: str) -> dict:
    d = json.loads((R / arm / "L3_vllm_val.json").read_text())["karok"]["temp"]
    return {"lef95": d["val"]["besorolasi_lefedettseg"], "lef90": d["at90"]["val"]["besorolasi_lefedettseg"],
            "aurc": d["val"]["aurc"]}


def compare(a: dict, b: dict, aurc_tie: float = 0.0) -> tuple[int, str]:
    """+1: a jobb, −1: b jobb, 0: teljes holtverseny. A második elem a döntő mérce."""
    for k in ("lef95", "lef90"):
        if abs(a[k] - b[k]) >= TIE:
            return (1 if a[k] > b[k] else -1), k
    if abs(a["aurc"] - b["aurc"]) > aurc_tie:
        return (1 if a["aurc"] < b["aurc"] else -1), "aurc"
    return 0, "holtverseny"


def best(arms: list[str]) -> tuple[str, list[dict]]:
    sc = {a: score(a) for a in arms}
    win, log = arms[0], []
    for a in arms[1:]:
        c, by = compare(sc[a], sc[win])
        log.append({"kihivo": a, "vedo": win, "dont": by, "kihivo_nyer": c > 0})
        if c > 0:
            win = a
    return win, [{"pontok": sc}, *log]


def tag(tg: str, fq: str) -> str:
    return "l3" + tg.replace("+", "") + ("fq" if fq != "none" else "")


def pilot_decision() -> dict:
    tg_win, tg_log = best(["l3mix_s1", "l3mixse_s1"])
    c, by = compare(score("l3mixfq_s1"), score("l3mix_s1"), aurc_tie=FQ_AURC_TIE)
    fq = "fp32" if c > 0 else "none"
    tg = PILOT[tg_win][0]
    res = {"celmodul_gyoztes": tg_win, "celmodulok": tg, "fakequant": fq,
           "fakequant_osszevetes": {"dont": by, "fq_egyertelmuen_jobb": c > 0, "aurc_holtverseny_sav": FQ_AURC_TIE},
           "celmodul_osszevetes": tg_log, "alap_kar": tg_win}
    write_json(R / "pilot_dontes.json", res)
    return res


def tuning_lines() -> list[str]:
    p = pilot_decision()
    t = tag(p["celmodulok"], p["fakequant"])
    return [f"{t}_{h}_s1|{p['celmodulok']}|{p['fakequant']}|--seed 1 {x}" for h, x in TUNING.items()]


def confirm_lines() -> list[str]:
    p = json.loads((R / "pilot_dontes.json").read_text())
    t = tag(p["celmodulok"], p["fakequant"])
    cand = {p["alap_kar"]: ""} | {f"{t}_{h}_s1": x for h, x in TUNING.items()}
    win, log = best(list(cand))
    extra, tg, fq = cand[win], p["celmodulok"], p["fakequant"]
    # a pilot-kar nyert → a konfig a pilot-döntés fake-quantjával; különben a hangolási kar neve
    name = tag(tg, fq) if win == p["alap_kar"] else win.rsplit("_s", 1)[0]
    # a H1 három seedje: ha a konfig seed 1-es tagja még nem futott (pl. mix+se fake-quanttal), az is ide kerül
    seeds = [s for s in (1, 2, 3) if s > 1 or not (R / f"{name}_s1" / "L3_vllm_val.json").exists()]
    write_json(R / "hangolas_dontes.json", {"gyoztes_kar": win, "konfig": name, "celmodulok": tg, "fakequant": fq,
                                            "kapcsolok": extra, "seedek": seeds, "osszevetes": log})
    return [f"{name}_s{s}|{tg}|{fq}|--seed {s} {extra}".rstrip() for s in seeds]


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    k = sub.add_parser("karok")
    k.add_argument("szakasz", choices=["hangolas", "megerosites"])
    sub.add_parser("onteszt")
    args = ap.parse_args()
    if args.cmd == "onteszt":
        assert compare({"lef95": .75, "lef90": .76, "aurc": .002}, {"lef95": .76, "lef90": .76, "aurc": .001}) == (-1, "aurc")
        assert compare({"lef95": .80, "lef90": .70, "aurc": .009}, {"lef95": .76, "lef90": .76, "aurc": .001}) == (1, "lef95")
        assert compare({"lef95": .75, "lef90": .79, "aurc": .009}, {"lef95": .76, "lef90": .76, "aurc": .001}) == (1, "lef90")
        assert compare({"lef95": .75, "lef90": .76, "aurc": .001}, {"lef95": .76, "lef90": .76, "aurc": .001}) == (0, "holtverseny")
        assert compare({"lef95": .75, "lef90": .76, "aurc": .0009}, {"lef95": .76, "lef90": .76, "aurc": .0012}, .001) == (0, "holtverseny")
        assert compare({"lef95": .75, "lef90": .76, "aurc": .0009}, {"lef95": .76, "lef90": .76, "aurc": .0021}, .001) == (1, "aurc")
        assert tag("mix+se", "fp32") == "l3mixsefq" and tag("mix", "none") == "l3mix"
        print("ok")
        return
    lines = tuning_lines() if args.szakasz == "hangolas" else confirm_lines()
    print("\n".join(lines))


if __name__ == "__main__":
    main()
