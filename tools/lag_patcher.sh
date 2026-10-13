#!/usr/bin/env bash
# Lager patchene i engine/patches på nytt fra endringene i engine/scummvm.
#
#   0001-dighd-hd-grafikk.patch  HD-motoren, den samme som i The Dig og Sam & Max
#   0002-verbhjul.patch          verbhjulet for Zak (engines/scumm/verbhjul.*, verbhjul_zak.h og krokene)
#
# Bruk:  tools/lag_patcher.sh            (etter endringer i engine/scummvm)
#
# Slik: en midlertidig kopi av ScummVM ved engine/SCUMMVM_COMMIT får alle filene som er endret
# i engine/scummvm. Filene verbhjul.* og verbhjul_zak.h fjernes og krokene i den gamle 0002 trekkes fra (git apply -R);
# det som er igjen, er den nye 0001.
# Så legges filene inn igjen, og forskjellen mot 0001 er den nye 0002. Går det ikke å trekke fra
# krokene (de er endret og blandet med DigHD), stopper skriptet uten å endre noe.
# Til slutt sjekkes det at 0001 og 0002 passer mot commiten etter hverandre.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="${SCUMMVM_SRC:-$ROOT/engine/scummvm}"
P="$ROOT/engine/patches"
COMMIT="$(cat "$ROOT/engine/SCUMMVM_COMMIT")"
TMP="$(mktemp -d)"
trap 'git -C "$SRC" worktree remove --force "$TMP/x" >/dev/null 2>&1 || true; git -C "$SRC" worktree remove --force "$TMP/sjekk" >/dev/null 2>&1 || true; rm -rf "${TMP:?}"' EXIT

cd "$SRC"
git add -N engines/scumm/dighd.cpp engines/scumm/dighd.h engines/scumm/verbhjul.cpp engines/scumm/verbhjul.h engines/scumm/verbhjul_zak.h
mapfile -t FILER < <(git diff --name-only "$COMMIT")
echo "Endrede filer: ${#FILER[@]}"

git worktree add -q --detach "$TMP/x" "$COMMIT"
for f in "${FILER[@]}"; do
	mkdir -p "$TMP/x/$(dirname "$f")"
	cp "$f" "$TMP/x/$f"
done
cd "$TMP/x"
git add -N engines/scumm/dighd.cpp engines/scumm/dighd.h engines/scumm/verbhjul.cpp engines/scumm/verbhjul.h engines/scumm/verbhjul_zak.h

# 0001: alt uten hjulet. De nye filene til hjulet fjernes, og krokene i resten trekkes fra.
X="--exclude=engines/scumm/verbhjul.cpp --exclude=engines/scumm/verbhjul.h --exclude=engines/scumm/verbhjul_zak.h"
git apply -R --check $X "$P/0002-verbhjul.patch" || { echo "Krokene i 0002 kan ikke trekkes fra. Lag patchene for hånd (se AGENTS.md)."; exit 1; }
git apply -R $X "$P/0002-verbhjul.patch"
rm -f engines/scumm/verbhjul.cpp engines/scumm/verbhjul.h engines/scumm/verbhjul_zak.h
git add -A
git -c core.abbrev=8 diff --cached > "$TMP/0001.patch"
git -c commit.gpgsign=false commit -q -m "midlertidig: 0001"

# 0002: forskjellen fra 0001 til det som er i engine/scummvm
for f in "${FILER[@]}"; do
	cp "$SRC/$f" "$TMP/x/$f"
done
git add -N engines/scumm/verbhjul.cpp engines/scumm/verbhjul.h engines/scumm/verbhjul_zak.h
git -c core.abbrev=8 diff > "$TMP/0002.patch"

# Sjekk at de passer etter hverandre
git -C "$SRC" worktree add -q --detach "$TMP/sjekk" "$COMMIT"
git -C "$TMP/sjekk" apply --check "$TMP/0001.patch"
git -C "$TMP/sjekk" apply "$TMP/0001.patch"
git -C "$TMP/sjekk" apply --check "$TMP/0002.patch"

cp "$TMP/0001.patch" "$P/0001-dighd-hd-grafikk.patch"
cp "$TMP/0002.patch" "$P/0002-verbhjul.patch"
echo "Ferdig: 0001 ($(wc -l < "$P/0001-dighd-hd-grafikk.patch") linjer) og 0002 ($(wc -l < "$P/0002-verbhjul.patch") linjer) passer mot $COMMIT."
