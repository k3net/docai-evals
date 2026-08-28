#!/usr/bin/env python3
"""Futasonkenti pontszam-szoras: a harness a TOBBSEGI kimenetet pontozza, elesben
viszont egyetlen valasz jon. Ez a script minden futast kulon pontoz, es megmondja,
hany itemnel ingadozik a PONT -- ez a valodi kockazat, nem a szoveg-elteres."""
import json, sys, statistics as st
sys.path.insert(0, "src")
from pontozo import pontoz_item

riport, itemsf = sys.argv[1], sys.argv[2]
items = {json.loads(l)["id"]: json.loads(l) for l in open(itemsf) if l.strip()}
d = json.load(open(riport))

sz_pont, sz_szoveg, ossz = 0, 0, 0
print("%-8s %-9s %s" % ("item", "tobbsegi", "futasonkenti pontok"))
for e in d["eredmenyek"]:
    if not e.get("instabil"):
        continue
    ossz += 1
    it = items[e["id"]]
    pk = []
    for f in e["futasok"]:
        try:
            pk.append(round(pontoz_item(it, f.get("pred"))["pont"], 2))
        except Exception:
            pk.append(None)
    kul = len({p for p in pk if p is not None}) > 1 or None in pk
    sz_pont += bool(kul)
    sz_szoveg += not kul
    print("%-8s %-9s %-24s %s" % (
        e["id"], "%.2f/%g" % (e["pont"]["pont"], e["pont"]["max"]), pk,
        "<< PONT IS INGADOZIK" if kul else "(csak a szoveg ter el)"))

print()
print("instabil item: %d" % ossz)
print("  ebbol a PONT is ingadozik: %d  <-- ez a valodi kockazat" % sz_pont)
print("  csak a szoveg ter el:      %d" % sz_szoveg)
