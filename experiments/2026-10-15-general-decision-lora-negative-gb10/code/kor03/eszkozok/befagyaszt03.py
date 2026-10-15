"""03-as kör — az eval-rétegek befagyasztása (03-runbook 5.: „Befagyasztás mérés előtt, hash-sel”).

Minden F0-családfájl (és ha már van, a szintetikus családok) eval-splitjeinek (teszt-ID, HO-rétegek, külső eval)
itemjeiről rétegenként: darabszám és sha256 (az id szerint rendezett, kanonikus JSON-sorokból). A manifest a modell-
eredmények előtt készül; a mérés előtt a `ellenoriz` újraszámolja, és eltérésnél hibával kilép.

  python3 kor03/eszkozok/befagyaszt03.py fagyaszt [--szint]   → adat/befagyasztas03.json (meglévő rétegek nem íródnak felül)
  python3 kor03/eszkozok/befagyaszt03.py ellenoriz
  python3 kor03/eszkozok/befagyaszt03.py ujrafagyaszt --ok "<indok>"
      → a megváltozott rétegek közül CSAK a szintetikus családokéi fagyaszthatók újra, mérési elemzés előtt, indokkal;
        a régi bejegyzés az `archiv` listába kerül (2026-10-10: a Muse-ellenőrző és a „hiányzó feltétel” pótlása)
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
F0, SZ = ROOT / "adat/f0", ROOT / "adat/f1/szint"
MAN = ROOT / "adat/befagyasztas03.json"
EVAL_SPLITS = {"test-id", "ho-termek", "ho-routing", "ho-uj", "ho-forras", "eval-kulso"}


def layers(with_szint: bool) -> dict[str, dict]:
    files = sorted(F0.glob("*.jsonl"))
    if with_szint and SZ.exists():
        files += [p for p in sorted(SZ.glob("*.jsonl")) if p.name != "forras_bekezdesek.jsonl"]
    rows = defaultdict(list)
    for p in files:
        for line in p.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r["split"] in EVAL_SPLITS:
                rows[f"{r['family']}|{r['split']}"].append((r["id"], json.dumps(r, ensure_ascii=False, sort_keys=True)))
    out = {}
    for k, v in sorted(rows.items()):
        v.sort()
        out[k] = {"n": len(v), "sha256": hashlib.sha256("\n".join(x for _, x in v).encode()).hexdigest()}
    return out


def main() -> None:
    cmd = sys.argv[1]
    man = json.loads(MAN.read_text(encoding="utf-8")) if MAN.exists() else {"retegek": {}, "naplo": []}
    cur = layers(with_szint=True)
    if cmd == "fagyaszt":
        new = {k: v for k, v in cur.items() if k not in man["retegek"]}
        if not ("--szint" in sys.argv):
            new = {k: v for k, v in new.items() if not k.split("|")[0] in _szint_families()}
        man["retegek"] |= new
        man["naplo"].append({"ido": datetime.now(timezone.utc).isoformat(timespec="seconds"), "uj_retegek": sorted(new)})
        MAN.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{len(new)} új réteg befagyasztva, összesen {len(man['retegek'])}; {sum(v['n'] for v in new.values())} item")
    elif cmd == "ujrafagyaszt":
        if "--ok" not in sys.argv or not sys.argv[sys.argv.index("--ok") + 1].strip():
            raise SystemExit("indok kell: --ok \"...\"")
        reason = sys.argv[sys.argv.index("--ok") + 1]
        changed = [k for k, v in man["retegek"].items() if cur.get(k) != v]
        szint = _szint_families()
        if bad := [k for k in changed if k.split("|")[0] not in szint]:
            raise SystemExit(f"nem szintetikus réteg változott, ez nem fagyasztható újra: {bad}")
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        man.setdefault("archiv", [])
        for k in changed:
            man["archiv"].append({"reteg": k, "regi": man["retegek"][k], "uj": cur.get(k), "ido": now, "ok": reason})
            if k in cur:
                man["retegek"][k] = cur[k]
            else:
                del man["retegek"][k]
        new = {k: v for k, v in cur.items() if k not in man["retegek"] and k.split("|")[0] in szint}
        man["retegek"] |= new
        man["naplo"].append({"ido": now, "ujrafagyasztva": changed, "uj_retegek": sorted(new), "ok": reason})
        MAN.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"újrafagyasztva {len(changed)} réteg, új {len(new)}; összesen {len(man['retegek'])}")
    else:
        bad = [k for k, v in man["retegek"].items() if cur.get(k) != v]
        print(f"{len(man['retegek'])} réteg, eltérés: {len(bad)}", bad[:10])
        if bad:
            raise SystemExit("A BEFAGYASZTOTT RÉTEGEK MEGVÁLTOZTAK")


def _szint_families() -> set[str]:
    import yaml

    return set(yaml.safe_load((ROOT / "spec/szintetikus_csaladok.yaml").read_text(encoding="utf-8"))["csaladok"])


if __name__ == "__main__":
    main()
