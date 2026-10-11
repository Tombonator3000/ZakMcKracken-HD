# Zak McKracken HD på GitHub Pages

Planen er den samme som for The Dig: en nettside som går rett inn i spillet, på PC og mobil, med bare den kompilerte ScummVM-motoren, HD-patchen, brukergrensesnittet, ScummVM sine temaer og tilhørende kildekode. Spillfiler og HD-bilder skal aldri inn i nettsidepakken.

Utgaven er den engelske FM-Towns-utgaven av *Zak McKracken and the Alien Mindbenders*: ScummVM-ID `zak`, variant FM-TOWNS, SCUMM v3 med 256 farger.

## Status

| Del | Status |
| --- | --- |
| Nettsiderepoet `Tombonator3000/ZakMcKracken-HD-Web` | Finnes ikke ennå |
| Nettsidekoden i `engine/pages` | Tilpasset Zak (filfilter, spill-ID `zak`, repo, valgfri HD-pakke). 18 nodetester består. Ikke bygget og ikke testet i nettleser |
| Motoren for nettleseren (`engine/build-web.sh`, `engine/build-pages.py`) | Ikke bygget for Zak. `build-web.sh` bygger nå libFLAC og slår på FLAC, men det er ikke kjørt (Emscripten finnes ikke der dette ble skrevet) |
| HD-grafikk | Ikke slått på for Zak (se under). Ingen HD-mod i `hd-mod` |

Alt under beskriver hvordan siden skal virke, etter The Dig sin nettside. Ingenting av det er prøvd med Zak i nettleser.

`./spill.sh --nettleser` er en egen løsning som kjører nettleserversjonen på localhost fra filene på maskinen (se [SPILLTEST.md](SPILLTEST.md)).

## Det som mangler for HD

HD-patchen (DigHD) er ikke slått på for Zak. `DigHD::create` godtar bare `GID_DIG` og `GID_SAMNMAX`. FM-Towns-spillene tegner gjennom ScummVMs `towns_drawStripToScreen` med 16-bits farger (640 x 480 med tekstlaget), ikke gjennom den vanlige `drawStripToScreen` som patchen bruker, så porten er et eget arbeid. Til den er gjort:

- Spillet vises med originalgrafikken. En HD-pakke trengs ikke, og siden starter uten.
- Lerretet: The Dig sin side venter på loggen `DigHD: screen` før den sender en resize, slik at lerretet får riktig størrelse (Known Issues i `dists/emscripten/README.md` i ScummVM), og fjerner statuslinjen. Den linjen kommer ikke for Zak. Sidene (`engine/pages/player.mjs` og `engine/web/index.html`) bruker derfor også den første spillfilen motoren ber om etter `00.LFL` som tegn: ScummVM leser bare indeksen `00.LFL` før spillet setter opp skjermen, og rommene og tegnsettene etterpå. Rekkefølgen er sjekket med motoren på maskinen (gdb på `initGraphics` og filåpningene), ikke i nettleser. Med `?uten-lyd` viser ScummVM meldingen om manglende CD-spor før den første romfilen leses, så resize kommer først etter OK.
- `?rom`, `?klassisk`, `?gult`, testkrokene (`DIGHD_*`), Ctrl+H og Ctrl+Shift+H gjør ingenting.

## Spille

Siden går rett inn i spillet, som originalen. Det er ingen knapper eller menyer rundt spillet. Grafikkvalget skal ligge i spillets egen meny når HD er på.

Første gang ber siden om en lesenøkkel til repoet `Tombonator3000/ZakMcKracken-HD`, der spillet (grenen `spilldata`) og HD-pakken (grenen `hd-mod`) ligger. Nøkkelen lages på https://github.com/settings/personal-access-tokens/new:

- Repository access: Only select repositories, ZakMcKracken-HD
- Permissions: Contents, Read-only
- Utløpsdato etter eget valg

Nøkkelen lagres bare i nettleseren (IndexedDB). Alle Pages-sider under tombonator3000.github.io deler opprinnelse og dermed nettleserlagring, så nøkkelen skal bare ha lesetilgang til dette ene repoet.

Filene hentes fra GitHub med nøkkelen når spillet trenger dem, og lagres i nettleseren etter git-blob-ID. Ved hver start hentes fillisten for de to grenene på nytt, så ny HD-grafikk i `hd-mod` kommer med av seg selv, og bare filene som er endret, hentes. Grenen `hd-mod` finnes ikke ennå. GitHub svarer da 404 for den, og siden starter med `spilldata` alene (en nøkkel uten tilgang får 404 allerede for `spilldata` og stopper der). Ingen spillfil eller HD-fil ligger på nettsiden eller sendes dit. Forespørslene går bare til api.github.com for repoet.

Spillfilene (i `game/` i grenen `spilldata`, med `game/SHA256SUMS`):

| Fil | Størrelse | Merknad |
| --- | --- | --- |
| `00.LFL` | 7 520 byte | Indeksen |
| `01.LFL` til `59.LFL` | 16 551 til 172 389 byte, 4,3 MB i alt | Rommene, med skript, kostymer og lyder |
| `98.LFL`, `99.LFL` | 2 042 byte hver | Tegnsettene |
| `Track1.fla` til `Track21.fla` | 2 461 860 til 24 770 455 byte, 325 713 399 byte i alt | CD-musikken i FLAC |

Totalt 83 filer på 330 040 888 byte (315 MiB). Ingen fil er over 90 MB, så ingen ligger i deler (Sam & Max hadde `MONSTER.SOU.001` og `.002`; den sammensetningen er tatt ut). Filfilteret i `engine/pages/local-files.mjs` godtar `NN.LFL` og `TRACKN.FLA` (store og små bokstaver), og krever `00.LFL`, `98.LFL` og `99.LFL`. Andre filer i mappen, som `SHA256SUMS`, tas ikke med.

Musikken: ScummVM spiller CD-sporene fra `TrackN.fla` bare når motoren er bygget med FLAC. Emscripten har ikke libFLAC, og uten den slår ScummVM sin configure av FLAC uten å si fra. `engine/build-web.sh` bygger derfor libFLAC 1.4.3 (kildearkivet fra downloads.xiph.org, kontrollert med SHA-256) til `dists/emscripten/libs/build` i ScummVM-kilden, gir configure `--enable-flac --with-flac-prefix=...`, og stopper hvis `USE_FLAC` ikke kom med. Lydeffektene kommer fra ScummVMs FM-Towns-lydemulering, ikke MIDI. Sidene stopper ScummVM sin forespørsel om Web MIDI, som Zak ikke bruker.

Sporene hentes ett og ett første gang de spilles, og spillet venter mens det skjer (siden viser fremdriften for filer over 4 MB). Hvert spor som har spilt, blir liggende i minnet mens spillet kjører. Med `?uten-lyd`, og på enheter som melder mindre enn 4 GB minne, tas sporene ikke med. ScummVM viser da en melding ved start om at CD-sporene mangler (OK lukker den), og spillet går uten musikk. Det er sett med motoren på maskinen, ikke i nettleser.

Skjermen: FM-Towns-utgaven har 320 x 240 punkter. Med høydekorrigering på (standard i ScummVM) viser Zak en melding om det ved hver start, så sidene starter med `--no-aspect-ratio` og `aspect_ratio=false` i `scummvm.ini`. Med motoren på maskinen starter spillet rett inn i tittelbildet med disse valgene.

Ikke målt: hvor mye som lastes ned før spillet kan vise noe, hvor mye minne siden bruker med musikken, og om musikken spilles i nettleseren.

Fra The Dig sin nettside, ventet å virke likt (ikke testet):

- **Fullskjerm:** nettlesere tillater fullskjerm bare etter et klikk eller en tast, så spillet går i fullskjerm ved det første klikket eller tastetrykket.
- **Tegning:** med WebGL. Uten WebGL brukes ScummVMs programvaretegning (`--gfx-mode=surfacesdl`), og `?programvare` velger den med vilje.
- **Meny:** F5 åpner spillets meny (lagre og laste). Raden HD Graphics og Ctrl+H krever at patchen er portet.
- **Mobil og nettbrett** (`engine/pages/touch.mjs`): trykk er klikk, dra flytter pekeren, hold fingeren i ro et halvt sekund for høyreklikk, to fingre åpner spillets meny (F5), tre fingre gir Esc. Første trykk gir fullskjerm.
- **Nett:** mistes kontakten med GitHub mens spillet trenger en fil, venter spillet, og siden prøver igjen til filen er kommet. Bare en nøkkel GitHub avviser, stopper.
- **Valg i adressen:** `?ny-nokkel` (be om ny nøkkel), `?programvare`, `?uten-lyd`, `?rom=N` (1 til 59), `?klassisk`, `?gult` og testkrokene fra motoren (`DIGHD_*`, se [HD-MOTOR.md](HD-MOTOR.md)). `?rom`, `?klassisk`, `?gult` og testkrokene virker ikke før patchen er portet.
- **Uten nøkkel:** spillet kan kjøre fra mapper på maskinen (lenken under nøkkelfeltet): spillmappen med `00.LFL` til `59.LFL`, `98.LFL`, `99.LFL` og `Track1.fla` til `Track21.fla`. HD-mappen (`mod.json`, `rooms`, vanligvis `mods/gpt`) er valgfri og velges før spillmappen, for spillet starter så snart spillmappen er valgt. Filene kopieres til nettleseren.
- **Lagring:** lagrede spill og scummvm.ini ligger i nettleserens lagring (IDBFS) og blir der selv om spillfilene slettes. Nettlesere kan slette lokal lagring ved lite ledig plass, og privatmodus kan gjøre lagringen midlertidig.

## Bygge fra kildekode

Krever git, make, Python 3, pkg-config, tar, xz og zip. Fra prosjektroten:

```sh
JOBS=2 engine/build-web.sh
python3 engine/build-pages.py
```

ScummVM er låst til `engine/SCUMMVM_COMMIT`. Emscripten 4.0.10 med Node, Clang og SDL3, libpng og zlib hentes til `engine/emsdk`. libFLAC 1.4.3 hentes og bygges til `engine/scummvm-web/dists/emscripten/libs`. Byggeskriptet bruker ScummVM sin konfigurasjon, bare SCUMM-motoren er med, og prosjektets HD-patch legges på. Ingen av stegene henter spillet eller HD-pakken.

Nettsiden havner i `out/pages`. `source.tar.gz` inneholder den patchede ScummVM-kilden, HD-patchen, kildearkivet til libFLAC, nettleserkoden og byggeoppskriften. Motoren og HD-patchen er GPL-3.0-or-later. libFLAC er BSD-lisensiert, og lisensen legges i `licenses/COPYING.FLAC`. ScummVM sin COPYRIGHT og lisensfilene skal følge nettsiden.

Ikke kjørt for Zak. Kontrollert der dette ble skrevet: `bash -n` på skriptet, og at libFLAC-stegene (configure med de samme valgene, `make -C src/libFLAC`, installasjon av biblioteket og overskriftene) gir `libFLAC.a` og `FLAC/*.h` med vanlig gcc. Ikke kontrollert med Emscripten.

## Publisere

Publiser bare innholdet i `out/pages`, i det egne repoet `Tombonator3000/ZakMcKracken-HD-Web`, som bare skal ha motoren (GPL). Repoet finnes ikke ennå.

En arbeidsflyt med `actions/upload-pages-artifact` og `actions/deploy-pages` kan publisere pakken. Nettsiden bruker relative adresser til motoren, så prosjektprefikset på GitHub Pages virker. Filpakkeren bruker en navneliste for ScummVM-temaene og kopierer aldri `data/games` fra distribusjonen. Kontroller `build.json` og filene før publisering.

## Verifisering

```sh
node --test engine/pages/tests/*.test.mjs
python3 -m http.server 8000 --bind 127.0.0.1 --directory out
```

Åpne http://127.0.0.1:8000/pages/ for å teste prosjektprefikset. Kontroller mappevalg, omlasting, lagring og musikk med spillfilene fra `game/`, at lerretet får riktig størrelse uten DigHD, og HD og HD-bryteren når patchen er portet. Spillfiler og HD-bilder skal ikke være tilgjengelige som HTTP-ressurser. En full gjennomspilling og mobiltest må rapporteres for seg.

Bare nodetestene er kjørt for Zak (18 bestått).
