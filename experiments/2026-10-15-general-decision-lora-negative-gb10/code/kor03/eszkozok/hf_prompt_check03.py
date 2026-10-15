"""03-as kör — a kiadott promptépítő (hf-release/adapter/decision_prompt.py) bájtra egyezik-e a tanítás és a kiolvasás
promptjával (kozos03.messages, generikus keret; common.permutation). A modellkártya „checked byte-for-byte” állításának
reprodukálása: minden val- és train-item, a 0–3. permutáció, plusz a kiadott (átnevezett mezős) adatkészlet val-sorai.

  python3 kor03/eszkozok/hf_prompt_check03.py   → a megnézett promptok száma és az eltérések száma (elvárt: 0)
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "kor03/eszkozok"))
sys.path.append(str(ROOT / "eszkozok"))
import common  # noqa: E402
import kozos03  # noqa: E402

RELEASE = ROOT / "kor03/hf-release/adapter/decision_prompt.py"
ITEMS = (ROOT / "kor03/adat/f1/pool_val.jsonl", ROOT / "kor03/adat/f3/mvp_train_v2.jsonl")
RELEASED = ROOT / "kor03/hf-release/dataset/data/permissive/validation.jsonl"


def load_release():
    spec = importlib.util.spec_from_file_location("decision_prompt", RELEASE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    dp = load_release()
    n = bad = 0
    for fn in ITEMS:
        for line in fn.open(encoding="utf-8"):
            it = json.loads(line)
            for p in (0, 1, 2, 3):
                o1, o2 = common.permutation(it, p), dp.permutation(it, p)
                n += 1
                bad += (o1 != o2 or common.labels_for(o1) != dp.labels_for(o2)
                        or kozos03.messages(it, o1, frame="generic") != dp.messages(it, o2))
    if RELEASED.exists():
        for line in RELEASED.open(encoding="utf-8"):
            it = json.loads(line)
            for p in (0, 3):
                n += 1
                bad += dp.messages(it, dp.permutation(it, p)) != kozos03.messages(it, common.permutation(it, p), frame="generic")
    print(json.dumps({"prompts": n, "mismatch": bad}))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
