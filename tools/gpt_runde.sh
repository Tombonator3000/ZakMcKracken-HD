#!/usr/bin/env bash
# Én runde i samarbeidet med ChatGPT. Claude kjører denne jevnlig.
#
#   1. Setter opp det som mangler (spillfiler, pipeline, uttrekk, jobber)
#   2. Henter nye bilder fra grenen gpt-arbeid
#   3. Kontrollerer dem (zakhd gpt-inn) og lager HD-rom, HD-objekter og HD-figurruter, og tar inn
#      figurarkene i glatt stil som myke figurruter (zakhd myke-figurer)
#   4. Bygger modden mods/gpt av de godkjente rommene, objektbildene og figurrutene og publiserer den i grenen hd-mod
#   5. Skriver ny ORDRE.md og sender status, rapport og retur tilbake til grenen
#
# Bruk: tools/gpt_runde.sh [--beskjed "tekst til ChatGPT"] ...
#
# Ikke i bruk for Zak ennå: bestillingen er ikke aktiv før stilpiloten er godkjent
# (docs/BESTILLING-CHATGPT.md). Ikke prøvd med Zak: hverken uttrekket (zakhd extract) eller resten.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
BESKJED=()
while [ $# -gt 0 ]; do
	case "$1" in
	--beskjed) BESKJED+=(--beskjed "$2"); shift 2 ;;
	*) echo "Ukjent valg: $1"; exit 1 ;;
	esac
done

# 1. Oppsett
[ -f game/00.LFL ] || tools/hent_spilldata.sh
if ! command -v zakhd >/dev/null 2>&1; then
	[ -x .venv/bin/zakhd ] || { python3 -m venv .venv && .venv/bin/pip install -q -e "pipeline[dev,uttrekk]"; }
	export PATH="$ROOT/.venv/bin:$PATH"
fi
[ -f work/extract/rooms.json ] || zakhd extract

# 2. Hent
before="$(cat work/gpt-ferdig/provenance.json work/gpt-ferdig/myke.json 2>/dev/null | sha256sum || true)"
status_before="$(sha256sum work/gpt/status.csv 2>/dev/null || true)"
tools/gpt_gren.sh hent

# 3. Kontroller. Figurarkene i glatt stil (ekte alfa) får status levert i gpt-inn og tas inn her,
#    med egen alfa og marg rundt rutene (costumes/costumeCCC_NNN_hd.png).
zakhd gpt-inn
zakhd myke-figurer
after="$(cat work/gpt-ferdig/provenance.json work/gpt-ferdig/myke.json 2>/dev/null | sha256sum || true)"

# 4. Mod, bare når noe nytt er godkjent. Rommene med HD-bakgrunn velges med --rooms.
#    Godkjente objektbilder i work/gpt-ferdig/objects kommer med uansett, også i rom
#    uten HD-bakgrunn (de får ingen automatisk oppskalert bakgrunn). Godkjente figurruter i
#    work/gpt-ferdig/costumes kommer også med; de andre rutene vises som originalen (ingen
#    --kostymer, så ingenting skaleres automatisk).
if [ "$before" != "$after" ] && [ -d work/gpt-ferdig ]; then
	rooms="$(ls work/gpt-ferdig/rooms 2>/dev/null | sed -n 's/^room0*\([0-9][0-9]*\)\.png$/\1/p' | paste -sd, - || true)"
	objects="$(ls work/gpt-ferdig/objects 2>/dev/null | grep -c '^obj.*\.png$' || true)"
	cels="$(ls work/gpt-ferdig/costumes 2>/dev/null | grep -c '^costume[0-9]*_[0-9]*\(_hd\)\?\.png$' || true)"
	if [ -n "$rooms" ] || [ "${objects:-0}" -gt 0 ] || [ "${cels:-0}" -gt 0 ]; then
		rm -rf mods/gpt
		zakhd build-mod --name gpt --method lanczos-sharp --rooms "${rooms:-ingen}" --egne work/gpt-ferdig
		tools/mod_gren.sh send mods/gpt
	fi
else
	echo "Ingen nye godkjente rom eller objekter denne runden."
fi

# 5. Ordre og status tilbake. Er ingenting nytt kommet inn og ingen ny beskjed gitt, står
#    ORDRE.md som før, så beskjeder ChatGPT ikke har lest ennå, ikke forsvinner.
status_after="$(sha256sum work/gpt/status.csv 2>/dev/null || true)"
if [ "$status_before" = "$status_after" ] && [ "${#BESKJED[@]}" -eq 0 ] && [ -f work/gpt/ORDRE.md ]; then
	echo "Ingen nye leveranser og ingen ny beskjed. ORDRE.md står som før."
	exit 0
fi
zakhd gpt-ordre "${BESKJED[@]}"
tools/gpt_gren.sh send
echo "Runden er ferdig. Rapport: work/gpt/RAPPORT.md, ordre: work/gpt/ORDRE.md"
