#!/usr/bin/env python3
"""D5 — a „nagy csomag”: D1+M1+M2+D2+D3+D4 összefűzve, töltelék-fejezetekkel 60–90k karakterre.

A T10 (szinonim tű) három célténye a töltelékbe van beágyazva, ELÖL / KÖZÉPEN / VÉGÉN.
A tényleges pozíciót a szkript MÉRI és kiírja — nem állítjuk, hanem megmutatjuk.
Minden célténynél a kérdés kulcsszava SZÁNDÉKOSAN nem szerepel a célmondatban,
viszont szerepel máshol, más jelentésben (near-miss).
"""
from pathlib import Path
import re

C = Path("corpus")

# --- a három céltény (T10) ---
T10_1 = ("**2.4.** A parkolóhely-használati hozzájárulás mértéke a jelen ÁSZF hatálybalépésekor "
         "havi 12 000 Ft/parkolóhely. A hozzájárulás **éves korrekciója** minden év "
         "**március 1. napjával, 4 %** mértékben történik.")
T10_2 = ("**5.7.** A gépészeti karbantartási ciklus **zárónapja** minden naptári évben "
         "**szeptember 15.** Az ezt követően jelzett igényeket az Üzemeltető a következő ciklusba sorolja.")
T10_3 = ("**9.3.** A hulladékkezelési hozzájárulás mértéke **havi 46 000 Ft**, amelyet az Üzemeltető "
         "a tárgyhót követő hónap 10. napjáig számláz ki.")

# --- near-miss csapdák: a kérdés kulcsszava máshol, MÁS jelentésben ---
NEARMISS = {
    "emelés": ("**7.2.** A **teheremelő** berendezés kezelése kizárólag érvényes emelőgép-kezelői "
               "jogosítvánnyal történhet. Az **emelés** megkezdése előtt a teherbírási táblát ellenőrizni kell; "
               "3 tonna feletti **emelés** csak második személy jelenlétében végezhető."),
    "befejezés": ("**4.6.** A napi takarítás **befejezése** után a takarítószemélyzet a folyosói világítást "
                  "lekapcsolja. A takarítás **befejezésének** tényét a takarítási naplóban rögzíteni kell."),
    "szállítás": ("**6.1.** Az áru **szállítása** kizárólag a 3-as kapun keresztül történhet. A **szállítást** "
                  "végző jármű a rakodóudvarban legfeljebb 45 percet tartózkodhat."),
}

def toltelek(cim, pontok):
    L = [f"\n## {cim}\n"]
    L += pontok
    return "\n\n".join(L) + "\n"

ASZF_ELEJE = toltelek("ÁLTALÁNOS SZERZŐDÉSI FELTÉTELEK — I. Bevezető rendelkezések", [
    "**1.1.** A jelen Általános Szerződési Feltételek (a továbbiakban: ÁSZF) a Kavicspart Ingatlanhasznosító Kft. mint Üzemeltető által üzemeltetett ipari ingatlanok használatának általános feltételeit tartalmazzák.",
    "**1.2.** Az ÁSZF rendelkezései a bérleti szerződés elválaszthatatlan részét képezik. Az egyedi bérleti szerződés és az ÁSZF eltérése esetén az egyedi szerződés rendelkezése az irányadó.",
    "**1.3.** Az Üzemeltető az ÁSZF-et egyoldalúan módosíthatja, a módosítás hatálybalépését megelőzően legalább 30 nappal írásban közölve.",
    "**1.4.** A jelen ÁSZF alkalmazásában Használó minden olyan természetes vagy jogi személy, aki az ingatlan területén jogszerűen tartózkodik.",
    "**1.5.** Az ÁSZF hatálya a teljes ingatlanra, a közös területekre és a parkolóra egyaránt kiterjed.",
])

ASZF_PARKOLO = toltelek("ÁSZF — II. Parkolás és területhasználat", [
    "**2.1.** A parkolóhelyek kijelöléséről az Üzemeltető gondoskodik. A kijelölés évente felülvizsgálatra kerül.",
    "**2.2.** A parkolóhelyek használata kizárólag a kijelölt Használó és alkalmazottai számára engedélyezett.",
    "**2.3.** A parkolóban a megengedett legnagyobb sebesség 10 km/h.",
    T10_1,
    "**2.5.** A parkolóhely-használati jog harmadik személyre nem ruházható át.",
    "**2.6.** Az Üzemeltető a parkolóban hagyott gépjárművekben keletkezett károkért felelősséget nem vállal.",
    "**2.7.** A rakodóudvar nem parkolóhely; ott a gépjárművek kizárólag rakodás idejére állhatnak meg.",
])

HAZIREND = toltelek("HÁZIREND — Munkavédelem és rakodás", [
    "**7.1.** A csarnok területén védősisak és védőcipő viselése kötelező.",
    NEARMISS["emelés"],
    "**7.3.** A raklapok legfeljebb három sorban tárolhatók egymáson.",
    "**7.4.** A közlekedési utakat szabadon kell hagyni; a sárga felfestésen tárolni tilos.",
    "**7.5.** Tűzoltó készülékek elé anyagot elhelyezni tilos.",
    "**7.6.** A munkavédelmi oktatás évente kötelező, elmulasztása a belépési jogosultság felfüggesztését vonja maga után.",
])

HAZIREND_TAKARITAS = toltelek("HÁZIREND — Takarítás és hulladék", [
    "**4.1.** A közös területek takarításáról az Üzemeltető gondoskodik.",
    "**4.2.** A bérlemény belső takarítása a Használó feladata.",
    "**4.3.** A takarítás időpontja munkanapokon 18:00 és 21:00 között van.",
    "**4.4.** A takarítószemélyzet a bérleményekbe kizárólag kísérettel léphet be.",
    "**4.5.** A veszélyes hulladék gyűjtése kizárólag a kijelölt konténerben történhet.",
    NEARMISS["befejezés"],
    "**4.7.** A szelektív gyűjtőedények ürítése hetente kétszer történik.",
])

USEM = toltelek("ÜZEMELTETÉSI SZABÁLYZAT — Karbantartás", [
    "**5.1.** Az Üzemeltető éves karbantartási tervet készít, amelyet minden év január 31-ig megküld a Használóknak.",
    "**5.2.** A tervezett karbantartás időpontjáról az Üzemeltető legalább 5 nappal előre értesítést küld.",
    "**5.3.** A rendkívüli karbantartás előzetes értesítés nélkül is elvégezhető, ha az élet- vagy vagyonbiztonság ezt indokolja.",
    "**5.4.** A karbantartási munkák idejére a Használó köteles a hozzáférést biztosítani.",
    "**5.5.** A Használó saját eszközeinek karbantartásáról maga gondoskodik.",
    "**5.6.** A karbantartási igényeket írásban, az üzemeltetési portálon keresztül kell bejelenteni.",
    T10_2,
    "**5.8.** A karbantartási napló a portán tekinthető meg.",
])

SZALLITAS = toltelek("ÜZEMELTETÉSI SZABÁLYZAT — Beléptetés és szállítás", [
    NEARMISS["szállítás"],
    "**6.2.** A beléptetés kizárólag érvényes kártyával történhet; a kártya át nem adható.",
    "**6.3.** Vendégek fogadása a portán történő bejelentkezéssel lehetséges.",
    "**6.4.** A kapuk nyitvatartása munkanapokon 6:00–20:00.",
    "**6.5.** A munkaidőn kívüli belépést előzetesen be kell jelenteni.",
    "**6.6.** A kamerarendszer felvételeit az Üzemeltető 30 napig őrzi meg.",
])

IRATKEZELES = toltelek("IRATKEZELÉSI ÉS ADATVÉDELMI TÁJÉKOZTATÓ", [
    "**8.1.** Az Üzemeltető a Használókkal kapcsolatos iratokat elektronikusan kezeli.",
    "**8.2.** A számviteli bizonylatokat a jogszabályban előírt ideig őrzi meg.",
    "**8.3.** A vitatott iratok **letétbe** helyezése az Üzemeltető ügyvédjénél történik; a letéti díj a letevőt terheli.",
    "**8.4.** Az adatkezelés jogalapja a szerződés teljesítése.",
    "**8.5.** A Használó az adatkezelésről tájékoztatást kérhet.",
])

KOZUZEM = toltelek("KÖZÜZEMI ÉS HULLADÉKKEZELÉSI RENDELKEZÉSEK", [
    "**9.1.** A közüzemi szolgáltatások almérők szerint kerülnek elszámolásra.",
    "**9.2.** Az almérők leolvasása minden hónap utolsó munkanapján történik.",
    T10_3,
    "**9.4.** A hulladékkezelési hozzájárulás a konténerhasználatot és az elszállítást is fedezi.",
    "**9.5.** A veszélyes hulladék elszállítása külön megrendelés alapján, külön díj ellenében történik.",
])


TUZVEDELEM = toltelek("TŰZVÉDELMI SZABÁLYZAT", [
    "**10.1.** A telephely tűzvédelmi osztályba sorolása: D kategória, mérsékelten tűzveszélyes.",
    "**10.2.** A tűzvédelmi felelős személyét az Üzemeltető jelöli ki, nevét a portán kifüggesztett tájékoztató tartalmazza.",
    "**10.3.** Nyílt lánggal járó tevékenység (hegesztés, vágás, forrasztás) kizárólag előzetesen kiadott, írásbeli tűzgyújtási engedély birtokában végezhető. Az engedély legfeljebb egy műszakra adható ki.",
    "**10.4.** A tűzgyújtási engedélyt a munka megkezdése előtt legalább 24 órával kell kérelmezni.",
    "**10.5.** A tűzveszélyes tevékenység befejezését követően a munkaterületet a felelős személy két órán át köteles felügyelni.",
    "**10.6.** A hordozható tűzoltó készülékek felülvizsgálata negyedévente, a nyomáspróba ötévente esedékes.",
    "**10.7.** A tűzriadó tervet évente legalább egyszer gyakorolni kell. A gyakorlatról jegyzőkönyv készül.",
    "**10.8.** A menekülési útvonalakat jelző világítás akkumulátoros üzemidejének legalább 60 percnek kell lennie.",
    "**10.9.** A tűzjelző rendszer hibája esetén az Üzemeltető haladéktalanul tűzvédelmi ügyeletet rendel el.",
    "**10.10.** A telephely területén dohányozni kizárólag a kijelölt, táblával megjelölt helyen szabad.",
    "**10.11.** Az elektromos berendezések érintésvédelmi felülvizsgálata háromévente kötelező.",
    "**10.12.** A tűzcsapok környezetében 1,5 méter sugarú körben tárolni tilos.",
])

KORNYEZET = toltelek("KÖRNYEZETVÉDELMI MELLÉKLET", [
    "**11.1.** A Használó köteles a tevékenységéből származó hulladékot a jogszabályi előírásoknak megfelelően gyűjteni, nyilvántartani és kezelésre átadni.",
    "**11.2.** A veszélyes hulladék gyűjtőhelyének kialakítása a Használó feladata; a gyűjtőhely kialakítását az Üzemeltetővel előzetesen egyeztetni kell.",
    "**11.3.** A csapadékvíz-elvezető rendszerbe technológiai szennyvizet bevezetni tilos.",
    "**11.4.** Az olajos vizek kezelésére a rakodóudvarban olajfogó műtárgy üzemel; annak tisztítása félévente történik.",
    "**11.5.** A telephelyen zajkibocsátási határérték: nappal 55 dB, éjjel 45 dB, a telekhatáron mérve.",
    "**11.6.** A Használó évente, január 31-ig köteles hulladékbevallást megküldeni az Üzemeltetőnek.",
    "**11.7.** A talajszennyezés gyanúját a Használó haladéktalanul köteles bejelenteni.",
    "**11.8.** Az Üzemeltető jogosult a Használó hulladékkezelési gyakorlatát évente egyszer, előzetes értesítés mellett ellenőrizni.",
    "**11.9.** Az energiahatékonysági auditban való részvétel a Használó számára ajánlott, de nem kötelező.",
    "**11.10.** A telephely villamosenergia-ellátásának 100 %-a igazoltan megújuló forrásból származik.",
])

MUSZAKI = toltelek("A VÁLLALKOZÁSI SZERZŐDÉS 1. SZ. MELLÉKLETE — MŰSZAKI TARTALOM", [
    "**M1.** Sűrített levegős hálózat: a meglévő horganyzott acél vezeték teljes cseréje présidomos rendszerű alumínium vezetékre, összesen 340 fm hosszban, 63 mm és 40 mm névleges átmérőben.",
    "**M2.** Kompresszorállomás: a meglévő két csavarkompresszor közül az egyik cseréje frekvenciaváltós, 22 kW teljesítményű egységre, hangszigetelt burkolattal.",
    "**M3.** Szárítóegység: hűtveszárító beépítése, +3 °C nyomásponttal, 3,5 m³/perc kapacitással.",
    "**M4.** Leágazások: 18 db új leágazási pont kialakítása gyorscsatlakozóval, mindegyiknél nyomásmérővel és golyóscsappal.",
    "**M5.** Csarnokfűtés: a meglévő négy darab gázsugárzó cseréje sötétsugárzókra, összesen 240 kW beépített teljesítménnyel.",
    "**M6.** Szabályozás: zónánkénti (négy zóna) hőmérséklet-szabályozás kiépítése, heti programozású termosztátokkal.",
    "**M7.** Gázellátás: a fűtőberendezésekhez tartozó gázvezeték-szakasz felülvizsgálata és szükség szerinti cseréje, legfeljebb 60 fm hosszban.",
    "**M8.** Elektromos elosztóhálózat: a 3-as és 4-es elosztószekrény teljes belső cseréje, új kismegszakítókkal és áram-védőkapcsolókkal.",
    "**M9.** Kábelezés: a csarnok keleti oldalán 12 db új háromfázisú csatlakozási pont kiépítése, kábeltálcás vezetéssel.",
    "**M10.** Világítás: a csarnokvilágítás LED-es átalakítása nem tárgya a jelen szerződésnek.",
    "**M11.** Dokumentáció: megvalósulási tervdokumentáció 3 példányban, nyomtatva és elektronikusan.",
    "**M12.** Próbaüzem: 72 órás folyamatos próbaüzem, mérési jegyzőkönyvvel.",
    "**M13.** Oktatás: a Megrendelő két munkavállalójának kezelői oktatása, legalább 4 óra időtartamban.",
    "**M14.** Garanciális bejárás: a teljesítést követő 6. és 12. hónapban, díjmentesen.",
])

BIZTONSAG = toltelek("VAGYONVÉDELMI ÉS BELÉPTETÉSI SZABÁLYZAT", [
    "**12.1.** A telephely őrzését az Üzemeltető által megbízott vagyonvédelmi szolgálat látja el, 0–24 órában.",
    "**12.2.** A beléptető rendszer minden belépést és kilépést naplóz; a napló megőrzési ideje 90 nap.",
    "**12.3.** Az elveszett beléptető kártya pótlási díja 4 500 Ft.",
    "**12.4.** A Használó köteles a munkaviszony megszűnését követő munkanapon a kártyát leadni.",
    "**12.5.** A telephelyre gépjárművel behajtani kizárólag a rendszám előzetes bejelentése után lehet.",
    "**12.6.** A portaszolgálat jogosult a kilépő gépjárművek rakterének szúrópróbaszerű ellenőrzésére.",
    "**12.7.** Az ellenőrzés megtagadása esetén a portaszolgálat a rendőrséget értesíti.",
    "**12.8.** A kamerarendszer 24 kamerával működik; a rögzítés folyamatos.",
    "**12.9.** Kamerafelvétel kiadása kizárólag hatósági megkeresésre történik.",
    "**12.10.** A telephely területén drónt üzemeltetni kizárólag az Üzemeltető írásbeli engedélyével szabad.",
])

PENZUGY = toltelek("SZÁMLÁZÁSI ÉS FIZETÉSI RENDELKEZÉSEK", [
    "**13.1.** Az Üzemeltető a bérleti díjról a tárgyhó első munkanapján állít ki számlát.",
    "**13.2.** A továbbszámlázott közüzemi díjakról az Üzemeltető külön számlát állít ki, a tárgyhót követő hónap 15. napjáig.",
    "**13.3.** A számlákat az Üzemeltető elektronikusan, a Használó által megadott e-mail-címre küldi meg.",
    "**13.4.** Az elektronikus számla befogadását a Használó a szerződés aláírásával elfogadja.",
    "**13.5.** Fizetési késedelem esetén az Üzemeltető a törvényes késedelmi kamatot és a behajtási költségátalányt érvényesíti.",
    "**13.6.** A behajtási költségátalány mértéke jogszabály szerinti, jelenleg 40 euró forintban kifejezett összege.",
    "**13.7.** A Használó a számlával szemben a kézhezvételtől számított 8 napon belül élhet kifogással.",
    "**13.8.** A kifogás a nem vitatott összeg megfizetésének kötelezettségét nem érinti.",
    "**13.9.** Az Üzemeltető évente egyszer, december 31-i fordulónappal egyenlegközlőt küld.",
    "**13.10.** A Használó a fizetéseket kizárólag banki átutalással teljesítheti; készpénzfizetés kizárt.",
])


ASZF_III = toltelek("ÁSZF — III. Szerződéskötés, módosítás, megszűnés", [
    "**3.1.** A bérleti jogviszony az egyedi bérleti szerződés mindkét fél általi aláírásával jön létre. Az Üzemeltető ajánlata — eltérő kikötés hiányában — az ajánlat keltétől számított 30 napig kötött.",
    "**3.2.** A Használó a szerződéskötést megelőzően köteles hitelt érdemlően igazolni képviseleti jogosultságát, valamint 30 napnál nem régebbi cégkivonattal és aláírási címpéldánnyal alátámasztani adatait.",
    "**3.3.** Az Üzemeltető a szerződéskötést indokolás nélkül megtagadhatja. A megtagadás miatt a Használót kártérítés nem illeti meg.",
    "**3.4.** A szerződés módosítása kizárólag írásban, a felek cégszerű aláírásával érvényes. Szóban, ráutaló magatartással vagy elektronikus levélváltással a szerződés nem módosítható.",
    "**3.5.** A szerződés megszűnik a határozott idő lejártával, közös megegyezéssel, rendkívüli felmondással, valamint a bérlemény megsemmisülésével.",
    "**3.6.** A szerződés megszűnésekor a Használó a bérleményt kiürített, rendeltetésszerű használatra alkalmas állapotban köteles visszaadni. Az általa létesített beépítéseket — az Üzemeltető eltérő rendelkezése hiányában — köteles elbontani és az eredeti állapotot helyreállítani.",
    "**3.7.** A visszaadásról átadás-átvételi jegyzőkönyv készül, amelyben a felek rögzítik a mérőállásokat és az esetleges hiányosságokat.",
    "**3.8.** Ha a Használó a bérleményt késedelmesen adja vissza, használati díjat köteles fizetni, amelynek mértéke a bérleti díj kétszerese, időarányosan.",
    "**3.9.** A megszűnést követően a Használó részére érkező küldeményeket az Üzemeltető 30 napig őrzi, azt követően visszaküldi a feladónak.",
    "**3.10.** A megszűnéskor fennálló tartozás a biztosítékokból közvetlenül kielégíthető.",
])

ENERGIA = toltelek("ÜZEMELTETÉSI SZABÁLYZAT — Energiagazdálkodás", [
    "**14.1.** Az Üzemeltető a telephely villamosenergia- és földgáz-beszerzését központosítottan, egyetemes szolgáltatáson kívüli, szabadpiaci szerződés keretében végzi.",
    "**14.2.** A Használók fogyasztása almérőkkel kerül meghatározásra. Az almérők hitelesítéséről az Üzemeltető gondoskodik; a hitelesítés költsége a Használókat a fogyasztás arányában terheli.",
    "**14.3.** Az almérők leolvasása havonta, a hónap utolsó munkanapján, elektronikus távleolvasással történik. Távleolvasási hiba esetén az Üzemeltető becsléssel él, amelyet a következő leolvasáskor korrigál.",
    "**14.4.** A közös területek fogyasztása a bérelt alapterület arányában kerül felosztásra.",
    "**14.5.** A csúcsidőszaki teljesítménydíj a mért legnagyobb negyedórás teljesítmény alapján kerül meghatározásra és felosztásra.",
    "**14.6.** A Használó köteles az általa üzemeltetett, 30 kW-nál nagyobb teljesítményfelvételű berendezés üzembe helyezését az Üzemeltetőnek előzetesen bejelenteni.",
    "**14.7.** Az Üzemeltető energiahatékonysági intézkedéseket vezethet be; ezek megtérülő költsége a Használókra továbbhárítható, legfeljebb az elért megtakarítás mértékéig.",
    "**14.8.** A telephelyen tilos olyan berendezést üzemeltetni, amely a hálózat feszültségminőségét a szabványos tűréshatáron kívülre viszi.",
    "**14.9.** A meddőenergia-fogyasztás miatti pótdíjat az azt okozó Használó viseli.",
    "**14.10.** Áramszünet esetén az Üzemeltető a szünetmentes ellátásért nem felel; a Használó saját szünetmentes áramforrásról maga gondoskodik.",
])

MINOSEG = toltelek("MINŐSÉGIRÁNYÍTÁSI MELLÉKLET", [
    "**15.1.** Az Üzemeltető integrált minőség- és környezetirányítási rendszert működtet.",
    "**15.2.** A rendszer hatálya kiterjed az ingatlanüzemeltetésre, a karbantartásra és a bérbeadási tevékenységre.",
    "**15.3.** A belső auditokat évente legalább egyszer, független auditor bevonásával kell lefolytatni.",
    "**15.4.** A nemmegfelelőségeket nyilvántartásba kell venni, és azokra 15 munkanapon belül helyesbítő intézkedést kell hozni.",
    "**15.5.** A helyesbítő intézkedés eredményességét a következő auditon értékelni kell.",
    "**15.6.** A Használók elégedettségét az Üzemeltető évente, kérdőíves felméréssel méri.",
    "**15.7.** A felmérés eredményét az Üzemeltető összesítve, anonimizáltan közzéteszi.",
    "**15.8.** A beszállítók értékelése évente történik, a szállítási pontosság, az ár és a minőség szempontjai szerint.",
    "**15.9.** A 3,0 alatti összesített értékelést kapott beszállítóval az Üzemeltető nem köt új szerződést.",
    "**15.10.** A dokumentumok kezelése verziókövetéssel történik; a hatályos verzió az üzemeltetési portálon érhető el.",
])

KOCKAZAT = toltelek("MUNKAVÉDELMI KOCKÁZATÉRTÉKELÉS — KIVONAT", [
    "**16.1.** A kockázatértékelés a telephely valamennyi munkahelyére és munkaeszközére kiterjed.",
    "**16.2.** A csarnoktérben azonosított fő kockázatok: elütés targoncával, leeső teher, zajterhelés, csúszás.",
    "**16.3.** Az elütés kockázatának csökkentése érdekében a gyalogos és a targoncaforgalom útvonalait fizikailag el kell választani.",
    "**16.4.** A targoncavezetők számára évenkénti időszakos orvosi alkalmassági vizsgálat kötelező.",
    "**16.5.** A zajterhelés a csarnoktérben 82 dB, ami hallásvédő eszköz biztosítását teszi szükségessé.",
    "**16.6.** A hallásvédő eszköz használata 85 dB felett kötelező, 80 dB felett biztosítandó.",
    "**16.7.** A csúszásveszély csökkentése érdekében a padozat csúszásmentesítő bevonatot kapott, amelynek felújítása háromévente esedékes.",
    "**16.8.** Az irodai munkahelyeken azonosított fő kockázat a képernyő előtti munkavégzés terhelése.",
    "**16.9.** A képernyő előtt napi 4 órát meghaladóan dolgozók számára kétévente szemészeti vizsgálat biztosítandó.",
    "**16.10.** A kockázatértékelést kétévente, illetve minden lényeges technológiai változás esetén felül kell vizsgálni.",
    "**16.11.** A soron következő felülvizsgálat esedékessége: 2027. március 31.",
])

PANASZ = toltelek("PANASZKEZELÉSI SZABÁLYZAT", [
    "**17.1.** A Használó panaszát írásban, az üzemeltetési portálon vagy e-mailben nyújthatja be.",
    "**17.2.** Az Üzemeltető a panasz beérkezését 2 munkanapon belül visszaigazolja.",
    "**17.3.** A panaszt az Üzemeltető 15 munkanapon belül érdemben kivizsgálja és írásban megválaszolja.",
    "**17.4.** Ha a kivizsgálás hosszabb időt vesz igénybe, az Üzemeltető erről a határidő lejárta előtt tájékoztatást ad, és új határidőt tűz, amely nem lehet hosszabb további 15 munkanapnál.",
    "**17.5.** A panasz elutasítása esetén az Üzemeltető az elutasítás indokát írásban közli.",
    "**17.6.** A Használó a válasz kézhezvételétől számított 15 napon belül másodfokú kivizsgálást kérhet az ügyvezetéstől.",
    "**17.7.** Az Üzemeltető a panaszokról nyilvántartást vezet, amelyet 5 évig megőriz.",
    "**17.8.** A panaszkezelés díjmentes.",
    "**17.9.** Az Üzemeltető a panaszstatisztikát évente összesíti és a minőségirányítási rendszer keretében értékeli.",
])

BIZTOSITAS = toltelek("BIZTOSÍTÁSI MELLÉKLET", [
    "**18.1.** Az Üzemeltető az ingatlanra vagyonbiztosítást tart fenn, amely a szerkezeti elemekre és az épületgépészetre terjed ki.",
    "**18.2.** Az Üzemeltető biztosítása a Használó ingóságaira, készleteire és technológiai berendezéseire NEM terjed ki.",
    "**18.3.** A Használó köteles saját vagyonára vagyonbiztosítást, továbbá tevékenységére felelősségbiztosítást kötni.",
    "**18.4.** A felelősségbiztosítás kártérítési limitje káreseményenként legalább 50 000 000 Ft, éves szinten legalább 100 000 000 Ft.",
    "**18.5.** A Használó a biztosítási kötvény másolatát a szerződéskötéskor, majd évente köteles az Üzemeltetőnek megküldeni.",
    "**18.6.** A biztosítás megszűnése esetén a Használó haladéktalanul, de legkésőbb 3 munkanapon belül köteles az Üzemeltetőt értesíteni.",
    "**18.7.** A biztosítás hiánya rendkívüli felmondási ok.",
    "**18.8.** A károk bejelentése a káresemény észlelésétől számított 2 munkanapon belül kötelező.",
    "**18.9.** Az önrész minden esetben a károkozót terheli.",
    "**18.10.** A biztosító regresszigénye esetén a felek együttműködnek a kárrendezésben.",
])


FOGALMAK = toltelek("FOGALOMMEGHATÁROZÁSOK", [
    "**F1. Bérlemény:** az egyedi bérleti szerződésben alaprajzzal és alapterülettel meghatározott, önálló használatra alkalmas ingatlanrész, a hozzá tartozó kizárólagos használatú területekkel együtt.",
    "**F2. Közös terület:** minden olyan terület, amely nem képezi egyetlen Használó kizárólagos használatának tárgyát sem, így különösen a folyosók, a lépcsőházak, a rakodóudvar, a porta és a parkoló.",
    "**F3. Használó:** a bérlő, továbbá minden olyan személy, aki a bérlő érdekkörében a telephely területén jogszerűen tartózkodik, ideértve a bérlő munkavállalóit, alvállalkozóit és látogatóit.",
    "**F4. Üzemeltető:** a Kavicspart Ingatlanhasznosító Kft., amely az ingatlan üzemeltetési feladatait ellátja.",
    "**F5. Bérleti díj:** az egyedi bérleti szerződésben meghatározott, a bérlemény használatáért fizetendő nettó ellenérték, a közüzemi és üzemeltetési költségek nélkül.",
    "**F6. Üzemeltetési költség:** a közös területek fenntartásával, takarításával, őrzésével, karbantartásával és biztosításával kapcsolatban felmerült, a Használókra felosztott költség.",
    "**F7. Almérő:** a Használó fogyasztásának mérésére szolgáló, a főmérő után beépített, hitelesített mérőeszköz.",
    "**F8. Tárgyhó:** az a naptári hónap, amelyre a szolgáltatás, illetve a díjfizetés vonatkozik.",
    "**F9. Munkanap:** a hétfőtől péntekig terjedő napok, kivéve a munkaszüneti napokat, valamint az áthelyezett pihenőnapokat; ideértve az áthelyezett munkanapokat.",
    "**F10. Rendkívüli felmondás:** a szerződésnek a másik fél súlyos szerződésszegése miatti, azonnali hatályú megszüntetése.",
    "**F11. Biztosíték:** az óvadék, a bankgarancia, továbbá minden olyan vagyoni fedezet, amelyet a Használó a szerződésből eredő kötelezettségei teljesítésének biztosítására nyújt.",
    "**F12. Készre jelentés:** a vállalkozó írásbeli nyilatkozata arról, hogy a munkát elvégezte és az átadás-átvételi eljárás megindítható.",
    "**F13. Próbaüzem:** a beépített berendezések rendeltetésszerű működésének folyamatos, mérésekkel dokumentált ellenőrzése.",
    "**F14. Megvalósulási dokumentáció:** a ténylegesen kivitelezett állapotot ábrázoló tervdokumentáció.",
])

GYIK = toltelek("BÉRLŐI KÉZIKÖNYV — GYAKORI KÉRDÉSEK", [
    "**GY1. Kihez fordulhatok műszaki hiba esetén?** Az üzemeltetési portálon nyitott hibajegy a leggyorsabb út. Sürgős, élet- vagy vagyonbiztonságot érintő esetben a portaszolgálat ügyeletét kell hívni, amely 0–24 órában elérhető.",
    "**GY2. Mikor kapom meg a havi számlát?** A bérleti díjról szóló számla a tárgyhó első munkanapján készül el, és elektronikusan érkezik. A továbbszámlázott közüzemi díjakról külön számla készül, a tárgyhót követő hónap közepéig.",
    "**GY3. Hogyan igényelhetek további parkolóhelyet?** Írásbeli igényt kell benyújtani az üzemeltetési portálon. Az Üzemeltető a szabad kapacitás függvényében, a beérkezés sorrendjében dönt.",
    "**GY4. Mit tegyek, ha elveszett a beléptető kártyám?** Haladéktalanul jelezni kell a portán, hogy a kártya letiltásra kerüljön. A pótlás díjköteles.",
    "**GY5. Végezhetek-e átalakítást a bérleményben?** Kizárólag az Üzemeltető előzetes írásbeli hozzájárulásával. A hozzájárulás iránti kérelemhez műszaki leírást és — ha jogszabály előírja — tervdokumentációt kell csatolni.",
    "**GY6. Ki felel a bérleményben tárolt árukészletemért?** A Használó. Az Üzemeltető vagyonbiztosítása a Használó ingóságaira nem terjed ki, ezért saját biztosítás megkötése szükséges.",
    "**GY7. Mi történik, ha késve fizetek?** Az Üzemeltető késedelmi kamatot és behajtási költségátalányt számít fel. Tartós késedelem esetén a biztosítékok érvényesíthetők, és a szerződés rendkívüli felmondással megszüntethető.",
    "**GY8. Milyen gyakran van karbantartás?** Az Üzemeltető éves karbantartási tervet készít, amelyet január végéig megküld. A tervezett munkákról előzetes értesítés érkezik.",
    "**GY9. Beléphetnek-e a bérleménybe a távollétemben?** Kizárólag életveszély, tűz, vízkár vagy hasonló, halasztást nem tűrő esetben, amelyről az Üzemeltető utólag írásban tájékoztat.",
    "**GY10. Hol találom a hatályos szabályzatokat?** Az üzemeltetési portálon, verziószámmal és hatálybalépési dátummal ellátva.",
    "**GY11. Hogyan mondhatom fel a szerződést?** A határozott idejű szerződés rendes felmondással nem szüntethető meg. Rendkívüli felmondásra a szerződésben meghatározott esetekben van mód.",
    "**GY12. Mi történik a szerződés végén az óvadékkal?** A bérlemény visszaadását és az elszámolást követően, az esetleges igényekkel csökkentve visszajár.",
])

VALTOZASJEGYZEK = toltelek("A SZABÁLYZATOK VÁLTOZÁSJEGYZÉKE", [
    "**V1.** 2023. január 1. — Az ÁSZF első kiadása.",
    "**V2.** 2023. július 1. — A parkolási rend kiegészítése az elektromos töltőállomások használatával.",
    "**V3.** 2024. január 1. — A hulladékkezelési rendelkezések átdolgozása a hatályos jogszabályi környezethez.",
    "**V4.** 2024. szeptember 1. — A beléptetési szabályzat kiegészítése a kamerarendszer bővítése miatt.",
    "**V5.** 2025. január 1. — A számlázási rendelkezések módosítása: áttérés a kizárólagos elektronikus számlázásra.",
    "**V6.** 2025. június 1. — A tűzvédelmi szabályzat felülvizsgálata, a tűzgyújtási engedély eljárásrendjének pontosítása.",
    "**V7.** 2026. január 1. — A minőségirányítási melléklet bevezetése.",
    "**V8.** 2026. május 1. — A munkavédelmi kockázatértékelés kivonatának csatolása.",
    "**V9.** A jelen iratcsomag a fenti változásokkal egységes szerkezetbe foglalt, hatályos szöveget tartalmazza.",
])


ALVALLALKOZO = toltelek("ALVÁLLALKOZÓI ÉS KIVITELEZÉSI REND", [
    "**19.1.** A Használó a bérlemény területén kivitelezési munkát kizárólag olyan alvállalkozóval végeztethet, akit az Üzemeltetőnek előzetesen, írásban bejelentett, és akinek adatait az Üzemeltető nyilvántartásba vette.",
    "**19.2.** A bejelentésnek tartalmaznia kell az alvállalkozó cégnevét, székhelyét, adószámát, a munka tárgyát és tervezett időtartamát, valamint a felelős műszaki vezető nevét és jogosultsági számát.",
    "**19.3.** Az Üzemeltető az alvállalkozó belépését megtagadhatja, ha az nem rendelkezik érvényes felelősségbiztosítással, vagy ha korábbi munkája során a házirendet ismételten megsértette.",
    "**19.4.** Az alvállalkozó munkavállalói a telephelyre kizárólag munkavédelmi oktatás elvégzését követően léphetnek be. Az oktatást az Üzemeltető tartja, díjmentesen, előzetes időpont-egyeztetés alapján.",
    "**19.5.** A kivitelezési munkák munkanapokon 7:00 és 18:00 között végezhetők. Zajos munkavégzés (bontás, vésés, ütvefúrás) kizárólag 9:00 és 16:00 között engedélyezett, a szomszédos Használók előzetes értesítése mellett.",
    "**19.6.** A munkaterületet a kivitelező köteles a környezetétől elhatárolni, és a por- és zajterhelést a lehető legkisebb mértékre szorítani.",
    "**19.7.** A kivitelezés során keletkezett hulladék elszállítása a kivitelező feladata. A telephely hulladékgyűjtő edényeinek használata kivitelezési hulladékra tilos.",
    "**19.8.** A közös területek szennyezése esetén az Üzemeltető a takarítás költségét a Használóra hárítja.",
    "**19.9.** A kivitelezés befejezését követően a Használó köteles a megvalósulási dokumentációt az Üzemeltetőnek átadni.",
    "**19.10.** A tűzvédelmi és gépészeti rendszereket érintő beavatkozás kizárólag az Üzemeltető által jóváhagyott szakvállalkozó útján végezhető.",
    "**19.11.** A kivitelezés idejére a Használó köteles a szokásosnál magasabb, legalább 20 000 000 Ft kártérítési limitű kivitelezői felelősségbiztosítást igazolni.",
    "**19.12.** A jelen fejezet megsértése súlyos szerződésszegésnek minősül.",
])

VIS_MAIOR = toltelek("VIS MAIOR ÉS ÜZEMZAVAR", [
    "**20.1.** Vis maiornak minősül minden olyan, a felek érdekkörén kívül eső, előre nem látható és el nem hárítható esemény, amely a szerződés teljesítését akadályozza, így különösen a természeti katasztrófa, a háború, a járvány miatti hatósági korlátozás, valamint az országos energiaellátási zavar.",
    "**20.2.** A vis maior tényét az arra hivatkozó fél köteles a másik féllel haladéktalanul, de legkésőbb 5 munkanapon belül írásban közölni, és annak fennállását hitelt érdemlően igazolni.",
    "**20.3.** A vis maior időtartama alatt a felek kötelezettségei szünetelnek, a bérleti díjfizetési kötelezettség kivételével, kivéve, ha a bérlemény használata teljes egészében lehetetlenné vált.",
    "**20.4.** Ha a vis maior 90 napot meghaladóan fennáll, bármelyik fél jogosult a szerződést azonnali hatállyal felmondani.",
    "**20.5.** Üzemzavarnak minősül a közüzemi szolgáltatás vagy az épületgépészeti rendszer előre nem tervezett kiesése.",
    "**20.6.** Üzemzavar esetén az Üzemeltető haladéktalanul intézkedik a helyreállításról, és a Használókat a várható időtartamról tájékoztatja.",
    "**20.7.** A 8 órát meghaladó, az Üzemeltetőnek felróható üzemzavar idejére a Használó időarányos díjcsökkentést igényelhet.",
    "**20.8.** A díjcsökkentés iránti igényt az üzemzavar megszűnésétől számított 15 napon belül, írásban kell bejelenteni.",
    "**20.9.** Az Üzemeltető nem felel a szolgáltató érdekkörében felmerült kiesésért.",
    "**20.10.** A felek vitás esetben közösen felkért, független műszaki szakértő véleményét kérik.",
])


JOGVITA = toltelek("JOGVITÁK RENDEZÉSE ÉS EGYÜTTMŰKÖDÉS", [
    "**21.1.** A felek a szerződésből eredő vitáikat elsősorban tárgyalásos úton, jóhiszeműen és a másik fél méltányos érdekeinek figyelembevételével kísérlik meg rendezni.",
    "**21.2.** A tárgyalásos rendezés kezdeményezése írásban történik, a vitatott kérdés pontos megjelölésével és az igény összegszerű megjelölésével.",
    "**21.3.** A felek a kezdeményezés kézhezvételétől számított 15 munkanapon belül egyeztetést tartanak. Az egyeztetésről emlékeztető készül, amelyet mindkét fél aláír.",
    "**21.4.** Ha az egyeztetés 30 napon belül nem vezet eredményre, a felek közvetítői eljárást vehetnek igénybe. A közvetítő személyében a feleknek egyet kell érteniük.",
    "**21.5.** A közvetítői eljárás költségeit a felek egyenlő arányban viselik, kivéve, ha másként állapodnak meg.",
    "**21.6.** A közvetítői eljárás sikertelensége esetén a felek a jelen szerződésben kikötött bíróság előtt érvényesíthetik igényüket.",
    "**21.7.** A jogvita fennállása alatt a felek a nem vitatott kötelezettségeiket teljesíteni kötelesek.",
    "**21.8.** A felek kötelezettséget vállalnak arra, hogy a szerződés teljesítése során tudomásukra jutott üzleti titkot megőrzik, és azt harmadik személynek nem adják ki.",
    "**21.9.** A titoktartási kötelezettség a szerződés megszűnését követő 5 évig fennmarad.",
    "**21.10.** A felek kapcsolattartóikat és azok elérhetőségét írásban jelölik ki. A kapcsolattartó személyének változásáról a másik felet 3 munkanapon belül értesíteni kell.",
    "**21.11.** A felek közötti írásbeli közlésnek minősül az elektronikus levél is, ha annak kézbesítését a címzett visszaigazolja, vagy ha a küldő fél tértivevényes postai küldeménnyel megismétli.",
    "**21.12.** A jelen szerződésre és a szabályzatokra a magyar jog az irányadó.",
])

ARCHIV = toltelek("KORÁBBI ÜZEMELTETÉSI TÁJÉKOZTATÓK — ARCHÍVUM", [
    "**A1.** *2025. március 4.* — Tájékoztatjuk Használóinkat, hogy a rakodóudvar burkolatának felújítása 2025. március 17. és április 4. között zajlik. Ezen időszakban a rakodás a 2-es kapun keresztül történik.",
    "**A2.** *2025. június 11.* — A nyári időszakban a portaszolgálat munkarendje nem változik. A hűtött italautomata a porta melletti előtérben üzemel.",
    "**A3.** *2025. szeptember 2.* — Az őszi karbantartási ciklus keretében a csarnokfűtés próbaüzemére 2025. szeptember 22-én kerül sor. A próbaüzem idejére a fűtésszabályozás a kezelők számára nem elérhető.",
    "**A4.** *2025. november 18.* — Felhívjuk a figyelmet, hogy a téli időszakban a járdák síkosságmentesítése reggel 6 órakor kezdődik. Kérjük, a korai érkezők fokozott figyelemmel közlekedjenek.",
    "**A5.** *2026. február 9.* — Az éves karbantartási terv megküldésre került. A tervet az üzemeltetési portálon is közzétettük.",
    "**A6.** *2026. április 20.* — A parkoló felfestésének megújítása 2026. május 4-én történik. Kérjük, ezen a napon a gépjárműveket a rakodóudvarban helyezzék el.",
    "**A7.** *2026. július 1.* — A nyári üzemszünet a telephelyen nem érinti a portaszolgálatot és a hulladékszállítást.",
    "**A8.** *2026. október 12.* — Az őszi tűzriadó-gyakorlat időpontja 2026. október 27., 10:00. A gyakorlaton minden Használó részvétele kötelező.",
    "**A9.** *2026. november 5.* — A beléptető rendszer szoftverfrissítése 2026. november 14-én, szombaton történik. A frissítés ideje alatt a belépés a portán, kézi nyilvántartással történik.",
    "**A10.** *2026. december 1.* — Az év végi ünnepek alatt a telephely nyitva tart, a portaszolgálat folyamatosan üzemel. Az üzemeltetési ügyelet elérhetősége változatlan.",
])

def load(n):
    return C.joinpath(n).read_text()

if __name__ == "__main__":
    reszek = [
        ("ÁSZF I.", ASZF_ELEJE),
        ("ÁSZF II. (T10-1)", ASZF_PARKOLO),
        ("D1 bérleti szerződés", load("D1.md")),
        ("HÁZIREND rakodás (near-miss: emelés)", HAZIREND),
        ("D1 1. sz. módosítás", load("D1-M1.md")),
        ("ÜZEMELTETÉS karbantartás (T10-2)", USEM),
        ("D1 2. sz. módosítás", load("D1-M2.md")),
        ("HÁZIREND takarítás (near-miss: befejezés)", HAZIREND_TAKARITAS),
        ("D2 vállalkozási szerződés", load("D2.md")),
        ("ÜZEMELTETÉS szállítás (near-miss: szállítás)", SZALLITAS),
        ("D3 számlacsomag", load("D3.md")),
        ("FOGALMAK", FOGALMAK),
        ("ÁSZF III.", ASZF_III),
        ("MŰSZAKI TARTALOM", MUSZAKI),
        ("ENERGIAGAZDÁLKODÁS", ENERGIA),
        ("TŰZVÉDELEM", TUZVEDELEM),
        ("IRATKEZELÉS", IRATKEZELES),
        ("VAGYONVÉDELEM", BIZTONSAG),
        ("MINŐSÉGIRÁNYÍTÁS", MINOSEG),
        ("KOCKÁZATÉRTÉKELÉS", KOCKAZAT),
        ("D4 jegyzőkönyv + e-mail", load("D4.md")),
        ("KÖRNYEZETVÉDELEM", KORNYEZET),
        ("SZÁMLÁZÁS", PENZUGY),
        ("GYIK", GYIK),
        ("ALVÁLLALKOZÓI REND", ALVALLALKOZO),
        ("PANASZKEZELÉS", PANASZ),
        ("VIS MAIOR", VIS_MAIOR),
        ("JOGVITÁK", JOGVITA),
        ("ARCHÍVUM", ARCHIV),
        ("VÁLTOZÁSJEGYZÉK", VALTOZASJEGYZEK),
        ("BIZTOSÍTÁS", BIZTOSITAS),
        ("KÖZÜZEM (T10-3)", KOZUZEM),
    ]
    fej = ("# IRATCSOMAG — Verseny utca 3. telephely\n\n"
           "*(tesztelési célra összeállított, kitalált tartalmú iratcsomag. Tartalmazza a bérleti "
           "szerződést és módosításait, a vállalkozási szerződést, a számlacsomagot, az átadás-átvételi "
           "jegyzőkönyvet és az e-mail-láncot, valamint az üzemeltető általános szerződési feltételeit, "
           "házirendjét és üzemeltetési szabályzatát.)*\n\n---\n")
    doc = fej
    poz = []
    for nev, txt in reszek:
        doc += "\n\n---\n\n" + txt
    n = len(doc)
    for cim, teny in (("T10-1 parkolóhely éves korrekció", T10_1),
                      ("T10-2 karbantartási ciklus zárónapja", T10_2),
                      ("T10-3 hulladékkezelési hozzájárulás", T10_3)):
        i = doc.find(teny[:60])
        poz.append((cim, i, 100 * i / n))
    Path("corpus/D5.md").write_text(doc)
    print(f"D5 mérete: {n:,} karakter".replace(",", " "))
    print(f"cél: 60 000–90 000 → {'✅ BENNE' if 60000 <= n <= 90000 else '⛔ KÍVÜL'}")
    print("\nA T10 céltények MÉRT pozíciója:")
    for cim, i, p in poz:
        print(f"  {cim:38s} {i:7,} karakter  ({p:5.1f} %)".replace(",", " "))
    print("\nnear-miss kulcsszavak előfordulása a teljes D5-ben:")
    for kw in ("emelés", "emelked", "befejez", "szállít", "letét", "korrekció", "zárónap", "hozzájárulás"):
        print(f"  {kw:12s} {len(re.findall(kw, doc, re.I)):3d}×")
