"""Listen over all grafikk som skal byttes ut, laget fra uttrekket (zakhd extract).

Skriver to filer:

  docs/grafikkliste.csv   én rad per rombakgrunn, objektbilde, kostyme og tegnsett, med mål, antall
                          ruter, HD-størrelse (4x) og et grovt anslag på antall grafikkjobber
  docs/rom-oversikt.csv   én rad per rom, samme kolonner som i The Dig og Sam & Max

Navnet på rommene hentes fra docs/romnavn.csv (beskrivelser skrevet fra skript og bilder), siden
indeksen ikke har romnavn.

Med de dekompilerte skriptene (work/skript/objekter.tsv) merkes objekter som kan plukkes opp
(verb 8, Pick up), siden de er kandidater til inventarikoner (docs/GRENSESNITT.md).

Anslaget på jobber følger jobbformatet i docs/BESTILLING-CHATGPT.md: ett lerret dekker 384 x 256
originalpiksler. Et rom bredere enn 384 deles i deler på 384 med 64 piksler overlapp. Kostymer
regnes som ett figurark per 24 synlige ruter. Det er et anslag til planlegging, ikke jobblisten.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

SKALA = 4
JOBB_B = 384
OVERLAPP = 64
RUTER_PER_ARK = 24


def _romjobber(bredde: int) -> int:
    if bredde <= JOBB_B:
        return 1
    return math.ceil((bredde - OVERLAPP) / (JOBB_B - OVERLAPP))


def _les_verb(skript: Path | None) -> dict[int, list[int]]:
    if not skript:
        return {}
    f = skript / "objekter.tsv"
    if not f.exists():
        return {}
    out: dict[int, list[int]] = {}
    for linje in f.read_text(encoding="utf-8").splitlines():
        if linje.startswith("#") or not linje.strip():
            continue
        del_ = linje.split("\t")
        verb = [int(v) for v in del_[7].split(",") if v.isdigit()]
        out.setdefault(int(del_[0]), []).extend(verb)
    return out


def _les_romnavn(docs: Path) -> dict[str, str]:
    """Beskrivelsene i docs/romnavn.csv (rom, beskrivelse, kilde), skrevet for hånd fra skript og bilder."""
    f = docs / "romnavn.csv"
    if not f.exists():
        return {}
    with open(f, newline="", encoding="utf-8") as fh:
        return {r["rom"]: r["beskrivelse"] for r in csv.DictReader(fh)}


def skriv(extract: Path, docs: Path, skript: Path | None = None) -> dict:
    rooms = json.loads((extract / "rooms.json").read_text())["rooms"]
    romnavn = _les_romnavn(docs)
    costumes = json.loads((extract / "costumes.json").read_text())
    fonts_f = extract / "fonts.json"
    fonts = json.loads(fonts_f.read_text()) if fonts_f.exists() else {}
    verb = _les_verb(skript)

    kolonner = ["type", "id", "rom", "navn", "bredde", "hoyde", "ruter", "unike_bilder", "bredde_x4", "hoyde_x4",
                "piksler", "jobber_anslag", "inventar", "merknad"]
    rader: list[dict] = []
    for k in sorted(rooms, key=int):
        r = rooms[k]
        if not r.get("width"):
            continue
        rader.append({"type": "rom", "id": k, "rom": k, "navn": romnavn.get(k, r.get("name", "")), "bredde": r["width"],
                      "hoyde": r["height"], "ruter": "", "unike_bilder": 1, "bredde_x4": r["width"] * SKALA,
                      "hoyde_x4": r["height"] * SKALA, "piksler": r["width"] * r["height"],
                      "jobber_anslag": _romjobber(r["width"]), "inventar": "",
                      "merknad": "z-plan" if r.get("zplane") else ""})
    for k in sorted(rooms, key=int):
        for o in rooms[k]["objects"]:
            if not o.get("states"):
                continue
            kan_plukkes = 8 in verb.get(o["id"], [])
            rader.append({"type": "objekt", "id": o["id"], "rom": k, "navn": o.get("navn", ""), "bredde": o["w"],
                          "hoyde": o["h"], "ruter": "", "unike_bilder": 1, "bredde_x4": o["w"] * SKALA,
                          "hoyde_x4": o["h"] * SKALA, "piksler": o["w"] * o["h"],
                          "jobber_anslag": "", "inventar": "kan plukkes opp" if kan_plukkes else "",
                          "merknad": "males på plass i rommet (lagjobb)"})
    for k in sorted(costumes, key=int):
        c = costumes[k]
        cels = c["cels"]
        unike = [e for e in cels if "samme_bilde_som" not in e]
        piksler = sum(e["w"] * e["h"] for e in unike)
        storst = max(cels, key=lambda e: e["w"] * e["h"]) if cels else {"w": 0, "h": 0}
        rader.append({"type": "kostyme", "id": k, "rom": c["room"], "navn": "", "bredde": storst["w"],
                      "hoyde": storst["h"], "ruter": len(cels), "unike_bilder": len(unike),
                      "bredde_x4": storst["w"] * SKALA, "hoyde_x4": storst["h"] * SKALA, "piksler": piksler,
                      "jobber_anslag": max(1, math.ceil(len(unike) / RUTER_PER_ARK)) if unike else 0, "inventar": "",
                      "merknad": f"format {c['format']}, {c['farger']} farger, mål er største rute"})
    for k in sorted(fonts, key=int):
        f = fonts[k]
        rader.append({"type": "tegnsett", "id": k, "rom": "", "navn": f["fil"], "bredde": 8, "hoyde": f["hoeyde"],
                      "ruter": f["med_piksler"], "unike_bilder": f["med_piksler"], "bredde_x4": 32,
                      "hoyde_x4": f["hoeyde"] * SKALA, "piksler": f["med_piksler"] * 8 * f["hoeyde"],
                      "jobber_anslag": "", "inventar": "",
                      "merknad": "tegn med piksler; HD-skrift som i The Dig, ikke tegnet av grafiker"})
    docs.mkdir(parents=True, exist_ok=True)
    with open(docs / "grafikkliste.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=kolonner)
        w.writeheader()
        w.writerows(rader)

    rom_kol = ["rom", "navn", "bredde", "hoyde", "z_plan", "paletter", "objektbilder", "bredde_x4", "hoyde_x4",
               "prioritet", "status", "notat"]
    n_rom = 0
    with open(docs / "rom-oversikt.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=rom_kol)
        w.writeheader()
        for k in sorted(rooms, key=int):
            r = rooms[k]
            if not r.get("width"):
                continue
            n_rom += 1
            w.writerow({"rom": k, "navn": romnavn.get(k, r.get("name", "")), "bredde": r["width"], "hoyde": r["height"],
                        "z_plan": int(bool(r.get("zplane"))), "paletter": 1,
                        "objektbilder": sum(len(o.get("states", [])) for o in r["objects"]),
                        "bredde_x4": r["width"] * SKALA, "hoyde_x4": r["height"] * SKALA,
                        "prioritet": "", "status": "ikke startet", "notat": ""})
    return {"rader": len(rader), "rom": n_rom}
