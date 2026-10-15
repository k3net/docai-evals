"""03-as kör — a MILQA és a HuRC forrásadaptere a közös sémára (03-runbook 3.1, F0).

Mindkét forrásnál a jelöltek a saját szövegből jönnek, modell nélkül:

  MILQA (qa.milqa)    choice: a kérdés rövid válasza a gold, a disztraktorok ugyanannak a bekezdésnek a többi kérdésére
                      adott rövid válaszok (felületesen közeli, a szövegben szereplő részletek). A megválaszolhatatlan
                      kérdés (`is_impossible`, válasz nélkül) X, természetes (2. típus).
                      noul: az eldöntendő kérdések (válaszjelölés csak „Igen” vagy csak „Nem”); a „Nincs válasz”
                      jelölésű eldöntendő kérdés X, természetes.
                      Kimarad: a több rövid válaszú (listás), a „Más a pontos válasz” / „Aritmetika” jelölésű (a
                      szövegrészlet nem maga a válasz), a vegyes jelölésű és a válasz mellett is megválaszolhatatlannak
                      jelölt kérdés.
  HuRC (qa.hurc)      choice: cloze entitásválasztás. A gold a MASK (a mondatbeli, ragozott alak), a disztraktorok a
                      bevezető és a cikk nagybetűs névkifejezései. Csak az az item marad, ahol a gold szó szerint
                      szerepel a szövegben; különben a „szövegben nem szereplő opció a jó” shortcut lenne. Kimarad
                      minden jelölt, amely a golddal közös szótövű (5 betűs előtag), annak betűszava, vagy a gold
                      valamelyik előfordulása mellett áll (±25 karakter), vagy elírt/ragozott változata (fuzzy): ezek a
                      gold változatai vagy névrészei lehetnek. Kimaradnak a nagybetűs funkciószavak (STOP) és a
                      mondatkezdő köznevek (a teljes HuRC kis- és nagybetűs gyakorisága szerint, Lexicon). A
                      betűszó-összetételt (PTE ↔ Pécsi Tudományegyetem) ez nem fogja meg: arra az F1 modelles
                      szinonimaszűrője (4.3) való, a gold-drop itemek ezt a jelölést viszik. A disztraktorok fele lehetőleg a golddal azonos végződésű (a ragegyezés
                      shortcutja ellen). Az itemek 20%-a gold-drop X (1. típus); a modelles szinonimaszűrés (4.3) az
                      F1-ben fut rájuk.

Splitek:
  MILQA: csak a train-je van letöltve (a test tilos, 3.1). A cikk (title) sha256-ja szerint 10% val, 10% teszt-ID, a
         többi train; egy cikk minden kérdése egy splitbe kerül.
  HuRC:  a forrás val-ja a teszt-ID (a test címkéi rejtettek); a forrás train-jéből a cikk szövegének hash-e szerint
         10% val, a többi train.

  python3 kor03/eszkozok/adapter_qa.py      # → kor03/adat/f0/qa.{milqa,hurc}.jsonl + adapter_qa_riport.json
"""

from __future__ import annotations

import difflib
import hashlib
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kozos03 import MAX_OPTIONS, noul_options, validate  # noqa: E402  (a MAX_OPTIONS a common-ból)

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "forras/hf"
OUT = ROOT / "adat/f0"
SEED = 20261009
HURC_XDROP = 20  # %


def h100(s: str) -> int:
    return int(hashlib.sha256(s.encode()).hexdigest(), 16) % 100


def norm(s: str) -> str:
    return re.sub(r"[^\w]+", " ", s.lower()).strip()


def overlaps(a: str, b: str) -> bool:
    na, nb = norm(a), norm(b)
    return not na or not nb or na in nb or nb in na


def options_with(gold_text: str | None, distractors: list[str], rnd: random.Random) -> tuple[list[dict], str | None]:
    texts = distractors + ([gold_text] if gold_text is not None else [])
    rnd.shuffle(texts)
    opts = [{"id": f"o{i + 1}", "text": t} for i, t in enumerate(texts)]
    gold = next((o["id"] for o in opts if o["text"] == gold_text), None) if gold_text is not None else None
    return opts, gold


# --- MILQA ---------------------------------------------------------------------------------------------------------

SKIP_TYPES = {"Más a pontos válasz", "Aritmetika"}


def milqa_types(answers: dict) -> set[str]:
    t = set()
    for a in answers.get("short", []) + answers.get("long", []):
        x = a.get("type")
        x = json.loads(x) if isinstance(x, str) else (x or [])
        t |= set(x)
    return t


def milqa_split(title: str) -> str:
    v = h100("milqa:" + title)
    return "val" if v < 10 else "test-id" if v < 20 else "train"


def milqa() -> tuple[list[dict], Counter]:
    data = json.loads((SRC / "SzegedAI/MILQA/train.MILQA-2023-03-27.squad.s.json").read_text(encoding="utf-8"))["data"]
    rows, why = [], Counter()
    for ai, art in enumerate(data):
        split = milqa_split(art["title"])
        for pi, par in enumerate(art["paragraphs"]):
            # a bekezdés rövid válaszai: ezekből lesznek a disztraktorok
            pool = []
            for q in par["qas"]:
                for a in (q.get("answers") or {}).get("short", []):
                    t = a["text"].strip()
                    if t and all(norm(t) != norm(p) for p in pool):
                        pool.append(t)
            for qi, q in enumerate(par["qas"]):
                ans = q.get("answers") or {}
                short, long_ = ans.get("short", []), ans.get("long", [])
                types = milqa_types(ans)
                sid = f"{ai}:{pi}:{qi}"
                iid = f"qa.milqa:{sid}"
                rnd = random.Random(f"{SEED}:{iid}")
                base = {"id": iid, "family": "qa.milqa", "group": "qa", "source": "MILQA", "source_license": "CC-BY-SA-4.0",
                        "source_ref": f"train:{sid}", "split": split, "group_id": f"qa.milqa:{art['title']}", "lang": "hu",
                        "state": par["context"], "question": q["question"], "ketertelmu": False, "soft": None,
                        "x_type": None, "meta": {"milqa_cim": art["title"]}}
                yn = types & {"Igen", "Nem", "Nincs válasz"}
                if q["is_impossible"] and (short or long_):
                    why["kimarad: megválaszolhatatlan, mégis van válasza"] += 1
                    continue
                if types & SKIP_TYPES:
                    why["kimarad: más a pontos válasz / aritmetika"] += 1
                    continue
                if yn:
                    if len(yn) != 1 or q["is_impossible"]:
                        why["kimarad: vegyes eldöntendő jelölés"] += 1
                        continue
                    g = {"Igen": "igen", "Nem": "nem", "Nincs válasz": None}[next(iter(yn))]
                    rows.append({**base, "kind": "noul", "options": noul_options("hu"), "gold": g,
                                 "x_type": None if g else "natural"})
                    why["noul" + (" X" if g is None else "")] += 1
                    continue
                if q["is_impossible"]:
                    cands = list(pool)
                    rnd.shuffle(cands)
                    k = rnd.randint(2, MAX_OPTIONS) if len(cands) >= 2 else 0
                    if k == 0:
                        why["kimarad: X, kevés jelölt"] += 1
                        continue
                    opts, _ = options_with(None, cands[:k], rnd)
                    rows.append({**base, "kind": "choice", "options": opts, "gold": None, "x_type": "natural"})
                    why["choice X"] += 1
                    continue
                if len(short) != 1:
                    why["kimarad: " + ("nincs rövid válasz" if not short else "listás válasz")] += 1
                    continue
                gold = short[0]["text"].strip()
                cands = [p for p in pool if not overlaps(p, gold)]
                if not cands:
                    why["kimarad: nincs disztraktor"] += 1
                    continue
                rnd.shuffle(cands)
                k = rnd.randint(1, min(MAX_OPTIONS - 1, len(cands)))
                opts, g = options_with(gold, cands[:k], rnd)
                rows.append({**base, "kind": "choice", "options": opts, "gold": g})
                why["choice"] += 1
    return rows, why


# --- HuRC ----------------------------------------------------------------------------------------------------------

CAP = "ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÖŐÚÜŰ"
# nagybetűvel is gyakori funkciószavak (idézet, felsorolás után): soha nem jelöltek
STOP = set("""a az egy ez ezt ezzel ezek azok de és is hogy ha mint míg most már nem sem se ott itt akkor amikor bár mert
pedig szerinte szerint ugyanakkor emellett továbbá közben majd így ilyen ami aki amely amelyet akik amelyek ő ők mi ki
mit hol mikor miért hogyan minden sok több csak még vagy illetve valamint tavaly idén jelenleg korábban később végül
először ezért azért ezen azon abban ebben arra erre ennek annak neki nekik ráadásul igen nos persze mindez mindezt
egyik másik néhány senki semmi valaki valami""".split())
TOKEN = re.compile(r"\w[\w.\-]*")


def tokens_with_flags(text: str) -> list[tuple[str, bool]]:
    """(token, mondatkezdő-e) párok, a záró pont és kötőjel nélkül. Mondatkezdő: a szöveg vagy egy sor eleje, a
    ponttal záruló token utáni szóköz, és a !?…: utáni token."""
    out, prev_end, prev_raw = [], 0, ""
    for m in TOKEN.finditer(text):
        gap = text[prev_end:m.start()]
        initial = (not out or "\n" in gap or bool(re.search(r"[!?…:]", gap))
                   or (prev_raw.endswith(".") and gap[:1].isspace()))
        out.append((m.group(0).rstrip(".-"), initial))
        prev_end, prev_raw = m.end(), m.group(0)
    return out


class Lexicon:
    """A teljes HuRC-szövegből: egy szóalak hányszor áll kisbetűvel, és hányszor nagybetűvel nem mondat elején. Ha a
    kisbetűs alak a gyakoribb (több mint kétszer), a nagybetűs előfordulás mondatkezdő vagy idézetkezdő köznév."""

    def __init__(self) -> None:
        self.low: Counter = Counter()
        self.cap: Counter = Counter()

    def add(self, text: str) -> None:
        for t, ini in tokens_with_flags(text):
            if t[:1].islower():
                self.low[t] += 1
            elif t[:1] in CAP and not ini:
                self.cap[t.lower()] += 1

    def common(self, t: str) -> bool:
        lw = t.lower()
        return lw in STOP or self.low[lw] > 2 * self.cap[lw]


LEX = Lexicon()


def entity_spans(text: str) -> list[str]:
    toks = tokens_with_flags(text)
    is_cap = [bool(t) and t[0] in CAP for t, _ in toks]
    spans, i = [], 0
    while i < len(toks):
        if not is_cap[i]:
            i += 1
            continue
        j = i
        # a futás nem lépi át a mondathatárt
        while j + 1 < len(toks) and is_cap[j + 1] and not toks[j + 1][1] and j - i < 3:
            j += 1
        run = [t for t, _ in toks[i:j + 1]]
        while run and LEX.common(run[0]):
            run = run[1:]
        while run and (run[-1].lower() in STOP or len(run[-1]) == 1):
            run = run[:-1]
        if run:
            spans.append(" ".join(run))
        i = j + 1
    seen, out = set(), []
    for s in spans:
        if len(s) >= 2 and s not in seen:
            seen.add(s)
            out.append(s)
    return out


def stems(s: str) -> set[str]:
    return {w.lower()[:5] for w in re.findall(r"\w+", s) if len(w) >= 4}


def acronym_of(short: str, long_: str) -> bool:
    words = re.findall(r"\w+", long_)
    return short.isupper() and len(short) >= 2 and len(words) >= 2 and "".join(w[0] for w in words).upper() == short


def near_gold(c: str, gold: str, text: str, window: int = 25) -> bool:
    """A jelölt a gold valamelyik előfordulásának ±window karakteres környezetében áll: ugyanannak a névnek a része
    lehet (pl. „Lula da Silva”: Lula ↔ Silva)."""
    for m in re.finditer(r"(?<!\w)" + re.escape(gold) + r"(?!\w)", text):
        if re.search(r"(?<!\w)" + re.escape(c) + r"(?!\w)", text[max(0, m.start() - window):m.end() + window]):
            return True
    return False


def fuzzy_token(c: str, gold: str) -> bool:
    """Elírt vagy ragozott névváltozat (pl. Fujimori ↔ Fuhimoriként): a jelölt-token eleje ≥ 0,8 hasonlóságú a
    gold-tokenhez."""
    for g in re.findall(r"\w{4,}", gold.lower()):
        for t in re.findall(r"\w{4,}", c.lower()):
            if difflib.SequenceMatcher(None, g, t[: len(g) + 1]).ratio() >= 0.8:
                return True
    return False


def related(c: str, gold: str, text: str) -> bool:
    return (bool(stems(c) & stems(gold)) or overlaps(c, gold) or acronym_of(c, gold) or acronym_of(gold, c)
            or fuzzy_token(c, gold) or near_gold(c, gold, text))


def suffix_len(a: str, b: str) -> int:
    n = 0
    while n < 3 and n < min(len(a), len(b)) and a[-1 - n].lower() == b[-1 - n].lower():
        n += 1
    return n


def hurc() -> tuple[list[dict], Counter]:
    rows, why = [], Counter()
    datas = {s: json.loads((SRC / f"NYTK/HuRC/data/hurc_{s}.json").read_text(encoding="utf-8")) for s in ("train", "val")}
    for data in datas.values():
        for r in data:
            LEX.add("\n".join(r["lead"] + r["passage"]))
    # a forrásban egy cikk a train-ben és a val-ban is előfordulhat: a train-oldali példány kimarad (a val a teszt-ID)
    val_ph = {hashlib.sha256(" ".join(r["passage"]).encode()).hexdigest() for r in datas["val"]}
    for src_split, data in datas.items():
        for r in data:
            if src_split == "train" and hashlib.sha256(" ".join(r["passage"]).encode()).hexdigest() in val_ph:
                why["kimarad: a cikk a forrás val-jában is szerepel"] += 1
                continue
            text = "\n".join(r["lead"] + r["passage"])
            gold = r["MASK"].strip()
            if not re.search(r"(?<!\w)" + re.escape(gold) + r"(?!\w)", text):
                why["kimarad: a gold nincs szó szerint a szövegben"] += 1
                continue
            ph = hashlib.sha256(" ".join(r["passage"]).encode()).hexdigest()
            split = "test-id" if src_split == "val" else ("val" if int(ph, 16) % 100 < 10 else "train")
            iid = f"qa.hurc:{src_split}:{r['id']}"
            rnd = random.Random(f"{SEED}:{iid}")
            cands = [c for c in entity_spans(text) if not related(c, gold, text)]
            if len(cands) < 2:
                why["kimarad: kevés jelölt"] += 1
                continue
            rnd.shuffle(cands)
            cands.sort(key=lambda c: -min(suffix_len(c, gold), 2))  # stabil: az azonos végződésűek előre
            xdrop = h100(f"hurc-x:{iid}") < HURC_XDROP
            k = rnd.randint(2 if xdrop else 1, min(MAX_OPTIONS - (0 if xdrop else 1), len(cands)))
            head = cands[: (k + 1) // 2]
            rest = cands[(k + 1) // 2:]
            rnd.shuffle(rest)
            chosen = head + rest[: k - len(head)]
            opts, g = options_with(None if xdrop else gold, chosen, rnd)
            q = r["query"].replace("[MASK]", "___")
            rows.append({"id": iid, "family": "qa.hurc", "group": "qa", "source": "HuRC", "source_license": "CC-BY-4.0",
                         "source_ref": f"{src_split}:{r['id']}", "split": split, "group_id": f"qa.hurc:{ph[:16]}",
                         "lang": "hu", "kind": "choice", "state": text,
                         "question": f"Melyik kifejezés illik a ___ helyére? „{q}”", "options": opts, "gold": g,
                         "x_type": "gold-drop" if xdrop else None, "ketertelmu": False, "soft": None,
                         "meta": {"hurc_gold": gold, "szinonimaszures": "F1"} if xdrop else {}})
            why["choice X" if xdrop else "choice"] += 1
    return rows, why


def report(rows: list[dict], why: Counter) -> dict:
    return {"n": len(rows), "ok": dict(why), "split": dict(Counter(r["split"] for r in rows)),
            "kind": dict(Counter(r["kind"] for r in rows)),
            "x_arany": sum(r["gold"] is None for r in rows) / max(1, len(rows)),
            "opcioszam": dict(sorted(Counter(len(r["options"]) for r in rows).items()))}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rep = {}
    for family, fn in (("qa.milqa", milqa), ("qa.hurc", hurc)):
        rows, why = fn()
        bad = [(r["id"], e) for r in rows if (e := validate(r))]
        if bad:
            raise SystemExit(f"{family}: {len(bad)} sémahiba, pl. {bad[:3]}")
        (OUT / f"{family}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                                             encoding="utf-8")
        rep[family] = report(rows, why)
        print(family, json.dumps(rep[family], ensure_ascii=False))
    (OUT / "adapter_qa_riport.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
