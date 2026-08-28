#!/usr/bin/env python3
"""Riport a harness futásaiból — a terv §7 táblázatai. Minden szám SZÁMOLT."""
import json, sys, statistics as st
from pathlib import Path

def betolt(p):
    d = json.load(open(p))
    return d["cimke"], d["eredmenyek"]

def tesztsor(er):
    ki = {}
    for e in er:
        a = ki.setdefault(e["teszt"], [0.0, 0.0])
        a[0] += e["pont"]["pont"]; a[1] += e["pont"]["max"]
    return ki

def mellek(er):
    n = len(er)
    formhiba = sum(1 for e in er if e["formatum_hiba"])
    instabil = sum(1 for e in er if e["instabil"])
    jsonhiba = sum(1 for e in er if e["pont"].get("json_hiba"))
    dec, wall, itok, otok, csonk, atbocs = [], [], [], [], 0, []
    for e in er:
        for f in e["futasok"]:
            if "hiba" in f: continue
            t = f.get("timings") or {}
            if t.get("predicted_per_second"): dec.append(t["predicted_per_second"])
            wall.append(f["wall_ms"])
            u = f.get("usage") or {}
            if u.get("prompt_tokens"): itok.append(u["prompt_tokens"])
            if u.get("completion_tokens"):
                otok.append(u["completion_tokens"])
                # ⛔ a vLLM nem ad `timings`-et, a llama.cpp igen — ez a sor MINDKÉT
                # motoron azonos módon számol (TTFT-t is tartalmaz), tehát összevethető
                if f.get("wall_ms"):
                    atbocs.append(u["completion_tokens"] / (f["wall_ms"] / 1000))
            if f.get("finish") == "length": csonk += 1
    return dict(n=n, formhiba=formhiba, instabil=instabil, jsonhiba=jsonhiba, csonkolt=csonk,
                decode=st.median(dec) if dec else None,
                wall=st.median(wall) if wall else None,
                itok=st.median(itok) if itok else None,
                otok=st.median(otok) if otok else None,
                atbocs=st.median(atbocs) if atbocs else None)

def fmt(x, n=1):
    return "—" if x is None else f"{x:,.{n}f}".replace(",", " ").replace(".", ",")

if __name__ == "__main__":
    futasok = [betolt(p) for p in sys.argv[1:]]
    tesztek = sorted({t for _, er in futasok for t in tesztsor(er)}, key=lambda z: int(z[1:]))
    print("## Fő táblázat — tesztenkénti pontszám\n")
    print("| Teszt | " + " | ".join(c for c, _ in futasok) + " | Max |")
    print("|---|" + "---|" * (len(futasok) + 1))
    for t in tesztek:
        sorok = []
        maxp = 0
        for _, er in futasok:
            ts = tesztsor(er)
            p, m = ts.get(t, (0.0, 0.0))
            sorok.append(f"{fmt(p, 2)}"); maxp = max(maxp, m)
        print(f"| **{t}** | " + " | ".join(sorok) + f" | {maxp:.0f} |")
    print("| **ÖSSZESEN** | " + " | ".join(
        f"**{fmt(sum(e['pont']['pont'] for e in er), 2)}**" for _, er in futasok) +
        f" | **{sum(e['pont']['max'] for e in futasok[0][1]):.0f}** |")
    biro = sum(e["pont"].get("biro_suly", 0) or 0 for _, er in futasok for e in er) / max(len(futasok), 1)
    if biro:
        print(f"\n> ⛔ Az LLM-bírói réteg nincs implementálva: **{biro:.0f} pont elérhetetlen** "
              f"(T1-01 `ertelmezes`, T7-09 `indoklas`) — mindkét modellre azonosan. "
              f"Az elérhető maximum {sum(e['pont']['max'] for e in futasok[0][1]) - biro:.0f} pont.")
    print("\n## Mellékmetrikák\n")
    print("| Metrika | " + " | ".join(c for c, _ in futasok) + " |")
    print("|---|" + "---|" * len(futasok))
    ms = [mellek(er) for _, er in futasok]
    for cim, kulcs, n in (("Formátumsértés (item)", "formhiba", 0), ("JSON-hiba (item)", "jsonhiba", 0),
                          ("Instabil (item)", "instabil", 0), ("Csonkolt válasz (futás)", "csonkolt", 0),
                          ("Decode tok/s (motor-mérés)", "decode", 1),
                          ("Kimeneti tok/s (válaszidőre)", "atbocs", 1), ("Válaszidő ms (medián)", "wall", 0),
                          ("Prompt token (medián)", "itok", 0), ("Kimeneti token (medián)", "otok", 0)):
        print(f"| {cim} | " + " | ".join(fmt(m[kulcs], n) for m in ms) + " |")
