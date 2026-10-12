#!/usr/bin/env python3
"""Lager et lesbart lag over de dekompilerte skriptene i Zak McKracken (FM-Towns).

Bruk (fra roten av repoet, etter tools/dekompiler_skript.py):
    python3 tools/skriptoversikt.py                  # leser work/skript, skriver til work/skript
    python3 tools/skriptoversikt.py --skript work/skript --extract work/extract

Leser utskriften fra descumm (work/skript), objekter.tsv og, hvis det finnes, uttrekket
(work/extract/rooms.json og costumes.json). Skriver til samme mappe som skriptene, fordi
alt er laget fra spillet og skal holdes utenfor git:

  ROM.md                 én del per rom: mål, objekter med navn og bilde, skript, hvilke rom
                         rommet leder til og kommer fra, figurer og kostymer, antall replikker
  REPLIKKER.md           all tekst spillet skriver (print og printEgo), per rom og skript, med
                         hvem som snakker der skriptene sier det
  rom-koblinger.tsv      fra rom, til rom, hvordan (loadRoom eller loadRoomWithEgo) og skriptfil
  kostymer-i-rom.tsv     kostyme, rom og hvordan skriptene viser det (ActorOps, loadCostume)

Bare tall som står rett i skriptene, telles. Rombytter og kostymer som går gjennom variabler
(for eksempel Var[314] for rommet en figur sist var i) er ikke med, og står som et antall i ROM.md.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINJE = re.compile(r"^\[[0-9A-F]{4,}\] \([0-9A-F*]{2}\) ?(.*)$")
TALL = re.compile(r"^-?\d+$")


# ---------------------------------------------------------------- tolking av utskriften

def _kall(tekst: str, navn: str) -> list[str]:
    """Argumentlistene til alle kall av navn( ... ) i en linje, med parenteser og strenger tatt hensyn til."""
    ut = []
    i = 0
    while True:
        j = tekst.find(navn + "(", i)
        if j < 0:
            return ut
        if j > 0 and (tekst[j - 1].isalnum() or tekst[j - 1] in "_."):
            i = j + 1
            continue
        k = j + len(navn) + 1
        dybde, streng = 1, False
        start = k
        while k < len(tekst) and dybde:
            c = tekst[k]
            if streng:
                if c == '"':
                    streng = False
            elif c == '"':
                streng = True
            elif c in "([":
                dybde += 1
            elif c in ")]":
                dybde -= 1
            k += 1
        ut.append(tekst[start:k - 1])
        i = k


def _del_argumenter(a: str) -> list[str]:
    deler, dybde, streng, start = [], 0, False, 0
    for k, c in enumerate(a):
        if streng:
            if c == '"':
                streng = False
        elif c == '"':
            streng = True
        elif c in "([":
            dybde += 1
        elif c in ")]":
            dybde -= 1
        elif c == "," and dybde == 0:
            deler.append(a[start:k].strip())
            start = k + 1
    deler.append(a[start:].strip())
    return deler


def lesbar_tekst(uttrykk: str) -> str:
    """Text("Hei" + newline() + "du") -> 'Hei / du'. Funksjoner blir korte merker i hakeparentes."""
    deler = []
    i = 0
    while i < len(uttrykk):
        c = uttrykk[i]
        if c == '"':
            j = uttrykk.index('"', i + 1)
            deler.append(uttrykk[i + 1:j])
            i = j + 1
        elif c.isalpha():
            m = re.match(r"([A-Za-z]+)\(([^()]*(?:\([^()]*\)[^()]*)*)\)", uttrykk[i:])
            if not m:
                i += 1
                continue
            f, arg = m.group(1), m.group(2)
            deler.append({"newline": " / ", "wait": " ", "keepText": "", "getName": f"[navn {arg}]",
                          "getInt": f"[tall {arg}]", "getVerb": f"[verb {arg}]",
                          "getString": f"[tekst {arg}]"}.get(f, f"[{f}]"))
            i += m.end()
        else:
            i += 1
    tekst = "".join(deler).replace("^", "...").rstrip("@")
    return re.sub(r"@+", "", tekst).strip()


def tekst_i_print(argumenter: str) -> str | None:
    t = _kall(argumenter, "Text")
    if not t:
        return None
    s = lesbar_tekst(t[0])
    return s or None


# ---------------------------------------------------------------- innsamling

def les_objekter(skript: Path) -> dict[int, list[dict]]:
    per_rom: dict[int, list[dict]] = defaultdict(list)
    f = skript / "objekter.tsv"
    if not f.exists():
        return per_rom
    for linje in f.read_text(encoding="utf-8").splitlines():
        if linje.startswith("#") or not linje.strip():
            continue
        nr, rom, x, y, w, h, bilde, verb, navn = (linje.split("\t") + [""] * 9)[:9]
        per_rom[int(rom)].append({"nr": int(nr), "x": int(x), "y": int(y), "w": int(w), "h": int(h),
                                  "bilde": bilde == "ja", "verb": verb, "navn": navn})
    return per_rom


def skriptfiler(skript: Path):
    """(rom eller None for globale, sti) for alle skriptfilene."""
    for f in sorted((skript / "globale").glob("*.txt")):
        yield None, f
    for d in sorted(skript.glob("rom_*")):
        if d.is_dir():
            rom = int(d.name.split("_")[1])
            for f in sorted(d.glob("*.txt")):
                yield rom, f


def samle(skript: Path) -> dict:
    data = {
        "replikker": defaultdict(list),     # rom (0 = globale) -> [(fil, taler, tekst)]
        "koblinger": [],                    # (fra, til, hvordan, fil)
        "variabel_bytter": Counter(),       # rom -> antall rombytter gjennom variabler
        "kostymer": [],                     # (kostyme, rom, hvordan, fil)
        "navn": defaultdict(dict),          # rom -> skuespiller -> navn (ActorOps Name)
        "figurer_inn": defaultdict(set),    # rom -> skuespillere satt inn i rommet (putActorInRoom)
        "skript": Counter(),                # rom -> antall skriptfiler
    }
    for rom, f in skriptfiler(skript):
        nokkel = rom if rom is not None else 0
        data["skript"][nokkel] += 1
        filnavn = f"{f.parent.name}/{f.name}"
        for linje in f.read_text(encoding="utf-8", errors="replace").splitlines():
            m = LINJE.match(linje)
            if not m:
                continue
            kode = m.group(1).strip()
            for a in _kall(kode, "ActorOps"):
                deler = _del_argumenter(a)
                aktor = deler[0] if deler else ""
                for n in _kall(a, "Name"):
                    s = n.strip().strip('"').rstrip("@")
                    if s and TALL.match(aktor):
                        data["navn"][nokkel].setdefault(int(aktor), s)
                for c in _kall(a, "Costume"):
                    if TALL.match(c.strip()) and rom is not None:
                        data["kostymer"].append((int(c), rom, f"ActorOps({aktor})", filnavn))
            for c in _kall(kode, "Resource.loadCostume"):
                if TALL.match(c.strip()) and rom is not None:
                    data["kostymer"].append((int(c), rom, "loadCostume", filnavn))
            for a in _kall(kode, "putActorInRoom"):
                deler = _del_argumenter(a)
                if len(deler) == 2 and TALL.match(deler[1]) and TALL.match(deler[0]):
                    data["figurer_inn"][int(deler[1])].add(int(deler[0]))
            for a in _kall(kode, "loadRoomWithEgo"):
                deler = _del_argumenter(a)
                if len(deler) >= 2 and TALL.match(deler[1]):
                    data["koblinger"].append((nokkel, int(deler[1]), "loadRoomWithEgo", filnavn))
                else:
                    data["variabel_bytter"][nokkel] += 1
            for a in _kall(kode, "loadRoom"):
                if TALL.match(a.strip()):
                    if int(a) != 0:
                        data["koblinger"].append((nokkel, int(a), "loadRoom", filnavn))
                else:
                    data["variabel_bytter"][nokkel] += 1
            for a in _kall(kode, "printEgo"):
                t = tekst_i_print(a)
                if t:
                    data["replikker"][nokkel].append((filnavn, "spilleren", t))
            for a in _kall(kode, "print"):
                deler = _del_argumenter(a)
                t = tekst_i_print(a)
                if not t:
                    continue
                hvem = deler[0] if deler else "?"
                data["replikker"][nokkel].append((filnavn, hvem, t))
    return data


def _romliste(rom: set) -> str:
    """Romnumre som tekst; 0 er de globale skriptene (de gjelder i alle rom)."""
    if not rom:
        return "ingen faste"
    return ", ".join("globale skript" if r == 0 else str(r) for r in sorted(rom))


def taler(hvem: str, navn_rom: dict[int, str], navn_glob: dict[int, str]) -> str:
    if hvem == "spilleren":
        return "spilleren"
    if hvem == "255":
        return "melding"
    if hvem == "VAR_EGO":
        return "spilleren"
    if TALL.match(hvem):
        n = int(hvem)
        navn = navn_rom.get(n) or navn_glob.get(n)
        return f"{navn} ({n})" if navn else f"skuespiller {n}"
    return f"skuespilleren i {hvem}"


# ---------------------------------------------------------------- utskrift

def skriv(skript: Path, extract: Path | None) -> dict:
    data = samle(skript)
    objekter = les_objekter(skript)
    rooms = {}
    costumes = {}
    if extract and (extract / "rooms.json").exists():
        rooms = json.loads((extract / "rooms.json").read_text())["rooms"]
    if extract and (extract / "costumes.json").exists():
        costumes = json.loads((extract / "costumes.json").read_text())
    navn_glob = data["navn"].get(0, {})

    fra: dict[int, set] = defaultdict(set)
    til: dict[int, set] = defaultdict(set)
    for a, b, _, _ in data["koblinger"]:
        til[a].add(b)
        fra[b].add(a)
    kostymer_rom: dict[int, set] = defaultdict(set)
    rom_kostymer: dict[int, set] = defaultdict(set)
    for c, r, _, _ in data["kostymer"]:
        kostymer_rom[c].add(r)
        rom_kostymer[r].add(c)
    for c, meta in costumes.items():
        rom_kostymer[int(meta["room"])].add(int(c))

    alle_rom = sorted({int(k) for k in rooms} | {r for r in data["skript"] if r} | set(objekter))
    linjer = [
        "# Rommene i Zak McKracken (FM-Towns)",
        "",
        "Laget med tools/skriptoversikt.py fra de dekompilerte skriptene og uttrekket. Bare tall som står",
        "rett i skriptene er med; rombytter gjennom variabler står som et antall. Kostymer: de skriptene",
        "i rommet setter med ActorOps eller laster, og de som ligger i rommets fil.",
        "",
    ]
    for r in alle_rom:
        meta = rooms.get(str(r), {})
        objs = sorted(objekter.get(r, []), key=lambda o: o["nr"])
        mål = f"{meta['width']} x {meta['height']}" if meta.get("width") else "ingen grafikk"
        linjer += [f"## Rom {r}", "",
                   f"- Mål: {mål}" + (", z-plan" if meta.get("zplane") else ""),
                   f"- Skriptfiler: {data['skript'].get(r, 0)}, replikker: {len(data['replikker'].get(r, []))}",
                   f"- Leder til: {_romliste(til[r])}"
                   + (f" (pluss {data['variabel_bytter'][r]} bytter gjennom variabler)" if data["variabel_bytter"][r] else ""),
                   f"- Kommer fra: {_romliste(fra[r])}",
                   f"- Kostymer: {', '.join(map(str, sorted(rom_kostymer[r]))) or 'ingen'}"]
        navn_rom = data["navn"].get(r, {})
        figurer = sorted(data["figurer_inn"].get(r, set()))
        if figurer or navn_rom:
            linjer.append("- Figurer: " + ", ".join(
                taler(str(a), navn_rom, navn_glob) for a in sorted(set(figurer) | set(navn_rom))))
        if objs:
            med_navn = [o for o in objs if o["navn"]]
            linjer.append(f"- Objekter: {len(objs)} ({sum(o['bilde'] for o in objs)} med eget bilde, "
                          f"{len(med_navn)} med navn)")
            linjer += ["", "| Objekt | Navn | Plass | Mål | Bilde | Verb |", "| ---: | --- | --- | --- | --- | --- |"]
            for o in objs:
                linjer.append(f"| {o['nr']} | {o['navn']} | {o['x']},{o['y']} | {o['w']} x {o['h']} | "
                              f"{'ja' if o['bilde'] else 'nei'} | {o['verb']} |")
        linjer.append("")
    (skript / "ROM.md").write_text("\n".join(linjer) + "\n", encoding="utf-8")

    rep = ["# Replikker og meldinger", "",
           "All tekst skriptene skriver med print og printEgo. \"spilleren\" er figuren som styres; "
           "\"melding\" er meldingslinjen (skuespiller 255). Hakeparentes er tekst spillet setter inn.", ""]
    antall = 0
    for r in sorted(data["replikker"]):
        rader = data["replikker"][r]
        if not rader:
            continue
        rep += [f"## {'Globale skript' if r == 0 else f'Rom {r}'}", ""]
        forrige = None
        navn_rom = data["navn"].get(r, {})
        for fil, hvem, t in rader:
            if fil != forrige:
                rep.append(f"### {fil}")
                forrige = fil
            rep.append(f"- {taler(hvem, navn_rom, navn_glob)}: {t}")
            antall += 1
        rep.append("")
    (skript / "REPLIKKER.md").write_text("\n".join(rep) + "\n", encoding="utf-8")

    with open(skript / "rom-koblinger.tsv", "w", encoding="utf-8") as fh:
        fh.write("# fra\ttil\thvordan\tskript\n")
        for a, b, hvordan, fil in sorted(set(data["koblinger"])):
            fh.write(f"{a}\t{b}\t{hvordan}\t{fil}\n")
    with open(skript / "kostymer-i-rom.tsv", "w", encoding="utf-8") as fh:
        fh.write("# kostyme\trom\thvordan\tskript\n")
        for c, r, hvordan, fil in sorted(set(data["kostymer"])):
            fh.write(f"{c}\t{r}\t{hvordan}\t{fil}\n")
    return {"rom": len(alle_rom), "replikker": antall, "koblinger": len(set(data["koblinger"])),
            "kostymer": len(set(data["kostymer"])),
            "variabel_bytter": sum(data["variabel_bytter"].values())}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Lesbar oversikt over de dekompilerte skriptene i Zak McKracken.")
    ap.add_argument("--skript", type=Path, default=ROOT / "work" / "skript")
    ap.add_argument("--extract", type=Path, default=ROOT / "work" / "extract")
    a = ap.parse_args(argv)
    if not (a.skript / "OVERSIKT.md").exists():
        sys.exit(f"Fant ikke {a.skript / 'OVERSIKT.md'}. Kjør tools/dekompiler_skript.py først.")
    n = skriv(a.skript, a.extract if a.extract.exists() else None)
    print(f"{n['rom']} rom, {n['replikker']} replikker, {n['koblinger']} faste rombytter "
          f"({n['variabel_bytter']} gjennom variabler), {n['kostymer']} kostymebruk -> {a.skript}")
    print("Filer: ROM.md, REPLIKKER.md, rom-koblinger.tsv, kostymer-i-rom.tsv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
