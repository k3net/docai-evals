# K01F4 eredménylap (01-runbook v1, 6. és 8. pont)

A számok a teszten; τ@95 és a temperature a val-on rögzítve (n(val) = 3524, n(teszt) = 10013). Az L1★ temperature-e 1,370; az L3-é seedenként s1 0,797, s2 0,818, s3 0,817. Bootstrap: 10000 ismétlés, seed × klaszter, a val minden replikában újramintázva és τ újraválasztva. Generálta: `kor01/eszkozok/f4_riport01.py`.

**Definíciók.** Besorolási lef@95: a pontozott itemek aránya, amelyeket a kar a τ@95 fölött eszközhöz rendel (zárójelben a plafonhoz mért arány; a plafon a réteg pontozott nem-X aránya). Elért precizitás: a helyes eszköz aránya a besoroltak közt; ⚠ = precizitás-bukás (< 0,93). X-prec: a kar X-válaszai közül hány X-gold; X-fedés: az X-gold itemek közül hánynál X a kar top-válasza (τ-független, a H5 definíciója). Az AURC a kar saját nem-X döntéseinek görbéjén számolódik (a 00 definíciója); a közös lefedettségre vágott változat a leíró bontásokban.

## Rétegek

**H1-pool** — n = 7639, pontozott 7561, plafon 0,669

| kar | besorolási lef@95 (/plafon) | elért precizitás | AURC | ECE | X-prec / X-fedés | pontosság |
|---|---|---|---|---|---|---|
| L0 | 0,684 (1,02) | 0,893 ⚠ | 0,0333 | 0,056 | 0,912 / 0,762 | 0,883 |
| L1★ (perm. átlag + temperature) | 0,717 (1,07) | 0,882 ⚠ | 0,0331 | 0,023 | 0,919 / 0,762 | 0,887 |
| L3 (`temp`, 3 seed átlaga) [0,758–0,775] | 0,767 (1,15) | 0,840 ⚠ | 0,0609 | 0,088 | 0,964 / 0,673 | 0,867 |

**T-BFCL-live + When2Call (H2)** — n = 5571, pontozott 5571, plafon 0,657

| kar | besorolási lef@95 (/plafon) | elért precizitás | AURC | ECE | X-prec / X-fedés | pontosság |
|---|---|---|---|---|---|---|
| L0 | 0,678 (1,03) | 0,870 ⚠ | 0,0453 | 0,074 | 0,896 / 0,724 | 0,860 |
| L1★ (perm. átlag + temperature) | 0,718 (1,09) | 0,856 ⚠ | 0,0442 | 0,037 | 0,904 / 0,721 | 0,865 |
| L3 (`temp`, 3 seed átlaga) [0,763–0,781] | 0,773 (1,18) | 0,814 ⚠ | 0,0754 | 0,109 | 0,956 / 0,629 | 0,845 |

**T-hu (H2)** — n = 593, pontozott 553, plafon 0,653

| kar | besorolási lef@95 (/plafon) | elért precizitás | AURC | ECE | X-prec / X-fedés | pontosság |
|---|---|---|---|---|---|---|
| L0 | 0,618 (0,95) | 0,942 | 0,0101 | 0,032 | 0,920 / 0,896 | 0,922 |
| L1★ (perm. átlag + temperature) | 0,640 (0,98) | 0,944 | 0,0059 | 0,051 | 0,916 / 0,906 | 0,926 |
| L3 (`temp`, 3 seed átlaga) [0,682–0,703] | 0,693 (1,06) | 0,915 ⚠ | 0,0156 | 0,032 | 0,980 / 0,858 | 0,934 |

**T-BFCL (leíró)** — n = 839, pontozott 839, plafon 0,714

| kar | besorolási lef@95 (/plafon) | elért precizitás | AURC | ECE | X-prec / X-fedés | pontosság |
|---|---|---|---|---|---|---|
| L0 | 0,747 (1,05) | 0,949 | 0,0198 | 0,026 | 0,995 / 0,858 | 0,958 |
| L1★ (perm. átlag + temperature) | 0,751 (1,05) | 0,946 | 0,0209 | 0,016 | 0,990 / 0,858 | 0,957 |
| L3 (`temp`, 3 seed átlaga) [0,789–0,795] | 0,793 (1,11) | 0,901 ⚠ | 0,0271 | 0,061 | 1,000 / 0,725 | 0,921 |

**T-katalógus (leíró)** — n = 636, pontozott 598, plafon 0,732

| kar | besorolási lef@95 (/plafon) | elért precizitás | AURC | ECE | X-prec / X-fedés | pontosság |
|---|---|---|---|---|---|---|
| L0 | 0,721 (0,98) | 0,977 | 0,0033 | 0,013 | 0,961 / 0,912 | 0,957 |
| L1★ (perm. átlag + temperature) | 0,732 (1,00) | 0,975 | 0,0026 | 0,047 | 0,968 / 0,931 | 0,965 |
| L3 (`temp`, 3 seed átlaga) [0,734–0,764] | 0,751 (1,03) | 0,933 ⚠ | 0,0095 | 0,033 | 0,969 / 0,900 | 0,941 |

**T-új-eszköz (leíró)** — n = 5556, pontozott 5556, plafon 0,682

| kar | besorolási lef@95 (/plafon) | elért precizitás | AURC | ECE | X-prec / X-fedés | pontosság |
|---|---|---|---|---|---|---|
| L0 | 0,702 (1,03) | 0,884 ⚠ | 0,0388 | 0,066 | 0,902 / 0,731 | 0,873 |
| L1★ (perm. átlag + temperature) | 0,736 (1,08) | 0,873 ⚠ | 0,0387 | 0,031 | 0,908 / 0,728 | 0,877 |
| L3 (`temp`, 3 seed átlaga) [0,785–0,801] | 0,793 (1,16) | 0,826 ⚠ | 0,0693 | 0,103 | 0,956 / 0,617 | 0,851 |

**L0n (natív tool calling), H1-pool:** hívásarány 0,674, a hívások precizitása 0,850, X-fedés 0,735, ismeretlen eszköznév 1.

## Hipotézisek

| hipotézis | ítélet | részletek |
|---|---|---|
| H1 (L3 vs. L1★, pool, Holm) | **cáfolt** | lef@95: Δ = 4,9 pont [3,6; 6,6], p < 0,0001; cáfolat: seed s1: precizitás-bukás a poolon; seed s2: precizitás-bukás a poolon; seed s3: precizitás-bukás a poolon. AURC: Δ = 0,0279 [0,0219; 0,0340], p < 0,0001; cáfolat: az L1★ javára mutat; seed s1: pontbecslés ≥ L1★; seed s2: pontbecslés ≥ L1★; seed s3: pontbecslés ≥ L1★ |
| H2 — T-BFCL-live+W2C | **általánosít** | lef@95: Δ = 5,3 pont [3,9; 7,4], p < 0,0001; AURC (másodlagos): Δ = 0,0312 [0,0246; 0,0380], p < 0,0001 |
| H2 — T-hu | **általánosít** | lef@95: Δ = 5,1 pont [2,6; 7,8], p = 0,0002; AURC (másodlagos): Δ = 0,0096 [0,0034; 0,0174], p = 0,0012 |
| H3 (L3 vs. L0n, az L0n munkapontján) | **igaz** | (i) precizitás az L0n lefedettségén: Δ = 3,4 pont [2,4; 4,3], p < 0,0001; (ii) lefedettség az L0n precizitásán: Δ = 7,4 pont [5,7; 8,7], p < 0,0001; X-fedés (L3 − L0n, leíró): Δ = -6,3 pont [-9,1; -3,4], p < 0,0001 |
| H4 (két adapter egy példányon) | **igaz** | L3_soros: egyezés 0,9932, zaj-alap 0,9935, Δ alsó95 -0,26 pont; L3_par16: egyezés 0,9926, zaj-alap 0,9935, Δ alsó95 -0,29 pont; BA_soros: egyezés 0,9821, zaj-alap 0,9821, Δ alsó95 -0,70 pont; BA_par16: egyezés 0,9841, zaj-alap 0,9821, Δ alsó95 -0,30 pont |
| H5 (nincs irrelevancia-kompromisszum) | **cáfolt** | X-fedés: Δ = -8,9 pont [-11,4; -6,3], p < 0,0001 (küszöb: alsó > −2 pont); nem-X pontosság: Δ = 1,4 pont [0,6; 2,2], p = 0,0004 |

**Leíró rétegek (Δ lef@95, L3 − L1★):** T-BFCL: Δ = 4,2 pont [2,9; 5,6], p < 0,0001 (általánosít); T-katalogus: Δ = 1,7 pont [-0,6; 4,0], p = 0,1532 (nem eldönthető); T-uj-eszkoz: Δ = 5,5 pont [4,1; 7,4], p < 0,0001 (általánosít); T-hu-dedup: Δ = 5,4 pont [2,7; 8,2], p < 0,0001 (általánosít); T-hu-maradek: Δ = 5,4 pont [3,7; 7,8], p < 0,0001 (általánosít); T-BFCL-live: Δ = 6,1 pont [4,5; 7,9], p < 0,0001 (általánosít); T-When2Call: Δ = 4,8 pont [3,3; 7,4], p < 0,0001 (általánosít).

**Másodlagos (pool):** lef@90 Δ = 4,3 pont [3,3; 5,4], p < 0,0001; X-arány-standardizált lef@95: 25% X Δ = 4,3 pont [3,1; 5,9], p < 0,0001, 10% X Δ = 3,2 pont [2,2; 4,7], p < 0,0001; ECE Δ = 0,063 [0,055; 0,071], p < 0,0001.

## Publikálási szabály (01-runbook 8. pont)

A H1 cáfolt, ezért a „H1 bukik” sor érvényes: az adatkészlet publikus, az adapter nem, a tanulmány „a kalibrált logit elég” negatív eredményként publikálható.

## Zaj és motor

- **Ismétlési zaj (L0 ↔ L0′, ugyanazon a példányon):** top-címke billenés 0,0044, átl. |Δp| 0,0013 (max 0,669), lef@95-különbség rögzített τ-val 0,0005.
- **Permutációs billenés a poolon** (a 4 sorrend közt változik a döntött opció): L3 s1 0,039, bázis 0,070.
- **Motor-hűség (val, perm 0, HF ↔ vLLM top-1 egyezés):** s1 0,9932, s2 0,9935, s3 0,9949.
- **McNemar a poolon (L3 vs. L1★, top-1 helyes):** L3_s1: csak L1★ jó 198, csak L3 jó 339; L3_s2: csak L1★ jó 198, csak L3 jó 400; L3_s3: csak L1★ jó 207, csak L3 jó 319.

## L3→S2 (leíró)

τ@95 = 0,339 (L3 s1). A τ alatti pool-itemek (1743) a bázis gondolkodó módjához mennek: válaszolt 1726, ebből eszközhöz rendelt 91 (precizitás 0,231); késleltetés mediánja 19,6 s. Együtt: lefedettség 0,782, precizitás 0,831, X-fedés 0,643.
Bontás (gold → S2-válasz): X->X 1596, X->nincs 14, X->rossz 69, nemX->X 39, nemX->jo 21, nemX->nincs 3, nemX->rossz 1.

## Leíró bontások (utólagos, F4 után; ítéletet nem változtatnak)

**BFCL és When2Call forrásonként.** X-itemeken: X-fedés / az @95 eszközhöz rendelt X-arány; nem-X itemeken: lef@95 / precizitás@95. L0n: X-itemen a hívás nélküli arány, nem-X itemen a helyes hívás aránya.

| forrás | n | L1★ | L3 s1 | L3 s2 | L3 s3 | L0n |
|---|---|---|---|---|---|---|
| bfcl_irrelevance (X) | 240 | 0,858 / 0,142 | 0,717 / 0,283 | 0,721 / 0,279 | 0,738 / 0,263 | 0,887 |
| bfcl_live_irrelevance (X) | 875 | 0,657 / 0,331 | 0,545 / 0,455 | 0,504 / 0,482 | 0,560 / 0,432 | 0,745 |
| bfcl_live_multiple | 1050 | 0,98 / 0,984 | 1,00 / 0,977 | 0,99 / 0,972 | 1,00 / 0,969 | 0,962 |
| bfcl_live_simple | 258 | 0,93 / 1,000 | 0,99 / 1,000 | 1,00 / 1,000 | 0,99 / 1,000 | 0,942 |
| bfcl_multiple | 200 | 0,99 / 1,000 | 1,00 / 1,000 | 1,00 / 1,000 | 1,00 / 1,000 | 0,930 |
| bfcl_simple | 399 | 1,00 / 1,000 | 1,00 / 1,000 | 1,00 / 1,000 | 1,00 / 1,000 | 0,955 |
| w2c_teszt | 2353 | 0,94 / 0,977 | 0,98 / 0,973 | 0,98 / 0,968 | 0,98 / 0,966 | 0,784 |
| w2c_teszt (X) | 1035 | 0,775 / 0,210 | 0,700 / 0,300 | 0,689 / 0,309 | 0,730 / 0,269 | 0,640 |

**T-hu átcímkézett itemjei.** A réteg 593 itemjéből 40-et javított az átnézés (új eszköz vagy X). Karonként: hánynál adja a régi MASSIVE-címkét (ebből a τ@95 fölött), hánynál az újat; a réteg lef@95 / precizitás / AURC értéke teljesen és az átcímkézettek nélkül.

| kar | régi címke (τ fölött) | új címke | teljes | átcímkézettek nélkül |
|---|---|---|---|---|
| L1★ | 8 (7) | 32 | 0,640 / 0,944 / 0,0059 | 0,657 / 0,961 / 0,0028 |
| L3 s1 | 24 (24) | 16 | 0,703 / 0,905 / 0,0182 | 0,698 / 0,964 / 0,0019 |
| L3 s2 | 22 (22) | 17 | 0,693 / 0,911 / 0,0143 | 0,690 / 0,969 / 0,0013 |
| L3 s3 | 18 (18) | 20 | 0,682 / 0,928 / 0,0143 | 0,682 / 0,980 / 0,0011 |

**Kockázat közös lefedettségen.** A görbéket a legrövidebb kar lefedettségéig vágva (AURC@közös), valamint a kockázat 0,5 és 0,6 lefedettségnél.

| réteg | közös lef. | L1★ | L3 s1 | L3 s2 | L3 s3 |
|---|---|---|---|---|---|
| pool | 0,726 | 0,0456 · r@0,5 0,049 · r@0,6 0,070 | 0,0748 · r@0,5 0,077 · r@0,6 0,093 | 0,0777 · r@0,5 0,080 · r@0,6 0,098 | 0,0723 · r@0,5 0,073 · r@0,6 0,089 |
| T-BFCL-live+W2C | 0,727 | 0,0609 · r@0,5 0,066 · r@0,6 0,095 | 0,0926 · r@0,5 0,093 · r@0,6 0,111 | 0,0921 · r@0,5 0,094 · r@0,6 0,118 | 0,0921 · r@0,5 0,091 · r@0,6 0,106 |
| T-hu | 0,656 | 0,0089 · r@0,5 0,007 · r@0,6 0,039 | 0,0216 · r@0,5 0,036 · r@0,6 0,048 | 0,0165 · r@0,5 0,029 · r@0,6 0,048 | 0,0190 · r@0,5 0,033 · r@0,6 0,048 |

**Kétlépcsős (bázis P(X) + L3 eszközválasztás).** A hívjon-e kérdést a bázis (L1★) P(X)-e dönti el, az eszközt az L3; τ@95 a val-on. Rétegenként lef@95 / precizitás / AURC / X-fedés.

| seed | pool | T-BFCL-live+W2C | T-hu |
|---|---|---|---|
| hibrid s1 | 0,726 / 0,873 ⚠ / 0,0354 / 0,762 | 0,726 / 0,847 ⚠ / 0,0449 / 0,720 | 0,664 / 0,932 / 0,0074 / 0,901 |
| hibrid s2 | 0,726 / 0,868 ⚠ / 0,0366 / 0,761 | 0,728 / 0,843 ⚠ / 0,0464 / 0,719 | 0,662 / 0,932 / 0,0060 / 0,901 |
| hibrid s3 | 0,725 / 0,869 ⚠ / 0,0364 / 0,762 | 0,726 / 0,842 ⚠ / 0,0465 / 0,720 | 0,660 / 0,940 / 0,0073 / 0,901 |

## Értelmezés (kézzel írt, 2026-10-09; a fenti leíró bontásokra épül)

### Hol nyer és hol veszít az L3

1. **A val-on, eloszláson belül nyer.** A 3 seed lef@95-je 0,723–0,724 (plafon 0,729), az L1★-é 0,682. Az AURC
   0,0026–0,0035, az L1★-é 0,0059. A seedek szórása 0,0006.
2. **A teszt nem-X itemjein szinte hibátlan.** A BFCL és a When2Call nem-X itemjeinek 98–100%-át sorolja be
   @95-ön, 97–100%-os precizitással. Az L1★ ugyanitt 93–100%-ot sorol be.
3. **A teljes precizitásesés az X-itemekből jön.** Az L3 az irrelevancia-itemek nagyobb részét rendeli magabiztosan
   eszközhöz:
   - BFCL-live irrelevance: 43–48% (L1★: 33%);
   - When2Call „cannot_answer”: 27–31% (L1★: 21%);
   - BFCL irrelevance: 26–28% (L1★: 14%).

   A train 3774 X-iteméből 80% gold-drop: a saját gold-drop és az xlam-irrelevance is a helyes eszköz kivételével
   készül, ugyanarra a kérésre. 20% természetes X: 499 When2Call cannot_answer és 255 MASSIVE-csevegés. Ebből a LoRA
   azt tanulta meg, hogy ha van hasonló eszköz, hívja meg. A When2Call-típusú irrelevanciát kis arányban látta, és
   mégis romlott rajta a bázishoz képest. A BFCL-live és a When2Call irrelevanciája más: valódi kérés, közeli, de nem illő eszközökkel. Ez a Hammer-cikk
   kompromisszuma (H5 cáfolt: X-fedés −8,9 pont).
4. **Nem a görbehossz műterméke.** Az AURC a 00 definíciója szerint a kar saját besorolásain fut, így a többet
   besoroló kar hosszabb görbét kap. Közös lefedettségre vágva is az L3 kockázata a nagyobb: a poolon 0,5-ös
   lefedettségnél 0,073–0,080, az L1★-é 0,049. Az L3 a rossz X-besorolásokat magas bizalommal, a rangsor elejére
   teszi.
5. **A T-hu-n a MASSIVE címkézési szokásait is megtanulta.** A réteg 40 átcímkézett itemjéből az L3 18–24-nél a
   régi MASSIVE-címkét adja, mindet a τ fölött; az L1★ 8-nál. Az átcímkézettek nélkül az L3 a T-hu-n is jobb:
   - precizitás 0,964–0,980 (L1★: 0,961);
   - AURC 0,0011–0,0019 (L1★: 0,0028).

   Ez utólagos részhalmaz, ezért csak magyarázat. Azt mutatja, hogy a kemény címkés tanítás a forrás címkézési
   konvencióit magabiztosan beégeti.
6. **A τ egyik karnál sem viszi át a 95%-ot a tesztre.** Az L1★ a poolon 88%-on, az L0 89%-on áll. A val
   X-eloszlása (xLAM, MASSIVE) nem képviseli a teszt irrelevancia-típusait. Ez a docai-0122 éles küszöbválasztásának
   is tanulsága: τ csak a célforgalom X-eloszlásán választható.
7. **Az S2 nem tudja javítani.** A τ alatti 1743 item 96%-a X-gold, és ezek 95%-ánál a bázis gondolkodó módja
   helyesen X-et mond. Az L3 X-hibái viszont a τ fölött vannak, így az S2 elé sem jutnak.
8. **Ami megáll:**
   - a natív tool callingot az L3 a natív munkapontján veri (H3);
   - a két adapter egy példányon, párhuzamos terhelés mellett is hű marad (H4);
   - a permutációs billenés a bázis 7,0%-áról 3,9%-ra esik.
9. **A H2 definíciójának gyengesége.** A H2 a Δ lef@95-öt ítéli meg precizitási feltétel nélkül, ezért ad
   „általánosít” ítéletet mindkét rétegen, miközben ott az L3 precizitása bukik. Előre rögzített szabályról van szó,
   ezért nem írjuk át. A H1 nélkül azonban nincs rá épülő állítás, és a 03-ban a rétegítélet a precizitási
   feltételhez kötött.

### Összevetés a JEV-27B(-VL)-vel

A forrás a HF-kártya (`autotrust/JEV-27B`, `autotrust/JEV-27B-VL`, olvasva 2026-10-09).

| | JEV-27B(-VL) | 01 |
|---|---|---|
| Mihez hasonlít | a tanárhoz (TypeSafe Jev 1.13): KL ≈ 0,017, top-1 egyezés 95,8%, ECE 0,0009 | a kalibrált bázishoz, ugyanazokkal az opciókkal (L1★) |
| Bázis-összevetés | nincs a kártyán | a H1 maga |
| „Egyik sem” opció | nincs, rögzített opciókészlet | X; a poolban ~33% X |
| Kiértékelés | főleg a 53 tanító-domén kitartott sorai; az Open-Jev OOD-részén a KL 0,017 → 0,104, a top-1 0,942 | más eloszlású teszt (BFCL-live, When2Call, javított T-hu) |
| Mérőszám | pontosság, KL, ECE | lefedettség 95%-os precizitás mellett, AURC |
| Szelektív döntés | „usage pattern, not benchmarked” | elsődleges végpont |
| Tanítóadat | 656 ezer sor; KL a tanár teljes eloszlására (puha cél) | 14,5 ezer kemény címke, ε = 0,05 |
| Kalibráció | típusonkénti temperature a saját eloszlásukból (10 954 sor), T ≈ 1,0 | temperature és τ a val-on (xLAM, MASSIVE), T ≈ 0,8 |
| System 1 → 2 | 0,792 → 0,892 pontosság, 70% System 1-ben | az S2 elé szinte csak X jut; a hibák a τ fölött vannak |

**A két eredmény összefér.**
- Amit a JEV mér (eloszláson belüli hűség és pontosság rögzített opciókészleten), abban a 01 L3 is jó, a val-on
  egyértelműen.
- Amin a 01 elbukott (irrelevancia és szelektív precizitás eloszlásváltás mellett, kalibrált bázissal szemben), azt
  a JEV-kártya nem méri.

**F5b: a JEV mérve ugyanezen a kérdésen.** Forrás: `autotrust/jev-decision-index-results`, a gold a kit rögzített
forrásaiból újraépítve. A JEV közölt pontosságai mindkét sávon, mindhárom modellnél pontosan visszajönnek. Eredmények:
`eredmenyek/F5b/f5b_jev.json`, szkript: `kor01/eszkozok/f5b_jev.py`. A JEV-9B és a JEV-27B ezeket a benchmarkokat nem
látta. A JEV-Gemma4 a train-splitjükön is tanult, és a 01 L3 is a When2Call-trainen (1999 item: 1500
request_for_info, 499 cannot_answer), ezért a When2Call-on ez a kettő nem kitartott.

- **When2Call, a 01 tesztjének ugyanazon itemjein** (1293 tool_call és 1035 cannot_answer).
  - Kérdés: hív-e eszközt a modell. A 01 karjainál P(hív) = 1 − P(X), a JEV-nél P(tool_call).

    | kar | AUROC | hamis hívás 90% helyes hívásnál | 95%-nál | hívás a cannot_answer itemeken (top-1) |
    |---|---|---|---|---|
    | L1★ | **0,964** | **8,6%** | **14,1%** | 22,5% |
    | L3 s1–s3 | 0,945–0,959 | 9,5–11,7% | 15,7–17,3% | 27–31% |
    | JEV-9B | 0,953 | 10,4% | 33,4% | 24,3% |
    | JEV-27B | 0,949 | 9,7% | 37,3% | 6,2% |
    | JEV-Gemma4 | 0,943 | 15,1% | 35,7% | 12,0% |

  - A JEV-27B alacsony hívásaránya óvatosabb munkapont, nem jobb szétválasztás: a jó tool_call itemeken is csak 87%-ban
    hív (a 01 karjai 97–99%).
  - Küszöbtől függetlenül a puha célú JEV-27B (a When2Call-t nem látta) sem választja szét jobban a „hívni kell” és a
    „nincs illő eszköz” eseteket, mint a kemény címkés L3 (látta), és mindkettő elmarad a kalibrált bázistól. A
    When2Call-trainen tanult két modell (L3, JEV-Gemma4) sem éri el a bázist.
  - A keretek eltérnek: a JEV négy válaszmód közül választ, a 01 eszközlistából és X-ből. Az itemek azonosak.
- **CLINC150+OOS** (4500 hatókörön belüli és 1000 hatókörön kívüli kérés). Az OOS-felismerés a top-1 alapján:
  - JEV-9B: 21%;
  - JEV-27B: 38%, miközben a hatókörön belüli pontossága 89%;
  - JEV-Gemma4 (az OOS-t is tanulta): 67%.

  95%-os precizitáshoz (keresztillesztett τ) a JEV-27B a kérések 49%-át sorolja be, a plafon 82%.
- **Következtetés:** a puha cél önmagában nem védi ki az irrelevancia-csapdát. Az X-típus tanítása segíthet (a
  CLINC-OOS-on a JEV-Gemma4 38 → 67%), de a When2Call-szétválasztásban a rajta tanult modellek közül egyik sem éri el
  a kalibrált bázist.

**A különbségek súlya, az F5b után:**
1. **Az X-típus lefedése a trainben** a legvalószínűbb kar, de nem elégséges. A JEV-27B a nem látott X-típuson
   (CLINC-OOS, When2Call) ugyanúgy gyenge, mint a 01 L3. A tanítás a CLINC-on javított, a When2Call-on a 13%-os
   train-X arány (01 L3) és a teljes train-split (JEV-Gemma4) sem hozta a bázis szintjére.
2. **Puha célok kemény címke helyett.** Az irrelevancián az F5b szerint nem segít. A konvenció-beégést (5. pont)
   csökkentheti, ez nem mért; a 03 H6-ja méri.
3. **A kalibrációs minta a saját eloszlásukból jön.** A 01-ben a val X-eloszlása eltér a tesztétől (6. pont).
4. **Méret és változatosság:** 53 domén és 656 ezer sor, a 01-ben két forrás és 14,5 ezer sor. Az X-csapdát ez sem
   oldotta meg.

A 24 slotos `lm_head`-fej és a template nélküli prompt nem mutat érdemi különbséget; erre nincs bizonyítékunk egyik
irányba sem.

**Kétlépcsős próba** (utólagos, a fenti táblában). Ha a hívjon-e kérdést a bázis dönti el és az eszközt az L3, az X-fedés
visszajön a bázis szintjére (0,762). A lefedettség viszont csak ~1 ponttal nő (0,726 vs. 0,717), és a val-τ
precizitása így is bukik. A 01 feladaton a döntési fej értéke az X-kezelésben lett volna; az eszközválasztásban a bázis
már eleve szinte hibátlan.

### Következmények a 03-ra (03-runbook v0.2)

- **Valódi irrelevancia a trainben**, nem csak gold-drop, nagyobb arányban. Az F5b szerint ez a legvalószínűbb kar,
  de egyedül nem bizonyítottan elég.
- **Horgony a bázishoz az X-viselkedésre** (KL a bázis eloszlására). Az F5b ezt alátámasztja: a hívás/nem hívás
  szétválasztásában a kalibrált bázis a legjobb.
- **Puha célok Apache-2.0 tanártól** (Mistral Small 4, Gemma 4 26B-A4B-it, Qwen3.6 gondolkodó mód). Az irrelevanciára
  az F5b szerint önmagukban nem elegendők; a konvenció-beégés ellen a H6 méri őket.
- **A kalibrációs minta a célpiaci eloszlásból.**
- **A rétegítélet a precizitási feltételhez kötött.**
