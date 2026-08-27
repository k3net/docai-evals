#!/usr/bin/env python3
"""Validate every experiments/*/eval-card.yaml against schemas/eval-card.schema.json.

Runs in CI and before opening a pull request. Requires PyYAML; uses jsonschema when available and
falls back to a built-in structural check (required keys, enums, level values) when it is not, so
that the repository stays inspectable without installing anything. Pass --strict (as CI does) to
refuse that fallback: a weaker check that reports "ok" is worse than no check at all.

Usage:
    pip install -r scripts/requirements.txt
    python3 scripts/validate_eval_cards.py --strict

Part of DocAI Evals — https://docai.hu
"""
import argparse
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
        sys.exit("PyYAML is required: pip install -r scripts/requirements.txt")
    with open(path) as fh:
        return yaml.safe_load(fh)


def json_scalar_errors(card):
    """Reject values YAML invents but JSON has no room for.

    An eval card is a machine-readable artefact: whatever consumes it will go through JSON. YAML
    resolves an unquoted 2026-08-26 to a datetime.date and an unquoted `no` to a boolean, and both
    survive every structural check until something tries to serialise them. This is exactly how the
    schema job went red: all thirteen dates were unquoted, so `type: string` failed on all thirteen
    cards at once, with a message ('datetime.date(...) is not of type string') that says nothing
    about the fix.
    """
    errors = []

    def walk(node, path):
        if isinstance(node, dict):
            for key, value in node.items():
                walk(value, f"{path}/{key}" if path else str(key))
        elif isinstance(node, list):
            for i, value in enumerate(node):
                walk(value, f"{path}/{i}")
        elif node is not None and not isinstance(node, (str, int, float, bool)):
            errors.append(f"{path or '<root>'}: {type(node).__name__} is not a JSON type — "
                          f"quote the value in YAML (got {node!r})")

    walk(card, "")
    return errors


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
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--strict", action="store_true",
                    help="fail instead of falling back to structural checks when jsonschema "
                         "is missing (use in CI)")
    args = ap.parse_args()

    with open(SCHEMA_PATH) as fh:
        schema = json.load(fh)

    try:
        # `date` is checked only with a format checker attached; `uri` needs rfc3987, which we do
        # not require — an unvalidated uri is a smaller risk than a dependency that drifts.
        from jsonschema import Draft202012Validator, FormatChecker
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
    except ImportError:
        if args.strict:
            sys.exit("jsonschema is required under --strict: "
                     "pip install -r scripts/requirements.txt")
        validator = None
        print("note: jsonschema not installed — running structural checks only.")
        print("      This is WEAKER than CI. Install it before trusting a green run.\n")

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
        errors = json_scalar_errors(card)
        if validator is not None:
            errors += [f"{'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}"
                       for e in validator.iter_errors(card)]
        else:
            errors += fallback_check(card, schema)
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
