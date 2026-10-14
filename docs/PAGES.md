# Zak McKracken HD på GitHub Pages

**https://tombonator3000.github.io/ZakMcKracken-HD/**

En nettside som går rett inn i spillet, som for The Dig, med bare den kompilerte ScummVM-motoren, patchene, brukergrensesnittet, ScummVM sine temaer og tilhørende kildekode. Spillfiler og HD-bilder skal aldri inn i nettsidepakken. Nettleseren henter spillet fra dette repoet med eierens lesenøkkel.

Utgaven er den engelske FM-Towns-utgaven av *Zak McKracken and the Alien Mindbenders*: ScummVM-ID `zak`, variant FM-TOWNS, SCUMM v3 med 256 farger.

## Status

| Del | Status |
| --- | --- |
| Nettsiden | Publisert 14. oktober 2026 fra dette repoet med arbeidsflyten `.github/workflows/pages.yml` (Pages-kilden er GitHub Actions). Ikke noe eget nettsiderepo |
| Motoren for nettleseren | Bygget i Actions med `engine/build-web.sh`: Emscripten 4.0.10, libFLAC 1.4.3, patchene 0001 og 0002 og nettleserpatchene i `engine/patches-web` (fra Dig-HD-Web). `scummvm.wasm` er 11,9 MB |
| Nettsidekoden i `engine/pages` | Tilpasset Zak. 20 nodetester består |
| Spilt i nettleser | 14. oktober i Chromium (Playwright, SwiftShader) mot den publiserte siden, med spillfilene fra repoet: tittelbildet, introen med CD-musikk, rommet til Zak, klikk for å gå og verbhjulet. Se Verifisering |
| HD-grafikk | Ikke slått på for Zak (se under). Ingen HD-mod ennå |

Det som ikke er prøvd i nettleser med Zak, står under Verifisering.

`./spill.sh --nettleser` er en egen løsning som kjører nettleserversjonen på localhost fra filene på maskinen (se [SPILLTEST.md](SPILLTEST.md)).

## Det som mangler for HD

HD-patchen (DigHD) er ikke slått på for Zak. `DigHD::create` godtar bare `GID_DIG` og `GID_SAMNMAX`. FM-Towns-spillene tegner gjennom ScummVMs `towns_drawStripToScreen` med 16-bits farger (640 x 480 med tekstlaget), ikke gjennom den vanlige `drawStripToScreen` som patchen bruker, så porten er et eget arbeid. Til den er gjort:

- Spillet vises med originalgrafikken. En HD-pakke trengs ikke, og siden starter uten.
- Lerretet: The Dig sin side venter på loggen `DigHD: screen` før den sender en resize, slik at lerretet får riktig størrelse (Known Issues i `dists/emscripten/README.md` i ScummVM), og fjerner statuslinjen. Den linjen kommer ikke for Zak. Sidene (`engine/pages/player.mjs` og `engine/web/index.html`) bruker derfor også den første spillfilen motoren ber om etter `00.LFL` som tegn: ScummVM leser bare indeksen `00.LFL` før spillet setter opp skjermen, og rommene og tegnsettene etterpå. Rekkefølgen er sjekket med motoren på maskinen (gdb på `initGraphics` og filåpningene), ikke i nettleser. Med `?uten-lyd` viser ScummVM meldingen om manglende CD-spor før den første romfilen leses, så resize kommer først etter OK.
- `?rom`, `?klassisk`, `?gult`, testkrokene (`DIGHD_*`), Ctrl+H og Ctrl+Shift+H gjør ingenting.

## Spille

Siden går rett inn i spillet, som originalen. Det er ingen knapper eller menyer rundt spillet. Grafikkvalget skal ligge i spillets egen meny når HD er på.

Første gang ber siden om en lesenøkkel til repoet `Tombonator3000/ZakMcKracken-HD`, der spillet og HD-pakken ligger. Nøkkelen lages på https://github.com/settings/personal-access-tokens/new:

- Repository access: Only select repositories, ZakMcKracken-HD
- Permissions: Contents, Read-only
- Utløpsdato etter eget valg

Nøkkelen lagres bare i nettleseren (IndexedDB). Alle Pages-sider under tombonator3000.github.io deler opprinnelse og dermed nettleserlagring, så nøkkelen skal bare ha lesetilgang til dette ene repoet.

Filene hentes fra GitHub med nøkkelen når spillet trenger dem, og lagres i nettleseren etter git-blob-ID. Hvor de ligger (`SOURCES` i `engine/pages/local-files.mjs`):

| Hva | Først | Ellers |
| --- | --- | --- |
| Spillet | `game/` i `main` (etter flettingen Tom vil gjøre) | `game/` i grenen `spilldata` (slik det er nå) |
| HD-pakken | `mods/gpt/` i `main` | grenen `hd-mod` |

Ved hver start hentes fillisten for `main` på nytt, og grenene bare når `main` ikke har filene. Ny HD-grafikk kommer derfor med av seg selv, og bare filene som er endret, hentes. HD-pakken brukes bare når den har `mod.json`; `hd-mod` har nå bare README og SHA256SUMS, og siden starter da med spillet alene. Før 14. oktober stoppet siden på det med «Velg HD-mappen som inneholder mod.json og rooms». En nøkkel uten tilgang får 404 allerede for `main` og stopper der. Ingen spillfil eller HD-fil ligger på nettsiden eller sendes dit. Forespørslene går bare til api.github.com for repoet.

Spillfilene (i `game/`, med `game/SHA256SUMS`):

| Fil | Størrelse | Merknad |
| --- | --- | --- |
| `00.LFL` | 7 520 byte | Indeksen |
| `01.LFL` til `59.LFL` | 16 551 til 172 389 byte, 4,3 MB i alt | Rommene, med skript, kostymer og lyder |
| `98.LFL`, `99.LFL` | 2 042 byte hver | Tegnsettene |
| `Track1.fla` til `Track21.fla` | 2 461 860 til 24 770 455 byte, 325 713 399 byte i alt | CD-musikken i FLAC |

Totalt 83 filer på 330 040 888 byte (315 MiB). Ingen fil er over 90 MB, så ingen ligger i deler (Sam & Max hadde `MONSTER.SOU.001` og `.002`; den sammensetningen er tatt ut). Filfilteret i `engine/pages/local-files.mjs` godtar `NN.LFL` og `TRACKN.FLA` (store og små bokstaver), og krever `00.LFL`, `98.LFL` og `99.LFL`. Andre filer i mappen, som `SHA256SUMS`, tas ikke med.

Musikken: ScummVM spiller CD-sporene fra `TrackN.fla` bare når motoren er bygget med FLAC. Emscripten har ikke libFLAC, og uten den slår ScummVM sin configure av FLAC uten å si fra. `engine/build-web.sh` bygger derfor libFLAC 1.4.3 (kildearkivet fra downloads.xiph.org, kontrollert med SHA-256) til `dists/emscripten/libs/build` i ScummVM-kilden, gir configure `--enable-flac --with-flac-prefix=...`, og stopper hvis `USE_FLAC` ikke kom med. Lydeffektene kommer fra ScummVMs FM-Towns-lydemulering, ikke MIDI. Sidene stopper ScummVM sin forespørsel om Web MIDI, som Zak ikke bruker.

Sporene hentes ett og ett første gang de spilles, og spillet venter mens det skjer (siden viser fremdriften for filer over 4 MB). Hvert spor som har spilt, blir liggende i minnet mens spillet kjører. I testen 14. oktober hentet introen sporene 5, 8 og 14 (9,5, 18,3 og en til), og motoren leste dem uten feil. Om musikken høres riktig, er ikke sjekket med ører. Med `?uten-lyd`, og på enheter som melder mindre enn 4 GB minne, tas sporene ikke med. ScummVM viser da en melding ved start om at CD-sporene mangler (OK lukker den), og spillet går uten musikk. Det er sett med motoren på maskinen, ikke i nettleser.

Skjermen: FM-Towns-utgaven har 320 x 240 punkter. Med høydekorrigering på (standard i ScummVM) viser Zak en melding om det ved hver start, så sidene starter med `--no-aspect-ratio` og `aspect_ratio=false` i `scummvm.ini`. Med motoren på maskinen starter spillet rett inn i tittelbildet med disse valgene.

Målt 14. oktober: før tittelbildet hentes motoren (12 MB) og 00.LFL, 49.LFL og 99.LFL; til rommet til Zak etter introen er det 26 kall til GitHub og omtrent 30 MB, mest musikk. Ikke målt: hvor mye minne siden bruker med musikken over tid.

Fra The Dig sin nettside, ventet å virke likt (ikke testet med Zak der ikke annet står):

- **Fullskjerm:** nettlesere tillater fullskjerm bare etter et klikk eller en tast, så spillet går i fullskjerm ved det første klikket eller tastetrykket.
- **Tegning:** med WebGL. Uten WebGL brukes ScummVMs programvaretegning (`--gfx-mode=surfacesdl`), og `?programvare` velger den med vilje.
- **Meny:** F5 åpner spillets meny (lagre og laste). Raden HD Graphics og Ctrl+H krever at patchen er portet.
- **Mobil og nettbrett** (`engine/pages/touch.mjs`): trykk er klikk, dra flytter pekeren, hold fingeren i ro et halvt sekund for høyreklikk, to fingre åpner spillets meny (F5), tre fingre gir Esc. Første trykk gir fullskjerm. Prøvd 14. oktober bare som Pixel 7 i Chromium på stående skjerm: siden og introen kom opp, men SwiftShader på to kjerner var for treg til å nå spillet. Ikke prøvd på en ekte telefon.
- **Fullskjerm og musen:** nettleserpatchen `engine/patches-web/0002-browser-canvas-coordinate-sync.patch` holder OpenGL-visningen og musekoordinatene i takt med lerretet, så klikk treffer i fullskjerm (rettet i Dig-HD-Web 12. oktober). Ikke prøvd i fullskjerm med Zak.
- **Ny motor:** `scummvm.js` og `scummvm.wasm` hentes med sjekksummen fra `build.json` i adressen, så en ny motor ikke blandes med en gammel fra nettleserens hurtiglager (fra Dig-HD-Web).
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

ScummVM er låst til `engine/SCUMMVM_COMMIT`. Emscripten 4.0.10 med Node, Clang og SDL3, libpng og zlib hentes til `engine/emsdk`. libFLAC 1.4.3 hentes og bygges til `engine/scummvm-web/dists/emscripten/libs`. Byggeskriptet bruker ScummVM sin konfigurasjon, bare SCUMM-motoren er med, og patchene legges på i rekkefølge: `engine/patches` (0001 DigHD, 0002 verbhjulet) og så `engine/patches-web` (HTTP-filsystemet og lerretet, se README der). Ingen av stegene henter spillet eller HD-pakken. Proxyen i Claude-økten stopper nedlastingen av SDL3-porten, så bygget kjøres i Actions.

Nettsiden havner i `out/pages` (272 MB, 47 filer; `source.tar.gz` er 263 MB av det og lastes bare ned av den som vil ha kildekoden). `engine/build-pages.py` sjekker først at hele patchstakken er lagt på og ingenting annet er endret (fra Dig-HD-Web). `source.tar.gz` inneholder den patchede ScummVM-kilden med filene patchene legger til (`dighd.*`, `verbhjul.*`, `verbhjul_zak.h`), alle patchene, kildearkivet til libFLAC, nettleserkoden, testene og byggeoppskriften. Før 14. oktober manglet verbhjulet og 0002 i arkivet. Motoren og patchene er GPL-3.0-or-later. libFLAC er BSD-lisensiert, og lisensen legges i `licenses/COPYING.FLAC`. ScummVM sin COPYRIGHT og lisensfilene følger nettsiden.

Kjørt i Actions 14. oktober (pages.yml, run 38573454225): byggingen tok 4,5 minutter, `USE_FLAC` kom med, og testen av HTTP-filsystemet i Wasm besto (90 000 oppslag blant 30 000 filer).

## Publisere

`.github/workflows/pages.yml` bygger og publiserer når noe under `engine/`, `docs/PAGES.md` eller arbeidsflyten endres i `main`, og kan startes for hånd (Actions, pages, Run workflow). Den sjekker ut bare `engine/`, `docs/PAGES.md` og `tools/sjekk_patcher.py`, så spillfilene lastes aldri ned i bygget, og kjører nodetestene, patchtestene, byggingen, testen av HTTP-filsystemet, pakkingen og en sjekk av at pakken ikke har LFL-, FLA- eller PNG-filer. Bare innholdet i `out/pages` publiseres, med `actions/upload-pages-artifact` og `actions/deploy-pages`. Ingenting skrives til en gren. Nettsiden bruker relative adresser til motoren, så prosjektprefikset `/ZakMcKracken-HD/` virker. Filpakkeren bruker en navneliste for ScummVM-temaene og kopierer aldri `data/games` fra distribusjonen.

Pages fra dette repoet krever at repoet er offentlig (eller GitHub Pro). Gjøres repoet privat, slutter siden å virke. Da kan arbeidsflyten flyttes uendret til et eget offentlig repo med bare `engine/` (som Dig-HD-Web), og `REPO` i `local-files.mjs` peker fortsatt hit.

## Verifisering

```sh
node --test engine/pages/tests/*.test.mjs
python3 -m http.server 8000 --bind 127.0.0.1 --directory out
```

Åpne http://127.0.0.1:8000/pages/ for å teste prosjektprefikset. Kontroller mappevalg, omlasting, lagring og musikk med spillfilene fra `game/`, at lerretet får riktig størrelse uten DigHD, og HD og HD-bryteren når patchen er portet. Spillfiler og HD-bilder skal ikke være tilgjengelige som HTTP-ressurser. En full gjennomspilling og mobiltest må rapporteres for seg.

14. oktober, mot den publiserte siden: `engine/pages/tests` 20 bestått, `engine/tests/test-build-pages.py` 4 bestått, og `tools/nettsidetest.py` i Chromium 141 (Playwright, `--use-angle=swiftshader`, 1280 x 800) med en dummy-nøkkel, der kallene til api.github.com og github.io gikk gjennom proxyen i økten:

- Nøkkelsiden kom opp; etter nøkkelen leste siden `main`, `spilldata` og `hd-mod` (ingen mod.json) og startet `zak` uten feil i konsollen.
- Tittelbildet og introen på kontoret til The National Inquisitor med tekst, og CD-sporene 5, 8 og 14 hentet. Lerretet fikk riktig størrelse (1280 x 800) uten DigHD.
- Etter introen (rundt 120 til 175 sekunder i SwiftShader) var Zak i soverommet med «Walk to» og billetten i inventaret. Klikk på gulvet fikk Zak til å gå dit, klikk på akvariet ga «Walk to Sushi in fish bowl» og Zak gikk dit. Høyreklikk holdt over telefonsvareren åpnet verbhjulet med Off og On og navnet «answering machine» der pekeren var.
- Siden hentet bare motor, temaer og nettsidekode fra github.io. Spillfilene kom bare fra api.github.com.

Ikke prøvd: Esc forbi introen (et Esc etter 40 sekunder gjorde ingenting synlig), F5-menyen, lagring og lasting etter omlasting, fullskjerm, lyden med ører, mappevalget uten nøkkel, Firefox og Safari, en ekte telefon, og en hel gjennomspilling.
