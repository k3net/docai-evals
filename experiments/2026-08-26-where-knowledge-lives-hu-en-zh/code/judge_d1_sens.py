#!/usr/bin/env python3
"""A keretezési érzékenységvizsgálat válaszainak bírálata — UGYANAZZAL a rubrikával, mint a D1.

    python3 code/judge_d1_sens.py

Fontos, hogy a rubrika és a modell azonos legyen a D1-gyel, különben nem a keretezést
mérnénk, hanem a bírálót. Ezért a `judge_d1`-ből importáljuk a rubrikát és a hívást.
"""
import json
import pathlib

from judge_d1 import RUBRIKA_UNT, call, parse
import scope_paths


HERE = pathlib.Path(__file__).resolve().parent.parent
RES = scope_paths.res(HERE)


def main():
    items = {json.loads(l)["id"]: json.loads(l) for l in
             (scope_paths.data(HERE, "items.jsonl")).read_text(encoding="utf-8").splitlines() if l.strip()}
    files = sorted((RES / "gen_sens").glob("*.json"))
    out = []
    for f in files:
        g = json.loads(f.read_text(encoding="utf-8"))
        it = items[g["item_id"]]
        user = (f"Fogalom: {it['concept']} (forrásnyelv: {it['src_lang']})\n"
                f"Kötelező jelentéskomponensek:\n"
                + "\n".join(f"  {i+1}. {c}" for i, c in enumerate(it["native"])) + "\n"
                f"Torzítás-jelek:\n"
                + "\n".join(f"  {i+1}. {c}" for i, c in enumerate(it["distortion"])) + "\n\n"
                f"A modell válasza (zh):\n{g['text']}\n"
                + ("\nMegjegyzés: a válasz elvágódott a token-keretnél.\n" if g["truncated"] else ""))
        d = parse(call([{"role": "system", "content": RUBRIKA_UNT}, {"role": "user", "content": user}]))
        ok = d and isinstance(d.get("native"), list)
        rec = {"item_id": g["item_id"], "concept": it["concept"],
               "native_hit": sum(bool(x) for x in d["native"][:len(it["native"])]) if ok else None,
               "native_n": len(it["native"]),
               "distortion_hit": sum(bool(x) for x in d["distortion"][:len(it["distortion"])]) if ok else None,
               "distortion_n": len(it["distortion"]),
               "indoklas": (d.get("indoklas") if d else "")[:300],
               "truncated": g["truncated"], "text": g["text"][:600]}
        out.append(rec)
        print(f"  {rec['item_id']} ({rec['concept']}): native {rec['native_hit']}/{rec['native_n']}", flush=True)

    (RES / "d1_sens_judge.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"→ {RES / 'd1_sens_judge.json'} ({len(out)} fogalom)")


if __name__ == "__main__":
    main()
