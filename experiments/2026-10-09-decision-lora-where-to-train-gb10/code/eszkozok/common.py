"""Közös definíciók a LoRA-decision-head kísérlethez.

A kérdésforma, a címke-tokenek és a tokenizálás egyetlen helyen él, hogy a
vLLM-kiolvasás, a HF-kiolvasás és a tréning bitre ugyanazt a promptot lássa.
Konténerben fut (lora-train:2): az /exp a kísérlet munkakönyvtára, a /hf a
HuggingFace-cache.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
from pathlib import Path

EXP = Path(os.environ.get("LDH_EXP", "/exp"))
HF = Path(os.environ.get("LDH_HF", "/hf"))

SUBJECT_REPO = "Qwen/Qwen3.6-35B-A3B-FP8"
SUBJECT_SNAPSHOT = HF / "hub/models--Qwen--Qwen3.6-35B-A3B-FP8/snapshots/95a723d08a9490559dae23d0cff1d9466213d989"
BF16_BASE = EXP / "cache/qwen36-fp8hu-bf16"  # a K0f konverter kimenete
# BAAI/bge-m3 @ 5617a9f6 (a prod refs/main revíziója); a <user> HF-cache-ében csak az onnx-része van,
# ezért a teljes snapshot a kísérlet saját cache-ébe másolva (f0b_vezenylo.sh: bge_m3_cache)
BGE_M3 = EXP / "cache/bge-m3"

OPTION_LABELS = list("ABCDEFGHIJ")
NONE_LABEL = "X"
MAX_OPTIONS = len(OPTION_LABELS)

SYSTEM_PROMPT = "Döntési modell vagy. Egyetlen betűvel válaszolj: a választott opció betűjével."
NONE_TEXT = {"alap": "Egyik sem", "kontroll": "Nincs illő"}

# perplexitás-épség (K0f/K0d): ugyanazok a szövegek a HF- és a vLLM-motoron
PPL_SZOVEGEK = [
    "A számla kiállításának napja és a teljesítés időpontja eltérhet egymástól, ezért a könyvelés során mindkét dátumot rögzíteni kell.",
    "A szálloda konyhája hetente kétszer rendel friss zöldséget és gyümölcsöt a helyi nagykereskedőtől.",
    "Az energiaszolgáltató havi részszámlát bocsát ki, amelyet az éves elszámoló számla korrigál.",
]


def read_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --- Permutáció ------------------------------------------------------------

def permutation(item: dict, perm_id: int, move_none: bool = False) -> list[str | None]:
    """Az opciók megjelenítési sorrendje (opció-id-k; None = az X opció).

    perm_id 0 = az item tárolt sorrendje. A többi seedelt keverés az item
    id-jából, tehát motoroktól és futásoktól függetlenül reprodukálható. Az X
    alapból az utolsó; move_none=True esetén az X is keveredik (diagnosztikai
    részhalmaz).
    """
    ids = [o["id"] for o in item["options"]]
    order: list[str | None] = list(ids)
    if perm_id:
        rng = random.Random(f"{item['id']}|{perm_id}")
        rng.shuffle(order)
    if move_none:
        rng = random.Random(f"{item['id']}|{perm_id}|x")
        order.insert(rng.randrange(len(order) + 1), None)
    else:
        order.append(None)
    return order


def labels_for(order: list[str | None]) -> list[str]:
    """Az order-hez tartozó címkék: a valódi opciók A..J sorrendben, az X mindig X."""
    out, i = [], 0
    for oid in order:
        if oid is None:
            out.append(NONE_LABEL)
        else:
            out.append(OPTION_LABELS[i])
            i += 1
    return out


def gold_label(item: dict, order: list[str | None]) -> str:
    labels = labels_for(order)
    target = item.get("gold")
    for oid, lab in zip(order, labels):
        if oid == target:  # gold=None → az X opció (oid None)
            return lab
    raise ValueError(f"{item['id']}: a gold nincs az opciók közt")


# --- Prompt ---------------------------------------------------------------

def render_user(item: dict, order: list[str | None], none_text: str = NONE_TEXT["alap"]) -> str:
    ctx = item["context"]
    opts = {o["id"]: o for o in item["options"]}
    lines = [
        "Feladat: melyik cikktörzs-tételhez tartozik a számlasor?",
        f"Számlasor: \"{ctx['sor']}\"",
        f"Szállító: {ctx['szallito']} · Mennyiség: {ctx['mennyiseg']} {ctx['egyseg']} · Nettó egységár: {ctx['egysegar']} Ft",
        "Opciók:",
    ]
    for oid, lab in zip(order, labels_for(order)):
        if oid is None:
            lines.append(f"{lab}) {none_text}")
        else:
            o = opts[oid]
            lines.append(f"{lab}) {o['text']} [{o['path']}]")
    return "\n".join(lines)


_KERET01 = None


def _keret01():
    """A 01-es kör kerete (kor01/eszkozok/keret.py), fájlútról betöltve: a kor01/eszkozok a sys.path-ra téve a két kör
    azonos nevű moduljait (osszeallit) összekeverné."""
    global _KERET01
    if _KERET01 is None:
        import importlib.util

        spec = importlib.util.spec_from_file_location("ldh_keret01", Path(__file__).resolve().parent.parent / "kor01/eszkozok/keret.py")
        assert spec and spec.loader
        _KERET01 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_KERET01)
    return _KERET01


def messages_for(item: dict, order: list[str | None], none_text: str = NONE_TEXT["alap"]) -> list[dict]:
    if "request" in item:  # 01-es eszközválasztó item: a saját, nyelvkövető keretével (a none_text ott nyelvenként rögzített)
        return _keret01().messages_for(item, order)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": render_user(item, order, none_text)},
    ]


class PromptTokenizer:
    """Offline tokenizálás a HF-tokenizerrel, kikapcsolt thinkinggel.

    A prefill (pl. "(") az asszisztens-előtag után kerül a promptba; a döntési
    pozíció mindig a token-sor utáni első pozíció.
    """

    def __init__(self, path: Path | str = SUBJECT_SNAPSHOT):
        from transformers import AutoTokenizer

        self.tok = AutoTokenizer.from_pretrained(str(path))
        self.label_ids = {lab: self._single_id(lab) for lab in OPTION_LABELS + [NONE_LABEL]}

    def _single_id(self, text: str) -> int:
        ids = self.tok.encode(text, add_special_tokens=False)
        if len(ids) != 1:
            raise ValueError(f"a(z) {text!r} címke nem egytokenes: {ids}")
        return ids[0]

    def chat_text(self, messages: list[dict]) -> str:
        return self.tok.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
        )

    def encode(self, messages: list[dict], prefill: str = "") -> list[int]:
        text = self.chat_text(messages) + prefill
        return self.tok.encode(text, add_special_tokens=False)

    def encode_item(self, item: dict, order, prefill: str = "", none_text: str = NONE_TEXT["alap"]) -> list[int]:
        return self.encode(messages_for(item, order, none_text), prefill)


# --- Kiolvasott eloszlás ----------------------------------------------------

def restricted(label_logprobs: dict[str, float]) -> dict[str, float]:
    """Szűkített softmax a címkék (teljes szótárra normált) logprobjaiból."""
    import math

    m = max(label_logprobs.values())
    z = sum(math.exp(v - m) for v in label_logprobs.values())
    return {k: math.exp(v - m) / z for k, v in label_logprobs.items()}


def label_mass(label_logprobs: dict[str, float]) -> float:
    import math

    return sum(math.exp(v) for v in label_logprobs.values())
