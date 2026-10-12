"""Jobber for ChatGPT: pakking av oppgaver og mottak av ferdige bilder.

Arbeidsdeling: Claude (koden) lager jobbene og tar imot resultatene. ChatGPT lager
grafikken. Tom flytter filer mellom dem hvis ChatGPT ikke jobber direkte i repoet.

Hver jobb er ett lerret på 1536 x 1024 piksler (standardstørrelsen til ChatGPT sine
bilder, 3:2). Lerretet tilsvarer 384 x 256 originalpiksler i 4x, så et vanlig rom på
320 x 200 får en grå kant rundt seg, og bredere eller høyere rom deles i flere jobber
som overlapper. Da blir hver jobb nøyaktig 4x, uten omregning.

Store objektbilder (nærbilder, kart, paneler som spillet tegner over rommet) blir egne
jobber på samme måte: objektjobber med ID objNNN_SS. Referansen er objektbildet lagt over
rommets bakgrunn der spillet tegner det, så gjennomsiktige deler viser det som er bak.
Resultatet blir objects/objNNN_SS.png i nøyaktig 4x objektstørrelse.

De andre objektbildene er små (dører, brytere, lys, ting) og tegnes på plass i rommet i lag:
lagjobber med ID lagNNN_KK (rom NNN, lag KK). Et lag er rommets bakgrunn med et sett
objekttilstander lagt oppå der spillet tegner dem, og deles i de samme delene som rommet.
Objekter som overlapper, havner i hvert sitt lag. Ligger et objekt oppå et stort objektbilde
(spillet tegner objekter med lavere indeks sist), er det store bildet med i laget under det.
Etter kontrollen klippes hvert objekt ut på rektangelet sitt med gjennomsiktigheten fra originalen.
Ikoner i inventaret og andre ikoner som ikke tegnes på plass i rommet, legges i rutenett
på ikonark med ID ikonNN og klippes ut på samme måte. (I The Dig var det rom 93 og 107.
Zak har inventaret som tekst nederst på skjermen, så ikonark er trolig ikke aktuelle der.
Ikke kartlagt.)

Kostymerutene (figurene) pakkes på figurark med ID figCCC_KK, animasjon for animasjon, og
klippes ut til costumes/costumeCCC_NNN.png. Planleggingen og kontrollen av dem står i figur.py.

Mottaket sjekker hvert resultat mot originalen:
  - forskyvning (fasekorrelasjon på hele bildet og i blokker, for å se zoom og vridning)
  - likhet i kanter (om formene er de samme)
  - fargeavvik
og låser fargene til originalen (de grove fargene fra originalen, detaljene fra ChatGPT).
Deler av samme rom sys sammen med myk overgang i overlappen.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import shutil
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from .upscale import upscale_alpha

SCALE = 4
TILE = (384, 256)            # originalpiksler per jobb (gir 1536 x 1024 i 4x)
CANVAS = (TILE[0] * SCALE, TILE[1] * SCALE)
OVERLAP = 64                 # originalpiksler overlapp mellom deler
BORDER = (128, 128, 128)     # grå kant rundt bildet på lerretet

# Grenser for vurdering (originalpiksler). Kan justeres når vi ser ekte resultater.
OK_SHIFT, OK_BLOCK, OK_EDGES = 0.75, 1.0, 0.55
CHECK_SHIFT, CHECK_BLOCK, CHECK_EDGES = 1.5, 2.0, 0.40

# Objektbilder som er så store at de dekker mye av skjermen, blir egne jobber
BIG_AREA, BIG_W, BIG_H = 16000, 200, 150
# Store objekter som ikke blir jobber (i The Dig de ensfargede rutenettene i inventaret, obj618
# og obj627). Ikke kartlagt for Zak ennå.
SKIP_OBJECTS: dict[int, str] = {}

# Små objektbilder: lag i rommet (lagNNN_KK) og ikonark (ikonNN)
LAYER_MARGIN = 2             # originalpiksler fri avstand mellom objekter i samme lag
OBJ_EDGES = 0.50             # kantlikhet per objekt i lag og ikonark; under dette avvises jobben
OBJ_SAME_AS_BACK = 0.90      # objekter som ligner så mye på bakgrunnen, sjekkes ikke for om de mangler
OBJ_MISSING_MARGIN = 0.05    # et objekt mangler når resultatet ligner mer på bakgrunnen enn på objektet, med denne margen
OBJ_MIN_PIXELS = 40          # objekter med færre synlige piksler i utsnittet kontrolleres ikke enkeltvis
OBJ_MIN_EDGE = 1.0           # heller ikke objekter nesten uten kanter i originalen (jevn flate)
OBJ_REDRAWN_EDGE = 2.0       # grensen OBJ_EDGES gjelder bare objekter med så tydelige kanter (ellers tilfeldig)
ICON_MAX = (32, 24)          # små bilder på (0, 0) i et vanlig rom er ikoner (The Dig: rom 107)
ICON_BG = (0, 0, 171)        # bakgrunnen på ikonarket (The Dig: inventaret; ikke valgt for Zak)
ICON_SHEET = (320, 224)      # ikonarket i originalpiksler, midt på lerretet med grå kant
ICON_PAD = 8                 # originalpiksler mellom ikonene på arket

PROMPT_BASE = """Task: faithful HD remaster of one background picture from the adventure game Zak McKracken and the Alien Mindbenders (the English FM-Towns edition, 256 colors). This is a production asset. A game engine lays it exactly on top of the original picture, so the geometry must not change at all.

Input: the attached image is the original low-resolution artwork enlarged 4x with hard pixel edges. It sits on a plain gray (#808080) border. The border is only padding.

Do:
- Repaint the picture inside the gray border in high resolution with clean, natural detail: smooth gradients instead of dithering and color banding, crisp edges, believable texture in wood, metal, fabric, sky, water and light.
- Keep the original look: the same pixel-art style as the original FM-Towns game, the same colors, light direction, shadows, mood and contrast.
- Keep every shape exactly where it is: outlines, horizon, edges, doorways, signs, furniture and highlights must line up with the original pixels.

Do not:
- Do not move, zoom, crop, rotate, mirror or reframe anything. Do not extend the picture into the gray border. Keep the border plain gray (#808080).
- Do not add, remove or replace anything: no new objects, people, creatures, text, symbols or details. Do not fix or reinterpret anything.
- Copy symbols, glyphs, markings and engravings exactly in shape and position.
- No photorealism, no modern 3D look, no film grain, no vignette, no frame, no watermark, no signature.

Output: one image, exactly 1536 x 1024 pixels, with the same layout as the input."""

PROMPT_STYLE = """If a second image is attached, it is an already approved HD picture from the same game. Match its level of detail and brushwork, but take all content, shapes and colors from the first image."""

PROMPT_TILE = """This is part {part} of {parts} of a larger scene. The other parts are made separately and joined afterwards, so keep the edges of the picture natural, with no vignette, frame or fading."""

PROMPT_STATE = """This picture is one of several states of the same image in the game, and the game switches between them. If a second image is attached, it is the approved HD version of the first state. Copy everything that looks the same in both from that second image, so the states match exactly, and only paint the parts that differ."""

PROMPT_OBJECT = """This picture is a large image that the game draws on top of the room, such as a close-up, a map or a panel. Treat it as a background picture and follow all the rules above."""

PROMPT_LAYER = """This picture is the room with some of the game's small objects (such as doors, switches, lights, panels and items) drawn in place on top of it. Paint everything faithfully by the rules above: the room and every object. The objects are cut out of your picture afterwards by their exact position, so every object must stay exactly where it is, with the same size, outline and colors as in the input. Do not leave out, move, merge or redesign any object."""

PROMPT_LAYER_STYLE = """If a second image is attached, it is the approved HD version of the same room, or of the large picture the objects lie on, without these objects. Paint the room the same way as in that image, and give the objects the same level of detail, brushwork and light, so they fit into it. Take all shapes, positions and colors from the first image."""

PROMPT_ICONS = """This picture is a sheet of small inventory icons from the game, laid out in a grid on the plain dark blue color that the game shows behind them. Paint every icon faithfully by the rules above. The icons are cut out of your picture afterwards by their exact position, so every icon must stay exactly where it is, with the same size, outline and colors. Icons next to each other are often states of the same item (for example normal and highlighted): keep everything they have in common identical. Keep the dark blue background plain and flat, with no frames or grid."""


@dataclass
class Job:
    id: str
    rom: int
    navn: str
    del_nr: int
    deler: int
    rom_storrelse: tuple[int, int]
    region: tuple[int, int, int, int]      # x, y, w, h i bildet: rommet, eller objektbildet (originalpiksler)
    plassering: tuple[int, int]            # hvor regionen ligger på 384 x 256-lerretet
    skala: int = SCALE
    lerret: tuple[int, int] = CANVAS
    type: str = "rom"                      # "rom", "objekt", "lag", "ikon" eller "figur"
    objekt: int | None = None              # objekt-ID (bare objektjobber)
    tilstand: str | None = None            # tilstand som i filnavnet, for eksempel "01"
    objekt_i_rom: tuple[int, int, int, int] | None = None   # objektbildets x, y, b, h i rommet
    # Bare lag, ikonark og figurark. For ikonark og figurark er rom_storrelse arkets størrelse.
    lag: int | None = None                 # lagnummer (KK i lagNNN_KK) eller arknummer (NN i ikonNN, KK i figCCC_KK)
    objekter: list[dict] | None = None     # objektbildene i dette utsnittet: bilde, objekt, tilstand, rom, rekt
    underlag: list[str] | None = None      # store objektbilder under objektene, i tegnerekkefølge
    bilde_to: str | None = None            # anbefalt bilde to, for eksempel jobber/rom005/resultat.png
    # Bare figurark (figCCC_KK, se figur.py). rom er hjemrommet til kostymet og navn figuren.
    kostyme: int | None = None             # kostyme-ID (CCC)
    ruter: list[dict] | None = None        # kostymerutene i utsnittet: bilde, kostyme, rute, rekt, synlig, animasjon ...
    bakgrunn: list[int] | None = None      # den flate bakgrunnsfargen på arket
    pilot: bool | None = None              # med i piloten (står tidlig i ordren)
    rekkefolge: int | None = None          # plassen til kostymet i docs/figurer.csv
    innhold: str | None = None             # hva som står på arket, på norsk

    @property
    def bilde(self) -> str:
        """Bildet jobben hører til: roomNNN, objNNN_SS, lagNNN_KK, ikonNN eller figCCC_KK."""
        if self.type == "objekt":
            return f"obj{self.objekt:03d}_{self.tilstand}"
        if self.type == "lag":
            return f"lag{self.rom:03d}_{self.lag:02d}"
        if self.type == "ikon":
            return f"ikon{self.lag:02d}"
        if self.type == "figur":
            return f"fig{self.kostyme:03d}_{self.lag:02d}"
        return f"room{self.rom:03d}"

    @property
    def storrelse(self) -> tuple[int, int]:
        """Størrelsen på hele bildet (rommet, objektbildet eller ikonarket) i originalpiksler."""
        if self.type == "objekt":
            return (self.objekt_i_rom[2], self.objekt_i_rom[3])
        return (self.rom_storrelse[0], self.rom_storrelse[1])


# Felt som bare lag, ikonark og figurark har. Romjobber og objektjobber skriver dem ikke i jobb.json.
_PIECE_FIELDS = ("lag", "objekter", "underlag", "bilde_to", "kostyme", "ruter", "bakgrunn", "pilot", "rekkefolge",
                 "innhold")


def _load_job(data: dict) -> Job:
    """Leser jobb.json. Jobber laget før objektjobbene fantes, har ikke type og er romjobber."""
    in_room = data.get("objekt_i_rom")
    return Job(data["id"], data["rom"], data["navn"], data["del_nr"], data["deler"],
               tuple(data["rom_storrelse"]), tuple(data["region"]), tuple(data["plassering"]),
               type=data.get("type") or "rom", objekt=data.get("objekt"), tilstand=data.get("tilstand"),
               objekt_i_rom=tuple(in_room) if in_room else None, lag=data.get("lag"),
               objekter=data.get("objekter"), underlag=data.get("underlag"), bilde_to=data.get("bilde_to"),
               kostyme=data.get("kostyme"), ruter=data.get("ruter"), bakgrunn=data.get("bakgrunn"),
               pilot=data.get("pilot"), rekkefolge=data.get("rekkefolge"), innhold=data.get("innhold"))


def _order(job: Job) -> tuple:
    """Rom- og objektjobbene først: etter rom, romjobbene før objektjobbene i samme rom, så objekt,
    tilstand og del. Så lagjobbene etter rom, lag og del, ikonarkene, og til slutt figurarkene:
    piloten først, så etter rekkefølgen i docs/figurer.csv, kostyme, ark og del."""
    if job.type == "lag":
        return (1, job.rom, job.lag, 0, "", job.del_nr)
    if job.type == "ikon":
        return (2, job.lag, 0, 0, "", job.del_nr)
    if job.type == "figur":
        return (3, 0 if job.pilot else 1, job.rekkefolge or 10 ** 6, job.kostyme or 0, job.lag or 0, job.del_nr)
    return (0, job.rom, job.type != "rom", job.objekt or 0, job.tilstand or "", job.del_nr)


# ---------------------------------------------------------------- planlegging

def _positions(size: int, tile: int, overlap: int) -> list[int]:
    if size <= tile:
        return [0]
    n = math.ceil((size - overlap) / (tile - overlap))
    n = max(n, 2)
    return [round(i * (size - tile) / (n - 1)) for i in range(n)]


def plan_tiles(width: int, height: int) -> list[tuple[int, int, int, int, int, int]]:
    """Gir (x, y, w, h, ox, oy) for hver del av et rom."""
    out = []
    for y in _positions(height, TILE[1], OVERLAP):
        for x in _positions(width, TILE[0], OVERLAP):
            w, h = min(width, TILE[0]), min(height, TILE[1])
            ox, oy = (TILE[0] - w) // 2, (TILE[1] - h) // 2
            out.append((x, y, w, h, ox, oy))
    return out


def _is_nearly_empty(im: Image.Image) -> bool:
    colors = im.getcolors(maxcolors=4096)
    return colors is not None and len(colors) < 6


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_notes(path: Path | None) -> dict[int | str, str]:
    """Romnotater (rom = nummer), objektnotater (rom = objNNN, for eksempel obj241), notater for
    lagjobbene i et rom (rom = lagNNN) og for figurarkene til et kostyme (rom = figCCC). Lagnotatet
    går foran romnotatet i lagjobbene, for eksempel når romnotatet sier at en flate skal være tom
    fordi spillet tegner objekter der."""
    if not path or not path.exists():
        return {}
    notes: dict[int | str, str] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key, note = row.get("rom", "").strip().lower(), row.get("notat", "").strip()
            if not note:
                continue
            if key.isdigit():
                notes[int(key)] = note
            elif re.fullmatch(r"(obj|lag|fig)\d+", key):
                notes[f"{key[:3]}{int(key[3:]):03d}"] = note
    return notes


def is_big_object(width: int, height: int) -> bool:
    """Objektbilder som dekker mye av skjermen (nærbilder, kart, paneler) blir egne jobber."""
    return width * height >= BIG_AREA or width >= BIG_W or height >= BIG_H


def object_in_room(room: Image.Image | None, obj: Image.Image, x: int, y: int) -> Image.Image:
    """Objektbildet lagt over rommet der spillet tegner det.

    Gjennomsiktighet: objNNN_SS.png er RGBA med alfa 0 der objNNN_SS_idx.png har fargen som er
    merket gjennomsiktig. Der vises rommet bak. Utenfor rommet (noen UI-objekter er større
    enn rommet sitt) er det svart, som på skjermen.
    """
    obj = obj.convert("RGBA")
    if room is None:
        back = Image.new("RGBA", obj.size, (0, 0, 0, 255))
    else:
        # crop fyller det som ligger utenfor rommet med svart
        back = room.convert("RGB").crop((x, y, x + obj.width, y + obj.height)).convert("RGBA")
    back.alpha_composite(obj)
    return back.convert("RGB")


def _prompt(num: int, notes: dict, part: int, parts: int, is_object: bool = False,
            obj_key: str | None = None, later_state: bool = False) -> str:
    prompt = PROMPT_BASE
    if is_object:
        prompt += "\n\n" + PROMPT_OBJECT
    if obj_key and obj_key in notes:
        # Objektet har eget notat. Romnotatet beskriver rommet bak og kan være feil for objektet.
        prompt += "\n\nNote for this picture: " + notes[obj_key]
    elif num in notes:
        prompt += "\n\nNote for this room: " + notes[num]
    if parts > 1:
        prompt += "\n\n" + PROMPT_TILE.format(part=part, parts=parts)
    return prompt + "\n\n" + (PROMPT_STATE if later_state else PROMPT_STYLE)


def _write_job(jobs_dir: Path, job: Job, image: Image.Image, prompt: str, style_ref: Path | None) -> None:
    """Skriver referanse.png, original_1x.png, prompt.txt og jobb.json for én jobb."""
    x, y, w, h = job.region
    ox, oy = job.plassering
    d = jobs_dir / job.id
    d.mkdir(parents=True, exist_ok=True)
    canvas = Image.new("RGB", CANVAS, BORDER)
    part = image.crop((x, y, x + w, y + h)).resize((w * SCALE, h * SCALE), Image.NEAREST)
    canvas.paste(part, (ox * SCALE, oy * SCALE))
    canvas.save(d / "referanse.png")
    # Originalutsnittet i 1x, til kontroll og til ChatGPT hvis den vil se det
    image.crop((x, y, x + w, y + h)).save(d / "original_1x.png")
    (d / "prompt.txt").write_text(prompt + "\n", encoding="utf-8")

    data = asdict(job)
    for key in _PIECE_FIELDS:
        if data[key] is None:
            del data[key]
    data.update({
        "laget": time.strftime("%Y-%m-%d %H:%M"),
        "sha256_referanse": _sha(d / "referanse.png"),
        "sha256_prompt": hashlib.sha256(prompt.encode()).hexdigest(),
        "bilde_i_lerret": [ox * SCALE, oy * SCALE, w * SCALE, h * SCALE],
        "stilreferanse": style_ref.name if style_ref else None,
    })
    (d / "jobb.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))


def make_jobs(extract: Path, out: Path, rooms: set[int] | None = None, notes: dict[int, str] | None = None,
              style_ref: Path | None = None, figures: str | set[int] | None = None, game: Path | None = None,
              figure_list: Path | None = None) -> list[Job]:
    """Lager alle jobbene i out/jobber, status.csv og JOBBER.md.

    figures: figurark (figCCC_KK) for kostymene. None eller "ingen": ingen. "pilot": bare piloten
    (FIG_PILOT i figur.py). "alle" eller et sett kostyme-ID-er: alle arkene for dem. Animasjonene
    leses fra costumes.json, eller fra spillfilene i game når uttrekket er eldre. figure_list er
    docs/figurer.csv (navn og rekkefølge).
    """
    meta = json.loads((extract / "rooms.json").read_text())
    jobs_dir = out / "jobber"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    notes = notes or {}
    jobs: list[Job] = []
    skipped = []
    selected = []
    for key, info in sorted(meta["rooms"].items(), key=lambda kv: int(kv[0])):
        num = int(key)
        if rooms and num not in rooms:
            continue
        src = extract / "rooms" / f"room{num:03d}.png"
        room = Image.open(src).convert("RGB") if src.exists() else None
        selected.append((num, info, room))
        if room is not None and _is_nearly_empty(room):
            skipped.append(f"rom {num} ({info['name']}): nesten tomt (under 6 farger)")
        elif room is not None:
            tiles = plan_tiles(room.width, room.height)
            for i, (x, y, w, h, ox, oy) in enumerate(tiles):
                jid = f"rom{num:03d}" if len(tiles) == 1 else f"rom{num:03d}_del{i + 1}av{len(tiles)}"
                job = Job(jid, num, info["name"], i + 1, len(tiles), (room.width, room.height),
                          (x, y, w, h), (ox, oy))
                _write_job(jobs_dir, job, room, _prompt(num, notes, i + 1, len(tiles)), style_ref)
                jobs.append(job)
        # Store objektbilder i rommet, også når selve rommet er hoppet over
        jobs += _object_jobs(extract, jobs_dir, num, info, room, notes, style_ref)

    # Så de små objektbildene: lag i rommene etter romnummer, og til slutt ikonarkene
    icons: list[tuple[int, dict, list]] = []
    left: list[str] = []
    for num, info, room in selected:
        layer_objs, room_icons, room_left = sort_small_objects(extract, num, info, room)
        icons += [(num, obj, states) for _, obj, states in room_icons]
        left += room_left
        if layer_objs:
            layers = plan_layers(extract, num, info, room.size, layer_objs)
            big_jobs = [j for j in jobs if j.type == "objekt" and j.rom == num]
            jobs += _layer_jobs(extract, jobs_dir, num, info, room, layers, notes, big_jobs)
    jobs += _icon_jobs(extract, jobs_dir, plan_icon_sheets(icons), style_ref)

    # Figurark for kostymene, etter alt annet
    if figures not in (None, "ingen"):
        from . import export, figur
        costumes = export.load_costumes(extract, game)
        names = figur.read_figure_list(figure_list)
        chosen, pilot_only = figur.select_costumes(figures, costumes, names)
        jobs += figur.figure_jobs(extract, jobs_dir, chosen, costumes, names, meta["rooms"], notes, style_ref,
                                  pilot_only)

    _write_status(out, jobs, {})
    _write_overview(out, jobs, skipped, left)
    return jobs


def _object_jobs(extract: Path, jobs_dir: Path, num: int, info: dict, room: Image.Image | None,
                 notes: dict[int, str], style_ref: Path | None) -> list[Job]:
    jobs = []
    for obj in info["objects"]:
        if obj["id"] in SKIP_OBJECTS:
            continue
        for state in obj["states"]:
            name = f"obj{obj['id']:03d}_{state}"
            src = extract / "objects" / f"{name}.png"
            if not src.exists():
                continue
            im = Image.open(src)
            if not is_big_object(im.width, im.height):
                continue
            image = object_in_room(room, im, obj["x"], obj["y"])
            tiles = plan_tiles(image.width, image.height)
            for i, (x, y, w, h, ox, oy) in enumerate(tiles):
                jid = name if len(tiles) == 1 else f"{name}_del{i + 1}av{len(tiles)}"
                job = Job(jid, num, info["name"], i + 1, len(tiles), (info["width"], info["height"]),
                          (x, y, w, h), (ox, oy), type="objekt", objekt=obj["id"], tilstand=state,
                          objekt_i_rom=(obj["x"], obj["y"], image.width, image.height))
                prompt = _prompt(num, notes, i + 1, len(tiles), is_object=True, obj_key=f"obj{obj['id']:03d}",
                                 later_state=state != min(obj["states"]))
                _write_job(jobs_dir, job, image, prompt, style_ref)
                jobs.append(job)
    return jobs


# ---------------------------------------------------------------- små objekter: lag og ikonark

@dataclass
class Piece:
    """Et lite objektbilde i et lag (på plass i rommet) eller på et ikonark."""
    bilde: str                                 # objNNN_SS
    objekt: int
    tilstand: str
    rom: int                                   # rommet objektet hører til
    rekt: tuple[int, int, int, int]            # hele objektbildet (x, y, b, h) i lagbildet, originalpiksler
    synlig: tuple[int, int, int, int]          # de synlige pikslene (x0, y0, x1, y1) i lagbildet

    def to_json(self) -> dict:
        return {"bilde": self.bilde, "objekt": self.objekt, "tilstand": self.tilstand, "rom": self.rom,
                "rekt": list(self.rekt)}


@dataclass
class Layer:
    underlag: list[tuple[str, int, int]]       # store objektbilder under objektene (navn, x, y), tegnes først
    pieces: list[Piece]


def _mask_in(size: tuple[int, int], alpha: Image.Image, x: int, y: int, grow: int = 0) -> np.ndarray:
    """De synlige pikslene i et objektbilde som maske i rommets størrelse, eventuelt med margin."""
    m = Image.new("L", size, 0)
    m.paste(alpha.point(lambda v: 255 if v else 0), (x, y))
    if grow:
        m = m.filter(ImageFilter.MaxFilter(2 * grow + 1))
    return np.asarray(m) > 0


def _paste_over(base: Image.Image, im: Image.Image, x: int, y: int) -> None:
    """Legger et RGBA-bilde over base (RGBA) med hjørnet i (x, y). Det som havner utenfor, kuttes."""
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(base.width, x + im.width), min(base.height, y + im.height)
    if x1 > x0 and y1 > y0:
        base.alpha_composite(im, (x0, y0), (x0 - x, y0 - y, x1 - x, y1 - y))


def _overlaps(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    """Om to bokser (x0, y0, x1, y1) har noe felles."""
    return min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])


def sort_small_objects(extract: Path, num: int, info: dict, room: Image.Image | None
                       ) -> tuple[list[tuple[int, dict, list]], list[tuple[int, dict, list]], list[str]]:
    """Deler de små objektbildene i et rom i tre: de som tegnes i lag, ikonene og de som står igjen.

    Gir (lag, ikoner, igjen). Lag og ikoner er lister med (indeks, objekt, [(tilstand, RGBA-bilde)]),
    der indeksen er plassen i rommets objektliste. Store objektbilder (egne objektjobber) og
    SKIP_OBJECTS er ikke med. Ikoner er alle objektbildene i rom uten bakgrunn eller med nesten tom
    bakgrunn (inventaret i The Dig), og små bilder som står på (0, 0) i et vanlig rom.
    Ingen av dem tegnes på plass i rommet. Igjen står bilder som er helt gjennomsiktige eller
    ligger helt utenfor rommet.
    """
    empty_room = room is None or _is_nearly_empty(room)
    layer, icons, left = [], [], []
    for i, obj in enumerate(info["objects"]):
        if obj["id"] in SKIP_OBJECTS:
            continue
        states = []
        for state in obj["states"]:
            src = extract / "objects" / f"obj{obj['id']:03d}_{state}.png"
            if src.exists():
                im = Image.open(src).convert("RGBA")
                if not is_big_object(im.width, im.height):
                    states.append((state, im))
        if not states:
            continue
        w, h = states[0][1].size
        if empty_room or (obj["x"] == 0 and obj["y"] == 0 and w <= ICON_MAX[0] and h <= ICON_MAX[1]):
            icons.append((i, obj, states))
            continue
        keep = []
        for state, im in states:
            name = f"obj{obj['id']:03d}_{state}"
            box = im.getchannel("A").getbbox()
            if box is None:
                left.append(f"{name} (rom {num}): helt gjennomsiktig, ingenting å male")
            elif not _overlaps((obj["x"] + box[0], obj["y"] + box[1], obj["x"] + box[2], obj["y"] + box[3]),
                               (0, 0, room.width, room.height)):
                left.append(f"{name} (rom {num}): ligger utenfor rommet")
            else:
                keep.append((state, im))
        if keep:
            layer.append((i, obj, keep))
    return layer, icons, left


def plan_layers(extract: Path, num: int, info: dict, size: tuple[int, int],
                objects: list[tuple[int, dict, list]]) -> list[Layer]:
    """Fordeler de små objektbildene i et rom på lag.

    Lag 1 tar første tilstand av hvert objekt, lag 2 neste og så videre. Et objekt som ville
    overlappe (synlige piksler med LAYER_MARGIN) et annet i samme lag, venter til et senere lag.
    Objekter med flest tilstander igjen plasseres først, så det blir færre lag.

    ScummVM tegner rommets objekter fra siste til første i listen, så et objekt ligger oppå et
    stort objektbilde med høyere indeks. Er det store bildet under de synlige pikslene, er det
    med i laget som underlag (første tilstand). Objekter med ulikt underlag havner i ulike lag,
    de uten underlag først.
    """
    W, H = size
    bigs = []
    for j, obj in enumerate(info["objects"]):
        if obj["id"] in SKIP_OBJECTS or not obj["states"]:
            continue
        name = f"obj{obj['id']:03d}_{obj['states'][0]}"
        src = extract / "objects" / f"{name}.png"
        if not src.exists():
            continue
        im = Image.open(src).convert("RGBA")
        if is_big_object(im.width, im.height):
            bigs.append((j, name, obj["x"], obj["y"], _mask_in(size, im.getchannel("A"), obj["x"], obj["y"])))
    bigs.sort(key=lambda b: -b[0])        # tegnerekkefølge: høyeste indeks først

    groups: dict[tuple, list] = {}
    for i, obj, states in objects:
        seen = np.zeros((H, W), bool)
        for _, im in states:
            seen |= _mask_in(size, im.getchannel("A"), obj["x"], obj["y"])
        under = tuple((name, x, y) for j, name, x, y, m in bigs if j > i and (m & seen).any())
        groups.setdefault(under, []).append((i, obj, list(states)))

    layers = []
    for under in sorted(groups, key=lambda u: (len(u), u)):
        queue = {i: (obj, states) for i, obj, states in groups[under]}
        while any(states for _, states in queue.values()):
            taken = np.zeros((H, W), bool)
            pieces = []
            for i in sorted((i for i in queue if queue[i][1]), key=lambda i: (-len(queue[i][1]), i)):
                obj, states = queue[i]
                state, im = states[0]
                alpha = im.getchannel("A")
                if taken.any() and (_mask_in(size, alpha, obj["x"], obj["y"], LAYER_MARGIN) & taken).any():
                    continue
                taken |= _mask_in(size, alpha, obj["x"], obj["y"])
                states.pop(0)
                x, y = obj["x"], obj["y"]
                b = alpha.getbbox()
                pieces.append((i, Piece(f"obj{obj['id']:03d}_{state}", obj["id"], state, num,
                                        (x, y, im.width, im.height), (x + b[0], y + b[1], x + b[2], y + b[3]))))
            layers.append(Layer(list(under), [p for _, p in sorted(pieces, key=lambda ip: ip[0])]))
    return layers


def _layer_note(num: int, notes: dict, underlag: list[str]) -> str | None:
    """Notatet for et lag: lagnotatet for rommet, ellers notatet for det store bildet under, ellers romnotatet."""
    if f"lag{num:03d}" in notes:
        return notes[f"lag{num:03d}"]
    for name in reversed(underlag):         # det øverste store bildet først
        key = f"obj{int(_OBJ_ID.match(name).group(1)):03d}"
        if key in notes:
            return notes[key]
    return notes.get(num)


def _layer_prompt(num: int, notes: dict, part: int, parts: int, underlag: list[str]) -> str:
    prompt = PROMPT_BASE + "\n\n" + PROMPT_LAYER
    note = _layer_note(num, notes, underlag)
    if note:
        prompt += "\n\nNote for this room: " + note
    if parts > 1:
        prompt += "\n\n" + PROMPT_TILE.format(part=part, parts=parts)
    return prompt + "\n\n" + PROMPT_LAYER_STYLE


def layer_image(extract: Path, room: Image.Image, layer: Layer) -> Image.Image:
    """Lagbildet: rommet, de store bildene under og objektbildene i laget, slik spillet tegner dem."""
    image = room.convert("RGBA")
    for name, x, y in layer.underlag:
        _paste_over(image, Image.open(extract / "objects" / f"{name}.png").convert("RGBA"), x, y)
    for p in layer.pieces:
        _paste_over(image, Image.open(extract / "objects" / f"{p.bilde}.png").convert("RGBA"), p.rekt[0], p.rekt[1])
    return image.convert("RGB")


def _second_image(num: int, i: int, n: int, region: tuple[int, int, int, int], underlag: list[str],
                  big_jobs: list[Job]) -> str:
    """Anbefalt bilde to for en lagjobb: romjobben for samme del, eller objektjobben for et stort
    bilde under objektene når det dekker minst halve utsnittet."""
    x, y, w, h = region
    for name in reversed(underlag):          # det øverste store bildet først
        best, area = None, 0
        for j in big_jobs:
            if j.bilde != name:
                continue
            bx, by = j.objekt_i_rom[0] + j.region[0], j.objekt_i_rom[1] + j.region[1]
            a = (max(0, min(x + w, bx + j.region[2]) - max(x, bx)) *
                 max(0, min(y + h, by + j.region[3]) - max(y, by)))
            if a > area:
                best, area = j, a
        if best and area * 2 >= w * h:
            return f"jobber/{best.id}/resultat.png"
    jid = f"rom{num:03d}" if n == 1 else f"rom{num:03d}_del{i + 1}av{n}"
    return f"jobber/{jid}/resultat.png"


def assign_parts(pieces: list[Piece], tiles: list[tuple[int, int, int, int, int, int]]) -> dict[int, list[Piece]]:
    """Velger hvilke deler av rommet hvert objektbilde i et lag klippes ut av.

    Et objekt som ligger helt inne i en del, trenger bare den delen. Da velges helst en del som
    laget allerede trenger, ellers den som rommer flest slike objekter, og blant like den der
    objektet ligger mest midt i. Et objekt som ikke får plass i én del, klippes ut av alle delene
    det ligger i, sydd sammen. Gir delene (indeks i tiles) med objektene som klippes ut av dem.
    """
    boxes = [(x, y, x + w, y + h) for x, y, w, h, _, _ in tiles]

    def inside(p: Piece, b: tuple) -> bool:
        return b[0] <= p.synlig[0] and b[1] <= p.synlig[1] and p.synlig[2] <= b[2] and p.synlig[3] <= b[3]

    def off_center(p: Piece, b: tuple) -> float:
        return math.hypot((p.synlig[0] + p.synlig[2] - b[0] - b[2]) / 2, (p.synlig[1] + p.synlig[3] - b[1] - b[3]) / 2)

    out: dict[int, list[Piece]] = {}
    rest = []
    for p in pieces:
        full = [i for i, b in enumerate(boxes) if inside(p, b)]
        if full:
            rest.append((p, full))
        else:
            for i, b in enumerate(boxes):
                if _overlaps(p.synlig, b):
                    out.setdefault(i, []).append(p)
    while rest:
        waiting = []
        for p, full in rest:
            have = [i for i in full if i in out]
            if have:
                out[min(have, key=lambda i: off_center(p, boxes[i]))].append(p)
            else:
                waiting.append((p, full))
        rest = waiting
        if rest:
            counts: dict[int, int] = {}
            for _, full in rest:
                for i in full:
                    counts[i] = counts.get(i, 0) + 1
            best = max(counts, key=lambda i: (counts[i], -sum(off_center(p, boxes[i]) for p, f in rest if i in f)))
            out[best] = []
    return {i: sorted(out[i], key=lambda p: pieces.index(p)) for i in sorted(out) if out[i]}


def _layer_jobs(extract: Path, jobs_dir: Path, num: int, info: dict, room: Image.Image, layers: list[Layer],
                notes: dict, big_jobs: list[Job]) -> list[Job]:
    """Lagjobbene i et rom: samme deler og utsnitt som rommets egne jobber. Deler uten objekter hoppes over."""
    tiles = plan_tiles(room.width, room.height)
    jobs = []
    for k, layer in enumerate(layers, 1):
        image = layer_image(extract, room, layer)
        under = [name for name, _, _ in layer.underlag]
        for i, inside in assign_parts(layer.pieces, tiles).items():
            x, y, w, h, ox, oy = tiles[i]
            jid = f"lag{num:03d}_{k:02d}" + ("" if len(tiles) == 1 else f"_del{i + 1}av{len(tiles)}")
            job = Job(jid, num, info["name"], i + 1, len(tiles), (room.width, room.height), (x, y, w, h), (ox, oy),
                      type="lag", lag=k, objekter=[p.to_json() for p in inside], underlag=under,
                      bilde_to=_second_image(num, i, len(tiles), (x, y, w, h), under, big_jobs))
            _write_job(jobs_dir, job, image, _layer_prompt(num, notes, i + 1, len(tiles), under), None)
            jobs.append(job)
    return jobs


def plan_icon_sheets(icons: list[tuple[int, dict, list]]) -> list[list[Piece]]:
    """Legger ikonene i rutenett på ark (ICON_SHEET), med alle tilstandene til et ikon etter hverandre.

    Hver rute er det største ikonet pluss ICON_PAD. Et ikon deles ikke mellom to ark.
    """
    if not icons:
        return []
    cw = max(im.width for _, _, states in icons for _, im in states) + ICON_PAD
    ch = max(im.height for _, _, states in icons for _, im in states) + ICON_PAD
    cols, rows = max(1, ICON_SHEET[0] // cw), max(1, ICON_SHEET[1] // ch)
    x0, y0 = (ICON_SHEET[0] - cols * cw) // 2, (ICON_SHEET[1] - rows * ch) // 2
    sheets: list[list[Piece]] = [[]]
    for num, obj, states in icons:
        if len(sheets[-1]) + len(states) > cols * rows and sheets[-1]:
            sheets.append([])
        for state, im in states:
            n = len(sheets[-1])
            cx = x0 + (n % cols) * cw + (cw - im.width) // 2
            cy = y0 + (n // cols) * ch + (ch - im.height) // 2
            b = im.getchannel("A").getbbox() or (0, 0, 0, 0)
            sheets[-1].append(Piece(f"obj{obj['id']:03d}_{state}", obj["id"], state, num,
                                    (cx, cy, im.width, im.height), (cx + b[0], cy + b[1], cx + b[2], cy + b[3])))
    return sheets


def icon_sheet_image(extract: Path, pieces: list[Piece]) -> Image.Image:
    """Ikonarket: ikonene på inventarets mørkeblå farge."""
    image = Image.new("RGBA", ICON_SHEET, (*ICON_BG, 255))
    for p in pieces:
        _paste_over(image, Image.open(extract / "objects" / f"{p.bilde}.png").convert("RGBA"), p.rekt[0], p.rekt[1])
    return image.convert("RGB")


def _icon_jobs(extract: Path, jobs_dir: Path, sheets: list[list[Piece]], style_ref: Path | None) -> list[Job]:
    jobs = []
    sw, sh = ICON_SHEET
    for n, pieces in enumerate(sheets, 1):
        rooms = sorted({p.rom for p in pieces})
        job = Job(f"ikon{n:02d}", rooms[0], "ikonark", 1, 1, ICON_SHEET, (0, 0, sw, sh),
                  ((TILE[0] - sw) // 2, (TILE[1] - sh) // 2), type="ikon", lag=n,
                  objekter=[p.to_json() for p in pieces])
        prompt = PROMPT_BASE + "\n\n" + PROMPT_ICONS + "\n\n" + PROMPT_STYLE
        _write_job(jobs_dir, job, icon_sheet_image(extract, pieces), prompt, style_ref)
        jobs.append(job)
    return jobs


def _pieces_of(jobs: list[Job], kind: str) -> set[str]:
    """Objektbildene i lag eller ikonark, eller kostymerutene på figurarkene (kind = figur)."""
    return {p["bilde"] for j in jobs if j.type == kind for p in (j.ruter if kind == "figur" else j.objekter) or []}


def _write_overview(out: Path, jobs: list[Job], skipped: list[str], left: list[str] | None = None) -> None:
    n = {t: sum(j.type == t for j in jobs) for t in ("rom", "objekt", "lag", "ikon", "figur")}
    lines = ["# Jobbliste", "",
             f"{len(jobs)} jobber: {n['rom']} for rom, {n['objekt']} for store objektbilder, {n['lag']} lagjobber "
             f"med {len(_pieces_of(jobs, 'lag'))} små objektbilder og {n['ikon']} ikonark med "
             f"{len(_pieces_of(jobs, 'ikon'))} ikoner"
             + (f", og {len({j.bilde for j in jobs if j.type == 'figur'})} figurark ({n['figur']} jobber) med "
                f"{len(_pieces_of(jobs, 'figur'))} kostymeruter" if n["figur"] else "")
             + ". Status oppdateres i `status.csv` av `zakhd gpt-inn`.", "",
             "Objektjobbene (`objNNN_SS`) er store bilder som spillet tegner over rommet (nærbilder, kart, paneler). "
             "Utsnittet er da en del av objektbildet, ikke av rommet.", "",
             "Lagjobbene (`lagNNN_KK`) er rommet med et sett små objektbilder tegnet på plass, delt som rommet. "
             "Objektene klippes ut etterpå. Ikonarkene (`ikonNN`) er ikonene i inventaret i et rutenett.", ""]
    if n["figur"]:
        lines += ["Figurarkene (`figCCC_KK`) er animasjonsruter fra kostyme CCC på en flat bakgrunnsfarge. Rutene "
                  "klippes ut etterpå til `costumes/costumeCCC_NNN.png`. Kolonnen Objektbilder er da antall ruter.", ""]
    lines += ["| Jobb | Type | Rom | Navn | Del | Utsnitt (x, y, b, h) | Objektbilder |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
    for j in jobs:
        pieces = j.ruter if j.type == "figur" else j.objekter
        lines.append(f"| {j.id} | {j.type} | {j.rom} | {j.navn} | {j.del_nr} av {j.deler} | "
                     f"{', '.join(map(str, j.region))} | {len(pieces) if pieces else ''} |")
    if skipped:
        lines += ["", "Hoppet over:", ""] + [f"- {s}" for s in skipped]
    if left:
        lines += ["", "Objektbilder uten jobb (automatisk oppskalering i modden):", ""] + [f"- {s}" for s in left]
    (out / "JOBBER.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


STATUS_FIELDS = ["jobb", "type", "rom", "navn", "del", "status", "skift_x", "skift_y", "blokk_maks", "kantlikhet",
                 "fargeavvik", "kommentar"]


def _write_status(out: Path, jobs: list[Job], results: dict[str, dict]) -> None:
    with (out / "status.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=STATUS_FIELDS)
        w.writeheader()
        for j in jobs:
            r = results.get(j.id, {})
            w.writerow({"jobb": j.id, "type": j.type, "rom": j.rom, "navn": j.navn, "del": f"{j.del_nr}/{j.deler}",
                        "status": r.get("status", "ny"), "skift_x": r.get("skift_x", ""),
                        "skift_y": r.get("skift_y", ""), "blokk_maks": r.get("blokk_maks", ""),
                        "kantlikhet": r.get("kantlikhet", ""), "fargeavvik": r.get("fargeavvik", ""),
                        "kommentar": r.get("kommentar", "")})


# ---------------------------------------------------------------- bildeanalyse

def _lum(a: np.ndarray) -> np.ndarray:
    return a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114


def _box(a: np.ndarray, r: int, axis: int) -> np.ndarray:
    if r <= 0:
        return a
    pad = [(0, 0)] * a.ndim
    pad[axis] = (r + 1, r)
    p = np.pad(a, pad, mode="edge")
    c = np.cumsum(p, axis=axis)
    n = a.shape[axis]
    hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
    lo = np.take(c, np.arange(0, n), axis=axis)
    return (hi - lo) / (2 * r + 1)


def blur(a: np.ndarray, sigma: float) -> np.ndarray:
    """Tilnærmet gaussisk uskarphet med tre bokseuskarpheter (rask, bare numpy)."""
    if sigma <= 0:
        return a
    r = max(1, int(round(math.sqrt(12 * sigma * sigma / 3 + 1) - 1) // 2))
    out = a.astype(np.float64)
    for _ in range(3):
        out = _box(_box(out, r, 0), r, 1)
    return out


def phase_shift(ref: np.ndarray, img: np.ndarray) -> tuple[float, float, float]:
    """Hvor mye `img` er forskjøvet i forhold til `ref` (dx, dy) og hvor tydelig toppen er."""
    h, w = ref.shape
    win = np.outer(np.hanning(h), np.hanning(w))
    a = np.fft.fft2((ref - ref.mean()) * win)
    b = np.fft.fft2((img - img.mean()) * win)
    r = b * np.conj(a)
    r /= np.abs(r) + 1e-9
    c = np.fft.ifft2(r).real
    py, px = np.unravel_index(np.argmax(c), c.shape)
    peak = c[py, px]

    def sub(cm, c0, cp):
        d = cm - 2 * c0 + cp
        return 0.0 if abs(d) < 1e-12 else 0.5 * (cm - cp) / d

    dy = py + sub(c[(py - 1) % h, px], peak, c[(py + 1) % h, px])
    dx = px + sub(c[py, (px - 1) % w], peak, c[py, (px + 1) % w])
    if dy > h / 2:
        dy -= h
    if dx > w / 2:
        dx -= w
    return float(dx), float(dy), float(peak)


def _edges(l: np.ndarray) -> np.ndarray:
    gy, gx = np.gradient(blur(l, 0.8))
    return np.hypot(gx, gy)


def _edge_maps(original: Image.Image, candidate_4x: Image.Image) -> tuple[np.ndarray, ...]:
    """Originalen og resultatet i 1x (RGB) og kantene i begge."""
    w, h = original.size
    small = candidate_4x.resize((w, h), Image.BOX)
    o = np.asarray(original.convert("RGB"), dtype=np.float64)
    s = np.asarray(small.convert("RGB"), dtype=np.float64)
    return o, s, _edges(_lum(o)), _edges(_lum(s))


def compare(original: Image.Image, candidate_4x: Image.Image) -> dict:
    """Sammenligner et 4x-resultat med originalutsnittet (1x). Alle mål i originalpiksler."""
    w, h = original.size
    o, s, eo, es = _edge_maps(original, candidate_4x)
    dx, dy, _ = phase_shift(eo, es)

    # Forskyvning i blokker: avslører zoom, vridning og ting som er flyttet
    block_max = 0.0
    bw, bh = max(48, w // 3), max(48, h // 2)
    if w >= 2 * 48 or h >= 2 * 48:
        for by in range(0, max(1, h - bh + 1), bh):
            for bx in range(0, max(1, w - bw + 1), bw):
                a, b = eo[by:by + bh, bx:bx + bw], es[by:by + bh, bx:bx + bw]
                if a.std() < 1e-3 or b.std() < 1e-3:
                    continue
                bdx, bdy, _ = phase_shift(a, b)
                block_max = max(block_max, math.hypot(bdx, bdy))
    corr = float(np.corrcoef(eo.ravel(), es.ravel())[0, 1]) if eo.std() > 0 and es.std() > 0 else 0.0
    color = float(np.abs(blur(o, 2.0) - blur(s, 2.0)).mean())
    return {"skift_x": round(dx, 2), "skift_y": round(dy, 2), "blokk_maks": round(block_max, 2),
            "kantlikhet": round(corr, 3), "fargeavvik": round(color, 1)}


def judge(m: dict) -> tuple[str, str]:
    shift = math.hypot(m["skift_x"], m["skift_y"])
    if shift <= OK_SHIFT and m["blokk_maks"] <= OK_BLOCK and m["kantlikhet"] >= OK_EDGES:
        return "godkjent", ""
    reasons = []
    if shift > OK_SHIFT:
        reasons.append(f"forskjøvet {m['skift_x']:+.1f}, {m['skift_y']:+.1f} originalpiksler")
    if m["blokk_maks"] > OK_BLOCK:
        reasons.append(f"deler av bildet er flyttet eller zoomet (opptil {m['blokk_maks']:.1f} px)")
    if m["kantlikhet"] < OK_EDGES:
        reasons.append(f"formene ligner for lite på originalen (kantlikhet {m['kantlikhet']:.2f})")
    if shift <= CHECK_SHIFT and m["blokk_maks"] <= CHECK_BLOCK and m["kantlikhet"] >= CHECK_EDGES:
        return "sjekk", "; ".join(reasons)
    return "avvist", "; ".join(reasons)


def _piece_background(extract: Path, job: Job) -> Image.Image:
    """Utsnittet av et lag eller ikonark uten objektbildene: rommet med underlaget, eller arkets farge."""
    x, y, w, h = job.region
    if job.type == "ikon":
        return Image.new("RGB", (w, h), ICON_BG)
    room = Image.open(extract / "rooms" / f"room{job.rom:03d}.png").convert("RGBA")
    if job.underlag:
        objs = json.loads((extract / "rooms.json").read_text())["rooms"][str(job.rom)]["objects"]
        where = {o["id"]: (o["x"], o["y"]) for o in objs}
        for name in job.underlag:
            _paste_over(room, Image.open(extract / "objects" / f"{name}.png").convert("RGBA"),
                        *where[int(_OBJ_ID.match(name).group(1))])
    return room.convert("RGB").crop((x, y, x + w, y + h))


def _corr(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.corrcoef(a, b)[0, 1]) if a.std() > 0 and b.std() > 0 else 0.0


def check_pieces(original: Image.Image, candidate_4x: Image.Image, job: Job, extract: Path) -> dict[str, dict | None]:
    """Kontroll per objektbilde i et lag eller på et ikonark, bare på objektets synlige piksler.

    "objekt" er kantlikheten mellom resultatet og originalen (laget med objektet). "bakgrunn" er
    kantlikheten mellom resultatet og det samme utsnittet uten objektet, og måles bare når objektet
    skiller seg fra bakgrunnen. "kanter" er hvor tydelige kantene i originalen er (standardavvik).
    Avslører objekter som mangler, er flyttet eller tegnet om, selv når resten av utsnittet er
    riktig. None betyr ikke målt: for få synlige piksler i utsnittet, eller nesten ingen kanter.
    """
    _, _, eo, es = _edge_maps(original, candidate_4x)
    eb = _edges(_lum(np.asarray(_piece_background(extract, job), dtype=np.float64)))
    rx, ry, rw, rh = job.region
    out: dict[str, dict | None] = {}
    for p in job.objekter or []:
        src = extract / "objects" / f"{p['bilde']}.png"
        if not src.exists():
            out[p["bilde"]] = None
            continue
        x, y = p["rekt"][0] - rx, p["rekt"][1] - ry
        m = _mask_in((rw, rh), Image.open(src).convert("RGBA").getchannel("A"), x, y, grow=1)
        if m.sum() < OBJ_MIN_PIXELS or eo[m].std() < OBJ_MIN_EDGE:
            out[p["bilde"]] = None
            continue
        back = _corr(es[m], eb[m]) if _corr(eo[m], eb[m]) < OBJ_SAME_AS_BACK else None
        out[p["bilde"]] = {"objekt": round(_corr(eo[m], es[m]), 3),
                           "bakgrunn": None if back is None else round(back, 3),
                           "kanter": round(float(eo[m].std()), 1)}
    return out


def piece_problem(c: dict | None) -> str | None:
    """Hva som er galt med et objektbilde etter check_pieces, eller None når det er godt nok.

    Mangler: resultatet ligner mer på bakgrunnen uten objektet enn på objektet. Tegnet om:
    kantlikheten er under OBJ_EDGES, for objekter med tydelige kanter. Grensene er prøvd på ekte
    ChatGPT-rom (laveste kantlikhet i objektenes masker 0,75 med kantstyrke 2 eller mer) og på
    kunstige lag der objektene mangler.
    """
    if c is None:
        return None
    if c["bakgrunn"] is not None and c["bakgrunn"] > c["objekt"] + OBJ_MISSING_MARGIN:
        return f"mangler (kantlikhet {c['objekt']:.2f}, med bakgrunnen {c['bakgrunn']:.2f})"
    if c["objekt"] < OBJ_EDGES and c.get("kanter", OBJ_REDRAWN_EDGE) >= OBJ_REDRAWN_EDGE:
        return f"tegnet om (kantlikhet {c['objekt']:.2f})"
    return None


def lock_colors(candidate: np.ndarray, original_4x: np.ndarray, sigma: float, strength: float) -> np.ndarray:
    """Beholder detaljene fra ChatGPT, men tar de grove fargene fra originalen."""
    if strength <= 0:
        return candidate
    diff = blur(original_4x, sigma) - blur(candidate, sigma)
    return np.clip(candidate + strength * diff, 0, 255)


# ---------------------------------------------------------------- mottak

def detect_layout(size: tuple[int, int], region: tuple[int, int]) -> str | None:
    """Gjenkjenner hvordan et resultat er levert.

    "lerret": hele 1536 x 1024-lerretet med grå kant (3:2), slik referanse.png er.
    "direkte": bare bildet, i samme sideforhold som utsnittet (16:10 for rom på 320 x 200; Zak sine romstørrelser er ikke målt).
    Er utsnittet selv 3:2, er de to like, og lerret brukes (da er det ingen kant).
    """
    aspect = size[0] / size[1]
    canvas = CANVAS[0] / CANVAS[1]
    own = region[0] / region[1]
    if abs(aspect - canvas) / canvas <= 0.02:
        return "lerret"
    if abs(aspect - own) / own <= 0.02:
        return "direkte"
    return None


def has_native_alpha(path: Path) -> bool:
    """Har bildet sin egen myke alfakant (ny stil), ikke bare en flat bakgrunn?

    Figurark i den gamle stilen leveres på en flat bakgrunnsfarge (RGB). Den glatte stilen leveres
    som RGBA med gjennomsiktig bakgrunn og mellomnivåer i kantene.
    """
    with Image.open(path) as im:
        if im.mode not in ("RGBA", "LA", "PA") and "transparency" not in im.info:
            return False
        a = np.asarray(im.convert("RGBA"))[..., 3]
    transparent = float((a < 16).mean())
    soft = float(((a > 16) & (a < 240)).mean())
    return transparent > 0.2 and soft > 0.0005


def _find_result(d: Path) -> Path | None:
    for name in ("resultat.png", "resultat.webp", "resultat.jpg", "resultat.jpeg"):
        if (d / name).exists():
            return d / name
    return None


def read_rejections(path: Path | None) -> dict[str, dict]:
    """Manuelle avvisninger etter at Claude har sett på bildet: jobb, sha256_resultat, grunn, forslag, status.

    status er avvist (standard) eller sjekk. Sjekk betyr at bildet brukes til et bedre kommer, men at
    ChatGPT skal gjøre det om etter forslaget (for eksempel en søm mot HD-rommet).

    Avvisningen gjelder bare resultatet med den sjekksummen (eller alle med "*"), så en ny
    leveranse blir kontrollert på vanlig måte.
    """
    if not path or not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as f:
        return {r["jobb"].strip(): r for r in csv.DictReader(f) if r.get("jobb", "").strip()}


RANK = {"avvist": 0, "sjekk": 1, "godkjent": 2}


def repair_edges(part: Image.Image, sides: set[str], max_px: int = 8, factor: float = 3.0,
                 floor: float = 6.0) -> tuple[Image.Image, dict[str, int]]:
    """Retter ytterrader som er farget av den grå kanten på lerretet.

    For hver side som grenser mot kanten sammenlignes radene (eller kolonnene) ytterst med raden
    `max_px` piksler inn. Rader nær kanten som skiller seg mye mer fra den enn radene lenger inn gjør
    fra hverandre, byttes med den nærmeste gode raden. Gir bildet og hvor mange rader som ble byttet per side.
    """
    a = np.asarray(part, dtype=np.float64).copy()
    fixed: dict[str, int] = {}
    H, W = a.shape[:2]
    for side in sides:
        if side in ("topp", "bunn"):
            n = H
            line = (lambda i: a[i]) if side == "topp" else (lambda i: a[H - 1 - i])
        else:
            n = W
            line = (lambda i: a[:, i]) if side == "venstre" else (lambda i: a[:, W - 1 - i])
        if n < 3 * max_px:
            continue
        ref = line(max_px)
        noise = max(floor, float(np.abs(line(max_px) - line(max_px + 3)).mean()))
        bad = 0
        for i in range(max_px):
            if float(np.abs(line(i) - ref).mean()) > factor * noise:
                bad = i + 1
        if not bad:
            continue
        good = line(bad).copy()
        for i in range(bad):
            if side == "topp":
                a[i] = good
            elif side == "bunn":
                a[H - 1 - i] = good
            elif side == "venstre":
                a[:, i] = good
            else:
                a[:, W - 1 - i] = good
        fixed[side] = bad
    if not fixed:
        return part, fixed
    return Image.fromarray(np.clip(np.rint(a), 0, 255).astype(np.uint8)), fixed


def _evaluate(res_path: Path, job: "Job", d: Path, extract: Path, manual: dict, sigma: float, strength: float,
              preview_dir: Path) -> tuple[dict, np.ndarray | None]:
    """Kontrollerer én leveranse for en jobb. Gir resultatraden og det fargelåste bildet (None hvis avvist på format)."""
    res = Image.open(res_path).convert("RGB")
    x, y, w, h = job.region
    ox, oy = job.plassering
    r = {"resultat": res_path.name, "storrelse": list(res.size), "sha256_resultat": _sha(res_path)}
    layout = detect_layout(res.size, (w, h))
    if layout is None:
        r.update(status="avvist", kommentar=f"feil sideforhold {res.width}x{res.height}: skal være 3:2 som "
                 f"referanse.png (1536x1024) eller {w}:{h} som utsnittet (for eksempel {w * SCALE}x{h * SCALE})")
        return r, None
    r["format"] = layout
    if layout == "lerret":
        sx, sy = res.width / CANVAS[0], res.height / CANVAS[1]
        box = (ox * SCALE * sx, oy * SCALE * sy, (ox + w) * SCALE * sx, (oy + h) * SCALE * sy)
        part = res.crop(tuple(round(v) for v in box)).resize((w * SCALE, h * SCALE), Image.LANCZOS)
        # Sider som grenser mot den grå kanten: ChatGPT lar ofte kanten blø noen piksler inn
        sides = {s for s, touch in (("venstre", ox > 0), ("hoyre", ox + w < TILE[0]),
                                     ("topp", oy > 0), ("bunn", oy + h < TILE[1])) if touch}
        part, fixed = repair_edges(part, sides)
        if fixed:
            r["kantreparasjon"] = fixed
    else:
        part = res.resize((w * SCALE, h * SCALE), Image.LANCZOS)
    if min(res.width / (w * SCALE), res.height / (h * SCALE)) < 0.6:
        r["merknad"] = "lav oppløsning fra generatoren"
    original = Image.open(d / "original_1x.png").convert("RGB")
    m = compare(original, part)
    status, why = judge(m)
    orig4 = np.asarray(original.resize((w * SCALE, h * SCALE), Image.LANCZOS), dtype=np.float64)
    locked = lock_colors(np.asarray(part, dtype=np.float64), orig4, sigma, strength)
    if job.objekter:
        # Lag og ikonark: hvert objekt må også ligne på originalen, ellers blir utklippet feil
        checks = check_pieces(original, part, job, extract)
        r["objektkontroll"] = checks
        bad = [f"{n} {piece_problem(c)}" for n, c in checks.items() if piece_problem(c)]
        if bad:
            status = "avvist"
            listed = ", ".join(bad[:5]) + (f" og {len(bad) - 5} til" if len(bad) > 5 else "")
            why = "; ".join(filter(None, [why, f"objekter er feil: {listed}"]))
            r["forslag"] = PIECE_RETRY
    if job.type == "figur":
        # Figurark: hver rute for seg, og flimmer mellom nabo-ruter (etter fargelåsen, som i spillet)
        from . import figur
        checks = figur.check_cels(original, part, job, extract)
        pairs = figur.check_flicker(locked, job, extract)
        r["figurkontroll"], r["flimmer"] = checks, pairs
        bad, flick = figur.judge_sheet(checks, pairs)
        if bad:
            listed = ", ".join(bad[:5]) + (f" og {len(bad) - 5} til" if len(bad) > 5 else "")
            why = "; ".join(filter(None, [why, f"ruter er feil: {listed}"]))
        if flick:
            listed = ", ".join(flick[:3]) + (f" og {len(flick) - 3} til" if len(flick) > 3 else "")
            why = "; ".join(filter(None, [why, f"flimmer mellom nabo-ruter: {listed}"]))
        if bad or flick:
            status = "avvist"
            r["forslag"] = figur.FIG_RETRY if bad else figur.FIG_FLICKER_RETRY
    rej = manual.get(job.id)
    if rej and rej.get("sha256_resultat", "").strip() in ("*", r["sha256_resultat"]):
        status = (rej.get("status") or "").strip()
        if status not in ("avvist", "sjekk"):
            status = "avvist"
        why = rej.get("grunn", "").strip() or f"{status} ved gjennomsyn"
        r["forslag"] = rej.get("forslag", "").strip()
    r.update(m, status=status, kommentar=why)
    _preview(preview_dir / f"{job.id}.png", original, part, locked)
    return r, locked


def _spill(arr: np.ndarray, stem: Path) -> Path:
    """Legger et bilde på disk (PNG når det går, ellers npy) og gir stien."""
    if arr.dtype == np.uint8 and (arr.ndim == 2 or (arr.ndim == 3 and arr.shape[2] in (3, 4))):
        path = stem.with_suffix(".png")
        Image.fromarray(arr).save(path, compress_level=1)
    else:
        # Fargelåste bilder er float64 med verdier 0 til 255. float32 er nøyaktig nok for det
        # som blir lagret som 8 bit til slutt, og tar halve plassen.
        path = stem.with_suffix(".npy")
        np.save(path, arr.astype(np.float32) if arr.dtype == np.float64 else arr)
    return path


def _unspill(t):
    """Det motsatte av _spill. Annet enn en sti gis tilbake som det er."""
    if not isinstance(t, Path):
        return t
    if t.suffix == ".npy":
        a = np.load(t)
        return a.astype(np.float64) if a.dtype == np.float32 else a
    with Image.open(t) as im:
        return np.asarray(im).copy()


def import_results(work: Path, extract: Path, out: Path, *, sigma: float = 6.0, strength: float = 1.0,
                   only_approved: bool = False, rejections: Path | None = None) -> dict:
    jobs_dir = work / "jobber"
    best_dir = work / "beste"   # beste godtatte leveranse per jobb, så en dårligere ny ikke erstatter den
    manual = read_rejections(rejections)
    _take_inbox(work / "innboks", jobs_dir)
    preview_dir = work / "forhandsvisning"
    preview_dir.mkdir(parents=True, exist_ok=True)
    (out / "rooms").mkdir(parents=True, exist_ok=True)
    (out / "objects").mkdir(parents=True, exist_ok=True)

    spill_dir = tempfile.TemporaryDirectory(prefix="zakhd-inn-")
    entries = sorted(((_load_job(json.loads(jf.read_text())), jf.parent) for jf in jobs_dir.glob("*/jobb.json")),
                     key=lambda e: _order(e[0]))
    jobs: list[Job] = []
    results: dict[str, dict] = {}
    # Delene til hvert HD-bilde (roomNNN eller objNNN_SS), i jobbrekkefølge
    tiles: dict[str, list[tuple[Job, np.ndarray | None]]] = {}
    for job, d in entries:
        jobs.append(job)
        res_path = _find_result(d)
        if not res_path:
            tiles.setdefault(job.bilde, []).append((job, None))
            continue
        if job.type == "figur" and has_native_alpha(res_path):
            # Ny, glatt stil med egen alfakant: klippes ikke med originalens pikselmaske (Tom avviste
            # trappekantene). Tas inn med figurmottaket for ekte alfa (zakhd myke-figurer).
            results[job.id] = {"status": "levert", "sha256_resultat": _sha(res_path),
                               "kommentar": "glatt stil med ekte alfa, tas inn med figurmottaket for myke kanter"}
            tiles.setdefault(job.bilde, []).append((job, None))
            continue
        r, locked = _evaluate(res_path, job, d, extract, manual, sigma, strength, preview_dir)
        best_png, best_json = best_dir / f"{job.id}.png", best_dir / f"{job.id}.json"
        best = json.loads(best_json.read_text()) if best_json.exists() and best_png.exists() else None
        if best and best["sha256"] != r["sha256_resultat"] and RANK[r["status"]] < RANK.get(best["status"], 0):
            # Den nye leveransen er dårligere enn en tidligere: bruk den tidligere
            rb, lb = _evaluate(best_png, job, d, extract, manual, sigma, strength, preview_dir)
            if RANK[rb["status"]] > RANK[r["status"]]:
                rb["resultat"] = f"beste tidligere leveranse ({best['sha256'][:12]})"
                rb["kommentar"] = "; ".join(filter(None, [
                    rb.get("kommentar"), f"ny leveranse ({r['sha256_resultat'][:12]}) ble {r['status']}: "
                    f"{r.get('kommentar') or 'se retur.md'}, så den forrige brukes"]))
                r, locked = rb, lb
            else:
                best_png.unlink(missing_ok=True)
                best_json.unlink(missing_ok=True)
        elif RANK[r["status"]] > 0 and (not best or RANK[r["status"]] >= RANK.get(best["status"], 0)):
            best_dir.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(res_path, best_png)
            best_json.write_text(json.dumps({"sha256": r["sha256_resultat"], "status": r["status"]}))
        status = r["status"]
        results[job.id] = r
        _write_return(d, r)
        keep = status == "godkjent" or (status == "sjekk" and not only_approved)
        if keep and locked is not None:
            # Til disk og lest inn igjen først når HD-bildet settes sammen, så alle de godkjente
            # bildene ikke ligger i minnet samtidig (6 GB med 4463 jobber). Mindre enn før på disk
            # (npy med float64 fylte 14 GB med 2098 nye leveranser).
            locked = _spill(locked, Path(spill_dir.name) / job.id)
        tiles.setdefault(job.bilde, []).append((job, locked if keep else None))

    _write_status(work, jobs, results)

    provenance = {}
    done_rooms, done_objects, incomplete = [], [], []
    done_pieces: dict[str, list[str]] = {"lag": [], "ikon": [], "figur": []}
    first_state = {}
    piece_first: dict[int, str] = {}
    for j in jobs:
        if j.type == "objekt":
            first_state[j.objekt] = min(first_state.get(j.objekt, j.tilstand), j.tilstand)
        for p in j.objekter or []:
            piece_first[p["objekt"]] = min(piece_first.get(p["objekt"], p["tilstand"]), p["tilstand"])
    finished: dict[str, np.ndarray] = {}
    stale: list[str] = []
    settings = {"sigma": sigma, "styrke": strength}
    for name, parts in tiles.items():
        parts = [(j, _unspill(t)) for j, t in parts]
        first = parts[0][0]
        if first.type == "figur":
            from . import figur
            done, not_done, prov = figur.finish_cels(name, parts, results, jobs_dir, extract, out, settings)
            done_pieces["figur"] += done
            stale += not_done
            provenance.update(prov)
            if not_done and (done or any(t is not None for _, t in parts)):
                incomplete.append(f"{name} (kostyme {first.kostyme}): {len(done)} av {len(done) + len(not_done)} "
                                  "ruter klare")
            continue
        if first.type in ("lag", "ikon"):
            done, not_done, waiting, prov = _finish_pieces(name, parts, results, jobs_dir, extract, out, finished,
                                                           piece_first, settings)
            done_pieces[first.type] += done
            stale += not_done
            provenance.update(prov)
            if not_done and (done or any(t is not None for _, t in parts)):
                label = f"{name} (rom {first.rom})" if first.type == "lag" else name
                incomplete.append(f"{label}: {len(done)} av {len(done) + len(not_done)} objektbilder klare"
                                  + (f", {len(waiting)} venter på første tilstand" if waiting else ""))
            continue
        base = f"obj{first.objekt:03d}_{first_state[first.objekt]}" if first.type == "objekt" else None
        if base and base != name and base not in finished and all(t is not None for _, t in parts):
            # Senere tilstander venter på den første, så de kan bli like der bildene er like
            incomplete.append(f"{name} (rom {first.rom}): venter på {base}")
            stale.append(name)
            continue
        if any(t is None for _, t in parts):
            stale.append(name)
            have = sum(t is not None for _, t in parts)
            if have:
                label = f"rom {first.rom}" if first.type == "rom" else f"{name} (rom {first.rom})"
                incomplete.append(f"{label}: {have} av {len(parts)} deler klare")
            continue
        W, H = first.storrelse
        img = _stitch(W, H, [(j.region, t) for j, t in parts])
        made_by = [{"jobb": j.id, **results[j.id],
                    **{k: v for k, v in json.loads((jobs_dir / j.id / "jobb.json").read_text()).items()
                       if k in ("sha256_referanse", "sha256_prompt", "laget", "stilreferanse")}}
                   for j, _ in parts]
        if first.type == "objekt":
            same_as = None
            if base != name:
                img = match_state(img, finished[base], extract / "objects" / f"{name}_idx.png",
                                  extract / "objects" / f"{base}_idx.png")
                same_as = base
            finished[name] = img
            dest = out / "objects" / f"{name}.png"
            _with_alpha(img, extract / "objects" / f"{name}.png").save(dest)
            done_objects.append(name)
            provenance[name] = {
                "fil": f"objects/{name}.png", "sha256": _sha(dest), "storrelse": [W * SCALE, H * SCALE],
                "type": "objekt", "rom": first.rom, "objekt": first.objekt, "tilstand": first.tilstand,
                "fargelås": {"sigma": sigma, "styrke": strength}, "jobber": made_by,
            }
            if same_as:
                provenance[name]["likt_med"] = same_as
        else:
            dest = out / "rooms" / f"{name}.png"
            Image.fromarray(img).save(dest)
            done_rooms.append(first.rom)
            provenance[name] = {
                "fil": f"rooms/{name}.png", "sha256": _sha(dest), "storrelse": [W * SCALE, H * SCALE],
                "fargelås": {"sigma": sigma, "styrke": strength}, "jobber": made_by,
            }

    prov_path = out / "provenance.json"
    old = json.loads(prov_path.read_text()) if prov_path.exists() else {}
    # Objektbilder fra lag og ikonark og kostymeruter fra figurark er bestemt av jobbene som finnes nå.
    # De som ikke kom fra noen av dem denne gangen (for eksempel etter at lagene er lagt på nytt),
    # er ikke ferdige lenger.
    stale += [name for name, entry in old.items()
              if entry.get("type") in ("lag", "ikon", "figur") and name not in provenance]
    for name in stale:
        # Et bilde som var ferdig før, men ikke er det nå, skal ikke bli med i modden
        entry = old.pop(name, None)
        if entry:
            (out / entry["fil"]).unlink(missing_ok=True)
    old.update(provenance)
    prov_path.write_text(json.dumps(old, indent=1, ensure_ascii=False))
    summary = _report(work, jobs, results, sorted(done_rooms), sorted(done_objects), incomplete,
                      {k: sorted(v) for k, v in done_pieces.items()})
    return summary


PIECE_RETRY = ("Precise correction of the attached picture. Some of the small objects did not match the original: "
               "they were missing, moved or painted differently. Start again from referanse.png. Paint every object "
               "exactly where it is, with the same outline, size and colors, and keep every other shape in place. "
               "Do not zoom, shift, crop or reframe. Keep the gray border plain gray. Same size 1536 x 1024.")


def _cut(size: tuple[int, int], parts: list[tuple[tuple[int, int, int, int], np.ndarray]], rect: list[int],
         original: Path) -> np.ndarray:
    """Klipper ut et objektbilde (x, y, b, h i originalpiksler) i 4x av delene det ligger i, sydd sammen.

    Det som ingen av delene dekker (gjennomsiktige kanter, eller deler av objekter som stikker ut av
    rommet og som spillet derfor aldri viser), tas fra originalen forstørret, så størrelsen blir riktig.
    """
    x, y, w, h = rect
    W, H = size
    with Image.open(original) as o:
        out = np.array(o.convert("RGB").resize((w * SCALE, h * SCALE), Image.LANCZOS))
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return out
    box = (x0, y0, x1 - x0, y1 - y0)
    covered = np.zeros(((y1 - y0) * SCALE, (x1 - x0) * SCALE), bool)
    for (px, py, pw, ph), _ in parts:
        cx0, cy0, cx1, cy1 = max(px, x0), max(py, y0), min(px + pw, x1), min(py + ph, y1)
        if cx1 > cx0 and cy1 > cy0:
            covered[(cy0 - y0) * SCALE:(cy1 - y0) * SCALE, (cx0 - x0) * SCALE:(cx1 - x0) * SCALE] = True
    view = out[(y0 - y) * SCALE:(y1 - y) * SCALE, (x0 - x) * SCALE:(x1 - x) * SCALE]
    view[covered] = _stitch(W, H, parts, box)[covered]
    return out


def _finish_pieces(name: str, parts: list[tuple[Job, np.ndarray | None]], results: dict[str, dict], jobs_dir: Path,
                   extract: Path, out: Path, finished: dict[str, np.ndarray], first_state: dict[int, str],
                   settings: dict) -> tuple[list[str], list[str], list[str], dict]:
    """Klipper ut objektbildene som er ferdige, av delene til et lag eller ikonark.

    Hver del lister objektbildene som klippes ut av den (se assign_parts). Et objektbilde er ferdig
    når alle delene det står i, er godtatt, og klippes da ut av dem, sydd sammen hvis de er flere.
    Senere tilstander venter på den første og gjøres like den der originalbildene er like
    (match_state), som for objektjobbene. Gir (ferdige, ikke ferdige, venter, provenance).
    """
    first = parts[0][0]
    kept = {j.id: t for j, t in parts if t is not None}
    pieces: dict[str, dict] = {}
    holders: dict[str, list[Job]] = {}
    for j, _ in parts:
        for p in j.objekter or []:
            pieces.setdefault(p["bilde"], p)
            holders.setdefault(p["bilde"], []).append(j)
    done, not_done, waiting, prov = [], [], [], {}
    for bilde, p in pieces.items():
        if any(j.id not in kept for j in holders[bilde]):
            not_done.append(bilde)
            continue
        base = f"obj{p['objekt']:03d}_{first_state[p['objekt']]}"
        if base != bilde and base not in finished:
            not_done.append(bilde)
            waiting.append(bilde)
            continue
        src = extract / "objects" / f"{bilde}.png"
        hd = _cut(first.storrelse, [(j.region, kept[j.id]) for j in holders[bilde]], p["rekt"], src)
        if base != bilde:
            hd = match_state(hd, finished[base], extract / "objects" / f"{bilde}_idx.png",
                             extract / "objects" / f"{base}_idx.png")
        finished[bilde] = hd
        dest = out / "objects" / f"{bilde}.png"
        _with_alpha(hd, src).save(dest)
        done.append(bilde)
        made_by = []
        for j in holders[bilde]:
            r = {k: v for k, v in results[j.id].items() if k != "objektkontroll"}
            meta = json.loads((jobs_dir / j.id / "jobb.json").read_text())
            made_by.append({"jobb": j.id, **r, "kantlikhet_objekt": results[j.id].get("objektkontroll", {}).get(bilde),
                            **{k: v for k, v in meta.items()
                               if k in ("sha256_referanse", "sha256_prompt", "laget", "stilreferanse")}})
        prov[bilde] = {
            "fil": f"objects/{bilde}.png", "sha256": _sha(dest), "storrelse": [p["rekt"][2] * SCALE, p["rekt"][3] * SCALE],
            "type": first.type, "rom": p["rom"], "objekt": p["objekt"], "tilstand": p["tilstand"],
            "lag": name, "rekt_i_lag": p["rekt"], "underlag": first.underlag or [],
            "fargelås": settings, "jobber": made_by,
        }
        if base != bilde:
            prov[bilde]["likt_med"] = base
    return done, not_done, waiting, prov


def match_state(img: np.ndarray, base_hd: np.ndarray, idx: Path, base_idx: Path, grow: int = 2,
                feather: float = 3.0) -> np.ndarray:
    """Gjør en senere tilstand lik den første der originalbildene er like.

    Der indeksbildene er like (med en margin på `grow` originalpiksler), brukes HD-bildet til den
    første tilstanden. Bare det som er forskjellig, tas fra ChatGPT-bildet for denne tilstanden.
    Overgangen mykes opp med `feather` HD-piksler. Da skifter ikke hender og bakgrunn utseende
    når spillet bytter tilstand.
    """
    a, b = np.asarray(Image.open(idx)), np.asarray(Image.open(base_idx))
    if a.shape != b.shape or base_hd.shape != img.shape:
        return img
    diff = Image.fromarray(((a != b) * 255).astype(np.uint8))
    if grow:
        diff = diff.filter(ImageFilter.MaxFilter(2 * grow + 1))
    mask = np.asarray(diff.resize((img.shape[1], img.shape[0]), Image.NEAREST), dtype=np.float64) / 255
    if feather:
        mask = np.clip(blur(mask, feather), 0, 1)
    out = base_hd.astype(np.float64) * (1 - mask[..., None]) + img.astype(np.float64) * mask[..., None]
    return np.clip(np.rint(out), 0, 255).astype(np.uint8)


def _with_alpha(img: np.ndarray, original: Path) -> Image.Image:
    """HD-objektbildet som RGBA med gjennomsiktigheten fra originalen (skarpe kanter, som i modden)."""
    hd = Image.fromarray(img).convert("RGBA")
    if original.exists():
        o = Image.open(original).convert("RGBA")
        if (o.width * SCALE, o.height * SCALE) == hd.size:
            hd.putalpha(upscale_alpha(o.getchannel("A"), SCALE))
    return hd


def _take_inbox(inbox: Path, jobs_dir: Path) -> None:
    """Bilder lagt i work/gpt/innboks/ med jobbnavnet (for eksempel rom022.png) flyttes inn i jobben."""
    if not inbox.is_dir():
        return
    for f in sorted(inbox.iterdir()):
        if f.suffix.lower() not in (".png", ".webp", ".jpg", ".jpeg") or not (jobs_dir / f.stem).is_dir():
            continue
        d = jobs_dir / f.stem
        old = _find_result(d)
        if old:
            old.rename(d / f"forrige_{time.strftime('%Y%m%d_%H%M%S')}{old.suffix}")
        f.rename(d / f"resultat{f.suffix.lower()}")


def _write_return(d: Path, r: dict) -> None:
    ret = d / "retur.md"
    if r["status"] == "godkjent":
        if ret.exists():
            ret.unlink()
        return
    suggestion = r.get("forslag") or (
        "Precise correction of the attached HD picture. The previous result did not line up with the original. "
        "Start again from referanse.png and keep every outline, edge and object at exactly the same pixel position "
        "as in that image. Do not zoom, shift, crop or reframe. Keep the gray border plain gray. "
        "Same size 1536 x 1024.")
    text = [f"# {d.name}: {r['status']}", "", f"Grunn: {r.get('kommentar') or 'se status.csv'}", "",
            "Forslag til nytt forsøk (lim inn sammen med referanse.png):", "", "```text", suggestion, "```"]
    ret.write_text("\n".join(text) + "\n", encoding="utf-8")


def _preview(path: Path, original: Image.Image, part: Image.Image, locked: np.ndarray) -> None:
    w, h = part.size
    a = original.resize((w, h), Image.NEAREST)
    c = Image.fromarray(locked.astype(np.uint8))
    sheet = Image.new("RGB", (w * 3 + 16, h), (24, 24, 28))
    for i, im in enumerate((a, part, c)):
        sheet.paste(im, (i * (w + 8), 0))
    if sheet.width > 2400:
        sheet = sheet.resize((2400, round(sheet.height * 2400 / sheet.width)), Image.LANCZOS)
    sheet.save(path)


def _stitch(W: int, H: int, parts: list[tuple[tuple[int, int, int, int], np.ndarray]],
            box: tuple[int, int, int, int] | None = None) -> np.ndarray:
    """Syr sammen deler av et bilde på W x H originalpiksler med myk overgang i overlappen.

    Med box (x, y, b, h) lages bare det utsnittet, med de samme vektene som i hele bildet.
    """
    bx, by, bw, bh = box or (0, 0, W, H)
    acc = np.zeros((bh * SCALE, bw * SCALE, 3))
    wsum = np.zeros((bh * SCALE, bw * SCALE, 1))
    ramp = OVERLAP * SCALE
    for (x, y, w, h), img in parts:
        x0, y0, x1, y1 = max(x, bx), max(y, by), min(x + w, bx + bw), min(y + h, by + bh)
        if x1 <= x0 or y1 <= y0:
            continue
        wx = np.ones(w * SCALE)
        wy = np.ones(h * SCALE)
        idx = np.arange(w * SCALE) + 0.5
        if x > 0:
            wx = np.minimum(wx, idx / ramp)
        if x + w < W:
            wx = np.minimum(wx, (w * SCALE - idx) / ramp)
        idy = np.arange(h * SCALE) + 0.5
        if y > 0:
            wy = np.minimum(wy, idy / ramp)
        if y + h < H:
            wy = np.minimum(wy, (h * SCALE - idy) / ramp)
        sx, sy = slice((x0 - x) * SCALE, (x1 - x) * SCALE), slice((y0 - y) * SCALE, (y1 - y) * SCALE)
        dx, dy = slice((x0 - bx) * SCALE, (x1 - bx) * SCALE), slice((y0 - by) * SCALE, (y1 - by) * SCALE)
        weight = np.clip(np.outer(wy[sy], wx[sx]), 1e-4, 1)[..., None]
        acc[dy, dx] += img[sy, sx] * weight
        wsum[dy, dx] += weight
    return np.clip(acc / np.maximum(wsum, 1e-9), 0, 255).astype(np.uint8)


def _done_line(label: str, done: list, total: int) -> str:
    return f"Ferdige {label}: {len(done)} av {total}" + (f" ({', '.join(map(str, done))})" if done else "")


def _report(work: Path, jobs: list[Job], results: dict[str, dict], done_rooms: list[int], done_objects: list[str],
            incomplete: list[str], done_pieces: dict[str, list[str]] | None = None) -> dict:
    done_pieces = done_pieces or {}
    counts: dict[str, int] = {}
    by_type: dict[tuple[str, str], int] = {}
    for j in jobs:
        s = results.get(j.id, {}).get("status", "ny")
        counts[s] = counts.get(s, 0) + 1
        by_type[(j.type, s)] = by_type.get((j.type, s), 0) + 1
    rooms_total = len({j.rom for j in jobs if j.type == "rom"})
    objects_total = len({j.bilde for j in jobs if j.type == "objekt"})
    pieces_total = {k: len(_pieces_of(jobs, k)) for k in ("lag", "ikon", "figur")}
    types = [("rom", "Romjobber"), ("objekt", "Objektjobber"), ("lag", "Lagjobber"), ("ikon", "Ikonark")]
    if pieces_total["figur"]:
        types.append(("figur", "Figurark"))
    lines = ["# Rapport fra gpt-inn", "", time.strftime("Laget %Y-%m-%d %H:%M"), "",
             "| Status | " + " | ".join(t for _, t in types) + " |", "| --- " * (len(types) + 1) + "|"]
    lines += [f"| {s} | " + " | ".join(str(by_type.get((k, s), 0)) for k, _ in types) + " |" for s in sorted(counts)]
    lines += ["", f"- {_done_line('rom', done_rooms, rooms_total)}",
              f"- {_done_line('objekter', done_objects, objects_total)}"]
    if pieces_total["lag"]:
        lines.append(f"- Ferdige objektbilder fra lag: {len(done_pieces.get('lag', []))} av {pieces_total['lag']}")
    if pieces_total["ikon"]:
        lines.append(f"- Ferdige ikoner fra ikonark: {len(done_pieces.get('ikon', []))} av {pieces_total['ikon']}")
    if pieces_total["figur"]:
        sheets = {j.bilde for j in jobs if j.type == "figur"}
        ok = {j.bilde for j in jobs if j.type == "figur"} - {
            j.bilde for j in jobs if j.type == "figur" and results.get(j.id, {}).get("status") not in ("godkjent", "sjekk")}
        lines.append(f"- Figurark: {len(ok)} av {len(sheets)} godtatt. Ferdige figurruter: "
                     f"{len(done_pieces.get('figur', []))} av {pieces_total['figur']}")
    if incomplete:
        lines += ["", "Bilder som venter på flere deler:", ""] + [f"- {s}" for s in incomplete]
    bad = [(j, results[j.id]) for j in jobs if results.get(j.id, {}).get("status") in ("avvist", "sjekk")]
    if bad:
        lines += ["", "Må sees på (se `retur.md` i jobbmappen):", "", "| Jobb | Status | Grunn |", "| --- | --- | --- |"]
        lines += [f"| {j.id} | {r['status']} | {r.get('kommentar', '')} |" for j, r in bad]
    lines += ["", "Forhåndsvisning per jobb i `forhandsvisning/`: original 4x, ChatGPT, etter fargelås."]
    (work / "RAPPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"status": counts, "ferdige_rom": done_rooms, "ferdige_objekter": done_objects,
            "rom_totalt": rooms_total, "objekter_totalt": objects_total, "venter": incomplete,
            "ferdige_lagobjekter": done_pieces.get("lag", []), "lagobjekter_totalt": pieces_total["lag"],
            "ferdige_ikoner": done_pieces.get("ikon", []), "ikoner_totalt": pieces_total["ikon"],
            "ferdige_figurruter": done_pieces.get("figur", []), "figurruter_totalt": pieces_total["figur"]}


# ---------------------------------------------------------------- ordre til ChatGPT

def read_status(work: Path) -> list[dict]:
    """Leser status.csv. Eldre filer uten kolonnen type har bare romjobber."""
    path = work / "status.csv"
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["type"] = (r.get("type") or "").strip() or "rom"
    return rows


_OBJ_ID = re.compile(r"obj(\d+)_([0-9A-Za-z]+)")
_LAG_ID = re.compile(r"lag(\d+)_(\d+)(_del\d+av\d+)?")
_FIG_ID = re.compile(r"fig(\d+)_(\d+)(_del\d+av\d+)?")


def _image_of(row: dict) -> str:
    """Bildet en rad i status.csv hører til: roomNNN, objNNN_SS, lagNNN_KK, ikonNN eller figCCC_KK
    (jobb-ID uten delnummer)."""
    m = _OBJ_ID.match(row["jobb"]) if row["type"] == "objekt" else None
    if m:
        return m.group(0)
    m = _LAG_ID.match(row["jobb"]) if row["type"] == "lag" else None
    if m:
        return f"lag{m.group(1)}_{m.group(2)}"
    m = _FIG_ID.match(row["jobb"]) if row["type"] == "figur" else None
    if m:
        return f"fig{m.group(1)}_{m.group(2)}"
    return row["jobb"] if row["type"] in ("objekt", "ikon") else f"room{int(row['rom']):03d}"


def _job_info(work: Path | None, row: dict) -> dict:
    """Objektbildene og anbefalt bilde to for en lagjobb eller et ikonark, fra jobb.json.

    Uten jobb.json gir en lagjobb romjobben for samme del som bilde to.
    """
    path = work / "jobber" / row["jobb"] / "jobb.json" if work else None
    data = json.loads(path.read_text()) if path and path.exists() else {}
    if row["type"] == "lag" and not data.get("bilde_to"):
        m = _LAG_ID.match(row["jobb"])
        if m:
            data["bilde_to"] = f"jobber/rom{m.group(1)}{m.group(3) or ''}/resultat.png"
    return data


def _second_job(info: dict) -> str | None:
    """Jobben bilde to kommer fra (jobber/<jobb>/resultat.png)."""
    m = re.match(r"jobber/([^/]+)/", info.get("bilde_to") or "")
    return m.group(1) if m else None


def _piece_progress(work: Path | None, rows: list[dict], kind: str) -> tuple[int, int]:
    """Ferdige og alle objektbilder i lagjobbene (kind = lag) eller ikonarkene (kind = ikon), eller
    kostymeruter på figurarkene (kind = figur).

    Et objektbilde eller en rute er ferdig når alle jobbene det ligger i, er godkjent.
    """
    states: dict[str, list[str]] = {}
    for r in rows:
        if r["type"] == kind:
            for p in _job_info(work, r).get("ruter" if kind == "figur" else "objekter") or []:
                states.setdefault(p["bilde"], []).append(r["status"])
    return sum(all(s == "godkjent" for s in v) for v in states.values()), len(states)


def _is_pilot(work: Path | None, r: dict) -> bool:
    return r["type"] == "figur" and bool(_job_info(work, r).get("pilot"))


def work_queue(rows: list[dict], work: Path | None = None) -> list[dict]:
    """Alle jobber som ikke er godkjent, i den rekkefølgen ChatGPT skal ta dem.

    Avviste rom- og objektjobber først. Så figurarkene i piloten (avviste, så nye), så de andre
    avviste. Så nye etter romnummer, romjobbene før objektjobbene i samme rom; objektjobber i rom
    som allerede er ferdige, kommer først blant de nye, så rommet blir helt ferdig. Etter rom- og
    objektjobbene kommer lagjobbene etter romnummer: først de der bilde to (det godkjente HD-bildet)
    finnes, så resten. Så ikonarkene og figurarkene utenfor piloten. Helt til slutt de som er
    godtatt foreløpig, men kan bli bedre (sjekk).
    """
    room_rows = [r for r in rows if r["type"] == "rom"]
    rooms_done = {int(r["rom"]) for r in room_rows} - {int(r["rom"]) for r in room_rows if r["status"] != "godkjent"}
    status = {r["jobb"]: r["status"] for r in rows}

    def key(r: dict) -> tuple:
        if r["type"] == "lag":
            ready = status.get(_second_job(_job_info(work, r))) == "godkjent"
            return (2 if ready else 3, int(r["rom"]), 0)
        if r["type"] == "ikon":
            return (4, int(r["rom"]), 0)
        if r["type"] == "figur":
            return (5, 0, 0)                      # i rekkefølgen fra status.csv (sortert stabilt)
        return (0 if r["type"] == "objekt" and int(r["rom"]) in rooms_done else 1, int(r["rom"]), r["type"] != "rom")

    pilot = [r for r in rows if _is_pilot(work, r)]
    pilot = [r for r in pilot if r["status"] == "avvist"] + [r for r in pilot if r["status"] == "ny"]
    in_pilot = {r["jobb"] for r in pilot}
    retry_main = [r for r in rows if r["status"] == "avvist" and r["type"] in ("rom", "objekt")]
    retry_rest = [r for r in rows if r["status"] == "avvist" and r["type"] not in ("rom", "objekt")
                  and r["jobb"] not in in_pilot]
    fresh = sorted((r for r in rows if r["status"] == "ny" and r["jobb"] not in in_pilot), key=key)
    better = [r for r in rows if r["status"] == "sjekk"]
    return retry_main + pilot + retry_rest + fresh + better


def _piece_label(work: Path | None, r: dict) -> tuple[str, str | None]:
    """Hva en lagjobb, et ikonark eller et figurark er, og anbefalt bilde to."""
    info = _job_info(work, r)
    if r["type"] == "figur":
        m = _FIG_ID.match(r["jobb"])
        sheet = int(m.group(2)) if m else r["jobb"]
        n = len(info.get("ruter") or [])
        cid = f"kostyme {int(m.group(1))}" if m else "kostyme"
        who = cid if r["navn"].startswith("kostyme") else f"{r['navn']} ({cid})"
        what = f"figurark {sheet} for {who}, {n} {'rute' if n == 1 else 'ruter'}"
        if info.get("innhold"):
            what += f": {info['innhold']}"
        return what, info.get("bilde_to")
    n = len(info.get("objekter") or [])
    if r["type"] == "ikon":
        sheet = re.match(r"ikon(\d+)", r["jobb"])
        return (f"ikonark {int(sheet.group(1)) if sheet else r['jobb']}"
                + (f" med {n} {'ikon' if n == 1 else 'ikoner'}" if n else ""), info.get("bilde_to"))
    m = _LAG_ID.match(r["jobb"])
    what = f"lag {m.group(2)}" if m else "lag"
    return what + (f" med {n} {'objektbilde' if n == 1 else 'objektbilder'}" if n else ""), info.get("bilde_to")


def write_list(work: Path, batch: int = 10) -> Path:
    """Skriver GRAFIKKLISTE.md: alt ChatGPT skal lage, i rekkefølge og delt i bestillinger.

    Bestilling 1 er det samme som står i ORDRE.md. Når den er levert, tar ChatGPT neste
    bestilling uten å vente på ny ordre.
    """
    rows = read_status(work)
    queue = work_queue(rows, work)
    done = [r for r in rows if r["status"] == "godkjent"]
    room_rows = [r for r in rows if r["type"] == "rom"]
    obj_rows = [r for r in rows if r["type"] == "objekt"]
    lag_rows = [r for r in rows if r["type"] == "lag"]
    icon_rows = [r for r in rows if r["type"] == "ikon"]
    fig_rows = [r for r in rows if r["type"] == "figur"]
    rooms_all = {int(r["rom"]) for r in room_rows}
    rooms_done = rooms_all - {int(r["rom"]) for r in room_rows if r["status"] != "godkjent"}
    objects_all = {_image_of(r) for r in obj_rows}
    objects_done = objects_all - {_image_of(r) for r in obj_rows if r["status"] != "godkjent"}

    def label(r: dict) -> str:
        what = f"rom {r['rom']} {r['navn']}"
        second = None
        m = _OBJ_ID.match(r["jobb"]) if r["type"] == "objekt" else None
        if m:
            what += f", objekt {int(m.group(1))} tilstand {m.group(2)}"
        if r["type"] == "lag":
            piece, second = _piece_label(work, r)
            what += f", {piece}"
        elif r["type"] in ("ikon", "figur"):
            what, second = _piece_label(work, r)
        if r["del"] not in ("1/1", ""):
            what += f", del {r['del']}"
        if second:
            what += f", bilde to `{second}`"
        note = {"avvist": " (avvist, les retur.md)", "sjekk": " (kan bli bedre)"}.get(r["status"], "")
        if _is_pilot(work, r):
            note += " (pilot)"
        return f"`{r['jobb']}` ({what}){note}"

    if lag_rows or icon_rows:
        lag_done, lag_total = _piece_progress(work, rows, "lag")
        icon_done, icon_total = _piece_progress(work, rows, "ikon")
        small = [f"| Små objektbilder i lag (`lagNNN_KK`: dører, brytere, lys, ting) | {lag_done} | {lag_total} | "
                 f"Etter rommene og de store objektbildene ({len(lag_rows)} lagjobber) |",
                 f"| Ikoner i inventaret (`ikonNN`) | {icon_done} | {icon_total} | Til slutt ({len(icon_rows)} ikonark) |"]
    else:
        small = ["| Andre objektbilder | 0 | ikke telt | Senere, egen bestilling når rommene er ferdige |"]
    if fig_rows:
        fig_done, fig_total = _piece_progress(work, rows, "figur")
        pilot_rows = [r for r in fig_rows if _is_pilot(work, r)]
        sheets = {_image_of(r) for r in fig_rows}
        if len(pilot_rows) == len(fig_rows):
            figures = [f"| Figurer: pilot med figurark for {pilot_rows[0]['navn']} (`figCCC_KK`, kostymeruter) | "
                       f"{fig_done} | {fig_total} | Nå, etter de avviste rom- og objektjobbene ({len(sheets)} ark) |",
                       f"| Alle figurene | {fig_done} | ikke telt | Senere, når piloten er godkjent |"]
        else:
            figures = [f"| Figurer (`figCCC_KK`, kostymeruter; piloten først) | {fig_done} | {fig_total} | "
                       f"Piloten etter de avviste rom- og objektjobbene, resten til slutt ({len(sheets)} ark) |"]
    else:
        figures = ["| Figurer (modellark for Zak, Annie, Melissa og Leslie) | 0 | ikke telt | Senere, egen bestilling |"]

    lines = ["# Grafikkliste", "", time.strftime("Oppdatert %Y-%m-%d %H:%M (norsk tid)"), "",
             "Alt som skal lages til Zak McKracken HD Remake, i den rekkefølgen det skal lages. "
             "Bestilling 1 er det samme som står i `ORDRE.md`. Når en bestilling er levert, tar du neste "
             "uten å vente på ny ordre. Hopp over jobber som er krysset av.", "",
             "## Oversikt", "",
             "| Del | Ferdig | Totalt | Når |", "| --- | --- | --- | --- |",
             f"| Rombakgrunner | {len(rooms_done)} | {len(rooms_all)} | Nå, bestillingene under ({len(room_rows)} jobber, brede og høye rom er delt) |",
             f"| Store objektbilder (nærbilder og store objekter) | {len(objects_done)} | {len(objects_all)} | Nå, sammen med rommene |",
             *small,
             *figures, ""]
    if fig_rows:
        lines += ["Figurarkene i piloten står rett etter de avviste rom- og objektjobbene. De er en pilot: vi skal se "
                  "om ChatGPT kan male animasjonsruter som er like nok til at figuren ikke flimrer, før resten av "
                  "figurene bestilles.", ""]
    for i in range(0, len(queue), batch):
        part = queue[i:i + batch]
        n = i // batch + 1
        rooms = sorted({int(r["rom"]) for r in part if r["type"] != "figur"})
        who = list(dict.fromkeys(r["navn"] for r in part if r["type"] == "figur"))
        where = ([f"Rom {', '.join(map(str, rooms))}."] if rooms else []) + \
            ([f"Figurark for {', '.join(who)}."] if who else [])
        lines += [f"## Bestilling {n}" + (" (nå, samme som ORDRE.md)" if n == 1 else ""), "", " ".join(where), ""]
        lines += [f"- [ ] {label(r)}" for r in part]
        lines.append("")
    if not queue:
        lines += ["## Bestillinger", "", "Alle jobber er levert og godkjent.", ""]
    lines += ["## Ferdig", ""]
    lines += [f"- [x] `{r['jobb']}` (rom {r['rom']} {r['navn']})" for r in done] or ["Ingen ennå."]
    path = work / "GRAFIKKLISTE.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_orders(work: Path, batch: int = 10, anchors: list[str] | None = None,
                 messages: list[str] | None = None, tasks: Path | None = None) -> Path:
    """Skriver ORDRE.md: status, neste jobber og beskjeder. ChatGPT leser denne først."""
    rows = read_status(work)
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    room_rows = [r for r in rows if r["type"] == "rom"]
    obj_rows = [r for r in rows if r["type"] == "objekt"]
    # Et rom er ferdig når romjobbene er godkjent, uavhengig av objektene
    rooms_all = {int(r["rom"]) for r in room_rows}
    rooms_done = sorted(rooms_all - {int(r["rom"]) for r in room_rows if r["status"] != "godkjent"})
    objects_all = {_image_of(r) for r in obj_rows}
    objects_done = sorted(objects_all - {_image_of(r) for r in obj_rows if r["status"] != "godkjent"})
    lag_rows = [r for r in rows if r["type"] == "lag"]
    icon_rows = [r for r in rows if r["type"] == "ikon"]
    fig_rows = [r for r in rows if r["type"] == "figur"]
    status = {r["jobb"]: r["status"] for r in rows}

    queue = work_queue(rows, work)[:batch]

    lines = ["# Ordre fra Claude", "", time.strftime("Oppdatert %Y-%m-%d %H:%M (norsk tid)"), "",
             "Les denne filen før du starter. Den erstatter tidligere ordre.", "",
             "## Status", "",
             f"- Jobber: {len(rows)}. " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())),
             f"- {_done_line('rom', rooms_done, len(rooms_all))}"]
    if obj_rows:
        lines.append(f"- {_done_line('objekter', objects_done, len(objects_all))}")
    for kind, kind_rows, jobs_label, label in (("lag", lag_rows, "Lagjobber", "objektbilder fra lag"),
                                                ("ikon", icon_rows, "Ikonark", "ikoner fra ikonark"),
                                                ("figur", fig_rows, "Figurark", "figurruter")):
        if kind_rows:
            done, total = _piece_progress(work, rows, kind)
            ok = sum(r["status"] == "godkjent" for r in kind_rows)
            lines.append(f"- {jobs_label}: {ok} av {len(kind_rows)} godkjent. Ferdige {label}: {done} av {total}")
    lines += ["", "## Gjør disse nå", ""]
    if not queue:
        lines.append("Alle jobber er levert. Vent på ny bestilling.")
    for i, r in enumerate(queue, 1):
        why = ""
        if r["status"] == "avvist":
            why = f" Avvist: {r['kommentar']}. Les retur.md."
        elif r["status"] == "sjekk":
            why = f" Godtatt foreløpig, men kan bli bedre: {r['kommentar']}."
        if r["type"] == "figur":
            what, second = _piece_label(work, r)
            pilot = " Pilot for figurarkene, så vi ser om figurene kan lages slik." if _is_pilot(work, r) else ""
            if second:
                dep = _second_job({"bilde_to": second})
                why += (f" Legg ved `{second}` som bilde to (ikke stilankeret), så figuren blir lik på alle arkene.")
                if dep and status.get(dep) != "godkjent":
                    why += f" Lag denne etter at {dep} er godkjent."
            else:
                why += " Legg ved stilankeret som bilde to."
            lines.append(f"{i}. `{r['jobb']}` ({what}, del {r['del']}).{pilot}{why}")
            continue
        what = f"rom {r['rom']}, {r['navn']}"
        m = _OBJ_ID.match(r["jobb"]) if r["type"] == "objekt" else None
        if m:
            what += f", objekt {int(m.group(1))} tilstand {m.group(2)}"
            states = sorted({_OBJ_ID.match(o["jobb"]).group(2) for o in obj_rows
                             if _OBJ_ID.match(o["jobb"]) and _OBJ_ID.match(o["jobb"]).group(1) == m.group(1)})
            if m.group(2) != states[0]:
                first = f"obj{m.group(1)}_{states[0]}"
                why += (f" Legg ved `jobber/{first}/resultat.png` som bilde to (ikke stilankeret), så tilstandene "
                        f"blir like. Lag denne etter {first}.")
        if r["type"] in ("lag", "ikon"):
            piece, second = _piece_label(work, r)
            what = f"{what}, {piece}" if r["type"] == "lag" else piece
            if second:
                why += (f" Legg ved `{second}` som bilde to (ikke stilankeret), så objektene får samme stil og lys "
                        "som HD-bildet.")
                dep = _second_job({"bilde_to": second})
                if dep and status.get(dep) != "godkjent":
                    why += f" Lag denne etter at {dep} er godkjent."
        lines.append(f"{i}. `{r['jobb']}` ({what}, del {r['del']}).{why}")
    if queue:
        lines += ["", "Når disse er levert, fortsett med bestilling 2 i `GRAFIKKLISTE.md` uten å vente på ny ordre."]
    lines += ["", "## Stilankere", ""]
    if anchors:
        lines += [f"- `stil/{a}`" for a in anchors]
        lines += ["", "Legg ved det ankeret som ligner mest på rommet som bilde to."]
    else:
        lines.append("Ingen ennå.")
    lines += ["", "## Leveringsformat", "",
              "Begge formatene godtas av kontrollen:", "",
              "- `resultat.png` på 1536 x 1024 med samme grå kant som `referanse.png`.",
              "- `resultat.png` med bare bildet, i samme sideforhold som utsnittet (16:10 og minst 1280 x 800 "
              "for et rom på 320 x 200; sideforholdet står i `jobb.json`).", "",
              "Objektjobbene (`objNNN_SS`) er store bilder som spillet tegner over rommet (nærbilder, kart, "
              "paneler). De lages og leveres på samme måte. Utsnittet er da objektbildet, så leverer du bare "
              "bildet, skal det ha objektets sideforhold (se `bilde_i_lerret` i `jobb.json`).", ""]
    if lag_rows or icon_rows:
        lines += ["Lagjobbene (`lagNNN_KK`) er rommet med spillets små objekter tegnet på plass. Mal alt trofast. "
                  "Objektene klippes ut etter posisjonen, så de må ligge nøyaktig der de er. Bilde to er det "
                  "godkjente HD-bildet som står i ordren (`bilde_to` i `jobb.json`). Ikonarkene (`ikonNN`) er "
                  "ikonene i inventaret på mørkeblå bakgrunn. Begge leveres som rommene.", ""]
    if fig_rows:
        lines += ["Figurarkene (`figCCC_KK`) er animasjonsruter av samme figur på en flat bakgrunnsfarge. Mal alle "
                  "rutene som den samme personen (samme ansikt, klær, farger og lys), med nøyaktig samme omriss som "
                  "originalen, og hold bakgrunnen flat. Rutene klippes ut etter posisjonen. Arkene i piloten er en "
                  "prøve: lag dem i rekkefølge, ark 01 først. Leveres som rommene.", ""]
    lines += ["Skriv `notat.md` i jobbmappen. Commit 5 til 10 jobber om gangen i grenen `gpt-arbeid` og push.", ""]
    if messages:
        lines += ["## Beskjeder", ""] + [f"- {m}" for m in messages] + [""]
    if tasks and tasks.exists() and tasks.read_text(encoding="utf-8").strip():
        lines += ["## Kodeoppgaver", "", tasks.read_text(encoding="utf-8").strip(), ""]
    lines += ["## Neste sjekk", "", "Claude henter grenen omtrent hver halvtime, kontrollerer leveransene, "
              "oppdaterer `status.csv`, `RAPPORT.md` og `retur.md`, og skriver ny ordre her."]
    path = work / "ORDRE.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
