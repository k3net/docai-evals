"""08 G5 utólag (11-05; nem rögzített) — a K1 a teljes rendszeren (G1-rögzítés 6., 7.: a diagnózis mellett kötelező leíró
sor; a rögzített `k08g5.sh` nem írja ki). A rögzített `g5_k1_08` változatlanul fut, csak a `diagnozis` szűrője helyett
minden pontozott tétel bent marad (a modellhez jutott tételek, a kinyerési hibásak is). A paraméterek a `g5_k1_08`-éi; a
„fő” jelölés itt csak örökölt felirat, a fő próba a diagnózison van.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path[:0] = [str(Path(__file__).resolve().parent)]
import g5_k1_08 as K  # noqa: E402


def mind(_fam, ids, _items, _lanc_dir, _orakulum_dir):
    return np.ones(len(ids), bool), Counter()


K.diagnozis = mind

if __name__ == "__main__":
    K.main()
