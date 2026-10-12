#!/usr/bin/env python3
"""Dekompilerer alle skriptene i Zak McKracken, FM-Towns (SCUMM v3) til tekst med descumm.

Bruk (fra roten av repoet):
    tools/bygg_descumm.sh                         # bygger descumm til work/scummvm-tools/descumm
    python3 tools/dekompiler_skript.py            # alle skript til work/skript/
    python3 tools/dekompiler_skript.py --descumm /sti/descumm --spill game --ut work/skript

descumm finnes slik: --descumm, ellers miljøvariabelen DESCUMM, ellers descumm i PATH,
ellers work/scummvm-tools/descumm (der tools/bygg_descumm.sh legger den).

Hva som leses (filene er ikke kryptert; blokkene har et hode på 6 byte, se pipeline/zakhd/lfl.py):
  00.LFL, 0S: nummeret til hvert globale skript som (rom, offset i rommets LFL-fil). Blokken er SC.
  NN.LFL, RO: LS (lokale skript, første byte etter hodet er nummeret), EN (inngang), EX (utgang)
        og OC (objekter: hode, verbtabell fra byte 19, navn og kode).

descumm får hele blokken med hodet og flaggene -3 -z (v3 og Zak256-tilpasningene). Den kjenner
taggene SC, LS, EN, EX og OC (parseHeader i engines/scumm/descumm-tool.cpp). For OC leser den
verbtabellen fra byte 19 (skipVerbHeader_V34) og begynner på den laveste offseten. Offsetene i
utskriften er da fra starten av OC-blokken, som i verbtabellen. For de andre er de fra starten av
koden (etter hodet, for LS også etter nummeret).

Resultat (work/ er gitignorert; spilldata skrives ikke andre steder):
  globale/scrp_NNN.txt        globalt skript NNN (nummer fra 0S)
  rom_RR/lokal_NNN.txt        lokalt skript NNN i rom RR
  rom_RR/inngang.txt          inngangsskriptet (EN)
  rom_RR/utgang.txt           utgangsskriptet (EX)
  rom_RR/obj_OOOO_verb.txt    verbskriptene til objekt OOOO. Objekter uten verb får ingen fil.
  OVERSIKT.md                 tellinger, og hvilke skript descumm ikke klarte, med feilmeldingen
  objekter.tsv                alle objektene: nummer, rom, posisjon, størrelse, bilde, verb og navn

Hver fil begynner med noen linjer som starter med ";" og sier hvor skriptet kommer fra.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

try:
    from zakhd import lfl
except ImportError:  # zakhd er ikke installert: bruk kildekoden i pipeline/
    sys.path.insert(0, str(ROOT / "pipeline"))
    from zakhd import lfl

TIDSGRENSE = 60  # sekunder per descumm-kjøring
FLAGG = ["-3", "-z"]

SORTER = [
    ("globalt", "Globale skript (SC)"),
    ("lokalt", "Lokale skript (LS)"),
    ("inngang", "Inngangsskript (EN)"),
    ("utgang", "Utgangsskript (EX)"),
    ("objekt", "Objektskript (OC med verb)"),
]
KODESTART = {"globalt": 6, "lokalt": 7, "inngang": 6, "utgang": 6, "objekt": 0}


@dataclass
class Jobb:
    sort: str
    rom: int
    data: bytes
    filer: list[str]
    hode: list[str]
    status: str = ""
    melding: str = ""
    advarsler: list[str] = field(default_factory=list)


def finn_jobber(game: Path) -> tuple[list[Jobb], dict]:
    idx = lfl.les_indeks(game / lfl.INDEX_FILE)
    info: dict = {"rom": 0, "rom_uten_ro": [], "skript_plasser": idx.plasser.get("0S", 0),
                  "skript_brukt": len(idx.skript), "skript_feil": [], "oc": 0, "oc_uten_verb": 0,
                  "doble": [], "objekter": []}
    jobber: list[Jobb] = []
    filer: dict[int, bytes] = {}

    def fil(rom: int) -> bytes:
        if rom not in filer:
            filer[rom] = lfl.rom_fil(game, rom).read_bytes()
        return filer[rom]

    for nr, (rom, off) in sorted(idx.skript.items()):
        try:
            d = fil(rom)
        except OSError:
            info["skript_feil"].append(f"skript {nr}: {rom:02d}.LFL finnes ikke")
            continue
        if d[off + 4:off + 6] != b"SC":
            info["skript_feil"].append(f"skript {nr}: {rom:02d}.LFL offset {off} er {d[off + 4:off + 6]!r}, ikke SC")
            continue
        size = lfl.le32(d, off)
        jobber.append(Jobb("globalt", rom, d[off:off + size], [f"globale/scrp_{nr:03d}.txt"],
                           [f"; Globalt skript {nr} (SC i {rom:02d}.LFL, offset 0x{off:X})"]))

    for rom in lfl.rom_numre(game):
        r = lfl.les_rom(game, rom)
        if not r.ro_size:
            info["rom_uten_ro"].append(rom)
            continue
        info["rom"] += 1
        d = r.d
        mappe = f"rom_{rom:02d}"
        for nr, o, size in r.lokale:
            jobber.append(Jobb("lokalt", rom, d[o:o + size], [f"{mappe}/lokal_{nr:03d}.txt"],
                               [f"; Lokalt skript {nr} i rom {rom} (LS)"]))
        if r.inngang:
            o, size = r.inngang
            jobber.append(Jobb("inngang", rom, d[o:o + size], [f"{mappe}/inngang.txt"],
                               [f"; Inngangsskriptet til rom {rom} (EN)"]))
        if r.utgang:
            o, size = r.utgang
            jobber.append(Jobb("utgang", rom, d[o:o + size], [f"{mappe}/utgang.txt"],
                               [f"; Utgangsskriptet til rom {rom} (EX)"]))
        brukte: Counter = Counter()
        for ob in r.objekter:
            info["oc"] += 1
            oi = r.bilder.get(ob.nr)
            bilde = "ja" if oi is not None and lfl.le32(d, oi) > 8 else "nei"
            navn = ob.navn.rstrip("@")
            info["objekter"].append((ob.nr, rom, ob.x, ob.y, ob.bredde, ob.hoeyde, bilde,
                                     [v for v, _ in ob.verb], navn))
            if not ob.verb:
                info["oc_uten_verb"] += 1
                continue
            brukte[ob.nr] += 1
            ekstra = f"_{brukte[ob.nr]}" if brukte[ob.nr] > 1 else ""
            if ekstra:
                info["doble"].append((rom, ob.nr, navn))
            hode = [f'; Objekt {ob.nr} "{navn}" i rom {rom} (OC). Plass {ob.x},{ob.y}, '
                    f"{ob.bredde} x {ob.hoeyde}, eget bilde: {bilde}",
                    "; Verbtabell (verb: offset fra starten av OC-blokken): "
                    + ", ".join(f"{v}: 0x{off:04X}" for v, off in ob.verb)]
            jobb = Jobb("objekt", rom, d[ob.oc:ob.oc + ob.oc_size], [f"{mappe}/obj_{ob.nr:04d}_verb{ekstra}.txt"], hode)
            if min(off for _, off in ob.verb) > 255:
                jobb.advarsler.append("laveste inngang er over 0xFF, men descumm begynner på 0xFF")
            jobber.append(jobb)
    return jobber, info


def finn_descumm(valg: str | None) -> Path:
    def kjorbar(sti) -> bool:
        return bool(sti) and Path(sti).is_file() and os.access(sti, os.X_OK)

    for kilde, sti in (("--descumm", valg), ("DESCUMM", os.environ.get("DESCUMM"))):
        if sti:
            if not kjorbar(sti):
                sys.exit(f"{kilde} peker på {sti}, som ikke er en kjørbar fil.")
            return Path(sti).resolve()
    for sti in (shutil.which("descumm"), ROOT / "work" / "scummvm-tools" / "descumm"):
        if kjorbar(sti):
            return Path(sti).resolve()
    sys.exit("Fant ikke descumm. Bygg den med tools/bygg_descumm.sh, eller bruk --descumm eller DESCUMM.")


def descumm_commit(descumm: Path) -> str:
    try:
        tekst = (descumm.parent / ".git" / "HEAD").read_text().strip()
    except OSError:
        return ""
    return tekst if re.fullmatch(r"[0-9a-f]{40}", tekst) else ""


def kjor(descumm: Path, jobb: Jobb, fil: Path) -> str:
    fil.write_bytes(jobb.data)
    try:
        r = subprocess.run([str(descumm), *FLAGG, str(fil)], capture_output=True, timeout=TIDSGRENSE, check=False)
    except subprocess.TimeoutExpired as e:
        jobb.status, jobb.melding = "feilet", f"tidsgrensen på {TIDSGRENSE} s gikk ut"
        return (e.stdout or b"").decode("latin1")
    finally:
        fil.unlink(missing_ok=True)
    ut = r.stdout.decode("latin1")
    feil = r.stderr.decode("latin1").strip()
    linjer = ut.rstrip("\n").split("\n")
    if r.returncode != 0:
        jobb.status = "feilet"
        jobb.melding = (f"descumm stoppet med signal {-r.returncode}" if r.returncode < 0
                        else (feil.splitlines()[-1] if feil else f"descumm avsluttet med kode {r.returncode}"))
    elif linjer[-1] != "END":
        jobb.status, jobb.melding = "feilet", "utskriften slutter ikke med END"
    elif "**** INVALID DATA ****" in ut or "ERROR: No items on stack" in ut:
        jobb.status = "feil_underveis"
        jobb.melding = f"{ut.count('INVALID DATA') + ut.count('ERROR: No items on stack')} feilmerker i utskriften"
    else:
        jobb.status = "ok"
    if feil and jobb.status != "feilet":
        jobb.advarsler += feil.splitlines()
    return ut


def skriv(utmappe: Path, jobb: Jobb, ut: str) -> None:
    hode = list(jobb.hode)
    if jobb.status == "feilet":
        hode.append(f"; descumm feilet: {jobb.melding}. Det som står under, er det den rakk.")
        siste = re.findall(r"^\[([0-9A-F]{4,})\]", ut, re.MULTILINE)
        if siste:
            fra = int(siste[-1], 16)
            rest = jobb.data[KODESTART[jobb.sort] + fra:]
            hode.append(f"; Byte fra siste viste offset 0x{fra:04X} ({len(rest)} byte): "
                        + rest[:96].hex(" ") + (" ..." if len(rest) > 96 else ""))
    elif jobb.status == "feil_underveis":
        hode.append(f"; descumm meldte feil underveis: {jobb.melding}")
    for a in jobb.advarsler:
        hode.append(f"; Advarsel: {a}")
    tekst = "\n".join(hode) + "\n\n" + ut
    if not tekst.endswith("\n"):
        tekst += "\n"
    for navn in jobb.filer:
        sti = utmappe / navn
        sti.parent.mkdir(parents=True, exist_ok=True)
        sti.write_text(tekst, encoding="utf-8")


def oversikt(utmappe: Path, jobber: list[Jobb], info: dict, descumm: Path, spill: Path, md5: str) -> None:
    tid = dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")
    commit = descumm_commit(descumm)
    linjer = [
        "# Dekompilerte skript",
        "",
        f"Laget {tid} med tools/dekompiler_skript.py.",
        f"descumm: {descumm}" + (f" (scummvm-tools {commit})" if commit else "") + f", flaggene {' '.join(FLAGG)}.",
        f"Spillfiler: {spill} (00.LFL md5 {md5}).",
        "",
        "Uten feil: descumm avsluttet normalt med END og ingen feilmerker.",
        "Feil underveis: utskriften har \"INVALID DATA\" eller \"ERROR: No items on stack\", men resten er med.",
        "Feilet: descumm stoppet. Filen har det den rakk.",
        "",
        "| Sort | Skript | Uten feil | Feil underveis | Feilet |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    sum_ = Counter()
    for sort, tittel in SORTER:
        js = [j for j in jobber if j.sort == sort]
        c = Counter(j.status for j in js)
        linjer.append(f"| {tittel} | {len(js)} | {c['ok']} | {c['feil_underveis']} | {c['feilet']} |")
        sum_.update(c)
        sum_["alle"] += len(js)
    linjer.append(f"| Sum | {sum_['alle']} | {sum_['ok']} | {sum_['feil_underveis']} | {sum_['feilet']} |")
    linjer += [
        "",
        "## Telling",
        "",
        f"- Rom med RO-blokk: {info['rom']}. Filer uten RO (bare skript, lyder og kostymer): "
        f"{', '.join(f'{r:02d}.LFL' for r in info['rom_uten_ro']) or 'ingen'}.",
        f"- 0S: {info['skript_brukt']} av {info['skript_plasser']} plasser er i bruk.",
        f"- Objekter (OC): {info['oc']}. Uten verb: {info['oc_uten_verb']}.",
    ]
    linjer += [f"- Feil i 0S: {f}." for f in info["skript_feil"]]
    linjer += [f'- Objekt {o} "{n}" har mer enn én OC i rom {r}; den andre har _2 i filnavnet.'
               for r, o, n in info["doble"]]
    for tittel, status in (("Feilet", "feilet"), ("Feil underveis", "feil_underveis")):
        js = [j for j in jobber if j.status == status]
        linjer += ["", f"## {tittel}", ""]
        linjer += [f"- {j.filer[0]}: {j.melding}" for j in js] or ["Ingen."]
    adv = [j for j in jobber if j.advarsler]
    linjer += ["", "## Advarsler", ""]
    linjer += [f"- {j.filer[0]}: {'; '.join(j.advarsler)}" for j in adv] or ["Ingen."]
    (utmappe / "OVERSIKT.md").write_text("\n".join(linjer) + "\n", encoding="utf-8")


def objektliste(utmappe: Path, info: dict) -> None:
    linjer = ["# objekt\trom\tx\ty\tbredde\thoeyde\tbilde\tverb\tnavn"]
    for obj, rom, x, y, w, h, bilde, verb, navn in sorted(info["objekter"]):
        linjer.append(f"{obj}\t{rom}\t{x}\t{y}\t{w}\t{h}\t{bilde}\t{','.join(map(str, verb)) or '-'}\t{navn}")
    (utmappe / "objekter.tsv").write_text("\n".join(linjer) + "\n", encoding="utf-8")


def rydd(utmappe: Path) -> None:
    """Fjerner det en tidligere kjøring laget, og ingenting annet."""
    for sti in utmappe.iterdir():
        laget = sti.name == "globale" or re.fullmatch(r"rom_\d{2,3}", sti.name) or sti.name.startswith("tmp_descumm_")
        if sti.is_dir() and laget:
            shutil.rmtree(sti)
        elif sti.is_file() and sti.name in ("OVERSIKT.md", "objekter.tsv"):
            sti.unlink()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Dekompilerer alle skriptene i Zak McKracken (FM-Towns, SCUMM v3) med descumm.")
    ap.add_argument("--descumm", help="sti til descumm (ellers DESCUMM, PATH eller work/scummvm-tools/descumm)")
    ap.add_argument("--spill", type=Path, default=ROOT / "game", help="mappen med 00.LFL til 59.LFL (game/)")
    ap.add_argument("--ut", type=Path, default=ROOT / "work" / "skript", help="utmappen (work/skript/)")
    ap.add_argument("--jobber", type=int, default=os.cpu_count() or 2, help="descumm-kjøringer samtidig")
    a = ap.parse_args(argv)

    utmappe = a.ut.resolve()
    work = (ROOT / "work").resolve()
    if utmappe.is_relative_to(ROOT) and not utmappe.is_relative_to(work):
        sys.exit(f"Utmappen {utmappe} er i repoet, men ikke under work/. Skriptene er spilldata og skal ikke inn i git.")
    descumm = finn_descumm(a.descumm)
    spill = a.spill.resolve()
    if not (spill / lfl.INDEX_FILE).is_file():
        sys.exit(f"Fant ikke {spill / lfl.INDEX_FILE}. Hent spillfilene med tools/hent_spilldata.sh.")
    md5 = hashlib.md5((spill / lfl.INDEX_FILE).read_bytes()).hexdigest()
    jobber, info = finn_jobber(spill)
    print(f"Fant {len(jobber)} skript i {info['rom']} rom. Kjører {descumm} {' '.join(FLAGG)} ...")

    utmappe.mkdir(parents=True, exist_ok=True)
    rydd(utmappe)
    tmp = Path(tempfile.mkdtemp(prefix="tmp_descumm_", dir=utmappe))
    try:
        def en(i_jobb):
            i, jobb = i_jobb
            skriv(utmappe, jobb, kjor(descumm, jobb, tmp / f"{i:04d}.bin"))
        with ThreadPoolExecutor(max(1, a.jobber)) as pool:
            list(pool.map(en, enumerate(jobber)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    oversikt(utmappe, jobber, info, descumm, spill, md5)
    objektliste(utmappe, info)
    c = Counter(j.status for j in jobber)
    print(f"Ferdig: {c['ok']} uten feil, {c['feil_underveis']} med feil underveis, {c['feilet']} feilet.")
    print(f"Resultat i {utmappe}, oversikt i {utmappe / 'OVERSIKT.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
