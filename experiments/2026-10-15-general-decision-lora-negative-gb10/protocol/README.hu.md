# Protokoll és eredménylap (magyarul; elsődleges források)

A 03-as kör protokollja **a mérés előtt** készült. A hipotézisek, a rétegítéletek szabályai, az elsődleges végpontok,
a statisztikai eljárás, a kitartott rétegek és a célréteg-kalibrációs minták a v1-ben rögzítve vannak (2026-10-14
10:08). Ekkor a G3-karok kitartott (F4) eredményeit és az összehasonlításokat még senki nem nézte meg. Ami menet közben
változott, az dátummal és okkal a runbook **Napló** szakaszában van, a hibákkal együtt.

| fájl | mi ez |
|---|---|
| [v1/03-runbook-v1.md](v1/03-runbook-v1.md) | a rögzített v1 pillanatképe, bájtra az, amit a manifest hash-e lefed |
| [v1/MANIFEST.sha256](v1/MANIFEST.sha256) | a rögzítés manifestje, 32 fájl sha256-ja: az elemzőkód, a runbook-pillanatkép, az itemfájlok, a kalibrációs minták, az MVP v2 és a val-kiolvasások |
| [v1/PECSET-pillanatkep.sha256](v1/PECSET-pillanatkep.sha256) | a lepecsételt kiolvasások pecsétfájlja a rögzítés pillanatában |
| [v1/ROGZITES.txt](v1/ROGZITES.txt) | a rögzítés rekordja: időpont, jóváhagyás, a manifest és az elemzőlánc hash-e |
| [03-runbook.md](03-runbook.md) | a runbook mai állapota, a teljes naplóval (az F4 lezárása, az elemzés, a 2026-10-15-i értelmezés, a kétlépcsős feltáró elemzés és a publikálási döntés) |
| [03-F4-eredmenylap.md](03-F4-eredmenylap.md) | a kézzel írt eredménylap: rétegtáblák, hipotézisek, leíró bontások, értelmezés, kétlépcsős feltáró kiegészítés |

A gépi eredménylap és az elemzés teljes kimenete a [../results/](../results/) alatt van. A rögzítés és a
pecsétlánc ellenőrzése: [../code/verify_package.py](../code/verify_package.py).

## Ami a runbookban hivatkozott, de itt nincs

- **A 04-es kör vázlata** (`04-runbook.md`, v0.1): a terv 2026-10-15 óta parkol, mérés nem indult.
- **A licenc- és szerződésjegyzet** (`jegyzokonyv/2026-10-03-licenc-szerzodes.md`): egy ügyfélszerződésre vonatkozó
  részleteket tartalmaz.
- **Belső munkaanyagok**: az ötletanyag (`magyar-dontesi-tanitoanyag-otletek.md`) és egy külső kutatási összefoglaló
  (`open_datasets_research.md`). A nyilvános adatkészletek 2026-10-04-i áttekintése az előző kör csomagjában van:
  [../../2026-10-09-decision-lora-where-to-train-gb10/protocol/jegyzokonyv/2026-10-04-hf-dontesi-datasetek.md](../../2026-10-09-decision-lora-where-to-train-gb10/protocol/jegyzokonyv/2026-10-04-hf-dontesi-datasetek.md).
- **Az itemenkénti kiolvasások** (`kor03/eredmenyek/F2|F3|F4/**/*.jsonl`), az itemfájlok (`kor03/adat/`), a pótolt
  (id, perm) párok listája (`potolt_parok.jsonl`) és a futási logok. A kiolvasásoknak csak a sha256-ja szerepel itt
  (`results/PECSET.sha256`, `results/V1-MANIFEST-kiolvasasok.sha256`). A tanító- és a val-split a Hugging Face-en van:
  [k3dani/hu-general-decision-mix](https://huggingface.co/datasets/k3dani/hu-general-decision-mix).

## Kitakarás

A szövegek a mérés idején íródtak, és változatlanok. Egyetlen kivétel a `code/eszkozok/common.py` egy
kommentsora: a mérőgépen használt felhasználónév helyén `<user>` áll, ugyanúgy, mint az előző kör csomagjában. Emiatt
ennek a fájlnak a hash-e nem egyezik a `v1/MANIFEST.sha256` bejegyzésével; a többi publikált, manifestben szereplő
fájl bájtra azonos. A mérőgép neve (`spark-dev`) a szövegekben marad, hogy a rögzített runbook hash-e ellenőrizhető
legyen.

## Útvonalak

A runbook és a manifestek a kutatási mappa szerkezetére hivatkoznak. A csomagban:

| a runbookban és a manifestekben | itt |
|---|---|
| `kor03/rogzites/v1/` | `protocol/v1/` |
| `kor03/eredmenyek/F4/eredmenylap.md` | `protocol/03-F4-eredmenylap.md` |
| `kor03/eredmenyek/F4/*.json`, `*.sha256`, `eredmenylap_gepi.md`, `v1_manifest_ellenorzes.txt` | `results/` |
| `kor03/eszkozok/`, `kor03/spec/` | `code/kor03/eszkozok/`, `code/kor03/spec/` |
| `eszkozok/` (a 00/01 közös moduljai) | `code/eszkozok/` |
| `kor01/eszkozok/keret.py` | `code/kor01/eszkozok/keret.py` |
| `kor03/adat/…`, `adat/…`, `kor01/adat/…` | nincs a csomagban (ld. fent) |
