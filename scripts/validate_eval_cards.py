#!/usr/bin/env python3
"""Validate every experiments/*/eval-card.yaml against schemas/eval-card.schema.json.

Runs in CI and before opening a pull request. Requires PyYAML; uses jsonschema when available and
falls back to a built-in structural check (required keys, enums, level values) when it is not, so
that the repository stays inspectable without installing anything.

Usage:
    python3 scripts/validate_eval_cards.py

Part of DocAI Evals — https://docai.hu
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_PATH = os.path.join(ROOT, "schemas", "eval-card.schema.json")
EXPERIMENTS = os.path.join(ROOT, "experiments")


def load_yaml(path):
    try:
        import yaml
    except ImportError:
        sys.exit("PyYAML is required: pip install pyyaml")
    with open(path) as fh:
        return yaml.safe_load(fh)


def fallback_check(card, schema):
    """Minimal structural validation when jsonschema is not installed."""
    errors = []
    for key in schema.get("required", []):
        if key not in card:
            errors.append(f"missing required key: {key}")
    level = (card.get("reproducibility") or {}).get("level")
    if level not in ("R1", "R2", "R3"):
        errors.append(f"reproducibility.level must be R1/R2/R3, got {level!r}")
    access = (card.get("dataset") or {}).get("access")
    if access not in ("public", "synthetic-only", "private"):
        errors.append(f"dataset.access must be public/synthetic-only/private, got {access!r}")
    task_type = (card.get("task") or {}).get("type")
    allowed = schema["properties"]["task"]["properties"]["type"]["enum"]
    if task_type not in allowed:
        errors.append(f"task.type must be one of {allowed}, got {task_type!r}")
    if not card.get("limitations"):
        errors.append("limitations must list at least one entry — every measurement has limits")
    if not card.get("systems"):
        errors.append("systems must list every arm of the comparison, including the baseline")
    return errors


def main():
    with open(SCHEMA_PATH) as fh:
        schema = json.load(fh)

    try:
        from jsonschema import Draft202012Validator
        validator = Draft202012Validator(schema)
    except ImportError:
        validator = None
        print("note: jsonschema not installed — running structural checks only\n")

    cards = []
    for entry in sorted(os.listdir(EXPERIMENTS)):
        path = os.path.join(EXPERIMENTS, entry, "eval-card.yaml")
        if os.path.isfile(path):
            cards.append(path)
    if not cards:
        sys.exit("no eval cards found")

    failed = 0
    for path in cards:
        rel = os.path.relpath(path, ROOT)
        card = load_yaml(path)
        if validator is not None:
            errors = [f"{'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}"
                      for e in validator.iter_errors(card)]
        else:
            errors = fallback_check(card, schema)
        if errors:
            failed += 1
            print(f"FAIL  {rel}")
            for err in errors:
                print(f"        {err}")
        else:
            print(f"ok    {rel}")

    print()
    print(f"{len(cards) - failed}/{len(cards)} eval cards valid")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
