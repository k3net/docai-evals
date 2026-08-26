#!/usr/bin/env python3
"""A generált válaszok degeneráltság-jelölése — a `truncated` flag KÉT jelenséget takar.

    python3 src/flag_degenerate.py            # a results/gen.jsonl-t bővíti (stdlib, GPU nélkül)

MÉRT PROBLÉMA: a 200/500-as kerettel is csonkolt válaszok egy része nem azért ért véget a
keretnél, mert sok mondanivalója volt, hanem mert a greedy dekódolás **ismétlési hurokba**
esett („a »kalák« szóból származik, ami a »kalák« szóból származik, …"). A kettőt szét kell
választani, mert ellentétes a kezelésük: a hurokra a keret NÖVELÉSE semmit nem ér (csak
tovább ismételne), a valódi keret-ütközés viszont nagyobb kerettel megoldható.

A hurok maga is EREDMÉNY (nyelvfüggő dekódolási stabilitás), de a D1 komponens-lefedettséget
lefelé torzítja: a beragadt válaszban kevesebb komponens fér el. Ezért jelöljük, nem javítjuk —
a dekódolás marad greedy, ahogy a runbook előírja.

Mérce: az 5-gramok ismétlődése a válaszban.
  repeat_ratio = 1 − (különböző 5-gram) / (összes 5-gram)   ∈ [0, 1)
  max_repeat   = a leggyakoribb 5-gram előfordulásszáma
  degenerate   = repeat_ratio ≥ 0,5 VAGY max_repeat ≥ 5
"""
import collections
import json
import pathlib
import scope_paths

N = 5
HERE = pathlib.Path(__file__).resolve().parent.parent
GEN = scope_paths.res(HERE) / "gen.jsonl"


def stats(text):
    w = text.split()
    if len(w) < N * 2:
        return 0.0, 0
    grams = [" ".join(w[i:i + N]) for i in range(len(w) - N + 1)]
    c = collections.Counter(grams)
    return round(1 - len(c) / len(grams), 3), max(c.values())


def main():
    rows = [json.loads(l) for l in GEN.read_text(encoding="utf-8").splitlines() if l.strip()]
    for r in rows:
        # a kínai/japán szöveg nem szóközzel tagolt → ott karakter-5-gramokkal mérünk
        text = r["text"] if r["lang"] != "zh" else " ".join(r["text"].replace(" ", ""))
        rr, mx = stats(text)
        r["repeat_ratio"], r["max_repeat"] = rr, mx
        r["degenerate"] = bool(rr >= 0.5 or mx >= 5)
    GEN.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")

    print(f"{len(rows)} rekord jelölve → {GEN}\n")
    print(f"{'':6s} {'degenerált':>22s} {'csonkolt ÉS nem degenerált':>30s}")
    for kind in ("fact", "unt", "ctrl"):
        ks = [r for r in rows if r["kind"] == kind]
        d = " ".join(f"{l}={sum(r['degenerate'] for r in ks if r['lang'] == l):2d}" for l in ("hu", "en", "zh"))
        t = " ".join(f"{l}={sum(r['truncated'] and not r['degenerate'] for r in ks if r['lang'] == l):2d}"
                     for l in ("hu", "en", "zh"))
        print(f"{kind:6s} {d:>22s} {t:>30s}   (n={len(ks)//3}/nyelv)")
    deg = [r for r in rows if r["degenerate"]]
    print(f"\ndegenerált összesen: {len(deg)}/{len(rows)} · ebből csonkolt is: {sum(r['truncated'] for r in deg)}")
    print("legrosszabbak:", [f"{r['item_id']}/{r['lang']}({r['repeat_ratio']})" for r in
                             sorted(deg, key=lambda r: -r["repeat_ratio"])[:5]])


if __name__ == "__main__":
    main()
