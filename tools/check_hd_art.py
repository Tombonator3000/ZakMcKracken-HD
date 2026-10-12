#!/usr/bin/env python3
"""Kontroller egne HD-bilder før build-mod, som ellers kan falle stille tilbake."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from PIL import Image, ImageChops


PATTERNS = {
    "rooms": r"room\d{3}\.png",
    "objects": r"obj\d{3}_[0-9A-F]{2}\.png",
    "costumes": r"costume\d{3}_\d{3,}\.png",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(extract: Path, own: Path, scale: int) -> dict:
    report = {"scale": scale, "assets": [], "errors": []}
    files = sorted(own.rglob("*.png")) if own.is_dir() else []
    if not files:
        report["errors"].append(f"Ingen PNG-bilder i {own}")
    for path in files:
        rel = path.relative_to(own)
        problems = []
        if len(rel.parts) != 2 or not re.fullmatch(PATTERNS.get(rel.parts[0], r"(?!)"), rel.name):
            report["errors"].append(f"{rel}: filnavnet følger ikke motorens oppslag")
            continue
        source = extract / rel
        index = source.with_name(source.stem + "_idx.png")
        if not source.is_file() or not index.is_file():
            report["errors"].append(f"{rel}: mangler originalbilde eller indeksbilde i uttrekket")
            continue
        try:
            with Image.open(source) as original, Image.open(index) as indexed, Image.open(path) as hd:
                original.load()
                indexed.load()
                hd.load()
                want = (original.width * scale, original.height * scale)
                mode = "RGB" if rel.parts[0] == "rooms" else "RGBA"
                if hd.format != "PNG" or hd.mode != mode:
                    problems.append(f"må være PNG i {mode}, er {hd.format}/{hd.mode}")
                if hd.size != want:
                    problems.append(f"må være {want[0]}x{want[1]}, er {hd.width}x{hd.height}")
                if indexed.mode != "P" or indexed.size != original.size:
                    problems.append("originalindeksen må være uendret palett-PNG i originalmål")
                if mode == "RGBA" and hd.mode == "RGBA" and hd.size == want:
                    mask = original.convert("RGBA").getchannel("A").resize(want, Image.Resampling.NEAREST)
                    alpha = hd.getchannel("A").point(lambda a: 255 if a >= 128 else 0)
                    mask = mask.point(lambda a: 255 if a >= 128 else 0)
                    if ImageChops.difference(mask, alpha).getbbox():
                        problems.append("alfasilhuetten stemmer ikke med originalen ved motorens terskel 128")
                report["assets"].append({
                    "file": rel.as_posix(), "source_size": list(original.size),
                    "target_size": list(hd.size), "mode": hd.mode,
                    "source_sha256": sha256(source), "index_sha256": sha256(index),
                    "hd_sha256": sha256(path), "pass": not problems,
                })
        except (OSError, ValueError) as exc:
            problems.append(f"kan ikke lese PNG: {exc}")
        report["errors"].extend(f"{rel}: {problem}" for problem in problems)
    report["pass"] = not report["errors"]
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--extract", type=Path, default=Path("work/extract"))
    ap.add_argument("--own", type=Path, required=True)
    ap.add_argument("--scale", type=int, default=4)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()
    if args.scale <= 0:
        ap.error("skala må være positiv")
    report = check(args.extract, args.own, args.scale)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    for problem in report["errors"]:
        print("FEIL:", problem)
    print(f"{'PASS' if report['pass'] else 'FAIL'}: {len(report['assets'])} bilder kontrollert")
    print("Kontrollen gjelder filformat, mål, indeks og alfasilhuett. Visuell registrering må inspiseres i spillet.")
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
