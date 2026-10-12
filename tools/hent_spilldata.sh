#!/usr/bin/env bash
# Henter spillfilene fra grenen "spilldata" inn i game/ og sjekker sjekksummene.
# Ingen filer er over 90 MB, så ingenting må settes sammen av deler (i motsetning til Sam & Max).
# Bruk: tools/hent_spilldata.sh            (fra roten av repoet)
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

echo "Henter grenen spilldata ..."
git fetch --depth 1 origin "+refs/heads/spilldata:refs/remotes/origin/spilldata"

echo "Pakker ut til game/ ..."
mkdir -p game
git archive refs/remotes/origin/spilldata game | tar -x -C "$ROOT"

echo "Sjekker sjekksummer ..."
(cd game && sha256sum --quiet -c SHA256SUMS)
echo "Ferdig. Spillfilene og CD-musikken ligger i $ROOT/game"
