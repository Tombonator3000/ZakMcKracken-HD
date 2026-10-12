"""Eksport av originalgrafikk til PNG, klar for oppskalering.

Ikke portet til Sam & Max: dette er uttrekket fra The Dig (SCUMM v7, AKOS, dekoderne i
thedig-textures). For Zak (v3) brukes eksport_v3.py i stedet. Formatet på filene
under er det motoren og resten av pipelinen venter, og et v6-uttrekk må lage det samme.

For hvert rom og hvert objektbilde lages to filer:
  roomNNN.png       RGB (objekter: RGBA) med romets første palett. Dette er utgangspunktet for oppskalering.
  roomNNN_idx.png   8-bit indeksert med palett. Motoren bruker denne til å vite hvilke piksler
                    som fortsatt viser original bakgrunn, og til å fargekorrigere ved palettbytte.

Kostymeruter (AKOS) eksporteres som RGBA med fargene spillet viser, og som 8-bit
indeksbilde med kodene og de samme fargene som palett. Navnet bruker den ekte
kostyme-ID-en fra DCOS-katalogen, som er det motoren kjenner, ikke rekkefølgen i filen.

Hvilke farger kodene får, avhenger av kodeken (AKHD), slik ScummVM tegner dem:
  kodek 1   Koden er en plass i AKPL. Fargene er RGBS-blokken (de ekte fargene).
  kodek 5   Kodene tegnes rett som palettindekser i rommet, uten AKPL, så lenge skriptet
            ikke har satt skuespillerpaletten (AkosRenderer::setPalette, _useBompPalette).
  kodek 16  Kodene tegnes alltid rett som palettindekser (paintCelMajMin bruker ikke paletten).
For kodek 5 og 16 er fargene derfor paletten til rommet der kostymet vises. Rommet og
paletten står i docs/kostymefarger.csv når de er målt i spillet. Ellers brukes rommet
kostymet ligger i, og den av rommets paletter som gir det jevneste bildet (er flere
nesten like jevne, den første av dem). Står det "rgbs" i tabellen, brukes RGBS som for
kodek 1 (for kostymer skriptet setter skuespillerpaletten på).

Dekoding gjøres av digart (thedig-textures), som er sjekket byte for byte mot ScummVM.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image

from . import gamedata

CODEC_BYLE = 1     # AKOS_BYLE_RLE_CODEC
CODEC_BOMP = 5     # AKOS_CDAT_RLE_CODEC
CODEC_MAJMIN = 16  # AKOS_RUN_MAJMIN_CODEC
RAW_CODECS = (CODEC_BOMP, CODEC_MAJMIN)


def _require_digart():
    try:
        from digart import akos, la1  # noqa: F401
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("Mangler thedig-textures (digart), som uttrekket for The Dig trenger. Installer med: pip install -e \"pipeline[uttrekk]\" (se memory.md om repoet er borte)") from exc
    return la1, akos


def _indexed(index: bytes, w: int, h: int, palette: bytes, transparent: int | None) -> Image.Image:
    im = Image.frombytes("P", (w, h), index)
    im.putpalette(palette)
    if transparent is not None:
        im.info["transparency"] = transparent
    return im


def export_la1(game: Path, out: Path, rooms_filter: set[int] | None = None) -> dict:
    """Eksporterer rombakgrunner og objektbilder. Returnerer metadata som også skrives til rooms.json."""
    la1mod, _ = _require_digart()
    data = (game / "DIG.LA1").read_bytes()
    index = gamedata.read_index(game / "DIG.LA0")
    rooms = gamedata.read_rooms(game / "DIG.LA1")
    (out / "rooms").mkdir(parents=True, exist_ok=True)
    (out / "objects").mkdir(parents=True, exist_ok=True)

    # Hvilket rom hører hvert objekt til
    obj_room = {o.obj_id: r.number for r in rooms.values() for o in r.objects}
    errors: list = []
    written = 0
    for bmp in la1mod.iter_bitmaps(data, errors):
        if bmp.name.startswith("room"):
            num = int(bmp.name[4:])
            if rooms_filter and num not in rooms_filter:
                continue
            idx = _indexed(bmp.index, bmp.width, bmp.height, bmp.palette, None)
            idx.save(out / "rooms" / f"{bmp.name}_idx.png")
            idx.convert("RGB").save(out / "rooms" / f"{bmp.name}.png")
        else:
            obj_id = int(bmp.name[3:6])
            if rooms_filter and obj_room.get(obj_id) not in rooms_filter:
                continue
            idx = _indexed(bmp.index, bmp.width, bmp.height, bmp.palette, bmp.transparent)
            idx.save(out / "objects" / f"{bmp.name}_idx.png", transparency=bmp.transparent)
            idx.convert("RGBA").save(out / "objects" / f"{bmp.name}.png")
        written += 1

    meta = {
        "game_md5_la0": index.md5,
        "engine_version": index.engine_version,
        "rooms": {
            str(r.number): {
                "name": index.room_names.get(r.number, ""),
                "width": r.width,
                "height": r.height,
                "palettes": len(r.palettes),
                "zplane": r.has_zplane,
                "cycles": [list(c) for c in r.cycles],
                "objects": [
                    {"id": o.obj_id, "x": o.x, "y": o.y, "w": o.width, "h": o.height, "states": o.states}
                    for o in r.objects if o.states
                ],
            }
            for r in sorted(rooms.values(), key=lambda r: r.number)
            if not rooms_filter or r.number in rooms_filter
        },
        "errors": [str(e) for e in errors],
    }
    (out / "rooms.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    meta["written"] = written
    return meta


# ---------------------------------------------------------------- kostymefarger

def read_costume_colours(path: Path | None) -> dict[int, dict]:
    """Leser docs/kostymefarger.csv: kostyme,farger,rom,palett,kilde,notat.

    farger er "rom" (kodene som palettindekser i rommet og paletten som står der)
    eller "rgbs" (RGBS-blokken, for kostymer skriptet setter skuespillerpaletten på).
    """
    if not path or not Path(path).exists():
        return {}
    out: dict[int, dict] = {}
    with Path(path).open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = (row.get("kostyme") or "").strip()
            if not cid or cid.startswith("#"):
                continue
            kind = (row.get("farger") or "").strip().lower()
            if kind not in ("rom", "rgbs"):
                raise ValueError(f"{path}: kostyme {cid}: farger må være rom eller rgbs, ikke {kind!r}")
            spec = {"kind": kind, "source": (row.get("kilde") or "").strip() or "tabell"}
            if kind == "rom":
                spec["room"] = int(row["rom"])
                spec["palette"] = int(row.get("palett") or 0)
            out[int(cid)] = spec
    return out


def smoothness(rgb: np.ndarray, cels: list[tuple[np.ndarray, int]]) -> float:
    """Hvor ujevnt kostymet blir med fargene rgb (256 x 3): snitt av største kanalforskjell
    mellom nabopiksler (til høyre og under) som begge er synlige. Lavere er jevnere.

    Med feil palett får nabokoder som ligger tett i tegnerens palett, helt ulike farger, og
    bildet blir prikkete. Ruter under 20 synlige piksler telles ikke.
    """
    total = 0.0
    count = 0
    for idx, transparent in cels:
        mask = idx != transparent
        if int(mask.sum()) < 20:
            continue
        img = rgb[idx].astype(np.int16)
        for a, b, ma, mb in ((img[:, 1:], img[:, :-1], mask[:, 1:], mask[:, :-1]),
                             (img[1:], img[:-1], mask[1:], mask[:-1])):
            m = ma & mb
            if m.any():
                d = np.abs(a - b).max(axis=2)[m]
                total += float(d.sum())
                count += int(d.size)
    return total / count if count else 0.0


def costume_palette(codec: int, akpl: bytes, rgbs: bytes, home_room: int, rooms: dict,
                    cels: list[tuple[np.ndarray, int]], spec: dict | None) -> tuple[bytes, dict]:
    """Fargene (768 byte, kode -> RGB) kostymet tegnes med i spillet, og hvordan de er valgt.

    Kodek 1, og kostymer med farger=rgbs i tabellen: RGBS for kodene den dekker, ellers
    AKPL-plassen i hjemmerommets første palett (som før). Kodek 5 og 16: kodene rett i
    paletten til rommet i tabellen, ellers hjemmerommets jevneste palett.
    """
    home_pals = rooms[home_room].palettes if home_room in rooms else []
    if codec not in RAW_CODECS or (spec and spec["kind"] == "rgbs"):
        palette = home_pals[0] if home_pals else bytes(768)
        pal = bytearray(768)
        for code in range(256):
            if 3 * code + 3 <= len(rgbs):
                pal[3 * code:3 * code + 3] = rgbs[3 * code:3 * code + 3]
            else:
                pal_idx = akpl[code] if code < len(akpl) else code
                pal[3 * code:3 * code + 3] = palette[3 * pal_idx:3 * pal_idx + 3]
        info = {"kind": "rgbs"}
        if spec:
            info["source"] = spec["source"]
        return bytes(pal), info

    if spec:
        room, palno = spec["room"], spec["palette"]
        pals = rooms[room].palettes if room in rooms else []
        if palno >= len(pals):
            raise ValueError(f"rom {room} har ikke palett {palno}")
        return bytes(pals[palno]), {"kind": "rom", "room": room, "palette": palno, "source": spec["source"]}
    if not home_pals:
        return bytes(768), {"kind": "rom", "room": home_room, "palette": 0, "source": "ingen palett"}
    if len(home_pals) == 1:
        return bytes(home_pals[0]), {"kind": "rom", "room": home_room, "palette": 0, "source": "eneste palett"}
    scores = [smoothness(np.frombuffer(p, np.uint8).reshape(256, 3), cels) for p in home_pals]
    # Nesten like gode paletter (under 2 prosent fra den beste) gir nesten de samme fargene.
    # Da brukes den første av dem, helst palett 0, som rommet starter med.
    best = next(i for i, s in enumerate(scores) if s <= min(scores) * 1.02)
    return bytes(home_pals[best]), {"kind": "rom", "room": home_room, "palette": best, "source": "jevnest",
                                    "jevnhet": [round(s, 1) for s in scores]}


def export_costumes(game: Path, out: Path, costume_filter: set[int] | None = None,
                    colours: dict[int, dict] | None = None) -> int:
    """Eksporterer alle AKOS-ruter som RGBA med fargene spillet viser, og indeksbilder med kodene.

    colours: fra read_costume_colours (docs/kostymefarger.csv), kostyme-ID -> valg.
    """
    la1mod, akos = _require_digart()
    data = (game / "DIG.LA1").read_bytes()
    index = gamedata.read_index(game / "DIG.LA0")
    rooms = gamedata.read_rooms(game / "DIG.LA1")
    ids = gamedata.costume_ids(index, rooms)
    colours = colours or {}
    dest = out / "costumes"
    dest.mkdir(parents=True, exist_ok=True)

    errors: list = []
    written = 0
    file_no = 0
    meta: dict = {}
    for room_num, room_off in la1mod._iter_rooms(data, "LA1"):
        lflf_off = room_off - 8
        lflf_end = lflf_off + gamedata.be32(data, lflf_off + 4)
        for tag, c, size in gamedata.children(data, room_off, lflf_end):
            if tag != b"AKOS":
                continue
            cid = ids[file_no]
            file_no += 1
            if costume_filter and cid not in costume_filter:
                continue
            akhd_off = gamedata.find_child(data, c, size, b"AKHD")
            codec = gamedata.le16(data, akhd_off + 8 + 8) if akhd_off else 0
            akpl_off = gamedata.find_child(data, c, size, b"AKPL")
            akpl = data[akpl_off + 8:akpl_off + gamedata.be32(data, akpl_off + 4)] if akpl_off else b""
            # RGBS har de "ekte" fargene for hver AKPL-plass. Motoren tilpasser dem til
            # rompaletten med remapActorPalette. For kodek 1 er dette fargene tegnerne mente,
            # for kodek 5 og 16 brukes rompaletten (se costume_palette).
            rgbs_off = gamedata.find_child(data, c, size, b"RGBS")
            rgbs = data[rgbs_off + 8:rgbs_off + gamedata.be32(data, rgbs_off + 4)] if rgbs_off else b""
            anims = gamedata.akos_animations(data, c, size)
            cels = list(akos._process_costume(data, c, cid, errors, "AKOS"))
            arrays = [(np.frombuffer(cel.index, np.uint8).reshape(cel.height, cel.width), cel.transparent)
                      for cel in cels]
            # Palett for rutene og _idx-bildene: kode -> fargen spillet viser
            code_pal, how = costume_palette(codec, akpl, rgbs, room_num, rooms, arrays, colours.get(cid))
            pal = np.frombuffer(code_pal, np.uint8).reshape(256, 3)
            info = []
            for cel, (idx, transparent) in zip(cels, arrays):
                rgba = np.zeros((cel.height, cel.width, 4), np.uint8)
                rgba[..., :3] = pal[idx]
                rgba[..., 3] = np.where(idx != transparent, 255, 0)
                rgba[idx == transparent, :3] = 0
                Image.fromarray(rgba).save(dest / f"costume{cid:03d}_{cel.cel:03d}.png")
                # Kodene slik motoren ser dem, med fargene som palett. Motoren bruker
                # dette til å finne ut hvilken del av ruta en skjermpiksel kommer fra, og til
                # å fargejustere HD-pikslene når rommet er mørkere eller lysere.
                idx_im = _indexed(cel.index, cel.width, cel.height, code_pal, cel.transparent)
                idx_im.save(dest / f"costume{cid:03d}_{cel.cel:03d}_idx.png", transparency=cel.transparent)
                info.append({"cel": cel.cel, "w": cel.width, "h": cel.height})
                written += 1
            meta[str(cid)] = {"room": room_num, "codec": codec, "colours": how, "cels": info, **anims}
    (out / "costumes.json").write_text(json.dumps(meta, indent=1))
    return written


def costume_animations(game: Path) -> dict[int, dict]:
    """Animasjonene i hvert kostyme (gamedata.akos_animations), lest rett fra DIG.LA1.

    Det samme som `zakhd extract` skriver i costumes.json (retninger, animasjoner). Brukes når
    uttrekket er laget før animasjonene kom med.
    """
    data = (game / "DIG.LA1").read_bytes()
    index = gamedata.read_index(game / "DIG.LA0")
    rooms = gamedata.read_rooms(game / "DIG.LA1")
    return {cid: gamedata.akos_animations(data, off, size)
            for cid, _, off, size in gamedata.iter_akos(data, index, rooms) if cid >= 0}


def load_costumes(extract: Path, game: Path | None = None) -> dict[int, dict]:
    """costumes.json med animasjonene. Mangler de i uttrekket, leses de fra spillfilene når de finnes.

    Uten animasjoner (og uten spillfiler) har kostymet "animasjoner": [] og 4 retninger.
    """
    path = extract / "costumes.json"
    if not path.exists():
        return {}
    meta = {int(k): v for k, v in json.loads(path.read_text()).items()}
    if any("animasjoner" not in v for v in meta.values()) and game and (game / "DIG.LA1").exists():
        anims = costume_animations(game)
        for cid, v in meta.items():
            if "animasjoner" not in v and cid in anims:
                v.update(anims[cid])
    for v in meta.values():
        v.setdefault("retninger", 4)
        v.setdefault("animasjoner", [])
    return meta
