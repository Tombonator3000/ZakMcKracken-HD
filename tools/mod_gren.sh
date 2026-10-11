#!/usr/bin/env bash
# Publiserer eller henter den ferdige HD-modden via grenen hd-mod.
#
#   tools/mod_gren.sh send [modmappe]   Legger mods/gpt (standard) i grenen hd-mod som én commit og pusher
#   tools/mod_gren.sh hent [modmappe]   Henter grenen hd-mod til mods/gpt (standard)
#
# Grenen inneholder bare siste versjon (én commit som erstattes), så repoet ikke vokser for hver runde.
# Kjør spillet etterpå med: engine/run.sh gpt
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
BRANCH=hd-mod
MOD="${2:-$ROOT/mods/gpt}"

case "${1:-}" in
send)
	[ -f "$MOD/mod.json" ] || { echo "Fant ikke $MOD/mod.json. Bygg modden først."; exit 1; }
	TMP="$(mktemp -d "$ROOT/work/.mod-gren.XXXXXX")"
	trap 'rm -rf "$TMP"' EXIT
	git -C "$TMP" init -q
	git -C "$TMP" checkout -q -b "$BRANCH"
	cp -r "$MOD"/. "$TMP/"
	(cd "$TMP" && find . -path ./.git -prune -o -type f -print | sort | sed 's|^\./||' | grep -v '^SHA256SUMS$' | xargs sha256sum > SHA256SUMS)
	printf '# hd-mod\n\nSiste HD-mod for Zak McKracken HD Remake. Hentes med tools/mod_gren.sh hent. Spillet og grafikken tilhører Disney/Lucasfilm.\n' > "$TMP/README.md"
	git -C "$TMP" add -A
	git -C "$TMP" -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -q -m "HD-mod $(date '+%Y-%m-%d %H:%M')"
	git -C "$TMP" push -q -f "$(git -C "$ROOT" remote get-url origin)" "$BRANCH:$BRANCH"
	echo "Modden er publisert i grenen $BRANCH ($(du -sh "$MOD" | cut -f1))."
	;;
hent)
	git -C "$ROOT" fetch -q --depth 1 origin "+refs/heads/$BRANCH:refs/remotes/origin/$BRANCH"
	rm -rf "$MOD"
	mkdir -p "$MOD"
	git -C "$ROOT" archive "refs/remotes/origin/$BRANCH" | tar -x -C "$MOD"
	(cd "$MOD" && sha256sum --quiet -c SHA256SUMS)
	echo "Modden er hentet til $MOD og sjekksummene stemmer. Start med: engine/run.sh $(basename "$MOD")"
	;;
*)
	echo "Bruk: tools/mod_gren.sh send|hent [modmappe]"
	exit 1
	;;
esac
