# Baseline summary (Qwen3.6-35B-A3B FP8, one read per item)

| run | n | accuracy [95%] | wrong option | wrong exit | no answer |
|---|---:|---:|---:|---:|---:|
| calc_traps.f2.direct | 1273 | 44.1 [41.4; 46.8] | 53.2 | 2.7 | 0.0 |
| calc_traps.f4.direct | 1273 | 42.3 [39.6; 45.0] | 52.8 | 4.9 | 0.0 |
| calc_traps.f4.think | 1273 | 95.1 [93.7; 96.1] | 4.8 | 0.2 | 0.0 |
| interpretation.f2.direct | 2184 | 70.4 [68.5; 72.3] | 27.7 | 1.9 | 0.0 |
| interpretation.f4.direct | 2184 | 66.9 [64.9; 68.8] | 27.7 | 5.4 | 0.0 |
| interpretation.f4.think | 588 | 70.7 [66.9; 74.3] | 28.4 | 0.9 | 0.0 |
| minimal_pairs.f2.direct | 684 | 52.9 [49.2; 56.6] | 46.6 | 0.4 | 0.0 |
| minimal_pairs.f4.direct | 684 | 44.2 [40.5; 47.9] | 45.8 | 10.1 | 0.0 |
| minimal_pairs.f4.think | 684 | 51.0 [47.3; 54.8] | 47.5 | 1.3 | 0.1 |
| natural.f2.direct | 8974 | 83.7 [83.0; 84.5] | 15.0 | 1.2 | 0.0 |
| natural.f4.direct | 8974 | 77.5 [76.7; 78.4] | 12.7 | 9.8 | 0.0 |

## By cell

- **calc_traps.f2.direct**: family=finance.bank_matching 55.0 (wrong option 42.9, n 387); family=policy.expense_claims 29.7 (wrong option 68.0, n 518); family=technical.troubleshooting 52.7 (wrong option 43.2, n 368); label=MATCH 44.1 (wrong option 53.2, n 1273); trap=amount_in_words 88.3 (wrong option 5.0, n 60); trap=currency 23.3 (wrong option 72.5, n 258); trap=net_vs_gross 36.2 (wrong option 63.5, n 260); trap=partial_payment 48.9 (wrong option 49.8, n 327); trap=unit_conversion 52.7 (wrong option 43.2, n 368)
- **calc_traps.f4.direct**: family=finance.bank_matching 53.2 (wrong option 42.9, n 387); family=policy.expense_claims 27.0 (wrong option 67.0, n 518); family=technical.troubleshooting 52.2 (wrong option 43.2, n 368); label=MATCH 42.3 (wrong option 52.8, n 1273); trap=amount_in_words 90.0 (wrong option 5.0, n 60); trap=currency 15.9 (wrong option 78.3, n 258); trap=net_vs_gross 38.1 (wrong option 55.8, n 260); trap=partial_payment 46.5 (wrong option 49.8, n 327); trap=unit_conversion 52.2 (wrong option 43.2, n 368)
- **calc_traps.f4.think**: family=finance.bank_matching 84.0 (wrong option 15.8, n 387); family=policy.expense_claims 100.0 (wrong option 0.0, n 518); family=technical.troubleshooting 99.7 (wrong option 0.0, n 368); label=MATCH 95.1 (wrong option 4.8, n 1273); trap=amount_in_words 96.7 (wrong option 1.7, n 60); trap=currency 100.0 (wrong option 0.0, n 258); trap=net_vs_gross 100.0 (wrong option 0.0, n 260); trap=partial_payment 81.7 (wrong option 18.3, n 327); trap=unit_conversion 99.7 (wrong option 0.0, n 368)
- **interpretation.f2.direct**: family=policy.expense_claims 70.4 (wrong option 27.7, n 2184); label=MATCH 88.4 (wrong option 9.0, n 1638); label=MISSING_DATA 16.5 (wrong option 83.5, n 546)
  - undecidable_member: {"n": 546, "answers": {"option": 456, "X": 90}, "chose_option": 0.8351648351648352, "chose_option_ci95": [0.8017221767634913, 0.8639242456519106]}
  - all_members_correct: {"n": 546, "rate": 0.13186813186813187}
- **interpretation.f4.direct**: family=policy.expense_claims 66.9 (wrong option 27.7, n 2184); label=MATCH 88.0 (wrong option 9.4, n 1638); label=MISSING_DATA 3.7 (wrong option 82.4, n 546)
  - undecidable_member: {"n": 546, "answers": {"option": 450, "Y": 20, "X": 76}, "chose_option": 0.8241758241758241, "chose_option_ci95": [0.7900120520670192, 0.853809897482304]}
  - all_members_correct: {"n": 546, "rate": 0.031135531135531136}
- **interpretation.f4.think**: family=policy.expense_claims 70.7 (wrong option 28.4, n 588); label=MATCH 93.9 (wrong option 6.1, n 441); label=MISSING_DATA 1.4 (wrong option 95.2, n 147)
  - undecidable_member: {"n": 147, "answers": {"option": 140, "X": 5, "Y": 2}, "chose_option": 0.9523809523809523, "chose_option_ci95": [0.9049758739051633, 0.9767445827012907]}
  - all_members_correct: {"n": 147, "rate": 0.013605442176870748}
- **minimal_pairs.f2.direct**: family=policy.expense_claims 52.9 (wrong option 46.6, n 684); label=MATCH 87.7 (wrong option 11.4, n 342); label=MISSING_DATA 18.1 (wrong option 81.9, n 342)
  - undecidable_member: {"n": 342, "answers": {"option": 280, "X": 62}, "chose_option": 0.8187134502923976, "chose_option_ci95": [0.7744162612232341, 0.8559303742124689]}
  - all_members_correct: {"n": 342, "rate": 0.14327485380116958}
- **minimal_pairs.f4.direct**: family=policy.expense_claims 44.2 (wrong option 45.8, n 684); label=MATCH 85.7 (wrong option 12.9, n 342); label=MISSING_DATA 2.6 (wrong option 78.7, n 342)
  - undecidable_member: {"n": 342, "answers": {"option": 269, "X": 62, "Y": 9, "Z": 2}, "chose_option": 0.7865497076023392, "chose_option_ci95": [0.740065880475099, 0.8266677917514966]}
  - all_members_correct: {"n": 342, "rate": 0.02046783625730994}
- **minimal_pairs.f4.think**: family=policy.expense_claims 51.0 (wrong option 47.5, n 684); label=MATCH 96.8 (wrong option 3.2, n 342); label=MISSING_DATA 5.3 (wrong option 91.8, n 342)
  - undecidable_member: {"n": 342, "answers": {"option": 314, "X": 9, "Y": 18, "None": 1}, "chose_option": 0.9181286549707602, "chose_option_ci95": [0.8842180838552117, 0.9427504378631878]}
  - all_members_correct: {"n": 342, "rate": 0.05263157894736842}
- **natural.f2.direct**: family=finance.bank_matching 82.1 (wrong option 17.4, n 2983); family=policy.expense_claims 82.9 (wrong option 16.7, n 2995); family=technical.troubleshooting 86.2 (wrong option 10.9, n 2996); label=MATCH 96.0 (wrong option 2.0, n 5386); label=MISSING_DATA 26.2 (wrong option 73.8, n 896); label=NO_MATCH 67.9 (wrong option 32.1, n 1795); label=OUT_OF_SCOPE 99.6 (wrong option 0.4, n 897)
- **natural.f4.direct**: family=finance.bank_matching 71.7 (wrong option 16.0, n 2983); family=policy.expense_claims 81.3 (wrong option 11.1, n 2995); family=technical.troubleshooting 79.5 (wrong option 11.1, n 2996); label=MATCH 96.4 (wrong option 1.6, n 5386); label=MISSING_DATA 38.4 (wrong option 50.6, n 896); label=NO_MATCH 65.5 (wrong option 33.2, n 1795); label=OUT_OF_SCOPE 27.4 (wrong option 0.3, n 897)

## Thinking runs

- calc_traps.f4.think: {"finish": {"stop": 1273}, "completion_tokens_median": 1689.0, "completion_tokens_p95": 2572.7999999999997}
- interpretation.f4.think: {"finish": {"stop": 588}, "completion_tokens_median": 1499.0, "completion_tokens_p95": 2428.85}
- minimal_pairs.f4.think: {"finish": {"stop": 683, "length": 1}, "completion_tokens_median": 1629.5, "completion_tokens_p95": 2735.5}

## Text-only baseline (label from surface text)

- natural: {"n": 8974, "accuracy": 0.6317138399821707, "majority": 0.6001782928459996, "by_label": {"MATCH": 0.6336799108800594, "MISSING_DATA": 0.6919642857142857, "NO_MATCH": 0.4222841225626741, "OUT_OF_SCOPE": 0.9788182831661093}, "by_family_label": {"finance.bank_matching:MATCH": 0.5687150837988827, "finance.bank_matching:MISSING_DATA": 0.9832214765100671, "finance.bank_matching:NO_MATCH": 0.5563025210084034, "finance.bank_matching:OUT_OF_SCOPE": 0.9733333333333334, "policy.expense_claims:MATCH": 0.7033945464663328, "policy.expense_claims:MISSING_DATA": 0.7993311036789298, "policy.expense_claims:NO_MATCH": 0.36333333333333334, "policy.expense_claims:OUT_OF_SCOPE": 0.9866220735785953, "technical.troubleshooting:MATCH": 0.6286826014452473, "technical.troubleshooting:MISSING_DATA": 0.29431438127090304, "technical.troubleshooting:NO_MATCH": 0.34833333333333333, "technical.troubleshooting:OUT_OF_SCOPE": 0.9765100671140939}}
- interpretation: {"n": 2184, "accuracy": 0.9752747252747253, "majority": 0.75, "by_label": {"MATCH": 0.9682539682539683, "MISSING_DATA": 0.9963369963369964}, "auroc": 0.9994823044273594}
- minimal_pairs: {"n": 684, "accuracy": 0.6067251461988304, "majority": 0.5, "auroc": 0.6724291234909887, "cv": "5-fold, grouped by scenario_group (matched scenario pairs)"}
