# Logg

Alt som gjøres i prosjektet, med tidspunkt (norsk tid). Nyeste nederst.

## 2026-10-09 21:36
- Repo opprettet av Tom (bare README).

## 2026-10-11 18:05 til 22:45 (Claude)
- Tom: gjør som The Dig- og Sam & Max-repoene og klargjør repoet; dekompiler, og lag liste over grafikken som skal byttes ut.
- Sjekket etter AGENTS.md. Fantes ikke (bare README). Leste skillen `scumm-hd-remake`, og AGENTS, memory, STATUS, todo og log i Sam-Max-HD (main 5ef6f1f), som ble satt opp på samme måte fra Dig-HD-Remake 10. oktober.
- Spillfilene: Drive-mappen `Zak-fm` ligger i `Scummvm`, som fortsatt var delt med lenke. Lastet ned alle 83 filer med curl (00.LFL til 59.LFL, 98.LFL, 99.LFL, Track1.fla til Track21.fla); størrelsene stemmer med Drive. MD5 av 00.LFL `2d4536a56e01da4b02eb021e7770afa2` er zak, FM-TOWNS, EN_ANY i ScummVMs `scumm-md5.h` ved c9091321.
- Grenen `spilldata` (uten felles historikk med main): README og LFL-filene med `game/SHA256SUMS` for alle 83 filer (431e119), så CD-sporene i fem commits på under 80 MB hver (siste df8ce95). SHA-256 sjekket i grenens arbeidskopi etter siste push.
- Arbeidsgren `oppsett-som-sam-max`. Kopiert alt fra Sam-Max-HD main 5ef6f1f, pakken `smhd` omdøpt til `zakhd`.
- ScummVM: `engine/build.sh` bygde c9091321 med patchen. Første bygg var uten FLAC (libflac-dev manglet), så CD-sporene ville ikke spilt; installert libflac-dev og bygget på nytt (`USE_FLAC = 1`). `build.sh` sier nå fra når FLAC mangler, og `spill.sh` sjekker etter libFLAC. Zak startet fra `game/` uten skjerm i 30 sekunder: `zak`, FM-TOWNS, SCUMM 3, riktig MD5, rommene 49, 1, 47, 9 og 50 lest (introen).
- Funnet i ScummVM-kilden: FM-Towns tegner gjennom `towns_drawStripToScreen`, som returnerer før DigHD-kroken i `drawStripToScreen`. HD-porten må enten slå av FM-Towns-laget eller lage kroker der. Skrevet i `docs/HD-MOTOR.md`.
- Pipeline: nye moduler `lfl.py` (v3-filene med små blokkhoder), `v3grafikk.py` (stripekodekene 1, 2, 3, 4 og 7 for GF_OLD256, BM med z-plan, v3-kostymer med én byte startindeks, tegnsett; oversatt fra ScummVM ved c9091321), `eksport_v3.py` og `grafikkliste.py`. `zakhd info`, `zakhd extract` og `zakhd grafikkliste` lagt inn i cli.py.
- Uttrekket: 58 rom, 585 objektbilder, 847 kostymeruter fra 40 kostymer og 2 tegnsett, 0 feil, omtrent 6 sekunder. Første kjøring ga 167 feil for objekter med OI på 8 byte; det er objekter uten eget bilde (en del av bakgrunnen), og de står nå som `uten_bilde`. Sett på kontaktark over alle rom, rom 1 med alle objektene på plass og den største ruten i hvert kostyme. Rom 46 og 55 er svarte i originalen.
- Skriptene: `tools/dekompiler_skript.py` skrevet om for v3 (0S, LS, EN, EX og OC; descumm `-3 -z`). 1094 skript, alle uten feil. Første kjøring merket to skript som feil fordi teksten i dem inneholder ordet ERROR; sjekken ser nå bare etter descumm sine egne feilmerker.
- Fra skriptene: skuespiller 1 til 4 er Zak (kostyme 1), Annie (2), Melissa (7) og Leslie (36); verb og inventar settes opp i globalt skript 36; skjermen deles med `SetScreen(16,144)`. `docs/figurer.csv` fylt med de kjente figurene.
- Grafikklisten: `docs/grafikkliste.csv` (685 rader: 58 rom, 585 objektbilder, 40 kostymer, 2 tegnsett, med HD-mål og anslag på jobber) og `docs/rom-oversikt.csv`. Sammendrag i `docs/ANALYSE.md`: rundt 105 romjobber og 58 figurark etter jobbformatet fra The Dig.
- `zakhd build-mod --method nearest --kostymer 1` med Zak-uttrekket: 58 rom, 585 objektbilder, 51 ruter på 3 sekunder.
- Tester: nye for stripekodekene, BM med z-plan og v3-kostymer; game-testene byttet til Zak-tall. `pytest`: 36 bestått (34 uten spillfiler).
- To hjelpeagenter. Den ene tilpasset nettsidekoden (filfilter for LFL og FLA, ingen deler, lerretet venter ikke lenger på loggen fra DigHD, libFLAC bygget for Emscripten i `build-web.sh`, ikke prøvd) og `docs/PAGES.md`; `node --test` 18 bestått. Den andre tilpasset Linux-pakken (`ZakHD-x86_64.AppImage`, krever FLAC, AppDir startet uten skjerm), `linux.yml` (push-utløseren fortsatt av; nattkjøringen tåler at `hd-mod` mangler), gpt-verktøyene og dokumentene BESTILLING, gpt-arbeid-AGENTS, HD-REMASTER-METODE, SPILLTEST og gpt-kodeoppgaver.
- Tilpasset selv: `tools/hent_spilldata.sh` (ingen deler), `tools/indeks_info.py` (v3), `engine/run.sh`, `engine/test.sh` (stopper med kode 3 til DigHD er på), `engine/build.sh`, `spill.sh`, `tools/romtest.py` (bare spill-ID og filnavn; ikke kjørt), `.gitignore` og sjekken mot spillfiler i `test.yml`.
- Tom spurte underveis om et mer moderne grensesnitt (verbhjul som i Curse of Monkey Island og Full Throttle, ikoninventar som i Monkey Island 2, større bilde). Utredningen er `docs/GRENSESNITT.md`, med kilder: A (rom og panel i hver sin skala, rommet 78 prosent større på 16:9 uten å skjule noe), B (ikoninventar, 70 til 90 ikoner), C (verbhjul med alle verb). Et hjul med tre ikoner frarådes, fordi Zak bruker 14 verb i gåtene. Punktene står i todo.
- Grenene `hd-mod` (README og SHA256SUMS) og `gpt-arbeid` (AGENTS, BESTILLING, ORDRE uten jobber) laget og pushet, som i Sam & Max.
- AGENTS, README, memory, todo, STATUS, ANALYSE og HD-MOTOR skrevet for Zak.
- Ikke gjort: HD-motoren for Zak, stilpiloten, nettsiden og AppImage-arbeidsflyten.

## 2026-10-11 22:55 (Claude)
- PR 1 (`oppsett-som-sam-max`) åpnet. CI (test: nettleser og pipeline) grønn på 4ad21f0.
- Kontroll: fersk `git clone` av grenen, så `tools/hent_spilldata.sh`: 83 filer hentet, SHA-256 stemmer for alle, `git status` tom etterpå.
- Jeg får ikke flette min egen PR. Tom fletter.
