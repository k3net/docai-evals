# Protokollok és jegyzőkönyvek (magyarul; elsődleges források)

A két kör protokollja **a mérés előtt** készült: a hipotézisek, a cáfolati kritériumok, az elsődleges végpontok, a
statisztikai eljárás és a publikálási döntési szabály rögzítve, mielőtt bármelyik kar a tesztet érintette. Ami menet
közben változott, az dátummal és okkal a runbookok **Napló** szakaszában van, a hibákkal együtt.

| fájl | mi ez |
|---|---|
| [00-runbook.md](00-runbook.md) | az 1. kör (számlasor → cikk) protokollja és teljes naplója; rögzítve 2026-10-03, a 00b kiegészítés (16 új szállító) 2026-10-07 |
| [01-runbook.md](01-runbook.md) | a 2. kör (eszközválasztás) protokollja (v1, 2026-10-08) és naplója, az F4 és az F5b (JEV-összevetés) lezárásával |
| [jegyzokonyv/2026-10-08-01-runbook-v0.1.md](jegyzokonyv/2026-10-08-01-runbook-v0.1.md) | a 2. kör protokolljának rögzítés előtti változata, szó szerint (a v1 eltéréseit a 01-runbook Naplója sorolja) |
| [01-F4-ertelmezes.md](01-F4-ertelmezes.md) | a 2. kör eredménylapjának kézzel írt értelmezése: mechanizmus, JEV-összevetés, kétlépcsős próba (utólagos, leíró) |
| [jegyzokonyv/2026-10-03-pilot-megfigyelesek.md](jegyzokonyv/2026-10-03-pilot-megfigyelesek.md) | az 1. kör generátor-pilotjának megfigyelései |
| [jegyzokonyv/2026-10-04-hf-dontesi-datasetek.md](jegyzokonyv/2026-10-04-hf-dontesi-datasetek.md) | a nyilvános döntési és function-calling adatkészletek áttekintése (forrás- és licencválasztás) |

## Ami a runbookokban hivatkozott, de itt nincs

- **A licenc- és szerződésjegyzet** (`jegyzokonyv/2026-10-03-licenc-szerzodes.md`): egy ügyfélszerződésre vonatkozó
  részleteket tartalmaz.
- **Egy termék-backlog jegyzet** (`jegyzokonyv/2026-10-07-docai-0122-jegyzet.md`): belső termékterv.
- **A `_belso/` mappa**: a tenant aggregált profilja, valós minták. Az 1. kör szintetikus adatkészlete ebből a
  profilból készült; a profil nem publikus, a befagyasztott adatkészlet igen.
- **A futási logok** (`jegyzokonyv/spark-logs/`) és a 03-as kör terve.

## Kitakarás

A szövegek a mérés idején íródtak. A publikus másolatban automatikusan kicserélve
(`eszkozok/docai_evals_csomag.py`):

- a tenant neve → `<tenant>`, az adatbázisa → `<tenant-db>`;
- egy ügyfél-azonosító alkategórianév (az 1. kör Naplójában, 2026-10-04) → általános megfogalmazás;
- a termék forráskódjára mutató útvonalak → `<product-code>`, egy belső mérési jegyzőkönyv → `<internal: …>`;
- a mérőgép neve → `measurement-host`, a belső címek és felhasználónevek → `<remote-host>`, `<user>`, `<home>`.

A szám, a dátum és az állítás sehol nem változott.

## Útvonalak

A runbookok a kutatási mappa szerkezetére hivatkoznak. A csomagban:

| a runbookban | itt |
|---|---|
| `eszkozok/` | `code/eszkozok/` |
| `kor01/eszkozok/` | `code/kor01/eszkozok/` |
| `eredmenyek/F4/…`, `eredmenyek/K00b/…` | `results/r00/…` (a kiolvasások: `results/r00/readouts/`) |
| `kor01/eredmenyek/F4/…` | `results/r01/…` (a kiolvasások: `results/r01/readouts/`) |
| `kor01/eredmenyek/F5b/…` | `results/f5b/` |
| `adat/f1`, `adat/k00b/meres` | `dataset/r00/` (a HF-en publikált splitek) |
| `kor01/adat/…`, `kor01/katalogus/` | `dataset/r01/` |
