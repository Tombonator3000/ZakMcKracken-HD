"""Leser spillfilene i Zak McKracken, FM-Towns (SCUMM v3 med 256 farger, GF_OLD256).

Formatet er sjekket mot ScummVM ved c9091321 (engine/SCUMMVM_COMMIT) og mot filene 11. oktober 2026:

  Hver blokk har et lite hode på 6 byte: størrelse (uint32 LE, med hodet) og en tag på 2 tegn.
  Filene er ikke kryptert.

  00.LFL (indeksen, ScummEngine_v4::readIndexFile):
    0R  rom: antall (uint16) og (disk, offset) per rom. For Zak er alle 0; rom N ligger i N.LFL.
    0S  globale skript: (rom, offset fra starten av rommets LFL-fil) per skriptnummer.
    0N  lyder, samme form.
    0C  kostymer, samme form.
    0O  objekter: antall og 4 byte per objekt (klassebiter i 3 byte, eier og tilstand i 1 byte).
    RN  romnavn, XOR 0xFF (finnes ikke i den engelske FM-Towns-utgaven).

  NN.LFL (rom N): én RO-blokk først, så skript, lyder og kostymer som egne blokker (SC, SO, CO).
    RO inneholder HD (bredde, høyde, antall objekter), BX (bokser), PA (palett: antall farger
    uint16, så RGB), SA (skalering), BM (bakgrunnen), OI (objektbilder), OC (objektkode),
    NL og SL (lister over lokale skript og lyder som lastes med rommet), EX og EN (utgang og
    inngang) og LS (lokale skript, første byte er nummeret).

  98.LFL og 99.LFL: tegnsett 1 og 0 (ScummEngine_v3::loadCharset leser %02d.LFL med 99 - nr).
    Først en uint16 med størrelsen, så ressursen.
"""
from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass, field
from pathlib import Path

INDEX_FILE = "00.LFL"
CHARSET_FILES = {0: "99.LFL", 1: "98.LFL"}
GAME_ID = "zak"
KJENT_MD5 = {"2d4536a56e01da4b02eb021e7770afa2": "zak FM-TOWNS, engelsk (ScummVM scumm-md5.h)"}


def le16(d: bytes, o: int) -> int:
    return d[o] | (d[o + 1] << 8)


def le32(d: bytes, o: int) -> int:
    return struct.unpack_from("<I", d, o)[0]


def blokker(d: bytes, start: int, end: int):
    """Blokkene mellom start og end: (tag, offset, størrelse). Taggen er en str på 2 tegn."""
    p = start
    while p + 6 <= end:
        size = le32(d, p)
        if size < 6 or p + size > end:
            raise ValueError(f"ugyldig blokk ved 0x{p:X} (størrelse {size})")
        yield d[p + 4:p + 6].decode("latin1"), p, size
        p += size


def finn(d: bytes, start: int, end: int, tag: str) -> int | None:
    for t, o, _ in blokker(d, start, end):
        if t == tag:
            return o
    return None


def rom_fil(game: Path, nr: int) -> Path:
    return game / f"{nr:02d}.LFL"


def rom_numre(game: Path) -> list[int]:
    return sorted(int(p.stem) for p in game.glob("[0-9][0-9].LFL") if 1 <= int(p.stem) <= 97)


# ---------------------------------------------------------------- indeksen

@dataclass
class Indeks:
    md5: str
    rom_navn: dict[int, str]
    skript: dict[int, tuple[int, int]]       # nummer -> (rom, offset i rommets fil)
    lyder: dict[int, tuple[int, int]]
    kostymer: dict[int, tuple[int, int]]
    objekter: int
    klasser: list[int]
    eiere: list[int]
    tilstander: list[int]
    plasser: dict[str, int]                  # antall plasser per liste
    version: int = 3


def les_indeks(sti: Path) -> Indeks:
    d = sti.read_bytes()
    md5 = hashlib.md5(d).hexdigest()
    lister: dict[str, dict[int, tuple[int, int]]] = {}
    plasser: dict[str, int] = {}
    navn: dict[int, str] = {}
    klasser: list[int] = []
    eiere: list[int] = []
    tilstander: list[int] = []
    n_obj = 0
    for tag, o, size in blokker(d, 0, len(d)):
        q = o + 6
        if tag in ("0R", "0S", "0N", "0C"):
            n = le16(d, q)
            plasser[tag] = n
            ent = {}
            for i in range(n):
                rom, off = d[q + 2 + 5 * i], le32(d, q + 3 + 5 * i)
                if rom:
                    ent[i] = (rom, off)
            lister[tag] = ent
        elif tag == "0O":
            n_obj = le16(d, q)
            for i in range(n_obj):
                b = d[q + 2 + 4 * i:q + 6 + 4 * i]
                klasser.append(b[0] | (b[1] << 8) | (b[2] << 16))
                eiere.append(b[3] & 0x0F)
                tilstander.append(b[3] >> 4)
        elif tag == "RN":
            p = q
            while d[p]:
                nr = d[p]
                navn[nr] = bytes(c ^ 0xFF for c in d[p + 1:p + 10]).split(b"\0")[0].decode("latin1")
                p += 10
    return Indeks(md5, navn, lister.get("0S", {}), lister.get("0N", {}), lister.get("0C", {}),
                  n_obj, klasser, eiere, tilstander, plasser)


# ---------------------------------------------------------------- rommene

@dataclass
class ObjektKode:
    nr: int
    x: int
    y: int
    bredde: int
    hoeyde: int
    forelder: int
    forelder_tilstand: int
    walk_x: int
    walk_y: int
    retning: int
    navn: str
    oc: int                 # offset til OC-blokken i filen
    oc_size: int
    verb: list[tuple[int, int]]   # (verb, offset fra starten av OC-blokken)


@dataclass
class Rom:
    nr: int
    d: bytes                # hele LFL-filen
    ro: int
    ro_size: int            # 0 når filen ikke har noen RO-blokk
    bredde: int
    hoeyde: int
    antall_objekter: int
    palett: bytes           # 768 byte RGB
    farger: int             # antall farger i PA
    bm: int | None          # offset til dataene i BM (etter hodet)
    objekter: list[ObjektKode]
    bilder: dict[int, int]  # objektnummer -> offset til OI-blokken
    lokale: list[tuple[int, int, int]]   # (nummer, offset, størrelse) for LS
    inngang: tuple[int, int] | None
    utgang: tuple[int, int] | None
    tagger: list[str]
    andre: list[tuple[str, int, int]] = field(default_factory=list)  # blokker etter RO i filen


def _objektkode(d: bytes, o: int, size: int) -> ObjektKode:
    """OC-blokken (ScummEngine_v4::resetRoomObject, versjon 3)."""
    nr = le16(d, o + 6)
    x = d[o + 9] * 8
    y = (d[o + 10] & 0x7F) * 8
    parentstate = 1 if d[o + 10] & 0x80 else 0
    w = d[o + 11] * 8
    parent = d[o + 12]
    walk_x, walk_y = le16(d, o + 13), le16(d, o + 15)
    retning = d[o + 17] & 7
    h = d[o + 17] & 0xF8
    navn_off = d[o + 18]
    verb = []
    p = o + 19
    while p < o + size and d[p]:
        verb.append((d[p], le16(d, p + 1)))
        p += 3
    navn = ""
    if navn_off and navn_off < size:
        navn = d[o + navn_off:o + size].split(b"\0")[0].decode("latin1")
    return ObjektKode(nr, x, y, w, h, parent, parentstate, walk_x, walk_y, retning, navn, o, size, verb)


def les_rom(game: Path, nr: int) -> Rom:
    d = rom_fil(game, nr).read_bytes()
    # Noen filer har ingen RO-blokk, bare skript, lyder og kostymer (47.LFL i Zak)
    ro_size = le32(d, 0) if d[4:6] == b"RO" else 0
    tagger = []
    bredde = hoeyde = n_obj = 0
    palett = bytes(768)
    farger = 0
    bm = None
    objekter: list[ObjektKode] = []
    bilder: dict[int, int] = {}
    lokale = []
    inngang = utgang = None
    for tag, o, size in (blokker(d, 6, ro_size) if ro_size else ()):
        tagger.append(tag)
        if tag == "HD":
            bredde, hoeyde, n_obj = le16(d, o + 6), le16(d, o + 8), le16(d, o + 10)
        elif tag == "PA":
            farger = le16(d, o + 6)
            raw = d[o + 8:o + 8 + 3 * farger]
            palett = raw + bytes(768 - len(raw))
        elif tag == "BM":
            bm = o + 6
        elif tag == "OI":
            bilder[le16(d, o + 6)] = o
        elif tag == "OC":
            objekter.append(_objektkode(d, o, size))
        elif tag == "LS":
            lokale.append((d[o + 6], o, size))
        elif tag == "EN":
            inngang = (o, size)
        elif tag == "EX":
            utgang = (o, size)
    andre = list(blokker(d, ro_size, len(d)))
    return Rom(nr, d, 0, ro_size, bredde, hoeyde, n_obj, palett, farger, bm, objekter, bilder,
               lokale, inngang, utgang, tagger, andre)


def les_alle_rom(game: Path) -> dict[int, Rom]:
    return {nr: les_rom(game, nr) for nr in rom_numre(game)}


# ---------------------------------------------------------------- tegnsett

@dataclass
class Tegnsett:
    nr: int
    antall: int
    hoeyde: int
    bredder: bytes
    glyfer: bytes           # 8 byte per tegn, 1 bit per piksel, øverste rad først


def les_tegnsett(game: Path, nr: int) -> Tegnsett:
    raw = (game / CHARSET_FILES[nr]).read_bytes()
    size = le16(raw, 0)
    res = raw[2:2 + size]
    n, h = res[4], res[5]
    return Tegnsett(nr, n, h, res[6:6 + n], res[6 + n:6 + n + 8 * n])
