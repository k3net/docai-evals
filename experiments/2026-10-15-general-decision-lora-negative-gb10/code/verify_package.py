#!/usr/bin/env python3
"""Check what this package can check without a GPU: the pre-registration freeze, the seal chain of the read-outs,
the hashes of the analysis outputs, and the headline numbers quoted in README.md against the machine outputs.

What it does, CPU only, standard library only, in about a second:
  1. the freeze (protocol/v1/): the sha256 of MANIFEST.sha256 equals the one recorded in ROGZITES.txt and the one
     hard-coded in the analysis chain (code/kor03/eszkozok/f4_elemzes_lanc.sh), and the chain's own sha256 equals the
     one in ROGZITES.txt; every MANIFEST entry that is published here (the frozen runbook, the seal snapshot, the
     analysis code) matches byte for byte. Entries not published here (item files, validation read-outs, the training
     mix) are counted and listed by kind;
  2. the seal chain (results/): the seal snapshot taken at the freeze is a prefix of the final PECSET.sha256 (the
     re-read only appended); the last seal hash of every sealed read-out equals its entry in
     V1-MANIFEST-kiolvasasok.sha256 and in teljesseg.json; validation read-outs listed in both the freeze manifest and
     the final manifest did not change;
  3. the analysis outputs: results/elemzes.sha256 and results/teljesseg.sha256 against the published files;
  4. the pre-registered verdicts, and about 160 numbers quoted in README.md, recomputed by rounding the
     machine outputs (f4_elemzes03.json, f4_leiro03.json, f4_ketlepcso03.json) the way README.md prints them.

Not checked here, because it is not published here: the per-item read-outs (each is in the seal chain by hash only),
the item files of the held-out layers, and the bootstrap itself (re-run code/kor03/eszkozok/f4_elemzes03.py on the
read-outs; about an hour on CPU). The published training and validation split is on Hugging Face
(k3dani/hu-general-decision-mix), the adapters at k3dani/Qwen3.6-35B-A3B-hu-general-decision-lora-negative-result.

    python3 code/verify_package.py

Part of DocAI Evals - https://docai.hu
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# research-tree path (as written in the manifests) -> path in this package
PUBLISHED = {
    "kor03/rogzites/v1/03-runbook-v1.md": "protocol/v1/03-runbook-v1.md",
    "kor03/rogzites/v1/PECSET-pillanatkep.sha256": "protocol/v1/PECSET-pillanatkep.sha256",
    "kor03/eszkozok/f4_elemzes03.py": "code/kor03/eszkozok/f4_elemzes03.py",
    "kor03/eszkozok/f4_teljesseg03.py": "code/kor03/eszkozok/f4_teljesseg03.py",
    "kor03/eszkozok/f4_elemzes_lanc.sh": "code/kor03/eszkozok/f4_elemzes_lanc.sh",
    "eszkozok/elemzes.py": "code/eszkozok/elemzes.py",
    "eszkozok/f4_elemzes.py": "code/eszkozok/f4_elemzes.py",
    "eszkozok/common.py": "code/eszkozok/common.py",
    "eszkozok/lib.sh": "code/eszkozok/lib.sh",
    "kor03/eredmenyek/F4/teljesseg.json": "results/teljesseg.json",
    "kor03/eredmenyek/F4/V1-MANIFEST-kiolvasasok.sha256": "results/V1-MANIFEST-kiolvasasok.sha256",
    "kor03/eredmenyek/F4/f4_elemzes03.json": "results/f4_elemzes03.json",
    "kor03/eredmenyek/F4/eredmenylap_gepi.md": "results/eredmenylap_gepi.md",
}
# published with a redaction, so the frozen hash cannot match; the reason is printed
REDACTED = {"eszkozok/common.py": "one comment line redacted (a username on the measurement host -> <user>)"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sums(path: Path) -> list[tuple[str, str]]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            h, name = line.split(None, 1)
            out.append((h, name.strip()))
    return out


class Report:
    def __init__(self) -> None:
        self.ok = 0
        self.bad: list[str] = []
        self.notes: list[str] = []

    def check(self, cond: bool, what: str) -> None:
        if cond:
            self.ok += 1
        else:
            self.bad.append(what)


def check_freeze(r: Report) -> None:
    v1 = ROOT / "protocol/v1"
    rec = {}
    for line in (v1 / "ROGZITES.txt").read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) >= 2 and len(parts[1]) == 64:
            rec[parts[0]] = parts[1]
    man_sha = sha(v1 / "MANIFEST.sha256")
    r.check(man_sha == rec.get("MANIFEST.sha256"), f"MANIFEST.sha256 is {man_sha}, ROGZITES.txt says {rec.get('MANIFEST.sha256')}")
    chain = ROOT / PUBLISHED["kor03/eszkozok/f4_elemzes_lanc.sh"]
    r.check(sha(chain) == rec.get("f4_elemzes_lanc.sh"), "f4_elemzes_lanc.sh differs from the hash in ROGZITES.txt")
    r.check(f"MANIFEST_SHA={man_sha}" in chain.read_text(encoding="utf-8"),
            "the analysis chain does not carry the manifest's hash")
    unpublished: dict[str, int] = {}
    for h, name in sums(v1 / "MANIFEST.sha256"):
        if name in REDACTED:
            r.notes.append(f"freeze: {name} not compared - {REDACTED[name]}")
        elif name in PUBLISHED:
            r.check(sha(ROOT / PUBLISHED[name]) == h, f"freeze: {PUBLISHED[name]} differs from the frozen hash of {name}")
        else:
            kind = ("validation read-out" if name.endswith("_val.jsonl") or "/F2/qwen_" in name
                    else "training mix" if "mvp_train" in name else "item file or calibration sample")
            unpublished[kind] = unpublished.get(kind, 0) + 1
    r.notes.append("freeze: not published here (hash only): "
                   + "; ".join(f"{k}: {n}" for k, n in sorted(unpublished.items())))


def check_seals(r: Report) -> None:
    snap = sums(ROOT / "protocol/v1/PECSET-pillanatkep.sha256")
    seal = sums(ROOT / "results/PECSET.sha256")
    r.check(seal[:len(snap)] == snap, "the final PECSET.sha256 does not start with the snapshot taken at the freeze")
    last = {}
    for h, name in seal:
        last[name] = h
    final = dict((name, h) for h, name in sums(ROOT / "results/V1-MANIFEST-kiolvasasok.sha256"))
    for name, h in last.items():
        r.check(final.get(name) == h, f"seal: last hash of {name} is not the one in V1-MANIFEST-kiolvasasok.sha256")
    frozen = dict((name, h) for h, name in sums(ROOT / "protocol/v1/MANIFEST.sha256"))
    for name, h in final.items():
        if name in frozen:
            r.check(frozen[name] == h, f"seal: {name} changed between the freeze and the analysis")
    tj = json.loads((ROOT / "results/teljesseg.json").read_text(encoding="utf-8"))
    for arm, e in tj["karok"].items():
        r.check(final.get(e["ut"]) == e["sha256"], f"teljesseg.json: {arm} hash differs from the final manifest")
    reread = sum(1 for name in last if sum(1 for _, n in seal if n == name) > 1)
    r.notes.append(f"seals: {len(seal)} seal lines, {len(last)} sealed read-outs, {reread} of them re-read "
                   f"(append-only); {len(final)} read-outs in the final manifest")


def check_outputs(r: Report) -> None:
    for f in ("results/elemzes.sha256", "results/teljesseg.sha256"):
        for h, name in sums(ROOT / f):
            if name in PUBLISHED:
                r.check(sha(ROOT / PUBLISHED[name]) == h, f"{f}: {PUBLISHED[name]} differs")
            else:
                r.notes.append(f"{f}: {name.split('/')[-1]} not published (per-item (id, perm) pairs)")


# --- numbers -------------------------------------------------------------------------------------------------------

def fmt(x: float, d: int) -> str:
    return f"{x:.{d}f}"


def check_numbers(r: Report) -> None:
    E = json.loads((ROOT / "results/f4_elemzes03.json").read_text(encoding="utf-8"))
    L = json.loads((ROOT / "results/f4_leiro03.json").read_text(encoding="utf-8"))
    K = json.loads((ROOT / "results/f4_ketlepcso03.json").read_text(encoding="utf-8"))
    B, P, MR = E["bootstrap"], E["pont"], E["leiro"]["pont_minden_reteg"]
    n = 0

    def eq(label: str, value: float, expected: str, d: int, scale: float = 1.0) -> None:
        nonlocal n
        n += 1
        got = fmt(value * scale, d)
        r.check(got == expected, f"number: {label}: README {expected}, machine output {got}")

    def ci(label: str, c: list, expected: str, d: int, scale: float = 1.0) -> None:
        eq(label + " (CI low)", c[0], expected.split(";")[0].strip(), d, scale)
        eq(label + " (CI high)", c[1], expected.split(";")[1].strip(), d, scale)

    G3 = ("k03v2_g3_s1", "k03v2_g3_s2", "k03v2_g3_s3")
    # 5.2 arm tables: L1*, G3 (mean of 3 seeds), coverage / precision / AURC / ECE / X recall
    arms = {
        "ho-termek": {"L1": ("0.653", "0.963", "0.0296", "0.058", "0.415"), "G3": ("0.761", "0.912", "0.0434", "0.062", "0.340")},
        "ho-routing": {"L1": ("0.644", "0.918", "0.0343", "0.023", "0.765"), "G3": ("0.732", "0.866", "0.0816", "0.064", "0.570")},
        "ho-uj": {"L1": ("0.568", "0.938", "0.0717", "0.043", "0.353"), "G3": ("0.636", "0.905", "0.0444", "0.074", "0.653")},
    }
    for g, rows in arms.items():
        for arm, (lef, prec, aurc, ece, xf) in rows.items():
            if arm == "L1":
                m = MR[g]["L1"]
                vals = (m["besorolasi_lefedettseg"], m["besorolasi_precizitas"], m["aurc"], m["ece"], m["x_fedes"])
            else:
                a = P[g]["G3_atlag"]
                vals = (a["lef"], a["prec"], a["aurc"], sum(MR[g][s]["ece"] for s in G3) / 3, a["x_fedes"])
            for (lbl, v, exp, d) in zip(("coverage", "precision", "AURC", "ECE", "X recall"), vals,
                                        (lef, prec, aurc, ece, xf), (3, 3, 4, 3, 3)):
                eq(f"{g} {arm} {lbl}", v, exp, d)
        seeds = [P[g]["karok"][s]["lef"] for s in G3]
        precs = [P[g]["karok"][s]["prec"] for s in G3]
        r.check(min(seeds) <= P[g]["G3_atlag"]["lef"] <= max(seeds), f"{g}: G3 mean coverage outside the seed range")
        r.check(min(precs) < 0.93 or P[g]["G3_atlag"]["prec"] < 0.93, f"{g}: no seed or mean below 0.93")

    # 5.3 H1: Delta coverage@95 (bootstrap median, points) and Delta AURC, 95 % CI; verdict
    h1 = {"ho-termek": ("11.1", "6.9; 16.1", "0.014", "0.002; 0.027"),
          "ho-routing": ("8.9", "6.7; 11.3", "0.047", "0.039; 0.057"),
          "ho-uj": ("7.2", "3.7; 11.0", "-0.027", "-0.033; -0.022")}
    for g, (dl, dlci, da, daci) in h1.items():
        eq(f"H1 {g} dcov", B[f"H1:{g}:lef"]["median"], dl, 1, 100)
        ci(f"H1 {g} dcov", B[f"H1:{g}:lef"]["ci95"], dlci, 1, 100)
        eq(f"H1 {g} dAURC", B[f"H1:{g}:aurc"]["median"], da, 3)
        ci(f"H1 {g} dAURC", B[f"H1:{g}:aurc"]["ci95"], daci, 3)
        r.check(E["H1"][g]["itelet"] == "nem teljesíti a követelményeket", f"H1 {g}: verdict is {E['H1'][g]['itelet']}")
    eq("H1 ho-termek AURC p", B["H1:ho-termek:aurc"]["p_ketoldali"], "0.016", 3)
    r.check(B["H1:ho-termek:lef"]["p_ketoldali"] < 0.0001, "H1 ho-termek coverage p is not < 0.0001")
    # H2
    h2 = {"ho-termek": ("10.3", "6.3; 15.3", "5.7", "2.5; 9.7", "1.05", "0.73; 1.62"),
          "ho-routing": ("12.4", "9.6; 15.1", "2.6", "0.7; 4.9", "0.71", "0.55; 0.94")}
    for g, (gain, gci, dd, dci, ratio, rci) in h2.items():
        h = E["H2"][g]
        eq(f"H2 {g} L3-L1", h["L3_minus_L1"]["pont"], gain, 1, 100)
        ci(f"H2 {g} L3-L1", h["L3_minus_L1"]["ci95"], gci, 1, 100)
        eq(f"H2 {g} D", h["D"]["pont"], dd, 1, 100)
        ci(f"H2 {g} D", h["D"]["ci95"], dci, 1, 100)
        eq(f"H2 {g} ratio", h["nyeresegarany_leiro"]["pont"], ratio, 2)
        ci(f"H2 {g} ratio", h["nyeresegarany_leiro"]["ci95"], rci, 2)
        r.check(h["itelet"] == "érdemi átvitel", f"H2 {g}: verdict is {h['itelet']}")
    # H3(a) precision [CI]; H3(b) verdicts
    for g, (p, pci) in {"ho-termek": ("0.912", "0.875; 0.941"), "ho-routing": ("0.866", "0.846; 0.882"),
                        "ho-uj": ("0.905", "0.880; 0.925")}.items():
        a = E["H3"][g]["a"]
        eq(f"H3a {g} precision", a["G3_precizitas_atlag"], p, 3)
        ci(f"H3a {g} precision", a["G3_ci_hierarchikus"]["ci95"], pci, 3)
        r.check(a["itelet"] == "az előírt toleranciaküszöböt nem teljesítette", f"H3a {g}: verdict is {a['itelet']}")
    for g in ("ho-termek", "ho-routing"):
        r.check(E["H3"][g]["b"]["itelet"].startswith("nincs megfelelő τ"), f"H3b {g}: verdict")
    r.check(E["H3"]["ho-uj"]["b"]["itelet"] == "az előírt toleranciaküszöböt teljesítette", "H3b ho-uj: verdict")
    # H4
    h4 = {"ho-termek": ("2.5", "-0.3; 5.9", "0.005", "0.002; 0.009", "nem teljesíti a követelményeket"),
          "ho-uj": ("2.9", "1.4; 5.4", "-0.003", "-0.009; 0.002", "nem teljesíti a követelményeket"),
          "ho-routing-hu": ("0.6", "-1.6; 3.0", "-0.0026", "-0.0048; -0.0010", "segít")}
    for g, (dl, dlci, da, daci, verdict) in h4.items():
        b = E["H4"][g]
        eq(f"H4 {g} dcov", b["d_lef"]["median"], dl, 1, 100)
        ci(f"H4 {g} dcov", b["d_lef"]["ci95"], dlci, 1, 100)
        d = 4 if g == "ho-routing-hu" else 3
        eq(f"H4 {g} dAURC", b["d_aurc"]["median"], da, d)
        ci(f"H4 {g} dAURC", b["d_aurc"]["ci95"], daci, d)
        r.check(b["itelet"] == verdict, f"H4 {g}: verdict is {b['itelet']}")
    # H6(a), H6(b)
    h6 = {"ho-routing": ("-19.3", "-24.3; -15.5", "-23.6", "-25.3; -21.9", "-1.1", "-2.2; -0.1", "-0.006", "-0.010; -0.003"),
          "ho-termek": ("-7.6", "-13.8; -0.4", "-2.0", "-4.5; 0.4", "-6.7", "-8.8; -4.6", "0.007", "0.004; 0.010")}
    for g, (a, aci, k, kci, bx, bxci, ba, baci) in h6.items():
        h = E["H6"][g]
        eq(f"H6a {g} G3", h["a_G3"]["median"], a, 1, 100)
        ci(f"H6a {g} G3", h["a_G3"]["ci95"], aci, 1, 100)
        eq(f"H6a {g} hard", h["a_kemeny"]["median"], k, 1, 100)
        ci(f"H6a {g} hard", h["a_kemeny"]["ci95"], kci, 1, 100)
        hb = h["b_horgony_G3s1_minus_kemeny"]
        eq(f"H6b {g} X recall", hb["x_fedes"]["median"], bx, 1, 100)
        ci(f"H6b {g} X recall", hb["x_fedes"]["ci95"], bxci, 1, 100)
        eq(f"H6b {g} AURC", hb["aurc"]["median"], ba, 3)
        ci(f"H6b {g} AURC", hb["aurc"]["ci95"], baci, 3)
        r.check(not h["a_G3"]["megorzi_minus2pont"] and not h["a_kemeny"]["megorzi_minus2pont"], f"H6a {g}: verdict")

    # 5.4 where the errors come from (f4_leiro03.json, mean of 3 seeds for G3)
    errs = {("ho-termek", "L1"): ("0.997", "9.2"), ("ho-termek", "G3"): ("0.991", "25.1"),
            ("ho-routing", "L1"): ("0.995", "15.0"), ("ho-routing", "G3"): ("0.993", "28.3"),
            ("ho-uj", "L1"): ("0.947", "4.2"), ("ho-uj", "G3"): ("0.921", "7.8")}
    for (g, arm), (nxp, acc) in errs.items():
        e = L["retegek"][g][arm]
        eq(f"{g} {arm} non-X precision", e["nemx_prec"], nxp, 3)
        eq(f"{g} {arm} X-gold accepted", e["x_elfogadasi_arany"], acc, 1, 100)
    # X recall by source on HO-routing: base -> G3
    src = {"w2c_teszt": ("0.781", "0.544"), "bfcl_live_irrelevance": ("0.655", "0.449"),
           "bfcl_irrelevance": ("0.860", "0.672")}
    for s, (b0, g3) in src.items():
        eq(f"ho-routing {s} L1 X recall", L["bontas"]["ho-routing"][s]["L1"]["x_fedes"], b0, 3)
        eq(f"ho-routing {s} G3 X recall", L["bontas"]["ho-routing"][s]["G3"]["x_fedes"], g3, 3)
    # X recall by X type on HO-uj (natural, missing precondition): L1* -> G3 (2 decimals in README)
    xt = MR["ho-uj"]
    for t, (b0, g3) in {"natural": ("0.01", "0.84"), "missing-precondition": ("0.50", "0.58")}.items():
        eq(f"ho-uj {t} L1 X recall", xt["L1"]["x_fedes_tipusonkent"][t]["x_fedes"], b0, 2)
        eq(f"ho-uj {t} G3 X recall", sum(xt[s]["x_fedes_tipusonkent"][t]["x_fedes"] for s in G3) / 3, g3, 2)

    # 5.7 two-stage (exploratory): gate variant, mean of 3 seeds; coverage at 95 % precision with own-test tau
    two = {"ho-termek": ("0.723", "0.936", "7.5", "3.2; 12.3", "0.682", "0.675", "0.650"),
           "ho-routing": ("0.655", "0.916", "1.4", "-1.3; 4.0", "0.471", "0.490", "0.016"),
           "ho-uj": ("0.634", "0.907", "7.1", "3.4; 11.5", "0.525", "0.512", "0.528")}
    for g, (lef, prec, dl, dlci, o1, o2, o3) in two.items():
        k = K["pont"][g]
        eq(f"two-stage {g} coverage", k["kapu_atlag"]["lef"], lef, 3)
        eq(f"two-stage {g} precision", k["kapu_atlag"]["prec"], prec, 3)
        eq(f"two-stage {g} dcov", K["bootstrap"][f"kapu:{g}:lef"]["median"], dl, 1, 100)
        ci(f"two-stage {g} dcov", K["bootstrap"][f"kapu:{g}:lef"]["ci95"], dlci, 1, 100)
        eq(f"two-stage {g} L1 cov@95 own tau", k["L1"]["lef_azonos_95_precizitason"], o1, 3)
        eq(f"two-stage {g} gate cov@95 own tau", k["kapu_atlag"]["lef_azonos_95_precizitason"], o2, 3)
        eq(f"two-stage {g} G3 cov@95 own tau", k["G3_atlag"]["lef_azonos_95_precizitason"], o3, 3)

    # layer sizes
    for g, (nn, sc, cl) in {"ho-termek": (5441, 4524, 2759), "ho-routing": (7493, 7416, 4169),
                            "ho-uj": (2200, 2200, 2200)}.items():
        m = E["retegmeret"][g]
        r.check((m["n"], m["pontozott"], m["klaszter"]) == (nn, sc, cl), f"layer size {g}: {m}")
    r.check(E["reps"] == 10000 and not E["proba"], "the analysis was not the 10 000-replicate production run")
    r.check(E["konzisztencia_pont_a_ci_n_kivul"] == [], "a point estimate falls outside its own CI")
    r.notes.append(f"numbers: {n} values quoted in README.md compared with the machine outputs")


def main() -> int:
    r = Report()
    for step in (check_freeze, check_seals, check_outputs, check_numbers):
        step(r)
    for note in r.notes:
        print("  " + note)
    if r.bad:
        print(f"FAILED: {len(r.bad)} of {r.ok + len(r.bad)} checks")
        for b in r.bad:
            print("  - " + b)
        return 1
    print(f"OK: {r.ok} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
