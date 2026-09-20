#!/usr/bin/env python3
"""Determinisztikus pontozó (a terv §3.1 exact-match rétege).

Normalizálás — a terv szerint, ÉKEZETMEGŐRZÉSSEL:
  · whitespace-összevonás; a NEM TÖRHETŐ SZÓKÖZ (U+00A0) is sima szóköznek számít
    (a korpusz vegyesen használja — mérve: D1/D2 sima, D3 nem törhető)
  · kis/nagybetű-érzéketlenség, de az ékezet KÜLÖNBSÉG (kavics ≠ kavics típusú ékezetvesztés = hiba)
  · dátum → ISO 8601
  · szám → ezres elválasztó el, tizedesvessző → pont
  · listamező → sorrendfüggetlen halmaz-összevetés, részpont: talált_helyes / max(elvárt, adott)
"""
import re, unicodedata
from datetime import date

NBSP = " "
HONAP = {"január":1,"február":2,"március":3,"április":4,"május":5,"június":6,
         "július":7,"augusztus":8,"szeptember":9,"október":10,"november":11,"december":12}

def _ws(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace(NBSP, " ").replace(" ", " ")).strip()

def norm_szoveg(v) -> str:
    if v is None:
        return ""
    return _ws(str(v)).lower()

def norm_szam(v):
    """'1 234 567,50' / '1234567.5' / 1234567.5 → Decimal-szerű float; None ha nem szám."""
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if v is None:
        return None
    s = _ws(str(v))
    s = re.sub(r"[^\d,.\-]", "", s)              # Ft, %, szóköz le
    if s.count(",") == 1 and s.count(".") == 0:
        s = s.replace(",", ".")
    else:
        s = s.replace(",", "")
    if s in ("", "-", "."):
        return None
    try:
        return float(s)
    except ValueError:
        return None

def norm_datum(v):
    """ISO-ra hozza a '2027. január 1.' / '2027-01-01' / '2027.01.01' alakokat."""
    if v is None:
        return None
    s = _ws(str(v)).lower().rstrip(".")
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
    if m:
        return s
    m = re.match(r"^(\d{4})[.\-/ ]\s*(\d{1,2})[.\-/ ]\s*(\d{1,2})$", s)
    if m:
        return f"{int(m[1]):04d}-{int(m[2]):02d}-{int(m[3]):02d}"
    m = re.match(r"^(\d{4})\.?\s*([a-záéíóöőúüű]+)\s*(\d{1,2})$", s)
    if m and m[2] in HONAP:
        return f"{int(m[1]):04d}-{HONAP[m[2]]:02d}-{int(m[3]):02d}"
    return None

def egyezik(gt, pred, tipus="auto") -> bool:
    if isinstance(gt, bool) or isinstance(pred, bool):
        return bool(gt) == bool(pred) if isinstance(gt, bool) and isinstance(pred, bool) else False
    if tipus == "datum" or (isinstance(gt, str) and re.match(r"^\d{4}-\d{2}-\d{2}$", gt)):
        return norm_datum(gt) is not None and norm_datum(gt) == norm_datum(pred)
    if isinstance(gt, (int, float)):
        p = norm_szam(pred)
        return p is not None and abs(p - float(gt)) < 1e-9
    a, b = norm_szoveg(gt), norm_szoveg(pred)
    if a == b:
        return True
    # szám-alakú szöveg (pl. „6" vs 6)
    na, nb = norm_szam(gt), norm_szam(pred)
    return na is not None and nb is not None and abs(na - nb) < 1e-9

_HIV_SZOTOVEK = [
    (r"\bpontj(a|át|ában|ai|aiban)\b", "pont"),
    (r"\bpontban\b", "pont"),
    (r"\bpontjának\b", "pont"),
    (r"\bszámú\b", "sz."),
    (r"\bmellékletének\b", "melléklet"),
    (r"\bmellékletében\b", "melléklet"),
    (r"\bmelléklete\b", "melléklet"),
]

def norm_hivatkozas(v) -> str:
    """Pont-/szakaszhivatkozás normalizálása: „11.4. pont" ≡ „11.4" ≡ „11.4. pontja".

    ⛔ Ez FORMÁZÁSI normalizálás, nem tartalmi engedmény: a hivatkozott SZÁM nem változik.
    """
    s = norm_szoveg(v)
    for mint, csere in _HIV_SZOTOVEK:
        s = re.sub(mint, csere, s)
    s = re.sub(r"(\d)\.(?=\s|$)", r"\1", s)      # záró pont a szám után: „11.4." → „11.4"
    s = re.sub(r"[\s,;:]+", " ", s).strip(" .,;:")
    return s

_HIV_TOKEN = re.compile(r"[a-z0-9]+(?:\.[a-z0-9]+)*", re.I)

def hivatkozas_egyezik(gt, pred) -> bool:
    """A GT-hivatkozás TOKENJEI hiánytalanul szerepelnek-e a predikcióban.

    Így a bőbeszédű, de helyes válasz („…MŰSZAKI TARTALOM, M1. pont") is elfogadott,
    a rossz hivatkozás („4.4." a „4.2" helyett) viszont NEM.
    """
    g, p = norm_hivatkozas(gt), norm_hivatkozas(pred)
    if not g:
        return False
    if g == p:
        return True
    gt_tok = _HIV_TOKEN.findall(g)
    p_tok = set(_HIV_TOKEN.findall(p))
    return bool(gt_tok) and all(t in p_tok for t in gt_tok)

def _dict_reszpont(gt_d, pred_d) -> float:
    """Listaelem-dict összevetése: CSAK a ground truth kulcsait nézzük.

    ⛔ A predikció extra kulcsai (pl. a sémában kért `megnevezes`) nem rontanak —
    a T5-03-at pontosan ez buktatta meg a kalibrációban.
    """
    if not isinstance(pred_d, dict):
        return 0.0
    if not gt_d:
        return 1.0
    jo = sum(1 for k, v in gt_d.items() if egyezik(v, pred_d.get(k)))
    return jo / len(gt_d)

def lista_reszpont(gt_lista, pred, hivatkozas=False) -> float:
    """talált_helyes / max(elvárt, adott) — sorrendfüggetlen.

    Dict-elemű listánál elemenként a GT kulcsain mért részpontot adja (mohó párosítás).
    """
    if not isinstance(pred, list):
        return 0.0
    if gt_lista and isinstance(gt_lista[0], dict):
        maradek = list(pred)
        ossz = 0.0
        for gd in gt_lista:
            if not maradek:
                break
            pontok = [_dict_reszpont(gd, pd) for pd in maradek]
            legjobb = max(range(len(pontok)), key=lambda i: pontok[i])
            ossz += pontok[legjobb]
            maradek.pop(legjobb)
        return ossz / max(len(gt_lista), len(pred))
    if hivatkozas:
        maradek = list(pred)
        talalt = 0
        for x in gt_lista:
            for i, y in enumerate(maradek):
                if hivatkozas_egyezik(x, y):
                    maradek.pop(i); talalt += 1; break
        return talalt / max(len(gt_lista), len(pred)) if max(len(gt_lista), len(pred)) else 1.0
    g = [norm_szoveg(x) for x in gt_lista]
    p = [norm_szoveg(x) for x in pred]
    maradek = list(p)
    talalt = 0
    for x in g:
        if x in maradek:
            maradek.remove(x)
            talalt += 1
    return talalt / max(len(g), len(p)) if max(len(g), len(p)) else 1.0

BIRO_JELOLOK = ("__BIRO__", "__BIRO_NEM_PONTOZOTT__")

def pontoz_item(item, pred) -> dict:
    """Egy item pontszáma. A bírói mezőket kihagyja (azokat a §3.2 réteg pontozza)."""
    gt = item["gt"]
    max_pont = item["pont"]
    if pred is None:
        return {"pont": 0.0, "max": max_pont, "reszletek": {}, "json_hiba": True}
    exact_mezok = {k: v for k, v in gt.items() if v not in BIRO_JELOLOK}
    biro_mezok = [k for k, v in gt.items() if v == "__BIRO__"]
    if not exact_mezok:
        return {"pont": 0.0, "max": max_pont, "reszletek": {}, "json_hiba": False,
                "csak_biro": True}
    # a bírói mező súlya a T1-nél 1 pont, a T7-09-nél 2-ből 2 → a maradék az exact mezőkre oszlik
    biro_suly = {"T1-01": 1.0, "T7-09": 1.0}.get(item["id"], 0.0)
    exact_keret = max_pont - biro_suly
    egysegnyi = exact_keret / len(exact_mezok)
    tipusok = item.get("mezo_tipusok", {})
    reszl, ossz = {}, 0.0
    for k, gv in exact_mezok.items():
        pv = pred.get(k)
        hiv = tipusok.get(k) == "hivatkozas"
        if isinstance(gv, list):
            r = lista_reszpont(gv, pv, hivatkozas=hiv)
        elif hiv:
            r = 1.0 if hivatkozas_egyezik(gv, pv) else 0.0
        else:
            r = 1.0 if egyezik(gv, pv) else 0.0
        reszl[k] = {"gt": gv, "pred": pv, "arany": r}
        ossz += r * egysegnyi
    return {"pont": round(ossz, 4), "max": max_pont, "reszletek": reszl,
            "json_hiba": False, "biro_mezok": biro_mezok, "biro_suly": biro_suly}

if __name__ == "__main__":
    assert egyezik("2027-01-01", "2027. január 1.")
    assert egyezik(1860000, "1 860 000 Ft")
    assert egyezik(1860000, "1 860 000")
    assert egyezik(1234567.5, "1 234 567,50")
    assert egyezik(6, "6")
    assert not egyezik("kéményseprő", "kéményseprô"), "az ékezetvesztés HIBA"
    assert egyezik("Óvadék", "óvadék")
    assert abs(lista_reszpont(["a", "b", "c"], ["a", "c"]) - 2/3) < 1e-9
    assert abs(lista_reszpont(["a", "b"], ["a", "b", "x"]) - 2/3) < 1e-9
    assert egyezik(False, False) and not egyezik(False, True)
    # hivatkozás-normalizálás (a kalibrációban MÉRT alakok)
    assert hivatkozas_egyezik("10.5", "10.5.")
    assert hivatkozas_egyezik("11.4", "11.4. pont")
    assert hivatkozas_egyezik("1. sz. melléklet 4. pont", "1. sz. melléklet 4. pontja")
    assert hivatkozas_egyezik("1. sz. melléklet 4. pont", "1. számú melléklet 4. pontja")
    assert hivatkozas_egyezik("M1", "A VÁLLALKOZÁSI SZERZŐDÉS 1. SZ. MELLÉKLETE — MŰSZAKI TARTALOM, M1. pont")
    assert not hivatkozas_egyezik("4.2", "4.4."), "a ROSSZ hivatkozás nem mehet át"
    assert not hivatkozas_egyezik("11.4", "11.45")
    assert not hivatkozas_egyezik("10.5", "")
    # dict-listánál a predikció extra kulcsa nem ronthat (T5-03)
    assert abs(lista_reszpont(
        [{"netto_ft": 100, "afakulcs_vagy_jogcim": "27%"}],
        [{"megnevezes": "x", "netto_ft": 100, "afakulcs_vagy_jogcim": "27%"}]) - 1.0) < 1e-9
    assert abs(lista_reszpont(
        [{"netto_ft": 100, "afakulcs_vagy_jogcim": "27%"}],
        [{"netto_ft": 100, "afakulcs_vagy_jogcim": "5%"}]) - 0.5) < 1e-9
    print("pontozó önteszt: minden állítás teljesül")
