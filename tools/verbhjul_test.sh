#!/usr/bin/env bash
# Tester verbhjulet uten skjerm: de samme handlingene i rom 1 gjøres én gang med originalpanelet
# og én gang med hjulet, og setningene spillet kjører (doSentence) må bli like.
#
# Bruk:  tools/verbhjul_test.sh            (krever game/ og engine/scummvm/scummvm med patchene)
#
# Spillet går introen til ende uten tastetrykk og står i rom 1 med styring etter rundt
# 1300 rammer (målt 13. oktober 2026). Handlingene starter ved ramme 1400. Hver kjøring tar
# omtrent tre minutter, og de to går samtidig.
#
# Handlingene:
#   Open door (84), Pull dresser drawer (92, med hold og dra), Turn on lamp (103),
#   Pull window shade (90), Turn on cat clock (95), Read ticket (82, fra inventaret),
#   Use ticket in door (to objekter: hjulet venter på det andre objektet).
# Til slutt et avbrudd (Use ticket, så høyreklikk) og skjermbilder av hjulet i work/verbhjul-test.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN="${SCUMMVM:-$ROOT/engine/scummvm/scummvm}"
OUT="$ROOT/work/verbhjul-test"
[ -x "$BIN" ] || { echo "Fant ikke $BIN. Kjør engine/build.sh først."; exit 2; }
[ -f "$ROOT/game/00.LFL" ] || { echo "Spillfilene mangler. Kjør tools/hent_spilldata.sh først."; exit 2; }

rm -rf "${OUT:?}"
mkdir -p "$OUT/home-a" "$OUT/home-b" "$OUT/bilder"

# Originalpanelet: verbet, objektet, objektet en gang til (eller det andre objektet to ganger)
A="1400:click=52/155,1412:click=308/96,1424:click=308/96"
A+=",1460:click=4/163,1472:click=56/84,1484:click=56/84"
A+=",1520:click=260/155,1532:click=256/72,1544:click=256/72"
A+=",1580:click=4/163,1592:click=100/64,1604:click=100/64"
A+=",1640:click=260/155,1652:click=156/52,1664:click=156/52"
A+=",1700:click=52/171,1712:click=10/179,1724:click=10/179"
A+=",1760:click=180/171,1772:click=10/179,1784:click=308/96,1796:click=308/96"
A+=",1840:quit"

# Hjulet: høyreklikk og valg, eller hold og dra
B="1400:rclick=308/96,1405:dump=hjul_dor,1408:pick=2"
B+=",1460:rdrag=56/84>6"
B+=",1520:rclick=256/72,1528:pick=5"
B+=",1580:rclick=100/64,1588:pick=6"
B+=",1640:rclick=156/52,1645:dump=hjul_kattklokke,1648:pick=5"
B+=",1700:rclick=10/179,1705:dump=hjul_inventar,1708:pick=12"
B+=",1760:rclick=10/179,1768:pick=14,1778:dump=venter,1784:click=308/96"
B+=",1810:rclick=10/179,1818:pick=14,1826:rclick=160/100,1832:log"
B+=",1835:dump=etter,1840:quit"

kjor() {  # navn, VERBHJUL, test
	HOME="$OUT/home-$1" XDG_CONFIG_HOME="$OUT/home-$1/.config" SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
	VERBHJUL="$2" VERBHJUL_TEST="$3" VERBHJUL_DUMP_DIR="$OUT/bilder" \
	timeout 600 "$BIN" --path="$ROOT/game" --gfx-mode=surfacesdl --no-aspect-ratio --music-driver=null \
		--debuglevel=1 zak > "$OUT/$1.log" 2>&1 || true
}

echo "Kjører originalpanelet og hjulet (omtrent tre minutter) ..."
kjor a 0 "$A" &
kjor b 1 "$B" &
wait

grep "Verbhjul: doSentence" "$OUT/a.log" > "$OUT/setninger-original.txt" || true
grep "Verbhjul: doSentence" "$OUT/b.log" > "$OUT/setninger-hjul.txt" || true
echo "Originalpanelet:"; sed 's/^/  /' "$OUT/setninger-original.txt"
echo "Hjulet:"; sed 's/^/  /' "$OUT/setninger-hjul.txt"

feil=0
[ -s "$OUT/setninger-original.txt" ] || { echo "FEIL: ingen setninger med originalpanelet (nådde spillet rom 1?)"; feil=1; }
if ! diff -q "$OUT/setninger-original.txt" "$OUT/setninger-hjul.txt" > /dev/null; then
	echo "FEIL: setningene er ulike"; diff "$OUT/setninger-original.txt" "$OUT/setninger-hjul.txt" || true; feil=1
fi
grep -q "Verbhjul: waiting for the second object" "$OUT/b.log" || { echo "FEIL: hjulet ventet ikke på det andre objektet"; feil=1; }
grep -q "Verbhjul: cancelled the sentence" "$OUT/b.log" || { echo "FEIL: avbruddet ble ikke registrert"; feil=1; }
grep "Verbhjul: state" "$OUT/b.log" | tail -1 | grep -q "prep 0" || { echo "FEIL: setningen ble ikke tømt etter avbruddet"; feil=1; }
echo "Skjermbilder: $OUT/bilder"
[ "$feil" = 0 ] && echo "Bestått: $(wc -l < "$OUT/setninger-hjul.txt") like setninger, venting og avbrudd virker."
exit "$feil"
