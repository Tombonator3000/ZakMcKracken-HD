#!/usr/bin/env bash
# Spill Zak McKracken (FM-Towns) rett fra repoet.
#
# HD-motoren er ikke slått på for Zak ennå (docs/HD-MOTOR.md), så spillet vises med originalgrafikken
# også når en HD-mod finnes. Valgene under som gjelder HD (--rom, --klassisk, --gult, Ctrl+H) virker
# først når porten er gjort.
#
#   ./spill.sh                 henter det som mangler, oppdaterer HD-modden og motoren, starter spillet
#   ./spill.sh --rom 22        starter i rom 22 (for å se på et bestemt rom)
#   ./spill.sh --klassisk      starter med originalgrafikken (Ctrl+H bytter underveis)
#   ./spill.sh --gult          farger gult der HD mangler (Ctrl+Shift+H slår av og på)
#   ./spill.sh --auto          fyller rom og objekter uten ChatGPT-bilde med automatisk oppskalering
#   ./spill.sh --fort          ingen henting eller bygging, bare start
#   ./spill.sh --fullskjerm    fullskjerm
#   ./spill.sh --programvare   uten OpenGL (hvis spillet ikke starter og sier "Could not load any graphics mode")
#   ./spill.sh --nettleser     i nettleseren på http://localhost:8000, bare på denne maskinen (--port N for en annen port)
#
# Valg som ikke står over, sendes videre til ScummVM.
# I spillet: Ctrl+H bytter mellom HD og originalgrafikk (valget huskes).
# Ctrl+Shift+H (gult felt der HD mangler), Alt+S (skjermbilde).
# Hva du bør se etter: docs/SPILLTEST.md.
# Nettleseren: spillet og HD-grafikken tilhører Disney/Lucasfilm og skal aldri legges på en åpen adresse.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

ROM="" KLASSISK=0 GULT=0 AUTO=0 FORT=0 NETTLESER=0 PORT=8000 FULLSKJERM=0 PROGRAMVARE=0
EKSTRA=()
while [ $# -gt 0 ]; do
	case "$1" in
	--rom) ROM="$2"; shift 2 ;;
	--klassisk) KLASSISK=1; shift ;;
	--gult) GULT=1; shift ;;
	--auto) AUTO=1; shift ;;
	--fort) FORT=1; shift ;;
	--fullskjerm) FULLSKJERM=1; shift ;;
	--programvare) PROGRAMVARE=1; shift ;;
	--nettleser) NETTLESER=1; shift ;;
	--port) PORT="$2"; shift 2 ;;
	-h|--help) sed -n '2,21p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
	*) EKSTRA+=("$1"); shift ;;
	esac
done

mangler=()
if [ "$NETTLESER" = 1 ]; then
	# Emscripten har sin egen kompilator og hentes av engine/build-web.sh
	for cmd in git make sha256sum tar xz python3 pkg-config zip; do command -v "$cmd" >/dev/null 2>&1 || mangler+=("$cmd"); done
	if [ ${#mangler[@]} -gt 0 ]; then
		echo "Mangler: ${mangler[*]}"
		echo "Ubuntu/Debian: sudo apt install git make python3 pkg-config xz-utils zip"
		echo "Fedora: sudo dnf install git make python3 pkgconf xz zip"
		exit 1
	fi
else
	for cmd in git make sha256sum tar; do command -v "$cmd" >/dev/null 2>&1 || mangler+=("$cmd"); done
	command -v c++ >/dev/null 2>&1 || command -v g++ >/dev/null 2>&1 || mangler+=("g++")
	command -v sdl2-config >/dev/null 2>&1 || mangler+=("SDL2 (libsdl2-dev)")
	pkg-config --exists libpng 2>/dev/null || [ -f /usr/include/png.h ] || mangler+=("libpng (libpng-dev)")
	pkg-config --exists flac 2>/dev/null || [ -f /usr/include/FLAC/all.h ] || mangler+=("libFLAC (libflac-dev), for CD-musikken")
	if [ ${#mangler[@]} -gt 0 ]; then
		echo "Mangler: ${mangler[*]}"
		echo "Ubuntu/Debian: sudo apt install build-essential git pkg-config libsdl2-dev libpng-dev zlib1g-dev libflac-dev"
		echo "Fedora: sudo dnf install gcc-c++ make git pkgconf SDL2-devel libpng-devel zlib-devel flac-devel"
		exit 1
	fi
fi

steg() { printf '\n== %s\n' "$*"; }

# 1. Spillfilene (første gang)
if [ ! -f game/00.LFL ]; then
	steg "Henter spillfilene"
	tools/hent_spilldata.sh
fi

# 2. Siste HD-mod fra grenen hd-mod (tom til den første modden er laget)
if [ "$FORT" = 0 ] || [ ! -f mods/gpt/mod.json ]; then
	steg "Henter siste HD-mod"
	tools/mod_gren.sh hent || echo "Fikk ikke hentet grenen hd-mod."
fi

# 3. Motoren: bygges første gang og når patchen eller ScummVM-versjonen er endret
if [ "$NETTLESER" = 1 ]; then
	# Nettleserversjonen har sitt eget stempel. Byggeskriptet er med, fordi valgene til configure står der.
	STEMPEL="$(cat engine/SCUMMVM_COMMIT engine/patches/*.patch engine/build-web.sh | sha256sum | cut -c1-16)"
	BYGD="$(cat engine/scummvm-web/.dighd-stempel 2>/dev/null || true)"
	if [ ! -f engine/scummvm-web/build-emscripten/scummvm.wasm ] || { [ "$FORT" = 0 ] && [ "$STEMPEL" != "$BYGD" ]; }; then
		steg "Bygger motoren for nettleseren (første gang laster den ned Emscripten og tar noen minutter)"
		engine/build-web.sh
		echo "$STEMPEL" > engine/scummvm-web/.dighd-stempel
	fi
else
	STEMPEL="$(cat engine/SCUMMVM_COMMIT engine/patches/*.patch | sha256sum | cut -c1-16)"
	BYGD="$(cat engine/scummvm/.dighd-stempel 2>/dev/null || true)"
	if [ ! -x engine/scummvm/scummvm ] || { [ "$FORT" = 0 ] && [ "$STEMPEL" != "$BYGD" ]; }; then
		steg "Bygger motoren (første gang tar det noen minutter)"
		engine/build.sh
		echo "$STEMPEL" > engine/scummvm/.dighd-stempel
	fi
fi

# 4. Automatisk oppskalering der ChatGPT ikke har levert ennå (valgfritt)
MOD=gpt
[ -f mods/gpt/mod.json ] || { MOD=ingen; echo "Ingen HD-mod ennå, starter uten."; }
if [ "$AUTO" = 1 ]; then
	MOD=auto
	GPT_STEMPEL="$(sha256sum mods/gpt/SHA256SUMS | cut -c1-16)"
	if [ ! -f mods/auto/mod.json ] || [ "$(cat mods/auto/.gpt-stempel 2>/dev/null || true)" != "$GPT_STEMPEL" ]; then
		steg "Lager automatisk oppskalering for resten (første gang tar det 5 til 10 minutter)"
		if [ ! -x .venv/bin/zakhd ]; then
			python3 -c 'import sys; sys.exit(sys.version_info < (3, 12))' || { echo "--auto krever Python 3.12 eller nyere."; exit 1; }
			python3 -m venv .venv
			.venv/bin/pip install -q -e pipeline
		fi
		[ -f work/extract/rooms.json ] || .venv/bin/zakhd extract --only rom
		rm -rf mods/auto
		.venv/bin/zakhd build-mod --name auto --method lanczos-sharp --egne mods/gpt
		echo "$GPT_STEMPEL" > mods/auto/.gpt-stempel
	fi
fi

# 5. Start
if [ "$NETTLESER" = 1 ]; then
	# Bare lokalt: webserveren lytter på 127.0.0.1 og siden nekter å starte fra en annen adresse.
	steg "Starter Zak i nettleseren (mod: $MOD)"
	[ "$FULLSKJERM" = 1 ] && echo "--fullskjerm gjelder ikke i nettleseren. Bruk F11 i nettleseren."
	[ "$PROGRAMVARE" = 1 ] && echo "--programvare gjelder ikke i nettleseren."
	VALG=(--port "$PORT")
	[ -n "$ROM" ] && VALG+=(--rom "$ROM")
	[ "$KLASSISK" = 1 ] && VALG+=(--klassisk)
	[ "$GULT" = 1 ] && VALG+=(--gult)
	exec engine/run-web.sh "$MOD" "${VALG[@]}" "${EKSTRA[@]}"
fi

[ "$FULLSKJERM" = 1 ] && EKSTRA+=(--fullscreen)
[ "$PROGRAMVARE" = 1 ] && EKSTRA+=(--gfx-mode=surfacesdl)
steg "Starter Zak (mod: $MOD)"
[ -n "$ROM" ] && export DIGHD_TEST_ROOM="$ROM" DIGHD_TEST_AT="${DIGHD_TEST_AT:-240}" DIGHD_SKIP_VIDEO=1 && echo "Hopper til rom $ROM (virker først når HD-patchen er portet til Zak)."
[ "$KLASSISK" = 1 ] && export DIGHD_CLASSIC=1
[ "$GULT" = 1 ] && export DIGHD_SHOW_MISSING=1
echo "HD er ikke slått på for Zak ennå; spillet vises med originalgrafikken. Alt+S: skjermbilde."
exec engine/run.sh "$MOD" "${EKSTRA[@]}"
