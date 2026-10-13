#!/usr/bin/env bash
# Tester verbhjulet uten skjerm: de samme handlingene i rom 1 gjøres én gang med originalpanelet
# og én gang med hjulet, og setningene spillet kjører (doSentence) må bli like.
#
# Bruk:  tools/verbhjul_test.sh            (krever game/ og engine/scummvm/scummvm med patchene)
#
# Spillet går introen til ende uten tastetrykk og står i rom 1 med styring etter rundt
# 1300 rammer (målt 13. oktober 2026). Handlingene starter ved ramme 1400. Hver kjøring tar
# omtrent fire minutter, og de to går samtidig.
#
# Handlingene (hjulet i dynamisk modus, som er standard):
#   Open door (84), Open dresser drawer (92, med hold og dra; Open og Pull er ett ikon),
#   Turn on lamp (103), Pull window shade (90), Turn off cat clock (95; klokken går når rom 1
#   starter, så hjulet viser Turn off), Read ticket (82, fra
#   inventaret), Use ticket in door (to objekter: hjulet venter på det andre objektet),
#   et avbrudd (Use ticket, så høyreklikk), Close dresser drawer (skuffen er åpen, så hjulet
#   viser Close i stedet for Open), Open dresser (91, sender verbet videre til skuffen; regel
#   for hånd), og figurbytte til Annie: med portrettet i hjulet, med F2 i originalen. Annie
#   blir gjort tilgjengelig i testen ved å sette variablene ScummVM sjekker for F1 til F4
#   (Var[145] bit 0) og dem skript 24 bruker for å slå på Switch (Var[152] bit 4, Var[250]).
# Hjulet sjekker også at alle reglene i verbhjul_zak.h leses riktig (skrives tilbake og sammenlignes).
# Skjermbilder av hjulet og portrettene havner i work/verbhjul-test.
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
A+=",1460:click=52/155,1472:click=56/84,1484:click=56/84"
A+=",1520:click=260/155,1532:click=256/72,1544:click=256/72"
A+=",1580:click=4/163,1592:click=100/64,1604:click=100/64"
A+=",1640:click=260/163,1652:click=156/52,1664:click=156/52"
A+=",1700:click=52/171,1712:click=10/179,1724:click=10/179"
A+=",1760:click=180/171,1772:click=10/179,1784:click=308/96,1796:click=308/96"
A+=",1840:click=52/163,1852:click=60/92,1864:click=60/92"
A+=",1900:click=52/155,1912:click=24/80,1924:click=24/80"
A+=",1960:setbit=145.0/0,1960:setbit=152.4/1,1960:setvar=250/1,1961:script=24,1966:log,1975:fkey=2"
A+=",2040:log,2045:quit"

# Hjulet: høyreklikk og valg, eller hold og dra
B="100:rules,1400:rclick=308/96,1405:dump=hjul_dor,1408:pick=2"
B+=",1460:rdrag=56/84>2"
B+=",1520:rclick=256/72,1528:pick=5"
B+=",1580:rclick=100/64,1588:pick=6"
B+=",1640:rclick=156/52,1645:dump=hjul_kattklokke,1648:pick=10"
B+=",1700:rclick=10/179,1705:dump=hjul_inventar,1708:pick=12"
B+=",1760:rclick=10/179,1768:pick=14,1778:dump=venter,1784:click=308/96"
B+=",1810:rclick=10/179,1818:pick=14,1826:rclick=160/100,1832:log"
B+=",1835:dump=etter"
B+=",1840:rclick=60/92,1845:dump=hjul_skuff_aapen,1848:pick=7"
B+=",1900:rclick=24/80,1905:dump=hjul_kommode,1908:pick=2"
B+=",1960:setbit=145.0/0,1960:setbit=152.4/1,1960:setvar=250/1,1961:script=24,1966:log,1970:dump=portretter,1975:portrait=2"
B+=",2040:log,2042:dump=etter_bytte,2045:quit"

kjor() {  # navn, VERBHJUL (og portrettene), test
	HOME="$OUT/home-$1" XDG_CONFIG_HOME="$OUT/home-$1/.config" SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
	VERBHJUL="$2" VERBHJUL_PORTRETTER="$2" VERBHJUL_DYNAMISK=1 VERBHJUL_TEST="$3" VERBHJUL_DUMP_DIR="$OUT/bilder" \
	timeout 600 "$BIN" --path="$ROOT/game" --gfx-mode=surfacesdl --no-aspect-ratio --music-driver=null \
		--debuglevel=1 zak > "$OUT/$1.log" 2>&1 || true
}

echo "Kjører originalpanelet og hjulet (omtrent fire minutter) ..."
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
grep -q "Verbhjul: rules checked: [0-9]*, 0 differ" "$OUT/b.log" || { echo "FEIL: reglene i verbhjul_zak.h ble ikke lest riktig"; grep "Verbhjul: rule" "$OUT/b.log" | head; feil=1; }
grep -q "Verbhjul: waiting for the second object" "$OUT/b.log" || { echo "FEIL: hjulet ventet ikke på det andre objektet"; feil=1; }
grep -q "Verbhjul: cancelled the sentence" "$OUT/b.log" || { echo "FEIL: avbruddet ble ikke registrert"; feil=1; }
grep "test log" -A1 "$OUT/b.log" | grep "Verbhjul: state" | sed -n 1p | grep -q "prep 0" || { echo "FEIL: setningen ble ikke tømt etter avbruddet"; feil=1; }
grep -q "Verbhjul: portraits ego 1:" "$OUT/b.log" || { echo "FEIL: portrettene ble ikke vist"; feil=1; }
grep -q "Verbhjul: portrait 2" "$OUT/b.log" || { echo "FEIL: klikket på portrettet til Annie ble ikke tatt imot"; feil=1; }
grep "Verbhjul: state" "$OUT/b.log" | tail -1 | grep -q "ego 2" || { echo "FEIL: byttet ikke til Annie med portrettet"; feil=1; }
grep "Verbhjul: state" "$OUT/a.log" | tail -1 | grep -q "ego 2" || { echo "FEIL: byttet ikke til Annie med F2 i originalen"; feil=1; }
echo "Skjermbilder: $OUT/bilder"
[ "$feil" = 0 ] && echo "Bestått: $(wc -l < "$OUT/setninger-hjul.txt") like setninger, venting, avbrudd og figurbytte virker."
exit "$feil"
