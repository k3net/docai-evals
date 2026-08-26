#!/usr/bin/env python3
"""Futáskör-váltó: melyik modellt mérjük és hova írunk.

A dolgozat több KÖRT futtat ugyanazon a 258 prompton (base → instruct → …). A körök
csak két dologban térnek el: a modellben és a kimeneti könyvtárban. Ezt két
környezeti változó dönti el, hogy egyetlen szkriptet se kelljen forkolni:

    SCOPE_MODEL   alapértelmezés: Qwen/Qwen3.5-9B-Base
    SCOPE_RES     alapértelmezés: results          (pl. results_instruct)
    SCOPE_REPORTS alapértelmezés: reports          (pl. reports_instruct)
    SCOPE_FIGURES alapértelmezés: a SCOPE_RES-ből SZÁRMAZTATVA (results_instruct → figures_instruct)
    SCOPE_CHAT    "1" → a modell chat-sablonjával promptozunk (instruct körhöz)
    SCOPE_PROMPTS alapértelmezés: prompts.jsonl  (pl. prompts_d3b.jsonl — a D3b újramérés
                  16 angol közelítőszó-promptja, KÜLÖN eredmény-könyvtárba: SCOPE_RES=results_d3b)

Példa a 2. körre (spark-dev, konténer):

    SCOPE_MODEL=Qwen/Qwen3.5-9B SCOPE_RES=results_instruct SCOPE_CHAT=1 \
        bash src/run_spark.sh src/run.py

⚠️ A `run_spark.sh` ezeket a változókat továbbadja a konténernek — ha új változót veszel
fel ide, oda is fel kell venni, különben némán az alapértelmezés fut le.
"""
import os

# ⛔ `get(k, default)` NEM jó: a run_spark.sh üres sztringként adja tovább a be nem
# állított változót, és az üres sztring létező kulcs — a default sosem lépne életbe.
MODEL = os.environ.get("SCOPE_MODEL") or "Qwen/Qwen3.5-9B-Base"
CHAT = os.environ.get("SCOPE_CHAT", "") in ("1", "true", "yes")


def res(root):
    """A futáskör eredmény-könyvtára a megadott gyökér alatt."""
    return root / (os.environ.get("SCOPE_RES") or "results")


def prompts(root):
    """A futtatandó prompt-fájl. ⛔ Ha nem az alapértelmezett, a SCOPE_RES-t is állítsd át,
    különben a mellék-promptok a fő kör gen.jsonl-jébe keverednek."""
    return root / (os.environ.get("SCOPE_PROMPTS") or "prompts.jsonl")


def reports(root):
    return root / (os.environ.get("SCOPE_REPORTS") or "reports")


def figures(root):
    """⛔⛔ Az ábra-könyvtárnak IS körönként külön kell lennie, különben a 2. kör elemzése
    NÉMÁN felülírja az 1. kör ábráit (azonos fájlnevek: `02_A1_...png` stb.), és a base kör
    ábrái visszaállíthatatlanul elvesznek. Ezért a nevet a SCOPE_RES-ből származtatjuk:
    `results` → `figures`, `results_instruct` → `figures_instruct`. Külön beállítani csak
    a SCOPE_FIGURES-szel kell, ha valakinek nem tetszik a származtatás."""
    explicit = os.environ.get("SCOPE_FIGURES")
    if explicit:
        return root / explicit
    r = os.environ.get("SCOPE_RES") or "results"
    suffix = r[len("results"):] if r.startswith("results") else "_" + r
    return root / ("figures" + suffix)


def tag():
    """Rövid, emberi címke a riportokba — melyik kör számai ezek."""
    return f"{MODEL.split('/')[-1]}{' · chat-sablon' if CHAT else ''}"
