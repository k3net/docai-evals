"""allapot05 egységtesztek: a szabály esetei és a 04-runbook 3.3 darabszámai.  python3 -m pytest kor05/eszkozok"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from allapot05 import content_state, ellenoriz, gold_set, soft_target  # noqa: E402


def item(**kw):
    return {"id": "t1", "family": "qa.milqa", "options": [{"id": "o1"}, {"id": "o2"}], "gold": None, **kw}


def test_match():
    assert content_state(item(gold="o1")) == "MATCH"
    assert gold_set(item(gold="o1")) == ["o1"]


@pytest.mark.parametrize("xt,st", [("gold-drop", "NO_MATCH"), ("out-of-scope", "OUT_OF_SCOPE"),
                                   ("missing-precondition", "MISSING_DATA")])
def test_x_types(xt, st):
    assert content_state(item(x_type=xt)) == st
    assert gold_set(item(x_type=xt)) == [st]


@pytest.mark.parametrize("fam,st", [("rag.relevancia", "NO_MATCH"), ("kie.osszeg", "NO_MATCH"),
                                    ("en.proc.state_perturbation", "NO_MATCH"), ("qa.milqa", "MISSING_DATA"),
                                    ("nli.hucb", "MISSING_DATA")])
def test_natural(fam, st):
    assert content_state(item(x_type="natural", family=fam)) == st


def test_unknown_natural_fails():
    with pytest.raises(ValueError):
        content_state(item(x_type="natural", family="uj.csalad"))


def test_x_without_type_fails():
    with pytest.raises(ValueError):
        content_state(item())


def test_ambiguous_dict_soft():
    it = item(gold="o1", ketertelmu=True, soft={"o1": 0.6, "o2": 0.4, "o3": 0.0})
    assert content_state(it) == "MATCH"
    assert gold_set(it) == ["o1", "o2"]
    assert soft_target(it) == pytest.approx({"o1": 0.6, "o2": 0.4})


def test_ambiguous_list_soft_with_none():
    it = item(gold=None, ketertelmu=True, soft=[None, "o1", "o2"])
    assert content_state(it) == "MATCH"
    assert gold_set(it) == ["o1", "o2", "NO_MATCH"]
    assert soft_target(it) == pytest.approx({"o1": 1 / 3, "o2": 1 / 3, "NO_MATCH": 1 / 3})


def test_counts_match_runbook04():
    res = ellenoriz()
    assert res["ok"], {k: v.get("elteres") for k, v in res.items() if isinstance(v, dict) and v.get("elteres")}
