"""Kommandolinje for HD-pipelinen.

  zakhd info                        Sjekker spillfilene og viser nøkkeltall
  zakhd extract                     Eksporterer rom, objekter, kostymer og tegnsett til work/extract (eksport_v3.py)
  zakhd grafikkliste                Skriver docs/grafikkliste.csv og docs/rom-oversikt.csv fra uttrekket
  zakhd build-mod --name test        Lager en mod-mappe for HD-motoren
  zakhd compare --room 22            Lager et sammenligningsbilde av oppskaleringsmetoder
  zakhd gpt-pakke                    Lager jobber for ChatGPT i work/gpt (rom, store objektbilder, lag, ikonark
                                     og figurark; --figurer alle for alle kostymene)
  zakhd gpt-inn                      Tar imot bilder fra ChatGPT, sjekker dem og lager HD-rom og HD-objekter
  zakhd gpt-ordre                    Skriver ORDRE.md med neste jobber til ChatGPT
  zakhd myke-figurer                 Tar inn figurarkene i glatt stil (ekte alfa) som myke kostymeruter
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import export, gamedata, gpt, lfl, modpack, myk
from .upscale import METHODS

# Zak McKracken, engelsk FM-Towns-utgave (ScummVM scumm-md5.h)
KNOWN_INDEX_MD5 = "2d4536a56e01da4b02eb021e7770afa2"
INDEX_FILE = lfl.INDEX_FILE


def _repo_root() -> Path:
    here = Path.cwd().resolve()
    for p in [here, *here.parents]:
        if (p / "tools" / "hent_spilldata.sh").exists():
            return p
    return here


def _rooms(arg: str | None) -> set[int] | None:
    """Romliste fra kommandolinjen. Uten liste betyr alle rom, og "ingen" betyr ingen rom."""
    if not arg:
        return None
    if arg.strip().lower() == "ingen":
        return set()
    out: set[int] = set()
    for part in arg.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.update(range(int(a), int(b) + 1))
        elif part.strip():
            out.add(int(part))
    return out


def cmd_info(a) -> int:
    game = Path(a.game)
    idx = lfl.les_indeks(game / INDEX_FILE)
    rooms = lfl.les_alle_rom(game)
    ok = idx.md5 == KNOWN_INDEX_MD5
    med_ro = [r for r in rooms.values() if r.ro_size]
    bilder = sum(1 for r in med_ro for o in r.objekter if o.nr in r.bilder and lfl.le32(r.d, r.bilder[o.nr]) > 8)
    spor = sorted(game.glob("Track*.fla"))
    print(f"Spillmappe:   {game}")
    print(f"{INDEX_FILE} MD5:  {idx.md5} ({'engelsk FM-Towns-utgave' if ok else 'ukjent utgave'})")
    print(f"SCUMM:        v{idx.version} (256 farger, GF_OLD256, små blokkhoder)")
    print(f"Rom:          {len(med_ro)} med grafikk, brede: {sum(r.bredde > 320 for r in med_ro)}, "
          f"filer uten rom: {', '.join(f'{r.nr:02d}.LFL' for r in rooms.values() if not r.ro_size) or 'ingen'}")
    print(f"Objekter:     {sum(len(r.objekter) for r in med_ro)} ({bilder} med eget bilde)")
    print(f"Skript:       {len(idx.skript)} globale, {sum(len(r.lokale) for r in med_ro)} lokale")
    print(f"Kostymer:     {len(idx.kostymer)}")
    print(f"Lyder:        {len(idx.lyder)}")
    print(f"CD-musikk:    {len(spor)} spor (Track*.fla)")
    return 0 if ok else 1


def cmd_extract(a) -> int:
    from . import eksport_v3
    game, out = Path(a.game), Path(a.out)
    parts = set(a.only.split(",")) if a.only else {"rom", "kostymer", "tegnsett"}
    ok = True
    if "rom" in parts:
        meta = eksport_v3.export_rooms(game, out, _rooms(a.rooms))
        n_rooms = sum(1 for r in meta["rooms"].values() if "codecs" in r)
        n_obj = sum(len(o["states"]) for r in meta["rooms"].values() for o in r["objects"])
        print(f"Rom og objekter: {meta['written']} bilder ({n_rooms} rom, {n_obj} objektbilder) -> {out}")
        if meta["errors"]:
            ok = False
            print(f"  {len(meta['errors'])} feil, se rooms.json")
    if "kostymer" in parts:
        res = eksport_v3.export_costumes(game, out, _rooms(a.costumes))
        print(f"Kostymeruter: {res['written']} bilder fra {res['costumes']} kostymer -> {out / 'costumes'}")
        if res["errors"]:
            ok = False
            print(f"  {len(res['errors'])} feil: " + "; ".join(res["errors"][:5]))
    if "tegnsett" in parts:
        f = eksport_v3.export_fonts(game, out)
        print(f"Tegnsett: {len(f)} ark -> {out / 'fonts'}")
    return 0 if ok else 1


def cmd_grafikkliste(a) -> int:
    from . import grafikkliste
    n = grafikkliste.skriv(Path(a.extract), Path(a.docs), Path(a.skript) if a.skript else None)
    print(f"Grafikklisten: {n['rader']} rader -> {Path(a.docs) / 'grafikkliste.csv'}; "
          f"romlisten: {n['rom']} rom -> {Path(a.docs) / 'rom-oversikt.csv'}")
    return 0


def _upscale_kw(a) -> dict:
    return {"tool": a.tool, "model": a.model, "cmd": a.cmd}


def cmd_build_mod(a) -> int:
    out = Path(a.out) if a.out else Path(a.mods) / a.name
    if a.kun_ui:
        modpack.build_ui_mod(out, Path(a.egne) if a.egne else None, a.scale)
        return 0
    costumes = {-1} if a.kostymer == "alle" else _rooms(a.kostymer)
    modpack.build_mod(Path(a.extract), out, scale=a.scale, method=a.method, rooms=_rooms(a.rooms),
                      own=Path(a.egne) if a.egne else None, with_objects=not a.uten_objekter,
                      costumes=costumes, films=a.filmer.split(",") if a.filmer else None,
                      san=Path(a.san), text_font=not a.uten_skrift, **_upscale_kw(a))
    return 0


def cmd_compare(a) -> int:
    methods = a.methods.split(",")
    out = Path(a.out or f"work/compare/room{a.room:03d}.png")
    modpack.compare_sheet(Path(a.extract), a.room, methods, a.scale, out, **_upscale_kw(a))
    print(f"Sammenligning ({', '.join(methods)}) -> {out}")
    return 0


def _figures(arg: str | None):
    """--figurer: pilot (standard), alle, ingen eller kostyme-ID-er (14,18 eller 14-20)."""
    arg = (arg or "pilot").strip().lower()
    return arg if arg in ("pilot", "alle", "ingen") else _rooms(arg)


def cmd_gpt_pakke(a) -> int:
    notes = gpt.read_notes(Path(a.notater)) if a.notater else {}
    jobs = gpt.make_jobs(Path(a.extract), Path(a.ut), _rooms(a.rooms), notes, figures=_figures(a.figurer),
                         game=Path(a.game), figure_list=Path(a.figurliste) if a.figurliste else None)
    n = {t: sum(j.type == t for j in jobs) for t in ("rom", "objekt", "lag", "ikon", "figur")}
    pieces = {t: len(gpt._pieces_of(jobs, t)) for t in ("lag", "ikon", "figur")}
    sheets = len({j.bilde for j in jobs if j.type == "figur"})
    print(f"{len(jobs)} jobber ({n['rom']} for rom, {n['objekt']} for store objektbilder, {n['lag']} lagjobber med "
          f"{pieces['lag']} små objektbilder, {n['ikon']} ikonark med {pieces['ikon']} ikoner, {n['figur']} jobber "
          f"for {sheets} figurark med {pieces['figur']} kostymeruter) -> "
          f"{Path(a.ut) / 'jobber'} (oversikt i JOBBER.md, status i status.csv)")
    return 0


def cmd_gpt_inn(a) -> int:
    s = gpt.import_results(Path(a.fra), Path(a.extract), Path(a.ut), sigma=a.sigma, strength=a.styrke,
                           rejections=Path(a.avvisninger) if a.avvisninger else None,
                           only_approved=a.bare_godkjente)
    print("Status:", ", ".join(f"{k} {v}" for k, v in sorted(s["status"].items())))
    print(f"Ferdige rom ({len(s['ferdige_rom'])} av {s['rom_totalt']}):",
          ", ".join(map(str, s["ferdige_rom"])) or "ingen")
    print(f"Ferdige objekter ({len(s['ferdige_objekter'])} av {s['objekter_totalt']}):",
          ", ".join(s["ferdige_objekter"]) or "ingen")
    if s["lagobjekter_totalt"]:
        print(f"Ferdige objektbilder fra lag: {len(s['ferdige_lagobjekter'])} av {s['lagobjekter_totalt']}")
    if s["ikoner_totalt"]:
        print(f"Ferdige ikoner fra ikonark: {len(s['ferdige_ikoner'])} av {s['ikoner_totalt']}")
    if s["figurruter_totalt"]:
        print(f"Ferdige figurruter fra figurark: {len(s['ferdige_figurruter'])} av {s['figurruter_totalt']}")
    for line in s["venter"]:
        print("  venter:", line)
    print(f"Rapport: {Path(a.fra) / 'RAPPORT.md'}. Bruk resultatet med: zakhd build-mod --egne {a.ut}")
    return 0


def cmd_gpt_ordre(a) -> int:
    anchors = sorted(p.name for p in Path(a.stil).glob("*.png")) if a.stil and Path(a.stil).is_dir() else []
    path = gpt.write_orders(Path(a.fra), batch=a.antall, anchors=anchors, messages=a.beskjed or None,
                           tasks=Path(a.oppgaver) if a.oppgaver else None)
    gpt.write_list(Path(a.fra), batch=a.antall)
    print(f"Ordre skrevet: {path}")
    return 0


def cmd_myke_figurer(a) -> int:
    only = {j.strip() for j in a.jobb.split(",") if j.strip()} if a.jobb else None
    r = myk.import_all(Path(a.gren), Path(a.extract), Path(a.ut), only=only,
                       previews=Path(a.forhandsvisning) if a.forhandsvisning else None,
                       rejections=gpt.read_rejections(Path(a.avvisninger) if a.avvisninger else None))
    bad = {j: x["feil"] for j, x in r["ark"].items() if x.get("feil")}
    rejected = sorted(j for j, x in r["ark"].items() if x.get("avvist") is not None)
    if rejected:
        print(f"Avviste ark, ikke tatt inn: {', '.join(rejected)}")
    print(f"Myke figurer: {len(r['ark']) - len(bad)} ark, {r['ruter_ok']} ruter ok, {r['ruter_sjekk']} til "
          f"gjennomsyn, {r['ruter_mangler']} uten del på arket -> {Path(a.ut) / 'costumes'} (rapport i myke.json)")
    for j, why in sorted(bad.items()):
        print(f"  {j}: {why}")
    return 0


def main(argv: list[str] | None = None) -> int:
    root = _repo_root()
    ap = argparse.ArgumentParser(prog="zakhd", description="HD-pipeline for Zak McKracken (FM-Towns)")
    ap.add_argument("--game", default=str(root / "game"), help="mappe med 00.LFL til 59.LFL, 98.LFL, 99.LFL og Track*.fla (standard: game/)")
    sub = ap.add_subparsers(dest="command", required=True)

    sub.add_parser("info", help="sjekk spillfilene")

    p = sub.add_parser("extract", help="eksporter originalgrafikk")
    p.add_argument("--out", default=str(root / "work" / "extract"))
    p.add_argument("--only", help="rom, kostymer, tegnsett (kommaseparert). Standard: alle")
    p.add_argument("--rooms", help="for eksempel 22,24 eller 20-30")
    p.add_argument("--costumes", help="kostyme-ID-er, for eksempel 1-10")

    p = sub.add_parser("grafikkliste", help="skriv listen over all grafikk som skal byttes ut")
    p.add_argument("--extract", default=str(root / "work" / "extract"))
    p.add_argument("--docs", default=str(root / "docs"))
    p.add_argument("--skript", default=str(root / "work" / "skript"),
                   help="dekompilerte skript (tools/dekompiler_skript.py), for objektnavn og inventar. Tom streng for ingen")

    def up(p):
        p.add_argument("--method", default="lanczos", choices=METHODS)
        p.add_argument("--scale", type=int, default=4)
        p.add_argument("--tool", help="sti til realesrgan-ncnn-vulkan")
        p.add_argument("--model", default="realesrgan-x4plus")
        p.add_argument("--cmd", help="kommandomal for metoden cmd, med {inn} {ut} {skala}")
        p.add_argument("--extract", default=str(root / "work" / "extract"))

    p = sub.add_parser("build-mod", help="lag mod-mappe for HD-motoren")
    up(p)
    p.add_argument("--name", default="hd")
    p.add_argument("--mods", default=str(root / "mods"))
    p.add_argument("--out", help="overstyr målmappe")
    p.add_argument("--rooms", help="for eksempel 22,24 eller 20-30, eller 'ingen' (standard: alle)")
    p.add_argument("--egne", help="mappe med egne HD-bilder (rooms/, objects/, costumes/) som brukes i stedet. Egne "
                   "objektbilder tas med også for rom utenfor --rooms, men da uten bakgrunn, og egne kostymeruter "
                   "tas med for alle kostymer")
    p.add_argument("--uten-objekter", action="store_true", help="bare bakgrunner")
    p.add_argument("--kostymer", help="kostyme-ID-er der rutene uten eget bilde skaleres automatisk, for eksempel "
                   "14-18, eller 'alle'")
    p.add_argument("--filmer", help="filmer som skal skaleres, for eksempel SQ1,TRAM1, eller 'alle' (tar mye plass)")
    p.add_argument("--san", default=str(root / "work" / "san"), help="utdata fra zakhd san")
    p.add_argument("--uten-skrift", action="store_true", help="uten HD-skriften (Exo 2) for teksten")
    p.add_argument("--kun-ui", action="store_true", help="bare ikonene til verbhjulet og bildene til inventaret "
                   "(fra grafikk/ og --egne), uten rom og figurer; trenger ikke uttrekket")

    p = sub.add_parser("compare", help="sammenlign oppskaleringsmetoder på ett rom")
    up(p)
    p.add_argument("--room", type=int, required=True)
    p.add_argument("--methods", default="nearest,lanczos,lanczos-sharp")
    p.add_argument("--out")

    p = sub.add_parser("gpt-pakke", help="lag jobber for ChatGPT (referansebilder og prompter)")
    p.add_argument("--extract", default=str(root / "work" / "extract"))
    p.add_argument("--ut", default=str(root / "work" / "gpt"))
    p.add_argument("--rooms", help="for eksempel 22,24 eller 20-30 (standard: alle)")
    p.add_argument("--notater", default=str(root / "docs" / "gpt-romnotater.csv"), help="CSV med rom,notat")
    p.add_argument("--figurer", default="pilot",
                   help="figurark: pilot (standard, arkene i FIG_PILOT i figur.py, tom til stilpiloten er valgt), alle, ingen, eller "
                        "kostyme-ID-er som 14,18 eller 14-20 (alle arkene for dem)")
    p.add_argument("--figurliste", default=str(root / "docs" / "figurer.csv"),
                   help="CSV med kostymene (navn og rekkefølge for figurarkene)")

    p = sub.add_parser("gpt-inn", help="ta imot bilder fra ChatGPT, sjekk dem og lag HD-rom")
    p.add_argument("--extract", default=str(root / "work" / "extract"))
    p.add_argument("--fra", default=str(root / "work" / "gpt"))
    p.add_argument("--ut", default=str(root / "work" / "gpt-ferdig"))
    p.add_argument("--sigma", type=float, default=6.0, help="hvor grove fargene som låses til originalen er (HD-piksler)")
    p.add_argument("--styrke", type=float, default=1.0, help="fargelås 0 til 1 (0 = av)")
    p.add_argument("--bare-godkjente", action="store_true", help="ikke bruk jobber med status sjekk")
    p.add_argument("--avvisninger", default=str(root / "docs" / "gpt-avvisninger.csv"),
                   help="CSV med jobb,sha256_resultat,grunn,forslag for bilder avvist ved gjennomsyn")

    p = sub.add_parser("gpt-ordre", help="skriv ORDRE.md med neste jobber til ChatGPT")
    p.add_argument("--fra", default=str(root / "work" / "gpt"))
    p.add_argument("--stil", default=str(root / "work" / ".gpt-gren" / "stil"), help="mappe med stilankere")
    p.add_argument("--antall", type=int, default=10)
    p.add_argument("--beskjed", action="append", help="beskjed til ChatGPT (kan gjentas)")
    p.add_argument("--oppgaver", default=str(root / "docs" / "gpt-kodeoppgaver.md"),
                   help="kodeoppgaver som tas med i ORDRE.md (tom streng for ingen)")

    p = sub.add_parser("myke-figurer", help="ta inn figurarkene i glatt stil som myke kostymeruter (_hd.png)")
    p.add_argument("--gren", default=str(root / "work" / ".gpt-gren"), help="arbeidsgrenen gpt-arbeid (sjekket ut)")
    p.add_argument("--extract", default=str(root / "work" / "extract"))
    p.add_argument("--ut", default=str(root / "work" / "gpt-ferdig"))
    p.add_argument("--jobb", help="bare disse arkene, for eksempel fig014_01,fig014_05")
    p.add_argument("--forhandsvisning", default=str(root / "work" / "gpt" / "forhandsvisning"),
                   help="mappe for kontaktark myk_<jobb>.png (tom streng for ingen)")
    p.add_argument("--avvisninger", default=str(root / "docs" / "gpt-avvisninger.csv"),
                   help="avviste ark (jobb, sha256_resultat, status avvist) tas ikke inn")

    a = ap.parse_args(argv)
    return {"info": cmd_info, "extract": cmd_extract, "build-mod": cmd_build_mod,
            "compare": cmd_compare, "gpt-pakke": cmd_gpt_pakke,
            "gpt-inn": cmd_gpt_inn, "gpt-ordre": cmd_gpt_ordre, "myke-figurer": cmd_myke_figurer,
            "grafikkliste": cmd_grafikkliste}[a.command](a)


if __name__ == "__main__":
    sys.exit(main())
