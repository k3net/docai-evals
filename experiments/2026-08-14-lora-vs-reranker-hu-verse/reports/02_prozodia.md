# F0.3 — A prozódiai mérőeszköz validálása

A modul: `src/hu_prosody.py`. Egyetlen modellhívás sincs benne — ugyanez a kód annotálja a korpuszt és értékeli az F4 generálásait.

## A — Szótagszámláló külső igazsághoz mérve

| mű | elvárt | sor | pontos találat | ±1 szótagon belül | medián |
|---|---:|---:|---:|---:|---:|
| felező tizenkettes (TOLDI:, TOLDI ESTÉJE:, JÁNOS VITÉZ) | 12 | 4,125 | 99.7% | 99.8% | 12 |

**A teljes korpusz szótagszám-eloszlása** (80,193 sor): 12: 38.3%, 8: 16.9%, 10: 13.0%, 6: 6.2%, 11: 5.5%, 9: 5.4%. Medián 11, átlag 10.2.

## B — Rímdetektor kontrollcsoporthoz mérve

### B/a — A pontozó változatai (abláció)

| pontozó | küszöb | Arany (1–2, 3–4) | Petőfi (2–4) | kontroll | **rés** |
|---|---:|---:|---:|---:|---:|
| **v1** additív, coda opcionális *(ez fut)* | 0.6 | 85.4% | 64.7% | 10.1% | **+64.9%** |
| **v1** additív, coda opcionális *(ez fut)* | 0.8 | 77.7% | 50.5% | 4.2% | **+59.9%** |
| v2 — coda kötelező | 0.6 | 79.2% | 57.1% | 5.7% | **+62.5%** |
| v2 — coda kötelező | 0.8 | 77.7% | 50.5% | 4.2% | **+59.9%** |
| v3 — csak magánhangzó | 0.6 | 87.4% | 72.4% | 21.1% | **+58.8%** |
| v3 — csak magánhangzó | 0.8 | 75.9% | 40.9% | 6.0% | **+52.4%** |

A v1 adja a legnagyobb rést 0,6-nál, ezért ez fut. Ára megnevezhető: a coda-egyezés hiányát két magánhangzó-egyezés kiválthatja, így az „isten / kell” párt rímnek látja (0,6). A v2 ezt kiszűrné, de vele esne Petőfi valódi „svábság / adósságát” ríme is — a mérés szerint többet veszítenénk, mint nyernénk.

### B/b — Melyik sorpár rímel a négysoros strófákban?

| szerző | négysoros strófa | 1–2 | 1–3 | 1–4 | 2–3 | 2–4 | 3–4 | **kontroll** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Arany János | 3,481 | 86.0% | 14.4% | 11.5% | 10.5% | 21.0% | 84.8% | 10.9% |
| Petőfi Sándor | 3,350 | 35.6% | 15.1% | 10.9% | 10.5% | 64.7% | 34.9% | 9.9% |

A **kontroll** oszlop ugyanazokból a sorokból, de eltérő strófákból párosít — a szókincs és a szerző azonos, csak a rímszándék hiányzik. A valódi rímpozíciók és a kontroll közti rés a detektor jele.

### B/c — Küszöbválasztás

| küszöb | valódi rímpozíció (2–4 és 3–4) | kontroll | rés |
|---:|---:|---:|---:|
| 0.4 | 98.4% | 29.5% | **+68.9%** |
| 0.6 | 93.5% | 10.0% | **+83.5%** |
| 0.8 | 81.3% | 3.9% | **+77.4%** |
| 1.0 | 58.6% | 1.1% | **+57.5%** |

### B/d — Rímséma-eloszlás a négysoros strófákban

| szerző | küszöb | `AABB` | `ABAB` | `ABCB` | `AABA` | `ABCD` | `AAAA` | egyéb |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Arany János | 0.6 (asszonánc) | 72.1% | 4.4% | 5.3% | 2.0% | 1.0% | 10.0% | 5.2% |
| Arany János | 0.8 (tiszta rím) | 63.4% | 3.4% | 5.7% | 1.4% | 3.1% | 5.4% | 17.6% |
| Petőfi Sándor | 0.6 (asszonánc) | 23.1% | 8.3% | 42.2% | 4.4% | 4.4% | 5.7% | 11.9% |
| Petőfi Sándor | 0.8 (tiszta rím) | 18.5% | 5.1% | 40.7% | 1.3% | 17.2% | 2.1% | 15.1% |

`ABCB` = félrím (csak a páros sorok rímelnek) — a magyar népies vers alapformája, nem detektálási hiba. `ABCD` = a detektor egyetlen rímet sem talált: ide gyűlik a hibák nagy része, ezért ezt nézzük kézzel.

## C — Kézi ellenőrzésre kiválasztott minta (F0-gate)

Rögzített seed (20260814), 20 vers. A teljes szöveg: `reports/02_prozodia_minta.md`.

