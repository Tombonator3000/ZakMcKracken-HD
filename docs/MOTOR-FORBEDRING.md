# Motoren: forbedringer, ytelse og nye effekter

Utredning 14. oktober 2026 (Claude). Tom ba om å sjekke om koden og motoren kan forbedres og optimaliseres, og om nyere effekter og shadere kan legges til.

## Kort

- **Patch 0002 var ødelagt i `main`.** Motoren bygget ikke. Rettet i samme PR som dette dokumentet, med en CI-sjekk som stopper samme feil neste gang (del 1).
- **ScummVM er ikke flaskehalsen.** Zak i 320 x 240 med 256 farger koster nesten ingenting å kjøre. Det som koster, er HD-laget (DigHD), som regner ut hver HD-piksel på prosessoren.
- **Den varmeste løkken i HD-laget kan bli 20 til 35 ganger raskere** med en tabell per palettindeks, uten at bildet endres med én byte (målt, del 2). Den er felles med The Dig og Sam & Max, så endringen bør gjøres der HD-laget kjører i dag.
- **Shadere virker allerede.** ScummVM har libretro-shadere i OpenGL-tegningen, også for WebGL. To egne shadere er laget og prøvd i Zak: en CRT for originalgrafikken og en mild glød for HD-bildet (del 5).
- **Myk rulling må med i porten.** FM-Towns-utgaven ruller én piksel om gangen. Planen om å slå av FM-Towns-laget (HD-MOTOR punkt 1 a) gir hopp på 8 originalpiksler, som blir 32 piksler i HD (del 4).
- **Effekter som lys med normalkart og glød bare fra lamper** trenger mer enn en shader på det ferdige bildet: enten arbeid i HD-laget på prosessoren, eller at HD-laget tegner med skjermkortet (del 7).

## 1. Feil funnet: patch 0002 bygget ikke fra `main`

- Flettingen 13. oktober 2026 kl. 11.02 (commit `087fd93`, «Merge branch 'main' into verbhjul-dynamisk», gjort i GitHub) slo sammen to versjoner av `engine/patches/0002-verbhjul.patch` som tekst. Linjene fra begge kom med, men tallene i hunk-hodene ble stående: `verbhjul.cpp` sa 1226 nye linjer og hadde 1233, `verbhjul.h` sa 245 og hadde 247.
- `git apply` stoler på tallene og hopper over resten uten feilmelding. Filene ble kuttet før slutten, og byggingen stoppet på `unterminated #ifndef` i `verbhjul.h`. `./spill.sh` og `engine/build.sh` feilet derfor fra `main`.
- CI fanget det ikke: `test.yml` bygger ikke motoren, og `linux.yml` kjøres bare for hånd og om natten.
- Rettet: patchene er laget på nytt med `tools/lag_patcher.sh` (bare hodene endret seg; innholdet og 0001 er som før). Ny sjekk `tools/sjekk_patcher.py` teller linjene i hver hunk og stopper ved avvik; den kjøres i `test.yml`. Ny arbeidsflyt `motor.yml` bygger motoren når en PR endrer patchene eller byggeskriptet.
- Testet: `git apply --recount` og bygging, deretter `tools/verbhjul_test.sh` med den flettede koden (bestått, 11 like setninger, venting, avbrudd og figurbytte). Etter at patchene ble laget på nytt: `engine/build.sh` fra ren kopi med vanlig `git apply` (bygget). `tools/sjekk_patcher.py` finner de to feilene i den gamle patchen og ingen i den nye eller i de tre tidligere versjonene.
- Lærdom: patchfiler skal ikke flettes for hånd. Ved konflikt: lag patchene på nytt fra `engine/scummvm` med `tools/lag_patcher.sh`.

## 2. Hvor tiden går

| Del | Hva som skjer | Kostnad | Kilde |
| --- | --- | --- | --- |
| ScummVM (SCUMM v3) | Skript, figurer og tegning i 8 bit, 320 x 240 | Liten. Ikke målt, men et bilde på 76 800 byte | |
| DigHD `compose()`, romkilden | For hver av de 16 HD-pikslene per originalpiksel: `tinted()` sammenligner paletten, og `PixelFormat` regner om fargen to ganger (`colorToARGB` med `expand`, så `RGBToColor`). Formatet ligger i et objekt, så kompilatoren kan ikke forenkle | 12 til 21 ms for hele skjermen (1280 x 960) med vanlig palett, 25 ms under nedtoning | Målt med `tools/ytelse/compose_bench.cpp` |
| Nedtoning og fargeskifte | `redrawColors()` bygger alle piksler i endrede farger på nytt; ved nedtoning er det hele skjermen hver ramme | Som over, hver ramme | Lest i koden |
| Myk rulling | Hele bildet flyttes, så alt bygges på nytt hver ramme mens kameraet går | Som over, hver ramme | Lest i koden |
| Figurruter | Samme mønster som rommet, pluss en deling per underpiksel for skalering (`((lx * n + dx) * cw) / cs.rw`), også når ruten ikke er skalert | Ikke målt | Lest i koden |
| Lasting av bilder | PNG dekodes første gang et bilde brukes, midt i en ramme. `clearRoom()` frigjør også alle figurruter ved hvert rombytte, så Zaks gangsyklus dekodes på nytt i hvert rom | Ikke målt. Gir trolig små hakk første gang en figur går i et rom | Lest i koden |
| Verbhjulet | `draw()` kalles hver gang skjermen oppdateres i ventesløyfa (opptil rundt 100 ganger i sekundet). Mens portrettene vises, låses skjermen hver gang, og OpenGL laster da hele skjermteksturen opp på nytt (`unlockScreen` merker alt som endret) | Liten på PC, unødig på mobil og nett | Lest i koden |

Måleoppsett: `tools/ytelse/compose_bench.cpp` bygges mot ScummVMs egne hoder og kjører romdelen av `compose()` slik den står i dag, og forslaget under, på et tilfeldig HD-rom (960 x 128 originalpiksler) til en skjerm på 1280 x 960. Én tråd på en Xeon på 2,8 GHz i sandkassen; tidene varierer med maskinen (12 og 21 ms i to kjøringer av samme kode). For 60 bilder i sekundet er budsjettet 16,7 ms for alt, så under rulling og nedtoning går HD-laget alene over budsjettet. På mobil og i nettleseren (WebAssembly) er det tregere.

## 3. Forslag til optimalisering

I rekkefølge etter gevinst og risiko:

1. **Tabell per palettindeks i `compose()`.** Når paletten endres, regnes én gang per indeks: uendret farge (kopier HD-pikslene) eller en faktor per kanal i fast komma (16 bit). Per originalpiksel gjøres valget én gang; uendret farge og samme format som HD-bildet gir en kopi av fire og fire piksler. Kopien forutsetter at HD-bildet er helt dekkende (alfa 255), for i dag settes alfa alltid til 255 i utdataene; det sjekkes én gang når bildet lastes, og ellers brukes veien med faktor. Målt: 0,6 ms mot 12 til 21 ms med vanlig palett, 9 ms mot 25 ms under nedtoning, og **0 ulike byte** i begge (faktoren rundes opp, og med høyst 255 i hver kanal gir det alltid samme heltall som divisjonen i dag). `composeCycled()` gjør allerede noe lignende for fargesykling.
2. **Samme grep for figurrutene:** en egen vei når ruten ikke er skalert eller speilvendt, og fargefaktoren fra tabellen.
3. **Bildebuffer på tvers av rom.** Figurrutene tilhører kostymet, ikke rommet, og bør ikke frigjøres ved rombytte. En buffer med tak på minnet (for eksempel 256 MB på PC og 96 MB på mobil og nett) som kaster det som er brukt minst nylig. Rommets egne bilder lastes ved rombyttet, mens skjermen er svart, i stedet for midt i første ramme.
4. **Verbhjulet:** tegn bare når noe har endret seg, og flytt tegningen inn i HD-laget når DigHD er portet (står allerede i todo).
5. **Ikke nå:** raskere bildeformat i modden (for eksempel QOI i stedet for PNG). Det løser bare lastingen, og punkt 3 tar det meste av den.

**Hvor endringene hører hjemme:** punkt 1 til 3 er i `0001-dighd-hd-grafikk.patch`, som skal være byte for byte lik den i Sam & Max HD. Optimaliseringen bør derfor gjøres i Sam & Max HD (eller The Dig), der HD-laget kjører og kan måles med `DIGHD_BENCH` og kontrolleres med `engine/test.sh` (0 avvik med en nearest-mod), og så kopieres hit. Alternativet er å gjøre det her sammen med porten, og da slutter 0001 å være lik.

## 4. Myk rulling: viktig for porten

- FM-Towns-utgaven av Zak ruller jevnt: `requestScroll()` legger 8 piksler i kø, og `towns_updateGfx()` flytter laget én piksel per 1/60 sekund (`TownsScreen::scrollLayer`, `gfx_towns.cpp`). Valget `smooth_scroll` er på som standard for FM-Towns.
- Med FM-Towns-laget slått av (`DISABLE_TOWNS_DUAL_LAYER_MODE`, HD-MOTOR punkt 1 a) finnes ikke dette: kameraet hopper 8 originalpiksler om gangen, som i DOS-utgaven. I HD blir det hopp på 32 piksler, og 34 av de 58 rommene er bredere enn skjermen.
- Det betyr ikke at a) er feil vei for å få HD-laget i gang, men myk rulling må lages i HD-laget før Tom spiller med skjerm, ellers ser HD-utgaven dårligere ut enn originalen den bygger på. To måter:
  - **I DigHD:** det virtuelle skjermbildet har allerede én stripe ekstra (`vs->pitch += 8` i `initVirtScreen`). HD-laget kan bygge 328 originalpiksler i bredden og vise et vindu på 320 som flyttes jevnt. I HD kan steget være én HD-piksel, altså jevnere enn originalen.
  - **Med FM-Towns-laget på** (HD-MOTOR punkt 1 b): krokene i `towns_drawStripToScreen`, og HD-laget speiler lag 0 med samme `hScroll`.
- Ikke prøvd. Bør avgjøres i starten av porten.

## 5. Shadere: det som virker i dag

ScummVM sin OpenGL-tegning har en libretro-pipeline: forhåndsoppsett (`.glslp`) med én eller flere passeringer i GLSL, med originalbildet (`Orig`), tidligere passeringer (`PassPrevN`), tidligere bilder (`Prev`), bildeteller og parametere. Shaderen kjøres på skjermkortet etter at spillet har tegnet bildet, så den koster ingenting for motoren.

- Bygget vårt har den: `USE_OPENGL_SHADERS = 1` i `config.mk`. `configure` slår den også på for GLES2, altså for nettversjonen når nettleseren har WebGL.
- ScummVM har med 451 shaderfiler i `gui/themes/shaders.dat` (CRT, xBRZ, ScaleFX, hqx, FXAA og flere). `tools/pakke_linux.sh` legger allerede `shaders.dat` i Linux-pakken.
- Velges med `--shader=` på kommandolinjen eller i ScummVMs grafikkvalg, og kan byttes mens spillet går (`g_system->setShader()`).

**Laget for Zak** (i `engine/shadere/`, egne filer, ikke kopiert):

| Oppsett | Hva | Til |
| --- | --- | --- |
| `klassisk-crt.glslp` | Skannlinjer med gaussisk stråle som blir bredere i lyse partier, skarp overgang langs linjen, svak skyggemaske og litt krumning. Parameteren `KILDEPIKSEL` sier hvor mange skjermpiksler én originalpiksel er: 1 uten HD-laget, 4 når HD-laget viser originalgrafikken | Originalgrafikken |
| `hd-glod.glslp` | Fire passeringer: lyse partier i en firedel av størrelsen, gaussisk uskarphet vannrett og loddrett, og til slutt originalbildet med gløden lagt til som lys, vignett, metning og kontrast. Svakt som standard | HD-bildet |

Prøv selv: `engine/run.sh ingen --shader=engine/shadere/klassisk-crt.glslp` (eller `--shader=crt/crt-lottes-fast.glslp` for en fra ScummVM).

**Testet 14. oktober:** Zak startet med OpenGL under Xvfb med programvare-OpenGL (Mesa llvmpipe, OpenGL 4.5), Esc for å hoppe over introen, skjermbilde av rom 1 etter 24 sekunder. Seks varianter: uten shader, `klassisk-crt`, `crt-lottes-fast`, `xbrz-freescale`, `scalefx` og `hd-glod` (her på originalgrafikken). Alle lastet uten feil i loggen og ga ulike bilder. Bildene er sendt til Tom og ligger ikke i repoet (de er laget fra spillets grafikk).

**Ikke testet:** på ekte skjermkort, i nettleseren (WebGL), på mobil, hastighet på svake skjermkort, og `KILDEPIKSEL = 4` sammen med HD-laget (som ikke er portet ennå).

**Begrensningen:** shaderen ser bare det ferdige bildet. Med HD-laget er det 1280 x 960, så pikselskalerere (xBRZ, ScaleFX, hqx) og vanlige CRT-shadere passer bare i klassisk modus, og CRT-en må få `KILDEPIKSEL = 4`. I HD-modus passer glød, vignett, fargejustering og skarphet.

## 6. Effekter knyttet til HD-valget (forslag, ikke laget)

- Spilleren velger allerede HD eller originalgrafikk med Ctrl+H og en rad i menyen (Tom 14. oktober). Effekten kan følge valget: `setClassic()` i DigHD kaller `g_system->setShader()` med shaderen for den modusen.
- Innstillinger: `dighd_effekt_hd` og `dighd_effekt_klassisk`, begge av som standard, så spillet starter som originalen.
- En rad i spillets meny, «Effekter»: av, glød (HD) eller CRT (klassisk). Virker på mobil uten tastatur.
- Shaderfilene må med i Linux-pakken og på nettsiden (i dag bare `shaders.dat`).

## 7. Effekter som trenger mer enn en shader på det ferdige bildet

| Effekt | Hvorfor etterbehandling ikke holder | Vei |
| --- | --- | --- |
| Lys med normalkart (planlagt etter stilpiloten, Tom 13. oktober) | Shaderen vet ikke hva som er rom, figur eller tekst, og har ikke normalkartet | På prosessoren i DigHD: statisk lys regnes inn i HD-rommet én gang når rommet lastes; figurene får lysfarge etter lyskildene der de står. Billig etter punkt 1 i del 3 |
| Glød bare fra lamper, skjermer og himmel | Det ferdige bildet vet ikke hva som lyser; `hd-glod` gløder fra alt som er lyst | En maske per rom (hva som lyser), lagt inn i HD-bildet ved lasting, eller sendt til skjermkortet |
| Myk rulling med HD-presisjon | Må gjøres der bildet bygges | Del 4 |
| Parallakse, partikler, vær | Nytt innhold i bildet. Remastermetoden sier purisme, ikke revisjon | Bare hvis Tom vil |

**Vei med skjermkortet:** ScummVM lar en motor tegne selv med OpenGL (`initGraphics3d`, `OpenGL::Shader`, brukt av blant annet Grim Fandango, Myst 3 og The Longest Journey). En blandet løsning: prosessoren avgjør fortsatt kilden for hver originalpiksel slik DigHD gjør nå (76 800 oppslag), og sender kartet til skjermkortet som en tekstur; skjermkortet tegner 4x, fargejusteringen, lyset og effektene. Gevinst: nesten ingen tid på prosessoren, og alle effekter per lag. Kostnad: tegnedelen av DigHD skrives om, verbhjulet og pekeren også; `lockScreen` virker ikke i den modusen (verbhjulet og miniatyrbildene i lagrede spill må lages på annen måte); libretro-shaderne gjelder ikke der, så etterbehandlingen må skrives selv; og nettsiden må prøves med WebGL. Anbefaling: ikke nå. Først optimaliseringen i del 3 og porten; vurder skjermkortet hvis lyset blir for tregt på mobil.

## 8. Det som ikke trenger forbedring

- ScummVM er låst til `c9091321` fra 6. oktober 2026, som er ny. SCUMM-tolkeren er ikke noe å optimalisere for Zak.
- Spillets egne skript er gammel kode, men gir ingen ytelsesgevinst, og de lappes ikke uten Toms ja (AGENTS).

## 9. Forslag til rekkefølge

1. Tom fletter PR-en med rettingen av patch 0002 (motoren bygger ikke fra `main` før det).
2. Myk rulling som krav i porten av DigHD (del 4).
3. Optimaliseringen i del 3, punkt 1 til 3, gjort i Sam & Max HD med `DIGHD_BENCH` og `engine/test.sh`, og 0001 kopiert hit.
4. Effektvalget i menyen (del 6), når HD-laget virker for Zak.
5. Lys med normalkart på prosessoren etter stilpiloten (del 7).
6. Skjermkortveien bare hvis 5 ikke holder på mobil, eller Tom vil ha effekter per lag.
