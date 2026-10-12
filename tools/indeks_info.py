#!/usr/bin/env python3
"""Leser indeksfilen 00.LFL fra Zak McKracken, FM-Towns (SCUMM v3) og skriver ut det viktigste.

Bruk:
    python3 tools/indeks_info.py game/00.LFL            # oversikt
    python3 tools/indeks_info.py game/00.LFL --json     # alt som JSON
    python3 tools/indeks_info.py game/00.LFL --rooms    # romlisten (CSV: rom, fil, størrelse)

Skriptet leser filene og endrer ingenting. Det trenger bare standardbiblioteket.

Format (bekreftet mot ScummVM engines/scumm/resource_v4.cpp ved c9091321, ScummEngine_v4::readIndexFile,
som ScummEngine_v3 arver):
  Blokker: 4 byte størrelse (little endian, med hodet) + 2 byte tag. Filen er ikke kryptert.
  0R, 0S, 0N, 0C: uint16 antall, så (1 byte rom, 4 byte offset) per plass. 0R er 0 for alle rom i Zak:
                  rom N ligger i N.LFL. For skript, lyder og kostymer er offset fra starten av rommets fil.
  0O:             uint16 antall, så 4 byte per objekt (3 byte klassebiter, 1 byte eier og tilstand).
  RN:             romnavn XOR 0xFF (finnes ikke i den engelske FM-Towns-utgaven).
"""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

KNOWN_MD5 = {
    "2d4536a56e01da4b02eb021e7770afa2": "Zak McKracken, engelsk FM-Towns-utgave",
    "1ca86e2cf9aaa2068738a1e5ba477e60": "Zak McKracken, japansk FM-Towns-utgave",
    "ce3edc99cd4f478c5b37104d70c68ca5": "Zak McKracken, japansk FM-Towns-utgave",
}
NAVN = {"0R": "rooms", "0S": "scripts", "0N": "sounds", "0C": "costumes"}


def les(sti: Path) -> dict:
    d = sti.read_bytes()
    out = {"file": str(sti), "size": len(d), "md5": hashlib.md5(d).hexdigest(), "blocks": [], "room_names": {}}
    out["edition"] = KNOWN_MD5.get(out["md5"], "ukjent utgave")
    p = 0
    while p + 6 <= len(d):
        size = struct.unpack_from("<I", d, p)[0]
        tag = d[p + 4:p + 6].decode("latin1")
        if size < 6 or p + size > len(d):
            raise SystemExit(f"Ugyldig blokk ved 0x{p:X}")
        out["blocks"].append({"tag": tag, "offset": p, "size": size})
        q = p + 6
        if tag in NAVN:
            n = struct.unpack_from("<H", d, q)[0]
            ent = [(d[q + 2 + 5 * i], struct.unpack_from("<I", d, q + 3 + 5 * i)[0]) for i in range(n)]
            out[NAVN[tag]] = {"slots": n, "used": sum(1 for r, _ in ent if r),
                              "entries": {i: [r, o] for i, (r, o) in enumerate(ent) if r}}
        elif tag == "0O":
            out["global_objects"] = struct.unpack_from("<H", d, q)[0]
        elif tag == "RN":
            r = q
            while d[r]:
                out["room_names"][d[r]] = bytes(c ^ 0xFF for c in d[r + 1:r + 10]).split(b"\0")[0].decode("latin1")
                r += 10
        p += size
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("index", type=Path, help="00.LFL")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--rooms", action="store_true")
    a = ap.parse_args()
    info = les(a.index)
    if a.json:
        print(json.dumps(info, indent=1))
        return 0
    if a.rooms:
        print("rom,fil,storrelse")
        for f in sorted(a.index.parent.glob("[0-9][0-9].LFL")):
            nr = int(f.stem)
            if 1 <= nr <= 97:
                print(f"{nr},{f.name},{f.stat().st_size}")
        return 0
    print(f"Fil:       {info['file']} ({info['size']} byte)")
    print(f"MD5:       {info['md5']} ({info['edition']})")
    print(f"Blokker:   {', '.join(b['tag'] for b in info['blocks'])}")
    for k in ("scripts", "sounds", "costumes"):
        if k in info:
            print(f"{k:10} {info[k]['used']} av {info[k]['slots']} plasser i bruk")
    if "rooms" in info:
        print(f"rooms      {info['rooms']['slots']} plasser (rom N ligger i N.LFL)")
    print(f"objekter   {info.get('global_objects', 0)}")
    print(f"romnavn    {len(info['room_names']) or 'ingen'}")
    return 0 if info["edition"] != "ukjent utgave" else 1


if __name__ == "__main__":
    sys.exit(main())
