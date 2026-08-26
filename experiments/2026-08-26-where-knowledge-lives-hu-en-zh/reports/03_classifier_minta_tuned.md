# Nyelvosztályozó — 100 véletlen token ellenőrző bírálatre

A `text` a dekódolt token (a `piece` a nyers BPE-alak). Írd át az `osztály` oszlopot, ha nem értesz egyet; az egyezési arány megy a módszertanba.

| # | text | piece | osztály |
|---|---|---|---|
| 1 | `元` | `åħĥ` | zh |
| 2 | `格拉斯` | `æł¼æĭīæĸ¯` | zh |
| 3 | `兰` | `åħ°` | zh |
| 4 | ` 
` | `ĠĊ` | egyéb |
| 5 | ` Nep` | `ĠNep` | ismeretlen |
| 6 | `可以帮助` | `åı¯ä»¥å¸®åĬ©` | zh |
| 7 | `一天` | `ä¸Ģå¤©` | zh |
| 8 | `研究` | `çłĶç©¶` | zh |
| 9 | `这两款` | `è¿Ļä¸¤æ¬¾` | zh |
| 10 | `-ra` | `-ra` | en |
| 11 | `斯坦` | `æĸ¯åĿ¦` | zh |
| 12 | `大` | `å¤§` | zh |
| 13 | `著名` | `èĳĹåĲį` | zh |
| 14 | ` Cold` | `ĠCold` | en |
| 15 | `靜` | `éĿľ` | zh |
| 16 | ` Er` | `ĠEr` | en |
| 17 | ` Meat` | `ĠMeat` | en |
| 18 | ` Special` | `ĠSpecial` | en |
| 19 | `五日` | `äºĶæĹ¥` | zh |
| 20 | `gy` | `gy` | ismeretlen |
| 21 | `瑞士` | `çĳŀå£«` | zh |
| 22 | ` olyan` | `Ġolyan` | hu |
| 23 | ` Belgium` | `ĠBelgium` | közös |
| 24 | `圓` | `åľĵ` | zh |
| 25 | `雅典` | `éĽħåħ¸` | zh |
| 26 | ` Tá` | `ĠTÃ¡` | ékezetes? |
| 27 | `重庆市` | `éĩįåºĨå¸Ĥ` | zh |
| 28 | ` Japanese` | `ĠJapanese` | en |
| 29 | ` friendships` | `Ġfriendships` | en |
| 30 | ` Aug` | `ĠAug` | en |
| 31 | `人或` | `äººæĪĸ` | zh |
| 32 | ` water` | `Ġwater` | en |
| 33 | `一词` | `ä¸Ģè¯į` | zh |
| 34 | ` Gathering` | `ĠGathering` | en |
| 35 | `岩` | `å²©` | zh |
| 36 | `以下是` | `ä»¥ä¸ĭæĺ¯` | zh |
| 37 | ` America` | `ĠAmerica` | en |
| 38 | `nev` | `nev` | en |
| 39 | `鱼` | `é±¼` | zh |
| 40 | ` Northwestern` | `ĠNorthwestern` | en |
| 41 | `她在` | `å¥¹åľ¨` | zh |
| 42 | `长寿` | `éķ¿å¯¿` | zh |
| 43 | ` Based` | `ĠBased` | en |
| 44 | `年初` | `å¹´åĪĿ` | zh |
| 45 | `杨` | `æĿ¨` | zh |
| 46 | `內` | `åħ§` | zh |
| 47 | `两种` | `ä¸¤ç§į` | zh |
| 48 | ` Shanghai` | `ĠShanghai` | en |
| 49 | ` those` | `Ġthose` | en |
| 50 | `kak` | `kak` | ismeretlen |
| 51 | `西方` | `è¥¿æĸ¹` | zh |
| 52 | `v` | `v` | en |
| 53 | ` More` | `ĠMore` | en |
| 54 | `奥地利` | `å¥¥åľ°åĪ©` | zh |
| 55 | `没有` | `æ²¡æľī` | zh |
| 56 | `的帮助` | `çļĦå¸®åĬ©` | zh |
| 57 | `阜阳市` | `éĺľéĺ³å¸Ĥ` | zh |
| 58 | `主要由` | `ä¸»è¦ģçĶ±` | zh |
| 59 | `小麦` | `å°ıéº¦` | zh |
| 60 | `,` | `,` | egyéb |
| 61 | `是用` | `æĺ¯çĶ¨` | zh |
| 62 | `杜` | `æĿľ` | zh |
| 63 | ` Smile` | `ĠSmile` | en |
| 64 | ` Christianity` | `ĠChristianity` | en |
| 65 | `它是一种` | `å®ĥæĺ¯ä¸Ģç§į` | zh |
| 66 | ` hurried` | `Ġhurried` | en |
| 67 | `公共交通` | `åħ¬åħ±äº¤éĢļ` | zh |
| 68 | ` main` | `Ġmain` | en |
| 69 | `pus` | `pus` | en |
| 70 | `自古` | `èĩªåı¤` | zh |
| 71 | ` Bol` | `ĠBol` | ismeretlen |
| 72 | ` Hab` | `ĠHab` | hu |
| 73 | ` Cai` | `ĠCai` | ismeretlen |
| 74 | ` Boston` | `ĠBoston` | közös |
| 75 | ` Fas` | `ĠFas` | ismeretlen |
| 76 | `共有` | `åħ±æľī` | zh |
| 77 | `二十` | `äºĮåįģ` | zh |
| 78 | ` relations` | `Ġrelations` | en |
| 79 | ` Min` | `ĠMin` | en |
| 80 | ` Relationships` | `ĠRelationships` | en |
| 81 | `所谓` | `æīĢè°ĵ` | zh |
| 82 | `赫` | `èµ«` | zh |
| 83 | `Fe` | `Fe` | en |
| 84 | ` Scientists` | `ĠScientists` | en |
| 85 | `第三方` | `ç¬¬ä¸īæĸ¹` | zh |
| 86 | ` Rhode` | `ĠRhode` | közös |
| 87 | `起源于` | `èµ·æºĲäºİ` | zh |
| 88 | ` battle` | `Ġbattle` | en |
| 89 | `当天` | `å½ĵå¤©` | zh |
| 90 | ` Carnival` | `ĠCarnival` | en |
| 91 | ` Vér` | `ĠVÃ©r` | ékezetes? |
| 92 | `安徽` | `å®īå¾½` | zh |
| 93 | ` Having` | `ĠHaving` | en |
| 94 | `这里的` | `è¿ĻéĩĮçļĦ` | zh |
| 95 | `亚洲` | `äºļæ´²` | zh |
| 96 | `早期` | `æĹ©æľŁ` | zh |
| 97 | `�` | `âĳ` | egyéb |
| 98 | `冬` | `åĨ¬` | zh |
| 99 | ` West` | `ĠWest` | en |
| 100 | `正确答案` | `æŃ£ç¡®çŃĶæ¡Ī` | zh |
