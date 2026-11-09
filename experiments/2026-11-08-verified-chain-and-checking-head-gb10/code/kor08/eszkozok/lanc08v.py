"""08B — a lánc valódi banki tételeken (G1-rögzítés 4.3, „bank (valódi, 08B)” sor; runbook 7.). A `lanc08` és a J-javítás (`lanc08j`) burkolója, a rögzített fájlok nem változnak.

Eltérés a szintetikus banktól:
  - az összeg, a pénznem és a partner strukturált mező a tételsorból (`b7_epit` formátuma), nem a kinyerésből; a kinyerő csak a közleményt kapja (`kinyeres_kozlemenybol`), és belőle csak a hivatkozás és a részlet-arány jön, a J-es ellenőrzéssel;
  - **kizárás csak strukturális ellentmondásból:** eltérő pénznem; az irányt a jelöltlista már szűri (a számla típusa az opcióban nem látszik), az összegeltérés nem kizáró ok;
  - **kötés** mint a szintetikus banknál: a hivatkozás pontosan egy jelölt számlaszáma, a pénznem azonos, az összeg (a részlet-arány után) a tűrésen belül egyezik, a partner nem mond ellent, és a
    tétel nem nevez meg más jelölt partnert. Az összeg egyezése pozitív bizonyíték; a részfizetés-jel hiányából nem következik teljes fizetés;
  - a feladatszabály nem kerül a kérdésbe (4.3); ikrek a modellhez (D3).
A `szamitott.kozvetlen` leíró: mely jelöltek számlaszáma áll szó szerint a közleményben vagy a hivatkozásban (a kinyerés fedésének mérésére, a döntésbe nem számít).
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent)]
import lanc08 as L  # noqa: E402
import lanc08j as J  # noqa: E402

SOR = re.compile(r"^(?P<datum>\d{4}-\d{2}-\d{2}) · (?P<irany>[^·]+?) · (?P<osszeg>[^·]+?) · Partner: (?P<partner>.*?) · Közlemény: (?P<kozlemeny>.*?)(?: · Hivatkozás: (?P<hiv>.*))?$", re.S)
PENZ = re.compile(r"([\d\s]+(?:,\d+)?)\s*(Ft|[A-Z]{3})")
_OPCIO0 = L._bank_opcio
BEHOZOTT = ("hivatkozas", "reszlet_arany")


def tetelsor(it: dict) -> dict | None:
    """A tételsor mezői; None, ha nem a `b7_epit` formátuma."""
    m = SOR.match(it["state"].strip().split("\n\n", 1)[-1])
    if not m:
        return None
    p = PENZ.fullmatch(m["osszeg"].strip())
    if not p:
        return None
    osszeg = L.szam(re.sub(r"\s", "", p[1]), "hu")
    partner = m["partner"].strip()
    return {"osszeg": osszeg, "deviza": "HUF" if p[2] == "Ft" else p[2], "partner": None if partner in ("", "—") else partner,
            "kozlemeny": m["kozlemeny"].strip(), "hivatkozas": (m["hiv"] or "").strip(), "sor": m[0]}


def bank_opcio(t: str, lang: str) -> dict | None:
    """A `b7_epit` a nem forintos számlát „1 234,56 EUR” alakban írja; a szintetikus forma a `lanc08`-é."""
    j = _OPCIO0(t, lang)
    if j is not None:
        return j
    p = t.split(" · ")
    m = PENZ.fullmatch(p[2].strip()) if len(p) == 4 else None
    if not m:
        return None
    return {"szamlaszam": p[0].strip(), "partner": p[1].strip(), "osszeg": L.szam(re.sub(r"\s", "", m[1]), "hu"), "deviza": "HUF" if m[2] == "Ft" else m[2],
            "esedekes": re.sub(r"^(esedékes|due)\s+", "", p[3].strip())}


def fold(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", L.norm(s)) if not unicodedata.combining(c))


def partner_egyezik(a: str, b: str) -> bool:
    x, y = fold(a), fold(b)
    return x == y or x.split()[0] == y.split()[0]


def lanc_v(it: dict, mezok: list[dict] | None) -> dict:
    lang, text = it["lang"], it["state"]
    jel, rossz_opc = L.jeloltek(L.BANK, it["options"], lang)
    res = {"id": it["id"], "kimenet": None, "megmaradt": [], "kizart": {}, "kotes": None, "szamitott": {}, "blokk": "", "bukott": [], "nem_ertelmezheto_opcio": rossz_opc, "elvetett": []}
    t = tetelsor(it)
    if t is None:
        res["kimenet"], res["bukott"] = "emberhez", [{"ok": "a tételsor nem értelmezhető"}]
        return res
    if mezok is None:
        res["kimenet"], res["bukott"] = "emberhez", [{"ok": "nincs kinyerés"}]
        return res
    jo, rossz = L.ellenoriz(L.BANK, text, lang, [f for f in mezok if f.get("szerep") in BEHOZOTT], jel)
    res["elvetett"] = [{k: v for k, v in f.items() if not k.startswith("_")} for f in rossz]
    arany = {round(f["_v"], 6) for f in L._egy(jo, "reszlet_arany")}
    if len(arany) > 1:
        res["kimenet"], res["bukott"] = "emberhez", [{"ok": "ellentmondás: több reszlet_arany"}]
        return res
    a, dev = abs(t["osszeg"]), t["deviza"]
    r = next(iter(arany)) if arany else None
    teljes = a * 100 / r if r else a
    tol = (1.0 if dev == "HUF" else 0.01) * (1 + (50 / r if r else 0))
    pz = lambda x: L.penz(x, lang, dev)  # noqa: E731
    blokk = [f"a tétel összege: {pz(a)}"]
    if r:
        blokk.append(f"részlet-arány: {L.fmt(r, lang)}%; a számla teljes bruttó összege ennek alapján: {pz(teljes)}")
    allit = {j["id"]: ("lehetseges", None) for j in jel}
    for j in jel:
        if j["deviza"] != dev:
            allit[j["id"]] = ("kizart", "a pénznem ellentmond")
    refs = {L.norm_ref(str(f["_v"])) for f in L._egy(jo, "hivatkozas")}
    talalt = [j for j in jel if L.norm_ref(j["szamlaszam"]) in refs]
    osszegben = [j["id"] for j in jel if j["deviza"] == dev and abs(j["osszeg"] - teljes) <= tol]
    sor = f"{t['partner'] or ''} {t['kozlemeny']} {t['hivatkozas']}"
    res["szamitott"] = {"osszeg": a, "deviza": dev, "reszlet_arany": r, "teljes": teljes, "tol": tol, "osszegben": osszegben, "talalt": [j["id"] for j in talalt],
                        "kozvetlen": [j["id"] for j in jel if L.norm_ref(j["szamlaszam"]) in L.norm_ref(f"{t['kozlemeny']} {t['hivatkozas']}")]}
    if len(talalt) == 1 and allit[talalt[0]["id"]][0] != "kizart" and talalt[0]["id"] in osszegben:
        j = talalt[0]
        mas = [x for x in jel if fold(x["partner"]) != fold(j["partner"]) and not partner_egyezik(x["partner"], j["partner"]) and L._partner_a_szovegben(x["partner"], sor)]
        if (t["partner"] is None or partner_egyezik(t["partner"], j["partner"])) and not mas:
            allit[j["id"]] = ("kotheto", "hivatkozás + összeg + partner")
    res["allitasok"] = {k: v[0] for k, v in allit.items()}
    res["kizart"] = {k: v[1] for k, v in allit.items() if v[0] == "kizart"}
    res["megmaradt"] = [j["id"] for j in jel if allit[j["id"]][0] != "kizart"] + rossz_opc
    res["blokk"] = "Ellenőrzött adatok (a rendszer számította):\n" + "\n".join(f"- {b}" for b in blokk)
    kot = [k for k, v in allit.items() if v[0] == "kotheto"]
    if kot:
        res["kimenet"], res["kotes"] = "kotes", kot[0]
    else:
        res["kimenet"] = "modell"
    return res


def kinyeres_kozlemenybol() -> None:
    """A kinyerő csak a közleményt látja (runbook 7.): a tételsor `Hivatkozás:` mezője a bank saját azonosítója, ugyanolyan alakú, mint a számlaszám, és az alany azt adta vissza (K08V első futása, 0 kötés)."""
    regi = L.kinyero_prompt

    def prompt(fam: str, it: dict, jel: list[dict], sema: int = 1) -> list[dict]:
        t = tetelsor(it)
        return regi(fam, {**it, "state": t["kozlemeny"]} if t else it, jel, sema)
    L.kinyero_prompt = prompt


def aktival() -> None:
    """A valódi út: a J-es ellenőrzés, a `lanc_v`, a feladatszabály nélküli kérdés."""
    J.aktival()
    L._bank_opcio = bank_opcio
    L.lanc = lambda fam, it, mezok, ures="modell", valtozat="v0": lanc_v(it, mezok)  # noqa: E731
    L.bank_kerdes = lambda it: it["question"]  # noqa: E731
