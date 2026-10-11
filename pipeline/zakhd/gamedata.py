"""Leser strukturen i indeks- og datafilen til et SCUMM v6- eller v7-spill.

Sam & Max Hit the Road (v6): SAMNMAX.000 og SAMNMAX.001, kryptert med XOR 0x69.
The Dig (v7, der koden kommer fra): DIG.LA0 og DIG.LA1, ukryptert. Begge leses her.

Dette er bare det HD-arbeidet trenger: romnavn, romstørrelser, paletter,
fargesykling, hvor objektene står, og hvilken kostyme-ID hver kostymeblokk
har (AKOS i v7, COST i v6). Bildene dekodes i v6grafikk.py (v6) og av
thedig-textures (v7, export.py).

Blokkformat: 4 byte tagg + 4 byte størrelse (big endian, inkludert hodet).
Ingen utfylling til partall (neste = start + størrelse).

Forskjeller i v6 (bekreftet mot ScummVM resource.cpp og object.cpp ved c9091321):
  MAXS er 15 x uint16 uten versjonstekster (blokkstørrelse 38).
  RMHD er bredde, høyde og antall objekter uten versjonsfelt.
  Objektenes plass og mål står i CDHD i OBCD, ikke i IMHD.
  Kostymene er COST-blokker (klassiske kostymer), ikke AKOS.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field
from pathlib import Path


def be32(d: bytes, o: int) -> int:
    return struct.unpack_from(">I", d, o)[0]


def le16(d: bytes, o: int) -> int:
    return struct.unpack_from("<H", d, o)[0]


def le16s(d: bytes, o: int) -> int:
    return struct.unpack_from("<h", d, o)[0]


def le32(d: bytes, o: int) -> int:
    return struct.unpack_from("<I", d, o)[0]


def children(d: bytes, start: int, end: int):
    """Gir (tagg, offset, størrelse) for blokkene mellom start og end."""
    p = start
    while p + 8 <= end:
        tag = d[p:p + 4]
        size = be32(d, p + 4)
        if size < 8 or p + size > end:
            break
        yield tag, p, size
        p += size


XOR_V6 = 0x69
_FIRST_TAGS = (b"RNAM", b"MAXS", b"LECF")


def load(path: Path) -> tuple[bytes, int]:
    """Leser en spillfil og dekrypterer den om nødvendig. Gir (data, XOR-nøkkel eller 0)."""
    raw = Path(path).read_bytes()
    if raw[:4] in _FIRST_TAGS:
        return raw, 0
    table = bytes(i ^ XOR_V6 for i in range(256))
    if raw[:4].translate(table) in _FIRST_TAGS:
        return raw.translate(table), XOR_V6
    raise ValueError(f"Kjenner ikke formatet til {path}")


def find_child(d: bytes, start: int, size: int, tag: bytes) -> int | None:
    for t, o, _ in children(d, start + 8, start + size):
        if t == tag:
            return o
    return None


# ---------------------------------------------------------------- LA0

@dataclass
class Index:
    room_names: dict[int, str]
    maxs: dict[str, int]
    engine_version: str
    data_version: str
    costume_dir: list[tuple[int, int]]  # (rom, offset) per kostyme-ID
    md5: str = ""
    version: int = 7
    xor: int = 0


MAXS_FIELDS = [
    "variables", "bit_variables", "unknown", "global_objects", "local_objects",
    "new_names", "verbs", "fl_objects", "inventory", "arrays", "rooms",
    "scripts", "sounds", "charsets", "costumes",
]

# v6 (ScummEngine_v6::readMAXS, blokkstørrelse 38)
MAXS_FIELDS_V6 = [
    "variables", "unknown", "bit_variables", "local_objects", "arrays",
    "unknown2", "verbs", "fl_objects", "inventory", "rooms",
    "scripts", "sounds", "charsets", "costumes", "global_objects",
]


def _directory(body: bytes) -> list[tuple[int, int]]:
    n = le16(body, 0)
    rooms = body[2:2 + n]
    offs = [le32(body, 2 + n + 4 * i) for i in range(n)]
    return list(zip(rooms, offs))


def read_index(path: Path) -> Index:
    import hashlib
    raw = Path(path).read_bytes()
    d, key = load(path)
    version = 7
    names: dict[int, str] = {}
    maxs: dict[str, int] = {}
    ev = dv = ""
    cos: list[tuple[int, int]] = []
    p = 0
    while p + 8 <= len(d):
        tag, size = d[p:p + 4], be32(d, p + 4)
        body = d[p + 8:p + size]
        if tag == b"RNAM":
            q = 0
            while q < len(body) and body[q] != 0:
                raw = bytes(b ^ 0xFF for b in body[q + 1:q + 10])
                names[body[q]] = raw.split(b"\x00")[0].decode("latin1")
                q += 10
        elif tag == b"MAXS" and size == 38:
            version = 6
            maxs = dict(zip(MAXS_FIELDS_V6, struct.unpack_from("<15H", body, 0)))
        elif tag == b"MAXS":
            ev = body[:50].split(b"\x00")[0].decode("latin1")
            dv = " ".join(body[50:100].replace(b"\x00", b" ").decode("latin1").split())
            maxs = dict(zip(MAXS_FIELDS, struct.unpack_from("<15H", body, 100)))
        elif tag == b"DCOS":
            cos = _directory(body)
        if size < 8:
            break
        p += size
    return Index(names, maxs, ev, dv, cos, hashlib.md5(raw).hexdigest(), version, key)


# ---------------------------------------------------------------- LA1

@dataclass
class ObjectImage:
    obj_id: int
    x: int
    y: int
    width: int
    height: int
    states: list[str]  # "01", "02", ... (heksadesimalt, som IMxx-taggene)


@dataclass
class Room:
    number: int
    offset: int
    width: int = 0
    height: int = 0
    palettes: list[bytes] = field(default_factory=list)
    cycles: list[tuple[int, int, int, int]] = field(default_factory=list)  # (start, slutt, forsinkelse, flagg)
    has_zplane: bool = False
    objects: list[ObjectImage] = field(default_factory=list)
    akos_offsets: list[int] = field(default_factory=list)  # relativt til ROOM-blokken (v7)
    cost_offsets: list[int] = field(default_factory=list)  # COST-blokkene, relativt til ROOM-blokken (v6)
    version: int = 7


def _palettes(d: bytes, pals: int) -> list[bytes]:
    wrap = find_child(d, pals, be32(d, pals + 4), b"WRAP")
    if wrap is None:
        return []
    offs = find_child(d, wrap, be32(d, wrap + 4), b"OFFS")
    if offs is None:
        return []
    n = (be32(d, offs + 4) - 8) // 4
    base = offs + 8
    return [d[base + le32(d, base + 4 * i):base + le32(d, base + 4 * i) + 768] for i in range(n)]


def _cycles(body: bytes) -> list[tuple[int, int, int, int]]:
    """CYCL i v6+: [id, 2 ukjente, forsinkelse BE16, flagg BE16, start, slutt] ... 0."""
    out = []
    p = 0
    while p < len(body) and body[p] != 0:
        if p + 9 >= len(body):
            break
        delay = struct.unpack_from(">H", body, p + 3)[0]
        flags = struct.unpack_from(">H", body, p + 5)[0]
        start, end = body[p + 7], body[p + 8]
        if delay and start < end:
            out.append((start, end, delay, flags))
        p += 9
    return out


def read_rooms(path: Path) -> dict[int, Room]:
    d, _ = load(path)
    if d[:4] != b"LECF" or d[8:12] != b"LOFF":
        raise ValueError("Ikke en SCUMM v6/v7-datafil (LECF med LOFF)")
    rooms: dict[int, Room] = {}
    n = d[16]
    for i in range(n):
        num = d[17 + 5 * i]
        off = le32(d, 18 + 5 * i)
        room = Room(num, off)
        rsize = be32(d, off + 4)
        lflf_end = off - 8 + be32(d, off - 4)
        blocks = list(children(d, off + 8, off + rsize))
        # v6: RMHD er 6 byte (bredde, høyde, antall objekter); v7 har et versjonsfelt først
        rmhd = next(((c, size) for tag, c, size in blocks if tag == b"RMHD"), None)
        v6 = rmhd is not None and rmhd[1] == 14
        room.version = 6 if v6 else 7
        cdhd: dict[int, tuple[int, int, int, int]] = {}
        if v6:
            for tag, c, size in blocks:
                if tag == b"OBCD":
                    h = find_child(d, c, size, b"CDHD")
                    if h is not None:
                        h += 8
                        cdhd[le16(d, h)] = (le16s(d, h + 2), le16s(d, h + 4), le16(d, h + 6), le16(d, h + 8))
        for tag, c, size in blocks:
            if tag == b"RMHD":
                if v6:
                    room.width, room.height = le16(d, c + 8), le16(d, c + 10)
                else:
                    room.width, room.height = le16(d, c + 12), le16(d, c + 14)
            elif tag == b"PALS":
                room.palettes = _palettes(d, c)
            elif tag == b"CYCL":
                room.cycles = _cycles(d[c + 8:c + size])
            elif tag == b"RMIM":
                im00 = find_child(d, c, size, b"IM00")
                if im00 is not None:
                    room.has_zplane = find_child(d, im00, be32(d, im00 + 4), b"ZP01") is not None
            elif tag == b"OBIM":
                imhd = find_child(d, c, size, b"IMHD")
                if imhd is None:
                    continue
                h = imhd + 8
                states = [t[2:4].decode("latin1") for t, _, _ in children(d, c + 8, c + size)
                          if t[:2] == b"IM" and t != b"IMHD"]
                if v6:
                    obj = le16(d, h)
                    x, y, w, hh = cdhd.get(obj, (0, 0, le16(d, h + 12), le16(d, h + 14)))
                    room.objects.append(ObjectImage(obj, x, y, w, hh, states))
                else:
                    room.objects.append(ObjectImage(le16(d, h + 4), le16s(d, h + 8), le16s(d, h + 10),
                                                    le16(d, h + 12), le16(d, h + 14), states))
        # Kostymene (AKOS i v7, COST i v6) ligger i LFLF etter ROOM-blokken
        for tag, c, _ in children(d, off, lflf_end):
            if tag == b"AKOS":
                room.akos_offsets.append(c - off)
            elif tag == b"COST":
                room.cost_offsets.append(c - off)
        rooms[num] = room
    return rooms


def costume_ids(index: Index, rooms: dict[int, Room]) -> list[int]:
    """Kostyme-ID for hver kostymeblokk (AKOS eller COST) i filrekkefølge (samme rekkefølge som digart bruker).

    DCOS-katalogen sier (rom, offset) per kostyme-ID. Offset er relativt til ROOM-blokken.
    """
    by_pos = {(r, o): cid for cid, (r, o) in enumerate(index.costume_dir) if r != 0}
    ids = []
    for num in sorted(rooms, key=lambda n: rooms[n].offset):
        for o in rooms[num].akos_offsets + rooms[num].cost_offsets:
            ids.append(by_pos.get((num, o), -1))
    return ids


def iter_akos(d: bytes, index: Index, rooms: dict[int, Room]):
    """Gir (kostyme-ID, hjemrom, offset, størrelse) for hver AKOS-blokk i filrekkefølge."""
    ids = costume_ids(index, rooms)
    n = 0
    for num in sorted(rooms, key=lambda r: rooms[r].offset):
        off = rooms[num].offset
        lflf_end = off - 8 + be32(d, off - 4)
        for tag, c, size in children(d, off, lflf_end):
            if tag == b"AKOS":
                yield ids[n], num, c, size
                n += 1


# ---------------------------------------------------------------- AKOS-animasjoner
#
# Fra ScummVM (akos.cpp, akos.h): AKHD har versjon, flagg, antall valg (chores), antall
# ruter, kodek og antall lag. AKCH har en offset per valg. Valg nummer = retning +
# animasjon * 4, eller * 8 når flagg & 2 (8 retninger). Ved offseten står en 16-bits maske
# med ett bit per lag (bit 15 er lag 0), og for hvert lag en kode: 1 (tømt), 4 (stoppet),
# 5 (startet igjen) eller animasjonstypen fulgt av start og lengde i AKSQ. AKSQ er en
# bytekode der en verdi under 0xC000 er en rute (verdi & 0xFFF er rutenummeret i AKOF) og
# 0xC0xx er kommandoer. Animasjonsnumrene ScummVM bruker for skuespillere: 1 start,
# 2 gange, 3 stå, 4 snakke, 5 slutt å snakke. Andre nummer settes av skriptene.

# Kommandoer i AKSQ og hvor mange byte de tar (akos_increaseAnim, AKAT_AlwaysRun)
_AKC_SIZE = {
    **dict.fromkeys((0x10, 0x16, 0x17, 0x18, 0x19, 0x31, 0x40, 0x90, 0x91, 0x92, 0x93, 0x94, 0x95), 5),
    **dict.fromkeys((0x15, 0x42, 0x44, 0x50, 0x80, 0x81, 0x83, 0x88, 0x8C, 0x8D, 0xA3), 3),
    **dict.fromkeys((0x85, 0x87, 0x8B), 6),
    **dict.fromkeys((0x01, 0x60, 0x61, 0x86, 0x9F, 0xFF), 2),
    **dict.fromkeys((0x70, 0x71, 0x72, 0x73, 0x74, 0x75, 0x82), 7),
    **dict.fromkeys((0x30, 0x84, 0x8A, 0x8E, 0xA0, 0xA1, 0xA2), 4),
    0x89: 8,
}
_AKC_DRAW_MANY, _AKC_REL_DRAW_MANY = 0x20, 0x25
_AKC_COND = (0x21, 0x22, 0x45, 0x46, 0x47, 0x48)          # lengden står i byte 2
_AKC_GOTO = 0x30
_AKC_COND_JUMPS = (0x16, 0x17, 0x18, 0x19, 0x31, 0x70, 0x71, 0x72, 0x73, 0x74, 0x75, 0xA1, 0xA2)
_AKC_EMPTY, _AKC_END = 0x01, 0xFF


def akos_sequence(aksq: bytes, start: int, limit: int = 4096) -> list[list[int]]:
    """Rutene en animasjon i AKSQ viser, steg for steg fra `start`.

    Hvert steg er listen av ruter som tegnes samtidig (én, eller flere med DrawMany). Hopp
    følges til et sted som er besøkt før (animasjonen går i ring) eller til slutten. Hopp som
    avhenger av variabler, følges begge veier etter hverandre, så alle rutene kommer med.
    """
    steps: list[list[int]] = []
    seen: set[int] = set()
    todo = [start]
    while todo and len(seen) < limit:
        p = todo.pop(0)
        while 0 <= p < len(aksq) and p not in seen:
            seen.add(p)
            b = aksq[p]
            code = struct.unpack_from(">H", aksq, p)[0] if b & 0x80 and p + 1 < len(aksq) else b
            if code & 0xC000 != 0xC000:
                steps.append([code & 0xFFF])
                p += 2 if b & 0x80 else 1
                continue
            op = code & 0xFF
            if op in (_AKC_DRAW_MANY, _AKC_REL_DRAW_MANY):
                q = p + 3 + (4 if op == _AKC_REL_DRAW_MANY else 0)
                if q > len(aksq):
                    break
                cels = []
                for _ in range(aksq[q - 1]):
                    q += 4
                    if q >= len(aksq):
                        break
                    bb = aksq[q]
                    c = struct.unpack_from(">H", aksq, q)[0] if bb & 0x80 else bb
                    cels.append(c & 0xFFF)
                    q += 2 if bb & 0x80 else 1
                steps.append(cels)
                p = q
                continue
            if op == _AKC_END:
                break
            if op == _AKC_EMPTY:
                p += 2
                continue
            if op == _AKC_GOTO:
                p = struct.unpack_from("<H", aksq, p + 2)[0]
                continue
            if op in _AKC_COND_JUMPS:
                todo.append(struct.unpack_from("<H", aksq, p + 2)[0])
            if op in _AKC_COND:
                p += max(1, aksq[p + 2]) if p + 2 < len(aksq) else len(aksq)
                continue
            if op not in _AKC_SIZE:
                break                          # ukjent kommando: stopp her
            p += _AKC_SIZE[op]
    return steps


def akos_animations(d: bytes, akos: int, size: int) -> dict:
    """Animasjonene i en AKOS-blokk: antall retninger og rutene per valg og lag.

    Gir {"retninger": 4 eller 8, "animasjoner": [{"valg", "animasjon", "retning", "lag", "ruter"}]}.
    "ruter" er rutene i rekkefølgen animasjonen viser dem første gang, uten gjentakelser. Lag
    som tømmes eller stoppes, er ikke med.
    """
    blocks = {t: (o, s) for t, o, s in children(d, akos + 8, akos + size)}
    if b"AKHD" not in blocks or b"AKCH" not in blocks or b"AKSQ" not in blocks:
        return {"retninger": 4, "animasjoner": []}
    akhd = blocks[b"AKHD"][0] + 8
    flags, chores = le16(d, akhd + 2), le16(d, akhd + 4)
    dirs = 8 if flags & 2 else 4
    akch, akch_size = blocks[b"AKCH"]
    aksq_off, aksq_size = blocks[b"AKSQ"]
    aksq = d[aksq_off + 8:aksq_off + aksq_size]
    body = akch + 8
    out = []
    for chore in range(min(chores, (akch_size - 8) // 2)):
        offs = le16(d, body + 2 * chore)
        if not offs or body + offs + 2 > akch + akch_size:
            continue
        r = body + offs
        mask = le16(d, r)
        r += 2
        for limb in range(16):
            if not mask & (0x8000 >> limb):
                continue
            kind = d[r]
            r += 1
            if kind in (1, 4, 5):
                continue
            start = le16(d, r)
            r += 4
            cels: list[int] = []
            for step in akos_sequence(aksq, start):
                cels += [c for c in step if c not in cels]
            if cels:
                out.append({"valg": chore, "animasjon": chore // dirs, "retning": chore % dirs, "lag": limb,
                            "ruter": cels})
    return {"retninger": dirs, "animasjoner": out}
