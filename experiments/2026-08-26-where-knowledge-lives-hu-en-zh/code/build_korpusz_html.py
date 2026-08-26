#!/usr/bin/env python3
"""A tesztkorpusz böngészhető aloldala: items.jsonl → korpusz.html.

    python3 code/build_korpusz_html.py

Az oldal a dolgozat aloldala: ugyanaz a stíluslap (a `dolgozat.html` `<style>` blokkját
emeli át, hogy a kettő ne csúszhasson szét), és a dolgozatból link mutat rá. Minden
tartalom az `items.jsonl`-ből jön; a fájlba kézzel írt itemadat nem kerülhet.

⛔ A prompt-sablonokat a `build_prompts.py`-ból olvassa (TEMPLATE, CTRL_Q, MAX_NEW), hogy a
melléklet és a tényleges futtatás sablonja bitre ugyanaz legyen.
"""
import html
import json
import pathlib

import scope_paths
import sys
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import build_prompts

ROOT = pathlib.Path(__file__).resolve().parent.parent
ITEMS = scope_paths.data(ROOT, "items.jsonl")
OUT = ROOT / "korpusz.html"
SZERZO = "Kiss Dániel"


def find_dolgozat():
    """⛔ A dolgozat fájlneve változhat (beadáskor a szerző nevére átnevezve), ezért nem
    rögzítjük: a `<title>Hol lakik a tudás?` alapján keressük meg, és a visszalinket
    URL-kódolva írjuk ki (szóköz és ékezet van benne)."""
    jelolt = [f for f in sorted(ROOT.glob("*.html")) if f.name != OUT.name
              and "Hol lakik a tudás?" in f.read_text(encoding="utf-8")[:4096]]
    if not jelolt:
        raise SystemExit("nem találom a dolgozat HTML-t (a <title>-ben „Hol lakik a tudás?” kell legyen)")
    return max(jelolt, key=lambda f: f.stat().st_mtime)


DOLGOZAT = find_dolgozat()
HREF = urllib.parse.quote(DOLGOZAT.name)

GROUPS = [
    ("ZH", "ZH-only", "Kínai Wikipédián vagy Baidu Baikén van szócikk, az angolon és a magyaron nincs."),
    ("HU", "HU-only", "Magyar Wikipédián van szócikk, az angolon és a kínain nincs."),
    ("UNI", "UNI", "Mindhárom wikin van szócikk: közös tudás, a mérés kontrollcsoportja."),
]
LANGS = [("hu", "hu"), ("en", "en"), ("zh", "zh")]
SRC_LABEL = {"zhwiki": "zh.wikipedia", "huwiki": "hu.wikipedia", "baike": "Baidu Baike",
             "huwiki+enwiki+zhwiki": "mindhárom wiki"}


def esc(x):
    return html.escape(str(x), quote=False)


def qcell(q):
    """A kérdés három nyelven, nyelvjelölővel."""
    return "<br>".join(
        f'<span class="lt lt-{code}">{lab}</span>{esc(q[code])}' for code, lab in LANGS)


def style_block():
    s = DOLGOZAT.read_text(encoding="utf-8")
    a, b = s.index("<style>"), s.index("</style>") + len("</style>")
    return s[a:b]


def main():
    rows = [json.loads(l) for l in ITEMS.read_text(encoding="utf-8").splitlines() if l.strip()]
    by = {}
    for r in rows:
        by.setdefault(r["group"], []).append(r)
    for v in by.values():
        v.sort(key=lambda r: r["id"])
    frozen = sorted({r["frozen"] for r in rows})
    assert len(frozen) == 1, f"több fagyasztási dátum: {frozen}"
    n_item = len(rows)
    n_unt = len(by.get("UNT", []))
    n_prompt = n_item * 3 + n_unt * 3

    o = ['<meta charset="utf-8">', f"<title>A tesztkorpusz — Hol lakik a tudás? — {SZERZO}</title>",
         style_block(),
         """<style>
  /* ── aloldal-specifikus ── */
  .backlink { font-family: var(--sans); font-size: .82rem; margin-bottom: 1rem; }
  .backlink a { color: var(--muted); text-decoration: none; }
  .backlink a:hover { color: var(--accent); }
  .grp-note { font-family: var(--sans); font-size: .86rem; color: var(--muted);
    margin: -.4rem 0 1rem; }
  table td .lt { margin-right: .3rem; }
  .qid { font-family: var(--mono); font-size: .78rem; }
  .qid a { color: var(--muted); text-decoration: none; }
  .qid a:hover { color: var(--accent); }
  .note { color: var(--zh); font-size: .82rem; }
  .komp { margin: 0; padding-left: 1rem; font-size: .84rem; }
  .komp li { margin-bottom: .15rem; }
  .torz { color: var(--muted); }
  /* ⛔ Mobilon a négyoszlopos itemtábla oldalra görgethető lenne, és a kérdés-oszlop
     olvashatatlanul keskeny: 700 px alatt ezért soronként egy kártyára bomlik. */
  @media (max-width: 700px) {
    table.korpusz thead { display: none; }
    table.korpusz, table.korpusz tbody, table.korpusz tr, table.korpusz td { display: block; width: 100%; }
    table.korpusz tr { border-bottom: 1px solid var(--hairline); padding: .5rem 0 .7rem; }
    table.korpusz tbody tr:last-child { border-bottom: none; }
    table.korpusz td { border: none; padding: .2rem .8rem; text-align: left; min-width: 0; }
    table.korpusz td[data-l]::before {
      content: attr(data-l); display: block; font-size: .64rem; letter-spacing: .07em;
      text-transform: uppercase; color: var(--muted); margin: .5rem 0 .15rem;
    }
    table.korpusz td:first-child { color: var(--accent); font-family: var(--mono); font-size: .8rem; }
  }
</style>""",
         '<div class="page">', "  <header>",
         f'    <p class="eyebrow">Melléklet a „Hol lakik a tudás?” dolgozathoz · {SZERZO}</p>',
         "    <h1>A tesztkorpusz</h1>",
         '    <p class="subtitle">Mind a 70 tesztkérdés három nyelven, a hozzájuk tartozó '
         "elvárt válasszal, forrással és a lefordíthatatlan fogalmak teljes jelentés-adatlapjával. "
         "Ez a lista rögzített: minden mérés ezen a korpuszon futott.</p>",
         '    <div class="meta-grid">',
         f'      <div><div class="k">Itemek</div><div class="v">{n_item}</div></div>',
         f'      <div><div class="k">Promptok</div><div class="v">{n_prompt}</div></div>',
         '      <div><div class="k">Nyelvek</div><div class="v">hu · en · zh</div></div>',
         f'      <div><div class="k">Rögzítve</div><div class="v">{frozen[0]}</div></div>',
         "    </div>", "  </header>", "",
         f'  <p class="backlink"><a href="{HREF}">← Vissza a dolgozathoz</a></p>', ""]

    # ── bevezető: hogyan lett a kérdésből prompt ──────────────────────────────
    tpl = build_prompts.TEMPLATE
    ctrl = build_prompts.CTRL_Q
    mx = build_prompts.MAX_NEW
    o += ["  <p>",
          f"    A korpusz négy csoportból áll: {len(by['ZH'])} csak kínaiul dokumentált tény, "
          f"{len(by['HU'])} csak magyarul dokumentált, {len(by['UNI'])} mindhárom nyelven meglévő "
          f"közös tény, végül {n_unt} lefordíthatatlan fogalom. A csoportbesorolás a Wikidata-sitelinkek alapján készült: ez azt mondja "
          "meg, melyik nyelvű enciklopédiában van szócikk, nem azt, hogy a modell tanítókorpusza "
          "mit tartalmazott. Ahol a többi nyelven említés-szintű nyom is akad, az a megjegyzés "
          "oszlopban szerepel.",
          "  </p>", "",
          "  <p>",
          "    Minden kérdésből három prompt készült, nyelvenként ugyanazzal a formázás nélküli "
          "folytatásos sablonnal (a base modell nem követ instrukciót, és minden burkolat nyelvi "
          "jelet vinne a mérésbe):",
          "  </p>",
          "  <pre><code>" + esc("\n".join(
              f"{lang}:  " + tpl[lang].replace("\n", "\\n") for lang, _ in LANGS)) + "</code></pre>",
          "  <p>",
          f"    A faktuális kérdések token-kerete {mx['fact']}, a fogalom-definícióké és a "
          f"kontrollszavaké {mx['unt']}. A lefordíthatatlan fogalmak mellé egy-egy jól fordítható "
          "kontrollszó is bekerült ugyanabból a jelentésmezőből, ugyanezzel a kérdés-formával:",
          "  </p>",
          "  <pre><code>" + esc("\n".join(
              f"{lang}:  " + tpl[lang].format(q=ctrl[lang].format(w="…")).replace("\n", "\\n")
              for lang, _ in LANGS)) + "</code></pre>", ""]

    # ── faktuális csoportok ───────────────────────────────────────────────────
    for gid, title, note in GROUPS:
        g = by[gid]
        o += [f'  <h2 id="{gid.lower()}"><span class="num">{len(g)} item</span>{esc(title)}</h2>',
              f'  <p class="grp-note">{esc(note)}</p>',
              '  <div class="tw wide">', '    <table class="korpusz">',
              "      <thead><tr><th>id</th><th class=\"wrap\">téma · forrás</th>"
              "<th class=\"wrap\">kérdés</th><th class=\"wrap\">elvárt válasz</th></tr></thead>",
              "      <tbody>"]
        for r in g:
            qid = r.get("qid") or ""
            qid_html = (f'<div class="qid"><a href="https://www.wikidata.org/wiki/{esc(qid)}" '
                        f'target="_blank" rel="noopener">{esc(qid)}</a></div>' if qid and qid != "—"
                        else '<div class="qid">—</div>')
            note_html = f'<div class="note">⚠ {esc(r["note"])}</div>' if r.get("note") else ""
            ans = "<br>".join(f'<span class="lt lt-{c}">{lab}</span>{esc(r["answer"][c])}'
                              for c, lab in LANGS)
            o += ["        <tr>",
                  f"          <td><strong>{esc(r['id'])}</strong></td>",
                  f'          <td class="wrap" data-l="téma · forrás">{esc(r["title"])}'
                  f'<div class="qid">{esc(SRC_LABEL.get(r["source"], r["source"]))}</div>'
                  f"{qid_html}{note_html}</td>",
                  f'          <td class="wrap" data-l="kérdés">{qcell(r["q"])}</td>',
                  f'          <td class="wrap" data-l="elvárt válasz">{ans}</td>',
                  "        </tr>"]
        o += ["      </tbody>", "    </table>", "  </div>", ""]

    # ── UNT ───────────────────────────────────────────────────────────────────
    unt = by["UNT"]
    n_hu = sum(1 for r in unt if r["src_lang"] == "hu")
    o += [f'  <h2 id="unt"><span class="num">{len(unt)} fogalom</span>UNT · lefordíthatatlan fogalmak</h2>',
          f'  <p class="grp-note">{n_hu} magyar és {len(unt) - n_hu} kínai fogalom, amelyeknek az '
          "angol közelítése bizonyíthatóan szegényebb. Minden fogalomhoz előre rögzítve: a natív "
          "jelentéskomponensek (ezeknek a válaszban meg kell jelenniük), az angol közelítés "
          "torzítás-jelei, és egy jól fordítható kontrollszó.</p>"]
    for r in unt:
        native = "".join(f"<li>{esc(x)}</li>" for x in r["native"])
        dist = "".join(f"<li>{esc(x)}</li>" for x in r["distortion"])
        ctrl_w = " · ".join(f'<span class="lt lt-{c}">{lab}</span>{esc(r["control"][c])}'
                            for c, lab in LANGS)
        o += ['  <div class="pelda">',
              f'    <div class="lbl">{esc(r["id"])} · {esc(r["concept"])} '
              f'({esc(r["src_lang"])}) → „{esc(r["en_approx"])}”</div>',
              f'    <p>{qcell(r["q"])}</p>',
              "    <p><strong>Natív jelentéskomponensek</strong> (ezek hiánya a torzulás mérőszáma):</p>",
              f'    <ul class="komp">{native}</ul>',
              '    <p class="torz"><strong>Az angol közelítés torzítás-jelei:</strong></p>',
              f'    <ul class="komp torz">{dist}</ul>',
              f"    <p><strong>Kontrollszó:</strong> {ctrl_w}</p>",
              "  </div>"]

    o += ["", "  <hr>", "  <footer>",
          f"    A korpusz gépi olvasható formája: <code>items.jsonl</code> (rögzítve {frozen[0]}), "
          "a belőle generált promptok: <code>prompts.jsonl</code>. Ez az oldal az "
          "<code>items.jsonl</code>-ből épül (<code>code/build_korpusz_html.py</code>), a kérdések "
          "szövege tehát bitre az, amit a modell kapott.",
          f'    <br><a href="{HREF}">← Vissza a dolgozathoz</a>',
          "  </footer>", "", "</div>", ""]

    OUT.write_text("\n".join(o), encoding="utf-8")
    print(f"→ {OUT} · {n_item} item · {n_prompt} prompt · {len(OUT.read_text(encoding='utf-8')):,} bájt"
          .replace(",", " "))


if __name__ == "__main__":
    main()
