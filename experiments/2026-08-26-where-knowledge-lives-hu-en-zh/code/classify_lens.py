#!/usr/bin/env python3
"""Mérés B / 2. rész — a logit lens tokenjeinek nyelvi osztályozása (LAPTOP).

    python3 src/classify_lens.py

Miért a laptopon? Mert itt van rendes szótár: a hunspell **hu_HU.dic** (magyar) és a
`/usr/share/dict/american-english` (angol). A runbook 2000 szavas gyakorisági listát írt
elő — ennél a két szótár erősebb és hivatkozható.

Osztályok (a runbook három kategóriája FINOMÍTVA, mert a kényszerített hármas besorolás
elrejtené a zajt):
  zh          — CJK írásjegyet tartalmaz
  hu          — `ő`/`ű` (gyakorlatilag magyar-egyedi), vagy a magyar szótárban van (angolban nem)
  en          — az angol szótárban van (magyarban nem)
  közös       — MINDKÉT szótárban szerepel (pl. „a", „is", „ha") → nyelvileg NEM dönthető el
  ékezetes?   — más ékezet (á é í ó ö ú ü), de egyik szótárban sincs → tipikusan magyar TÖREDÉK
  ismeretlen  — latin betűs töredék, ékezet nélkül, egyik szótárban sincs
  egyéb       — írásjel, szám, whitespace, más írásrendszer

⛔ A dolgozat központi görbéjéhez („angol tokenek aránya") ezért KÉT határt adunk:
  szigorú = csak `en`
  tág     = `en` + `közös` + `ismeretlen`
A kettő közti sáv maga a mérési bizonytalanság — ezt az ábrán is meg kell mutatni.

Kimenet: reports/03_logit_lens.{json,md} · reports/03_classifier_minta.md ·
         figures/03_logit_lens.png · figures/03_valasz_rang.png
"""
import argparse
import json
import pathlib
import random
import re
import unicodedata
from collections import defaultdict

import numpy as np
import scope_paths


HERE = pathlib.Path(__file__).resolve().parent.parent
RES = scope_paths.res(HERE)
OUT = scope_paths.reports(HERE)
FIG = scope_paths.figures(HERE)
HU_DIC = pathlib.Path("/usr/share/hunspell/hu_HU.dic")
EN_DIC = pathlib.Path("/usr/share/dict/american-english")
CLASSES = ("zh", "hu", "en", "közös", "ékezetes?", "ismeretlen", "egyéb")


def load_dicts():
    hu = set()
    for line in HU_DIC.read_text(encoding="iso-8859-2", errors="replace").splitlines()[1:]:
        w = line.split("/")[0].strip().lower()
        if w:
            hu.add(w)
    en = {w.strip().lower() for w in EN_DIC.read_text(encoding="utf-8", errors="replace").splitlines() if w.strip()}
    return hu, en


def has_cjk(s):
    return any("一" <= c <= "鿿" or "㐀" <= c <= "䶿" or "豈" <= c <= "﫿" for c in s)


def other_script(s):
    for c in s:
        if c.isalpha():
            name = unicodedata.name(c, "")
            if not name.startswith("LATIN") and not has_cjk(c):
                return True
    return False


def make_classifier(hu, en):
    strip_re = re.compile(r"^[^\w]+|[^\w]+$", re.UNICODE)

    def classify(text):
        t = text.strip()
        if not t:
            return "egyéb"
        if has_cjk(t):
            return "zh"
        if other_script(t):
            return "egyéb"
        core = strip_re.sub("", t).lower()
        if not core or core.isdigit() or not any(c.isalpha() for c in core):
            return "egyéb"
        if any(c in "őű" for c in core):
            return "hu"
        in_hu, in_en = core in hu, core in en
        if in_hu and in_en:
            return "közös"
        if in_hu:
            return "hu"
        if in_en:
            return "en"
        if any(c in "áéíóöúü" for c in core):
            return "ékezetes?"
        return "ismeretlen"

    return classify


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tuned", action="store_true", help="a tanult fordítókkal készült lens_top_tuned.npz-t olvassa")
    args = ap.parse_args()
    sfx = "_tuned" if args.tuned else ""
    tag = " (tuned lens)" if args.tuned else ""
    hu, en = load_dicts()
    classify = make_classifier(hu, en)
    print(f"szótárak: magyar {len(hu)} · angol {len(en)} szó")

    vocab = json.load(open(RES / f"lens_vocab{sfx}.json", encoding="utf-8"))
    tok_class = {int(k): classify(v["text"]) for k, v in vocab.items()}
    z = np.load(RES / f"lens_top{sfx}.npz")
    ids, logits = z["ids"], z["logits"].astype(np.float32)      # [N, 33, 20]
    index = json.load(open(RES / f"lens_index{sfx}.json", encoding="utf-8"))
    N, L, K = ids.shape

    cls_idx = {c: i for i, c in enumerate(CLASSES)}
    lut = np.zeros(int(ids.max()) + 1, dtype=np.int8)
    for tid, c in tok_class.items():
        lut[tid] = cls_idx[c]
    cls = lut[ids]                                              # [N, 33, 20]

    # softmax a top-20-on belül — a puszta darabszám elmossa, hogy az 1. és a 20. hely nem egyenrangú
    w = np.exp(logits - logits.max(-1, keepdims=True))
    w /= w.sum(-1, keepdims=True)

    agg = defaultdict(lambda: {c: np.zeros(L) for c in CLASSES} | {f"w_{c}": np.zeros(L) for c in CLASSES})
    counts = defaultdict(int)
    for n, meta in enumerate(index):
        key = f"{meta['group']}/{meta['lang']}" if meta["kind"] == "fact" else f"{meta['kind'].upper()}/{meta['lang']}"
        counts[key] += 1
        for c, ci in cls_idx.items():
            m = (cls[n] == ci)
            agg[key][c] += m.sum(-1) / K
            agg[key][f"w_{c}"] += (w[n] * m).sum(-1)

    result = {}
    for key, d in agg.items():
        n = counts[key]
        result[key] = {"n": n, **{c: (d[c] / n).round(4).tolist() for c in CLASSES},
                       **{f"w_{c}": (d[f"w_{c}"] / n).round(4).tolist() for c in CLASSES}}
    (OUT / f"03_logit_lens{sfx}.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")

    # ── 100 token ellenőrző bírálatre (a runbook előírja az osztályozó pontosságát) ──
    rnd = random.Random(0)
    sample = rnd.sample(sorted(tok_class), 100)
    lines = ["# Nyelvosztályozó — 100 véletlen token ellenőrző bírálatre", "",
             "A `text` a dekódolt token (a `piece` a nyers BPE-alak). Írd át az `osztály` oszlopot, "
             "ha nem értesz egyet; az egyezési arány megy a módszertanba.", "",
             "| # | text | piece | osztály |", "|---|---|---|---|"]
    for i, tid in enumerate(sample, 1):
        v = vocab[str(tid)]
        lines.append(f"| {i} | `{v['text']}` | `{v['piece']}` | {tok_class[tid]} |")
    (OUT / f"03_classifier_minta{sfx}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ── összefoglaló ────────────────────────────────────────────────────────
    md = ["# Mérés B — logit lens", "",
          f"258 prompt utolsó prompt-tokene, {L} sík (0 = embedding, L+1 = resid_post(L)), top-{K} token rétegenként.",
          f"Osztályozó: hunspell hu_HU ({len(hu)} szó) + american-english ({len(en)} szó); a besorolás "
          "mintája: [03_classifier_minta.md](03_classifier_minta.md).", "",
          "## Angol tokenek aránya rétegenként (szigorú → tág)", "",
          "| csoport/nyelv | n | 0. réteg | 8. | 16. | 24. | 32. (utolsó) | csúcs (réteg) |",
          "|---|---|---|---|---|---|---|---|"]
    for key in sorted(result):
        r = result[key]
        strict = np.array(r["en"])
        loose = strict + np.array(r["közös"]) + np.array(r["ismeretlen"])
        peak = int(strict.argmax())
        md.append(f"| {key} | {r['n']} | " + " | ".join(
            f"{strict[i]:.0%}–{loose[i]:.0%}" for i in (0, 8, 16, 24, L - 1)) +
            f" | {strict[peak]:.0%} ({peak}) |")

    md += ["", "## A prompt saját nyelvének aránya rétegenként", "",
           "| csoport/nyelv | 0. | 8. | 16. | 24. | 32. |", "|---|---|---|---|---|---|"]
    for key in sorted(result):
        lang = key.split("/")[1]
        own = np.array(result[key][lang if lang != "en" else "en"])
        md.append(f"| {key} | " + " | ".join(f"{own[i]:.0%}" for i in (0, 8, 16, 24, L - 1)) + " |")

    (OUT / f"03_logit_lens{sfx}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md[:14]))
    print(f"\n→ {OUT / '03_logit_lens.md'}")


if __name__ == "__main__":
    main()
