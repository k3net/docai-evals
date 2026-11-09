"""08 G1 — a szabályalapú kinyerő (D1: csak leíró összevetés az alany kinyerésével). Ugyanazt látja, mint az alany: a
tétel szövegét, a hibacsaládon a szabályok mérésneveit is, a jelölteket nem. Reguláris kifejezések és a lánc
számfelismerője (`lanc08.szamok`); a forrásrészlet a szám mondata (mint az orákulumé). A kimenet a `kinyer08`
formátumában (`{"id", "family", "sema": "szabaly", "mezok"}`), így a `g1_lanc08` ugyanúgy veti össze az orákulummal.

  bank    osszeg: az első pénznemjelölős szám (abszolút érték); reszlet_arany: %-os szám 1–99 közt, ha nem áfa-környezet;
          hivatkozas: számlaszám-minta (`XX-2026/1234`, `XX-2026-1234`); partner: jogi formára végződő cégnév, nem a
          számlatulajdonosé
  hiba    meres: a szabály mérésneve után az első szám és a mögötte álló egység (kapcsolat: a mérésnév)
  szab    osszeg: pénznemjelölős szám (bruttó / nettó / teljes jelölő előnyben), deviza, alap; afakulcs: %-os szám
          áfa-környezetben; arfolyam: szám pénznempár (Ft/EUR …) vagy árfolyam-szó mellett

  python3 kor08/eszkozok/szabkin08.py --out kor08/adat/G1/kinyeres_szabaly
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lanc08 as L  # noqa: E402

DEVIZA = [("HUF", re.compile(r"\b(?:Ft|HUF|forint)\b", re.I)), ("EUR", re.compile(r"(?:\bEUR\b|€|\beuró|\beuro)", re.I)),
          ("GBP", re.compile(r"(?:\bGBP\b|£|\bpounds?\b)", re.I))]
PAR = re.compile(r"\b(Ft|HUF|EUR|GBP)\s*/\s*(EUR|GBP|HUF)\b")
AFA = re.compile(r"áf[aá]|\bvat\b", re.I)  # „áfával”: a toldalékos alak „áfá”
SZAZALEK = re.compile(r"^\s*(?:%|százal[ée]k|percent|per cent)")
REF = re.compile(r"\b[A-Z]{1,5}-\d{4}[/-]\d{2,6}\b")
JOGI = r"(?:Kft\.|Zrt\.|Bt\.|Nyrt\.|Kkt\.|Ltd\.?|LLC|plc|PLC|Inc\.?|GmbH)"
CEG = re.compile(r"(?:[A-ZÁÉÍÓÖŐÚÜŰ][\wÁÉÍÓÖŐÚÜŰáéíóöőúüű&.'\-]*\s+(?:(?:és|and|&)\s+)?){1,5}" + JOGI)
TULAJ = re.compile(r"^(?:Számlatulajdonos|Account holder)\s*:\s*(.*?)\s*$", re.M)
NEM_NEV = {"a", "az", "the", "ft", "huf", "eur", "gbp"}  # a cégnév elé csúszó szavak
BRUTTO = re.compile(r"\b(?:bruttó|gross|összesen|teljes|total)\b", re.I)
NETTO = re.compile(r"\b(?:nettó|net of VAT|net)\b", re.I)
ARFOLYAM_SZO = re.compile(r"(?:árfolyam|exchange rate|\brate\b)", re.I)
ABLAK = 6  # a pénznemjelölő legfeljebb ennyi karakterre a számtól
NEVES_MERES = re.compile(r"(?m)(?:^|[;:.]\s*|\|\s*)(?P<nev>[A-ZÁÉÍÓÖŐÚÜŰ][^\n:;|]{2,60}?):\s*(?P<szam>[-−]?\d[\d.,]*)\s*"
                         r"(?P<egyseg>[^\s;,()|]+)")


def _deviza(text: str, a: int, b: int) -> str | None:
    elotte, utana = text[max(0, a - ABLAK):a], text[b:b + ABLAK]
    if PAR.match(text[b:b + 12].lstrip()):
        return None  # „407 Ft/EUR”: árfolyam, nem összeg
    for dev, rx in DEVIZA:
        if rx.search(utana) or rx.search(elotte):
            return dev
    return None


def _mezo(szerep: str, ertek, text: str, a: int, b: int, **kw) -> dict:
    return {"szerep": szerep, "ertek": ertek, "forras": L._mondat(text, a, b), **kw}


def bank(text: str, lang: str) -> list[dict]:
    tulaj = [(m.start(), m.end()) for m in TULAJ.finditer(text)]
    kint = [n for n in L.szamok(text, lang) if not any(a <= n[0] < b for a, b in tulaj)]
    out: list[dict] = []
    for a, b, v in kint:
        if _deviza(text, a, b):
            out.append(_mezo("osszeg", abs(v), text, a, b))
            break
    for a, b, v in kint:
        if SZAZALEK.match(text[b:b + 12]) and 1 <= v <= 99 and not AFA.search(text[max(0, a - 15):b + 15]):
            out.append(_mezo("reszlet_arany", v, text, a, b))
            break
    if m := REF.search(text):
        out.append(_mezo("hivatkozas", m.group(0), text, m.start(), m.end()))
    sajat = {L.norm(m.group(1)) for m in TULAJ.finditer(text)}
    for m in CEG.finditer(text):
        if any(a <= m.start() < b for a, b in tulaj):
            continue
        szavak, kezd = m.group(0).split(), m.start()
        while len(szavak) > 1 and (szavak[0].lower() in NEM_NEV or szavak[0].isupper()):
            kezd = text.index(szavak[1], kezd + len(szavak[0]))
            szavak = szavak[1:]
        nev = text[kezd:m.end()].strip()
        if L.norm(nev) not in sajat:
            out.append(_mezo("partner", nev, text, kezd, kezd + len(nev)))
            break
    return out


def hiba(text: str, lang: str, it: dict) -> list[dict]:
    nevek = sorted({j["meres"] for j in L.jeloltek(L.HIBA, it["options"], lang)[0]}, key=len, reverse=True)
    out, fog = [], set()
    low = text.lower()
    for nev in nevek:
        i = low.find(nev.lower())
        if i < 0:
            continue
        for a, b, v in L.szamok(text, lang):
            if a >= i + len(nev) and a - (i + len(nev)) <= 40 and a not in fog:
                egy = re.match(r"\s*([^\s;,()]+)", text[b:])
                egyseg = egy.group(1).rstrip(".") if egy else ""
                fog.add(a)
                out.append(_mezo("meres", v, text, a, b, egyseg=egyseg, kapcsolat=nev))
                break
    for m in NEVES_MERES.finditer(text):  # a szabályok közt nem szereplő mérés is mező, kapcsolat nélkül (mint az orákulum)
        a = m.start("szam") - (1 if m.group("szam").startswith(("-", "−")) else 0)
        n = [x for x in L.szamok(text, lang) if m.start("szam") - 1 <= x[0] <= m.start("szam")]
        if n and n[0][0] not in fog:
            fog.add(n[0][0])
            out.append(_mezo("meres", n[0][2], text, n[0][0], n[0][1], egyseg=m.group("egyseg").rstrip("."),
                             kapcsolat=None))
    return out


def szab(text: str, lang: str) -> list[dict]:
    nums = L.szamok(text, lang)
    out: list[dict] = []
    jelolt = [(a, b, v, d) for a, b, v in nums if (d := _deviza(text, a, b))]
    if jelolt:
        def pont(x):
            mondat = L._mondat(text, x[0], x[1])
            return (bool(BRUTTO.search(mondat)) or bool(NETTO.search(mondat)), abs(x[2]))
        a, b, v, d = max(jelolt, key=pont)
        mondat = L._mondat(text, a, b)
        alap = "brutto" if BRUTTO.search(mondat) and re.search(r"bruttó|gross", mondat, re.I) else (
            "netto" if NETTO.search(mondat) else None)
        out.append(_mezo("osszeg", v, text, a, b, deviza=d, alap=alap))
    for a, b, v in nums:
        if SZAZALEK.match(text[b:b + 12]) and AFA.search(text[max(0, a - 25):b + 25]):
            out.append(_mezo("afakulcs", v, text, a, b))
            break
    for a, b, v in nums:
        par = PAR.match(text[b:b + 12].lstrip())
        if par or (ARFOLYAM_SZO.search(text[max(0, a - 40):a]) and not _deviza(text, a, b)):
            p = f"{'HUF' if par and par.group(1) == 'Ft' else par.group(1)}/{par.group(2)}" if par else None
            out.append(_mezo("arfolyam", v, text, a, b, **({"par": p} if p else {})))
            break
    return out


def kinyer(fam: str, it: dict, lang: str) -> list[dict]:
    text = it["state"]
    if fam == L.BANK:
        return bank(text, lang)
    if fam == L.HIBA:
        return hiba(text, lang, it)
    return szab(text, lang)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forras", nargs="+", default=list(L.ONTESZT))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out) if Path(a.out).is_absolute() else L.EXP / a.out
    out.mkdir(parents=True, exist_ok=True)
    for src in a.forras:
        for fam in L.CSALADOK:
            sor = [json.dumps({"id": it["id"], "family": fam, "sema": "szabaly", "mezok": kinyer(fam, it, terv["lang"])},
                              ensure_ascii=False) for terv, it in L.betolt(src, fam)]
            (out / f"{src}_{fam}.jsonl").write_text("\n".join(sor) + "\n", encoding="utf-8")
            print(f"{src} {fam}: {len(sor)}")


if __name__ == "__main__":
    main()
