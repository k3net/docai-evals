"""08 — a lánc utáni kiolvasások pontozása a karok megbízhatósági pontszámaival, és a 08-as fejek tanítása
(G1-rögzítés 2., 3., 5.3, 11.).

`tanit`: családonként, a 07 F3R receptjével (a 07 B1-4R0 előtanított fejéből, a 07 tanulási rátájával, 3 seed, öt fold a
sabloncsoport szerint, foldonként belső 20%-os korai megállás; `b1rel07.finomhangol` útja súlyozással):
  L-R      a láncos T500-on (orákulum-út: a fej a lánc kimenetének formáját látja, kinyerési zaj nélkül, mint a tanítómintán)
  L-RN     a láncos T500 és az értelmezési tanítóminta együtt, **forrásonként 50–50% össz-súllyal** (5.3): a T500 példasúlya
           (N_T + N_É) / (2 N_T), az értelmezési mintáé (N_T + N_É) / (2 N_É), N a ténylegesen tanítható döntések száma
           (a modellhez jutott, nem kétértelmű tétel); a súly a tanítási és a korai megállás validációs BCE-jében is
  L-LR     L2-logisztikus: a 07 B1-4LR 10 jellemzője + a lánc két jellemzője (log(megmaradt + 1), log(kizárt + 1)); a C a
           07 rácsán sablonos ötszörös CV-vel; a T500-on
  L-LRN    mint az L-LR, az L-RN példáin és súlyaival
A neurális fejek architektúrája a 07-é (a lánc a bemeneten át hat: a blokk és a megmaradt opciók; a `log k` a megmaradtaké).
Súlyok nélkül (L-R) a ciklus a 05 `train_rel`-é.

`pontoz`: egy lánc utáni szelet (a `kiolvas08` kimenete, `<forrás>_<család>_<szelet>`) négyállapotú döntései (B1-4S,
`b1rel07.decide4` a 07 B1-4 temperature-jével; a döntés minden láncos karnál ugyanaz, a karok csak a megbízhatóságban
térnek el) és a karok pontszámai:
  L-S      az alany saját pontszáma: a választott válasz átlagolt valószínűsége (q)
  L-R07    a 07 B1-4R befagyasztva (`cache/k07/fejek`), seedenként az öt fold logitjának átlaga (`b1rel07.fold_atlag`)
  L-R, L-RN, L-LR, L-LRN   a 08-as fejtanító kimenetéből (`--fejek08`; a G3-ban; a tanító még nincs meg)
A pontszám iránya: **nagyobb = megbízhatóbb** (a hibapontszám a negáltja, `g5_k1_08`). Az L-S pontszáma valószínűség, a
fejeké logit; a kalibrációt (temperature a friss CAL-on) az elemzők végzik. A kimenet a 07 `pontoz` alakjában
(`keret4`: ids, dontes, pontszam; a seedes karok `<kar>|<seed>` kulccsal), hogy a 08 elemzői ugyanazt a formát olvassák.
A kétértelmű itemek kimaradnak (`set4`); az üres listás tétel (a lánc minden jelöltet kizárt) is pontozható.
  python3 kor08/eszkozok/b1rel08.py pontoz --szelet oERT2J_szabaly.koltsegelszamolas_ERT2J --out cache/k08/pontoz/G1
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE), str(EXP / "kor07/eszkozok")]
import b1rel07 as R7  # noqa: E402

CSALADOK = R7.CSALADOK
SEEDS = R7.SEEDS
VALOSZINUSEG = {"L-S": True, "L-R07": False, "L-R": False, "L-RN": False, "L-LR": False, "L-LRN": False, "B1-4S": True,
                "B1-4R": False}
LANC_NELKUL = {"L-S": "B1-4S", "L-R07": "B1-4R"}  # a lánc nélküli bemeneten a 07 karjai a saját nevükön


def csalad_of(prefix: str) -> str:
    fam = [c for c in CSALADOK if f"_{c}_" in prefix]
    if len(fam) != 1:
        raise SystemExit(f"a szelet nevéből nem derül ki a család: {prefix}")
    return fam[0]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# --- a példák: a 07 `to_example4` / `rel_example4` / `set4`, az üres listával (a lánc minden jelöltet kizárt) ----------
# A 07 útja k = 0-nál elhasal (`reshape(0, -1)`, `log(0)`); k ≥ 1-nél a kimenet bitre a 07-é (ugyanazok a függvények).
# k = 0-nál a jelölt-sorok üresek, és a kis jellemzők `log k` tagja log(max(k, 1)) = 0 (mint k = 1-nél): az üres listát
# a fej a rejtett állapotokból és a döntés típusából látja (a döntés ott csak X, Y vagy Z lehet).

def to_example4(e: dict) -> dict:
    r, f = e["row"], e["feat"]
    labs, order = r["labels"], r["order"]
    if len(labs) - 3 > 0:
        return R7.to_example4(e)
    if labs != ["X", R7.K7.Y_LABEL, R7.K7.Z_LABEL] or order != [None, R7.K7.Y_ID, R7.K7.Z_ID]:
        raise SystemExit(f"{r['id']}: nem négyállapotú sorrend ({labs})")
    cf, gf = R7.fej05.c_features(r)
    he, hm = f["h_opt_end"], f["h_opt_mean"]
    if len(cf) != 2 or he.shape[1] != 3:
        raise SystemExit(f"{r['id']}: span- vagy jellemzőszám eltér (k=0, cf={len(cf)}, span={he.shape[1]})")
    d = he.shape[0] * he.shape[2]
    return {"id": r["id"], "k": 0, "cand_ids": [], "ketertelmu": bool(r["ketertelmu"]),
            "cf": R7.torch.tensor(cf), "gf": R7.torch.tensor(gf), "q": f["h_last"].reshape(-1),
            "c_end": he.new_zeros((0, d)), "c_mean": hm.new_zeros((0, d)),
            "s_end": {None: he[:, 0].reshape(-1), R7.K7.Y_ID: he[:, 1].reshape(-1), R7.K7.Z_ID: he[:, 2].reshape(-1)},
            "s_mean": {None: hm[:, 0].reshape(-1), R7.K7.Y_ID: hm[:, 1].reshape(-1), R7.K7.Z_ID: hm[:, 2].reshape(-1)}}


def rel_example4(e: dict, d: dict, st) -> dict:
    if e["k"] > 0:
        return R7.rel_example4(e, d, st)
    if d["kind"] == "SELECT" or d["k"] != 0:
        raise SystemExit(f"{e['id']}: üres listán SELECT vagy eltérő opciószám")
    key = d["cand"]
    cf = st.z("cf", e["cf"])
    cfj = R7.torch.zeros(cf.shape[1]) if key is None else cf[0 if key == R7.K7.Y_ID else 1]
    x, y, z = d["x"], d["y"], d["z"]
    small = [1.0, d["q"], d["top2"], d["gap"], x, d["ent"], d["agree"], 1 - x, 0.0,
             y, z, max(0.0, 1 - x - y - z), float(d["kind"] == "NONE"), float(d["kind"] == "MISSING"), float(d["kind"] == "OOS")]
    return {"small": R7.torch.tensor(small), "cf": cfj, "gf": st.z("gf", e["gf"]), "q": st.z("h", e["q"]),
            "c": st.z("h", e["s_end"][key]), "cm": st.z("h", e["s_mean"][key]), "y": float(bool(d["helyes"]))}


def set4(prefix: str, temp: float, st, root: Path) -> tuple[list[str], list[dict], dict]:
    """A `b1rel07.set4` az üres listával: (id-k, példák, döntések), a kétértelmű itemek nélkül."""
    by = R7.rows4(prefix, root)
    ids, rs, info = [], [], {}
    for e in (to_example4(x) for x in R7.fej05.load_dir(root / f"{prefix}__kanonikus")):
        if e["ketertelmu"] or e["id"] not in by:
            continue
        d = R7.decide4(by[e["id"]], temp)
        ids.append(e["id"])
        info[e["id"]] = d
        rs.append(rel_example4(e, d, st))
    return ids, rs, info


# --- tanítás --------------------------------------------------------------------------------------------------------

LANC_JELLEMZOK = ("log_megmaradt", "log_kizart")
LR8_JELLEMZOK = R7.LR4_JELLEMZOK + LANC_JELLEMZOK


def h(tag: str, g: str) -> int:
    """A fold-hash a sabloncsoporton (D23): egy sabloncsoport (és így egy egység minden változata) egy foldban."""
    return int(hashlib.sha256(f"{R7.M5.TMETA_SEED}|{tag}|{g}".encode()).hexdigest(), 16)


def lanc_jellemzok(lanc: dict, i: str) -> list[float]:
    r = lanc[i]
    return [R7.math.log(len(r["megmaradt"]) + 1), R7.math.log(len(r["kizart"]) + 1)]


def train_rel_w(fit: list[dict], val: list[dict], w_fit: list[float] | None, w_val: list[float] | None, ms, dims: dict,
                lr: float, seed: int, init):
    """A 05 `train_rel` (AdamW, 64-es köteg, 20 epoch, 3 epoch türelem, gradiens-vágás 1,0) példasúllyal; súly nélkül a
    05-é lépésről lépésre."""
    torch, nn, M5 = R7.torch, R7.nn, R7.M5
    if w_fit is None:
        return M5.train_rel("B1", fit, val, ms, dims, lr, seed, "cpu", init=init)
    torch.manual_seed(seed)
    model = init
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    g = torch.Generator().manual_seed(seed)
    wf, wv = torch.tensor(w_fit, dtype=torch.float32), torch.tensor(w_val, dtype=torch.float32)

    @torch.no_grad()
    def val_bce() -> tuple[float, list[float]]:
        model.eval()
        lg = []
        for i in range(0, len(val), 256):
            lg += model(M5.batch(val[i:i + 256], ms, "cpu")).cpu().tolist()
        y = torch.tensor([r["y"] for r in val])
        return float(nn.functional.binary_cross_entropy_with_logits(torch.tensor(lg), y, weight=wv)), lg
    best, best_state, bad, hist = R7.math.inf, None, 0, []
    for epoch in range(20):
        model.train()
        perm = torch.randperm(len(fit), generator=g).tolist()
        tot = 0.0
        for i in range(0, len(perm), 64):
            idx = perm[i:i + 64]
            b = M5.batch([fit[j] for j in idx], ms, "cpu")
            loss = nn.functional.binary_cross_entropy_with_logits(model(b), b["y"], weight=wf[idx])
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            tot += loss.item() * len(idx)
        v, lg = val_bce()
        hist.append({"epoch": epoch + 1, "train_bce": tot / len(fit), "val_bce": v, "val_auroc": M5.auroc(lg, [r["y"] for r in val])})
        if v < best - 1e-6:
            best, bad = v, 0
            best_state = {k: t.detach().cpu().clone() for k, t in model.state_dict().items()}
        else:
            bad += 1
            if bad >= 3:
                break
    model.load_state_dict(best_state)
    return model, {"lr": lr, "seed": seed, "legjobb_val_bce": best, "tortenet": hist}


def finomhangol_w(rs: list[dict], groups: list[str], w: list[float] | None, load, lr: float, seed: int):
    """A `b1rel07.finomhangol` (öt fold a sabloncsoport szerint, foldonként belső 20%-os megállás), súllyal."""
    fold = [h("fold", g) % 5 for g in groups]
    models, epochs = [], []
    for f in range(5):
        tr = [n for n, x in enumerate(fold) if x != f]
        iv = [n for n in tr if h("belso", groups[n]) % 5 == 0]
        it = [n for n in tr if h("belso", groups[n]) % 5 != 0]
        if not iv or not it:
            raise SystemExit("üres fold a finomhangolásban")
        model, ms, dims = load()
        model, inf = train_rel_w([rs[n] for n in it], [rs[n] for n in iv], None if w is None else [w[n] for n in it],
                                 None if w is None else [w[n] for n in iv], ms, dims, lr, seed * 10 + f, model)
        models.append((model, ms, dims))
        epochs.append(len(inf["tortenet"]))
    return models, epochs


def lr_illesztes_w(X, y, groups: list[str], w, nevek: tuple[str, ...]) -> dict:
    """A `b1rel07.lr_illesztes` (C a 07 rácsán, sablonos ötszörös CV, végül a teljes mintán) példasúllyal; a CV
    veszteség is súlyozott."""
    np = R7.np
    from sklearn.linear_model import LogisticRegression  # noqa: PLC0415
    from sklearn.preprocessing import StandardScaler  # noqa: PLC0415
    if len(set(y.tolist())) < 2:
        return {"C": None, "megjegyzes": "egyosztályú minta", "jellemzok": list(nevek), "n": int(len(y))}
    fold = np.array([h("lr-fold", g) % 5 for g in groups])
    best, best_c = R7.math.inf, None
    for c in R7.B.C_RACS:
        ll = 0.0
        for f in range(5):
            tr, va = fold != f, fold == f
            if len(set(y[tr].tolist())) < 2 or not va.any():
                continue
            sc = StandardScaler().fit(X[tr])
            m = LogisticRegression(C=c, max_iter=2000).fit(sc.transform(X[tr]), y[tr], sample_weight=w[tr])
            p = np.clip(m.predict_proba(sc.transform(X[va]))[:, 1], 1e-6, 1 - 1e-6)
            ll -= float(np.sum(w[va] * (y[va] * np.log(p) + (1 - y[va]) * np.log(1 - p))))
        if ll < best:
            best, best_c = ll, c
    sc = StandardScaler().fit(X)
    m = LogisticRegression(C=best_c, max_iter=2000).fit(sc.transform(X), y, sample_weight=w)
    return {"C": best_c, "jellemzok": list(nevek), "n": int(len(y)), "pozitiv_arany": float(y.mean()),
            "standardizalas": {"mean": sc.mean_.tolist(), "scale": sc.scale_.tolist()},
            "egyutthatok": m.coef_[0].tolist(), "konstans": float(m.intercept_[0])}


def tanito(prefix: str, lanc_dir: Path, fam: str, temp: float, st, jell: Path) -> dict:
    """Egy tanítóforrás: példák, döntések, sabloncsoportok és a lánc jellemzői, itemsorrendben."""
    ids, rs, info = set4(prefix, temp, st, jell)
    items = {r["id"]: r for r in map(json.loads, (lanc_dir / "items" / f"{fam}.jsonl").read_text(encoding="utf-8").splitlines()) if r}
    lanc = {r["id"]: r for r in map(json.loads, (lanc_dir / f"lanc_{fam}.jsonl").read_text(encoding="utf-8").splitlines()) if r}
    return {"ids": ids, "rs": rs, "info": info, "groups": [items[i]["template_group_id"] for i in ids],
            "X": R7.np.array([R7.lr4_features(info[i]) + lanc_jellemzok(lanc, i) for i in ids])}


def tanit(a) -> None:
    np = R7.np
    fejek07, out = EXP / a.fejek07, EXP / a.out
    temps = json.loads((fejek07 / "temperature.json").read_text())
    lr = json.loads((fejek07 / "elotanit4.json").read_text())["lr_valasztott"]
    st = R7.fej05.Stats.from_state(json.loads((R7.FEJ_H / "fej.json").read_text())["stats"])
    karok = a.karok.split(",")
    res = {"keszult": time.strftime("%Y-%m-%dT%H:%M:%S"), "lr": lr, "temperature_dontes": temps["B1-4"], "karok": karok,
           "csaladok": {}, "fajlok": {}}
    for fam in a.csalad or CSALADOK:
        t0 = time.time()
        T = tanito(a.t500.format(csalad=fam), EXP / a.t500_lanc, fam, temps["B1-4"], st, EXP / a.jell)
        E = tanito(a.ert.format(csalad=fam), EXP / a.ert_lanc.format(csalad=fam), fam, temps["B1-4"], st,
                   EXP / (a.ert_jell or a.jell)) \
            if a.ert else None
        nT, nE = len(T["rs"]), len(E["rs"]) if E else 0
        R = {"N_T500": nT, "N_ert": nE, "helyes_T500": float(np.mean([T["info"][i]["helyes"] for i in T["ids"]])),
             "helyes_ert": float(np.mean([E["info"][i]["helyes"] for i in E["ids"]])) if E else None, "karok": {}}
        if E:
            wT, wE = (nT + nE) / (2 * nT), (nT + nE) / (2 * nE)
            R["suly"] = {"T500": wT, "ert": wE}
            rsN, gN, wN = T["rs"] + E["rs"], T["groups"] + E["groups"], [wT] * nT + [wE] * nE
            XN = np.vstack([T["X"], E["X"]])
            if set(T["groups"]) & set(E["groups"]):
                raise SystemExit(f"{fam}: a T500 és az értelmezési tanítóminta sabloncsoportjai átfednek")
        for kar in karok:
            if kar in ("L-RN", "L-LRN") and not E:
                continue
            if kar in ("L-R", "L-RN"):
                rs, g, w = (T["rs"], T["groups"], None) if kar == "L-R" else (rsN, gN, wN)
                R["karok"][kar] = {}
                for s in SEEDS:
                    models, epochs = finomhangol_w(rs, g, w, R7.load_b14(fejek07 / f"B1-4R0_s{s}.pt"), lr, s)
                    for f, (m, ms, dims) in enumerate(models):
                        pth = out / fam / f"{kar}_s{s}_f{f}.pt"
                        R7.mentes(pth, m, ms, dims, kar=kar, csalad=fam, seed=s, fold=f, lr=lr, temperature=temps["B1-4"],
                                  sulyozott=w is not None)
                        res["fajlok"][str(pth.relative_to(EXP))] = sha(pth)
                    R["karok"][kar][s] = {"epoch": epochs}
                    print(f"{fam}: {kar} s{s} kész (epoch {epochs})", flush=True)
            else:
                X, y, g, w = ((T["X"], np.array([float(bool(T["info"][i]["helyes"])) for i in T["ids"]]), T["groups"], np.ones(nT))
                              if kar == "L-LR" else
                              (XN, np.array([float(bool(x["info"][i]["helyes"])) for x in (T, E) for i in x["ids"]]), gN, np.array(wN)))
                ill = lr_illesztes_w(X, y, g, w, LR8_JELLEMZOK)
                pth = out / fam / f"{kar}.json"
                pth.parent.mkdir(parents=True, exist_ok=True)
                pth.write_text(json.dumps({"kar": kar, "csalad": fam, "temperature": temps["B1-4"], **ill}) + "\n", encoding="utf-8")
                res["fajlok"][str(pth.relative_to(EXP))] = sha(pth)
                R["karok"][kar] = {"C": ill.get("C")}
                print(f"{fam}: {kar} kész (C {ill.get('C')})", flush=True)
        R["ido_s"] = round(time.time() - t0)
        res["csaladok"][fam] = R
    out.mkdir(parents=True, exist_ok=True)
    (out / "fejek08.json").write_text(json.dumps({**res, "t500": a.t500, "t500_lanc": a.t500_lanc, "ert": a.ert,
                                                  "ert_lanc": a.ert_lanc}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({f: {k: v for k, v in R.items() if k != "karok"} for f, R in res["csaladok"].items()}, ensure_ascii=False, indent=1))


# --- pontozás ------------------------------------------------------------------------------------------------------------

def pontoz(a) -> None:
    fejek07 = EXP / a.fejek07
    temps = json.loads((fejek07 / "temperature.json").read_text())
    st = R7.fej05.Stats.from_state(json.loads((R7.FEJ_H / "fej.json").read_text())["stats"])
    fam = csalad_of(a.szelet)
    ids, rs, info = set4(a.szelet, temps["B1-4"], st, EXP / a.jell)
    p = {"L-S": [info[i]["q"] for i in ids]}
    fajlok = {}
    for s in SEEDS:
        paths = [fejek07 / fam / f"B1-4R_s{s}_f{f}.pt" for f in range(5)]
        p[f"L-R07|{s}"] = R7.fold_atlag(R7.load_b14, paths, rs)
        fajlok.update({str(x.relative_to(EXP)): sha(x) for x in paths})
    if a.fejek08:
        f8 = EXP / a.fejek08
        for kar in ("L-R", "L-RN"):
            for s in SEEDS:
                paths = [f8 / fam / f"{kar}_s{s}_f{f}.pt" for f in range(5)]
                if all(x.exists() for x in paths):
                    p[f"{kar}|{s}"] = R7.fold_atlag(R7.load_b14, paths, rs)
                    fajlok.update({str(x.relative_to(EXP)): sha(x) for x in paths})
        if not a.lanc:
            raise SystemExit("a logisztikus 08-as karokhoz kell a lánc könyvtára (--lanc)")
        lanc = {r["id"]: r for r in map(json.loads, (EXP / a.lanc / f"lanc_{fam}.jsonl").read_text(encoding="utf-8").splitlines()) if r}
        X = R7.np.array([R7.lr4_features(info[i]) + lanc_jellemzok(lanc, i) for i in ids])
        for kar in ("L-LR", "L-LRN"):
            pth = f8 / fam / f"{kar}.json"
            if pth.exists():
                p[kar] = R7.lr_pontszam(json.loads(pth.read_text()), X).tolist()
                fajlok[str(pth.relative_to(EXP))] = sha(pth)
    if a.lanc_nelkul:
        if a.fejek08:
            raise SystemExit("a lánc nélküli bemeneten csak a 07 karjai (B1-4S, B1-4R) pontozandók")
        p = {LANC_NELKUL[k.split("|")[0]] + k[len(k.split("|")[0]):]: v for k, v in p.items()}
    out = {"szelet": a.szelet, "csalad": fam, "jell": a.jell, "keszult": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "temperature_dontes": temps["B1-4"], "irany": "nagyobb = megbízhatóbb", "valoszinuseg": VALOSZINUSEG,
           "fejek": fajlok, "keret4": {"ids": ids, "dontes": {i: info[i] for i in ids}, "pontszam": p}}
    o = EXP / a.out
    o.mkdir(parents=True, exist_ok=True)
    (o / f"{a.szelet}.json").write_text(json.dumps(out) + "\n", encoding="utf-8")
    print(f"{a.szelet}: {len(ids)} item, karok {sorted(p)} → {(o / (a.szelet + '.json')).relative_to(EXP)}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pontoz")
    p.add_argument("--szelet", required=True, help="a kiolvasás előtagja, pl. oERT2J_szabaly.koltsegelszamolas_ERT2J")
    p.add_argument("--jell", default="cache/k08/jellemzok")
    p.add_argument("--fejek07", default="cache/k07/fejek")
    p.add_argument("--fejek08", help="a `tanit` kimenete (L-R, L-RN, L-LR, L-LRN)")
    p.add_argument("--lanc", help="a szelet láncának könyvtára (a logisztikus karok lánc-jellemzőihez)")
    p.add_argument("--lanc-nelkul", action="store_true", help="az eredeti item (lánc nélkül): a karok B1-4S és B1-4R néven")
    p.add_argument("--out", required=True)
    p.add_argument("--szalak", type=int)
    t = sub.add_parser("tanit")
    t.add_argument("--t500", default="o06_{csalad}_T500", help="a láncos T500 kiolvasásának előtagja")
    t.add_argument("--t500-lanc", default="kor08/adat/G1/orakulum_06")
    t.add_argument("--ert", help="az értelmezési tanítóminta kiolvasásának előtagja, `{csalad}` helyőrzővel")
    t.add_argument("--ert-lanc", help="az értelmezési tanítóminta láncának könyvtára, `{csalad}` helyőrzővel")
    t.add_argument("--ert-jell", help="az értelmezési tanítóminta kiolvasásának gyökere (alapból a --jell)")
    t.add_argument("--karok", default="L-R,L-RN,L-LR,L-LRN")
    t.add_argument("--csalad", action="append", choices=CSALADOK)
    t.add_argument("--jell", default="cache/k08/jellemzok")
    t.add_argument("--fejek07", default="cache/k07/fejek")
    t.add_argument("--out", required=True)
    t.add_argument("--szalak", type=int)
    a = ap.parse_args()
    if a.szalak:
        R7.torch.set_num_threads(a.szalak)
    {"pontoz": pontoz, "tanit": tanit}[a.cmd](a)


if __name__ == "__main__":
    main()
