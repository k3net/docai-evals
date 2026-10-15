"""03-as kör — a források listája, licence és rögzített revíziója (03-runbook 3. pont, F0).

A lista a runbook 3. pontjából jön. A HF-en lévő forrásoknál a HF-API adja a licencet (a `license:` címke és a kártya
`license` mezője), a gated állapotot és a commitot, amelyre a letöltés rögzül. Ahol a HF-licenc hiányzik vagy eltér a
runbookétól, a sor `ellenorzendo` jelzést kap, és a szigorúbbat követjük. A nem HF-forrásoknál (GitHub, TED, NJT,
KN/VTSZ, Wikipédia) a licenc kézi, a forrás-URL-lel.

  python3 kor03/eszkozok/forrasok03.py      # → kor03/forras/forrasok03.json + forrasok03.md
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "forras"

# (név, hely, runbook-licenc, csoport, szerep) — szerep: train | eval | ho (kitartott csoport) | kizarva
SOURCES = [
    ("HuRTE", "hf:NYTK/HuRTE", "CC-BY-SA-4.0", "nli", "train; a val a teszt"),
    ("HuCOLA", "hf:NYTK/HuCOLA", "CC-BY-SA-4.0", "szentiment", "train; a val a teszt"),
    ("HuWNLI", "hf:NYTK/HuWNLI", "CC-BY-SA-4.0", "nli", "train; a val a teszt"),
    ("HuCommitmentBank", "hf:NYTK/HuCommitmentBank", "CC-BY-SA-4.0", "nli", "train; a val a teszt; „nem eldönthető” → X"),
    ("HuSST", "hf:NYTK/HuSST", "CC-BY-SA-4.0", "szentiment", "train; a val a teszt (HF: BSD-2, GitHub: CC-BY-SA → a szigorúbb)"),
    ("HuCoPA", "hf:NYTK/HuCoPA", "BSD-2-Clause", "qa", "train"),
    ("HuRC", "hf:NYTK/HuRC", "CC-BY-4.0", "qa", "train; cloze entitásválasztás + gold-drop X"),
    ("HuBoolQ", "hf:NYTK/HuBoolQ", "CC-BY-SA-3.0", "kizarva",
     "kizárva: Google Translate + GPT-4o mini átírás (3.6: csak Apache-2.0 fordító, zárt modell kimenete nem)"),
    ("MILQA", "hf:SzegedAI/MILQA", "CC-BY-SA-4.0", "qa", "train; a test tilos; megválaszolhatatlan → X"),
    ("MultiEURLEX", "hf:coastalcph/multi_eurlex", "CC-BY-SA-4.0", "jogi",
     "train; HO-forrás jelölt; a `refs/convert/parquet` ág `hu` konfigurációja"),
    ("NerKor", "url:https://github.com/nytud/NYTK-NerKor", "CC-BY-SA-4.0", "entitas", "train"),
    ("Belebele", "hf:facebook/belebele", "CC-BY-SA-4.0", "eval", "csak eval (hun_Latn)"),
    ("SIB-200", "hf:Davlan/sib200", "CC-BY-SA-4.0", "eval", "csak eval (hun_Latn); FLORES-szöveg"),
    ("MASSIVE", "hf:AmazonScience/massive", "CC-BY-4.0", "routing", "ho (routing-csoport)"),
    ("TED-hirdetmények", "url:https://ted.europa.eu/en/help/data-reuse", "EU-2011/833", "kozbeszerzes",
     "train; egy CPV-főcsoport HO-forrás; PII-szűrés"),
    ("Nemzeti Jogszabálytár", "url:https://njt.jog.gov.hu", "HU-Szjt-1-4", "jogi",
     "train; rögzített jogszabálylista, kíméletes letöltés (robots.txt: a /jogszabaly/* engedett)"),
    ("KN/VTSZ leírások", "url:https://eur-lex.europa.eu", "EU-2011/833", "termek", "ho (termék-csoport)"),
    ("Wikipédia (hu)", "hf:wikimedia/wikipedia", "CC-BY-SA-3.0", "konstrukcios",
     "train (konstrukciós forrásszöveg); a 20231101.hu pillanatkép egy shardja"),
    ("tasksource-jev-typed-decisions", "hf:tasksource/tasksource-jev-typed-decisions", "soronkent", "angol_gerinc",
     "train: a `full` konfiguráció (a `default` keverékét Jev-ítéletek súlyozták), csak license_use == commercial; a "
     "routing-, termék- és KIE-rokon források kiszűrve (kitartás-lista)"),
    ("procedural-typed-decisions", "hf:tasksource/procedural-typed-decisions", "Apache-2.0", "angol_gerinc",
     "train: 9 feladat; az arithmetic, a record_aggregation, a table_lookup (KIE/validáció-rokon) és a "
     "taxonomy_routing (routing) kimarad"),
    ("helmo synthetic-typed-decisions", "hf:helmo/synthetic-typed-decisions", "MIT", "kizarva",
     "kizárva: a címkéket a DeepSeek-V4-Flash generátor írta, ellenőrzés nélkül (9.: generátor csak Apache-2.0; "
     "4.1: tanárcél csak kapun átment tanártól)"),
    ("Open-Jev (CC0)", "hf:ZefanCai/Open-Jev", "CC0-1.0", "angol_gerinc",
     "train: 7 kontroll-konfiguráció; a release-v2 és a browser-drone (ügyfélszolgálati routing, ellenőrizetlen "
     "licencű leírások) és az amount/email/phone-extraction (KIE) kimarad"),
    ("LocalLLaMA typed-decisions", "hf:LocalLLaMA/typed-decisions", "Apache-2.0", "eval", "csak eval (test)"),
    ("fastino fast-decisions", "hf:fastino/fast-decisions", "Apache-2.0", "eval", "csak eval"),
    ("tasksource synthetic-typed-decisions", "hf:tasksource/synthetic-typed-decisions", "Apache-2.0", "kizarva",
     "kizárva: Jev-desztilláció"),
    ("OpinHuBank", "url:https://metashare.nytud.hu", "tisztazatlan", "kizarva", "kizárva: tisztázatlan licenc"),
]

# kézi megállapítások, ahol a HF-metaadat hiányzik vagy ellentmond (2026-10-09)
MANUAL = {
    "HuRTE": "CC-BY-SA-4.0: a HF-kártya szövege („This work is licensed under … CC BY-SA 4.0”), metaadat-címke nélkül",
    "HuCommitmentBank": "CC-BY-SA-4.0: a HF-kártya szövege („released under the CC-BY-SA-4.0 License”), metaadat-címke nélkül",
    "HuSST": "a HF-metaadat BSD-2-Clause, a GitHub-repó (nytud/HuSST) CC-BY-SA-4.0: a szigorúbbat követjük",
    "Wikipédia (hu)": "kettős licenc (CC-BY-SA-3.0 és GFDL): a CC-BY-SA-3.0-t választjuk",
}
NOTES_NONHF = {
    "NerKor": "CC-BY-SA-4.0 a GitHub-API szerint (2026-10-09); commit 7c9c5b5f",
    "Nemzeti Jogszabálytár": "a jogszabályszöveg nem védett (Szjt. 1. § (4)), közkincs (Dani, 2026-10-09)",
}

NORM = {"cc-by-sa-4.0": "CC-BY-SA-4.0", "cc-by-4.0": "CC-BY-4.0", "cc-by-sa-3.0": "CC-BY-SA-3.0", "mit": "MIT",
        "apache-2.0": "Apache-2.0", "bsd-2-clause": "BSD-2-Clause", "cc0-1.0": "CC0-1.0", "other": "other"}


def hf_info(repo: str) -> dict:
    with urllib.request.urlopen(f"https://huggingface.co/api/datasets/{repo}", timeout=30) as r:
        d = json.loads(r.read())
    tags = [t.split(":", 1)[1] for t in d.get("tags", []) if t.startswith("license:")]
    card = (d.get("cardData") or {}).get("license")
    card = card if isinstance(card, list) else [card] if card else []
    lic = sorted({NORM.get(str(x).lower(), str(x)) for x in tags + card if x})
    return {"hf_license": lic, "gated": d.get("gated") or False, "sha": d.get("sha"),
            "last_modified": d.get("lastModified"), "files": len(d.get("siblings") or [])}


def main() -> None:
    prev_path = OUT / "forrasok03.json"
    prev = {r["name"]: r for r in json.loads(prev_path.read_text())} if prev_path.exists() else {}
    rows = []
    for name, where, lic, group, role in SOURCES:
        row = {"name": name, "where": where, "runbook_license": lic, "group": group, "role": role}
        if where.startswith("hf:"):
            try:
                row |= hf_info(where[3:])
            except Exception as e:  # noqa: BLE001
                row["error"] = str(e)
            hl = row.get("hf_license") or []
            if not hl:
                row["status"] = "ellenorzendo: a HF-en nincs licenc"
            elif lic not in hl and lic not in ("soronkent",):
                row["status"] = f"ellenorzendo: a HF szerint {', '.join(hl)}"
            else:
                row["status"] = "ok"
            if name in MANUAL:
                row["status"] = f"ok (kézi): {MANUAL[name]}"
            if row.get("gated"):
                row["status"] += "; gated"
        else:
            row["status"] = "kézi" if lic not in ("ellenorzendo", "tisztazatlan") else lic
            if name in NOTES_NONHF:
                row["status"] += f": {NOTES_NONHF[name]}"
        # a korábban rögzített commit marad (a letöltés arra történt); ha a HEAD azóta elmozdult, jelezzük
        if prev.get(name, {}).get("sha") and row.get("sha") and prev[name]["sha"] != row["sha"]:
            row["head_sha"], row["sha"] = row["sha"], prev[name]["sha"]
            row["status"] += "; a HEAD azóta elmozdult"
        rows.append(row)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "forrasok03.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    md = ["| forrás | hely | licenc (runbook) | HF-licenc | csoport | szerep | állapot | commit |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['name']} | `{r['where']}` | {r['runbook_license']} | {', '.join(r.get('hf_license') or []) or '—'} | "
                  f"{r['group']} | {r['role']} | {r['status']} | {(r.get('sha') or '—')[:10]} |")
    (OUT / "forrasok03.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
