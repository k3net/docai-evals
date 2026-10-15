"""03-as kör — konstrukciós családok a magyar Wikipédiából (03-runbook 3.4; legfeljebb a train 15%-a a keverékben).

Forrás: a HF `wikimedia/wikipedia` 20231101.hu pillanatképének egy shardja (CC-BY-SA-3.0 / GFDL; a CC-BY-SA-3.0-t
választjuk). A gold a szöveg szerkezetéből jön:

  konstrukcios.wiki_szakaszcim   melyik szakaszcím tartozik a szövegrészhez (a szócikk saját címei közül)
  konstrukcios.wiki_folytatas    melyik mondat folytatja közvetlenül a szöveget (a disztraktorok ugyanannak a
                                 szócikknek legalább két bekezdéssel távolabbi mondatai)

Mindkettőben 15% gold-drop X. Szűrés:
  - szakaszcím: rövid (< 60 karakter), ponttal nem záruló sor, utána legalább 200 karakteres bekezdés; a sablon-
    szakaszok (Jegyzetek, Források, Külső hivatkozások stb.) és a táblázatsorok kimaradnak; azonos szövegű cím nem
    lehet a gold disztraktora;
  - mondat: clean_sentence (30–300 karakter, legalább hat szó, belül nincs pont, a szavak legalább 40%-a kisbetűs):
    a rövidítésnél vagy bibliográfiai listán elvágott töredék kimarad, mert kilógó, könnyű disztraktor lenne;
  - **szivárgás:** a MILQA magyar Wikipédia-bekezdésekből készült, ezért a MILQA-ban szereplő szócikkek kimaradnak. A
    NerKor wikipédiás alkorpuszával az F1 MinHash-auditja vet össze.
Szócikkenként családonként legfeljebb egy item; családonként legfeljebb N_MAX. Split: a szócikk-id hash-e szerint 10%
val, 10% teszt-ID, a többi train.

  kor01/.venv/bin/python kor03/eszkozok/adapter_wiki.py   # → kor03/adat/f0/konstrukcios.wiki_*.jsonl
"""

from __future__ import annotations

import glob
import hashlib
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kozos03 import MAX_OPTIONS, validate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "forras/hf/wikimedia/wikipedia/20231101.hu"
OUT = ROOT / "adat/f0"
SEED = "20261009"
N_MAX = 6000
X_SHARE = 15
BOILER = {"jegyzetek", "források", "forrás", "kapcsolódó szócikkek", "további információk", "külső hivatkozások",
          "fordítás", "irodalom", "hivatkozások", "lásd még", "megjegyzés", "megjegyzések", "dokumentáció",
          "hivatalos weboldal", "hivatalos honlap", "statisztika", "végeredmény", "képgaléria", "galéria", "filmográfia",
          "diszkográfia", "művei", "díjai", "díjak", "elismerései", "bibliográfia", "szakirodalom"}
SENT = re.compile(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÖŐÚÜŰ„])")


def hnum(s: str) -> int:
    return int(hashlib.sha256(f"{SEED}:{s}".encode()).hexdigest(), 16)


def is_heading(line: str) -> bool:
    s = line.strip()
    return (0 < len(s) < 60 and not s.endswith((".", ":", ",", ";")) and "|" not in s and not s[:1].isdigit()
            and s.lower().rstrip(":") not in BOILER)


def sections(text: str) -> list[tuple[str, list[str]]]:
    """(cím, bekezdések) párok; az első, cím nélküli rész a bevezető ("")."""
    out: list[tuple[str, list[str]]] = [("", [])]
    for line in text.split("\n"):
        s = line.strip()
        if not s:
            continue
        if is_heading(s):
            out.append((s, []))
        elif s.lower().rstrip(":") in BOILER and len(s) < 60:
            out.append(("__boiler__", []))
        elif "|" not in s and len(s) >= 80:
            out[-1][1].append(s)
    return [(h, ps) for h, ps in out if h != "__boiler__" and ps]


def clean_sentence(x: str) -> bool:
    """Valódi mondat, nem rövidítésnél vagy bibliográfiai listán elvágott töredék: 30–300 karakter, írásjellel zárul,
    legalább hat szó, belül nincs pont, az utolsó szó legalább három betű, a szavak legalább 40%-a kisbetűs."""
    w = x.split()
    if not (30 <= len(x) <= 300 and x[-1] in ".!?" and len(w) >= 6):
        return False
    if "." in x[:-1] or len(re.sub(r"\W", "", w[-1])) < 3:
        return False
    return sum(t[:1].islower() for t in w) / len(w) >= 0.4


def sentences(par: str) -> list[str]:
    return [x.strip() for x in SENT.split(par) if clean_sentence(x.strip())]


def item(fam: str, art: dict, k: int, state: str, question: str, gold_text: str, pool: list[str],
         rnd: random.Random) -> dict | None:
    cands = [c for c in dict.fromkeys(pool) if c.strip().lower() != gold_text.strip().lower()]
    rnd.shuffle(cands)
    xdrop = hnum(f"x:{fam}:{art['id']}") % 100 < X_SHARE
    lo = 2 if xdrop else 1
    if len(cands) < lo:
        return None
    n = rnd.randint(lo, min(MAX_OPTIONS - (0 if xdrop else 1), len(cands), 6))
    texts = cands[:n] + ([] if xdrop else [gold_text])
    rnd.shuffle(texts)
    opts = [{"id": f"o{i + 1}", "text": t} for i, t in enumerate(texts)]
    v = hnum(f"split:{art['id']}") % 100
    return {"id": f"{fam}:{art['id']}:{k}", "family": fam, "group": "konstrukcios", "source": "Wikipédia (hu)",
            "source_license": "CC-BY-SA-3.0", "source_ref": f"20231101.hu:{art['id']}",
            "split": "val" if v < 10 else "test-id" if v < 20 else "train", "group_id": f"wiki:{art['id']}",
            "lang": "hu", "kind": "choice", "state": state, "question": question, "options": opts,
            "gold": None if xdrop else next(o["id"] for o in opts if o["text"] == gold_text),
            "x_type": "gold-drop" if xdrop else None, "ketertelmu": False, "soft": None,
            "meta": {"wiki_cim": art["title"]}}


def main() -> None:
    milqa = {json.loads(l)["meta"]["milqa_cim"] for l in (OUT / "qa.milqa.jsonl").read_text(encoding="utf-8").splitlines()}
    arts = [r for f in sorted(glob.glob(str(WIKI / "*.parquet"))) for r in pq.read_table(f).to_pylist()]
    arts.sort(key=lambda a: hnum(f"order:{a['id']}"))
    rows = {"konstrukcios.wiki_szakaszcim": [], "konstrukcios.wiki_folytatas": []}
    why = Counter()
    for art in arts:
        if art["title"] in milqa:
            why["kimarad: MILQA-szócikk"] += 1
            continue
        secs = sections(art["text"])
        rnd = random.Random(f"{SEED}:wiki:{art['id']}")
        titled = [(h, ps) for h, ps in secs if h and len(ps[0]) >= 200]
        if len(rows["konstrukcios.wiki_szakaszcim"]) < N_MAX and len({h.lower() for h, _ in titled}) >= 3:
            h, ps = rnd.choice(titled)
            st = ps[0] if len(ps[0]) <= 700 else ps[0][:700].rsplit(" ", 1)[0] + " […]"
            it = item("konstrukcios.wiki_szakaszcim", art, 0, st,
                      f"Melyik szakaszcím alá tartozik ez a szövegrész a(z) „{art['title']}” szócikkben?", h,
                      [x for x, _ in titled], rnd)
            if it:
                rows["konstrukcios.wiki_szakaszcim"].append(it)
                why["szakaszcim"] += 1
        pars = [p for _, ps in secs for p in ps]
        if len(rows["konstrukcios.wiki_folytatas"]) < N_MAX and len(pars) >= 4:
            cand = [i for i, p in enumerate(pars) if len(sentences(p)) >= 4]
            if cand:
                i = rnd.choice(cand)
                ss = sentences(pars[i])
                cut = rnd.randint(2, min(4, len(ss) - 1))
                far = [s for j, p in enumerate(pars) if abs(j - i) >= 2 for s in sentences(p)]
                if len(far) >= 2:
                    it = item("konstrukcios.wiki_folytatas", art, 1, " ".join(ss[:cut]),
                              "Melyik mondat folytatja közvetlenül a szöveget?", ss[cut], far, rnd)
                    if it:
                        rows["konstrukcios.wiki_folytatas"].append(it)
                        why["folytatas"] += 1
        if all(len(v) >= N_MAX for v in rows.values()):
            break
    rep: dict[str, dict] = {"szures": dict(why)}
    for fam, rs in rows.items():
        bad = [(r["id"], e) for r in rs if (e := validate(r))]
        if bad:
            raise SystemExit(f"{fam}: {len(bad)} sémahiba, pl. {bad[:3]}")
        (OUT / f"{fam}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rs), encoding="utf-8")
        rep[fam] = {"n": len(rs), "split": dict(Counter(r["split"] for r in rs)),
                    "x_arany": sum(r["gold"] is None for r in rs) / max(1, len(rs))}
        print(fam, json.dumps(rep[fam], ensure_ascii=False))
    print(json.dumps(rep["szures"], ensure_ascii=False))
    (OUT / "adapter_wiki_riport.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
