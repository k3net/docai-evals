"""K0f — „FP8-hű BF16 checkpoint”: a Qwen3.6-35B-A3B-FP8 súlyai BF16-ra dekvantálva,
a HF `Qwen3_5MoeForCausalLM` natív (csak-szöveges) kulcsaira és alakjaira képezve.

Miért kell: a transformers 5.6 a `qwen3_5_moe_text` típushoz nem fésüli össze az
FP8 checkpoint expertenkénti kulcsait a 3D `gate_up_proj`/`down_proj`
paraméterekbe — betöltéskor az expertek csendben véletlen inicializálással
maradnának. Itt a várt kulcskészletet a modell meta-példányából vesszük, és
minden kulcsot explicit forrásból állítunk elő; ami nem állítható elő, az hiba.

Dekvantálás: W = fp8(W) · weight_scale_inv, 128×128-as blokkokban (DeepSeek-
/Qwen-FP8 formátum), float32-ben számolva, BF16-ra kerekítve.

Futtatás (lora-train:2, GPU nem kell):
  python3 eszkozok/konvertal_fp8_bf16.py --out cache/qwen36-fp8hu-bf16
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
from collections import defaultdict
from pathlib import Path

import torch
from safetensors import safe_open
from safetensors.torch import save_file

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import EXP, SUBJECT_SNAPSHOT, write_json  # noqa: E402

BLOCK = 128
SHARD_BYTES = 5 * 1024**3


class Source:
    def __init__(self, snap: Path):
        self.snap = snap
        self.wmap = json.load(open(snap / "model.safetensors.index.json"))["weight_map"]
        self._open: dict[str, object] = {}
        self.used: set[str] = set()

    def has(self, key: str) -> bool:
        return key in self.wmap

    def raw(self, key: str) -> torch.Tensor:
        fn = self.wmap[key]
        if fn not in self._open:
            self._open[fn] = safe_open(str(self.snap / fn), framework="pt")
        self.used.add(key)
        return self._open[fn].get_tensor(key)

    def weight(self, key: str) -> torch.Tensor:
        """A kulcs BF16-ban; FP8 esetén blokkonként dekvantálva."""
        w = self.raw(key)
        skey = key[: -len("weight")] + "weight_scale_inv" if key.endswith("weight") else None
        if skey and self.has(skey):
            s = self.raw(skey).float()
            out_f, in_f = w.shape
            s_full = s.repeat_interleave(BLOCK, 0)[:out_f].repeat_interleave(BLOCK, 1)[:, :in_f]
            return (w.float() * s_full).to(torch.bfloat16)
        if w.dtype in (torch.float8_e4m3fn, torch.float8_e5m2):
            raise ValueError(f"{key}: FP8 súly skála nélkül")
        return w


def expected_params(cfg) -> dict[str, tuple[tuple[int, ...], torch.dtype]]:
    from transformers import Qwen3_5MoeForCausalLM

    with torch.device("meta"):
        model = Qwen3_5MoeForCausalLM(cfg)
    return {k: (tuple(v.shape), v.dtype) for k, v in model.state_dict().items()}


def produce(key: str, src: Source, n_experts: int) -> torch.Tensor:
    if key == "lm_head.weight":
        return src.weight("lm_head.weight")
    if not key.startswith("model."):
        raise KeyError(key)
    skey = "model.language_model." + key[len("model."):]
    m = re.fullmatch(r"(model\.language_model\.layers\.\d+\.mlp\.experts)\.(gate_up_proj|down_proj)", skey)
    if m:
        base, kind = m.groups()
        mats = []
        for e in range(n_experts):
            if kind == "gate_up_proj":
                g = src.weight(f"{base}.{e}.gate_proj.weight")
                u = src.weight(f"{base}.{e}.up_proj.weight")
                mats.append(torch.cat([g, u], dim=0))  # HF: gate, up = linear(...).chunk(2)
            else:
                mats.append(src.weight(f"{base}.{e}.down_proj.weight"))
        return torch.stack(mats, 0)
    return src.weight(skey)


def build_config():
    from transformers import Qwen3_5MoeTextConfig

    full = json.load(open(SUBJECT_SNAPSHOT / "config.json"))
    tc = dict(full["text_config"])
    tc["architectures"] = ["Qwen3_5MoeForCausalLM"]
    tc["torch_dtype"] = "bfloat16"
    return Qwen3_5MoeTextConfig(**tc)


def source_keys_for(key: str, n_experts: int) -> list[str]:
    """A várt HF-kulcs előállításához szükséges forráskulcsok (skála nélkül)."""
    if key == "lm_head.weight":
        return ["lm_head.weight"]
    skey = "model.language_model." + key[len("model."):]
    m = re.fullmatch(r"(model\.language_model\.layers\.\d+\.mlp\.experts)\.(gate_up_proj|down_proj)", skey)
    if m:
        base, kind = m.groups()
        parts = ["gate_proj", "up_proj"] if kind == "gate_up_proj" else ["down_proj"]
        return [f"{base}.{e}.{p}.weight" for e in range(n_experts) for p in parts]
    return [skey]


def dry_run() -> None:
    cfg = build_config()
    exp = expected_params(cfg)
    wmap = json.load(open(SUBJECT_SNAPSHOT / "model.safetensors.index.json"))["weight_map"]
    missing, used = [], set()
    for k in exp:
        for s in source_keys_for(k, cfg.num_experts):
            if s in wmap:
                used.add(s)
                sc = s[: -len("weight")] + "weight_scale_inv"
                if sc in wmap:
                    used.add(sc)
            else:
                missing.append(f"{k} ← {s}")
    unused = sorted({re.sub(r"\d+", "N", k) for k in wmap if k not in used})
    print(json.dumps({
        "expected": len(exp), "missing_sources": missing[:30], "n_missing": len(missing),
        "unused_kinds": [u for u in unused if not u.startswith(("model.visual.", "mtp."))][:40],
        "sample_expected": sorted(exp)[:12],
    }, ensure_ascii=False, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(EXP / "cache/qwen36-fp8hu-bf16"))
    ap.add_argument("--dry", action="store_true", help="csak a kulcsleképezés ellenőrzése, tenzor-olvasás nélkül")
    args = ap.parse_args()
    if args.dry:
        dry_run()
        return
    out = Path(args.out)
    if (out / "OK").exists():
        print(f"{out}: kész (OK), kihagyva")
        return
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    cfg = build_config()
    exp = expected_params(cfg)
    src = Source(SUBJECT_SNAPSHOT)

    # rétegenként csoportosítva írunk, hogy a memória egy réteg körül maradjon
    groups: dict[str, list[str]] = defaultdict(list)
    for k in exp:
        m = re.match(r"model\.layers\.(\d+)\.", k)
        groups[f"L{int(m.group(1)):02d}" if m else "misc"].append(k)

    shard, shard_bytes, shard_idx, weight_map, problems = {}, 0, 0, {}, []
    dtype_counts: dict[str, int] = defaultdict(int)

    def flush():
        nonlocal shard, shard_bytes, shard_idx
        if not shard:
            return
        name = f"model-{shard_idx:05d}.safetensors"
        save_file(shard, str(out / name), metadata={"format": "pt"})
        for k in shard:
            weight_map[k] = name
        shard, shard_bytes, shard_idx = {}, 0, shard_idx + 1

    for g in sorted(groups):
        for k in sorted(groups[g]):
            shape, dtype = exp[k]
            try:
                t = produce(k, src, cfg.num_experts)
            except KeyError as e:
                problems.append(f"hiányzó forrás: {k} ({e})")
                continue
            if tuple(t.shape) != shape:
                problems.append(f"alak-eltérés: {k} kapott {tuple(t.shape)} várt {shape}")
                continue
            t = t.contiguous()
            dtype_counts[str(t.dtype)] += 1
            shard[k] = t
            shard_bytes += t.numel() * t.element_size()
            if shard_bytes >= SHARD_BYTES:
                flush()
        print(f"[{time.time() - t0:7.0f}s] {g} kész", flush=True)
    flush()

    unused = sorted(k for k in src.wmap if k not in src.used)
    unused_kinds = sorted({re.sub(r"\d+", "N", k) for k in unused})
    allowed = all(k.startswith(("model.visual.", "mtp.")) for k in unused)
    report = {
        "expected_keys": len(exp),
        "written_keys": len(weight_map),
        "problems": problems,
        "unused_source_keys": len(unused),
        "unused_source_kinds_sample": unused_kinds[:40],
        "unused_only_visual_mtp": allowed,
        "dtype_counts": dict(dtype_counts),
        "wall_s": round(time.time() - t0, 1),
    }
    write_json(out / "konverzio_riport.json", report)
    if problems or not allowed or len(weight_map) != len(exp):
        print(json.dumps(report, ensure_ascii=False, indent=2))
        raise SystemExit("K0f konverzió: HIBA (ld. konverzio_riport.json)")

    total = sum((out / f).stat().st_size for f in set(weight_map.values()))
    write_json(out / "model.safetensors.index.json", {"metadata": {"total_size": total}, "weight_map": weight_map})
    cfg.save_pretrained(out)
    for f in ["tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt", "chat_template.jinja", "generation_config.json"]:
        if (SUBJECT_SNAPSHOT / f).exists():
            shutil.copy(SUBJECT_SNAPSHOT / f, out / f)
    (out / "OK").write_text(json.dumps(report))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
