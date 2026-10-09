"""Az ujjlenyomat-próbahalmaz (50 item) előállítása — kézzel írt mini-katalógusból.

Célja nem a mérés, hanem (1) a vLLM-példány numerika-módjának azonosítása
(ujjlenyomat), (2) a K0a/K0b/K0d környezet-kapuk a pilot-adat előtt. Egyszer
készül, utána soha nem változik; a hash-e a jegyzőkönyvbe kerül.

Futtatás: python3 eszkozok/probe_keszlet.py  → adat/probe50.jsonl
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import EXP, file_sha256, write_jsonl  # noqa: E402

# (id, név, kategória-út, egység, ár Ft) — testvér-klaszterekben
KATALOGUS = [
    ("p01", "Kóla 0,5 l PET", "Ital › Üdítő", "db", 290),
    ("p02", "Kóla Zero 0,5 l PET", "Ital › Üdítő", "db", 290),
    ("p03", "Kóla 1,75 l PET", "Ital › Üdítő", "db", 640),
    ("p04", "Narancslé 100% 1 l", "Ital › Gyümölcslé", "db", 520),
    ("p05", "Almalé 100% 1 l", "Ital › Gyümölcslé", "db", 480),
    ("p06", "Ásványvíz szénsavas 1,5 l", "Ital › Víz", "db", 160),
    ("p07", "Ásványvíz szénsavmentes 1,5 l", "Ital › Víz", "db", 160),
    ("p08", "Tej 2,8% 1 l", "Élelmiszer – növényi, tej › Tejtermék", "db", 390),
    ("p09", "Tej 1,5% 1 l", "Élelmiszer – növényi, tej › Tejtermék", "db", 370),
    ("p10", "Tejföl 20% 330 g", "Élelmiszer – növényi, tej › Tejtermék", "db", 450),
    ("p11", "Trappista sajt tömb", "Élelmiszer – növényi, tej › Sajt", "kg", 3200),
    ("p12", "Edami sajt tömb", "Élelmiszer – növényi, tej › Sajt", "kg", 3100),
    ("p13", "Csirkemell filé friss", "Élelmiszer – hús, hal › Baromfi", "kg", 2400),
    ("p14", "Csirkecomb friss", "Élelmiszer – hús, hal › Baromfi", "kg", 1500),
    ("p15", "Sertéskaraj csont nélkül", "Élelmiszer – hús, hal › Sertés", "kg", 2600),
    ("p16", "Burgonya mosott", "Élelmiszer – növényi, tej › Zöldség", "kg", 290),
    ("p17", "Vöröshagyma", "Élelmiszer – növényi, tej › Zöldség", "kg", 350),
    ("p18", "Liszt BL55 1 kg", "Élelmiszer – feldolgozott › Szárazáru", "kg", 260),
    ("p19", "Kristálycukor 1 kg", "Élelmiszer – feldolgozott › Szárazáru", "kg", 420),
    ("p20", "Napraforgó étolaj 1 l", "Élelmiszer – feldolgozott › Szárazáru", "l", 690),
    ("p21", "Mosogatószer gépi 10 l", "Konyhaüzemi anyag › Tisztítószer", "db", 9800),
    ("p22", "Öblítőszer gépi 5 l", "Konyhaüzemi anyag › Tisztítószer", "db", 6400),
    ("p23", "Alufólia 30 cm × 100 m", "Konyhaüzemi anyag › Csomagolóanyag", "tekercs", 4200),
    ("p24", "Folpack 30 cm × 300 m", "Konyhaüzemi anyag › Csomagolóanyag", "tekercs", 3900),
    ("p25", "Villamosenergia – havi díj", "Energia és közüzem › Villamos energia", "hó", 850000),
    ("p26", "Földgáz – havi díj", "Energia és közüzem › Gáz", "hó", 420000),
    ("p27", "Hulladékszállítás – havi díj", "Szolgáltatás › Hulladék", "hó", 96000),
    ("p28", "Egyéb élelmiszer", "Élelmiszer – feldolgozott › Egyéb", "db", 0),
]

# szállítói írásmód (név, nagybetű?, rövidítő függvény)
SZALLITOK = [
    ("Délibáb Ital Kft.", True),
    ("Zöldmező Nagyker Zrt.", False),
    ("Pannon Konyhatechnika Bt.", True),
    ("Alföldi Tejüzem Kft.", False),
]

ROVIDITES = {
    "Ásványvíz": "ÁSV.VÍZ", "szénsavas": "SZSV", "szénsavmentes": "SZM", "Narancslé": "NARANCSLE",
    "Csirkemell": "CS.MELL", "Csirkecomb": "CS.COMB", "Sertéskaraj": "SERT.KARAJ", "csont nélkül": "CS.N.",
    "Mosogatószer": "MOSOGATÓSZ.", "Öblítőszer": "ÖBLÍTŐ", "Kristálycukor": "KR.CUKOR",
    "Napraforgó étolaj": "NAPR.OLAJ", "Burgonya": "BURGONYA", "mosott": "MOS.",
}


def sor_szoveg(nev: str, nagybetu: bool, rng: random.Random) -> str:
    s = nev
    for k, v in ROVIDITES.items():
        if k in s and rng.random() < 0.7:
            s = s.replace(k, v)
    s = s.replace(" l", "L").replace(",", ".") if rng.random() < 0.5 else s
    if rng.random() < 0.4:
        s += rng.choice([" 6/KRT", " 12/KRT", " /DB", " (GYŰJTŐ)"])
    return s.upper() if nagybetu else s


def main() -> None:
    rng = random.Random(20261003)
    by_root: dict[str, list] = {}
    for c in KATALOGUS:
        by_root.setdefault(c[2].split(" › ")[0], []).append(c)
    items = []
    for i in range(50):
        gold = KATALOGUS[i % 27]  # a gyűjtőcikk (p28) csak jelölt lehet
        szall, nagy = SZALLITOK[i % len(SZALLITOK)]
        root = gold[2].split(" › ")[0]
        mas = [c for c in KATALOGUS if c[0] != gold[0]]
        rokon = [c for c in by_root[root] if c[0] != gold[0]]
        n_opt = rng.randint(5, 8)
        jeloltek = rokon[: n_opt - 1]
        jeloltek += rng.sample([c for c in mas if c not in jeloltek], n_opt - 1 - len(jeloltek))
        x_item = i % 4 == 3  # ~25% „egyik sem”: a gold kiesik, a helyére egy további jelölt
        opts = jeloltek + ([rng.choice([c for c in mas if c not in jeloltek])] if x_item else [gold])
        rng.shuffle(opts)
        menny = rng.choice([1, 2, 6, 12, 24]) if gold[3] == "db" else rng.choice([1, 5, 10, 25])
        items.append({
            "id": f"probe-{i:02d}",
            "split": "probe",
            "task": "ba_cikk",
            "context": {
                "sor": sor_szoveg(gold[1], nagy, rng),
                "szallito": szall,
                "mennyiseg": str(menny),
                "egyseg": gold[3],
                "egysegar": f"{gold[4]:,}".replace(",", " "),
            },
            "options": [{"id": c[0], "text": c[1], "path": c[2]} for c in opts],
            "gold": None if x_item else gold[0],
            "meta": {"valodi_cikk": gold[0], "x_fajta": "a" if x_item else None},
        })
    out = EXP / "adat/probe50.jsonl"
    write_jsonl(out, items)
    print(f"{out}: {len(items)} item, sha256={file_sha256(out)}")


if __name__ == "__main__":
    main()
