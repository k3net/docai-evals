"""08 illesztett kontroll (M) — a nem döntő mondatok. Az (a) a G5-ben azért volt felismerhető, mert rövid, a jel nélküli szöveg (eredménylap,
E függelék). Az illesztett (a) ugyanaz a terv, és ugyanúgy mond ki egy konkrét tényt, mint a (b), de ez a tény a kért összeg tárgyáról nem mond semmit:
a rendelés, a számla, a fizetés vagy a bizonylat körülménye. A címke marad Y: a mondatból a gold és a csali közt nem lehet dönteni.

Szabály a mondatokra (a G2 forgatókönyveinek D7-tanulságai szerint):
  - nem mondja ki, ki használja vagy kapta, mire szolgál, és mi pontosan a kért összeg tárgya;
  - a számlázó, a helyszín önmagában nem dönt (Dani 11-03);
  - nincs benne szám, pénzösszeg, dátum, nettó / bruttó, és nincs jóváhagyó (a kinyerés és a generátor utasítása miatt);
  - egyik költségnem árulkodó szava sincs benne, ami nem szerepel a helyzetben (`ellenoriz`).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE)]
import forgatokonyv08_szab as FK  # noqa: E402

# forgatókönyv → (hu, en)
MONDAT = {
    "F01": ("a tabletet és a tollat a beszerzőnk két webáruház ajánlata közül a gyorsabb szállítás miatt választotta, és a hét végére meg is érkeztek",
            "our purchasing colleague chose the tablet and stylus from two online shops' offers because of the faster delivery, and they arrived by the end of the week"),
    "F02": ("a készlet éppen akciós volt a szaküzletben, és a garanciajegyet a pénzügyesünk a számlához tűzte",
            "the set was on offer at the specialist shop, and our finance colleague stapled the warranty card to the invoice"),
    "F07": ("az olvasót a titkárságunk rendelte meg a gyártó webáruházából, és a szállítás késése miatt csak a múlt héten ért ide",
            "the reader was ordered by our office from the manufacturer's online shop, and because of a delivery delay it only arrived last week"),
    "F08": ("a hangszórót a múlt héten vettük egy műszaki áruházban, mert csak ott volt készleten ebben a színben, a blokkot a titkárságunk őrzi",
            "the speaker was bought last week at an electronics store, because only they had it in stock in this colour, and our office is keeping the receipt"),
    "F13": ("a kért összeg a szervező számláján szerepel; a számlát a szervező csak az esemény után két héttel küldte meg, ezért adom be most",
            "the amount claimed appears on the organiser's invoice; the organiser only sent the invoice two weeks after the event, which is why I am submitting it now"),
    "F14": ("a díjat a szervező előre kérte banki átutalással; a visszaigazolást a titkárságunk a számla mellé tette, és a névsor is nálunk van",
            "the organiser asked for the fee in advance by bank transfer; our office filed the confirmation with the invoice, and we also hold the list of names"),
    "F17": ("a kódot a szolgáltató webáruházában vettük bankkártyával, és e-mailben érkezett meg néhány perccel a fizetés után",
            "we bought the code in the provider's online shop by card, and it arrived by email a few minutes after payment"),
    "F18": ("a beszélgetés a belvárosi rendezvényközpontban volt csütörtökön, és a kért összeg a rendezvényközpont számlájával egyezik, amelyet a titkárságunk ellenőrzött",
            "the discussion took place at the downtown event centre on Thursday, and the amount claimed matches the event centre's invoice, which our office checked"),
    "F21": ("a díjat a szolgáltató a hónap elején számlázta, a számla postán érkezett, és a fizetés banki átutalással történt",
            "the provider invoiced the fee at the start of the month, the invoice came by post, and it was paid by bank transfer"),
    "F22": ("a díjat a szolgáltató ügyfélszolgálatán egyeztettük, mert a számlán eleinte rossz cégnév szerepelt; a javított számla a múlt héten érkezett",
            "we sorted out the fee with the provider's customer service, because the invoice first showed the wrong company name; the corrected invoice arrived last week"),
    "F26": ("a díjat a platformon bankkártyával fizettük, a számlát a rendszer automatikusan e-mailben küldte el, és az ügyfélszolgálat gyorsan válaszolt a kérdésünkre",
            "we paid the fee by card on the platform, the system emailed the invoice automatically, and customer service answered our question quickly"),
    "F27": ("a díjról a kiadó díjbekérőt küldött, és a kolléganőm a kiadó ügyfélszolgálatával egyeztette a számlázási címet; a fizetés átutalással történt",
            "the publisher sent a pro forma invoice for the fee, and my colleague confirmed the billing address with the publisher's customer service; it was paid by transfer"),
    "F31": ("a költségről a bizonylatot a miskolci ügyintézőtől kaptam meg, és a papírokat a hét elején adtam le a titkárságon",
            "I received the receipt for this cost from the Sheffield administrator, and I handed in the paperwork at the office at the start of the week"),
    "F32": ("a tételről a bizonylat a hétvége után érkezett meg; a fizetés bankkártyával történt, és a kártyakivonatot is mellékelem",
            "the receipt for this item arrived after the weekend; it was paid by card, and I am attaching the card statement as well"),
    "F36": ("a látogatás csütörtökön volt, és a bizonylatot pénteken adtam le a titkárságon, mert addig házon kívül voltam",
            "the visit was on Thursday, and I handed in the receipt at the office on Friday, because I was out of the office until then"),
    "F37": ("a tételről a számla a kiküldetés után két héttel jött meg, és eleinte hibás volt rajta a cégnevünk; a helyesbített számlát mellékelem",
            "the invoice for this item came two weeks after the trip, and it first showed our company name incorrectly; I am attaching the corrected invoice"),
    "F41": ("az ügyféltalálkozó a tervezettnél később ért véget, és erről a költségről a bizonylatot másnap reggel adtam le a titkárságon; a fizetés bankkártyával történt",
            "the client meeting ended later than planned, and I handed in the receipt for this cost at the office the next morning; I paid by card"),
    "F42": ("a látogatás a vártnál tovább tartott, és a számlát a kollégánk a hónap végén kapta meg; a fizetés átutalással történt",
            "the visit lasted longer than expected, and our colleague received the invoice at the end of the month; it was paid by transfer"),
    "F45": ("a tárgyalások a lengyel partnercéggel jól haladtak; a számlát a titkárságunk a látogatás után egy héttel kapta meg, és a kért összeg azzal egyezik",
            "the negotiations with the Polish partner company went well; our office received the invoice a week after the visit, and the amount claimed matches it"),
    "F46": ("a találkozó a tervek szerint zajlott, a vevőink elégedettek voltak; a számlát utána a titkárságunk kapta meg, és a kért összeg azzal egyezik",
            "the meeting went to plan and our customers were pleased; our office received the invoice afterwards, and the amount claimed matches it"),
    "F49": ("a kért összeg a szállító első számláján szerepel, és a rendszert a szállító a múlt hónapban helyezte üzembe a raktárunkban",
            "the amount claimed appears on the supplier's first invoice, and the supplier commissioned the system at our warehouse last month"),
    "F50": ("a rendszert a telephelyünkön egy helyi vállalkozó állította be, és a számlát a bejárás után két nappal kaptuk meg",
            "a local contractor set up the system at our site, and we received the invoice two days after the walk-through"),
    "F54": ("a tétel a szállító legutóbbi számláján szerepel; a számlát a flottakezelőnk ellenőrizte, és a fizetés átutalással történt",
            "the item appears on the supplier's latest invoice; our fleet manager checked the invoice, and it was paid by transfer"),
    "F55": ("a tétel a nyomtató szállítójának számláján szerepel; a számlát az irodavezetőnk ellenőrizte, és a nyomtató a második emeleti irodában áll",
            "the item appears on the printer supplier's invoice; our office manager checked the invoice, and the printer stands in the second-floor office"),
    "F59": ("a szerelés a tervezettnél tovább tartott, mert egy alkatrész késett, és a tételről a bizonylatot a visszaérkezésünk után adtam le",
            "the installation took longer than planned because a part was late, and I handed in the receipt for this item after we got back"),
    "F60": ("a gépátadás a megbeszélt napon rendben lezajlott, és a tételről a bizonylatokat a következő héten adtam le a titkárságon",
            "the machine handover went smoothly on the agreed day, and I handed in the receipts for this item at the office the following week"),
    "F63": ("a felmérő csapat rendben végzett a helyszínen, és a számlát a visszaérkezésem után kaptam meg",
            "the survey team finished on site without problems, and I received the invoice after getting back"),
    "F64": ("a tételt a helyszínen fizettem ki bankkártyával; a blokk kicsit elmosódott, ezért a kártyakivonatot is mellékelem",
            "I paid for the item on site by card; the receipt is a bit faded, so I am attaching the card statement too"),
    "F67": ("a díjat a platformon bankkártyával fizettem, a visszaigazolás azonnal megjött e-mailben, és a számlát a fiókomból töltöttem le",
            "I paid the fee on the platform by card, the confirmation came by email straight away, and I downloaded the invoice from my account"),
    "F68": ("a díjat az alkalmazásban bankkártyával fizettem, a bizonylatot az alkalmazás e-mailben küldte el, és a kártyakivonatot is mellékelem",
            "I paid the fee in the app by card, the app emailed the receipt, and I am attaching the card statement too"),
    "F71": ("a díjat az alkalmazás szolgáltatója a cég bankszámlájáról vonta le, a kollégáim régóta ismerik ezt az alkalmazást, és a számla tegnap érkezett meg",
            "the app's provider took the fee from the company's bank account, my colleagues have known this app for a long time, and the invoice arrived yesterday"),
    "F72": ("az összeget a vasúttársaság ügyfélkapuján fizettük, a számla a vasúttársaság központjából érkezett, és a pénzügyesünk már feldolgozta",
            "we paid the amount through the rail operator's customer portal, the invoice came from the operator's head office, and our finance colleague has already processed it"),
    "F75": ("a tétel a hegesztőkészülék forgalmazójának számláján szerepel, és a forgalmazó képviselője a múlt héten járt nálunk a műhelyben",
            "the item appears on the welding machine distributor's invoice, and the distributor's representative visited our workshop last week"),
    "F76": ("a tétel a nyomtató forgalmazójának számláján szerepel; a műszaki csapat két tagja intézte az ügyet a forgalmazóval, és a számla a múlt héten érkezett",
            "the item appears on the printer distributor's invoice; two members of the technical team dealt with the distributor, and the invoice arrived last week"),
    "F79": ("a tétel a beszállító számláján szerepel; a belső oktatásokat a tárgyalóban tartjuk, és a számlát az irodavezetőnk a múlt héten kapta meg",
            "the item appears on the supplier's invoice; we hold the internal training sessions in the meeting room, and our office manager received the invoice last week"),
    "F80": ("a tétel a múlt havi számlán szerepel; a minőségellenőreink egyeztettek a szállítóval, és a számla a hónap végén érkezett",
            "the item appears on last month's invoice; our quality inspectors dealt with the supplier, and the invoice arrived at the end of the month"),
    "F83": ("a hozzáférést a folyóirat kiadójától vettük átutalással; a kiadó ügyfélszolgálata e-mailben visszaigazolta, és a számla a hét végén érkezett",
            "we bought the access from the journal's publisher by bank transfer; the publisher's customer service confirmed by email, and the invoice arrived at the end of the week"),
    "F84": ("a díjat a hírlevél kiadója díjbekérőn kérte; a fizetés átutalással történt, és a számla a múlt héten érkezett meg",
            "the newsletter's publisher requested the fee on a pro forma invoice; it was paid by transfer, and the invoice arrived last week"),
    "F87": ("a csomagot a szolgáltató viszonteladójától vettük; a kártyák ajánlott levélben érkeztek, és a csomagolásuk sértetlen volt",
            "we bought the pack from the provider's reseller; the cards came by registered post, and the packaging was undamaged"),
    "F88": ("a díjat a szolgáltató a cég bankkártyájáról vonta le, a számlát a szolgáltató oldaláról töltöttük le, és az ügyfélszolgálattal nem volt gond",
            "the provider charged the fee to the company card, we downloaded the invoice from the provider's site, and there was no issue with customer service"),
}

# bank: a két cég kapcsolatáról szóló mondat, amelyből nem derül ki, kinek a számlája (a (b) három szerepének párja)
BANK = {
    "hu": ("a tétel {B} és {A} közös elszámolásához tartozik, a felek a múlt havi egyeztetésen állapodtak meg benne",
           "az utalás {B} és {A} közös projektjének lezárásához kapcsolódik, az ütemezés szerint most esedékes",
           "a tétel {B} és {A} egymás közti megállapodása szerint, a szokásos havi egyeztetés után érkezett"),
    "en": ("this item belongs to the joint settlement between {B} and {A}, agreed at last month's meeting",
           "the transfer relates to closing the joint project of {B} and {A}, due now under the schedule",
           "this item arrived under the agreement between {B} and {A}, after the usual monthly reconciliation"),
}

# hiba: a bejelentés körülményei; a (b) konkrét megfigyeléseinek párja, tünet nélkül
HIBA = {
    "hu": " Írd le viszont részletesen a bejelentés körülményeit, a saját szavaiddal: mikor és melyik műszakban vették észre, ki van a helyszínen, mikor volt utoljára szerviz, mennyire sürgős a javítás, és mikor tudják fogadni a szerelőt. Ezek közt semmi ne jellemezze a berendezés viselkedését, hangját, szagát, kijelzését vagy teljesítményét.",
    "en": " Do describe the circumstances of the report in detail, in your own words: when and on which shift it was noticed, who is on site, when it was last serviced, how urgent the repair is, and when they can receive the technician. None of this may characterise the device's behaviour, sound, smell, display or performance.",
}

_TILTOTT = re.compile(r"\d|bruttó|nettó|\bgross\b|\bnet\b|jóváhagy|approv", re.I)


def mondat(fid: str, lang: str) -> str:
    return MONDAT[fid][0 if lang == "hu" else 1]


def arulkodo(helyzet: str, lang: str) -> list[str]:
    """Mind az öt költségnem árulkodó szavai, a helyzetben szereplők nélkül."""
    h = helyzet.lower()
    return [k for v in FK.ARULKODO.values() for k in v[0 if lang == "hu" else 1] if k.lower() not in h]


def tovek(s: str) -> list[str]:
    """A mondat tartalmas szavainak első öt betűje (a generált szöveg ellenőrzéséhez)."""
    return sorted({w[:5].lower() for w in re.findall(r"[^\W\d_]{6,}", s)})


def ellenoriz() -> list[str]:
    hibak = []
    fk = FK.forgatokonyvek("teszt")
    if set(MONDAT) != {f["id"] for f in fk["hu"]}:
        hibak.append(f"a mondatok nem a 40 teszt-forgatókönyvet fedik: {sorted(set(MONDAT) ^ {f['id'] for f in fk['hu']})}")
    for lang in ("hu", "en"):
        for f in fk[lang]:
            m = mondat(f["id"], lang)
            low = m.lower()
            if _TILTOTT.search(m):
                hibak.append(f"{f['id']} {lang}: tiltott elem: {_TILTOTT.search(m).group(0)}")
            for k in [*f["kulcs"], *f["kulcs2"], *arulkodo(f["helyzet"], lang)]:
                if k.lower() in low:
                    hibak.append(f"{f['id']} {lang}: árulkodó szó: {k}")
    return hibak


if __name__ == "__main__":
    h = ellenoriz()
    print("\n".join(h) if h else f"rendben: {len(MONDAT)} forgatókönyv, két nyelven")
    sys.exit(1 if h else 0)
