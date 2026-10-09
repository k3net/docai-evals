"""01-es kör — közös segédek az F1 spark-lépéseihez: útvonalak, JSON-L, katalógus, LLM-hívás.

Az LLM-hívás a 00-ás `biralo.chat`-et használja (újrapróbával); a 00-ás `eszkozok/` a kísérlet gyökerében él, a
measurement-hosten is (`/exp/eszkozok`), ezért innen importálható. Konténerben a `kor01` a `/exp/kor01`.
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "adat"
F1S = A / "f1s"
R = ROOT / "eredmenyek"
sys.path.append(str(ROOT.parent / "eszkozok"))  # a végére: a kor01 saját moduljai (pl. osszeallit) elsőbbséget kapnak
from biralo import chat  # noqa: E402,F401
from common import read_jsonl, write_json, write_jsonl  # noqa: E402,F401

sys.path.insert(0, str(Path(__file__).resolve().parent))  # a 00-ás modulok a saját könyvtárukat előre teszik

CJK = re.compile(r"[぀-ヿ㐀-鿿가-힯]")
YES = {"igen", "ig", "i", "yes", "y", "ye"}
NO = {"nem", "ne", "n", "no"}
SPLITS = ("train", "val", "teszt")


def catalog() -> dict[str, dict]:
    return {t["name"]: t for t in json.loads((ROOT / "katalogus/eszkozok.json").read_text())}


def massive_map() -> dict[str, str | None]:
    """MASSIVE-intent → katalógus-eszköz (None: csevegés, X)."""
    return {k: v["eszkoz"] for k, v in json.loads((ROOT / "katalogus/massive_lekepezes.json").read_text()).items()}


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", (s or "").lower())).strip()


def opt_line(o: dict, lang: str) -> str:
    req = f" ({'kötelező' if lang == 'hu' else 'required'}: {', '.join(o['required'])})" if o.get("required") else ""
    return f"{o['name']}: {' '.join((o.get('description') or '').split())}{req}"


def p_yes(r: dict) -> tuple[float | None, float]:
    """P(igen) a top-20 logprobból (igen/nem-szerű első tokenek tömegével), és a két válasz együttes tömege."""
    yes = no = 0.0
    for t in r["choices"][0]["logprobs"]["content"][0]["top_logprobs"]:
        tok = t["token"].strip().lower()
        if tok in YES:
            yes += math.exp(t["logprob"])
        elif tok in NO:
            no += math.exp(t["logprob"])
    return (yes / (yes + no) if yes + no > 0 else None), yes + no


def llm_json(url: str, model: str, system: str, user: str, extra: dict, seed: int, tries: int = 4):
    """JSON-választ kér; a kódblokk-kerítést és a lezáratlan farkat kezeli. CJK-szöveget nem fogad el."""
    last = None
    for k in range(tries):
        try:
            r = chat(url, model, [{"role": "system", "content": system}, {"role": "user", "content": user}],
                     {**extra, "seed": seed * 10 + k}, None, timeout=900)
            txt = r["choices"][0]["message"]["content"] or ""
        except Exception as e:  # hálózati / szerverhiba → újrapróba
            last = f"http: {e}"
            continue
        if CJK.search(txt):
            last = "CJK"
            continue
        txt = re.sub(r"^```(?:json)?|```$", "", txt.strip(), flags=re.M).strip()
        start = min([i for i in (txt.find("{"), txt.find("[")) if i >= 0], default=-1)
        try:
            return json.loads(txt[start:]) if start >= 0 else json.loads(txt)
        except json.JSONDecodeError:
            end = txt.rfind("}")
            try:
                return json.loads(txt[start:end + 1])
            except Exception:
                last = "JSON"
    raise RuntimeError(f"LLM-hívás sikertelen ({last})")
