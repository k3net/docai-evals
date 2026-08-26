# Nyelvosztályozó — mért pontosság (naiv lens)

**100 véletlen token** (seed 0) a naiv lens top-20-jából, kétszeres értékeléssel (gépi osztályozó + Claude másodvélemény, nem emberi ellenőrző bírálat). Egyetértés: **92/100 = 92%**.

**Az `en` osztály precíziója:** a mintában 17 tokent jelölt a gép angolnak, ebből 4 nem angol szó → precízió **76%**. A `hu` osztály: 2 jelölt, 2 téves, 0 elmaradt találat.

## Az eltérések és a mintázatuk

| token | gépi | helyes | miért |
|---|---|---|---|
| ` Eb` | hu | **ismeretlen** | az „eb” benne van a magyar szótárban, de itt latin betűs TÖREDÉK, nem magyar szó |
| ` telem` | hu | **ismeretlen** | ragozott alakként a szótárban van, tokenként viszont töredék |
| ` Ir` | en | **ismeretlen** | kétbetűs töredék; angol szóként is kétes |
| ` Mir` | en | **ismeretlen** | ⚠️ épp a magyar „Mirr-Murr” töredéke — a HU11 itemnél ANGOLNAK számolná |
| ` Wei` | en | **ismeretlen** | kínai átírás latin betűkkel, nem angol szó |
| ` Jana` | en | **ismeretlen** | tulajdonnév, nem nyelvi jel |
| `*pi` | közös | **egyéb** | kódtöredék, nem szó |
| `	TokenName` | ismeretlen | **egyéb** | kódazonosító, nem természetes nyelv |

⛔ **A hibák egy irányba mutatnak: rövid latin betűs töredék vagy tulajdonnév → `en`** (4 a 8 hibából). Ez pont az a zaj, amire a runbook figyelmeztetett („az angol–magyar közös tokenek zajt adnak”) — a mérés ezt számszerűsíti.

**Következmény:** a `hu`/`en` megkülönböztetés SZAVAKRA megbízható, TÖREDÉKEKRE nem. A nyelvi arány-görbét csak a `közös`+`ismeretlen` sávval együtt szabad olvasni, és az „angol arány” számokat a fenti precízióval korrigálva (76% szorzó) érdemes alsó becslésként is közölni. A CJK-detektálás (zh) Unicode-alapú és a mintában **hibátlan**.

