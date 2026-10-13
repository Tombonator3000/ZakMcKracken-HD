#!/usr/bin/env python3
"""Regner ut ikonene i det dynamiske verbhjulet, objekt for objekt.

Leser verbtabellene og objektkoden i de dekompilerte skriptene (work/skript, fra
tools/dekompiler_skript.py) og klassene i indeksen (game/00.LFL).

1. Lik kode: verb som hopper til samme kode blir ett ikon, men ikke når koden
   (eller et skript den starter) leser hvilket verb som ble valgt (Var[52],
   Var[116], eller Local[1] i objektkoden), ikke Give (trenger alltid en
   mottaker) og ikke Use når objektet har preposisjonsklasse 1 til 4 (setningen
   venter da på et objekt til).
2. Tilstand: Open og Close blir ett ikon når koden følger spillets egen regel
   (tilstand 0 lukket, 1 åpen, som globalt skript 31 og 32). Det samme for
   Turn on og Turn off. Noen bruker klasse 6 i stedet (lampen i rom 6).
3. Regler for hånd (HAAND) for objektene der det over ikke er nok, lest i
   skriptene. Hver regel har en kommentar med kilden.

Regelen per objekt skrives som en kort tekst som motoren leser:
  g=2,6;1,7;14    ikonene: verbene i hver gruppe hopper til samme kode
  p=2/7:s         par: vis bare ett av ikonene med 2 og 7; det med 7 når
                  betingelsen er sann. s = objektets tilstand er ikke 0,
                  s92 = tilstanden til objekt 92, c6 = klasse 6 er satt,
                  C6 = klasse 6 er ikke satt, v222=14|16 = Var[222] er 14 eller 16,
                  b143.0 = bit 0 i Var[143] er satt. Flere med + er "eller".
  i=11            verbene vises bare når hjulet åpnes i inventaret
  r=8             verbene vises bare når hjulet åpnes i rommet
  x=11            verbene vises aldri (bare en replikk; se kommentaren)

Bruk: python3 tools/verbhjul_dynamisk.py [--skript work/skript] [--game game]
          [--tsv work/verbhjul-dynamisk.tsv] [--cpp engine/scummvm/engines/scumm/verbhjul_zak.h]
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
# Lesing av verbet (ikke skriving som "Var[52] = 0")
VERBLES = re.compile(r"Var\[(52|116)\](?!\s*=[^=])")
LOCAL1LES = re.compile(r"Local\[1\](?!\s*=[^=])")
KALL = re.compile(r"(?:startScript|chainScript)\((\d+),")
LINJE = re.compile(r"\[([0-9A-F]{4})\] \(..\) ?(.*)")
PAR = ((2, 7), (5, 10))          # (Open, Close), (Turn on, Turn off)

LISENS = """/* ScummVM - Graphic Adventure Engine
 *
 * ScummVM is the legal property of its developers, whose names
 * are too numerous to list here. Please refer to the COPYRIGHT
 * file distributed with this source distribution.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

"""

# Regler lest for hånd i skriptene. "+" foran betyr: legg til den utregnede regelen.
HAAND = {
    # Sushi i fiskebollen (rom 1): Put on setter Var[222] til 14 eller 16 (bollen på hodet),
    # Take off setter den tilbake. Give bare fra inventaret, Pick up bare i rommet.
    14: "g=4;8;9;11;14 p=4/9:v222=14|16 i=11 r=8",
    # Kommoden (rom 1) sender verbet videre til skuffen 92 (startObject(92,Var[52])),
    # der Open og Pull har samme kode, og Push og Close.
    91: "g=2,6;1,7;14 p=2/7:s92",
    # Våtdrakten (rom 7): globalt skript 75 setter klasse 6 når den tas på. Buy bare i butikken
    # (verbet er bare på der). Give bare fra inventaret.
    39: "g=4;9;11;12;15 p=4/9:c6 i=11",
    # Oksygentanken (rom 11): Put on setter Var[219] til 15, Take off til 11.
    50: "g=4,14;8;9;11;12 p=4/9:v219=15 i=11 r=8",
    # Mikrobølgeovnen (rom 11): døren er tilstanden til 260 (lokalt skript 224 og 225),
    # om den går er tilstanden til 261 (lokalt skript 206 og 223).
    260: "g=2;5;7;10;14 p=2/7:s p=5/10:s261",
    # Boom-boksen (globalt skript 129): på betyr at den tar opp (klasse 6 satt) eller spiller av
    # (Var[143] bit 0); Turn off stopper begge. Give gir bare "No way, it's mine!" og vises ikke;
    # Read (merket) bare i inventaret, Pick up bare i rommet.
    71: "g=2;5;8;10;11;12;14 p=5/10:c6+b143.0 x=11 i=12 r=8",
    # Døren 247 (rom 11) åpner og lukker døren 246 (lokalt skript 221 og 222).
    247: "+p=2/7:s246",
    # Skapet 367 (rom 18) sender Open og Close videre til skapdøren 368.
    367: "+p=2/7:s368",
    # Verktøykassen (globalt skript 75): Open når klasse 6 er satt (lukket), Close når den ikke er det.
    34: "+p=2/7:C6",
    # Koffertene 258 og 259 (rom 11) sender verbet til 257, som svarer det samme på alle fire.
    258: "g=2,6,7,8",
    259: "g=2,6,7,8",
    # Fallskjermen (rom 40): Put on gir bare "I'm already wearing it." og vises ikke.
    77: "+x=4",
    # Klasse 6 som av og på uten sjekk først; det skjulte verbet gjør det samme en gang til
    # (lyset regnes ut på nytt, animasjonen eller lyden startes igjen):
    # lighteren (49) og lommelykten (69) setter klassen når de tennes (globalt skript 162),
    # radioen (492) likeså, katteklokken (95) fjerner den når den startes (rom 1 starter
    # animasjonen når klassen ikke er satt).
    49: "+p=5/10:c6",
    69: "+p=5/10:c6",
    492: "+p=5/10:c6",
    95: "+p=5/10:C6",
    # Setet (rom 2): Open sjekker tilstanden; Close setter bare tilstanden 0 og stopper skript 204,
    # som gjør det samme når man går fra setet. Ingenting å gjøre for Close når det er lukket.
    119: "+p=2/7:s",
    # Skriveunderlaget (rom 6): Open og Close setter bare tilstanden.
    175: "+p=2/7:s",
    # Vasken i rom 11: Turn on sjekker tilstanden for lyden og starter skript 226 (den renner over);
    # Turn off stopper det og setter tilstanden 0. Ingenting nytt å gjøre for det skjulte verbet.
    242: "+p=5/10:s",
}


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
    sti = rot / "globale" / f"scrp_{nr:03d}.txt" if nr < 200 else rot / f"rom_{rom:02d}" / f"lokal_{nr}.txt"
    return sti.read_text(encoding="utf-8") if sti.exists() else ""


def kalte(rot: Path, rom: int, tekst: str) -> list[str]:
    """Skriptene koden starter, to ledd ned. Lokale skript (200 og over) bare fra
    objektkoden selv; fra et globalt skript vet vi ikke hvilket rom som gjelder."""
    ut, sett = [], set()
    kø = [(tekst, 0)]
    while kø:
        t, d = kø.pop()
        for n in map(int, KALL.findall(t)):
            if n in sett or n in (14, 18, 19) or d >= 2 or (n >= 200 and d > 0):
                continue
            sett.add(n)
            s = les_skript(rot, rom, n)
            ut.append(s)
            kø.append((s, d + 1))
    return ut


def leser_verbet(rot: Path, ob: Objekt, offset: int) -> bool:
    tekst = "\n".join(ob.bit(offset))
    if VERBLES.search(tekst) or LOCAL1LES.search(tekst):
        return True
    return any(VERBLES.search(s) for s in kalte(rot, ob.rom, tekst))


def tilstandsregel(rot: Path, ob: Objekt, a: int, b: int, vo: dict[int, int]) -> str | None:
    """Betingelsen for paret a/b når koden følger tilstand 0/1 eller klasse 6."""
    def alt(v):
        t = "\n".join(ob.bit(vo[v]))
        return "\n".join([t] + kalte(rot, ob.rom, t))
    ta, tb = alt(a), alt(b)
    meg = rf"(?:{ob.nr}|VAR_ME|Var\[50\])"
    # Begge sider må sjekke tilstanden før de gjør noe (eller bruke skript 31 og 32, som gjør det),
    # så verbet som skjules ikke ville gjort noe i den tilstanden. Bare setState er ikke nok:
    # telefonsvareren spiller av nye beskjeder med Turn on også når den står på.
    a_til = re.search(rf"getState\({meg}\) == 0|startScript\(31,\[{meg}\]\)", ta)
    b_til = re.search(rf"getState\({meg}\) == 1|startScript\(32,\[{meg}\]\)", tb)
    if a_til and b_til:
        return "s"
    # Klasse 6 som av og på, også bare når begge sider sjekker den først (lampen i rom 6)
    if re.search(rf"classOfIs\({meg},\[6\]\)", ta) and re.search(rf"classOfIs\({meg},\[134\]\)", tb):
        return "c6"
    if re.search(rf"classOfIs\({meg},\[134\]\)", ta) and re.search(rf"classOfIs\({meg},\[6\]\)", tb):
        return "C6"
    return None


def regel(ob: Objekt, rot: Path, klasser: list[int]) -> str | None:
    """Regelen for objektet som tekst, eller None når det ikke har verb til hjulet."""
    verb = [(v, o) for v, o in ob.tabell if v not in UTENFOR]
    hånd = HAAND.get(ob.nr)
    if hånd and not hånd.startswith("+"):
        return hånd
    if not verb:
        return None
    prep = klasser[ob.nr] & 0xF if ob.nr < len(klasser) else 0
    grupper: dict[tuple, list[int]] = {}
    for v, o in verb:
        egen = v == 11 or (v == 14 and prep) or leser_verbet(rot, ob, o)
        grupper.setdefault((o, v) if egen else (o,), []).append(v)
    deler = ["g=" + ";".join(",".join(map(str, g)) for g in grupper.values())]
    vo = dict(verb)
    for a, b in PAR:
        if a in vo and b in vo and vo[a] != vo[b]:
            betingelse = tilstandsregel(rot, ob, a, b, vo)
            if betingelse:
                deler.append(f"p={a}/{b}:{betingelse}")
    if hånd:
        deler.append(hånd[1:])
    return " ".join(deler)


def tolk(spec: str):
    """Teksten tilbake til grupper, par og filtre (som motoren gjør)."""
    g, par, inv, rom, aldri = [], [], set(), set(), set()
    for del_ in spec.split():
        k, v = del_.split("=", 1)
        if k == "g":
            g = [[int(x) for x in grp.split(",")] for grp in v.split(";")]
        elif k == "p":
            ab, bet = v.split(":", 1)
            a, b = map(int, ab.split("/"))
            par.append((a, b, bet))
        elif k in ("i", "r", "x"):
            {"i": inv, "r": rom, "x": aldri}[k].update(int(x) for x in v.split(","))
    return g, par, inv, rom, aldri


def ikoner(spec: str, i_inventaret: bool) -> int:
    """Hvor mange ikoner som vises (høyst, uansett tilstand)."""
    g, par, inv, rom, aldri = tolk(spec)
    skjult = set(aldri) | (rom if i_inventaret else inv)
    synlig = [grp for grp in g if any(v not in skjult for v in grp)]
    n = len(synlig)
    for a, b, _ in par:
        ga = next((i for i, grp in enumerate(synlig) if a in grp), None)
        gb = next((i for i, grp in enumerate(synlig) if b in grp), None)
        if ga is not None and gb is not None and ga != gb:
            n -= 1
    if i_inventaret and not any(11 in grp for grp in synlig) and 11 not in aldri:
        n += 1          # hjulet gir alltid Give for ting i inventaret
    return n


def inventarting(rot: Path) -> set[int]:
    """Objekter som kan havne i inventaret: pickupObject eller setOwnerOf til en figur i skriptene."""
    ut = set()
    for f in rot.glob("**/*.txt"):
        t = f.read_text(encoding="utf-8")
        m = re.match(r"; Objekt (\d+) ", t)
        if m:
            t = t.replace("VAR_ME", m.group(1))
        ut.update(int(x) for x in re.findall(r"pickupObject\((\d+)\)", t))
        ut.update(int(x) for x in re.findall(r"setOwnerOf\((\d+),(?:VAR_EGO|[1-4]|Local\[\d\]|Var\[\d+\])\)", t))
    return ut


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skript", type=Path, default=REPO / "work" / "skript")
    ap.add_argument("--game", type=Path, default=REPO / "game")
    ap.add_argument("--tsv", type=Path)
    ap.add_argument("--cpp", type=Path, help="tabellen for motoren (engines/scumm/verbhjul_zak.h)")
    a = ap.parse_args()
    if not (a.skript / "globale").is_dir():
        print(f"Fant ikke {a.skript}; kjør tools/dekompiler_skript.py først", file=sys.stderr)
        return 1
    klasser = les_indeks(a.game / "00.LFL").klasser
    objekter = [Objekt(f) for f in sorted(a.skript.glob("rom_*/obj_*_verb.txt"))]
    inv_ting = inventarting(a.skript)

    idag, rom_n, inv_n = collections.Counter(), collections.Counter(), collections.Counter()
    par_typer = collections.Counter()
    rader, store = [], []
    for ob in objekter:
        spec = regel(ob, a.skript, klasser)
        if not spec:
            continue
        verb = [v for v, _ in ob.tabell if v not in UTENFOR]
        idag[len(verb)] += 1
        # Inventaret bare for ting som kan havne der (kan plukkes opp, kjøpes eller gis til en figur)
        kan_eies = ob.nr in inv_ting or any(v in (8, 15) for v in verb)
        nr, ni = ikoner(spec, False), (ikoner(spec, True) if kan_eies else 0)
        rom_n[nr] += 1
        if kan_eies:
            inv_n[ni] += 1
        for _, _, bet in tolk(spec)[1]:
            par_typer[bet[0]] += 1
        if max(nr, ni) > 4:
            store.append((ob, spec, nr, ni))
        rader.append((ob, spec, nr, ni))

    def linje(c):
        return ", ".join(f"{k}: {c[k]}" for k in sorted(c))

    print(f"Objekter med verbkode: {sum(idag.values())}")
    print(f"I dag (ett ikon per verb): {linje(idag)}")
    print(f"Dynamisk, i rommet: {linje(rom_n)}")
    print(f"Dynamisk, i inventaret (med Give, {sum(inv_n.values())} ting som kan havne der): {linje(inv_n)}")
    print(f"Par etter tilstand (s), klasse (c, C) eller variabel (v): {dict(par_typer)}")
    print(f"Regler for hånd: {len(HAAND)}")
    print(f"Over fire ikoner: {len(store)}")
    for ob, spec, nr, ni in store:
        print(f"  rom {ob.rom}, objekt {ob.nr} {ob.navn}: {spec} (rom {nr}, inventar {ni})")
    if a.tsv:
        with a.tsv.open("w", encoding="utf-8") as f:
            f.write("# objekt\trom\tikoner_rom\tikoner_inventar\tregel\tnavn\n")
            for ob, spec, nr, ni in rader:
                f.write(f"{ob.nr}\t{ob.rom}\t{nr}\t{ni}\t{spec}\t{ob.navn}\n")
        print(f"Skrev {a.tsv}")
    if a.cpp:
        with a.cpp.open("w", encoding="utf-8") as f:
            f.write(LISENS +
                    "/*\n * Generated by tools/verbhjul_dynamisk.py in the ZakMcKracken-HD repository;\n"
                    " * do not edit by hand. The icons of the dynamic verb wheel for Zak McKracken\n"
                    " * FM-Towns, per object. The format is described in verbhjul.h.\n */\n\n"
                    "#ifndef SCUMM_VERBHJUL_ZAK_H\n#define SCUMM_VERBHJUL_ZAK_H\n\nnamespace Scumm {\n\n"
                    "struct VerbWheelRule {\n\tuint16 obj;\n\tconst char *spec;\n};\n\n"
                    "static const VerbWheelRule kZakVerbWheelRules[] = {\n")
            for ob, spec, _, _ in sorted(rader, key=lambda r: r[0].nr):
                f.write(f'\t{{ {ob.nr}, "{spec}" }},\n')
            f.write("\t{ 0, nullptr }\n};\n\n} // End of namespace Scumm\n\n#endif\n")
        print(f"Skrev {a.cpp} ({len(rader)} objekter)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
