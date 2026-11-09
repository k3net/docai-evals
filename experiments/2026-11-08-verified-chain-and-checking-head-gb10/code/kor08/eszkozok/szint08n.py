"""08 erősebb kontroll (N) — minimális pár a szabálycsaládon. Egy egységből két szöveg, ugyanazzal a tervvel és formával, mindkettőben egy döntő jellegű mondat (J, a forgatókönyv `jel2`-je), egy nem döntő mondat
(L, `illeszt08m.MONDAT`) és egy „korábbi, másik kérelem” jelölés:
  (b'')  a kért összegről J(f), a korábbi kérelemről L(f');  gold a terv goldja
  (a'')  a kért összegről L(f), a korábbi kérelemről J(f');  címke Y
Az f' az f párja: ugyanaz a (gold, csali) a teszt-forgatókönyvek közt (`par_of`), így a szókincs a két osztályban cserélhető, és a tárgy nem ütközik; az egyetlen különbség, hogy a J a kért összegre vonatkozik-e.
A korábbi kérelem helye (a szöveg eleje vagy vége) egységenként hash, a két tagban azonos. A (b'') a (b) első változatának formája. A szelet `N1T`, a gyökér `kor08/adat/N` (`N_GYOKER`).

  terv  (CPU);  minta [--n 3];  gen --url U --model M (GPU: Muse);  final
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent)]
import forgatokonyv08_szab as FK  # noqa: E402
import illeszt08m as I  # noqa: E402
import szint08 as T  # noqa: E402

E, S, L = T.E, T.S, T.L
FAM = T.SZAB
G2 = T.EXP / "kor08/adat/G2/ert_teszt"
GY = T.EXP / os.environ.get("N_GYOKER", "kor08/adat/N")
SZELET = "N1T"
E.KOR["n"] = 2
VEG = {"hu": " A költség céljáról vagy jellegéről ezen túl semmit ne írj.", "en": " Do not say anything more about the purpose or nature of the expense."}
TENY = {"hu": " A szöveg mondja ki ezt a tényt is a kért összegről, a saját szavaiddal, de a költség kategóriáját ne nevezd meg: {m}.",
        "en": " The text must also state this fact about the amount claimed, in your own words, without naming the expense category: {m}."}
MAS = {"hu": " Külön mondatban, jól elkülönítve említse meg azt is, hogy egy korábbi, már lezárt, másik kérelmében, egy másik tételnél ez történt, és ennek a mostani összeghez nincs köze: {m}. Ezt az említést a szöveg {h} tedd.",
       "en": " In a separate sentence, clearly set apart, it must also mention that on an earlier, already closed, different claim, for a different item, the following was the case, and that this has nothing to do with the present amount: {m}. Put this mention at the {h} of the text."}
HELY = {"hu": ("elejére", "végére"), "en": ("beginning", "end")}
JELOLO = {"hu": re.compile(r"korábbi|előző|múltkori|régebbi|másik kérelem", re.I), "en": re.compile(r"earlier|previous|prior|another claim|separate claim|different claim", re.I)}


def path(kind: str) -> Path:
    return GY / kind / f"{FAM}.jsonl"


def par_of() -> dict[str, str]:
    by = defaultdict(list)
    for x in FK.F:
        if x[1] == "teszt":
            by[(x[2], x[3])].append(x[0])
    if any(len(v) != 2 for v in by.values()):
        raise SystemExit("a teszt-forgatókönyvek nem párosak")
    return {a: b for v in by.values() for a, b in (v, v[::-1])}


def adat(lang: str) -> dict[str, dict]:
    return {f["id"]: f for f in FK.forgatokonyvek("teszt")[lang]}


def terv() -> list[dict]:
    kesz = {i["meta"]["ertelmezes"]["egyseg"] for i in S.jl_read(G2 / "items" / f"{FAM}.jsonl")}
    par = par_of()
    rows = []
    for p in S.jl_read(G2 / "terv" / f"{FAM}.jsonl"):
        e = p["ertelmezes"]
        if e["egyseg"] not in kesz or not (e["alt"] == "a" or e["valtozat"] == 1):
            continue
        fid, lang = e["forgatokonyv"], p["lang"]
        fk = adat(lang)
        f2 = par[fid]
        b = e["alt"] == "b"
        q = {**p, "szelet": SZELET, "group_id": p["group_id"].replace(":G2T:", f":{SZELET}:"), "ertelmezes": {**e, "minimalis_par": True, "szelet": "minimalis"}}
        q["illesztes"] = {"par": f2, "kert": fk[fid]["jel2"] if b else I.mondat(fid, lang), "mas": I.mondat(f2, lang) if b else fk[f2]["jel2"],
                          "kulcs_van": fk[fid]["kulcs2"] if b else fk[f2]["kulcs2"], "kulcs_nincs": fk[f2]["kulcs2"] if b else fk[fid]["kulcs2"],
                          "L": I.mondat(f2, lang) if b else I.mondat(fid, lang), "hely": S.h(f"n08hely:{e['egyseg']}") % 2}
        rows.append(q)
    return rows


def gen_prompt_n(p: dict) -> str:
    lang, m = p["lang"], p["illesztes"]
    alap = {**p, "ertelmezes": {**p["ertelmezes"], "alt": "a"}}
    s = E.gen_prompt_e(alap)
    if s.count(VEG[lang]) != 1:
        raise SystemExit(f"{p['group_id']}: a generátor utasítása nem a várt alakú")
    return s.replace(VEG[lang], TENY[lang].format(m=m["kert"]) + MAS[lang].format(m=m["mas"], h=HELY[lang][m["hely"]]) + VEG[lang])


def fact_check_n(p: dict, text: str) -> str | None:
    m, low = p["illesztes"], text.lower()
    q = {**p, "tenyek": {**p["tenyek"], "kulcs": [], "kulcs2": []}, "ertelmezes": {**p["ertelmezes"], "alt": "a"}}
    if (err := E.fact_check_e(q, text)):
        return err
    if not JELOLO[p["lang"]].search(text):
        return "hiányzik a korábbi kérelem jelölése"
    if not any(k.lower() in low for k in m["kulcs_van"]):
        return "hiányzik a döntő jellegű mondat"
    if any(k.lower() in low for k in m["kulcs_nincs"]):
        return "a másik forgatókönyv jele a szövegben"
    t = I.tovek(m["L"])
    if sum(x in low for x in t) * 3 < len(t):
        return "hiányzik a nem döntő mondat"
    return None


def gen_one(p: dict, a, extra: dict) -> dict:
    out = {"group_id": p["group_id"], "terv": p, "probak": []}
    for k in range(4):
        try:
            obj = S.llm_json(a.url, a.model, p["lang"], gen_prompt_n(p), extra, S.h(f"gen08n:{a.seed}:{p['group_id']}:{k}") % 10**6)
        except RuntimeError as e:
            out["probak"].append(str(e))
            continue
        txt = str(obj.get("szoveg") or "").strip()
        err = "üres szöveg" if not txt else fact_check_n(p, txt)
        if err is None:
            return out | {"szoveg": txt}
        out["probak"].append(err)
    return out | {"hiba": out["probak"][-1] if out["probak"] else "ismeretlen"}


def cmd_terv(_a) -> None:
    rows = terv()
    S.jl_write(path("terv"), rows)
    print(f"{len(rows)} terv; {dict(Counter(r['ertelmezes']['alt'] for r in rows))}")


def cmd_minta(a) -> None:
    rows = S.jl_read(path("terv"))
    out = ["# 08 N — mintapromptok\n"]
    for p in rows[:a.n * 2] + [r for r in rows if r["lang"] == "en"][:a.n * 2]:
        out += [f"## {p['lang']} · {p['ertelmezes']['alt']} · {p['ertelmezes']['forgatokonyv']} (pár {p['illesztes']['par']})", "", gen_prompt_n(p), ""]
    (GY / "minta_promptok.md").write_text("\n".join(out) + "\n", encoding="utf-8")


def cmd_gen(a) -> None:
    out = path("raw")
    done = {r["group_id"] for r in S.jl_read(out)} if out.exists() else set()
    todo = [p for p in S.jl_read(path("terv")) if p["group_id"] not in done]
    extra = json.loads(a.extra) if a.extra else {}
    print(f"{len(done)} kész, {len(todo)} hátra", flush=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "a", encoding="utf-8") as fh, ThreadPoolExecutor(a.workers) as ex:
        for i, r in enumerate(ex.map(lambda p: gen_one(p, a, extra), todo), 1):
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            fh.flush()
            if i % 100 == 0:
                print(f"  {i}/{len(todo)}", flush=True)


def cmd_final(_a) -> None:
    raw = S.jl_read(path("raw"))
    ok = [r for r in raw if "szoveg" in r]
    db = Counter(r["terv"]["ertelmezes"]["egyseg"] for r in ok)
    items = []
    for r in ok:
        e = r["terv"]["ertelmezes"]
        if db[e["egyseg"]] != 2:
            continue
        it = S.to_item(r)
        it["meta"] |= {"ertelmezes": e, "illesztes": {k: r["terv"]["illesztes"][k] for k in ("par", "hely")}}
        it["template_group_id"] = f"{FAM}:G2:{e['forgatokonyv']}"
        it["question"] = L.bank_kerdes(it)
        items.append(it)
    S.jl_write(path("items"), items)
    print(f"{len(items)} item, {dict(Counter(i['meta']['ertelmezes']['alt'] for i in items))}; elveszett: {dict(Counter(r.get('hiba') for r in raw if 'szoveg' not in r))}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("terv")
    m = sub.add_parser("minta")
    m.add_argument("--n", type=int, default=2)
    g = sub.add_parser("gen")
    g.add_argument("--url", required=True)
    g.add_argument("--model", required=True)
    g.add_argument("--extra", default="")
    g.add_argument("--workers", type=int, default=64)
    g.add_argument("--seed", default="1")
    sub.add_parser("final")
    a = ap.parse_args()
    {"terv": cmd_terv, "minta": cmd_minta, "gen": cmd_gen, "final": cmd_final}[a.cmd](a)


if __name__ == "__main__":
    main()
