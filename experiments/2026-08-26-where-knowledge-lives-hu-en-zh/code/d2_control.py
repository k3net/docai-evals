#!/usr/bin/env python3
"""D2 utólagos kontrollok: mennyit ér a „0/32" null-eredmény?

A dolgozat adverszáriális átolvasása (2026-08-25) három lyukat talált a D2-ben:
  1. NINCS POZITÍV KONTROLL — sosem mértük meg, hogy az ANGOL prompton (ahol a
     közelítőszó bizonyosan releváns) a műszer egyáltalán előhozza-e a szót.
  2. NINCS ELÉRHETŐSÉGI NEVEZŐ — több fogalom jelöltszava a teljes korpusz EGYETLEN
     top-20 olvasatában sem fordul elő; ezeknél a találat szerkezetileg lehetetlen,
     mégis benne vannak a 0/32 nevezőjében.
  3. A MATCHER ÍRÁSJEL-ÉRZÉKENY — az `analyze_d.py` szó szerinti egyezést vár, és a
     jelöltlistában `distinction)`, `'you'`, `(t–v` alakok maradnak, amik sosem
     egyezhetnek. Tisztított matcherrel az eredmény változhat.

Ez a szkript mindhármat megméri MINDKÉT lencsére, és riportot ír:
    python3 src/d2_control.py          → reports/05_d2_kontroll.md
(Körváltás a szokásos SCOPE_RES/SCOPE_REPORTS változókkal — ld. scope_paths.py.)

⛔ A tanulság a dolgozat 7. fejezetében: a 0/32 GYENGE evidencia — a pozitív
kontroll szerint a műszer az angol prompton is csak 3/16 (naiv) ill. 1/16 (tuned)
fogalomnál látja a szót a középső síkokon.
"""
import json
import pathlib
import re
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import scope_paths

ROOT = pathlib.Path(__file__).resolve().parent.parent
RES = scope_paths.res(ROOT)
OUT = scope_paths.reports(ROOT)
MID = 24                                    # a „középső" tartomány: 0–23. sík


def cand_original(it):
    """Az analyze_d.py eredeti matchere — írásjelekkel együtt."""
    return {w.strip().lower() for w in it["en_approx"].replace("/", " ").split()
            if len(w.strip()) > 3}


def cand_clean(it):
    """Írásjel-tisztított matcher: zárójel/aposztróf le, kötőjel mentén bontva."""
    out = set()
    for w in re.split(r"[/\s]+", it["en_approx"]):
        w = re.sub(r"[^a-z\-']", "", w.lower()).strip("-'")
        for part in w.split("-"):
            if len(part) > 3:
                out.add(part)
    return out


def main():
    unt = {}
    for line in open(ROOT / "items.jsonl", encoding="utf-8"):
        it = json.loads(line)
        if it.get("group") == "UNT":
            unt[it["id"]] = it

    md = ["# D2 kontroll — mennyit ér a null-eredmény?", "",
          f"Kör: `{RES.name}` · középső tartomány: 0–{MID - 1}. sík · "
          "matcher: az `analyze_d.py` eredetije + írásjel-tisztított változat.", ""]

    for sfx, nev in (("", "naiv"), ("_tuned", "tuned")):
        vp, tp, ip = (RES / f"lens_vocab{sfx}.json", RES / f"lens_top{sfx}.npz",
                      RES / f"lens_index{sfx}.json")
        if not (vp.exists() and tp.exists() and ip.exists()):
            md += [f"## {nev} lens — ⏭️ nincs lens-kimenet ebben a körben", ""]
            continue
        vocab = json.load(open(vp, encoding="utf-8"))
        lens = np.load(tp)["ids"]
        index = json.load(open(ip, encoding="utf-8"))
        key = "item_id" if "item_id" in index[0] else "id"
        pos = {(m[key], m["lang"]): i for i, m in enumerate(index)}
        n_l = lens.shape[1]

        # a teljes korpusz top-20 tokenkészlete (elérhetőség-teszthez)
        all_tok = set()
        for n in range(lens.shape[0]):
            for L in range(n_l):
                for t in lens[n, L]:
                    all_tok.add(vocab[str(int(t))]["text"].strip().lower())

        md += [f"## {nev} lens", ""]
        for cf, cnev in ((cand_original, "eredeti matcher"),
                         (cand_clean, "tisztított matcher")):
            unreachable = sorted(iid for iid, it in unt.items()
                                 if not (cf(it) & all_tok))
            pc_mid, pc_any, null_hits = [], [], []
            for iid, it in sorted(unt.items()):
                w = cf(it)
                tops = [{vocab[str(int(t))]["text"].strip().lower()
                         for t in lens[pos[(iid, "en")], L]} for L in range(n_l)]
                if any(w & s for s in tops[:MID]):
                    pc_mid.append(iid)
                if any(w & s for s in tops):
                    pc_any.append(iid)
                # ⛔ promptonként számolunk, nem (prompt, sík) páronként — a 0/32
                # nevezője 32 prompt, az egységnek egyeznie kell
                for lang in ("hu", "zh"):
                    m = pos[(iid, lang)]
                    per_layer = {}
                    for L in range(MID):
                        got = w & {vocab[str(int(t))]["text"].strip().lower()
                                   for t in lens[m, L]}
                        if got:
                            per_layer[L] = sorted(got)
                    if per_layer:
                        null_hits.append((iid, lang, per_layer))
            md += [f"### {cnev}", "",
                   f"- **Elérhetőség:** {len(unt) - len(unreachable)}/{len(unt)} fogalom "
                   f"jelöltszava fordul elő egyáltalán a korpusz top-20 olvasataiban — "
                   f"a többinél ({', '.join(unreachable) or '—'}) a találat szerkezetileg "
                   "lehetetlen.",
                   f"- **Pozitív kontroll (ANGOL prompt):** középső síkon {len(pc_mid)}/16 "
                   f"({', '.join(pc_mid) or '—'}) · bármely síkon {len(pc_any)}/16.",
                   f"- **Null-eredmény (hu+zh prompt, középső sík):** "
                   f"{len(null_hits)}/32 találat"
                   + (f" — {null_hits}" if null_hits else "") + ".", ""]

    md += ["## Következtetés", "",
           "A pozitív kontroll szerint a műszer érzékenysége alacsony: az angol prompton "
           "is csak kevés fogalomnál jelenik meg a közelítőszó a középső síkokon. "
           "A nem-angol promptok nullája ezért **gyenge evidencia** a fordítási útvonal "
           "ellen — a dolgozat 7. fejezete ennek megfelelően fogalmaz.", ""]
    out = OUT / "05_d2_kontroll.md"
    out.write_text("\n".join(md), encoding="utf-8")
    print(f"→ {out}")


if __name__ == "__main__":
    main()
