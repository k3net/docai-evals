#!/usr/bin/env bash
# F2 — a maradék hat kar: S07, S03, S01, A050, S05F, A200F.
#
# ⛔ CSAK a Kapu F1 kiértékelése UTÁN indítandó. A runbook §6 szerint az F1 pilot a
# protokoll validálása, és ott el lehet elegánsan állni; ez a szkript nem dönt helyetted.
#
# A sorrend nem véletlen. Ha a GPU-idő elfogy, a korábban lefutott karokból akkor is
# összeáll egy közölhető dózis-hatás görbe:
#   S07, S03  → a dózis-sor két szélső pontja a már mért S05 körül (H1)
#   S01       → a dózis-sor alsó vége. ⚠️ 2026-09-19: az F1 megmutatta, hogy a magyar
#               csapda greedy alatt KONSTRUKCIÓBÓL vak a foltra (K0 ≡ S05 ≡ A200 bájtra),
#               tehát az S01 „pozitív kontroll" szerepe a magyar tengelyen okafogyott;
#               a költség tengelye a KÍNAI próba, és ott S05 már totális (2,8 %).
#   A050      → az irány-forma fél dózisa (H2): él-e itt még a kínai?
#   S05F, A200F → a finomított maszk mindkét formában (H3, H4): a meghagyott gyakori
#               Han-karakterek megtartják-e a kínait, és mi lesz a magyar kockázattal?
#
# ⛔ 2026-09-19, döntés: SIMA motoron, sorosan, ismétlés nélkül. A példányzaj (±2–5
# item/150) benne marad; a csapdán minden K0-tól való eltérés példányzaj, nem folthatás.
set -u
EX=$HOME/experiments/2026-09-18-cjk-csillapitas
say() { echo "[$(date +%H:%M:%S)] $*"; echo "$*" > "$EX/STATUS-F2"; }

if ! grep -q "^F1 KÉSZ" "$EX/STATUS-F1" 2>/dev/null; then
  say "HIBA: az F1 nem zárult le (STATUS-F1) — a Kapu F1 kiértékelése nélkül nem indulok."
  exit 1
fi

# ⛔ 2026-09-18: soros mérés, ismétlés nélkül (`1 1 3`). A párhuzamosság-kapu megbukott,
# a soros dekódolás viszont bitre reprodukálható — az ismétlés így nem hordoz
# információt a két greedy műszeren. A Han-szonda mintavételezett, ott marad a 3×.
say "F2 indul"
for KAR in S07 S03 S01 A050 S05F A200F; do
  "$EX/eszkozok/kar_futtat.sh" "$KAR" "/work/karok/$KAR" 1 1 3 \
    || { say "HIBA: $KAR"; exit 1; }
done
say "F2 KÉSZ — mind a kilenc kar lemérve"
