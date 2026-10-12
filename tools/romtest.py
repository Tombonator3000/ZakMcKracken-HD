#!/usr/bin/env python3
"""Romtest: kjører spillet uten skjerm i hvert rom og ser hva HD-motoren gjør der.

Zak (11. oktober): bare spill-ID og filnavn er byttet. Testen trenger DigHD (testhoppet og dumpene),
som ikke er slått på for Zak ennå, så den er ikke kjørt for Zak.

Med Sam & Max (10. oktober): kjørt i alle 85 rom med en nearest-mod. Rom som henger etter
hoppet (skriptfeil uten riktig spilltilstand), stoppes av --tidsgrense.

For hvert rom (og for brede og høye rom flere kameraplasser) hopper spillet til
rommet med DIGHD_TEST_ROOM, går et antall bilder og lagrer skjermbildet i HD og
med originalpikslene (DIGHD_DUMP_FLAT). Loggen sier om rommet og HD-bakgrunnen
ble lastet, og hvor pikslene i det siste bildet kom fra. Bildene sammenlignes
for å finne forskyvning, svarte felt og store avvik, og det lages kontaktark med
HD og originalen side om side.

Med --objekter kjøres hvert rom én gang til med DIGHD_TEST_OBJSTATE=alle: motoren
viser hver tilstand av hvert objekt i rommet etter hverandre og lagrer skjermen
etter hver tilstand. Rapporten sier for hvert objekt og hver tilstand om HD-bildet
ble brukt, hvor stor del av objektpikslene som var HD, og avviket fra originalen,
med nærbilder.

Resultat i work/romtest: RAPPORT.md, romtest.csv, ark_NN.png, en mappe per kjøring
med logg og bilder, og nærbilder av det som skiller seg mest ut i naerbilder/.
Med --objekter også objekter.csv og nærbilder av objektene (naerbilder/objNNN_SS_romRRR.png).
Notater fra gjennomsynet kan legges i FUNN.md i samme mappe; de tas med i rapporten.

Bruk: tools/romtest.sh [--rom 2,9,22 | --rom 20-30] [--mod gpt] [--kamera ett|alle] [--objekter] ...
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SCREEN_W, SCREEN_H, SCALE = 320, 200, 4

# Grenser for merknadene i rapporten
SHIFT_GAIN = 0.92        # forskyvning meldes når beste flytting gir under 92 prosent av feilen uten flytting
DIFF_LEVEL = 56          # avvik per originalpiksel (største kanal, 0 til 255) som regnes som stort
DIFF_MIN_AREA = 24       # minste sammenhengende område med stort avvik, i originalpiksler
BLACK_MIN_AREA = 16      # minste svarte felt (HD nesten svart, originalen ikke)
FIG_MIN_AREA = 30        # minste figur funnet mot originalbakgrunnen
CLOSEUPS_PER_KIND = 3    # nærbilder per kjøring og slag
SEAM_LEVEL = 32          # avvik mellom HD-objekt og HD-rom (største kanal) som gir en synlig søm
OBJ_START = 30           # bilder etter hoppet før objekttilstandene begynner (DIGHD_TEST_OBJSTATE_AT)


# ---------------------------------------------------------------- oppsett

@dataclass
class Run:
    room: int
    camx: int | None = None
    camy: int | None = None
    objekter: bool = False   # DIGHD_TEST_OBJSTATE=alle: alle tilstandene til alle objektene i rommet

    @property
    def name(self) -> str:
        s = f"rom{self.room:03d}"
        if self.camx is not None:
            s += f"_x{self.camx:04d}"
        if self.camy is not None:
            s += f"_y{self.camy:04d}"
        if self.objekter:
            s += "_objekter"
        return s

    @property
    def camera_wish(self) -> str:
        if self.camx is None and self.camy is None:
            return ""
        return f"{'' if self.camx is None else self.camx},{'' if self.camy is None else self.camy}"


@dataclass
class Result:
    run: Run
    name: str = ""
    status: str = "ok"
    notes: list[str] = field(default_factory=list)
    seconds: float = 0.0
    exit: str = ""
    jumped: bool = False
    entered: bool = False
    hd_loaded: str = ""          # ja, nei, ikke i modden
    in_mod: bool = False
    warnings: list[str] = field(default_factory=list)
    films: list[str] = field(default_factory=list)
    dump_frame: int | None = None
    dump_room: int | None = None
    camera: tuple[int, int] | None = None
    px: dict[str, int] = field(default_factory=dict)
    verify_bad: float | None = None
    verify_stale: int | None = None
    shift: tuple[float, float] = (0.0, 0.0)
    shift_gain: float = 1.0
    light: float | None = None   # snittlysstyrke i originalbildet (0 til 255)
    black_px: int = 0
    mean_diff: float | None = None
    regions: list[dict] = field(default_factory=list)
    figures: list[dict] = field(default_factory=list)
    closeups: list[str] = field(default_factory=list)
    dump: str = ""
    flat: str = ""
    log: str = ""
    tail: list[str] = field(default_factory=list)


def parse_rooms(spec: str | None, all_rooms: list[int]) -> list[int]:
    if not spec:
        return all_rooms
    out: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            out.update(range(int(a), int(b) + 1))
        else:
            out.add(int(part))
    return sorted(out)


def camera_runs(room: int, meta: dict, mode: str) -> list[Run]:
    """Kjøringene for et rom: én der spillet selv setter kameraet, og med
    `alle` i tillegg kameraplasser som dekker hele bredden og høyden."""
    runs = [Run(room)]
    if mode != "alle":
        return runs
    w, h = meta.get("width", SCREEN_W), meta.get("height", SCREEN_H)
    nx = math.ceil(w / SCREEN_W) if w > SCREEN_W else 0
    ny = math.ceil(h / SCREEN_H) if h > SCREEN_H else 0
    xs = [round(SCREEN_W / 2 + i * (w - SCREEN_W) / (nx - 1)) for i in range(nx)] if nx > 1 else [None]
    ys = [round(SCREEN_H / 2 + i * (h - SCREEN_H) / (ny - 1)) for i in range(ny)] if ny > 1 else [None]
    if nx <= 1 and ny <= 1:
        return runs
    for y in ys:
        for x in xs:
            runs.append(Run(room, x, y))
    return runs


# ---------------------------------------------------------------- kjøring

def run_engine(run: Run, args, out: Path, dense: bool = False) -> Result:
    """Én kjøring. Vanlig: to bilder, det siste etter args.bilder bilder i rommet.
    Tett (andre forsøk for rom spillet forlater fort): et bilde hvert 10. bilde."""
    res = Result(run=run, name=run.name)
    rundir = out / run.name
    if rundir.exists():
        shutil.rmtree(rundir)
    rundir.mkdir(parents=True)
    timeout = args.tidsgrense
    if run.objekter:
        # Motoren avslutter selv når alle tilstandene er vist; grensen er for sikkerhets skyld
        steps = object_steps(args.rooms_meta.get(str(run.room), {}))
        quit_at = args.hopp + OBJ_START + (steps + 4) * args.objekt_bilder + 300
        every = 0
        timeout = args.tidsgrense + 3 * steps
    elif dense:
        quit_at = args.hopp + min(args.bilder, 300)
        every = 10
    else:
        quit_at = args.hopp + args.bilder
        every = max(1, quit_at // 2)
    home = Path(tempfile.mkdtemp(prefix="romtest-"))
    env = {k: v for k, v in os.environ.items() if not k.startswith("DIGHD_")}
    env.update({
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "XDG_DATA_HOME": str(home / ".local/share"),
        "XDG_CACHE_HOME": str(home / ".cache"),
        "SDL_VIDEODRIVER": "dummy",
        "SDL_AUDIODRIVER": "dummy",
        "DIGHD_MOD": str(args.mod),
        "DIGHD_TEST_ROOM": str(run.room),
        "DIGHD_TEST_AT": str(args.hopp),
        "DIGHD_SKIP_VIDEO": "1",
        "DIGHD_QUIT_AT": str(quit_at),
        "DIGHD_DUMP_DIR": str(rundir),
        "DIGHD_DUMP_FLAT": "1",
        "DIGHD_VERIFY": "1",
    })
    if every:
        env["DIGHD_DUMP_EVERY"] = str(every)
    if run.objekter:
        # Skjermen lagres ved slutten av hver tilstand
        env["DIGHD_TEST_OBJSTATE"] = "alle"
        env["DIGHD_TEST_OBJSTATE_AT"] = str(OBJ_START)
        env["DIGHD_TEST_OBJSTATE_EVERY"] = str(args.objekt_bilder)
    if run.camx is not None:
        env["DIGHD_TEST_CAMX"] = str(run.camx)
    if run.camy is not None:
        env["DIGHD_TEST_CAMY"] = str(run.camy)
    cmd = [str(args.motor), f"--path={args.spill}", "--debuglevel=1", "--no-aspect-ratio", "zak"]
    log = rundir / "scummvm.log"
    t0 = time.monotonic()
    with open(log, "wb") as fh:
        try:
            p = subprocess.run(cmd, env=env, cwd=home, stdout=fh, stderr=subprocess.STDOUT,
                               timeout=timeout)
            code = p.returncode
        except subprocess.TimeoutExpired:
            code = None
    res.seconds = time.monotonic() - t0
    shutil.rmtree(home, ignore_errors=True)
    if code is None:
        res.exit = f"tidsgrense {timeout} s"
    elif code < 0:
        res.exit = f"signal {-code}"
    elif code > 0:
        res.exit = f"kode {code}"
    # DIGHD_VERIFY lagrer originalpikslene en gang til uten romnummer; de trengs ikke
    for f in rundir.glob("frame_[0-9][0-9][0-9][0-9][0-9][0-9]_flat.png"):
        f.unlink()
    (rundir / "kjoring.json").write_text(json.dumps({
        "rom": run.room, "kamera": run.camera_wish, "sekunder": round(res.seconds, 1), "slutt": res.exit,
        "mod": str(args.mod), "motor": str(args.motor), "bilder": quit_at - args.hopp, "hopp": args.hopp,
        "tett": dense, "objekter": run.objekter,
        "bilder_per_tilstand": args.objekt_bilder if run.objekter else None,
    }, indent=1))
    return res


def prune_dumps(res: Result, out: Path) -> None:
    """Etter en tett kjøring: bare bildet som brukes og det siste beholdes."""
    rundir = out / res.run.name
    keep = {Path(res.dump).name, Path(res.flat).name} if res.dump else set()
    frames = sorted({int(p.name[6:12]) for p in rundir.glob("frame_*.png")})
    if frames:
        keep |= {p.name for p in rundir.glob(f"frame_{frames[-1]:06d}_*.png")}
    for p in rundir.glob("frame_*.png"):
        if p.name not in keep:
            p.unlink()


# ---------------------------------------------------------------- loggen

RE_JUMP = re.compile(r"DigHD: test, jumping to room (\d+)")
RE_NOJUMP = re.compile(r"DigHD: test, room (\d+) is (\d+)x(\d+), smaller than the screen: no jump")
RE_LOADED = re.compile(r"DigHD: room (\d+) loaded \((\d+)x(\d+)\)")
RE_NOHD = re.compile(r"DigHD: no HD background for room (\d+)")
RE_DUMP = re.compile(r"DigHD: dumped frame (\d+) \(room (\d+), smush (\d)\) (.*)")
RE_WHOLE = re.compile(
    r"DigHD: whole screen frame (\d+) \(room (\d+), screen at (-?\d+),(-?\d+)\): HD room px (\d+), "
    r"HD object px (\d+), HD sprite px (\d+), original px (\d+) \(background without HD (\d+), "
    r"figure without HD (\d+)\), HD text px (\d+), cycled HD px (\d+)")
RE_STALE = re.compile(r"DigHD: verify frame (\d+): (\d+) screen pixels differ from the whole screen")
RE_BAD = re.compile(r"DigHD: verify frame (\d+): (\d+) of (\d+) HD pixels differ strongly from the original")
RE_FILM = re.compile(r"DigHD: film (\S+)")
RE_WARN = re.compile(r"WARNING: (DigHD: .*)")
RE_STAT = re.compile(r"(HD room|HD object|HD sprite|original) px (\d+)")


def parse_log(res: Result, args, out: Path, mod_rooms: set[int]) -> None:
    run = res.run
    rundir = out / run.name
    log = rundir / "scummvm.log"
    res.log = str(log.relative_to(out))
    text = log.read_text(errors="replace") if log.exists() else ""
    lines = text.splitlines()
    res.tail = [ln for ln in lines if ln.strip()][-6:]
    res.in_mod = run.room in mod_rooms
    jumped_at = None
    dumps: dict[int, dict] = {}
    stale: dict[int, int] = {}
    bad: dict[int, float] = {}
    hd_state = ""  # siste melding om HD-bakgrunnen for rommet (ja eller nei)
    for i, ln in enumerate(lines):
        # Hopper spillet til rommet det allerede står i, lastes rommet ikke på nytt,
        # så meldingen om HD-bakgrunnen kan stå før hoppet
        if m := RE_LOADED.search(ln):
            if int(m.group(1)) == run.room:
                hd_state = "ja"
                res.entered |= jumped_at is not None
            continue
        if m := RE_NOHD.search(ln):
            if int(m.group(1)) == run.room:
                hd_state = "nei"
                res.entered |= jumped_at is not None
            continue
        if m := RE_JUMP.search(ln):
            if int(m.group(1)) == run.room:
                res.jumped = True
                jumped_at = i
            continue
        if m := RE_NOJUMP.search(ln):
            res.notes.append(f"motoren hopper ikke til et rom som er mindre enn skjermen ({m.group(2)}x{m.group(3)})")
            continue
        if jumped_at is None:
            continue  # resten før hoppet gjelder startrommet
        if m := RE_FILM.search(ln):
            res.films.append(m.group(1))
        elif m := RE_WARN.search(ln):
            if m.group(1) not in res.warnings:
                res.warnings.append(m.group(1))
        elif m := RE_STALE.search(ln):
            stale[int(m.group(1))] = int(m.group(2))
        elif m := RE_BAD.search(ln):
            total = int(m.group(3))
            bad[int(m.group(1))] = 100.0 * int(m.group(2)) / total if total else 0.0
        elif m := RE_DUMP.search(ln):
            f = int(m.group(1))
            d = dumps.setdefault(f, {})
            d.update(frame=f, room=int(m.group(2)), smush=int(m.group(3)))
            d["sum"] = {k: int(v) for k, v in RE_STAT.findall(m.group(4))}
        elif m := RE_WHOLE.search(ln):
            f = int(m.group(1))
            d = dumps.setdefault(f, {"frame": f, "room": int(m.group(2)), "smush": 0})
            # Kameraet er midten av skjermen; loggen gir hjørnet øverst til venstre
            d["camera"] = (int(m.group(3)) + SCREEN_W // 2, int(m.group(4)) + SCREEN_H // 2)
            keys = ["room", "object", "sprite", "original", "bg_missing", "fig_missing", "text", "cycled"]
            d["px"] = dict(zip(keys, (int(m.group(k)) for k in range(5, 13))))
    res.hd_loaded = "ikke i modden" if not res.in_mod else hd_state

    # Siste bilde i rommet som ikke er tonet ned (minst 60 prosent av det lyseste
    # bildet i rommet), ellers siste bilde etter hoppet
    inroom = [dumps[f] for f in sorted(dumps) if dumps[f].get("room") == run.room and not dumps[f].get("smush")]
    light = {}
    for d in inroom:
        p = rundir / f"frame_{d['frame']:06d}_room{run.room:03d}_flat.png"
        light[d["frame"]] = float(np.asarray(Image.open(p).convert("L").reduce(8)).mean()) if p.exists() else 0.0
    chosen = None
    if inroom:
        top = max(light.values())
        chosen = [d for d in inroom if light[d["frame"]] >= 0.6 * top][-1]
        res.light = light[chosen["frame"]]
    if chosen is not None and res.jumped:
        res.entered = True
    last = dumps[max(dumps)] if dumps else None
    if chosen is None and last is not None:
        chosen = last
    if chosen is not None:
        res.dump_frame = chosen["frame"]
        res.dump_room = chosen.get("room")
        res.camera = chosen.get("camera")
        if "px" in chosen:
            res.px = chosen["px"]
        elif "sum" in chosen:
            # Eldre motor uten linjen for hele skjermen: tallene er summert siden forrige bilde
            s = chosen["sum"]
            res.px = {"room": s.get("HD room", 0), "object": s.get("HD object", 0),
                      "sprite": s.get("HD sprite", 0), "original": s.get("original", 0)}
            res.notes.append("andelene er summert siden forrige bilde (motoren mangler linjen for hele skjermen)")
        res.verify_stale = stale.get(chosen["frame"])
        res.verify_bad = bad.get(chosen["frame"])
        if chosen.get("smush"):
            name = next((p for p in sorted(rundir.glob(f"frame_{chosen['frame']:06d}_*.png"))
                         if not p.stem.endswith("_flat")), None)
        else:
            name = rundir / f"frame_{chosen['frame']:06d}_room{chosen['room']:03d}.png"
        if name and name.exists():
            res.dump = str(name.relative_to(out))
            flat = name.with_name(name.stem + "_flat.png")
            if flat.exists():
                res.flat = str(flat.relative_to(out))
    if last is not None and last is not chosen and last.get("room") != run.room:
        res.notes.append(f"senere i rom {last.get('room')}")


# ---------------------------------------------------------------- bildene

def load_rgb(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.int16)


def box_down(img: np.ndarray, n: int) -> np.ndarray:
    h, w, c = img.shape
    return img.reshape(h // n, n, w // n, n, c).mean(axis=(1, 3))


def estimate_shift(hd: np.ndarray, flat: np.ndarray) -> tuple[float, float, float]:
    """Flytting av HD-bildet mot originalen i originalpiksler (halve piksler),
    og forholdet mellom feilen med og uten flytting."""
    g_hd = box_down(hd, 2).mean(axis=2)
    g_fl = flat[::2, ::2].mean(axis=2).astype(np.float32)
    h, w = g_hd.shape
    m = 8
    base = g_hd[m:h - m, m:w - m]
    errs = {}
    for dy in range(-4, 5):
        for dx in range(-4, 5):
            f = g_fl[m - dy:h - m - dy, m - dx:w - m - dx]
            errs[(dx, dy)] = float(np.abs(base - f).mean())
    best = min(errs, key=errs.get)
    e0 = errs[(0, 0)]
    gain = errs[best] / e0 if e0 > 0 else 1.0
    return best[0] / 2, best[1] / 2, gain


def mean3(a: np.ndarray) -> np.ndarray:
    """Snitt over 3 x 3 piksler (kantene gjentas)."""
    p = np.pad(a.astype(np.float32), 1, mode="edge")
    h, w = a.shape
    return sum(p[dy:dy + h, dx:dx + w] for dy in range(3) for dx in range(3)) / 9


def components(mask: np.ndarray, weight: np.ndarray, min_area: int, limit: int) -> list[dict]:
    """Sammenhengende områder (8 naboer) i masken, sterkeste først (sum av vekten)."""
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    found = []
    for y0, x0 in zip(*np.nonzero(mask)):
        if seen[y0, x0]:
            continue
        seen[y0, x0] = True
        stack = [(y0, x0)]
        pts = []
        while stack:
            y, x = stack.pop()
            pts.append((y, x))
            for ny in (y - 1, y, y + 1):
                if ny < 0 or ny >= h:
                    continue
                for nx in (x - 1, x, x + 1):
                    if 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
        if len(pts) < min_area:
            continue
        ys = np.array([p[0] for p in pts])
        xs = np.array([p[1] for p in pts])
        score = float(weight[ys, xs].sum())
        found.append({"x0": int(xs.min()), "y0": int(ys.min()), "x1": int(xs.max()) + 1, "y1": int(ys.max()) + 1,
                      "areal": len(pts), "styrke": round(score / len(pts), 1), "_sum": score})
    found.sort(key=lambda c: -c["_sum"])
    for c in found:
        del c["_sum"]
    return found[:limit]


def room_background(extract: Path, room: int, camera: tuple[int, int] | None,
                    meta: dict) -> tuple[np.ndarray, np.ndarray, int, int] | None:
    """Originalbakgrunnen (palett 0) for utsnittet kameraet viser, i originalpiksler,
    og hvilke piksler som har en farge som sykles."""
    p = extract / "rooms" / f"room{room:03d}.png"
    pi = extract / "rooms" / f"room{room:03d}_idx.png"
    if not p.exists():
        return None
    img = np.asarray(Image.open(p).convert("RGB"), dtype=np.int16)
    h, w = img.shape[:2]
    cx, cy = camera if camera else (SCREEN_W // 2, SCREEN_H // 2)
    left = min(max(cx - SCREEN_W // 2, 0), max(w - SCREEN_W, 0))
    top = min(max(cy - SCREEN_H // 2, 0), max(h - SCREEN_H, 0))
    crop = img[top:top + SCREEN_H, left:left + SCREEN_W]
    if crop.shape[:2] != (SCREEN_H, SCREEN_W):
        return None
    cycled = np.zeros((SCREEN_H, SCREEN_W), dtype=bool)
    if pi.exists() and meta.get("cycles"):
        idx = np.asarray(Image.open(pi))[top:top + SCREEN_H, left:left + SCREEN_W]
        if idx.shape == cycled.shape:
            for c in meta["cycles"]:
                cycled |= (idx >= c[0]) & (idx <= c[1])
    return crop, cycled, left, top


def grow(a: int, b: int, size: int, limit: int) -> tuple[int, int]:
    """Utvider [a, b) til minst size, innenfor [0, limit)."""
    if b - a < size:
        c = (a + b) // 2
        a, b = c - size // 2, c - size // 2 + size
    if a < 0:
        a, b = 0, b - a
    if b > limit:
        a, b = max(0, a - (b - limit)), limit
    return a, b


def closeup(hd_img: Image.Image, flat_img: Image.Image, box: dict, title: str, margin: int = 12) -> Image.Image:
    x0, x1 = grow(box["x0"] - margin, box["x1"] + margin, 64, SCREEN_W)
    y0, y1 = grow(box["y0"] - margin, box["y1"] + margin, 40, SCREEN_H)
    crop = (x0 * SCALE, y0 * SCALE, x1 * SCALE, y1 * SCALE)
    a, b = hd_img.crop(crop), flat_img.crop(crop)
    w, h = a.size
    f = 1.0
    if 2 * w < 900:
        f = min(3.0, 900 / (2 * w))
    if 2 * w * f > 1600:
        f = 1600 / (2 * w)
    if f != 1.0:
        size = (max(1, round(w * f)), max(1, round(h * f)))
        a = a.resize(size, Image.NEAREST if f > 1 else Image.LANCZOS)
        b = b.resize(size, Image.NEAREST if f > 1 else Image.LANCZOS)
    font = font_of(18)
    pad, bar = 8, 30
    text = f"{title}   originalpiksler x {x0}-{x1}, y {y0}-{y1}   venstre HD, høyre original"
    # Smale bilder (høye objekter) får teksten på to linjer
    lines = [text]
    width = a.width * 2 + pad * 3
    if hasattr(font, "getlength") and font.getlength(text) > width - 2 * pad:
        lines = [title, f"originalpiksler x {x0}-{x1}, y {y0}-{y1}   venstre HD, høyre original"]
        bar = 54
        width = max(width, int(max(font.getlength(ln) for ln in lines)) + 2 * pad)
    sheet = Image.new("RGB", (width, a.height + bar + pad), (40, 40, 40))
    d = ImageDraw.Draw(sheet)
    for i, ln in enumerate(lines):
        d.text((pad, 6 + 24 * i), ln, fill=(255, 255, 255), font=font)
    sheet.paste(a, (pad, bar))
    sheet.paste(b, (pad * 2 + a.width, bar))
    return sheet


_FONTS: dict[int, ImageFont.ImageFont] = {}


FONT_FILES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
]


def font_of(size: int):
    """En font med æ, ø og å; standardfonten i Pillow mangler dem."""
    if size not in _FONTS:
        for f in FONT_FILES:
            if Path(f).exists():
                _FONTS[size] = ImageFont.truetype(f, size)
                break
        else:
            try:
                _FONTS[size] = ImageFont.load_default(size=size)
            except TypeError:
                _FONTS[size] = ImageFont.load_default()
    return _FONTS[size]


def analyse(res: Result, out: Path, args, meta: dict) -> None:
    if not res.dump or not res.flat:
        return
    hd = load_rgb(out / res.dump)
    flat = load_rgb(out / res.flat)
    if hd.shape != (SCREEN_H * SCALE, SCREEN_W * SCALE, 3) or hd.shape != flat.shape:
        res.notes.append(f"uventet bildestørrelse {hd.shape[1]}x{hd.shape[0]}")
        return
    dx, dy, gain = estimate_shift(hd, flat)
    res.shift_gain = gain
    if (dx, dy) != (0, 0) and gain < SHIFT_GAIN:
        res.shift = (dx, dy)

    hd1 = box_down(hd, SCALE)
    fl1 = flat[::SCALE, ::SCALE].astype(np.float32)
    diff = np.abs(hd1 - fl1).max(axis=2)
    res.mean_diff = round(float(diff.mean()), 1)
    smooth = mean3(diff)
    res.regions = components(smooth > DIFF_LEVEL, smooth, DIFF_MIN_AREA, CLOSEUPS_PER_KIND)

    luma = lambda a: a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114
    black = (luma(hd1) < 10) & (luma(fl1) > 40)
    res.black_px = int(black.sum())
    blacks = components(black, np.ones_like(diff), BLACK_MIN_AREA, CLOSEUPS_PER_KIND)

    # Figurer og ting som står foran bakgrunnen: originalpikslene som ikke er
    # originalbakgrunnen og ikke ligger i et objekt. Bare når paletten er den samme.
    bgc = room_background(args.uttrekk, res.run.room, res.camera, meta) if res.dump_room == res.run.room else None
    if bgc is not None:
        bg, cycled, left, top = bgc
        fg = (np.abs(fl1 - bg).max(axis=2) > 24) & ~cycled
        for o in meta.get("objects", []):
            x0, y0 = o["x"] - left, o["y"] - top
            fg[max(0, y0):max(0, y0 + o["h"]), max(0, x0):max(0, x0 + o["w"])] = False
        if fg.mean() < 0.25:
            res.figures = components(fg, np.ones_like(diff), FIG_MIN_AREA, CLOSEUPS_PER_KIND)

    # Nærbilder
    want = []
    if res.shift != (0.0, 0.0):
        want.append(("forskyvning", {"x0": 100, "y0": 60, "x1": 220, "y1": 140}))
    want += [("svart", b) for b in blacks]
    want += [("avvik", r) for r in res.regions]
    if meta.get("zplane") and res.run.camx is None and res.run.camy is None:
        want += [("figur", f) for f in res.figures]
    if not want:
        return
    hd_img = Image.open(out / res.dump).convert("RGB")
    flat_img = Image.open(out / res.flat).convert("RGB")
    nd = out / "naerbilder"
    nd.mkdir(exist_ok=True)
    count: dict[str, int] = {}
    for kind, box in want:
        count[kind] = count.get(kind, 0) + 1
        name = f"{res.name}_{kind}{count[kind]}.png"
        title = f"Rom {res.run.room} ({meta.get('name', '')}) {kind} {count[kind]}"
        closeup(hd_img, flat_img, box, title).save(nd / name)
        res.closeups.append(f"naerbilder/{name}")


# ---------------------------------------------------------------- sømmer

def load_idx(path: Path) -> tuple[np.ndarray, int | None]:
    """Indeksbilde og gjennomsiktig indeks (første med alfa 0 i tRNS), som i motoren."""
    im = Image.open(path)
    t = im.info.get("transparency")
    if isinstance(t, (bytes, bytearray, list)):
        t = next((i for i, v in enumerate(t) if v == 0), None)
    return np.asarray(im), t


def object_seams(mod: Path, extract: Path, rooms: list[int], rooms_meta: dict, jobs: list[dict], out: Path,
                 limit: int) -> list[dict]:
    """Sømmer mellom HD-objekter og HD-rommet.

    Motoren viser HD-rommet der objektet har samme indeks som rombakgrunnen, og
    HD-objektet bare der objektet skiller seg fra den. Er objektbildet og rombildet
    laget hver for seg, møtes de to bildene langs grensen mellom disse feltene inne
    i objektet. Der originalen går jevnt over grensen (nabopikslene har nesten samme
    farge), skal HD-bildet også gjøre det; ellers synes en søm. Her telles slike
    grensepiksler der HD-objektet og HD-rommet skiller seg mye (snitt per
    originalpiksel, største kanal, over SEAM_LEVEL) på romsiden av grensen.
    """
    gpt_objects = {j["id"] for j in jobs if j.get("type") == "objekt"}

    def seam(room: int, o: dict, name: str, images: bool):
        rp = mod / "rooms" / f"room{room:03d}.png"
        rip = mod / "rooms" / f"room{room:03d}_idx.png"
        op, oip = mod / "objects" / f"{name}.png", mod / "objects" / f"{name}_idx.png"
        if not (rp.exists() and rip.exists() and op.exists() and oip.exists()):
            return None
        room_idx, _ = load_idx(rip)
        oidx, tr = load_idx(oip)
        h, w = oidx.shape
        x, y = o["x"], o["y"]
        if x < 0 or y < 0 or y + h > room_idx.shape[0] or x + w > room_idx.shape[1]:
            return None
        opaque = oidx != tr if tr is not None else np.ones_like(oidx, dtype=bool)
        same = (oidx == room_idx[y:y + h, x:x + w]) & opaque
        diff = opaque & ~same
        if diff.sum() < 20 or same.sum() < 20:
            return None
        # Originalfargene (objektets palett er rommets)
        with Image.open(oip) as im:
            orig = np.asarray(im.convert("RGB"), dtype=np.int16)
        # Grensepiksler på romsiden der originalen går jevnt over til objektsiden
        edge = np.zeros_like(same)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            ys = slice(max(0, -dy), h - max(0, dy))
            xs = slice(max(0, -dx), w - max(0, dx))
            yq = slice(max(0, dy), h - max(0, -dy))
            xq = slice(max(0, dx), w - max(0, -dx))
            smooth = np.abs(orig[ys, xs] - orig[yq, xq]).max(axis=2) < 24
            edge[ys, xs] |= same[ys, xs] & diff[yq, xq] & smooth
        if edge.sum() < 10:
            return None
        obj_hd = np.asarray(Image.open(op).convert("RGB"), dtype=np.int16)
        if obj_hd.shape[:2] != (h * SCALE, w * SCALE):
            return None
        with Image.open(rp) as im:
            part = np.asarray(im.convert("RGB").crop((x * SCALE, y * SCALE, (x + w) * SCALE, (y + h) * SCALE)),
                              dtype=np.int16)
        d = np.abs(box_down(obj_hd, SCALE) - box_down(part, SCALE)).max(axis=2)
        strong = edge & (d > SEAM_LEVEL)
        info = {"objekt": name, "rom": room, "kilde": "ChatGPT" if name in gpt_objects else "automatisk",
                "grense_px": int(edge.sum()), "som_px": int(strong.sum()),
                "avvik": round(float(d[edge].mean()), 1), "x": x, "y": y, "w": w, "h": h}
        if strong.any():
            ys, xs = np.nonzero(strong)
            info["omrade"] = [int(xs.min()) + x, int(ys.min()) + y, int(xs.max()) + 1 + x, int(ys.max()) + 1 + y]
        return (info, same, part, obj_hd) if images else info

    found = []
    for room in rooms:
        for o in rooms_meta.get(str(room), {}).get("objects", []):
            for st in o.get("states", []):
                info = seam(room, o, f"obj{o['id']:03d}_{st}", False)
                if info and info["som_px"] > 0:
                    info["_o"] = o
                    found.append(info)
    found.sort(key=lambda f: (-f["som_px"], -f["avvik"]))
    nd = out / "naerbilder"
    nd.mkdir(exist_ok=True)
    for f in found[:limit]:
        info, same, part, obj_hd = seam(f["rom"], f["_o"], f["objekt"], True)
        # Slik motoren setter det sammen: HD-rommet der objektet er lik rommet, ellers HD-objektet
        mask = np.repeat(np.repeat(same, SCALE, axis=0), SCALE, axis=1)[..., None]
        a = Image.fromarray(np.where(mask, part, obj_hd).astype(np.uint8))
        orig = extract / "rooms" / f"room{f['rom']:03d}.png"
        if orig.exists():
            base = Image.open(orig).convert("RGB").crop((f["x"], f["y"], f["x"] + f["w"], f["y"] + f["h"]))
            ob = extract / "objects" / f"{f['objekt']}.png"
            if ob.exists():
                oi = Image.open(ob).convert("RGBA")
                base.paste(oi, (0, 0), oi)
            b = base.resize(a.size, Image.NEAREST)
        else:
            b = Image.new("RGB", a.size, (60, 60, 60))
        sheet_w = a.width * 2 + 24
        scale = min(1.0, 1600 / sheet_w)
        if scale < 1.0:
            a = a.resize((round(a.width * scale), round(a.height * scale)), Image.LANCZOS)
            b = b.resize(a.size, Image.LANCZOS)
        img = Image.new("RGB", (a.width * 2 + 24, a.height + 38), (40, 40, 40))
        d = ImageDraw.Draw(img)
        d.text((8, 6), f"Rom {f['rom']} {f['objekt']} ({f['kilde']}): HD slik motoren viser det, og originalen. "
               f"{f['som_px']} sømpiksler", fill=(255, 255, 255), font=font_of(18))
        img.paste(a, (8, 34))
        img.paste(b, (16 + a.width, 34))
        name = f"som_{f['objekt']}_rom{f['rom']:03d}.png"
        img.save(nd / name)
        f["naerbilde"] = f"naerbilder/{name}"
    for f in found:
        f.pop("_o", None)
    return found


# ---------------------------------------------------------------- objekttilstander

def object_steps(meta: dict) -> int:
    """Antall tilstander motoren viser med DIGHD_TEST_OBJSTATE=alle (fra rooms.json)."""
    return sum(len(o.get("states", [])) for o in meta.get("objects", []))


RE_OBJROOM = re.compile(r"DigHD: test, object states in room (\d+): (\d+) objects with images, (\d+) states")
RE_OBJLEFT = re.compile(r"DigHD: test, object (\d+) state (\d+) (has no image|is not a room image)")
RE_OBJSET = re.compile(r"DigHD: test, object (\d+) state (\d+) at frame (\d+)(?: \((?:step (\d+) of (\d+)|parent of object (\d+))\))?"
                       r", at (-?\d+),(-?\d+) (\d+)x(\d+), (\d+) images")
RE_OBJLOG = re.compile(
    r"DigHD: test object (\d+) state (\d+) frame (\d+): drawn (yes|no|with state \d+), HD image ([a-z ]+), "
    r"object px (\d+), HD object px (\d+), at (-?\d+),(-?\d+) (\d+)x(\d+), on screen (\d+) px: HD room px (\d+), "
    r"other HD object px (\d+), HD sprite px (\d+), original px (\d+) \(without HD (\d+)\)")
RE_OBJCHANGED = re.compile(r"DigHD: test, the game set object (\d+) to state (\d+) at frame (\d+); set back to (\d+)")
RE_OBJSTOP = re.compile(r"DigHD: test, object states stopped at frame (\d+): the game left room (\d+) for room (\d+)")
RE_OBJDONE = re.compile(r"DigHD: test, object states done at frame (\d+)")
RE_OBJCAM = re.compile(r"DigHD: test, camera to (-?\d+),(-?\d+) for object (\d+)")


@dataclass
class ObjRun:
    run: Run
    status: str = "ok"
    notes: list[str] = field(default_factory=list)
    seconds: float = 0.0
    exit: str = ""
    expected: int = 0            # tilstander i rooms.json
    shown: int | None = None     # tilstander motoren fant
    rows: list[dict] = field(default_factory=list)


def object_states(run: Run, args, out: Path, meta: dict, jobs: list[dict]) -> ObjRun:
    """Leser loggen fra en kjøring med DIGHD_TEST_OBJSTATE=alle og ser på hver tilstand:
    om objektet ble tegnet, om HD-bildet ble brukt, andelen HD-objektpiksler (fra motoren)
    og avviket mot originalen i objektpikslene (fra bildene), med nærbilder."""
    res = ObjRun(run=run, expected=object_steps(meta))
    rundir = out / run.name
    info = rundir / "kjoring.json"
    k = json.loads(info.read_text()) if info.exists() else {}
    res.seconds = k.get("sekunder", 0.0)
    res.exit = k.get("slutt", "")
    log = rundir / "scummvm.log"
    lines = log.read_text(errors="replace").splitlines() if log.exists() else []
    gpt = {j["id"] for j in jobs if j.get("type") == "objekt"}
    stale: dict[int, int] = {}
    screen: dict[int, tuple[int, int]] = {}
    steps: dict[tuple[int, int], dict] = {}   # (objekt, tilstand) -> bildet tilstanden ble satt
    parents: dict[int, list[int]] = {}        # objekt -> foreldre som ble satt sammen med det
    changed: dict[int, list[str]] = {}
    camera: dict[int, str] = {}               # objekt -> kameraet testkroken satte
    logged: list[dict] = []
    done = False
    current = None  # tilstanden som vises nå (ikke en forelder som ble satt sammen med den)
    left_out: dict[tuple[int, int], str] = {}  # tilstander motoren ikke kan tegne som en del av rommet
    for ln in lines:
        if m := RE_OBJROOM.search(ln):
            res.shown = int(m.group(3))
        elif m := RE_OBJLEFT.search(ln):
            why = "uten bilde" if m.group(3) == "has no image" else "BOMP, tegnes av skriptene som blast-objekt"
            left_out[(int(m.group(1)), int(m.group(2)))] = why
        elif m := RE_OBJSET.search(ln):
            o, st, f = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if m.group(6):
                parents.setdefault(int(m.group(6)), []).append(o)
            else:
                steps[(o, st)] = {"frame": f, "images": int(m.group(11))}
                current = (o, st)
        elif m := RE_OBJLOG.search(ln):
            g = m.groups()
            if (int(g[0]), int(g[1])) != current:
                continue
            logged.append({
                "objekt": int(g[0]), "tilstand": int(g[1]), "bilde": int(g[2]), "tegnet": g[3], "hd_bilde": g[4],
                "objekt_px": int(g[5]), "hd_objekt_px": int(g[6]), "x": int(g[7]), "y": int(g[8]), "w": int(g[9]),
                "h": int(g[10]), "paa_skjermen": int(g[11]), "hd_rom_px": int(g[12]), "annet_objekt_px": int(g[13]),
                "figur_px": int(g[14]), "original_px": int(g[15]), "uten_hd_px": int(g[16])})
        elif m := RE_OBJCHANGED.search(ln):
            changed.setdefault(int(m.group(1)), []).append(f"spillet satte tilstand {m.group(2)} ved bilde {m.group(3)}")
        elif m := RE_OBJSTOP.search(ln):
            res.notes.append(f"spillet forlot rommet for rom {m.group(3)} ved bilde {m.group(1)}")
        elif m := RE_NOJUMP.search(ln):
            res.notes.append(f"motoren hopper ikke til et rom som er mindre enn skjermen ({m.group(2)}x{m.group(3)})")
        elif RE_OBJDONE.search(ln):
            done = True
        elif m := RE_OBJCAM.search(ln):
            camera[int(m.group(3))] = f"{m.group(1)},{m.group(2)}"
        elif m := RE_STALE.search(ln):
            stale[int(m.group(1))] = int(m.group(2))
        elif m := RE_WHOLE.search(ln):
            screen[int(m.group(1))] = (int(m.group(3)), int(m.group(4)))

    if res.exit:
        res.status = "hang" if res.exit.startswith("tidsgrense") else "krasj"
        res.notes.insert(0, f"avsluttet: {res.exit}")
    elif res.shown is None:
        res.status = "ikke startet"
    elif not done:
        res.status = "ikke ferdig"
    if res.shown is not None and res.shown + len(left_out) != res.expected:
        res.notes.append(f"motoren fant {res.shown + len(left_out)} tilstander, rooms.json har {res.expected}")
    for (o, st), why in sorted(left_out.items()):
        res.rows.append({"objekt": o, "tilstand": st, "navn": f"obj{o:03d}_{st:02X}", "rom": run.room,
                         "status": "utelatt", "merknad": [why]})

    nd = out / "naerbilder"
    nd.mkdir(exist_ok=True)
    room = run.room
    # Der objektet er likt rombakgrunnen, viser motoren HD-rommet, men bare når modden har det
    ridx_path = args.uttrekk / "rooms" / f"room{room:03d}_idx.png"
    hd_room = (args.mod / "rooms" / f"room{room:03d}.png").exists()
    room_idx = load_idx(ridx_path)[0] if ridx_path.exists() and hd_room else None
    for e in logged:
        o, st, f = e["objekt"], e["tilstand"], e["bilde"]
        name = f"obj{o:03d}_{st:02X}"
        e.update(navn=name, rom=room, kilde="ChatGPT" if name in gpt else "automatisk",
                 i_modden=(args.mod / "objects" / f"{name}.png").exists(), ulik_hel_skjerm_px=stale.get(f),
                 snittavvik=None, sterkt_avvik_pst=None, maske_px=0, naerbilde="", merknad=[])
        if parents.get(o):
            e["merknad"].append("forelder satt: " + ", ".join(f"obj{p:03d}" for p in parents[o]))
        e["merknad"] += changed.get(o, [])
        if e["ulik_hel_skjerm_px"]:
            e["merknad"].append(f"{e['ulik_hel_skjerm_px']} px ulik hele skjermen bygget på nytt")
        # Status for objektet i denne tilstanden. Motoren tegner ikke objekter utenfor skjermen
        if e["paa_skjermen"] == 0:
            e["status"] = "ikke på skjermen"
            if o in camera and f in screen:
                e["merknad"].append(f"kameraet ble satt til {camera[o]}, men skjermen viste rommet fra "
                                    f"{screen[f][0]},{screen[f][1]} (skriptet flytter kameraet)")
        elif e["tegnet"] != "yes":
            e["status"] = "ikke tegnet" if e["tegnet"] == "no" else f"tegnet i tilstand {e['tegnet'].split()[-1]}"
        elif e["hd_bilde"] == "no":
            e["status"] = "ikke i modden"
        elif e["hd_bilde"] != "yes":
            e["status"] = "HD-bildet ikke lest"
        elif e["objekt_px"] == 0:
            e["status"] = "likt rommet"   # alle synlige piksler er som rombakgrunnen; der vises HD-rommet
        elif e["hd_objekt_px"] == 0:
            e["status"] = "HD ikke brukt"
        else:
            e["status"] = "HD brukt"
        e["hd_andel_pst"] = round(100 * e["hd_objekt_px"] / e["objekt_px"], 1) if e["objekt_px"] else None

        # Avviket mellom HD og originalen i objektpikslene: der objektet ikke er
        # gjennomsiktig og skiller seg fra rombakgrunnen (uttrekket)
        dump = rundir / f"frame_{f:06d}_room{room:03d}.png"
        flat = rundir / f"frame_{f:06d}_room{room:03d}_flat.png"
        oidx_path = args.uttrekk / "objects" / f"{name}_idx.png"
        if not (dump.exists() and flat.exists()) or f not in screen:
            e["merknad"].append("mangler bildet fra motoren")
            res.rows.append(e)
            continue
        left, top = screen[f]
        x0, y0 = e["x"] - left, e["y"] - top
        cx0, cy0 = max(0, x0), max(0, y0)
        cx1, cy1 = min(SCREEN_W, x0 + e["w"]), min(SCREEN_H, y0 + e["h"])
        if cx1 <= cx0 or cy1 <= cy0:
            res.rows.append(e)
            continue
        hd1 = box_down(load_rgb(dump), SCALE)[cy0:cy1, cx0:cx1]
        fl1 = load_rgb(flat)[::SCALE, ::SCALE][cy0:cy1, cx0:cx1].astype(np.float32)
        diff = np.abs(hd1 - fl1).max(axis=2)
        if oidx_path.exists():
            oidx, tr = load_idx(oidx_path)
            part = oidx[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0]
            mask = part != tr if tr is not None else np.ones(part.shape, dtype=bool)
            if room_idx is not None:
                rpart = room_idx[cy0 + top:cy1 + top, cx0 + left:cx1 + left]
                if rpart.shape == part.shape:
                    mask &= part != rpart
            if mask.shape == diff.shape and mask.any():
                e["maske_px"] = int(mask.sum())
                e["snittavvik"] = round(float(diff[mask].mean()), 1)
                e["sterkt_avvik_pst"] = round(100 * float((diff[mask] > DIFF_LEVEL).mean()), 1)
        else:
            e["merknad"].append("objektet mangler i uttrekket")
        if e["hd_bilde"] != "yes" and e["tegnet"] == "yes" and e["maske_px"]:
            # Uten HD-bilde teller ikke motoren objektpikslene; uttrekket gir dem
            e["hd_andel_pst"] = 0.0
        if e["status"] == "likt rommet" and e["maske_px"]:
            # Objektet har egne piksler, men ingen av dem synes: noe annet ligger over
            e["status"] = "dekket"
            what = [f"et annet objekt ({e['annet_objekt_px']} px)" if e["annet_objekt_px"] else "",
                    f"en figur ({e['figur_px']} px)" if e["figur_px"] else ""]
            e["merknad"].append("dekket av " + (" og ".join(w for w in what if w) or "noe annet") +
                                "; prøv med en liste der det som dekker har tilstand 0")
            e["snittavvik"] = e["sterkt_avvik_pst"] = None
        box = {"x0": cx0, "y0": cy0, "x1": cx1, "y1": cy1}
        title = f"Rom {room} {name} ({e['kilde']}): {e['status']}"
        if e["hd_andel_pst"] is not None:
            title += f", HD {e['hd_andel_pst']:.0f} %"
        img = closeup(Image.open(dump).convert("RGB"), Image.open(flat).convert("RGB"), box, title, margin=8)
        fn = f"{name}_rom{room:03d}.png"
        img.save(nd / fn)
        e["naerbilde"] = f"naerbilder/{fn}"
        res.rows.append(e)
    seen = {(e["objekt"], e["tilstand"]) for e in res.rows}
    for (o, st), d in sorted(steps.items()):
        if (o, st) not in seen:
            res.rows.append({"objekt": o, "tilstand": st, "navn": f"obj{o:03d}_{st:02X}", "rom": room,
                             "status": "ingen måling", "bilde": d["frame"], "merknad": ["kjøringen sluttet før målingen"]})
    res.rows.sort(key=lambda e: (e["objekt"], e["tilstand"]))
    return res


def write_objects_csv(objruns: list[ObjRun], out: Path) -> None:
    cols = ["rom", "objekt", "tilstand", "navn", "kilde", "i_modden", "status", "tegnet", "hd_bilde", "objekt_px",
            "hd_objekt_px", "hd_andel_pst", "maske_px", "snittavvik", "sterkt_avvik_pst", "paa_skjermen", "hd_rom_px",
            "annet_objekt_px", "figur_px", "original_px", "uten_hd_px", "ulik_hel_skjerm_px", "x", "y", "w", "h",
            "bilde", "merknad", "naerbilde"]
    with open(out / "objekter.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in objruns:
            for e in r.rows:
                w.writerow(["; ".join(e.get(c) or []) if c == "merknad" else
                            ("" if e.get(c) is None else e.get(c)) for c in cols])


def objects_report(objruns: list[ObjRun], rooms_meta: dict, args) -> list[str]:
    rows = [e for r in objruns for e in r.rows]
    L = ["## Objekttilstander", ""]
    L.append(f"Hvert rom kjørt én gang til med `DIGHD_TEST_OBJSTATE=alle`: motoren setter hvert objekt i hver "
             f"tilstand slik skriptene gjør det (putState og ny tegning), viser den i {args.objekt_bilder} bilder og "
             "lagrer skjermen. Objektet settes tilbake til tilstanden det hadde før neste objekt, og kameraet "
             "flyttes til objekter som ikke er på skjermen. Objekt (px): objektets egne synlige piksler, det vil si "
             "ikke gjennomsiktige, ulik rombakgrunnen og ikke dekket av noe annet (talt i motoren; uten HD-bilde "
             "talt i uttrekket, uten det som dekker). HD-andel: andelen av dem som kom fra HD-objektet. Snitt og "
             "sterkt avvik: HD skalert ned mot originalen i objektpikslene fra uttrekket, største kanal, sterkt over "
             f"{DIFF_LEVEL}. Likt rommet: objektet er likt rombakgrunnen overalt, og motoren viser HD-rommet der. "
             "Dekket: objektet har egne piksler, men et annet objekt eller en figur ligger over alle; test det "
             "med en liste der det som dekker har tilstand 0, for eksempel `DIGHD_TEST_OBJSTATE=769:0,775:5`. "
             "Nærbildene viser HD til venstre og originalen til høyre.")
    L.append("")
    count = lambda s: sum(1 for e in rows if e.get("status") == s)
    L.append(f"- {len(rows)} tilstander av {len({(e['rom'], e['objekt']) for e in rows})} objekter i {len(objruns)} rom")
    L.append(f"- HD brukt: {count('HD brukt')}. Likt rommet (HD-rommet vises): {count('likt rommet')}. "
             f"Dekket av noe annet: {count('dekket')}. Ikke i modden: {count('ikke i modden')}")
    other = sorted({e.get("status", "") for e in rows} - {"HD brukt", "likt rommet", "dekket", "ikke i modden"})
    if other:
        L.append("- Annet: " + ", ".join(f"{s} {count(s)}" for s in other))
    stale = [e for e in rows if e.get("ulik_hel_skjerm_px")]
    L.append(f"- Skjermen ulik hele skjermen bygget på nytt (`DIGHD_VERIFY`): {len(stale)} tilstander")
    for r in objruns:
        if r.status != "ok" or r.notes:
            L.append(f"- {r.run.name}: {r.status}. {'; '.join(r.notes)}")
    L.append("")
    L.append("| Rom | Objekt | Kilde | Status | HD-andel | Objekt (px) | Snitt | Sterkt avvik | Merknad | Nærbilde |")
    L.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for e in rows:
        meta = rooms_meta.get(str(e["rom"]), {})
        num = lambda k, fmt="{}": "" if e.get(k) is None else fmt.format(e[k])
        px = e.get("objekt_px") or e.get("maske_px")  # uten HD-bilde: talt i uttrekket
        L.append(f"| {e['rom']} {meta.get('name', '')} | {e['navn']} | {e.get('kilde', '')} | {e.get('status', '')} | "
                 f"{num('hd_andel_pst', '{:.1f} %')} | {'' if px is None else px} | {num('snittavvik')} | "
                 f"{num('sterkt_avvik_pst', '{:.1f} %')} | {'; '.join(e.get('merknad') or [])} | "
                 f"{e.get('naerbilde', '')} |")
    L.append("")
    return L


# ---------------------------------------------------------------- vurdering

def judge(res: Result, meta: dict) -> None:
    run = res.run
    if res.exit:
        res.status = "hang" if res.exit.startswith("tidsgrense") else "krasj"
        res.notes.insert(0, f"avsluttet: {res.exit}")
    elif not res.jumped:
        res.status = "ikke testet" if any("mindre enn skjermen" in n for n in res.notes) else "hoppet ikke"
    elif not res.entered:
        res.status = "ikke lastet"
    elif res.dump_room != run.room:
        res.status = "byttet rom"
        if res.dump_room is not None:
            res.notes.append(f"siste bilde i rom {res.dump_room}")
    elif res.light is not None and res.light < 2:
        res.status = "svart skjerm"
    elif res.in_mod and res.hd_loaded != "ja":
        res.status = "HD-bakgrunn mangler"
    elif res.in_mod and res.px and res.px.get("room", 0) == 0:
        res.status = "HD-bakgrunn ikke brukt"
    elif not res.in_mod:
        res.status = "uten HD"
    else:
        res.status = "ok"
    if not res.dump and res.status in ("ok", "uten HD", "HD-bakgrunn ikke brukt"):
        res.status = "ingen bilder"
    w, h = meta.get("width", SCREEN_W), meta.get("height", SCREEN_H)
    if (w < SCREEN_W or h < SCREEN_H) and not any("mindre enn skjermen" in n for n in res.notes):
        res.notes.append(f"rommet er {w}x{h}, mindre enn skjermen")
    for w in res.warnings:
        res.notes.append(w.replace("DigHD: ", ""))
    if res.films:
        res.notes.append("film: " + ", ".join(dict.fromkeys(res.films)))
    total = sum(res.px.get(k, 0) for k in ("room", "object", "sprite", "original")) or 0
    if total and res.in_mod and res.status == "ok":
        if res.px.get("bg_missing", 0) > 0.01 * total:
            res.notes.append(f"bakgrunn uten HD {100 * res.px['bg_missing'] / total:.1f} %")
        if res.px.get("room", 0) < 0.3 * total:
            res.notes.append(f"lite HD-bakgrunn ({100 * res.px['room'] / total:.0f} %)")
    if res.verify_stale:
        res.notes.append(f"{res.verify_stale} px ulik hele skjermen bygget på nytt")
    if res.shift != (0.0, 0.0):
        res.notes.append(f"forskjøvet {res.shift[0]:+.1f}, {res.shift[1]:+.1f} px")
    if res.black_px >= BLACK_MIN_AREA:
        res.notes.append(f"svart i HD der originalen ikke er det: {res.black_px} px")
    if res.camera and (run.camx is not None or run.camy is not None):
        cx, cy = res.camera
        if (run.camx is not None and abs(cx - run.camx) > 8) or (run.camy is not None and abs(cy - run.camy) > 8):
            res.notes.append(f"kameraet sto på {cx},{cy}")


def pct(res: Result, key: str) -> str:
    total = sum(res.px.get(k, 0) for k in ("room", "object", "sprite", "original"))
    if not total or key not in res.px:
        return ""
    return f"{100 * res.px[key] / total:.1f}"


# ---------------------------------------------------------------- utdata

def write_csv(results: list[Result], out: Path, rooms_meta: dict) -> None:
    cols = ["rom", "navn", "kamera_valgt", "status", "hd_bakgrunn_lastet", "slutt", "sekunder", "bilde", "bilde_rom",
            "kamera", "hd_bakgrunn_pst", "hd_objekt_pst", "hd_figur_pst", "original_pst", "bakgrunn_uten_hd_pst",
            "figur_uten_hd_pst", "tekst_pst", "sterkt_avvik_pst", "ulik_hel_skjerm_px", "snittavvik",
            "forskyvning_x", "forskyvning_y", "svart_px", "store_avvik", "merknad", "dump", "original", "logg",
            "naerbilder"]
    with open(out / "romtest.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in results:
            w.writerow([
                r.run.room, rooms_meta.get(str(r.run.room), {}).get("name", ""), r.run.camera_wish, r.status,
                r.hd_loaded, r.exit, round(r.seconds, 1), r.dump_frame or "", "" if r.dump_room is None else r.dump_room,
                f"{r.camera[0]},{r.camera[1]}" if r.camera else "",
                pct(r, "room"), pct(r, "object"), pct(r, "sprite"), pct(r, "original"), pct(r, "bg_missing"),
                pct(r, "fig_missing"), pct(r, "text"),
                "" if r.verify_bad is None else f"{r.verify_bad:.2f}",
                "" if r.verify_stale is None else r.verify_stale,
                "" if r.mean_diff is None else r.mean_diff, r.shift[0], r.shift[1], r.black_px, len(r.regions),
                "; ".join(r.notes), r.dump, r.flat, r.log, " ".join(r.closeups),
            ])


def write_sheets(results: list[Result], out: Path, rooms_meta: dict, per_sheet: int) -> list[str]:
    for old in out.glob("ark_*.png"):
        old.unlink()
    tw, th = 640, 400
    pad, bar = 10, 34
    font = font_of(20)
    small = font_of(16)
    names = []
    rows = [results[i:i + per_sheet] for i in range(0, len(results), per_sheet)]
    for n, chunk in enumerate(rows, 1):
        sheet = Image.new("RGB", (tw * 2 + pad * 3, len(chunk) * (th + bar + pad) + pad), (30, 30, 30))
        d = ImageDraw.Draw(sheet)
        for i, r in enumerate(chunk):
            y = pad + i * (th + bar + pad)
            meta = rooms_meta.get(str(r.run.room), {})
            cam = f"  kamera {r.camera[0]},{r.camera[1]}" if r.camera else ""
            colour = (120, 230, 120) if r.status in ("ok", "uten HD") else (255, 120, 100)
            d.text((pad, y + 2), f"Rom {r.run.room} {meta.get('name', '')}{cam}", fill=(255, 255, 255), font=font)
            shares = (f"bakgrunn {pct(r, 'room') or '-'} %  objekt {pct(r, 'object') or '-'} %  "
                      f"original {pct(r, 'original') or '-'} %   {r.status}")
            d.text((pad + 470, y + 6), shares, fill=colour, font=small)
            for k, rel in enumerate((r.dump, r.flat)):
                x = pad + k * (tw + pad)
                if rel:
                    im = Image.open(out / rel).convert("RGB").resize((tw, th), Image.LANCZOS)
                    sheet.paste(im, (x, y + bar))
                else:
                    d.rectangle((x, y + bar, x + tw, y + bar + th), fill=(60, 60, 60))
                    d.text((x + 20, y + bar + 20), "ingen bilder", fill=(255, 255, 255), font=font)
            d.text((pad + 4, y + bar + th - 22), "HD", fill=(255, 255, 0), font=small)
            d.text((pad * 2 + tw + 4, y + bar + th - 22), "original", fill=(255, 255, 0), font=small)
        name = f"ark_{n:02d}.png"
        sheet.save(out / name)
        names.append(name)
    return names


def jobs_for(res: Result, box: dict, jobs: list[dict]) -> list[str]:
    """Jobbene som dekker et område på skjermen (romjobber og store objekter)."""
    if not res.camera:
        cx, cy = SCREEN_W // 2, SCREEN_H // 2
    else:
        cx, cy = res.camera
    left, top = max(cx - SCREEN_W // 2, 0), max(cy - SCREEN_H // 2, 0)
    mx, my = (box["x0"] + box["x1"]) / 2 + left, (box["y0"] + box["y1"]) / 2 + top
    out = []
    for j in jobs:
        if j.get("rom") != res.run.room:
            continue
        if j.get("type") == "rom":
            x, y, w, h = j["region"]
        elif j.get("type") == "objekt" and j.get("objekt_i_rom"):
            x, y, w, h = j["objekt_i_rom"]
        else:
            continue
        if x <= mx < x + w and y <= my < y + h:
            out.append(j["id"])
    return out


def write_report(results: list[Result], out: Path, args, rooms_meta: dict, sheets: list[str],
                 jobs: list[dict], started: str, seams: list[dict], objruns: list[ObjRun]) -> None:
    by_room: dict[int, list[Result]] = {}
    for r in results:
        by_room.setdefault(r.run.room, []).append(r)
    rank = {"krasj": 0, "hang": 1, "hoppet ikke": 2, "ikke lastet": 3, "ingen bilder": 4,
            "HD-bakgrunn mangler": 5, "HD-bakgrunn ikke brukt": 6, "byttet rom": 7, "svart skjerm": 8,
            "ikke testet": 9, "uten HD": 10, "ok": 11}
    room_status = {k: min((r.status for r in v), key=lambda s: rank.get(s, 99)) for k, v in by_room.items()}
    count = lambda s: sum(1 for v in room_status.values() if v == s)
    entered = sum(1 for v in by_room.values() if any(r.entered for r in v))

    L = []
    L.append("# Romtest")
    L.append("")
    L.append(f"Kjørt {started} med `tools/romtest.sh`. Mod: `{args.mod}`. Motor: `{args.motor}`. "
             f"Rapporten laget {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}.")
    L.append(f"{len(by_room)} rom og {len(results)} kjøringer. Hopp til rommet ved bilde {args.hopp}, "
             f"siste bilde {args.hopp + args.bilder}, tidsgrense {args.tidsgrense} s per kjøring. "
             f"Kamera: {args.kamera}." + (f" Objekttilstander: {len(objruns)} kjøringer, se Objekttilstander."
                                          if objruns else ""))
    L.append("")
    L.append("Hoppet setter ikke spillet i vanlig tilstand. Figurer og objekter kan mangle eller stå et annet sted "
             "enn i vanlig spill. Andelene gjelder hele skjermen i det siste bildet i rommet "
             "(originalpiksler, 64 000 i alt).")
    L.append("")
    L.append("## Sammendrag")
    L.append("")
    L.append(f"- Rommet lastet: {entered} av {len(by_room)}")
    L.append(f"- Krasj: {count('krasj')}, hang: {count('hang')}, hoppet ikke: {count('hoppet ikke')}, "
             f"ikke lastet: {count('ikke lastet')}, ikke testet (mindre enn skjermen): {count('ikke testet')}")
    L.append(f"- Ok med HD-bakgrunn: {count('ok')}. Uten HD i modden: {count('uten HD')}")
    L.append(f"- HD-bakgrunn mangler eller ikke brukt: {count('HD-bakgrunn mangler') + count('HD-bakgrunn ikke brukt')}")
    L.append(f"- Byttet rom før første bilde: {count('byttet rom')}. Svart skjerm i rommet: {count('svart skjerm')}")
    stale = [r for r in results if r.verify_stale]
    L.append(f"- Skjermen ulik hele skjermen bygget på nytt (`DIGHD_VERIFY`): {len(stale)} kjøringer")
    shifted = [r for r in results if r.shift != (0.0, 0.0)]
    L.append(f"- Forskjøvet HD-bilde: {len(shifted)} kjøringer")
    blacks = [r for r in results if r.black_px >= BLACK_MIN_AREA]
    L.append(f"- Svarte felt i HD: {len(blacks)} kjøringer")
    L.append("")
    nohd = [k for k, s in room_status.items() if s != "ok"]
    if nohd:
        L.append("Rom uten HD-bakgrunn i bildet, og hvorfor:")
        L.append("")
        for k in sorted(nohd):
            rs = by_room[k]
            why = "; ".join(dict.fromkeys(n for r in rs for n in r.notes))
            if not rs[0].in_mod:
                why = "ikke i modden" + (f"; {why}" if why else "")
            why = why[:1].upper() + why[1:]
            L.append(f"- Rom {k} ({rooms_meta.get(str(k), {}).get('name', '')}): {room_status[k]}. {why}")
        L.append("")
    funn = out / "FUNN.md"
    if funn.exists():
        L.append(funn.read_text().rstrip())
        L.append("")
    L.append("## Alle kjøringer")
    L.append("")
    L.append("Kolonnene: HD-bakgrunn, HD-objekt og original i prosent av skjermen. Avvik: andelen HD-piksler som "
             "skiller seg sterkt fra originalen (`DIGHD_VERIFY`, over 48 i en kanal). Snitt: snittavvik per "
             "originalpiksel (HD skalert ned mot originalen, største kanal).")
    L.append("")
    L.append("| Rom | Navn | Kamera | Status | Bakgrunn | Objekt | Original | Avvik | Snitt | Merknad | Bilde |")
    L.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in results:
        meta = rooms_meta.get(str(r.run.room), {})
        cam = f"{r.camera[0]},{r.camera[1]}" if r.camera else ""
        if r.run.camera_wish:
            cam += " (satt)"
        bad = "" if r.verify_bad is None else f"{r.verify_bad:.1f} %"
        dump = f"[HD]({r.dump}) [orig]({r.flat})" if r.dump else ""
        L.append(f"| {r.run.room} | {meta.get('name', '')} | {cam} | {r.status} | {pct(r, 'room')} | "
                 f"{pct(r, 'object')} | {pct(r, 'original')} | {bad} | {r.mean_diff if r.mean_diff is not None else ''} | "
                 f"{'; '.join(r.notes)} | {dump} |")
    L.append("")
    trouble = [r for r in results if r.status in ("krasj", "hang", "hoppet ikke", "ikke lastet", "ingen bilder")]
    if trouble:
        L.append("## Siste linjer i loggen for kjøringer som feilet")
        L.append("")
        for r in trouble:
            L.append(f"{r.name} ({r.status}, `{r.log}`):")
            L.append("")
            L.append("```")
            L.extend(r.tail)
            L.append("```")
            L.append("")
    L.append("## Største avvik mellom HD og originalen")
    L.append("")
    L.append(f"Områder der HD skalert ned skiller seg mer enn {DIFF_LEVEL} fra originalen (største kanal, snitt over "
             f"3 x 3 piksler), minst {DIFF_MIN_AREA} originalpiksler, de {CLOSEUPS_PER_KIND} sterkeste per kjøring. "
             "De fleste er detaljer ChatGPT har lagt til. Nærbildene ligger i `naerbilder/`.")
    L.append("")
    L.append("| Kjøring | Område (x, y) | Areal | Styrke | Jobb | Nærbilde |")
    L.append("| --- | --- | --- | --- | --- | --- |")
    allreg = [(r, k, b) for r in results for k, b in enumerate(r.regions, 1)]
    allreg.sort(key=lambda t: -t[2]["styrke"] * t[2]["areal"])
    for r, k, b in allreg[:args.topp]:
        jb = ", ".join(jobs_for(r, b, jobs)) or f"rom{r.run.room:03d}"
        L.append(f"| {r.name} | {b['x0']}-{b['x1']}, {b['y0']}-{b['y1']} | {b['areal']} | {b['styrke']} | {jb} | "
                 f"naerbilder/{r.name}_avvik{k}.png |")
    L.append("")
    L.append("## Sømmer mellom HD-objekter og HD-rommet")
    L.append("")
    L.append("Motoren viser HD-rommet der et objekt har samme indeks som rombakgrunnen, og HD-objektet bare der "
             "objektet skiller seg fra den. Er objektbildet laget for seg (ChatGPT-objekt eller automatisk "
             "oppskalering), møtes de to bildene langs grensen mellom feltene inne i objektet. Avvik: snittavviket "
             "(største kanal, 0 til 255) mellom HD-objektet og HD-rommet i grensepikslene på romsiden. Målt fra "
             "bildene i modden, uten motoren. Nærbildene viser objektet slik motoren setter det sammen, og originalen.")
    L.append("")
    L.append("| Objekt | Rom | Kilde | Grense (px) | Avvik | Nærbilde |")
    L.append("| --- | --- | --- | --- | --- | --- |")
    for f in seams[:args.topp]:
        L.append(f"| {f['objekt']} | {f['rom']} {rooms_meta.get(str(f['rom']), {}).get('name', '')} | {f['kilde']} | "
                 f"{f['grense_px']} | {f['avvik']} | {f.get('naerbilde', '')} |")
    L.append("")
    if objruns:
        L += objects_report(objruns, rooms_meta, args)
    L.append("## Kontaktark")
    L.append("")
    L.append("HD-bildet til venstre og originalpikslene til høyre, med romnummer, kamera og andelene over.")
    L.append("")
    for s in sheets:
        L.append(f"- `{s}`")
    L.append("")
    (out / "RAPPORT.md").write_text("\n".join(L) + "\n")


# ---------------------------------------------------------------- hoveddelen

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--rom", help="rom å teste, for eksempel 2,9,22 eller 20-30 (standard: alle)")
    ap.add_argument("--mod", default="gpt", help="navn i mods/ eller sti til en mod-mappe (standard gpt)")
    ap.add_argument("--kamera", choices=["ett", "alle"], default="alle",
                    help="alle: i tillegg kameraplasser over hele bredden og høyden av store rom (standard)")
    ap.add_argument("--ut", default=str(ROOT / "work" / "romtest"), help="mappe for resultatet")
    ap.add_argument("--motor", help="ScummVM med HD-patchen (standard $SCUMMVM_SRC/scummvm eller engine/scummvm/scummvm)")
    ap.add_argument("--spill", default=str(ROOT / "game"), help="spillfilene")
    ap.add_argument("--uttrekk", default=str(ROOT / "work" / "extract"), help="uttrekket (rooms.json og rombildene)")
    ap.add_argument("--jobber", default=str(ROOT / "work" / "gpt" / "jobber"),
                    help="jobbene til ChatGPT, for jobbnavn i rapporten (valgfritt)")
    ap.add_argument("--hopp", type=int, default=240, help="bildet der spillet hopper til rommet (standard 240)")
    ap.add_argument("--bilder", type=int, default=600, help="bilder etter hoppet (standard 600)")
    ap.add_argument("--tidsgrense", type=int, default=180, help="sekunder per kjøring før den regnes som hengt")
    ap.add_argument("--parallelt", type=int, default=os.cpu_count() or 2, help="kjøringer samtidig")
    ap.add_argument("--per-ark", type=int, default=4, help="kjøringer per kontaktark")
    ap.add_argument("--topp", type=int, default=40, help="antall avvik og sømmer i tabellene i rapporten")
    ap.add_argument("--somer", type=int, default=12, help="antall nærbilder av sømmer mellom HD-objekt og HD-rom")
    ap.add_argument("--objekter", action="store_true",
                    help="kjør hvert rom med objekter én gang til og vis alle tilstandene til alle objektene "
                         "(DIGHD_TEST_OBJSTATE=alle), med en dump og et nærbilde per tilstand")
    ap.add_argument("--objekt-bilder", type=int, default=40,
                    help="bilder hver objekttilstand vises før skjermen lagres (standard 40, omtrent 0,4 sekunder)")
    ap.add_argument("--bare-rapport", action="store_true", help="ingen nye kjøringer, bare rapport og ark fra mappene som finnes")
    args = ap.parse_args()

    mod = Path(args.mod)
    if not mod.is_dir():
        mod = ROOT / "mods" / args.mod
    args.mod = mod.resolve()
    if args.motor:
        args.motor = Path(args.motor)
    else:
        src = Path(os.environ.get("SCUMMVM_SRC", ROOT / "engine" / "scummvm"))
        args.motor = src / "scummvm"
    # Motoren kjører i en egen mappe, så stiene må være absolutte
    args.motor = args.motor.resolve()
    args.spill = Path(args.spill).resolve()
    args.uttrekk = Path(args.uttrekk).resolve()
    out = Path(args.ut).resolve()

    rooms_json = args.uttrekk / "rooms.json"
    if not rooms_json.exists():
        print(f"Fant ikke {rooms_json}. Kjør zakhd extract først.")
        return 1
    rooms_meta = json.loads(rooms_json.read_text())["rooms"]
    args.rooms_meta = rooms_meta
    all_rooms = sorted(int(k) for k in rooms_meta)
    rooms = parse_rooms(args.rom, all_rooms)
    mod_json = args.mod / "mod.json"
    mod_rooms = set(json.loads(mod_json.read_text()).get("rooms", [])) if mod_json.exists() else {
        int(p.name[4:7]) for p in (args.mod / "rooms").glob("room[0-9][0-9][0-9].png")}

    jobs = []
    jd = Path(args.jobber)
    if jd.is_dir():
        for p in sorted(jd.glob("*/jobb.json")):
            try:
                jobs.append(json.loads(p.read_text()))
            except (OSError, ValueError):
                pass

    runs = [r for room in rooms for r in camera_runs(room, rooms_meta.get(str(room), {}), args.kamera)]
    # Med --objekter: én kjøring til per rom med objekttilstander
    obj_runs = [Run(room, objekter=True) for room in rooms
                if args.objekter and object_steps(rooms_meta.get(str(room), {}))]
    out.mkdir(parents=True, exist_ok=True)
    started = dt.datetime.now().strftime("%Y-%m-%d %H:%M")

    if not args.bare_rapport:
        if not args.motor.exists():
            print(f"Fant ikke motoren {args.motor}. Kjør engine/build.sh, eller sett SCUMMVM_SRC eller --motor.")
            return 1
        if not (args.spill / "00.LFL").exists():
            print(f"Fant ikke spillfilene i {args.spill}. Kjør tools/hent_spilldata.sh.")
            return 1
        if not args.mod.is_dir():
            print(f"Fant ikke modden {args.mod}.")
            return 1
        extra = f" og {len(obj_runs)} med objekttilstander" if obj_runs else ""
        print(f"{len(runs)} kjøringer{extra} i {len(rooms)} rom, {args.parallelt} om gangen, mod {args.mod}")
        lock = threading.Lock()
        done = 0

        def one(run: Run, dense: bool = False, total: int = len(runs) + len(obj_runs)) -> None:
            nonlocal done
            r = run_engine(run, args, out, dense)
            with lock:
                done += 1
                print(f"  [{done}/{total}] {run.name}: {r.exit or 'ferdig'} ({r.seconds:.0f} s)", flush=True)

        # Kjøringene med objekttilstander tar lengst tid og starter først
        with ThreadPoolExecutor(max_workers=max(1, args.parallelt)) as ex:
            list(ex.map(one, obj_runs + runs))

        # Andre forsøk for rom spillet forlot før det første bildet: et bilde hvert 10. bilde
        retry = []
        for run in runs:
            r = Result(run=run, name=run.name)
            parse_log(r, args, out, mod_rooms)
            info = json.loads((out / run.name / "kjoring.json").read_text())
            if r.jumped and not info.get("slutt") and r.dump_room != run.room:
                retry.append(run)
        if retry:
            print(f"{len(retry)} kjøringer på nytt med et bilde hvert 10. bilde (spillet forlot rommet før første bilde)")
            done = 0
            with ThreadPoolExecutor(max_workers=max(1, args.parallelt)) as ex:
                list(ex.map(lambda r: one(r, True, len(retry)), retry))

    results = []
    # Nærbildene skriptet laget sist; egne nærbilder med andre navn blir liggende
    pats = ["rom*_avvik*.png", "rom*_figur*.png", "rom*_svart*.png", "rom*_forskyvning*.png", "som_*.png"]
    if obj_runs:
        pats.append("obj*_rom*.png")
    for pat in pats:
        for p in (out / "naerbilder").glob(pat):
            p.unlink()
    # Tid og motor for kjøringene (også når rapporten lages på nytt med --bare-rapport)
    logs = [out / r.name / "scummvm.log" for r in runs + obj_runs if (out / r.name / "scummvm.log").exists()]
    if logs:
        first, last = min(p.stat().st_mtime for p in logs), max(p.stat().st_mtime for p in logs)
        fmt = lambda t: dt.datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M")
        started = fmt(first) if fmt(first) == fmt(last) else f"{fmt(first)} til {fmt(last)}"
        info = logs[0].parent / "kjoring.json"
        if args.bare_rapport and info.exists():
            k = json.loads(info.read_text())
            args.motor = Path(k.get("motor", args.motor))
            args.mod = Path(k.get("mod", args.mod))
    for run in runs:
        if not (out / run.name / "scummvm.log").exists():
            continue
        res = Result(run=run, name=run.name)
        info = out / run.name / "kjoring.json"
        k = json.loads(info.read_text()) if info.exists() else {}
        res.seconds = k.get("sekunder", 0.0)
        res.exit = k.get("slutt", "")
        parse_log(res, args, out, mod_rooms)
        if k.get("tett"):
            prune_dumps(res, out)
            if res.dump_frame is not None and res.dump_room == run.room:
                res.notes.append(f"spillet forlot rommet; bildet er {res.dump_frame - args.hopp} bilder etter hoppet")
        meta = rooms_meta.get(str(run.room), {})
        analyse(res, out, args, meta)
        judge(res, meta)
        results.append(res)
    if not results:
        print("Ingen kjøringer å rapportere.")
        return 1

    write_csv(results, out, rooms_meta)
    sheets = write_sheets(results, out, rooms_meta, args.per_ark)
    seams = object_seams(args.mod, args.uttrekk, rooms, rooms_meta, jobs, out, args.somer)
    with open(out / "somer.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["objekt", "rom", "kilde", "grense_px", "avvik", "x", "y", "w", "h", "naerbilde"])
        for f in seams:
            w.writerow([f["objekt"], f["rom"], f["kilde"], f["grense_px"], f["avvik"], f["x"], f["y"], f["w"], f["h"],
                        f.get("naerbilde", "")])
    objruns = [object_states(run, args, out, rooms_meta.get(str(run.room), {}), jobs)
               for run in obj_runs if (out / run.name / "scummvm.log").exists()]
    if objruns:
        write_objects_csv(objruns, out)
    write_report(results, out, args, rooms_meta, sheets, jobs, started, seams, objruns)
    bad = [r for r in results if r.status not in ("ok", "uten HD")]
    print(f"Ferdig: {out / 'RAPPORT.md'}, {out / 'romtest.csv'}{', objekter.csv' if objruns else ''} "
          f"og {len(sheets)} kontaktark.")
    for r in bad:
        print(f"  {r.name}: {r.status}; {'; '.join(r.notes)}")
    if objruns:
        states: dict[str, int] = {}
        for e in (e for r in objruns for e in r.rows):
            states[e.get("status", "")] = states.get(e.get("status", ""), 0) + 1
        print("  Objekttilstander: " + ", ".join(f"{s} {n}" for s, n in sorted(states.items())))
    quiet = ("HD brukt", "likt rommet", "ikke i modden", "dekket", "utelatt")
    for r in objruns:
        if r.status != "ok":
            print(f"  {r.run.name}: {r.status}; {'; '.join(r.notes)}")
        for e in r.rows:
            if e.get("status") not in quiet:
                print(f"  {r.run.name} {e['navn']}: {e.get('status')}; {'; '.join(e.get('merknad') or [])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
