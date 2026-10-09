"""K01F4 — a 01-es kör eredménylapja az `f4_elemzes01.py` és a `h4_egyezes.py` kimenetéből, a nyers kiolvasásokkal.

Bemenet: kor01/eredmenyek/F4/{f4_elemzes.json, h4/h4.json, vllm/*.jsonl}, az F3 motor-hűségi kiolvasásai és az itemfájlok
(a T-hu átcímkézéseihez). Az értelmező szöveg (mechanizmus, JEV-összevetés) kézzel írt, a
kor01/eredmenyek/F4/ertelmezes.md-ből kerül a lap végére, így a lap újragenerálása nem írja felül.
Kimenet: kor01/eredmenyek/F4/eredmenylap.md és eredmenylap.json (a leíró bontások számai).

Az L3 sorai a három seed átlagát mutatják, zárójelben a seedek lef@95-tartományával. Az ítéletek az előre rögzített
szabályok szerint (01-runbook v1, 6.2 és 8. pont). A „Leíró bontások” szakasz utólagos: magyaráz, ítéletet nem változtat.

  python3 kor01/eszkozok/f4_riport01.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "eszkozok"))
from common import read_jsonl, write_json  # noqa: E402
from f4_elemzes01 import layers, load_arm, load_meta01  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
F4 = ROOT / "eredmenyek/F4"
V = F4 / "vllm"
SEEDS = ("s1", "s2", "s3")
LAYERS = [("pool", "H1-pool"), ("T-BFCL-live+W2C", "T-BFCL-live + When2Call (H2)"), ("T-hu", "T-hu (H2)"),
          ("T-BFCL", "T-BFCL (leíró)"), ("T-katalogus", "T-katalógus (leíró)"), ("T-uj-eszkoz", "T-új-eszköz (leíró)")]
COLS = ["besorolasi_lefedettseg", "besorolasi_precizitas", "aurc", "ece", "x_precizitas", "x_fedes", "pontossag"]


def fmt(x, nd: int = 3) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "—"
    return f"{x:.{nd}f}".replace(".", ",")


def ci(b: dict, nd: int = 3, pont: bool = True) -> str:
    """Δ bootstrap-medián és 95% CI; pont = True esetén százalékpontban."""
    k = 100 if pont else 1
    u = " pont" if pont else ""
    lo, hi = b["ci95"]
    p = b["p_ketoldali"]
    ps = "p < 0,0001" if p < 1e-4 else f"p = {fmt(p, 4)}"
    return f"Δ = {fmt(b['delta_median'] * k, 1 if pont else nd)}{u} [{fmt(lo * k, 1 if pont else nd)}; {fmt(hi * k, 1 if pont else nd)}], {ps}"


def arm_row(name: str, ms: list[dict], plafon: float, extra: str = "") -> str:
    avg = {c: np.mean([m[c] for m in ms if m.get(c) is not None]) if any(m.get(c) is not None for m in ms) else None
           for c in COLS}
    bukas = any(m["precizitas_bukas"] for m in ms)
    lefs = [m["besorolasi_lefedettseg"] for m in ms]
    rng = f" [{fmt(min(lefs))}–{fmt(max(lefs))}]" if len(ms) > 1 else ""
    return (f"| {name}{extra}{rng} | {fmt(avg['besorolasi_lefedettseg'])} ({fmt(avg['besorolasi_lefedettseg'] / plafon, 2)}) "
            f"| {fmt(avg['besorolasi_precizitas'])}{' ⚠' if bukas else ''} | {fmt(avg['aurc'], 4)} | {fmt(avg['ece'])} "
            f"| {fmt(avg['x_precizitas'])} / {fmt(avg['x_fedes'])} | {fmt(avg['pontossag'])} |")


def engine_fidelity() -> dict:
    out = {}
    for k in (1, 2, 3):
        d = ROOT / f"eredmenyek/F3/k01_l3mixse_p30_s{k}"
        if not (d / "hf_val.jsonl").exists():
            continue
        v = {r["id"]: r["pred"] for r in read_jsonl(d / "vllm_val.jsonl") if r["perm"] == 0}
        h = read_jsonl(d / "hf_val.jsonl")
        out[f"s{k}"] = sum(v.get(r["id"]) == r["pred"] for r in h) / len(h)
    return out


def x_cells(arms: dict, taus: dict, meta: dict, items: dict, nat: dict | None) -> list[dict]:
    """Forrásonként (BFCL, When2Call): X-itemeken az X-fedés (top = X) és az @95 besorolt X arány; nem-X itemeken a
    lefedettség és a precizitás @95."""
    cells = defaultdict(list)
    for i, it in items.items():
        if meta.get(i, {}).get("ketertelmu") or not it["forras"].startswith(("bfcl", "w2c")):
            continue
        cells[(it["forras"], it["gold"] is None)].append(i)
    rows = []
    for (src, x), ids in sorted(cells.items()):
        r = {"forras": src, "x": x, "n": len(ids)}
        for a, p in arms.items():
            if x:
                r[a] = {"x_fedes": sum(p[i][0] is None for i in ids) / len(ids),
                        "x_besorolva95": sum(p[i][0] is not None and p[i][1] >= taus[a] for i in ids) / len(ids)}
            else:
                auto = [i for i in ids if p[i][0] is not None and p[i][1] >= taus[a]]
                r[a] = {"lef95": len(auto) / len(ids),
                        "prec95": sum(p[i][0] == meta[i]["gold"] for i in auto) / max(1, len(auto))}
        if nat:
            r["L0n"] = ({"x_fedes": sum(nat[i]["pred"] is None for i in ids) / len(ids)} if x else
                        {"hivas_helyes": sum(nat[i]["pred"] == meta[i]["gold"] for i in ids) / len(ids)})
        rows.append(r)
    return rows


def relabel_thu(arms: dict, taus: dict, meta: dict, items: dict, ids: list[str]) -> dict:
    """A T-hu átnézésben átcímkézett itemjei: a régi vagy az új címkét adja-e a kar, és a réteg mérőszámai nélkülük."""
    from elemzes import FAIL_BELOW, metrics
    rel = [i for i in ids if (items[i]["meta"].get("atnezes") or {}).get("muvelet") == "javit"]
    rs = set(rel)
    out: dict = {"n_reteg": len(ids), "n_atcimkezett": len(rel)}
    for a, p in arms.items():
        old = [i for i in rel if p[i][0] == items[i]["meta"]["atnezes"].get("regi_gold")]
        m_all = metrics(p, meta, ids, taus[a], FAIL_BELOW["95"])
        m_ex = metrics(p, meta, [i for i in ids if i not in rs], taus[a], FAIL_BELOW["95"])
        out[a] = {"regi_cimke": len(old), "regi_cimke_tau_folott": sum(p[i][1] >= taus[a] for i in old),
                  "uj_cimke": sum(p[i][0] == meta[i]["gold"] for i in rel),
                  "teljes": {k: m_all[k] for k in ("besorolasi_lefedettseg", "besorolasi_precizitas", "aurc")},
                  "atcimkezettek_nelkul": {k: m_ex[k] for k in ("besorolasi_lefedettseg", "besorolasi_precizitas", "aurc")}}
    return out


def common_coverage(arms: dict, meta: dict, ids: list[str]) -> dict:
    """Kockázat–lefedettség görbe (a kar nem-X döntései bizalom szerint), közös lefedettségre vágva."""
    s = [i for i in ids if not meta[i].get("ketertelmu")]
    curves = {}
    for a, p in arms.items():
        o = sorted([i for i in s if p[i][0] is not None], key=lambda i: -p[i][1])
        err = np.cumsum([p[i][0] != meta[i]["gold"] for i in o])
        curves[a] = err / np.arange(1, len(o) + 1)
    m = min(len(c) for c in curves.values())
    out: dict = {"kozos_lefedettseg": m / len(s)}
    for a, c in curves.items():
        out[a] = {"aurc_kozos": float(c[:m].mean()),
                  **{f"kockazat@{cov}": float(c[int(cov * len(s)) - 1]) for cov in (0.5, 0.6) if int(cov * len(s)) <= len(c)}}
    return out


def hybrid(base: dict, l3: dict) -> dict:
    """Kétlépcsős (utólagos, leíró): a hívjon-e kérdést a bázis P(X)-e dönti el, az eszközt az L3 választja:
    P(X) = P_bázis(X), P(eszköz) = (1 − P_bázis(X)) · P_L3(eszköz | nem X)."""
    out = {}
    for i in base:
        pb, p3 = base[i][2], l3[i][2]
        px, rest = pb.get(None, 0.0), 1 - p3.get(None, 0.0)
        sc = {None: px, **{k: (1 - px) * v / rest for k, v in p3.items() if k is not None}} if rest > 0 else pb
        k = max(sc, key=lambda key: sc[key])
        out[i] = (k, sc[k], sc)
    return out


def s2_breakdown(rows: list[dict]) -> dict:
    c = Counter()
    for r in rows:
        g = "X" if r["gold"] is None else "nemX"
        p = "nincs" if not r["van_valasz"] else ("X" if r["pred"] is None else ("jo" if r["pred"] == r["gold"] else "rossz"))
        c[f"{g}->{p}"] += 1
    return dict(c)


def main() -> None:
    res = json.loads((F4 / "f4_elemzes.json").read_text())
    h4 = json.loads((F4 / "h4/h4.json").read_text())
    meta = load_meta01()
    items = {it["id"]: it for it in read_jsonl(ROOT / "adat/items_teszt.jsonl")}
    pont = res["pont"]
    rm = res["retegmeret"]

    arms = {"L1★": load_arm(V, "bazis_val", "bazis_test", meta, "perm_avg")[0]}
    for k in SEEDS:
        arms[f"L3 {k}"] = load_arm(V, f"l3_{k}_val", f"l3_{k}_test", meta, "temp")[0]
    taus = {"L1★": pont["L1csillag"]["95"]["tau"], **{f"L3 {k}": pont[f"L3_{k}"]["95"]["tau"] for k in SEEDS}}
    test_ids = [i for i in arms["L1★"] if meta[i]["split"] != "val"]
    uj = {r["id"] for r in read_jsonl(ROOT / "eredmenyek/F1S/uj_eszkoz.jsonl") if r["t_uj_eszkoz"]}
    L = layers(meta, test_ids, uj, set())
    nat = {r["id"]: r for r in read_jsonl(V / "l0n_test.jsonl")} if (V / "l0n_test.jsonl").exists() else None

    leiro = {"motor_huseg_val_hf_vllm": engine_fidelity(),
             "x_cellak": x_cells(arms, taus, meta, items, nat),
             "t_hu_atcimkezes": relabel_thu(arms, taus, meta, items, L["T-hu"]),
             "kozos_lefedettseg": {p: common_coverage(arms, meta, L[p]) for p in ("pool", "T-BFCL-live+W2C", "T-hu")},
             "hibrid": {},
             "s2_bontas": s2_breakdown(read_jsonl(V / "s2_test.jsonl")) if (V / "s2_test.jsonl").exists() else None}
    from elemzes import FAIL_BELOW, choose_tau, metrics
    val_ids = [i for i in arms["L1★"] if meta[i]["split"] == "val"]
    for k in SEEDS:
        h = hybrid(arms["L1★"], arms[f"L3 {k}"])
        tau = choose_tau(h, meta, val_ids, 0.95)
        leiro["hibrid"][k] = {p: {c: metrics(h, meta, L[p], tau, FAIL_BELOW["95"])[c] for c in
                                  ("besorolasi_lefedettseg", "besorolasi_precizitas", "precizitas_bukas", "aurc", "x_fedes")}
                              for p in ("pool", "T-BFCL-live+W2C", "T-hu")}
    write_json(F4 / "eredmenylap.json", leiro)

    o = ["# K01F4 eredménylap (01-runbook v1, 6. és 8. pont)", "",
         f"A számok a teszten; τ@95 és a temperature a val-on rögzítve (n(val) = {res['n_val']}, n(teszt) = {res['n_teszt']}). "
         f"Az L1★ temperature-e {fmt(res['L1_temperature'])}; az L3-é seedenként "
         + ", ".join(f"{k} {fmt(v)}" for k, v in res["L3_temperature"].items())
         + f". Bootstrap: {res['bootstrap']['reps']} ismétlés, seed × klaszter, a val minden replikában újramintázva és τ "
         "újraválasztva. Generálta: `kor01/eszkozok/f4_riport01.py`.", "",
         "**Definíciók.** Besorolási lef@95: a pontozott itemek aránya, amelyeket a kar a τ@95 fölött eszközhöz rendel "
         "(zárójelben a plafonhoz mért arány; a plafon a réteg pontozott nem-X aránya). Elért precizitás: a helyes eszköz "
         "aránya a besoroltak közt; ⚠ = precizitás-bukás (< 0,93). X-prec: a kar X-válaszai közül hány X-gold; X-fedés: "
         "az X-gold itemek közül hánynál X a kar top-válasza (τ-független, a H5 definíciója). Az AURC a kar saját nem-X "
         "döntéseinek görbéjén számolódik (a 00 definíciója); a közös lefedettségre vágott változat a leíró bontásokban.", ""]

    o += ["## Rétegek", ""]
    for key, title in LAYERS:
        if key not in rm:
            continue
        plaf = rm[key]["plafon"]
        o += [f"**{title}** — n = {rm[key]['n']}, pontozott {rm[key]['pontozott']}, plafon {fmt(plaf)}", "",
              "| kar | besorolási lef@95 (/plafon) | elért precizitás | AURC | ECE | X-prec / X-fedés | pontosság |",
              "|---|---|---|---|---|---|---|"]
        o.append(arm_row("L0", [pont["L0"]["95"]["retegek"][key]], plaf))
        o.append(arm_row("L1★ (perm. átlag + temperature)", [pont["L1csillag"]["95"]["retegek"][key]], plaf))
        o.append(arm_row("L3 (`temp`, 3 seed átlaga", [pont[f"L3_{k}"]["95"]["retegek"][key] for k in SEEDS], plaf, ")"))
        o.append("")
    if "L0n_pont_pool" in res:
        n0 = res["L0n_pont_pool"]
        o += [f"**L0n (natív tool calling), H1-pool:** hívásarány {fmt(n0['lefedettseg'])}, a hívások precizitása "
              f"{fmt(n0['precizitas'])}, X-fedés {fmt(n0['x_fedes'])}, ismeretlen eszköznév {n0['ismeretlen_nev']}.", ""]

    h1 = res["H1"]
    o += ["## Hipotézisek", "", "| hipotézis | ítélet | részletek |", "|---|---|---|"]
    o.append(f"| H1 (L3 vs. L1★, pool, Holm) | **{'igaz' if h1['teljesul'] else 'cáfolt'}** | "
             f"lef@95: {ci(res['bootstrap']['L3_minus_L1csillag']['pool:lef95'])}; cáfolat: {'; '.join(h1['lef95']['cafolat']) or '—'}. "
             f"AURC: {ci(res['bootstrap']['L3_minus_L1csillag']['pool:aurc'], 4, False)}; cáfolat: {'; '.join(h1['aurc']['cafolat']) or '—'} |")
    for part, b in res["H2"].items():
        if not b["H2_reteg"]:
            continue
        o.append(f"| H2 — {part} | **{b['itelet']}** | lef@95: {ci(b)}; AURC (másodlagos): {ci(b['aurc'], 4, False)} |")
    if "H3" in res:
        h3 = res["H3"]
        o.append(f"| H3 (L3 vs. L0n, az L0n munkapontján) | **{'igaz' if h3['teljesul'] else 'cáfolt'}** | "
                 f"(i) precizitás az L0n lefedettségén: {ci(h3['prec_az_L0n_lefedettsegen'])}; (ii) lefedettség az L0n "
                 f"precizitásán: {ci(h3['lef_az_L0n_precizitasan'])}; X-fedés (L3 − L0n, leíró): {ci(h3['x_fedes_L3_minus_L0n'])} |")
    o.append("| H4 (két adapter egy példányon) | **" + ("igaz" if h4["H4"] else "cáfolt") + "** | "
             + "; ".join(f"{k}: egyezés {fmt(v['egyezes'], 4)}, zaj-alap {fmt(v['zaj_egyezes'], 4)}, Δ alsó95 "
                         f"{fmt(v['d_also95_egyoldali'] * 100, 2)} pont" for k, v in h4.items() if isinstance(v, dict)) + " |")
    h5 = res["H5"]
    o.append(f"| H5 (nincs irrelevancia-kompromisszum) | **{'igaz' if h5['teljesul'] else 'cáfolt'}** | "
             f"X-fedés: {ci(h5['x_fedes'])} (küszöb: alsó > −2 pont); nem-X pontosság: {ci(h5['nemx_pontossag'])} |")
    o.append("")
    o += ["**Leíró rétegek (Δ lef@95, L3 − L1★):** "
          + "; ".join(f"{p}: {ci(b)} ({b['itelet']})" for p, b in res["H2"].items() if not b["H2_reteg"]) + ".", "",
          f"**Másodlagos (pool):** lef@90 {ci(h1['masodlagos_lef90'])}; X-arány-standardizált lef@95: 25% X "
          f"{ci(h1['x_standardizalt']['x25'])}, 10% X {ci(h1['x_standardizalt']['x10'])}; ECE "
          f"{ci(res['bootstrap']['L3_minus_L1csillag']['pool:ece'], 3, False)}.", ""]

    o += ["## Publikálási szabály (01-runbook 8. pont)", "",
          ("A H1 cáfolt, ezért a „H1 bukik” sor érvényes: az adatkészlet publikus, az adapter nem, a tanulmány "
           "„a kalibrált logit elég” negatív eredményként publikálható." if not h1["teljesul"] else
           "A H1 igaz; a sor a H2-ítéletektől függ."), ""]

    o += ["## Zaj és motor", ""]
    if "ismetlesi_zaj_L0_L0vesszo" in res:
        z = res["ismetlesi_zaj_L0_L0vesszo"]
        o.append(f"- **Ismétlési zaj (L0 ↔ L0′, ugyanazon a példányon):** top-címke billenés {fmt(z['top_cimke_billenes'], 4)}, "
                 f"átl. |Δp| {fmt(z['abs_dp_atlag'], 4)} (max {fmt(z['abs_dp_max'], 3)}), lef@95-különbség rögzített τ-val "
                 f"{fmt(z['lef95_kulonbseg_rogzitett_tau'], 4)}.")
    if "permutacios_billenes_L3_s1_pool" in res:
        o.append(f"- **Permutációs billenés a poolon** (a 4 sorrend közt változik a döntött opció): L3 s1 "
                 f"{fmt(res['permutacios_billenes_L3_s1_pool'])}, bázis {fmt(res['permutacios_billenes_bazis_pool'])}.")
    o.append("- **Motor-hűség (val, perm 0, HF ↔ vLLM top-1 egyezés):** "
             + ", ".join(f"{k} {fmt(v, 4)}" for k, v in leiro["motor_huseg_val_hf_vllm"].items()) + ".")
    o.append("- **McNemar a poolon (L3 vs. L1★, top-1 helyes):** "
             + "; ".join(f"{k.split('_vs')[0]}: csak L1★ jó {v['csak_a_jo']}, csak L3 jó {v['csak_b_jo']}"
                         for k, v in res["mcnemar_pool"].items()) + ".")
    if "L3_S2" in res:
        s = res["L3_S2"]
        o += ["", "## L3→S2 (leíró)", "",
              f"τ@95 = {fmt(s['tau95_L3'])} (L3 s1). A τ alatti pool-itemek ({s['s2_kapott']}) a bázis gondolkodó módjához "
              f"mennek: válaszolt {s['s2_valaszolt']}, ebből eszközhöz rendelt {s['s2_besorolt']} (precizitás "
              f"{fmt(s['s2_precizitas'])}); késleltetés mediánja {fmt(s['s2_kesleltetes_median_s'], 1)} s. Együtt: lefedettség "
              f"{fmt(s['lefedettseg'])}, precizitás {fmt(s['precizitas'])}, X-fedés {fmt(s['x_fedes'])}.",
              "Bontás (gold → S2-válasz): " + ", ".join(f"{k} {v}" for k, v in sorted(leiro["s2_bontas"].items())) + "."]

    o += ["", "## Leíró bontások (utólagos, F4 után; ítéletet nem változtatnak)", "",
          "**BFCL és When2Call forrásonként.** X-itemeken: X-fedés / az @95 eszközhöz rendelt X-arány; nem-X itemeken: "
          "lef@95 / precizitás@95. L0n: X-itemen a hívás nélküli arány, nem-X itemen a helyes hívás aránya.", "",
          "| forrás | n | " + " | ".join(arms) + (" | L0n |" if nat else " |"), "|---|---|" + "---|" * (len(arms) + bool(nat))]
    for r in leiro["x_cellak"]:
        cells = []
        for a in arms:
            c = r[a]
            cells.append(f"{fmt(c['x_fedes'])} / {fmt(c['x_besorolva95'])}" if r["x"] else f"{fmt(c['lef95'], 2)} / {fmt(c['prec95'])}")
        tail = ""
        if nat:
            tail = f" | {fmt(r['L0n']['x_fedes'] if r['x'] else r['L0n']['hivas_helyes'])}"
        o.append(f"| {r['forras']}{' (X)' if r['x'] else ''} | {r['n']} | " + " | ".join(cells) + tail + " |")
    t = leiro["t_hu_atcimkezes"]
    o += ["", f"**T-hu átcímkézett itemjei.** A réteg {t['n_reteg']} itemjéből {t['n_atcimkezett']}-et javított az "
          "átnézés (új eszköz vagy X). Karonként: hánynál adja a régi MASSIVE-címkét (ebből a τ@95 fölött), hánynál az újat; "
          "a réteg lef@95 / precizitás / AURC értéke teljesen és az átcímkézettek nélkül.", "",
          "| kar | régi címke (τ fölött) | új címke | teljes | átcímkézettek nélkül |", "|---|---|---|---|---|"]
    for a in arms:
        c = t[a]
        f_ = lambda m: f"{fmt(m['besorolasi_lefedettseg'])} / {fmt(m['besorolasi_precizitas'])} / {fmt(m['aurc'], 4)}"
        o.append(f"| {a} | {c['regi_cimke']} ({c['regi_cimke_tau_folott']}) | {c['uj_cimke']} | {f_(c['teljes'])} | "
                 f"{f_(c['atcimkezettek_nelkul'])} |")
    o += ["", "**Kockázat közös lefedettségen.** A görbéket a legrövidebb kar lefedettségéig vágva (AURC@közös), "
          "valamint a kockázat 0,5 és 0,6 lefedettségnél.", "",
          "| réteg | közös lef. | " + " | ".join(arms) + " |", "|---|---|" + "---|" * len(arms)]
    for p, c in leiro["kozos_lefedettseg"].items():
        o.append(f"| {p} | {fmt(c['kozos_lefedettseg'])} | " + " | ".join(
            f"{fmt(c[a]['aurc_kozos'], 4)} · r@0,5 {fmt(c[a].get('kockazat@0.5'))} · r@0,6 {fmt(c[a].get('kockazat@0.6'))}"
            for a in arms) + " |")

    o += ["", "**Kétlépcsős (bázis P(X) + L3 eszközválasztás).** A hívjon-e kérdést a bázis (L1★) P(X)-e dönti el, az eszközt "
          "az L3; τ@95 a val-on. Rétegenként lef@95 / precizitás / AURC / X-fedés.", "",
          "| seed | " + " | ".join(p for p in ("pool", "T-BFCL-live+W2C", "T-hu")) + " |", "|---|---|---|---|"]
    for k, r in leiro["hibrid"].items():
        o.append(f"| hibrid {k} | " + " | ".join(
            f"{fmt(m['besorolasi_lefedettseg'])} / {fmt(m['besorolasi_precizitas'])}{' ⚠' if m['precizitas_bukas'] else ''} / "
            f"{fmt(m['aurc'], 4)} / {fmt(m['x_fedes'])}" for m in r.values()) + " |")

    ert = F4 / "ertelmezes.md"
    if ert.exists():
        o += ["", ert.read_text().rstrip()]
    (F4 / "eredmenylap.md").write_text("\n".join(o) + "\n")
    print(f"kész: {F4 / 'eredmenylap.md'}")


if __name__ == "__main__":
    main()
