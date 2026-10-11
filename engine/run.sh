#!/usr/bin/env bash
# Starter Zak McKracken (FM-Towns) med motoren fra engine/build.sh.
#
# Bruk:  engine/run.sh [modnavn] [flere ScummVM-valg]
#        engine/run.sh ingen          (uten mod, slik spillet går nå)
#        engine/run.sh hd
#
# Modmappen er mods/<modnavn>. Spillfilene ligger i game/ (tools/hent_spilldata.sh).
#
# HD-motoren (DigHD) er ikke slått på for Zak ennå (docs/HD-MOTOR.md). En mod gjør derfor
# ingenting før porten er gjort; spillet vises med originalgrafikken.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
SRC="${SCUMMVM_SRC:-$HERE/scummvm}"
MOD="${1:-ingen}"
shift || true

[ -x "$SRC/scummvm" ] || { echo "Fant ikke $SRC/scummvm. Kjør engine/build.sh først."; exit 1; }
[ -f "$ROOT/game/00.LFL" ] || { echo "Fant ikke spillfilene. Kjør tools/hent_spilldata.sh først."; exit 1; }
[ -f "$ROOT/game/Track1.fla" ] || echo "Merk: Track1.fla mangler i game/, spillet blir uten CD-musikk."

if [ "$MOD" != "ingen" ]; then
	[ -d "$ROOT/mods/$MOD" ] || { echo "Fant ikke mods/$MOD. Lag den med: zakhd build-mod --name $MOD (eller bruk engine/run.sh ingen)"; exit 1; }
	export DIGHD_MOD="$ROOT/mods/$MOD"
fi
# FM-Towns-bildet er 320 x 240 med kvadratiske piksler, så sideforholdskorrigering trengs ikke
exec "$SRC/scummvm" --path="$ROOT/game" --gfx-mode=opengl --no-aspect-ratio "$@" zak
