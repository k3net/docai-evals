# Nyelvosztályozó — 100 véletlen token ellenőrző bírálatre

A `text` a dekódolt token (a `piece` a nyers BPE-alak). Írd át az `osztály` oszlopot, ha nem értesz egyet; az egyezési arány megy a módszertanba.

| # | text | piece | osztály |
|---|---|---|---|
| 1 | `egiat` | `egiat` | ismeretlen |
| 2 | `estens` | `estens` | ismeretlen |
| 3 | ` Speed` | `ĠSpeed` | en |
| 4 | `山西` | `å±±è¥¿` | zh |
| 5 | ` terze` | `Ġterze` | ismeretlen |
| 6 | ` Italie` | `ĠItalie` | ismeretlen |
| 7 | ` kamb` | `Ġkamb` | ismeretlen |
| 8 | `起源于` | `èµ·æºĲäºİ` | zh |
| 9 | ` معنى` | `ĠÙħØ¹ÙĨÙī` | egyéb |
| 10 | `喜马拉雅` | `åĸľé©¬æĭīéĽħ` | zh |
| 11 | `萨` | `èĲ¨` | zh |
| 12 | `halie` | `halie` | ismeretlen |
| 13 | `_hdl` | `_hdl` | ismeretlen |
| 14 | `的字` | `çļĦåŃĹ` | zh |
| 15 | `_story` | `_story` | ismeretlen |
| 16 | ` autumn` | `Ġautumn` | en |
| 17 | `顺企` | `é¡ºä¼ģ` | zh |
| 18 | ` дій` | `ĠÐ´ÑĸÐ¹` | egyéb |
| 19 | `_REFER` | `_REFER` | ismeretlen |
| 20 | `海市` | `æµ·å¸Ĥ` | zh |
| 21 | `*pi` | `*pi` | közös |
| 22 | `{EIF` | `{EIF` | ismeretlen |
| 23 | `披萨` | `æĬ«èĲ¨` | zh |
| 24 | `عديد` | `Ø¹Ø¯ÙĬØ¯` | egyéb |
| 25 | ` BAR` | `ĠBAR` | közös |
| 26 | `玉环` | `çİīçİ¯` | zh |
| 27 | ` 문제를` | `Ġë¬¸ìłľë¥¼` | egyéb |
| 28 | `家家户户` | `å®¶å®¶æĪ·æĪ·` | zh |
| 29 | ` oxy` | `Ġoxy` | ismeretlen |
| 30 | `ヨン` | `ãĥ¨ãĥ³` | egyéb |
| 31 | ` желания` | `ĠÐ¶ÐµÐ»Ð°Ð½Ð¸Ñı` | egyéb |
| 32 | `ńczy` | `ÅĦczy` | ismeretlen |
| 33 | ` Tiongkok` | `ĠTiongkok` | ismeretlen |
| 34 | `见到` | `è§ģåĪ°` | zh |
| 35 | ` Eb` | `ĠEb` | hu |
| 36 | `Kostenloser` | `Kostenloser` | ismeretlen |
| 37 | ` However` | `ĠHowever` | en |
| 38 | ` Hang` | `ĠHang` | közös |
| 39 | `خن` | `Ø®ÙĨ` | egyéb |
| 40 | ` (` | `Ġ(` | egyéb |
| 41 | ` determinadas` | `Ġdeterminadas` | ismeretlen |
| 42 | `施工过程中` | `æĸ½å·¥è¿ĩç¨ĭä¸Ń` | zh |
| 43 | `这是一` | `è¿Ļæĺ¯ä¸Ģ` | zh |
| 44 | `見面` | `è¦ĭéĿ¢` | zh |
| 45 | `ة` | `Ø©` | egyéb |
| 46 | ` paternal` | `Ġpaternal` | en |
| 47 | `当地` | `å½ĵåľ°` | zh |
| 48 | `驅` | `é©ħ` | zh |
| 49 | ` Silence` | `ĠSilence` | en |
| 50 | ` Shandong` | `ĠShandong` | ismeretlen |
| 51 | ` recons` | `Ġrecons` | ismeretlen |
| 52 | `	TokenName` | `ĉTokenName` | ismeretlen |
| 53 | `/Foundation` | `/Foundation` | en |
| 54 | `季节性` | `åŃ£èĬĤæĢ§` | zh |
| 55 | ` teis` | `Ġteis` | ismeretlen |
| 56 | `andenburg` | `andenburg` | ismeretlen |
| 57 | ` Saturn` | `ĠSaturn` | en |
| 58 | `早年` | `æĹ©å¹´` | zh |
| 59 | `グレ` | `ãĤ°ãĥ¬` | egyéb |
| 60 | `这个词` | `è¿Ļä¸ªè¯į` | zh |
| 61 | `Professional` | `Professional` | en |
| 62 | ` telem` | `Ġtelem` | hu |
| 63 | `品種` | `åĵģç¨®` | zh |
| 64 | `терпе` | `ÑĤÐµÑĢÐ¿Ðµ` | egyéb |
| 65 | `-Cds` | `-Cds` | ismeretlen |
| 66 | ` Ranh` | `ĠRanh` | ismeretlen |
| 67 | `酵母` | `éħµæ¯į` | zh |
| 68 | ` 봄` | `Ġë´Ħ` | egyéb |
| 69 | ` provinces` | `Ġprovinces` | en |
| 70 | ` Anh` | `ĠAnh` | ismeretlen |
| 71 | `末期` | `æľ«æľŁ` | zh |
| 72 | `暂无` | `æļĤæĹł` | zh |
| 73 | `主要经营` | `ä¸»è¦ģç»ıèĲ¥` | zh |
| 74 | `Hung` | `Hung` | en |
| 75 | `emode` | `emode` | ismeretlen |
| 76 | ` 😀` | `ĠðŁĺĢ` | egyéb |
| 77 | ` Ir` | `ĠIr` | en |
| 78 | `冬季` | `åĨ¬åŃ£` | zh |
| 79 | ` Jana` | `ĠJana` | en |
| 80 | `:)` | `:)` | egyéb |
| 81 | `until` | `until` | en |
| 82 | `ObjectContext` | `ObjectContext` | ismeretlen |
| 83 | ` yuan` | `Ġyuan` | en |
| 84 | ` Mir` | `ĠMir` | en |
| 85 | ` ,"` | `Ġ,"` | egyéb |
| 86 | `لان` | `ÙĦØ§ÙĨ` | egyéb |
| 87 | `upart` | `upart` | ismeretlen |
| 88 | `ekli` | `ekli` | ismeretlen |
| 89 | `我不知道` | `æĪĳä¸įçŁ¥éģĵ` | zh |
| 90 | ` тих` | `ĠÑĤÐ¸Ñħ` | egyéb |
| 91 | `本文为` | `æľ¬æĸĩä¸º` | zh |
| 92 | `阴` | `éĺ´` | zh |
| 93 | ` Tết` | `ĠTáº¿t` | ismeretlen |
| 94 | `这意味着` | `è¿ĻæĦıåĳ³çĿĢ` | zh |
| 95 | ` diza` | `Ġdiza` | ismeretlen |
| 96 | ` brabant` | `Ġbrabant` | ismeretlen |
| 97 | `堂的` | `åłĤçļĦ` | zh |
| 98 | ` historically` | `Ġhistorically` | en |
| 99 | `的节日` | `çļĦèĬĤæĹ¥` | zh |
| 100 | ` Wei` | `ĠWei` | en |
