"""Uttrekk av originalgrafikken i Zak McKracken, FM-Towns (SCUMM v3, 256 farger) til PNG.

Samme filer og samme metadata som uttrekket for The Dig og Sam & Max, så build-mod,
oppskaleringen og grafikkjobbene kan bruke dem:

  rooms/roomNNN.png          rombakgrunnen i RGB med rommets palett (PA)
  rooms/roomNNN_idx.png      samme bilde som 8-bits indeksbilde med paletten
  objects/objNNN_01.png      objektbildet i RGBA. v3 har ett bilde per objekt; det vises i alle
                             tilstander unntatt 0, og navnet bruker 01 (se docs/HD-MOTOR.md)
  objects/objNNN_01_idx.png  indeksbilde, med en ubrukt indeks som tRNS (bildene er heldekkende)
  costumes/costumeCCC_NNN.png      kostymerute i RGBA (rutenummer = lag * 128 + kode)
  costumes/costumeCCC_NNN_idx.png  indeksbilde med palettindeksene i rommet
  fonts/charsetN.png         alle tegnene i tegnsett N (0 og 1), 16 per rad, som oversikt
  rooms.json, costumes.json, fonts.json  metadata

Dekodingen står i v3grafikk.py og følger ScummVM ved c9091321. Kostymefargene er indekser i
rompaletten. Fargene i RGBA-bildene er fra paletten i rommet kostymet ligger i; spillet kan vise
dem med andre farger i andre rom og når et skript setter skuespillerpaletten.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from . import lfl, v3grafikk
from .eksport_v6 import _save_pair, _transparent_index


def export_rooms(game: Path, out: Path, rooms_filter: set[int] | None = None) -> dict:
    """Rombakgrunner og objektbilder. Returnerer metadata som også skrives til rooms.json."""
    index = lfl.les_indeks(game / lfl.INDEX_FILE)
    (out / "rooms").mkdir(parents=True, exist_ok=True)
    (out / "objects").mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    written = 0
    room_meta: dict = {}
    for num in lfl.rom_numre(game):
        if rooms_filter and num not in rooms_filter:
            continue
        r = lfl.les_rom(game, num)
        if not r.ro_size:
            room_meta[str(num)] = {"name": "", "width": 0, "height": 0, "uten_grafikk": True, "objects": []}
            continue
        d = r.d
        info = {"name": index.rom_navn.get(num, ""), "width": r.bredde, "height": r.hoeyde,
                "palettes": 1, "farger": r.farger, "zplane": False, "cycles": [], "transparent": None,
                "objects": []}
        if r.bm is not None and r.bredde >= 8 and r.hoeyde > 0:
            try:
                bm = v3grafikk.decode_bm(d, r.bm, r.bredde, r.hoeyde)
                _save_pair(out / "rooms", f"room{num:03d}", bm.width, bm.height, bm.pixels, bm.mask, r.palett, None)
                info["codecs"] = {str(k): v for k, v in sorted(bm.codecs.items())}
                info["zplane"] = bm.zplan is not None
                info["zplan_striper"] = bm.zplan_striper
                written += 1
            except (ValueError, IndexError) as e:
                errors.append(f"rom {num}: {e}")
        else:
            errors.append(f"rom {num}: ingen BM-blokk")
        for o in r.objekter:
            oi = r.bilder.get(o.nr)
            entry = {"id": o.nr, "x": o.x, "y": o.y, "w": o.bredde, "h": o.hoeyde, "navn": o.navn.rstrip("@"),
                     "forelder": o.forelder, "states": [], "kind": {}}
            if oi is None or lfl.le32(d, oi) <= 8 or o.bredde < 8 or o.hoeyde < 1:
                # OI på 8 byte: objektet har ikke noe eget bilde (det er en del av bakgrunnen)
                entry["uten_bilde"] = True
                info["objects"].append(entry)
                continue
            name = f"obj{o.nr:03d}_01"
            try:
                bm = v3grafikk.decode_bm(d, oi + 8, o.bredde, o.hoeyde)
                trans = _transparent_index(bm.pixels, bm.mask, 255)
                _save_pair(out / "objects", name, bm.width, bm.height, bm.pixels, bm.mask, r.palett, trans)
                entry["states"].append("01")
                entry["kind"]["01"] = "smap"
                entry["transparent"] = {"01": trans}
                entry["codecs"] = {str(k): v for k, v in sorted(bm.codecs.items())}
                entry["zplane"] = bm.zplan is not None
                written += 1
            except (ValueError, IndexError) as e:
                errors.append(f"rom {num}, {name}: {e}")
            info["objects"].append(entry)
        room_meta[str(num)] = info
    meta = {"game": lfl.GAME_ID, "scumm": index.version, "game_md5_la0": index.md5, "game_md5_index": index.md5,
            "rooms": room_meta, "errors": errors}
    (out / "rooms.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    meta["written"] = written
    return meta


def export_costumes(game: Path, out: Path, costume_filter: set[int] | None = None) -> dict:
    """Alle kostymerutene animasjonene bruker. Returnerer {"written", "errors"} og skriver costumes.json."""
    index = lfl.les_indeks(game / lfl.INDEX_FILE)
    dest = out / "costumes"
    dest.mkdir(parents=True, exist_ok=True)
    meta: dict = {}
    errors: list[str] = []
    written = 0
    filer: dict[int, bytes] = {}
    paletter: dict[int, bytes] = {}
    for cid, (rom, off) in sorted(index.kostymer.items()):
        if costume_filter and cid not in costume_filter:
            continue
        if rom not in filer:
            r = lfl.les_rom(game, rom)
            filer[rom] = r.d
            paletter[rom] = r.palett if r.ro_size else None
        d = filer[rom]
        palette = paletter[rom]
        palett_kilde = rom
        if palette is None:
            # Kostymet ligger i en fil uten rom (47.LFL); bruk paletten i rom 1 for bildene
            palett_kilde = 1
            palette = lfl.les_rom(game, 1).palett
        try:
            if d[off + 4:off + 6] != b"CO":
                raise ValueError(f"ingen CO-blokk ved {rom:02d}.LFL offset {off}")
            c = v3grafikk.decode_costume_v3(d, off)
        except (ValueError, IndexError) as e:
            errors.append(f"kostyme {cid}: {e}")
            continue
        cels = []
        first_by_data: dict[tuple, int] = {}
        empty = []
        for cel in c.cels:
            name = f"costume{cid:03d}_{cel.cel:03d}"
            if cel.width == 0 or cel.height == 0:
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
            "room": rom, "offset": off, "format": f"0x{c.format:02X}", "farger": len(c.palette), "speil": c.mirror,
            "kostymepalett": list(c.palette),
            "colours": {"kind": "rom", "room": palett_kilde, "palette": 0,
                        "source": "rommet kostymet ligger i" if palett_kilde == rom else "rom 1 (filen har ikke noe rom)"},
            "cels": cels, "tomme_ruter": empty, "retninger": 4, "animasjoner": c.animations,
            "advarsler": c.errors,
        }
    (out / "costumes.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    return {"written": written, "errors": errors, "costumes": len(meta)}


def export_fonts(game: Path, out: Path) -> dict:
    """Tegnsettene som oversiktsark (hvit tekst på svart, 16 tegn per rad) og fonts.json."""
    dest = out / "fonts"
    dest.mkdir(parents=True, exist_ok=True)
    meta: dict = {}
    for nr in sorted(lfl.CHARSET_FILES):
        ts = lfl.les_tegnsett(game, nr)
        cell = 10
        rows = (ts.antall + 15) // 16
        img = Image.new("L", (16 * cell, rows * cell), 0)
        brukt = []
        for t in range(ts.antall):
            w = ts.bredder[t]
            if not w:
                continue
            g = v3grafikk.glyf(ts.glyfer, t, w, ts.hoeyde)
            if any(g):
                brukt.append(t)
            ch = Image.frombytes("L", (w, ts.hoeyde), bytes(255 if v else 0 for v in g))
            img.paste(ch, ((t % 16) * cell + 1, (t // 16) * cell + 1))
        img.save(dest / f"charset{nr}.png")
        meta[str(nr)] = {"fil": lfl.CHARSET_FILES[nr], "tegn": ts.antall, "hoeyde": ts.hoeyde,
                         "med_bredde": sum(1 for w in ts.bredder if w), "med_piksler": len(brukt),
                         "bredder": list(ts.bredder)}
    (out / "fonts.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    return meta
