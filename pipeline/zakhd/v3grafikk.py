"""Dekodere for grafikken i Zak McKracken, FM-Towns (SCUMM v3 med 256 farger, GF_OLD256).

Oversatt fra ScummVM ved commit c9091321 (engine/SCUMMVM_COMMIT), slik at bildene blir de
samme som motoren tegner:

  Striper i rom (BM) og objektbilder (OI): gfx.cpp, Gdi::drawStrip og Gdi::decompressBitmap.
    For GF_OLD256 brukes drawStripRaw (kode 1), unkDecode8 (2), unkDecode9 (3), unkDecode10 (4)
    og unkDecode11 (7). Alle fyller stripen kolonne for kolonne: 8 kolonner, hver ovenfra og ned.
    Andre koder går til dekoderne for v5 og v6 i v6grafikk.py (de er ikke funnet i Zak).
  Hvor stripene står: Gdi::drawStrip med GF_SMALL_HEADER. Dataene i BM (og i OI etter 8 byte)
    begynner med en uint32 (lengden av stripedelen), så én uint32-offset per stripe fra samme start.
  Z-planet: Gdi::getZPlanes og drawBitmap. Det begynner rett etter stripedelen; er første uint32
    0, finnes det ikke. Stripe s har offset uint16 ved 4 + 2 * s, og dataene pakkes som i
    decompressMaskImg (en byte er 8 piksler i en rad). v3 har ett z-plan (_numZBuffer = 2).
  Klassiske kostymer (CO): costume.cpp, ClassicCostumeLoader med GF_SMALL_HEADER (ptr + 0), som i
    v6 der COST-blokken har det samme gamle hodet etter 8 byte. Forskjellen i v3: startindeksen i
    animasjonskommandoene er én byte (0xFF betyr ingen), ikke to (costumeDecodeData).

Rutenummer i kostymer: lag * 128 + kode, som i Sam & Max (drawLimb i patchen).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import v6grafikk
from .lfl import le16, le32
from .v6grafikk import Bitmap, Cel, Costume, _decode_cel

OLD256_KODER = {1: "rå", 2: "løp", 3: "4-bit", 4: "lokal palett", 7: "endring"}


class _Bits256:
    """READ_BIT_256 og READ_N_BITS: minst signifikante bit først."""
    __slots__ = ("d", "p", "buffer", "mask")

    def __init__(self, d: bytes, p: int):
        self.d, self.p, self.buffer, self.mask = d, p, 0, 128

    def bit(self) -> int:
        self.mask <<= 1
        if self.mask == 256:
            self.buffer = self.d[self.p] if self.p < len(self.d) else 0
            self.p += 1
            self.mask = 1
        return 1 if self.buffer & self.mask else 0

    def n(self, k: int) -> int:
        c = 0
        for b in range(k):
            c += self.bit() << b
        return c


def _kolonner(height: int):
    """Rekkefølgen NEXT_ROW skriver i: kolonne for kolonne, indeks i et 8 x height-bilde."""
    for x in range(8):
        for y in range(height):
            yield y * 8 + x


def decode_strip_old256(d: bytes, p: int, height: int) -> tuple[bytearray, bytearray, int]:
    """Én stripe på 8 x height. Gir (piksler rad for rad, maske, kodek)."""
    code = d[p]
    p += 1
    total = 8 * height
    pix = bytearray(total)
    order = list(_kolonner(height))
    if code == 1:
        for i, k in enumerate(order):
            pix[k] = d[p + i]
    elif code == 2:
        i = 0
        while i < total:
            run = d[p] + 1
            color = d[p + 1]
            p += 2
            for _ in range(run):
                if i >= total:
                    break
                pix[order[i]] = color
                i += 1
    elif code == 3:
        br = _Bits256(d, p)
        run = 0
        i = 0
        while i < total:
            c = br.n(4)
            kind = c >> 2
            if kind == 0:
                color = br.n(4)
                for _ in range((c & 3) + 2):
                    if i >= total:
                        break
                    pix[order[i]] = (run * 16 + color) & 0xFF
                    i += 1
            elif kind == 1:
                for _ in range((c & 3) + 1):
                    color = br.n(4)
                    if i >= total:
                        break
                    pix[order[i]] = (run * 16 + color) & 0xFF
                    i += 1
            elif kind == 2:
                run = br.n(4)
    elif code == 4:
        num = d[p]
        local = d[p + 1:p + 1 + num]
        p += 1 + num
        i = 0
        while i < total:
            color = d[p]
            p += 1
            if color < num:
                pix[order[i]] = local[color]
                i += 1
            else:
                run = color - num + 1
                color = d[p]
                p += 1
                for _ in range(run):
                    if i >= total:
                        break
                    pix[order[i]] = color
                    i += 1
    elif code == 7:
        color = d[p]
        br = _Bits256(d, p + 1)
        inc = 1
        for k in order:
            pix[k] = color
            i = 0
            while i < 3:
                if not br.bit():
                    break
                i += 1
            if i == 1:
                inc = -inc
                color = (color - inc) & 0xFF
            elif i == 2:
                color = (color - inc) & 0xFF
            elif i == 3:
                inc = 1
                color = br.n(8)
    else:
        # Kodekene fra v4 og v5 (rad for rad). Ikke funnet i Zak, men motoren kjenner dem.
        pix, mask, code = v6grafikk.decode_strip(d, p - 1, height, -1)
        return pix, mask, code
    return pix, bytearray([1]) * total, code


def _maskestripe(d: bytes, p: int, height: int) -> bytearray:
    """decompressMaskImg: en byte per rad i stripen (bit 7 er pikselen lengst til venstre)."""
    out = bytearray(height)
    y = 0
    while y < height:
        b = d[p]
        p += 1
        if b & 0x80:
            b &= 0x7F
            c = d[p]
            p += 1
            while True:
                out[y] = c
                y += 1
                b -= 1
                if not b or y >= height:
                    break
        else:
            while True:
                out[y] = d[p]
                p += 1
                y += 1
                b -= 1
                if not b or y >= height:
                    break
    return out


@dataclass
class Bilde(Bitmap):
    zplan: bytearray | None = None       # 1 = foran figurene, rad for rad, eller None
    zplan_striper: int = 0               # striper med z-data


def decode_bm(d: bytes, data: int, width: int, height: int) -> Bilde:
    """Et bilde i BM-format. data peker på uint32-lengden (etter blokkhodet, eller OI + 8)."""
    strips = width // 8
    smap_len = le32(d, data)
    pixels = bytearray(width * height)
    mask = bytearray(width * height)
    codecs: dict[int, int] = {}
    for s in range(strips):
        if 4 * s + 4 >= smap_len:
            raise ValueError(f"stripe {s} mangler")
        off = le32(d, data + 4 + 4 * s)
        if not 0 <= off < smap_len:
            raise ValueError(f"stripe {s} peker utenfor bildet")
        pix, msk, code = decode_strip_old256(d, data + off, height)
        codecs[code] = codecs.get(code, 0) + 1
        x0 = s * 8
        for y in range(height):
            row = y * width + x0
            pixels[row:row + 8] = pix[y * 8:y * 8 + 8]
            mask[row:row + 8] = msk[y * 8:y * 8 + 8]
    bilde = Bilde(width, height, pixels, mask, codecs)
    zp = data + smap_len
    if zp + 4 <= len(d) and le32(d, zp):
        z = bytearray(width * height)
        n = 0
        for s in range(strips):
            if zp + 4 + 2 * s + 2 > len(d):
                break
            offs = le16(d, zp + 4 + 2 * s)
            if not offs:
                continue
            n += 1
            rader = _maskestripe(d, zp + offs, height)
            for y, b in enumerate(rader):
                for bit in range(8):
                    if b & (0x80 >> bit):
                        z[y * width + s * 8 + bit] = 1
        bilde.zplan = z
        bilde.zplan_striper = n
    return bilde


# ---------------------------------------------------------------- kostymer

def _anim_frames_v3(base: bytes, anim_cmds: int, data_offsets: int, num_anim: int,
                    errors: list | None = None) -> list[dict]:
    """Som v6grafikk._anim_frames, men startindeksen er én byte (costumeDecodeData, versjon <= 3)."""
    out = []
    n = len(base)
    for anim in range(num_anim + 1):
        if data_offsets + anim * 2 + 2 > n:
            break
        rel = le16(base, data_offsets + anim * 2)
        if not rel:
            continue
        try:
            r = rel
            mask = le16(base, r)
            r += 2
            limb = 0
            found = []
            while mask & 0xFFFF:
                if mask & 0x8000:
                    j = base[r]
                    r += 1
                    if j != 0xFF:
                        extra = base[r]
                        r += 1
                        cmd = base[anim_cmds + j]
                        if cmd not in (0x79, 0x7A):
                            codes = []
                            for k in range(j, j + (extra & 0x7F) + 1):
                                c = base[anim_cmds + k] & 0x7F
                                if c < 0x79 and c not in codes:
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


def decode_costume_v3(d: bytes, co: int) -> Costume:
    """En CO-blokk (co peker på blokkstarten). Gir alle rutene animasjonene bruker."""
    size = le32(d, co)
    base = d[co:co + size]
    num_anim = base[6]
    fmt = base[7] & 0x7F
    mirror = bool(base[7] & 0x80)
    if fmt not in (0x58, 0x59):
        raise ValueError(f"ukjent kostymeformat 0x{fmt:02X}")
    ncol = 32 if fmt == 0x59 else 16
    palette = bytes(base[8:8 + ncol])
    p = 8 + ncol
    anim_cmds = le16(base, p)
    frame_offsets = p + 2
    data_offsets = p + 34
    errors: list[str] = []
    anims = _anim_frames_v3(base, anim_cmds, data_offsets, num_anim, errors)
    shr, cmask = (3, 7) if ncol == 32 else (4, 15)
    wanted = sorted({c for a in anims for c in a["ruter"]})
    cels: list[Cel] = []
    for cel_no in wanted:
        limb, code = divmod(cel_no, 128)
        try:
            cels.append(_decode_cel(base, fmt, frame_offsets, limb, code, palette, shr, cmask))
        except (IndexError, ValueError) as e:
            errors.append(f"rute {cel_no} (lag {limb}, kode {code}): {e or 'utenfor kostymet'}")
    return Costume(num_anim, fmt, mirror, palette, anims, cels, errors)


# ---------------------------------------------------------------- tegnsett

def glyf(glyfer: bytes, tegn: int, bredde: int, hoeyde: int) -> bytearray:
    """Ett tegn fra et v3-tegnsett som maske (1 = tegnes), bredde x hoeyde, rad for rad (drawBits1)."""
    out = bytearray(bredde * hoeyde)
    for y in range(hoeyde):
        b = glyfer[tegn * 8 + y] if tegn * 8 + y < len(glyfer) else 0
        for x in range(bredde):
            if b & (0x80 >> x):
                out[y * bredde + x] = 1
    return out
