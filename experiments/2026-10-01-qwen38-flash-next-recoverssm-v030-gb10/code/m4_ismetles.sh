#!/usr/bin/env bash
# M4 ismétlés: zöld = c84caa4 backport (3388ba1 javítással) x20; piros = a recoverssm_gdn.py 3388ba1 előtti állapota x12
cd ~/experiments/round8
SP=/usr/local/lib/python3.12/dist-packages
T=tests/kernels/mamba/test_recoverssm_gdn.py
run() { # $1 címke, $2 n, $3.. extra docker args
  local c=$1 n=$2; shift 2
  docker run --rm --gpus all --ipc=host --entrypoint bash -v $PWD/tests030:/work/tests -w /work "$@" qwen38-k2-test -c \
   "for i in \$(seq 1 $n); do r=\$(python3 -m pytest -q -p no:cacheprovider $T 2>&1 | tail -1); echo \"$c #\$i \$r\"; done"
}
echo "== zöld $(date -Is)"; run zold 20
echo "== piros $(date -Is)"; run piros 12 -v $PWD/pre3388/vllm/model_executor/layers/mamba/gdn/recoverssm_gdn.py:$SP/vllm/model_executor/layers/mamba/gdn/recoverssm_gdn.py:ro
echo "== KESZ $(date -Is)"
