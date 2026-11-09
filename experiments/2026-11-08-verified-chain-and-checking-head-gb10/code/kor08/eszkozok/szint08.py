"""08 G2 — a friss adat generátora (G1-rögzítés 5.): a `szint06`, a `szint07`, a `szint07k3` és a `szint08e` burkolója
(egyik sem módosul). **A G2 csak a rögzítés (D12) után fut; a GPU-s lépés (Muse) Dani jóváhagyásával.**

Sablonok: családonként egy friss készlet, sablon-id `<család>:k08:<nyelv>:<n>` (a 06 / 07 id-itől eltér); a sablonok a
hash-rang szerint diszjunkt készletekbe kerülnek (`KESZLET`): CAL, TESZT (természetes összetétel, a 07 kvótáival), K3
(a K3-típus), ERT-T (az értelmezési teszt) és ERT-N (az értelmezési tanítóminta). A bank- és a szabálysablon kódból,
a hibaelhárítás okkatalógusa a Muse-tól (a `szint06.cmd_sablon`).

Részek (`--resz`), kimenet `kor08/adat/G2/<rész>/{terv,raw,items}/<család>.jsonl`:
  friss       CAL 500 + TESZT 1000 családonként (a 07 `quotas07`-je: MATCH 60 / NO_MATCH 20 / MISSING_DATA 10 /
              OUT_OF_SCOPE 10%, fele magyar), item-id `<család>:<CAL|TESZT>:<nyelv>:<állapot>:k08-<n>`
  k3          a K3-típus négy változata (`szint07k3.plan3`): bank B3a részfizetés, hiba H3 mértékegység-váltás,
              szabály S3a nettó / bruttó és S3b deviza; változatonként 100 terv, nyelvenként fele
  ert_teszt   az értelmezési teszt: egységenként 1 (a) + 3 (b) (5.3). Bank és hiba: ERT-T sablononként 2 egység
              (33 sablon); szabály: a `forgatokonyv08_szab` 40 teszt-forgatókönyve, forgatókönyvenként és nyelvenként
              7 egység az ERT-T sablonjain (ahol a gold és a csali költségneme is szabálypont)
  ert_tanito  az értelmezési tanítóminta: bank ERT-N sablononként 5, hiba 3 egység; szabály: az 50 tanító-forgatókönyv,
              nyelvenként 5 egység
Az egység (b) változatai ugyanannak a tervnek három átfogalmazása (a 2. és a 3. más formában, `dim`), az (a) ugyanaz a
terv a jel nélkül (gold Y). A `meta.ertelmezes`: `egyseg` (= `par`), `alt`, `valtozat` (1–3; az (a)-nál 0), `szelet`
(teszt / tanito), a szabálycsaládon `forgatokonyv`. A klaszter (`template_group_id`): bankon és hibán a sablon, a
szabálycsaládon a forgatókönyv (mindkét nyelven). A darabszám a terv száma: ami a tényellenőrzőn elbukik, kimarad, egy
egység csak teljesen marad meg (a `final`), utánpótlás nincs. **A banki kérdés a feladatszabállyal** (`lanc08.bank_kerdes`).

  sablon --csalad F [--url U --model M]          (a hibánál GPU: Muse)
  terv   --csalad F --resz R                     (CPU)
  minta  --resz R [--n 2]                        mintapromptok → kor08/adat/G2/<rész>/minta_promptok.md (CPU)
  gen    --csalad F --resz R --url U --model M   (GPU: Muse)
  final  --csalad F --resz R
  `--gyoker <könyvtár>`: a kimenet gyökere (a kódpróba a scratch alá ír, nem a G2 alá)
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE), str(EXP / "kor07/eszkozok"), str(EXP / "kor06/eszkozok")]
import forgatokonyv08_szab as FK  # noqa: E402
import lanc08 as L  # noqa: E402
import szint06 as S  # noqa: E402
import szint07 as S7  # noqa: E402
import szint07k3 as K3  # noqa: E402
import szint08e as E  # noqa: E402

BANK, HIBA, SZAB = E.BANK, E.HIBA, E.SZAB
CSALADOK = E.CSALADOK
GYOKER = {"d": EXP / "kor08/adat/G2"}
RESZEK = ("friss", "k3", "ert_teszt", "ert_tanito")
KESZLETEK = ("CAL", "TESZT", "K3", "ERT-T", "ERT-N")
ERT_N = {"hu": 17, "en": 16}
KESZLET = {  # család → készlet → nyelv → sablonszám
    BANK: {"K3": {"hu": 15, "en": 15}, "ERT-T": ERT_N, "ERT-N": ERT_N},
    HIBA: {"K3": {"hu": 15, "en": 15}, "ERT-T": ERT_N, "ERT-N": {"hu": 15, "en": 15}},
    SZAB: {"K3": {"hu": 15, "en": 15}, "ERT-T": {"hu": 40, "en": 40}, "ERT-N": {"hu": 40, "en": 40}},
}
for _f in CSALADOK:
    KESZLET[_f] = {sz: {lang: S.K["sablon_per_nyelv"][sz] for lang in S.LANGS} for sz in ("CAL", "TESZT")} | KESZLET[_f]
EGYSEG = {"ert_teszt": {BANK: 2, HIBA: 2, SZAB: 7}, "ert_tanito": {BANK: 5, HIBA: 3, SZAB: 5}}  # sablononként / forgatókönyvenként
ERT_SZELET = {"ert_teszt": ("G2T", "teszt", "ERT-T"), "ert_tanito": ("G2N", "tanito", "ERT-N")}
K3_VALTOZAT = {BANK: ("B3a-reszfizetes",), HIBA: ("H3-valtas",), SZAB: ("S3a-netto", "S3b-deviza")}
K3_N = 100  # változatonként
K3_VALTOZAT_PAR = {BANK: {"B3a-reszfizetes": 0}, HIBA: {"H3-valtas": 0}, SZAB: {"S3a-netto": 0, "S3b-deviza": 1}}  # a plan3 sorszám-paritása


def path(kind: str, fam: str, _proba: bool = False, resz: str | None = None) -> Path:
    if kind == "sablon":
        return GYOKER["d"] / "sablon" / f"{fam}.jsonl"
    return GYOKER["d"] / (resz or RESZ["r"]) / kind / f"{fam}.jsonl"


RESZ = {"r": "friss"}


def sablon_ids08(fam: str, _proba: bool = False) -> list[tuple[str, str, str]]:
    """(sablon-id, nyelv, készlet): nyelvenként a hash-rang szerint, készletenként pontos darabszámmal."""
    out = []
    for lang in S.LANGS:
        n = [KESZLET[fam][k][lang] for k in KESZLETEK]
        ids = sorted((f"{fam}:k08:{lang}:{i:03d}" for i in range(sum(n))), key=lambda t: S.h(f"{S.SEED}:k08:keszlet:{t}"))
        k = 0
        for sz, m in zip(KESZLETEK, n):
            out += [(t, lang, sz) for t in ids[k:k + m]]
            k += m
    return out


def sablonok(fam: str, keszlet: str, lang: str) -> list[dict]:
    return sorted((s for s in S.jl_read(path("sablon", fam)) if s["szelet"] == keszlet and s["lang"] == lang),
                  key=lambda s: s["sablon_id"])


def telepit() -> None:
    """A `szint06` útjai a G2 alá (a `szint07.friss` mintájára)."""
    S.path = path
    S.sablon_ids = sablon_ids08
    S.quotas = S7.quotas07
    S.SPLITS = S7.SPLITS07


# --- tervek ------------------------------------------------------------------------------------------------------------

def terv_friss(fam: str) -> list[dict]:
    """A `szint07.cmd_friss_terv` a G2 sablonjain, k08-as id-kkal."""
    by = defaultdict(list)
    for s in S.jl_read(path("sablon", fam)):
        by[(s["szelet"], s["lang"])].append(s)
    rows = []
    for (sz, lang, st), n in S7.quotas07().items():
        pool = sorted(by[(sz, lang)], key=lambda s: S.h(f"{S.SEED}:kiosztas:{s['sablon_id']}:{st}"))
        if not pool:
            raise SystemExit(f"{fam}: nincs sablon a(z) {sz}/{lang} cellához")
        for i in range(n):
            sab = pool[i % len(pool)]
            gid = f"{fam}:{sz}:{lang}:{st}:k08-{i:04d}"
            rows.append(S.plan_case(fam, sab, st, i) | {"group_id": gid, "sorrend": S.h(f"{S.SEED}:sorrend08:{gid}") % 10**12})
    return rows


def terv_k3(fam: str) -> list[dict]:
    """A `szint07k3.plan3` a K3 készlet sablonjain: változatonként és nyelvenként K3_N / 2 terv, a sablonokon körbe
    járva (a változatot a sorszám párossága adja; a kimaradó terv a tervezéskor pótlódik, generálás előtt)."""
    rows = []
    for lang in S.LANGS:
        sabs = sablonok(fam, "K3", lang)
        for v in K3_VALTOZAT[fam]:
            n, j, i = 0, 0, 0
            while n < K3_N // 2:
                if j > 400 * len(sabs):
                    raise SystemExit(f"{fam} {lang} {v}: nem jön ki {K3_N // 2} terv")
                sab, seq = sabs[j % len(sabs)], j // len(sabs) * 2 + K3_VALTOZAT_PAR[fam][v]
                j += 1
                p = K3.plan3(fam, sab, seq)
                if p.get("kimarad") or p["nehez"]["valt"] != v:
                    continue
                gid = f"{fam}:G2K3:{lang}:MATCH:{K3_VALTOZAT[fam].index(v)}{i:03d}"
                rows.append(p | {"szelet": "G2K3", "group_id": gid, "sorrend": S.h(f"{S.SEED}:k3-08:{gid}") % 10**12})
                n += 1
                i += 1
    return rows



def _valtozatok(fam: str, p: dict, egyseg: str, szelet: tuple[str, str, str], extra: dict) -> list[dict]:
    """Egy egység: három (b) (a 2. és a 3. más formában) és az (a)."""
    out = []
    dims = [p["dim"]]
    for v in (2, 3):
        rnd = S.rnd_for("g2dim", egyseg, v)
        for _ in range(20):
            d = {k: rnd.choice(x)[S.LANGS.index(p["lang"])] for k, x in S.DIM[fam].items()}
            if d not in dims:
                break
        dims.append(d)
    e0 = {**p["ertelmezes"], **extra, "kor": 2, "par": egyseg, "egyseg": egyseg, "szelet": szelet[1]}
    for v, d in enumerate(dims, 1):
        out.append({**p, "dim": d, "szelet": szelet[0], "ertelmezes": {**e0, "alt": "b", "valtozat": v}})
    a = E.a_valtozat({**p, "szelet": szelet[0]})
    out.append({**a, "ertelmezes": {**e0, "alt": "a", "valtozat": 0}})
    return out


def terv_ert(fam: str, resz: str) -> list[dict]:
    sz = ERT_SZELET[resz]
    E.KOR["n"] = 2
    rows, kimarad = [], Counter()
    egysegek: list[tuple[str, str, list[dict]]] = []  # (nyelv, egység-id, változatok)
    if fam in (BANK, HIBA):
        for lang in S.LANGS:
            for sab in sablonok(fam, sz[2], lang):
                n, seq = 0, 0
                while n < EGYSEG[resz][fam]:
                    if seq > EGYSEG[resz][fam] + 40:
                        kimarad[f"{lang}: kevés egység a sablonban"] += 1
                        break
                    p = E.plan_e(fam, sab, seq)
                    seq += 1
                    if p is None:
                        continue
                    p = E.kieg2(fam, sab, p, seq - 1)
                    eid = f"{fam}:{sz[0]}:{sab['sablon_id']}:{n}"
                    egysegek.append((lang, eid, _valtozatok(fam, p, eid, sz, {})))
                    n += 1
    else:
        fk = FK.forgatokonyvek(sz[1])
        for lang in S.LANGS:
            sabs = sablonok(fam, sz[2], lang)
            for f in fk[lang]:
                jo = sorted((s for s in sabs if {x["tipus"] for x in s["pontok"]} >= {f["gold"], f["csali"]}),
                            key=lambda s: S.h(f"{S.SEED}:g2fk:{f['id']}:{s['sablon_id']}"))
                if not jo:
                    raise SystemExit(f"{f['id']} {lang}: egyik sablonban sincs meg a két költségnem")
                E.SZ.FORGATOKONYV[lang] = [{k: f[k] for k in ("gold", "csali", "helyzet", "jel", "kulcs")}]
                E.SZ.JEL2[lang] = [{k: f[k] for k in ("jel2", "kulcs2", "tamasz")}]
                n, j = 0, 0
                while n < EGYSEG[resz][fam]:
                    if j > 50 * len(jo):
                        raise SystemExit(f"{f['id']} {lang}: nem jön ki {EGYSEG[resz][fam]} egység")
                    sab, seq = jo[j % len(jo)], j // len(jo)
                    j += 1
                    p = E.plan_e(fam, sab, f"{f['id']}:{seq}")
                    if p is None:
                        continue
                    p = E.kieg2(fam, sab, p, seq)
                    eid = f"{fam}:{sz[0]}:{f['id']}:{lang}:{n}"
                    egysegek.append((lang, eid, _valtozatok(fam, p, eid, sz, {"forgatokonyv": f["id"]})))
                    n += 1
    i = defaultdict(int)
    for lang, _, vs in egysegek:
        for q in vs:
            gid = f"{fam}:{sz[0]}:{lang}:{q['allapot']}:{i[lang]:05d}"
            rows.append(q | {"group_id": gid, "sorrend": S.h(f"{S.SEED}:g2ert:{gid}") % 10**12})
            i[lang] += 1
    if kimarad:
        print(f"{fam}: {dict(kimarad)}")
    return rows


def cmd_terv(a) -> None:
    fam = a.csalad
    rows = (terv_friss(fam) if a.resz == "friss" else terv_k3(fam) if a.resz == "k3" else terv_ert(fam, a.resz))
    S.jl_write(path("terv", fam), rows)
    c = Counter(r["allapot"] for r in rows)
    extra = ""
    if a.resz.startswith("ert"):
        e = {r["ertelmezes"]["egyseg"] for r in rows}
        extra = f"; {len(e)} egység, {len({r['ertelmezes'].get('forgatokonyv') or r['sablon_id'] for r in rows})} klaszter"
    elif a.resz == "k3":
        extra = "; " + ", ".join(f"{k}={v}" for k, v in sorted(Counter(r["nehez"]["valt"] for r in rows).items()))
    print(f"{fam} ({a.resz}): {len(rows)} terv; " + ", ".join(f"{k}={v}" for k, v in sorted(c.items())) + extra)


# --- generálás és itemek -------------------------------------------------------------------------------------------------

def _generator(resz: str) -> None:
    """A rész generátor-utasítása és tényellenőrzője a `szint06` útján (a friss a 06-é, a k3 a `szint07k3`-é)."""
    if resz == "k3":
        S.gen_prompt, S.fact_check = K3.gen_prompt3, K3.fact_check3
    elif resz == "friss":
        S.gen_prompt, S.fact_check = E.ORIG_GEN, S.fact_check


def cmd_gen(a) -> None:
    a.proba = False
    if a.resz.startswith("ert"):
        E.KOR["n"] = 2
        E.path = lambda kind, fam: path(kind, fam)  # noqa: E731
        E.cmd_gen(a)
    else:
        _generator(a.resz)
        S.cmd_gen(a)


def cmd_final(a) -> None:
    fam = a.csalad
    if a.resz in ("friss", "k3"):
        a.proba = a.resz == "k3"  # a friss a 07 kvótáival (cellánként a hash-sorrend első N túlélője), a k3 minden túlélője
        _generator(a.resz)
        S.cmd_final(a)
        items = S.jl_read(path("items", fam))
    else:
        raw = [r for r in S.jl_read(path("raw", fam)) if "szoveg" in r]
        kesz = Counter(r["terv"]["ertelmezes"]["egyseg"] for r in raw)
        kell = Counter(p["ertelmezes"]["egyseg"] for p in S.jl_read(path("terv", fam)))
        items = []
        for r in raw:
            e = r["terv"]["ertelmezes"]
            if kesz[e["egyseg"]] != kell[e["egyseg"]]:
                continue
            it = S.to_item(r)
            it["meta"] |= {"ertelmezes": e}
            if fam == SZAB:
                it["template_group_id"] = f"{SZAB}:G2:{e['forgatokonyv']}"
            items.append(it)
        elv = Counter(r.get("hiba") for r in S.jl_read(path("raw", fam)) if "szoveg" not in r)
        print(f"{fam}: {len(items)} item, {len({i['meta']['ertelmezes']['egyseg'] for i in items})} teljes egység / "
              f"{len(kell)}; a generálásban elveszett: {dict(elv)}")
    for it in items:
        it["question"] = L.bank_kerdes(it)
    S.jl_write(path("items", fam), items)
    print(f"{fam} ({a.resz}): {len(items)} item; " + ", ".join(f"{k}={v}" for k, v in sorted(Counter(i["content_state"] for i in items).items())))


def cmd_minta(a) -> None:
    out = [f"# 08 G2 — mintapromptok ({a.resz}); a terv a G2 sablonjain\n"]
    for fam in CSALADOK:
        p_ = path("terv", fam)
        if not p_.exists():
            continue
        rows = S.jl_read(p_)
        _generator(a.resz)
        E.KOR["n"] = 2
        for lang in S.LANGS:
            sel = [r for r in rows if r["lang"] == lang][:a.n * (4 if a.resz.startswith("ert") else 1)]
            for p in sel:
                g = E.gen_prompt_e(p) if a.resz.startswith("ert") else S.gen_prompt(p)
                gold = next((o["text"] for o in p["opciok"] if o["sid"] == p["gold_sid"]), "— (Y)")
                out += [f"## {fam} · {lang} · {p['group_id']}" + (f" · ({p['ertelmezes']['alt']}{p['ertelmezes']['valtozat'] or ''})"
                                                                  if a.resz.startswith("ert") else ""),
                        "", g, "", "**Opciók:**", ""] + [f"- `{o['sid']}` {o['text']}" for o in p["opciok"]] + ["", f"**Gold:** {gold}", ""]
    o = GYOKER["d"] / a.resz / "minta_promptok.md"
    o.parent.mkdir(parents=True, exist_ok=True)
    o.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"→ {o}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sb = sub.add_parser("sablon")
    sb.add_argument("--url", default="")
    sb.add_argument("--model", default="")
    sb.add_argument("--extra", default="")
    sb.add_argument("--workers", type=int, default=16)
    t = sub.add_parser("terv")
    m = sub.add_parser("minta")
    m.add_argument("--n", type=int, default=2)
    g = sub.add_parser("gen")
    g.add_argument("--url", required=True)
    g.add_argument("--model", required=True)
    g.add_argument("--extra", default="")
    g.add_argument("--workers", type=int, default=32)
    f = sub.add_parser("final")
    for x in (sb, t, g, f):
        x.add_argument("--csalad", required=True, choices=CSALADOK)
    for x in (t, m, g, f):
        x.add_argument("--resz", required=True, choices=RESZEK)
    for x in (sb, t, m, g, f):
        x.add_argument("--gyoker", help="a kimenet gyökere (alapból kor08/adat/G2)")
    a = ap.parse_args()
    if a.gyoker:
        GYOKER["d"] = Path(a.gyoker) if Path(a.gyoker).is_absolute() else EXP / a.gyoker
    RESZ["r"] = getattr(a, "resz", "friss")
    telepit()
    if a.cmd == "sablon":
        a.proba = False
        S.cmd_sablon(a)
        return
    {"terv": cmd_terv, "minta": cmd_minta, "gen": cmd_gen, "final": cmd_final}[a.cmd](a)


if __name__ == "__main__":
    main()
