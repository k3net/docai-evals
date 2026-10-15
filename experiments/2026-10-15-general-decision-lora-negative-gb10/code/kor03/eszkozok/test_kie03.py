"""A KIE/validáció HO-új-család egységtesztje: a gold újraszámolása a generátortól függetlenül (03-runbook 4.6).

A teszt nem hívja a kie03 számoló vagy formázó függvényeit. Saját formázóval és parszolóval dolgozik:
  - a megjelenített értékeknek (meta.kie) szó szerint szerepelniük kell a renderelt szövegben;
  - a goldot a megjelenített értékekből és a szövegből számolja újra (ÁFA-kerekítés, határidő, késedelem, mezők);
  - az X-itemeknél azt nézi, hogy a döntéshez szükséges adat valóban hiányzik-e a szövegből, és egyik opció sem
    a helyes érték;
  - opció-egyediség, séma, split, determinizmus (két generálás bájtra azonos).

  kor01/.venv/bin/python kor03/eszkozok/test_kie03.py
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kie03  # noqa: E402  (csak a generate() és a kimeneti fájlok miatt)
from kozos03 import validate  # noqa: E402

F0 = Path(__file__).resolve().parents[1] / "adat/f0"
MONTHS = ["január", "február", "március", "április", "május", "június", "július", "augusztus", "szeptember",
          "október", "november", "december"]


def fmt_amount(n: int, style: str) -> str:
    g = f"{n:,}"
    return {"szokoz_ft": g.replace(",", " ") + " Ft", "pont_ft": g.replace(",", ".") + ",- Ft", "huf": f"{n} HUF",
            "szokoz_00": g.replace(",", " ") + ",00"}[style]


def parse_amount(s: str) -> int:
    s = s.replace(" HUF", "").replace(" Ft", "").replace(",-", "").replace(",00", "")
    return int(s.replace(" ", "").replace(".", ""))


def parse_date(s: str) -> dt.date:
    s = s.strip()
    if m := re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s):
        return dt.date(*map(int, m.groups()))
    if m := re.fullmatch(r"(\d{4})\.\s?(\d{2})\.\s?(\d{2})\.", s):
        return dt.date(*map(int, m.groups()))
    if m := re.fullmatch(r"(\d{4})\. (\w+) (\d{1,2})\.", s):
        return dt.date(int(m.group(1)), MONTHS.index(m.group(2)) + 1, int(m.group(3)))
    raise ValueError(s)


def vat(net: int, rate: str) -> int:
    if rate == "AAM":
        return 0
    q, r = divmod(net * int(rate), 100)
    return q + (1 if r >= 50 else 0)


SUPPLY_LABELS = ("Teljesítés dátuma: ", "Teljesítés: ", "TELJ.: ")
DUE_LABELS = ("Fizetési határidő: ", "ESED.: ")


def check(r: dict) -> list[str]:
    err = []
    m, st, opts = r["meta"]["kie"], r["state"], {o["id"]: o["text"] for o in r["options"]}
    A = lambda n: fmt_amount(n, m["amount_fmt"])  # noqa: E731
    texts = list(opts.values())
    if len(set(texts)) != len(texts):
        err.append("ismétlődő opció")
    gold_text = opts.get(r["gold"]) if r["kind"] == "choice" else None
    qt = m["qtype"]
    true_lines = [(ln["qty"] * ln["price"], ln["rate"]) for ln in m["lines"]]
    # a megjelenített tételértékek szerepelnek a szövegben
    for ln in m["lines"]:
        for k, flag in (("net", True), ("vat", m["show"]["vat_col"]), ("gross", m["show"]["gross_col"])):
            if flag and A(ln[k]) not in st:
                err.append(f"a megjelenített {k} ({A(ln[k])}) nincs a szövegben")
    if qt == "hibas_sor":
        bad = [i for i, ln in enumerate(m["lines"], 1)
               if ln["net"] != ln["qty"] * ln["price"] or ln["vat"] != vat(ln["qty"] * ln["price"], ln["rate"])
               or ln["gross"] != ln["qty"] * ln["price"] + vat(ln["qty"] * ln["price"], ln["rate"])]
        if r["gold"] is None:
            err += ["X, de van hibás sor"] if bad else []
        elif bad != [int(gold_text.split(".")[0])]:
            err.append(f"hibás sorok {bad}, gold {gold_text}")
    elif qt == "vegosszeg":
        ok = sum(ln["gross"] for ln in m["lines"]) == m["totals"]["gross"]
        if A(m["totals"]["gross"]) not in st or (r["gold"] == "igen") != ok:
            err.append("végösszeg-gold")
    elif qt == "afa_osszesen":
        true = sum(vat(n, rt) for n, rt in true_lines)
        hits = [t for t in texts if parse_amount(t) == true]
        if r["gold"] is None:
            if hits or re.search(r"\d\s?%", st) or "ÁFA-kulcs" in st:
                err.append("X: a kulcs látszik, vagy a helyes érték opció")
        elif hits != [gold_text]:
            err.append(f"ÁFA: {true} ≠ gold {gold_text}")
        if "ÁFA összesen" in st or "AFA:" in st or ", ÁFA " in st:
            err.append("az ÁFA-összeg látszik")
    elif qt == "hatarido_szamolt":
        issue = parse_date(m["dates"]["issue"])
        n = re.search(r"keltétől számított (\d+) naptári napon belül", st)
        if any(lab in st for lab in DUE_LABELS):
            err.append("a határidő látszik")
        if r["gold"] is None:
            if n or any(parse_date(t) == issue + dt.timedelta(days=30) for t in texts):
                err.append("X: van fizetési feltétel, vagy a 30 napos dátum opció")
        elif not n or parse_date(gold_text) != issue + dt.timedelta(days=int(n.group(1))) or \
                sum(parse_date(t) == parse_date(gold_text) for t in texts) != 1:
            err.append("határidő-gold")
    elif qt == "kesedelem":
        due, pay = parse_date(m["dates"]["due"]), parse_date(m["pay"])
        if not any(lab + m["dates"]["due"] in st for lab in DUE_LABELS) or (r["gold"] == "igen") != (pay > due):
            err.append("késedelem-gold")
    elif qt == "teljesites_datuma":
        sup = m["dates"]["supply"]
        shown = any(lab + sup in st for lab in SUPPLY_LABELS)
        if r["gold"] is None:
            if any(lab in st for lab in SUPPLY_LABELS) or sup in texts:
                err.append("X: a teljesítés látszik vagy opció")
        elif not shown or gold_text != sup:
            err.append("teljesítés-gold")
    elif qt == "mezo_valasztas":
        v = m["ids"][m["field"]]
        if r["gold"] is None:
            if v in st or v in texts:
                err.append("X: a mező látszik vagy opció")
        elif v not in st or gold_text != v or texts.count(v) != 1:
            err.append("mező-gold")
        for t in texts:
            if t != v and t in st and t not in m["ids"].values():
                err.append(f"ismeretlen opció a szövegben: {t}")
    elif qt == "kinyert_ertek":
        v = m["ids"][m["field"]]
        if v not in st or (r["gold"] == "igen") != (m["claimed"] == v) or m["claimed"] not in r["question"]:
            err.append("kinyert-érték-gold")
    else:
        err.append(f"ismeretlen kérdéstípus {qt}")
    return err


def main() -> None:
    rows = [json.loads(line) for f in ("osszeg", "datum", "mezo")
            for line in (F0 / f"kie.{f}.jsonl").read_text(encoding="utf-8").splitlines()]
    errors = []
    for r in rows:
        e = validate(r) + check(r)
        if r["split"] != "ho-uj" or r["group"] != "kie":
            e.append("split/csoport")
        if e:
            errors.append((r["id"], e))
    regen = kie03.generate()
    same = [json.dumps(a, ensure_ascii=False, sort_keys=True) == json.dumps(b, ensure_ascii=False, sort_keys=True)
            for a, b in zip(sorted(regen, key=lambda r: r["id"]), sorted(rows, key=lambda r: r["id"]))]
    print(f"{len(rows)} item, hibás: {len(errors)}; determinisztikus: {all(same) and len(regen) == len(rows)}")
    for i, e in errors[:15]:
        print(" ", i, e)
    if errors or not all(same):
        raise SystemExit("EREDMÉNY: HIBA")
    print("EREDMÉNY: OK")


if __name__ == "__main__":
    main()
