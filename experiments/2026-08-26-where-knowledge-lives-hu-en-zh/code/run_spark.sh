#!/usr/bin/env bash
# Konténer-futtató a spark-devre — minden GPU-s lépés ezen megy keresztül.
#
#   ssh spark-dev 'bash ~/lang-study/src/run_spark.sh src/env_probe.py'
#
# ⛔ A GB10-en (aarch64, sm_121a) NINCS pip-ből telepíthető működő torch: a
# házon belüli megoldás a `lora-train:3` image (torch 2.11+cu130, transformers
# 5.6.0, flash-linear-attention a Qwen3.5 hibrid rétegeihez). A runbook §0
# `python -m venv && pip install torch` lépése ezen a gépen zsákutca.
#
# ⚠️ Két örökölt buktató (ld. clf-study/src/run_spark.sh):
#   * `-u $(id -u)` nélkül a konténer root-ként ír a mountolt könyvtárba;
#   * `-u`-val viszont nincs passwd-bejegyzés → `getpass.getuser()` KeyError
#     már importnál, ezért mountoljuk az /etc/passwd-t read-only.
set -euo pipefail
IMAGE="${IMAGE:-lora-train:3}"
HOME_DIR="$HOME/lang-study"

exec docker run --rm --gpus all \
  -u "$(id -u):$(id -g)" \
  -v /etc/passwd:/etc/passwd:ro -v /etc/group:/etc/group:ro \
  -v "$HOME_DIR":/work -e HOME=/work -e HF_HOME=/work/hf \
  -e HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-0}" \
  -e TRANSFORMERS_VERBOSITY=error -e TOKENIZERS_PARALLELISM=false \
  -e PYTHONUNBUFFERED=1 \
  -e SCOPE_MODEL="${SCOPE_MODEL:-}" -e SCOPE_RES="${SCOPE_RES:-}" \
  -e SCOPE_REPORTS="${SCOPE_REPORTS:-}" -e SCOPE_CHAT="${SCOPE_CHAT:-}" \
  -e SCOPE_FIGURES="${SCOPE_FIGURES:-}" -e SCOPE_PROMPTS="${SCOPE_PROMPTS:-}" \
  -w /work --entrypoint python3 "$IMAGE" "$@"
