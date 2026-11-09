"""fej05 egységtesztek szintetikus jellemzőkön (CPU, a tréning-image-ben):  python3 -m pytest kor05/eszkozok/test_fej05.py

Kis rejtett dimenzióval (12) egy beültetett jelet kell megtanulnia: a helyes opció c_vég vektora a q-hoz igazodik, a
NO_MATCH itemeken egyik sem. A maszkolt (nem létező) opciók valószínűsége 0, a gold-halmaz NLL-je véges."""

from __future__ import annotations

import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fej05  # noqa: E402


def synth(n: int, seed: int, arm: str = "H") -> list[dict]:
    g = torch.Generator().manual_seed(seed)
    out = []
    for i in range(n):
        k = int(torch.randint(2, 6, (1,), generator=g))
        q = torch.randn(12, generator=g)
        ce = torch.randn(k, 12, generator=g)
        no_match = i % 4 == 0
        gold_j = int(torch.randint(0, k, (1,), generator=g))
        if not no_match:
            ce[gold_j] = q + 0.3 * torch.randn(12, generator=g)
        cand_ids = [f"o{j}" for j in range(k)]
        out_ids = cand_ids + list(fej05.STATES)
        gold = torch.tensor([(o == "NO_MATCH") if no_match else (o == f"o{gold_j}") for o in out_ids])
        ex = {"id": f"s{i}", "perm": 0, "k": k, "cand_ids": cand_ids, "out_ids": out_ids,
              "state": "NO_MATCH" if no_match else "MATCH", "ketertelmu": False,
              "cf": torch.randn(k, 4, generator=g), "gf": torch.randn(7, generator=g), "gold": gold}
        if arm in ("H", "A"):
            ex |= {"q": q, "c_end": ce, "c_mean": ce, "x_end": torch.randn(12, generator=g),
                   "x_mean": torch.randn(12, generator=g)}
        out.append(ex)
    return out


def test_mask_and_finite_nll():
    exs = synth(8, 1)
    st = fej05.Stats(exs, "H")
    b = fej05.collate(exs, "H", st, "cpu")
    m = fej05.ContentHead("H", 4, 7, 12)
    logits = m(b)
    p = torch.softmax(logits, -1)
    assert torch.all(p[:, :fej05.KMAX][~b["mask"]] == 0)
    assert torch.isfinite(fej05.set_nll(logits, b["gold"])).all()


def test_learns_planted_signal():
    fit, dev = synth(600, 2), synth(200, 3)
    st = fej05.Stats(fit, "H")
    torch.manual_seed(0)
    untrained = fej05.evaluate(fej05.ContentHead("H", 4, 7, 12), dev, "H", st, "cpu")["makro_nll"]
    _, info = fej05.train_one("H", fit, dev, st, 3e-3, 17, "cpu")
    assert info["legjobb_dev_makro_nll"] < 0.25 * untrained, (untrained, info["legjobb_dev_makro_nll"])


def test_c_arm_runs_without_hidden():
    fit, dev = synth(200, 4, "C"), synth(50, 5, "C")
    st = fej05.Stats(fit, "C")
    model, info = fej05.train_one("C", fit, dev, st, 3e-4, 17, "cpu")  # noqa: F841
    assert model.proj is None and info["legjobb_dev_makro_nll"] > 0
