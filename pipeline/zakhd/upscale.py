"""Oppskaleringsmetoder.

Alle metoder tar et RGB-bilde og gir et RGB-bilde som er nøyaktig `scale` ganger større.
Motoren krever eksakt størrelse, så resultatet tilpasses hvis et eksternt verktøy gir noe annet.

Metoder:
  nearest       Hver piksel blir en blokk. Nyttig som referanse og for testing.
  lanczos       Myk oppskalering, rask, ingen ekstra programmer.
  lanczos-sharp Lanczos med litt skarphet etterpå.
  realesrgan    Real-ESRGAN via realesrgan-ncnn-vulkan (må være installert, bruker skjermkortet).
  cmd           Valgfri kommando, for eksempel et annet KI-verktøy. Malen får {inn}, {ut} og {skala}.
"""
from __future__ import annotations

import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageFilter

METHODS = ["nearest", "lanczos", "lanczos-sharp", "realesrgan", "cmd"]


def _fit(im: Image.Image, size: tuple[int, int]) -> Image.Image:
    return im if im.size == size else im.resize(size, Image.LANCZOS)


def _external(im: Image.Image, scale: int, argv_template: list[str]) -> Image.Image:
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = Path(tmp) / "inn.png", Path(tmp) / "ut.png"
        im.save(src)
        argv = [a.format(inn=src, ut=dst, skala=scale) for a in argv_template]
        subprocess.run(argv, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        out = Image.open(dst).convert("RGB")
        out.load()
    return out


def upscale(im: Image.Image, scale: int, method: str, *, tool: str | None = None,
            model: str = "realesrgan-x4plus", cmd: str | None = None) -> Image.Image:
    im = im.convert("RGB")
    size = (im.width * scale, im.height * scale)
    if method == "nearest":
        return im.resize(size, Image.NEAREST)
    if method == "lanczos":
        return im.resize(size, Image.LANCZOS)
    if method == "lanczos-sharp":
        return im.resize(size, Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=2, percent=80, threshold=2))
    if method == "realesrgan":
        exe = tool or shutil.which("realesrgan-ncnn-vulkan")
        if not exe:
            raise SystemExit("Fant ikke realesrgan-ncnn-vulkan. Last ned fra "
                             "https://github.com/xinntao/Real-ESRGAN/releases og legg den i PATH, "
                             "eller bruk --tool STI.")
        out = _external(im, scale, [exe, "-i", "{inn}", "-o", "{ut}", "-s", "4", "-n", model])
        return _fit(out, size)
    if method == "cmd":
        if not cmd:
            raise SystemExit("Metoden cmd krever --cmd, for eksempel: --cmd 'mittverktoy {inn} {ut} {skala}'")
        return _fit(_external(im, scale, shlex.split(cmd)), size)
    raise SystemExit(f"Ukjent metode: {method}. Velg en av: {', '.join(METHODS)}")


def upscale_alpha(alpha: Image.Image, scale: int) -> Image.Image:
    """Alfakanalen skaleres med nærmeste nabo, så kantene blir like skarpe som i originalen."""
    return alpha.resize((alpha.width * scale, alpha.height * scale), Image.NEAREST)
