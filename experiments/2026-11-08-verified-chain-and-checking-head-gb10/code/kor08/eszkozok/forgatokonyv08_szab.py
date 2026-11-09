"""08 G2 — a szabálycsalád friss értelmezési forgatókönyvei (G1-rögzítés 5.3: 40 teszt- és 50 tanító-forgatókönyv,
mindkét nyelven; a G1b 12 forgatókönyvétől — `ertelmezes08_szab` — diszjunktak). Dani átnézi a generálás előtt.

Egy forgatókönyv: gold és csali költségnem (a `szint06.SZAB_TIPUS` öt kulcsa), a helyzet (a kiadás tárgya úgy, hogy a
felszíne a csali felé húz, de egyedül nem dönt: az (a) változat, gold Y), és az áttételes jel (`jel2`): egy tény, amelyből a
gold egy lépésben következik a szabálypont szövegéből (`tamasz`), és amely a csalit kizárja: a (b) változat. A `kulcs2` a
jel szavai, amelyeknek a (b)-ben szerepelniük kell és az (a)-ban nem; a `kulcs` a gold költségnem árulkodó szavai (az
(a)-ban nem szerepelhetnek), a helyzet szavai nélkül. A G1b D7 auditjának tanulságai (Dani 11-02):
  - az (a) legyen valóban eldönthetetlen a két költségnem közt (a helyzet ne a költségnem leírásának szavaival nevezze
    meg a kiadást);
  - a (b) jele a kért összeg tárgyát mondja ki, ne a kiállítóból kelljen kikövetkeztetni;
  - belső címzettnek adott tárgy nem ajándék; egyedül elköltött étkezés nem vendéglátás; a magyar utazás belföldi
    (a magyar szabálypont: „belföldi kiküldetés”).
Dani 11-03-i átnézése (64 rendben, 26 javítva, `JAVITVA`; `kor08/adat/G2/G2_forgatokonyvek_ertekeles.md`; a 2. kör 11-04: 25 rendben, F41 kiegészítve):
  - mindig a kért összeg tárgya döntsön: vegyes helyzetben (előadás + vacsora) a jel külön számlatételt mond ki; a
    számlázó, a helyszín vagy a tárgy későbbi sorsa önmagában nem elég;
  - ha az (a) már megnevezi a fizetett szolgáltatást (licenc, alkalmazás éves díja), a jel nem írhatja át más tárgyú
    díjjá: az (a) ilyenkor csak „a szolgáltatónak fizetett díj”;
  - nincs rejtett kategóriahatár (a vendég útja / szállása nem reprezentáció, a nyeremény nem ajándék): a jel az öt
    szabálypontból közvetlenül eldönthető tényt mond (a saját munkatárs kiküldetése, a vendégeknek adott étkezés, a
    térítésmentes, nem szerződéses átadás).

  python3 kor08/eszkozok/forgatokonyv08_szab.py lap --out kor08/adat/G2/forgatokonyv_szab_atnezes.md
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]

NEV = {"U": ("utazás", "travel"), "R": ("reprezentáció", "entertainment"), "K": ("képzés", "training"),
       "E": ("eszköz", "equipment"), "S": ("előfizetés", "subscription")}
TAMASZ = {"U": ("utazási és szállásköltség", "travel and accommodation"), "Rv": ("üzleti vendéglátás", "business entertainment"),
          "Ra": ("ajándék", "gifts"), "K": ("szakmai képzés", "professional training"), "Kt": ("tanfolyam", "courses"),
          "Kk": ("konferencia-részvétel", "conference fees"), "Ei": ("munkaeszköz-beszerzés (számítástechnika)", "work equipment purchases (IT)"),
          "Es": ("szerszám", "tools"), "S": ("szoftver- és szakmai előfizetés", "software and professional subscriptions")}
# a gold költségnem árulkodó szavai (a `kulcs`); a helyzetben szereplők kimaradnak (`kulcs_of`)
ARULKODO = {"U": (["szállás", "útiköltség"], ["accommodation", "travel cost"]),
            "R": (["ajándék", "vendégül"], ["gift", "hosted"]),
            # angolul nem a puszta „exam”: a generált e-mail-címek domainje `pelda.example` (Dani 11-04, K08G1M: a
            # képzés-gold (a) 18-ból 12 forgatókönyvön ezen bukott el)
            "K": (["tanfolyam", "vizsga"], ["course", "exam ", "exam.", "exam,", "exams", "examination"]),
            "E": (["leltár", "munkaeszköz"], ["asset register", "work equipment"]),
            "S": (["előfizet", "éves hozzáférés"], ["subscri", "annual access"])}

# Dani 11-03-i átnézése szerint javított forgatókönyvek (a csereszöveg az övé, a prompt alakjára igazítva; a kulcs2 újraillesztve);
# a 2. kör (11-04): 25 rendben, az F41 jele kiegészítve (a kért összeg a taxifuvar díja)
JAVITVA = {"F08", "F10", "F13", "F16", "F19", "F21", "F22", "F24", "F25", "F26", "F28", "F29", "F41", "F42", "F43", "F44", "F45",
           "F46", "F47", "F49", "F69", "F82", "F83", "F85", "F86", "F90"}

# (id, szelet, gold, csali, tamasz, (hu helyzet, hu jel2, hu kulcs2), (en helyzet, en jel2, en kulcs2))
F = [
    # --- eszköz ← reprezentáció: tárgy, amely ajándék is lehetne; a jel: a saját munkatárs napi munkaeszköze
    ("F01", "teszt", "E", "R", "Ei",
     ("egy tablet és a hozzá való toll vásárlása",
      "a tablet leltári számot kapott, és a raktárvezetőnk a készletfelvételhez használja minden nap", ["leltári szám", "készletfelvétel"]),
     ("the purchase of a tablet with a stylus",
      "the tablet received an asset tag and our warehouse manager uses it every day for stock-taking", ["asset tag", "stock-taking"])),
    ("F02", "teszt", "E", "R", "Es",
     ("egy akkus csavarbehajtó-készlet vásárlása",
      "a készletet a karbantartó csapatunk kapta meg, és a szerszámraktár nyilvántartásába vettük", ["karbantartó", "szerszámraktár"]),
     ("the purchase of a cordless screwdriver set",
      "the set was issued to our maintenance team and entered in the tool store register", ["maintenance team", "tool store"])),
    ("F03", "tanito", "E", "R", "Ei",
     ("egy okosóra vásárlása",
      "az órát a terepen dolgozó műszakvezetőnk kapta, a munkaidő-nyilvántartó alkalmazást használja rajta, és a cég leltárában szerepel",
      ["műszakvezető", "munkaidő-nyilvántart"]),
     ("the purchase of a smartwatch",
      "the watch was issued to our field shift supervisor, who uses the time-tracking app on it, and it is on the company asset register",
      ["shift supervisor", "time-tracking"])),
    ("F04", "tanito", "E", "R", "Ei",
     ("egy digitális fényképezőgép vásárlása",
      "a gépet a minőségellenőreink a hibás termékek fényképezésére használják, és leltári számot kapott", ["minőségellenőr", "hibás termék"]),
     ("the purchase of a digital camera",
      "our quality inspectors use the camera to photograph defective products, and it received an asset tag", ["quality inspector", "defective"])),
    ("F05", "tanito", "E", "R", "Es",
     ("egy lézeres távolságmérő vásárlása",
      "a mérőt a felmérő mérnökünk használja a helyszíni felmérésekhez, és a szerszámnyilvántartásba került", ["felmérő mérnök", "szerszámnyilvántart"]),
     ("the purchase of a laser distance meter",
      "our surveying engineer uses the meter for site surveys, and it was entered in the tool register", ["surveying engineer", "tool register"])),
    ("F06", "tanito", "E", "R", "Ei",
     ("két prémium hangszóró vásárlása",
      "a hangszórók leltári számmal a tárgyaló videokonferencia-rendszeréhez kerültek", ["videokonferencia", "leltári szám"]),
     ("the purchase of two premium speakers",
      "the speakers went into the meeting room's video conferencing system with asset tags", ["video conferenc", "asset tag"])),
    # --- reprezentáció ← eszköz: tárgy, amely munkaeszköz is lehetne; a jel: üzleti partner kapta ajándékba
    ("F07", "teszt", "R", "E", "Ra",
     ("egy e-könyv-olvasó vásárlása",
      "az olvasót díszcsomagolásban, kísérőlevéllel a beszállítónk ügyvezetőjének küldtük el a húszéves együttműködés alkalmából",
      ["díszcsomagolás", "kísérőlevél"]),
     ("the purchase of an e-book reader",
      "the reader was gift-wrapped and sent with a covering letter to our supplier's managing director to mark twenty years of cooperation",
      ["gift-wrapped", "covering letter"])),
    ("F08", "teszt", "R", "E", "Ra",
     ("egy hordozható Bluetooth-hangszóró vásárlása",
      "a hangszórót a vásári standunkon térítésmentesen, végleg átadtuk vevőcégünk beszerzőjének, köszönetként az "
      "együttműködésért; nem volt nyeremény vagy szerződéses juttatás", ["térítésmentes", "vevőcég"]),
     ("the purchase of a portable Bluetooth speaker",
      "at our trade fair stand, we gave the speaker to a buyer from one of our customer companies to keep, free of charge, as "
      "a thank-you for the cooperation; it was neither a prize nor a contractual benefit",
      ["free of charge", "customer compan"])),
    ("F09", "tanito", "R", "E", "Ra",
     ("vezeték nélküli töltőállomások vásárlása",
      "a logónkkal ellátott töltőállomásokat a viszonteladói találkozón a partnereink kapták meg", ["logó", "viszonteladó"]),
     ("the purchase of wireless charging stations",
      "the charging stations, branded with our logo, were given to our partners at the resellers' meeting", ["logo", "reseller"])),
    ("F10", "tanito", "R", "E", "Ra",
     ("egy okostelefon vásárlása",
      "a telefont a viszonteladónk vezetőjének személyesen, térítésmentesen adtuk át az éves találkozón, köszönőlevéllel; nem "
      "szerződéses bónusz vagy más ellenszolgáltatás volt", ["viszonteladó", "térítésmentes"]),
     ("the purchase of a smartphone",
      "at the annual meeting, we gave the phone personally to the head of our reseller, free of charge, with a thank-you "
      "letter; it was not a contractual bonus or payment for a service", ["reseller", "free of charge"])),
    ("F11", "tanito", "R", "E", "Ra",
     ("egy drón vásárlása",
      "a drónt az új gyárunk átadóünnepségén a kivitelező cég projektvezetőjének adtuk köszönetként", ["átadóünnepség", "kivitelező"]),
     ("the purchase of a drone",
      "the drone was given as a thank-you to the contractor's project manager at the opening ceremony of our new plant",
      ["opening ceremony", "contractor"])),
    ("F12", "tanito", "R", "E", "Ra",
     ("multiszerszám-készletek vásárlása",
      "a készleteket névre szóló kártyával a beszállítói napon a meghívott alvállalkozóink vezetői kapták meg", ["alvállalkozó", "névre szóló"]),
     ("the purchase of multi-tool sets",
      "the sets, each with a personal card, were given to the managers of our invited subcontractors at the supplier day",
      ["subcontractor", "personal card"])),
    # --- képzés ← reprezentáció: esemény, amely vendéglátás is lehetne; a jel: akkreditált képzés, a saját munkatárs tanult
    ("F13", "teszt", "K", "R", "K",
     ("egy vacsorával egybekötött esti előadáshoz kapcsolódó egyik számlatétel",
      "a kért összeg kizárólag az akkreditált szakmai előadás részvételi díja; a végén igazolást kaptam a kötelező "
      "kreditpontokról. A vacsora külön számlatétel, az összegét nem kérem", ["akkreditál", "kreditpont"]),
     ("one invoice item relating to an evening talk followed by dinner",
      "the amount claimed is solely the attendance fee for the accredited professional session; I received a certificate for "
      "my mandatory CPD points at the end. Dinner is a separate invoice item and is not included in this claim",
      ["accredited", "CPD"])),
    ("F14", "teszt", "K", "R", "K",
     ("egy borkóstolóval egybekötött esti program díja",
      "a díj egy borászati szakmai képzés harmadik, vizsgával záruló moduljáé; a résztvevők a saját beszerzőink voltak", ["vizsg", "beszerző"]),
     ("the fee for an evening programme with a wine tasting",
      "the fee is for the third module of a professional wine course, which ends with an exam; the participants were our own buyers",
      ["third module", "our own buyers"])),  # nem „exam”: a `pelda.example` domain kielégítené (Dani 11-04)
    ("F15", "tanito", "K", "R", "K",
     ("egy kétórás gasztronómiai bemutató díja",
      "a bemutató egy szakácsképzés kötelező gyakorlati foglalkozása volt, amelyen a konyhai csapatunk két tagja vett részt, és tanúsítványt kaptak",
      ["gyakorlati foglalkozás", "tanúsítvány"]),
     ("the fee for a two-hour culinary demonstration",
      "the demonstration was a mandatory practical session of a chef training programme attended by two members of our kitchen team, "
      "who received certificates", ["practical session", "certificate"])),
    ("F16", "tanito", "K", "R", "Kt",
     ("egy gyárlátogatáshoz és az azt követő ebédhez kapcsolódó egyik számlatétel",
      "a kért összeg kizárólag a minőségirányítási tanfolyam terepgyakorlatának részvételi díja. Az ebédet külön számlázták, "
      "annak árát ez a tétel nem tartalmazza", ["terepgyakorlat", "minőségirányítás"]),
     ("one invoice item relating to a factory visit followed by lunch",
      "the amount claimed is solely the participation fee for the field exercise of a quality management course. Lunch was "
      "invoiced separately and its price is not included in this item", ["field exercise", "quality management"])),
    # --- reprezentáció ← képzés: képzésnek tűnő tétel; a jel: üzleti partnereket láttunk vendégül, vagy ajándék
    ("F17", "teszt", "R", "K", "Ra",
     ("egy online oktatócsomag hozzáférési kódjának megvásárlása",
      "a kódot karácsonyi meglepetésként a legrégebbi ügyfelünk ügyvezetőjének küldtük el, üdvözlőlappal", ["karácsony", "üdvözlőlap"]),
     ("the purchase of an access code for an online learning package",
      "we sent the code as a Christmas surprise to the managing director of our longest-standing client, with a greeting card",
      ["Christmas", "greeting card"])),
    ("F18", "teszt", "R", "K", "Rv",
     ("egy szakmai kerekasztal-beszélgetés költsége",
      "a beszélgetést mi szerveztük a három legnagyobb megrendelőnk vezetőinek, a kért összeg az utána nekik adott állófogadás számlája",
      ["megrendelő", "állófogadás"]),
     ("the cost of a professional round-table discussion",
      "we organised the discussion for the executives of our three largest clients, and the amount claimed is the bill for the reception "
      "we gave them afterwards", ["clients", "reception"])),
    ("F19", "tanito", "R", "K", "Ra",
     ("egy előadássorozat jegyei",
      "az átruházható jegyeket üdvözlőlevéllel, térítésmentesen átadtuk partnercégünk két mérnökének, személyes köszönetként "
      "az együttműködésért; a címzettek szabadon dönthetnek a felhasználásról", ["térítésmentes", "partnercég", "átruházható"]),
     ("tickets for a lecture series",
      "we gave the transferable tickets to two engineers from our partner company, free of charge, with a greeting letter as a "
      "personal thank-you for the cooperation; the recipients may decide freely whether to use them",
      ["free of charge", "partner company", "transferable"])),
    ("F20", "tanito", "R", "K", "Rv",
     ("egy tréningközpont egynapos díja",
      "a központ éttermében a beszállítóinknak adtunk évzáró vacsorát, a díj a vacsora és a terem ára", ["beszállító", "évzáró vacsor"]),
     ("the one-day fee of a training centre",
      "we held a year-end dinner for our suppliers in the centre's restaurant, and the fee covers the dinner and the room",
      ["suppliers", "year-end dinner"])),
    # --- előfizetés ← képzés: tanulási felületnek vagy szolgáltatójának fizetett díj; a jel: napi munkaeszközként használt, megújuló szoftverhozzáférés
    ("F21", "teszt", "S", "K", "S",
     ("egy nyelvi szolgáltatónak fizetett díj",
      "a díj a szolgáltató alkalmazásában elérhető fordítómodul éves megújítása. A csapat ezzel fordítja az ügyfélleveleket; "
      "órákon való részvételt ez a díj nem tartalmaz", ["fordítómodul", "megújít"]),
     ("a fee paid to a language-services provider",
      "the fee is the annual renewal of the translation module in the provider's app. The team uses it to translate customer "
      "emails; the fee does not include attendance at any lessons", ["translation module", "renewal"])),
    ("F22", "teszt", "S", "K", "S",
     ("egy webinárszolgáltatónak fizetett díj",
      "a díj a szolgáltató platformján működő szervezői fiók éves megújítása. Ebben a fiókban mi tartjuk a saját "
      "termékbemutatóinkat az ügyfeleknek", ["szervezői fiók", "termékbemutató"]),
     ("a fee paid to a webinar-services provider",
      "the fee is the annual renewal of a host account on the provider's platform. We use that account to run our own product "
      "demos for customers", ["host account", "product demo"])),
    ("F23", "tanito", "S", "K", "S",
     ("egy szakmai e-learning portál díja",
      "a portálon csak a jogszabályfigyelő szolgáltatást használjuk, a díj a havonta megújuló hozzáférésé", ["jogszabályfigyel", "havonta megújuló"]),
     ("the fee for a professional e-learning portal",
      "we only use the portal's legislation tracker, and the fee is for the monthly renewing access", ["legislation tracker", "monthly"])),
    ("F24", "tanito", "S", "K", "S",
     ("egy kódolási gyakorlóoldal szolgáltatójának fizetett díj",
      "a fejlesztőink az oldal kódellenőrző eszközét használják a napi munkában, az éves licencet a szolgáltató automatikusan "
      "megújította", ["kódellenőrző", "automatikusan megújít"]),
     ("a fee paid to the provider of a coding practice site",
      "our developers use the site's code review tool in daily work, and the provider renewed the annual licence automatically",
      ["code review tool", "renewed"])),
    ("F25", "tanito", "S", "K", "S",
     ("egy prezentációs szolgáltatónak fizetett díj",
      "a díj a szolgáltató diaszerkesztő alkalmazásának éves használati díja; az értékesítőink ezzel készítik az ajánlataikat",
      ["diaszerkesztő", "ajánlat"]),
     ("a fee paid to a presentation-services provider",
      "the fee is the annual usage charge for the provider's slide-editing app, which our sales team uses to prepare proposals",
      ["slide-edit", "proposals"])),
    # --- képzés ← előfizetés: szoftver- vagy tartalomszolgáltatónak fizetett díj; a jel: oktatóval tartott, záróvizsgás képzés díja
    ("F26", "teszt", "K", "S", "Kt",
     ("egy online szakmai platform szolgáltatójának fizetett díj",
      "a díj egy tíz alkalmas, élő oktatóval tartott adótanácsadói felkészítőé, amely a platformon zajlik és tanúsítvánnyal "
      "zárul", ["felkészítő", "tanúsítv"]),
     ("a fee paid to the provider of an online professional platform",
      "the fee is for a ten-session tax adviser preparation course with a live instructor, held on the platform and ending "
      "with a certificate", ["preparation course", "certificate"])),
    ("F27", "teszt", "K", "S", "Kk",
     ("egy szakmai folyóirat kiadójának fizetett díj",
      "a díj a kiadó által szervezett egynapos szakmai konferencia részvételi díja; a folyóiratot nem fizetjük elő", ["egynapos", "részvételi díj"]),
     ("a fee paid to the publisher of a professional journal",
      "the fee is the attendance fee for a one-day professional conference organised by the publisher; we do not subscribe to the journal",
      ["one-day", "attendance fee"])),
    ("F28", "tanito", "K", "S", "K",
     ("egy statisztikai program használatához kapcsolódó egyetemi számlatétel",
      "a kért összeg az elemzőnk tízalkalmas, élő oktatóval tartott statisztikai felkészítésének részvételi díja, amely "
      "számonkéréssel zárul. A szoftverlicenc díját ez a tétel nem tartalmazza",
      ["élő oktató", "számonkérés", "részvételi díj"]),
     ("a university invoice item relating to the use of a statistics package",
      "the amount claimed is the attendance fee for our analyst's ten-session statistics programme with a live instructor and "
      "a final assessment. This item does not include any software licence fee",
      ["live instructor", "attendance fee", "final assessment"])),
    ("F29", "tanito", "K", "S", "Kt",
     ("egy nyelvi alkalmazás szolgáltatójának fizetett díj",
      "a díj egy anyanyelvi tanárral tartott, heti két alkalmas üzleti angol tanfolyamé, amelyet a szolgáltató az alkalmazáson "
      "keresztül szervez", ["anyanyelvi tanár", "heti két"]),
     ("a fee paid to the provider of a language app",
      "the fee is for a business English course with a native-speaker teacher, twice a week, which the provider organises "
      "through the app", ["native-speaker teacher", "twice a week"])),
    ("F30", "tanito", "K", "S", "Kt",
     ("egy könyvelőprogram gyártójának fizetett díj",
      "a díj a gyártó hivatalos, vizsgával záruló bérszámfejtő-tanfolyamáé, amelyen a bérszámfejtőnk vett részt; a programot nem tőle vesszük",
      ["bérszámfejtő", "hivatalos"]),
     ("a fee paid to the vendor of an accounting package",
      "the fee is for the vendor's official payroll course ending with an exam, attended by our payroll officer; we do not buy the software "
      "from this vendor", ["payroll", "official"])),
    # --- utazás ← képzés: képzéshez kapcsolódó tétel; a jel: a képzés díjmentes vagy külön fizetett, a tétel az út / szállás
    ("F31", "teszt", "U", "K", "U",
     ("a miskolci vizsgaközponthoz kapcsolódó költség",
      "a vizsgadíjat a cég közvetlenül átutalta; most csak a vizsganapi vonatjegyet és a Miskolcon töltött éjszaka szállását számolom el",
      ["vonat", "éjszaka"]),
     ("the cost relating to the Sheffield exam centre",
      "the company paid the exam fee directly; I am only claiming the train ticket on exam day and the night's accommodation in Sheffield",
      ["train", "night"])),
    ("F32", "teszt", "U", "K", "U",
     ("az egri tanfolyami hétvégéhez kapcsolódó egyik költségtétel",
      "a tétel a hétvége két éjszakájának szállásdíja egy egri panzióban; a tanfolyam díját a szervező alapítvány fedezte",
      ["panzió", "két éjszak"]),
     ("one of the cost items related to the Cardiff course weekend",
      "the item is the charge for the weekend's two nights at a guest house in Cardiff; the course fee was covered by the organising foundation",
      ["guest house", "two nights"])),
    ("F33", "tanito", "U", "K", "U",
     ("a nyíregyházi gyakorlati képzéshez kapcsolódó egyik költségtétel",
      "a tétel a Nyíregyházára és vissza tartó autóbuszjegyek ára; a képzés az anyavállalat belső képzése volt, díj nélkül",
      ["autóbuszjegy", "anyavállalat"]),
     ("one of the cost items related to the practical training in Norwich",
      "the item is the price of the coach tickets to Norwich and back; the training was an internal course of our parent company, free of charge",
      ["coach tickets", "parent company"])),
    ("F34", "tanito", "U", "K", "U",
     ("a soproni szakmai napokhoz kapcsolódó költség",
      "a kért összeg a soproni szálloda három éjszakás számlája; a szakmai napokra a meghívó szervezet díjmentes belépőt adott",
      ["három éjszak", "díjmentes belépő"]),
     ("the cost related to the professional days in Exeter",
      "the amount claimed is the Exeter hotel bill for three nights; the inviting organisation gave a free pass to the professional days",
      ["three nights", "free pass"])),
    ("F35", "tanito", "U", "K", "U",
     ("a veszprémi minősítő vizsgához kapcsolódó egyik tétel",
      "a tétel a vizsgára céges autóval megtett út üzemanyag-költsége az útnyilvántartás szerint; a vizsgadíjat a munkáltató közvetlenül fizette",
      ["üzemanyag", "útnyilvántartás"]),
     ("one of the items related to the qualification exam in Oxford",
      "the item is the fuel cost of driving to the exam in the company car, according to the mileage log; the employer paid the exam fee directly",
      ["fuel", "mileage log"])),
    # --- képzés ← utazás: útnak tűnő tétel; a jel: a kért összeg a helyszíni képzés díja
    ("F36", "teszt", "K", "U", "K",
     ("a szolnoki látogatás költsége",
      "a kért összeg a szolnoki tűzvédelmi oktatás részvételi díja, amely tanúsítvánnyal zárult; a vonatjegyet a bérletem fedezte",
      ["tűzvédelmi oktatás", "tanúsítv"]),
     ("the cost of the Reading visit",
      "the amount claimed is the attendance fee for the fire safety course in Reading, which ended with a certificate; my season ticket covered the train",
      ["fire safety", "certificate"])),
    ("F37", "teszt", "K", "U", "Kt",
     ("a zalaegerszegi kiküldetéshez kapcsolódó egyik költségtétel",
      "a tétel a helyszíni targoncavezető-tanfolyam vizsgadíja, amelyet a vizsgaközpont számlázott; a szállást a vendéglátó cég adta",
      ["targoncavezető", "vizsgaközpont"]),
     ("one of the cost items from the Plymouth business trip",
      "the item is the exam fee for the on-site forklift operator course, invoiced by the exam centre; the host company provided the accommodation",
      ["forklift", "exam centre"])),
    ("F38", "tanito", "K", "U", "K",
     ("a székesfehérvári út költségei közül egy tétel",
      "a tétel a székesfehérvári gyártó termékoktatásának díja, a számlát az oktatást tartó cég állította ki; útiköltséget nem számolok el",
      ["termékoktatás", "oktatást tartó"]),
     ("one item among the costs of the Coventry trip",
      "the item is the fee for the Coventry manufacturer's product training, invoiced by the company that ran the training; I am not claiming "
      "any travel costs", ["product training", "ran the training"])),
    ("F39", "tanito", "K", "U", "Kt",
     ("a kaposvári hét egyik költsége",
      "a költség a kaposvári mezőgazdasági szaktanácsadó-tanfolyam díja; a szállást és az utazást a tanfolyam szervezője biztosította",
      ["szaktanácsadó", "szervezője biztosította"]),
     ("one of the costs of the week in Lincoln",
      "the cost is the fee for the agricultural adviser course in Lincoln; the course organiser provided the accommodation and travel",
      ["adviser course", "organiser provided"])),
    ("F40", "tanito", "K", "U", "K",
     ("a tatabányai helyszíni nap egyik tétele",
      "a tétel a helyszínen tartott munkavédelmi oktatás díja, amelyről igazolást kaptunk; céges kisbusszal mentünk, szállás nem kellett",
      ["munkavédelmi oktatás", "igazolás"]),
     ("one item from the on-site day in Derby",
      "the item is the fee for the health and safety training held on site, for which we received certificates; we went by company minibus "
      "and needed no accommodation", ["health and safety", "certificates"])),
    # --- utazás ← reprezentáció: ügyféltalálkozóhoz vagy partnerlátogatáshoz kapcsolódó, meg nem nevezett tétel; a jel: a
    #     saját munkatárs kiküldetési útja vagy szállása
    ("F41", "teszt", "U", "R", "U",
     ("a miskolci esti ügyféltalálkozóhoz kapcsolódó egyik költségtétel",
      "a miskolci kiküldetésem estéjén egyedül mentem taxival a pályaudvarról a szállodába, és ennek a fuvarnak a díját kérem "
      "megtéríteni", ["pályaudvar", "szállod", "taxi"]),
     ("one cost item relating to the evening client meeting in Newcastle",
      "on the evening of my Newcastle business trip I took a taxi alone from the railway station to the hotel, and I am "
      "claiming the fare for that ride", ["railway station", "hotel", "taxi"])),
    ("F42", "teszt", "U", "R", "U",
     ("a debreceni karbantartási látogatáshoz kapcsolódó egyik számlatétel",
      "a kért összeg két szállodai szoba két éjszakájának ára; a szobákban a két saját szerelőnk aludt a debreceni kiküldetés "
      "alatt", ["szállod", "szerelő", "kiküldetés"]),
     ("one invoice item relating to the maintenance visit in Glasgow",
      "the amount claimed is the price of two hotel rooms for two nights; our own two fitters stayed in them during the "
      "business trip to Glasgow", ["hotel", "fitter", "business trip"])),
    ("F43", "tanito", "U", "R", "U",
     ("a dél-alföldi partnerlátogatásokhoz kapcsolódó egyik költségtétel",
      "a kért összeg a saját háromnapos belföldi kiküldetésemre bérelt autó díja, amellyel egyedül jártam a partnereink között",
      ["autó", "kiküldetés", "háromnapos"]),
     ("one cost item relating to visits to our business partners in the south-west",
      "the amount claimed is the hire charge for the car I used alone to travel between our partners on my three-day domestic "
      "business trip", ["hire charge", "business trip", "three-day"])),
    ("F44", "tanito", "U", "R", "U",
     ("az egri építkezés ügyfélegyeztetéséhez kapcsolódó egyik költségtétel",
      "a kért összeg a saját projektvezetőnk két éjszakás szállása az egri kiküldetés idején; külső vendég elhelyezését nem "
      "tartalmazza", ["projektvezető", "két éjszak", "kiküldetés"]),
     ("one cost item relating to the client meeting at the construction site in Durham",
      "the amount claimed is two nights' accommodation for our own project manager during the business trip to Durham; it "
      "includes no accommodation for external guests", ["project manager", "two nights", "business trip"])),
    # --- reprezentáció ← utazás: partnerlátogatáshoz kapcsolódó tétel; a jel: üzleti vendégeknek adott étkezés vagy fogadás
    #     (az út / szállás nem), vagy ajándék
    ("F45", "teszt", "R", "U", "Rv",
     ("a szegedi partnerlátogatáshoz kapcsolódó egyik számlatétel",
      "a kért összeg a lengyel partnercég két üzletkötőjének a tárgyalások után adott üzleti vacsora éttermi számlája; utazási "
      "vagy szállástétel nincs benne", ["vacsor", "étterm", "üzletkötő"]),
     ("one invoice item relating to the partner visit in Edinburgh",
      "the amount claimed is the restaurant bill for the business dinner we hosted for the Polish partner company's two sales "
      "representatives after the negotiations; it contains no travel or accommodation charge",
      ["dinner", "restaurant", "sales representatives"])),
    ("F46", "teszt", "R", "U", "Rv",
     ("a debreceni vevőtalálkozóhoz kapcsolódó egyik költségtétel",
      "a kért összeg a meghívott vevőinknek a találkozón felszolgált ebéd számlája. Vonatjegyet és más utazási díjat ez a "
      "tétel nem tartalmaz", ["ebéd", "felszolgált", "meghívott"]),
     ("one cost item relating to the customer meeting in Birmingham",
      "the amount claimed is the bill for the lunch served to our invited customers at the meeting. This item includes no "
      "train tickets or other travel charges", ["lunch", "invited"])),
    ("F47", "tanito", "R", "U", "Rv",
     ("a holland vevők gyárlátogatásához kapcsolódó egyik költségtétel",
      "a kért összeg a holland vevők küldöttségének adott állófogadás étel- és italszámlája; a szállításuk költségét ez a "
      "tétel nem tartalmazza", ["állófogadás", "küldöttség", "ital"]),
     ("one cost item relating to the Dutch customers' factory visit",
      "the amount claimed is the food and drink bill for the reception hosted for the delegation of Dutch customers; it does "
      "not include the cost of transporting them", ["reception", "delegation", "food and drink"])),
    ("F48", "tanito", "R", "U", "Ra",
     ("a hévízi hétvége költsége",
      "a hévízi szállodai csomagot a legfontosabb beszállítónk vezetőjének adtuk ajándékba a nyugdíjba vonulása alkalmából", ["nyugdíj", "beszállító"]),
     ("the cost of the Bath weekend",
      "we gave the Bath hotel package as a present to the head of our most important supplier on his retirement", ["retirement", "supplier"])),
    # --- eszköz ← előfizetés: eszköz és szolgáltatás együtt; a jel: a kért összeg csak az eszköz
    ("F49", "teszt", "E", "S", "Ei",
     ("a vonalkódolvasókból és készletkezelő szolgáltatásból álló rendszer egyik számlatétele",
      "a kért összeg csak a saját raktárunkba megvett két kézi olvasó ára; a készletkezelő szolgáltatás díját az anyavállalat "
      "fizeti", ["kézi olvasó", "két kézi", "anyavállalat"]),
     ("one invoice item for a system consisting of barcode scanners and a stock management service",
      "the amount claimed is only the purchase price of the two handheld scanners for our own warehouse; the stock management "
      "service fee is paid by the parent company", ["handheld", "parent company"])),
    ("F50", "teszt", "E", "S", "Ei",
     ("egy biztonsági kamerarendszerhez kapcsolódó tétel",
      "a számla négy kültéri kameráról szól, amelyek leltári számot kaptak; a felhős rögzítés díját külön szerződés alapján fizetjük",
      ["kültéri", "leltári szám"]),
     ("an item related to a security camera system",
      "the invoice is for four outdoor cameras, which received asset tags; the cloud recording fee is paid under a separate contract",
      ["outdoor", "asset tag"])),
    ("F51", "tanito", "E", "S", "Ei",
     ("egy grafikai rajzprogramhoz kapcsolódó tétel",
      "a tétel egy grafikus rajztábla ára, amelyet a tervezőnk munkaállomásához vettünk; a program hozzáférését a megrendelő biztosítja",
      ["rajztábla", "munkaállomás"]),
     ("an item related to a graphics drawing program",
      "the item is the price of a graphics tablet bought for our designer's workstation; the program access is provided by the client",
      ["graphics tablet", "workstation"])),
    ("F52", "tanito", "E", "S", "Ei",
     ("egy navigációs rendszerhez kapcsolódó tétel a szervizautóba",
      "a számla a műszerfalra szerelt navigációs készülékről szól; a térképfrissítés az első három évben ingyenes", ["műszerfal", "ingyenes"]),
     ("an item for a navigation system in the service van",
      "the invoice is for the dashboard-mounted navigation unit; map updates are free for the first three years", ["dashboard", "free for the first"])),
    ("F53", "tanito", "E", "S", "Ei",
     ("egy hálózati tárolóhoz és a felhőszinkronhoz kapcsolódó tétel",
      "a tétel a hálózati tároló két merevlemeze, amelyeket a meghibásodott lemezek helyére szereltünk be; a felhőszinkron díja nem szerepel "
      "a számlán", ["merevlemez", "meghibásodott"]),
     ("an item related to a network storage device and its cloud sync",
      "the item is the two hard drives for the network storage device, fitted to replace the failed drives; the cloud sync fee is not on "
      "the invoice", ["hard drives", "failed"])),
    # --- előfizetés ← eszköz: eszközhöz kapcsolódó tétel; a jel: a kért összeg a szoftver vagy szolgáltatás megújuló díja
    ("F54", "teszt", "S", "E", "S",
     ("flottakövető eszközökhöz kapcsolódó tétel",
      "a tétel a nyomkövető szolgáltatás éves díja a már beszerelt eszközökre; új készüléket nem vettünk", ["éves díj", "beszerelt"]),
     ("an item related to fleet tracking devices",
      "the item is the annual fee for the tracking service for devices already installed; no new devices were bought",
      ["annual fee", "already installed"])),
    ("F55", "teszt", "S", "E", "S",
     ("egy multifunkciós nyomtatóhoz kapcsolódó tétel",
      "a tétel a nyomtató felhős dokumentumkezelő szoftverének éves licence; a nyomtató bérelt, nem a miénk", ["dokumentumkezelő", "bérelt"]),
     ("an item related to a multifunction printer",
      "the item is the annual licence for the printer's cloud document management software; the printer is leased, not ours",
      ["document management", "leased"])),
    ("F56", "tanito", "S", "E", "S",
     ("egy mérőállomáshoz kapcsolódó tétel",
      "a tétel a mérőállomás adatfeldolgozó szoftverének havi díja; magát az állomást tavaly vettük meg", ["adatfeldolgozó", "tavaly"]),
     ("an item related to a measuring station",
      "the item is the monthly fee for the station's data processing software; the station itself was bought last year",
      ["data processing", "last year"])),
    ("F57", "tanito", "S", "E", "S",
     ("egy telefonközpont-rendszerhez kapcsolódó tétel",
      "a tétel a felhőalapú telefonközpont-szoftver negyedéves díja; a készülékek a régiek maradtak", ["negyedéves", "felhőalapú"]),
     ("an item related to a phone system",
      "the item is the quarterly fee for the cloud-based phone system software; the handsets are the old ones", ["quarterly", "cloud-based"])),
    ("F58", "tanito", "S", "E", "S",
     ("egy diagnosztikai műszerhez kapcsolódó tétel a szervizbe",
      "a tétel a műszer gyártói adatbázisának éves hozzáférési díja, amelyből a szerelők a hibakódokat keresik ki; a műszer már megvan",
      ["adatbázis", "hibakód"]),
     ("an item for a diagnostic instrument for the workshop",
      "the item is the annual access fee for the manufacturer's database, which the mechanics use to look up fault codes; we already have "
      "the instrument", ["database", "fault code"])),
    # --- utazás ← eszköz: helyszíni műszaki munkához kapcsolódó tétel; a jel: szállás vagy út
    ("F59", "teszt", "U", "E", "U",
     ("a kecskeméti helyszíni szereléshez kapcsolódó egyik költségtétel",
      "a tétel a kecskeméti szálloda két éjszakás számlája, amíg a szerelés tartott; szerszámot nem vettünk", ["szálloda", "két éjszak"]),
     ("one of the cost items related to the on-site installation in Swindon",
      "the item is the Swindon hotel bill for two nights while the installation lasted; no tools were bought", ["hotel", "two nights"])),
    ("F60", "teszt", "U", "E", "U",
     ("a békéscsabai gépátadáshoz kapcsolódó egyik tétel",
      "a tétel a Békéscsabára tartó vonatút jegye és a helyi buszjegy; a gépet a gyártó szállította", ["vonat", "buszjegy"]),
     ("one of the items related to the machine handover in Carlisle",
      "the item is the train ticket to Carlisle and the local bus fare; the machine was delivered by the manufacturer", ["train", "bus fare"])),
    ("F61", "tanito", "U", "E", "U",
     ("a szombathelyi hálózatbővítéshez kapcsolódó egyik költségtétel",
      "a tétel a hálózatbővítés idejére Szombathelyen bérelt apartman három éjszakája; az eszközöket a megrendelő adta",
      ["apartman", "három éjszak"]),
     ("one of the cost items related to the network expansion in Inverness",
      "the item is three nights in an apartment rented in Inverness for the network expansion; the client supplied the equipment",
      ["apartment", "three nights"])),
    ("F62", "tanito", "U", "E", "U",
     ("a szekszárdi műszerkalibráláshoz kapcsolódó egyik tétel",
      "a tétel a céges autó útdíja és üzemanyaga a szekszárdi útra, az útnyilvántartás szerint; műszert nem vásároltunk", ["útdíj", "útnyilvántartás"]),
     ("one of the items related to the instrument calibration in Hereford",
      "the item is the toll and fuel for the company car's trip to Hereford, according to the mileage log; no instrument was bought",
      ["toll", "mileage log"])),
    # --- eszköz ← utazás: úthoz kapcsolódó tétel; a jel: a kért összeg egy leltárba vett munkaeszköz
    ("F63", "teszt", "E", "U", "Es",
     ("a szolnoki helyszíni felméréshez kapcsolódó egyik költségtétel",
      "a számla egy lézeres szintezőről szól, amely leltári számot kapott, és azóta a felmérő csapat használja", ["szintező", "leltári szám"]),
     ("one of the cost items related to the site survey in Lancaster",
      "the invoice is for a laser level, which received an asset tag and has been used by the survey team ever since", ["laser level", "asset tag"])),
    ("F64", "teszt", "E", "U", "Es",
     ("az ózdi kiküldetéshez kapcsolódó egyik tétel",
      "a tétel egy szerszámkoffer, amelyet a helyszínen vettünk, mert a régi eltört; a karbantartók szerszámnyilvántartásába került",
      ["szerszámkoffer", "szerszámnyilvántart"]),
     ("one of the items from the Dundee business trip",
      "the item is a toolbox we bought on site because the old one broke; it was entered in the maintenance team's tool register",
      ["toolbox", "tool register"])),
    ("F65", "tanito", "E", "U", "Ei",
     ("a pécsi vásárhoz kapcsolódó egyik költségtétel",
      "a tétel egy hordozható projektor, amelyet a standra vettünk, és azóta leltári számmal a tárgyalóban használjuk", ["projektor", "leltári szám"]),
     ("one of the cost items related to the trade fair in Brighton",
      "the item is a portable projector we bought for the stand, now used in the meeting room with an asset tag", ["projector", "asset tag"])),
    ("F66", "tanito", "E", "U", "Ei",
     ("a hatvani ügyfélszerviz-út egyik tétele",
      "a tétel egy laptop-dokkoló, amelyet az út előtt vettem a terepi laptopomhoz, és a cég leltárába került", ["dokkoló", "leltár"]),
     ("one item from the Worcester customer service trip",
      "the item is a laptop docking station I bought before the trip for my field laptop, and it was added to the company asset register",
      ["docking station", "asset register"])),
    # --- utazás ← előfizetés: platformdíjnak tűnő tétel; a jel: a platformon fizetett szállás vagy jegy
    ("F67", "teszt", "U", "S", "U",
     ("egy online foglalási platformon fizetett díj",
      "a díj a platformon foglalt szállásé a két éjszakás szegedi kiküldetésemhez; a platform használata ingyenes", ["szállás", "ingyenes"]),
     ("a fee paid on an online booking platform",
      "the fee is for the accommodation I booked on the platform for my two-night business trip to Southampton; using the platform is free",
      ["accommodation", "free"])),
    ("F68", "teszt", "U", "S", "U",
     ("egy mobilalkalmazásban fizetett díj",
      "a díj a pécsi kiküldetéshez az alkalmazásban vett vonatjegy ára; az alkalmazásnak nincs havi vagy éves díja", ["vonatjegy", "nincs havi"]),
     ("a fee paid in a mobile app",
      "the fee is the price of the train ticket for the Leicester business trip, bought in the app; the app has no monthly or annual fee",
      ["train ticket", "no monthly"])),
    ("F69", "tanito", "U", "S", "U",
     ("egy utazási szolgáltatónak fizetett összeg",
      "a kért összeg a szolgáltatón keresztül a saját kétnapos miskolci üzleti kiküldetésemre foglalt szálloda ára; tagsági "
      "vagy rendszerhasználati díj nincs benne", ["szálloda", "kiküldetés", "kétnapos"]),
     ("an amount paid to a travel service provider",
      "the amount claimed is the price of the hotel booked through the provider for my own two-day business trip to Bradford; "
      "it includes no membership or system-access fee", ["hotel", "business trip", "two-day"])),
    ("F70", "tanito", "U", "S", "U",
     ("egy parkolási alkalmazásban fizetett díj",
      "a díj a veszprémi kiküldetés két napjának parkolása a megrendelő telephelye előtt", ["két nap", "telephely"]),
     ("a fee paid in a parking app",
      "the fee is the parking for the two days of the Gloucester business trip outside the client's site", ["two days", "client's site"])),
    # --- előfizetés ← utazás: úthoz kapcsolódó szolgáltatónak fizetett díj; a jel: a napi munkához használt szoftver díja
    ("F71", "teszt", "S", "U", "S",
     ("egy utazáshoz kapcsolódó alkalmazás díja",
      "a díj egy útvonaltervező szakmai szoftver évente megújuló hozzáférése, amelyet a fuvarszervezőink a napi munkához használnak; utazás "
      "nem kapcsolódik hozzá", ["fuvarszervező", "útvonaltervező"]),
     ("the fee for a travel-related app",
      "the fee is the annually renewed access to professional route-planning software that our transport planners use in daily work; no "
      "travel is involved", ["transport planner", "route-planning"])),
    ("F72", "teszt", "S", "U", "S",
     ("egy vasúti szolgáltatónak fizetett összeg",
      "az összeg a vasúttársaság menetrendi adatszolgáltatásának havi díja, amelyet a logisztikai rendszerünk lekérdez; jegyet nem vettünk",
      ["adatszolgáltatás", "logisztikai rendszer"]),
     ("an amount paid to a rail operator",
      "the amount is the monthly fee for the rail operator's timetable data service, which our logistics system queries; no tickets were bought",
      ["data service", "logistics system"])),
    ("F73", "tanito", "S", "U", "S",
     ("egy taxitársaságnak fizetett havi díj",
      "a díj a taxitársaság diszpécserszoftverének havi használati díja, amellyel a saját futárainkat irányítjuk; fuvart nem rendeltünk",
      ["diszpécser", "futár"]),
     ("a monthly fee paid to a taxi company",
      "the fee is the monthly charge for using the taxi company's dispatch software, with which we direct our own couriers; no rides were ordered",
      ["dispatch", "courier"])),
    ("F74", "tanito", "S", "U", "S",
     ("egy utazási iroda számlája",
      "a számla az iroda üzleti utazáskezelő szoftverének éves használati díjáról szól, amelyben a munkatársak maguk foglalnak; utazást a "
      "számla nem tartalmaz", ["utazáskezelő szoftver", "maguk foglalnak"]),
     ("an invoice from a travel agency",
      "the invoice is for the annual usage fee of the agency's business travel management software, in which staff make their own bookings; "
      "it includes no trips", ["travel management software", "own bookings"])),
    # --- képzés ← eszköz: géphez kapcsolódó tétel; a jel: a kezelők tanfolyama vagy vizsgája
    ("F75", "teszt", "K", "E", "Kt",
     ("egy hegesztőkészülékhez kapcsolódó tétel",
      "a tétel két hegesztőnk minősítő tanfolyamának vizsgadíja; a készüléket a cég korábban megvette", ["minősítő", "vizsgadíj"]),
     ("an item related to a welding machine",
      "the item is the exam fee for the qualification course of two of our welders; the company bought the machine earlier",
      ["qualification course", "exam fee"])),
    ("F76", "teszt", "K", "E", "K",
     ("egy 3D-nyomtatóhoz kapcsolódó tétel",
      "a tétel a nyomtató forgalmazója által tartott kétnapos kezelői oktatás díja, amelyet a műszaki csapat két tagja tanúsítvánnyal végzett el",
      ["kezelői oktatás", "tanúsítv"]),
     ("an item related to a 3D printer",
      "the item is the fee for the two-day operator training run by the printer's distributor, completed with a certificate by two members "
      "of the technical team", ["operator training", "certificate"])),
    ("F77", "tanito", "K", "E", "Kt",
     ("egy emelőkosaras géphez kapcsolódó tétel",
      "a tétel a karbantartóink emelőgép-kezelői tanfolyamának díja; a géppel a vizsgán gyakoroltak, de a gép a bérbeadóé",
      ["emelőgép-kezelői", "bérbeadó"]),
     ("an item related to a cherry picker",
      "the item is the fee for our maintenance staff's lifting platform operator course; they practised on the machine for the exam, but the "
      "machine belongs to the rental company", ["operator course", "rental company"])),
    ("F78", "tanito", "K", "E", "Kt",
     ("egy oszcilloszkóphoz kapcsolódó tétel",
      "a tétel a műszergyártó egynapos mérési tanfolyama, amelyen a két tesztmérnökünk vett részt; az oszcilloszkóp a laborunké",
      ["mérési tanfolyam", "tesztmérnök"]),
     ("an item related to an oscilloscope",
      "the item is the instrument maker's one-day measurement course attended by our two test engineers; the oscilloscope is our lab's",
      ["measurement course", "test engineer"])),
    # --- eszköz ← képzés: képzéshez kapcsolódó tétel; a jel: a kért összeg egy leltárba vett eszköz
    ("F79", "teszt", "E", "K", "Ei",
     ("a belső oktatásokhoz kapcsolódó egyik tétel",
      "a tétel egy interaktív tábla ára, amelyet leltári számmal a tárgyalóban szereltünk fel", ["interaktív tábla", "leltári szám"]),
     ("one of the items related to internal training sessions",
      "the item is the price of an interactive whiteboard, which was installed in the meeting room with an asset tag",
      ["interactive whiteboard", "asset tag"])),
    ("F80", "teszt", "E", "K", "Es",
     ("egy szakmai tanfolyamhoz kapcsolódó tétel",
      "a tétel a tanfolyamon használt mérőkészlet, amelyet a cég megvett, és azóta leltári számmal a minőségellenőrök napi eszköze",
      ["mérőkészlet", "leltári szám"]),
     ("an item related to a professional course",
      "the item is the measuring kit used on the course, which the company bought and which, with an asset tag, has since been the quality "
      "inspectors' daily tool", ["measuring kit", "asset tag"])),
    ("F81", "tanito", "E", "K", "Ei",
     ("a gyakornoki programhoz kapcsolódó egyik tétel",
      "a tétel három laptop ára, amelyeket a gyakornokok munkaállomásaként vettünk, és leltárba kerültek", ["laptop", "munkaállomás"]),
     ("one of the items related to the internship programme",
      "the item is the price of three laptops bought as the interns' workstations and added to the asset register", ["laptops", "workstation"])),
    ("F82", "tanito", "E", "K", "Es",
     ("a forgácsolási képzéshez kapcsolódó egyik tétel",
      "a kért összeg a számlán külön feltüntetett esztergakés-készlet vételára. A készlet a műhely szerszámnyilvántartásába "
      "került, és azóta a gyártás használja; részvételi díj nincs ebben a tételben", ["esztergakés", "szerszámnyilvántart"]),
     ("one of the items related to the machining training",
      "the amount claimed is the separately itemised purchase price of a set of lathe tools. The set was entered in the "
      "workshop's tool register and has been used by production since; this item includes no attendance fee",
      ["lathe tools", "tool register"])),
    # --- reprezentáció ← előfizetés: előfizetésnek tűnő díj; a jel: üzleti partner kapta ajándékba
    ("F83", "teszt", "R", "S", "Ra",
     ("egy műszaki szakfolyóirat videótárának éves hozzáférése",
      "a hozzáférés aktiváló kódját az évzáró találkozón térítésmentesen átadtuk legnagyobb megrendelőnk ügyvezetőjének, "
      "köszönőlevéllel; a kódot ő használja, nem a saját munkatársaink", ["évzáró", "térítésmentes", "megrendelő"]),
     ("annual access to the video library of a technical trade journal",
      "at the year-end meeting, we gave the access activation code to the managing director of our largest client, free of "
      "charge, with a thank-you letter; the code is for his use, not for our own staff",
      ["year-end", "free of charge", "largest client"])),
    ("F84", "teszt", "R", "S", "Ra",
     ("egy szakmai hírlevél éves díja",
      "a díjat a partnerünk három beszerzőjének fizettük ki köszönetként az együttműködésért, mi magunk nem olvassuk", ["köszönet", "beszerző"]),
     ("the annual fee for a professional newsletter",
      "we paid the fee for three of our partner's buyers as a thank-you for the cooperation; we do not read it ourselves", ["thank-you", "buyers"])),
    ("F85", "tanito", "R", "S", "Ra",
     ("egy online szakmai magazincsomag éves hozzáférési díja",
      "az éves hozzáférés kódjait karácsonyi üdvözlőlappal, térítésmentesen elküldtük beszállítóink tíz kapcsolattartójának, "
      "személyes használatra", ["karácsony", "kapcsolattartó", "térítésmentes"]),
     ("the annual access fee for a bundle of online professional magazines",
      "we sent the annual access codes to ten contacts at our suppliers, free of charge, with Christmas cards, for their "
      "personal use", ["christmas", "contacts", "free of charge"])),
    ("F86", "tanito", "R", "S", "Ra",
     ("egy edzésprogram-alkalmazás éves díja",
      "az éves hozzáférés kódjait térítésmentesen átadtuk partnercégünk kapcsolattartóinak, köszönetként az egész éves közös "
      "munkáért; nem versenydíj vagy szerződéses juttatás volt", ["partnercég", "kapcsolattartó", "térítésmentes"]),
     ("the annual fee for a fitness app",
      "we gave the annual access codes to our contacts at the partner company, free of charge, as a thank-you for the year's "
      "work together; they were neither competition prizes nor contractual benefits",
      ["partner company", "contacts", "free of charge"])),
    # --- előfizetés ← reprezentáció: ajándéknak vagy vendéglátásnak tűnő tétel; a jel: a saját napi munka szoftvere
    ("F87", "teszt", "S", "R", "S",
     ("egy kódkártya-csomag vásárlása",
      "a kártyák egy szakmai jogtár éves hozzáférésének aktiváló kódjai, amelyeket a saját jogászaink használnak a napi munkában",
      ["jogtár", "aktiváló"]),
     ("the purchase of a pack of code cards",
      "the cards are activation codes for annual access to a professional legal database used by our own lawyers in daily work",
      ["legal database", "activation"])),
    ("F88", "teszt", "S", "R", "S",
     ("egy étteremfoglaló szolgáltatás díja",
      "a díj a foglalószoftver havi díja, amellyel a saját éttermünk asztalfoglalásait kezeljük; mi magunk nem foglaltunk",
      ["asztalfoglalás", "saját éttermünk"]),
     ("the fee for a restaurant booking service",
      "the fee is the monthly charge for the booking software with which we manage table reservations at our own restaurant; we made no "
      "bookings ourselves", ["table reservations", "our own restaurant"])),
    ("F89", "tanito", "S", "R", "S",
     ("egy rendezvényszervező platform díja",
      "a díj a platform jegyértékesítő moduljának éves hozzáférése, amellyel a saját fizetős szakmai előadásainkra árulunk jegyet",
      ["jegyértékesítő", "fizetős"]),
     ("the fee for an event platform",
      "the fee is the annual access to the platform's ticketing module, which we use to sell tickets for our own paid professional talks",
      ["ticketing module", "paid"])),
    ("F90", "tanito", "S", "R", "S",
     ("egy ajándéktárgyakat is kínáló online platformhoz kapcsolódó díj",
      "a kért összeg a platformtól bérelt webáruházmotor havi szoftverlicence, amellyel a saját reklámtermékeinket "
      "értékesítjük; termékvásárlást nem tartalmaz", ["webáruházmotor", "reklámtermék", "szoftverlicenc"]),
     ("a fee relating to an online platform that also offers gift items",
      "the amount claimed is the monthly software licence for the platform's online shop engine, which we use to sell our own "
      "promotional products; it includes no product purchase", ["shop engine", "promotional products", "software licence"])),
]


# a gold költségnem leírásának szavai: a jel „szó szerinti”, ha ezek egyike szerepel benne, különben „áttételes” (leíró
# bontás a K1(b) és a Gemma mellett; G1-rögzítés 13.2, Dani 11-04)
SZO_SZERINT = {"utazás": ["kiküldetés", "utazás", "szállás", "útiköltség"], "travel": ["business trip", "travel", "accommodation"],
               "reprezentáció": ["vendéglát", "vendégül", "ajándék"], "entertainment": ["entertain", "gift", "hosted"],
               "képzés": ["képzés", "tanfolyam", "konferencia"], "training": ["training", "course", "conference"],
               "eszköz": ["munkaeszköz", "számítástechnik", "szerszám"], "equipment": ["work equipment", "tool"],
               "előfizetés": ["előfizet", "szoftver"], "subscription": ["software", "subscri"]}


def jel_fajta(f: dict) -> str:
    """„szó szerint” / „áttételes”: a (`forgatokonyvek` alakú) forgatókönyv jele kimondja-e a gold leírásának egy szavát."""
    return "szó szerint" if any(w in f["jel2"].lower() for w in SZO_SZERINT[f["gold"]]) else "áttételes"


def jel_fajtak() -> dict[tuple[str, str], str]:
    """(forgatókönyv-id, nyelv) → jelfajta."""
    return {(f["id"], lang): jel_fajta(f) for lang, fs in forgatokonyvek().items() for f in fs}


# a generátor minden szövegében előforduló sablonszöveg: kulcsszó nem lehet a része (a tényellenőrző részszót keres)
SABLONSZOVEG = ("pelda.example",)


def kulcs_of(gold: str, lang: str, helyzet: str) -> list[str]:
    """A gold árulkodó szavai, a helyzetben szereplők nélkül (az (a) a helyzetet mindig tartalmazza)."""
    h = helyzet.lower()
    return [k for k in ARULKODO[gold][0 if lang == "hu" else 1] if k.lower() not in h]


def forgatokonyvek(szelet: str | None = None) -> dict[str, list[dict]]:
    """A `ertelmezes08_szab.FORGATOKONYV` + `JEL2` alakjában, nyelvenként (a `szint08e.plan_e` / `kieg2` olvassa)."""
    out: dict[str, list[dict]] = {"hu": [], "en": []}
    for fid, sz, g, c, t, hu, en in F:
        if szelet and sz != szelet:
            continue
        for n, (lang, (helyzet, jel2, kulcs2)) in enumerate((("hu", hu), ("en", en))):
            out[lang].append({"id": fid, "szelet": sz, "gold": NEV[g][n], "csali": NEV[c][n], "helyzet": helyzet,
                              "jel": jel2, "kulcs": kulcs_of(g, lang, helyzet), "jel2": jel2, "kulcs2": kulcs2,
                              "tamasz": TAMASZ[t][n]})
    return out


def ellenoriz() -> list[str]:
    """Szerkezeti ellenőrzés: darabszám, párok, a kulcs2 nem szerepel a helyzetben, a helyzetek egyediek és a G1b-éitől
    különböznek."""
    import ertelmezes08_szab as SZ  # noqa: PLC0415
    hibak = []
    ids = [x[0] for x in F]
    if len(ids) != 90 or len(set(ids)) != 90:
        hibak.append(f"az id-k száma {len(set(ids))}, nem 90")
    if not JAVITVA <= set(ids):
        hibak.append(f"ismeretlen javított id: {sorted(JAVITVA - set(ids))}")
    sz = Counter(x[1] for x in F)
    if sz != {"teszt": 40, "tanito": 50}:
        hibak.append(f"a szeletek: {dict(sz)}")
    par = Counter((x[2], x[3]) for x in F if x[1] == "teszt")
    if len(par) != 20 or set(par.values()) != {2}:
        hibak.append(f"a tesztben nem minden rendezett pár kétszer: {dict(par)}")
    regi = {f["helyzet"].lower() for lang in SZ.FORGATOKONYV for f in SZ.FORGATOKONYV[lang]}
    for lang in ("hu", "en"):
        fk = forgatokonyvek()[lang]
        if len({f["helyzet"] for f in fk}) != len(fk):
            hibak.append(f"{lang}: ismétlődő helyzet")
        for f in fk:
            if f["helyzet"].lower() in regi:
                hibak.append(f"{f['id']} {lang}: a helyzet a G1b-é")
            if f["gold"] == f["csali"]:
                hibak.append(f"{f['id']}: a gold és a csali azonos")
            for k in f["kulcs"] + f["kulcs2"]:
                if any(k.lower() in b for b in SABLONSZOVEG):
                    hibak.append(f"{f['id']} {lang}: a kulcsszó „{k}” a generált sablonszövegben is szerepel")
            for k in f["kulcs2"]:
                if k.lower() in f["helyzet"].lower():
                    hibak.append(f"{f['id']} {lang}: a kulcs2 „{k}” a helyzetben")
                if k.lower() not in f["jel2"].lower():
                    hibak.append(f"{f['id']} {lang}: a kulcs2 „{k}” nincs a jelben")
    return hibak


def lap() -> str:
    import sys as _s  # noqa: PLC0415
    _s.path[:0] = [str(EXP / "kor06/eszkozok"), str(EXP / "eszkozok")]
    import szint06 as S6  # noqa: PLC0415
    o = ["# G2 — a szabálycsalád friss értelmezési forgatókönyvei (átnézésre)", "",
         f"**2. kör (11-03):** az első körben 64 rendben, 26 javítandó. A {len(JAVITVA)} javított forgatókönyv (a címsorban: "
         "„javítva”) szövege a te csereszöveged, csak a generátor promptjának alakjára igazítva (kisbetűs kezdés, záró pont "
         "nélkül, egyenes aposztróf); a kulcsszavakat újraillesztettem (a jel tövei, a helyzetben nem szerepelnek). Ezekre "
         "kérek ítéletet; a többi változatlan.", "",
         "**Mit kérek:** forgatókönyvenként egy ítéletet (rendben / javítandó / kihagyandó), javításnál a javasolt szöveget. Szempontok:",
         "", "1. **(a), csak a helyzet:** a lenti öt szabálypont-leírás alapján a gold és a csali közt valóban **eldönthetetlen** "
         "(a helyzet ne a költségnem leírásának szavaival nevezze meg a kiadást, és ne húzzon egyértelműen egyik felé sem).",
         "2. **(b), a helyzet + a jel:** a jelből a gold **egy lépésben** következik a szabálypont szövegéből (a „támasz”), és a "
         "csali kizárt.", "3. A két nyelvi változat ugyanazt a döntést adja; a magyar utazás belföldi.",
         "4. A helyzet természetes költségelszámolási tétel; az összeg a generáláskor a szabálypont küszöbéhez igazodik.", "",
         "A G1b 12 forgatókönyvétől diszjunktak; a D7 audit tanulságai (Dani 11-02) beépítve: a jel a kért összeg tárgyát mondja ki, "
         "belső címzettnek adott tárgy nem ajándék, egyedül elköltött étkezés nem vendéglátás. A generátor a jelet a saját szavaival "
         "írja át, a költségnemet nem nevezi meg; a (b)-ben a kulcsszavak egyikének szerepelnie kell, az (a)-ban egyiknek sem "
         "(tényellenőrző).", "", "**Az öt szabálypont-leírás:**", ""]
    for k in "URKES":
        hu, en = NEV[k]
        o.append(f"- **{hu}:** {S6.SZAB_TIPUS['hu'][hu]} · *{en}: {S6.SZAB_TIPUS['en'][en]}*")
    o += ["", "40 teszt-forgatókönyv (mind a 20 rendezett párra 2) és 50 tanító-forgatókönyv (mind a 20 párra 2, és 10 a "
          "legtermészetesebb párokra). Egy forgatókönyvből a tesztben nyelvenként 7, a tanításban 5 egység készül, mindegyik "
          "1 (a) + 3 (b) változattal.", ""]
    pr = None
    for fid, sz, g, c, t, hu, en in F:
        if (g, c) != pr:
            o += [f"## {NEV[g][0]} ← {NEV[c][0]} (gold ← csali)", ""]
            pr = (g, c)
        jv = " · **javítva (11-03)**" if fid in JAVITVA else ""
        o += [f"### {fid} · {'teszt' if sz == 'teszt' else 'tanító'} · támasz: „{TAMASZ[t][0]}” / „{TAMASZ[t][1]}”{jv}", "",
              "| | (a) helyzet | (b) jel (a helyzet mellé) | kulcsszavak |", "|---|---|---|---|",
              f"| hu | {hu[0]} | {hu[1]} | {', '.join(hu[2])} |", f"| en | {en[0]} | {en[1]} | {', '.join(en[2])} |", "",
              "Ítélet: ", ""]
    return "\n".join(o) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    l_ = sub.add_parser("lap")
    l_.add_argument("--out", required=True)
    sub.add_parser("ellenoriz")
    a = ap.parse_args()
    sys.path[:0] = [str(HERE)]
    h = ellenoriz()
    if h:
        raise SystemExit("\n".join(h))
    if a.cmd == "lap":
        out = EXP / a.out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(lap(), encoding="utf-8")
        print(f"→ {out.relative_to(EXP)}")
    else:
        print("rendben: 90 forgatókönyv (40 teszt, 50 tanító), mindkét nyelven")


if __name__ == "__main__":
    main()
