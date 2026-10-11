# todo.md

Det som gjenstår, viktigst først. Kryss av når noe er gjort, og logg det i `log.md`.

## Neste

### Oppsett (11. oktober)

- [x] Spillfilene hentet fra Drive (`Zak-fm`) og lagt i grenen `spilldata` med sjekksummer
- [x] Utgaven bekreftet med MD5: engelsk FM-Towns
- [x] Samme oppsett som Sam-Max-HD: AGENTS, README, memory, todo, log, STATUS, `engine/`, `pipeline/` (`zakhd`), `tools/`, `docs/`, `spill.sh`, arbeidsflyter
- [x] Grenene `hd-mod` og `gpt-arbeid` som startgrener
- [x] ScummVM ved c9091321 med patchen og FLAC bygget, og Zak startet uten skjerm (uten HD)
- [ ] Tom fletter PR-en med oppsettet når CI er grønn
- [ ] Tom skrur av lenkedelingen på Drive-mappen `Scummvm` når han ikke trenger den
- [ ] Tom starter `./spill.sh` på laptopen og ser at spillet starter med bilde og CD-musikk

### Analyse (`docs/ANALYSE.md`)

- [x] Tell rom, størrelser, z-plan, paletter, objektbilder, kostymer, tegnsett og skript (`zakhd info`, `zakhd extract`)
- [x] Dekompiler alle skriptene med descumm (`tools/dekompiler_skript.py`, 1094 av 1094)
- [x] Liste over all grafikk som skal byttes ut (`docs/grafikkliste.csv`, `zakhd grafikkliste`)
- [x] Romliste som CSV (`docs/rom-oversikt.csv`, uten navn)
- [x] De fire spillbare figurene koblet til kostymer (`docs/figurer.csv`)
- [ ] Navn på rommene i romlisten ved gjennomsyn (indeksen har ingen romnavn)
- [ ] Resten av kostymene koblet til figurer (fra `ActorOps` og `putActor` i skriptene)
- [ ] Hvilket rom og hvilken palett hvert kostyme faktisk vises i, og bruk den i RGBA-bildene
- [ ] Hvilke ting kan havne i inventaret (pickupObject i skriptene og verb 8), til eventuelle ikoner

### Motor (`docs/HD-MOTOR.md`)

- [ ] Prøv FM-Towns-laget slått av (`DISABLE_TOWNS_DUAL_LAYER_MODE`): starter Zak i 8 bit, og er fargene riktige?
- [ ] Slå på DigHD for `GID_ZAK` (FM-Towns), og testhoppet med HD-blokken i v3
- [ ] Rom og objekter med nearest-mod (0 avvik, `engine/test.sh`); objektbildet `_01` for alle tilstander
- [ ] Kostymer med krokene fra Sam & Max, og `DIGHD_TEST_COSTUME` med én byte startindeks
- [ ] Tekst: HD-glyfer i `CharsetRendererV3` (verb og inventar er tekst)
- [ ] Menyen (raden HD Graphics) og pekeren for FM-Towns-utgaven
- [ ] Romtesten i alle 58 rom

### Grensesnitt (`docs/GRENSESNITT.md`, ikke bestemt)

- [ ] Tom velger hva han vil ha: A (rom og panel skalert hver for seg), B (ikoninventar), C (verbhjul med alle verb)
- [ ] A: bygg skjermen av rom og panel i hver sin skala, og regn om musen
- [ ] B: ikonark for inventaret og klikk på ikon sendt som klikk på verbplassen
- [ ] C: verbhjul med alle verb, sendt som `runInputScript` som originalen
- [ ] Valgene i spillets egen meny, hver for seg

### Pipeline

- [x] Dekodere for v3 med 256 farger (`lfl.py`, `v3grafikk.py`) og uttrekket (`eksport_v3.py`)
- [x] `zakhd build-mod` med Zak-uttrekket (nearest, kostyme 1: 58 rom, 585 objektbilder, 51 ruter på 3 sekunder)
- [ ] Sammenlign uttrekket med motoren piksel for piksel (nearest-mod, når DigHD er på)
- [ ] Prompter og figurnavn i `gpt.py` og `figur.py` gjennomgått for Zak (grovt tilpasset 11. oktober)

### Grafikk

- [ ] Stilpilot med Tom: rom 1 og kostyme 1 sett i motoren, stilankere, godkjenning
- [ ] Master-figurark for Zak, Annie, Melissa og Leslie
- [ ] Aktiver bestillingen (`docs/BESTILLING-CHATGPT.md`) og grafikkrunder med `tools/gpt_runde.sh`

### Spillbart for Tom

- [x] `./spill.sh` fra repoet (starter originalspillet)
- [ ] Linux-pakken: kjør arbeidsflyten for hånd og test AppImage-filen
- [ ] Nettsiden: lag repoet `ZakMcKracken-HD-Web` (Tom), bygg i Actions (libFLAC for Emscripten er lagt inn i `engine/build-web.sh`, ikke prøvd) og test

## Senere

- [ ] Vurder én felles kode-repo for alle LucasArts-HD-spillene, når Sam & Max og Zak trenger samme motor
- [ ] Slå på push-utløseren i `.github/workflows/linux.yml` når HD virker
