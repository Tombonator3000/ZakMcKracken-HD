# Spilltest

Slik skal Tom spille og teste Zak McKracken (engelsk FM-Towns-utgave, ScummVM-ID `zak`) rett fra repoet, og hva han bør se etter. Oppsettet er kopiert fra The Dig HD Remake via Sam & Max HD.

## Status

HD-motoren (DigHD) er ikke slått på for Zak, og det finnes ingen HD-grafikk. Spillet vises som originalen. `DigHD::create` godtar bare `GID_DIG` og `GID_SAMNMAX`, og FM-Towns tegner gjennom `towns_drawStripToScreen` i 16 bit (RGB555, 640 x 480 med tekstlaget), så porten krever egne kroker der, eller at FM-Towns-laget slås av (`DISABLE_TOWNS_DUAL_LAYER_MODE`). Det er ikke bestemt. Se [HD-MOTOR.md](HD-MOTOR.md).

| Del | Status |
| --- | --- |
| Spillfilene til `game/` med `tools/hent_spilldata.sh` | Grenen `spilldata` har `00.LFL`, `01.LFL` til `59.LFL`, `98.LFL`, `99.LFL` og `Track1.fla` til `Track21.fla` (omtrent 315 MB) med `game/SHA256SUMS`. Sjekksummene stemte 11. oktober (kjørt av `tools/pakke_linux.sh`). Selve skriptet `hent_spilldata.sh` er ikke prøvd med Zak |
| HD-grafikk | Ikke slått på for Zak. Ingen HD-mod, og grenen `hd-mod` finnes ikke (sjekket lokalt) |
| `./spill.sh`, `engine/run.sh` | Ikke testet med Zak |
| `engine/test.sh`, `tools/romtest.sh` | Kan ikke brukes før DigHD er portet til Zak |
| `./spill.sh --auto` | Ikke kjørt med Zak. Trenger uttrekket av Zak, som ikke er prøvd |
| Nettsiden | Repoet `Tombonator3000/ZakMcKracken-HD-Web` finnes ikke. Se [PAGES.md](PAGES.md) |
| Linux-pakken | `tools/pakke_linux.sh` og `.github/workflows/linux.yml` er tilpasset Zak. AppDir laget (83 spillfiler, ingen HD-mod) og startet uten skjerm 11. oktober med SDL dummy: `Using gameid zak, variant FM-TOWNS`, `SCUMM version 3`, `Using MD5 '2d4536a56e01da4b02eb021e7770afa2'`, og spillet kjørte til de 60 sekundene var ute. AppImage og arbeidsflyten er ikke kjørt |
| ScummVM med patchen og Zak | `engine/scummvm/scummvm` har FLAC og starter Zak (FM-TOWNS, SCUMM v3) uten skjerm. Ikke testet med skjerm, mus og lyd. Patchen har ingen virkning på Zak |

Resten av dokumentet beskriver hvordan det skal virke når delene over er på plass.

## Første gang

Linux. Installer det motoren trenger:

```sh
sudo apt install build-essential git pkg-config libsdl2-dev libpng-dev zlib1g-dev libflac-dev     # Ubuntu/Debian
sudo dnf install gcc-c++ make git pkgconf SDL2-devel libpng-devel zlib-devel flac-devel          # Fedora
```

Hent repoet og spillfilene:

```sh
git clone https://github.com/Tombonator3000/ZakMcKracken-HD.git
cd ZakMcKracken-HD
tools/hent_spilldata.sh
```

`tools/hent_spilldata.sh` henter grenen `spilldata` til `game/` og sjekker sjekksummene. Etterpå ligger `00.LFL` (indeksen), `01.LFL` til `59.LFL` (rommene med skript, kostymer og lyder), `98.LFL` og `99.LFL` (tegnsettene) og `Track1.fla` til `Track21.fla` (CD-musikken) i `game/`. Det er ingen delte filer og ingen tale.

Når `spill.sh` er tilpasset, skal `./spill.sh` gjøre alt: hente spillfilene og siste HD-mod (grenen `hd-mod`) første gang, bygge motoren og starte spillet. Senere skal den starte med en gang og bare hente ny HD-mod og bygge motoren på nytt når den er endret.

Musikk: CD-musikken ligger i `Track1.fla` til `Track21.fla` (FLAC). Motoren må være bygget med FLAC (`libflac-dev`) for at den skal spilles. Sjekk med `engine/scummvm/scummvm --version`: linjen `Features compiled in` skal ha FLAC med. Motoren i `engine/scummvm` har det. Om og hvordan musikken høres, er ikke testet.

## Valg

Fra The Dig. Valgene som styrer HD (`--rom`, `--klassisk`, `--gult`) virker først når patchen er portet.

| Kommando | Hva |
| --- | --- |
| `./spill.sh` | Vanlig start med HD-modden |
| `./spill.sh --rom N` | Hopper til rom N like etter starten, for å se på ett rom. Spillet er ikke i normal tilstand etter et hopp, så bruk det til å se, ikke til å spille videre |
| `./spill.sh --klassisk` | Starter med originalgrafikken |
| `./spill.sh --gult` | Farger gult der HD mangler |
| `./spill.sh --auto` | Fyller rom og objekter som ikke har HD fra ChatGPT, med automatisk oppskalering. Krever Python 3.12 og uttrekket |
| `./spill.sh --fort` | Starter uten å hente eller bygge noe |
| `./spill.sh --fullskjerm` | Fullskjerm |
| `./spill.sh --programvare` | Uten OpenGL. Bruk den hvis spillet ikke starter og terminalen sier "Could not load any graphics mode" |
| `./spill.sh --nettleser` | I nettleseren på http://localhost:8000, bare på denne maskinen |
| `git pull && ./spill.sh` | Siste versjon av koden og modden |

Andre valg sendes videre til ScummVM.

## Taster i spillet

| Tast | Hva |
| --- | --- |
| Ctrl+H | Bytter mellom HD og originalgrafikken (når patchen er portet) |
| Ctrl+Shift+H | Gult felt der HD mangler, av og på (når patchen er portet) |
| Alt+S | Skjermbilde (lagres i mappen ScummVM skriver ut i terminalen) |
| F5 | Spillets meny (lagre, laste, avslutte). Hvor HD-valget skal ligge i Zak, er ikke bestemt |
| Ctrl+F5 | ScummVM-menyen |

## Hva du bør se etter

Når det finnes HD-grafikk:

1. Rom med HD-bakgrunn: bytt med Ctrl+H og se at alt står på samme sted.
2. Figurene (Zak, Annie, Melissa og Leslie og de andre) går bak ting i forgrunnen der de skal, og kanter og dører ligger der de lå.
3. Objekter som tas eller flyttes (Zak har ett bilde per objekt, uten tilstander med egne bilder) forsvinner og dukker opp riktig.
4. Verblinje, replikker og inventar: teksten står der den står i originalen. Ingen tekst blir stående igjen.
5. Menyen (F5) og replikker over en figur: ingen figur skal skinne gjennom.
6. Mellomsekvenser: de tegnes av motoren og skriptene, ikke som filmer, og skal vises riktig med HD.
7. Gå mellom rom med og uten HD, og se at spillet ikke krasjer eller blinker.
8. Ctrl+Shift+H: det gule skal vise nøyaktig det som mangler HD. Tekst og pekeren skal ikke bli gul.

Hvilke rom som er best å se på, står i `STATUS.md` når de første HD-rommene finnes.

## Uten skjerm: alle rom

Krever at patchen er portet til Zak, og at `tools/romtest.py` starter Zak. Ikke kjørt med Zak.

```sh
tools/romtest.sh                     # alle rom med mods/gpt
tools/romtest.sh --rom 1,2,3         # noen rom (--rom 10-20 for et område)
tools/romtest.sh --mod test-nearest  # en annen mod
tools/romtest.sh --kamera ett        # bare der spillet selv setter kameraet
tools/romtest.sh --objekter          # i tillegg alle tilstandene til alle objektene i hvert rom
tools/romtest.sh --bare-rapport      # rapport og ark på nytt fra kjøringene som finnes
```

Skriptet kjører motoren uten skjerm (SDL dummy) én gang per rom og hopper til rommet med `DIGHD_TEST_ROOM`. I rom som er bredere eller høyere enn skjermen, kjører det i tillegg med kameraet satt (`DIGHD_TEST_CAMX` og `DIGHD_TEST_CAMY`), så hele rommet blir vist. Skjermen lagres i HD og med originalpikslene. Motoren er `$SCUMMVM_SRC/scummvm` eller `engine/scummvm/scummvm` (`--motor` for en annen).

For hver kjøring samles: om rommet ble lastet, om motoren krasjet eller hang, om HD-bakgrunnen ble lastet og brukt, andelen piksler fra HD-bakgrunn, HD-objekt, HD-figur og originalen, og avviket fra originalen (`DIGHD_VERIFY`). Bildene sammenlignes også i skriptet: forskyvning, svarte felt der originalen ikke er svart, og de største avvikene, med nærbilder. Sømmene mellom HD-objekter og HD-rommet måles også.

Resultatet ligger i `work/romtest`: `RAPPORT.md`, `romtest.csv`, `somer.csv`, kontaktark `ark_NN.png` med HD og originalen side om side, en mappe per kjøring med logg og bilder, og `naerbilder/`. Notater fra gjennomsynet kan skrives i `work/romtest/FUNN.md` og kommer med i rapporten neste gang.

Hoppet setter ikke spillet i vanlig tilstand. Figurer og objekter kan mangle eller stå et annet sted enn i vanlig spill, og noen rom starter en mellomsekvens eller bytter rom selv. Testen fanger krasj, rom som ikke lastes, rom der HD-bakgrunnen ikke brukes og tydelige feil i bildet, ikke feil som bare viser seg i vanlig spill.

### Objekttilstander

Etter hoppet står hvert objekt i tilstanden skriptene ga det, så HD-bildene for de andre tilstandene blir ikke prøvd i den vanlige kjøringen. Med `--objekter` kjøres hvert rom som har objekter, én gang til med `DIGHD_TEST_OBJSTATE=alle`. Motoren setter hvert objekt i hver tilstand slik skriptene gjør det og lagrer skjermen. Rapporten har status, HD-andel og nærbilde per objekt og tilstand (`objekter.csv`).

Et objekt som et annet objekt dekker, kan testes for seg med en liste, der det som dekker får tilstand 0. Zak har ett bilde per objekt, så dette har mindre å vise enn i The Dig. Når motoren er tilpasset, blir kommandoen slik (R er rommet, A og B er objektnumre):

```sh
mkdir -p /tmp/dump
DIGHD_MOD="$PWD/mods/gpt" DIGHD_TEST_ROOM=R DIGHD_TEST_OBJSTATE=A:0,B:2 \
  DIGHD_DUMP_DIR=/tmp/dump DIGHD_DUMP_FLAT=1 DIGHD_QUIT_AT=400 \
  engine/scummvm/scummvm --path="$PWD/game" --debuglevel=1 zak 2>&1 | grep "DigHD: test"
```

## I nettleseren, på denne maskinen

```sh
./spill.sh --nettleser
```

Skriptet skal hente spillfilene og siste HD-mod, bygge ScummVM med HD-patchen for nettleseren (WebAssembly med Emscripten) og starte en webserver på maskinen. Åpne adressen det skriver ut, vanligvis http://localhost:8000. Ctrl+C i terminalen stopper serveren. `engine/run-web.sh` og `engine/web/` er kopiert fra The Dig. Ikke testet med Zak. CD-musikken i nettleseren krever FLAC i WebAssembly-bygget; `engine/build-web.sh` er skrevet for det, men ikke kjørt (se [PAGES.md](PAGES.md)).

**Bare lokalt.** Spillet og HD-grafikken tilhører Disney/Lucasfilm. Denne løsningen skal bare kjøres på egen maskin:

- webserveren (`engine/web/server.py`) lytter bare på 127.0.0.1 og svarer bare på forespørsler til localhost,
- siden (`engine/web/index.html`) nekter å starte hvis den er åpnet fra en annen adresse enn localhost,
- alt som serveres, ligger i `work/nettleser`, og byggefilene i `engine/emsdk` og `engine/scummvm-web`. Alle tre er ignorert av git.

Krav: git, make, python3, pkg-config, xz og zip, og en nyere Chrome, Edge eller Firefox.

```sh
sudo apt install git make python3 pkg-config xz-utils zip     # Ubuntu/Debian
sudo dnf install git make python3 pkgconf xz zip              # Fedora
```

Første gang installeres Emscripten 4.0.10 i `engine/emsdk` (omtrent 350 MB), og ScummVM hentes til `engine/scummvm-web`. Motoren bygges på nytt når patchen, ScummVM-versjonen eller `engine/build-web.sh` er endret.

| Kommando | Adresse | Hva |
| --- | --- | --- |
| `./spill.sh --nettleser` | http://localhost:8000/ | Vanlig start med HD-modden |
| `./spill.sh --nettleser --rom N` | http://localhost:8000/?rom=N | Hopper til rom N |
| `./spill.sh --nettleser --klassisk` | http://localhost:8000/?klassisk=1 | Starter med originalgrafikken |
| `./spill.sh --nettleser --gult` | http://localhost:8000/?gult=1 | Gult felt der HD mangler |
| `./spill.sh --nettleser --auto` | http://localhost:8000/?mod=auto | Med automatisk oppskalering for resten |
| `./spill.sh --nettleser --fort` | | Starter uten å hente eller bygge noe |
| `./spill.sh --nettleser --port 8001` | http://localhost:8001/ | En annen port, hvis 8000 er i bruk |

Tastene er de samme som ellers. Siden stopper nettleserens egne snarveier for F1 til F10 og for Ctrl og Alt med en bokstav, så F5 åpner spillmenyen i stedet for å laste siden på nytt. F11 gir fullskjerm.

Lagring: lagrede spill og innstillingene ligger i nettleseren (IndexedDB for localhost og porten), ikke i repoet.

## Fra GitHub Pages

Planen er en nettside som går rett inn i spillet, på PC og mobil, og henter spillet og HD-grafikken fra grenene `spilldata` og `hd-mod` med en lesenøkkel. Nettsiderepoet `Tombonator3000/ZakMcKracken-HD-Web` finnes ikke ennå. Se [PAGES.md](PAGES.md).

## Linux: én fil med alt

Planen er som for The Dig: én AppImage (`ZakHD-x86_64.AppImage`, med data i `zak-hd`) med ScummVM med patchen, spillet, CD-musikken og HD-grafikken når den finnes, under Releases i dette repoet. Spillet skal starte rett, i fullskjerm. HD-valget i menyen kommer når HD er slått på for Zak.

`tools/pakke_linux.sh` og `.github/workflows/linux.yml` er tilpasset Zak. Skriptet tar med `00.LFL`, `01.LFL` til `59.LFL`, `98.LFL`, `99.LFL` og `Track1.fla` til `Track21.fla`, og stopper hvis motoren er bygget uten FLAC. AppDir-mappen er laget og startet uten skjerm her 11. oktober (originalspillet, uten HD-mod). Selve AppImage-filen lages bare i arbeidsflyten Linux-pakke, som ikke er kjørt ennå. Den startes for hånd (push-utløseren er av) eller kjører om natten når `hd-mod` er endret. Testen i arbeidsflyten sjekker at spillet starter som `zak` (FM-TOWNS, SCUMM v3) og fortsatt kjører etter 60 sekunder.

## Si fra

Skriv hva du så, i hvilket rom og omtrent hvor, og legg ved skjermbilde (Alt+S) hvis du kan. Gi det til Claude i chatten, eller legg det i `rapporter/` i grenen `gpt-arbeid`.
