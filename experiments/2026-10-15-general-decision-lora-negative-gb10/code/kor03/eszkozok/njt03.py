"""03-as kör — Nemzeti Jogszabálytár: rögzített törvénylista letöltése és szerkezeti feldolgozása (03-runbook 3.2, F0).

A jogszabályszöveg nem áll szerzői jogi védelem alatt (Szjt. 1. § (4)); Dani döntése (2026-10-09): használható. A
letöltés kíméletes: a robots.txt a /jogszabaly/* utat engedi, kérésenként 3 s szünet, egyszer töltünk le, a nyers
HTML gzip-pel a `forras/njt/raw/` alá kerül, a `forras/njt/njt03.json` rögzíti az URL-t, a hatálydátumot, a méretet és
a sha256-ot. A szöveg a letöltés napján hatályos állapot.

A feldolgozás bekezdésszintű egységeket ad (`forras/njt/njt_egysegek.jsonl`): törvény, rész, fejezet, alfejezet,
tagolócím, §, bekezdés, szöveg; a pontok a bekezdésükhöz csatolva, a lábjegyzetszámok nélkül. Ebből készülnek a
konstrukciós jogi családok (3.4: tagolócím-, fejezet- és törvényválasztás); a gold a szerkezetből jön.

  python3 kor03/eszkozok/njt03.py letolt     # hiányzók letöltése
  python3 kor03/eszkozok/njt03.py feldolgoz  # → njt_egysegek.jsonl
"""

from __future__ import annotations

import gzip
import hashlib
import html
import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NJT = ROOT / "forras/njt"
BASE = "https://njt.jog.gov.hu/jogszabaly/"
UA = "docai-labs-research/1.0 (+https://docai.hu)"
PAUSE_S = 3.0

# (NJT-azonosító, rövid név): üzleti, adó-, munkaügyi, közigazgatási és ágazati törvények
LAWS = [
    ("2013-5-00-00", "Ptk."), ("2007-127-00-00", "Áfa tv."), ("2000-100-00-00", "Számv. tv."),
    ("2017-150-00-00", "Art."), ("2017-151-00-00", "Air."), ("1995-117-00-00", "Szja tv."),
    ("1996-81-00-00", "Tao. tv."), ("1990-100-00-00", "Htv."), ("2016-150-00-00", "Ákr."),
    ("2016-130-00-00", "Pp."), ("2012-1-00-00", "Mt."), ("2015-143-00-00", "Kbt."), ("2006-5-00-00", "Ctv."),
    ("1991-49-00-00", "Cstv."), ("2011-112-00-00", "Infotv."), ("2001-108-00-00", "Ekertv."),
    ("2005-164-00-00", "Kertv."), ("1997-155-00-00", "Fgytv."), ("2008-47-00-00", "Fttv."),
    ("1996-57-00-00", "Tpvt."), ("2013-237-00-00", "Hpt."), ("2017-53-00-00", "Pmt."),
    ("2003-125-00-00", "Ebktv."), ("1993-93-00-00", "Mvt."), ("2019-122-00-00", "Tbj."),
    ("2011-189-00-00", "Mötv."), ("2011-195-00-00", "Áht."), ("1999-76-00-00", "Szjt."),
    ("1995-33-00-00", "Szabadalmi tv."), ("1997-11-00-00", "Védjegytv."), ("2012-100-00-00", "Btk."),
    ("2012-2-00-00", "Szabs. tv."), ("2017-90-00-00", "Be."), ("1997-78-00-00", "Étv."),
    ("1995-53-00-00", "Kvt."), ("2012-185-00-00", "Ht."), ("2014-88-00-00", "Bit."), ("2001-120-00-00", "Tpt."),
    ("2015-222-00-00", "E-ügyintézési tv."), ("2011-175-00-00", "Civil tv."), ("2013-77-00-00", "Fktv."),
    ("2011-190-00-00", "Nkt."), ("2011-204-00-00", "Nftv."), ("1997-154-00-00", "Eütv."),
    ("2008-46-00-00", "Éltv."), ("1988-1-00-00", "Kkt."), ("2003-100-00-00", "Eht."), ("2010-185-00-00", "Mttv."),
    ("2004-34-00-00", "Kkv. tv."), ("2009-76-00-00", "Szolgtv."), ("2022-13-00-00", "Katv."),
    ("2012-147-00-00", "Kiva tv."),
]


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def letolt() -> None:
    (NJT / "raw").mkdir(parents=True, exist_ok=True)
    man_path = NJT / "njt03.json"
    man = json.loads(man_path.read_text()) if man_path.exists() else {}
    for lid, short in LAWS:
        if lid in man and (NJT / "raw" / f"{lid}.html.gz").exists():
            continue
        req = urllib.request.Request(BASE + lid, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                body, status, final = r.read(), r.status, r.geturl()
        except Exception as e:  # noqa: BLE001
            print(lid, "HIBA", e)
            man[lid] = {"rovid": short, "hiba": str(e)}
            time.sleep(PAUSE_S)
            continue
        h = body.decode("utf-8", "replace")
        desc = re.search(r'<meta name="description"[^>]*content="([^"]*)"', h)
        hat = re.search(r'<div class="hataly">([^<]*)</div>', h)
        (NJT / "raw" / f"{lid}.html.gz").write_bytes(gzip.compress(body, mtime=0))
        man[lid] = {"rovid": short, "url": final, "status": status, "bytes": len(body), "sha256": sha256(body),
                    "cim": html.unescape(desc.group(1)) if desc else None, "hataly": hat.group(1) if hat else None,
                    "letoltve": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        print(lid, status, len(body), man[lid]["cim"])
        man_path.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
        time.sleep(PAUSE_S)
    man_path.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")


TOKEN = re.compile(r'<span class="jhId" id="([^"]+)"></span>|<(div|h1|h2)[^>]*\bclass="([^"]+)"[^>]*>(.*?)</\2>', re.S)
FN = re.compile(r'<sup class="fnSup"[^>]*>.*?</sup>', re.S)
INLINE = re.compile(r"</?(?:a|span|i|b|em|strong|sup|sub|u)\b[^>]*>")
HEADINGS = ("resz", "reszcim", "fejezet", "fejezetCim", "alcim", "tagoloCim")


def clean(fragment: str) -> str:
    t = INLINE.sub("", FN.sub("", fragment))
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t).replace("\u2005", " ").replace("\xa0", " ")
    return re.sub(r"\s+", " ", t).strip()


def feldolgoz() -> None:
    """A § és a bekezdés a jhId-horgonyból jön (SZ51 = 51. §, SZ51@BE2 = annak (2) bekezdése); a címek a
    legutóbbi címsorból. Rész vagy fejezet váltásakor az alacsonyabb szintű címek nullázódnak, alcím váltásakor a
    tagolócím is (egyes törvényekben a kettő azonos szintű számozott cím)."""
    man = json.loads((NJT / "njt03.json").read_text())
    out, stat = [], {}
    for lid, short in LAWS:
        p = NJT / "raw" / f"{lid}.html.gz"
        if not p.exists():
            continue
        h = gzip.decompress(p.read_bytes()).decode("utf-8", "replace")
        main = h[h.find('class="pslice jogszabalyMainTitle'):]
        main = main[: main.find('class="footnote"')] if 'class="footnote"' in main else main
        ctx: dict[str, str | None] = dict.fromkeys(HEADINGS)
        anchor, szakasz, bekezdes, cur = "", None, None, None
        units = []
        for m in TOKEN.finditer(main):
            if m.group(1):
                anchor = m.group(1)
                # SZ51 = 51. §; SZ6:3 = a Ptk. 6:3. §-a (könyvenkénti számozás); @BE2 = (2) bekezdés; @BE0 = számozatlan
                sz = re.match(r"SZ((?:\d+:)?\d+/?[A-Za-z]?)(?:@BE(\d+[A-Za-z]?))?", anchor)
                if sz:
                    szakasz = f"{sz.group(1)}. §"
                    be = sz.group(2)
                    bekezdes = f"({be})" if be and be != "0" else (bekezdes if "@PO" in anchor else None)
                continue
            cls, body = m.group(3).split()[0], m.group(4)
            if cls in ctx:
                ctx[cls] = clean(body)
                low = {"resz": ("fejezet", "fejezetCim", "alcim", "tagoloCim"),
                       "fejezet": ("alcim", "tagoloCim"), "alcim": ("tagoloCim",)}.get(cls, ())
                for k in low:
                    ctx[k] = None
                if cls == "resz":
                    ctx["reszcim"] = None
                continue
            if cls == "bekezdesNyito":
                # a jel-span a §-jelet is tartalmazhatja (beágyazott span): az egészet vesszük le
                text = clean(re.sub(r'<span class="jel">(?:\s*<span class="szakasz-jel">[^<]*</span>)?[^<]*</span>\s*', "",
                                    body, count=1, flags=re.S))
                cur = {"law": lid, "rovid": short, "cim": man[lid]["cim"], "szakasz": szakasz,
                       "bekezdes": bekezdes if "@BE" in anchor else None, **ctx, "szoveg": text}
                units.append(cur)
            elif cls in ("betusPontNyito", "szamosPontNyito", "ketbetusAlPont", "pontZaro", "bekezdesZaro") and cur:
                cur["szoveg"] = (cur["szoveg"] + " " + clean(body)).strip()
        units = [u for u in units if len(u["szoveg"]) >= 40]
        out.extend(units)
        stat[lid] = {"rovid": short, "egyseg": len(units), "szakasz_nelkul": sum(u["szakasz"] is None for u in units),
                     "alcim_vagy_tagolocim": len({u["tagoloCim"] or u["alcim"] for u in units if u["tagoloCim"] or u["alcim"]}),
                     "fejezet": len({u["fejezet"] for u in units if u["fejezet"]})}
    (NJT / "njt_egysegek.jsonl").write_text("".join(json.dumps(u, ensure_ascii=False) + "\n" for u in out), encoding="utf-8")
    (NJT / "njt_egysegek_riport.json").write_text(json.dumps(stat, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(out), "egység; § nélkül:", sum(v["szakasz_nelkul"] for v in stat.values()))


if __name__ == "__main__":
    {"letolt": letolt, "feldolgoz": feldolgoz}[sys.argv[1]]()
