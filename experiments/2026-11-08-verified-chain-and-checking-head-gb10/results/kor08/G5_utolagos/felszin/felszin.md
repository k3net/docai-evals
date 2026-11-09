# 08 G5 utólag — a K1(a) felszíni jegyek próbája (leíró)

A szöveges modellek a tanítómintán tanulnak, a sabloncsoportok diszjunktak a teszttől. A halmaz a `g5_k1_08` K1(a)-ja. Az olvasati küszöbök a futás előtt rögzítve (`felszin08.py`).

## szabaly.koltsegelszamolas

Teszt: 453 (a)-SELECT, 1567 (b) helyes SELECT. Tanítóminta: 1980 item (495 (a)), 50 sabloncsoport. A legjobb szöveges modell a CV szerint: karakter.

| pontszám | tanító CV-AUROC | teszt AUROC | 95% |
|---|---|---|---|
| hossz | 0,752 | 0,731 | [0,712; 0,752] |
| szó | 0,975 | 0,987 | [0,982; 0,992] |
| karakter | 0,997 | 1,000 | [1,000; 1,000] |
| L-S | – | 0,738 | [0,647; 0,822] |
| L-RN | – | 0,926 | [0,884; 0,959] |

L-RN − legjobb szöveges: -0,074 [-0,115; -0,041].

**Egységen belül** (1280 pár):

| pontszám | AUROC | 95% |
|---|---|---|
| szó | 0,995 | [0,990; 0,998] |
| karakter | 1,000 | [1,000; 1,000] |
| L-S | 0,773 | [0,671; 0,860] |
| L-RN | 0,927 | [0,864; 0,969] |

**A legjobb szöveges pontszám kvartilisein belül:**

| kvartilis | n | (a) | L-RN | L-S |
|---|---|---|---|---|
| 1 | 505 | 0 | – | – |
| 2 | 505 | 0 | – | – |
| 3 | 505 | 0 | – | – |
| 4 | 505 | 453 | 0,853 | 0,695 |

Az (a) felé húzó szavak: expense claim, ft, írok kérem, expense, eur, 000, 000 ft, claim, expense details, nagy, item, employee, amount, an expense, elszámolását összeg

A (b) felé húzó szavak: our, nem, for the, was, for, on, we, két, három, course, use, számla, díj, charge, cég

## penzugy.bankparositas

Teszt: 54 (a)-SELECT, 182 (b) helyes SELECT. Tanítóminta: 648 item (162 (a)), 33 sabloncsoport. A legjobb szöveges modell a CV szerint: karakter.

| pontszám | tanító CV-AUROC | teszt AUROC | 95% |
|---|---|---|---|
| hossz | 0,673 | 0,802 | [0,732; 0,867] |
| szó | 1,000 | 1,000 | [1,000; 1,000] |
| karakter | 1,000 | 1,000 | [1,000; 1,000] |
| L-S | – | 0,857 | [0,805; 0,904] |
| L-RN | – | 0,994 | [0,984; 1,000] |

L-RN − legjobb szöveges: -0,006 [-0,016; -0,000].

**Egységen belül** (154 pár):

| pontszám | AUROC | 95% |
|---|---|---|
| szó | 1,000 | [1,000; 1,000] |
| karakter | 1,000 | [1,000; 1,000] |
| L-S | 0,857 | [0,805; 0,911] |
| L-RN | 0,987 | [0,960; 1,000] |

**A legjobb szöveges pontszám kvartilisein belül:**

| kvartilis | n | (a) | L-RN | L-S |
|---|---|---|---|---|
| 1 | 59 | 0 | – | – |
| 2 | 59 | 0 | – | – |
| 3 | 59 | 0 | – | – |
| 4 | 59 | 54 | 0,985 | 0,837 |

Az (a) felé húzó szavak: kft számla, settlement, kft ellenőrzött, számla kiegyenlítése, számla, settlement verified, közlemény számla, kiegyenlítése, bt számla, ft számla, kiegyenlítése ellenőrzött, invoice settlement, ltd settlement, kft tétel, details settlement

A (b) felé húzó szavak: of, debt, rendezi, teljesít, alapján, tartozásátvállalási, megállapodás alapján, tartozásátvállalási megállapodás, megállapodás, kezesként, pays, pays as, as, tartozását, kötelezettségéért

## muszaki.hibaelharitas

Teszt: 62 (a)-SELECT, 181 (b) helyes SELECT. Tanítóminta: 360 item (90 (a)), 30 sabloncsoport. A legjobb szöveges modell a CV szerint: szó.

| pontszám | tanító CV-AUROC | teszt AUROC | 95% |
|---|---|---|---|
| hossz | 0,841 | 0,860 | [0,819; 0,903] |
| szó | 1,000 | 1,000 | [1,000; 1,000] |
| karakter | 1,000 | 1,000 | [1,000; 1,000] |
| L-S | – | 0,930 | [0,886; 0,968] |
| L-RN | – | 0,998 | [0,995; 1,000] |

L-RN − legjobb szöveges: -0,002 [-0,005; -0,000].

**Egységen belül** (181 pár):

| pontszám | AUROC | 95% |
|---|---|---|
| szó | 1,000 | [1,000; 1,000] |
| karakter | 1,000 | [1,000; 1,000] |
| L-S | 0,945 | [0,904; 0,978] |
| L-RN | 1,000 | [1,000; 1,000] |

**A legjobb szöveges pontszám kvartilisein belül:**

| kvartilis | n | (a) | L-RN | L-S |
|---|---|---|---|---|
| 1 | 61 | 0 | – | – |
| 2 | 61 | 0 | – | – |
| 3 | 60 | 1 | 1,000 | 0,949 |
| 4 | 61 | 61 | – | – |

Az (a) felé húzó szavak: működik rendesen, nem működik, rendesen, működik, not working, working properly, properly, working, mért, is not, mért értékek, értékek, rendesen kérem, device is, rendesen mért

A (b) felé húzó szavak: and the, reggel, körül, 2025, 08, de, no, morning, kor, után, majd, 09, meg, kapcsolatban, szerint

