#!/usr/bin/env python3
"""Sjekker at hunk-hodene i motorpatchene stemmer med innholdet.

`git apply` stoler på tallene i hodene (@@ -a,b +c,d @@). Er tallet for nye linjer for
lavt, legger den på bare så mange linjer og hopper over resten uten feilmelding. Det
skjedde 13. oktober 2026: en fletting i GitHub la sju linjer til i verbhjul.cpp og to i
verbhjul.h uten å endre tallene, og motoren bygget ikke lenger fra main.

Bruk:  python3 tools/sjekk_patcher.py [patch ...]   (standard: engine/patches/*.patch)
Feil gir kode 1. Rett feilen ved å lage patchene på nytt med tools/lag_patcher.sh.
"""
import re
import sys
from pathlib import Path

HUNK = re.compile(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def sjekk(path: Path) -> list[str]:
    feil = []
    lines = path.read_text(encoding="utf-8").split("\n")
    fil = "?"
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("diff --git"):
            fil = line.split()[-1][2:]
            i += 1
            continue
        m = HUNK.match(line)
        if not m:
            i += 1
            continue
        old_n = int(m.group(2) or 1)
        new_n = int(m.group(4) or 1)
        old = new = 0
        start = i + 1
        i += 1
        # Linjene i hunken: kontekst, fjernet, lagt til og «\ No newline at end of file».
        # Hunken slutter ved neste hode, neste fil eller en linje uten slikt prefiks.
        while i < len(lines):
            s = lines[i][:1]
            if s == " ":
                old += 1
                new += 1
            elif s == "-":
                old += 1
            elif s == "+":
                new += 1
            elif s == "\\":
                pass
            else:
                break
            i += 1
        if (old, new) != (old_n, new_n):
            feil.append(
                f"{path.name}: {fil} (linje {start}): hodet sier {old_n} gamle og {new_n} nye linjer, "
                f"hunken har {old} og {new}"
            )
    return feil


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    paths = [Path(a) for a in argv] or sorted((root / "engine" / "patches").glob("*.patch"))
    if not paths:
        print("Fant ingen patcher")
        return 1
    alle = []
    for p in paths:
        alle += sjekk(p)
    for f in alle:
        print(f)
    if alle:
        print(f"{len(alle)} hunk(er) med feil telling. Lag patchene på nytt med tools/lag_patcher.sh.")
        return 1
    print(f"Hunk-hodene stemmer i {len(paths)} patch(er).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
