#!/usr/bin/env python3
"""Check what this package can check without a GPU: the frozen manifests, the hash chain of the published files, the
headline numbers quoted in README.md against the machine outputs, and that the package contains no forbidden string.

What it does, CPU only, standard library only, in a few seconds:
  1. the manifests (protocol/rogzites/): each round's manifest hash matches its freeze record (ROGZITES.json,
     manifest.json), cross-references between manifests hold (D12 hash in J/M/N/G4/seal chain, the K3 manifest's v1 hash,
     the G5 opening record), and every manifest entry that is published here matches byte for byte, except the files
     listed in REDACTED below (each with its reason). Entries not published (item files, per-item read-outs, trained
     heads under cache/) are counted and listed by kind;
  2. the hash files: results/kor08/G5/g5.sha256 against results/kor08/G5/, and results/RESULTS.sha256 and
     results/PACKAGE.sha256 (generated for this package) against the files;
  3. the numbers: about 150 values printed in README.md, recomputed from the JSON files in results/ and compared
     with the strings printed in README.md. Dates of the pre-registration are compared with the freeze records;
  4. a scan over the whole package for usernames with hosts, absolute home paths, e-mail addresses, access tokens and
     private addresses. A separate tenant-name scan was run before release and is deliberately not part of this file:
     even a hashed list of names could be confirmed by guessing.

Not checked here, because it is not published here: the synthetic item files, the generated texts, the per-item
extractions, read-outs and scores (they will accompany a later study), and everything under cache/. The read-outs and
the bootstraps cannot be recomputed from this package; the point is that the published numbers are the machine outputs
and the machine outputs are the ones the freeze records name.

    python3 code/verify_package.py
    python3 code/verify_package.py --list-numbers    # print every checked number with the string it must match

Part of DocAI Evals - https://docai.hu
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# -----------------------------------------------------------------------------------------------------------------------
# Files published with a redaction, so their frozen hash cannot match. Key: path as written in the manifest.
# -----------------------------------------------------------------------------------------------------------------------
REDACTED = {
    "kor07/rogzites/v1/07-runbook-v1.md":
        "tenant names replaced by <tenant>; the contributing tenants, the B0 survey and a consent detail cut to [kihagyva: ügyféladat]",
    "kor07/rogzites/k3/07-runbook-k3.md":
        "same redaction as the 07 v1 runbook snapshot",
    "kor07/rogzites/k3/nehez3-javaslat-k3.md":
        "one tenant name replaced by <tenant>",
    "eszkozok/common.py":
        "one comment line: a username on the measurement host replaced by <user> (as in the previous package)",
}

# research-tree paths under these prefixes map to these package paths
MAP_PREFIX = [
    (re.compile(r"^kor0(\d)/rogzites/(.*)$"), r"protocol/rogzites/kor0\1/\2"),
    (re.compile(r"^kor08/([GJMN]1?-rogzites\.md)$"), r"protocol/rogzites/kor08/\1"),
    (re.compile(r"^kor0(\d)/eszkozok/(.*)$"), r"code/kor0\1/eszkozok/\2"),
    (re.compile(r"^kor0(\d)/spec/(.*)$"), r"code/kor0\1/spec/\2"),
    (re.compile(r"^kor0(\d)/eredmenyek/(.*)$"), r"results/kor0\1/\2"),
    (re.compile(r"^kor03/eszkozok/(.*)$"), r"code/kor03/eszkozok/\1"),
    (re.compile(r"^eszkozok/(.*)$"), r"code/eszkozok/\1"),
]


def pkg(m: str) -> Path | None:
    for rx, rep in MAP_PREFIX:
        if rx.match(m):
            return ROOT / rx.sub(rep, m)
    return None


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sums(path: Path) -> list[tuple[str, str]]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            h, name = line.split(None, 1)
            out.append((h, name.strip()))
    return out


def jl(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


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


# --- 1. manifests --------------------------------------------------------------------------------------------------


def kind_of(name: str) -> str:
    if name.startswith("cache/"):
        return "trained heads, feature caches (cache/)"
    if "/adat/" in name or name.startswith("adat/"):
        return "item files and data (adat/)"
    if name.endswith(".jsonl"):
        return "per-item read-outs (.jsonl)"
    if name.startswith("kor0") and "/eredmenyek/" in name:
        return "earlier-round outputs not repeated here"
    if name.startswith("kor03/") or name.startswith("eszkozok/"):
        return "code of earlier rounds not repeated here"
    return "other"


def compare_entries(r: Report, label: str, entries) -> None:
    missing: dict[str, int] = {}
    n_ok = 0
    for h, name in entries:
        p = pkg(name)
        if name in REDACTED:
            if p is None or not p.exists():
                r.check(False, f"{label}: {name} is listed in REDACTED but is not published")
            else:
                r.notes.append(f"{label}: {name} not compared - {REDACTED[name]}")
            continue
        if p is not None and p.exists():
            r.check(sha(p) == h, f"{label}: {p.relative_to(ROOT)} differs from the frozen hash of {name}")
            n_ok += 1
        else:
            missing[kind_of(name)] = missing.get(kind_of(name), 0) + 1
    r.notes.append(f"{label}: {n_ok} entries compared byte for byte; not published here (hash only): "
                   + ("; ".join(f"{k}: {v}" for k, v in sorted(missing.items())) or "none"))


def check_manifests(r: Report) -> None:
    P = "protocol/rogzites/"
    # 05a
    rec = jl(P + "kor05/v1a/ROGZITES.json")
    m = ROOT / P / "kor05/v1a/MANIFEST.sha256"
    r.check(sha(m) == rec["manifest_sha256"], "05a: MANIFEST.sha256 differs from ROGZITES.json")
    for name, h in rec["pecset_manifestek"].items():
        r.check(sha(ROOT / P / f"kor05/v1a/{name}.json") == h, f"05a: seal manifest {name} differs from ROGZITES.json")
    compare_entries(r, "05a v1a manifest", sums(m))
    # 06
    rec = jl(P + "kor06/v1/ROGZITES.json")
    m = ROOT / P / "kor06/v1/MANIFEST.sha256"
    r.check(sha(m) == rec["manifest_sha256"], "06: MANIFEST.sha256 differs from ROGZITES.json")
    r.check(sha(ROOT / P / "kor06/v1/K06F3C.json") == rec["pecset_manifest"]["K06F3C"], "06: seal manifest differs")
    compare_entries(r, "06 v1 manifest", sums(m))
    # 07
    rec = jl(P + "kor07/v1/ROGZITES.json")
    m = ROOT / P / "kor07/v1/MANIFEST.sha256"
    r.check(sha(m) == rec["manifest_sha256"], "07: MANIFEST.sha256 differs from ROGZITES.json")
    r.check(sha(ROOT / P / "kor07/v1/K07F3.json") == rec["pecset_manifest"]["K07F3"], "07: seal manifest differs")
    compare_entries(r, "07 v1 manifest", sums(m))
    # K3
    rec3 = jl(P + "kor07/k3/ROGZITES.json")
    m3 = ROOT / P / "kor07/k3/MANIFEST.sha256"
    r.check(sha(m3) == rec3["manifest_sha256"], "K3: MANIFEST.sha256 differs from ROGZITES.json")
    r.check(rec3["v1_manifest_sha256"] == rec["manifest_sha256"], "K3: v1 manifest hash differs")
    op = jl(P + "kor07/k3/NYITAS.json")
    r.check(op["pecset_manifest_sha256"] == sha(ROOT / P / "kor07/k3/K07K3.json"), "K3: the opening record's seal hash differs")
    compare_entries(r, "07 K3 manifest", sums(m3))
    # 08
    d12 = jl(P + "kor08/D12/manifest.json")
    d12sha = sha(ROOT / P / "kor08/D12/manifest.json")
    entries = [(h, n) for n, h in d12["fajlok"].items()] + [(h, n) for n, h in d12["adatok"].items()]
    compare_entries(r, "08 D12 manifest", entries)
    for sub in ("J", "M", "N"):
        man = jl(P + f"kor08/{sub}/manifest.json")
        r.check(man["d12_sha256"] == d12sha, f"08 {sub}: the D12 hash in the manifest differs")
        compare_entries(r, f"08 {sub} manifest", [(h, n) for n, h in man["fajlok"].items()])
    g4 = jl(P + "kor08/pecset/K08G3.g4.json")
    r.check(g4["d12_manifest_sha256"] == d12sha, "08 G4 record: the D12 hash differs")
    r.check(g4["pecset"]["sha256"] == sha(ROOT / P / "kor08/pecset/K08G3.json"), "08 G4 record: the seal manifest's hash differs")
    ny = jl(P + "kor08/G5/NYITAS.json")
    for name, h in ny["g4_manifest"].items():
        r.check(sha(pkg(name)) == h, f"08 G5 opening record: {name} hash differs")
    ks = jl(P + "kor08/D12/kepek_kiegeszites.json")
    r.check(ks["manifest_sha256"] == d12sha, "08 D12: image addendum's manifest hash differs")


# --- 2. hash files -------------------------------------------------------------------------------------------------


def check_hashes(r: Report) -> None:
    g5 = sums(ROOT / "results/kor08/G5/g5.sha256")
    for h, name in g5:
        r.check(sha(pkg(name)) == h, f"g5.sha256: {name} differs")
    for f, base in (("results/RESULTS.sha256", ROOT), ("results/PACKAGE.sha256", ROOT)):
        entries = sums(ROOT / f)
        r.notes.append(f"{f}: {len(entries)} files listed")
        for h, name in entries:
            p = base / name
            r.check(p.exists() and sha(p) == h, f"{f}: {name} differs or is missing")


# --- 3. numbers ----------------------------------------------------------------------------------------------------

BA, HI, SZ = "penzugy.bankparositas", "muszaki.hibaelharitas", "szabaly.koltsegelszamolas"
FAM = (BA, HI, SZ)


def nz(x: float, d: int) -> str:
    return f"{x:.{d}f}".replace("-0." + "0" * d, "0." + "0" * d) if abs(x) < 10 ** -d / 2 else f"{x:.{d}f}"


def rng(c, d: int, s: str = "; ") -> str:
    return f"[{nz(c[0], d)}{s}{nz(c[1], d)}]"


def pc(x: float, d: int = 1) -> str:
    return f"{100 * x:.{d}f}%"


def pcrng(c, d: int = 1) -> str:
    return f"[{100 * c[0]:.{d}f}; {100 * c[1]:.{d}f}]"


def build_numbers() -> list[tuple[str, str]]:
    """(label, the string README.md must contain). Minus signs are normalised to ASCII before searching."""
    C: list[tuple[str, str]] = []
    def eq(label: str, s: str) -> None:
        C.append((label, s))
    R = "results/"
    # ---------------------------------------------------------------------------------- 05a
    E5 = jl(R + "kor05/F3/v1a/elemzes05.json")
    IT = jl(R + "kor05/F3/v1a/itelet05.json")
    assert IT["kapu_05b"] is False
    assert IT["H-B1"]["itelet"] == "nem lép tovább" and IT["H-B1"]["teljesul_retegek"] == []
    assert IT["H-T-meta~B1-T"]["teljesul_retegek"] == ["teszt:ho-routing"]
    def d5(layer, a, b):
        pt = E5["pont"][layer]["karok"]
        return pt[a]["atlag"]["aurc_sn"] - pt[b]["atlag"]["aurc_sn"]
    def b5(layer, key):
        return E5["bootstrap"][layer][key]["ci95"]
    L = {"termek": "teszt:ho-termek", "routing": "teszt:ho-routing", "uj": "teszt:ho-uj"}
    for k, layer in L.items():
        pr = E5["pont"][layer]["karok"]["H"]["atlag"].get("sn_prec")
        eq(f"05a {k} dAURC H-B1", f"{d5(layer, 'H', 'B1'):+.4f} {rng(b5(layer, 'H-B1|aurc_sn'), 4)}")
        eq(f"05a {k} H precision", f"{pr:.3f}")
    eq("05a S5 T-meta routing dAURC", f"{d5(L['routing'], 'H-T-meta', 'B1-T'):+.4f} {rng(b5(L['routing'], 'H-T-meta~B1-T|aurc_sn'), 4)}")
    for k, ref in (("L1v", "JEV-a~L1v"), ("G3", "JEV-a~G3")):
        for layer in (L["termek"], L["routing"], L["uj"]):
            arm = "JEV-a"; base = k
            eq(f"05a H6 {ref} {layer}", f"{d5(layer, arm, base):+.4f} {rng(b5(layer, ref + '|aurc_sn'), 4)}")
    eq("05a JEV-a precision termek", f"{E5['pont'][L['termek']]['karok']['JEV-a']['atlag']['sn_prec']:.3f}")
    eq("05a JEV-a precision routing", f"{E5['pont'][L['routing']]['karok']['JEV-a']['atlag']['sn_prec']:.3f}")
    M = jl(R + "kor05/F3/v1a_diag/jev_merleg05.json")["retegek"]["teszt:ho-termek"]["karok"]["JEV-a"]["pont"]
    assert M["elfogadott"] == 1262 and M["hiba"] == 5
    eq("05a JEV-a accepted", "1262")
    eq("05a JEV-a precision working point", f"{100 * M['precizitas']:.1f}%")
    eq("05a JEV-a coverage working point", f"{100 * M['lefedettseg']:.1f}%")
    eq("05a n HO-termek", "3854")
    # ---------------------------------------------------------------------------------- 06
    E6 = jl(R + "kor06/F5/f5_elemzes.json")
    H6 = E6["helyesseg"]["helyes"]
    K6 = E6["kapu"]["helyes"]
    assert K6["teljesul"] and K6["teljesul_d4"] and K6["javulo_retegek"] == 3
    eq("06 ratio", f"{K6['arany']:.3f} {rng(K6['arany_ci95'], 3)}")
    eq("06 lenient ratio", f"{E6['kapu']['helyes_enyhe']['arany']:.3f} {rng(E6['kapu']['helyes_enyhe']['arany_ci95'], 3)}")
    for fam in FAM:
        s = H6[f"{fam}:TESZT"]
        a = s["karok"]
        eq(f"06 {fam} B1-S", f"{a['B1-S']['aurc']:.4f}")
        eq(f"06 {fam} B1-R", f"{a['B1-R|None']['aurc']:.4f}")
        c = s["delta_B1S"]["B1-R|None"]["aurc"]
        eq(f"06 {fam} dAURC", f"{c['pont']:+.4f} {rng(c['ci95'], 4)}")
    B6 = jl(R + "kor06/F5/f5_bontas.json")["retegek"]
    avg = lambda k: sum(B6[f"{f}:TESZT"]["aurc"][k] for f in FAM) / 3
    eq("06 share of the NONE-last rule", f"{100 * (avg('B1-S') - avg('B1-S·NONE-utolsó')) / (avg('B1-S') - avg('B1-R')):.0f}%")
    W6 = jl(R + "kor06/F5/f5_munkapont.json")["csaladok"]
    for fam in FAM:
        p = W6[fam]["B1-R|None"]
        eq(f"06 {fam} working point coverage", f"{p['pont']['sn_lef']:.3f} {rng(p['ci95']['sn_lef'], 3)}")
        eq(f"06 {fam} working point precision", f"{p['pont']['sn_prec']:.3f} {rng(p['ci95']['sn_prec'], 3)}")
        assert W6[fam]["B1-S"]["nincs_munkapont_replika"] == 1.0 or W6[fam]["B1-S"]["nincs_munkapont_pont"]
    # ---------------------------------------------------------------------------------- 07
    E7 = jl(R + "kor07/F5/elemzes.json")
    k1 = E7["k1"]["K1: B1-4R − B1-4S"]["atlag"]
    assert k1["teljesul"]
    eq("07 K1 ratio", f"{k1['arany']:.3f} {rng(k1['arany_ci95'], 3)}")
    k2 = E7["k2"]["karok"]
    for arm in ("B1-R", "B1-4S", "B1-4R", "B1-N", "B1-LR"):
        eq(f"07 K2 {arm} coverage", f"{100 * k2[arm]['hasznos_lef']:.1f}")
    eq("07 K2 B1-R error", f"{100 * k2['B1-R']['lezarasi_hiba']:.1f}%")
    eq("07 K2 B1-4R error", f"{100 * k2['B1-4R']['lezarasi_hiba']:.1f}%")
    eq("07 K2 B1-4R coverage CI", pcrng(k2["B1-4R"]["hasznos_lef_ci95"]))
    assert k2["B1-S"]["hasznos_lef"] == 0
    kv = E7["k2"]["kovetkeztetes"]
    def points(d):
        return f"{100 * d['delta']:+.1f} points {pcrng(d['ci95'])}"
    eq("07 K2 prompt brings in", points(kv["behozza (B1-4S − B1-R)"]))
    eq("07 K2 improves on top", points(kv["javít mellette (B1-4R − B1-4S)"]))
    eq("07 K2 B1-4R vs B1-R", points(kv["B1-4R − B1-R (leíró)"]))
    assert kv["behozza (B1-4S − B1-R)"]["itelet"] == "nem hozza be"
    assert kv["javít mellette (B1-4R − B1-4S)"]["itelet"] == "javít mellette"
    # 07 K3
    K3 = jl(R + "kor07/K3/k3.json")["atlag"]["keret4"]
    for arm in ("B1-4S", "B1-4R"):
        eq(f"07 K3 {arm} AUROC", f"{K3['karok'][arm]['auroc']['pont']:.3f} {rng(K3['karok'][arm]['auroc']['ci95'], 3)}")
    d = K3["parok"]["B1-4R − B1-4S"]["select_aurc"]
    eq("07 K3 dSELECT-AURC", f"{d['pont']:+.3f} {rng(d['ci95'], 3)}")
    cs = jl(R + "kor07/K3/k3.json")["csaladok"]
    eq("07 K3 B1-4R bank AUROC", f"{cs[BA]['keret4']['karok']['B1-4R']['auroc']['pont']:.3f}")
    MP = jl(R + "kor07/K3/munkapont/munkapont.json")["csaladok"]
    for fam, cl, hb in ((BA, 11, 11), (HI, 60, 16), (SZ, 151, 122)):
        r = MP[fam]["keret4"]["összes"]["B1-4R"]
        assert round(r["atlag"]["lezart"]) == cl and round(r["atlag"]["hibas"]) == hb
        eq(f"07 K3 trap closures {fam}", f"{round(100 * hb / cl)}% ({hb} / {cl})")
        eq(f"07 K3 F5 error {fam}", pc(r["f5_teszt_lezarasi_hiba"]))
    AU = jl(R + "kor07/K3/aug/aug.json")["csaladok"]
    aug_expected = {BA: ("29%", "100%"), HI: ("52%", "94%"), SZ: ("24%", "67%")}
    for fam in FAM:
        ro = AU[fam]["keret4"]["sorok"]["összes"]
        a, b = aug_expected[fam]
        assert f"{100 * ro['helyes_eredeti'] / ro['n']:.0f}%" == a and f"{100 * ro['helyes_kiegeszitett'] / ro['n']:.0f}%" == b
        eq(f"07 aug {fam}", f"{a} to {b}")
    # ---------------------------------------------------------------------------------- 08 K2 (G5)
    G = jl(R + "kor08/G5/k2/g5_k2.json")["csaladok"]
    for fam, s in ((BA, "bank"), (HI, "hiba"), (SZ, "szab")):
        g = G[fam]
        eq(f"08 K2 {s} no chain", f"{100 * g['pont']['nelkul']:.1f}%")
        eq(f"08 K2 {s} chain", f"{100 * g['pont']['kinyert']:.1f}%")
        eq(f"08 K2 {s} oracle", f"{100 * g['pont']['orakulum']:.1f}%")
    ne = [G[f]["pont"]["nelkul"] for f in FAM]; ki = [G[f]["pont"]["kinyert"] for f in FAM]; ve = [G[f]["pont"]["veszteseg"] for f in FAM]
    eq("08 K2 no-chain range", f"{100 * min(ne):.0f}–{100 * max(ne):.0f}%")
    eq("08 K2 chain range", f"{100 * min(ki):.1f}–{100 * max(ki):.1f}%")
    eq("08 K2 extraction loss range", f"{100 * min(ve):.1f}–{100 * max(ve):.1f}")
    eq("08 K2 false pass hiba", f"{G[HI]['dbh']} / {G[HI]['atment']} = {100 * G[HI]['pont']['hamis_atengedes']:.1f}%")
    eq("08 K2 sample sizes", f"{G[BA]['n']} / {G[HI]['n']} / {G[SZ]['n']}")
    assert all(not G[f]["lanc_hibak"] for f in FAM)
    J = jl(R + "kor08/J/k2/g5_k2.json")["csaladok"]
    Jr = jl(R + "kor08/J/k2_rogzitett/g5_k2.json")["csaladok"]
    for fam, s in ((BA, "bank"), (HI, "hiba"), (SZ, "szab")):
        eq(f"J {s} n", str(J[fam]["n"]))
        eq(f"J {s} no chain", f"{100 * J[fam]['pont']['nelkul']:.1f}%")
        eq(f"J {s} chain", f"{100 * J[fam]['pont']['kinyert']:.1f}%")
        eq(f"J {s} false pass count", f"{J[fam]['dbh']} / {J[fam]['atment']}")
        assert not J[fam]["lanc_hibak"]
    eq("J hiba frozen chain false pass", f"{Jr[HI]['dbh']} / {Jr[HI]['atment']} = {100 * Jr[HI]['pont']['hamis_atengedes']:.1f}%")
    eq("J szab false pass rate", f"{100 * J[SZ]['pont']['hamis_atengedes']:.1f}%")
    jk = [J[f]["pont"]["kinyert"] for f in FAM]
    eq("J correct range", f"{100 * min(jk):.1f}–{100 * max(jk):.1f}%")
    # K3 natural
    K = jl(R + "kor08/G5/k3/g5_k3.json")["csaladok"]
    for fam, arms in ((SZ, ("L-S", "L-RN", "L-R", "B1-4R")), (HI, ("L-S", "L-RN", "L-R", "B1-4R"))):
        for arm in arms:
            p = K[fam]["pont"][arm]; c = K[fam]["ci95"][arm]
            eq(f"K3 {fam} {arm} coverage", f"{100 * p['hasznos_lef']:.1f}% {pcrng(c['hasznos_lef'])}")
            eq(f"K3 {fam} {arm} error", f"{100 * p['lezarasi_hiba']:.1f}%")
    bk = K[BA]["lanc_kimenet"]
    assert bk["kotes_hibas"] == 0 and bk["n"] == 1000
    eq("K3 bank bindings", f"{bk['kotes']} / {bk['n']}")
    eq("K3 bank B1-4R no chain", f"{100 * K[BA]['pont']['B1-4R']['hasznos_lef']:.1f}% {pcrng(K[BA]['ci95']['B1-4R']['hasznos_lef'])}")
    eq("K3 bank B1-4R no chain error", f"{100 * K[BA]['pont']['B1-4R']['lezarasi_hiba']:.1f}%")
    assert K[BA]["nincs_munkapont_replika"]["L-RN"] == 1.0
    for fam in (SZ, HI):
        d = K[fam]["parok"]["L-RN − L-S"]["hasznos_lef"]
        eq(f"K3 {fam} L-RN-L-S", f"{100 * d['delta']:+.1f} points {pcrng(d['ci95'])}")
        d = K[fam]["parok"]["L-R − L-S"]["hasznos_lef"]
        eq(f"K3 {fam} L-R-L-S", f"{100 * d['delta']:+.1f} points")
    # K1
    def K1fam(sub, fam):
        return jl(R + f"kor08/{sub}/k1/g5_k1.json")["csaladok"][fam]
    S1 = K1fam("G5", SZ)
    def pair(f):
        return f["parok"]["L-RN − L-S"]
    for lab, key in (("(a)", "K1a"), ("(b)", "K1b")):
        a = S1["karok"]["L-RN"][key]; b = S1["karok"]["L-S"][key]; d = pair(S1)[key]
        eq(f"K1{lab} L-RN", f"{a['auroc']:.3f} {rng(a['ci95'], 3)}")
        eq(f"K1{lab} L-S", f"{b['auroc']:.3f} {rng(b['ci95'], 3)}")
        eq(f"K1{lab} delta", f"{d['delta']:+.3f} {rng(d['ci95'], 3)}")
    d = pair(S1)["K1a"]
    assert d["olvasat"] == "javít érdemben"
    eq("K1(a) Holm interval", rng(d["ci_holm"], 3))
    eq("K1(b) reading", pair(S1)["K1b"]["olvasat"] and "not decidable")
    assert pair(S1)["K1b"]["olvasat"] == "nem eldönthető"
    F = jl(R + "kor08/G5_utolagos/felszin/felszin.json")[SZ]
    eq("text-only TF-IDF (char) on G5 K1(a)", f"{F['pont']['karakter']:.3f}")
    Mk = K1fam("M", SZ)
    dM = pair(Mk)["K1a"]; aM = Mk["karok"]["L-RN"]["K1a"]; bM = Mk["karok"]["L-S"]["K1a"]
    eq("M L-RN", f"{aM['auroc']:.3f} {rng(aM['ci95'], 3)}")
    eq("M L-S", f"{bM['auroc']:.3f} {rng(bM['ci95'], 3)}")
    eq("M delta", f"{dM['delta']:.3f} {rng(dM['ci95'], 3)}")
    IM = jl(R + "kor08/M/felszin/illesztes.json")[SZ]
    eq("M fresh text-only CV", f"{IM['friss_karakter']:.3f}")
    Nk = K1fam("N", SZ)
    dN = pair(Nk)["K1a"]; aN = Nk["karok"]["L-RN"]["K1a"]; bN = Nk["karok"]["L-S"]["K1a"]
    eq("N L-RN", f"{aN['auroc']:.3f} {rng(aN['ci95'], 3)}")
    eq("N L-S", f"{bN['auroc']:.3f} {rng(bN['ci95'], 3)}")
    eq("N delta", f"{dN['delta']:.3f} {rng(dN['ci95'], 3)}")
    assert dN["olvasat"] == "javít érdemben"
    t = jl(R + "kor08/N/szoveg.json")
    eq("N text-only (best) on K1(a) set", f"{t['friss_szó']:.3f}")
    assert Nk["egyseg"] == 348
    tr = Nk["a_lezart_tau_felett"]
    eq("N closed above tau, L-RN", f"{tr['L-RN']:.1f}%" if tr["L-RN"] > 1 else pc(tr["L-RN"]))
    eq("N closed above tau, L-S", f"{tr['L-S']:.1f}%" if tr["L-S"] > 1 else pc(tr["L-S"]))
    pc2 = jl(R + "kor08/N/erzekenyseg_parklaszter/g5_k1.json")["csaladok"][SZ]["parok"]["L-RN − L-S"]["K1a"]
    eq("N pair-clustered sensitivity", f"{pc2['delta']:.3f} {rng(pc2['ci95'], 3)}")
    # Audits (aggregate summary)
    A = jl(R + "audit_osszesito.json")
    a1, a2 = A["kor06_1_kor"], A["kor06_2_kor"]
    eq("audit 06 round 1", f"{a1['hiba']} label errors in {a1['atnezve']}")
    eq("audit 06 round 1 upper bound", f"{100 * a1['felso_korlat_95']:.2f} %")
    assert a1["kapu_atment"] is False and a2["kapu_atment"] is True
    eq("audit 06 round 2", f"{a2['hiba']} / {a2['atnezve']}, upper bound {100 * a2['felso_korlat_95']:.2f} %")
    a7 = A["kor07"]
    eq("audit 07", f"{a7['hiba']} / {a7['atnezve']}, upper bound {100 * a7['felso_korlat_95']:.2f} %")
    aD = A["kor08_G1b_D7"]
    eq("audit G1 D7", f"{aD['hiba']} / {aD['atnezve']} label errors (gate failed, upper bound {100 * aD['felso_korlat_95']:.2f} %)")
    G2a = A["kor08_G2_ert_teszt"]["csaladok"]
    def g2(fam):
        c = G2a[fam]["cimkehibaarany_veletlen"]
        return f"{G2a[fam]['veletlen']['hibas_alapeset']} / {G2a[fam]['veletlen']['alapeset']}", 100 * c["alapeset"], c["ci95"]
    nb, rb, cb = g2(BA); nh, rh, ch = g2(HI); ns, rs, cs_ = g2(SZ)
    eq("audit G2 rule", f"{ns} for the rule family [{100 * cs_[0]:.1f}%; {100 * cs_[1]:.1f}%]")
    eq("audit G2 bank", f"{nb} = {rb:.1f} % for bank [{100 * cb[0]:.1f}%; {100 * cb[1]:.1f}%]")
    eq("audit G2 fault", f"{nh} = {rh:.1f} % for fault [{100 * ch[0]:.1f}%; {100 * ch[1]:.1f}%]")
    Na = A["kor08_N"]
    assert Na["kor1"]["elteres"] == 3 and not Na["kor1"]["atment"] and Na["kor2"]["elteres"] == 0 and Na["kor2"]["atment"]
    eq("audit N round 1", f"{Na['kor1']['elteres']} / {Na['kor1']['n']}")
    eq("audit N round 2", f"{Na['kor2']['elteres']} / {Na['kor2']['n']}")
    # Real data (development)
    V = jl(R + "kor08/V/kozvetlen/v_ertekeles.json")
    V0 = jl(R + "kor08/V/v_ertekeles.json")
    la, ls = V["lepcsok"]["lánc"], V["lepcsok"]["lánc + L-S"]
    assert V["n_tetel"] == 262 and la["hibas"] == 0
    eq("K08V chain direct-search bindings", f"{la['lezart']} bindings, 0 errors")
    eq("K08V extracted-reference bindings", f"{V0['lepcsok']['lánc']['lezart']} bindings")
    eq("K08V reference items", f"{V['fedes']['kozvetlen_egy']}")
    mod, mh = ls["lezart"] - la["lezart"], ls["hibas"] - la["hibas"]
    eq("K08V model own closures", f"{mh} / {mod} = {100 * mh / mod:.1f}%")
    eq("K08V chain+model", f"{ls['hibas']} / {ls['lezart']} = {100 * ls['arany']:.1f}%")
    eq("K08V AUROC head", f"{V['auroc']['L-RN']:.3f}")
    eq("K08V AUROC self", f"{V['auroc']['L-S']:.3f}")
    uj = [r["uj"] for r in V["lepcsok"].values()]
    eq("K08V new closures", f"{min(uj)}–{max(uj)}")
    assert jl(R + "kor07/B7/vegleges.json")["n_tetel"] == 262
    return C


def check_numbers(r: Report, list_only: bool = False) -> None:
    text = "" if list_only else (ROOT / "README.md").read_text(encoding="utf-8").replace("−", "-")
    n = 0
    for label, expected in build_numbers():
        n += 1
        if list_only:
            print(f"  {label}: {expected}")
            continue
        r.check(expected.replace("−", "-") in text, f"number not printed in README.md: {label}: {expected}")
    if not list_only:
        r.notes.append(f"numbers: {n} values recomputed from results/ and found in README.md")


def check_freeze_dates(r: Report) -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    P = "protocol/rogzites/"
    dates = {
        "05a": (jl(P + "kor05/v1a/ROGZITES.json")["rogzitve"], "2026-10-29"),
        "06": (jl(P + "kor06/v1/ROGZITES.json")["rogzitve"], "2026-10-31"),
        "07": (jl(P + "kor07/v1/ROGZITES.json")["rogzitve"], "2026-11-01"),
        "K3": (jl(P + "kor07/k3/ROGZITES.json")["rogzitve"], "2026-11-01"),
        "D12": (jl(P + "kor08/D12/manifest.json")["rogzitve"], "2026-11-04"),
        "J": (jl(P + "kor08/J/manifest.json")["rogzitve"], "2026-11-05"),
        "M": (jl(P + "kor08/M/manifest.json")["rogzitve"], "2026-11-06"),
        "N": (jl(P + "kor08/N/manifest.json")["rogzitve"], "2026-11-08"),
    }
    for k, (ts, day) in dates.items():
        r.check(ts.startswith(day), f"freeze date of {k}: record says {ts}, expected {day}")
        r.check(ts[:16].replace("T", " ") in text, f"freeze time of {k} ({ts[:16]}) is not printed in README.md")
    r.notes.append(f"freeze records: {len(dates)} pre-registration times match README.md")


# --- 4. forbidden strings ------------------------------------------------------------------------------------------

SKIP_SUFFIX = {".png", ".pt", ".gz", ".jpg", ".svg"}


def check_forbidden(r: Report) -> None:
    patterns = [("e-mail address", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
                ("username@host", re.compile(r"\b(?:root|ubuntu|nvidia)@[A-Za-z0-9._-]+")),
                ("product database prefix", re.compile(r"(?i)docit[_]")),
                ("absolute home path", re.compile("/ho" "me/[a-z][a-z0-9_-]*")),  # split so this line does not match itself
                ("access token", re.compile(r"\bhf_[A-Za-z0-9]{20,}|Bearer\s+[A-Za-z0-9._~+/-]{20,}|-----BEGIN [A-Z ]*PRIVATE")),
                ("private IPv4 address", re.compile(r"(?<![\d.])(?:10|172\.(?:1[6-9]|2\d|3[01])|192\.168)(?:\.\d{1,3}){2,3}(?![\d.])"))]
    n_files = 0
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file() or p.suffix in SKIP_SUFFIX or p.name.endswith(".pyc") or "__pycache__" in p.parts:
            continue
        n_files += 1
        rel = str(p.relative_to(ROOT))
        try:
            txt = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            r.check(False, f"privacy scan: {rel} is not UTF-8 text")
            continue
        for label, rx in patterns:
            m = rx.search(txt)
            if m:
                r.check(False, f"{label} in {rel}: {txt[max(0, m.start() - 30):m.end() + 30]!r}")
    r.check(True, "privacy scan completed")
    r.notes.append(f"privacy scan: {n_files} text files, {len(patterns)} patterns, nothing found")


def main() -> int:
    if "--list-numbers" in sys.argv:
        r = Report()
        check_numbers(r, list_only=True)
        return 0
    r = Report()
    for step in (check_manifests, check_hashes, check_numbers, check_freeze_dates, check_forbidden):
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
