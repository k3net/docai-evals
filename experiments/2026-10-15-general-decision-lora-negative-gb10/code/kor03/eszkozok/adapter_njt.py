"""03-as kör — Nemzeti Jogszabálytár: konstrukciós jogi családok a bekezdésszintű egységekből (03-runbook 3.2, 3.4).

A gold a törvény szerkezetéből jön (njt03.py feldolgoz → forras/njt/njt_egysegek.jsonl), modell és ember nélkül:

  jogi.njt_torveny   melyik törvényből való a bekezdés (2–10 törvénycím)
  jogi.njt_fejezet   melyik fejezetébe tartozik a törvénynek (a törvény fejezetcímei)
  jogi.njt_cim       melyik alcím vagy tagolócím alá tartozik (a törvény címei; a disztraktorok előbb ugyanabból a
                     fejezetből, mert azok a nehezebbek)

Mindhárom családban 15% gold-drop X: a helyes cím kimarad, a többi ugyanígy választott. Szűrések:
  - a 80 karakternél rövidebb, és a több törvényben szó szerint előforduló bekezdés kimarad (pl. hatálybalépési
    sablon): ott a törvény nem dönthető el;
  - azonos szövegű cím (pl. „Értelmező rendelkezések” több fejezetben) nem lehet a gold disztraktora;
  - a pusztán sorszámot hordozó alcím („4. alfejezet”) nem cím; a címek elejéről a sorszám lekerül, a csupa nagybetűs
    cím mondatkezdő nagybetűs lesz.
Családonként és törvényenként legfeljebb CAP bekezdés (hash-alapú mintavétel). Split: a § (törvény + §) hash-e szerint
10% val, 10% teszt-ID, a többi train; egy § minden bekezdése egy splitbe kerül.

  python3 kor03/eszkozok/adapter_njt.py   # → kor03/adat/f0/jogi.njt_*.jsonl + adapter_njt_riport.json
"""

from __future__ import annotations

import hashlib
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kozos03 import MAX_OPTIONS, validate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
UNITS = ROOT / "forras/njt/njt_egysegek.jsonl"
OUT = ROOT / "adat/f0"
SEED = "20261009"
CAP = 60
X_SHARE = 15  # %


def hnum(s: str) -> int:
    return int(hashlib.sha256(f"{SEED}:{s}".encode()).hexdigest(), 16)


def norm(s: str) -> str:
    return re.sub(r"\W+", " ", s.lower()).strip()


def heading(s: str | None) -> str | None:
    if not s or re.fullmatch(r"\d+\.\s*alfejezet", s, re.I):
        return None
    s = re.sub(r"^\d+[/]?[a-z]?\.\s+", "", s).strip()
    if s.isupper():
        s = s.capitalize()
    return s or None


def nearest_title(u: dict) -> str | None:
    return heading(u["tagoloCim"]) or heading(u["alcim"])


def chapter(u: dict) -> str | None:
    return heading(u["fejezetCim"])


def split_of(u: dict) -> str:
    v = hnum(f"split:{u['law']}:{u['szakasz']}") % 100
    return "val" if v < 10 else "test-id" if v < 20 else "train"


def build(family: str, u: dict, k: int, gold_text: str, pool: list[str], rnd: random.Random, question: str,
          prefer: list[str] | None = None) -> dict | None:
    cands = [c for c in dict.fromkeys(pool) if norm(c) != norm(gold_text)]
    if prefer:
        pref = [c for c in dict.fromkeys(prefer) if norm(c) != norm(gold_text)]
        rnd.shuffle(pref)
        rest = [c for c in cands if c not in pref]
        rnd.shuffle(rest)
        cands = pref + rest
    else:
        rnd.shuffle(cands)
    xdrop = hnum(f"x:{family}:{u['law']}:{u['szakasz']}:{u['bekezdes']}:{k}") % 100 < X_SHARE
    need_lo = 2 if xdrop else 1
    if len(cands) < need_lo:
        return None
    n = rnd.randint(need_lo, min(MAX_OPTIONS - (0 if xdrop else 1), len(cands)))
    texts = cands[:n] + ([] if xdrop else [gold_text])
    rnd.shuffle(texts)
    opts = [{"id": f"o{i + 1}", "text": t} for i, t in enumerate(texts)]
    gold = None if xdrop else next(o["id"] for o in opts if o["text"] == gold_text)
    ref = f"{u['law']}:{u['szakasz']}:{u['bekezdes'] or '-'}:{k}"
    return {"id": f"{family}:{ref}", "family": family, "group": "jogi", "source": "Nemzeti Jogszabálytár",
            "source_license": "HU-Szjt-1-4", "source_ref": ref, "split": split_of(u),
            "group_id": f"jogi.njt:{u['law']}:{u['szakasz']}", "lang": "hu", "kind": "choice",
            "state": f"{u['szakasz']}{' ' + u['bekezdes'] if u['bekezdes'] else ''} {u['szoveg']}", "question": question,
            "options": opts, "gold": gold, "x_type": "gold-drop" if xdrop else None, "ketertelmu": False, "soft": None,
            "meta": {"njt": u["law"], "rovid": u["rovid"]} | ({"njt_gold": gold_text} if xdrop else {})}


def main() -> None:
    units = [json.loads(line) for line in UNITS.read_text(encoding="utf-8").splitlines()]
    by_text = defaultdict(set)
    for u in units:
        by_text[norm(u["szoveg"])].add(u["law"])
    why = Counter()
    ok = []
    for u in units:
        if len(u["szoveg"]) < 80:
            why["kimarad: rövid"] += 1
        elif len(by_text[norm(u["szoveg"])]) > 1:
            why["kimarad: több törvényben is szó szerint"] += 1
        else:
            ok.append(u)
    laws = {u["law"]: u["cim"] for u in ok}
    by_law = defaultdict(list)
    for u in ok:
        by_law[u["law"]].append(u)
    rows = {"jogi.njt_torveny": [], "jogi.njt_fejezet": [], "jogi.njt_cim": []}
    for law, us in by_law.items():
        chapters = [c for c in dict.fromkeys(chapter(u) for u in us) if c]
        titles = [t for t in dict.fromkeys(nearest_title(u) for u in us) if t]
        titles_in_chapter = defaultdict(list)
        for u in us:
            if nearest_title(u) and chapter(u):
                titles_in_chapter[chapter(u)].append(nearest_title(u))
        for k, fam in enumerate(rows):
            sample = sorted(us, key=lambda u: hnum(f"{fam}:{u['law']}:{u['szakasz']}:{u['bekezdes']}:{u['szoveg'][:50]}"))
            n = 0
            for u in sample:
                if n >= CAP:
                    break
                rnd = random.Random(f"{SEED}:{fam}:{u['law']}:{u['szakasz']}:{u['bekezdes']}")
                if fam == "jogi.njt_torveny":
                    it = build(fam, u, k, laws[law], [laws[x] for x in laws if x != law], rnd,
                               "Melyik törvényből való ez a rendelkezés?")
                elif fam == "jogi.njt_fejezet":
                    ch = chapter(u)
                    if not ch or len(chapters) < 3:
                        why[f"{fam} kimarad: nincs fejezet"] += 1
                        continue
                    it = build(fam, u, k, ch, chapters, rnd,
                               f"A(z) {laws[law]} melyik fejezetébe tartozik ez a rendelkezés?")
                else:
                    ti = nearest_title(u)
                    if not ti or len(titles) < 3:
                        why[f"{fam} kimarad: nincs cím"] += 1
                        continue
                    it = build(fam, u, k, ti, titles, rnd,
                               f"A(z) {laws[law]} melyik címe alá tartozik ez a rendelkezés?",
                               prefer=titles_in_chapter.get(chapter(u) or "", []))
                if it is None:
                    why[f"{fam} kimarad: kevés jelölt"] += 1
                    continue
                rows[fam].append(it)
                why[f"{fam} " + ("X" if it["gold"] is None else "ok")] += 1
                n += 1
    rep: dict[str, dict] = {"szures": dict(why)}
    for fam, rs in rows.items():
        bad = [(r["id"], e) for r in rs if (e := validate(r))]
        if bad:
            raise SystemExit(f"{fam}: {len(bad)} sémahiba, pl. {bad[:3]}")
        dup = Counter(r["id"] for r in rs).most_common(1)
        if dup and dup[0][1] > 1:
            raise SystemExit(f"{fam}: ismétlődő id {dup}")
        (OUT / f"{fam}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rs), encoding="utf-8")
        rep[fam] = {"n": len(rs), "torveny": len({r["meta"]["njt"] for r in rs}),
                    "split": dict(Counter(r["split"] for r in rs)),
                    "x_arany": sum(r["gold"] is None for r in rs) / max(1, len(rs)),
                    "opcioszam": dict(sorted(Counter(len(r["options"]) for r in rs).items()))}
        print(fam, json.dumps(rep[fam], ensure_ascii=False))
    print(json.dumps(rep["szures"], ensure_ascii=False))
    (OUT / "adapter_njt_riport.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
