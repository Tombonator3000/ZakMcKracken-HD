#!/usr/bin/env bash
# Romtest: kjører spillet uten skjerm i hvert rom med en HD-mod og lager rapport og kontaktark.
#
#   tools/romtest.sh                      alle rom med mods/gpt, også flere kameraplasser i store rom
#   tools/romtest.sh --rom 2,9,22         bare disse rommene (--rom 20-30 for et område)
#   tools/romtest.sh --mod test-nearest   en annen mod (navn i mods/ eller en sti)
#   tools/romtest.sh --kamera ett         én kjøring per rom, der spillet selv setter kameraet
#   tools/romtest.sh --objekter           i tillegg alle tilstandene til alle objektene i hvert rom
#   tools/romtest.sh --bare-rapport       lager rapport og ark på nytt uten å kjøre spillet
#
# Resultat i work/romtest: RAPPORT.md, romtest.csv, ark_NN.png (HD og original side om side),
# en mappe per kjøring med logg og bilder, og nærbilder i naerbilder/. Med --objekter også
# objekter.csv og et nærbilde per objekt og tilstand.
# Notater fra gjennomsynet i work/romtest/FUNN.md kommer med i rapporten.
# Motoren: $SCUMMVM_SRC/scummvm eller engine/scummvm/scummvm (engine/build.sh), eller --motor.
# Alle valg: tools/romtest.sh --help
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY=python3
[ -x "$ROOT/.venv/bin/python" ] && PY="$ROOT/.venv/bin/python"
"$PY" -c 'import numpy, PIL' 2>/dev/null || {
	echo "romtest trenger numpy og Pillow: pip install -e \"pipeline[dev]\" (eller pip install numpy pillow)"
	exit 1
}
exec "$PY" "$ROOT/tools/romtest.py" "$@"
