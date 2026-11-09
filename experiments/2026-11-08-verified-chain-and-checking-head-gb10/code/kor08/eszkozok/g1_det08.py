"""08 G1 — determinizmus-próba (Dani 11-03): billen-e a HF-kiolvasás futásonként bájtra azonos bemeneten (a K08G1B2K-ban
egy HU (b)-item rosszról helyesre váltott). A szabálycsalád v1 T500-kiolvasása (`o06`, K08G1A3) és a javított 2. kör
(`oERT2J`, K08G1B2K) újraolvasva külön cache-be (`--uj`), itemszintű összevetés a régivel: soronként a bemenet (sorrend,
címkék, prompt-tokenszám), a pred és a címke-logprobok; itemenként a B1-4S döntés és a helyesség
(`g1_dontes08.helyes`); a T500-on a v4 ↔ v1 javult / romlott a régi és az új v1-kiolvasással (a blokkválasztás 11 / 9-e
mennyiben zaj).
  python3 kor08/eszkozok/g1_det08.py --regi cache/k08/jellemzok --uj cache/k08/jellemzok_det --out kor08/eredmenyek/G1
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE), str(EXP / "kor07/eszkozok")]
import b1rel07 as R  # noqa: E402
import g1_dontes08 as G  # noqa: E402
import lanc08 as L  # noqa: E402

FAM = L.SZAB
MINTAK = {"T500": ("06", "T500", "o06"), "ERT2J": ("ERT2J", "ERT2J", "oERT2J")}  # minta → (forrás, szelet, előtag)


def sorok(regi: dict, uj: dict) -> dict:
    """Soronként (id, perm): azonos-e a bemenet és a pred, és mennyi a címke-logprobok legnagyobb eltérése."""
    a = {(r["id"], r["perm"]): r for rs in regi.values() for r in rs}
    b = {(r["id"], r["perm"]): r for rs in uj.values() for r in rs}
    if a.keys() != b.keys():
        raise SystemExit(f"a sorok kulcsai eltérnek: {len(a.keys() ^ b.keys())}")
    bem = sum(a[k]["order"] != b[k]["order"] or a[k]["labels"] != b[k]["labels"]
              or a[k]["n_prompt_tokens"] != b[k]["n_prompt_tokens"] for k in a)
    dm = [max(abs(a[k]["label_logprobs"][c] - b[k]["label_logprobs"][c]) for c in a[k]["label_logprobs"]) for k in a]
    return {"n": len(a), "bemenet_elter": bem, "pred_elter": sum(a[k]["pred"] != b[k]["pred"] for k in a),
            "logprob_azonos": sum(d == 0 for d in dm), "max_delta_median": statistics.median(dm),
            "max_delta_max": max(dm)}


def dontesek(src: str, szelet: str, by: dict, temp: float) -> dict[str, dict]:
    out = {}
    for _, it in L.betolt(src, FAM):
        if it["split"] != szelet or it["id"] not in by:
            continue
        d = R.decide4(by[it["id"]], temp)
        out[it["id"]] = {"ok": G.helyes(d, it["content_state"], it.get("gold")), "allapot": it["content_state"],
                         "dontes": f"SELECT {d['cand']}" if d["kind"] == "SELECT" else d["kind"], "gap": d["gap"]}
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--regi", default="cache/k08/jellemzok")
    ap.add_argument("--uj", default="cache/k08/jellemzok_det")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    temp = json.loads((EXP / "cache/k07/fejek/temperature.json").read_text())["B1-4"]
    res: dict = {}
    sor = ["# G1 — determinizmus-próba: a kiolvasás újra, bájtra azonos bemeneten (szabálycsalád, orákulum-út, B1-4S)", "",
           "A régi kiolvasás: `o06` (K08G1A3, 11-02), `oERT2J` (K08G1B2K, 11-03); az új külön cache-ben, ugyanazzal a",
           "kóddal, konténerrel és itemfájllal (az itemfájlok sha256-ja a futtató naplójában). HF, batch 1, itemenként.", ""]
    for minta, (src, szelet, elo) in MINTAK.items():
        pre = f"{elo}_{FAM}_{szelet}"
        ra, rb = R.rows4(pre, EXP / a.regi), R.rows4(pre, EXP / a.uj)
        s = sorok(ra, rb)
        da, db = dontesek(src, szelet, ra, temp), dontesek(src, szelet, rb, temp)
        elter = sorted(i for i in da if da[i]["dontes"] != db[i]["dontes"])
        r = {"sorok": s, "itemek": len(da), "dontes_elter": len(elter),
             "helyes_regi": sum(x["ok"] for x in da.values()), "helyes_uj": sum(x["ok"] for x in db.values()),
             "rosszbol_jo": sum(db[i]["ok"] and not da[i]["ok"] for i in da),
             "jobol_rossz": sum(da[i]["ok"] and not db[i]["ok"] for i in da),
             "eltero_itemek": [{"id": i, "allapot": da[i]["allapot"], "regi": da[i]["dontes"], "uj": db[i]["dontes"],
                                "ok_regi": da[i]["ok"], "ok_uj": db[i]["ok"], "gap_regi": da[i]["gap"],
                                "gap_uj": db[i]["gap"]} for i in elter]}
        sor += [f"## {minta} (n = {len(da)})", "",
                f"- Sorok (item × 4 sorrend): {s['n']}; bemenet eltér: {s['bemenet_elter']}; pred eltér: "
                f"{s['pred_elter']}; a címke-logprobok bitre azonosak: {s['logprob_azonos']}; a soronkénti legnagyobb "
                f"eltérés mediánja {s['max_delta_median']:.4f}, maximuma {s['max_delta_max']:.4f}.",
                f"- Itemek: a döntés eltér {len(elter)}; helyes régi / új: {r['helyes_regi']} / {r['helyes_uj']}; "
                f"rosszból jó {r['rosszbol_jo']}, jóból rossz {r['jobol_rossz']}."]
        if minta == "T500":
            d4 = dontesek(src, szelet, R.rows4(f"o06v4_{FAM}_{szelet}", EXP / a.regi), temp)
            for nev, d1 in (("régi", da), ("új", db)):
                r[f"v4 ↔ {nev} v1"] = {"javult": sum(d4[i]["ok"] and not d1[i]["ok"] for i in d1),
                                       "romlott": sum(d1[i]["ok"] and not d4[i]["ok"] for i in d1)}
            v14 = {i for i in da if da[i]["ok"] != d4[i]["ok"]}
            r["v1_v4_kulonbseg"] = len(v14)
            r["v1_v4_kulonbseg_billent"] = sorted(v14 & set(elter))
            sor.append("- A blokkválasztás: " + "; ".join(
                f"v4 ↔ {nev} v1: javult {r[f'v4 ↔ {nev} v1']['javult']}, romlott {r[f'v4 ↔ {nev} v1']['romlott']}"
                for nev in ("régi", "új")) + f". A v1 ↔ v4 helyesség-különbség {len(v14)} itemjéből "
                f"{len(r['v1_v4_kulonbseg_billent'])} döntése a két v1-futás között is eltér.")
        if elter:
            sor += ["", "| item | állapot | régi döntés | új döntés | helyes régi → új | gap régi / új |",
                    "|---|---|---|---|---|---|"]
            sor += [f"| `{x['id']}` | {x['allapot']} | {x['regi']} | {x['uj']} | {'i' if x['ok_regi'] else 'n'} → "
                    f"{'i' if x['ok_uj'] else 'n'} | {x['gap_regi']:.3f} / {x['gap_uj']:.3f} |"
                    for x in r["eltero_itemek"]]
        sor.append("")
        res[minta] = r
    out = EXP / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "determinizmus.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out / "determinizmus.md").write_text("\n".join(sor) + "\n", encoding="utf-8")
    print("\n".join(sor))


if __name__ == "__main__":
    main()
