#!/usr/bin/env python3
"""A ellenőrző kör útmutatójának GENERÁLÁSA az aktuális futáskörre.

    python3 code/kezi_kor_utmutato.py                                   # base kör
    SCOPE_RES=results_instruct SCOPE_REPORTS=reports_instruct \
        python3 code/kezi_kor_utmutato.py                               # instruct kör

⛔ Miért generált és nem kézzel írt? Mert a 2026-08-24-i kör pontosan azon bukott el, hogy
kézzel írt riportba kézzel másolt számok kerültek, és a forrásadat közben megváltozott.
Az útmutató minden száma (csonkolás, degeneráció, a bíráló ítélet-eloszlása, az előző kör
összevetése) ITT a `gen.jsonl`-ből és a `scores.csv`-ből számolódik.

A második és további köröknél a legfontosabb üzenet nem a rubrika, hanem a MÉRCE ÁLLANDÓSÁGA:
ha a 2. körben szigorúbb vagy elnézőbb vagyok, mint az 1.-ben, akkor a base↔instruct
különbség részben az ÉN elmozdulásomat méri, nem a post-trainingét.
"""
import argparse
import collections
import csv
import json
import pathlib

import scope_paths

HERE = pathlib.Path(__file__).resolve().parent.parent
RES, OUT = scope_paths.res(HERE), scope_paths.reports(HERE)
LANGS = ["hu", "en", "zh"]
LANG_NAME = {"hu": "magyar", "en": "angol", "zh": "kínai"}
# A körök sorrendje és neve — a fájlnévből azonosítva. Ha új kör jön, ide kell felvenni.
ROUNDS = [("results", "1. kör"), ("results_instruct", "2. kör"),
          ("results_instruct_raw", "3. kör — KONTROLL")]
BASE_RES = HERE / "results"                      # az 1. kör, viszonyításnak


def jsonl(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def round_label(res):
    """⛔ A modellt a MÉRT ADATBÓL olvassuk, nem a SCOPE_MODEL env-ből: az útmutatót gyakran
    env nélkül generálja az ember, és akkor a `tag()` némán a base modellt írná ki egy
    instruct kör útmutatójára. A `model` mezőt a `run.py` menti; a base kör futása régebbi,
    ott még nincs — a hiánya azonosítja a base kört."""
    r = json.loads((res / "gen.jsonl").read_text(encoding="utf-8").splitlines()[0])
    model = r.get("model") or "Qwen/Qwen3.5-9B-Base"
    chat = bool(r.get("chat_template"))
    return model.split("/")[-1] + (" · chat-sablon" if chat else " · nyers folytatásos prompt")


def gen_stats(res):
    """(csonkolt, degenerált, önértékelő-vágás) nyelvenként — a kör „terepviszonyai"."""
    g = jsonl(res / "gen.jsonl")
    return {
        "n": len(g),
        "trunc": collections.Counter(r["lang"] for r in g if r["truncated"]),
        "degen": collections.Counter(r["lang"] for r in g if r.get("degenerate")),
        "cut": sum(1 for r in g if r.get("self_eval_cut") is True),
        "suspect": [f'{r["item_id"]}/{r["lang"]}' for r in g if r.get("self_eval_cut") == "suspect"],
    }


MARKER = "Generált fájl (`code/kezi_kor_utmutato.py`)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true",
                    help="kézzel írt útmutatót is felülír (alapból megtagadja)")
    args = ap.parse_args()
    is_base = scope_paths.res(HERE) == BASE_RES
    names = [d for d, _ in ROUNDS]
    idx = names.index(RES.name) if RES.name in names else len(names)
    kor_nev = dict(ROUNDS).get(RES.name, "kör")
    # minden KORÁBBI kör, amelyiknek már van generálása — ezekhez viszonyítunk
    prev = [(lab, gen_stats(HERE / d)) for d, lab in ROUNDS[:idx]
            if (HERE / d / "gen.jsonl").exists()]
    st = gen_stats(RES)

    scores_p = RES / "scores.csv"
    if not scores_p.exists():
        raise SystemExit(f"nincs {scores_p} — előbb fusson a judge.py erre a körre")
    rows = list(csv.DictReader(scores_p.open(encoding="utf-8")))
    scope = [r for r in rows if r["group"] in ("ZH", "HU")]
    jd = collections.Counter(r["judge"].strip() for r in scope)
    done = sum(1 for r in scope if r["manual"].strip())

    d1_p = RES / "d1_scores.csv"
    unt = [r for r in csv.DictReader(d1_p.open(encoding="utf-8")) if r["kind"] == "unt"] \
        if d1_p.exists() else []
    d1_done = sum(1 for r in unt if (r["manual_native"] or "").strip())

    env = ("" if is_base else
           "SCOPE_RES=" + (scope_paths.res(HERE).name) +
           " SCOPE_REPORTS=" + (scope_paths.reports(HERE).name) + " ")
    kor = f"{kor_nev} — **{round_label(RES)}**"

    m = [f"# Ellenőrző kör — {kor}", "",
         f"> Generált fájl (`code/kezi_kor_utmutato.py`) — a benne lévő számok az aktuális",
         f"> `{RES.name}/` tartalmából jönnek. Ha újrafutott a bírálat, generáld újra.", ""]

    if not is_base:
        # mi változott az előző körhöz képest — ez dönti el, mire kell figyelni
        is_control = RES.name.endswith("_raw")
        naplok = [f"`{HERE.name}/{d}/kezi_validacio_naplo.md`".replace(HERE.name + "/", "")
                  for d, _ in ROUNDS[:idx]]
        naplok = [f"`{('reports' if d == 'results' else d.replace('results', 'reports'))}"
                  f"/kezi_validacio_naplo.md`" for d, _ in ROUNDS[:idx]
                  if (HERE / d.replace("results", "reports") / "kezi_validacio_naplo.md").exists()
                  or d == "results"]
        m += ["## ⛔⛔ A LEGFONTOSABB szabály ebben a körben: azonos mérce", ""]
        if is_control:
            m += ["Ez a **kontroll-kör**. Ugyanaz a modell fut benne, mint a 2. körben "
                  "(`Qwen3.5-9B` instruct), de a **base kör nyers, folytatásos promptjával** — "
                  "chat-sablon nélkül. A cél egyetlen kérdés megválaszolása:", "",
                  "> A 2. körben mért javulás a **modellsúlyoktól** jön, vagy attól, hogy "
                  "chat-sablonnal promptoztuk?", "",
                  "A gépi bíráló ítéletein már lefutott a felbontás, és azt adta, hogy **a javulást "
                  "szinte teljes egészében a promptozás magyarázza** (a puszta súlycsere nettó +1 "
                  "item, p = 1,000; a chat-sablonra váltás +10, p = 0,041). Ez a ellenőrző kör azt "
                  "hivatott eldönteni, hogy **ez a következtetés a gépi bíráló műterméke-e** — "
                  "különösen a `hallucinacio` kategóriában, amit a bíráló alig használ.", ""]
        else:
            m += ["Ez a kör **összevetésre** készül az 1. körrel. A korpusz ugyanaz a 70 item, a "
                  "prompt ugyanaz a kérdés, a rubrika ugyanaz, a bíráló ugyanaz a Qwen3.6-35B. "
                  "**Egyetlen dolog változott: a modell.**", ""]
        m += ["Ebből következik, hogy amit mérünk, **csak akkor a vizsgált hatás, ha a te mércéd "
              "változatlan.** Ha itt szigorúbb vagy, mint a korábbi körökben voltál, ez a kör "
              "rosszabbnak fog látszani, mint amilyen; ha elnézőbb, jobbnak. **Ez a kör legnagyobb "
              "kockázata, nem a rubrika.**", "",
              "**Ezért mielőtt belekezdesz, olvasd át a saját korábbi döntéseidet:** "
              + " · ".join(naplok)
              + " — különösen a *„Különösen fontos ellenőrző döntések”* és a *„D1 értelmezési elv”* "
                "szakaszt. Azok a precedenseid.", ""]
        if is_control:
            m += ["⚠️ **Amit ebben a körben NE csinálj:** ne igazítsd az ítéletet ahhoz, amit a 2. "
                  "körben ugyanarra az itemre adtál. A két kör válaszszövege MÁS; itt is csak azt "
                  "kell megítélned, ami a lapon van. Ha ugyanaz a tartalom, természetes, hogy ugyanaz "
                  "az ítélet — de ez következmény legyen, ne cél.", ""]

    m += ["## Hol tartok?", "", "```bash",
          "cd <experiment-dir>",
          f"{env}python3 code/set_manual.py status", "```", "",
          f"Jelenleg: **Mérés A {done}/{len(scope)}** kötelező válasz · **D1 UNT {d1_done}/{len(unt)}**.", "",
          "✅ A ellenőrző oszlopok túlélik a `judge.py` újrafuttatását — `(item_id, nyelv)` kulcson",
          "átmentődnek. Nyugodtan félbehagyhatod.", "",
          "---", "", "## Fájltérkép", "",
          "| Fájl | Szerep |", "|---|---|",
          f"| `{OUT.name}/02_kezi_ellenorzes.md` | **Mérés A olvasnivalója** — {len(scope)} válasz kérdéssel, várt válasszal, a modell válaszával, a bíráló indoklásával |",
          f"| `{OUT.name}/05_kezi_ellenorzes_d1.md` | **D1 olvasnivalója** — {len(unt)} UNT-válasz komponensenkénti pipákkal |",
          f"| `{RES.name}/scores.csv` → `manual` | Mérés A beírnivalója (a `set_manual.py`-n keresztül) |",
          f"| `{RES.name}/d1_scores.csv` → `manual_native` / `manual_distortion` | D1 beírnivalója |",
          f"| `{OUT.name}/02_meres_a.md`, `{OUT.name}/05_meres_d.md` | a **kimenet**, amit utána újragenerálsz |", "",
          "⛔ **A CSV-t soha ne szerkeszd kézzel.** A `answer` oszlop idézőjeleket, vesszőket és",
          "sortöréseket tartalmaz; a 08-24-i kör pontosan így veszett el (6 törött sor + 46 sorban",
          "kicserélt válaszszöveg). A `set_manual.py` validál: ismeretlen itemre, rossz nyelvre,",
          "érvénytelen ítéletre és a nevezőt túllépő darabszámra hibát dob.", "",
          "---", ""]

    # ── a kör terepviszonyai ────────────────────────────────────────────────
    m += ["## Ennek a körnek a terepviszonyai", "",
          "Amivel ebben a körben találkozni fogsz (a `gen.jsonl`-ből számolva):", "",
          "| jelenség | " + " | ".join(LANG_NAME[l] for l in LANGS) + " | összesen |",
          "|---|---|---|---|---|",
          "| a token-keretbe ütközött (csonkolt) | " + " | ".join(str(st["trunc"][l]) for l in LANGS)
          + f" | **{sum(st['trunc'].values())}/{st['n']}** |",
          "| ismétlési hurokba esett (degenerált) | " + " | ".join(str(st["degen"][l]) for l in LANGS)
          + f" | **{sum(st['degen'].values())}/{st['n']}** |"]
    if prev:
        cols = [lab for lab, _ in prev] + [f"{kor_nev} (ez)"]
        stats = [x for _, x in prev] + [st]
        def row(lab, key):
            return f"| {lab} | " + " | ".join(
                f"{sum(x[key].values())}/{x['n']} ({', '.join(f'{l} {x[key][l]}' for l in LANGS)})"
                for x in stats) + " |"
        m += ["", "Összevetés a korábbi körökkel — ez segít ráhangolódni, mi lesz MÁS:", "",
              "| | " + " | ".join(cols) + " |", "|---" * (len(cols) + 1) + "|",
              row("csonkolt", "trunc"), row("ismétlési hurok", "degen"),
              "| önértékelő toldalék levágva | " + " | ".join(f"{x['cut']}/{x['n']}" for x in stats) + " |", ""]
        ref_lab, ref = prev[0]                      # az 1. kör a viszonyítási alap
        notes = []
        if sum(st["trunc"].values()) > sum(ref["trunc"].values()) * 1.3:
            notes.append(f"⚠️ **Lényegesen több a csonkolt válasz**, mint az {ref_lab}ben "
                         f"({sum(st['trunc'].values())} vs. {sum(ref['trunc'].values())}): a modell "
                         "bőbeszédűbb. A keret minden körben ugyanaz (fact 200, UNT/kontroll 800 "
                         "token), tehát ez nem mérési hiba — de **sok választ félbevágva fogsz látni**.")
        if st["degen"]["hu"] == 0 and ref["degen"]["hu"]:
            notes.append(f"⭐ **A magyar ismétlési hurok eltűnt** ({ref['degen']['hu']} → 0), a kínai "
                         f"viszont megmaradt ({ref['degen']['zh']} → {st['degen']['zh']}). Kínai "
                         "válaszoknál számíts beragadásra.")
        if st["cut"] == 0 and ref["cut"]:
            notes.append(f"⭐ **Önértékelő toldalék nincs** ({ref['cut']} → 0): ez a kör nem ír a válasz "
                         "után saját feladatkiírást, tehát a `text_clean` = a nyers szöveg.")
        if st["cut"] and st["cut"] >= ref["cut"]:
            notes.append(f"⛔ **Az önértékelő toldalék VISSZATÉRT** ({ref['cut']} → {st['cut']}): a modell "
                         "a válasz után gyakran saját feladatkiírást ír "
                         "(*请判断回答是否正确…*, *A single-select problem…*). A `clean_answers.py` "
                         "levágja, és az ív a levágott (`text_clean`) szöveget mutatja — **azt ítéld meg**, "
                         "ne a nyerset. Ahol a vágás történt, az ív külön jelzi.")
        if sum(st["degen"].values()) >= sum(ref["degen"].values()):
            worst = max(LANGS, key=lambda l: st["degen"][l])
            notes.append(f"⛔ **Az ismétlési hurok is visszatért** (összesen "
                         f"{sum(ref['degen'].values())} → {sum(st['degen'].values())}; a legtöbb a "
                         f"{LANG_NAME[worst]} válaszoknál: {ref['degen'][worst]} → {st['degen'][worst]}). "
                         "A beragadás dekódolási jelenség: a hurok ELŐTTI tartalom alapján ítélj, a "
                         "hurkot magát ne rójuk fel.")
        if notes:
            m += notes + [""]
    if st["suspect"]:
        m += [f"⛔ **{len(st['suspect'])} válaszban az önértékelő marker a szöveg ELEJÉN áll**, ezért nem "
              f"vágtunk: {', '.join(st['suspect'])}. Ezeket nézd meg külön — lehet, hogy a marker a "
              "válasz része.", ""]

    m += ["---", "", f"# Mérés A — {len(scope)} válasz (kötelező)", "",
          "## A négy ítélet", "",
          "| ítélet | mikor |", "|---|---|",
          "| `helyes` | a válasz konkrétan megnevezi a várt információt (más megfogalmazás, más nyelv rendben) |",
          "| `reszben` | konkrét és a jó irányba mutat, de nem pontosan a várt érték — „nagyjából stimmel”: jó kategória rossz elemmel, jó időszak rossz ablakkal, kettőből egy jó |",
          "| `helytelen` | mást állít, kitér, felsorolja a lehetőségeket, vagy nem válaszol |",
          "| `hallucinacio` | KONKRÉT kitalált tényt állít magabiztosan (nevet, helyet, dátumot, intézményt), és az téves |",
          "",
          "### A `helytelen` / `hallucinacio` határ — ez a kör legfontosabb megkülönböztetése", "",
          "Az 1. körben ez adta a korrekciók **43/45-ét**, és ebből lett a dolgozat egyik önálló",
          "eredménye (a téves válaszok 50–86%-a magabiztos kitaláció). A gépi bíráló ezt a",
          f"kategóriát gyakorlatilag nem használja — ebben a körben is csak **{jd['hallucinacio']}** "
          f"hallucinációt és **{jd['reszben']}** `reszben`-t adott {len(scope)} válaszra.", "",
          "A szabály, amit az 1. körben alkalmaztál (`kezi_validacio_naplo.md`):", "",
          "> A `hallucinacio` címkét akkor használtam, amikor a hibás válasz konkrét kitalált",
          "> szerzőt, helyet, dátumot, intézményt vagy részletes fabrikált tényt állított;",
          "> egyszerű rossz kategória vagy nem-válasz `helytelen` maradt.", "",
          "### Döntési fa", "", "```",
          "Válaszol egyáltalán a kérdésre?",
          "├─ NEM (kitér, felsorol, kérdést ismétel) ──────────────► helytelen",
          "└─ IGEN, konkrétumot állít",
          "   ├─ pontosan a várt érték ──────────────────────────► helyes",
          "   ├─ nem pontosan, de a jó irányba mutat ────────────► reszben",
          "   └─ téves",
          "      ├─ konkrét kitalált név/hely/dátum/intézmény ───► hallucinacio",
          "      └─ csak rossz kategória, nincs kitalált adat ───► helytelen",
          "```", "",
          "## ⚠️ Amit NE rójunk fel", "",
          "- **Bőbeszédűség és formázás.** Ez a modell markdownt használ (`**félkövér**`, felsorolás,",
          "  fejezetcím). A forma nem számít, csak a tartalom.",
          "- **A válasz nyelve.** Ha magyar kérdésre angolul felel, de a tartalom jó, az `helyes`.",
          "- **A hiányzó rész csonkolt válaszban.** CSAK a meglévő szövegrészt értékeld. Ha a leírt",
          "  rész alapján nem dönthető el, az `helytelen` — de nem `hallucinacio`, mert nem állított",
          "  kitalált konkrétumot.",
          "- **Az ismétlési hurok.** A beragadás dekódolási jelenség; a hurok ELŐTTI tartalom számít.",
          "",
          "## Ha nem olvasol kínaiul", "",
          "A kínai cellák (`*/zh`) a mátrix harmadát adják, ezért nem hagyhatók ki. Amit tehetsz:",
          "a várt válasz kínai alakja ott van az ívben (`Várt:` sor), és a legtöbb ítélet eldönthető",
          "azzal, hogy **szerepel-e a várt karaktersorozat a válaszban**. Ha igen és a mondat állítja",
          "(nem tagadja, nem alternatívaként sorolja) → `helyes`. Ha nem szerepel, de a válasz",
          "magabiztosan megnevez EGY MÁSIK konkrét helyet/nevet → `hallucinacio`. Ha csak körülír",
          "vagy felsorol → `helytelen`. Kétes esetben jelöld meg és kérdezz rá.", "",
          "## Beírás", "", "```bash",
          f"{env}python3 code/set_manual.py a HU04 en helytelen",
          f"{env}python3 code/set_manual.py a ZH10 hu hallucinacio", "",
          "# a bíráló ítéletének tömeges megerősítése (a ZH+HU csoportra):",
          f"{env}python3 code/set_manual.py a --confirm-all", "```", "",
          "⚠️ A `--confirm-all` **minden** még üres sorra beírja a bíráló ítéletét. Csak akkor",
          "használd, ha már végigolvastad az ívet, és a maradékkal tényleg egyetértesz.", "",
          "## Kiértékelés", "", "```bash",
          f"{env}python3 code/analyze_a.py", "```", "",
          f"→ `{OUT.name}/02_meres_a.md` (3×3 mátrix, hallucinációs tábla, megbízhatósági szakasz)", "",
          "---", "", f"# Mérés D1 — {len(unt)} UNT-válasz (kötelező)", "",
          "## Mit kell eldöntened", "",
          "Fogalmanként előre rögzített **native** (a fogalom valódi jelentésmagjai) és **distortion**",
          "(tipikus félreértések) komponenslista van. Minden válaszra két szám kell: hány native és",
          "hány distortion komponens jelenik meg ténylegesen a szövegben.", "",
          "Az 1. körben alkalmazott elved (`kezi_validacio_naplo.md`):", "",
          "> Egy komponens csak akkor kapott találatot, ha a komponens tartalmi magja ténylegesen",
          "> megjelent. Összetett komponensnél nem vettem automatikusan teljes találatnak egy",
          "> részletet. A torzításokat is pozitív állításként kezeltem: csak akkor számoltam, ha a",
          "> hibás keretezés a válaszban ténylegesen megjelent, puszta hiányból nem következtettem",
          "> rá — kivéve ahol maga a torzítás definíciója kifejezetten egy jelentésárnyalat hiánya volt.", "",
          "## Beírás", "", "```bash",
          f"{env}python3 code/set_manual.py d UNT-HU01 hu --native 2 --distortion 1", "```", "",
          "A `set_manual.py` ellenőrzi, hogy a szám belefér-e a fogalom komponenslistájába —",
          "a nevezőt (`native_n`) a **befagyasztott** `items.jsonl` adja, azt nem lehet felülírni.", "",
          "## Kiértékelés", "", "```bash",
          f"{env}python3 code/analyze_d.py", "```", "",
          "---", "", "# Ellenőrző lista", "",
          f"- [ ] Mérés A: mind a {len(scope)} kötelező válasz kapott ellenőrző ítéletet (`set_manual.py status`)",
          f"- [ ] D1: mind a {len(unt)} UNT-válasz kapott `--native` és `--distortion` számot",
          "- [ ] `analyze_a.py` és `analyze_d.py` újrafuttatva",
          "- [ ] a riportok fejlécében nincs már „a ellenőrző kör hátravan” figyelmeztetés"]
    if not is_base:
        m += ["- [ ] **a mércéd egyezik az 1. körével** — kétes eseteknél visszanéztél a "
              "`kezi_validacio_naplo.md`-be",
              "- [ ] a kör eltéréseit ugyanúgy naplóztad, mint az 1. körnél"]
    m += ["", "# Gyakori hibák", "",
          "| hiba | miért baj |", "|---|---|",
          "| a CSV kézi szerkesztése | idézőjel-/vesszőtörés → némán elromlik egy cella (megtörtént) |",
          "| a nyers válaszra ítélni a tisztított helyett | a bíráló a `text_clean`-t látta; az ív is azt mutatja |",
          "| a csonkolt válasz hiányát felróni | a keret a mérés korlátja, nem a modell hibája |",
          "| a formázást (markdown) hibának venni | a tartalom számít |",
          "| a `hallucinacio` és a `helytelen` összemosása | ez adja a kör fő eredményét |"]
    if not is_base:
        m.append("| más mércével ítélni, mint az 1. körben | a base↔instruct különbség a SZERZŐ elmozdulását mérné |")

    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / "00_KEZI_KOR_UTMUTATO.md"
    # ⛔ ŐR: a base kör útmutatója KÉZZEL írt (2026-08-24), és egyszer már felülírtam
    # generálttal. Kézzel írt fájlt csak `--force`-szal írunk felül.
    if p.exists() and MARKER not in p.read_text(encoding="utf-8"):
        raise SystemExit(f"⛔ {p} létezik és NEM generált (nincs benne a generátor-jelölés).\n"
                         f"   Ha tényleg felül akarod írni: --force. Előbb mentsd el.")
    p.write_text("\n".join(m) + "\n", encoding="utf-8")
    print(f"→ {p}")


if __name__ == "__main__":
    main()
