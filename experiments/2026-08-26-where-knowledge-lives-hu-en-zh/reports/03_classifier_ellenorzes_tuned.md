# Nyelvosztályozó — mért pontosság (tuned lens)

**100 véletlen token** (seed 0) a tuned lens top-20-jából, kétszeres értékeléssel (gépi osztályozó + Claude másodvélemény, nem emberi ellenőrző bírálat). Egyetértés: **90/100 = 90%**.

**Az `en` osztály precíziója:** a mintában 32 tokent jelölt a gép angolnak, ebből 8 nem angol szó → precízió **75%**. A `hu` osztály: 2 jelölt, 1 téves, 1 elmaradt találat.

## Az eltérések és a mintázatuk

| token | gépi | helyes | miért |
|---|---|---|---|
| `-ra` | en | **ismeretlen** | ⚠️ magyar RAG (-ra), az angol szótár miatt angolnak számolva |
| ` Er` | en | **ismeretlen** | kétbetűs töredék |
| `nev` | en | **ismeretlen** | ⚠️ a magyar „név” ékezet nélküli töredéke, angolnak számolva |
| `v` | en | **ismeretlen** | egybetűs token, nem nyelvi jel |
| `pus` | en | **ismeretlen** | töredék (pl. „campus”, „puszi”), nem angol szó |
| ` Min` | en | **ismeretlen** | töredék vagy kínai átírás (Min-folyó, Fujian), nem angol szó |
| `Fe` | en | **ismeretlen** | töredék / vegyjel |
| ` Shanghai` | en | **ismeretlen** | kínai tulajdonnév latin átírásban — a naiv mintában a „Wei” ugyanígy |
| ` Hab` | hu | **ismeretlen** | a „hab” szótári szó, itt tulajdonnév-töredék (Habsburg) |
| ` Vér` | ékezetes? | **hu** | valódi magyar szó (vér), a nagy kezdőbetű miatt nem találta a szótárban |

⛔ **A hibák egy irányba mutatnak: rövid latin betűs töredék vagy tulajdonnév → `en`** (8 a 10 hibából). Ez pont az a zaj, amire a runbook figyelmeztetett („az angol–magyar közös tokenek zajt adnak”) — a mérés ezt számszerűsíti.

**Következmény:** a `hu`/`en` megkülönböztetés SZAVAKRA megbízható, TÖREDÉKEKRE nem. A nyelvi arány-görbét csak a `közös`+`ismeretlen` sávval együtt szabad olvasni, és az „angol arány” számokat a fenti precízióval korrigálva (75% szorzó) érdemes alsó becslésként is közölni. A CJK-detektálás (zh) Unicode-alapú és a mintában **hibátlan**.

