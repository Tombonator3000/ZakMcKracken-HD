"""Uttrekk av originalgrafikken i et SCUMM v6-spill (Sam & Max Hit the Road) til PNG.

Samme filer og samme metadata som uttrekket for The Dig (export.py), så build-mod,
oppskaleringen og grafikkjobbene kan bruke dem:

  rooms/roomNNN.png          rombakgrunnen i RGB med rommets første palett
  rooms/roomNNN_idx.png      samme bilde som 8-bits indeksbilde med paletten
  objects/objNNN_SS.png      objektbilde i tilstand SS (heksadesimalt, som IMxx) i RGBA
  objects/objNNN_SS_idx.png  indeksbilde, med den gjennomsiktige indeksen som tRNS
  costumes/costumeCCC_NNN.png      kostymerute i RGBA (rutenummer = lag * 128 + kode)
  costumes/costumeCCC_NNN_idx.png  indeksbilde med palettindeksene i rommet
  rooms.json, costumes.json  metadata

Dekodingen står i v6grafikk.py og følger ScummVM ved c9091321. Kostymefargene er indekser i
rompaletten. Fargene i RGBA-bildene er fra paletten i rommet kostymet ligger i (palett 0);
spillet kan vise dem med andre farger i andre rom og når et skript setter skuespillerpaletten.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from . import gamedata, v6grafikk

INDEX_FILE = "SAMNMAX.000"
DATA_FILE = "SAMNMAX.001"


def _transparent_index(pixels: bytearray, mask: bytearray, prefer: int) -> int:
    """En indeks ingen synlig piksel bruker, helst prefer. Den blir tRNS i indeksbildet."""
    used = {p for p, m in zip(pixels, mask) if m}
    if prefer not in used:
        return prefer
    for i in range(255, -1, -1):
        if i not in used:
            return i
    raise ValueError("alle 256 indekser er i bruk; ingen plass til gjennomsiktighet")


def _save_pair(dest: Path, name: str, w: int, h: int, pixels: bytearray, mask: bytearray, palette: bytes,
               transparent: int | None):
    """Lagrer name.png (RGB eller RGBA) og name_idx.png."""
    data = bytearray(pixels)
    if transparent is not None:
        for i, m in enumerate(mask):
            if not m:
                data[i] = transparent
    idx = Image.frombytes("P", (w, h), bytes(data))
    idx.putpalette(palette)
    if transparent is None:
        idx.save(dest / f"{name}_idx.png")
        idx.convert("RGB").save(dest / f"{name}.png")
    else:
        idx.save(dest / f"{name}_idx.png", transparency=transparent)
        rgb = idx.convert("RGB")
        alpha = Image.frombytes("L", (w, h), bytes(255 if m else 0 for m in mask))
        rgba = rgb.copy()
        rgba.putalpha(alpha)
        # Usynlige piksler får svart farge, som i uttrekket for The Dig
        black = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        black.paste(rgba, (0, 0), alpha)
        black.save(dest / f"{name}.png")


def _room_blocks(d: bytes, room: gamedata.Room) -> dict:
    off = room.offset
    size = gamedata.be32(d, off + 4)
    return {"off": off, "size": size}


def export_rooms(game: Path, out: Path, rooms_filter: set[int] | None = None) -> dict:
    """Rombakgrunner og objektbilder. Returnerer metadata som også skrives til rooms.json."""
    d, _ = gamedata.load(game / DATA_FILE)
    index = gamedata.read_index(game / INDEX_FILE)
    rooms = gamedata.read_rooms(game / DATA_FILE)
    (out / "rooms").mkdir(parents=True, exist_ok=True)
    (out / "objects").mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    written = 0
    room_meta: dict = {}
    for num in sorted(rooms):
        if rooms_filter and num not in rooms_filter:
            continue
        r = rooms[num]
        off, size = r.offset, gamedata.be32(d, r.offset + 4)
        trns = gamedata.find_child(d, off, size, b"TRNS")
        tcol = d[trns + 8] if trns is not None else 255
        palette = r.palettes[0] if r.palettes else bytes(768)
        info = {"name": index.room_names.get(num, ""), "width": r.width, "height": r.height,
                "palettes": len(r.palettes), "zplane": r.has_zplane, "cycles": [list(c) for c in r.cycles],
                "transparent": tcol, "objects": []}
        # Rombakgrunnen
        if r.width >= 8 and r.height > 0:
            rmim = gamedata.find_child(d, off, size, b"RMIM")
            im00 = gamedata.find_child(d, rmim, gamedata.be32(d, rmim + 4), b"IM00") if rmim is not None else None
            smap = gamedata.find_child(d, im00, gamedata.be32(d, im00 + 4), b"SMAP") if im00 is not None else None
            if smap is None:
                errors.append(f"rom {num}: fant ikke SMAP")
            else:
                try:
                    bm = v6grafikk.decode_smap(d, smap, r.width, r.height, tcol)
                    _save_pair(out / "rooms", f"room{num:03d}", bm.width, bm.height, bm.pixels, bm.mask, palette, None)
                    info["codecs"] = {str(k): v for k, v in sorted(bm.codecs.items())}
                    written += 1
                except (ValueError, IndexError) as e:
                    errors.append(f"rom {num}: {e}")
        # Objektbildene, hver tilstand
        cdhd = {o.obj_id: o for o in r.objects}
        for tag, c, s in gamedata.children(d, off + 8, off + size):
            if tag != b"OBIM":
                continue
            imhd = gamedata.find_child(d, c, s, b"IMHD")
            if imhd is None:
                continue
            obj_id = gamedata.le16(d, imhd + 8)
            o = cdhd.get(obj_id)
            if o is None or not o.states:
                continue
            entry = {"id": obj_id, "x": o.x, "y": o.y, "w": o.width, "h": o.height, "states": [], "kind": {}}
            for t2, c2, s2 in gamedata.children(d, c + 8, c + s):
                if t2[:2] != b"IM" or t2 == b"IMHD":
                    continue
                state = t2[2:4].decode("latin1")
                name = f"obj{obj_id:03d}_{state}"
                try:
                    smap = gamedata.find_child(d, c2, s2, b"SMAP")
                    bomp = gamedata.find_child(d, c2, s2, b"BOMP")
                    if smap is not None:
                        if o.width < 8 or o.height < 1:
                            raise ValueError(f"mål {o.width} x {o.height} i CDHD")
                        bm = v6grafikk.decode_smap(d, smap, o.width, o.height, tcol)
                        kind = "smap"
                    elif bomp is not None:
                        bm = v6grafikk.decode_bomp(d, bomp + 8)
                        kind = "bomp"
                    else:
                        raise ValueError("verken SMAP eller BOMP")
                    trans = _transparent_index(bm.pixels, bm.mask, tcol if kind == "smap" else 255)
                    _save_pair(out / "objects", name, bm.width, bm.height, bm.pixels, bm.mask, palette, trans)
                    entry["states"].append(state)
                    entry["kind"][state] = kind
                    if kind == "bomp":
                        entry.setdefault("bomp_size", {})[state] = [bm.width, bm.height]
                    entry.setdefault("transparent", {})[state] = trans
                    written += 1
                except (ValueError, IndexError) as e:
                    errors.append(f"rom {num}, {name}: {e}")
            if entry["states"]:
                info["objects"].append(entry)
        room_meta[str(num)] = info
    meta = {"game": "samnmax", "scumm": index.version, "game_md5_la0": index.md5, "game_md5_index": index.md5,
            "rooms": room_meta, "errors": errors}
    (out / "rooms.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    meta["written"] = written
    return meta


def export_costumes(game: Path, out: Path, costume_filter: set[int] | None = None) -> dict:
    """Alle kostymerutene animasjonene bruker. Returnerer {"written", "errors"} og skriver costumes.json."""
    d, _ = gamedata.load(game / DATA_FILE)
    index = gamedata.read_index(game / INDEX_FILE)
    rooms = gamedata.read_rooms(game / DATA_FILE)
    ids = gamedata.costume_ids(index, rooms)
    dest = out / "costumes"
    dest.mkdir(parents=True, exist_ok=True)
    meta: dict = {}
    errors: list[str] = []
    written = 0
    n = 0
    for num in sorted(rooms, key=lambda k: rooms[k].offset):
        r = rooms[num]
        palette = r.palettes[0] if r.palettes else bytes(768)
        for o in r.cost_offsets:
            cid = ids[n]
            n += 1
            if costume_filter and cid not in costume_filter:
                continue
            try:
                c = v6grafikk.decode_costume(d, r.offset + o)
            except (ValueError, IndexError) as e:
                errors.append(f"kostyme {cid}: {e}")
                continue
            cels = []
            first_by_data: dict[tuple, int] = {}
            empty = []
            for cel in c.cels:
                name = f"costume{cid:03d}_{cel.cel:03d}"
                if cel.width == 0 or cel.height == 0:
                    # Ruter uten mål tegner ingenting i motoren; de får ikke noe bilde
                    empty.append(cel.cel)
                    continue
                trans = _transparent_index(cel.pixels, cel.mask, 255)
                _save_pair(dest, name, cel.width, cel.height, cel.pixels, cel.mask, palette, trans)
                key = (cel.data, cel.width, cel.height)
                entry = {"cel": cel.cel, "lag": cel.limb, "kode": cel.code, "w": cel.width, "h": cel.height,
                         "rel_x": cel.rel_x, "rel_y": cel.rel_y, "move_x": cel.move_x, "move_y": cel.move_y,
                         "transparent": trans}
                if key in first_by_data:
                    entry["samme_bilde_som"] = first_by_data[key]
                else:
                    first_by_data[key] = cel.cel
                cels.append(entry)
                written += 1
            meta[str(cid)] = {
                "room": num, "format": f"0x{c.format:02X}", "farger": len(c.palette), "speil": c.mirror,
                "kostymepalett": list(c.palette),
                "colours": {"kind": "rom", "room": num, "palette": 0, "source": "rommet kostymet ligger i"},
                "cels": cels, "tomme_ruter": empty, "retninger": 4, "animasjoner": c.animations,
                "advarsler": c.errors,
            }
    (out / "costumes.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    return {"written": written, "errors": errors, "costumes": len(meta)}
