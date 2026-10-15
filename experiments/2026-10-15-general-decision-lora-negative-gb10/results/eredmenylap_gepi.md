# 03 F4 — gépi eredménylap (v1)

Bootstrap: 10000 ismétlés, seed 0. Minden előre rögzített hipotézis szerepel, a negatív és a nem eldönthető eredmény is. Az értelmezés külön, kézzel írt szakaszba kerül.

## H1 — G3 vs. L1★

| réteg | ítélet | G3 prec. (átlag) | Δlef@95 [CI] | p | ΔAURC [CI] | p | L0′−L1★ lef |
|---|---|---|---|---|---|---|---|
| ho-termek | **nem teljesíti a követelményeket** | 0,912 | 0,111 [0,069; 0,161] | 0,0000 | 0,0137 [0,0017; 0,0269] | 0,0164 | 0,001 |
| ho-routing | **nem teljesíti a követelményeket** | 0,866 | 0,089 [0,067; 0,113] | 0,0000 | 0,0471 [0,0388; 0,0573] | 0,0000 | 0,000 |
| ho-uj | **nem teljesíti a követelményeket** | 0,905 | 0,072 [0,037; 0,110] | 0,0000 | −0,0272 [−0,0331; −0,0216] | 0,0000 | −0,000 |

- ho-termek: precizitás 0.9117 < 0.93; aurc: szignifikáns a kar ellen
- ho-routing: precizitás 0.8656 < 0.93; aurc: szignifikáns a kar ellen
- ho-uj: precizitás 0.9052 < 0.93

Általánosít: egyik rétegen sem. Egyetlen sikeres réteg alapján nem állítható minden feladatcsaládra általánosítás.

Seedenként (pontbecslés, val-τ):

| réteg | seed | lef@95 | prec. | AURC | Δlef [CI] | ΔAURC [CI] |
|---|---|---|---|---|---|---|
| ho-termek | k03v2_g3_s1 | 0,744 | 0,924 | 0,0431 | 0,092 [0,058; 0,140] | 0,0135 [0,0093; 0,0184] |
| ho-termek | k03v2_g3_s2 | 0,794 | 0,878 | 0,0564 | 0,141 [0,107; 0,187] | 0,0268 [0,0210; 0,0331] |
| ho-termek | k03v2_g3_s3 | 0,744 | 0,933 | 0,0306 | 0,092 [0,060; 0,137] | 0,0011 [−0,0017; 0,0041] |
| ho-routing | k03v2_g3_s1 | 0,732 | 0,861 | 0,0780 | 0,088 [0,061; 0,120] | 0,0437 [0,0381; 0,0493] |
| ho-routing | k03v2_g3_s2 | 0,733 | 0,870 | 0,0902 | 0,089 [0,070; 0,115] | 0,0559 [0,0485; 0,0632] |
| ho-routing | k03v2_g3_s3 | 0,730 | 0,867 | 0,0766 | 0,086 [0,065; 0,110] | 0,0423 [0,0363; 0,0486] |
| ho-uj | k03v2_g3_s1 | 0,620 | 0,916 | 0,0438 | 0,052 [0,027; 0,089] | −0,0279 [−0,0339; −0,0220] |
| ho-uj | k03v2_g3_s2 | 0,661 | 0,892 | 0,0432 | 0,093 [0,063; 0,133] | −0,0285 [−0,0343; −0,0229] |
| ho-uj | k03v2_g3_s3 | 0,627 | 0,908 | 0,0463 | 0,059 [0,032; 0,095] | −0,0253 [−0,0309; −0,0198] |

## H2 — a specifikus LoRA-hoz mérve

| réteg | ítélet | L3−L1★ [CI] | D [CI] | nyereségarány (leíró) [CI] |
|---|---|---|---|---|
| ho-termek | **érdemi átvitel** | 0,103 [0,063; 0,153] | 0,057 [0,025; 0,097] | 1,05 [0,73; 1,62] |
| ho-routing | **érdemi átvitel** | 0,124 [0,096; 0,151] | 0,026 [0,007; 0,049] | 0,71 [0,55; 0,94] |

Rétegenkénti 95%-os intervallumok; vizsgálatszintű, többszörösségre korrigált állítás nem következik belőlük.

## H3 — a kalibráció átvihetősége

| réteg | út | ítélet | G3 prec. (átlag) [CI] | NaN-replikák | seedenként prec. / lef / elfogadott (nincs τ) |
|---|---|---|---|---|---|
| ho-termek | (a) | **az előírt toleranciaküszöböt nem teljesítette** | 0,912 [0,875; 0,941] | 0,000 | 0,924 / 0,744 / 3368; 0,878 / 0,794 / 3592; 0,933 / 0,744 / 3367 |
| ho-termek | (b) | **nincs megfelelő τ a kalibrációs mintán: nem siker** | – [0,947; 0,987] | 0,902 | – / 0,000 / 0 (0,655); – / 0,000 / 0 (0,973); – / 0,000 / 0 (0,690) |
| ho-routing | (a) | **az előírt toleranciaküszöböt nem teljesítette** | 0,866 [0,846; 0,882] | 0,000 | 0,861 / 0,732 / 5429; 0,870 / 0,733 / 5435; 0,867 / 0,730 / 5417 |
| ho-routing | (b) | **nincs megfelelő τ a kalibrációs mintán: nem siker** | – [0,888; 0,927] | 0,968 | – / 0,000 / 0 (0,937); – / 0,000 / 0 (0,967); – / 0,000 / 0 (0,915) |
| ho-uj | (a) | **az előírt toleranciaküszöböt nem teljesítette** | 0,905 [0,880; 0,925] | 0,000 | 0,916 / 0,620 / 1364; 0,892 / 0,661 / 1454; 0,908 / 0,627 / 1379 |
| ho-uj | (b) | **az előírt toleranciaküszöböt teljesítette** | 0,975 [0,938; 0,989] | 0,131 | 0,987 / 0,341 / 750 (0,185); 0,976 / 0,523 / 1150 (0,000); 0,962 / 0,520 / 1143 (0,000) |

A ≥ 0,93-as pontbecslés az előírt toleranciaküszöb teljesítése, nem a 95%-os precizitás igazolása. Az intervallumok a val-on választott kiolvasási módra és temperature-re feltételesek.

## H4 — angol gerinc (G3 s1 vs. G3-hu s1, egy seed)

| réteg | ítélet | Δlef@95 [CI] | ΔAURC [CI] |
|---|---|---|---|
| ho-termek | **nem teljesíti a követelményeket** | 0,025 [−0,003; 0,059] | 0,0052 [0,0024; 0,0085] |
| ho-uj | **nem teljesíti a követelményeket** | 0,029 [0,014; 0,054] | −0,0028 [−0,0094; 0,0024] |
| ho-routing-hu | **segít** | 0,006 [−0,016; 0,030] | −0,0026 [−0,0048; −0,0010] |

Az angol adattal bővített tanítás hatása ennél a seednél; a nyelv hatása nem választható el a nagyobb adatmennyiségtől és lépésszámtól.

## H6 — horgony (feltáró)

| réteg | ΔX-fedés G3−L1★ [CI] | CI alsó > −2 pont? | ΔX-fedés kemény−L1★ [CI] | CI alsó > −2 pont? | G3 s1−kemény s1: ΔX-fedés [CI] | ΔAURC [CI] |
|---|---|---|---|---|---|---|
| ho-routing | −0,193 [−0,243; −0,155] | nem | −0,236 [−0,253; −0,219] | nem | −0,011 [−0,022; −0,001] | −0,0064 [−0,0098; −0,0034] |
| ho-termek | −0,076 [−0,138; −0,004] | nem | −0,020 [−0,045; 0,004] | nem | −0,067 [−0,088; −0,046] | 0,0066 [0,0038; 0,0096] |

A G3-nál igazolható és a G3-keménynél nem igazolható non-inferiority önmagában nem bizonyít horgonyhatást.

**X-fedés X-típusonként (leíró, H1 és H6):**

| réteg | X-típus | n | L1★ | G3 (3 seed átlaga) | G3-kemény |
|---|---|---|---|---|---|
| ho-termek | gold-drop | 975 | 0,418 | 0,344 | 0,395 |
| ho-termek | out-of-scope | 128 | 0,391 | 0,310 | 0,398 |
| ho-routing | gold-drop | 271 | 0,959 | 0,903 | 0,904 |
| ho-routing | out-of-scope | 2183 | 0,741 | 0,529 | 0,482 |
| ho-uj | missing-precondition | 215 | 0,498 | 0,575 | 0,470 |
| ho-uj | natural | 91 | 0,011 | 0,835 | 0,945 |

## H5 — eloszláson belül (teszt-ID, leíró)

| család | n | L1★ lef@95 / prec. | G3 lef@95 / prec. (3 seed átlaga) |
|---|---|---|---|
| entitas.egyezes | 107 | 0,692 / 0,973 | 0,798 / 0,992 |
| entitas.nerkor | 4198 | 0,823 / 0,905 | 0,842 / 0,970 |
| jogi.hivatali_ugytipus | 159 | 0,711 / 0,973 | 0,792 / 0,995 |
| jogi.multieurlex | 5000 | 0,458 / 0,776 | 0,693 / 0,682 |
| jogi.njt_cim | 289 | 0,394 / 0,947 | 0,667 / 0,868 |
| jogi.njt_fejezet | 257 | 0,296 / 0,934 | 0,651 / 0,773 |
| jogi.njt_torveny | 303 | 0,630 / 0,948 | 0,718 / 0,907 |
| konstrukcios.wiki_folytatas | 630 | 0,413 / 0,885 | 0,702 / 0,851 |
| konstrukcios.wiki_szakaszcim | 638 | 0,715 / 0,884 | 0,822 / 0,842 |
| kozbeszerzes.ted_cpv | 460 | 0,617 / 0,940 | 0,799 / 0,926 |
| level.dokumentumtipus | 134 | 0,821 / 0,991 | 0,853 / 0,991 |
| level.szerzodesklauzula | 142 | 0,852 / 1,000 | 0,859 / 1,000 |
| level.triage | 108 | 0,796 / 1,000 | 0,880 / 1,000 |
| nli.hucb | 103 | 0,786 / 0,716 | 0,887 / 0,719 |
| nli.hurte | 243 | 0,897 / 0,968 | 0,938 / 0,974 |
| nli.huwnli | 60 | 0,867 / 0,865 | 0,917 / 0,885 |
| nyelv.hucola | 910 | 0,762 / 0,889 | 0,834 / 0,882 |
| qa.hucopa | 100 | 0,870 / 1,000 | 0,957 / 0,993 |
| qa.hurc | 6539 | 0,648 / 0,949 | 0,767 / 0,924 |
| qa.milqa | 998 | 0,598 / 0,936 | 0,610 / 0,938 |
| rag.relevancia | 103 | 0,757 / 0,923 | 0,851 / 0,924 |
| rag.valaszbiralat | 95 | 0,863 / 1,000 | 0,982 / 0,996 |
| szentiment.husst | 1165 | 0,756 / 0,719 | 0,834 / 0,704 |

**H6(c), leíró:** 51 átcímkézett routing-item ({'massive_hu': 44, 'katalogus_hu': 7}); karonként régi címke (τ fölött) / új címke: L1 13 (6) / 38; k03v2_g3_s1 15 (8) / 36; k03v2_g3_s2 15 (10) / 36; k03v2_g3_s3 12 (8) / 38; k03v2_g3kemeny_s1 15 (10) / 36; k03v2_g3hu_s1 17 (12) / 34; k01_l3mixse_p30_s1 28 (28) / 23; k01_l3mixse_p30_s2 29 (29) / 21; k01_l3mixse_p30_s3 26 (26) / 23

## Technikai és érzékenységi blokkok

- ho-routing-tervezet: n = 9638, G3 prec. 0,882, Δlef@95 0,083 [0,060; 0,108], ΔAURC 0,0407 [0,0337; 0,0496]
- ho-routing:potolt: n = 1363, G3 prec. 0,952, Δlef@95 0,055 [0,040; 0,073], ΔAURC 0,0116 [0,0038; 0,0211]
- ho-routing:nem-potolt: n = 6053, G3 prec. 0,842, Δlef@95 0,097 [0,071; 0,124], ΔAURC 0,0676 [0,0567; 0,0803]
- L0′ példányzaj: ho-termek: billenés 0,0230, Δlef 0,001; ho-routing: billenés 0,0115, Δlef 0,000; ho-uj: billenés 0,0345, Δlef −0,000; test-id: billenés 0,0234, Δlef −0,002
- Az L0′ a bázis példányzaját méri; az adapteres kiolvasások példány-stabilitását önmagában nem igazolja.
