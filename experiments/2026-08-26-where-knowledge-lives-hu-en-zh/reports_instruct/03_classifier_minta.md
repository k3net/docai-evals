# Nyelvosztályozó — 100 véletlen token ellenőrző bírálatre

A `text` a dekódolt token (a `piece` a nyers BPE-alak). Írd át az `osztály` oszlopot, ha nem értesz egyet; az egyezési arány megy a módszertanba.

| # | text | piece | osztály |
|---|---|---|---|
| 1 | ` keters` | `Ġketers` | ismeretlen |
| 2 | `秦` | `ç§¦` | zh |
| 3 | `దు` | `à°¦à±ģ` | egyéb |
| 4 | `这个问题` | `è¿Ļä¸ªéĹ®é¢ĺ` | zh |
| 5 | `La` | `La` | en |
| 6 | `"L` | `"L` | en |
| 7 | `话音` | `è¯ĿéŁ³` | zh |
| 8 | `古今` | `åı¤ä»Ĭ` | zh |
| 9 | `保留` | `ä¿ĿçķĻ` | zh |
| 10 | `вери` | `Ð²ÐµÑĢÐ¸` | egyéb |
| 11 | ` exitos` | `Ġexitos` | ismeretlen |
| 12 | ` Mention` | `ĠMention` | en |
| 13 | `称呼` | `ç§°åĳ¼` | zh |
| 14 | `_STMT` | `_STMT` | ismeretlen |
| 15 | `翻译成` | `ç¿»è¯ĳæĪĲ` | zh |
| 16 | `Regardless` | `Regardless` | en |
| 17 | `上火` | `ä¸Ĭçģ«` | zh |
| 18 | `/apache` | `/apache` | en |
| 19 | `(Content` | `(Content` | en |
| 20 | `'h` | `'h` | en |
| 21 | `бут` | `Ð±ÑĥÑĤ` | egyéb |
| 22 | ` speeds` | `Ġspeeds` | en |
| 23 | `alagi` | `alagi` | ismeretlen |
| 24 | `yword` | `yword` | ismeretlen |
| 25 | `prep` | `prep` | en |
| 26 | `举世` | `ä¸¾ä¸ĸ` | zh |
| 27 | `irat` | `irat` | hu |
| 28 | `itora` | `itora` | ismeretlen |
| 29 | `ướng` | `Æ°á»Ľng` | ismeretlen |
| 30 | `(cs` | `(cs` | en |
| 31 | `Shock` | `Shock` | en |
| 32 | ` correction` | `Ġcorrection` | en |
| 33 | `рто` | `ÑĢÑĤÐ¾` | egyéb |
| 34 | `.with` | `.with` | en |
| 35 | `ugna` | `ugna` | ismeretlen |
| 36 | ` tijdens` | `Ġtijdens` | ismeretlen |
| 37 | `latable` | `latable` | ismeretlen |
| 38 | `虽说` | `èĻ½è¯´` | zh |
| 39 | `完本小说` | `å®Įæľ¬å°ıè¯´` | zh |
| 40 | `Though` | `Though` | en |
| 41 | `approximately` | `approximately` | en |
| 42 | `从天` | `ä»İå¤©` | zh |
| 43 | `'E` | `'E` | en |
| 44 | `опо` | `Ð¾Ð¿Ð¾` | egyéb |
| 45 | `торая` | `ÑĤÐ¾ÑĢÐ°Ñı` | egyéb |
| 46 | `embr` | `embr` | ismeretlen |
| 47 | `在许多` | `åľ¨è®¸å¤ļ` | zh |
| 48 | `这两种` | `è¿Ļä¸¤ç§į` | zh |
| 49 | `橋` | `æ©ĭ` | zh |
| 50 | `汉中` | `æ±īä¸Ń` | zh |
| 51 | `Christopher` | `Christopher` | en |
| 52 | `legend` | `legend` | en |
| 53 | ` провин` | `ĠÐ¿ÑĢÐ¾Ð²Ð¸Ð½` | egyéb |
| 54 | `人的一生` | `äººçļĦä¸ĢçĶŁ` | zh |
| 55 | `This` | `This` | en |
| 56 | ` holidays` | `Ġholidays` | en |
| 57 | `クリスマス` | `ãĤ¯ãĥªãĤ¹ãĥŀãĤ¹` | egyéb |
| 58 | ` capol` | `Ġcapol` | ismeretlen |
| 59 | `含义` | `åĲ«ä¹ī` | zh |
| 60 | ` Jú` | `ĠJÃº` | ékezetes? |
| 61 | ` MIR` | `ĠMIR` | en |
| 62 | ` разница` | `ĠÑĢÐ°Ð·Ð½Ð¸ÑĨÐ°` | egyéb |
| 63 | `тего` | `ÑĤÐµÐ³Ð¾` | egyéb |
| 64 | `짓` | `ì§ĵ` | egyéb |
| 65 | `C` | `C` | en |
| 66 | `iett` | `iett` | ismeretlen |
| 67 | `这个词` | `è¿Ļä¸ªè¯į` | zh |
| 68 | ` gác` | `ĠgÃ¡c` | ékezetes? |
| 69 | ` pearls` | `Ġpearls` | en |
| 70 | `*R` | `*R` | en |
| 71 | `اعي` | `Ø§Ø¹ÙĬ` | egyéb |
| 72 | `SSIP` | `SSIP` | ismeretlen |
| 73 | ` nenhuma` | `Ġnenhuma` | ismeretlen |
| 74 | `ooks` | `ooks` | ismeretlen |
| 75 | `eldon` | `eldon` | en |
| 76 | `杰作` | `æĿ°ä½ľ` | zh |
| 77 | `ognito` | `ognito` | ismeretlen |
| 78 | `_LANE` | `_LANE` | ismeretlen |
| 79 | `kler` | `kler` | ismeretlen |
| 80 | `-invalid` | `-invalid` | en |
| 81 | ` appels` | `Ġappels` | ismeretlen |
| 82 | `搜索资料` | `æĲľç´¢èµĦæĸĻ` | zh |
| 83 | `雖然` | `éĽĸçĦ¶` | zh |
| 84 | `-inline` | `-inline` | en |
| 85 | `(Date` | `(Date` | en |
| 86 | `bedo` | `bedo` | ismeretlen |
| 87 | `是用来` | `æĺ¯çĶ¨æĿ¥` | zh |
| 88 | `差異` | `å·®çķ°` | zh |
| 89 | ` distinction` | `Ġdistinction` | en |
| 90 | `IPH` | `IPH` | ismeretlen |
| 91 | `海涛` | `æµ·æ¶Ľ` | zh |
| 92 | ` planta` | `Ġplanta` | ismeretlen |
| 93 | `reras` | `reras` | ismeretlen |
| 94 | `cerpt` | `cerpt` | ismeretlen |
| 95 | `皮革城` | `çļ®éĿ©åŁİ` | zh |
| 96 | `_resolver` | `_resolver` | ismeretlen |
| 97 | ` Ouro` | `ĠOuro` | ismeretlen |
| 98 | `所称` | `æīĢç§°` | zh |
| 99 | ` mientras` | `Ġmientras` | ismeretlen |
| 100 | `シャ` | `ãĤ·ãĥ£` | egyéb |
