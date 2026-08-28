#!/usr/bin/env python3
"""corpus/D6.md — a NEHÉZ suite (T11–T20) irata.

⛔⛔ Minden szám a `gt_nehez.py`-ből jön, egyetlen érték sincs kézzel beírva.
A dokumentum három szereplős, és szándékosan tartalmazza:
  · értelmezési SORRENDET, amely a mellékletet helyezi a törzsszöveg elé (2.1)
  · számmal és betűvel ELTÉRŐ összeget + a betűvel írt elsőbbségét (4.3–4.4)
  · négyszintű, egymásba ágyazott kivételt (5.4)
  · vegyes devizás díjtáblát rögzített árfolyammal + csali árfolyammal (3.3–3.5)
  · „banki nap" fogalmát, amely a munkanaptól ELTÉR (6.2)
  · anaforát három fél között (8.2) és irányt jelölő esetragokat (9.1–9.2)
  · szándékos HALLGATÁST a személyi sérülésből eredő károkról (10.2)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gt_nehez as G

def ft(n):
    return f"{int(n):,}".replace(",", " ") + " Ft"

def szam(n):
    return f"{int(n):,}".replace(",", " ")

IDX = G.indexalas_lanc()
KOLT = G.eves_uzemeltetesi_koltseg()

D = f"""# ÜZEMELTETÉSI ÉS BÉRLETI KERETMEGÁLLAPODÁS

*(a Kavicspart Ingatlanhasznosító Kft. és a Delta-Ipari Szolgáltató Zrt. között 2024. december 18-án
létrejött bérleti szerződéshez — a továbbiakban: **Alapszerződés** — kapcsolódóan)*

Kelt: Pécs, 2026. november 12.

---

## 1. A MEGÁLLAPODÁS FELEI

**1.1.** A jelen Megállapodást megkötötte **egyrészről** a **Kavicspart Ingatlanhasznosító Kft.**
(7621 Pécs, Munkácsy Mihály utca 14.; adószám: 12345676-2-02) mint **Bérbeadó**,
**másrészről** a **Delta-Ipari Szolgáltató Zrt.** (1095 Budapest, Soroksári út 30–34.;
adószám: 24681353-2-43) mint **Bérlő**, **harmadrészről** a
**Hegyi és Társa Építőipari Bt.** (7634 Pécs, Nagy Imre út 8.; adószám: 31415929-1-02)
mint **Üzemeltető** (a továbbiakban együtt: **Felek**).

**1.2.** A Felek rögzítik, hogy az Üzemeltető az Alapszerződésnek nem részese; a jelen
Megállapodás az Üzemeltetőre nézve önálló kötelezettségeket keletkeztet.

---

## 2. ÉRTELMEZÉSI SORREND

**2.1.** A jelen Megállapodás és a hozzá tartozó iratok között felmerülő **ellentmondás esetén**
az alábbi sorrend irányadó, elöl a magasabb rangú irattal:

1. a jelen Megállapodás **1. sz. melléklete**,
2. a jelen Megállapodás **törzsszövege**,
3. az **Alapszerződés** és annak módosításai.

**2.2.** A 2.1. pont szerinti sorrendtől eltérni csak a Felek egybehangzó, írásbeli
nyilatkozatával lehet. Ilyen nyilatkozatot a Felek a jelen Megállapodás aláírásáig nem tettek.

---

## 3. ÜZEMELTETÉSI DÍJAK

**3.1.** A bérlemény a jelen Megállapodás alkalmazásában **{szam(G.ALAPTERULET_M2)} m²**
hasznos alapterületű.

**3.2.** Az Üzemeltető a bérlemény üzemeltetéséért az alábbi díjakra jogosult:

| Tétel | Díj | Mértékegység |
|---|---|---|
| Üzemeltetési alapdíj | {G.UZEMELTETESI_EUR_M2_HO} EUR | **/ m² / hó** |
| Parkolóhely-üzemeltetés | {ft(G.PARKOLO_FT_HO)} | / hó |
| Biztonsági szolgálat | {ft(G.BIZTONSAGI_FT_EV)} | **/ év** |
| Kertészeti szolgáltatás | {ft(G.KERTESZET_FT_HO)} | / hó |

**3.3.** A táblázat valamennyi értéke **nettó** összeg.

**3.4.** Az euróban meghatározott tételeket a Felek a jelen Megállapodás teljes időtartamára
**rögzített, {G.ARFOLYAM} Ft/EUR** árfolyamon számolják el. Ettől eltérő árfolyam alkalmazására
egyik Fél sem jogosult.

**3.5.** *Tájékoztatásul:* a jelen Megállapodás előkészítése során a Felek által megvizsgált
2026. januári középárfolyam {G.ARFOLYAM_CSALI} Ft/EUR volt. **Ez az adat tájékoztató jellegű,
elszámolási alapként nem alkalmazható.**

---

## 4. BELÉPÉSI DÍJ

**4.1.** A Bérlő az Üzemeltető szolgáltatásainak igénybevételéért **egyszeri belépési díjat**
fizet, amely a jelen Megállapodás aláírásától számított 30 napon belül esedékes.

**4.2.** A belépési díj a Bérlőt terheli; azt a Bérbeadóra áthárítani nem lehet.

**4.3.** A belépési díj összege: **{ft(G.BELEPESI_DIJ_SZAMMAL)}**, azaz
**{G.BELEPESI_DIJ_BETUVEL_SZOVEG} forint**.

**4.4.** Ha a jelen Megállapodásban valamely összeg **számmal és betűvel is** szerepel, és a két
megjelölés egymástól eltér, a **betűvel kiírt** összeg az irányadó.

---

## 5. A MEGÁLLAPODÁS MEGSZŰNÉSE ÉS AZ ÁLLAGMEGÓVÁS

**5.1.** A jelen Megállapodás határozatlan időre jött létre.

**5.2.** A Bérlő a jelen Megállapodást **{G.FELMONDAS_TORZS_NAP} napos** felmondási idővel,
indokolás nélkül felmondhatja.

**5.3.** A Bérbeadó felmondási ideje 180 nap.

**5.4.** A Bérlő köteles a bérlemény **állagmegóvási** munkáit saját költségén elvégezni,
**kivéve**, ha a munka a **tartószerkezetet** érinti; a tartószerkezetet érintő munka költsége a
**Bérbeadót** terheli, **kivéve**, ha a szerkezeti hibát a Bérlő technológiai tevékenysége
okozta — amely esetben a költség, a Bérbeadó általi megelőlegezés mellett, végső soron a
**Bérlőt** terheli. **Nem terheli a Bérlőt a költség akkor sem**, ha a kárt okozó technológiai
tevékenységet a Bérbeadó előzetesen, **írásban engedélyezte**.

**5.5.** A Felek rögzítik, hogy a Bérbeadó a Bérlő présgépének üzembe helyezését
**2026. május 4-én írásban engedélyezte**.

---

## 6. HATÁRIDŐK

**6.1.** A jelen Megállapodásban **munkanapban** megállapított határidőkre az Alapszerződéshez
tartozó vállalkozási szerződés 2. sz. melléklete szerinti munkarend irányadó.

**6.2.** A jelen Megállapodás alkalmazásában **banki nap** az a munkanap, amely nem esik a
**naptári év utolsó munkanapjára**. A naptári év utolsó munkanapja banki napnak nem minősül.

**6.3.** A határidő számításakor **a kézhezvétel napja nem számít bele**.

**6.4.** Az Üzemeltető által kiállított elszámolás alapján a Bérlő a fizetést a kézhezvételtől
számított **{G.T16_NAPOK} banki napon** belül teljesíti.

---

## 7. A BÉRLETI DÍJ TOVÁBBI INDEXÁLÁSA

**7.1.** A Felek rögzítik, hogy az Alapszerződés szerinti havi nettó bérleti díj a 2. sz.
módosítás 3. pontja alapján **{ft(G.INDEX_BAZIS)}**, és hogy az indexálás felső határa az
1. sz. módosítás 3. pontja szerint **{G.INDEX_PLAFON} %**.

**7.2.** A Felek az indexálás alapjául az alábbi — a KSH által közzétett, illetve előrejelzett —
éves fogyasztóiár-indexeket fogadják el:

| Naptári év | Éves fogyasztóiár-index |
|---|---|
""" + "\n".join(
    f"| {ev} | {G.KSH_INDEX[ev]} % |" for ev in sorted(G.KSH_INDEX)
) + f"""

**7.3.** Az indexálást **évente, január 1-jén** kell végrehajtani, az **előző naptári év**
fogyasztóiár-indexével, a 7.1. pont szerinti felső határ figyelembevételével. Az indexált összeget
**minden egyes lépésben {szam(G.KEREKITES)} forintra felfelé** kell kerekíteni, és a **következő évi
indexálás alapja a már kerekített összeg**.

**7.4.** Az első indexálás időpontja az Alapszerződés 7.3. pontjában meghatározott nap.

---

## 8. EGYÜTTMŰKÖDÉS

**8.1.** A Felek a bérlemény tűzvédelmi felülvizsgálatát évente elvégeztetik. A felülvizsgálat
megrendelése és költségviselése egyetlen Felet terhel.

**8.2.** A 8.1. pont szerinti kötelezettség azt a Felet terheli, amelyet az 1.1. pont
**másodikként nevez meg**.

**8.3.** Az Üzemeltető a felülvizsgálat elvégzését a helyszínen ellenőrzi, és annak
eredményéről a Bérbeadót tájékoztatja.

---

## 9. ELSZÁMOLÁS ÉS KIFOGÁS

**9.1.** Az elszámolást — a Bérlő részére — negyedévente **az Üzemeltető** állítja ki.

**9.2.** A 9.1. pont szerinti elszámolással szemben a **Bérbeadó az Üzemeltetőnél** — és nem a
Bérlőnél — élhet észrevétellel; az Üzemeltető a Bérbeadó észrevételét a Bérlőnek továbbítja.

**9.3.** A Bérbeadó az Üzemeltetőtől havonta teljesítési igazolást kér.

---

## 10. FELELŐSSÉG

**10.1.** Az Üzemeltető a jelen Megállapodásban vállalt szolgáltatások körében okozott károkért
a Ptk. szabályai szerint felel.

**10.2.** Az Üzemeltető felelőssége a bérleményben bekövetkezett **vagyoni károk** tekintetében
káreseményenként legfeljebb **{ft(G.UZEMELTETO_VAGYONI_PLAFON_FT)}** összegre korlátozott.

**10.3.** A 10.2. pont szerinti korlátozás nem alkalmazható szándékos károkozás esetén.

---

## 11. ZÁRÓ RENDELKEZÉSEK

**11.1.** A jelen Megállapodás az Alapszerződést nem módosítja; az Alapszerződés rendelkezései
a jelen Megállapodásban nem szabályozott kérdésekben változatlanul irányadók.

**11.2.** A jelen Megállapodás 1. sz. melléklete a Megállapodás elválaszthatatlan része.

---

## 1. SZ. MELLÉKLET — KIEGÉSZÍTŐ RENDELKEZÉSEK

**1. pont.** Az Üzemeltető a szolgáltatásokat munkanapokon 6:00 és 20:00 óra között nyújtja.

**2. pont.** A parkolóhely-üzemeltetési díj a bérleményhez tartozó 24 parkolóhelyre vonatkozik.

**3. pont.** **A Bérlő felmondási ideje {G.FELMONDAS_MELLEKLET_NAP} nap.**

**4. pont.** Az Üzemeltető a jelen melléklet 1. pontján kívüli időszakban is köteles a
készenléti ügyeletet biztosítani.

---

*Aláírások:*

Kavicspart Ingatlanhasznosító Kft. — Bérbeadó
Delta-Ipari Szolgáltató Zrt. — Bérlő
Hegyi és Társa Építőipari Bt. — Üzemeltető
"""

Path("corpus/D6.md").write_text(D)
print(f"corpus/D6.md kiírva — {len(D):,} karakter".replace(",", " "))
