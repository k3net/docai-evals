"""Szintetikus BA-adat — S5–S6 (runbook 4.2): aliasok + jelöltgenerálás a PROD logikájával.

- BM25: saját OpenSearch (ldh-opensearch, :9201) a prod mappingjével és lekérdezésével
  (<product-code> hu_item_text analyzer;
  multi_match best_fields, aliases^3 / name^2 / category, fuzziness AUTO, active-szűrő).
- Vektor: bge-m3 (CLS + L2-normálás) a prod index_text szövegén (név · ≤50 alias ·
  kategória), PONTOS kNN (nem HNSW).
- Aliasok csak TRAIN-párokból; a gyűjtőcikkek aliasai a train-beli „új termékek”
  (X(b)) szövegei — prodban is a be nem sorolt sorok kerülnek a gyűjtőre.
- A train-sorok a kitartott gyökerek NÉLKÜLI katalógusban keresnek, a többi a teljesben.
Kimenet: <out>/s6_jeloltek.jsonl — soronként a BM25 és a vektor top-8 (id, pont).

Futtatás (lora-train:2, GPU): python3 eszkozok/jeloltek.py --out adat/pilot
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import BGE_M3, EXP, read_jsonl, write_json, write_jsonl  # noqa: E402
from generator import HELDOUT_ROOTS  # noqa: E402

OS_URL = "http://127.0.0.1:9201"
TOPK = 8
MAX_ALIASES = 50  # EMBEDDING_MAX_ALIASES (prod config.py:490)

MAPPING = {  # = BA_ITEMS_INDEX_MAPPING (prod)
    "settings": {
        "index": {"number_of_shards": 1, "number_of_replicas": 0},
        "analysis": {
            "filter": {
                "hu_stop": {"type": "stop", "stopwords": "_hungarian_"},
                "ascii_folding": {"type": "asciifolding", "preserve_original": True},
            },
            "analyzer": {"hu_item_text": {"type": "custom", "tokenizer": "standard", "filter": ["lowercase", "hu_stop", "ascii_folding"]}},
        },
    },
    "mappings": {"properties": {
        "item_id": {"type": "keyword"}, "name": {"type": "text", "analyzer": "hu_item_text"},
        "aliases": {"type": "text", "analyzer": "hu_item_text"}, "category": {"type": "text", "analyzer": "hu_item_text"},
        "active": {"type": "boolean"},
    }},
}


def http(method: str, path: str, body=None, ndjson: bool = False):
    data = None
    headers = {"Content-Type": "application/x-ndjson" if ndjson else "application/json"}
    if body is not None:
        data = body.encode() if isinstance(body, str) else json.dumps(body).encode()
    req = urllib.request.Request(OS_URL + path, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read() or b"{}")


def wait_os(timeout_s: int = 300) -> None:
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        try:
            if http("GET", "/_cluster/health").get("status") in ("green", "yellow"):
                return
        except Exception:
            pass
        time.sleep(5)
    raise TimeoutError("OpenSearch nem állt fel")


def build_index(name: str, docs: list[dict]) -> None:
    try:
        http("DELETE", f"/{name}")
    except Exception:
        pass
    http("PUT", f"/{name}", MAPPING)
    for b in range(0, len(docs), 500):
        lines = []
        for d in docs[b:b + 500]:
            lines.append(json.dumps({"index": {"_index": name, "_id": d["item_id"]}}))
            lines.append(json.dumps({k: d[k] for k in ("item_id", "name", "aliases", "category", "active")}, ensure_ascii=False))
        r = http("POST", "/_bulk", "\n".join(lines) + "\n", ndjson=True)
        if r.get("errors"):
            raise RuntimeError("OpenSearch bulk-hiba")
    http("POST", f"/{name}/_refresh")


def bm25(index: str, text: str, size: int) -> list[tuple[str, float]]:
    body = {"query": {"bool": {
        "must": [{"multi_match": {"query": text, "fields": ["aliases^3", "name^2", "category"], "type": "best_fields", "fuzziness": "AUTO"}}],
        "filter": [{"term": {"active": True}}],
    }}, "size": size}
    hits = http("POST", f"/{index}/_search", body)["hits"]["hits"]
    return [(h["_source"]["item_id"], float(h["_score"])) for h in hits]


def index_text(d: dict) -> str:
    parts = [d["name"], *d["aliases"][:MAX_ALIASES]]
    if d["category"]:
        parts.append(d["category"])
    return " · ".join(p for p in parts if p.strip())


class Embedder:
    def __init__(self):
        from transformers import AutoModel, AutoTokenizer

        self.tok = AutoTokenizer.from_pretrained(BGE_M3)
        self.model = AutoModel.from_pretrained(BGE_M3, dtype=torch.float16).cuda().eval()

    @torch.inference_mode()
    def __call__(self, texts: list[str], max_len: int, bs: int = 64) -> torch.Tensor:
        out = []
        for b in range(0, len(texts), bs):
            enc = self.tok(texts[b:b + bs], padding=True, truncation=True, max_length=max_len, return_tensors="pt").to("cuda")
            h = self.model(**enc).last_hidden_state[:, 0]
            out.append(torch.nn.functional.normalize(h.float(), dim=-1))
        return torch.cat(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    out = Path(args.out)
    if not out.is_absolute():
        out = EXP / out
    if (out / "s6_jeloltek.jsonl").exists():
        print("S6 kész, kihagyva")
        return
    arts = read_jsonl(out / "s1_katalogus.jsonl")
    pairs = read_jsonl(out / "parok.jsonl")
    rows = read_jsonl(out / "s4_sorok.jsonl")
    names = json.load(open(out / "s3_megnevezes.json"))
    xb = {p["article"] for p in pairs if p["xb"]}
    A = {a["id"]: a for a in arts}

    # A train-párok két foldra oszlanak; egy train-sor a MÁSIK fold aliasaiból épült indexben
    # keres. Így a saját párja sosem alias — ugyanaz a helyzet, mint a val/teszt-soroknál.
    def fold(p: dict) -> int:
        return int(random.Random(f"{p['supplier']}|{p['article']}|fold").random() < 0.5)

    catch = defaultdict(list)
    for a in arts:
        if a["catchall"]:
            catch[(a["root"], a["sub"])].append(a["id"])

    def build_aliases(use_fold: int | None) -> dict[str, list[str]]:
        al = defaultdict(list)
        for p in pairs:
            if p["split"] == "train" and not p["xb"] and (use_fold is None or fold(p) == use_fold):
                n = names.get(f"{p['supplier']}|{p['article']}")
                if n and n not in al[p["article"]]:
                    al[p["article"]].append(n)
        # a gyűjtőkre a train-beli „új termékek” (X(b)) sorai kerülnek, mint prodban a be nem soroltak
        for r in rows:
            if r["split"] == "train" and r["xb"] and (use_fold is None or fold(r) == use_fold):
                a = A[r["article"]]
                for cid in catch.get((a["root"], a["sub"])) or catch.get((a["root"], "Egyéb")) or []:
                    if len(al[cid]) < 200:
                        al[cid].append(r["text"])
        for cid in [a["id"] for a in arts if a["catchall"]]:
            random.Random(f"{cid}|{use_fold}").shuffle(al[cid])
        return al

    def docs_for(al: dict, heldout_ok: bool) -> list[dict]:
        return [{"item_id": a["id"], "name": a["name"], "aliases": al[a["id"]], "category": a["sub"], "active": True,
                 "root": a["root"]} for a in arts if a["id"] not in xb and (heldout_ok or a["root"] not in HELDOUT_ROOTS)]

    alias_sets = {"full": build_aliases(None), "tr0": build_aliases(1), "tr1": build_aliases(0)}
    doc_sets = {"full": docs_for(alias_sets["full"], True), "tr0": docs_for(alias_sets["tr0"], False),
                "tr1": docs_for(alias_sets["tr1"], False)}

    wait_os()
    for k, d in doc_sets.items():
        build_index(f"ldh_{k}", d)

    emb = Embedder()
    dvecs = {k: (emb([index_text(x) for x in d], max_len=2048), [x["item_id"] for x in d]) for k, d in doc_sets.items()}
    qvec = emb([r["text"] for r in rows], max_len=256)

    res = []
    for i, r in enumerate(rows):
        k = f"tr{fold(r)}" if r["split"] == "train" else "full"
        dv, did = dvecs[k]
        top = torch.topk(qvec[i] @ dv.T, TOPK)
        vec = [(did[j], round(float(s), 6)) for s, j in zip(top.values.tolist(), top.indices.tolist())]
        res.append({"row": r["row"], "bm25": bm25(f"ldh_{k}", r["text"], TOPK), "vector": vec, "index": k})
    write_jsonl(out / "s6_jeloltek.jsonl", res)
    write_json(out / "s5_aliasok.json", alias_sets["full"])
    print(f"S5–S6: {len(doc_sets['full'])} cikk a teljes indexben ({len(doc_sets['tr0'])} a train-indexekben), {len(res)} sor visszakeresve")


if __name__ == "__main__":
    main()
