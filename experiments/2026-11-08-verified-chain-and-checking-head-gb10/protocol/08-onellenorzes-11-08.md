# 08 — önellenőrzés a beszámoló előtt (2026-11-08, Dani kérésére)

Cél: a módszertan és a közölt számok átnézése kritikus hiba után kutatva, a beszámoló megírása előtt. Kritikus hibát nem találtam. Az alábbi nem kritikus megállapítások és korlátok a beszámolóba kerülnek.

## Ellenőrzött tételek

| mit | hogyan | eredmény |
|---|---|---|
| a rögzítések sértetlensége | `rogzit08`, `j08`, `m08`, `n08 ellenoriz` | zöld (a D12 a spark-deven, a K08N kapujában; helyben a cache-fájl hiánya miatt nem fut) |
| az N minimális párok szerkezete | 348 egység: egy (a'') + egy (b''), azonos opciók, összeg, forma, hely, pár, nyelv; a (b'') goldja = a G2 (b) goldja; az (a'') gold nélkül, Y | 0 hiba |
| a G és F függelék számai | 30 szám a `g5_k1.json`, `szoveg.json`, `utolagos.json`, `illesztes.json` ellen | mind egyezik |
| a bootstrap klaszterezése az N-ben | a rögzített elemző a forgatókönyvet veszi klaszternek (33), de a párok tagjai megosztják a mondatokat; érzékenység: a klaszter a forgatókönyv-pár (17) | Δ 0,075 [0,021; 0,148], az olvasat ugyanaz („javít érdemben”); `kor08/eredmenyek/N/erzekenyseg_parklaszter/` |
| mit mér a K1(a'') | az (a'')-ben az alany 183-szor a J(f') sugallta gold-kategóriát, 139-szer a csalit választja; a fej mindkét részesetet elválasztja a (b'') helyes döntéseitől (gold-kategória: L-RN 0,844 / L-S 0,760; csali: 0,906 / 0,844) | a fej nem csak a rossz kategóriát ismeri fel, hanem azt is, hogy a döntő mondat nem a kért összegről szól |
| a K08V értékelő | a 07B pontszámain visszaadja a 07B számait (139 / 38 / 15, AUROC 0,933) | rendben |
| a J K2 és a G5 K2 számai | a lapok a gépi JSON-okból; a G5 56 száma 11-05-én visszaellenőrizve | rendben |

## Nem kritikus megállapítások (a beszámolóba kerülnek)

1. **Egymás utáni próbák a fejen (G5 → M → N).** Három mérés ugyanarra a kérdésre; a kockázat, hogy addig mértünk, amíg pozitív lett. Ellene szól: mindhárom olvasat a futás előtt rögzült, minden lépés szigorúbb kontroll volt, nem lazább, és a hatás minden lépésben csökkent (0,186 → 0,144 → 0,075), ahogy a zavaró jegyek kiestek. A beszámoló az N-t adja fő eredménynek, a G5 számát csak történetként.
2. **A szűrő az első címkeellenőrzés hibáiból készült.** Ezért a 30-ból megmaradt 21 egyezés nem bizonyíték; a friss, diszjunkt 30-as kör (0 eltérés) az. A kitöltés gyors volt (kb. 5 perc, tételenként kb. 10 másodperc), és a kulcsfájl ugyanabban a mappában állt, mint a lap. Dani vak kitöltésnek nyilvánította; a lap összetétele (14 / 16) a tervezetből ismert volt. Ez marad a kontroll leggyengébb pontja.
3. **A Holm az N-ben.** A rögzítés egy próbát mondott, az elemző mégis a két fő próbát futtatta Holm-mal; a K1(a) a szigorúbb 97,5%-os szintet kapta, és ott is tart. A 95%-os intervallum a közölt.
4. **A rögzített olvasat 2. feltétele pontbecslés** (L-RN > legjobb szöveges modell): 0,872 a 0,699 ellen, intervallum nélkül. A különbség nagy, de ez így formális feltétel, nem próba.
5. **A K08V τ-ja a 262-n választott,** a modell-lépcsők hibaaránya optimista; fejlesztési szám. A friss 150-es mintán a τ rögzített lesz.
6. **A G5 „nem tartható” és az N „szűkített formában áll” együtt igaz:** a G5 konstrukciója a felszínen is szétválik, az N-é nem. A lap összefoglalója mindkettőt mondja.

## Ami nem változik

A G5, J, M, N rögzített számai és olvasatai; a rögzített fájlok. A lap G függeléke a részesettel és az érzékenységgel bővül (leíró).
