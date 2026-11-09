"""05-ös kör — a 03 itemjeinek tartalmi állapota (05-runbook 2.2; a 04-runbook 3.3 leképezése).

A szabály konstrukció és forrás szerint dönt, itemenkénti átsorolás nélkül:

  MATCH          a gold egy opció (a kétértelmű itemeknél: a `soft` pozitív tagjai az elfogadható halmaz)
  NO_MATCH       gold-drop; natural a `NO_MATCH_NATURAL` családokban (a döntés meghozható, de egyik opció sem jó)
  MISSING_DATA   missing-precondition; natural a `MISSING_NATURAL` családokban (a szöveg nem tartalmazza a döntéshez
                 szükséges adatot)
  OUT_OF_SCOPE   out-of-scope

Az AMBIGUOUS a 03 adatán nem fordul elő (2.3): a 03 promptjai nem mondják ki az egyetlen válasz szabályát.
Ismeretlen natural család hibát ad, nem csendes besorolást.

  python3 kor05/eszkozok/allapot05.py ellenoriz   → a 2.2 táblázatának darabszámai a 03 rétegein (a 04 3.3 ellen)
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]

STATES = ("MATCH", "NO_MATCH", "MISSING_DATA", "OUT_OF_SCOPE", "AMBIGUOUS")
NON_MATCH = STATES[1:]
X_TYPE_STATE = {"gold-drop": "NO_MATCH", "out-of-scope": "OUT_OF_SCOPE", "missing-precondition": "MISSING_DATA"}
NO_MATCH_NATURAL = {"rag.relevancia", "en.proc.state_perturbation", "kie.osszeg"}
# a nli.hucb „neutral”-ja a 04-ben nem szerepelt (nincs az MVP v2-ben); a qa.milqa analógiájára: a szöveg alapján nem
# dönthető el (05-runbook Napló, 2026-10-28)
MISSING_NATURAL = {"qa.milqa", "nli.hucb"}


def content_state(item: dict) -> str:
    if item.get("gold") is not None or item.get("ketertelmu"):
        return "MATCH" if _soft_options(item) or item.get("gold") is not None else "NO_MATCH"
    xt = item.get("x_type")
    if xt in X_TYPE_STATE:
        return X_TYPE_STATE[xt]
    if xt == "natural":
        if item["family"] in NO_MATCH_NATURAL:
            return "NO_MATCH"
        if item["family"] in MISSING_NATURAL:
            return "MISSING_DATA"
        raise ValueError(f"{item['id']}: ismeretlen natural család: {item['family']}")
    raise ValueError(f"{item['id']}: X-gold x_type nélkül ({xt!r})")


def _soft_options(item: dict) -> list[str]:
    s = item.get("soft")
    if isinstance(s, dict):
        return [k for k, v in s.items() if v > 0]
    if isinstance(s, list):
        return [k for k in s if k is not None]
    return []


def gold_set(item: dict) -> list[str]:
    """Az elfogadható kimenetek: opció-id-k, illetve a nem-MATCH állapot neve. A kétértelmű lista-`soft` None tagja
    (az X is elfogadható) NO_MATCH-ként kerül a halmazba."""
    st = content_state(item)
    if not item.get("ketertelmu"):
        return [item["gold"]] if st == "MATCH" else [st]
    out = _soft_options(item)
    if isinstance(item.get("soft"), list) and None in item["soft"]:
        out.append("NO_MATCH")
    return out or [st]


def soft_target(item: dict) -> dict[str, float]:
    """A tanítási cél: a dict-`soft` súlyai, egyébként egyenletes eloszlás a gold-halmazon."""
    s = item.get("soft")
    if item.get("ketertelmu") and isinstance(s, dict):
        z = sum(v for v in s.values() if v > 0)
        return {k: v / z for k, v in s.items() if v > 0}
    g = gold_set(item)
    return {k: 1 / len(g) for k in g}


# --- ellenőrzés a 03 rétegein ----------------------------------------------------------------------------------------

# a 04-runbook 3.3 táblázata (pontozott X-gold itemek) és az MVP v2 X-összetétele
ELVART = {
    "train": {"NO_MATCH": 1037, "MISSING_DATA": 188, "OUT_OF_SCOPE": 394},
    "ho-termek": {"NO_MATCH": 975, "MISSING_DATA": 0, "OUT_OF_SCOPE": 128},
    "ho-routing": {"NO_MATCH": 271, "MISSING_DATA": 0, "OUT_OF_SCOPE": 2183},
    "ho-uj": {"NO_MATCH": 91, "MISSING_DATA": 215, "OUT_OF_SCOPE": 0},
}


def rows(p: Path):
    with open(p, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def scored_layers() -> dict[str, list[dict]]:
    """A 03 v1-rétegei pontosan úgy, ahogy a 03 F4 pontozta őket (`f4_elemzes03.retegek`), itemekkel."""
    sys.path[:0] = [str(EXP / "kor03/eszkozok"), str(EXP / "eszkozok")]
    import f4_elemzes03 as f4  # noqa: PLC0415

    meta = f4.load_meta03()
    kal = {s: v["ids"] for s, v in json.loads((EXP / "kor03/adat/f4/kalib.json").read_text())["retegek"].items()}
    L, _ = f4.retegek(meta, kal)
    items = {it["id"]: it for name in ("val", "eval") for it in rows(EXP / f"kor03/adat/f2/items_{name}.jsonl")}
    return {g: [items[i] for i in L[g] if not meta[i]["ketertelmu"]] for g in ("ho-termek", "ho-routing", "ho-uj")}


def ellenoriz() -> dict:
    layers = {"train": [it for it in rows(EXP / "kor03/adat/f3/mvp_train_v2.jsonl")], **scored_layers()}
    out, ok = {}, True
    for name, its in layers.items():
        c = Counter(content_state(it) for it in its)
        out[name] = {"n": len(its), **{s: c.get(s, 0) for s in STATES}}
        for s, n in ELVART[name].items():
            if c.get(s, 0) != n:
                ok = False
                out[name].setdefault("elteres", {})[s] = {"elvart": n, "kapott": c.get(s, 0)}
    # a többi 03-as split hibamentesen leképezhető (a test-id és a val is: D_meta, D_cal, D_dev)
    for name in ("val", "eval"):
        c = Counter((it["split"], content_state(it)) for it in rows(EXP / f"kor03/adat/f2/items_{name}.jsonl"))
        out[f"osszes:{name}"] = {f"{sp}/{st}": n for (sp, st), n in sorted(c.items())}
    out["ok"] = ok
    return out


if __name__ == "__main__":
    if sys.argv[1:] != ["ellenoriz"]:
        raise SystemExit(__doc__)
    res = ellenoriz()
    print(json.dumps(res, ensure_ascii=False, indent=1))
    if not res["ok"]:
        raise SystemExit("ELTÉRÉS a 04-runbook 3.3 darabszámaitól")
