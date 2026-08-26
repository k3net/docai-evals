#!/usr/bin/env python3
"""Tiszta klón füstteszt — a kísérlet reprodukálhatóságát ellenőrzi kívülről.

    python3 code/smoke_repro.py            # teljes kör
    python3 code/smoke_repro.py --keep     # a munkakönyvtár marad, hogy bele lehessen nézni

Miért kell: a repó `code/` + `dataset/` szerkezetű, a mérési munkapéldány viszont lapos.
Amikor a szkriptek átkerültek ide, az útvonalak nem követték őket, és a kísérlet tiszta
klónból `FileNotFoundError`-ral halt — miközben az eval-card R1-et ígért. Ez a teszt pont
azt méri, amit az R1 állít: a publikált adatból a publikált kóddal ugyanazok a számok
jönnek-e ki.

⛔ A teszt SOHA nem ír a repóba: az egészet egy ideiglenes könyvtárba másolja, ott futtat,
és a keletkezett fájlokat hasonlítja a commitolt eredetihez. Enélkül egy füstteszt maga
írná felül azt, amit ellenőriznie kellene.

Amit NEM fed le (nincs elhallgatott korlát): a Mérés C és a D3/D3b SAE-alapú szakaszai,
valamint a logit lens nyers futtatása GPU-t igényel — a `results*/sae/` (33-42 MB/kör) és a
`hidden/` nincs commitolva. Ezek a `code/run_sae.py` és a `code/logit_lens.py` újrafuttatásával
állnak elő; a belőlük SZÁRMAZTATOTT `lens_rank*.json` / `lens_index*.json` viszont publikált,
ezért a Mérés B itt is ellenőrizhető.
"""
import argparse
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent.parent

# (szkript, körcímke, környezet) — a körök a scope_paths.py változóival állnak be.
ROUNDS = {
    "base": {},
    "instruct": {"SCOPE_RES": "results_instruct", "SCOPE_REPORTS": "reports_instruct", "SCOPE_CHAT": "1"},
    "instruct_raw": {"SCOPE_RES": "results_instruct_raw", "SCOPE_REPORTS": "reports_instruct_raw"},
}
# Csak az a (szkript, kör) pár szerepel, amelynek MINDEN bemenete commitolva van.
ANALYSES = [
    ("analyze_a.py", "base"), ("analyze_a.py", "instruct"), ("analyze_a.py", "instruct_raw"),
    ("analyze_b.py", "base"), ("analyze_b.py", "instruct"),
    # d2_control: az instruct_raw körnek nincs lens-kimenete, ott a futás csak stubot
    # hozna létre — az nem reprodukció, ezért kimarad.
    ("d2_control.py", "base"), ("d2_control.py", "instruct"),
    ("analyze_tokens.py", "base"),
    ("compare_rounds.py", "base"),
]
BUILDERS = [
    ("build_prompts.py", "prompts.jsonl"),
    ("build_prompts_d3b.py", "prompts_d3b.jsonl"),
    ("build_prompts_d3b_x.py", "prompts_d3b_x.jsonl"),
]

ok, fail = [], []


def say(good, msg):
    (ok if good else fail).append(msg)
    print(f"{'✅' if good else '❌'} {msg}")


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def mtimes(root):
    """A riport-fájlok időbélyegei — ebből látjuk, melyiket írta újra egy futás.
    ⛔ Tartalom-hash NEM elég: a sikeres eset épp az, amikor a fájl változatlan marad."""
    return {p: p.stat().st_mtime_ns
            for d in root.glob("reports*") for p in d.rglob("*") if p.is_file()}


def run(script, work, env_extra):
    env = {**os.environ, **{k: "" for k in ("SCOPE_RES", "SCOPE_REPORTS", "SCOPE_CHAT",
                                            "SCOPE_FIGURES", "SCOPE_PROMPTS")}, **env_extra}
    return subprocess.run([sys.executable, f"code/{script}"], cwd=work, env=env,
                          capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true", help="a munkakönyvtár maradjon meg")
    args = ap.parse_args()

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="scope-smoke-"))
    work = tmp / "exp"
    shutil.copytree(HERE, work, ignore=shutil.ignore_patterns("__pycache__"))
    print(f"munkapéldány: {work}\n")

    # (1) Betöltődik-e egyáltalán az adat.
    print("── 1. adatbetöltés ─────────────────────────────────────────")
    for name, expect in (("items.jsonl", None), ("prompts.jsonl", 258),
                         ("prompts_d3b.jsonl", 16), ("prompts_d3b_x.jsonl", 16)):
        p = work / "dataset" / name
        if not p.exists():
            say(False, f"{name} — HIÁNYZIK ({p})")
            continue
        rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
        say(expect is None or len(rows) == expect,
            f"{name} — {len(rows)} sor" + (f" (várt: {expect})" if expect else ""))

    # (2) A promptok a korpuszból újraépülnek-e, bitre azonosan.
    print("\n── 2. promptok újragenerálása ──────────────────────────────")
    for script, out in BUILDERS:
        before = sha(work / "dataset" / out)
        r = run(script, work, {})
        if r.returncode:
            say(False, f"{script} — elszállt: {r.stderr.strip().splitlines()[-1][:120]}")
            continue
        say(sha(work / "dataset" / out) == before, f"{script} → {out} bitre azonos")

    # (3) A származtatott pontszám-oszlop konzisztens-e.
    print("\n── 3. pontozás-ellenőrzés ──────────────────────────────────")
    r = run("check_scores.py", work, {})
    say(r.returncode == 0, "check_scores.py — " +
        (r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "hiba"))

    # (4) A CPU-n futtatható elemzések ugyanazt a riportot adják-e.
    print("\n── 4. elemzések újrafuttatása ──────────────────────────────")
    for script, round_ in ANALYSES:
        snap = mtimes(work)
        r = run(script, work, ROUNDS[round_])
        if r.returncode:
            say(False, f"{script} [{round_}] — elszállt: {r.stderr.strip().splitlines()[-1][:120]}")
            continue
        touched = [p for p, m in mtimes(work).items() if snap.get(p) != m]
        if not touched:
            say(False, f"{script} [{round_}] — lefutott, de EGY fájlt sem írt")
            continue
        bad = [p for p in touched
               if not (HERE / p.relative_to(work)).exists()
               or sha(p) != sha(HERE / p.relative_to(work))]
        say(not bad, f"{script} [{round_}] — {len(touched)} fájl újragenerálva" +
            (f", ELTÉR: {[str(p.relative_to(work)) for p in bad]}" if bad else ", mind azonos"))

    print("\n── kihagyva (GPU kell hozzá, nincs elhallgatva) ────────────")
    for s in ("analyze_c.py", "analyze_d.py", "analyze_d3b.py", "analyze_d3b_x.py"):
        print(f"⏭️  {s} — a results*/sae/ nincs commitolva (code/run_sae.py állítja elő)")

    print(f"\n{'=' * 60}\n{len(ok)} rendben · {len(fail)} hibás")
    if args.keep:
        print(f"munkapéldány megtartva: {work}")
    else:
        shutil.rmtree(tmp)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
