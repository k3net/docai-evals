# Nyelvosztályozó — 100 véletlen token ellenőrző bírálatre

A `text` a dekódolt token (a `piece` a nyers BPE-alak). Írd át az `osztály` oszlopot, ha nem értesz egyet; az egyezési arány megy a módszertanba.

| # | text | piece | osztály |
|---|---|---|---|
| 1 | `在上海` | `åľ¨ä¸Ĭæµ·` | zh |
| 2 | `请以` | `è¯·ä»¥` | zh |
| 3 | `(n` | `(n` | en |
| 4 | `请` | `è¯·` | zh |
| 5 | ` nincs` | `Ġnincs` | ismeretlen |
| 6 | `表面上` | `è¡¨éĿ¢ä¸Ĭ` | zh |
| 7 | `廣` | `å»£` | zh |
| 8 | ` Dương` | `ĠDÆ°Æ¡ng` | ismeretlen |
| 9 | `陕西` | `éĻķè¥¿` | zh |
| 10 | `Newton` | `Newton` | közös |
| 11 | ` Yang` | `ĠYang` | en |
| 12 | `怀` | `æĢĢ` | zh |
| 13 | `UK` | `UK` | en |
| 14 | ` Union` | `ĠUnion` | en |
| 15 | `日` | `æĹ¥` | zh |
| 16 | `Techn` | `Techn` | ismeretlen |
| 17 | `赫` | `èµ«` | zh |
| 18 | `ez` | `ez` | hu |
| 19 | `Auth` | `Auth` | ismeretlen |
| 20 | `名为` | `åĲįä¸º` | zh |
| 21 | ` magyar` | `Ġmagyar` | közös |
| 22 | `」` | `ãĢį` | egyéb |
| 23 | `卢` | `åį¢` | zh |
| 24 | `能以` | `èĥ½ä»¥` | zh |
| 25 | `主要是` | `ä¸»è¦ģæĺ¯` | zh |
| 26 | `wu` | `wu` | en |
| 27 | `Más` | `MÃ¡s` | ékezetes? |
| 28 | `长兴` | `éķ¿åħ´` | zh |
| 29 | `元` | `åħĥ` | zh |
| 30 | ` ${` | `Ġ${` | egyéb |
| 31 | `as` | `as` | közös |
| 32 | `Math` | `Math` | en |
| 33 | `的第二` | `çļĦç¬¬äºĮ` | zh |
| 34 | `.` | `.` | egyéb |
| 35 | ` czek` | `Ġczek` | ismeretlen |
| 36 | `綠` | `ç¶ł` | zh |
| 37 | `人` | `äºº` | zh |
| 38 | `蔚` | `èĶļ` | zh |
| 39 | `/**` | `/**` | egyéb |
| 40 | `Someone` | `Someone` | en |
| 41 | `Pizza` | `Pizza` | közös |
| 42 | ` áll` | `ĠÃ¡ll` | ékezetes? |
| 43 | `Zoom` | `Zoom` | közös |
| 44 | `地球的` | `åľ°çĲĥçļĦ` | zh |
| 45 | ` civil` | `Ġcivil` | közös |
| 46 | ` King` | `ĠKing` | en |
| 47 | `走了` | `èµ°äºĨ` | zh |
| 48 | ` nyug` | `Ġnyug` | ismeretlen |
| 49 | `Since` | `Since` | en |
| 50 | `態` | `æħĭ` | zh |
| 51 | `尚` | `å°ļ` | zh |
| 52 | ` ú` | `ĠÃº` | ékezetes? |
| 53 | `公有` | `åħ¬æľī` | zh |
| 54 | `*K` | `*K` | en |
| 55 | `赶` | `èµ¶` | zh |
| 56 | `卡罗` | `åį¡ç½Ĺ` | zh |
| 57 | `Here` | `Here` | közös |
| 58 | `朋友的` | `æľĭåıĭçļĦ` | zh |
| 59 | `陕` | `éĻķ` | zh |
| 60 | `Wa` | `Wa` | en |
| 61 | `菲` | `èı²` | zh |
| 62 | ` ép` | `ĠÃ©p` | ékezetes? |
| 63 | ` christmas` | `Ġchristmas` | en |
| 64 | `zhou` | `zhou` | ismeretlen |
| 65 | `ca` | `ca` | en |
| 66 | `集` | `éĽĨ` | zh |
| 67 | ` selama` | `Ġselama` | ismeretlen |
| 68 | ` World` | `ĠWorld` | en |
| 69 | `She` | `She` | en |
| 70 | `correct` | `correct` | en |
| 71 | `_second` | `_second` | ismeretlen |
| 72 | ` trans` | `Ġtrans` | en |
| 73 | `inn` | `inn` | en |
| 74 | `法國` | `æ³ķåľĭ` | zh |
| 75 | `京` | `äº¬` | zh |
| 76 | `Mountain` | `Mountain` | en |
| 77 | `Christopher` | `Christopher` | en |
| 78 | `日是` | `æĹ¥æĺ¯` | zh |
| 79 | `发生` | `åıĳçĶŁ` | zh |
| 80 | `這兩個` | `éĢĻåħ©åĢĭ` | zh |
| 81 | ` эп` | `ĠÑįÐ¿` | egyéb |
| 82 | `河南` | `æ²³åįĹ` | zh |
| 83 | `ette` | `ette` | hu |
| 84 | `鏡` | `éı¡` | zh |
| 85 | ` Sky` | `ĠSky` | en |
| 86 | ` annak` | `Ġannak` | hu |
| 87 | `涅` | `æ¶ħ` | zh |
| 88 | `Ф` | `Ð¤` | egyéb |
| 89 | `Haz` | `Haz` | ismeretlen |
| 90 | ` g` | `Ġg` | en |
| 91 | `人的` | `äººçļĦ` | zh |
| 92 | `General` | `General` | en |
| 93 | `ész` | `Ã©sz` | ékezetes? |
| 94 | `历史上` | `åİĨåı²ä¸Ĭ` | zh |
| 95 | `Friend` | `Friend` | en |
| 96 | `在全` | `åľ¨åħ¨` | zh |
| 97 | `海市` | `æµ·å¸Ĥ` | zh |
| 98 | `New` | `New` | közös |
| 99 | `-wsj` | `-wsj` | ismeretlen |
| 100 | `Lie` | `Lie` | en |
