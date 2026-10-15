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

## 2026-10-12 15:33 (Codex)
- Tom ba om regelen for kildetro motiv- og designanalyse i remake-skillen i Dig, Sam & Max og Zak. Oppdatert `docs/skills/scumm-hd-remake/SKILL.md` i Dig og lagt samme skill inn her i alle tre repoer.
- Regelen krever avklart originalkontekst, motiv, funksjon, palett, person/drakt og design før stilpilot eller nytegning. Hele animasjoner og sammensatte figurdeler kontrolleres visuelt i spillet i tillegg til teknisk mottak. Spillets egne stilvalg gjelder.
- Koblet regelen fra AGENTS, remastermetoden, bestillingen og malen for grafikkgrenen. Presisert at påviste feil i en prompt rettes i separat notat før generering når jobbfilene er beskyttet. Eksisterende godkjenninger gjelder fortsatt.
- Kontroll: skill-validatoren bestått for alle tre kopier, identiske skill-filer bekreftet med SHA-256, og lokale lenker og henvisninger til riktig repo kontrollert. `git diff --check` bestått. Ingen motor- eller pipelineendring; spillet er ikke startet på nytt og ingen ny grafikk er laget i denne oppgaven.

## 2026-10-12 23:25 til 23:40 (Claude)
- Tom: "Dekompiler zak". Sjekket AGENTS.md (Tom/Codex la inn remake-skillen og regelen om kildetro motiv og design i dag, 34eca10). PR 1 var flettet. Ny gren `dekompiler-lesbart` fra main.
- Dekompilerte alle skriptene på nytt fra main (`tools/dekompiler_skript.py`): 1094 skript uten feil, alle filene like som 11. oktober (bare tidspunktet i OVERSIKT.md er nytt).
- Nytt verktøy `tools/skriptoversikt.py`: et lesbart lag over utskriften fra descumm i work/skript. ROM.md (per rom: mål, objekter med navn og bilde, rom det leder til og kommer fra, figurer og kostymer), REPLIKKER.md (1309 replikker og meldinger per rom og skript, med taler der skriptene sier det), rom-koblinger.tsv (123 faste rombytter; 43 går gjennom variabler og er ikke med) og kostymer-i-rom.tsv (25). Stikkprøver lest mot skriptfilene. Ny enhetstest for tekstlesingen.
- Romnavn: indeksen har ingen, og bynavnene på reisekartet (rom 45) er bilder, ikke tekst. Skrev en beskrivelse av alle 58 rom med kilde i `docs/romnavn.csv` (objektnavn, replikker og bilder; rom 5 Lou's Loans og rom 59 The National Inquisitor står på bildene). Rom 48 og 56 er ikke avklart. `zakhd grafikkliste` leser filen, så `docs/rom-oversikt.csv` og `docs/grafikkliste.csv` har nå beskrivelsene. Første versjon av CSV-filen manglet sitering og ble skrevet på nytt med csv-modulen.
- Tom (23:30): gjør klar for C, verbhjul som i DOTT Remastered, med forslag om å slå sammen verbene til tre ikoner (øye, hånd, tannhjul).
  - Kildene om DOTT Remastered (PopMatters, PCWorld): hjulet viser verbene som gjelder objektet, ikke alle ni. GRENSESNITT.md sa at alle ni var med; rettet.
  - Målt i spillfilene: med alle verbene fordelt på tre ikoner får 97 av 489 objekter med verbkode et tvetydig valg (for eksempel skuffen i rom 1: Open og Pull åpner, Push og Close lukker; lampen har egen kode for Turn on, Turn off og Use). Med bare sju verb mister 145 objekter verb de har kode for. Med DOTT sin metode trengs ingen sammenslåing: 433 av 770 objekter trenger ikke hjul, de fleste andre har ett til tre verb, høyst sju.
  - Lest i skriptene: klikk går til globalt skript 11; setningen står i Var[116] til Var[119]; den kjøres ved andre klikk på samme objekt eller på setningslinjen (verb 100); Use får preposisjon fra klasse 1 til 4 (skript 21), Give alltid "to"; skript 18 tømmer setningen. Verb 31 til 40 er spesialmoduser.
  - Skrev `docs/VERBHJUL.md` (DOTT sin metode, oppførsel, kallene hjulet sender, to objekter, avbryt med Walk to, spesialmodus, ikoner, motorarbeid, tester og fire åpne spørsmål) og `docs/verbhjul-verb.csv` (verb, tekst, tast, plass, antall objekter med kode, forslag til ikonmotiv). Ikonbestillingen er ikke aktiv; motiv og design avklares først etter remake-skillen.
  - GRENSESNITT.md, todo og memory oppdatert med beslutningen.
- Til Tom: zak-skript.zip (work/skript med ROM.md og REPLIKKER.md), zak-sprites.zip (uttrekket uten indeksbildene) og kontaktark over rom (med beskrivelsene) og kostymer. Laget fra work/, ikke lagt i repoet.
- `pytest`: 37 bestått. Ingenting i motoren er endret, og verbhjulet er ikke bygget.

## 2026-10-12 23:48 til 2026-10-13 00:35 (Claude)
- Tom spurte hva den beste løsningen for verbhjulet er. Svar: urskive med tolv faste plasser, ett handlingsverb per plass, bare objektets verb som standard (som DOTT), høyreklikk og hold-og-dra, hele setningen som tekst, ikonene i stilpiloten. Tom: «Lag det». Han spurte også om det trengs en egen inventarskjerm; svar nei (rommet er 2,5:1, så på 16:9 er det plass til inventaret under rommet uansett, og MI SE ble kritisert for å gjemme inventaret).
- Ny gren `verbhjul` fra main (PR 2 var flettet, f2c5db9).
- Bygget hjulet i ScummVM: `engines/scumm/verbhjul.cpp` og `.h` (klassen VerbWheel, bare for zak på FM-Towns), med kroker i `ScummEngine::parseEvent` (hendelsene), starten av `checkExecVerbs` (ett klikk per ramme), `findVerbAtPos` og `drawVerb` (verb 1 til 17 skjules), `waitForTimer` (tegning rett før `updateScreen`, opprydding med skittent rektangel i FM-Towns-skjermen) og `doSentence` (logg). Lagt i en egen patch, `engine/patches/0002-verbhjul.patch`, oppå 0001.
- Hjulet sender de samme klikkene som originalpanelet gjennom skript 11: verb, objekt (klikk i rommet med `VAR_VIRT_MOUSE` satt for det ene kallet, eller inventarplassen), så setningslinjen (verb 100).
- Feil funnet og rettet underveis:
  - Ikonene overlappet (radius 30 og ikonradius 11). Med tolv plasser må radiusen være minst 3,86 ganger ikonradiusen; nå 40 og 10.
  - Etikettene var for brede på spillets 320 x 240-skjerm; nå tre bokstaver i konsollskriften, og hele setningen står under hjulet.
  - «Use ticket in door» ble tømt: skript 11 kjører skript 18 når setningslinjen klikkes før objekt nummer to er valgt. Hjulet sjekker nå preposisjonen først og klikker ikke setningslinjen da.
  - Navnekollisjon med `kVerbWalkTo` i verbs.h; konstantene heter nå kZak*.
- Testdriver i hjulet (`VERBHJUL_TEST`, `VERBHJUL_DUMP_DIR`): taster, klikk, høyreklikk, hold og dra, valg av ikon, skjermbilder og logg uten skjerm.
- `tools/verbhjul_test.sh`: originalpanelet og hjulet uten skjerm, samtidig, i rom 1 (introen går av seg selv til rom 1 med styring etter rundt 1300 rammer). Bestått med motoren bygget av `engine/build.sh` med begge patchene: like 8 setninger (Open door, Pull dresser drawer med hold og dra, Turn on lamp, Pull window shade, Turn on cat clock, Read ticket fra inventaret, Use ticket in door med venting), og avbrudd med høyreklikk tømmer setningen. Tok 3 minutter 23 sekunder.
- Prøvd for hånd uten skjerm: «alle verb» (døren får alle tolv), Ctrl+W av (originalpanelet tegnes igjen) og på (skjules igjen), og skjermbilder som viser at hjulet ryddes bort. ScummVM skrev ingen scummvm.ini i testmiljøet, så lagringen av valget er ikke bekreftet.
- `tools/lag_patcher.sh` lager 0001 og 0002 på nytt fra `engine/scummvm` og sjekker at de passer etter hverandre. Første versjon feilet når hjulfilene var endret (de holdes nå utenfor `git apply -R`), og ga 9 tegn lange hasher i `index`-linjene; nå `core.abbrev=8`, og 0001 er byte for byte lik den i Sam & Max.
- Dokumentert i VERBHJUL.md (oppførselen, motorarbeidet, testene, det som gjenstår), AGENTS (to patcher, nye verktøy), HD-MOTOR, SPILLTEST (taster og en kort spilltest), GRENSESNITT, README, spill.sh (hjelpetekst), todo, STATUS og memory.
- Ikke gjort: navnet under pekeren mens hjulet er lukket, F5-menyen, HD-tegning, de tegnede ikonene, prøving med skjerm, i nettleseren og på mobil.

## 2026-10-13 07:10 til 07:25 (Claude)
- Tom spurte om et dynamisk verbhjul: høyst tre eller fire ikoner per objekt, verb slått sammen (øye, hånd, bryter, snakkeboble), Fly utenfor hjulet (flybillett på skranken åpner kartet), figurbytte som portretter i et hjørne.
- Nytt verktøy `tools/verbhjul_dynamisk.py`: leser verbtabellene og objektkoden i work/skript og klassene i 00.LFL, og teller ikoner per objekt med tre regler: lik kode blir ett ikon (ikke når koden eller skript den starter leser verbet, ikke Give, ikke Use med preposisjon), og Open/Close og Turn on/off blir ett når koden følger tilstandsregelen 0/1 (globalt skript 31 og 32). `--tsv` skriver tabellen til work/.
- Resultat for 337 objekter med verbkode: i dag har 20 objekter 5 til 7 verb; med lik kode 7; med tilstand også 184 ett ikon, 96 to, 36 tre, 14 fire og 7 over fire (Sushi i fiskebollen, kommoden, våtdrakten, oksygentanken, mikrobølgeovnen, boom-boksen, fallskjermen). 26 objekter har verb med samme kode som må holdes adskilt (boom-boksen: skript 129 ser på verbet). Tilstandsregelen påvist for 30 av 56 Open/Close-par og 2 av 18 Turn on/off-par.
- Lest i skriptene: Zak har ikke Look at eller Talk to. Flyreiser går gjennom Use på reservasjonsterminalen (objekt 194 i rom 8, 220 i rom 9) med CashCard, som laster reisemålskjermen (rom 45, globalt skript 90, inndataskript 92). «Fly to» er Walk to når Zak styrer fuglen (skuespiller 6, skript 24 og 119). Figurbytte kan sende verb 36 og 37 til 40 som F1 til F4 i ScummVM.
- Skrevet inn i `docs/VERBHJUL.md` (ny del «Dynamisk hjul»). Ingenting bygget i motoren; venter på Toms svar.

## 2026-10-13 07:24 til 09:05 (Claude)
- Tom: «Ja gjør det» til dynamisk verbhjul og portretter, uten snakkeboble. PR 3 var flettet før målingen ble pushet, så ny gren `verbhjul-dynamisk` fra main med målingen plukket over.
- Lest i skriptene: de 42 parene (Open/Close, Turn on/off) som ikke fulgte tilstandsregelen påviselig, og de sju objektene med mer enn fire valg. `tools/verbhjul_dynamisk.py` skriver nå én regel per objekt (grupper, par med betingelse, filtre for inventar, rom og aldri) og tabellen `engines/scumm/verbhjul_zak.h` med `--cpp`. Regler for hånd står i `HAAND` med kilden. Feil funnet underveis: lokale skript ble fulgt fra globale skript (feil rom), skriving til Var[116] ble regnet som lesing, og par ble godtatt på bare `setState`; da ville telefonsvareren mistet avspilling av nye beskjeder. Nå kreves sjekk av tilstanden eller klassen på begge sider.
- Resultat: høyst fire ikoner for alle 337 objekter (rommet 202/89/36/10 for 1 til 4 ikoner, inventaret 42/59/21 for 2 til 4). Mistet fra hjulet: bare tre replikker (Give og Read på boom-boksen i rommet, Put on på fallskjermen).
- Motoren: dynamisk utvalg i `VerbWheel` (leser tabellen, velger ikon etter tilstand, klasse, variabel eller bit, sender ett verb av gruppen på verbets plass), portretter nederst til høyre som sender verb 37 til 40 som F1 til F4, Switch skjult mens de er på. Valgene `verbhjul_dynamisk` og `verbhjul_portretter`. Testkommandoer fkey, portrait, setvar, setbit, script og rules. `tools/lag_patcher.sh` tar med `verbhjul_zak.h`.
- Gjennomgang av koden med en egen agent: rettet at køede klikk ikke ble sjekket på nytt (nå sjekkes verb og figur når de sendes, og køen kastes ved rombytte), grensesjekk av betingelser (ved bruk; ved lesing var spillets størrelser ikke kjent, det ga advarsler for alle regler i første forsøk), grensesjekk i testkommandoene, tekstboksen klippes til skjermen, portrettklikk krever ikke synlig peker. Ikke rettet: taster og klikk i de tre eller fire rammene hjulet sender klikk går tapt (i todo).
- Testet: `tools/verbhjul_test.sh` med motoren fra `engine/build.sh`: 11 like setninger (blant dem Close på åpen skuff, kommoden, Turn off på katteklokken, bytte til Annie med portrett mot F2), venting, avbrudd, og alle 337 regler lest riktig. Hjulet uten dynamisk utvalg og Esc prøvd uten skjerm. `pytest`: 38 bestått (ny test for regelverktøyet). Patchene gir byte for byte samme kode som arbeidskopien; 0001 uendret.
- Ikke testet: med skjerm, i nettleseren og på mobil, reglene for hånd i spillet utenom kommoden, figurbytte der Switch kommer i spillet.
- Dokumentert i VERBHJUL.md, SPILLTEST.md, GRENSESNITT.md, AGENTS.md, README, spill.sh, STATUS, todo og memory.
## 2026-10-13 06:48 til 07:35 (Claude)
- Tom limte inn begrunnelsen for C (verbhjul som i DOTT Remastered, med forslag om tre ikoner: øye, hånd, tannhjul) og ba meg sjekke om hjulet er logisk.
- Sjekket AGENTS.md, memory, todo og log. Hentet LFL- og CD-filene fra `spilldata` (alle 83 sjekksummer stemmer), bygget descumm og dekompilerte de 1094 skriptene (uten feil), og bygget motoren med begge patchene. libsdl2-dev og libflac-dev måtte installeres i testmiljøet.
- Teksten: DOTT-delen stemmer (hjulet viser verbene for objektet, og den nye modusen gir bredere bilde ifølge TheSixthAxis). Full Throttle hadde aldri tekstverb, myntmenyen var med fra 1995. Thimbleweed Park beholdt verblisten nederst også på Switch (Vooks), så det er ikke et eksempel på hjul. «Færre verb enn du tror» stemmer ikke for Zak: tolv handlingsverb, og tre ikoner gir 97 tvetydige objekter (målt 12. oktober). Hjulet slik det er bygget følger DOTT, ikke treikonforslaget, og det er riktig.
- Gikk gjennom patch 0002 mot skript 11, 14, 15, 18, 19, 21 og 22. Filtreringen (bare verbene objektet har egen oppføring for) stemmer med skript 15, som bare slår opp objekt A (`getVerbEntryPoint`) og ellers sier «That doesn't seem to work». Give og Sell for alt i inventaret stemmer. Av de 77 objektene med oppføring 255 er nesten alle knapper og kart som virker med vanlig klikk; bare rug corner 109 sender alle verb videre til 107, så hjulet åpnes ikke på den (107 ligger ved siden av). Knappen hjulet sender som 0 (Local[2]) brukes bare av What is, så den spiller ingen rolle.
- Feil funnet og bekreftet i spillet uten skjerm: skript 11 beholder objektet når verbet byttes. Walk to lamp, så Use på ticket i hjulet, kjørte `doSentence 14 103 82` («Use lamp with ticket») med en gang. Originalpanelet viser «Use lamp with ticket» og venter på et klikk til. 102 objekter i rommene har preposisjonsklasse, så det ville skjedd ofte.
- Rettet i grenen `verbhjul-tom-setning`, PR 4: hjulet tømmer setningen før verbet (Walk to om et annet verb er valgt, så setningslinjen; skript 11 kjører da skript 18). Pilene i inventaret avbryter ikke lenger ventingen på objekt nummer to (ikke testet, krever flere ting i inventaret). VERBHJUL.md rettet: skript 22 ser bare etter skuespillere når Give venter og for What is.
- `tools/verbhjul_test.sh` har fått saken Walk to lamp, så Use ticket in door. Bestått med motoren bygget fra patchene: 11 like setninger, 3 minutter 38 sekunder. Første kjøring feilet fordi testen klikket setningslinjen utenfor teksten (x 160); flyttet til x 20. `pytest -m "not game"` 35 bestått, `node --test` 18 bestått. 0001 er byte for byte lik.
- Ikke gjort: pilene prøvd i spillet, prøving med skjerm og på mobil. Forslag lagt i todo: valg på vinkel i stedet for treff på ikonet, og spillkontroll.

## 2026-10-13 09:50 (Claude)
- Tom spurte om grafikkløsningene fra Sam & Max HD (fast størrelse, skygger, hovedark) kan brukes her, og om dynamisk lys med normalkart og luminansmaske. Han sa at Zak er FM-Towns, at kastede skygger ikke trengs, at lyset skal være valgfritt for spilleren og vente til stilpiloten er godkjent.
- Sjekket AGENTS, memory, todo og log. Hentet spillfilene (sjekksummene stemmer) og målte kostymene med `v3grafikk.decode_costume_v3`: 40 kostymer, 847 ruter, ingen over 640 x 400, alle med speilflagg av. Bare kostyme 8 (hostellet på Mars, rom 28) har piksler med palettindeks 13 (104 av 287 i 12 ruter).
- I ScummVM (c9091321) tegnes 13 gjennom skyggetabellen i `byleRLEDecode`, men `_shadowTable` settes bare for v5 og nyere i `actor.cpp` og er ellers null. I Zak er 13 derfor en vanlig farge, og skyggeregelen fra Sam & Max skal ikke tas med. Ikke sett i spillet.
- Lagt inn i todo: hva som kan tas inn fra Sam & Max PR 4, og dynamisk lys som forsøk etter stilpiloten. memory oppdatert. Ingen kode endret.

## 2026-10-13 10:32 (Claude)
- Tom viste Bernard, Laverne og Hoagie fra Day of the Tentacle, original og remaster side om side, og ba om at metoden legges i guiden for hvordan originalgrafikk gjøres om til HD.
- Nytt punkt «Fra piksel til HD-strek, slik DOTT Remastered gjorde det» under Figurstilen i `docs/skills/scumm-hd-remake/SKILL.md`, og en henvisning under forbildene: samme positur, silhuett og proporsjoner, hver pikselklynge tegnet som det den forestiller, samme farge per flate, ren mørk kontur, flate farger med ett skyggetrinn, ingen nye detaljer, hodet ikke større. Med forslag til engelsk prompttekst. Skillen er lik i Dig, Sam & Max og Zak (SHA-256 kontrollert).
- Kort avsnitt i `docs/HD-REMASTER-METODE.md`. Bildet er ikke lagt i repoet (grafikken tilhører Disney/Lucasfilm).
- 10:41 Presisert punktet om rom og objekter i skillen: malte bakgrunner beholder malt lys og fargeoverganger, figurene får flate farger. Skillen er lik i alle tre repoer.
- 10:46 Codex påpekte at DOTT-punktet i skillen tvang tegneseriestil på alle spill og påsto at Double Fine tegnet over originalen. Rettet: punktene om form (samme figur, pikselklynger blir det de forestiller, farge per flate, ingenting nytt) gjelder alle spill; ren strek og flate farger gjelder bare tegneseriespill (DOTT, Sam & Max, Zak), og The Dig beholder sin malte stil. Overskriften sier nå «sett i DOTT Remastered», ikke «slik de gjorde det». Skillen er lik i alle tre repoer.

## 2026-10-13 12:39 (Claude)
- Tom: tillat at det deles utenfor repoet, til hans eget private bruk. Regelen i AGENTS er endret: grafikk og annet fra spillet kan deles utenfor repoet til Toms private bruk (for eksempel testsider på GitHub Pages og filer til egne enheter). Spillfilene og alt laget fra dem holdes fortsatt utenfor `main` og kodegrenene.
- 12:45 Presisert etter Codex (Dig PR 48): privat deling gjelder egne enheter og private steder. Offentlige sider og pakker (GitHub Pages, releaser) har fortsatt ingen spillgrafikk, så README, Linux-pakken, SPILLTEST og PAGES stemmer som de er.

## 2026-10-14 08:47 (Claude)
- Tom sendte fem referansebilder til Zak HD og ba om at de legges i repoet. Sjekket AGENTS, memory, todo og log. Bildene er laget fra spillets figurer og hører ikke hjemme i `main`, så de ligger i `gpt-arbeid` under `referanser/zak-hd-20261014/` (ce4780b), med README og manifest.
- Fire av dem var byte for byte like konseptene Codex la i `gpt-arbeid` 13. oktober (Zak, Annie, Caponian v3, rom 42). Avisforsiden av The National Inquisitor er ny; Caponian-tegningen der har øyehull høyt i hattekronen, som i rettelse 03.
- Ikke lagt i `stil/` og ORDRE.md ikke endret, siden Tom ikke har sagt at de er godkjente stilankere. Spørsmålet står i todo.

## 2026-10-14 08:48 til 08:51 (Claude)
- Tom: «omskriv agents, det er greit å legge HD-grafikk til main. Spillet skal ha HD-valg, så spilleren selv velger HD eller vanlig mens man spiller.» Like etter: «de bildene er godkjente stilankere.»
- AGENTS skrevet om: HD-grafikk kan ligge i `main` under `grafikk/`; spillfilene ligger fortsatt bare i `spilldata`, og det som lages automatisk fra dem (work/, mods/, uttrekket, dekompilerte skript) sjekkes ikke inn. Ny regel: HD er alltid et valg for spilleren, også mens spillet går, med Ctrl+H (`DigHD::handleKey` i 0001) og en rad i menyen for mobil; valget lagres som `dighd_classic`. Grentabellen oppdatert.
- De fem bildene lagt i `grafikk/stil/` som godkjente stilankere, med README (stilen, figurenes utseende, kilder) og manifest med SHA-256 (sjekket mot filene). Samme filer i `stil/` i `gpt-arbeid`.
- Samme regel rettet i README, STATUS, memory, todo, .gitignore, HD-MOTOR (punkt 8), BESTILLING-CHATGPT (status, avsnitt 1, rekkefølgen, opphav) og gpt-arbeid-AGENTS (stilen følger ankrene, også Annies blå genser; innholdet er originalens).
- Funnet: romprompten i `pipeline/zakhd/gpt.py` (linje 90) ber om originalens pikselstil og farger, som ikke stemmer med ankrene. Lagt i todo; ingen kode endret.
- Ikke testet: ingenting i motoren er endret. HD-valget for Zak finnes ikke ennå, fordi HD-motoren ikke er portet.

## 2026-10-14 11:19 til 11:55 (Claude)
- Tom ba om å sjekke om koden og motoren kan forbedres og optimaliseres, og om nyere effekter og shadere kan legges til. Sjekket AGENTS, memory, todo, log, STATUS og HD-MOTOR, og leste DigHD (0001) og verbhjulet (0002).
- Funnet: motoren bygget ikke fra main. Flettingen 13. oktober 11.02 (087fd93, i GitHub) slo sammen to versjoner av `0002-verbhjul.patch` som tekst, uten å rette tallene i hunk-hodene (`verbhjul.cpp` 1226 mot 1233 linjer, `verbhjul.h` 245 mot 247). `git apply` kuttet filene uten feil, og byggingen stoppet på `unterminated #ifndef`. Med `git apply --recount` bygget alt, og `tools/verbhjul_test.sh` besto med den flettede koden (11 like setninger). Patchene laget på nytt med `tools/lag_patcher.sh` (bare hodene endret, 0001 uendret), og `engine/build.sh` fra ren kopi bygget.
- Ny `tools/sjekk_patcher.py` (teller linjene i hver hunk) i `test.yml`, og ny arbeidsflyt `motor.yml` som bygger motoren når en PR endrer patchene. Sjekken finner de to feilene i den gamle patchen og ingen i de andre versjonene. `motor.yml` bygget motoren grønt i Actions på PR 10. AGENTS: patchfiler flettes aldri for hånd.
- Målt den varmeste løkken i HD-laget med `tools/ytelse/compose_bench.cpp` (ScummVMs egne hoder, romdelen av `compose()` slik den står, mot tabell per palettindeks): hele skjermen 1280 x 960 tok 12 til 21 ms i dag og 0,6 ms med forslaget, under nedtoning 25 og 9 ms, 0 ulike byte i begge. Ikke endret i 0001, som er felles med Sam & Max.
- Lest i koden, ikke målt: figurrutene deler per underpiksel også uten skalering; `clearRoom()` frigjør figurrutene ved hvert rombytte, så de dekodes på nytt; verbhjulet låser skjermen hver gang den oppdateres mens portrettene vises.
- Lest i ScummVM: FM-Towns-laget ruller jevnt (én piksel per 1/60 sekund). Med laget slått av (HD-MOTOR punkt 1 a) hopper kameraet 8 originalpiksler, 32 i HD. Skrevet inn i HD-MOTOR og todo.
- Shadere: bygget har `USE_OPENGL_SHADERS` (libretro, også GLES2 for nettet), og `shaders.dat` har 451 filer. Laget `engine/shadere/klassisk-crt.glslp` (CRT med `KILDEPIKSEL` for forhåndsskalert bilde) og `hd-glod.glslp` (glød i fire passeringer, vignett, metning, kontrast). Prøvd under Xvfb med Mesa llvmpipe: Zak med OpenGL, Esc forbi introen, skjermbilde av rom 1 etter 24 sekunder, med ingen shader, de to egne, `crt-lottes-fast`, `xbrz-freescale` og `scalefx`. Alle lastet og ga riktig bilde. Bildene sendt til Tom, ikke lagt i repoet. Ikke prøvd på ekte skjermkort, i nettleseren eller på mobil.
- Utredningen er `docs/MOTOR-FORBEDRING.md`, med forslag til rekkefølge. todo, STATUS, memory, AGENTS og HD-MOTOR oppdatert. Alt i PR 10 fra grenen `motor-patch-og-ytelse`.

## 2026-10-14 12:00 til 12:10 (Claude)
- Tom: «Omgjør agent regler, legg alt til main.» Lest som: kode går rett i `main` uten PR, og arbeidet fra PR 10 legges i `main`. Grenene `spilldata`, `hd-mod` og `gpt-arbeid` er som før, og ikke-godkjent grafikk ligger fortsatt i `gpt-arbeid`.
- AGENTS: alt committes rett i `main`, også kode. Hent `main` før arbeid og push, små commits som bygger, testene før push (for motoren minst `tools/sjekk_patcher.py` og `engine/build.sh`, og `tools/verbhjul_test.sh` når hjulet er endret), CI etter hver push og rød CI rettes med en gang. Godkjent grafikk legges rett i `main`. Reglene gjelder foran flytregelen i remake-skillen, som er felles med The Dig og Sam & Max og ikke er endret.
- Samme regel rettet i memory, STATUS, todo, MOTOR-FORBEDRING, HD-REMASTER-METODE, gpt-kodeoppgaver og gpt-arbeid-AGENTS (Codex: kode rett i `main`, grafikk fortsatt bare i `gpt-arbeid`), og i AGENTS.md i grenen `gpt-arbeid`. Todo: PR 4 var flettet (8eaeb88).
- Grenen `motor-patch-og-ytelse` spolt fram inn i `main` (ingen flettecommit), og PR 10 lukket.

## 2026-10-14 12:07 til 12:15 (Claude)
- Tom: «Alt inn i main», som svar på om grenene `spilldata`, `hd-mod` og `gpt-arbeid` også skulle inn i `main`.
- Plan: én flettecommit med alle tre som foreldre, `spilldata` til `game/`, `hd-mod` til `mods/gpt/` og `gpt-arbeid` til `gpt-arbeid/`, og så verktøyene (spill.sh, hent_spilldata.sh, mod_gren.sh, gpt_gren.sh, gpt_runde.sh, linux.yml, test.yml, .gitignore, nettsidekoden) og reglene skrevet om til mappene i `main`.
- Sikkerhetskontrollen i Claude-økten stoppet flettingen før den startet (begrunnelse: endring av delte ressurser). Trolig fordi spillfilene til Disney/Lucasfilm da havner i standardgrenen til et offentlig repo. Ingenting er endret i noen gren. Venter på Toms valg.

## 2026-10-14 12:15 til 12:45 (Claude)
- Tom valgte først å flette selv med repoet offentlig, så å gjøre repoet privat. Tom gjorde det privat (sjekket: `visibility` er `private`). Økten fikk ikke endre synligheten selv (GitHub-forbindelsen stopper endringer i repoets innstillinger, HTTP 403).
- CI-sjekken «Ingen spillfiler i grenen» erstattet med en sjekk av `work/` og filer over 90 MB (b17af77), så flettingen ikke gir rød CI.
- Oppskriften for flettingen prøvd i en lokal kopi som ikke ble pushet: flettecommit med fire foreldre, 85 filer i `game/` med riktige sjekksummer, `mods/gpt/` og `gpt-arbeid/` som i grenene.
- Claude prøvde å flette etter at repoet ble privat; sikkerhetskontrollen stoppet det igjen («Out-of-Place Publication»). Ingenting ble endret. Flettingen må gjøres av Tom; oppskriften står i todo.
- Forberedt og testet mot den flettede kopien (31 filer): `spill.sh`, `tools/hent_spilldata.sh`, `tools/mod_gren.sh`, `tools/gpt_gren.sh`, `tools/gpt_runde.sh`, `tools/pakke_linux.sh`, `linux.yml`, `.gitignore`, nettsidekoden (én filliste over `main`), `zakhd` (`--gren` og `--stil` i `gpt-arbeid/`), AGENTS (tabellen Mapper i main, repoet privat), README, memory, STATUS, todo, SPILLTEST, PAGES, BESTILLING, ANALYSE, HD-REMASTER-METODE, `gpt-arbeid/AGENTS.md` med malen (malen fikk linjen som bare sto i grenen), grafikk. Testet: `node --test` 18 bestått, `pytest` 38 bestått (også spilltestene), `bash -n` på alle skript, `hent_spilldata.sh` og `mod_gren.sh hent` mot kopien. Ikke kjørt: hele `spill.sh`, en grafikkrunde og Linux-arbeidsflyten.
- Lagret som `claude/alt-i-main.patch` i Claude-prosjektet, siden Tom venter med flettingen til han har en terminal.

## 2026-10-14 15:27 til 16:20 (Claude)
- Tom: «gjør så spillet kan kjøres fra github pages». Sjekket AGENTS, memory, todo, log, PAGES og remake-skillen, og hentet nettsideoppsettet fra Dig-HD-Web (a8e4474) til sammenligning.
- Funnet: repoet var offentlig igjen (endret 15.27) og hadde Pages slått på, men ingenting publisert (404). Nettsiden publiseres derfor fra dette repoet, ikke fra et eget nettsiderepo. Grenen `spilldata` med spillfilene er da også offentlig; spurt Tom om synligheten (todo).
- Funnet: nettsiden ville ha stoppet med «Velg HD-mappen som inneholder mod.json og rooms», fordi grenen `hd-mod` finnes med bare README og SHA256SUMS. Bekreftet med den gamle koden i en egen test.
- `engine/pages/local-files.mjs`: spillet fra `game/` i `main` og ellers fra grenen `spilldata`, moden fra `mods/gpt/` i `main` og ellers fra `hd-mod`, og bare når det finnes `mod.json`. `main` leses én gang. Siden virker dermed både før og etter flettingen Tom vil gjøre. Nye nodetester for begge oppsettene (20 bestått).
- `engine/pages/player.mjs`: motorfilene hentes med sjekksummen fra `build.json` i adressen (fra Dig-HD-Web), så en ny motor ikke blandes med en gammel fra hurtiglageret.
- `engine/build-pages.py`: sjekker hele patchstakken i en egen indeks (fra Dig-HD-Web; den gamle sjekken så bare på 0001), og kildearkivet tar nå med `verbhjul.*`, `verbhjul_zak.h`, alle patchene og testene. Før manglet verbhjulet i arkivet. `engine/tests/test-build-pages.py` (4 bestått) i `test.yml` og `pages.yml`.
- `engine/patches-web/`: HTTP-filsystemet og lerretet i fullskjerm fra Dig-HD-Web, lagt på bare av `engine/build-web.sh`. Alle fire patchene lagt på ScummVM c9091321 med `git apply`, og `verify_patches` godtok stakken. `tools/sjekk_patcher.py` sjekker også `patches-web`. `engine/tests/test-http-fs-cache.sh` fra Dig-HD-Web.
- Ny arbeidsflyt `.github/workflows/pages.yml`: tester, Emscripten-bygget, testen av HTTP-filsystemet, pakkingen, sjekk av at pakken ikke har spillfiler eller bilder, og publisering med `deploy-pages`. Sjekker ut bare `engine/`, `docs/PAGES.md` og `tools/sjekk_patcher.py`. Pushet c0509c7; første kjøring grønn (bygget 4,5 minutter, publisert 13.44 UTC). https://tombonator3000.github.io/ZakMcKracken-HD/ svarer 200.
- Spilt i Chromium 141 med SwiftShader og en dummy-nøkkel mot den publiserte siden (`tools/nettsidetest.py`, nytt): nøkkelsiden, fillistene fra `main`, `spilldata` og `hd-mod`, tittelbildet, introen med CD-sporene 5, 8 og 14, og Zak i soverommet. Klikk på gulvet fikk Zak til å gå, klikk på akvariet ga «Walk to Sushi in fish bowl», og høyreklikk holdt over telefonsvareren åpnet verbhjulet med Off og On. Ingen feil i konsollen. Siden hentet bare motor, temaer og nettsidekode; spillfilene kom bare fra api.github.com. Som Pixel 7 (stående) kom introen opp, men SwiftShader var for treg til å nå spillet.
- Ikke prøvd: Esc forbi introen (et Esc etter 40 sekunder gjorde ingenting synlig), F5-menyen, lagring, fullskjerm, lyden med ører, Firefox, Safari og en ekte telefon.
- PAGES, STATUS, SPILLTEST, README, AGENTS, memory og todo oppdatert.
- 16:30 Løsningskortet `nettside-med-github-api-i-sandkassen` lagt i prosjektbiblioteket (f89f2a1). `claude/alt-i-main.patch` i Claude-prosjektet går ikke rett på etter nettsidearbeidet; `git apply --3way` med `local-files.mjs`, testen og PAGES.md utelatt er skrevet i todo og i `claude/zak-hd-status.md` (prøvd for README.md: fletter uten konflikt). Patchen sier at repoet er privat; det stemmer ikke nå.

## 2026-10-15 05:26 (Claude)
- Tom (i Dig-økta): «fiks zak fmtowns». Først den felles motorpatchen inn her, så porten av HD-laget til FM-Towns.
- `engine/patches/0001-dighd-hd-grafikk.patch` byttet til den felles patchen for The Dig og Sam & Max (byte for byte lik Dig main bf582dc og Sam & Max main 3598f39). 0002 (verbhjulet) legger seg uendret oppå. `engine/patches-web/0001` laget på nytt oppå den nye 0001 (den felles patchen har sin egen retting av lekkasjen i HTTP-filsystemet); filene blir de samme som før.
- Testet: `engine/build.sh` bygget (spillfilene hentet), `tools/verbhjul_test.sh` bestått (11 like setninger, venting, avbrudd og figurbytte), `tools/sjekk_patcher.py` (4 patcher), `test-build-pages.py`, nodetester (20), og hele stakken med nettleserpatchene lagt på c9091321.

## 2026-10-15 05:51 (Claude)
- HD-laget slått på for Zak FM-Towns. Valgt vei a) fra HD-MOTOR: FM-Towns-lagene av ved bygging (`DISABLE_TOWNS_DUAL_LAYER_MODE`, lagt i `config.mk` av `engine/build.sh` og `engine/build-web.sh`). Zak går da gjennom den vanlige 8-bits tegningen der DigHD henger.
- Den felles 0001 endret på tre steder, alt bare for Zak: `DigHD::create` godtar `GID_ZAK` (og sier fra og er av i et bygg med FM-Towns-lagene på), objektene slår opp `_01` uansett tilstand i v3, og testhoppet sammenligner romhøyden med spillflaten. 0001 må kopieres til The Dig, Sam & Max og Dig-HD-Web.
- Testet uten skjerm med en nearest-mod: `engine/test.sh` 3000 bilder, 12 av 12 kontroller uten avvik (rom 46, 58, 51, 55); Esc forbi introen til soverommet, Zak med HD-ruter, 13 av 13; `tools/verbhjul_test.sh` med HD på bestått, hjulet riktig på 1280 x 960; testhoppet til rom 2; fersk `RECONFIGURE=1 engine/build.sh` tar med definisjonen. `engine/test.sh` stopper nå med kode 1 ved avvik.
- Funnet underveis: uten egne XDG-mapper hang ScummVM ved start uten skjerm (ikke HD-laget).
- Igjen: myk rulling, HD-tekst i `CharsetRendererV3`, menyraden, pekeren, romtesten i alle rom (kjører), prøving med skjerm.

## 2026-10-15 06:07 (Claude)
- Den felles 0001 er nå byte for byte lik i alle fire repoene: Dig-HD-Remake PR 55 (8bc0ddc), Sam-Max-HD PR 23 (0bdb64a) og Dig-HD-Web PR 2 (2dc5be3) flettet etter grønn CI. Her var a73125d grønn i test, motor og pages.
- Romtesten med nearest-mod i alle 59 rom: 52 med HD-bakgrunn, ingen krasj, 0 avvik mot full ombygging. Rom 13 og 55 svarte, 15 og 37 forlatt før første bilde, 46 er startrommet, 47 er tomt.
- Rom 21 og 24 viste 39 og 42 prosent originalpiksler. Kjørt rom 21 for hånd med gult der HD mangler og `DIGHD_DEBUG_PIXEL`: spillet tegner hver indeks 144 høyere enn uttrekket (26 blir 170, sand i stedet for rødt) fordi skriptet fargelegger om med `SO_ROOM_COLOR` (`_roomPalette`). DigHD gjør rett i å vise originalen der. Uttrekket må ta med omfargingen; står i todo.
- Rom 31 henger ved testhoppet i rommets eget inngangsskript (gdb: `runEntryScript` > `o5_startScript` > `runScriptNested`, 100 prosent CPU), også med `DIGHD_CLASSIC=1`. Ikke HD-laget.
- `tools/romtest.py` regner fortsatt med skjermen fra Sam & Max (320 x 200); står i todo.
- HD-MOTOR, STATUS og todo oppdatert.

## 2026-10-15 08:24 til 09:05 (Claude)
- Tom: «kan man lage verb hjul som ser bedre ut og med grafikk? feks hand munn etc sånn som day of tentacle og sam og max? se veldig pixelert ut nå.» Sjekket AGENTS, memory, log (HD-laget ble slått på for Zak i natt) og VERBHJUL.
- Årsak til pikslene: uten HD-pakke var HD-laget av, så hjulet ble tegnet på spillets 320 x 240-skjerm med tre bokstaver i konsollskriften. Med HD-laget var det runde flater uten myke kanter.
- Svart Tom: Zak har ikke Talk to, så en munn har ingen jobb i hjulet uten nye skript.
- Nytt `tools/verbhjul_ikoner.py`: 15 ikoner tegnet som SVG (hånd som dytter, neve som drar, hånd som griper, hånd som gir, dør åpen og lukket, lyspære på og av, hatt på og av, øye, tannhjul, mynter, glimt), egne tegninger i stilen fra stilankerne. SVG og PNG i `grafikk/ui/verbhjul/`, skriften Comic Neue Bold (OFL, fra google/fonts) i `grafikk/ui/skrift/`. Skriptet lager `engines/scumm/verbhjul_ikoner.h` med PNG-ene og skriftbildet i base64 (270 kB).
- Patch 0002: hjulet tegnes i HD med myke kanter (skygge, gul ring og større ikon under pekeren, tekstboks med verbet i gult), ikonene glir ut fra klikket, og pikslene under tas vare på så kantene ikke mørkner ramme for ramme. HD-laget går nå også uten HD-pakke for Zak (`VerbWheel::defaultHD`, `ZAKHD_LAV=1` slår det av). 16 og 32 bits skjerm. 0001 uendret. `tools/lag_patcher.sh` kjenner den nye filen; den kunne ikke trekke fra krokene i den gamle 0002 fordi kroken i scumm.cpp fikk nye linjer ved siden av, så 0002 ble laget én gang ved å diffe mot commit + 0001. Etterpå gir `lag_patcher.sh` den samme 0002 byte for byte.
- Testet: uten skjerm med programvaretegning (lampen, katteklokken, billetten i inventaret, med pekeren på ikonet, og lukket igjen: pikslene tilbake), under Xvfb med OpenGL (skuffen), `tools/verbhjul_test.sh` bestått (11 like setninger), hele stakken med nettleserpatchene lagt på c9091321, `sjekk_patcher.py`, `test-build-pages.py`, nodetestene (20).
- Nettsiden: lisensen til skriften legges i `licenses/`, og credits nevner den.
- Ikke testet: med ekte mus og skjerm, på telefon. Ikonene er ikke godkjent av Tom.
- 08:57 Tom: «gjør klar for at verbhjul kan bruke ekte grafikk fra gpt etterhvert, og at alle inventory objekter klargjøres for å vise grafikk istedet for text.»
- 09:05 Nettsiden bygget og publisert med det nye hjulet (pages grønn for 98e56cf); prøvd i Chromium mot github.io: hjulet med lyspære og tannhjul og navnet «lamp» i HD.

## 2026-10-15 09:00 til 09:40 (Claude)
- Patch 0002: motoren leser `ui/verbhjul/<navn>.png` fra HD-modden i stedet for det innebygde ikonet, og `inventory/objNNN.png` for tingene i inventaret. Inventaret vises (med hjulet på og HD-laget) som et rutenett i HD: fem ruter i to rader der panelet og tekstinventaret var, pilene som gule trekanter, bildet eller navnet i HD-skrift, navnet over ruten under pekeren. Klikkene går til de samme verbplassene (101 til 110, 115, 116) gjennom en krok i `findVerbAtPos`, så skriptene ser ingen forskjell. Når panelet viser verb 31 til 40 der rutenettet ville vært, brukes tekstinventaret. `verbhjul_inventar` / `VERBHJUL_INVENTAR=0` slår det av.
- Overleggene (hjulet og inventaret) legger nå spillets piksler tilbake før hver ramme, hjulet først, og tegnes så på nytt.
- `tools/lag_patcher.sh` lager nå bare 0002 (oppå uendret 0001) som standard; første forsøk la den nye kroken i verbs.cpp i 0001. 0001 er fortsatt byte for byte den felles. `--ny-0001` gir den gamle måten.
- `pipeline/zakhd/modpack.py`: `build_ui` tar med `grafikk/ui/verbhjul-gpt/` og `grafikk/inventar/` (og `--egne`) i modden; ny pytest. `local-files.mjs` tar med de nye stiene; ny nodetest. Nye `tools/inventarliste.py` og `docs/inventar.csv` (123 ting, 98 med bilde i rommet). Bestillingen beskrevet i BESTILLING-CHATGPT (ikke bestilt), README i `grafikk/inventar/` og `grafikk/ui/verbhjul-gpt/`.
- Testet: uten skjerm med en testmod (et testbilde for billetten og et omfarget Use-ikon): bildet i ruten, navnet over ruten, hjulet åpnet på ruten med ikonet fra modden; uten mod navnet i ruten; `tools/verbhjul_test.sh` bestått (11 like setninger); hele stakken lagt på c9091321; pytest 37, nodetester 21, sjekk_patcher, test-build-pages.
- Ikke testet: pilene med mer enn ti ting, ruten når panelet viser figurnavnene, ekte mus og telefon.

## 2026-10-15 09:21 til 09:55 (Claude)
- Tom (med skjermbilder fra nettsiden): to forskjellige lagremenyer, og den ene er ødelagt (blå ramme med tomme knapper oppå rommet og oppå sfinksen). Bare FM-Towns-menyen skal vises.
- Årsak: DigHD-kroken i 0001 (`digHDMenuKey`) åpner ScummVMs gjenskaping av menyen fra DOS-utgavene (`showMainMenu`) på F5, F1 og Ctrl+K når HD-laget går. For The Dig er det riktig. For Zak FM-Towns, der HD-laget nå alltid går, stjal den tasten fra spillets egen lagreskjerm (rom 50, sfinksen med Play, Save og Load), og F1 fra figurbyttet. Menyen fra DOS er ikke laget for FM-Towns og tegnes feil.
- Rettet i 0002 (0001 uendret): kroken gjelder ikke Zak (`!_verbWheel`), så F5 går til spillets skript som i originalen, og F1 til F4 velger figur. Avskjæringen av avslutning gjelder heller ikke Zak, fordi sfinks-skjermen ikke har Quit; lukking av vinduet gir ScummVMs eget spørsmål. Alt+Q åpner sfinks-skjermen.
- Testet uten skjerm (`tools/verbhjul_test.sh` bestått etterpå): F5 i soverommet gir rom 50 med «Select SAVE or LOAD», klikk på SAVE, en linje og skriving av «test» vises som i originalen. Ikke testet: lagring ferdig og lasting etter omstart, F1 til F4 når figurbytte er slått på, lukking av vinduet.

## 2026-10-15 09:41 til 10:30 (Claude)
- Tom: «1: lag en liste med objekter og hvordan de ser ut til gpt som skal lage grafikk til verb hjul og inventory, legg dette i repo så chatgpt ser det. 2: sørg for at inventory fyller hele underdelen der inventory text sto før og de gamle verb listene, så vi utnytter all plass under scenen.»
- Rutenettet fyller nå hele området under setningslinjen (spillets y 153 til 239): fem ruter i to rader på x 1 til 271 (ruter på omtrent 54 x 43), pilene øverst og nederst i kolonnen til høyre, og portrettene to og to mellom dem (de flyttes når rutenettet slås av og på). Navnet under pekeren står nederst i ruten, over bildet, så setningslinjen ikke dekkes.
- Funnet i skriptene (`setObjectName`): flere ting bytter navn og utseende (fish bowl med og uten Sushi og teipet, lit lighter, lit flashlight, phone bill map, wallpaper map, yellow crayon, bent butter knife, recording boom box). Motoren velger nå `inventory/objNNN-<navn>.png` for navnet tingen har, og `objNNN.png` ellers. Nettsiden og `build_ui` tar med variantene.
- Ny `docs/GRAFIKK-HJUL-OG-INVENTAR.md`: felles krav (stil, 512 x 512, alfa), de 15 ikonene med motiv på engelsk, og alle 123 tingene fra `inventar.csv` slått sammen der samme ting finnes flere steder, med filnavn, varianter, rom, om den havner i inventaret (ja, usikker, trolig ikke), utseende og motiv på engelsk. Kontrollert at alle objektnumrene er med. Bildene av objektene i rommene viser for det meste stedet tingen ligger, ikke tingen, så utseendet er skrevet ut fra navn, rom og bruk; usikre er merket. Henvist fra BESTILLING-CHATGPT, gpt-arbeid-AGENTS, VERBHJUL og `grafikk/inventar/README.md`, og lagt i grenen `gpt-arbeid`.
- Testet uten skjerm: det store rutenettet med portrettene, navnet nederst i ruten, variantbildet for billetten (obj082-ticket.png) valgt foran obj082.png; `tools/verbhjul_test.sh` bestått; nodetester 21, `build_ui`-testen.
- Listen lagt i grenen `gpt-arbeid` (6e95ba2) med henvisning i AGENTS.md der. `tools/verbhjul_test.sh` bestått etter alle endringene.

## 2026-10-15 10:14 til 10:50 (Claude)
- Tom: «husk vi må også ha figur ikon velger å trykke på når det er mulig med flere å styre. 2: vil også at musehjul skal kunne bevege seg opp og ned mellom inventory ikke bare trykke på pilene.»
- Portrettene: fire tegnede portretter i mynt (Zak, Annie, Melissa, Leslie) i `tools/verbhjul_ikoner.py` og `grafikk/ui/portretter/`, farger fra figurarkene og spillets figurer (Melissa lyst hår og blå-lilla drakt, Leslie rødbrunt krøllete hår og rosa drakt). Med rutenettet tegnes de i HD i kolonnen til høyre (22 x 22, to og to), gul ring på den man styrer, større og med navn under pekeren. Malte kan byttes inn som `ui/verbhjul/portrett-<figur>.png`. Uten rutenettet brukes de gamle boksene.
- Musehjulet over inventaret sender klikk på pilene (115 opp, 116 ned) gjennom skript 11, høyst to i kø.
- Nye testkommandoer: `give=OBJ` (en ting i rommet til inventaret, som pickupObject) og `wheel=up@x/y`.
- Testet uten skjerm: 12 ting i inventaret, hjulet ned blar to ting fram og pilen opp kommer, hjulet opp tilbake; portrettene med gul ring og navn. Listen til ChatGPT har fått portrettene (del 1b).
- `tools/verbhjul_test.sh` stoppet først på «portrettene ble ikke vist»: testen leter etter logglinjen fra de gamle boksene. HD-portrettene logger nå det samme («portraits ego 1:...»). Deretter bestått (11 like setninger, figurbyttet med portrettet virker).

## 2026-10-15 13:03 (Codex)
- Tom bestilte innlegging av alle karakterkonsepter, inventar og verbhjul i repoet med PR og pull. Denne direkte bestillingen gjelder foran den eldre regelen om ingen PR.
- Kjørte git pull --ff-only origin main til b44ed20 og laget grenen grafikk-karakterer-inventar-verbhjul.
- Flyttet inn 15 verbikoner, 126 inventarfiler og 22 karakterark med gallerier, faktiske prompter, manifest og SHA-256. Bildene bevares byte for byte; originaluttrekk og skript beholdes i gpt-arbeid.
- UI-bildene ligger i grafikk/ui/verbhjul-gpt/ og grafikk/inventar/, der build_ui allerede leser dem. Konseptarkene importeres ikke som animasjonsruter. Ingen motor- eller pipelinekode endret.
- Kontroll før PR: build_ui tok inn alle 141 UI-filer med uendrede dekodede piksler; 172 PNG er byteidentiske med gpt-arbeid, 79 aliaskoblinger stemmer og alle 96 bilder i UI-galleriet finnes. Tre SHA-256-lister kontrollert. 37 pipelinetester bestått (2 spilldatatester utelatt), 21 nettlesertester, 4 Pages-pakkertester og hunk-hoder i 4 patcher bestått.

## 2026-10-15 13:26 (Codex)
- Tom godkjente resten av grafikkleveransen, men ba om Elvis-hår som tupé på The King. Ett innebygd image_gen-redigeringskall ga king-v2.png med tupé i alle seks visninger. Hodeform, høye øyne, scenedrakt og positurer kontrollert visuelt.
- Godkjenning, valgt fil, galleri, kontaktoversikt, prompt og sjekksummer oppdatert både i grafikkleveransen og gpt-arbeid. Tidligere King v1 beholdes som ikke godkjent historikk.
- Tom bestilte deretter spritesheet for bare Zak først. Originalens kostyme 1 har 51 ruter fordelt på tre ark i eksisterende pipeline.

## 2026-10-15: Zak spritesheet (Codex)
- Laget bare Zak, kostyme 1, etter Toms bestilling. Tre image_gen-ark med 51 deler og det godkjente Zak-ankeret. Side 2 v2 forkastet fordi munnfragmenter forsvant; alle valgte ark er v1.
- Laget transparent spritesheet med 24 sammensatte stå- og gåruter, rutekart, faktiske prompter, kontrollnotat og SHA-256 under grafikk/sprites/zak/. Ingen originalbilder kopiert til kodegrenen.
- Eksplisitt kobling og eksisterende myk-mottak: 51 importert fra de nye arkene, 38 ok, 13 sjekk, 0 mangler. Alle 24 sammensatte ruter kontrollert for cellekanter og visuelt. De 13 små munn-/utstyrsrutene må fortsatt kontrolleres før motorbruk. Ingen motor- eller pipelinekode endret; grafikken er ikke prøvd i motoren.
## 2026-10-15 13:27 til 14:10 (Claude)
- Tom: «gpt har lagd inventory og verb hjul grafikk men integrer dem i spillet.» Codex hadde lagt 15 malte verbikoner i `grafikk/ui/verbhjul-gpt/` og 126 inventarbilder i `grafikk/inventar/` (PR 11, flettet), alle 512 x 512 RGBA. Sett over i kontaktark: motivene stemmer med listen.
- Ny `zakhd build-mod --kun-ui` (`build_ui_mod`): mod.json og grensesnittet uten rom og figurer. `build_ui` skalerer nå ned til 256 piksler i modden (originalene i `grafikk/` urørt); modden ble 8,3 MB. Nettsiden godtar en mod uten rom (`selectFiles` krevde `rooms/`). Nye tester: pytest 38, nodetester 21.
- Modden bygget og publisert i grenen `hd-mod` med `tools/mod_gren.sh send` (mod.json, ui/, inventory/, SHA256SUMS).
- Testet uten skjerm med modden: «19 drawn icons (15 from the HD pack)», de malte ikonene i hjulet (Turn on lamp), inventaret med malte bilder (billett, fiskebolle med Sushi, regning, kazoo, tapet, CashCard, plastkort) og navn for tingene uten bilde (receiver, telephone, cat clock), hjulet åpnet på billetten.
- `docs/inventar.csv` laget på nytt: status «godkjent» der bildet finnes.
