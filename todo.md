# todo.md

Det som gjenstår, viktigst først. Kryss av når noe er gjort, og logg det i `log.md`.

## Neste

- [x] Innført kildetro motiv- og designanalyse før HD-produksjon i `docs/skills/scumm-hd-remake/SKILL.md`, med henvisninger fra arbeidsinstruksene (12. oktober 2026)

### Oppsett (11. oktober)

- [x] Spillfilene hentet fra Drive (`Zak-fm`) og lagt i grenen `spilldata` med sjekksummer
- [x] Utgaven bekreftet med MD5: engelsk FM-Towns
- [x] Samme oppsett som Sam-Max-HD: AGENTS, README, memory, todo, log, STATUS, `engine/`, `pipeline/` (`zakhd`), `tools/`, `docs/`, `spill.sh`, arbeidsflyter
- [x] Grenene `hd-mod` og `gpt-arbeid` som startgrener
- [x] ScummVM ved c9091321 med patchen og FLAC bygget, og Zak startet uten skjerm (uten HD)
- [x] Tom fletter PR-en med oppsettet når CI er grønn (PR 1, flettet 12. oktober)
- [ ] Tom skrur av lenkedelingen på Drive-mappen `Scummvm` når han ikke trenger den
- [ ] Tom starter `./spill.sh` på laptopen og ser at spillet starter med bilde og CD-musikk

### Analyse (`docs/ANALYSE.md`)

- [x] Tell rom, størrelser, z-plan, paletter, objektbilder, kostymer, tegnsett og skript (`zakhd info`, `zakhd extract`)
- [x] Dekompiler alle skriptene med descumm (`tools/dekompiler_skript.py`, 1094 av 1094)
- [x] Liste over all grafikk som skal byttes ut (`docs/grafikkliste.csv`, `zakhd grafikkliste`)
- [x] Romliste som CSV (`docs/rom-oversikt.csv`, uten navn)
- [x] De fire spillbare figurene koblet til kostymer (`docs/figurer.csv`)
- [x] Beskrivelse av alle 58 rommene fra objektnavn, replikker og bilder (`docs/romnavn.csv`, brukes av `zakhd grafikkliste`). Rom 48 og 56 er ikke avklart
- [x] Lesbart lag over skriptene: `tools/skriptoversikt.py` gir ROM.md, REPLIKKER.md (1309 replikker), rom-koblinger.tsv og kostymer-i-rom.tsv i work/skript
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

### Grensesnitt: verbhjulet (`docs/VERBHJUL.md`)

- [x] Tom valgte C, verbhjul som i DOTT Remastered (12. oktober)
- [x] Klargjort: hvordan DOTT gjorde det, hvordan skript 11 tar imot klikk, verb per objekt, forslag til oppførsel, ikonliste (`docs/verbhjul-verb.csv`), motorarbeid og tester
- [ ] Tom svarer på de fire åpne spørsmålene i VERBHJUL.md (verb for objektet eller alle, høyreklikk og hold, tekst ved ikonene, ikonene i stilpiloten)
- [ ] Logikken i patchen: tilstand, verbtabellen uten 255, verb som er på i panelet, kallene til skript 11 (verb, objekt, setningslinje 100), to objekter, avbryt med Walk to
- [ ] Test uten skjerm: samme `doSentence` med hjulet som med originalpanelet for alle objekter i et rom
- [ ] Inndata: høyreklikk og langt trykk; `checkExecVerbs` får ikke klikkene mens hjulet er åpent
- [ ] Enkel tegning med tekst for å prøve oppførselen før HD-motoren er portet
- [ ] Tegning i HD-laget når DigHD er portet til Zak
- [ ] Skjul verbradene når hjulet er på; spesialmodus (verb 31 til 40) viser panelet
- [ ] Menyvalg i F5: verbhjul av eller på, verb for objektet eller alle verb
- [ ] Ikonene (15) etter motiv- og designavklaring, godkjent av Tom
- [ ] Senere, hvis ønsket: A (rom og panel i hver sin skala) og B (ikoninventar), se GRENSESNITT.md

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
