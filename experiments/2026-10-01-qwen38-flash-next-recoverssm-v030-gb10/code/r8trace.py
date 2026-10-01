"""Round8 scheduler-trace overlay — CSAK naplóz, a scheduler viselkedését nem módosítja.

A konténer site-packages-ébe csatolt `r8trace.pth` importálja minden Python-folyamatban. Ha az
`R8_TRACE` env egy könyvtár, egy import-hook a `vllm.v1.core.sched.scheduler` modul betöltése
után becsomagolja:
  * `Scheduler.__init__`  -> egy `init` sor: blokkgeometria, retention, eagle-bitek, KV-csoportok;
  * `Scheduler._mamba_block_aligned_split` -> kérésenként és lépésenként egy `split` sor
    (start, kért és visszaadott tokenszám, prompt-hossz, shared_prefix_boundary);
  * `Scheduler._get_local_prefix_cache_hit` (ha létezik) -> `hit` sor: lokális találat hossza.
Kimenet: $R8_TRACE/sched-<pid>.jsonl. Bármilyen hiba a trace-ben elnyelődik (a mérést nem állítja meg).
"""
import importlib.abc
import importlib.machinery
import json
import os
import sys
import time

_DIR = os.environ.get("R8_TRACE")
_TARGET = "vllm.v1.core.sched.scheduler"


def _out():
    return open(os.path.join(_DIR, f"sched-{os.getpid()}.jsonl"), "a", buffering=1)


def _w(rec):
    try:
        rec["t"] = round(time.time(), 4)
        with _out() as f:
            f.write(json.dumps(rec, default=str) + "\n")
    except Exception:
        pass


def _g(o, *names, default=None):
    for n in names:
        o = getattr(o, n, None)
        if o is None:
            return default
    return o


def _patch(mod):
    S = getattr(mod, "Scheduler", None)
    if S is None or getattr(S, "_r8_patched", False):
        return
    S._r8_patched = True
    orig_init = S.__init__

    def __init__(self, *a, **k):
        orig_init(self, *a, **k)
        try:
            cc = self.cache_config
            groups = []
            kvc = _g(self, "kv_cache_config") or k.get("kv_cache_config")
            for gi, grp in enumerate(_g(kvc, "kv_cache_groups", default=[]) or []):
                spec = grp.kv_cache_spec
                groups.append({
                    "i": gi, "type": type(spec).__name__, "block_size": getattr(spec, "block_size", None),
                    "n_layers": len(getattr(grp, "layer_names", []) or []),
                    "num_prefill_checkpoint_blocks": getattr(spec, "num_prefill_checkpoint_blocks", None),
                    "prefill_checkpoint_alignment": getattr(spec, "prefill_checkpoint_alignment", None),
                    "num_speculative_blocks": getattr(spec, "num_speculative_blocks", None),
                })
            _w({"ev": "init", "pid": os.getpid(),
                "block_size": getattr(self, "block_size", None),
                "cache_config.block_size": getattr(cc, "block_size", None),
                "hash_block_size": getattr(self, "hash_block_size", None),
                "mamba_block_size": getattr(cc, "mamba_block_size", None),
                "mamba_cache_mode": getattr(cc, "mamba_cache_mode", None),
                "prefix_cache_retention_interval": getattr(cc, "prefix_cache_retention_interval", "<n/a>"),
                "enable_prefix_caching": getattr(cc, "enable_prefix_caching", None),
                "use_recoverssm": getattr(cc, "use_recoverssm", "<n/a>"),
                "use_eagle": getattr(self, "use_eagle", None),
                "use_eagle_block_drop": getattr(self, "use_eagle_block_drop", "<n/a>"),
                "need_mamba_block_aligned_split": getattr(self, "need_mamba_block_aligned_split", None),
                "mamba_prefill_checkpoint_alignment": getattr(self, "mamba_prefill_checkpoint_alignment", "<n/a>"),
                "mamba_has_prefill_checkpoint_blocks": getattr(self, "mamba_has_prefill_checkpoint_blocks", "<n/a>"),
                "mamba_partial_cache_hit": getattr(self, "mamba_partial_cache_hit", "<n/a>"),
                "mamba_fine_grained_prefix_cache": getattr(self, "mamba_fine_grained_prefix_cache", "<n/a>"),
                "max_num_scheduled_tokens": getattr(self, "max_num_scheduled_tokens", None),
                "kv_groups": groups})
        except Exception as e:  # noqa: BLE001
            _w({"ev": "init_err", "err": repr(e)})

    S.__init__ = __init__

    if hasattr(S, "_mamba_block_aligned_split"):
        orig_split = S._mamba_block_aligned_split

        def _mamba_block_aligned_split(self, request, num_new_tokens, *a, **k):
            r = orig_split(self, request, num_new_tokens, *a, **k)
            try:
                extra = list(a) + list(k.values())
                _w({"ev": "split", "req": request.request_id,
                    "num_prompt_tokens": request.num_prompt_tokens, "num_tokens": request.num_tokens,
                    "num_computed_tokens": request.num_computed_tokens,
                    "extra_local_ext": extra, "num_new_tokens_in": num_new_tokens, "out": r,
                    "shared_prefix_boundary": getattr(request, "shared_prefix_boundary", None)})
            except Exception:
                pass
            return r

        S._mamba_block_aligned_split = _mamba_block_aligned_split

    if hasattr(S, "_get_local_prefix_cache_hit"):
        orig_hit = S._get_local_prefix_cache_hit

        def _get_local_prefix_cache_hit(self, request, *a, **k):
            r = orig_hit(self, request, *a, **k)
            try:
                _w({"ev": "hit", "req": request.request_id, "num_prompt_tokens": request.num_prompt_tokens,
                    "num_local": r[1] if isinstance(r, tuple) and len(r) > 1 else None,
                    "rest": [x for x in (r[2:] if isinstance(r, tuple) else []) if isinstance(x, (int, bool))]})
            except Exception:
                pass
            return r

        S._get_local_prefix_cache_hit = _get_local_prefix_cache_hit
    _w({"ev": "patched", "pid": os.getpid(), "has_split": hasattr(S, "_mamba_block_aligned_split"),
        "has_hit": hasattr(S, "_get_local_prefix_cache_hit")})


class _Finder(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path, target=None):
        if name != _TARGET:
            return None
        spec = importlib.machinery.PathFinder.find_spec(name, path)
        if spec is None or spec.loader is None:
            return spec
        orig_exec = spec.loader.exec_module

        def exec_module(module):
            orig_exec(module)
            try:
                _patch(module)
            except Exception as e:  # noqa: BLE001
                _w({"ev": "patch_err", "err": repr(e)})

        spec.loader.exec_module = exec_module
        return spec


if _DIR and os.path.isdir(_DIR) and not any(isinstance(f, _Finder) for f in sys.meta_path):
    sys.meta_path.insert(0, _Finder())
