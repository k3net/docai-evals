# F4 eredménylap (runbook 14. pont)

A számok a teszten; τ és a temperature a val-on rögzítve. Az L3 a három seed átlaga.

## vLLM

n(val) = 1006, n(teszt) = 3534; az L1★ temperature-e 1,337.

**T-belső**

| fok / kar | besorolási lef@95 | elért precizitás | AURC | döntési lef@95 | X-prec / X-fedés | ECE | kétértelmű-átlépés | pozíció-billenés | címketömeg | döntés/s |
|---|---|---|---|---|---|---|---|---|---|---|
| L0 | 0,620 | 0,969 | 0,0337 | 0,634 | 0,775 / 0,333 | 0,058 | 0,410 | 0,232 | 0,998 | 6,4 |
| L1★ (perm. átlag + temperature) | 0,639 | 0,977 | 0,0228 | 0,651 | 0,860 / 0,398 | 0,058 | 0,475 | — | 0,998 | 1,6 |
| L3 (`temp`, 3 seed átlaga; lef@95 [0,772–0,780]) | 0,775 | 0,985 | 0,0014 | 0,999 | 0,971 / 0,968 | 0,014 | 0,852 | 0,051 | 0,988 | 6,2 |

**T-szállító**

| fok / kar | besorolási lef@95 | elért precizitás | AURC | döntési lef@95 | X-prec / X-fedés | ECE | kétértelmű-átlépés | pozíció-billenés | címketömeg | döntés/s |
|---|---|---|---|---|---|---|---|---|---|---|
| L0 | 0,548 | 0,960 | 0,0383 | 0,561 | 0,836 / 0,413 | 0,031 | 0,315 | 0,280 | 0,998 | 6,4 |
| L1★ (perm. átlag + temperature) | 0,572 | 0,981 | 0,0275 | 0,583 | 0,882 / 0,449 | 0,062 | 0,341 | — | 0,998 | 1,6 |
| L3 (`temp`, 3 seed átlaga; lef@95 [0,738–0,758]) | 0,746 | 0,978 | 0,0018 | 1,000 | 0,936 / 0,962 | 0,013 | 0,772 | 0,077 | 0,988 | 6,2 |

**T-közeli**

| fok / kar | besorolási lef@95 | elért precizitás | AURC | döntési lef@95 | X-prec / X-fedés | ECE | kétértelmű-átlépés | pozíció-billenés | címketömeg | döntés/s |
|---|---|---|---|---|---|---|---|---|---|---|
| L0 | 0,636 | 0,924 ⚠ | 0,0545 | 0,650 | 0,873 / 0,293 | 0,096 | 0,286 | 0,238 | 0,998 | 6,4 |
| L1★ (perm. átlag + temperature) | 0,643 | 0,952 | 0,0429 | 0,657 | 0,855 / 0,323 | 0,040 | 0,327 | — | 0,998 | 1,6 |
| L3 (`temp`, 3 seed átlaga; lef@95 [0,745–0,752]) | 0,748 | 0,967 | 0,0035 | 0,999 | 0,938 / 0,927 | 0,019 | 0,793 | 0,068 | 0,989 | 6,2 |

**T-távoli**

| fok / kar | besorolási lef@95 | elért precizitás | AURC | döntési lef@95 | X-prec / X-fedés | ECE | kétértelmű-átlépés | pozíció-billenés | címketömeg | döntés/s |
|---|---|---|---|---|---|---|---|---|---|---|
| L0 | 0,646 | 0,977 | 0,0203 | 0,668 | 0,905 / 0,459 | 0,044 | 0,390 | 0,237 | 0,998 | 6,4 |
| L1★ (perm. átlag + temperature) | 0,666 | 0,988 | 0,0138 | 0,692 | 0,952 / 0,548 | 0,060 | 0,390 | — | 0,998 | 1,6 |
| L3 (`temp`, 3 seed átlaga; lef@95 [0,745–0,766]) | 0,757 | 0,989 | 0,0002 | 0,999 | 0,958 / 0,973 | 0,011 | 0,805 | 0,053 | 0,989 | 6,2 |

**pool**

| fok / kar | besorolási lef@95 | elért precizitás | AURC | döntési lef@95 | X-prec / X-fedés | ECE | kétértelmű-átlépés | pozíció-billenés | címketömeg | döntés/s |
|---|---|---|---|---|---|---|---|---|---|---|
| L0 | 0,596 | 0,957 | 0,0370 | 0,611 | 0,850 / 0,385 | 0,048 | 0,333 | 0,256 | 0,998 | 6,4 |
| L1★ (perm. átlag + temperature) | 0,616 | 0,975 | 0,0273 | 0,630 | 0,891 / 0,434 | 0,043 | 0,362 | — | 0,998 | 1,6 |
| L3 (`temp`, 3 seed átlaga; lef@95 [0,745–0,761]) | 0,752 | 0,979 | 0,0018 | 1,000 | 0,945 / 0,957 | 0,010 | 0,791 | 0,067 | 0,988 | 6,2 |

⚠ = precizitás-bukás (a teszten elért precizitás < 0,93). Az AURC a kar saját nem-X döntéseinek görbéjén számolódik, így a több X-et mondó kar rövidebb görbét kap; a közös lefedettségre vágott változat az önellenőrzés szakaszban. Az L1★ döntés/s-e az L0-é negyede, mert a permutáció-átlag 4 kérés.

### Hipotézisek

| hipotézis | ítélet | részletek |
|---|---|---|
| H1 (L3 vs. L1★, Holm) | **igaz** | @95: Δ = 0,1369 (bootstrap-medián 0,1284), 95% CI [0,0484; 0,2098], p < 0,0001; AURC: Δ = -0,0255 (bootstrap-medián -0,0255), 95% CI [-0,0300; -0,0213], p < 0,0001; @95: megáll; AURC: megáll; másodlagos @90: Δ = -0,0017 (bootstrap-medián 0,0003), 95% CI [-0,0326; 0,0490], p = 0,9888 |
| H2 — T-szallito | **nem tesztelhető** (a számolt ítélet „általánosít”, de a 14 szállító mind szerepel a train-ben — generátorhiba, lásd Napló 2026-10-07; a számok leírók) | @95: Δ = 0,1736 (bootstrap-medián 0,1625), 95% CI [0,0689; 0,2592], p < 0,0001; szállító-permutáció (14 szállító, rögzített val-τ, egzakt): p = 0,00012 |
| H2 — T-kategoria | **általánosít** | @95: Δ = 0,0976 (bootstrap-medián 0,0880), 95% CI [0,0168; 0,1552], p = 0,0046 |
| H2 — T-kozeli | **általánosít** | @95: Δ = 0,1044 (bootstrap-medián 0,0931), 95% CI [0,0147; 0,1631], p = 0,0116 |
| H2 — T-tavoli | **általánosít** | @95: Δ = 0,0906 (bootstrap-medián 0,0797), 95% CI [0,0117; 0,1549], p = 0,0134 |
| H3 (négy feltétel) | **cáfolt** | a: ✓; b: ✓; c: ✓; d: ✗; r = 0,976; (c) alsó korlát 0,0362; (d) LoRA-s ↔ LoRA nélküli példány 0,9366, LoRA nélküliek egymás közt 1,0000 (küszöb −1 pont) |
| H5 (ECE, vllm) | **igaz** | Δ = -0,0337 (bootstrap-medián -0,0351), 95% CI [-0,0489; -0,0228], p < 0,0001; Holm-küszöb 0,050; az L1★ temperature-e a perm-0 kiolvasásra illesztett, ez az L1★ ECE-jét felfelé torzítja (önellenőrzés) |
| H6 (külön fej) | nem tesztelhető | az F5 nem futott |

- **Ismétlési zaj (L0 ↔ L0′):** top-címke billenés 0,0000, átl. |Δp| 0,00005 (max 0,0689), lef@95-különbség rögzített τ-val 0,0000.
- **Javítatlan teszten (érzékenység, pontbecslés):** L1csillag: lef@95 0,615, AURC 0,0273; L3_s1: lef@95 0,750, AURC 0,0019; L3_s2: lef@95 0,761, AURC 0,0023; L3_s3: lef@95 0,745, AURC 0,0012.
- **Kétértelmű sorok (L3):** L3_s1: átlépés 0,798, soft-gold találat az átlépőkön 0,976; L3_s2: átlépés 0,802, soft-gold találat az átlépőkön 0,983; L3_s3: átlépés 0,772, soft-gold találat az átlépőkön 0,975.

## HF

n(val) = 1006, n(teszt) = 3534; az L1★ temperature-e 1,429.

**T-belső**

| fok / kar | besorolási lef@95 | elért precizitás | AURC | döntési lef@95 | X-prec / X-fedés | ECE | kétértelmű-átlépés | pozíció-billenés | címketömeg | döntés/s |
|---|---|---|---|---|---|---|---|---|---|---|
| L0 | 0,630 | 0,965 | 0,0363 | 0,642 | 0,838 / 0,333 | 0,067 | 0,426 | 0,228 | 0,998 | — |
| L1★ (perm. átlag + temperature) | 0,656 | 0,978 | 0,0228 | 0,666 | 0,881 / 0,398 | 0,057 | 0,508 | — | 0,998 | — |
| L2a (40. réteg) | 0,726 | 0,977 | 0,0027 | 0,908 | 0,904 / 0,914 | 0,064 | 0,656 | — | — | — |
| L3 (`temp`, 3 seed átlaga; lef@95 [0,772–0,782]) | 0,776 | 0,983 | 0,0012 | 0,999 | 0,971 / 0,961 | 0,016 | 0,858 | — | 0,989 | — |

**T-szállító**

| fok / kar | besorolási lef@95 | elért precizitás | AURC | döntési lef@95 | X-prec / X-fedés | ECE | kétértelmű-átlépés | pozíció-billenés | címketömeg | döntés/s |
|---|---|---|---|---|---|---|---|---|---|---|
| L0 | 0,563 | 0,963 | 0,0404 | 0,572 | 0,832 / 0,371 | 0,050 | 0,311 | 0,275 | 0,998 | — |
| L1★ (perm. átlag + temperature) | 0,606 | 0,976 | 0,0269 | 0,620 | 0,876 / 0,446 | 0,064 | 0,355 | — | 0,998 | — |
| L2a (40. réteg) | 0,682 | 0,973 | 0,0056 | 0,888 | 0,828 / 0,880 | 0,062 | 0,473 | — | — | — |
| L3 (`temp`, 3 seed átlaga; lef@95 [0,739–0,757]) | 0,746 | 0,978 | 0,0018 | 1,000 | 0,940 / 0,964 | 0,011 | 0,781 | — | 0,988 | — |

**T-közeli**

| fok / kar | besorolási lef@95 | elért precizitás | AURC | döntési lef@95 | X-prec / X-fedés | ECE | kétértelmű-átlépés | pozíció-billenés | címketömeg | döntés/s |
|---|---|---|---|---|---|---|---|---|---|---|
| L0 | 0,643 | 0,935 | 0,0521 | 0,657 | 0,873 / 0,293 | 0,096 | 0,276 | 0,223 | 0,998 | — |
| L1★ (perm. átlag + temperature) | 0,670 | 0,944 | 0,0433 | 0,685 | 0,855 / 0,323 | 0,025 | 0,357 | — | 0,998 | — |
| L2a (40. réteg) | 0,726 | 0,936 | 0,0141 | 0,889 | 0,852 / 0,701 | 0,027 | 0,500 | — | — | — |
| L3 (`temp`, 3 seed átlaga; lef@95 [0,741–0,754]) | 0,746 | 0,968 | 0,0033 | 1,000 | 0,939 / 0,933 | 0,019 | 0,816 | — | 0,989 | — |

**T-távoli**

| fok / kar | besorolási lef@95 | elért precizitás | AURC | döntési lef@95 | X-prec / X-fedés | ECE | kétértelmű-átlépés | pozíció-billenés | címketömeg | döntés/s |
|---|---|---|---|---|---|---|---|---|---|---|
| L0 | 0,648 | 0,982 | 0,0199 | 0,673 | 0,893 / 0,459 | 0,043 | 0,366 | 0,225 | 0,998 | — |
| L1★ (perm. átlag + temperature) | 0,686 | 0,981 | 0,0143 | 0,714 | 0,949 / 0,514 | 0,057 | 0,402 | — | 0,998 | — |
| L2a (40. réteg) | 0,727 | 0,993 | 0,0008 | 0,954 | 0,884 / 0,938 | 0,060 | 0,488 | — | — | — |
| L3 (`temp`, 3 seed átlaga; lef@95 [0,750–0,763]) | 0,757 | 0,989 | 0,0002 | 1,000 | 0,958 / 0,975 | 0,010 | 0,809 | — | 0,989 | — |

**pool**

| fok / kar | besorolási lef@95 | elért precizitás | AURC | döntési lef@95 | X-prec / X-fedés | ECE | kétértelmű-átlépés | pozíció-billenés | címketömeg | döntés/s |
|---|---|---|---|---|---|---|---|---|---|---|
| L0 | 0,606 | 0,961 | 0,0377 | 0,620 | 0,854 / 0,366 | 0,059 | 0,327 | 0,248 | 0,998 | — |
| L1★ (perm. átlag + temperature) | 0,643 | 0,970 | 0,0273 | 0,659 | 0,890 / 0,426 | 0,045 | 0,381 | — | 0,998 | — |
| L2a (40. réteg) | 0,706 | 0,970 | 0,0060 | 0,905 | 0,854 / 0,856 | 0,050 | 0,502 | — | — | — |
| L3 (`temp`, 3 seed átlaga; lef@95 [0,747–0,761]) | 0,753 | 0,979 | 0,0017 | 1,000 | 0,947 / 0,959 | 0,009 | 0,802 | — | 0,988 | — |

⚠ = precizitás-bukás (a teszten elért precizitás < 0,93). Az AURC a kar saját nem-X döntéseinek görbéjén számolódik, így a több X-et mondó kar rövidebb görbét kap; a közös lefedettségre vágott változat az önellenőrzés szakaszban. Az L1★ döntés/s-e az L0-é negyede, mert a permutáció-átlag 4 kérés.

### Hipotézisek

| hipotézis | ítélet | részletek |
|---|---|---|
| H1 (L3 vs. L1★, Holm) | **igaz** | @95: Δ = 0,1098 (bootstrap-medián 0,1039), 95% CI [0,0397; 0,1854], p < 0,0001; AURC: Δ = -0,0256 (bootstrap-medián -0,0256), 95% CI [-0,0302; -0,0214], p < 0,0001; @95: megáll; AURC: megáll; másodlagos @90: Δ = 0,0010 (bootstrap-medián -0,0019), 95% CI [-0,0354; 0,0424], p = 0,9444 |
| H2 — T-szallito | **nem tesztelhető** (a számolt ítélet „általánosít”, de a 14 szállító mind szerepel a train-ben — generátorhiba, lásd Napló 2026-10-07; a számok leírók) | @95: Δ = 0,1401 (bootstrap-medián 0,1343), 95% CI [0,0596; 0,2359], p < 0,0001; szállító-permutáció (14 szállító, rögzített val-τ, egzakt): p = 0,00012 |
| H2 — T-kategoria | **általánosít** | @95: Δ = 0,0737 (bootstrap-medián 0,0667), 95% CI [0,0086; 0,1362], p = 0,0146 |
| H2 — T-kozeli | **általánosít** | @95: Δ = 0,0763 (bootstrap-medián 0,0694), 95% CI [0,0074; 0,1443], p = 0,0266 |
| H2 — T-tavoli | **általánosít** | @95: Δ = 0,0709 (bootstrap-medián 0,0636), 95% CI [0,0044; 0,1414], p = 0,0328 |
| H3 | — | motorközi feltétel, lásd a vLLM-szakaszt |
| H4 (L2a vs. L1★, HF) | **igaz** | Δ = 0,0636 (bootstrap-medián 0,0637), 95% CI [0,0095; 0,1325], p = 0,0144; Holm-küszöb 0,050 |
| H5 (ECE, hf) | **igaz** | Δ = -0,0359 (bootstrap-medián -0,0372), 95% CI [-0,0502; -0,0241], p < 0,0001; Holm-küszöb 0,025; az L1★ temperature-e a perm-0 kiolvasásra illesztett, ez az L1★ ECE-jét felfelé torzítja (önellenőrzés) |
| H6 (külön fej) | nem tesztelhető | az F5 nem futott |

- **Ismétlési zaj (L0 ↔ L0′):** top-címke billenés 0,0000, átl. |Δp| 0,00000 (max 0,0000), lef@95-különbség rögzített τ-val 0,0000.
- **Javítatlan teszten (érzékenység, pontbecslés):** L1csillag: lef@95 0,643, AURC 0,0273; L3_s1: lef@95 0,750, AURC 0,0016; L3_s2: lef@95 0,761, AURC 0,0023; L3_s3: lef@95 0,746, AURC 0,0011.
- **Kétértelmű sorok (L3):** L3_s1: átlépés 0,790, soft-gold találat az átlépőkön 0,983; L3_s2: átlépés 0,835, soft-gold találat az átlépőkön 0,981; L3_s3: átlépés 0,780, soft-gold találat az átlépőkön 0,980.

## Címkezaj (F1 átnézés)

- Teszt: pont 0,0040, felső95 0,0136 (n = 3021).
- Rétegenként (becsült maradék a javítás után): T-belso: 0,0000; T-szallito: 0,0077; T-kozeli: 0,0000; T-tavoli: 0,0000.

## Kiszolgálás

- **K0c:** kapu átment (részletek: eredmenyek/F0/k0c/k0c.json).
- **Példány-billenés (≥ 5 friss példány):** LoRA nélkül L0 0,0000, LoRA-s példány L0 0,0431, L3 0,0106; numerika-módok (próba-ujjlenyomat): LoRA-val 5, nélküle 3.
- **Mélyfúrás (utólagos, leíró; `h3_modok.json`).**
  - *Számítási út.* A megmaradt logok szerint `--enable-lora` mellett a MoE FP8-backend TRITON (13 korábbi indítás, F0–F3), nélküle DEEPGEMM (az egyetlen megmaradt LoRA nélküli H3-log). A H3 LoRA-s példányainak logja felülíródott, rájuk ez következtetés. Az `--enable-lora` a lefordított gráfot is megváltoztatja (más torch.compile-kulcs, `PunicaWrapperGPU`), így az eltérés a számítási út egészéből jön; hogy ebből mennyi a MoE-backend, azt egy kényszerített Triton-backendes LoRA nélküli kontroll döntené el (nem futott).
  - *Numerika-módok* (utólagos definíció: páronként ≤ 1% top-címke-billenés; 5 példányból alsó becslés): {lora_k1, lora_k3, lora_k4}; {lora_k2}; {lora_k5, fo_L0}; {nolora_k1, nolora_k2, nolora_k3, nolora_k4, nolora_k5}. A LoRA nélküli példányok egymás közt 0 billenéssel, de nem bitazonosan (991–996/1000 bájtazonos sor) egyeznek. A LoRA-s módok egymás közt 52–64, a LoRA nélkülitől 58–77 billenésre vannak; a HF-referencia mindegyiktől 50–63 billenésre (1000 itemből).
  - *Rendszeres eltolódás:* a LoRA-s módok átl. Δ log p(A)-ja a LoRA nélkülihez képest +0,206…+0,212, egymás közt ≈ 0; a HF +0,103. Szűkített entrópia: LoRA-s módok 0,456–0,457, LoRA nélkül 0,444, HF 0,438.
  - *Pontosság a pontozott itemeken* (n = 875): a LoRA-s módok Δ-ja a LoRA nélkülihez képest −0,001 [−0,014; +0,010], billenés jóra/rosszra 14/15; +0,001 [−0,012; +0,014], billenés jóra/rosszra 17/16; +0,001 [−0,013; +0,015], billenés jóra/rosszra 20/19. Kb. ±1,3 pontos felbontással nincs kimutatható romlás. A billenő itemek top-2 margója medián 0,103 (max 0,751), a nem billenőké 0,974.
  - *A (d) bukása bázisfüggetlen:* a LoRA-s példányok egymás közti egyezése is csak 0,957, a keresztegyezés ennél is kisebb.
  - *H1 módonként* (a fő példány val-ján rögzített temperature és τ@95, perm 0, `temp` kar): L0 lef@95 0,597–0,609 (LoRA nélküli példányokon is), L3 − L0 = +0,123…+0,137.
  - *Nem mért:* csak soros forgalom volt, vegyes köteg (LoRA-s és LoRA nélküli kérés együtt) és a chat-decode ára (runbook 6. pont) nem.

A (b) és a (c) ugyanazon a, órák óta futó fő példányon mért, ezért a LoRA-kérés többletköltsége a kettő különbsége. Az (a) egy másik, frissen indított H3-példányon futott, és ott a MoE-kernel is más (DEEPGEMM a TRITON helyett), ezért az (a)–(b) különbség a backendet és a példányt együtt méri, nem a LoRA-támogatás költségét.

| konfiguráció | concurrency | döntés/s | p50 (ms) | p95 (ms) |
|---|---|---|---|---|
| (a) LoRA nélküli példány | 1 | 4,7 | 212 | 226 |
| (a) LoRA nélküli példány | 8 | 10,5 | 782 | 837 |
| (a) LoRA nélküli példány | 32 | 14,5 | 2277 | 2656 |
| (b) LoRA-s példány, LoRA nélküli kérés | 1 | 6,4 | 158 | 171 |
| (b) LoRA-s példány, LoRA nélküli kérés | 8 | 12,2 | 637 | 690 |
| (b) LoRA-s példány, LoRA nélküli kérés | 32 | 16,9 | 1959 | 2285 |
| (c) `lora_request` | 1 | 6,2 | 161 | 174 |
| (c) `lora_request` | 8 | 11,8 | 678 | 724 |
| (c) `lora_request` | 32 | 15,2 | 2172 | 2526 |

- **MTP nélküli chat decode:** nem mérve ebben a körben (eltérés a runbook 6. pontjától).

## Önellenőrzés (utólagos, leíró; 2026-10-07, `onellenorzes.json`)

**Split-szivárgás.** A T-szállító réteg szállítóinak a terv szerint csak a tesztben kellett volna szerepelniük. A generátor (`generator.py`, S-párosítás) a train-pár nélküli cikkek tesztpárját a train-be tette, így ezek a szállítók a train-ben is megjelentek. A H2 T-szállító ítélete ezért nem tesztelhető.

| réteg | itemek | szállítók | ebből a train-ben | azok train-sorai | (szállító, cikk) átfedés | sorszöveg + gold duplikátum |
|---|---|---|---|---|---|---|
| val-belso | 240 | 17 | 17 | 4291 | 0 | 9 |
| val-szallito | 766 | 8 | 8 | 910 | 0 | 18 |
| T-belso | 474 | 17 | 17 | 4291 | 0 | 10 |
| T-szallito | 1627 | 14 | 14 | 900 | 0 | 47 |
| T-kozeli | 740 | 8 | 4 | 1052 | 0 | 0 |
| T-tavoli | 693 | 5 | 0 | 0 | 0 | 0 |

- **Nem látott szállítók (feltáró):** T-közeli: nem látott 0,092 (n = 319), látott 0,117 (n = 323); T-távoli (mind nem látott) 0,091; T-belső (mind látott) 0,136. A kategóriaváltással keveredik. A T-szállítón a szállítónkénti nyereség és a train-sorok száma: Spearman ρ = 0,27 (p = 0,35).
- **Plafon és hibaszerkezet:** a pontozott teszt nem-X aránya 0,756, ez a lef@95 felső korlátja. L1csillag@95: lef 0,616, precizitás 0,975, hibák: X-gold besorolva 42, rossz cikk 4; L1csillag@90: lef 0,754, precizitás 0,928, hibák: X-gold besorolva 150, rossz cikk 14; L3_s1@95: lef 0,751, precizitás 0,981, hibák: X-gold besorolva 29, rossz cikk 14; L3_s1@90: lef 0,751, precizitás 0,981, hibák: X-gold besorolva 29, rossz cikk 14.
- **AURC közös lefedettségen (0,745):** L1csillag 0,0108; L3_s1 0,0018; L3_s2 0,0019; L3_s3 0,0012. Kockázat 0,7-es lefedettségen: L1csillag 0,0482; L3_s1 0,0043; L3_s2 0,0052; L3_s3 0,0043.
- **X-arány-érzékenység** (a val és a teszt X-itemjeinek ritkítása, L3 − L1★ lef@95): X 0,25 → 13,7 pont [13,7; 13,7]; X 0,10 → 3,5 pont [1,9; 6,7]; X 0,05 → 1,1 pont [0,0; 2,6].
- **Az L1★ temperature-e:** perm0_illesztes_hasznalt: T = 1,337, ECE 0,043, lef@95 0,616; perm_atlagra_illesztve: T = 1,171, ECE 0,026, lef@95 0,607; T1: T = 1,000, ECE 0,018, lef@95 0,589. Az L3 ECE-je 0,010.
