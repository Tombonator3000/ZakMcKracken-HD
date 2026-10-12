#!/usr/bin/env bash
# Bygger ScummVM med HD-patchen fra The Dig HD (DigHD) for nettleseren (WebAssembly med Emscripten).
# Patchen er ikke slått på for Zak McKracken ennå, så Zak kjører med originalgrafikken.
# Nettleserversjonen er ikke bygget for Zak ennå.
#
# Resultatet kjøres lokalt med engine/run-web.sh på http://localhost:8000.
# engine/build-pages.py lager en egen offentlig motorpakke som leser private filer
# fra nettleserens lokale lagring. Spillfilene og HD-grafikken skal aldri publiseres.
#
# Følger ScummVM sin egen oppskrift (dists/emscripten/build.sh på den låste commiten):
# samme Emscripten-versjon, configure med --host=wasm32-unknown-emscripten, make og
# make dist-emscripten. Bare SCUMM-motoren, som i engine/build.sh.
#
# Zak spiller musikken fra CD-sporene Track1.fla til Track21.fla (FLAC). ScummVM leser dem bare
# når den er bygget med libFLAC, og Emscripten har ikke libFLAC. Skriptet bygger derfor libFLAC
# først (steg 3), i ScummVM sin mappe for nettleserbiblioteker (dists/emscripten/libs), og
# configure får --enable-flac.
#
# Krever: git, make, python3, pkg-config, tar, xz og zip. Emscripten (emsdk) installeres i
# engine/emsdk første gang (omtrent 350 MB). ScummVM sin configure bruker pkg-config for SDL3,
# og make dist-emscripten bruker zip. libFLAC (1 MB) hentes fra downloads.xiph.org.
#
# Bruk:  engine/build-web.sh        (kildekoden havner i engine/scummvm-web, resultatet i
#                                    engine/scummvm-web/build-emscripten)
#        SCUMMVM_WEB_SRC=/annen/mappe EMSDK_DIR=/annen/emsdk engine/build-web.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${SCUMMVM_WEB_SRC:-$HERE/scummvm-web}"
EMSDK_DIR="${EMSDK_DIR:-$HERE/emsdk}"
COMMIT="$(cat "$HERE/SCUMMVM_COMMIT")"
JOBS="${JOBS:-$(nproc 2>/dev/null || echo 2)}"

# 1. Kildekoden: samme commit og samme patch som den vanlige motoren
if [ ! -d "$SRC/.git" ]; then
	echo "Henter ScummVM ($COMMIT) til $SRC ..."
	git init -q "$SRC"
	git -C "$SRC" remote add origin https://github.com/scummvm/scummvm
fi
git -C "$SRC" fetch -q --depth 1 origin "$COMMIT"
git -C "$SRC" checkout -q -f FETCH_HEAD
git -C "$SRC" clean -fdq engines/scumm

echo "Legger på patcher ..."
for p in "$HERE"/patches/*.patch; do
	git -C "$SRC" apply --whitespace=nowarn "$p"
	echo "  $(basename "$p")"
done

# 2. Emscripten: versjonen ScummVM sin egen byggeoppskrift bruker på denne commiten
EMSDK_VERSION="${EMSDK_VERSION:-$(sed -n 's/^EMSDK_VERSION="\${EMSDK_VERSION:-\([0-9.]*\)}"$/\1/p' "$SRC/dists/emscripten/build.sh")}"
EMSDK_VERSION="${EMSDK_VERSION:-4.0.10}"
if [ ! -x "$EMSDK_DIR/emsdk" ]; then
	echo "Henter emsdk til $EMSDK_DIR ..."
	git clone -q https://github.com/emscripten-core/emsdk "$EMSDK_DIR"
fi
if [ "$(cat "$EMSDK_DIR/.dighd-versjon" 2>/dev/null || true)" != "$EMSDK_VERSION" ]; then
	echo "Installerer Emscripten $EMSDK_VERSION (første gang laster den ned omtrent 350 MB) ..."
	(cd "$EMSDK_DIR" && { ./emsdk install "$EMSDK_VERSION" || { git pull -q && ./emsdk install "$EMSDK_VERSION"; }; } && ./emsdk activate "$EMSDK_VERSION") > "$EMSDK_DIR/install.log" 2>&1 \
		|| { tail -20 "$EMSDK_DIR/install.log"; echo "Installasjonen av Emscripten feilet, se $EMSDK_DIR/install.log"; exit 1; }
	echo "$EMSDK_VERSION" > "$EMSDK_DIR/.dighd-versjon"
fi
# shellcheck disable=SC1091
EMSDK_QUIET=1 source "$EMSDK_DIR/emsdk_env.sh"

# 3. libFLAC for musikksporene. Bygges slik ScummVM sin egen oppskrift bygger de andre
# autoconf-bibliotekene (libmad, liba52): emconfigure med --host=wasm32-unknown-none og et
# prefiks i dists/emscripten/libs/build. Bare biblioteket og overskriftene, uten Ogg.
# Mappen er ikke sporet i ScummVM sitt git (står i .gitignore der), så den blir stående
# mellom byggene.
FLAC_VERSION=1.4.3
FLAC_SHA256=6c58e69cd22348f441b861092b825e591d0b822e106de6eb0ee4d05d27205b70
LIBS="$SRC/dists/emscripten/libs"
if [ ! -f "$LIBS/build/lib/libFLAC.a" ] || [ ! -f "$LIBS/build/COPYING.FLAC" ]; then
	echo "Bygger libFLAC $FLAC_VERSION for nettleseren ..."
	mkdir -p "$LIBS"
	FLAC_TAR="$LIBS/flac-$FLAC_VERSION.tar.xz"
	if [ "$(sha256sum "$FLAC_TAR" 2>/dev/null | cut -d' ' -f1)" != "$FLAC_SHA256" ]; then
		python3 -c 'import sys, urllib.request; open(sys.argv[2], "wb").write(urllib.request.urlopen(sys.argv[1], timeout=60).read())' \
			"https://downloads.xiph.org/releases/flac/flac-$FLAC_VERSION.tar.xz" "$FLAC_TAR"
		[ "$(sha256sum "$FLAC_TAR" | cut -d' ' -f1)" = "$FLAC_SHA256" ] || { echo "Feil sjekksum for $FLAC_TAR"; exit 1; }
	fi
	rm -rf "$LIBS/flac-$FLAC_VERSION"
	tar -xJf "$FLAC_TAR" -C "$LIBS"
	(
		cd "$LIBS/flac-$FLAC_VERSION"
		# ac_cv_c_bigendian=no: WebAssembly er little endian, og configure kan ikke kjøre en test for det
		CFLAGS="-O2" emconfigure ./configure --host=wasm32-unknown-none --build=wasm32-unknown-none \
			--prefix="$LIBS/build" --enable-static --disable-shared --with-pic \
			--disable-ogg --disable-cpplibs --disable-programs --disable-examples --disable-doxygen-docs \
			--disable-asm-optimizations --disable-stack-smash-protection --disable-fortify-source \
			--disable-version-from-git ac_cv_c_bigendian=no
		emmake make -C src/libFLAC -j"$JOBS"
		emmake make -C src/libFLAC install
		emmake make -C include install
	) > "$LIBS/flac.log" 2>&1 || { tail -30 "$LIBS/flac.log"; echo "Byggingen av libFLAC feilet, se $LIBS/flac.log"; exit 1; }
	# Lisensen (BSD) skal følge motoren; engine/build-pages.py legger den i licenses/
	cp "$LIBS/flac-$FLAC_VERSION/COPYING.Xiph" "$LIBS/build/COPYING.FLAC"
fi

# 4. Konfigurer og bygg
cd "$SRC"
if [ ! -f config.mk ] || [ "${RECONFIGURE:-0}" = "1" ] || ! grep -q '^USE_FLAC = 1' config.mk; then
	echo "Konfigurerer for nettleseren (bare SCUMM-motoren) ..."
	# Emscripten slår av valgfrie biblioteker som ikke er slått på; DigHD trenger PNG og zlib.
	# Zak (SCUMM v3) trenger ikke scumm-7-8, men dighd.cpp bruker ScummEngine_v7 uten
	# #ifdef, og scumm_v7.h er tom uten ENABLE_SCUMM_7_8. Valget står derfor som før.
	# FLAC slås på med libFLAC fra steg 3. Uten den finner configure ikke FLAC og slår det av
	# uten å si fra, og musikken i Zak blir borte.
	# Zak (FM-Towns) bruker ikke MIDI: musikken er CD-sporene, og lydeffektene kommer fra
	# FM-Towns-lydemuleringen (fmtowns_pc98_audio, som SCUMM-motoren tar med selv).
	# --disable-mt32emu og --disable-fluidsynth står som for The Dig og har ingen betydning for Zak.
	emconfigure ./configure --host=wasm32-unknown-emscripten --build=wasm32-unknown-emscripten \
		--disable-all-engines --enable-engine=scumm,scumm-7-8 \
		--disable-engine=he,rebel2-psx --disable-detection-full \
		--disable-debug --enable-optimizations \
		--enable-png --enable-zlib \
		--enable-flac --with-flac-prefix="$LIBS/build" \
		--disable-mt32emu --disable-fluidsynth --disable-cloud --disable-libcurl \
		--disable-sdlnet --disable-tts --disable-eventrecorder > configure.log 2>&1 \
		|| { tail -30 configure.log; echo "Konfigureringen feilet, se $SRC/configure.log"; exit 1; }
	rm -f scummvm-conf.*
	grep -q '^USE_FLAC = 1' config.mk || { echo "FLAC kom ikke med i konfigurasjonen, se $SRC/configure.log"; exit 1; }
fi

echo "Bygger med $JOBS tråder (første gang tar det noen minutter) ..."
emmake make -j"$JOBS" > build.log 2>&1 || { tail -30 build.log; echo "Bygging feilet, se $SRC/build.log"; exit 1; }
rm -rf build-emscripten
emmake make dist-emscripten >> build.log 2>&1 || { tail -30 build.log; echo "Pakkingen feilet, se $SRC/build.log"; exit 1; }
echo "Ferdig: $SRC/build-emscripten"
