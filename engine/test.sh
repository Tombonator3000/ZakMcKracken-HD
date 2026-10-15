#!/usr/bin/env bash
# Kjører spillet uten skjerm og sjekker at HD-grafikken havner på riktig sted.
#
# Lager en mod med "nearest" (hver piksel blir en blokk). Da skal HD-bildet være likt
# originalen skalert opp, og motoren skriver selv hvor mange piksler som avviker.
# Bilder av skjermen lagres i work/test-dumps.
#
# Bruk: engine/test.sh [antall bilder, standard 3000]
#
# Zak: motoren må være bygget med FM-Towns-lagene av (engine/build.sh gjør det), ellers er HD av.
# Testen stopper med kode 1 hvis en kontroll finner avvik.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
SRC="${SCUMMVM_SRC:-$HERE/scummvm}"
FRAMES="${1:-3000}"
OUT="$ROOT/work/test-dumps"

[ -x "$SRC/scummvm" ] || { echo "Fant ikke $SRC/scummvm. Kjør engine/build.sh først."; exit 2; }
[ -f "$ROOT/game/00.LFL" ] || { echo "Spillfilene mangler. Kjør tools/hent_spilldata.sh først."; exit 2; }
[ -f "$ROOT/work/extract/rooms.json" ] || { echo "Uttrekket mangler. Kjør zakhd extract først."; exit 2; }
[ -d "$ROOT/mods/test-nearest" ] || zakhd build-mod --name test-nearest --method nearest --kostymer 1-40

rm -rf "$OUT"
mkdir -p "$OUT" "$ROOT/work/test-home"
export HOME="$ROOT/work/test-home" XDG_CONFIG_HOME="$ROOT/work/test-home/.config" XDG_DATA_HOME="$ROOT/work/test-home/.local/share"
export SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy
export DIGHD_MOD="$ROOT/mods/test-nearest" DIGHD_VERIFY=1 DIGHD_SKIP_VIDEO=1
export DIGHD_DUMP_DIR="$OUT" DIGHD_DUMP_EVERY=250 DIGHD_QUIT_AT="$FRAMES"

timeout 120 "$SRC/scummvm" --path="$ROOT/game" --gfx-mode=surfacesdl --no-aspect-ratio --debuglevel=1 zak > "$OUT/scummvm.log" 2>&1 || true
grep -q "Using gameid zak, variant FM-TOWNS" "$OUT/scummvm.log" || { echo "Spillet startet ikke, se $OUT/scummvm.log"; exit 1; }
grep -E "DigHD: (verify|screen|room)" "$OUT/scummvm.log" || { echo "Ingen DigHD-linjer i loggen (bygget med FM-Towns-lagene på?), se $OUT/scummvm.log"; exit 1; }
if grep -qE "verify frame [0-9]+: [1-9][0-9]* (screen pixels|of)" "$OUT/scummvm.log"; then
	echo "Avvik funnet, se linjene over og $OUT/scummvm.log"
	exit 1
fi
echo "Bilder: $OUT"
