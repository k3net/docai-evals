#!/usr/bin/env python3
"""A blogcikk számainak ellenőrzése a gépi kimenetekből.

    python3 kor08/publikacio/szamellenorzes.py <cikk.blade.php> hu|en

Minden sor: a JSON-okból számolt érték a cikk formátumában, és hogy szerepel-e a látható szövegben (a képek alt-szövege nem).
A végén kilistázza a látható szöveg azon számait, amelyeket egyik ellenőrzés sem fedett le: ezeket kézzel kell átnézni.
Kilépési kód 1, ha valamelyik érték hiányzik.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
K7, K8, K6, K5 = ROOT / "kor07/eredmenyek", ROOT / "kor08/eredmenyek", ROOT / "kor06/eredmenyek", ROOT / "kor05/eredmenyek"
BA, HI, SZ = "penzugy.bankparositas", "muszaki.hibaelharitas", "szabaly.koltsegelszamolas"
FAM = (BA, HI, SZ)


def jl(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def main():
    cikk, L = sys.argv[1], sys.argv[2]
    s = Path(cikk).read_text(encoding="utf-8")
    t = s[s.index('<div class="prose">'):s.index("@include('partials.blog-author')")]
    t = re.sub(r"<img[^>]*>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t).replace("&nbsp;", " ").replace("&ndash;", "–").replace(" ", " ")
    t = re.sub(r"[ \t\r\n]+", " ", t)

    dec = "," if L == "hu" else "."

    def nm(v, nd=3):
        return f"{v:.{nd}f}".replace(".", dec)

    def pc(v, nd=1):
        return nm(100 * v, nd) + "%"

    def rng(a, b, nd=1):
        return f"{nm(100 * a, nd)}–{nm(100 * b, nd)}%"

    S = {"hu": lambda a, b: f"{a}-ról {b}-ra", "en": lambda a, b: f"from {a} to {b}"}[L]
    C = []

    def chk(nev, *minta):
        C.append((nev, minta))

    # 05a
    it = jl(K5 / "F3/v1a/itelet05.json")
    assert it["H-B1"]["teljesul_retegek"] == [], "05a: a H-B1 valamelyik rétegen teljesül"
    # 06: a NONE-hátrasorolás részesedése (átlagos AURC-ból)
    b6 = jl(K6 / "F5/f5_bontas.json")["retegek"]
    a = lambda k: sum(b6[f"{f}:TESZT"]["aurc"][k] for f in FAM) / 3  # noqa: E731
    chk("06: a szabály részesedése", pc((a("B1-S") - a("B1-S·NONE-utolsó")) / (a("B1-S") - a("B1-R")), 0))
    # 07 K2
    k2 = jl(K7 / "F5/elemzes.json")["k2"]["karok"]
    assert k2["B1-S"]["hasznos_lef"] == 0
    chk("07 K2 B1-R lefedettség", pc(k2["B1-R"]["hasznos_lef"]))
    chk("07 K2 B1-R hiba", pc(k2["B1-R"]["lezarasi_hiba"]))
    chk("07 K2 B1-4S lefedettség", pc(k2["B1-4S"]["hasznos_lef"]))
    chk("07 K2 B1-4R lefedettség", pc(k2["B1-4R"]["hasznos_lef"]))
    # 07 K3
    mp = jl(K7 / "K3/munkapont/munkapont.json")["csaladok"]
    for f in FAM:
        r = mp[f]["keret4"]["összes"]["B1-4R"]
        chk(f"K3 {f}: F5 hiba", pc(r["f5_teszt_lezarasi_hiba"]))
        lez, hib = round(r["atlag"]["lezart"]), round(r["atlag"]["hibas"])
        chk(f"K3 {f}: csapda", f"{round(100 * hib / lez)}% ({hib} / {lez})")
    au = jl(K7 / "K3/aug/aug.json")["csaladok"]
    for f in FAM:
        r = au[f]["keret4"]["sorok"]["összes"]
        chk(f"K3 páros {f}", S(pc(r["helyes_eredeti"] / r["n"], 0), pc(r["helyes_kiegeszitett"] / r["n"], 0)))
    # 08 K2 és J
    g = jl(K8 / "G5/k2/g5_k2.json")["csaladok"]
    j = jl(K8 / "J/k2/g5_k2.json")["csaladok"]
    ne = [g[f]["pont"]["nelkul"] for f in FAM]
    ki = [g[f]["pont"]["kinyert"] for f in FAM]
    ve = [g[f]["pont"]["veszteseg"] for f in FAM]
    chk("G5 lánc nélkül", rng(min(ne), max(ne), 0))
    chk("G5 lánccal", rng(min(ki), max(ki)))
    chk("G5 kinyerés vesztesége", f"{nm(100 * min(ve), 1)}–{nm(100 * max(ve), 1)}")
    chk("G5 hamis átengedés (hiba)", pc(g[HI]["pont"]["hamis_atengedes"]))
    jk = [j[f]["pont"]["kinyert"] for f in FAM]
    chk("J lánccal", f"{nm(100 * min(jk), 1)}–{nm(100 * max(jk), 0)}%")
    ja = [j[f]["pont"]["hamis_atengedes"] for f in FAM]
    assert ja[0] == 0 and ja[1] == 0
    chk("J hamis átengedés", pc(ja[2]))
    k3 = jl(K8 / "G5/k3/g5_k3.json")["csaladok"][BA]["lanc_kimenet"]
    assert k3["kotes_hibas"] == 0
    chk("G5 K3 kötés", str(k3["kotes"]), str(k3["n"]))
    chk("csapdatételek száma", str(sum(g[f]["n"] for f in FAM)))
    chk("javító kör tételszáma", str(sum(j[f]["n"] for f in FAM)))
    # 08 K1 és ellenpróbák
    G, M, N = (jl(K8 / f"{x}/k1/g5_k1.json")["csaladok"][SZ] for x in ("G5", "M", "N"))
    chk("minimális párok egységszáma", str(N["egyseg"]))
    chk("G5 L-S", nm(G["karok"]["L-S"]["K1a"]["auroc"]))
    chk("G5 L-RN", nm(G["karok"]["L-RN"]["K1a"]["auroc"]))
    chk("G5 Δ", "+" + nm(G["parok"]["L-RN − L-S"]["K1a"]["delta"]))
    assert G["parok"]["L-RN − L-S"]["K1a"]["ci_holm"][0] > 0
    assert G["parok"]["L-RN − L-S"]["K1b"]["olvasat"] == "nem eldönthető"
    chk("G5 szöveges", nm(jl(K8 / "G5_utolagos/felszin/felszin.json")[SZ]["pont"]["karakter"]))
    chk("M szöveges", nm(jl(K8 / "M/felszin/illesztes.json")[SZ]["friss_karakter"]))
    chk("M Δ", nm(M["parok"]["L-RN − L-S"]["K1a"]["delta"]))
    chk("N szöveges", nm(jl(K8 / "N/szoveg.json")["friss_szó"]))
    chk("N Δ", "+" + nm(N["parok"]["L-RN − L-S"]["K1a"]["delta"]))
    chk("N τ fölött, L-RN", nm(N["a_lezart_tau_felett"]["L-RN"], 1) + "%" if N["a_lezart_tau_felett"]["L-RN"] > 1 else pc(N["a_lezart_tau_felett"]["L-RN"]))
    chk("N τ fölött, L-S", nm(N["a_lezart_tau_felett"]["L-S"], 1) + "%" if N["a_lezart_tau_felett"]["L-S"] > 1 else pc(N["a_lezart_tau_felett"]["L-S"]))
    # Valódi adat (fejlesztési)
    v0 = jl(K8 / "V/v_ertekeles.json")
    v = jl(K8 / "V/kozvetlen/v_ertekeles.json")
    la, ls = v["lepcsok"]["lánc"], v["lepcsok"]["lánc + L-S"]
    assert la["hibas"] == 0
    chk("V közlemény", str(v["fedes"]["kozvetlen_egy"]))
    chk("V kinyert hivatkozás", str(v0["fedes"]["kinyert_egy"]))
    chk("V kinyert kötés", str(v0["lepcsok"]["lánc"]["lezart"]))
    chk("V keresés kötés", f"{la['lezart']} ")
    mod, mh = ls["lezart"] - la["lezart"], ls["hibas"] - la["hibas"]
    chk("V modell saját", str(mod))
    chk("V modell saját hiba", pc(mh / mod))
    chk("V lánc + modell", str(ls["lezart"]))
    chk("V lánc + modell hiba", pc(ls["arany"]))
    chk("V AUROC fej", nm(v["auroc"]["L-RN"]))
    chk("V AUROC alany", nm(v["auroc"]["L-S"]))
    uj = [r["uj"] for r in v["lepcsok"].values()]
    chk("V új lezárás", f"{min(uj)}–{max(uj)}")
    assert v["n_tetel"] == 262

    hiany, fedett = 0, []
    for nev, minta in C:
        for m in minta:
            ok = m in t
            hiany += not ok
            fedett.append(m.strip())
            print(("  ok   " if ok else "HIÁNYZIK ") + f"{nev}: {m}")
    tok = sorted(set(re.findall(r"\+?\d[\d ]*(?:[.,]\d+)?(?:–\d+(?:[.,]\d+)?)?%?", t)), key=lambda x: t.index(x))
    maradek = [x.strip() for x in tok if x.strip() and not any(x.strip() in f or f in x.strip() for f in fedett)]
    print("\nLe nem fedett számok (kézi átnézés):")
    print(" | ".join(maradek))
    print(f"\n{len(C)} ellenőrzés, hiányzik: {hiany}")
    sys.exit(1 if hiany else 0)


if __name__ == "__main__":
    main()
