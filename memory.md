# memory.md

Faste fakta og beslutninger. Oppdateres når noe endrer seg.

## Mål
- HD-versjon av *Zak McKracken and the Alien Mindbenders* (FM-Towns-utgaven, SCUMM v3 med 256 farger): HD-bakgrunner, HD-objekter, HD-figurer og HD-tekst, lagt oppå originalen slik som i The Dig HD og Sam & Max HD.
- Tom vil ha det samme som for The Dig: spillet starter rett inn som originalen, HD eller originalgrafikk velges i spillets egen meny, det virker på mobil, og det finnes en komplett fil til nedlasting (Linux først).
- Tom ba 11. oktober om en utredning av et mer moderne grensesnitt (verbhjul som i Curse of Monkey Island og Full Throttle, eller ikoninventar som i Monkey Island 2) og større bilde. Utredningen er `docs/GRENSESNITT.md`.
- Tom valgte 12. oktober C: verbhjul som i Day of the Tentacle Remastered, og godkjente oppførselen samme kveld («Lag det»): urskive med tolv faste plasser (12 Pick up/Buy, 1 Open, 2 Close, 3 Use, 4 Give/Sell, 5 Turn on, 6 Turn off, 7 Put on, 8 Take off, 9 Read, 10 Push/Teleport to, 11 Pull), verb for objektet som standard og «alle verb» som valg, høyreklikk og hold-og-dra, teksten under hjulet, ikonene i samme stilpilot som rom 1. Tre ikoner (øye, hånd, tannhjul) ble frarådet: 97 av 489 objekter med verbkode får da et tvetydig valg.
- Verbhjulet er bygget som `engine/patches/0002-verbhjul.patch` (13. oktober), oppå 0001, som holdes lik den i Sam & Max. `tools/lag_patcher.sh` lager begge; `tools/verbhjul_test.sh` tester hjulet mot originalpanelet uten skjerm.
- Tom spurte om en egen inventarskjerm; svaret var nei: rommet er 2,5:1, så på 16:9 er det uansett plass til inventaret under rommet, og MI SE ble kritisert for å gjemme inventaret.
- Tom spurte 13. oktober om et dynamisk hjul (høyst fire valg, øye/hånd/bryter/snakkeboble, Fly utenfor hjulet, portretter for figurbytte). Målt: høyst fire går for 330 av 337 objekter med lik kode og tilstand (0 lukket/av, 1 åpen/på), sju trenger en regel hver. Zak har ikke Look at eller Talk to. Flyreiser går allerede gjennom Use på reservasjonsterminalen (rom 8 og 9) til reisemålskjermen (rom 45); Fly to er fuglen. Tom sa ja samme morgen (uten snakkeboble). Bygget: dynamisk utvalg er standard (`verbhjul_dynamisk`), reglene i `engines/scumm/verbhjul_zak.h` lages av `tools/verbhjul_dynamisk.py --cpp`, regler for hånd i `HAAND` i verktøyet. Et par (Open/Close, Turn on/off) slås bare sammen når begge sider sjekker tilstanden først; telefonsvareren, vasken i rom 2 og bryterne i rom 16, 25 og 35 har begge ikonene. Portretter for figurbytte nederst til høyre (`verbhjul_portretter`), Switch skjult mens de er på.
- DOTT Remastered sitt hjul viser verbene som gjelder objektet (PopMatters, PCWorld), ikke alle ni. GRENSESNITT.md sa først det motsatte; rettet 12. oktober.

## Spillfilene
- Original på Google Drive, mappen `Zak-fm` (id `1C4-aa3j3Jgso3Z2J00UYS3lfvNcxl4-Z`) i mappen `Scummvm` (id `1YpufOwLtohaVAPOdRxnIs4DHzO_0GcQ5`). `Scummvm` var fortsatt delt med lenke 11. oktober (fra Sam & Max-arbeidet), så filene ble hentet med curl.
- Utgave: engelsk FM-Towns. `00.LFL` MD5 `2d4536a56e01da4b02eb021e7770afa2`, i ScummVMs `scumm-md5.h` ved c9091321: zak, FM-TOWNS, 7520 byte, EN_ANY. `detection_tables.h`: versjon 3, GF_OLD256 | GF_AUDIOTRACKS.
- Filer: `00.LFL` (indeks), `01.LFL` til `59.LFL` (rom med skript, lyder og kostymer; `47.LFL` har ingen RO-blokk), `98.LFL` og `99.LFL` (tegnsett 1 og 0), `Track1.fla` til `Track21.fla` (CD-musikk, FLAC). 83 filer, 330 040 888 byte.
- Kopi i grenen `spilldata` (uten felles historikk med `main`) med `game/SHA256SUMS`. Ingen fil er over 90 MB, så ingenting er delt. Pushet i seks commits (rom og tegnsett, så sporene i fem grupper) 11. oktober.
- Spillfiler og alt laget fra dem (work/, mods/) skal aldri inn i main.

## Skriptene (12. oktober)
- Klikk går til globalt skript 11 (`VAR_VERB_SCRIPT`, satt i skript 7). Setningslinjen (verb 100) må ikke klikkes når en preposisjon venter uten objekt nummer to; da tømmer skript 11 setningen. Setningen: verb Var[116], objekt Var[117] og Var[118], preposisjon Var[119] (129 in, 130 with, 131 on, 132 to), standardverb Var[120] (3, Walk to). Objektet under musen finnes av skript 22 (Var[114]). Setningen kjøres ved andre klikk på samme objekt eller klikk på setningslinjen (verb 100). Skript 18 tømmer setningen. Var[300] er spillets tilstand (3 vanlig spill).
- Skript 11 beholder objektet når verbet byttes (Walk to lamp, så Use gir «Use lamp with»). Verbhjulet tømmer derfor setningen før verbet (Walk to om nødvendig, så setningslinjen), rettet 13. oktober. Skript 22 ser bare etter skuespillere når Give venter på mottakeren og for What is.
- Verb 1 til 14 er standardverbene, 15 Buy, 16 Sell, 17 Teleport to, 31 til 40 spesialmoduser (Switch, figurnavn, verb når man styrer dyr). Inventaret er verb 101 til 110, pilene 115 og 116.
- Romene har ingen navn i indeksen; beskrivelser i `docs/romnavn.csv`.

## Format (sjekket 11. oktober)
- Små blokkhoder: uint32 LE størrelse med hodet, så 2 tegn. Ikke kryptert.
- Indeksen: 0R (99 plasser, alle 0: rom N ligger i N.LFL), 0S (169 av 199), 0N (120 av 199), 0C (40 av 199), 0O (1000 objekter). Ingen RN.
- Skript, lyder og kostymer står som (rom, offset fra starten av rommets fil).
- Rommet: HD, BX, PA (256 farger), SA, BM, OI, OC, NL, SL, EX, EN, LC, LS. Ingen CC (ingen fargesykling).
- 58 rom med grafikk, alle 128 høye unntatt rom 46 (136), bredde 320 til 960 (34 brede). 43 med z-plan. 770 objekter, 585 med eget bilde (OI på 8 byte = ingen bilde). 40 kostymer i format 0x58, 847 ruter. 2 tegnsett med 226 tegn, 8 piksler høye.
- Stripekodekene er 1, 2, 3, 4 og 7 (GF_OLD256, `unkDecode8` til `11`), kolonne for kolonne. BM-data: uint32 lengde, uint32-offset per stripe, så z-planet (uint32 0 = ingen, ellers uint16-offset per stripe fra byte 4).
- Objekter har ett bilde (getObjectImage ser bort fra tilstanden). Uttrekket kaller det `objNNN_01`.
- Kostymer: CO-blokken har samme gamle hode som i v6 etter 8 byte; i v3 er startindeksen i animasjonene én byte. Rutenummer lag * 128 + kode.
- Figurer (ActorOps i skriptene): skuespiller 1 Zak (kostyme 1), 2 Annie (2), 3 Melissa (7), 4 Leslie (36).
- Skjermen 320 x 240: meldingslinje 0 til 15, rom 16 til 143 (`SetScreen(16,144)`), setningslinje 144, verb 152 til 175, inventar 176 til 215 (verb 101 til 110, piler 115 og 116).

## Oppsettet (11. oktober)
- Tom: gjør som The Dig- og Sam & Max-repoene, klargjør repoet, dekompiler og lag liste over grafikken som skal byttes ut.
- Kopiert fra Sam-Max-HD (main 5ef6f1f): `engine/` (patch og byggeskript), `pipeline/` (pakken `smhd` omdøpt til `zakhd`), `tools/`, `docs/`, `spill.sh`, `.github/workflows/`. Tilpasset Zak.
- Nye moduler: `pipeline/zakhd/lfl.py` (v3-filene), `v3grafikk.py` (dekodere oversatt fra ScummVM), `eksport_v3.py` (uttrekket), `grafikkliste.py` (listen). `gamedata.py`, `eksport_v6.py` og `v6grafikk.py` (v6/v7) står igjen, fordi v3-koden bruker deler av dem og for en mulig felles kodebase senere.
- Miljøvariablene `DIGHD_*`, klassen DigHD, patchnavnet og mod-formatet beholdes.
- Motoren må bygges med libFLAC (libflac-dev) for CD-musikken. `engine/build.sh` sier fra hvis den mangler.
- Grenene `hd-mod` (README og SHA256SUMS, ingen mod) og `gpt-arbeid` (AGENTS, BESTILLING, ORDRE uten jobber) er startgrener.
- Nettsiderepoet (planlagt `Tombonator3000/ZakMcKracken-HD-Web`) finnes ikke.

## Teknisk plan (ikke testet for Zak)
- DigHD er ikke på for Zak. FM-Towns tegner gjennom `towns_drawStripToScreen` (16-bits lag, 640 x 480 i ScummVM), som returnerer før DigHD-kroken i `drawStripToScreen`. Valg: slå av FM-Towns-laget (`DISABLE_TOWNS_DUAL_LAYER_MODE`) så v3 går gjennom vanlig 8-bits tegning, eller kroker i FM-Towns-tegningen. Anbefalt å prøve det første. Se `docs/HD-MOTOR.md`.
- Tekst tegnes av `CharsetRendererV3`; kroken for HD-glyfer finnes ikke der.
- Ingen blast-objekter, ingen filmer, ingen tale, ingen fargesykling i Zak.
- Kostymene (målt 13. oktober): 40 kostymer med 847 ruter, alle med speilflagg av, ingen søppelruter. Skyggeregelen fra Sam & Max (palettindeks 13 gjennom skyggetabellen) gjelder ikke: ScummVM setter `_shadowTable` bare for v5 og nyere, så i v3 er 13 en vanlig farge (kostyme 8 bruker den).
- Dynamisk lys (normalkart og luminansmaske) er planlagt etter stilpiloten: valgfritt for spilleren, ingen kastede skygger (Tom 13. oktober).
- ScummVM låst til c9091321, som The Dig og Sam & Max.

## Arbeidsform
- Roller: Claude koden, ChatGPT/Codex grafikken, Tom godkjenner.
- Claude får ikke flette sine egne PR-er (som i de andre repoene). Tom fletter når CI er grønn.
- Stilpilot med ett rom og ett figurark før noe bestilles i mengde. Glatt figurstil med ekte alfa fra starten. Forslag til pilot: rom 1 (Zaks leilighet) og kostyme 1 (Zak).

## Kildetro grafikk og design (12. oktober 2026)
- Tom ba om samme regel i remake-skillen i Dig, Sam & Max og Zak: avklar motiv, funksjon, palett, figuridentitet og design fra riktig originalkontekst før grafisk HD-arbeid, også stilpilot.
- Skillen ligger i `docs/skills/scumm-hd-remake/SKILL.md`. Den er koblet fra AGENTS, remastermetoden, bestillingen og malen for grafikkgrenen. Spillets egne stilvalg gjelder; Dig sine figurer og materialer er ikke designfasit for de andre spillene.
- Rett påviste feil i produksjonsgrunnlaget før generering. Beskyttede jobbfiler beholdes; korrigert prompt og kildebegrunnelse leveres i et separat notat.
- Visuell kontroll av mening, identitet og hele animasjoner i spillet kommer i tillegg til teknisk mottak. Innført regel er ikke bevis for at alle ressursene er analysert eller spilltestet.
- Referansebilder fra Tom (14. oktober 2026) ligger i `referanser/zak-hd-20261014/` i grenen `gpt-arbeid`: forsiden av The National Inquisitor (Caponian i cowboyforkledning med øyehull i hattekronen), figurarkene for Zak, Annie og Caponian v3 og rom 42 i Sam & Max-stil. Ikke sagt at de er godkjente stilankere.
- Deling (13. oktober 2026): Tom tillater at grafikk og annet fra spillet deles utenfor repoet til hans eget private bruk (egne enheter, private steder). Offentlige sider og pakker har fortsatt ingen spillgrafikk. Spillfilene og det som lages fra dem holdes fortsatt utenfor `main`.
