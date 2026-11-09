# Protokollok és eredménylapok (magyarul; elsődleges források)

Ez a mappa a négy kör magyar protokolljait, naplóit és kézzel írt eredménylapjait tartalmazza. A hipotézisek, a döntési
szabályok, a végpontok és a statisztikai eljárás minden körben **a mérés előtt** rögzültek, hash-elt manifesttel
(`rogzites/`). Ami menet közben változott, az dátummal és okkal a runbookok naplójában van, a hibákkal együtt.

| fájl | mi ez |
|---|---|
| [05-runbook.md](05-runbook.md) | a 05-ös kör runbookja, a teljes naplóval (rögzítés: 2026-10-29 12:41; az 05a negatív eredménye a napló 2026-10-29-i soraiban) |
| [06-runbook.md](06-runbook.md) | a 06-os kör runbookja (rögzítés: 2026-10-31 09:15; az audit két köre, a D18–D22 döntések) |
| [07-runbook.md](07-runbook.md) | a 07-es kör runbookja (rögzítés: 2026-11-01 09:42; K3: 19:45; a 07B naplója) |
| [08-runbook.md](08-runbook.md) | a 08-as kör runbookja (D12: 2026-11-04; J: 11-05; M: 11-06; N: 11-08) |
| [06-F5-eredmenylap.md](06-F5-eredmenylap.md) | a 06 kézzel írt eredménylapja |
| [07-F5-eredmenylap.md](07-F5-eredmenylap.md) | a 07 kézzel írt eredménylapja |
| [07-K3-eredmenylap.md](07-K3-eredmenylap.md) | a K3 (csapdatételek) eredménylapja, a munkaponti és a páros próba kiegészítéssel |
| [08-G5-eredmenylap.md](08-G5-eredmenylap.md) | a 08 G5 eredménylapja, A–G függelékkel (K2, K1, K3, J, felszíni próba, M, N) |
| [08-onellenorzes-11-08.md](08-onellenorzes-11-08.md) | az önellenőrzés a beszámoló előtt: a sorozatos kontrollok, a szűrő, a Holm és a többi nem kritikus megállapítás |
| [rogzites/kor05/v1a/](rogzites/kor05/v1a/) | a 05a rögzítése: `05-runbook-v1a.md` (pillanatkép), `v1a-vazlat.md`, `MANIFEST.sha256`, `ROGZITES.json`, a pecsétmanifestek |
| [rogzites/kor06/v1/](rogzites/kor06/v1/) | a 06 rögzítése |
| [rogzites/kor07/v1/](rogzites/kor07/v1/) | a 07 rögzítése |
| [rogzites/kor07/k3/](rogzites/kor07/k3/) | a K3 rögzítése és nyitása (`NYITAS.json`) |
| [rogzites/kor08/](rogzites/kor08/) | a 08 rögzítései: `G1-rogzites.md` (D12), `J-rogzites.md`, `M-rogzites.md`, `N-rogzites.md`, a manifestek (`D12/`, `J/`, `M/`, `N/`), a G5-nyitás (`G5/NYITAS.json`), a pecsétmanifestek (`pecset/`) |

A gépi eredmények és a hash-fájlok a [../results/](../results/) alatt vannak, az elemzőkód a [../code/](../code/) alatt. Ellenőrzés:
[../code/verify_package.py](../code/verify_package.py).

## Ami a runbookokban hivatkozott, de itt nincs

- **A szintetikus itemek, a generált szövegek, a tételszintű kinyerések, kiolvasások és pontszámok** (`kor0X/adat/`, `cache/`, `*.jsonl`). A kör
  kiolvasásainak és itemfájljainak csak a hash-e szerepel itt, a manifestekben. Ebben a körben nincs Hugging Face-adatkészlet vagy -modell; a
  későbbi tanulmányhoz készül adatkészlet.
- **A `cache/` fa** (fejek, jellemzők, pecsétek): a mérőgépen van, a manifestekben hash-ként hivatkozott bejegyzései itt nem ellenőrizhetők.
- **A címkék és az auditlapok** (`cimkek.json`, `dontesek*.json`, `atnezo*.html`, `kulcs*.json`): valódi adat vagy tételszintű ítélet. Az
  auditok összesítő számai a [../results/audit_osszesito.json](../results/audit_osszesito.json)-ban vannak.
- **A valódi banki adat** (`kor07/adat/b7`), a B0-felmérés (`kor07/eredmenyek/B0/`) és a hozzá tartozó, a tükrökhöz nyúló kód (`b0_felmeres.sh`, `b0_jeloltek.py`,
  `b7_epit.py`, `b7_cimke.py`): tenantadat. A 07B és a K08V eredményei csak aggregátumként, fejlesztési számként szerepelnek
  (`../results/kor07/B7/`, `../results/kor08/V/`).
- **A tételszintű K2-átengedéseket tételesen tartalmazó** `kor08/eredmenyek/G5_utolagos/k2_atengedes.md`: tételszintű kinyerés és pontszám; a G5
  eredménylap A függelékének táblája emiatt kihagyva.
- **A G1 és G2 köztes eredményei** (`kor08/eredmenyek/G1`, `G1b`, `G2`), a 03–04-es körök anyagai és a belső jegyzetek
  (`kor08/publikacio/beszamolo-lanc.hu.md`). A korábbi körök kódjának egy része (`kor03/...`) csak hash-ként szerepel.

## Kitakarás

A szövegek a mérés idején íródtak. Változtatások a közzétett példányokban:

- **Tenantnév:** mindenhol `<tenant>`; felhasználónév: `<user>` (`08-runbook.md`, `code/eszkozok/common.py`).
- **`[kihagyva: ügyféladat]`:** a hozzájáruló tenantok felsorolása, a B0-felmérés eredménybekezdése és egy hozzájárulási megjegyzés a 07-es
  runbook három változatában (`07-runbook.md`, `rogzites/kor07/v1/07-runbook-v1.md`, `rogzites/kor07/k3/07-runbook-k3.md`).
- **A G5 eredménylap A függeléke:** a négy hamis átengedés tételes táblája kihagyva (tételszintű adat; a tételes jegyzék nincs publikálva).
- **Szerkesztői megjegyzés:** a G5 eredménylap egyetlen, a termékspecifikációra vonatkozó mondata mellett (a tulajdonos 2026-11-08-i
  döntése: a lánc állítása szintetikus marad).

Ami a kitakarás miatt nem egyezik a rögzített hash-sel, az a [../code/verify_package.py](../code/verify_package.py) `REDACTED` listájában
szerepel, okkal együtt. A többi publikált, manifestben szereplő fájl bájtra azonos. A mérőgép neve (`spark-dev`) a szövegekben marad.

## Útvonalak

A runbookok és a manifestek a kutatási mappa szerkezetére hivatkoznak. A csomagban:

| a runbookban és a manifestekben | itt |
|---|---|
| `kor05/rogzites/v1a/` stb. | `protocol/rogzites/kor05/v1a/` stb. |
| `kor08/G1-rogzites.md`, `J-`, `M-`, `N-rogzites.md`, `kor08/rogzites/...` | `protocol/rogzites/kor08/...` |
| `kor0X/eredmenyek/...` | `results/kor0X/...` |
| `kor0X/eszkozok/`, `kor06/spec/` | `code/kor0X/eszkozok/`, `code/kor06/spec/` |
| `eszkozok/`, `kor03/eszkozok/` (közös modulok) | `code/eszkozok/`, `code/kor03/eszkozok/` |
| `kor0X/adat/`, `cache/` | nincs a csomagban (ld. fent) |
