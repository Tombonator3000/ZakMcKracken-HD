#!/usr/bin/env python3
"""Måler hvor mange ikoner et dynamisk verbhjul trenger per objekt.

Leser verbtabellene og objektkoden i de dekompilerte skriptene (work/skript, fra
tools/dekompiler_skript.py) og klassene i indeksen (game/00.LFL). Regnes:

1. I dag: ett ikon per verb med egen kode (uten Walk to, What is og 255).
2. Lik kode: verb som hopper til samme kode blir ett ikon, men ikke når koden
   (eller et skript den starter) leser hvilket verb som ble valgt (Var[52],
   Var[116], eller Local[1] i objektkoden), ikke Give (trenger alltid en
   mottaker) og ikke Use når objektet har preposisjonsklasse 1 til 4 (setningen
   venter da på et objekt til).
3. Tilstand: Open og Close blir ett ikon når koden følger spillets egen regel
   (tilstand 0 lukket, 1 åpen, som globalt skript 31 og 32). Det samme for
   Turn on og Turn off.

Bruk: python3 tools/verbhjul_dynamisk.py [--skript work/skript] [--game game]
          [--tsv work/verbhjul-dynamisk.tsv]
TSV-filen er laget fra spillfilene og hører hjemme i work/, ikke i main.
"""
from __future__ import annotations

import argparse
import collections
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "pipeline"))
from zakhd.lfl import les_indeks  # noqa: E402

NAVN = {1: "Push", 2: "Open", 4: "Put on", 5: "Turn on", 6: "Pull", 7: "Close", 8: "Pick up",
        9: "Take off", 10: "Turn off", 11: "Give", 12: "Read", 14: "Use", 15: "Buy",
        16: "Sell", 17: "Teleport to"}
UTENFOR = (3, 13, 255)          # Walk to, What is, koden for alle andre verb
VERBREF = re.compile(r"Var\[(52|116)\]")
KALL = re.compile(r"(?:startScript|chainScript)\((\d+),")
LINJE = re.compile(r"\[([0-9A-F]{4})\] \(..\) ?(.*)")
PAR = ((2, 7), (5, 10))          # (Open, Close), (Turn on, Turn off)


class Objekt:
    def __init__(self, fil: Path):
        tekst = fil.read_text(encoding="utf-8").splitlines()
        m = re.match(r'; Objekt (\d+) "(.*)" i rom (\d+)', tekst[0])
        self.nr, self.navn, self.rom = int(m.group(1)), m.group(2), int(m.group(3))
        tabell = tekst[1].split(":", 1)[1]
        self.tabell = [(int(v), int(o, 16)) for v, o in re.findall(r"(\d+): 0x([0-9A-F]+)", tabell)]
        self.kode = []
        for linje in tekst:
            mm = LINJE.match(linje)
            if mm:
                self.kode.append((int(mm.group(1), 16), mm.group(2).strip()))
        self.starter = sorted({o for _, o in self.tabell})

    def bit(self, offset: int) -> list[str]:
        """Koden fra offset til neste inngang i verbtabellen."""
        neste = [x for x in self.starter if x > offset]
        slutt = neste[0] if neste else 1 << 30
        return [t for a, t in self.kode if offset <= a < slutt]


def les_skript(rot: Path, rom: int, nr: int) -> str:
    for sti in (rot / "globale" / f"scrp_{nr:03d}.txt", rot / f"rom_{rom:02d}" / f"lokal_{nr}.txt"):
        if sti.exists():
            return sti.read_text(encoding="utf-8")
    return ""


def leser_verbet(rot: Path, rom: int, tekst: str, dybde: int = 0, sett: set | None = None) -> bool:
    sett = set() if sett is None else sett
    if VERBREF.search(tekst) or (dybde == 0 and "Local[1]" in tekst):
        return True
    if dybde >= 3:
        return False
    for n in map(int, KALL.findall(tekst)):
        if n in sett or n in (14, 18, 19):      # standardsvaret og oppryddingen
            continue
        sett.add(n)
        if leser_verbet(rot, rom, les_skript(rot, rom, n), dybde + 1, sett):
            return True
    return False


def foelger_tilstand(ob: Objekt, a: int, b: int, verb: dict[int, int]) -> bool:
    ta, tb = " ".join(ob.bit(verb[a])), " ".join(ob.bit(verb[b]))
    return ((f"getState({ob.nr}) == 0" in ta or f"startScript(31,[{ob.nr}])" in ta) and
            (f"getState({ob.nr}) == 1" in tb or f"startScript(32,[{ob.nr}])" in tb))


def ikoner(ob: Objekt, rot: Path, klasser: list[int]):
    """Ikonene som lister av verb, og parene som velges etter tilstand."""
    verb = [(v, o) for v, o in ob.tabell if v not in UTENFOR]
    prep = klasser[ob.nr] & 0xF if ob.nr < len(klasser) else 0
    grupper: dict[tuple, list[int]] = {}
    for v, o in verb:
        egen = v == 11 or (v == 14 and prep) or leser_verbet(rot, ob.rom, "\n".join(ob.bit(o)))
        grupper.setdefault((o, v) if egen else (o,), []).append(v)
    vo = dict(verb)
    par = [(a, b) for a, b in PAR
           if a in vo and b in vo and vo[a] != vo[b] and foelger_tilstand(ob, a, b, vo)]
    return list(grupper.values()), par


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skript", type=Path, default=REPO / "work" / "skript")
    ap.add_argument("--game", type=Path, default=REPO / "game")
    ap.add_argument("--tsv", type=Path)
    a = ap.parse_args()
    if not (a.skript / "globale").is_dir():
        print(f"Fant ikke {a.skript}; kjør tools/dekompiler_skript.py først", file=sys.stderr)
        return 1
    klasser = les_indeks(a.game / "00.LFL").klasser
    objekter = [Objekt(f) for f in sorted(a.skript.glob("rom_*/obj_*_verb.txt"))]

    idag, lik, tilst = collections.Counter(), collections.Counter(), collections.Counter()
    delt = 0
    par_ok, par_ukjent = collections.Counter(), collections.Counter()
    store, rader = [], []
    for ob in objekter:
        verb = [(v, o) for v, o in ob.tabell if v not in UTENFOR]
        if not verb:
            continue
        g, par = ikoner(ob, a.skript, klasser)
        idag[len(verb)] += 1
        lik[len(g)] += 1
        tilst[len(g) - len(par)] += 1
        if len({o for _, o in verb}) != len(g):
            delt += 1
        vo = dict(verb)
        for x, y in PAR:
            if x in vo and y in vo and vo[x] != vo[y]:
                (par_ok if (x, y) in par else par_ukjent)[NAVN[x] + "/" + NAVN[y]] += 1
        if len(g) - len(par) > 4:
            store.append((ob, g))
        rader.append((ob, g, par))

    def linje(c):
        return ", ".join(f"{k}: {c[k]}" for k in sorted(c))

    print(f"Objekter med verbkode: {sum(idag.values())}")
    print(f"I dag (ett ikon per verb): {linje(idag)}")
    print(f"Lik kode slått sammen: {linje(lik)}  (grupper delt fordi koden leser verbet, Give eller Use med preposisjon: {delt} objekter)")
    print(f"Pluss Open/Close og Turn on/Turn off etter tilstand: {linje(tilst)}")
    print(f"Par som følger tilstandsregelen: {dict(par_ok)}; ikke påvist: {dict(par_ukjent)}")
    print(f"Over fire ikoner: {len(store)}")
    for ob, g in store:
        print(f"  rom {ob.rom}, objekt {ob.nr} {ob.navn}: " + " | ".join("/".join(NAVN[v] for v in x) for x in g))
    if a.tsv:
        with a.tsv.open("w", encoding="utf-8") as f:
            f.write("# objekt\trom\tikoner\tgrupper\ttilstandspar\tnavn\n")
            for ob, g, par in rader:
                f.write(f"{ob.nr}\t{ob.rom}\t{len(g) - len(par)}\t"
                        + ";".join(",".join(map(str, x)) for x in g) + "\t"
                        + ";".join(f"{x},{y}" for x, y in par) + f"\t{ob.navn}\n")
        print(f"Skrev {a.tsv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
