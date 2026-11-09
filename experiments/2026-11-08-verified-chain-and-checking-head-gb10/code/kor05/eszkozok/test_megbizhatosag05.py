"""megbizhatosag05 egységtesztek szintetikus jellemzőkön (CPU, a tréning-image-ben; a pytest nincs benne, a
függvények közvetlenül is hívhatók): a javaslat-leképezés, és hogy a fej a beültetett helyességi jelet megtanulja."""

from __future__ import annotations

import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fej05  # noqa: E402
import megbizhatosag05 as m  # noqa: E402
from test_fej05 import synth  # noqa: E402


def _p(k: int, opt: list[float], st: list[float]) -> torch.Tensor:
    p = torch.zeros(fej05.KMAX + len(fej05.STATES))
    p[:k] = torch.tensor(opt)
    p[fej05.KMAX:] = torch.tensor(st)
    return p


def test_proposal_mapping():
    e = synth(1, 1)[0]
    e |= {"k": 3, "cand_ids": ["o0", "o1", "o2"], "state": "MATCH",
          "gold": torch.tensor([False, True, False, False, False, False])}
    pr = m.proposal(e, _p(3, [0.1, 0.6, 0.1], [0.1, 0.05, 0.05]))
    assert (pr["kind"], pr["cand"], pr["helyes"]) == ("SELECT", "o1", True)
    pr = m.proposal(e, _p(3, [0.1, 0.1, 0.1], [0.6, 0.05, 0.05]))
    assert (pr["kind"], pr["helyes"], pr["helyes_enyhe"]) == ("NONE", False, False)
    e["state"] = "OUT_OF_SCOPE"
    pr = m.proposal(e, _p(3, [0.1, 0.1, 0.1], [0.6, 0.05, 0.05]))
    assert (pr["kind"], pr["helyes"], pr["helyes_enyhe"]) == ("NONE", False, True)
    pr = m.proposal(e, _p(3, [0.1, 0.1, 0.1], [0.05, 0.05, 0.6]))
    assert (pr["kind"], pr["defer_reason"], pr["helyes"]) == ("DEFER", "OUT_OF_SCOPE", None)
    assert len(pr["small"]) == m.d_small("H")
    pr = m.proposal(e, torch.cat([_p(3, [0.1, 0.1, 0.1], [0, 0, 0])[:fej05.KMAX], torch.tensor([0.7])]), ("X",))
    assert (pr["kind"], pr["helyes"], pr["helyes_enyhe"], len(pr["small"])) == ("NONE", False, True, m.d_small("HX"))


def test_learns_planted_correctness():
    g = torch.Generator().manual_seed(0)
    rs = []
    for i in range(1500):
        y = float(i % 3 != 0)
        small = torch.randn(m.d_small("H"), generator=g)
        small[1] = 0.8 * y + 0.2 * torch.rand(1, generator=g).item()  # a javaslat valószínűsége hordozza a jelet
        rs.append({"small": small, "cf": torch.randn(4, generator=g), "gf": torch.randn(7, generator=g),
                   "q": torch.randn(12, generator=g), "c": torch.randn(12, generator=g),
                   "cm": torch.randn(12, generator=g), "y": y})
    fit, val = rs[:1200], rs[1200:]
    sm = torch.stack([r["small"] for r in fit])
    ms = (sm.mean(0), sm.std(0))
    dims = m.dims_for("H", fit[0])
    _, info = m.train_rel("H", fit, val, ms, dims, 3e-3, 17, "cpu")
    best = min(info["tortenet"], key=lambda h: h["val_bce"])
    assert best["val_auroc"] > 0.95, best


if __name__ == "__main__":
    test_proposal_mapping()
    test_learns_planted_correctness()
    print("megbizhatosag05: OK")
