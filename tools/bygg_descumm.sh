#!/usr/bin/env bash
# Henter scummvm-tools ved en låst commit og bygger bare descumm (SCUMM-skriptdekompilatoren).
#
# Krever: git, en POSIX-skall og g++ (eller clang++). Ingen biblioteker, ikke wxWidgets eller Boost.
#
# Bruk:  tools/bygg_descumm.sh                 (kildekoden og descumm havner i work/scummvm-tools)
#        SCUMMVM_TOOLS_SRC=/annen/mappe tools/bygg_descumm.sh
#        CXX=clang++ tools/bygg_descumm.sh
#
# descumm trenger fem kildefiler: engines/scumm/descumm.cpp, descumm6.cpp, descumm-common.cpp,
# descumm-tool.cpp og common/util.cpp (error og warning). Makefile.common lister flere
# (tool.o, version.o og lyd- og filkode) som descumm ikke bruker, og "make descumm" bygger i
# tillegg objektene til de andre verktøyene, fordi version.o avhenger av dem. Derfor kalles
# kompilatoren direkte her. configure kjøres bare for å lage config.h (endianness og typer).
set -euo pipefail

# scummvm-tools master 30. august 2026 ("MACS2: fixed hotspot names encoding")
COMMIT=8665aa1d3221a6cc884026f5ed7144fac512e0e9
URL=https://github.com/scummvm/scummvm-tools

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="${SCUMMVM_TOOLS_SRC:-$ROOT/work/scummvm-tools}"
CXX="${CXX:-g++}"

if [ ! -e "$SRC" ] || [ -z "$(ls -A "$SRC" 2>/dev/null)" ]; then
	echo "Henter scummvm-tools ($COMMIT) til $SRC ..."
	mkdir -p "$SRC"
	git init -q "$SRC"
	git -C "$SRC" remote add origin "$URL"
elif [ ! -d "$SRC/.git" ] || [ "$(git -C "$SRC" remote get-url origin 2>/dev/null || true)" != "$URL" ]; then
	# Mappen finnes, men er ikke en klone som dette skriptet har laget: rør den ikke
	echo "$SRC finnes og er ikke en scummvm-tools-klone (origin $URL). Velg en annen mappe med SCUMMVM_TOOLS_SRC."
	exit 1
fi

if [ "$(git -C "$SRC" rev-parse -q --verify HEAD 2>/dev/null || true)" != "$COMMIT" ]; then
	git -C "$SRC" fetch -q --depth 1 "$URL" "$COMMIT"
	git -C "$SRC" checkout -q -f FETCH_HEAD
	rm -f "$SRC/config.h" "$SRC/descumm"
fi

cd "$SRC"
if [ ! -f config.h ]; then
	echo "Lager config.h ..."
	./configure --disable-wxwidgets --disable-boost --disable-vorbis --disable-tremor \
		--disable-flac --disable-mad --disable-png --disable-zlib --disable-freetype2 \
		--disable-iconv > configure.log 2>&1 || { tail -20 configure.log; echo "configure feilet, se $SRC/configure.log"; exit 1; }
fi

echo "Bygger descumm med $CXX ..."
"$CXX" -O2 -std=c++11 -DHAVE_CONFIG_H -DPOSIX -I. \
	-Wno-multichar -Wno-unused-parameter -Wno-format-overflow \
	-o descumm \
	engines/scumm/descumm.cpp engines/scumm/descumm6.cpp \
	engines/scumm/descumm-common.cpp engines/scumm/descumm-tool.cpp \
	common/util.cpp > build-descumm.log 2>&1 || { tail -30 build-descumm.log; echo "Bygging feilet, se $SRC/build-descumm.log"; exit 1; }

# Røyktest: uten argumenter skriver descumm hjelpeteksten og avslutter med 0
./descumm | grep -q "SCUMM Script decompiler" || { echo "descumm ble bygget, men svarer ikke som forventet"; exit 1; }
echo "Ferdig: $SRC/descumm (scummvm-tools $COMMIT)"
echo "Bruk: DESCUMM=$SRC/descumm .venv/bin/python tools/dekompiler_skript.py (finner den også uten DESCUMM)"
