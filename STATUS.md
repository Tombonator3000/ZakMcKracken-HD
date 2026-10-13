# Status

Oppdatert 13. oktober 2026.

## Kort

Repoet har samme oppsett som Sam & Max HD og The Dig HD Remake, tilpasset Zak McKracken (FM-Towns). Spillfilene ligger i `spilldata`, ScummVM med HD-patchen og FLAC bygger og kjører spillet, all originalgrafikk er trukket ut, alle skript er dekompilert, og listen over grafikken som skal byttes ut finnes. HD-motoren er ikke portet til Zak, så spillet vises med originalgrafikken. Ingen HD-grafikk ennå.

## Det som virker

| Del | Hva | Hvordan det er testet |
| --- | --- | --- |
| Spillfiler | 83 filer (00.LFL til 59.LFL, 98.LFL, 99.LFL, Track1.fla til Track21.fla) i `spilldata`, hentes og sjekkes med `tools/hent_spilldata.sh` | Størrelsene sjekket mot Drive ved nedlasting. Fersk klone og `tools/hent_spilldata.sh` 11. oktober: 83 filer, SHA-256 stemmer for alle |
| Utgave | Engelsk FM-Towns | MD5 av 00.LFL funnet i ScummVMs `scumm-md5.h` ved c9091321 |
| Motor | ScummVM c9091321 med `engine/patches/0001-dighd-hd-grafikk.patch` (Sam & Max sin, uendret), `0002-verbhjul.patch` og FLAC | `engine/build.sh` her 11. oktober. Zak startet fra `game/` uten skjerm i 30 sekunder: `zak`, FM-TOWNS, SCUMM 3, riktig MD5, rommene 49, 1, 47, 9 og 50 lest. Ikke spilt med skjerm og lyd |
| HD i motoren | Ikke portet. DigHD er av for Zak | `docs/HD-MOTOR.md` sier hva som må til |
| Pipeline | `zakhd info`, `zakhd extract`, `zakhd grafikkliste`, `zakhd build-mod` | `pytest`: 36 bestått (34 uten spillfiler), med nye tester for stripekodekene, BM med z-plan og v3-kostymer. `build-mod --method nearest --kostymer 1`: 58 rom, 585 objektbilder, 51 ruter |
| Uttrekk | 58 rombakgrunner, 585 objektbilder, 847 kostymeruter fra 40 kostymer, 2 tegnsett, med rooms.json, costumes.json og fonts.json | Kjørt mot spillfilene 11. oktober, 0 feil, omtrent 6 sekunder. Kontaktark over alle rom, rom 1 med alle objektene på plass, og største rute fra hvert kostyme sett på. Ikke sammenlignet piksel for piksel med motoren |
| Grafikkliste | `docs/grafikkliste.csv` (685 rader) og `docs/rom-oversikt.csv` (58 rom) | Laget med `zakhd grafikkliste` fra uttrekket og `work/skript/objekter.tsv` |
| Skript | `tools/bygg_descumm.sh` og `tools/dekompiler_skript.py`: 1094 skript til `work/skript` | 1094 uten feil (descumm `-3 -z`), kjørt på nytt fra main 12. oktober med like filer som 11. oktober. Verbene, inventaret og skjermdelingen lest ut og brukt i `docs/GRENSESNITT.md` og `docs/VERBHJUL.md` |
| Skriptoversikt | `tools/skriptoversikt.py`: ROM.md, REPLIKKER.md, rom-koblinger.tsv og kostymer-i-rom.tsv i `work/skript` | Kjørt 12. oktober: 59 rom, 1309 replikker, 123 faste rombytter (43 gjennom variabler), 25 kostymebruk. Stikkprøver lest mot skriptfilene (rom 1, globalt skript 4) |
| Romnavn | `docs/romnavn.csv`: beskrivelse av alle 58 rom med kilde (objektnavn, replikker, bilde) | Skrevet for hånd 12. oktober; rom 48 og 56 er ikke avklart. `zakhd grafikkliste` tar dem inn |
| Verbhjulet | `engine/patches/0002-verbhjul.patch`: dynamisk urskive med høyst fire ikoner (verb med lik kode slått sammen, Open/Close og Turn on/off etter tilstand, regler for hånd for 19 objekter, tabellen `verbhjul_zak.h` fra `tools/verbhjul_dynamisk.py`), portretter for figurbytte nederst til høyre, høyreklikk eller hold og dra, to objekter, avbrudd, Ctrl+W. Midlertidige ikoner. Se `docs/VERBHJUL.md` | `tools/verbhjul_test.sh` uten skjerm 13. oktober, med motoren fra `engine/build.sh`: originalpanelet og hjulet gir de samme 11 setningene i rom 1 (blant dem Close på en åpen skuff, kommoden med regel for hånd og bytte til Annie med portrettet mot F2), venting og avbrudd virker, og alle 337 reglene leses riktig. Figurbyttet er testet med variabler satt av testen, ikke der Switch kommer i spillet. «Alle verb», Esc, Ctrl+W og hjulet uten dynamisk utvalg prøvd for hånd uten skjerm. Ikke prøvd med skjerm, i nettleseren, på mobil, i butikken, teleporten eller med dyr, og reglene for hånd er ikke prøvd i spillet utenom kommoden |
| Indeksverktøy | `tools/indeks_info.py game/00.LFL` | Kjørt mot spillfilene |
| `./spill.sh` | Henter spillfiler og `hd-mod`, bygger motoren og starter spillet | Ikke kjørt i sin helhet her; delene (henting, bygging, `engine/run.sh`) er kjørt hver for seg |
| Nettsidekoden | `engine/pages` tilpasset Zak (filfilter for LFL og FLA, ingen deler, lerretet venter ikke på DigHD) | `node --test`: 18 bestått. Ikke bygget for nettleser |
| Linux-pakken | `tools/pakke_linux.sh` lager pakken uten HD-mod (ZakHD-x86_64.AppImage) | AppDir laget her og startet uten skjerm: spillet kjente igjen utgaven og kjørte i 60 sekunder. AppImage og arbeidsflyten er ikke kjørt |
| Grener | `spilldata`, `hd-mod` (tom) og `gpt-arbeid` (uten jobber) | Pushet 11. oktober |

## Ikke portet eller ikke testet

- HD-motoren for Zak: FM-Towns-tegningen går forbi krokene. Se `docs/HD-MOTOR.md`.
- Verbhjulet er bygget med midlertidige ikoner og portretter og testet uten skjerm i rom 1. Mangler: navnet under pekeren når hjulet er lukket, F5-menyen, HD-tegning, de tegnede ikonene og portrettene, og prøving med skjerm og på mobil. Taster og klikk i de tre eller fire rammene hjulet sender klikk, går tapt. Lagringen av valget er ikke bekreftet (ScummVM skrev ingen scummvm.ini i testmiljøet).
- `tools/romtest.sh` og `engine/test.sh` trenger DigHD; test.sh sjekker til da bare at spillet starter.
- Kostymefargene i RGBA-bildene er fra rommet kostymet ligger i; spillet kan vise andre farger.
- Promptene i `gpt.py` og `figur.py` er grovt tilpasset Zak, ikke prøvd. Bestillingen er ikke aktiv før stilpiloten.
- Nettsiden: eget repo finnes ikke, ikke bygget eller prøvd.
