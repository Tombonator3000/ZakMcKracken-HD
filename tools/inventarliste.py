#!/usr/bin/env python3
"""Lager docs/inventar.csv: alle tingene som kan havne i inventaret, med filnavnet til bildet.

En ting kan havne i inventaret når skriptene plukker den opp (pickupObject) eller gir den til en
figur (setOwnerOf), eller når den har Pick up eller Buy i verbtabellen. Samme regel som
tools/verbhjul_dynamisk.py bruker for inventaret i hjulet.

Bildet til en ting heter inventory/objNNN.png i HD-modden. Godkjente bilder legges i
grafikk/inventar/objNNN.png; `zakhd build-mod` tar dem med (pipeline/zakhd/modpack.py, build_ui).

Bruk:  python3 tools/inventarliste.py      (krever work/skript fra tools/dekompiler_skript.py)
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from verbhjul_dynamisk import inventarting  # noqa: E402


def main() -> int:
    skript = ROOT / "work" / "skript"
    tsv = skript / "objekter.tsv"
    if not tsv.exists():
        print("Fant ikke work/skript/objekter.tsv; kjør tools/dekompiler_skript.py først", file=sys.stderr)
        return 1
    eies = inventarting(skript)
    rader = []
    for linje in tsv.read_text(encoding="utf-8").splitlines():
        if linje.startswith("#") or not linje.strip():
            continue
        nr, rom, x, y, b, h, bilde, verb, navn = linje.split("\t")[:9]
        verbliste = {int(v) for v in verb.split(",") if v.strip().isdigit()}
        if int(nr) in eies or verbliste & {8, 15}:
            fil = f"obj{int(nr):03d}.png"
            ferdig = (ROOT / "grafikk" / "inventar" / fil).exists()
            rader.append([int(nr), navn, int(rom), "ja" if bilde == "ja" else "nei", fil,
                          "godkjent" if ferdig else "mangler"])
    rader.sort()
    ut = ROOT / "docs" / "inventar.csv"
    with ut.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["objekt", "navn", "rom", "bilde_i_rommet", "fil", "status"])
        w.writerows(rader)
    print(f"{len(rader)} ting som kan havne i inventaret -> {ut.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
