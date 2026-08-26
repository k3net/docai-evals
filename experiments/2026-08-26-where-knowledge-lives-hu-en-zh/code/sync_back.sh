#!/usr/bin/env bash
# Eredmények vissza a laptopra. A hidden state-ek (results/hidden) NEM jönnek:
# több GB, és a promptokból bármikor újragenerálhatók.
set -euo pipefail
REMOTE="${1:-spark-dev}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Több mérési kör él egymás mellett (base → instruct → …), mindegyik saját
# results*/reports* könyvtárban — ld. code/scope_paths.py. Mindet visszahozzuk.
for d in $(ssh "$REMOTE" 'cd ~/lang-study && ls -d results* reports* 2>/dev/null'); do
  mkdir -p "$HERE/$d"
  # ⛔ A nagy köztes fájlok NEM jönnek át: a `hidden/` több GB, a `lens_cache.npy` a
  # 300k tokenes tuned-lens cache (~80 GB!), a `tuned_lens.pt` 269 MB — mind regenerálható,
  # és a WireGuard-linken egy figyelmetlen pull órákra elveszi a sávot.
  # ⚠️ A `sae/` viszont JÖN (33–42 MB/kör): kicsi, és az `analyze_d.py` D3/D3b szakasza
  # közvetlenül olvassa. Egy ideig ki volt zárva, és emiatt az instruct kör D-elemzése
  # `FileNotFoundError`-ral állt le — a kizárás a modellsúlyokra vonatkozott, nem erre.
  # ⛔⛔ `--update` KÖTELEZŐ: a `clean_answers.py` / `flag_degenerate.py` / `set_manual.py`
  # ugyanabba a könyvtárba ír, és néha a LAPTOPON fut. 2026-08-25-én egy sima `rsync -az`
  # a spark 08-24-i `results/gen.jsonl`-jével felülírta a frissebb helyit, és NÉMÁN eltűnt
  # belőle a `text_clean` — vagyis a riportok a NYERS szöveget kezdték mutatni, miközben a
  # bíráló a tisztítottat látta. A `--update` sosem ír felül frissebb helyi fájlt.
  rsync -azu --exclude 'hidden/' --exclude 'lens_cache.npy' --exclude 'tuned_lens.pt' \
        "$REMOTE:~/lang-study/$d/" "$HERE/$d/"
  echo "  ← $d"
done
echo "visszahozva ← $REMOTE:~/lang-study/"
