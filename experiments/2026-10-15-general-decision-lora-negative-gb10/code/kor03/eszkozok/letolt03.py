"""03-as kör — a HF-források letöltése a forráslistában rögzített commitra, fájlonkénti sha256-tal (F0).

A commit a `forras/forrasok03.json`-ból jön (forrasok03.py); ahol a fájlok más ágon vannak (a MultiEURLEX nyelvenkénti
parquetje a `refs/convert/parquet` ágon), a REVISION rögzíti az ág commitját. Csak a megadott mintájú fájlok jönnek le:
a nagy, többnyelvű készletekből a magyar rész, a tiltott splitekből semmi (MILQA test: 03-runbook 3.1), a kitartott
csoportokkal rokon konfigurációkból semmi (5. pont: routing, termék, KIE/validáció). A kimenet a `forras/hf/<repo>/`
alá kerül; a `forras/letoltes03.json` fájlonként rögzíti a commitot, a méretet és a sha256-ot. A GitHub-források
(GITHUB) a rögzített commit zip-jéből jönnek, a `forras/gh/<repo>/` alá.

  kor01/.venv/bin/python kor03/eszkozok/letolt03.py [--csak NYTK/HuRTE,...]
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import io
import json
import urllib.request
import zipfile
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download

ROOT = Path(__file__).resolve().parents[1]
FORRAS = ROOT / "forras"

# repó → (befoglaló minták, kizáró minták); a dokumentáció (README, LICENSE) mindig jön
PATTERNS = {
    "NYTK/HuRTE": (["data/*"], []),
    "NYTK/HuCOLA": (["data/*"], []),
    "NYTK/HuWNLI": (["data/*"], []),
    "NYTK/HuCommitmentBank": (["data/*"], []),
    "NYTK/HuSST": (["data/*"], []),
    "NYTK/HuCoPA": (["data/*"], []),
    "NYTK/HuRC": (["data/*"], []),
    "SzegedAI/MILQA": (["train.*"], ["test.*"]),
    "coastalcph/multi_eurlex": (["hu/*"], []),
    "facebook/belebele": (["data/hun_Latn.jsonl"], []),
    "Davlan/sib200": (["data/hun_Latn/*"], []),
    # angol gerinc (3.3): a `full` konfiguráció (a `default` keverékét Jev-ítéletek súlyozták), a vision nélkül
    "tasksource/tasksource-jev-typed-decisions": (["full/*.parquet"], []),
    # a KIE/validációval (arithmetic, record_aggregation, table_lookup) és a routinggal (taxonomy_routing) rokon
    # feladatok nélkül
    "tasksource/procedural-typed-decisions": ([f"{t}/*" for t in (
        "entity_belief_tracking", "event_state_reconstruction", "evidence_sufficiency", "multi_view_adjudication",
        "needle_retrieval", "partial_observation_calibration", "policy_applicability", "policy_under_uncertainty",
        "state_perturbation")], []),
    # a release-v2 és a browser-drone ügyfélszolgálati routingot és ellenőrizetlen licencű leírásokat tartalmaz, az
    # amount/email/phone-extraction KIE: ezek kimaradnak
    "ZefanCai/Open-Jev": ([f"data/{c}/*" for c in (
        "citation-control-v1", "entity-alignment-control-v1", "mailroom-control-v1", "context-retention-control-v1",
        "silent-failure-control-v1", "ir-control-v1", "sponsor-segment-control-v1")], []),
    "LocalLLaMA/typed-decisions": (["all/test-*"], []),
    "fastino/fast-decisions": (["*.jsonl"], []),
    "wikimedia/wikipedia": (["20231101.hu/train-00001-of-00004.parquet"], []),
}
# ahol a fájlok nem a forráslistában rögzített commiton vannak
REVISION = {"coastalcph/multi_eurlex": "6278c7994cd86297e823becad7fdf897faaea174",  # refs/convert/parquet
            "wikimedia/wikipedia": "b04c8d1ceb2f5cd4588862100d08de323dccfbaa"}
# GitHub-források: repó → commit
GITHUB = {"nytud/NYTK-NerKor": "7c9c5b5f1f3ec7f94e724e0b92f3afa8eb262d00"}
DOCS = ["README.md", "LICENSE*", "LICENCE*"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csak", default="", help="vesszővel elválasztott repólista (alap: mind a PATTERNS-ből)")
    args = ap.parse_args()
    shas = {r["where"][3:]: r["sha"] for r in json.loads((FORRAS / "forrasok03.json").read_text())
            if r["where"].startswith("hf:") and r.get("sha")}
    repos = [r for r in (args.csak.split(",") if args.csak else [*PATTERNS, *GITHUB]) if r]
    man_path = FORRAS / "letoltes03.json"
    man = json.loads(man_path.read_text()) if man_path.exists() else {}
    api = HfApi()
    for repo in repos:
        if repo in GITHUB:
            man[repo] = github_zip(repo, GITHUB[repo])
            man_path.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
            continue
        inc, exc = PATTERNS[repo]
        rev = REVISION.get(repo) or shas[repo]
        files = [f for f in api.list_repo_files(repo, repo_type="dataset", revision=rev)
                 if any(fnmatch.fnmatch(f, p) for p in inc + DOCS) and not any(fnmatch.fnmatch(f, p) for p in exc)]
        out = FORRAS / "hf" / repo
        entry = {"revision": rev, "files": {}}
        for f in files:
            p = Path(hf_hub_download(repo, f, repo_type="dataset", revision=rev, local_dir=out))
            entry["files"][f] = {"bytes": p.stat().st_size, "sha256": sha256(p)}
        man[repo] = entry
        print(f"{repo}@{rev[:10]}: {len(files)} fájl, {sum(v['bytes'] for v in entry['files'].values()) / 1e6:.1f} MB")
        man_path.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")


def github_zip(repo: str, commit: str) -> dict:
    """A rögzített commit zip-je kicsomagolva a `forras/gh/<repo>/` alá; a zip sha256-ja és a fájlok listája."""
    out = FORRAS / "gh" / repo
    url = f"https://codeload.github.com/{repo}/zip/{commit}"
    with urllib.request.urlopen(url, timeout=300) as r:
        data = r.read()
    entry = {"revision": commit, "url": url, "zip_bytes": len(data), "zip_sha256": hashlib.sha256(data).hexdigest(),
             "files": {}}
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for n in z.namelist():
            if n.endswith("/"):
                continue
            rel = n.split("/", 1)[1]
            p = out / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(z.read(n))
            entry["files"][rel] = {"bytes": p.stat().st_size, "sha256": sha256(p)}
    print(f"{repo}@{commit[:10]}: {len(entry['files'])} fájl, {len(data) / 1e6:.1f} MB zip")
    return entry


if __name__ == "__main__":
    main()
