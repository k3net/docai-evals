#!/usr/bin/env python3
"""Mérés-részletek riport — a `qwen3.8-flash-next/eredmenyek/01-meres-reszletek.md` formátumában,
a magyar-kie-eval riportjaiból. MINDEN szám a reports/*.json-ból számolt; a fájl teljes egészében
generált, kézzel ne szerkeszd (futtasd újra: python3 src/reszletek.py > <cél>)."""
import json, statistics as st, sys
from pathlib import Path
from collections import OrderedDict

R = Path("reports")

# (címke, fájl, motor-leírás) — sorrend = a riport sorrendje
SUITEK = OrderedDict([
    ("Fő suite (T1–T10, 50 item × 3 futás, 100 pont)", [
        ("Flash IQ4_XS · llama.cpp · 4k keret", "meres-flash-next.json"),
        ("Flash NVFP4 · vLLM+mmap-PLE · MTP=2 · 16k keret", "meres-flash-nvfp4.json"),
        ("35B FP8 · vLLM · MTP=2 · 4k keret", "meres-qwen36.json"),
        ("35B FP8 · vLLM · MTP=2 · 16k keret", "meres-qwen36-16k.json"),
        ("122B NVFP4 · vLLM · 16k keret", "meres-122b.json"),
    ]),
    ("Nehéz suite (T11–T20, 10 item × 3 futás, 100 pont)", [
        ("Flash IQ4_XS · llama.cpp", "nehez-flash.json"),
        ("Flash NVFP4 · vLLM+mmap-PLE · MTP=2", "nehez-flash-nvfp4.json"),
        ("35B FP8 · vLLM", "nehez-qwen36.json"),
        ("122B NVFP4 · vLLM", "nehez-122b.json"),
    ]),
    ("Hosszú kontextus suite (T21–T25, 5 item × 1 futás, 217k token, 100 pont)", [
        ("Flash IQ4_XS · llama.cpp · cache_prompt=false", "hosszu-flash.json"),
        ("Flash IQ4_XS · llama.cpp · prompt-cache MELEG", "hosszu-flash-cache.json"),
        ("Flash NVFP4 · vLLM+mmap-PLE · MTP=2", "hosszu-flash-nvfp4.json"),
        ("35B FP8 · vLLM", "hosszu-qwen36.json"),
        ("122B NVFP4 · vLLM", "hosszu-122b.json"),
    ]),
    ("Izoláció — a 13 instabil item × 5 futás, Flash NVFP4 (egyszerre egy kapcsoló)", [
        ("MTP=0 (spekulatív dekódolás KI)", "izo-mtp0.json"),
        ("cudagraph_mode=NONE", "izo-cgnone.json"),
        ("VLLM_PLE_MMAP_WORKERS=1", "izo-w1.json"),
        ("⭐ egzakt kanonikus top-k a QSA persistent_topk helyett (MTP=2 marad)", "izo-topk.json"),
    ]),
])
CHALLENGE = [
    ("Flash IQ4_XS · llama.cpp", "challenge__flash.json"),
    ("Flash NVFP4 · vLLM", "challenge__flash-nvfp4.json"),
    ("35B FP8 · vLLM", "challenge__qwen36.json"),
    ("122B NVFP4 · vLLM", "challenge__122b.json"),
]

def f(x, n=0):
    return "—" if x is None else f"{x:,.{n}f}".replace(",", " ").replace(".", ",")

def mmm(v, n=0):
    return f"**{f(st.median(v), n)}** | {f(min(v), n)} | {f(max(v), n)}" if v else "— | — | —"

def suite_blokk(cim, fajl):
    p = R / fajl
    if not p.exists():
        return f"### `{cim}` — {fajl}\n\n- ⏳ még nincs adat\n"
    d = json.load(open(p))
    er = d["eredmenyek"]
    futasok = [x for e in er for x in e["futasok"]]
    jok = [x for x in futasok if "hiba" not in x]
    hib = len(futasok) - len(jok)
    it = [x["usage"]["prompt_tokens"] for x in jok if x.get("usage", {}).get("prompt_tokens")]
    ot = [x["usage"]["completion_tokens"] for x in jok if x.get("usage", {}).get("completion_tokens")]
    wall = [x["wall_ms"] for x in jok if x.get("wall_ms")]
    dec = [x["timings"]["predicted_per_second"] for x in jok if (x.get("timings") or {}).get("predicted_per_second")]
    atb = [x["usage"]["completion_tokens"] / (x["wall_ms"] / 1000) for x in jok
           if x.get("usage", {}).get("completion_tokens") and x.get("wall_ms")]
    csonk = sum(1 for x in jok if x.get("finish") == "length")
    ures = sum(1 for x in jok if not (x.get("nyers") or ""))
    jsonok = sum(1 for x in jok if x.get("pred") is not None)
    inst = sum(1 for e in er if e.get("instabil"))
    pont = sum(e["pont"]["pont"] for e in er); mx = sum(e["pont"]["max"] for e in er)
    biro = sum(e["pont"].get("biro_suly") or 0 for e in er)
    ki = [f"### `{cim}` — {fajl}", "",
          f"- **futtatott esetek:** {len(er)} item, {len(jok)} sikeres futás, {hib} hibás",
          "", "| Metrika | Medián | Min | Max |", "|---|---|---|---|",
          f"| Prompt tokenek | {mmm(it)} |", f"| Kimeneti tokenek | {mmm(ot)} |"]
    if dec:
        ki.append(f"| Decode tok/s (motor-mérés, llama.cpp `timings`) | {mmm(dec, 1)} |")
    ki += [f"| Kimeneti tok/s (válaszidőre, TTFT-vel — mindkét motoron azonos képlet) | {mmm(atb, 1)} |",
           f"| Teljes válaszidő (ms) | {mmm(wall)} |", "",
           f"- **JSON-validitás:** {jsonok}/{len(jok)} ({100*jsonok/max(1,len(jok)):.0f} %)",
           f"- **Csonkolt (finish_reason=length):** {csonk}/{len(jok)}" + (f" — ebből ÜRES tartalom: {ures}" if ures else ""),
           f"- **Instabil item (eltérő kimenet azonos greedy kérésre):** {inst}/{len(er)}",
           f"- **Pontszám (többségi kimenet):** **{f(pont, 2)} / {mx:.0f}**"
           + (f" (LLM-bírói {biro:.0f} pont elérhetetlen, elérhető max {mx-biro:.0f})" if biro else ""), ""]
    # tesztenként
    ts = OrderedDict()
    for e in er:
        a = ts.setdefault(e["teszt"], [0.0, 0.0, 0]); a[0] += e["pont"]["pont"]; a[1] += e["pont"]["max"]; a[2] += bool(e.get("instabil"))
    ki += ["| Teszt | Pont | Max | Instabil item |", "|---|---|---|---|"]
    for t, (p_, m_, i_) in sorted(ts.items(), key=lambda z: int(z[0][1:])):
        ki.append(f"| **{t}** | {f(p_, 2)} | {m_:.0f} | {i_ or '—'} |")
    # mezőnként
    mez = OrderedDict()
    for e in er:
        for k, v in (e["pont"].get("reszletek") or {}).items():
            a = mez.setdefault(k, [0, 0, []]); a[1] += 1
            if v.get("arany", 0) >= 1: a[0] += 1
            elif len(a[2]) < 2:
                a[2].append(f"`{e['id']}`: GT `{json.dumps(v.get('gt'), ensure_ascii=False)[:60]}` → `{json.dumps(v.get('pred'), ensure_ascii=False)[:60]}`")
    ki += ["", "| Mező | Egyezés | Eltérések (első 2) |", "|---|---|---|"]
    for k, (ok, n, pl) in sorted(mez.items(), key=lambda z: z[1][0] / z[1][1]):
        ki.append(f"| `{k}` | {ok}/{n} ({100*ok/n:.0f} %) | {'; '.join(pl) or '—'} |")
    ki.append("")
    return "\n".join(ki)

def challenge_blokk():
    ki = ["## HU-CH magyar nyelvértés-challenge (10 tétel × 1 futás, friss kontextus, a szerző protokollja)", "",
          "> Nincs gépi pontszám: a szerző integritási megjegyzése szerint LLM-bíró nélkül, a vak `reports/challenge-pontozolap.md`-n kézzel pontozandó. Itt csak a futás-metrikák.", ""]
    for cim, fajl in CHALLENGE:
        p = R / fajl
        if not p.exists():
            ki.append(f"### `{cim}` — ⏳ nincs adat\n"); continue
        d = json.load(open(p)); er = d["eredmenyek"]
        ot = [e["usage"]["completion_tokens"] for e in er if e.get("usage", {}).get("completion_tokens")]
        wall = [e["wall_ms"] for e in er if e.get("wall_ms")]
        vh = [len(e.get("valasz") or "") for e in er]
        ures = sum(1 for e in er if not (e.get("valasz") or ""))
        csonk = sum(1 for e in er if e.get("finish") == "length")
        ki += [f"### `{cim}` — {fajl}", "", "| Metrika | Medián | Min | Max |", "|---|---|---|---|",
               f"| Kimeneti tokenek | {mmm(ot)} |", f"| Válasz hossza (karakter) | {mmm(vh)} |",
               f"| Teljes válaszidő (ms) | {mmm(wall)} |", "",
               f"- **Csonkolt:** {csonk}/{len(er)} · **Üres válasz:** {ures}/{len(er)}" + (" ⛔" if ures else ""), ""]
        ki += ["| Tétel | finish | ki-token | válasz (első 60 kar.) |", "|---|---|---|---|"]
        for e in er:
            v = (e.get("valasz") or "").replace("\n", " ").replace("|", "¦")
            ki.append(f"| {e['id']} | {e.get('finish')} | {f(e.get('usage', {}).get('completion_tokens'))} | {v[:60] or '⛔ ÜRES'} |")
        ki.append("")
    return "\n".join(ki)

out = ["# Magyar KIE-eval — mérés-részletek (generált)", "",
       f"> Forrás: `magyar-kie-eval/reports/*.json` · generátor `src/reszletek.py` · minden szám számolt. "
       "Mérce: greedy, minden item 3× (hosszú 1×, izoláció 5×), a többségi kimenet pontozva. "
       "A kalibrációs kör (`kalibracio-flash.json`, 76/100) a pontozó-javítás ELŐTTI, nem összevethető — kihagyva. "
       "A hosszú suite-ból a T22 GT-je az iratból visszaparszolt; az LLM-bírói mezők (T1-01 `ertelmezes`, T7-09 `indoklas`) 2 pontja minden modellre elérhetetlen.", ""]
for cim, lista in SUITEK.items():
    out.append(f"## {cim}\n")
    for c, fajl in lista:
        out.append(suite_blokk(c, fajl))
out.append(challenge_blokk())
print("\n".join(out))
