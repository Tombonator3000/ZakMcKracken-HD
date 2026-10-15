# memory.md

Faste fakta og beslutninger. Oppdateres når noe endrer seg.

## Mål
- HD-versjon av *Zak McKracken and the Alien Mindbenders* (FM-Towns-utgaven, SCUMM v3 med 256 farger): HD-bakgrunner, HD-objekter, HD-figurer og HD-tekst, lagt oppå originalen slik som i The Dig HD og Sam & Max HD.
- Tom vil ha det samme som for The Dig: spillet starter rett inn som originalen, HD eller originalgrafikk velges i spillets egen meny (også mens man spiller, Tom 14. oktober), det virker på mobil, og det finnes en komplett fil til nedlasting (Linux først).
- Tom ba 11. oktober om en utredning av et mer moderne grensesnitt (verbhjul som i Curse of Monkey Island og Full Throttle, eller ikoninventar som i Monkey Island 2) og større bilde. Utredningen er `docs/GRENSESNITT.md`.
- Tom valgte 12. oktober C: verbhjul som i Day of the Tentacle Remastered, og godkjente oppførselen samme kveld («Lag det»): urskive med tolv faste plasser (12 Pick up/Buy, 1 Open, 2 Close, 3 Use, 4 Give/Sell, 5 Turn on, 6 Turn off, 7 Put on, 8 Take off, 9 Read, 10 Push/Teleport to, 11 Pull), verb for objektet som standard og «alle verb» som valg, høyreklikk og hold-og-dra, teksten under hjulet, ikonene i samme stilpilot som rom 1. Tre ikoner (øye, hånd, tannhjul) ble frarådet: 97 av 489 objekter med verbkode får da et tvetydig valg.
- Verbhjulet er bygget som `engine/patches/0002-verbhjul.patch` (13. oktober), oppå 0001, som holdes lik den i Sam & Max. `tools/lag_patcher.sh` lager begge; `tools/verbhjul_test.sh` tester hjulet mot originalpanelet uten skjerm.
- Tom spurte om en egen inventarskjerm; svaret var nei: rommet er 2,5:1, så på 16:9 er det uansett plass til inventaret under rommet, og MI SE ble kritisert for å gjemme inventaret.
- Tom spurte 13. oktober om et dynamisk hjul (høyst fire valg, øye/hånd/bryter/snakkeboble, Fly utenfor hjulet, portretter for figurbytte). Målt: høyst fire går for 330 av 337 objekter med lik kode og tilstand (0 lukket/av, 1 åpen/på), sju trenger en regel hver. Zak har ikke Look at eller Talk to. Flyreiser går allerede gjennom Use på reservasjonsterminalen (rom 8 og 9) til reisemålskjermen (rom 45); Fly to er fuglen. Tom sa ja samme morgen (uten snakkeboble). Bygget: dynamisk utvalg er standard (`verbhjul_dynamisk`), reglene i `engines/scumm/verbhjul_zak.h` lages av `tools/verbhjul_dynamisk.py --cpp`, regler for hånd i `HAAND` i verktøyet. Et par (Open/Close, Turn on/off) slås bare sammen når begge sider sjekker tilstanden først; telefonsvareren, vasken i rom 2 og bryterne i rom 16, 25 og 35 har begge ikonene. Portretter for figurbytte nederst til høyre (`verbhjul_portretter`), Switch skjult mens de er på.
- DOTT Remastered sitt hjul viser verbene som gjelder objektet (PopMatters, PCWorld), ikke alle ni. GRENSESNITT.md sa først det motsatte; rettet 12. oktober.

- Verbhjulet i HD (15. oktober): Tom ba om grafiske ikoner som i DOTT og Sam & Max i stedet for pikslene. 15 egne tegnede ikoner (`tools/verbhjul_ikoner.py`, `grafikk/ui/`), bygget inn i motoren som base64-PNG (`verbhjul_ikoner.h`), tekst i Comic Neue Bold (OFL). HD-laget går for Zak også uten HD-pakke, så hjulet alltid er skarpt (`ZAKHD_LAV=1` slår av). Ikke godkjent av Tom ennå. Ingen munn: Zak har ikke Talk to.
- Grafikk fra ChatGPT (Tom 15. oktober: gjør klar): motoren leser `ui/verbhjul/<navn>.png` og `inventory/objNNN.png` fra modden; godkjente legges i `grafikk/ui/verbhjul-gpt/` og `grafikk/inventar/`. Inventaret vises som rutenett i HD (bilde eller navn) med hjulet på. `docs/inventar.csv`: 123 ting. Ingen bilder bestilt ennå.
- Lagring i Zak: bare spillets egen lagreskjerm (rom 50, sfinksen), åpnet med F5. ScummVMs meny fra DOS-utgavene skal ikke vises (Tom 15. oktober); DigHD-menykroken og avskjæringen av avslutning er av for Zak i 0002.
- `tools/lag_patcher.sh` lager bare 0002 som standard; 0001 er felles og endres ikke herfra.

## Spillfilene
- Original på Google Drive, mappen `Zak-fm` (id `1C4-aa3j3Jgso3Z2J00UYS3lfvNcxl4-Z`) i mappen `Scummvm` (id `1YpufOwLtohaVAPOdRxnIs4DHzO_0GcQ5`). `Scummvm` var fortsatt delt med lenke 11. oktober (fra Sam & Max-arbeidet), så filene ble hentet med curl.
- Utgave: engelsk FM-Towns. `00.LFL` MD5 `2d4536a56e01da4b02eb021e7770afa2`, i ScummVMs `scumm-md5.h` ved c9091321: zak, FM-TOWNS, 7520 byte, EN_ANY. `detection_tables.h`: versjon 3, GF_OLD256 | GF_AUDIOTRACKS.
- Filer: `00.LFL` (indeks), `01.LFL` til `59.LFL` (rom med skript, lyder og kostymer; `47.LFL` har ingen RO-blokk), `98.LFL` og `99.LFL` (tegnsett 1 og 0), `Track1.fla` til `Track21.fla` (CD-musikk, FLAC). 83 filer, 330 040 888 byte.
- Kopi i grenen `spilldata` (uten felles historikk med `main`) med `game/SHA256SUMS`. Ingen fil er over 90 MB, så ingenting er delt. Pushet i seks commits (rom og tegnsett, så sporene i fem grupper) 11. oktober.
- Spillfilene ligger bare i `spilldata`. Det som lages automatisk fra dem (work/, mods/) sjekkes ikke inn. Godkjent HD-grafikk kan ligge i `main` under `grafikk/` (Tom 14. oktober 2026).

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
- DigHD er på for Zak fra 15. oktober 2026. Valgt: FM-Towns-lagene av ved bygging (`DISABLE_TOWNS_DUAL_LAYER_MODE` i `config.mk`, lagt inn av `engine/build.sh` og `engine/build-web.sh`), så v3 går gjennom vanlig 8-bits tegning. Prisen er at myk rulling må lages i HD-laget. 0001 er felles med The Dig og Sam & Max og må holdes byte for byte lik.
- Noen rom farges om av skriptet med `SO_ROOM_COLOR` (`_roomPalette`). Rom 21 og 24 tegnes med hver indeks 144 høyere enn i uttrekket. DigHD viser da originalen, fordi indeksene ikke stemmer. Uttrekket må bruke omfargingen før HD-bildet lages. Rom 31 henger ved testhopp (skriptet, ikke HD).
- Testmiljø uten egne `XDG_CONFIG_HOME` og `XDG_DATA_HOME` kan gjøre at ScummVM henger ved start uten skjerm; sett dem som `engine/test.sh` gjør.
- Tekst tegnes av `CharsetRendererV3`; kroken for HD-glyfer finnes ikke der.
- Ingen blast-objekter, ingen filmer, ingen tale, ingen fargesykling i Zak.
- Kostymene (målt 13. oktober): 40 kostymer med 847 ruter, alle med speilflagg av, ingen søppelruter. Skyggeregelen fra Sam & Max (palettindeks 13 gjennom skyggetabellen) gjelder ikke: ScummVM setter `_shadowTable` bare for v5 og nyere, så i v3 er 13 en vanlig farge (kostyme 8 bruker den).
- Dynamisk lys (normalkart og luminansmaske) er planlagt etter stilpiloten: valgfritt for spilleren, ingen kastede skygger (Tom 13. oktober).
- ScummVM låst til c9091321, som The Dig og Sam & Max.
- FM-Towns-laget gir myk rulling (én piksel per 1/60 sekund, `smooth_scroll`). Slås laget av, må myk rulling lages i HD-laget (MOTOR-FORBEDRING del 4, 14. oktober).

## Nettsiden (14. oktober)
- Tom: «gjør så spillet kan kjøres fra github pages». Repoet var da offentlig igjen (endret 15.27) og hadde Pages slått på. Nettsiden publiseres fra dette repoet: https://tombonator3000.github.io/ZakMcKracken-HD/ , av `.github/workflows/pages.yml` ved push til `main` som endrer `engine/`. Ikke noe eget nettsiderepo.
- Pages fra et privat repo krever GitHub Pro. Blir repoet privat, må `engine/` og arbeidsflyten flyttes til et eget offentlig repo (Tom må lage det; økten får ikke lage repoer).
- Siden har bare motoren (GPL), temaer, nettsidekode og kildearkivet. Spillet hentes av nettleseren fra `game/` i `main` eller grenen `spilldata`, moden fra `mods/gpt/` eller `hd-mod`, med Toms lesenøkkel (`SOURCES` i `local-files.mjs`). Moden brukes bare med `mod.json`.
- Nettleserpatchene i `engine/patches-web` (HTTP-filsystemet og lerretet i fullskjerm) er fra Dig-HD-Web a8e4474, og legges på bare av `engine/build-web.sh`. Motorfilene hentes med sjekksum fra `build.json`.
- Spilt i Chromium med SwiftShader og en dummy-nøkkel gjennom proxyen (`tools/nettsidetest.py`): introen med CD-musikk, soverommet, gå og verbhjulet virker. Introen tar 120 til 175 sekunder i SwiftShader; testen venter til setningslinjen har tekst før den klikker.

## Ytelse og effekter (14. oktober)
- Tom ba om å sjekke om motoren kan optimaliseres og få nyere effekter og shadere. Utredningen er `docs/MOTOR-FORBEDRING.md`.
- ScummVM er ikke flaskehalsen; HD-laget er. Romdelen av `compose()` bruker 12 til 21 ms for hele skjermen (1280 x 960), 0,6 ms med tabell per palettindeks, byte for byte likt (`tools/ytelse/compose_bench.cpp`). Endringen hører hjemme i 0001, som er felles med Sam & Max, så den bør gjøres der.
- 15. oktober (Tom: «Gjør de to grepene»): kopi av uendrede HD-piksler i `compose()` (0001, 32-bits skjerm) og overlegg i verbhjulet som bare tegnes ved endring (0002); `verbhjul.cpp` delt i fire filer. Målt i spillet: `compose()` 4,7 til 5,9 ms ned til 1,6 til 2,7 ms. 0001 er da endret her og må kopieres til de tre andre repoene. Spillets skript refaktoreres ikke.
- ScummVM sine libretro-shadere virker i bygget vårt (`USE_OPENGL_SHADERS`, også GLES2 for nettet). Egne oppsett i `engine/shadere/`: `klassisk-crt` (parameter `KILDEPIKSEL`, 4 med HD-laget) og `hd-glod`. En shader ser bare det ferdige bildet; lys med normalkart og glød bare fra lamper må gjøres i HD-laget.
- Patchfilene flettes aldri for hånd: flettingen 13. oktober (087fd93) ga feil tall i hunk-hodene i 0002, og `git apply` kuttet verbhjul-filene uten feil. `tools/sjekk_patcher.py` og `motor.yml` stopper det nå.

## Arbeidsform
- Roller: Claude koden, ChatGPT/Codex grafikken, Tom godkjenner.
- Alt går rett i `main`, også kode, uten PR (Tom 14. oktober 2026: «Omgjør agent regler, legg alt til main»). Testene kjøres før push, og CI kjører etter. Før det gikk kode via PR som Tom flettet, fordi Claude ikke får flette egne PR-er.
- Stilpilot med ett rom og ett figurark før noe bestilles i mengde. Glatt figurstil med ekte alfa fra starten. Stilankerne ble godkjent 14. oktober (se under); de er ikke sett i motoren ennå.

## Kildetro grafikk og design (12. oktober 2026)
- Tom ba om samme regel i remake-skillen i Dig, Sam & Max og Zak: avklar motiv, funksjon, palett, figuridentitet og design fra riktig originalkontekst før grafisk HD-arbeid, også stilpilot.
- Skillen ligger i `docs/skills/scumm-hd-remake/SKILL.md`. Den er koblet fra AGENTS, remastermetoden, bestillingen og malen for grafikkgrenen. Spillets egne stilvalg gjelder; Dig sine figurer og materialer er ikke designfasit for de andre spillene.
- Rett påviste feil i produksjonsgrunnlaget før generering. Beskyttede jobbfiler beholdes; korrigert prompt og kildebegrunnelse leveres i et separat notat.
- Visuell kontroll av mening, identitet og hele animasjoner i spillet kommer i tillegg til teknisk mottak. Innført regel er ikke bevis for at alle ressursene er analysert eller spilltestet.
- Stilankere (Tom 14. oktober 2026): figurarkene for Zak, Annie og Caponian v3, rom 42 i Sam & Max-stil og forsiden av The National Inquisitor er godkjente stilankere. De ligger i `grafikk/stil/` i `main` og i `stil/` i `gpt-arbeid`, med beskrivelse i `grafikk/stil/README.md`. Stilen er lett Purcell-inspirert tegneserie. Annie har blå genser og svart skulderlangt hår (FM-Towns: rosa/magenta og kortere hår); arket gjelder. Caponianen: korallhud, svart dress, gult slips, øyehull høyt i cowboyhatten. Innholdet (motiv, plassering, positur) er fortsatt originalens.
- HD-grafikk i `main` (Tom 14. oktober 2026): godkjent HD-grafikk legges under `grafikk/`. Spillfilene ligger fortsatt bare i `spilldata`.
- HD av og på (Tom 14. oktober 2026): spilleren velger selv HD eller originalgrafikk mens spillet går, med Ctrl+H og en rad i menyen (for mobil). Valget lagres (`dighd_classic`).
- Deling (13. oktober 2026): Tom tillater at grafikk og annet fra spillet deles utenfor repoet til hans eget private bruk (egne enheter, private steder). Offentlige sider og pakker har fortsatt ingen spillgrafikk.

## Godkjent grafikk, 15. oktober 2026
- Tom godkjente alle de 21 øvrige karakterarkene, 15 verbikonene og 126 inventarfilene. The King v1 var unntaket: han skal ha svart Elvis-tupé på Caponian-hodet. Høye ekte øyne og langt smalt midtansikt skal beholdes.
- The King v2 er rettet med tupé og lagt i PR 11. Ny rettelse registreres ikke automatisk som godkjent.
- Neste spritesheet-bestilling gjelder bare Zak først, med godkjent Zak-master som identitetsanker.

## Retur på verbhjul, 15. oktober
- Toms rettelse: hender skal ha fem fingre, uten dressjakke eller erme. Begge hattikonene skal forestille fedora, med lav krone, midtfold og vanlig brem. Ny grafikkrettelse registreres ikke automatisk som godkjent.

- Andre retur på verbikoner 15. oktober: Tom avviste buy/give/take-off på nytt. Tellbare fingre alene er ikke nok; kontroller sammenhengende håndflate, tommelplassering og naturlig grep. Nye hender erstatter de tre avviste filene, uten automatisk godkjenning.
