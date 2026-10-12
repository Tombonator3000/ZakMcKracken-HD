"""Tester for HD-pipelinen.

Vanlige tester trenger ikke spillfilene. Tester merket `game` bruker game/ og kjøres med:
    pytest -m game
"""
import struct
from pathlib import Path

import pytest
from PIL import Image

from zakhd import cli, gamedata, modpack, upscale

ROOT = Path(__file__).resolve().parents[2]
GAME = ROOT / "game"


@pytest.fixture(autouse=True)
def _figurpilot(monkeypatch):
    """Testene bruker et kunstig kostyme 14 med fire ark som pilot, slik The Dig hadde.
    Zak har ingen figurpilot ennå (FIG_PILOT er tom)."""
    from zakhd import figur
    monkeypatch.setattr(figur, "FIG_PILOT", {14: 4})


def _block(tag: bytes, body: bytes) -> bytes:
    return tag + struct.pack(">I", len(body) + 8) + body


def test_index_parsing_and_helpers(tmp_path):
    # Lager en liten LA0 med romnavn, MAXS og en kostymekatalog
    rnam = b"".join(bytes([n]) + bytes(c ^ 0xFF for c in name.ljust(9, b"\0")) for n, name in [(1, b"logo"), (22, b"beach")]) + b"\0"
    maxs = b"7.3.4".ljust(50, b"\0") + b"data".ljust(50, b"\0") + struct.pack("<15H", *range(15)) + bytes(8)
    dcos = struct.pack("<H", 3) + bytes([0, 22, 22]) + struct.pack("<3I", 0, 100, 200)
    la0 = tmp_path / "DIG.LA0"
    la0.write_bytes(_block(b"RNAM", rnam) + _block(b"MAXS", maxs) + _block(b"DCOS", dcos))

    idx = gamedata.read_index(la0)
    assert idx.room_names == {1: "logo", 22: "beach"}
    assert idx.engine_version == "7.3.4"
    assert idx.maxs["rooms"] == 10 and idx.maxs["costumes"] == 14
    assert idx.costume_dir == [(0, 0), (22, 100), (22, 200)]

    # Kostyme-ID-er følger katalogen, ikke rekkefølgen i filen
    room = gamedata.Room(22, offset=1000, akos_offsets=[200, 100])
    assert gamedata.costume_ids(idx, {22: room}) == [2, 1]

    assert cli._rooms("22,24") == {22, 24}
    assert cli._rooms("20-22,30") == {20, 21, 22, 30}
    assert cli._rooms(None) is None
    assert cli._rooms("ingen") == set()


def test_v6_index_and_rooms_with_xor(tmp_path):
    """SCUMM v6 som Sam & Max: XOR 0x69, MAXS uten tekster, RMHD uten versjon, plass i CDHD, COST."""
    def xor(b: bytes) -> bytes:
        return bytes(c ^ 0x69 for c in b)

    maxs = struct.pack("<15H", 400, 16, 512, 189, 50, 0, 15, 70, 40, 3, 122, 95, 6, 2, 1100)
    dcos = struct.pack("<H", 2) + bytes([0, 1]) + struct.pack("<2I", 0, 0)  # offset fylles inn under
    pal = bytes(range(256)) * 3
    offs = _block(b"OFFS", struct.pack("<I", 12))   # fra starten av OFFS-dataene til fargene i APAL
    pals = _block(b"PALS", _block(b"WRAP", offs + _block(b"APAL", pal)))
    rmhd = _block(b"RMHD", struct.pack("<3H", 480, 200, 1))
    cycl = _block(b"CYCL", bytes([1, 0, 0]) + struct.pack(">HH", 10, 0) + bytes([16, 31]) + b"\0")
    rmim = _block(b"RMIM", _block(b"RMIH", struct.pack("<H", 1)) + _block(b"IM00", _block(b"SMAP", bytes(4)) + _block(b"ZP01", bytes(4))))
    imhd = _block(b"IMHD", struct.pack("<3H", 77, 2, 0) + bytes(6) + struct.pack("<2H", 48, 24))
    obim = _block(b"OBIM", imhd + _block(b"IM01", bytes(4)) + _block(b"IM02", bytes(4)))
    obcd = _block(b"OBCD", _block(b"CDHD", struct.pack("<H2h2H", 77, 120, 64, 48, 24) + bytes(7)))
    room = _block(b"ROOM", rmhd + cycl + pals + rmim + obim + obcd)
    cost = _block(b"COST", bytes(10))
    lflf_body = room + cost
    head = 8 + 8 + 1 + 5                                       # LECF-hode, LOFF-hode, antall, én oppføring
    room_off = head + 8                                        # ROOM står rett etter LFLF-hodet
    loff = _block(b"LOFF", bytes([1, 1]) + struct.pack("<I", room_off))
    data = loff + _block(b"LFLF", lflf_body)
    lecf = _block(b"LECF", data)
    dcos = struct.pack("<H", 2) + bytes([0, 1]) + struct.pack("<2I", 0, len(room))
    (tmp_path / "SAMNMAX.000").write_bytes(xor(_block(b"RNAM", b"\0") + _block(b"MAXS", maxs) + _block(b"DCOS", dcos)))
    (tmp_path / "SAMNMAX.001").write_bytes(xor(lecf))

    idx = gamedata.read_index(tmp_path / "SAMNMAX.000")
    assert idx.version == 6 and idx.xor == 0x69
    assert idx.maxs["rooms"] == 3 and idx.maxs["costumes"] == 2 and idx.maxs["global_objects"] == 1100
    rooms = gamedata.read_rooms(tmp_path / "SAMNMAX.001")
    r = rooms[1]
    assert r.version == 6 and (r.width, r.height) == (480, 200)
    assert r.has_zplane and len(r.palettes) == 1 and r.palettes[0] == pal
    assert r.cycles == [(16, 31, 10, 0)]
    o = r.objects[0]
    assert (o.obj_id, o.x, o.y, o.width, o.height, o.states) == (77, 120, 64, 48, 24, ["01", "02"])
    assert r.cost_offsets == [len(room)] and r.akos_offsets == []
    assert gamedata.costume_ids(idx, rooms) == [1]


def _bits(bitlist: list[int]) -> bytes:
    """Bitstrøm med minst signifikante bit først, som bitleserne i gfx.cpp."""
    out = bytearray((len(bitlist) + 7) // 8 + 2)
    for i, b in enumerate(bitlist):
        out[i // 8] |= b << (i % 8)
    return bytes(out)


def _num(v: int, n: int) -> list[int]:
    return [(v >> i) & 1 for i in range(n)]


def test_v6_strip_codecs():
    from zakhd import v6grafikk as v
    # Rå piksler (kodek 1), 8 x 2
    raw = bytes([1]) + bytes(range(16))
    pix, mask, code = v.decode_strip(raw, 0, 2, 5)
    assert code == 1 and pix == bytearray(range(16)) and all(mask)
    # BasicH (kodek 28, 8 bit per ny farge): farge 10, ny farge 20 etter fire piksler
    bits = [0, 0, 0] + [1, 0] + _num(20, 8) + [0, 0, 0, 0]
    pix, mask, _ = v.decode_strip(bytes([28, 10]) + _bits(bits), 0, 1, 5)
    assert list(pix) == [10, 10, 10, 10, 20, 20, 20, 20] and all(mask)
    # BasicH: +1 og så snu retningen (-1 to ganger)
    bits = [1, 1, 0] + [1, 1, 1] + [1, 1, 0] + [0, 0, 0, 0, 0]
    pix, _, _ = v.decode_strip(bytes([28, 10]) + _bits(bits), 0, 1, 5)
    assert list(pix) == [10, 9, 10, 11, 11, 11, 11, 11]
    # BasicV (kodek 18), 8 x 2: pikslene går nedover kolonnene
    bits = [1, 0] + _num(30, 8) + [0] * 14
    pix, _, _ = v.decode_strip(bytes([18, 10]) + _bits(bits), 0, 2, 5)
    assert list(pix[:8]) == [10] + [30] * 7 and list(pix[8:]) == [30] * 8
    # MajMin (kodek 108): farge 7, +2 (3 bit: 6 - 4), så ny farge 40 med 8 bit
    bits = [0] + [1, 1] + _num(6, 3) + [0, 0] + [1, 0] + _num(40, 8) + [0, 0, 0]
    pix, mask, _ = v.decode_strip(bytes([108, 7]) + _bits(bits), 0, 1, 5)
    assert list(pix) == [7, 7, 9, 9, 9, 40, 40, 40] and all(mask)
    # MajMin med gjentakelse: diff 0 og antall 3 (8 bit), så samme farge videre
    bits = [1, 1] + _num(4, 3) + _num(3, 8) + [0] * 10
    pix, _, _ = v.decode_strip(bytes([108, 7]) + _bits(bits), 0, 1, 5)
    assert list(pix) == [7] * 8
    # Med gjennomsiktighet (kodek 128): fargen 9 tegnes ikke
    bits = [0] + [1, 1] + _num(6, 3) + [0] * 10
    pix, mask, _ = v.decode_strip(bytes([128, 7]) + _bits(bits), 0, 1, 9)
    assert list(mask) == [1, 1, 0, 0, 0, 0, 0, 0]
    with pytest.raises(ValueError):
        v.decode_strip(bytes([99, 0, 0, 0]), 0, 1, 5)


def test_v6_smap_and_bomp():
    from zakhd import v6grafikk as v
    # SMAP med to striper, 16 x 1: stripe 0 rå, stripe 1 rå med andre verdier
    s0 = bytes([1]) + bytes([1] * 8)
    s1 = bytes([1]) + bytes([2] * 8)
    body = struct.pack("<2I", 16, 16 + len(s0)) + s0 + s1
    smap = _block(b"SMAP", body)
    bm = v.decode_smap(smap, 0, 16, 1, 5)
    assert list(bm.pixels) == [1] * 8 + [2] * 8 and bm.codecs == {1: 2}
    # BOMP 4 x 2: linje 1 er ett løp med farge 3, linje 2 er 4 bokstavelige byte (255 er gjennomsiktig)
    line1 = bytes([(3 << 1) | 1, 3])
    line2 = bytes([(3 << 1), 4, 255, 5, 6])
    data = struct.pack("<3H", 0, 4, 2) + bytes(4) + struct.pack("<H", len(line1)) + line1 + struct.pack("<H", len(line2)) + line2
    bm = v.decode_bomp(data, 0)
    assert (bm.width, bm.height) == (4, 2)
    assert list(bm.pixels) == [3, 3, 3, 3, 4, 255, 5, 6] and list(bm.mask) == [1, 1, 1, 1, 1, 0, 1, 1]


def _cost(fmt: int) -> bytes:
    """En liten COST-blokk: én animasjon med to ruter i lag 0."""
    ex = fmt in (0x60, 0x61)
    pal = bytes([0] + list(range(50, 65)))           # 16 farger
    head = bytes(6) + bytes([0, fmt]) + pal          # antall animasjoner 0 (bare animasjon 0)
    p = len(head)
    frame_offsets = p + 2
    data_offsets = p + 34
    anim = data_offsets + 2
    cmds = anim + 5
    table = cmds + 2
    cel0 = table + 4
    hdr0 = struct.pack("<6h", 2, 3, -1, -40, 0, 0) + (bytes([0xFF, 0xFF]) if ex else b"")
    rle0 = bytes([0x13, 0x01, 0x22])
    cel1 = cel0 + len(hdr0) + len(rle0)
    if ex:
        # Ruten bruker bildet til lag 0, kode 0 (ex1 = 0, ex2 = 0), med eget hode
        hdr1, rle1 = struct.pack("<6h", 2, 3, 0, 0, 0, 0) + bytes([0, 0]), b""
    else:
        hdr1, rle1 = struct.pack("<6h", 1, 3, 0, 0, 0, 0), bytes([0x30, 0x03])
    body = bytearray(head)
    body += struct.pack("<H", cmds)
    body += struct.pack("<16H", table, *([0] * 15))
    body += struct.pack("<H", anim)
    body += struct.pack("<HH", 0x8000, 0) + bytes([1])   # lag 0, kommando 0 og 1
    body += bytes([0, 1])                                 # kodene 0 og 1
    body += struct.pack("<2H", cel0, cel1)
    body += hdr0 + rle0 + hdr1 + rle1
    return _block(b"COST", bytes(body))


def test_v6_costume():
    from zakhd import v6grafikk as v
    c = v.decode_costume(_cost(0x58), 0)
    assert c.format == 0x58 and len(c.palette) == 16 and not c.errors
    assert c.animations == [{"valg": 0, "animasjon": 0, "retning": 0, "lag": 0, "ruter": [0, 1]}]
    a, b = c.cels
    assert (a.cel, a.width, a.height, a.rel_x, a.rel_y) == (0, 2, 3, -1, -40)
    # Løpene går nedover kolonnene: kolonne 0 er farge 1, kolonne 1 er 0, 2, 2
    assert list(a.colours) == [1, 0, 1, 2, 1, 2]
    assert list(a.pixels) == [50, 0, 50, 51, 50, 51] and list(a.mask) == [1, 0, 1, 1, 1, 1]
    # Antall 0 i den første byten: antallet står i neste byte
    assert (b.width, b.height) == (1, 3) and list(b.colours) == [3, 3, 3]
    # Format 0x60: ruten kan bruke bildet til en annen rute
    c = v.decode_costume(_cost(0x60), 0)
    assert list(c.cels[1].colours) == list(c.cels[0].colours) and c.cels[1].data == c.cels[0].data


@pytest.mark.game
def test_v3_extract_real_game(tmp_path):
    """Uttrekket av Zak (FM-Towns): alle rom, objektbilder, kostymeruter og tegnsett, uten feil."""
    if not (GAME / "00.LFL").exists():
        pytest.skip("game/ mangler, kjør tools/hent_spilldata.sh")
    import json
    from zakhd import eksport_v3
    meta = eksport_v3.export_rooms(GAME, tmp_path)
    assert not meta["errors"]
    assert sum(1 for r in meta["rooms"].values() if "codecs" in r) == 58
    assert sum(len(o["states"]) for r in meta["rooms"].values() for o in r["objects"]) == 585
    res = eksport_v3.export_costumes(GAME, tmp_path)
    assert not res["errors"] and res["costumes"] == 40 and res["written"] == 847
    cm = json.loads((tmp_path / "costumes.json").read_text())
    assert cm["1"]["format"] in ("0x58", "0x59") and cm["1"]["cels"]
    im = Image.open(tmp_path / "costumes" / f"costume001_{cm['1']['cels'][0]['cel']:03d}.png")
    assert im.mode == "RGBA" and im.size == (cm["1"]["cels"][0]["w"], cm["1"]["cels"][0]["h"])
    f = eksport_v3.export_fonts(GAME, tmp_path)
    assert f["0"]["tegn"] == 226 and f["0"]["hoeyde"] == 8


def test_upscale_and_alpha():
    im = Image.new("RGB", (10, 6), (200, 40, 10))
    for method in ("nearest", "lanczos", "lanczos-sharp"):
        out = upscale.upscale(im, 4, method)
        assert out.size == (40, 24)
        assert out.getpixel((20, 12)) == (200, 40, 10) or method != "nearest"
    alpha = Image.new("L", (3, 3), 0)
    alpha.putpixel((1, 1), 255)
    big = upscale.upscale_alpha(alpha, 4)
    assert big.size == (12, 12)
    assert set(big.tobytes()) == {0, 255}  # skarpe kanter, ingen halvgjennomsiktighet
    with pytest.raises(SystemExit):
        upscale.upscale(im, 4, "finnesikke")


def test_bleed_and_object_context():
    # En rød prikk på gjennomsiktig bakgrunn: bleed skal farge naboene røde
    cel = Image.new("RGBA", (5, 5), (0, 0, 0, 0))
    cel.putpixel((2, 2), (255, 0, 0, 255))
    filled = modpack._bleed(cel)
    assert filled.getpixel((1, 2)) == (255, 0, 0)

    # Objekt skalert i sammenheng med bakgrunnen: riktig størrelse og alfa fra originalen
    room = Image.new("RGB", (40, 30), (0, 0, 255))
    obj = Image.new("RGBA", (8, 6), (0, 255, 0, 255))
    obj.putpixel((0, 0), (0, 0, 0, 0))
    hd = modpack._upscale_object_in_context(room, obj, 10, 10, 4, "nearest")
    assert hd.size == (32, 24)
    assert hd.getpixel((0, 0))[3] == 0 and hd.getpixel((10, 10)) == (0, 255, 0, 255)


@pytest.mark.game
def test_real_game_files():
    if not (GAME / "00.LFL").exists():
        pytest.skip("game/ mangler, kjør tools/hent_spilldata.sh")
    from zakhd import lfl
    idx = lfl.les_indeks(GAME / "00.LFL")
    assert idx.md5 == cli.KNOWN_INDEX_MD5
    assert idx.plasser == {"0R": 99, "0S": 199, "0N": 199, "0C": 199}
    assert len(idx.skript) == 169 and len(idx.kostymer) == 40 and len(idx.lyder) == 120 and idx.objekter == 1000
    rooms = lfl.les_alle_rom(GAME)
    med_ro = {n: r for n, r in rooms.items() if r.ro_size}
    assert len(rooms) == 59 and len(med_ro) == 58 and not rooms[47].ro_size
    assert sum(r.bredde > 320 for r in med_ro.values()) == 34
    assert all(r.hoeyde == 128 for n, r in med_ro.items() if n != 46) and med_ro[46].hoeyde == 136
    assert sum(len(r.objekter) for r in med_ro.values()) == 770
    assert (rooms[1].bredde, rooms[1].hoeyde, rooms[1].farger) == (320, 128, 256)
    assert rooms[1].objekter[0].navn == "rope"


def test_v3_strip_codecs():
    """Stripekodekene for GF_OLD256 fyller kolonne for kolonne (NEXT_ROW i gfx.cpp)."""
    from zakhd import v3grafikk as v
    h = 2
    # Kode 1: rå, 16 byte i kolonnerekkefølge
    raw = bytes([1]) + bytes(range(16))
    pix, mask, code = v.decode_strip_old256(raw, 0, h)
    assert code == 1 and all(mask)
    assert pix[0] == 0 and pix[8] == 1 and pix[1] == 2 and pix[9] == 3   # kolonne 0: 0,1; kolonne 1: 2,3
    # Kode 2: løp (antall - 1, farge)
    pix, _, _ = v.decode_strip_old256(bytes([2, 7, 5, 7, 6]), 0, h)
    col = [pix[y * 8 + x] for x in range(8) for y in range(h)]
    assert col == [5] * 8 + [6] * 8
    # Kode 4: lokal palett med to farger, så et løp på 14 med farge 9
    pix, _, _ = v.decode_strip_old256(bytes([4, 2, 40, 41, 0, 1, 2 + 13, 9]), 0, h)
    col = [pix[y * 8 + x] for x in range(8) for y in range(h)]
    assert col == [40, 41] + [9] * 14
    # Kode 7: lik farge hele veien når alle bit er 0
    pix, _, _ = v.decode_strip_old256(bytes([7, 33, 0, 0]), 0, h)
    assert set(pix) == {33}
    # Kode 3: 4-bit med løp: c=0b0010 (gjenta (c&3)+2=4 ganger farge 3), fire ganger
    bits = []
    for _ in range(4):
        bits += [0, 1, 0, 0] + [1, 1, 0, 0]          # c = 2 (lsb først), farge = 3
    data = bytearray()
    for i in range(0, len(bits), 8):
        data.append(sum(b << k for k, b in enumerate(bits[i:i + 8])))
    pix, _, _ = v.decode_strip_old256(bytes([3]) + bytes(data), 0, h)
    assert set(pix) == {3}


def test_v3_bm_and_zplane():
    """Et BM-bilde med to striper og et z-plan (stripe 1 har maske)."""
    from zakhd import v3grafikk as v
    import struct
    h = 2
    s0 = bytes([2, 15, 1])          # 16 piksler farge 1
    s1 = bytes([2, 15, 2])
    hode = 4 + 2 * 4
    smap = struct.pack("<III", hode + len(s0) + len(s1), hode, hode + len(s0)) + s0 + s1
    z_off = 4 + 2 * 2
    z = struct.pack("<I", 1) + struct.pack("<HH", 0, z_off) + bytes([0x82, 0xF0])   # 2 rader med 0xF0
    bm = v.decode_bm(smap + z, 0, 16, h)
    assert bm.codecs == {2: 2} and bm.pixels[0] == 1 and bm.pixels[8] == 2
    assert bm.zplan is not None and bm.zplan_striper == 1
    assert list(bm.zplan[8:16]) == [1, 1, 1, 1, 0, 0, 0, 0] and not any(bm.zplan[:8])


def test_v3_costume_one_byte_start():
    """I v3 er startindeksen i animasjonene én byte (costumeDecodeData)."""
    from zakhd import v3grafikk as v
    import struct
    pal = bytes(range(16))
    # Hode: størrelse, 'CO', antall animasjoner, format 0x58, palett, animCmds-offset, 16 rammeoffsets, animasjonsoffsets
    p = 8 + 16
    frame_offsets = p + 2
    data_offsets = p + 34
    anim = data_offsets + 2               # én animasjon (nr 0)
    animdata = struct.pack("<H", 0x8000) + bytes([0, 0])      # lag 0: start 0, extra 0
    cmds = anim + len(animdata)
    cmddata = bytes([0])                  # kode 0
    frame = cmds + len(cmddata)
    celtab = struct.pack("<H", frame + 2)
    cel = frame + 2
    celdata = struct.pack("<hhhhhh", 1, 2, 0, 0, 0, 0) + bytes([0x12, 0x00])   # farge 1, 2 piksler
    body = bytearray(cel + len(celdata))
    body[4:6] = b"CO"
    body[6] = 0
    body[7] = 0x58
    body[8:24] = pal
    struct.pack_into("<H", body, p, cmds)
    struct.pack_into("<H", body, frame_offsets, frame)
    struct.pack_into("<H", body, data_offsets, anim)
    body[anim:anim + len(animdata)] = animdata
    body[cmds:cmds + 1] = cmddata
    body[frame:frame + 2] = celtab
    body[cel:cel + len(celdata)] = celdata
    struct.pack_into("<I", body, 0, len(body))
    c = v.decode_costume_v3(bytes(body), 0)
    assert not c.errors and len(c.cels) == 1
    assert (c.cels[0].width, c.cels[0].height) == (1, 2) and list(c.cels[0].colours) == [1, 1]


def test_costume_colours(tmp_path):
    import numpy as np
    from zakhd import export

    # Kodene 0 til 63 er en jevn overgang i rommets riktige palett (palett 1). Palett 0 har
    # de samme fargene i en annen rekkefølge, slik en feil palett gir prikkete bilder.
    ramp = bytes(v for k in range(256) for v in (4 * (k % 64), 2 * (k % 64), 255 - 4 * (k % 64)))
    order = list(range(256))
    np.random.default_rng(5).shuffle(order)
    shuffled = bytes(v for k in order for v in ramp[3 * k:3 * k + 3])
    rooms = {7: gamedata.Room(7, offset=0, palettes=[shuffled, ramp])}
    codes = np.tile(np.arange(64, dtype=np.uint8), (16, 1))
    codes[0, :8] = 255  # gjennomsiktig (kodek 5 og 16)
    cels = [(codes, 255)]
    rgb = [np.frombuffer(p, np.uint8).reshape(256, 3) for p in (shuffled, ramp)]
    assert export.smoothness(rgb[1], cels) < export.smoothness(rgb[0], cels) / 4

    rgbs = bytes(range(256)) * 3
    akpl = bytes(range(256))
    # Kodek 5 og 16 uten tabell: kodene rett i den jevneste paletten i hjemmerommet
    for codec in (export.CODEC_BOMP, export.CODEC_MAJMIN):
        pal, how = export.costume_palette(codec, akpl, rgbs, 7, rooms, cels, None)
        assert pal == ramp and how["kind"] == "rom" and how["palette"] == 1 and how["source"] == "jevnest"
    # Like jevne paletter: den første, som rommet starter med
    same = {8: gamedata.Room(8, offset=0, palettes=[ramp, shuffled, ramp])}
    assert export.costume_palette(export.CODEC_BOMP, akpl, rgbs, 8, same, cels, None)[1]["palette"] == 0
    # Kodek 1: RGBS som før, uansett rom
    pal, how = export.costume_palette(export.CODEC_BYLE, akpl, rgbs, 7, rooms, cels, None)
    assert pal == rgbs[:768] and how == {"kind": "rgbs"}
    # Kodek 1 uten RGBS: AKPL-plassen i hjemmerommets første palett
    pal, _ = export.costume_palette(export.CODEC_BYLE, bytes([3, 9]), b"", 7, rooms, cels, None)
    assert pal[:6] == shuffled[9:12] + shuffled[27:30] and pal[6:9] == shuffled[6:9]

    # Tabellen går foran: rom og palett, eller RGBS for kostymer skriptet setter paletten på
    csv_path = tmp_path / "kostymefarger.csv"
    csv_path.write_text("kostyme,farger,rom,palett,kilde,notat\n"
                        "96,rom,7,0,målt,Spøkelset\n"
                        "120,rgbs,,,målt,\n", encoding="utf-8")
    table = export.read_costume_colours(csv_path)
    assert table[96] == {"kind": "rom", "room": 7, "palette": 0, "source": "målt"}
    assert table[120]["kind"] == "rgbs"
    pal, how = export.costume_palette(export.CODEC_MAJMIN, akpl, b"", 2, rooms, cels, table[96])
    assert pal == shuffled and how["source"] == "målt" and how["room"] == 7
    pal, how = export.costume_palette(export.CODEC_BOMP, akpl, rgbs, 7, rooms, cels, table[120])
    assert pal == rgbs[:768] and how["kind"] == "rgbs"
    assert export.read_costume_colours(tmp_path / "finnes-ikke.csv") == {}
    csv_path.write_text("kostyme,farger,rom,palett,kilde,notat\n5,feil,1,0,,\n", encoding="utf-8")
    with pytest.raises(ValueError):
        export.read_costume_colours(csv_path)

    # Tabellen i repoet kan leses, og hver kostyme står bare én gang
    path = ROOT / "docs" / "kostymefarger.csv"
    table = export.read_costume_colours(path)
    ids = [line.split(",")[0] for line in path.read_text(encoding="utf-8").splitlines()[1:] if line.strip()]
    assert len(table) == len(ids) == len(set(ids)) and all(t["kind"] in ("rom", "rgbs") for t in table.values())


def test_gpt_tiles_shift_and_judge():
    from zakhd import gpt
    import numpy as np

    # Vanlig rom: én jobb med grå kant, nøyaktig 4x på lerretet
    assert gpt.plan_tiles(320, 200) == [(0, 0, 320, 200, 32, 28)]
    # Bredt rom: flere deler som dekker hele bredden og overlapper
    tiles = gpt.plan_tiles(976, 200)
    assert len(tiles) == 3 and tiles[0][0] == 0 and tiles[-1][0] + tiles[-1][2] == 976
    assert all(t[2] == 384 for t in tiles)
    # Høyt rom deles i høyden
    assert len(gpt.plan_tiles(320, 528)) == 3

    # Fasekorrelasjon finner en kjent forskyvning med riktig fortegn
    rng = np.random.default_rng(0)
    base = gpt.blur(rng.random((96, 128)), 1.5)
    moved = np.roll(base, (2, -3), axis=(0, 1))
    dx, dy, _ = gpt.phase_shift(base, moved)
    assert abs(dx + 3) < 0.3 and abs(dy - 2) < 0.3

    assert gpt.judge({"skift_x": 0.1, "skift_y": 0.0, "blokk_maks": 0.3, "kantlikhet": 0.8})[0] == "godkjent"
    assert gpt.judge({"skift_x": 0.0, "skift_y": 0.0, "blokk_maks": 1.4, "kantlikhet": 0.8})[0] == "sjekk"
    assert gpt.judge({"skift_x": 3.0, "skift_y": 0.0, "blokk_maks": 3.0, "kantlikhet": 0.5})[0] == "avvist"


def test_gpt_lock_and_stitch():
    from zakhd import gpt
    import numpy as np

    # Fargelås fjerner et fargestikk, men beholder fin detalj
    rng = np.random.default_rng(1)
    orig = np.full((64, 64, 3), 100.0)
    detail = rng.normal(0, 8, (64, 64, 3))
    cand = orig + 40 + detail
    locked = gpt.lock_colors(cand, orig, sigma=6, strength=1.0)
    assert abs(locked.mean() - 100) < 1.5
    assert locked.std() > 5

    # To like deler sys sammen uten skjøt
    W, H = 600, 200
    full = rng.random((H * gpt.SCALE, W * gpt.SCALE, 3)) * 255
    parts = []
    for x, y, w, h, _, _ in gpt.plan_tiles(W, H):
        parts.append(((x, y, w, h), full[y * 4:(y + h) * 4, x * 4:(x + w) * 4]))
    out = gpt._stitch(W, H, parts)
    assert np.abs(out.astype(float) - full).max() <= 1.0


def test_gpt_layout_and_orders(tmp_path):
    from zakhd import gpt

    # Hele lerretet, bare bildet i rommets sideforhold, eller feil
    assert gpt.detect_layout((1536, 1024), (320, 200)) == "lerret"
    assert gpt.detect_layout((1280, 800), (320, 200)) == "direkte"
    assert gpt.detect_layout((1024, 1024), (320, 200)) is None
    # Utsnitt som selv er 3:2 regnes som lerret
    assert gpt.detect_layout((1536, 1024), (384, 256)) == "lerret"

    rows = [
        ("rom002_del1av3", 2, "ny", ""),
        ("rom009", 9, "godkjent", ""),
        ("rom010", 10, "avvist", "forskjøvet 3 px"),
        ("rom011", 11, "sjekk", "kantlikhet 0,50"),
    ]
    with (tmp_path / "status.csv").open("w", encoding="utf-8") as f:
        f.write(",".join(gpt.STATUS_FIELDS) + "\n")
        for jobb, rom, status, kommentar in rows:
            row = {k: "" for k in gpt.STATUS_FIELDS}
            row.update(jobb=jobb, rom=rom, navn="x", status=status, kommentar=kommentar)
            row["del"] = "1/1"
            f.write(",".join(str(row[k]) for k in gpt.STATUS_FIELDS) + "\n")
    text = gpt.write_orders(tmp_path, batch=2, anchors=["room009_core.png"], messages=["Hei"]).read_text()
    # Avviste først, så nye. Sjekk-jobben kommer ikke med når køen er full.
    assert text.index("rom010") < text.index("rom002_del1av3")
    assert "1. `rom010`" in text and "rom011" not in text
    assert "Ferdige rom: 1 av 4 (9)" in text
    assert "stil/room009_core.png" in text and "- Hei" in text
    tasks = tmp_path / "oppgaver.md"
    tasks.write_text("1. Test på laptopen.\n", encoding="utf-8")
    text = gpt.write_orders(tmp_path, tasks=tasks).read_text()
    assert "## Kodeoppgaver" in text and "1. Test på laptopen." in text
    lst = gpt.write_list(tmp_path, batch=2).read_text()
    # Samme rekkefølge som ordren, delt i bestillinger, og ferdige jobber krysset av
    assert lst.index("## Bestilling 1") < lst.index("rom010") < lst.index("rom002_del1av3") < lst.index("## Bestilling 2")
    assert "- [x] `rom009`" in lst and "rom011" in lst.split("## Bestilling 2")[1]


def _texture(rng, w, h, sigma=2.0):
    """Kunstig bilde med former og farger, så kontrollen har noe å kjenne igjen."""
    from zakhd import gpt
    import numpy as np

    a = np.stack([gpt.blur(rng.random((h, w)), sigma) for _ in range(3)], axis=-1)
    a = (a - a.min()) / (a.max() - a.min()) * 255
    return Image.fromarray(a.astype("uint8"))


def _fake_extract(tmp_path):
    """Et lite uttrekk: rom 5 (320 x 200) med ett stort objektbilde med gjennomsiktig hjørne og ett lite."""
    import json
    import numpy as np

    rng = np.random.default_rng(3)
    ex = tmp_path / "extract"
    (ex / "rooms").mkdir(parents=True)
    (ex / "objects").mkdir()
    room = _texture(rng, 320, 200)
    room.save(ex / "rooms" / "room005.png")
    Image.new("P", (320, 200)).save(ex / "rooms" / "room005_idx.png")
    big = _texture(rng, 220, 120, 1.5).convert("RGBA")
    for x in range(60):
        for y in range(40):
            big.putpixel((x, y), (255, 0, 255, 0))   # gjennomsiktig, fargen skal ikke synes
    big.save(ex / "objects" / "obj241_01.png")
    Image.new("P", (220, 120)).save(ex / "objects" / "obj241_01_idx.png")
    Image.new("RGBA", (20, 20), (9, 9, 9, 255)).save(ex / "objects" / "obj007_01.png")
    Image.new("P", (20, 20)).save(ex / "objects" / "obj007_01_idx.png")
    meta = {"game_md5_la0": "x", "rooms": {"5": {
        "name": "testrom", "width": 320, "height": 200, "palettes": 1, "zplane": False, "cycles": [],
        "objects": [{"id": 241, "x": 40, "y": 30, "w": 220, "h": 120, "states": ["01"]},
                    {"id": 7, "x": 10, "y": 10, "w": 20, "h": 20, "states": ["01"]}]}}}
    (ex / "rooms.json").write_text(json.dumps(meta))
    return ex, room, big


def test_gpt_object_jobs_and_import(tmp_path):
    import json
    from PIL import ImageFilter
    from zakhd import gpt

    ex, room, big = _fake_extract(tmp_path)
    work, done = tmp_path / "gpt", tmp_path / "gpt-ferdig"
    jobs = gpt.make_jobs(ex, work, notes={5: "Test note."})
    # Romjobben først, så det store objektbildet. Det lille kommer i en lagjobb til slutt.
    assert [j.id for j in jobs] == ["rom005", "obj241_01", "lag005_01"]
    assert [r["type"] for r in gpt.read_status(work)] == ["rom", "objekt", "lag"]

    d = work / "jobber" / "obj241_01"
    data = json.loads((d / "jobb.json").read_text())
    assert data["type"] == "objekt" and data["objekt"] == 241 and data["tilstand"] == "01"
    assert data["objekt_i_rom"] == [40, 30, 220, 120] and data["region"] == [0, 0, 220, 120]
    ox, oy = (384 - 220) // 2, (256 - 120) // 2
    assert data["plassering"] == [ox, oy] and data["bilde_i_lerret"] == [ox * 4, oy * 4, 880, 480]
    room_job = json.loads((work / "jobber" / "rom005" / "jobb.json").read_text())
    assert room_job["type"] == "rom" and room_job["objekt"] is None

    # Samme lerret og kant som rommene, objektet i 4x på riktig sted
    ref = Image.open(d / "referanse.png")
    assert ref.size == (1536, 1024) and ref.getpixel((0, 0)) == gpt.BORDER

    def at(x, y):
        return ref.getpixel(((ox + x) * 4 + 2, (oy + y) * 4 + 2))

    # Gjennomsiktig del: rommet bak objektet. Synlig del: objektet.
    assert at(5, 5) == room.getpixel((40 + 5, 30 + 5))
    assert at(100, 80) == big.getpixel((100, 80))[:3]
    orig = Image.open(d / "original_1x.png")
    assert orig.size == (220, 120) and orig.getpixel((5, 5)) == room.getpixel((45, 35))
    prompt = (d / "prompt.txt").read_text()
    assert gpt.PROMPT_OBJECT in prompt and "Note for this room: Test note." in prompt
    assert prompt.startswith(gpt.PROMPT_BASE) and prompt.rstrip().endswith(gpt.PROMPT_STYLE)

    # Et riktig plassert, litt mykere resultat godkjennes og blir et HD-objekt i 4x
    ref.filter(ImageFilter.GaussianBlur(1.5)).save(d / "resultat.png")
    s = gpt.import_results(work, ex, done)
    assert s["ferdige_objekter"] == ["obj241_01"] and s["ferdige_rom"] == []
    assert (s["rom_totalt"], s["objekter_totalt"]) == (1, 1)
    status = {r["jobb"]: r for r in gpt.read_status(work)}
    assert status["obj241_01"]["status"] == "godkjent" and status["obj241_01"]["type"] == "objekt"
    hd = Image.open(done / "objects" / "obj241_01.png")
    assert hd.size == (880, 480) and hd.mode == "RGBA"
    assert hd.getpixel((5 * 4, 5 * 4))[3] == 0 and hd.getpixel((100 * 4, 80 * 4))[3] == 255
    assert not (done / "rooms" / "room005.png").exists()
    prov = json.loads((done / "provenance.json").read_text())["obj241_01"]
    assert prov["fil"] == "objects/obj241_01.png" and prov["storrelse"] == [880, 480]
    assert prov["type"] == "objekt" and prov["jobber"][0]["status"] == "godkjent"
    report = (work / "RAPPORT.md").read_text()
    assert "Ferdige rom: 0 av 1" in report and "Ferdige objekter: 1 av 1 (obj241_01)" in report
    orders = gpt.write_orders(work).read_text()
    assert "Ferdige rom: 0 av 1" in orders and "Ferdige objekter: 1 av 1 (obj241_01)" in orders
    assert "1. `rom005`" in orders

    # Modden: det godkjente objektbildet kommer med selv om rommet ikke har HD-bakgrunn
    m = modpack.build_mod(ex, tmp_path / "mod", scale=4, method="nearest", rooms=set(), own=done)
    assert m["rooms"] == [] and m["objects"] == ["obj241_01"]
    assert not (tmp_path / "mod" / "rooms" / "room005.png").exists()
    assert (tmp_path / "mod" / "objects" / "obj241_01_idx.png").exists()
    assert not (tmp_path / "mod" / "objects" / "obj007_01.png").exists()
    # Med rommet valgt: bakgrunnen og det lille objektet skaleres automatisk, det store er det egne
    m = modpack.build_mod(ex, tmp_path / "mod2", scale=4, method="nearest", rooms={5}, own=done)
    assert m["rooms"] == [5] and m["objects"] == ["obj007_01", "obj241_01"]
    assert Image.open(tmp_path / "mod2" / "objects" / "obj241_01.png").tobytes() == hd.tobytes()


def test_gpt_orders_with_objects(tmp_path):
    from zakhd import gpt

    # Gammel status.csv uten kolonnen type: alt er romjobber
    old = ["jobb", "rom", "navn", "del", "status", "kommentar"]
    with (tmp_path / "status.csv").open("w", encoding="utf-8") as f:
        f.write(",".join(old) + "\nrom009,9,core,1/1,godkjent,\nrom010,10,x,1/1,ny,\n")
    assert [r["type"] for r in gpt.read_status(tmp_path)] == ["rom", "rom"]
    assert "Ferdige rom: 1 av 2 (9)" in gpt.write_orders(tmp_path).read_text()

    rows = [
        ("rom002_del1av3", "rom", 2, "ny", ""),
        ("rom003", "rom", 3, "ny", ""),
        ("obj060_01", "objekt", 3, "ny", ""),
        ("rom009", "rom", 9, "godkjent", ""),
        ("obj050_01", "objekt", 9, "ny", ""),
        ("obj050_02", "objekt", 9, "godkjent", ""),
        ("rom010", "rom", 10, "avvist", "forskjøvet 3 px"),
        ("rom011", "rom", 11, "sjekk", "kantlikhet 0,50"),
    ]
    with (tmp_path / "status.csv").open("w", encoding="utf-8") as f:
        f.write(",".join(gpt.STATUS_FIELDS) + "\n")
        for jobb, typ, rom, status, kommentar in rows:
            row = {k: "" for k in gpt.STATUS_FIELDS}
            row.update(jobb=jobb, type=typ, rom=rom, navn="x", status=status, kommentar=kommentar)
            row["del"] = "1/1"
            f.write(",".join(str(row[k]) for k in gpt.STATUS_FIELDS) + "\n")
    text = gpt.write_orders(tmp_path, batch=10).read_text()
    # Avviste, så nye objektjobber i ferdige rom, så nye etter romnummer (rom før objekt), så sjekk
    order = ["rom010", "obj050_01", "rom002_del1av3", "rom003", "obj060_01", "rom011"]
    pos = [text.index(f"`{j}`") for j in order]
    assert pos == sorted(pos)
    assert "Ferdige rom: 1 av 5 (9)" in text and "Ferdige objekter: 1 av 3 (obj050_02)" in text
    assert "`obj050_01` (rom 9, x, objekt 50 tilstand 01, del 1/1)" in text


def test_gpt_object_notes_and_states(tmp_path):
    from zakhd import gpt
    import numpy as np
    from PIL import Image

    notes_csv = tmp_path / "notater.csv"
    notes_csv.write_text('rom,navn,notat\n28,shardcu,"Hands."\nobj241,shardcu,"No hands."\n', encoding="utf-8")
    notes = gpt.read_notes(notes_csv)
    assert notes == {28: "Hands.", "obj241": "No hands."}
    p = gpt._prompt(28, notes, 1, 1, is_object=True, obj_key="obj241")
    assert "No hands." in p and "Hands." not in p.replace("No hands.", "")
    assert gpt._prompt(28, notes, 1, 1, is_object=True, obj_key="obj999", later_state=True).endswith(gpt.PROMPT_STATE)

    # Senere tilstand: likt område tas fra første tilstand, forskjellen fra det nye bildet
    a = np.zeros((40, 40), np.uint8)
    b = a.copy()
    b[10:20, 10:20] = 7
    Image.fromarray(a, "L").convert("P").save(tmp_path / "base_idx.png")
    Image.fromarray(b, "L").convert("P").save(tmp_path / "ny_idx.png")
    base = np.full((160, 160, 3), 100, np.uint8)
    new = np.full((160, 160, 3), 200, np.uint8)
    out = gpt.match_state(new, base, tmp_path / "ny_idx.png", tmp_path / "base_idx.png")
    assert out[60, 60, 0] == 200          # midt i det som er forskjellig
    assert out[150, 150, 0] == 100        # langt unna: som første tilstand
    assert out[5, 5, 0] == 100


def test_gpt_manual_rejection(tmp_path):
    from zakhd import gpt

    rej = tmp_path / "avvisninger.csv"
    rej.write_text('jobb,sha256_resultat,grunn,forslag\nrom011,abc,"feil merker","Redo it."\nrom012,*,"alt",""\n',
                   encoding="utf-8")
    m = gpt.read_rejections(rej)
    assert m["rom011"]["grunn"] == "feil merker" and m["rom012"]["sha256_resultat"] == "*"
    d = tmp_path / "rom011"
    d.mkdir()
    gpt._write_return(d, {"status": "avvist", "kommentar": "feil merker", "forslag": "Redo it."})
    text = (d / "retur.md").read_text()
    assert "feil merker" in text and "Redo it." in text and "Precise correction" not in text


def _layer_extract(tmp_path, small=True):
    """Uttrekk med rom 6 (320 x 200) og objekter til lagjobbene.

    Rekkefølgen i listen er tegnerekkefølgen baklengs: obj020 (indeks 0) tegnes oppå det store obj024.
      obj020  20 x 16 på (60, 120), ligger oppå det store obj024 (underlag)
      obj021  30 x 20 på (20, 20), to tilstander, gjennomsiktig hjørne
      obj022  24 x 24 på (100, 10)
      obj023  20 x 20 på (110, 20), overlapper obj022 og må i et annet lag
      obj024  320 x 150 på (0, 50), stort objektbilde (egen objektjobb)
      obj025  16 x 16 på (0, 0), ikon
      obj026  helt gjennomsiktig, står igjen
    Med small=False er bare det store objektbildet med, som før lagjobbene fantes.
    """
    import json
    import numpy as np

    rng = np.random.default_rng(7)
    ex = tmp_path / "extract"
    (ex / "rooms").mkdir(parents=True)
    (ex / "objects").mkdir()
    room = _texture(rng, 320, 200, 3.0)
    room.save(ex / "rooms" / "room006.png")
    Image.new("P", (320, 200)).save(ex / "rooms" / "room006_idx.png")
    specs = [(20, 60, 120, 20, 16, ["01"]), (21, 20, 20, 30, 20, ["01", "02"]), (22, 100, 10, 24, 24, ["01"]),
             (23, 110, 20, 20, 20, ["01"]), (24, 0, 50, 320, 150, ["01"]), (25, 0, 0, 16, 16, ["01"]),
             (26, 200, 20, 16, 16, ["01"])]
    objects = []
    for oid, x, y, w, h, states in specs:
        images = [_texture(rng, w, h, 1.0).convert("RGBA") for _ in states]
        if not small and oid != 24:
            continue
        for k, (s, im) in enumerate(zip(states, images)):
            if oid == 21:
                for yy in range(5):
                    for xx in range(5):
                        im.putpixel((xx, yy), (255, 0, 255, 0))
            if oid == 26:
                im = Image.new("RGBA", (w, h), (255, 0, 255, 0))
            im.save(ex / "objects" / f"obj{oid:03d}_{s}.png")
            idx = np.zeros((h, w), np.uint8)
            idx[h // 2:, :] = 1 + k              # nedre halvdel skiller tilstandene, øvre er lik
            Image.fromarray(idx, "L").convert("P").save(ex / "objects" / f"obj{oid:03d}_{s}_idx.png")
        objects.append({"id": oid, "x": x, "y": y, "w": w, "h": h, "states": states})
    meta = {"game_md5_la0": "x", "rooms": {"6": {"name": "lagrom", "width": 320, "height": 200, "palettes": 1,
                                                 "zplane": False, "cycles": [], "objects": objects}}}
    (ex / "rooms.json").write_text(json.dumps(meta))
    return ex, room


def _blurred_reference(d, radius=1.2):
    from PIL import ImageFilter
    Image.open(d / "referanse.png").convert("RGB").filter(ImageFilter.GaussianBlur(radius)).save(d / "resultat.png")


def test_gpt_layer_jobs(tmp_path):
    import json
    from zakhd import gpt

    ex, room = _layer_extract(tmp_path)
    notes = {6: "Keep the panel empty.", "lag006": "Small things on the panel."}
    work = tmp_path / "gpt"
    jobs = gpt.make_jobs(ex, work, notes=notes)
    # Rom- og objektjobbene først, så lagene i rommet, og ikonarket til slutt
    assert [j.id for j in jobs] == ["rom006", "obj024_01", "lag006_01", "lag006_02", "lag006_03", "ikon01"]
    assert [r["type"] for r in gpt.read_status(work)] == ["rom", "objekt", "lag", "lag", "lag", "ikon"]
    pieces = {j.id: [p["bilde"] for p in j.objekter] for j in jobs if j.objekter}
    # Lag 1 tar første tilstand av hvert objekt; obj023 overlapper obj022 og flyttes til lag 2.
    # obj020 ligger oppå det store bildet og får sitt eget lag med det som underlag.
    assert pieces == {"lag006_01": ["obj021_01", "obj022_01"], "lag006_02": ["obj021_02", "obj023_01"],
                      "lag006_03": ["obj020_01"], "ikon01": ["obj025_01"]}
    overview = (work / "JOBBER.md").read_text()
    assert "obj026_01 (rom 6): helt gjennomsiktig" in overview and "3 lagjobber med 5 små objektbilder" in overview

    d = work / "jobber" / "lag006_01"
    data = json.loads((d / "jobb.json").read_text())
    assert data["type"] == "lag" and data["lag"] == 1 and data["underlag"] == []
    assert data["bilde_to"] == "jobber/rom006/resultat.png"
    assert data["objekter"][0] == {"bilde": "obj021_01", "objekt": 21, "tilstand": "01", "rom": 6, "rekt": [20, 20, 30, 20]}
    under = json.loads((work / "jobber" / "lag006_03" / "jobb.json").read_text())
    assert under["underlag"] == ["obj024_01"] and under["bilde_to"] == "jobber/obj024_01/resultat.png"
    # Romjobber skriver ikke feltene for lag
    assert "objekter" not in json.loads((work / "jobber" / "rom006" / "jobb.json").read_text())

    # Referansen: rommet med lagets objekter på plass, 4x på samme lerret som rommet
    ref = Image.open(d / "referanse.png")
    ox, oy = data["plassering"]

    def at(x, y):
        return ref.getpixel(((ox + x) * 4 + 1, (oy + y) * 4 + 1))

    obj21 = Image.open(ex / "objects" / "obj021_01.png")
    assert at(30, 30) == obj21.getpixel((10, 10))[:3]
    assert at(21, 21) == room.getpixel((21, 21))          # gjennomsiktig hjørne viser rommet
    assert at(115, 30) == Image.open(ex / "objects" / "obj022_01.png").getpixel((15, 20))[:3]
    assert at(60 + 5, 120 + 5) == room.getpixel((65, 125))  # obj020 er i et annet lag
    ref3 = Image.open(work / "jobber" / "lag006_03" / "referanse.png")
    big = Image.open(ex / "objects" / "obj024_01.png")
    assert ref3.getpixel(((ox + 200) * 4, (oy + 100) * 4)) == big.getpixel((200, 50))[:3]

    prompt = (d / "prompt.txt").read_text()
    assert prompt.startswith(gpt.PROMPT_BASE) and gpt.PROMPT_LAYER in prompt
    assert prompt.rstrip().endswith(gpt.PROMPT_LAYER_STYLE)
    assert "Small things on the panel." in prompt and "Keep the panel empty." not in prompt
    icon_prompt = (work / "jobber" / "ikon01" / "prompt.txt").read_text()
    assert gpt.PROMPT_ICONS in icon_prompt and icon_prompt.rstrip().endswith(gpt.PROMPT_STYLE)
    sheet = Image.open(work / "jobber" / "ikon01" / "original_1x.png")
    assert sheet.size == gpt.ICON_SHEET and sheet.getpixel((1, 1)) == gpt.ICON_BG

    # Rom- og objektjobbene er de samme som uten de små objektene
    plain = tmp_path / "uten"
    ex2, _ = _layer_extract(plain, small=False)
    jobs2 = gpt.make_jobs(ex2, plain / "gpt", notes=notes)
    assert [j.id for j in jobs2] == ["rom006", "obj024_01"]
    for jid in ("rom006", "obj024_01"):
        for f in ("referanse.png", "prompt.txt", "original_1x.png"):
            assert (work / "jobber" / jid / f).read_bytes() == (plain / "gpt" / "jobber" / jid / f).read_bytes()


def test_gpt_layer_import_and_mod(tmp_path):
    import json
    import numpy as np
    from zakhd import gpt, upscale

    ex, room = _layer_extract(tmp_path)
    work, done = tmp_path / "gpt", tmp_path / "gpt-ferdig"
    gpt.make_jobs(ex, work)
    jd = work / "jobber"
    # Lag 1 riktig. Lag 2 er bare rommet: objektene mangler, og laget avvises.
    _blurred_reference(jd / "lag006_01")
    Image.open(jd / "rom006" / "referanse.png").save(jd / "lag006_02" / "resultat.png")
    _blurred_reference(jd / "ikon01")
    s = gpt.import_results(work, ex, done)
    status = {r["jobb"]: r for r in gpt.read_status(work)}
    assert status["lag006_01"]["status"] == "godkjent" and status["ikon01"]["status"] == "godkjent"
    assert status["lag006_02"]["status"] == "avvist"
    assert "obj021_02 mangler" in status["lag006_02"]["kommentar"]
    assert "small objects did not match" in (jd / "lag006_02" / "retur.md").read_text()
    assert s["ferdige_lagobjekter"] == ["obj021_01", "obj022_01"] and s["lagobjekter_totalt"] == 5
    assert s["ferdige_ikoner"] == ["obj025_01"] and s["ikoner_totalt"] == 1

    # Utklippet: nøyaktig 4x, alfa fra originalen, innholdet fra laget der objektet ligger
    hd = Image.open(done / "objects" / "obj021_01.png")
    orig = Image.open(ex / "objects" / "obj021_01.png")
    assert hd.size == (120, 80) and hd.mode == "RGBA"
    assert hd.tobytes("raw", "A") == upscale.upscale_alpha(orig.getchannel("A"), 4).tobytes()
    assert hd.getpixel((2, 2))[3] == 0 and hd.getpixel((60, 40))[3] == 255
    res = Image.open(jd / "lag006_01" / "resultat.png").convert("RGB")
    ox, oy = json.loads((jd / "lag006_01" / "jobb.json").read_text())["plassering"]
    crop = res.crop(((ox + 20) * 4, (oy + 20) * 4, (ox + 50) * 4, (oy + 40) * 4))
    diff = np.abs(np.asarray(hd.convert("RGB"), float) - np.asarray(crop, float))[np.asarray(hd)[..., 3] > 0]
    assert diff.mean() < 6
    assert Image.open(done / "objects" / "obj025_01.png").size == (64, 64)
    prov = json.loads((done / "provenance.json").read_text())
    p = prov["obj021_01"]
    assert p["type"] == "lag" and p["lag"] == "lag006_01" and p["rekt_i_lag"] == [20, 20, 30, 20]
    assert p["fil"] == "objects/obj021_01.png" and p["jobber"][0]["jobb"] == "lag006_01"
    assert p["jobber"][0]["kantlikhet_objekt"]["objekt"] > 0.9
    assert prov["obj025_01"]["type"] == "ikon" and prov["obj025_01"]["lag"] == "ikon01"
    assert "obj021_02" not in prov and not (done / "objects" / "obj021_02.png").exists()
    report = (work / "RAPPORT.md").read_text()
    assert "| Status | Romjobber | Objektjobber | Lagjobber | Ikonark |" in report
    assert "Ferdige objektbilder fra lag: 2 av 5" in report and "Ferdige ikoner fra ikonark: 1 av 1" in report

    # Ordre og grafikkliste: lagjobbene etter rom- og objektjobbene, med bilde to
    orders = gpt.write_orders(work, batch=10).read_text()
    assert "Lagjobber: 1 av 3 godkjent. Ferdige objektbilder fra lag: 2 av 5" in orders
    assert orders.index("`lag006_02`") < orders.index("`rom006`") < orders.index("`lag006_03`")
    assert ("`lag006_03` (rom 6, lagrom, lag 03 med 1 objektbilde, del 1/1). Legg ved "
            "`jobber/obj024_01/resultat.png` som bilde to") in orders
    assert "Lag denne etter at obj024_01 er godkjent." in orders
    lst = gpt.write_list(work).read_text()
    assert "| Små objektbilder i lag (`lagNNN_KK`: dører, brytere, lys, ting) | 2 | 5 |" in lst
    assert "bilde to `jobber/rom006/resultat.png`" in lst

    # Ny leveranse av lag 2: senere tilstand gjøres lik den første der originalene er like
    _blurred_reference(jd / "lag006_02")
    gpt.import_results(work, ex, done)
    prov = json.loads((done / "provenance.json").read_text())
    assert prov["obj021_02"]["likt_med"] == "obj021_01" and "obj023_01" in prov
    first = np.asarray(Image.open(done / "objects" / "obj021_01.png"))
    later = np.asarray(Image.open(done / "objects" / "obj021_02.png"))
    assert np.array_equal(first[8, 60], later[8, 60])  # øvre halvdel er lik i originalene

    # Modden: godkjente ChatGPT-objekter brukes som de er, resten skaleres automatisk
    m = modpack.build_mod(ex, tmp_path / "mod", scale=4, method="nearest", rooms={6}, own=done)
    for name in ("obj021_01", "obj021_02", "obj022_01", "obj023_01", "obj025_01"):
        assert name in m["objects"]
        assert Image.open(tmp_path / "mod" / "objects" / f"{name}.png").tobytes() == \
            Image.open(done / "objects" / f"{name}.png").tobytes()
    assert "obj020_01" in m["objects"]                       # ikke ferdig: automatisk oppskalert
    m = modpack.build_mod(ex, tmp_path / "mod2", scale=4, method="nearest", rooms=set(), own=done)
    assert m["objects"] == ["obj021_01", "obj021_02", "obj022_01", "obj023_01", "obj025_01"]

    # Lag 1 er ikke ferdig lenger: objektene fjernes, og senere tilstander som bygger på dem venter
    (jd / "lag006_01" / "resultat.png").rename(jd / "lag006_01" / "forrige.png")
    s = gpt.import_results(work, ex, done)
    prov = json.loads((done / "provenance.json").read_text())
    assert sorted(n for n in prov if prov[n]["type"] == "lag") == ["obj023_01"]
    assert not (done / "objects" / "obj021_01.png").exists() and not (done / "objects" / "obj021_02.png").exists()
    assert any("venter på første tilstand" in v for v in s["venter"])


def test_gpt_layer_parts_and_stitch():
    from zakhd import gpt
    import numpy as np

    # Bredt rom med tre deler (0, 296 og 592, overlapp 88)
    tiles = gpt.plan_tiles(976, 200)
    assert [t[0] for t in tiles] == [0, 296, 592]

    def piece(name, x0, x1):
        return gpt.Piece(name, 1, "01", 2, (x0, 50, x1 - x0, 20), (x0, 50, x1, 70))

    a = piece("objA", 300, 340)    # helt inne i del 1 og del 2, trenger bare én
    b = piece("objB", 600, 640)    # helt inne i del 2 og del 3
    c = piece("objC", 560, 700)    # ikke helt inne i noen del: sys sammen av del 2 og 3
    d = piece("objD", 10, 40)      # bare del 1
    names = {i: [p.bilde for p in ps] for i, ps in gpt.assign_parts([a, b, c, d], tiles).items()}
    # C trenger del 2 og 3, så A og B legges i del 2 i stedet for i egne deler (B ligger mest midt i del 2)
    assert names == {0: ["objD"], 1: ["objA", "objB", "objC"], 2: ["objC"]}
    assert len(gpt.assign_parts([a], tiles)) == 1

    # Sammensying av et utsnitt gir det samme som det tilsvarende stedet i hele bildet
    rng = np.random.default_rng(2)
    parts = [((x, y, w, h), rng.random((h * 4, w * 4, 3)) * 255) for x, y, w, h, _, _ in tiles]
    full = gpt._stitch(976, 200, parts)
    box = gpt._stitch(976, 200, parts, (350, 40, 300, 30))
    assert np.array_equal(box, full[40 * 4:70 * 4, 350 * 4:650 * 4])


def test_gpt_keeps_better_earlier_delivery(tmp_path):
    from PIL import ImageFilter
    from zakhd import gpt

    ex, room, big = _fake_extract(tmp_path)
    work, done = tmp_path / "gpt", tmp_path / "gpt-ferdig"
    gpt.make_jobs(ex, work)
    d = work / "jobber" / "obj241_01"
    ref = Image.open(d / "referanse.png")
    # Første leveranse er god og blir husket
    ref.filter(ImageFilter.GaussianBlur(1.5)).save(d / "resultat.png")
    gpt.import_results(work, ex, done)
    good = Image.open(done / "objects" / "obj241_01.png").tobytes()
    assert (work / "beste" / "obj241_01.png").exists()
    # Ny leveranse er forskjøvet og blir avvist: den forrige brukes fortsatt
    ref.transform(ref.size, Image.AFFINE, (1, 0, -24, 0, 1, -16)).save(d / "resultat.png")
    s = gpt.import_results(work, ex, done)
    row = {r["jobb"]: r for r in gpt.read_status(work)}["obj241_01"]
    assert row["status"] == "godkjent" and "så den forrige brukes" in row["kommentar"]
    assert s["ferdige_objekter"] == ["obj241_01"]
    assert Image.open(done / "objects" / "obj241_01.png").tobytes() == good
    # Avvises den forrige ved gjennomsyn, finnes ingen god leveranse lenger
    import hashlib
    sha = hashlib.sha256((work / "beste" / "obj241_01.png").read_bytes()).hexdigest()
    rej = tmp_path / "avvisninger.csv"
    rej.write_text(f'jobb,sha256_resultat,grunn,forslag\nobj241_01,{sha},"feil",""\n', encoding="utf-8")
    s = gpt.import_results(work, ex, done, rejections=rej)
    assert s["ferdige_objekter"] == [] and not (done / "objects" / "obj241_01.png").exists()
    assert not (work / "beste" / "obj241_01.png").exists()


def test_gpt_manual_check_status(tmp_path):
    import hashlib
    from PIL import ImageFilter
    from zakhd import gpt

    ex, room, big = _fake_extract(tmp_path)
    work, done = tmp_path / "gpt", tmp_path / "gpt-ferdig"
    gpt.make_jobs(ex, work)
    d = work / "jobber" / "obj241_01"
    Image.open(d / "referanse.png").filter(ImageFilter.GaussianBlur(1.5)).save(d / "resultat.png")
    sha = hashlib.sha256((d / "resultat.png").read_bytes()).hexdigest()
    rej = tmp_path / "avvisninger.csv"
    rej.write_text(f'jobb,sha256_resultat,grunn,forslag,status\nobj241_01,{sha},"søm mot rommet","Redo with room.",sjekk\n',
                   encoding="utf-8")
    s = gpt.import_results(work, ex, done, rejections=rej)
    row = {r["jobb"]: r for r in gpt.read_status(work)}["obj241_01"]
    # Sjekk: bildet brukes fortsatt, men skal gjøres om
    assert row["status"] == "sjekk" and row["kommentar"] == "søm mot rommet"
    assert s["ferdige_objekter"] == ["obj241_01"] and (done / "objects" / "obj241_01.png").exists()
    assert "Redo with room." in (d / "retur.md").read_text()


# ---------------------------------------------------------------- figurark

def _figure_extract(tmp_path, with_room=True):
    """Uttrekk med kostyme 14: gange mot høyre (ruter 0 til 5), stående mot høyre og venstre (6 og 7),
    én rute som er bredere enn lerretet (8, 400 x 60) og én helt gjennomsiktig (9).

    Gangrutene er laget av den samme figuren (samme tekstur), med et bein som flytter seg, slik
    rutene i en ekte animasjon er like bortsett fra posen. Med with_room er rom 5 fra _fake_extract med.
    """
    import json
    import numpy as np

    if with_room:
        ex, _, _ = _fake_extract(tmp_path)
    else:
        ex = tmp_path / "extract"
        (ex / "rooms").mkdir(parents=True)
        (ex / "rooms.json").write_text(json.dumps({"game_md5_la0": "x", "rooms": {}}))
    (ex / "costumes").mkdir()
    rng = np.random.default_rng(11)
    tex = np.asarray(_texture(rng, 400, 60, 1.5), dtype=np.float64) / 255
    # Brune farger, langt fra alle bakgrunnsfargene
    lo, hi = np.array([110, 60, 30]), np.array([220, 140, 90])
    colours = (lo + tex * (hi - lo)).astype(np.uint8)

    def cel(n, w, h, mask):
        rgba = np.zeros((h, w, 4), np.uint8)
        rgba[..., :3] = colours[:h, :w]
        rgba[..., 3] = np.where(mask, 255, 0)
        rgba[~mask, :3] = 0
        Image.fromarray(rgba).save(ex / "costumes" / f"costume014_{n:03d}.png")
        idx = Image.fromarray(np.where(mask, 1 + (np.arange(w)[None, :] % 7), 0).astype(np.uint8), "L").convert("P")
        idx.save(ex / "costumes" / f"costume014_{n:03d}_idx.png", transparency=0)

    yy, xx = np.mgrid[0:48, 0:24]
    body = ((xx - 12) / 10.0) ** 2 + ((yy - 18) / 17.0) ** 2 <= 1
    for k in range(6):
        cel(k, 24, 48, body | ((yy >= 30) & (abs(xx - (9 + k)) <= 2)))
    cel(6, 24, 48, body)
    cel(7, 24, 48, body | ((yy >= 30) & (abs(xx - 15) <= 2)))
    by, bx = np.mgrid[0:60, 0:400]
    cel(8, 400, 60, ((bx - 200) / 195.0) ** 2 + ((by - 30) / 28.0) ** 2 <= 1)
    cel(9, 10, 10, np.zeros((10, 10), bool))
    anims = [{"valg": 26, "animasjon": 3, "retning": 2, "lag": 0, "ruter": [6]},
             {"valg": 30, "animasjon": 3, "retning": 6, "lag": 0, "ruter": [7]},
             {"valg": 18, "animasjon": 2, "retning": 2, "lag": 0, "ruter": [0, 1, 2, 3, 4, 5]},
             {"valg": 72, "animasjon": 9, "retning": 0, "lag": 0, "ruter": [8]}]
    sizes = [(24, 48)] * 8 + [(400, 60), (10, 10)]
    meta = {"14": {"room": 5, "codec": 1, "colours": {"kind": "rgbs"}, "retninger": 8, "animasjoner": anims,
                   "cels": [{"cel": n, "w": w, "h": h} for n, (w, h) in enumerate(sizes)]}}
    (ex / "costumes.json").write_text(json.dumps(meta))
    return ex


def test_akos_sequence_and_animations():
    # AKSQ: rute 3, DrawMany med rutene 4 og 0x105 (to byte), betinget hopp til 30, GoToState tilbake
    # til 0 (animasjonen går i ring). Ved 30: rute 7 og slutt.
    seq = bytes([3]) + bytes([0xC0, 0x20, 2]) + struct.pack("<hh", 0, 0) + bytes([4]) + struct.pack("<hh", 1, 1) \
        + bytes([0x81, 0x05]) + bytes([0xC0, 0x70]) + struct.pack("<H", 30) + bytes([0, 1, 0]) \
        + bytes([0xC0, 0x30]) + struct.pack("<H", 0)
    seq = seq.ljust(30, b"\0") + bytes([7]) + bytes([0xC0, 0xFF])
    assert gamedata.akos_sequence(seq, 0) == [[3], [4, 0x105], [7]]

    # En AKOS-blokk med AKHD (8 retninger), AKCH (bare valg 18 = gange mot høyre, lag 0) og AKSQ
    akhd = struct.pack("<6H", 1, 2, 24, 10, 1, 2)
    chores = [0] * 24
    chores[18] = 48
    akch = struct.pack("<24H", *chores) + struct.pack("<H", 0x8000) + bytes([6]) + struct.pack("<HH", 0, 0)
    akos = _block(b"AKOS", _block(b"AKHD", akhd) + _block(b"AKCH", akch) + _block(b"AKSQ", seq))
    out = gamedata.akos_animations(akos, 0, len(akos))
    assert out == {"retninger": 8,
                   "animasjoner": [{"valg": 18, "animasjon": 2, "retning": 2, "lag": 0, "ruter": [3, 4, 0x105, 7]}]}


def test_figure_sheets_plan_and_jobs(tmp_path, monkeypatch):
    import json
    import numpy as np
    from zakhd import export, figur, gpt

    ex = _figure_extract(tmp_path)
    meta = export.load_costumes(ex)
    info = meta[14]
    groups = figur.groups_of(info, figur.cel_boxes(ex, 14, info))
    # Stående i begge retninger først, så gange mot høyre i rekkefølge, så den store ruten. Den
    # gjennomsiktige ruten er ikke med.
    assert [[c.rute for c in g] for g in groups] == [[6], [7], [0, 1, 2, 3, 4, 5], [8]]
    sheets = figur.plan_sheets(groups)
    assert [len(s.cels) for s in sheets] == [8, 1] and not sheets[0].stor and sheets[1].stor
    # Rutene ligger inne på arket med minst FIG_PAD mellom de synlige pikslene, gangen på én rad i rekkefølge
    boxes = [(x + c.box[0], y + c.box[1], x + c.box[2], y + c.box[3]) for c, x, y in sheets[0].cels]
    for b in boxes:
        assert b[0] >= figur.FIG_MARGIN and b[1] >= figur.FIG_MARGIN
        assert b[2] <= figur.FIG_SHEET[0] - figur.FIG_MARGIN and b[3] <= figur.FIG_SHEET[1] - figur.FIG_MARGIN
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            assert not gpt._overlaps((a[0] - figur.FIG_PAD + 1, a[1] - figur.FIG_PAD + 1,
                                      a[2] + figur.FIG_PAD - 1, a[3] + figur.FIG_PAD - 1), b)
    walk = [(x, y) for c, x, y in sheets[0].cels if c.animasjon == 2]
    assert len({y for _, y in walk}) == 1 and [x for x, _ in walk] == sorted(x for x, _ in walk)
    # Den store ruten får et eget ark som er bredere enn lerretet (deles i to jobber)
    c8 = sheets[1].cels[0][0]
    assert sheets[1].size == (c8.vw + 2 * figur.FIG_MARGIN, c8.vh + 2 * figur.FIG_MARGIN)
    assert sheets[1].size[0] > gpt.TILE[0]

    # Bakgrunnen er en farge som ikke finnes i kostymet
    bg, name, dist = figur.background_for(ex, 14, info)
    assert dist > 100

    work, plain = tmp_path / "gpt", tmp_path / "uten"
    jobs = gpt.make_jobs(ex, work, notes={5: "Test note."}, figures={14})
    gpt.make_jobs(ex, plain, notes={5: "Test note."})
    assert [j.id for j in jobs] == ["rom005", "obj241_01", "lag005_01", "fig014_01", "fig014_02_del1av2",
                                    "fig014_02_del2av2"]
    # De andre jobbene er byte for byte de samme som uten figurark
    for jid in ("rom005", "obj241_01", "lag005_01"):
        for f in ("referanse.png", "prompt.txt", "original_1x.png"):
            assert (work / "jobber" / jid / f).read_bytes() == (plain / "jobber" / jid / f).read_bytes()
    assert "kostyme" not in json.loads((work / "jobber" / "lag005_01" / "jobb.json").read_text())

    d = work / "jobber" / "fig014_01"
    data = json.loads((d / "jobb.json").read_text())
    assert data["type"] == "figur" and data["kostyme"] == 14 and data["lag"] == 1 and data["rom"] == 5
    # Arkene i FIG_PILOT er merket som pilot også når alle arkene for kostymet lages
    assert data["bakgrunn"] == list(bg) and "bilde_to" not in data and data["pilot"] is True
    assert [c["rute"] for c in data["ruter"]] == [6, 7, 0, 1, 2, 3, 4, 5]
    assert "gange mot høyre (6 ruter)" in data["innhold"]
    second = json.loads((work / "jobber" / "fig014_02_del2av2" / "jobb.json").read_text())
    assert second["bilde_to"] == "jobber/fig014_01/resultat.png" and second["deler"] == 2
    # Referansen: 4x på lerretet med grå kant, rutene på den flate bakgrunnen
    ref = Image.open(d / "referanse.png")
    ox, oy = data["plassering"]
    assert ref.size == (1536, 1024) and ref.getpixel((0, 0)) == gpt.BORDER
    assert ref.getpixel(((ox + 1) * 4, (oy + 1) * 4)) == tuple(bg)
    c = data["ruter"][2]
    cel0 = Image.open(ex / "costumes" / "costume014_000.png")
    assert ref.getpixel(((ox + c["rekt"][0] + 12) * 4 + 1, (oy + c["rekt"][1] + 18) * 4 + 1)) == \
        cel0.getpixel((12, 18))[:3]
    prompt = (d / "prompt.txt").read_text()
    assert "the same face, hair, clothes, colors and light in every frame" in prompt
    # Glatt stil: gjennomsiktig bakgrunn med ekte alfa, ikke originalens omriss piksel for piksel
    assert "#%02X%02X%02X" % bg in prompt and "fully transparent background" in prompt
    assert "outline of every frame exactly" not in prompt
    assert "walking, facing right (6 frames)" in prompt and prompt.rstrip().endswith(figur.PROMPT_FIGURE_STYLE)
    assert "part 2 of 2" in (work / "jobber" / "fig014_02_del2av2" / "prompt.txt").read_text()
    # Linjen om magenta skyggemerker er bare med når kostymet har slike
    assert "shadow markers" not in prompt
    assert figur.has_markers(np.array([[255.0, 87, 255], [20, 20, 20]])) and not figur.has_markers(np.zeros((1, 3)))
    assert not figur.has_markers(np.array([[220.0, 120, 90]]))
    assert "2 figurark (3 jobber) med 9 kostymeruter" in (work / "JOBBER.md").read_text()

    # Piloten: bare de første arkene, merket som pilot
    monkeypatch.setattr(figur, "FIG_PILOT", {14: 1})
    jobs = gpt.make_jobs(ex, tmp_path / "pilot", figures="pilot")
    figs = [j for j in jobs if j.type == "figur"]
    assert [j.id for j in figs] == ["fig014_01"] and figs[0].pilot
    assert [j.id for j in gpt.make_jobs(ex, tmp_path / "ingen", figures="ingen")] == ["rom005", "obj241_01",
                                                                                       "lag005_01"]


def _figure_result(d, change=None):
    """Kunstig resultat for et figurark: referansen litt uskarp, eventuelt med noe endret."""
    from PIL import ImageFilter
    im = Image.open(d / "referanse.png").convert("RGB").filter(ImageFilter.GaussianBlur(1.2))
    if change:
        im = change(im)
    im.save(d / "resultat.png")


def test_figure_import_cut_and_mod(tmp_path):
    import json
    import numpy as np
    from PIL import ImageFilter
    from zakhd import figur, gpt, upscale

    ex = _figure_extract(tmp_path)
    work, done = tmp_path / "gpt", tmp_path / "gpt-ferdig"
    jobs = gpt.make_jobs(ex, work, figures="pilot")
    jd = work / "jobber"
    figs = ["fig014_01", "fig014_02_del1av2", "fig014_02_del2av2"]
    assert [j.id for j in jobs if j.type == "figur"] == figs and all(j.pilot for j in jobs if j.type == "figur")
    for jid in figs:
        _figure_result(jd / jid)
    s = gpt.import_results(work, ex, done)
    status = {r["jobb"]: r for r in gpt.read_status(work)}
    # Et jevnt ark godkjennes
    assert all(status[j]["status"] == "godkjent" for j in figs)
    assert s["ferdige_figurruter"] == [f"costume014_{n:03d}" for n in range(9)] and s["figurruter_totalt"] == 9

    # Utklippet: nøyaktig 4x, samme alfa som build-mod lager, innholdet fra arket
    for n in range(9):
        hd = Image.open(done / "costumes" / f"costume014_{n:03d}.png")
        orig = Image.open(ex / "costumes" / f"costume014_{n:03d}.png")
        assert hd.size == (orig.width * 4, orig.height * 4) and hd.mode == "RGBA"
        assert hd.tobytes("raw", "A") == upscale.upscale_alpha(orig.getchannel("A"), 4).tobytes()
    data = json.loads((jd / "fig014_01" / "jobb.json").read_text())
    c = next(c for c in data["ruter"] if c["rute"] == 3)
    ox, oy = data["plassering"]
    x, y, w, h = c["rekt"]
    res = Image.open(jd / "fig014_01" / "resultat.png").convert("RGB")
    crop = np.asarray(res.crop(((ox + x) * 4, (oy + y) * 4, (ox + x + w) * 4, (oy + y + h) * 4)), float)
    hd = np.asarray(Image.open(done / "costumes" / "costume014_003.png"))
    alpha = Image.open(ex / "costumes" / "costume014_003.png").getchannel("A").resize((w * 4, h * 4), Image.NEAREST)
    inner = np.asarray(alpha.filter(ImageFilter.MinFilter(9))) > 0
    assert np.abs(hd[..., :3].astype(float) - crop)[inner].mean() < 8
    # Ingen glorie i arkets bakgrunnsfarge langs omrisset: i resultatet er kantpikslene blandet med
    # bakgrunnen, i utklippet er de fylt innenfra
    o4 = np.asarray(Image.open(ex / "costumes" / "costume014_003.png").convert("RGB").resize((w * 4, h * 4),
                                                                                             Image.NEAREST), float)
    d = np.array(data["bakgrunn"], float) - o4

    def toward_bg(a):
        return ((a - o4) * d).sum(axis=2) / np.maximum((d * d).sum(axis=2), 1)
    mask = np.asarray(alpha) > 0
    assert toward_bg(crop)[mask].max() > 0.4
    assert toward_bg(hd[..., :3].astype(float))[mask].max() <= figur.FIG_BLEED + 0.01
    # Den store ruten er sydd sammen av to deler
    big = np.asarray(Image.open(done / "costumes" / "costume014_008.png"))
    orig_big = np.asarray(Image.open(ex / "costumes" / "costume014_008.png").resize((1600, 240), Image.NEAREST))
    assert np.abs(big[..., :3].astype(float) - orig_big[..., :3])[big[..., 3] > 0].mean() < 12

    prov = json.loads((done / "provenance.json").read_text())
    p = prov["costume014_003"]
    assert p["type"] == "figur" and p["fil"] == "costumes/costume014_003.png" and p["ark"] == "fig014_01"
    assert p["kostyme"] == 14 and p["rute"] == 3 and p["animasjon"] == 2 and p["rekt_i_ark"] == c["rekt"]
    assert p["jobber"][0]["rutekontroll"]["omriss"] > 0.85 and len(p["jobber"][0]["flimmer"]) == 2
    assert all(q["flimmer"] < figur.FIG_FLICKER for q in p["jobber"][0]["flimmer"])
    assert [j["jobb"] for j in prov["costume014_008"]["jobber"]] == ["fig014_02_del1av2", "fig014_02_del2av2"]
    report = (work / "RAPPORT.md").read_text()
    assert "| Status | Romjobber | Objektjobber | Lagjobber | Ikonark | Figurark |" in report
    assert "Figurark: 2 av 2 godtatt. Ferdige figurruter: 9 av 9" in report

    # Modden: figurrutene kommer med uten --kostymer, og ingenting annet fra kostymene
    m = modpack.build_mod(ex, tmp_path / "mod", scale=4, method="nearest", rooms=set(), own=done)
    assert m["costume_cels"] == 9 and m["costumes"] == ["costume014"]
    for n in range(9):
        name = f"costume014_{n:03d}"
        assert Image.open(tmp_path / "mod" / "costumes" / f"{name}.png").tobytes() == \
            Image.open(done / "costumes" / f"{name}.png").tobytes()
        assert (tmp_path / "mod" / "costumes" / f"{name}_idx.png").exists()
    assert not (tmp_path / "mod" / "costumes" / "costume014_009.png").exists()
    # Med --kostymer 14 skaleres resten (den gjennomsiktige ruten) automatisk, de egne er de samme
    m = modpack.build_mod(ex, tmp_path / "mod2", scale=4, method="nearest", rooms=set(), own=done, costumes={14})
    assert m["costume_cels"] == 10
    assert Image.open(tmp_path / "mod2" / "costumes" / "costume014_003.png").tobytes() == \
        Image.open(done / "costumes" / "costume014_003.png").tobytes()
    # Uten egne bilder og uten --kostymer: ingen kostymer
    assert modpack.build_mod(ex, tmp_path / "mod3", scale=4, method="nearest", rooms=set())["costume_cels"] == 0


def test_figure_sheet_in_smooth_style_is_not_cut_with_the_old_mask(tmp_path):
    # Tom avviste trappekantene: et ark med egen alfakant (RGBA, myke kanter) skal ikke klippes med
    # originalens pikselmaske, men vente på mottaket for myke kanter
    import numpy as np
    from PIL import ImageFilter
    from zakhd import gpt

    ex = _figure_extract(tmp_path)
    work, done = tmp_path / "gpt", tmp_path / "gpt-ferdig"
    gpt.make_jobs(ex, work, figures="pilot")
    jd = work / "jobber" / "fig014_01"
    a = Image.new("L", (1536, 1024), 0)
    a.paste(255, (200, 200, 600, 800))
    a = a.filter(ImageFilter.GaussianBlur(6))
    sheet = Image.new("RGBA", (1536, 1024), (200, 120, 60, 0))
    sheet.putalpha(a)
    sheet.save(jd / "resultat.png")
    assert gpt.has_native_alpha(jd / "resultat.png")
    s = gpt.import_results(work, ex, done)
    row = {r["jobb"]: r for r in gpt.read_status(work)}["fig014_01"]
    assert row["status"] == "levert" and "myke kanter" in row["kommentar"]
    assert s["ferdige_figurruter"] == [] and not list((done / "costumes").glob("*.png"))
    # Ikke i arbeidskøen igjen
    assert "fig014_01" not in [r["jobb"] for r in gpt.work_queue(gpt.read_status(work), work)]
    # Et ark i gammel stil (flat bakgrunn) har ingen egen alfakant
    Image.new("RGB", (1536, 1024), (0, 200, 200)).save(tmp_path / "flat.png")
    assert not gpt.has_native_alpha(tmp_path / "flat.png")


def test_figure_rejections_and_orders(tmp_path):
    import json
    import numpy as np
    from zakhd import figur, gpt

    ex = _figure_extract(tmp_path)

    def setup(name):
        work = tmp_path / name
        gpt.make_jobs(ex, work, figures="pilot")
        data = json.loads((work / "jobber" / "fig014_01" / "jobb.json").read_text())
        ox, oy = data["plassering"]
        rekt = {c["rute"]: c["rekt"] for c in data["ruter"]}

        def box(n):
            x, y, w, h = rekt[n]
            return ((ox + x) * 4, (oy + y) * 4, (ox + x + w) * 4, (oy + y + h) * 4)
        return work, tuple(data["bakgrunn"]), box

    # En rute som mangler, avviser arket
    work, bg, box = setup("mangler")

    def missing(im):
        im.paste(bg, box(7))                   # stående mot venstre er borte
        return im
    _figure_result(work / "jobber" / "fig014_01", missing)
    gpt.import_results(work, ex, tmp_path / "ferdig-mangler")
    row = {r["jobb"]: r for r in gpt.read_status(work)}["fig014_01"]
    assert row["status"] == "avvist" and "costume014_007 mangler" in row["kommentar"]
    assert "frames did not match" in (work / "jobber" / "fig014_01" / "retur.md").read_text()
    assert not (tmp_path / "ferdig-mangler" / "costumes" / "costume014_006.png").exists()

    # Flimmer: en rute med andre detaljer enn naborutene avvises, selv om omrisset stemmer
    work, bg, box = setup("flimmer")

    def flicker(im):
        a = np.asarray(im, dtype=np.float64).copy()
        x0, y0, x1, y1 = box(2)
        noise = np.random.default_rng(4).normal(0, 60, ((y1 - y0) // 4, (x1 - x0) // 4, 3)).repeat(4, 0).repeat(4, 1)
        mask = np.asarray(Image.open(ex / "costumes" / "costume014_002.png").getchannel("A").resize(
            (x1 - x0, y1 - y0), Image.NEAREST)) > 0
        a[y0:y1, x0:x1][mask] = np.clip(a[y0:y1, x0:x1][mask] + noise[mask], 0, 255)
        return Image.fromarray(a.astype(np.uint8))
    _figure_result(work / "jobber" / "fig014_01", flicker)
    done = tmp_path / "ferdig-flimmer"
    gpt.import_results(work, ex, done)
    row = {r["jobb"]: r for r in gpt.read_status(work)}["fig014_01"]
    assert row["status"] == "avvist" and "flimmer mellom nabo-ruter" in row["kommentar"]
    assert "costume014_002" in row["kommentar"] and "ruter er feil" not in row["kommentar"]
    assert "animation flickers" in (work / "jobber" / "fig014_01" / "retur.md").read_text()
    assert not (done / "costumes" / "costume014_002.png").exists()
    # Bare parene med den endrede ruten er over grensen
    job = gpt._load_job(json.loads((work / "jobber" / "fig014_01" / "jobb.json").read_text()))
    ox, oy = job.plassering
    x, y, w, h = job.region
    res = Image.open(work / "jobber" / "fig014_01" / "resultat.png").convert("RGB")
    part = res.crop((ox * 4, oy * 4, (ox + w) * 4, (oy + h) * 4))
    pairs = figur.check_flicker(np.asarray(part, dtype=np.float64), job, ex)
    assert len(pairs) == 5
    assert {tuple(p["ruter"]) for p in pairs if p["flimmer"] > figur.FIG_FLICKER} == \
        {("costume014_001", "costume014_002"), ("costume014_002", "costume014_003")}

    # Ordren: avviste romjobber først, så piloten, så resten av rom- og objektjobbene og lagjobbene
    rd = work / "jobber" / "rom005"
    ref = Image.open(rd / "referanse.png")
    ref.transform(ref.size, Image.AFFINE, (1, 0, -24, 0, 1, -16)).save(rd / "resultat.png")
    gpt.import_results(work, ex, done)
    orders = gpt.write_orders(work, batch=10).read_text()
    pos = [orders.index(f"`{j}`") for j in ("rom005", "fig014_01", "fig014_02_del1av2", "obj241_01", "lag005_01")]
    assert pos == sorted(pos)
    assert "Pilot for figurarkene" in orders and "Figurark: 0 av 3 godkjent. Ferdige figurruter: 0 av 9" in orders
    assert "Legg ved `jobber/fig014_01/resultat.png` som bilde to" in orders
    assert "Lag denne etter at fig014_01 er godkjent." in orders
    lst = gpt.write_list(work, batch=10).read_text()
    assert "`fig014_01` (figurark 1 for kostyme 14, 8 ruter: stående" in lst
    assert "(avvist, les retur.md) (pilot)" in lst and "De er en pilot" in lst
    assert "| Figurer: pilot med figurark for kostyme 14 (`figCCC_KK`, kostymeruter) | 0 | 9 |" in lst
    # Bestilling 1: de avviste romjobbene og piloten
    assert "Rom 5. Figurark for kostyme 14." in lst


def test_gpt_repair_edges():
    import numpy as np
    from zakhd import gpt

    rng = np.random.default_rng(5)
    base = 40 + gpt.blur(rng.random((64, 80, 3)) * 255, 2.0) * 0.3   # mørkt motiv, som de fleste rom
    bled = base.copy()
    bled[-3:] = 128 + 0.3 * (bled[-3:] - 128)        # grå kant blødd 3 rader inn nederst
    img = Image.fromarray(np.clip(bled, 0, 255).astype(np.uint8))
    out, fixed = gpt.repair_edges(img, {"bunn", "topp"})
    assert fixed == {"bunn": 3}
    o = np.asarray(out, dtype=float)
    assert np.abs(o[-1] - o[-4]).mean() < np.abs(bled[-1] - bled[-4]).mean() / 3
    # Et rent bilde endres ikke
    clean = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
    same, none = gpt.repair_edges(clean, {"bunn", "topp", "venstre", "hoyre"})
    assert none == {} and same is clean


def _smooth_sheet(ex, job, scale=5.2, head_shift=(0, 0)):
    """Et ark i glatt stil for jobben: hver rute tegnet på nytt i større skala (scale i stedet for 4),
    med myk alfakant og litt annen plassering enn i referansen. Gir arket og boksene (x, y, b, h)
    rundt hver tegnet rute med alfa over 128."""
    import numpy as np
    from PIL import ImageFilter

    sheet = Image.new("RGBA", tuple(job["lerret"]), (0, 0, 0, 0))
    boxes = {}
    ox, oy = job["bilde_i_lerret"][:2]
    for c in job["ruter"]:
        with Image.open(ex / "costumes" / f"{c['bilde']}.png") as im:
            o = im.convert("RGBA")
        bbox = o.getchannel("A").getbbox()
        if not bbox:
            continue
        o = o.crop(bbox)
        w, h = round(o.width * scale), round(o.height * scale)
        a = o.getchannel("A").resize((w, h), Image.BILINEAR).filter(ImageFilter.GaussianBlur(1.5))
        rgb = o.convert("RGB").resize((w, h), Image.BICUBIC)
        part = rgb.convert("RGBA")
        part.putalpha(a)
        # Arket er tegnet i større skala, med samme rekkefølge og rader som referansen
        cx = ox + (c["synlig"][0] + c["synlig"][2]) / 2 * scale + 6
        by = oy + c["synlig"][3] * scale + 10
        x, y = round(cx - w / 2), round(by - h)
        sheet.alpha_composite(part, (x, y))
        core = np.asarray(a) >= 128
        ys, xs = np.nonzero(core)
        boxes[c["bilde"]] = [x + int(xs.min()), y + int(ys.min()), int(xs.max() - xs.min() + 1),
                             int(ys.max() - ys.min() + 1)]
    return sheet, boxes


def test_smooth_figure_sheet_import(tmp_path):
    # Mottaket for figurark i glatt stil: tegningen skaleres til originalens høyde, legges over
    # originalruten og beholder sin egen myke alfa, med marg rundt ruten
    import hashlib
    import json
    import numpy as np
    from zakhd import gpt, myk

    ex = _figure_extract(tmp_path)
    work = tmp_path / "gpt"
    gpt.make_jobs(ex, work, figures="pilot")
    job = json.loads((work / "jobber" / "fig014_01" / "jobb.json").read_text())
    sheet, boxes = _smooth_sheet(ex, job)
    res = work / "jobber" / "fig014_01" / "resultat.png"
    sheet.save(res)
    rep_dir = work / "rapporter" / "figurer"
    rep_dir.mkdir(parents=True)
    (rep_dir / "fremdrift.json").write_text(json.dumps({"leveranser": [
        {"jobb": "fig014_01", "resultat": "jobber/fig014_01/resultat.png",
         "sha256": hashlib.sha256(res.read_bytes()).hexdigest()}]}))

    for with_map in (False, True):
        out = tmp_path / ("med-kart" if with_map else "uten-kart")
        if with_map:
            (rep_dir / "rutekart-del1.json").write_text(json.dumps({"fig014_01": {"koblinger": [
                {"bilde": b, "native_analyseboks_alfa128": box} for b, box in boxes.items()]}}))
        r = myk.import_all(work, ex, out)
        sheet_rep = r["ark"]["fig014_01"]
        assert sheet_rep["metode"] == ("rutekart" if with_map else "rader"), sheet_rep
        cels = sheet_rep["ruter"]
        drawn = [b for b in cels if cels[b]["status"] != "tom"]
        assert drawn and all(cels[b]["status"] == "ok" for b in drawn), cels
        for b in drawn:
            with Image.open(ex / "costumes" / f"{b}.png") as im:
                o = np.asarray(im.convert("RGBA"))[..., 3] > 0
            with Image.open(out / "costumes" / f"{b}_hd.png") as im:
                n = np.asarray(im.convert("RGBA"))[..., 3]
            mx, my = cels[b]["marg"]
            assert modpack.soft_size_ok((n.shape[1], n.shape[0]), (o.shape[1], o.shape[0]), 4)
            assert n.shape == ((o.shape[0] + 2 * my) * 4, (o.shape[1] + 2 * mx) * 4)
            # Egen myk kant, ikke originalens trappetrinn
            assert ((n > 20) & (n < 235)).sum() > 50
            # Samme høyde og samme sted som originalen i 4x
            core = n[my * 4:my * 4 + o.shape[0] * 4, mx * 4:mx * 4 + o.shape[1] * 4] >= 128
            o4 = np.repeat(np.repeat(o, 4, 0), 4, 1)
            iou = (core & o4).sum() / (core | o4).sum()
            assert iou > 0.85, (b, iou)
        assert (out / "myke.json").exists()

    # build-mod tar med de myke rutene og indeksbildene
    mod = tmp_path / "mod"
    modpack.build_mod(ex, mod, scale=4, method="nearest", rooms=set(), own=tmp_path / "med-kart")
    for b in drawn:
        assert (mod / "costumes" / f"{b}_hd.png").exists() and (mod / "costumes" / f"{b}_idx.png").exists()
    assert not modpack.soft_size_ok((100, 100), (24, 48), 4)


def test_smooth_figure_import_is_cached(tmp_path):
    # Et ark som er tatt inn før, med samme bilde, jobb og rutekart, tas ikke inn på nytt
    import hashlib
    import json
    from zakhd import gpt, myk

    ex = _figure_extract(tmp_path)
    work = tmp_path / "gpt"
    gpt.make_jobs(ex, work, figures="pilot")
    job = json.loads((work / "jobber" / "fig014_01" / "jobb.json").read_text())
    sheet, _ = _smooth_sheet(ex, job)
    res = work / "jobber" / "fig014_01" / "resultat.png"
    sheet.save(res)
    (work / "rapporter" / "x").mkdir(parents=True)
    (work / "rapporter" / "x" / "fremdrift.json").write_text(json.dumps({"leveranser": [
        {"jobb": "fig014_01", "resultat": "jobber/fig014_01/resultat.png",
         "sha256": hashlib.sha256(res.read_bytes()).hexdigest()}]}))
    out = tmp_path / "ut"
    first = myk.import_all(work, ex, out)
    calls = []
    real = myk.import_sheet
    myk.import_sheet = lambda *a, **k: calls.append(1) or real(*a, **k)
    try:
        again = myk.import_all(work, ex, out)
        assert not calls and again["ark"]["fig014_01"]["ruter"] == first["ark"]["fig014_01"]["ruter"]
        # En rute som mangler i ut-mappen, gir nytt mottak
        next(iter((out / "costumes").glob("*_hd.png"))).unlink()
        myk.import_all(work, ex, out)
        assert calls
    finally:
        myk.import_sheet = real


def test_text_font_letters(tmp_path):
    import numpy as np
    from zakhd import skrift
    n = skrift.lag_skrift(tmp_path)
    assert n == {"exo2": 94}
    fonts = tmp_path / "fonts"
    kart = {int(a): b for a, b in (l.split() for l in (fonts / "map.txt").read_text().splitlines()
                                   if l and not l.startswith("#"))}
    assert kart[2] == "exo2" and kart[100] == "exo2"
    assert (fonts / "OFL.txt").read_text().startswith("Copyright")
    # ett bilde for skriften, og en linje per bokstav med plassen i bildet
    atlas = Image.open(fonts / "exo2.png")
    assert atlas.mode == "RGBA" and (np.asarray(atlas)[..., :3] == 255).all()
    plass = {int(c): tuple(map(int, r)) for c, *r in (l.split() for l in (fonts / "exo2.txt").read_text().splitlines()
                                                     if l and not l.startswith("#"))}
    assert sorted(plass) == list(range(33, 127)) and 32 not in plass
    x, y, w, h = plass[105]  # "i": beskåret til blekket, prikken over staven
    a = np.asarray(atlas)[y:y + h, x:x + w, 3]
    assert a[0].max() > 128 and a[-1].max() > 128 and a[:, 0].max() > 128 and a[:, -1].max() > 128
    rows = a.max(axis=1) > 128
    assert rows[0] and rows[-1] and not rows.all()  # et mellomrom mellom prikk og stav
    for c, (x, y, w, h) in plass.items():
        assert x + w <= atlas.width and y + h <= atlas.height


def test_soft_cel_keeps_original_size():
    # Tom 10. oktober: figurene skiftet størrelse mellom rutene. Hver rute tilpasses originalens omriss
    # i bredde og høyde (innenfor FIT_RANGE), så en rute grafikeren tegnet for smal får originalens bredde.
    import numpy as np
    from zakhd import myk

    original = np.zeros((20, 10, 4), np.uint8)
    original[2:18, 2:8] = (200, 180, 160, 255)          # 6 x 16 originalpiksler
    drawing = np.zeros((80, 60, 4), np.uint8)
    drawing[5:69, 10:31] = (200, 180, 160, 255)         # 21 x 64: for smal i forhold til høyden
    scale = 16 * 4 / 64                                  # gruppens faktor gir originalens høyde
    plain = myk.place(drawing, original, scale)
    fitted = myk.place_fitted(drawing, original, scale)

    def size(r):
        ys, xs = np.nonzero(r["bilde"][..., 3] >= 128)
        return xs.max() - xs.min() + 1, ys.max() - ys.min() + 1

    assert size(plain)[0] < 6 * 4 - 1                     # uten tilpasning: smalere enn originalen
    assert fitted["tilpasset"] and size(fitted) == (6 * 4, 16 * 4)
    assert fitted["snitt_union"] > plain["snitt_union"]
    # Tilpasningen holdes innenfor FIT_RANGE: en tegning som er altfor smal, blir ikke strukket helt
    thin = np.zeros((80, 60, 4), np.uint8)
    thin[5:69, 10:20] = 255
    sx, sy = myk.fit_scales(thin, original, scale)
    assert abs(sx - scale * (1 + myk.FIT_RANGE)) < 1e-6 and abs(sy - scale) < 1e-6


def test_rejected_soft_sheet():
    # Et avvist ark (docs/gpt-avvisninger.csv) tas ikke inn av myke-figurer, bare for samme leveranse
    from zakhd import myk

    rej = {"fig001_01": {"jobb": "fig001_01", "sha256_resultat": "abc", "status": "avvist", "grunn": "feil figur"},
           "fig002_01": {"jobb": "fig002_01", "sha256_resultat": "*", "status": "avvist"},
           "fig003_01": {"jobb": "fig003_01", "sha256_resultat": "abc", "status": "sjekk"}}
    assert myk.rejected_sheet(rej, "fig001_01", "abc")["grunn"] == "feil figur"
    assert myk.rejected_sheet(rej, "fig001_01", "def") is None      # en ny leveranse er ikke avvist
    assert myk.rejected_sheet(rej, "fig002_01", "hva som helst")     # "*" gjelder alle
    assert myk.rejected_sheet(rej, "fig003_01", "abc") is None      # sjekk er ikke avvist
    assert myk.rejected_sheet(None, "fig004_01", "abc") is None


def test_skriptoversikt_tekst():
    """tools/skriptoversikt.py: tekst og argumenter fra utskriften til descumm."""
    import importlib.util
    sti = Path(__file__).resolve().parents[2] / "tools" / "skriptoversikt.py"
    spec = importlib.util.spec_from_file_location("skriptoversikt", sti)
    so = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(so)
    linje = 'print(10,[Text("Look." + newline() + "Write it^" + wait() + "now@@"),Color(3)]);'
    assert so._kall(linje, "print") == ['10,[Text("Look." + newline() + "Write it^" + wait() + "now@@"),Color(3)]']
    assert so.tekst_i_print(so._kall(linje, "print")[0]) == "Look. / Write it... now"
    assert so.lesbar_tekst('"It\'s " + getName(Var[55]) + "."') == "It's [navn Var[55]]."
    assert so._del_argumenter("Var[314],Var[315],-1,-1") == ["Var[314]", "Var[315]", "-1", "-1"]
    # loadRoom( inne i loadRoomWithEgo( skal ikke telles som loadRoom
    assert so._kall("loadRoomWithEgo(84,1,-1,-1);", "loadRoom") == []
