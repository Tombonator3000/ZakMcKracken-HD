#!/usr/bin/env bash
# Bygger ScummVM med HD-patchen (samme patch som The Dig HD og Sam & Max HD, se docs/HD-MOTOR.md).
# Patchen er ikke slått på for Zak ennå; motoren kjører Zak som vanlig ScummVM.
#
# Krever: git, make, g++ (eller clang++), SDL2, libpng og libFLAC med utviklingsfiler.
#   Ubuntu/Debian: sudo apt install build-essential git libsdl2-dev libpng-dev zlib1g-dev libflac-dev
# Uten libFLAC bygger ScummVM uten FLAC, og CD-musikken (Track1.fla til Track21.fla) spilles ikke.
# Har du bygget uten FLAC først: RECONFIGURE=1 engine/build.sh
#
# Bruk:  engine/build.sh            (kildekoden havner i engine/scummvm)
#        SCUMMVM_SRC=/annen/mappe engine/build.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${SCUMMVM_SRC:-$HERE/scummvm}"
COMMIT="$(cat "$HERE/SCUMMVM_COMMIT")"
JOBS="${JOBS:-$(nproc 2>/dev/null || echo 2)}"

if [ ! -d "$SRC/.git" ]; then
	echo "Henter ScummVM ($COMMIT) til $SRC ..."
	git init -q "$SRC"
	git -C "$SRC" remote add origin https://github.com/scummvm/scummvm
fi

# Samme commit hver gang, så patchen alltid passer
git -C "$SRC" fetch -q --depth 1 origin "$COMMIT"
git -C "$SRC" checkout -q -f FETCH_HEAD
git -C "$SRC" clean -fdq engines/scumm

echo "Legger på patcher ..."
for p in "$HERE"/patches/*.patch; do
	git -C "$SRC" apply --whitespace=nowarn "$p"
	echo "  $(basename "$p")"
done

cd "$SRC"
if [ ! -f config.mk ] || [ "${RECONFIGURE:-0}" = "1" ]; then
	echo "Konfigurerer (bare SCUMM-motoren) ..."
	./configure --disable-all-engines --enable-engine=scumm,scumm-7-8 \
		--disable-engine=he,rebel2-psx --disable-detection-full \
		--disable-debug --enable-optimizations \
		--disable-mt32emu --disable-fluidsynth --disable-cloud --disable-libcurl \
		--disable-sdlnet --disable-tts --disable-eventrecorder > configure.log
fi

echo "Bygger med $JOBS tråder (første gang tar det noen minutter) ..."
make -j"$JOBS" > build.log 2>&1 || { tail -30 build.log; echo "Bygging feilet, se $SRC/build.log"; exit 1; }
grep -q "^USE_FLAC = 1" config.mk || echo "Merk: bygget uten FLAC, så CD-musikken spilles ikke. Installer libflac-dev og kjør RECONFIGURE=1 engine/build.sh"
echo "Ferdig: $SRC/scummvm"
