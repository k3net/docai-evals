"""08 — a szabálycsalád értelmezési konstrukciójának forgatókönyvei (`kor08/ertelmezes-javaslat.md`, E-szabály-1).

Egy forgatókönyv: (gold kategória, csali kategória, helyzet, jel). A helyzet a kiadás tárgya úgy leírva, hogy a
felszíni szava a csali kategóriájáé; a jel egy mondat, amely kimondja a kiadás célját vagy jellegét, és ez a gold
kategóriáját adja. A (b) változat a helyzet + jel, az (a) változat csak a helyzet (gold Y). A kategóriák a `szint06`
`SZAB_TIPUS` kulcsai. A `kulcs` a jel szavai, amelyeknek az (a)-ban nem szabad szerepelniük (tényellenőrző).

2. kör (`JEL2`, Dani 11-02): áttételes jel, vagyis egy tény, amelyből a gold kategória egy lépésben következik, és a
besorolást a szabálypont szövege (`SZAB_TIPUS`) alátámasztja; a `tamasz` a szabálypont szövegének az a része, amelyre
a tény rámutat. A sorrend és a (gold, csali, helyzet) a `FORGATOKONYV`-é; a `kulcs2` a tényellenőrzőé.
"""

from __future__ import annotations

FORGATOKONYV = {
    "hu": [
        {"gold": "képzés", "csali": "reprezentáció",
         "helyzet": "vacsora egy kétnapos projektmenedzsment-tanfolyam második estéjén",
         "jel": "a vacsora a tanfolyam hivatalos programjának része volt, és a részvételi díj tartalmazza",
         "kulcs": ["program", "részvételi díj"]},
        {"gold": "reprezentáció", "csali": "képzés",
         "helyzet": "egy termékbemutató képzési nap ebédje",
         "jel": "a résztvevők a vevőink munkatársai voltak, őket láttuk vendégül",
         "kulcs": ["vevő", "vendégül"]},
        {"gold": "eszköz", "csali": "reprezentáció",
         "helyzet": "egy laptoptáska és egy vezeték nélküli egér, amelyet egy kollégának adtunk át",
         "jel": "a kolléga a napi munkájához használja, és mindkettő a cég leltárába került",
         "kulcs": ["leltár", "napi munkájához"]},
        {"gold": "reprezentáció", "csali": "eszköz",
         "helyzet": "két prémium fejhallgató vásárlása",
         "jel": "a legfontosabb ügyfelünk két vezetőjének vittük ajándékba",
         "kulcs": ["ügyfel", "ajándék"]},
        {"gold": "előfizetés", "csali": "képzés",
         "helyzet": "egy online oktatóplatform éves díja",
         "jel": "a platformot a csapat dokumentáció- és sablontárként használja a napi munkához, kurzust nem végzünk rajta",
         "kulcs": ["sablontár", "kurzust nem"]},
        {"gold": "képzés", "csali": "előfizetés",
         "helyzet": "egy szakmai szoftver éves licence",
         "jel": "a díj egy háromhónapos, vizsgával záruló tanfolyam részvételi díja, a szoftverhez csak a tanfolyam idejére kapunk hozzáférést",
         "kulcs": ["tanfolyam", "vizsga"]},
        {"gold": "utazás", "csali": "képzés",
         "helyzet": "egy budapesti szakmai konferencia költsége",
         "jel": "a részvételi díjat a szervező elengedte, a kért összeg kizárólag a vonatjegy és a két éjszakai szállás",
         "kulcs": ["vonatjegy", "szállás", "elengedte"]},
        {"gold": "képzés", "csali": "utazás",
         "helyzet": "a debreceni kiküldetés költsége",
         "jel": "a kért összeg teljes egészében a helyszíni tréning részvételi díja; a céges autóval mentem, szállás nem volt",
         "kulcs": ["tréning", "részvételi díj"]},
        {"gold": "reprezentáció", "csali": "utazás",
         "helyzet": "a szegedi ügyféllátogatás költsége",
         "jel": "az összeg az ügyfél két munkatársával elköltött munkaebéd számlája",
         "kulcs": ["munkaebéd", "ügyfél két munkatárs"]},
        {"gold": "utazás", "csali": "reprezentáció",
         "helyzet": "vacsora a győri kiküldetés estéjén",
         "jel": "egyedül vacsoráztam a szálláshelyen, a kiküldetés étkezési költségeként számolom el",
         "kulcs": ["egyedül", "étkezési költség"]},
        {"gold": "eszköz", "csali": "előfizetés",
         "helyzet": "egy tervezőszoftverhez tartozó tétel",
         "jel": "a díj egy USB-s hardverkulcs ára; magát a szoftverlicencet a cég korábban már megvette",
         "kulcs": ["hardverkulcs", "korábban már megvette"]},
        {"gold": "előfizetés", "csali": "eszköz",
         "helyzet": "egy külső SSD-meghajtó és a hozzá tartozó felhőmentés",
         "jel": "a kért összeg csak a felhőmentés éves díja, a meghajtót a cég adta",
         "kulcs": ["csak a felhőmentés", "éves díj"]},
    ],
    "en": [
        {"gold": "training", "csali": "entertainment",
         "helyzet": "a dinner on the second evening of a two-day project management course",
         "jel": "the dinner was part of the course's official programme and is included in the course fee",
         "kulcs": ["programme", "course fee"]},
        {"gold": "entertainment", "csali": "training",
         "helyzet": "the lunch of a product demonstration training day",
         "jel": "the attendees were staff of our customers, whom we hosted",
         "kulcs": ["customer", "hosted"]},
        {"gold": "equipment", "csali": "entertainment",
         "helyzet": "a laptop bag and a wireless mouse handed over to a colleague",
         "jel": "the colleague uses both for daily work and they were added to the company's asset register",
         "kulcs": ["asset register", "daily work"]},
        {"gold": "entertainment", "csali": "equipment",
         "helyzet": "the purchase of two premium headphones",
         "jel": "we brought them as a gift for two directors of our most important client",
         "kulcs": ["client", "gift"]},
        {"gold": "subscription", "csali": "training",
         "helyzet": "the annual fee of an online learning platform",
         "jel": "the team uses the platform as a documentation and template library for daily work; no courses are taken on it",
         "kulcs": ["template library", "no courses"]},
        {"gold": "training", "csali": "subscription",
         "helyzet": "an annual licence for a professional software tool",
         "jel": "the fee is the participation fee of a three-month course ending with an exam; software access is only for the duration of the course",
         "kulcs": ["course", "exam"]},
        {"gold": "travel", "csali": "training",
         "helyzet": "the cost of a professional conference in Manchester",
         "jel": "the organiser waived the attendance fee; the amount claimed is only the train ticket and two nights' accommodation",
         "kulcs": ["train ticket", "accommodation", "waived"]},
        {"gold": "training", "csali": "travel",
         "helyzet": "the cost of the Leeds business trip",
         "jel": "the amount claimed is entirely the on-site workshop fee; I drove the company car and there was no overnight stay",
         "kulcs": ["workshop fee", "no overnight"]},
        {"gold": "entertainment", "csali": "travel",
         "helyzet": "the cost of the Bristol client visit",
         "jel": "the amount is the bill for a working lunch with two of the client's staff",
         "kulcs": ["working lunch", "client's staff"]},
        {"gold": "travel", "csali": "entertainment",
         "helyzet": "a dinner on the evening of the York business trip",
         "jel": "I dined alone at the hotel and claim it as a meal cost of the trip",
         "kulcs": ["alone", "meal cost"]},
        {"gold": "equipment", "csali": "subscription",
         "helyzet": "an item for a design software package",
         "jel": "the fee is the price of a USB hardware licence key; the software licence itself was bought by the company earlier",
         "kulcs": ["hardware licence key", "bought by the company earlier"]},
        {"gold": "subscription", "csali": "equipment",
         "helyzet": "an external SSD drive with its cloud backup",
         "jel": "the amount claimed is only the annual cloud backup fee; the drive was provided by the company",
         "kulcs": ["only the annual", "provided by the company"]},
    ],
}


JEL2 = {  # a FORGATOKONYV sorrendjében
    "hu": [
        {"jel2": "a vacsorát a tanfolyamot szervező képzőintézet számlázta ki, a részvételi díjjal egy számlán, külön nem "
                 "fizettünk érte", "kulcs2": ["képzőintézet", "egy számlán"], "tamasz": "tanfolyam"},
        {"jel2": "a napot a három legnagyobb partnercégünk beszerzőinek tartottuk, a saját munkatársaink közül csak a "
                 "szervezők voltak jelen", "kulcs2": ["partnercég", "beszerző"], "tamasz": "üzleti vendéglátás"},
        {"jel2": "mindkét tétel leltári számot kapott, és a kolléga céges munkaállomásához tartozik",
         "kulcs2": ["leltári szám", "munkaállomás"], "tamasz": "munkaeszköz-beszerzés (számítástechnika)"},
        {"jel2": "a fejhallgatókat díszcsomagolásban, üdvözlőkártyával a legnagyobb megrendelőnk két igazgatójának "
                 "küldtük el", "kulcs2": ["díszcsomagolás", "üdvözlőkártya"], "tamasz": "ajándék"},
        {"jel2": "a platformon csak a belső szabályzatainkat és dokumentumsablonjainkat tároljuk, tanfolyami anyagot senki "
                 "nem használ rajta", "kulcs2": ["belső szabályzat", "dokumentumsablon"], "tamasz": "szoftver-előfizetés"},
        {"jel2": "a hozzáférés a háromhónapos tanfolyam záróvizsgájának napján megszűnik, a díjat a tanfolyamot tartó "
                 "oktatóközpont számlázta", "kulcs2": ["záróvizsga", "oktatóközpont"], "tamasz": "tanfolyam"},
        {"jel2": "a szervező a részvételt díjmentesen biztosította; a benyújtott két számla a vasúttársaságtól és a "
                 "szállodától származik", "kulcs2": ["díjmentes", "vasúttársaság"], "tamasz": "utazási és szállásköltség"},
        {"jel2": "az egyetlen benyújtott számla a helyszíni tréninget tartó cégtől származik; céges autóval mentem, "
                 "szállásom nem volt", "kulcs2": ["tréninget tartó", "egyetlen benyújtott számla"], "tamasz": "szakmai képzés"},
        {"jel2": "a számla egy étterem háromfős ebédjéről szól, és a három fő közül kettő az ügyfél munkatársa",
         "kulcs2": ["háromfős", "étterem"], "tamasz": "üzleti vendéglátás"},
        {"jel2": "a vacsora a szállodai számlán szerepel, a szállás díjával együtt; egyedül étkeztem",
         "kulcs2": ["szállodai számlán", "szállás díjával"], "tamasz": "szállásköltség"},
        {"jel2": "a számla egyetlen, futárral kézbesített USB-eszközről szól; a szoftver licencdíja nem szerepel rajta",
         "kulcs2": ["USB-eszköz", "futár"], "tamasz": "munkaeszköz-beszerzés (számítástechnika)"},
        {"jel2": "a meghajtó tavaly óta szerepel a céges leltárban; a mostani számla a felhőszolgáltató éves megújítási "
                 "díjbekérője", "kulcs2": ["megújítás", "felhőszolgáltató"], "tamasz": "szoftver-előfizetés"},
    ],
    "en": [
        {"jel2": "the dinner was invoiced by the training provider that runs the course, on the same invoice as the course "
                 "fee, and we did not pay for it separately", "kulcs2": ["training provider", "same invoice"],
         "tamasz": "courses"},
        {"jel2": "the day was held for the buyers of our three largest partner companies; only the organisers from our own "
                 "staff attended", "kulcs2": ["partner compan", "buyers"], "tamasz": "business entertainment"},
        {"jel2": "both items received asset tag numbers and belong to the colleague's company workstation",
         "kulcs2": ["asset tag", "workstation"], "tamasz": "work equipment purchases (IT)"},
        {"jel2": "the headphones were gift-wrapped and sent with a greeting card to two directors of our largest customer",
         "kulcs2": ["gift-wrapped", "greeting card"], "tamasz": "gifts"},
        {"jel2": "we only store our internal policies and document templates on the platform; nobody uses any course "
                 "material on it", "kulcs2": ["internal policies", "document templates"], "tamasz": "software subscriptions"},
        {"jel2": "the access ends on the day of the final exam of the three-month course, and the fee was invoiced by the "
                 "training centre running the course", "kulcs2": ["final exam", "training centre"], "tamasz": "courses"},
        {"jel2": "the organiser provided attendance free of charge; the two receipts submitted are from the railway company "
                 "and the hotel", "kulcs2": ["free of charge", "railway"], "tamasz": "business travel and accommodation"},
        {"jel2": "the only receipt submitted is from the company that ran the on-site workshop; I drove the company car and "
                 "had no overnight stay", "kulcs2": ["ran the on-site workshop", "only receipt"],
         "tamasz": "professional training"},
        {"jel2": "the receipt is for a restaurant lunch for three people, two of whom are the client's staff",
         "kulcs2": ["restaurant lunch", "three people"], "tamasz": "business entertainment"},
        {"jel2": "the dinner appears on the hotel bill together with the room charge; I dined alone",
         "kulcs2": ["hotel bill", "room charge"], "tamasz": "accommodation"},
        {"jel2": "the invoice is for a single USB device delivered by courier; the software licence fee is not on it",
         "kulcs2": ["USB device", "courier"], "tamasz": "work equipment purchases (IT)"},
        {"jel2": "the drive has been in the company asset register since last year; this invoice is the cloud provider's "
                 "annual renewal notice", "kulcs2": ["renewal", "cloud provider"], "tamasz": "software subscriptions"},
    ],
}
assert all(len(JEL2[n]) == len(FORGATOKONYV[n]) for n in JEL2)

# A 2. kör javítása (Dani 11-02, a D7 audit előtt): a forgatókönyv a megadott szabályzat szövegéhez mérve, a modell
# választásától függetlenül. A (b) legyen a szabályzat szavaiból egyértelműen eldönthető, az (a) a döntő jel nélkül valóban
# eldönthetetlen. A szabályzat csak az öt költségnem egysoros leírása (`szint06.SZAB_TIPUS`); a vak címkeellenőrzés
# (gold, párosítás és modellválasz nélkül) szerint ezek nem teljesültek. Index → a mezők új értéke (a FORGATOKONYV-é és a
# JEL2-é), vagy `kihagy`: ha természetes, egyértelmű pár nem készíthető, a forgatókönyv minden változatával kimarad. A
# javított szövegeken egy második vak ellenőrzés futott (11-02); a többi forgatókönyv változatlan.
JAVITAS2 = {
    "hu": {
        # a díjba foglalt vacsora: a szabályzat a közös számláról nem szól, ezért a jel a kért összeget mondja ki
        0: {"jel2": "a kért összeg a tanfolyam részvételi díja, amely a második esti vacsorát is tartalmazza; a vacsorát "
                    "külön nem számlázták", "kulcs2": ["részvételi díj"]},
        # „kollégának adtunk át”: belső címzettnek adott tárgy nem üzleti ajándék, az (a) eszköz; „laptoptáska és egér
        # vásárlása” változattal a második vak ellenőrzésen is eszköz → kimarad
        2: {"kihagy": True},
        # „éves szoftverlicenc”: a tárgy maga előfizetés, az (a) nem volt eldönthetetlen, a (b) jele a díj tárgyát nem
        # mondta ki
        5: {"helyzet": "egy szakmai szoftverhez kapcsolódó szolgáltatás díja",
            "jel": "a díj egy oktató által tartott, vizsgával záruló képzés díja, a szoftvert a cég korábban megvette",
            "kulcs": ["oktató", "vizsga"],
            "jel2": "a díj fejében a szoftver gyártójának oktatója négy alkalommal gyakorlati foglalkozást tartott a "
                    "csapatnak, amely vizsgával zárult; magát a szoftvert a cég korábban már megvette",
            "kulcs2": ["oktató", "gyakorlati foglalkozás"], "tamasz": "szakmai képzés"},
        # „a konferencia költsége”: a „konferencia-részvétel” szó szerint a képzésé, az (a) a csalira húzott
        6: {"helyzet": "a budapesti szakmai konferenciához kapcsolódó költségtételek"},
        # „a kiküldetés költsége”: a „kiküldetés” szó szerint az utazásé, az (a) a csalira húzott; a (b) a számla
        # tárgyát a kiállítóból hagyta kikövetkeztetni
        7: {"helyzet": "a debreceni kiküldetéshez kapcsolódó egyik költségtétel",
            "jel2": "az egyetlen benyújtott számla a helyszíni tréninget tartó cég számlája a tréning díjáról; céges "
                    "autóval mentem, szállásom nem volt", "kulcs2": ["tréning díj", "tréninget tartó"]},
        # a szállodai számlán szereplő vacsora: étkezés se nem utazási, se nem szállásköltség; a jel a szállás díját
        # mondja ki
        9: {"jel2": "a kért összeg a félpanziós szállás díja, amely a vacsorát is tartalmazza; egyedül étkeztem",
            "kulcs2": ["félpanzió", "szállás díj"]},
    },
    "en": {
        0: {"jel2": "the amount claimed is the course fee, which includes the second-evening dinner; the dinner was not "
                    "billed separately", "kulcs2": ["course fee"]},
        # D7 audit (11-02 23:04, Dani 23:10: javítani, nem kihagyni): az „only the organisers from our own staff attended”
        # úgy is olvasható, hogy senki más nem volt jelen; a generált szövegek két itemben a saját munkatársak étkezését
        # írták, kettőben az ebéd kimaradt. A jel a magyar mintájára: a vendégek a partnercégek beszerzői, a saját
        # munkatársak közül csak a szervezők. A „guest” a kulcs2-ben, hogy az (a) ne mondhassa ki a vendégkört. `d7`: a
        # forgatókönyv minden terve újra generálódik (más seeddel), a többi az auditált kor2j-ből marad.
        1: {"jel2": "the day was held for the buyers of our three largest partner companies, who were the guests at the "
                    "lunch; of our own staff, only the organisers were present",
            "kulcs2": ["partner compan", "buyers", "guest"], "d7": True},
        2: {"kihagy": True},
        5: {"helyzet": "the fee for a service related to a professional software tool",
            "jel": "the fee is for instructor-led training ending with an exam; the software itself was bought by the "
                   "company earlier", "kulcs": ["instructor", "exam"],
            "jel2": "for this fee, an instructor from the software vendor ran four hands-on sessions for the team, ending "
                    "with an exam; the software itself was bought by the company earlier",
            "kulcs2": ["instructor", "hands-on session"], "tamasz": "professional training"},
        6: {"helyzet": "the cost items related to a professional conference in Manchester"},
        7: {"helyzet": "one of the cost items from the Leeds business trip",
            # a „workshop” munkamegbeszélés is lehet (második vak ellenőrzés): a magyar „tréning” mintájára „course”
            "jel2": "the only receipt submitted is the invoice of the company that ran the on-site course, for the course "
                    "fee; I drove the company car and had no overnight stay",
            "kulcs2": ["course fee", "ran the on-site course"]},
        9: {"jel2": "the amount claimed is the half-board hotel rate, which includes the dinner; I dined alone",
            "kulcs2": ["half board", "half-board"]},
    },
}
_FK_MEZO = ("helyzet", "jel", "kulcs")


def kihagyott(lang: str, i: int) -> bool:
    return bool(JAVITAS2[lang].get(i, {}).get("kihagy"))


def d7_javitott(lang: str, i: int) -> bool:
    """A D7 audit után javított forgatókönyv: minden terve újra generálódik."""
    return bool(JAVITAS2[lang].get(i, {}).get("d7"))


def alkalmaz_javitas() -> None:
    """A `JAVITAS2` beírása a FORGATOKONYV-be és a JEL2-be (a `szint08e --javitott` hívja, a terv előtt)."""
    for lang, jav in JAVITAS2.items():
        for i, m in jav.items():
            FORGATOKONYV[lang][i] = {**FORGATOKONYV[lang][i], **{k: v for k, v in m.items() if k in _FK_MEZO}}
            JEL2[lang][i] = {**JEL2[lang][i], **{k: v for k, v in m.items() if k not in (*_FK_MEZO, "kihagy", "d7")}}
    for lang in FORGATOKONYV:
        assert len({f["helyzet"] for f in FORGATOKONYV[lang]}) == len(FORGATOKONYV[lang])  # a kieg2 a helyzettel keres

# 2. kör, bank: a fizető szerepe a számla partneréhez, és hogy ez a fizetés a partner kötelezettségét rendezi
BANK_SZEREP2 = {
    "hu": [("jogutód", "{B} {A} jogutódjaként fizet, és ezzel {A} beolvadás előtti kötelezettségét rendezi",
            r"jogutód"),
           ("kezes", "{B} kezesként teljesít {A} kötelezettségéért", r"kezes"),
           ("átvállalás", "{B} tartozásátvállalási megállapodás alapján törleszti {A} tartozását", r"átvállal")],
    "en": [("successor", "{B} pays as the legal successor of {A}, settling {A}'s pre-merger liability", r"successor"),
           ("guarantor", "{B} pays as guarantor for the obligation of {A}", r"guarantor"),
           ("assumption", "{B} repays the debt of {A} under a debt assumption agreement", r"assum")],
}
