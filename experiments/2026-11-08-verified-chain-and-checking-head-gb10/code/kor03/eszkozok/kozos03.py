"""03-as kör — közös itemséma, validálás és promptkeret (03-runbook 2. és 5. pont).

Egy 03-as item a családtól függetlenül ugyanazt a sémát követi:

  id            globálisan egyedi, családelőtaggal
  family        pl. `nli.hurte`, `termek.szamlasor_cikk`
  group         családcsoport (5. pont) — a kitartás egysége
  source, source_license, source_ref
                a forrás neve, licence (LICENSES) és a forrásbeli azonosító
  split         train | val | test-id | ho-termek | ho-routing | ho-uj | ho-forras | eval-kulso
  group_id      közös split-egység: permutációk, ellentényes párok, egy állapot összes kérdése
  lang          hu | en
  kind          choice | noul (kétopciós igen/nem, plusz X)
  state         az állapot szövege (lehet üres)
  question      a döntési kérdés
  options       2–10 opció: {id, text, use_when?}
  gold          opció-id, vagy None = X („egyik sem”)
  x_type        X-gold esetén: gold-drop | natural | out-of-scope | missing-precondition (2. pont)
  ketertelmu    nem pontozott; `soft` adja a puha célt
  native        a kitartott 00/01 itemeknél az eredeti item és a keret neve ("00" | "01"): ezekre az elsődleges
                prompt a saját, eredeti promptjuk (2. pont), bájtra azonos a mérttel (test_kozos03.py)
  meta          forrásspecifikus mezők

A kimenet minden kereten egyetlen címketoken: A…J az opciókra a megjelenítési sorrendben, X az „egyik sem”.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "eszkozok"))
from common import MAX_OPTIONS, NONE_TEXT, SYSTEM_PROMPT, labels_for, messages_for  # noqa: E402

GROUPS = ("termek", "routing", "kie", "nli", "szentiment", "qa", "jogi", "kozbeszerzes", "level", "rag", "entitas",
          "konstrukcios", "angol_gerinc")
HELD_OUT = {"termek": "ho-termek", "routing": "ho-routing", "kie": "ho-uj"}
SPLITS = ("train", "val", "test-id", "ho-termek", "ho-routing", "ho-uj", "ho-forras", "eval-kulso")
KINDS = ("choice", "noul")
X_TYPES = ("gold-drop", "natural", "out-of-scope", "missing-precondition")
# HU-Szjt-1-4: a jogszabályszöveg nem áll szerzői jogi védelem alatt (Szjt. 1. § (4)), NJT
LICENSES = ("Apache-2.0", "MIT", "CC0-1.0", "CC-BY-3.0", "CC-BY-4.0", "CC-BY-SA-3.0", "CC-BY-SA-4.0", "BSD-2-Clause",
            "BSD-3-Clause", "ODC-BY-1.0", "EU-2011/833", "HU-Szjt-1-4", "konstrukcio")

GENERIC = {
    "hu": {"system": SYSTEM_PROMPT, "state": "Állapot:", "question": "Kérdés", "options": "Opciók:",
           "none": NONE_TEXT["alap"], "yes": "Igen", "no": "Nem"},
    "en": {"system": "You are a decision model. Answer with a single letter: the letter of the chosen option.",
           "state": "State:", "question": "Question", "options": "Options:", "none": "None of these",
           "yes": "Yes", "no": "No"},
}


def noul_options(lang: str) -> list[dict]:
    f = GENERIC[lang]
    return [{"id": "igen", "text": f["yes"]}, {"id": "nem", "text": f["no"]}]


def validate(item: dict) -> list[str]:
    """A séma megsértései (üres lista = érvényes)."""
    err = []
    for k in ("id", "family", "group", "source", "source_license", "split", "group_id", "lang", "kind", "question",
              "options"):
        if item.get(k) in (None, "", []):
            err.append(f"hiányzó mező: {k}")
    if err:
        return err
    if item["group"] not in GROUPS:
        err.append(f"ismeretlen csoport: {item['group']}")
    if item["split"] not in SPLITS:
        err.append(f"ismeretlen split: {item['split']}")
    if item["lang"] not in GENERIC:
        err.append(f"ismeretlen nyelv: {item['lang']}")
    if item["kind"] not in KINDS:
        err.append(f"ismeretlen kind: {item['kind']}")
    if item["source_license"] not in LICENSES:
        err.append(f"nem engedett licenc: {item['source_license']}")
    if item["group"] in HELD_OUT and item["split"] not in (HELD_OUT[item["group"]], "eval-kulso"):
        err.append(f"a {item['group']} csoport kitartott, a split csak {HELD_OUT[item['group']]} lehet")
    ids = [o.get("id") for o in item["options"]]
    lo = 1 if "native" in item else 2  # a 01-ben az egyeszközös item is döntés: hívja, vagy X
    if not lo <= len(ids) <= MAX_OPTIONS:
        err.append(f"opciószám {len(ids)} ({lo}–{MAX_OPTIONS})")
    if len(set(ids)) != len(ids) or None in ids:
        err.append("ismétlődő vagy hiányzó opció-id")
    if item["kind"] == "noul" and ids != ["igen", "nem"]:
        err.append("noul: az opciók igen/nem")
    gold = item.get("gold")
    if gold is not None and gold not in ids:
        err.append("a gold nincs az opciók közt")
    if gold is None and not item.get("ketertelmu") and item.get("x_type") not in X_TYPES:
        err.append("X-gold x_type nélkül")
    if gold is not None and item.get("x_type"):
        err.append("x_type nem-X golddal")
    if item.get("ketertelmu") and not item.get("soft"):
        err.append("kétértelmű item soft nélkül")
    if "native" in item and item["native"].get("frame") not in ("00", "01"):
        err.append("ismeretlen natív keret")
    return err


# --- prompt ------------------------------------------------------------------------------------------------------

def generic_user(item: dict, order: list[str | None]) -> str:
    f = GENERIC[item["lang"]]
    opts = {o["id"]: o for o in item["options"]}
    lines = []
    if item.get("state"):
        lines += [f["state"], item["state"].strip(), ""]
    lines += [f"{f['question']}: {item['question']}", f["options"]]
    for oid, lab in zip(order, labels_for(order)):
        if oid is None:
            lines.append(f"{lab}) {f['none']}")
            continue
        o = opts[oid]
        lines.append(f"{lab}) {o['text']}" + (f" — {o['use_when']}" if o.get("use_when") else ""))
    return "\n".join(lines)


def messages(item: dict, order: list[str | None], frame: str = "auto") -> list[dict]:
    """A chat-üzenetek. `frame`: native (a 00/01 eredeti promptja), generic, vagy auto (native, ha van)."""
    if frame == "auto":
        frame = "native" if "native" in item else "generic"
    if frame == "native":
        return messages_for(item["native"]["item"], order)
    if frame != "generic":
        raise ValueError(frame)
    return [{"role": "system", "content": GENERIC[item["lang"]]["system"]},
            {"role": "user", "content": generic_user(item, order)}]


def default_order(item: dict) -> list[str | None]:
    return [o["id"] for o in item["options"]] + [None]


# --- a kitartott 00/01 itemek a közös sémában -----------------------------------------------------------------------

X_FAJTA_00 = {"a": "gold-drop", "a-termeszetes": "gold-drop", "b": "out-of-scope"}


def from_00(it: dict) -> dict:
    """A 00 (számlasor → cikk) itemje; a split a HO-termék, a gold és az opció-id-k változatlanok. Az X-fajták
    (00-runbook 4.2): X(a) kényszerített és X(a)-természetes (visszakeresési hiba) → gold-drop, mert a valódi cikk
    létezik, csak nincs a listán; X(b) új termék, amelyhez nincs cikk → out-of-scope."""
    c = it["context"]
    state = (f"Számlasor: \"{c['sor']}\"\nSzállító: {c['szallito']} · Mennyiség: {c['mennyiseg']} {c['egyseg']} · "
             f"Nettó egységár: {c['egysegar']} Ft")
    m = it.get("meta") or {}
    return {"id": f"00:{it['id']}", "family": "termek.szamlasor_cikk", "group": "termek",
            "source": "k3dani/hu-invoice-catalog-decisions", "source_license": "CC-BY-4.0", "source_ref": it["id"],
            "split": "ho-termek", "group_id": f"00:{m.get('article') or it['id']}", "lang": "hu", "kind": "choice",
            "state": state, "question": "Melyik cikktörzs-tételhez tartozik a számlasor?",
            "options": [{"id": o["id"], "text": f"{o['text']} [{o['path']}]"} for o in it["options"]],
            "gold": it["gold"],
            "x_type": X_FAJTA_00[m["x_fajta"]] if it["gold"] is None and not m.get("ketertelmu") else None,
            "ketertelmu": bool(m.get("ketertelmu")), "soft": m.get("soft"),
            "native": {"frame": "00", "item": it}, "meta": {"reteg": it["split"], "x_fajta00": m.get("x_fajta")}}


X_FAJTA_01 = {"gold-drop": "gold-drop", "csevegés": "out-of-scope"}
LICENSE_01 = {"katalogus_hu": "Apache-2.0"}


def x_type_01(it: dict) -> str | None:
    """A 01 X-itemjeinek típusa. A BFCL irrelevancia és a When2Call `cannot_answer` („egyik eszköz sem illik”)
    hatókörön kívüli kérés; a MASSIVE kitartott intentje (x_fajta nélkül) és a csevegés szintén; a gold-drop az."""
    m = it.get("meta") or {}
    if it["gold"] is not None or m.get("ketertelmu"):
        return None
    if it["forras"].startswith(("bfcl", "w2c")):
        return "out-of-scope"
    return X_FAJTA_01.get(m.get("x_fajta") or "", "out-of-scope")


def from_01(it: dict) -> dict:
    """A 01 (eszközválasztás) itemje; a split a HO-routing."""
    m = it.get("meta") or {}
    hist = " / ".join(x.get("content") or "" for x in it.get("history") or [] if (x.get("content") or "").strip())
    state = (f"{'Előzmény' if it['lang'] == 'hu' else 'Context'}: {hist}\n" if hist else "") + it["request"]
    return {"id": f"01:{it['id']}", "family": "routing.eszkozvalasztas", "group": "routing",
            "source": it["forras"],
            "source_license": "Apache-2.0" if it["forras"].startswith("bfcl") else LICENSE_01.get(it["forras"], "CC-BY-4.0"),
            "source_ref": it["id"], "split": "ho-routing", "group_id": f"01:{m.get('klaszter') or it['id']}",
            "lang": it["lang"], "kind": "choice", "state": state,
            "question": ("Melyik eszközt kell meghívni a felhasználó kérésére?" if it["lang"] == "hu"
                         else "Which tool should be called for the user's request?"),
            "options": [{"id": o["id"], "text": f"{o['name']}: {o['description']}"} for o in it["options"]],
            "gold": it["gold"], "x_type": x_type_01(it), "ketertelmu": bool(m.get("ketertelmu")), "soft": m.get("soft"),
            "native": {"frame": "01", "item": it}, "meta": {"forras": it["forras"], "split01": it["split"]}}
