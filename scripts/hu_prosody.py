"""Determinisztikus magyar prozódia: szótagszám, rímkulcs, rímséma.

Ez a modul a munka mérőeszköze. Ugyanez fut az F0-ban a korpusz annotálásakor
és az F4-ben a generált versek értékelésekor — tehát **nem az LLM-től várjuk a
formai helyességet, hanem mérjük**. Egyetlen sor sem hívja meg semmilyen
modellt.

Három dolgot csinál:

1. **Szótagszám.** Magyarban minden szótag magja pontosan egy magánhangzó, és
   a helyesírás nem ismer diftongust — így a magánhangzó-számlálás nem
   közelítés, hanem maga a szabály. (Az „au/eu” idegen szavakban két szótag:
   „a-u-tó” = 3, ami helyes.) A `validate_prosody.py` ezt külső igazsághoz méri:
   a Toldi és a János vitéz felező tizenkettesben íródott, tehát a soraiknak
   12 szótagosnak kell lenniük — irodalomtörténeti tény, nem a mi feltevésünk.

2. **Rímkulcs.** A magyar rím túlnyomórészt **asszonánc**: a magánhangzók
   egyeznek, a mássalhangzók lazábban. A kulcs a sor végétől visszafelé az
   utolsó két magánhangzóig tartó fonémasor, szóhatár nélkül — a rím a
   hangzáson alapul, nem a helyesíráson.

3. **Rímséma.** Strófán belüli páronkénti rím → betűcímkék (AABB, ABAB,
   ABCB…). A küszöböt nem hasból lőjük be: a `validate_prosody.py` a valódi
   strófák és a szerzők között összekevert kontroll-strófák pontszám-eloszlását
   veti össze.

Standalone: standard library only, no configuration file, no model call. Run it
directly for a self-test:

    python3 scripts/hu_prosody.py
"""

from __future__ import annotations

import re
import unicodedata

# Magyar magánhangzók. A szótagszámlálás alapja: magyarban minden szótag magja
# pontosan egy magánhangzó (nincs helyesírási diftongus), így a
# magánhangzó-számlálás nem közelítés, hanem a szabály maga.
VOWELS = set("aáeéiíoóöőuúüű")

# Kétjegyű és háromjegyű magyar mássalhangzók — a rímkulcs fonéma-szintű
# összevetéséhez kell, hogy az „sz” egy hangnak számítson, ne kettőnek.
DIGRAPHS = ("dzs", "cs", "dz", "gy", "ly", "ny", "sz", "ty", "zs")

# Rímküszöbök. NEM hasból választott értékek: a `validate_prosody.py` a valódi
# rímpozíciók és a kevert kontroll-párok szeparációját méri végig a
# küszöbtartományon, és a rés 0,6-nál maximális (+83,5 százalékpont). A 0,8 a
# szigorú („tiszta rím”) szint, ahol a coda is pontosan egyezik. A kiértékelés
# MINDKETTŐT jelenti — a laza küszöb önmagában szépíthetne.
RHYME_THRESHOLD = 0.6
STRICT_RHYME_THRESHOLD = 0.8

# A hosszú/rövid magánhangzópárok a magyar rímben egyenértékűek („kút/rút”,
# „tűz/szűz”), az a/á és e/é viszont minőségben is különbözik — azokat NEM
# vonjuk össze. Ez nem stilisztikai ízlés: az a/á eltérő nyelvállás.
VOWEL_CLASS = {
    "a": "a", "á": "á",
    "e": "e", "é": "é",
    "i": "i", "í": "i",
    "o": "o", "ó": "o",
    "ö": "ö", "ő": "ö",
    "u": "u", "ú": "u",
    "ü": "ü", "ű": "ü",
}

# Kettőzött kétjegyű mássalhangzók: „asszony” = a-sz-sz-o-ny, nem a-s-sz-o-ny.
DOUBLED = {"ssz": "sz", "ccs": "cs", "zzs": "zs", "ggy": "gy", "lly": "ly",
           "nny": "ny", "tty": "ty", "ddz": "dz"}

# Mássalhangzó-osztályok a LAZA rímegyezéshez. A magyar asszonánc a záró
# mássalhangzót nem követeli pontosan: Petőfi „kezemben / verekednem” rímében
# az m és az n cserélődik, „adósságát / svábság” zárhangot vált. Ezek nem
# hibák, hanem a népies rím normája — a nazálisok, a zöngés/zöngétlen párok
# és a likvidák egymással rímelnek.
CONSONANT_CLASS = {
    "m": "N", "n": "N", "ny": "N",
    "t": "T", "d": "T", "ty": "T", "gy": "T",
    "k": "K", "g": "K",
    "p": "P", "b": "P",
    "s": "S", "zs": "S",
    "sz": "Z", "z": "Z", "c": "Z", "dz": "Z",
    "cs": "C", "dzs": "C",
    "f": "F", "v": "F",
    "l": "L", "r": "L", "j": "L", "ly": "L",
    "h": "H",
}


def _coda_class(coda: list[str]) -> tuple[str, ...]:
    """Coda fonológiai osztály-sora — a laza (asszonánc) egyezéshez."""
    return tuple(CONSONANT_CLASS.get(c, c) for c in coda)


_RE_NONWORD = re.compile(r"[^\wáéíóöőúüű]+", re.UNICODE)
_RE_DIGIT = re.compile(r"\d")

# A leghosszabb digráfot kell előbb próbálni (dzs a dz előtt).
_DIGRAPHS_SORTED = tuple(sorted(DIGRAPHS, key=len, reverse=True))


def normalize(text: str) -> str:
    """Kisbetűs, írásjel nélküli alak — a prozódiai elemzés bemenete."""
    s = unicodedata.normalize("NFC", text).lower()
    s = s.replace("-", " ").replace("–", " ").replace("—", " ")
    return _RE_NONWORD.sub(" ", s).strip()


def count_syllables(text: str) -> int:
    """Szótagszám = magánhangzók száma (magyarban ez a szabály, nem becslés)."""
    return sum(1 for ch in normalize(text) if ch in VOWELS)


def phonemes(text: str) -> list[str]:
    """Fonémasor: a kétjegyű mássalhangzók egy hangnak számítanak.

    A szóhatárt eldobjuk: a rím a hangzáson alapul, nem a szótördelésen.
    """
    s = normalize(text).replace(" ", "")
    out: list[str] = []
    i = 0
    while i < len(s):
        tri = s[i : i + 3]
        if tri in DOUBLED:  # „ssz” → sz + sz
            out.append(DOUBLED[tri])
            out.append(DOUBLED[tri])
            i += 3
            continue
        for dg in _DIGRAPHS_SORTED:
            if s.startswith(dg, i):
                out.append(dg)
                i += len(dg)
                break
        else:
            out.append(s[i])
            i += 1
    return out


def rhyme_parts(line: str, depth: int = 2) -> tuple[list[str], list[str], list[str]]:
    """A sorvég rímre releváns darabjai.

    Visszaad: (magánhangzó-osztályok az utolsó `depth` szótagból,
               coda = az utolsó magánhangzó utáni mássalhangzók,
               a teljes fonémasor az utolsó `depth`. magánhangzótól).
    """
    ph = phonemes(line)
    vowel_pos = [i for i, p in enumerate(ph) if p in VOWELS]
    if not vowel_pos:
        return [], [], []
    take = vowel_pos[-depth:]
    start = take[0]
    tail = ph[start:]
    vowels = [VOWEL_CLASS.get(ph[i], ph[i]) for i in take]
    coda = ph[vowel_pos[-1] + 1 :]
    return vowels, coda, tail


def rhyme_score(a: str, b: str) -> float:
    """Két sorvég rímpontszáma [0..1] — determinisztikus, modell nélkül.

    Súlyozás: az utolsó magánhangzó és a záró mássalhangzó-váz (coda) a rím
    gerince (0,4 + 0,4), a megelőző szótag magánhangzója a „gazdagság” (0,2).
    A coda egyezése kétszintű: a pontos egyezés a teljes 0,4-et hozza, a
    fonológiai osztály-egyezés (nazális↔nazális, t↔d) 0,3-at — ez a magyar
    asszonánc, nem engedmény. A küszöböt a `validate_prosody.py` méri be a
    valódi és a kevert kontroll-párok szeparációja alapján.
    """
    va, ca, _ = rhyme_parts(a)
    vb, cb, _ = rhyme_parts(b)
    if not va or not vb:
        return 0.0
    score = 0.0
    if va[-1] == vb[-1]:
        score += 0.4
    if ca == cb:
        score += 0.4
    elif len(ca) == len(cb) and _coda_class(ca) == _coda_class(cb):
        score += 0.3
    if len(va) > 1 and len(vb) > 1 and va[-2] == vb[-2]:
        score += 0.2
    # Az azonos szó önmagával nem rím, hanem ismétlés — a magyar verstan
    # „önrímnek” hívja és hibának tekinti; a generálásnál pedig pont ez a
    # leggyakoribb olcsó trükk, ezért nem jutalmazzuk.
    if _last_word(a) and _last_word(a) == _last_word(b):
        score = min(score, 0.5)
    return round(score, 3)


def _last_word(line: str) -> str:
    words = normalize(line).split()
    return words[-1] if words else ""


# Gyakori magyar toldalékok a RAGRÍM felismeréséhez, hosszabb elöl. A magyar
# agglutináló, ezért az azonos toldalékú szavak automatikusan rímelnek
# („virágokat / dolgokat”) — költőileg ez a leggyengébb rím, és a generatív
# modell fő menekülőútja. A lista nem teljes morfológia, és nem is akar az
# lenni: a leggyakoribb rag/jel/képző-végződéseket fedi, determinisztikusan.
SUFFIXES = (
    "hetetlen", "hatatlan", "atlanul", "etlenül",
    "hattam", "hettem", "ottunk", "ettünk", "öttünk",
    "atlan", "etlen", "ságot", "séget", "okban", "ekben", "ökben",
    "ottam", "ettem", "öttem", "ottad", "etted", "unkat", "ünket",
    "ainak", "einek", "jaink", "jeink", "aihoz", "eihez",
    "ában", "ében", "ból", "ből", "ról", "ről", "tól", "től",
    "hoz", "hez", "höz", "nak", "nek", "val", "vel", "ért", "ként",
    "ság", "ség", "ást", "ést", "ása", "ése", "ásra", "ésre",
    "tam", "tem", "tál", "tél", "tunk", "tünk", "tak", "tek",
    "ott", "ett", "ött", "ván", "vén", "nék", "nák",
    "juk", "jük", "ják", "jék", "unk", "ünk", "tok", "tek", "tök",
    "ban", "ben", "ról", "nál", "nél", "kor", "ul", "ül",
    "ás", "és", "ok", "ek", "ök", "ak", "om", "em", "öm", "am",
    "ja", "je", "ai", "ei", "ra", "re", "ba", "be", "on", "en", "ön",
    "va", "ve", "ni", "ná", "né", "na", "ne", "ta", "te",
)


def inflectional_suffix(a: str, b: str) -> str | None:
    """Ha a két sorvégi szó UGYANARRA az ismert toldalékra végződik, adja vissza.

    Ez a ragrím jele: a rím a nyelvtanból jön, nem a költői választásból.
    Feltétel, hogy a toldalék levágása után maradjon érdemi tő — különben
    minden rövid szó ragrímnek minősülne.
    """
    wa, wb = _last_word(a), _last_word(b)
    if not wa or not wb or wa == wb:
        return None
    for suf in SUFFIXES:
        if (
            wa.endswith(suf)
            and wb.endswith(suf)
            and len(wa) >= len(suf) + 2
            and len(wb) >= len(suf) + 2
        ):
            return suf
    return None


def is_rich_rhyme(a: str, b: str, threshold: float = RHYME_THRESHOLD) -> bool:
    """Rímel-e, ÉS nem puszta ragrím. Ez az érdemi minőségi mérőszám.

    A modell a `rhyme_rate`-et olcsón emelheti ragrímmel; a `rhyme_quality`
    az, amit nem lehet trükkel megnyerni.
    """
    return rhyme_score(a, b) >= threshold and inflectional_suffix(a, b) is None


def rhyme_scheme(lines: list[str], threshold: float = RHYME_THRESHOLD) -> str:
    """Strófa → rímséma-címke (AABB, ABAB, ABCB…).

    Mohó címkézés: minden sor a legkorábbi olyan csoport betűjét kapja,
    amelynek BÁRMELY tagjával rímel a küszöb felett. A rímtelen sor új
    betűt kap — így az xAxA (félrím) `ABCB` alakban jelenik meg.
    """
    labels: list[str] = []
    groups: list[list[str]] = []
    for line in lines:
        found = None
        for gi, group in enumerate(groups):
            if any(rhyme_score(line, other) >= threshold for other in group):
                found = gi
                break
        if found is None:
            groups.append([line])
            found = len(groups) - 1
        else:
            groups[found].append(line)
        labels.append(chr(ord("A") + found) if found < 26 else "?")
    return "".join(labels)


def syllable_profile(lines: list[str]) -> list[int]:
    """Strófa szótagszám-profilja soronként (pl. [12, 12, 12, 12])."""
    return [count_syllables(ln) for ln in lines]


def has_digits(text: str) -> bool:
    """Számjegy a sorban → a szótagszámlálás nem megbízható (»1848« = ?)."""
    return bool(_RE_DIGIT.search(text))


if __name__ == "__main__":
    # A self-test KÜLSŐ IGAZSÁGHOZ mér, nem a saját kimenetéhez. A Toldi
    # felező tizenkettesben íródott — irodalomtörténeti tény, nem a mi
    # feltevésünk —, tehát ezeknek a soroknak 12 szótagosnak KELL lenniük.
    # (Mind a Toldi Előhangjából; a teljes 4 125 soros mérés 99,7 %-ban 12.)
    assert count_syllables("Ég a napmelegtől a kopár szík sarja") == 12
    assert count_syllables("Mint ha pásztortűz ég őszi éjszakákon,") == 12
    assert count_syllables("Messziről lobogva tenger pusztaságon:") == 12
    assert count_syllables("Toldi Miklós képe úgy lobog fel nékem") == 12
    # Az „au/eu” magyarul két szótag: „a-u-tó”. Ez helyes, nem hiba.
    assert count_syllables("autó") == 3

    # Valódi Arany-rímpárok az Előhangból. A második asszonánc: a magánhangzók
    # egyeznek, a mássalhangzók lazábban — magyarul ez a rím normája.
    assert rhyme_score("növését", "öklelését") == 1.0
    assert rhyme_score("nékem", "régiségben") >= RHYME_THRESHOLD

    # Ragrím: a pár azért „rímel”, mert ugyanaz a toldalék áll a végén. Nem
    # hiba — a magyar verselés normális eszköze, Aranynál a rímelő párok
    # 37,7 %-a ilyen —, de külön jelöljük, mert egy modell ezzel olcsón
    # megnyerné a rímarányt. Ezért van a `rhyme_quality` metrika.
    assert inflectional_suffix("éjszakákon", "pusztaságon") == "on"
    assert not is_rich_rhyme("éjszakákon", "pusztaságon")
    assert inflectional_suffix("növését", "öklelését") is None
    assert is_rich_rhyme("növését", "öklelését")

    # ⚠️ ISMERT KORLÁT, szándékosan tesztelve: a SUFFIXES lista nem teljes
    # morfológia. A tárgyesetű többes (`-okat`/`-eket`/`-akat`) nincs benne,
    # ezért a „virágokat / dolgokat” pár NEM minősül ragrímnek, pedig az.
    # A lista bővítése megváltoztatná a publikált `rhyme_quality` értékeket,
    # ezért a mérés lezárása után befagyasztottuk — ld. az eval-card
    # limitations szakaszát.
    assert inflectional_suffix("virágokat", "dolgokat") is None

    # Kontroll: két össze nem tartozó sorvég ne legyen rím.
    assert rhyme_score("asztal", "kertben") < RHYME_THRESHOLD

    assert rhyme_scheme(["növését", "öklelését", "nékem", "régiségben"]) == "AABB"
    assert syllable_profile(["autó", "autó"]) == [3, 3]
    assert has_digits("1848 tavaszán") and not has_digits("tavaszán")

    print(f"hu_prosody — self-test OK (rhyme threshold {RHYME_THRESHOLD}, "
          f"strict {STRICT_RHYME_THRESHOLD})")
