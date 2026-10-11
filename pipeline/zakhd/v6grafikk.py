"""Dekodere for grafikken i SCUMM v6 (Sam & Max Hit the Road).

Oversatt fra ScummVM ved commit c9091321 (engine/SCUMMVM_COMMIT), slik at bildene blir de
samme som motoren tegner:

  Striper (SMAP) i rom og objektbilder: gfx.cpp, Gdi::drawStrip og Gdi::decompressBitmap
    med drawStripRaw, drawStripBasicV, drawStripBasicH og drawStripComplex (MajMinCodec).
  Blast-objekter (BOMP): object.cpp, ScummEngine_v6::drawBlastObject, og bomp.cpp,
    bompDecodeLine. Fargen 255 er gjennomsiktig.
  Klassiske kostymer (COST): costume.cpp, ClassicCostumeLoader::loadCostume,
    ClassicCostumeLoader::costumeDecodeData, ClassicCostumeRenderer::drawLimb og
    paintCelByleRLE, og base-costume.cpp, byleRLEDecode.

Alt arbeider på dekrypterte data (gamedata.load). Bilder gis som bytearray med en
palettindeks per piksel, rad for rad, og en like stor maske der 1 betyr at pikselen tegnes.

Rutenummer i kostymer: en klassisk kostyme har én rutetabell per lag (limb), og ruten
velges med en kode (0 til 0x78) fra animasjonskommandoene. Rutenummeret her er
lag * 128 + kode, så motoren kan regne det ut rett fra drawLimb.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field

# Stripkodeker (gfx.h, BMCOMP_*). Siste siffer er antall bit for en ny farge.
RAW256 = 1
TPIX256 = 149


def _le16(d: bytes, o: int) -> int:
    return d[o] | (d[o + 1] << 8)


def _s16(v: int) -> int:
    return v - 0x10000 if v & 0x8000 else v


class _Bits:
    """Bitleseren i drawStripBasicH/V (FILL_BITS og READ_BIT)."""
    __slots__ = ("d", "p", "bits", "cl")

    def __init__(self, d: bytes, p: int):
        self.d, self.p = d, p

    def fill(self):
        if self.cl <= 8:
            self.bits |= (self.d[self.p] if self.p < len(self.d) else 0) << self.cl
            self.p += 1
            self.cl += 8

    def bit(self) -> int:
        self.cl -= 1
        b = self.bits & 1
        self.bits >>= 1
        return b


def _basic(d: bytes, p: int, height: int, shr: int, vertical: bool, transp: bool, tcol: int,
           pix: bytearray, mask: bytearray):
    """drawStripBasicV (vertical) og drawStripBasicH. Skriver en stripe på 8 x height."""
    dmask = 0xFF >> (8 - shr)
    color = d[p]
    br = _Bits(d, p + 2)
    br.bits = d[p + 1] if p + 1 < len(d) else 0
    br.cl = 8
    inc = -1
    if vertical:
        order = [(y * 8 + x) for x in range(8) for y in range(height)]
    else:
        order = range(8 * height)
    for i in order:
        br.fill()
        if not transp or color != tcol:
            pix[i] = color
            mask[i] = 1
        if not br.bit():
            pass
        elif not br.bit():
            br.fill()
            color = br.bits & dmask
            br.bits >>= shr
            br.cl -= shr
            inc = -1
        elif not br.bit():
            color = (color + inc) & 0xFF
        else:
            inc = -inc
            color = (color + inc) & 0xFF


def _majmin(d: bytes, p: int, height: int, shr: int, transp: bool, tcol: int,
            pix: bytearray, mask: bytearray):
    """drawStripComplex med MajMinCodec::decodeLine, 8 piksler per linje."""
    color = d[p]
    bits = d[p + 1] | (d[p + 2] << 8)
    nbits = 16
    q = p + 3
    n = len(d)
    repeat = False
    count = 0

    def read(k: int) -> int:
        nonlocal bits, nbits, q
        if nbits <= 8:
            bits |= (d[q] if q < n else 0) << nbits
            q += 1
            nbits += 8
        v = bits & ((1 << k) - 1)
        bits >>= k
        nbits -= k
        return v

    for i in range(8 * height):
        if not transp or color != tcol:
            pix[i] = color
            mask[i] = 1
        if not repeat:
            if read(1):
                if read(1):
                    diff = (read(3) - 4) & 0xFF
                    if diff:
                        color = (color + diff) & 0xFF
                    else:
                        repeat = True
                        count = read(8) - 1
                else:
                    color = read(shr)
        else:
            count -= 1
            if count == 0:
                repeat = False


def decode_strip(d: bytes, p: int, height: int, tcol: int) -> tuple[bytearray, bytearray, int]:
    """Én stripe (8 piksler bred). Gir (piksler, maske, kodek). Ukjent kodek gir ValueError."""
    code = d[p]
    p += 1
    pix = bytearray(8 * height)
    mask = bytearray(8 * height)
    shr = code % 10
    if code in (RAW256, TPIX256):
        transp = code == TPIX256
        for i in range(8 * height):
            c = d[p + i] if p + i < len(d) else 0
            if not transp or c != tcol:
                pix[i] = c
                mask[i] = 1
    elif 14 <= code <= 18 or 34 <= code <= 38:
        _basic(d, p, height, shr, True, code >= 34, tcol, pix, mask)
    elif 24 <= code <= 28 or 44 <= code <= 48:
        _basic(d, p, height, shr, False, code >= 44, tcol, pix, mask)
    elif 64 <= code <= 68 or 84 <= code <= 88 or 104 <= code <= 108 or 124 <= code <= 128:
        _majmin(d, p, height, shr, code in range(84, 89) or code in range(124, 129), tcol, pix, mask)
    else:
        raise ValueError(f"ukjent stripkodek {code}")
    return pix, mask, code


@dataclass
class Bitmap:
    width: int
    height: int
    pixels: bytearray          # palettindeks per piksel, rad for rad
    mask: bytearray            # 1 = tegnes, 0 = gjennomsiktig
    codecs: dict[int, int] = field(default_factory=dict)  # kodek -> antall striper


def decode_smap(d: bytes, smap: int, width: int, height: int, tcol: int) -> Bitmap:
    """Et bilde fra en SMAP-blokk (smap peker på taggen). Bredden må være delelig med 8."""
    strips = width // 8
    size = struct.unpack_from(">I", d, smap + 4)[0]
    pixels = bytearray(width * height)
    mask = bytearray(width * height)
    codecs: dict[int, int] = {}
    for s in range(strips):
        if 8 + 4 * s + 4 > size:
            raise ValueError(f"stripe {s} mangler i SMAP")
        off = struct.unpack_from("<I", d, smap + 8 + 4 * s)[0]
        if not 0 <= off < size:
            raise ValueError(f"stripe {s} peker utenfor SMAP")
        pix, msk, code = decode_strip(d, smap + off, height, tcol)
        codecs[code] = codecs.get(code, 0) + 1
        x0 = s * 8
        for y in range(height):
            row = y * width + x0
            pixels[row:row + 8] = pix[y * 8:y * 8 + 8]
            mask[row:row + 8] = msk[y * 8:y * 8 + 8]
    return Bitmap(width, height, pixels, mask, codecs)


def decode_bomp(d: bytes, bomp_data: int) -> Bitmap:
    """Et blast-objekt. bomp_data peker på dataene i BOMP-blokken (etter de 8 byte med hode)."""
    width = _le16(d, bomp_data + 2)
    height = _le16(d, bomp_data + 4)
    src = bomp_data + 10
    pixels = bytearray(width * height)
    mask = bytearray(width * height)
    for y in range(height):
        line = bytearray([255]) * width
        q = src + 2
        left = width
        x = 0
        while left > 0:
            code = d[q]
            q += 1
            num = min((code >> 1) + 1, left)
            left -= num
            if code & 1:
                line[x:x + num] = bytes([d[q]]) * num
                q += 1
            else:
                line[x:x + num] = d[q:q + num]
                q += num
            x += num
        src += _le16(d, src) + 2
        row = y * width
        pixels[row:row + width] = line
        mask[row:row + width] = bytes(1 if c != 255 else 0 for c in line)
    return Bitmap(width, height, pixels, mask, {"bomp": 1})


# ---------------------------------------------------------------- klassiske kostymer

@dataclass
class Cel:
    cel: int                   # lag * 128 + kode
    limb: int
    code: int
    width: int
    height: int
    rel_x: int
    rel_y: int
    move_x: int
    move_y: int
    data: int                  # hvor bildedataene starter, relativt til baseptr (for å finne like ruter)
    pixels: bytearray          # palettindeks i rommet (etter kostymepaletten), rad for rad
    mask: bytearray            # 1 = tegnes (fargen i kostymet er ikke 0)
    colours: bytearray         # fargen i kostymet (0 til 15 eller 31), rad for rad


@dataclass
class Costume:
    num_anim: int
    format: int
    mirror: bool
    palette: bytes             # kostymefarge -> palettindeks i rommet
    animations: list[dict]     # [{"valg", "animasjon", "retning", "lag", "ruter"}], som gamedata.akos_animations
    cels: list[Cel]
    errors: list[str] = field(default_factory=list)


def _anim_frames(base: bytes, anim_cmds: int, data_offsets: int, num_anim: int,
                 errors: list | None = None) -> list[dict]:
    """Hvilke ruter hver animasjon og hvert lag viser (costumeDecodeData og increaseAnim).

    Animasjoner som peker utenfor kostymet, hoppes over og noteres i errors. Motoren leser dem
    bare hvis et skript ber om dem, og da ville den lest tilfeldige byte.
    """
    out = []
    n = len(base)
    for anim in range(num_anim + 1):
        if data_offsets + anim * 2 + 2 > n:
            break
        rel = _le16(base, data_offsets + anim * 2)
        if not rel:
            continue
        try:
            r = rel
            mask = _le16(base, r)
            r += 2
            limb = 0
            found = []
            while mask & 0xFFFF:
                if mask & 0x8000:
                    j = _le16(base, r)
                    r += 2
                    if j != 0xFFFF:
                        extra = base[r]
                        r += 1
                        cmd = base[anim_cmds + j]
                        if cmd not in (0x79, 0x7A):
                            codes = []
                            for k in range(j, j + (extra & 0x7F) + 1):
                                c = base[anim_cmds + k] & 0x7F
                                if c not in (0x79, 0x7A, 0x7B) and c not in codes:
                                    codes.append(c)
                            if codes:
                                found.append({"valg": anim, "animasjon": anim // 4, "retning": anim % 4,
                                              "lag": limb, "ruter": [limb * 128 + c for c in codes]})
                limb += 1
                mask = (mask << 1) & 0xFFFF
            out += found
        except IndexError:
            if errors is not None:
                errors.append(f"animasjon {anim} peker utenfor kostymet")
    return out


def decode_costume(d: bytes, cost: int) -> Costume:
    """En COST-blokk (cost peker på taggen). Gir alle rutene animasjonene bruker."""
    size = struct.unpack_from(">I", d, cost + 4)[0]
    base = d[cost + 8:cost + size]
    num_anim = base[6]
    fmt = base[7] & 0x7F
    mirror = bool(base[7] & 0x80)
    if fmt not in (0x58, 0x59, 0x60, 0x61):
        raise ValueError(f"ukjent kostymeformat 0x{fmt:02X}")
    ncol = 32 if fmt in (0x59, 0x61) else 16
    palette = bytes(base[8:8 + ncol])
    p = 8 + ncol
    anim_cmds = _le16(base, p)
    frame_offsets = p + 2
    data_offsets = p + 34
    errors: list[str] = []
    anims = _anim_frames(base, anim_cmds, data_offsets, num_anim, errors)
    shr, cmask = (3, 7) if ncol == 32 else (4, 15)

    wanted = sorted({c for a in anims for c in a["ruter"]})
    cels = []
    for cel_no in wanted:
        limb, code = divmod(cel_no, 128)
        try:
            cels.append(_decode_cel(base, fmt, frame_offsets, limb, code, palette, shr, cmask))
        except (IndexError, ValueError) as e:
            errors.append(f"rute {cel_no} (lag {limb}, kode {code}): {e or 'utenfor kostymet'}")
    return Costume(num_anim, fmt, mirror, palette, anims, cels, errors)


def _decode_cel(base: bytes, fmt: int, frame_offsets: int, limb: int, code: int, palette: bytes,
                shr: int, cmask: int) -> Cel:
    """Én rute: hodet (CostumeInfo) og bildet (byleRLEDecode)."""
    cel_no = limb * 128 + code
    frameptr = _le16(base, frame_offsets + limb * 2)
    celptr = _le16(base, frameptr + code * 2)
    w, h = _le16(base, celptr), _le16(base, celptr + 2)
    rx, ry = _s16(_le16(base, celptr + 4)), _s16(_le16(base, celptr + 6))
    mx, my = _s16(_le16(base, celptr + 8)), _s16(_le16(base, celptr + 10))
    src = celptr + 12
    if fmt in (0x60, 0x61):
        ex1, ex2 = base[src], base[src + 1]
        src += 2
        if ex1 != 0xFF or ex2 != 0xFF:
            e1 = _le16(base, frame_offsets + ex1 * 2)
            src = _le16(base, e1 + ex2 * 2) + 14
    colours = bytearray(w * h)
    # byleRLEDecode: løp nedover hver kolonne, og løpet fortsetter i neste kolonne
    total = w * h
    i = 0
    q = src
    while i < total:
        b = base[q]
        q += 1
        col = b >> shr
        rep = b & cmask
        if not rep:
            rep = base[q] or 256       # len er en byte, så 0 gir 256 runder i do/while (--len)
            q += 1
        for _ in range(rep):
            if i >= total:
                break
            x, y = divmod(i, h)
            colours[y * w + x] = col
            i += 1
    if i < total:
        raise ValueError("bildedataene slutter før ruten er full")
    pixels = bytearray(palette[c] if c else 0 for c in colours)
    mask = bytearray(1 if c else 0 for c in colours)
    return Cel(cel_no, limb, code, w, h, rx, ry, mx, my, src, pixels, mask, colours)
