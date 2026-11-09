# 06 F1 — a javulás bontása NONE- és SELECT-javaslatokra (utólagos, leíró)

Szigorú helyesség, a teljes tanítómintás B1-R; bootstrap 10000 ismétlés, a 05 v1a kétszintű húzásával (család, azon belül alapeset). A B1-S·NONE-utolsó utólagos viszonyítás (a B1 sorrendje, a NONE-javaslatok a SELECT-ek mögött), nem kar.

| réteg | fajta | arány | szigorú | enyhe | AUROC B1-S | B1-R0 | B1-R | B1-LR |
|---|---|---|---|---|---|---|---|---|
| TESZT | SELECT | 0,78 | 0,772 | 0,772 | 0,963 | 0,840 | 0,976 | 0,966 |
| TESZT | NONE | 0,22 | 0,554 | 1,000 | 0,044 | 0,306 | 0,998 | 0,947 |
| TESZT | SELECT | 0,66 | 0,871 | 0,871 | 0,902 | 0,829 | 0,993 | 0,908 |
| TESZT | NONE | 0,34 | 0,471 | 0,942 | 0,362 | 0,474 | 0,955 | 0,872 |
| TESZT | SELECT | 0,78 | 0,766 | 0,766 | 0,901 | 0,848 | 0,977 | 0,911 |
| TESZT | NONE | 0,23 | 0,551 | 0,996 | 0,015 | 0,275 | 0,995 | 0,985 |

| réteg | B1-S | B1-S·NONE-utolsó | B1-R0 | B1-R | SELECT: B1-S | SELECT: B1-R |
|---|---|---|---|---|---|---|
| TESZT | 0,1422 | 0,0944 | 0,1365 | 0,0480 | 0,0398 | 0,0348 |
| TESZT | 0,2478 | 0,0915 | 0,1211 | 0,0442 | 0,0230 | 0,0099 |
| TESZT | 0,3037 | 0,1090 | 0,1308 | 0,0498 | 0,0562 | 0,0363 |

| réteg | összevetés | ΔAURC [CI] |
|---|---|---|
| TESZT | B1-R − B1-S | −0,0942 [−0,1114; −0,0786] |
| TESZT | B1-R − B1-S·NONE-utolsó | −0,0464 [−0,0530; −0,0401] |
| TESZT | SELECT: B1-R − SELECT: B1-S | −0,0050 [−0,0106; −0,0001] |
| TESZT | B1-R − B1-S | −0,2036 [−0,2297; −0,1769] |
| TESZT | B1-R − B1-S·NONE-utolsó | −0,0473 [−0,0536; −0,0415] |
| TESZT | SELECT: B1-R − SELECT: B1-S | −0,0131 [−0,0189; −0,0082] |
| TESZT | B1-R − B1-S | −0,2539 [−0,2783; −0,2276] |
| TESZT | B1-R − B1-S·NONE-utolsó | −0,0592 [−0,0665; −0,0516] |
| TESZT | SELECT: B1-R − SELECT: B1-S | −0,0199 [−0,0270; −0,0129] |
