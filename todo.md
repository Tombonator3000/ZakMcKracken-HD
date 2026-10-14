# todo.md

Det som gjenstår, viktigst først. Kryss av når noe er gjort, og logg det i `log.md`.

## Neste

- [x] Innført kildetro motiv- og designanalyse før HD-produksjon i `docs/skills/scumm-hd-remake/SKILL.md`, med henvisninger fra arbeidsinstruksene (12. oktober 2026)

### Alt i main (14. oktober, venter på Tom)

- [x] Repoet gjort privat (Tom 14. oktober)
- [ ] Tom fletter grenene `spilldata`, `hd-mod` og `gpt-arbeid` inn i `main` (sikkerhetskontrollen i Claude-økten stopper Claude). Oppskriften i en ny klone, prøvd lokalt av Claude:
  ```sh
  git clone https://github.com/Tombonator3000/ZakMcKracken-HD zak-flett
  cd zak-flett
  git merge -s ours --no-commit --allow-unrelated-histories origin/spilldata origin/hd-mod origin/gpt-arbeid
  git read-tree --prefix=game/ -u origin/spilldata:game
  git show origin/spilldata:README.md > game/README.md
  git add -f game/README.md
  git read-tree --prefix=mods/gpt/ -u origin/hd-mod
  git read-tree --prefix=gpt-arbeid/ -u origin/gpt-arbeid
  git commit -m "Grenene spilldata, hd-mod og gpt-arbeid inn i main"
  git push origin main
  ```
- [ ] Deretter: Claude legger inn verktøyene, nettsidekoden og reglene for mappene i `main` (31 filer, ferdig og testet mot den flettede treet; lagret som `claude/alt-i-main.patch` i Claude-prosjektet). Etter nettsidearbeidet 14. oktober går den ikke rett på: bruk en full klone og `git apply --3way --exclude=todo.md --exclude=engine/pages/local-files.mjs --exclude=engine/pages/tests/local-files.test.mjs --exclude=docs/PAGES.md` (de tre filene i `main` virker allerede med begge oppsettene), og løs konflikten i STATUS.md. Patchen sier at repoet er privat; rett det etter Toms valg

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

- [x] Patch 0002 rettet: flettingen 13. oktober (087fd93) ga feil tall i hunk-hodene, så motoren bygget ikke fra main. Laget på nytt med `tools/lag_patcher.sh`, verbhjul-testen bestått (14. oktober)
- [x] `tools/sjekk_patcher.py` i `test.yml`, og `motor.yml` som bygger motoren når en PR endrer patchene (14. oktober)
- [x] Rettingen lagt rett i `main` (Tom 14. oktober: alt i main)
- [x] Første kjøring av `motor.yml` i GitHub Actions: grønn på PR 10 (14. oktober)
- [ ] Myk rulling i HD-laget, eller kroker i FM-Towns-tegningen (HD-MOTOR punkt 1, MOTOR-FORBEDRING del 4). Avgjøres i starten av porten

- [ ] Prøv FM-Towns-laget slått av (`DISABLE_TOWNS_DUAL_LAYER_MODE`): starter Zak i 8 bit, og er fargene riktige?
- [ ] Slå på DigHD for `GID_ZAK` (FM-Towns), og testhoppet med HD-blokken i v3
- [ ] Rom og objekter med nearest-mod (0 avvik, `engine/test.sh`); objektbildet `_01` for alle tilstander
- [ ] Kostymer med krokene fra Sam & Max, og `DIGHD_TEST_COSTUME` med én byte startindeks
- [ ] Tekst: HD-glyfer i `CharsetRendererV3` (verb og inventar er tekst)
- [ ] HD av og på mens man spiller (Tom 14. oktober): Ctrl+H (finnes i 0001) og raden HD Graphics i menyen for FM-Towns-utgaven, så det går på mobil; valget lagres (`dighd_classic`)
- [ ] Pekeren for FM-Towns-utgaven
- [ ] Romtesten i alle 58 rom

### Grensesnitt: verbhjulet (`docs/VERBHJUL.md`)

- [x] Tom valgte C, verbhjul som i DOTT Remastered (12. oktober)
- [x] Klargjort: hvordan DOTT gjorde det, hvordan skript 11 tar imot klikk, verb per objekt, forslag til oppførsel, ikonliste (`docs/verbhjul-verb.csv`), motorarbeid og tester
- [x] Tom godkjente oppførselen (urskive med tolv faste plasser, verb for objektet, høyreklikk og hold-og-dra, tekst under hjulet, ikonene i stilpiloten) og ba om at det lages (12. oktober)
- [x] Logikken i `engine/patches/0002-verbhjul.patch`: urskiven, verbtabellen uten 255, verb som er på i panelet, klikkene til skript 11, venting på objekt nummer to (setningslinjen klikkes ikke da), avbryt med Walk to (13. oktober)
- [x] Inndata: høyreklikk, hold og dra, klikk på ikon; spillet får ikke klikkene mens hjulet er åpent; Esc lukker; Ctrl+W av og på
- [x] Enkel tegning med tre bokstaver på spillets skjerm, ryddes bort når hjulet lukkes
- [x] Verb 1 til 17 skjules i panelet når hjulet er på; tastene virker; resten av panelet står
- [x] `tools/verbhjul_test.sh`: originalpanelet og hjulet gir de samme 8 setningene i rom 1, med venting og avbrudd (bestått 13. oktober)
- [x] `tools/lag_patcher.sh` lager 0001 og 0002 på nytt; 0001 er byte for byte lik den i Sam & Max
- [x] Gjennomgang 13. oktober: objektet fra forrige klikk ble med i setningen (Walk to lamp, så Use på ticket kjørte «Use lamp with ticket»). Rettet i PR 4 (`verbhjul-tom-setning`), testen bestått
- [x] Tom fletter PR 4 når CI er grønn (8eaeb88, 13. oktober)
- [ ] Prøv pilene i inventaret mens hjulet venter på objekt nummer to (rettet i PR 4, ikke testet)
- [ ] Navnet på objektet under pekeren mens hjulet er lukket (What is er skjult)
- [ ] Vurder valg på vinkel: slipp hvor som helst i sektoren til et verb, ikke bare på ikonet (lettere på mobil og med spillkontroll)
- [ ] Spillkontroll: en knapp åpner hjulet på objektet under pekeren, stikken velger (hvis spillet skal på Steam Deck eller konsoll)
- [ ] Rug corner 109 sender alle verb til 107 (oppføring 255); hjulet kunne vist verbene til 107 der (lite viktig)
- [ ] Prøv med skjerm og mus, i nettleseren og på mobil (langt trykk), og at valget lagres i scummvm.ini
- [ ] Prøv butikken (Buy, Sell), teleporten, figurbytte og styring av dyr
- [ ] Tegning i HD-laget når DigHD er portet til Zak
- [ ] Menyvalg i F5: verbhjul av eller på, verb for objektet eller alle verb
- [ ] Ikonene (15) etter motiv- og designavklaring, godkjent av Tom
- [ ] Senere, hvis ønsket: A (rom og panel i hver sin skala) og B (ikoninventar), se GRENSESNITT.md
- [x] Målt et dynamisk hjul (Toms forslag 13. oktober) med `tools/verbhjul_dynamisk.py`: høyst fire ikoner for 330 av 337 objekter uten skriptendring, se VERBHJUL.md
- [x] Tom sa ja til dynamisk modus og portretter, uten snakkeboble (13. oktober)
- [x] Dynamisk modus bygget: reglene i `verbhjul_zak.h` fra `tools/verbhjul_dynamisk.py --cpp`, par bare når begge sider sjekker tilstanden, 19 regler for hånd, høyst fire ikoner for alle 337 objekter
- [x] Portretter for figurbytte (som F1 til F4), Switch skjult mens de er på
- [x] Testen utvidet: Close på åpen skuff, kommoden, katteklokken (Turn off), bytte til Annie, kontroll av alle reglene; bestått
- [x] Gjennomgang av koden (egen agent): klikk sjekkes igjen når de sendes, kastes ved rombytte, grensesjekk av betingelser, tekstboksen klippes
- [ ] Prøv reglene for hånd i spillet: Sushi, våtdrakten, oksygentanken, mikrobølgeovnen, boom-boksen, fallskjermen, lighteren, lommelykten, radioen
- [ ] Prøv figurbytte der Switch kommer i spillet
- [ ] Taster og klikk mens hjulet sender klikk (tre eller fire rammer) går tapt; ta vare på dem og send dem etterpå
- [ ] De fire portrettene som tegning, etter stilpiloten

### Ytelse og effekter (`docs/MOTOR-FORBEDRING.md`, 14. oktober)

- [x] Målt den varmeste løkken i HD-laget (`tools/ytelse/compose_bench.cpp`): 12 til 21 ms for hele skjermen i dag, 0,6 ms med tabell per palettindeks, 0 ulike byte
- [x] To egne shadere i `engine/shadere/` (klassisk CRT og HD-glød), prøvd i Zak under Xvfb med programvare-OpenGL, sammen med fire fra ScummVM
- [ ] Tom velger hva som skal gjøres (MOTOR-FORBEDRING del 9)
- [ ] Tabell per palettindeks og kopi i `compose()`, figurrutene uten skalering, bildebuffer på tvers av rom og lasting ved rombytte. Gjøres i Sam & Max HD med `DIGHD_BENCH` og `engine/test.sh`, og 0001 kopieres hit
- [ ] Verbhjulet tegner bare når noe er endret (i dag låses skjermen hver gang den oppdateres mens portrettene vises)
- [ ] Effektvalg som følger HD-valget: `dighd_effekt_hd` og `dighd_effekt_klassisk` (av som standard), `setShader()` ved Ctrl+H, raden «Effekter» i menyen
- [ ] Shaderne i Linux-pakken og på nettsiden; prøv på ekte skjermkort, i nettleseren og på mobil
- [ ] `klassisk-crt` med `KILDEPIKSEL = 4` når HD-laget viser originalgrafikken

### Pipeline

- [x] Dekodere for v3 med 256 farger (`lfl.py`, `v3grafikk.py`) og uttrekket (`eksport_v3.py`)
- [x] `zakhd build-mod` med Zak-uttrekket (nearest, kostyme 1: 58 rom, 585 objektbilder, 51 ruter på 3 sekunder)
- [ ] Sammenlign uttrekket med motoren piksel for piksel (nearest-mod, når DigHD er på)
- [ ] Prompter og figurnavn i `gpt.py` og `figur.py` gjennomgått for Zak (grovt tilpasset 11. oktober)

### Grafikk

- [x] Stilankere godkjent av Tom 14. oktober: figurarkene for Zak, Annie og Caponian v3, rom 42 og avisforsiden. I `grafikk/stil/` i `main` og `stil/` i `gpt-arbeid`
- [x] AGENTS skrevet om: HD-grafikk kan ligge i `main` under `grafikk/`, og HD er alltid et valg for spilleren (Tom 14. oktober)
- [ ] Stilankerne sett i motoren (krever HD-motoren for Zak)
- [ ] Master-figurark: Zak og Annie finnes som godkjente stilankere; Melissa og Leslie mangler
- [ ] Promptene i `gpt.py` og `figur.py` skrevet om etter stilankerne. I dag ber romprompten om originalens pikselstil og farger (`gpt.py`, linje 90)
- [ ] Resten av `docs/BESTILLING-CHATGPT.md` gått gjennom etter stilankerne (status, avsnitt 1, rekkefølgen og opphav er rettet 14. oktober)
- [ ] Aktiver bestillingen (`docs/BESTILLING-CHATGPT.md`) og grafikkrunder med `tools/gpt_runde.sh`
- [ ] Ta inn grafikkjobbene fra Sam & Max HD (PR 4 der, 13. oktober), tilpasset v3:
  - [ ] Fast størrelse i figurarkene: mål per rute i figurprompten, `tools/sjekk_leveranse.py` i `verktoy/` i `gpt-arbeid`, `myk.py` versjon 4 (her er den versjon 2)
  - [ ] Hovedark (`figur.MASTERS`, `master_jobs`) for Zak, Annie, Melissa og Leslie, brukt som bilde to i figurjobbene deres
  - [ ] Pilotordren: bare stilpiloten i ORDRE.md så lenge `stil/` er tom (`FIG_PILOT` og `PILOT_ROOMS`)
  - [ ] Ikonark pakket i rader rom for rom med flat bakgrunn, og den omskrevne romprompten (ingenting legges til, fjernes eller ryddes, skilt bokstav for bokstav)
  - [ ] Palett per kostyme fra skriptene (`tools/kostymer.py` i Sam & Max, `kostymer-i-rom.tsv` her) inn i `docs/kostymefarger.csv` og `zakhd extract`. Kostymepalettene peker på romindekser (for eksempel 225 til 229)
  - [ ] Ikke ta med skyggeregelen (`figur.SHADOW_INDEX`): i v3 setter ScummVM ingen skyggetabell (bare v5 og nyere, `actor.cpp`), så indeks 13 er en vanlig farge. Kostyme 8 bruker den i 104 piksler (målt 13. oktober). Gjør regelen til et valg per spill
  - [ ] Søppelrutegrensen (`figur.MAX_CEL`) kan tas med, men ingen av de 847 rutene i Zak er over 640 x 400
  - [ ] Speilvending som i Sam & Max: alle 40 kostymer har speilflagg av, så rutene mot venstre lages av motoren
- [ ] Dynamisk lys med normalkart og luminansmaske, etter godkjent stilpilot (Tom 13. oktober): valgfritt for spilleren (av som standard, eget valg i menyen), ingen kastede skygger. Prøv først i ett rom med normalkart regnet ut fra HD-bildene og lyset av og på med en tast. Lyset legges inn før fargeforholdet fra paletten. Samme plan som i Sam & Max HD

### Spillbart for Tom

- [x] `./spill.sh` fra repoet (starter originalspillet)
- [ ] Linux-pakken: kjør arbeidsflyten for hånd og test AppImage-filen
- [x] Nettsiden på GitHub Pages fra dette repoet: `pages.yml` bygger med Emscripten og libFLAC og publiserer, spilt i Chromium uten skjermkort (14. oktober). https://tombonator3000.github.io/ZakMcKracken-HD/
- [x] Nettsiden leser spillet fra `game/` i `main` og ellers fra `spilldata`, og moden fra `mods/gpt/` eller `hd-mod` bare når det finnes `mod.json` (hd-mod uten mod stoppet siden før)
- [ ] Tom spiller nettsiden på PC og telefon: lesenøkkel, lyd, fullskjerm, F5-menyen, lagring og lasting etter omlasting
- [ ] Tom bestemmer om repoet skal være offentlig (Pages virker da) eller privat (da trengs et eget offentlig nettsiderepo eller GitHub Pro). Det ble offentlig igjen 14. oktober 15.27, og `spilldata` er da åpen for alle
- [ ] Esc forbi introen i nettleseren (et Esc etter 40 sekunder gjorde ingenting synlig i testen); sjekk om det er likt i `./spill.sh`

## Senere

- [ ] Vurder én felles kode-repo for alle LucasArts-HD-spillene, når Sam & Max og Zak trenger samme motor
- [ ] Slå på push-utløseren i `.github/workflows/linux.yml` når HD virker
