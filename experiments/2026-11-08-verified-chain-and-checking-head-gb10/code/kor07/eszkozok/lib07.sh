#!/usr/bin/env bash
# 07-es kör — a queue-scriptek közös része (a lib.sh a 06 v1 manifestjében van, nem módosul; ez kiegészíti).
# A HF-betöltés csúcsa a gép teljes memóriáját kéri: a 65 GB-os BF16 mellett ~50 GB névtelen CPU-másolat (a
# MoE-szakértők összefűzése). A 06 öt kiolvasása azért élte túl, mert a spark-deven 16 GB swap van (/swap.img), és a
# betöltés végén a másolat egy része oda lapozódik ki (2026-10-31: két leállított próba 3, illetve 0 GB elérhetőnél;
# a konténer `--memory-swap` korlátja a swapot is megtiltotta volna, ezért nincs korlát). OOM-kill a gépen nem volt.
#   py07              a `py --gpu` (a lib.sh-é, változatlan beállításokkal, de ldh-py07 néven, hogy az őr felismerje)
#   memoria_or07 <log>   őr: csak valódi kimerülésnél (elérhető < 1 GB ÉS szabad swap < 2 GB) állítja le a konténert

py07() {
  docker run --rm --gpus all --ipc host --network host --name "ldh-py07-$$-$RANDOM" \
    -v "$EXP:/exp" -v "$HOME/.cache/huggingface:/hf:ro" -v /etc/localtime:/etc/localtime:ro \
    -e HF_HOME=/hf -e HF_HUB_OFFLINE=1 -e LDH_EXP=/exp -e LDH_HF=/hf -e PYTHONUNBUFFERED=1 \
    -w /exp "$TOOL_IMAGE" python3 "$@"
}

memoria_or07() {  # memoria_or07 <naplófájl>; a háttérben fut, amíg van ldh-py07 konténer
  local log="$1"
  ( sleep 30
    while docker ps --format '{{.Names}}' | grep -q ldh-py07; do
      a=$(free -g | awk 'NR==2{print $7}'); s=$(free -g | awk 'NR==3{print $4}')
      echo "$(date '+%T') elérhető ${a} GB, szabad swap ${s} GB" >> "$log"
      if [ "$a" -lt 1 ] && [ "$s" -lt 2 ]; then
        echo "LEÁLLÍTÁS: memória és swap kimerült $(date '+%T')" >> "$log"
        docker rm -f $(docker ps -q --filter name=ldh-py07)
      fi
      sleep 5
    done ) &
}
