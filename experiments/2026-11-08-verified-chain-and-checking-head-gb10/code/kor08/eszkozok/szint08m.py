"""08 illesztett kontroll (M) — az illesztett (a) generátora. A G2 értelmezési tesztjének (a)-tervei változatlanul (ugyanaz az egység, forma, összeg és opció), a generátor
utasításában a nem döntő mondattal (`illeszt08m`), a (b) utasításának alakjában. A címke Y. Az item-id és a szelet `M1T`; a (b) itemek a G2-éi maradnak. Az (a) tényellenőrzője
(`szint08e.fact_check_e`) változatlanul fut; mellette: nincs árulkodó szó, és a mondat legalább harmada visszajön a szövegben (`tovek`).

  terv  --csalad F                             (CPU)
  minta [--n 3]                                mintapromptok → <gyökér>/minta_promptok.md
  gen   --csalad F --url U --model M           (GPU: Muse)
  final --csalad F
A gyökér `kor08/adat/M` (`M_GYOKER`).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent)]
import illeszt08m as I  # noqa: E402
import szint08 as T  # noqa: E402

E, S, L = T.E, T.S, T.L
BANK, HIBA, SZAB = T.BANK, T.HIBA, T.SZAB
G2 = T.EXP / "kor08/adat/G2/ert_teszt"
GY = T.EXP / os.environ.get("M_GYOKER", "kor08/adat/M")
SZELET = "M1T"
E.KOR["n"] = 2
SZAB_VEG = {"hu": " A költség céljáról vagy jellegéről ezen túl semmit ne írj.", "en": " Do not say anything more about the purpose or nature of the expense."}
SZAB_TENY = {"hu": " A szöveg mondja ki ezt a tényt is, a saját szavaiddal, de a költség kategóriáját ne nevezd meg: {m}.",
             "en": " The text must also state this fact, in your own words, without naming the expense category: {m}."}
BANK_VEG = {"hu": "de ne derüljön ki, melyik cég számlájáról van szó, és az sem, hogy ki fizet kinek a nevében.",
            "en": "but it must not be clear whose invoice is being paid, nor who pays on whose behalf."}
BANK_TENY = {"hu": " A közlemény mondja ki ezt is, a saját szavaiddal: {m}.", "en": " The payment details must also state this, in your own words: {m}."}
HIBA_VEG = {"hu": "hogy pontosan mi a gond, ne derüljön ki.", "en": "it must not be clear what exactly is wrong."}


def path(kind: str, fam: str) -> Path:
    return GY / kind / f"{fam}.jsonl"


def nem_dontoi(p: dict) -> str:
    """A terv nem döntő mondata; a hibán nincs mondat, ott a körülmények utasítása."""
    lang, fam = p["lang"], p["csalad"]
    if fam == SZAB:
        return I.mondat(p["ertelmezes"]["forgatokonyv"], lang)
    if fam == BANK:
        t = p["tenyek"]
        return I.BANK[lang][S.h(f"m08bank:{p['ertelmezes']['egyseg']}") % 3].format(A=t["szamla_partnere"], B=t["fizeto"])
    return ""


def terv(fam: str) -> list[dict]:
    kesz = {i["meta"]["ertelmezes"]["egyseg"] for i in S.jl_read(G2 / "items" / f"{fam}.jsonl")}
    rows = []
    for p in S.jl_read(G2 / "terv" / f"{fam}.jsonl"):
        e = p["ertelmezes"]
        if e["alt"] != "a" or e["egyseg"] not in kesz:
            continue
        q = {**p, "szelet": SZELET, "group_id": p["group_id"].replace(":G2T:", f":{SZELET}:"), "ertelmezes": {**e, "illesztett": True, "szelet": "illesztett"}}
        rows.append({**q, "illesztes": {"mondat": nem_dontoi(q)}})
    return rows


def gen_prompt_m(p: dict) -> str:
    fam, lang = p["csalad"], p["lang"]
    s = E.gen_prompt_e(p)
    if fam == SZAB:
        veg, uj = SZAB_VEG[lang], SZAB_TENY[lang].format(m=p["illesztes"]["mondat"]) + SZAB_VEG[lang]
    elif fam == BANK:
        veg, uj = BANK_VEG[lang], BANK_VEG[lang] + BANK_TENY[lang].format(m=p["illesztes"]["mondat"])
    else:
        veg, uj = HIBA_VEG[lang], HIBA_VEG[lang] + I.HIBA[lang]
    if s.count(veg) != 1:
        raise SystemExit(f"{p['group_id']}: a generátor utasítása nem a várt alakú")
    return s.replace(veg, uj)


def fact_check_m(p: dict, text: str) -> str | None:
    if (err := E.fact_check_e(p, text)):
        return err
    low = text.lower()
    if p["csalad"] == SZAB:
        if any(k.lower() in low for k in I.arulkodo(p["tenyek"]["helyzet"], p["lang"])):
            return "árulkodó szó a szövegben"
    if (m := p["illesztes"]["mondat"]):
        t = I.tovek(m)
        if sum(x in low for x in t) * 3 < len(t):
            return "a nem döntő mondat hiányzik"
    return None


def gen_one(p: dict, a, extra: dict) -> dict:
    out = {"group_id": p["group_id"], "terv": p, "probak": []}
    for k in range(4):
        try:
            obj = S.llm_json(a.url, a.model, p["lang"], gen_prompt_m(p), extra, S.h(f"gen08m:{a.seed}:{p['group_id']}:{k}") % 10**6)
        except RuntimeError as e:
            out["probak"].append(str(e))
            continue
        txt = str(obj.get("szoveg") or "").strip()
        err = "üres szöveg" if not txt else fact_check_m(p, txt)
        if err is None:
            return out | {"szoveg": txt}
        out["probak"].append(err)
    return out | {"hiba": out["probak"][-1] if out["probak"] else "ismeretlen"}


def cmd_terv(a) -> None:
    rows = terv(a.csalad)
    S.jl_write(path("terv", a.csalad), rows)
    print(f"{a.csalad}: {len(rows)} terv")


def cmd_minta(a) -> None:
    out = ["# 08 M — mintapromptok\n"]
    for fam in T.CSALADOK:
        for lang in S.LANGS:
            for p in [r for r in S.jl_read(path("terv", fam)) if r["lang"] == lang][:a.n]:
                out += [f"## {fam} · {lang} · {p['group_id']}", "", gen_prompt_m(p), ""]
    (GY / "minta_promptok.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"→ {GY / 'minta_promptok.md'}")


def cmd_gen(a) -> None:
    fam = a.csalad
    out = path("raw", fam)
    done = {r["group_id"] for r in S.jl_read(out)} if out.exists() else set()
    todo = [p for p in S.jl_read(path("terv", fam)) if p["group_id"] not in done]
    extra = json.loads(a.extra) if a.extra else {}
    print(f"{fam}: {len(done)} kész, {len(todo)} hátra", flush=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "a", encoding="utf-8") as fh, ThreadPoolExecutor(a.workers) as ex:
        for i, r in enumerate(ex.map(lambda p: gen_one(p, a, extra), todo), 1):
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            fh.flush()
            if i % 50 == 0:
                print(f"  {i}/{len(todo)}", flush=True)


def cmd_final(a) -> None:
    fam = a.csalad
    raw = S.jl_read(path("raw", fam))
    items = []
    for r in raw:
        if "szoveg" not in r:
            continue
        it = S.to_item(r)
        e = r["terv"]["ertelmezes"]
        it["meta"] |= {"ertelmezes": e, "illesztes": r["terv"]["illesztes"]}
        if fam == SZAB:
            it["template_group_id"] = f"{SZAB}:G2:{e['forgatokonyv']}"
        it["question"] = L.bank_kerdes(it)
        items.append(it)
    S.jl_write(path("items", fam), items)
    print(f"{fam}: {len(items)} item; elveszett: {dict(Counter(r.get('hiba') for r in raw if 'szoveg' not in r))}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("terv")
    m = sub.add_parser("minta")
    m.add_argument("--n", type=int, default=3)
    g = sub.add_parser("gen")
    g.add_argument("--url", required=True)
    g.add_argument("--model", required=True)
    g.add_argument("--extra", default="")
    g.add_argument("--workers", type=int, default=64)
    g.add_argument("--seed", default="1")
    f = sub.add_parser("final")
    for x in (t, g, f):
        x.add_argument("--csalad", required=True, choices=T.CSALADOK)
    a = ap.parse_args()
    {"terv": cmd_terv, "minta": cmd_minta, "gen": cmd_gen, "final": cmd_final}[a.cmd](a)


if __name__ == "__main__":
    main()
