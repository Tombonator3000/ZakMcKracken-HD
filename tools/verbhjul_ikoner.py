#!/usr/bin/env python3
"""Tegner ikonene til verbhjulet som SVG, og lager PNG-ene og C-overskriften motoren bruker.

Ikonene er egne tegninger (Claude, 15. oktober 2026), i tegneseriestilen fra stilankerne i
grafikk/stil/: mørk kontur, flate farger, ett skyggetrinn. De er ikke laget fra spillets
grafikk, og kan derfor ligge i main og i nettsidepakken.

Teknikken: hver figur er satt sammen av enkle former (kapsler, ellipser, mangekanter).
Først tegnes alle formene i konturfargen med tykkere strek, så alle fyllene oppå. Da smelter
formene sammen til én silhuett med kontur rundt, som i en tegnet strek.

Bruk:
  python3 tools/verbhjul_ikoner.py                 # SVG og PNG til grafikk/ui/verbhjul/
  python3 tools/verbhjul_ikoner.py --ark ark.png   # kontaktark i tre størrelser
  python3 tools/verbhjul_ikoner.py --cpp engine/scummvm/engines/scumm/verbhjul_ikoner.h
Krever rsvg-convert (librsvg2-bin) og Pillow.
"""
import argparse
import base64
import io
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UT = ROOT / 'grafikk' / 'ui' / 'verbhjul'
STR = 128          # viewBox
PNG = 160          # PNG-størrelsen som legges i motoren (ikonet tegnes 96 til 112 px på en 4x-skjerm)

INK = '#2a1b12'
O = 5              # konturbredde (på hver side)
CREAM, CREAM_SH = '#f7ecd3', '#e6d3ab'
SKIN, SKIN_SH = '#f2bb8c', '#d8946a'
BLUE, BLUE_SH = '#4271c4', '#2d539a'
RED, RED_SH = '#d34a31', '#a5321f'
GOLD, GOLD_SH = '#f5c534', '#d39a17'
WOOD, WOOD_SH = '#b0703d', '#7e4b26'
GREEN, GREEN_SH = '#62b250', '#3f8a35'
METAL, METAL_SH = '#c3c9d0', '#8d96a1'
WHITE = '#ffffff'
PURPLE, PURPLE_SH = '#8a5fd0', '#5f3ea0'
DARK_GLASS = '#7d8590'


class Icon:
    def __init__(self):
        self.shapes = []   # (svg-element-uten-farge, fyll, tykkelse for linjer eller None)
        self.over = []     # detaljer uten kontur, tegnet til slutt

    # --- former med kontur
    def cap(self, x1, y1, x2, y2, w, fill):
        self.shapes.append(('line', dict(x1=x1, y1=y1, x2=x2, y2=y2), fill, w))

    def ell(self, cx, cy, rx, ry, fill, rot=0):
        t = f' transform="rotate({rot} {cx} {cy})"' if rot else ''
        self.shapes.append(('ellipse', dict(cx=cx, cy=cy, rx=rx, ry=ry, extra=t), fill, None))

    def rect(self, x, y, w, h, r, fill, rot=0):
        t = f' transform="rotate({rot} {x + w / 2} {y + h / 2})"' if rot else ''
        self.shapes.append(('rect', dict(x=x, y=y, width=w, height=h, rx=r, extra=t), fill, None))

    def poly(self, pts, fill):
        self.shapes.append(('polygon', dict(points=' '.join(f'{x},{y}' for x, y in pts)), fill, None))

    def path(self, d, fill):
        self.shapes.append(('path', dict(d=d), fill, None))

    # --- detaljer
    def line(self, x1, y1, x2, y2, w=3, color=INK):
        self.over.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>')

    def curve(self, d, w=3, color=INK, fill='none'):
        self.over.append(f'<path d="{d}" stroke="{color}" stroke-width="{w}" fill="{fill}" stroke-linecap="round" stroke-linejoin="round"/>')

    def raw(self, s):
        self.over.append(s)

    def svg_body(self):
        out = []
        for outline in (True, False):
            for kind, a, fill, w in self.shapes:
                extra = a.get('extra', '')
                attrs = ' '.join(f'{k}="{v}"' for k, v in a.items() if k != 'extra')
                if kind == 'line':
                    color = INK if outline else fill
                    width = w + 2 * O if outline else w
                    out.append(f'<line {attrs} stroke="{color}" stroke-width="{width}" stroke-linecap="round"{extra}/>')
                else:
                    if outline:
                        out.append(f'<{kind} {attrs} fill="{INK}" stroke="{INK}" stroke-width="{2 * O}" stroke-linejoin="round"{extra}/>')
                    else:
                        out.append(f'<{kind} {attrs} fill="{fill}"{extra}/>')
        return '\n'.join(out + self.over)


def medallion():
    return (f'<defs><clipPath id="inne"><circle cx="64" cy="64" r="53"/></clipPath></defs>'
            f'<circle cx="64" cy="64" r="57" fill="{INK}"/>'
            f'<circle cx="64" cy="64" r="53" fill="{CREAM}"/>'
            f'<path d="M 108 50 A 46 46 0 0 1 50 108 A 52 52 0 0 0 108 50 Z" fill="{CREAM_SH}"/>')


def rim():
    # Ringen tegnes over figuren, så armer og ermer som går ut av mynten, forsvinner under den
    return f'<circle cx="64" cy="64" r="55" fill="none" stroke="{INK}" stroke-width="5"/>'


def arrow(ic, x, y, direction, color=GREEN, size=1.0):
    """En liten pil med kontur. direction: up, down, left, right."""
    s = size
    base = [(-7, 0), (-7, -10), (-15, -10), (0, -24), (15, -10), (7, -10), (7, 0)]
    rot = {'up': lambda p: p, 'down': lambda p: (-p[0], -p[1]),
           'left': lambda p: (p[1], -p[0]), 'right': lambda p: (-p[1], p[0])}[direction]
    ic.poly([(x + rot(p)[0] * s, y + rot(p)[1] * s) for p in base], color)


def motion(ic, x, y, n=3, length=12, gap=8, vertical=False):
    for i in range(n):
        if vertical:
            ic.line(x + i * gap - gap * (n - 1) / 2, y, x + i * gap - gap * (n - 1) / 2, y + length, 4)
        else:
            ic.line(x, y + i * gap - gap * (n - 1) / 2, x + length, y + i * gap - gap * (n - 1) / 2, 4)


# ------------------------------------------------------------------ hender

def open_hand_up(ic, cx, cy, tilt=0):
    """Åpen hånd med fingrene opp, flaten mot oss. Senter i håndflaten."""
    ic.rect(cx - 15, cy - 8, 30, 30, 11, SKIN)                    # håndflate
    for i, (dx, top) in enumerate(((-11, -32), (-3.5, -37), (4, -35), (11, -28))):
        ic.cap(cx + dx, cy - 4, cx + dx + i * 0.6 - 1, cy + top, 8.5, SKIN)
    ic.cap(cx + 13, cy + 10, cx + 25, cy - 4, 9, SKIN)            # tommel
    ic.cap(cx - 4, cy + 22, cx - 4, cy + 30, 18, BLUE)           # erme
    ic.curve(f'M {cx - 8} {cy + 8} Q {cx} {cy + 13} {cx + 8} {cy + 6}', 2.5, SKIN_SH)


def fist(ic, cx, cy, knuckles='up'):
    """Knyttet neve sett fra siden, knokene mot høyre."""
    ic.rect(cx - 15, cy - 14, 30, 28, 12, SKIN)
    ic.cap(cx - 13, cy - 6, cx + 4, cy - 9, 9, SKIN)              # tommel over fingrene
    ic.line(cx + 4, cy - 2, cx + 15, cy - 2, 2.5)
    ic.line(cx + 4, cy + 6, cx + 15, cy + 6, 2.5)


# ------------------------------------------------------------------ ikonene

def ikon_push():
    ic = Icon()
    motion(ic, 22, 62, 3, 12, 10)
    # hånd med flaten mot høyre, fingrene opp
    ic.cap(48, 92, 30, 104, 16, BLUE)                             # erme
    ic.rect(46, 52, 28, 40, 12, SKIN)                             # håndflate fra siden
    for i, y in enumerate((36, 32, 34, 40)):
        x = 52 + i * 6
        ic.cap(x, 60, x + 2, y, 7.5, SKIN)
    ic.cap(50, 72, 40, 58, 8, SKIN)                               # tommel
    ic.rect(76, 40, 22, 56, 4, WOOD)                              # kassen den dytter
    ic.line(80, 52, 94, 52, 3, WOOD_SH)
    ic.line(80, 68, 94, 68, 3, WOOD_SH)
    ic.line(80, 84, 94, 84, 3, WOOD_SH)
    return ic


def ikon_pull():
    ic = Icon()
    ic.cap(26, 34, 26, 98, 7, METAL)                              # stang festet til veggen
    ic.cap(26, 66, 56, 66, 9, RED)                                # håndtaket
    ic.cap(86, 70, 104, 78, 16, BLUE)                             # erme
    ic.rect(56, 52, 32, 30, 12, SKIN)                             # neve rundt håndtaket
    ic.cap(58, 58, 74, 54, 8, SKIN)
    ic.line(58, 64, 70, 64, 2.5)
    ic.line(58, 72, 70, 72, 2.5)
    arrow(ic, 64, 100, 'left', GREEN, 0.75)
    return ic


def ikon_pickup():
    ic = Icon()
    ic.ell(56, 92, 13, 12, RED)                                    # tingen
    ic.raw(f'<ellipse cx="51" cy="88" rx="4" ry="3" fill="{WHITE}" opacity="0.8"/>')
    # hånd ovenfra med fingrene ned rundt tingen
    ic.cap(58, 24, 58, 36, 20, BLUE)
    ic.rect(42, 34, 32, 28, 12, SKIN)
    for i, dx in enumerate((-12, -4, 4, 12)):
        ic.cap(58 + dx, 56, 58 + dx * 1.15, 74 - abs(dx) * 0.3, 7.5, SKIN)
    ic.cap(72, 46, 80, 62, 8, SKIN)                               # tommel
    arrow(ic, 94, 76, 'up', GREEN, 0.8)
    return ic


def ikon_give():
    ic = Icon()
    # gaven
    ic.rect(50, 30, 34, 30, 3, RED)
    ic.rect(63, 30, 8, 30, 0, GOLD)
    ic.rect(50, 40, 34, 7, 0, GOLD)
    ic.ell(60, 26, 7, 5, GOLD, -20)
    ic.ell(74, 26, 7, 5, GOLD, 20)
    # hånd med flaten opp under gaven
    ic.cap(26, 82, 40, 76, 16, BLUE)
    ic.path('M 40 66 Q 64 70 96 62 Q 104 66 98 74 Q 70 88 44 86 Z', SKIN)
    ic.cap(54, 66, 68, 58, 8, SKIN)                               # tommel
    ic.curve('M 60 78 Q 76 77 92 70', 2.5, SKIN_SH)
    return ic


def door(ic, open_):
    ic.rect(34, 24, 52, 82, 3, WOOD_SH)                            # karm
    if open_:
        ic.rect(40, 30, 40, 76, 0, GOLD)                           # lyset gjennom døra
        ic.poly([(40, 30), (58, 38), (58, 112), (40, 106)], WOOD)  # dørbladet slått opp
        ic.ell(53, 74, 3, 3.5, GOLD)
    else:
        ic.rect(40, 30, 40, 76, 0, WOOD)
        ic.rect(46, 38, 28, 24, 2, WOOD_SH)
        ic.rect(46, 70, 28, 28, 2, WOOD_SH)
        ic.ell(72, 68, 4, 4, GOLD)


def ikon_open():
    ic = Icon()
    door(ic, True)
    for x1, y1, x2, y2 in ((84, 40, 96, 34), (86, 62, 100, 62), (84, 84, 96, 90)):
        ic.line(x1, y1, x2, y2, 4, GOLD_SH)
    return ic


def ikon_close():
    ic = Icon()
    door(ic, False)
    return ic


def bulb(ic, on):
    glass = GOLD if on else METAL
    ic.ell(64, 52, 22, 22, glass)
    ic.rect(54, 66, 20, 14, 4, glass)
    ic.rect(53, 80, 22, 16, 3, METAL_SH)
    ic.line(55, 85, 73, 85, 2.5)
    ic.line(55, 91, 73, 91, 2.5)
    ic.curve('M 58 70 L 60 56 L 64 62 L 68 56 L 70 70', 2.5, GOLD_SH if on else DARK_GLASS)
    ic.raw(f'<ellipse cx="56" cy="44" rx="5" ry="7" fill="{WHITE}" opacity="0.7" transform="rotate(30 56 44)"/>')
    if on:
        for x1, y1, x2, y2 in ((64, 20, 64, 12), (36, 32, 30, 26), (92, 32, 98, 26),
                               (30, 54, 22, 54), (98, 54, 106, 54)):
            ic.line(x1, y1, x2, y2, 4.5, GOLD_SH)


def ikon_turn_on():
    ic = Icon()
    bulb(ic, True)
    return ic


def ikon_turn_off():
    ic = Icon()
    bulb(ic, False)
    return ic


def hat(ic, y):
    ic.ell(64, y + 16, 34, 9, BLUE)                                # brem
    ic.rect(44, y - 12, 40, 28, 10, BLUE)                          # pull
    ic.rect(44, y + 4, 40, 7, 0, RED)                              # bånd
    ic.curve(f'M 34 {y + 17} Q 64 {y + 27} 94 {y + 17}', 2.5, BLUE_SH)


def ikon_put_on():
    ic = Icon()
    hat(ic, 74)
    arrow(ic, 64, 40, 'down', GREEN, 0.8)
    return ic


def ikon_take_off():
    ic = Icon()
    hat(ic, 46)
    arrow(ic, 64, 108, 'up', GREEN, 0.8)
    return ic


def ikon_read():
    ic = Icon()
    ic.path('M 22 64 Q 64 24 106 64 Q 64 104 22 64 Z', WHITE)      # øyet
    ic.ell(64, 64, 17, 17, BLUE)
    ic.raw(f'<circle cx="64" cy="64" r="8" fill="{INK}"/>')
    ic.raw(f'<circle cx="59" cy="58" r="4" fill="{WHITE}"/>')
    ic.curve('M 26 54 Q 64 18 102 54', 4)                          # øyelokket
    for x1, y1, x2, y2 in ((40, 38, 36, 30), (64, 31, 64, 23), (88, 38, 92, 30)):
        ic.line(x1, y1, x2, y2, 4)
    return ic


def gear_path(cx, cy, r_out, r_in, teeth):
    import math
    pts = []
    for i in range(teeth * 4):
        a = 2 * math.pi * i / (teeth * 4)
        r = r_out if i % 4 in (1, 2) else r_in
        pts.append((round(cx + r * math.cos(a), 2), round(cy + r * math.sin(a), 2)))
    return pts


def ikon_use():
    ic = Icon()
    ic.poly(gear_path(64, 64, 38, 29, 10), METAL)
    ic.ell(64, 64, 12, 12, CREAM)
    ic.curve('M 46 82 A 26 26 0 0 0 86 78', 4, METAL_SH)
    return ic


def coin(ic, cx, cy):
    ic.ell(cx, cy, 24, 24, GOLD)
    ic.raw(f'<circle cx="{cx}" cy="{cy}" r="17" fill="none" stroke="{GOLD_SH}" stroke-width="3"/>')
    ic.raw(f'<text x="{cx}" y="{cy + 10}" font-family="DejaVu Sans" font-weight="bold" font-size="28" '
           f'text-anchor="middle" fill="{GOLD_SH}">$</text>')


def ikon_buy():
    ic = Icon()
    coin(ic, 58, 60)
    arrow(ic, 90, 86, 'down', GREEN, 0.75)
    return ic


def ikon_sell():
    ic = Icon()
    coin(ic, 58, 68)
    arrow(ic, 90, 58, 'up', RED, 0.75)
    return ic


def star(cx, cy, r1, r2, n=4):
    import math
    pts = []
    for i in range(2 * n):
        a = math.pi * i / n - math.pi / 2
        r = r1 if i % 2 == 0 else r2
        pts.append((round(cx + r * math.cos(a), 2), round(cy + r * math.sin(a), 2)))
    return pts


def ikon_teleport():
    ic = Icon()
    ic.poly(star(64, 60, 30, 9), PURPLE)
    ic.poly(star(36, 88, 13, 4), GOLD)
    ic.poly(star(92, 90, 10, 3), GOLD)
    ic.poly(star(94, 34, 9, 3), GOLD)
    ic.raw(f'<circle cx="64" cy="60" r="5" fill="{WHITE}"/>')
    return ic


# verbnummer i Zak -> (filnavn, tegnefunksjon)
IKONER = {
    1: ('push', ikon_push), 2: ('open', ikon_open), 4: ('put-on', ikon_put_on),
    5: ('turn-on', ikon_turn_on), 6: ('pull', ikon_pull), 7: ('close', ikon_close),
    8: ('pick-up', ikon_pickup), 9: ('take-off', ikon_take_off), 10: ('turn-off', ikon_turn_off),
    11: ('give', ikon_give), 12: ('read', ikon_read), 14: ('use', ikon_use),
    15: ('buy', ikon_buy), 16: ('sell', ikon_sell), 17: ('teleport', ikon_teleport),
}


def svg(ic):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{STR}" height="{STR}" viewBox="0 0 {STR} {STR}">\n'
            f'{medallion()}\n<g clip-path="url(#inne)">\n{ic.svg_body()}\n</g>\n{rim()}\n</svg>\n')


def render(svg_text, size):
    return subprocess.run(['rsvg-convert', '-w', str(size), '-h', str(size), '-f', 'png'],
                          input=svg_text.encode(), capture_output=True, check=True).stdout


def optimize(data):
    from PIL import Image
    buf = io.BytesIO()
    Image.open(io.BytesIO(data)).convert('RGBA').save(buf, 'PNG', optimize=True)
    return buf.getvalue()


def b64_lines(ident, data):
    """Base64 i strengbiter på 100 tegn (C-strenger slås sammen av kompilatoren)."""
    enc = base64.b64encode(data).decode()
    out = [f'static const char *const {ident} =']
    for i in range(0, len(enc), 100):
        out.append(f'\t"{enc[i:i + 100]}"')
    out[-1] += ';'
    return out


def write_all():
    UT.mkdir(parents=True, exist_ok=True)
    pngs = {}
    for verb, (name, fn) in IKONER.items():
        s = svg(fn())
        (UT / f'{name}.svg').write_text(s)
        data = optimize(render(s, PNG))
        (UT / f'{name}.png').write_bytes(data)
        pngs[verb] = (name, data)
    return pngs


def contact_sheet(pngs, out):
    from PIL import Image, ImageDraw
    sizes = (256, 96, 64)
    cols = len(pngs)
    W = sum(sizes) + 40
    sheet = Image.new('RGB', (cols * 270, W), (58, 52, 70))
    d = ImageDraw.Draw(sheet)
    for c, (verb, (name, data)) in enumerate(sorted(pngs.items())):
        im = Image.open(io.BytesIO(data)).convert('RGBA')
        y = 4
        for s in sizes:
            small = im.resize((s, s), Image.LANCZOS)
            sheet.paste(small, (c * 270 + (270 - s) // 2, y), small)
            y += s + 8
        d.text((c * 270 + 8, W - 22), f'{verb} {name}', fill=(255, 255, 255))
    sheet.save(out)


SKRIFT = ROOT / 'grafikk' / 'ui' / 'skrift' / 'ComicNeue-Bold.ttf'   # OFL, se OFL.txt der
SKRIFT_PX = 40     # skriftstørrelsen i motoren på en skjerm som er 4 ganger originalen


def font_atlas():
    """Tegnene 32 til 126 i Comic Neue Bold som gråtonebilde (alfa), og målene til hvert tegn:
    x, y, w, h i bildet, forskyvning fra pennen (ox, oy fra grunnlinjen) og fremdrift."""
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype(str(SKRIFT), SKRIFT_PX)
    ascent, descent = font.getmetrics()
    glyphs, x, y, rowh, W = [], 1, 1, 0, 512
    boxes = []
    for c in range(32, 127):
        ch = chr(c)
        l, t, r, b = font.getbbox(ch, anchor='ls')
        w, h = max(0, r - l), max(0, b - t)
        if x + w + 1 > W:
            x, y, rowh = 1, y + rowh + 1, 0
        boxes.append((ch, x, y, w, h, l, t, round(font.getlength(ch))))
        x += w + 1
        rowh = max(rowh, h)
    H = y + rowh + 1
    atlas = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(atlas)
    for ch, gx, gy, w, h, l, t, adv in boxes:
        if w and h:
            d.text((gx - l, gy - t), ch, font=font, fill=255, anchor='ls')
    # Hvit med alfa (RGBA), så motoren leser den som ikonene
    rgba = Image.new('RGBA', (W, H), (255, 255, 255, 0))
    rgba.putalpha(atlas)
    buf = io.BytesIO()
    rgba.save(buf, 'PNG', optimize=True)
    return buf.getvalue(), boxes, ascent, descent


def write_cpp(pngs, out):
    lines = ['/* Laget av tools/verbhjul_ikoner.py. Ikke rediger for hånd.',
             ' * Ikonene til verbhjulet som PNG (RGBA, %d x %d), egne tegninger.' % (PNG, PNG),
             ' */', '', '#ifndef SCUMM_VERBHJUL_IKONER_H', '#define SCUMM_VERBHJUL_IKONER_H', '',
             'namespace Scumm {', '', 'struct VerbWheelIcon {', '\tint verb;', '\tconst char *name;',
             '\tconst char *png;      // base64', '\tunsigned int size;    // bytes after decoding', '};', '']
    for verb, (name, data) in sorted(pngs.items()):
        lines += b64_lines('kIcon_' + name.replace('-', '_'), data)
    lines.append('')
    lines.append('static const VerbWheelIcon kVerbWheelIcons[] = {')
    for verb, (name, data) in sorted(pngs.items()):
        lines.append(f'\t{{ {verb}, "{name}", kIcon_{name.replace("-", "_")}, {len(data)} }},')
    lines += ['\t{ 0, nullptr, nullptr, 0 }', '};', '']
    data, boxes, ascent, descent = font_atlas()
    lines.append('// Comic Neue Bold (SIL Open Font License 1.1), %d px, tegnene 32 til 126' % SKRIFT_PX)
    lines.append(f'static const int kVerbWheelFontPx = {SKRIFT_PX}, kVerbWheelFontAscent = {ascent}, kVerbWheelFontDescent = {descent};')
    lines.append(f'static const unsigned int kVerbWheelFontPngSize = {len(data)};')
    lines += b64_lines('kVerbWheelFontPng', data)
    lines.append('// x, y, w, h, ox, oy, advance')
    lines.append('static const short kVerbWheelGlyphs[95][7] = {')
    for ch, gx, gy, w, h, l, t, adv in boxes:
        lines.append(f'\t{{ {gx}, {gy}, {w}, {h}, {l}, {t}, {adv} }},')
    lines += ['};', '', '} // End of namespace Scumm', '', '#endif', '']
    Path(out).write_text('\n'.join(lines))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--ark', help='kontaktark (PNG)')
    ap.add_argument('--cpp', help='C-overskrift med PNG-ene til motoren')
    a = ap.parse_args()
    pngs = write_all()
    if a.ark:
        contact_sheet(pngs, a.ark)
    if a.cpp:
        write_cpp(pngs, a.cpp)
    print(f'{len(pngs)} ikoner i {UT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
