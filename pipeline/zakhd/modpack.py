"""Bygger en mod-mappe som HD-motoren leser.

Oppsett (N = skala, for eksempel 4):
  mods/<navn>/mod.json
  mods/<navn>/rooms/roomNNN.png        HD-bakgrunn, eksakt (bredde*N) x (høyde*N), RGB
  mods/<navn>/rooms/roomNNN_idx.png    original 8-bit bakgrunn med palett (fra eksporten)
  mods/<navn>/objects/objNNN_SS.png    HD-objektbilde, RGBA, eksakt N ganger originalen
  mods/<navn>/objects/objNNN_SS_idx.png  original 8-bit objektbilde

Objekter skaleres sammen med bakgrunnen rundt seg og klippes ut etterpå. Da får de samme
detaljnivå og farger som bakgrunnen og stikker seg ikke ut.

Har du laget HD-bilder selv (KI-verktøy, maling), legg dem i en mappe med samme navn
(rooms/roomNNN.png, objects/objNNN_SS.png) og bruk --egne. De brukes da i stedet for
automatisk oppskalering, så lenge størrelsen stemmer.

Egne objektbilder tas med også for rom som ikke er valgt med --rooms (for eksempel store
nærbilder fra ChatGPT i rom som ikke har HD-bakgrunn ennå). Da lages ingen bakgrunn og
ingen automatisk oppskalerte objekter for rommet, bare de egne objektbildene. Motoren
bruker objektbildene også når rommet ikke har HD-bakgrunn.

Egne kostymeruter (costumes/costumeCCC_NNN.png, for eksempel figurruter fra ChatGPT) tas
med på samme måte for alle kostymer, også uten --kostymer. --kostymer velger kostymene
der resten av rutene skaleres automatisk. Ruter uten HD-bilde vises som originalen.

Myke kostymeruter (costumes/costumeCCC_NNN_hd.png, fra mottaket for figurark i glatt stil,
myk.py) har en marg rundt ruten og egen alfa. De tas med når størrelsen er
(bredde + 2 * marg) * N x (høyde + 2 * marg) * N med hele marger, og motoren bruker dem
før den vanlige ruten.

HD-skriften for teksten (fonts/map.txt og fonts/<mappe>/NNN.png, se skrift.py) legges med
i alle modder, uten --uten-skrift.
"""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

from PIL import Image

from . import skrift
from .upscale import upscale, upscale_alpha

MARGIN = 8  # piksler med bakgrunn rundt et objekt når det skaleres


def soft_size_ok(size: tuple[int, int], cel: tuple[int, int], scale: int) -> bool:
    """Om en myk rute (_hd.png) har en størrelse motoren godtar: hele originalpiksler med like stor
    marg på begge sider av ruten."""
    W, H = size
    w, h = cel
    if W % scale or H % scale:
        return False
    px, py = W // scale - w, H // scale - h
    return px >= 0 and py >= 0 and px % 2 == 0 and py % 2 == 0


def _check_size(im: Image.Image, want: tuple[int, int], name: str) -> bool:
    if im.size != want:
        print(f"  Hopper over {name}: er {im.size[0]}x{im.size[1]}, skal være {want[0]}x{want[1]}")
        return False
    return True


def build_mod(extract: Path, out: Path, *, scale: int, method: str, rooms: set[int] | None,
              own: Path | None = None, with_objects: bool = True, costumes: set[int] | None = None,
              films: list[str] | None = None, san: Path | None = None, text_font: bool = True,
              **upscale_kw) -> dict:
    meta = json.loads((extract / "rooms.json").read_text())
    (out / "rooms").mkdir(parents=True, exist_ok=True)
    (out / "objects").mkdir(parents=True, exist_ok=True)
    done_rooms, done_objects = [], []
    t0 = time.time()

    for key, info in meta["rooms"].items():
        num = int(key)
        if rooms is not None and num not in rooms:
            if own and with_objects:
                extra = _own_objects_only(extract, out, own, info, scale)
                if extra:
                    done_objects += extra
                    print(f"  rom {num:3d} {info['name']:<10} bare egne objektbilder: {', '.join(extra)}")
            continue
        src = extract / "rooms" / f"room{num:03d}.png"
        if not src.exists():
            continue
        want = (info["width"] * scale, info["height"] * scale)
        custom = own / "rooms" / f"room{num:03d}.png" if own else None
        if custom and custom.exists():
            hd = Image.open(custom).convert("RGB")
            if not _check_size(hd, want, custom.name):
                hd = None
        else:
            hd = None
        base = Image.open(src).convert("RGB")
        if hd is None:
            hd = upscale(base, scale, method, **upscale_kw)
        hd.save(out / "rooms" / f"room{num:03d}.png")
        shutil.copyfile(extract / "rooms" / f"room{num:03d}_idx.png", out / "rooms" / f"room{num:03d}_idx.png")
        done_rooms.append(num)
        print(f"  rom {num:3d} {info['name']:<10} {base.width}x{base.height} -> {hd.width}x{hd.height}")

        if not with_objects:
            continue
        for obj in info["objects"]:
            for state in obj["states"]:
                name = f"obj{obj['id']:03d}_{state}"
                osrc = extract / "objects" / f"{name}.png"
                if not osrc.exists():
                    continue
                oim = Image.open(osrc).convert("RGBA")
                owant = (oim.width * scale, oim.height * scale)
                custom = own / "objects" / f"{name}.png" if own else None
                ohd = None
                if custom and custom.exists():
                    ohd = Image.open(custom).convert("RGBA")
                    if not _check_size(ohd, owant, custom.name):
                        ohd = None
                if ohd is None:
                    ohd = _upscale_object_in_context(base, oim, obj["x"], obj["y"], scale, method, **upscale_kw)
                ohd.save(out / "objects" / f"{name}.png")
                shutil.copyfile(extract / "objects" / f"{name}_idx.png", out / "objects" / f"{name}_idx.png")
                done_objects.append(name)

    has_own_cels = bool(own and (own / "costumes").is_dir() and any((own / "costumes").glob("costume*.png")))  # også _hd.png
    done_costumes = _build_costumes(extract, out, scale, method, costumes or set(), own, **upscale_kw) \
        if costumes or has_own_cels else []
    done_films = _build_films(san, out, scale, method, films, own, **upscale_kw) if films and san else []
    letters = skrift.lag_skrift(out) if text_font else {}

    manifest = {
        "format": 1,
        "scale": scale,
        "method": method if not own else f"{method} + egne bilder",
        "created": time.strftime("%Y-%m-%d %H:%M"),
        "game_md5_la0": meta.get("game_md5_la0"),
        "rooms": sorted(done_rooms),
        "objects": sorted(done_objects),
        "costumes": sorted(set(c.split("_")[0] for c in done_costumes)),
        "costume_cels": len(done_costumes),
        "films": done_films,
        "fonts": letters,
    }
    (out / "mod.json").write_text(json.dumps(manifest, indent=1))
    print(f"Ferdig: {len(done_rooms)} rom, {len(done_objects)} objektbilder og {len(done_costumes)} kostymeruter "
          f"på {time.time() - t0:.1f} s -> {out}")
    return manifest


def _own_objects_only(extract: Path, out: Path, own: Path, info: dict, scale: int) -> list[str]:
    """Egne objektbilder for et rom som ikke er med i modden. Ingen bakgrunn, ingen automatisk oppskalering."""
    done = []
    for obj in info["objects"]:
        for state in obj["states"]:
            name = f"obj{obj['id']:03d}_{state}"
            custom = own / "objects" / f"{name}.png"
            osrc = extract / "objects" / f"{name}.png"
            if not custom.exists() or not osrc.exists():
                continue
            with Image.open(osrc) as oim:
                owant = (oim.width * scale, oim.height * scale)
            ohd = Image.open(custom).convert("RGBA")
            if not _check_size(ohd, owant, custom.name):
                continue
            ohd.save(out / "objects" / f"{name}.png")
            shutil.copyfile(extract / "objects" / f"{name}_idx.png", out / "objects" / f"{name}_idx.png")
            done.append(name)
    return done


def _upscale_object_in_context(room: Image.Image, obj: Image.Image, x: int, y: int, scale: int,
                               method: str, **kw) -> Image.Image:
    """Limer objektet inn i bakgrunnen, skalerer et utsnitt med litt marg, og klipper ut igjen."""
    x0, y0 = max(0, x - MARGIN), max(0, y - MARGIN)
    x1 = min(room.width, x + obj.width + MARGIN)
    y1 = min(room.height, y + obj.height + MARGIN)
    if x1 <= x0 or y1 <= y0 or x < 0 or y < 0 or x + obj.width > room.width or y + obj.height > room.height:
        # Objektet ligger utenfor rommet (skjer for enkelte UI-objekter): skaler det alene
        rgb = upscale(obj.convert("RGB"), scale, method, **kw)
        rgb.putalpha(upscale_alpha(obj.getchannel("A"), scale))
        return rgb
    canvas = room.crop((x0, y0, x1, y1)).convert("RGBA")
    canvas.alpha_composite(obj, (x - x0, y - y0))
    big = upscale(canvas.convert("RGB"), scale, method, **kw)
    ox, oy = (x - x0) * scale, (y - y0) * scale
    cut = big.crop((ox, oy, ox + obj.width * scale, oy + obj.height * scale))
    cut.putalpha(upscale_alpha(obj.getchannel("A"), scale))
    return cut


def compare_sheet(extract: Path, room: int, methods: list[str], scale: int, out: Path, crop: int = 96, **kw) -> Path:
    """Lager et sammenligningsbilde av et utsnitt av ett rom med flere metoder side om side."""
    base = Image.open(extract / "rooms" / f"room{room:03d}.png").convert("RGB")
    cx, cy = base.width // 2 - crop // 2, base.height // 2 - crop // 2
    part = base.crop((cx, cy, cx + crop, cy + crop))
    tiles = [upscale(part, scale, m, **kw) for m in methods]
    sheet = Image.new("RGB", (len(tiles) * crop * scale + (len(tiles) - 1) * 8, crop * scale), (20, 20, 20))
    for i, t in enumerate(tiles):
        sheet.paste(t, (i * (crop * scale + 8), 0))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return out


def _bleed(im: Image.Image, passes: int = 3) -> Image.Image:
    """Fyller gjennomsiktige piksler med farger fra naboene, så kantene ikke blir mørke ved oppskalering."""
    from PIL import ImageFilter
    rgb = im.convert("RGB")
    alpha = im.getchannel("A")
    filled = rgb
    mask = alpha
    for _ in range(passes):
        grown = filled.filter(ImageFilter.MaxFilter(3))
        filled = Image.composite(filled, grown, mask)
        mask = mask.filter(ImageFilter.MaxFilter(3))
    return filled


def _build_costumes(extract: Path, out: Path, scale: int, method: str, costumes: set[int],
                    own: Path | None, **kw) -> list[str]:
    """Kostymeruter. Filnavn: costumes/costumeCCC_NNN.png (+ _idx.png fra eksporten).

    Egne ruter (own/costumes, for eksempel figurruter fra ChatGPT) tas med for alle kostymer når
    størrelsen stemmer. For kostymene i `costumes` ({-1} er alle) skaleres resten av rutene
    automatisk. Andre kostymer får bare de egne rutene, og rutene uten HD-bilde vises som originalen.
    """
    meta = json.loads((extract / "costumes.json").read_text())
    dest = out / "costumes"
    dest.mkdir(parents=True, exist_ok=True)
    done = []
    for key, info in sorted(meta.items(), key=lambda kv: int(kv[0])):
        cid = int(key)
        auto = costumes == {-1} or cid in costumes
        n_own = n_auto = n_soft = 0
        for cel in info["cels"]:
            name = f"costume{cid:03d}_{cel['cel']:03d}"
            src = extract / "costumes" / f"{name}.png"
            custom = own / "costumes" / f"{name}.png" if own else None
            soft = own / "costumes" / f"{name}_hd.png" if own else None
            if soft and soft.exists() and src.exists():
                with Image.open(soft) as sim, Image.open(src) as oim:
                    ok = soft_size_ok(sim.size, oim.size, scale)
                if ok:
                    shutil.copyfile(soft, dest / f"{name}_hd.png")
                    shutil.copyfile(extract / "costumes" / f"{name}_idx.png", dest / f"{name}_idx.png")
                    n_soft += 1
                    if not (auto or (custom and custom.exists())):
                        done.append(name)
                        continue
                else:
                    print(f"  Hopper over {soft.name}: størrelsen gir ikke hele og like marger")
            if not src.exists() or not (auto or (custom and custom.exists())):
                continue
            im = Image.open(src).convert("RGBA")
            want = (im.width * scale, im.height * scale)
            hd = None
            if custom and custom.exists():
                hd = Image.open(custom).convert("RGBA")
                if not _check_size(hd, want, custom.name):
                    hd = None
            if hd is None and not auto:
                continue
            if hd is None:
                hd = upscale(_bleed(im), scale, method, **kw)
                hd.putalpha(upscale_alpha(im.getchannel("A"), scale))
                n_auto += 1
            else:
                n_own += 1
            hd.save(dest / f"{name}.png")
            shutil.copyfile(extract / "costumes" / f"{name}_idx.png", dest / f"{name}_idx.png")
            done.append(name)
        if n_own or n_auto or n_soft:
            print(f"  kostyme {cid:3d}: {len(info['cels'])} ruter, {n_own} egne, {n_soft} myke og "
                  f"{n_auto} skalert automatisk")
    return done


def _build_films(san: Path, out: Path, scale: int, method: str, films: list[str], own: Path | None, **kw) -> list[str]:
    """Skalerer filmrammer fra `san`-uttrekket i The Dig (work/san/san/<FILM>/<ramme>.png) til mods/<navn>/san/. Zak har ingen filmer.

    Merk: én film i 4x tar mye plass som PNG (omtrent 1 MB per ramme). Velg filmene du vil teste.
    """
    src_root = san / "san"
    names = sorted(p.name for p in src_root.iterdir() if p.is_dir()) if films == ["alle"] else [f.upper() for f in films]
    done = []
    for name in names:
        src = src_root / name
        if not src.is_dir():
            print(f"  fant ikke film {name} i {src_root} (Zak har ingen filmer)")
            continue
        dest = out / "san" / name
        dest.mkdir(parents=True, exist_ok=True)
        frames = sorted(src.glob("*.png"))
        for f in frames:
            custom = own / "san" / name / f.name if own else None
            if custom and custom.exists():
                shutil.copyfile(custom, dest / f.name)
                continue
            upscale(Image.open(f).convert("RGB"), scale, method, **kw).save(dest / f.name)
        done.append(name)
        print(f"  film {name}: {len(frames)} rammer")
    return done
