---
name: "scumm-hd-remake"
description: "Bruk ved HD-remake av LucasArts/SCUMM-spill eller når HD-grafikk lages eller rettes. Avklar originalens motiv, funksjon, figuridentitet og design før produksjon, og følg grafikkreglene og den tekniske fremgangsmåten fra The Dig HD."
---

# HD-utgave av et SCUMM-spill

Dette er fremgangsmåten fra The Dig HD Remake (oktober 2026), skrevet ned for neste spill. The Dig ble bygget slik:

- en ScummVM-patch som legger HD-grafikk over originalen,
- en Python-pipeline for uttrekk og HD-pakker,
- et arbeidsbord der ChatGPT/Codex maler grafikken,
- en nettleserversjon og en Linux-pakke.

Denne utgaven er for ChatGPT og Codex. Rollene i prosjektet: Claude skriver koden (motor, pipeline, tester og verktøy) og kontrollerer grafikken, ChatGPT/Codex lager HD-grafikken i grenen `gpt-arbeid` og tar kodeoppgaver Tom gir, og Tom godkjenner stil og resultater. Der det står at Claude gjør noe, er det for at du skal vite hvordan resten av løypa virker. Delene som gjelder deg mest er Forbildene, Grafikk fra ChatGPT/Codex og Arbeidsform med Tom.

Det tekniske erfaringsgrunnlaget nedenfor ble skrevet 10. oktober 2026 fra The Dig (SCUMM v7). Tilpasningene til andre spill er forslag fra den gjennomgangen, ikke en oppdatert statusrapport. Bruk alltid det aktuelle repoets `AGENTS.md`, `memory.md`, `STATUS.md` og motordokumentasjon for dagens beslutninger og testresultater. Grafikkregelen nedenfor er oppdatert 12. oktober 2026 etter Toms rettelser av feil motiv og figuridentitet.

## Før HD-produksjon: avklar motiv og design

Forstå hva originalen forestiller og gjør før noe tegnes om, også før stilpiloten. En penere tegning er feil når den endrer personen, materialet, funksjonen eller hendelsen. Denne regelen gjelder rom, forgrunn, figurer, animasjoner, objekter, ikoner, effekter og grensesnitt.

1. **Se riktig original i sammenheng.** Fastslå spillutgave, ressurs-ID, rom, kostyme, palett og tilstand. Se motivet i spillet og fasene før, under og etter en handling. Et filnavn, ett utsnitt, en rå eksport med feil palett eller en gammel generering er ikke nok til å avgjøre hva et uklart motiv er. Bruk original, skript, dialog, metadata og dokumenterte primærkilder ved behov.
2. **Beskriv betydning og funksjon.** Skriv hva motivet er, hva det gjør og hvilke materialer og egenskaper som formidler det. I The Dig er energivesenet energi, ikke røyk; forgrunnsplantene må forstås som planter før de tegnes. Et redskap må fortsatt være riktig redskap, med riktig grep og kontaktpunkt. Bevar gåteledetråder, symboler, tekst og tilsiktede tilstandsendringer.
3. **Avklar identitet og design.** Bruk godkjent figurreferanse med navn, ansikt, hår, alder, kroppsform, klær, utstyr, farger og proporsjoner. Koble hver drakt og hvert kostyme til riktig person. Hode og kropp skal passe sammen, og den samme figuren skal kjennes igjen i gange, tale, handlinger og mellomsekvenser. Avviste bilder er feilbeskrivelser, aldri nye stil- eller identitetsankere.
4. **Bruk spillets egne stilvalg.** Fastslå streker, fargeflater, lys, materialer, kantbehandling, alfa, oppløsning og feste-/kontaktpunkter før produksjon. Beskriv hva som kan forbedres og hva som skal ligge fast. Sam & Max beholder tegneserieuttrykket; Zak bruker den valgte spillutgaven; The Dig følger sine godkjente referanser. Gjenbruk metoden mellom spillene, ikke automatisk persondesign, palett eller tegnestil. Et UI-forslag gir ikke i seg selv tillatelse til å endre spillets handlinger eller regler.
5. **Før analysen inn i bestillingen.** Bruk eksisterende `docs/ANALYSE.md`, figur-/romnotater og jobbens brief eller notat. Før opp kilde, betydning, låste kjennetegn, stilanker og reell usikkerhet. Skill dokumenterte fakta fra tolkning. Rett et påvist feil premiss før videre generering. Behold beskyttede originaler og jobbfiler; legg en nødvendig korrigert prompt og kildebegrunnelse i et separat notat og bruk rettelsen fremfor en kjent feil prompt.
6. **Kontroller betydning og teknikk hver for seg.** Sammenlign med originalen og godkjent design, både isolert og samlet i spillet, ved relevant zoom, lys og palett. Se hele berørte animasjoner med hode/kropp og hånd/redskap samlet, også overganger og små oversiktsfigurer. Alfa, rutekart, sjekksummer og automatisk kantlikhet beviser ikke riktig motiv eller identitet. Ved avvik: finn feilen i kilde, tegning, rutekobling, import eller motor før serien fortsetter. Den faktiske leverte pakken må inneholde de kontrollerte filene.

Hvis avgjørende betydning eller et nødvendig designvalg fortsatt mangler, avklar det før den berørte grafikken produseres. Fortsett uavhengig, autorisert arbeid. Behold Toms eksisterende godkjenninger; regelen innfører ikke nye bekreftelser for allerede avklart arbeid. Logg presist hva som er avklart, kontrollert og fortsatt utestet.

## Referansen

Klon github.com/Tombonator3000/Dig-HD-Remake (offentlig) grunt, og les i denne rekkefølgen:

1. `AGENTS.md`, `memory.md`, `todo.md`, `STATUS.md` og siste del av `log.md`: regler, beslutninger og status.
2. `docs/HD-MOTOR.md`: hvordan motoren velger kilde for hver piksel, alle innstillinger og testkroker, hva som er testet, og kjente begrensninger. Den viktigste filen.
3. `engine/patches/0001-dighd-hd-grafikk.patch`: patchen mot ScummVM `c9091321` (`engine/SCUMMVM_COMMIT`).
   - Det meste ligger i `engines/scumm/dighd.cpp` og `dighd.h`.
   - Resten er kroker i ScummVM-filene. Tabellen "Stedene i ScummVM som er endret" i HD-MOTOR sier hvilke.
4. `docs/ANALYSE.md`: hvordan spillfilene ble kartlagt.
5. `docs/BESTILLING-CHATGPT.md` og `docs/gpt-arbeid-AGENTS.md`: bestillingen til grafikerne, jobbformatet og kontrollene.
6. `pipeline/dighd/`:
   - `gamedata` (LA0/LA1, AKOS)
   - `export`, `upscale`, `modpack`
   - `gpt` (jobber og kontroll)
   - `figur` (figurark)
   - `myk` (figurark i glatt stil)
   - `cli`
7. `tools/`:
   - `hent_spilldata.sh`, `gpt_runde.sh`, `gpt_gren.sh` og `mod_gren.sh`
   - `romtest.sh` og `romtest.py`, som kjører alle rom uten skjerm
   - `pakke_linux.sh`
8. `docs/PAGES.md` og `engine/pages/`: nettleserversjonen.
9. `docs/SPILLTEST.md`: hvordan Tom spiller og tester.
10. `docs/HD-REMASTER-METODE.md` (arbeidsmetode og godkjenningstrinn) og `docs/REMASTER-FORBILDER.md` (hva LucasArts og Double Fine gjorde, kritikken og tiltak, med kilder).

Nettsiden har eget repo, Tombonator3000/Dig-HD-Web, med bare motoren (GPL).

Patchen er skrevet for SCUMM v7. Ikke kopier den blindt; se Tilpasning per spill.

## Grunnideen

Motoren kjører spillet uendret i 320 x 200 og 256 farger, med skript, lagring og lyd som før. Bare det siste steget endres: når et 8-bits område sendes til skjermen (`drawStripToScreen`), bygger DigHD det samme området i 4x i full farge, piksel for piksel.

Hva som står i 8 bit avgjør kilden for hver piksel:

| Det som står der | Kilde |
| --- | --- |
| Uendret bakgrunn: lik bakgrunnsbufferen og lik indeksbildet til rommet | HD-rommet |
| Et objekt som nettopp er tegnet, og som stemmer | HD-objektet |
| En kostymerute | HD-ruten |
| Tekst | HD-glyf |
| Film | HD-rammen |
| Alt annet | Originalpikselen skalert opp |

Resten av grunnideen:

- **Indeksbildene:** hvert HD-bilde har originalen ved siden av som 8-bits indeksbilde (`_idx.png`). Sammenligningen med det gjør at HD aldri havner feil, og at det som mangler vises som originalen. Spillet kan spilles hele veien mens grafikken lages.
- **Farger:** HD-pikselen ganges med forholdet mellom fargen spillet viser nå og originalfargen. Det gir nedtoning, lysbytte og skygger uten mer arbeid. Fargesykling (vann, fosser) går gjennom et glatt fargekart: kvadratisk B-spline over 3 x 3 originalpiksler.
- **Figurer:** hver piksel en rute tegner, merkes med tegningen (`seq`), ruten (`slot`) og verdien. Pikselen viser HD bare så lenge den har verdien og tegningen er den siste. `markRectAsDirty` tar bort merkene der noe annet tegnes. Bannere lagrer merkene og legger dem tilbake.
- **Myke figurer** (glatt stil med ekte alfa, `costumeCCC_NNN_hd.png` med marg):
  - Under rutens piksler bygges bakgrunnen.
  - Bildet legges over etter blokkene, i tegnerekkefølge, bak z-masken og under tekst og menyer.
  - Området med margen bygges på nytt rett før skjermen oppdateres.
- **Tekst:** tegnsett-rutinene melder hver glyf med fontnummer og tegnkode. DigHD tegner bokstaven med en ekte skrift (Exo 2) i boksen til originalbokstaven, med kant og skygge som originalen; glyfer som ikke passer, lages med xBR fra spillets egne fonter.
- **Blast-objekter** (inventaret og andre ting skriptene tegner over skjermen): pikslene under merkes før objektet tegnes og sammenlignes etterpå. Det som er mørknet gjennom skyggetabellen, bygges i HD fra det som er under og mørknes med fargeforholdet; det som er malt, får objektets HD-bilde.
- **Klassisk grafikk:** det samme bildet med bare originalpikslene. Valget heter HD Graphics i spillets egen meny (F5), og Ctrl+H bytter. Valget lagres.

## Forbildene: LucasArts og Double Fine

Offisielle remastere: Monkey Island SE (LucasArts 2009), Monkey Island 2 SE (2010), Grim Fandango (Double Fine 2015), Day of the Tentacle (2016) og Full Throttle (2017). Detaljer og kilder i `docs/REMASTER-FORBILDER.md` i The Dig-repoet. Det vi har tatt med:

- **Originalen kjører under.** Double Fine (GDC 2017) lot SCUMM gå urørt og la et lag over som leser tilstanden og tegner på nytt. Tre nivåer for å gripe inn, i økende risiko: lese tilstand, endre tilstand, lappe skriptkoden. DigHD er bygget likt: les først, endre bare der det må til (avslutning via menyen, Esc-vakten), og lapp aldri skript uten Toms ja. Skriv i HD-MOTOR hvilket nivå hver endring er.
- **To feillister:** feil som fantes i originalen og feil som bare finnes i HD. Merk funn `[original]` eller `[HD]`. Eksempel: «Heap ... Mem ... Vid» i The Dig er originalens, asserten etter romhopp var vår.
- **Master-figurark før mengden.** Full Throttle laget ett hovedark per figur med Larry Ahern, og rundt 30 tegnere fulgte det. Lag ett godkjent ark per hovedperson (forfra, profil, bakfra, alle drakter), og krev det som referanse i alle figurjobber. Det hadde hindret de tre like kvinnene i The Dig.
- **Purisme, ikke revisjon** (Yujin Keim om Full Throttle). Fjern gjenstander fra gammel teknologi (dithering, komprimering, pikseltrapper), ikke design. Monkey Island SE ble kritisert for ny frisyre på Guybrush; minst én anmelder byttet tilbake til klassisk grafikk på grunn av det.
- **Figurer og rom på samme nivå.** Grim fikk skarpe nye figurer på nesten urørte bakgrunner, og figurene stakk seg ut. Kontroller kantmykhet, lysretning og metning i ekte spillbilde, ikke enkeltbilder.
- **Overtegning av originalen** (DOTT): hver figur er den samme figuren tegnet med ren strek over pikslene, se «Fra piksel til HD-strek» under Grafikk fra ChatGPT/Codex.
- **Nye tegninger på gamle bevegelser** kan se stive ut (MI SE), og lav bildefrekvens og dithering synes bedre i HD (DOTT). Ikke legg til mellombilder som endrer tempoet; sørg heller for at rutene er like i størrelse og form.
- **Uavhengige valg.** DOTT lot grafikk, lyd og grensesnitt byttes hver for seg; MI SE ble kritisert for å låse dem sammen. Hold HD-valget i spillets meny, og del det opp senere (HD-skrift, myke figurer) hvis det trengs.
- **Grensesnitt som ikke skjuler ledetråder.** MI SE la verb og inventar i egne menyer, og ordspillgåtene ble svakere. Et verbhjul (DOTT) må sende samme verb og objekt som originalen og ikke røpe løsningen.
- **Sideforhold:** aldri strekk. Grim ble kritisert for strukket 16:9; 4:3 med kunst på sidene ble godtatt.
- **Filmer** (Full Throttle, Trevor Diem): de originale SAN-filene var fasiten, et stort arkiv ble indeksert med sjekksummer, og hvert filmbilde ble koblet til kildene med visuell sammenligning (OpenCV). De nevner selv tre feil: lyden ble hørt for sent, lagringsplassen eksploderte, og rundene tok for lang tid. Test med lyd fra første runde og planlegg plassen.
- **Lyd:** de lette etter originalopptakene (DAT, spolebånd, Pro Tools-økter). Spill med god CD-lyd (The Dig, Full Throttle) trenger ikke ny musikk; sjekk bare at tale og undertekst går i takt.
- **Kilder for uklare detaljer:** Grim hadde mistet figurteksturene og malte dem på nytt etter konseptkunsten, med skjønn der noe var uleselig. Hos oss avgjøres slike detaljer av originalbildet og Tom, og valget noteres.
- **Ekstra** (kommentarspor, konseptgallerier, hint i MI SE) kommer etter at spillet er ferdig.
- **For spill med offisiell remaster** (Monkey Island 1 og 2, DOTT, Full Throttle): bruk den som sammenligning for hva som virket og ikke virket, men originalen er fortsatt fasiten. Zak McKracken og Sam & Max har ingen.

## Fremgangsmåten

1. **Oppsett.**
   - Nytt repo med samme oppsett som The Dig: `AGENTS.md`, `log.md` (norsk tid, nyeste nederst), `memory.md`, `todo.md`, `STATUS.md`.
   - Grener:
     - `main`: bare kode og dokumentasjon
     - `spilldata`: spillfilene med `SHA256SUMS`
     - `hd-mod`: siste HD-pakke, én commit som erstattes
     - `gpt-arbeid`: arbeidsbordet med grafikerne
   - Filer over 100 MB deles i deler på 90 MB, med sjekksum for hele filen.
2. **Utgave.**
   - Spør Tom hvilken utgave han har.
   - Sjekk MD5 mot `engines/scumm/detection_tables.h` og `scumm-md5.h` i ScummVM.
   - Velg utgaven med flest farger og best oppløsning som kilde.
3. **Analyse** (`docs/ANALYSE.md`).
   - Tell rom, objektbilder, kostymer og ruter, filmer og fonter.
   - Tell z-plan, paletter og fargesykling.
   - Lag en romliste (CSV).
   - Avklar motiv, funksjon, figuridentitet og design etter «Før HD-produksjon» over, og før grunnlaget inn i bestillingene før stilpilot eller nytegning.
4. **Uttrekk.**
   - Rom, objekter (hver tilstand) og kostymeruter som indekserte PNG med palett, pluss JSON med metadata.
   - Sjekk tellingene mot spillfilene.
   - Kostyme-ID er katalogens ID, ikke rekkefølgen i filen.
5. **Motor.**
   - Lås en ScummVM-commit.
   - Port DigHD og slå den på for det nye spillet: `DigHD::create` sjekker `GID_DIG`.
   - Begynn med rom og objekter, og test med en `nearest`-mod (se Test). Det beviser at krokene sitter riktig.
   - Ta så figurer, tekst, farger og sykling, filmer, menyen og klassisk grafikk.
6. **Pipeline.**
   - `build-mod` med automatisk oppskalering, så alt finnes i HD fra dag én.
   - Deretter jobbene til grafikerne.
7. **Stilpilot med Tom, før noe bestilles i mengde:**
   - motiv, identitet og design er avklart etter regelen over
   - ett rom og ett figurark, sett i motoren
   - stilankere
   - master-figurark for hver hovedperson, med navn på alle kostymer og drakter
   - Tom godkjenner
8. **Grafikkrunder:**
   - hente, kontrollere og bygge modden
   - publisere i `hd-mod`
   - skrive ny ordre
   - kjøres jevnlig
9. **Spillbart for Tom tidlig:**
   - `./spill.sh` fra repoet
   - nettsiden
   - Linux-pakken

## Lærdom og fallgruver

### Motor

- **Pikselformat:** `Graphics::PixelFormat::createFormatRGBA32()` er rekkefølgen i minnet. På little endian ligger R i laveste byte. Les kanalene med formatets `rShift`, `gShift`, `bShift` og `aShift`. Feil rekkefølge ga en rosa, gjennomsiktig figur.
- **Palett:** motoren kan endre paletten mellom tegningen av skuespillerne og sendingen til skjermen. Bygg ikke ting fra `setPalette` som trenger de nye pikslene. Utsett det til kroken før `updateScreen`.
- **Kontroll med `DIGHD_VERIFY`:** sammenlign skjermen med hele skjermen bygget på nytt. Den fanger alle områder som ikke ble bygget på nytt, og har funnet de fleste feilene.
- **SMUSH-filmer:** rammenummeret i filnavnet er `_frame - 1`.
- **Kodek 5 og 16** (v7) tegnes med kodene rett som palettindekser. Fargelegg disse rutene med rompaletten der kostymet vises.
- **Innstillinger:** lagre dem i `kApplicationDomain`. Et spill startet fra kommandolinjen har en midlertidig spillseksjon som ikke lagres.
- **PNG med tRNS:** ScummVMs dekoder gjør et palett-bilde med tRNS (gjennomsiktig indeks 255) om til RGBA. Fjern tRNS og les den gjennomsiktige indeksen selv.
- **Testhopp:** et hopp til et rom som er mindre enn skjermen (inventarrommet) stopper i `clampCameraPos`. Objekter med bare BOMP-bilde stopper i `drawBitmap` når testen setter tilstanden.
- **Myke figurer:** z-masken er en bit per pixel, i rader på `_numStrips` byte, slik `Gdi::getMaskBuffer` leser den. Satt bit betyr skjult. Kanten mot forgrunnen blir derfor 4 x 4-blokker.
- **Vedlikehold av patchen:** lag den på nytt med `git add -N` på nye filer og så `git diff` i ScummVM-kopien. Bygg ScummVM lokalt i en egen mappe. Sjekk at den passer med `git archive HEAD engines/scumm` i en tom mappe og `git apply --check`.
- **Blast-objekter (v6 og v7):** inventaret i The Dig er blast-objekter: en gjennomsiktig rute med skyggemodus 3 (`bompApplyShadow3`, tabell 0 til 7 valgt av kildepikselen) og ikonene oppå. Uten egen behandling blir alt under inventaret originalpiksler. Krok i `drawBlastObject` (før og etter `drawBomp`) og i `removeBlastObjects`. Mørkningen må gjøres etter de myke figurene og før teksten, og regnes med fargen før mørkningen, ikke bakgrunnen. Sam & Max og DOTT bruker også blast-objekter, så lag dette tidlig.
- **Avslutning:** med `confirm_exit=false` avslutter `queryQuit` med en gang, og Alt+Q kaller `quitGame()` direkte (v5 og nyere). Tom vil aldri ut til skrivebordet uten menyen: avskjær `EVENT_QUIT` og `EVENT_RETURN_TO_LAUNCHER` som ikke kommer fra Quit i menyen (`_quitByGUIPrompt`), og åpne menyen ved å sende menytasten med `VAR(VAR_MAINMENU_KEY)` som ASCII.
- **Esc og mellomsekvenser:** `abortCutscene` starter sporet fra `beginOverride` igjen. Er skriptet stoppet eller sporet tatt av et annet skript, kjøres feil kode og motoren stopper med en assert i `pop()` (programmet går rett ut). Husk skriptnummeret ved `beginOverride` og ignorer Esc når det ikke stemmer. Testhoppet til et rom etterlater slike mellomsekvenser («Script N stopped with active cutscene»), så det gjenskaper feilen raskt.
- **Menytasten:** originalmenyen åpnes bare når `lastKeyHit.ascii == VAR(VAR_MAINMENU_KEY)`. Gi F1 til F12 riktig ASCII-kode i motoren, og logg F-tastene, Esc og andre taster det klages på med kode, ASCII og flagg, så en logg fra Toms maskin viser hva som kom. Spillets egne skript har feilsøkingstaster (The Dig viser «Heap ... Mem ... Vid» på h); finn strengen i LA1 (SYSTEM.NNN) og les skriptet før det til for å se tasten.
- **Hurtigtaster:** `hasFlags(KBD_CTRL)` er også sant med Ctrl+Shift. Sjekk den lengste kombinasjonen først.
- **HD-skrift:** navn og beskrivelser kan ha tre farger (hvit bokstav, mørk skygge til høyre og under, noen halvmørke hjørnepiksler). Velg bokstavfargen etter hvilken som gir best passform for kant og skygge, se bort fra en farge med svært få piksler, og ha en skyggemodus for høyre og ned. Smale bokstaver gir hull; la bokstaven bli opptil 25 prosent bredere. En bokstav én piksel bred (l) blir en tynn grå strek når skriftens bokstav har fot; bruk originalbokstaven der.

### Grafikk fra ChatGPT/Codex

- **Jobbformat:** én jobb er et lerret på 1536 x 1024: 384 x 256 originalpiksler i 4x, med grå kant (#808080). Store rom deles i deler med overlapp og sys sammen.
- **Hver jobb har:**
  - `referanse.png`
  - `prompt.txt`
  - `jobb.json` med plassering og rektangler
  - et stilanker som bilde to
- **Automatisk kontroll** før noe godtas:
  - forskyvning og zoom: grensen er 0,75 px
  - kantlikhet
  - fargelås mot originalen
  - Erfaring: ChatGPT bommer på tekst og plassering, og stilen glir.
- **Leveranser:** en dårligere ny leveranse skal ikke erstatte en godtatt. Ta vare på den beste per jobb. Den grå lerretskanten blør inn i ytterradene; rett den.
- **Små objekter** males på plass i rommet (lagjobber) og klippes ut. Ikoner males i ikonark.
- **Figurer:** rutene i én animasjon står på samme ark, så figuren ikke flimrer.
- **Figurstilen:**
  - Tom avviste figurer klippet med originalens omriss: trappetrinn i 4x.
  - Velg glatt stil med ekte alfa og myke ruter fra starten.
  - Hodene blir tegnet omtrent 35 prosent større enn kroppene. Mottaket må derfor skalere per gruppe (animasjon, lag og rad på arket) til originalens høyde, og plassere etter best overlapp (`myk.py`).
  - Grafikeren tegner rutene litt ulikt i bredde og form, og figurene skifter da størrelse når de snakker (Tom så det). Tilpass hver rute til originalens omriss i bredde og høyde for seg, høyst 12 prosent fra gruppens faktor, og bruk det når overlappet ikke blir tydelig dårligere (`fit_scales` og `place_fitted` i `myk.py`, versjon 2). Mål spredningen i bredde og høyde mot originalen per kostyme etter hver innhenting. Se løsningskortet `losninger/grafikk/figurark-fast-storrelse.md` i prosjektbiblioteket.
- **Fra piksel til HD-strek, slik DOTT Remastered gjorde det** (Tom viste Bernard, Laverne og Hoagie side om side, original og HD, 13. oktober 2026). Dette er målet for figurene:
  - **Samme figur, tegnet over.** Positur, silhuett, proporsjoner og plass er de samme: føttene står på samme linje, hodet er like stort mot kroppen, armer og hender er der de var. HD-tegningen kunne lagt oppå originalen i 4x.
  - **Hver pikselklynge blir det den forestiller.** Fire piksler som er et par briller, blir et par briller med glass og innfatning. En grå flekk på brystet blir et navneskilt med rødt kors. En hvit og en svart klump blir en joggesko med snøring. Formen tolkes ut fra figuren og resten av spillet, ikke ut fra hva verktøyet liker.
  - **Fargen per flate ligger fast.** Den grønne genseren, det rødhvite skjørtet, de grå buksene, den blå capsen og den svarte t-skjorten med hodeskalle og oransje flammer har samme farge i HD. Det som var to toner (lys og skygge), blir lys og skygge, ikke nye farger.
  - **Ren strek og flate farger.** Mørk, sammenhengende kontur med litt varierende tykkelse, flate fargefelt med ett skyggetrinn og noen få høylys. Ingen tekstur, ingen myke gradienter, ingen dithering, ingen pikseltrapper.
  - **Ingenting nytt.** Ingen ekstra lommer, knapper, mønstre eller tilbehør som ikke står i originalen. Uklare piksler løses slik at det henger sammen med figuren (skjørtet blir tydelige folder med ruter), ikke med en ny idé.
  - **Samme ansikt og uttrykk.** Øynene blir tydeligere, men ikke større. Hodet blir ikke forstørret, selv om bildeverktøy gjerne gjør det.
  - **Det samme for rom og objekter:** hver form i originalen blir den samme formen med ren kant og flate felt, på samme plass.
  - I prompten: «Trace the original at 4x. Keep the pose, silhouette, proportions and position. Turn every cluster of pixels into the shape it shows. Clean dark outlines, flat colors with one shade and a few highlights, the same color for every area. Add nothing that is not in the original.» Den offisielle remasteren er laget for hånd av Double Fine; denne beskrivelsen er hva bildene viser, ikke hvilken arbeidsflyt de brukte.
- **Navn på hvert kostyme:** gi grafikeren navnet på personen for hvert kostyme, også varianter som romdrakter. The Dig hadde «Mannskapet i romdrakt» for kostyme 1, 2 og 3, og Codex tegnet tre like kvinner; det var Boston, Maggie og Brink. Finn hvem som er hvem tidlig: hold musen over figurene i spillet (navnet vises nederst) og sammenlign med posisjonene i `DIGHD_DEBUG_SOFT` (logger kostymenummer). Skriv det i figurlisten og notatene til promptene.
- **Avvisning:** avviste ark (`docs/gpt-avvisninger.csv`, jobb og sha256) må holdes ute av alle mottak, også de myke figurene, og rutene de ga før må slettes, så motoren viser originalen. Skriv grunnen og et engelsk forslag til prompt, og legg en kort rettelse øverst i `ORDRE.md`.
- **Når Tom avviser en stil:** hold leveransene etter avvisningen utenfor modden til en ny prøve er godkjent. Lapp modden fra den kjente mengden ark i stedet for å ta inn alt.
- **Codex lager egne jobber** utenfor jobblisten. Mottaket må lese leveransene (`rapporter/*/fremdrift.json`, med sha256) og rutekartene, ikke bare vår `status.csv`.
- **Arbeidsbordet:**
  - Grafikerne leser `ORDRE.md` i `gpt-arbeid` først.
  - Claude skriver `ORDRE.md`, `RAPPORT.md` og `retur.md` for hver runde.
  - Push `HEAD` til grenen, for arbeidskopien kan stå på en løs commit.

### Uttrekk

- **Dekoderne:** The Dig brukte thedig-textures. De er laget bare for The Dig, og CI fikk ikke alltid klonet dem; nå er de valgfrie.
- **For neste spill, enten:**
  - en dump-modus i motorpatchen (motoren dekoder alt allerede: rom fra bakgrunnsbufferen, objekter per tilstand, alle ruter via kostymetegneren, slik `DIGHD_TEST_COSTUME` gjør), eller
  - egne dekodere i pipelinen etter ScummVM-kildene (`gfx.cpp`, `costume.cpp`, `akos.cpp`).
- **Ikke prøvd:** ingen av de to er laget ennå.
- **Uten dekoderne:** originalrutene kan lages fra arbeidsbordet: `original_1x.png` i hver figurjobb, `rekt` per rute i `jobb.json` og alfa der pikselen ikke er `bakgrunn`-fargen. Slik ble alle 28 480 ruter laget på nytt 10. oktober for å ta inn figurene igjen. Hent bare det som trengs med en sparse clone (`--filter=blob:none --sparse`, `git sparse-checkout set --no-cone`).

### Test

- **Krokene** gjør at Claude kan teste spillet uten skjerm. Alle er miljøvariabler:
  - `DIGHD_TEST_ROOM`, `AT`, `CAMX`, `CAMY`
  - `DIGHD_TEST_KEYS`, `DIGHD_TEST_CLICKS`
  - `DIGHD_TEST_COSTUME`, `DIGHD_TEST_WALK`, `DIGHD_TEST_CLIP`
  - `DIGHD_TEST_OBJSTATE`
  - `DIGHD_DUMP_DIR`, `DIGHD_DUMP_EVERY`, `DIGHD_DUMP_FLAT`
  - `DIGHD_VERIFY`, `DIGHD_BENCH`, `DIGHD_QUIT_AT`
  - `DIGHD_DEBUG_SOFT` (myke ruter med kostymenummer), `DIGHD_DEBUG_BLAST` (blast-objekter), `DIGHD_DEBUG_FACE` (valgene i HD-skriften)
  - `DIGHD_TEST_KEYS` tar a til z, 0 til 9, f1 til f12, space og escape
  - Kjør med `SDL_VIDEODRIVER=dummy` og `SDL_AUDIODRIVER=dummy`.
- **`engine/test.sh`:** en mod laget med `nearest` skal gi 0 avvik mot originalen. Unntak er skalerte figurer (under 0,25 prosent).
- **`tools/romtest.sh`:** hvert rom, med kamera over hele rommet og objekttilstander. Den gir rapport og kontaktark.
- **Nettleseren:** Playwright Chromium med SwiftShader, eller Firefox med sandkassens CA i profilen. En dummy-nøkkel virker mot api.github.com fra sandkassen.
- **Ekte inndata:** `Xvfb` og `xdotool` med SDL sin X11-driver tester tastatur, mus og tekstinntasting som på en ekte maskin. Uten vindusbehandler må vinduet få fokus med `xdotool windowfocus` før tastene virker. Ta skjermbilder med `import -window root`.
- **Pakken som Tom har:** last ned AppImage fra releasen med `gh api` (assets, `Accept: application/octet-stream`), pakk ut med `--appimage-extract` og kjør `AppRun` med egne `HOME` og `XDG_*`. Test lagring og lasting både med testtastene (Alt+1, Ctrl+1) og gjennom menyen.
- **Toms egen tilstand:** med koblingen til maskinen hans kan Claude be om tilgang til bestemte mapper (lagrede spill, innstillinger, `~/.cache/scummvm/logs`). Hent hans automatiske lagring (`dig.s00`) og start med `--save-slot=0` for å teste der han var. Loggen viser rom, filmer og valg; den overskrives ved hver start.
- **Menyene uten skjerm:** `DIGHD_TEST_CLICKS` i originalpiksler. I The Dig (320 x 200): Save 265,76, Load 265,91, Quit 265,121, plass 1 75,52, OK 265,92.
- **Spør Tom presist:** når noe ikke kan gjenskapes, still flervalgsspørsmål om nøyaktig hva han gjorde og hvor det stoppet (hvilken tast, hvilken skjerm, hva som skjedde). Ett skjermbilde fra ham sparer mange runder.

### Distribusjon

- **Nettsiden:**
  - ScummVM bygget med Emscripten, i eget offentlig repo med bare motoren (GPL).
  - Spillfilene hentes fra repoets grener via GitHub-API-et, med en fin-kornet lesenøkkel. De lagres i IndexedDB etter blob-sha, med ny henting ved nettfeil.
  - Filfilteret i `local-files.mjs` må kjenne alle filnavnmønstre i modden. `_hd.png` manglet en stund, så nettsiden viste de gamle figurene.
  - Rett inn i spillet, uten oppsettside.
  - Berøring: trykk er klikk, hold er høyreklikk, to fingre er F5, tre er Esc. Fullskjerm ved første klikk.
  - Uten WebGL: `--gfx-mode=surfacesdl`.
  - Første start på PC laster ned rundt 530 MB, så siden viser fremdriften.
- **Linux:**
  - AppImage bygget på ubuntu-22.04 med linuxdeploy og appimagetool.
  - Egen `AppRun` med `--config`, `--path` og `--savepath`, og fullskjerm.
  - Testes i en Debian 12-container med skrivebordsbibliotekene.
  - Bygges hver natt når `hd-mod` er endret, og legges som release. En push som endrer patchen starter den også; start den ikke for hånd i tillegg (`cancel-in-progress` avbryter den første).
- **Størrelse:** HD-pakken er rundt 1 GB, mest myke figurer. Prøvd: oxipng 3 til 6 prosent, pngquant 55 til 60 prosent (lite synlig), JPEG for rom 80 prosent (motoren må lese JPEG). Indeksbildene må være tapsfrie. Tom vil ha dette helt til slutt.

### Sandkassen (Claude i skyen)

- GraphQL er stengt: bruk `gh api` REST til PR, releaser og nedlasting av vedlegg.
- Claude får ikke flette sine egne PR-er (sikkerhetskontrollen stopper det). Be Tom flette når CI er grønn, og vent med pakke og nettside til det er gjort.
- `rm -rf` med variabler stoppes; skriv `"${S:?}"/...`.
- Proxyen stopper nedlastingen av SDL3-porten, så nettmotoren bygges i Actions. Ikke gå rundt sperrer.
- `pkill -f` og `pgrep -f` med et mønster som treffer egen kommando, dreper skallet.
- Jobber over 10 minutter kjøres med `nohup` i bakgrunnen, og loggen sjekkes.

## Tilpasning per spill

Ikke testet. Bekreft alt i ScummVM-kilden for commiten du låser.

| Spill | SCUMM | ScummVM-ID | Det som må tilpasses |
| --- | --- | --- | --- |
| The Dig | v7 | `dig` | Ferdig. Referansen |
| Full Throttle | v7 | `ft` | Nærmest The Dig: AKOS-kostymer, SMUSH-filmer, NUT-fonter. Mye kan brukes som det er |
| Sam & Max Hit the Road | v6 | `samnmax` | Se under |
| Day of the Tentacle | v6 | `tentacle` | Som Sam & Max |
| Monkey Island 1 og 2, Indy 4 | v5 | `monkey`, `monkey2`, `atlantis` | Klassiske kostymer og tegnsett, verblinje |
| Zak McKracken | v1, v2, v3 | `zak` | Se under |
| Curse of Monkey Island | v8 | `comi` | 640 x 480: skala 2 |

**Sam & Max (v6):**

- Filene er `samnmax.000/.001` eller `.sm0/.sm1`, kryptert med XOR 0x69 (`GF_USE_KEY`). Talen ligger i `MONSTER.SOU` på CD-en.
- Kostymene tegnes av `ClassicCostumeRenderer` i `costume.cpp`, ikke `akos.cpp`. Krokene for rutene (`beginActor`, `noteCel`) må inn der.
- Teksten tegnes av `CharsetRendererClassic`.
- Det er ingen SMUSH-filmer: mellomsekvensene og minispillene tegnes av motoren.
- Blast-objekter og blast-tekst finnes, som i v7.
- Menyvalget: sjekk at originalmenyen for v6 er den samme (`digHDMenuRow`).
- Blokkformatet er nær v7, så `gamedata.py` kan kanskje lese det etter XOR.

**Zak McKracken:**

- **v2 (PC, Amiga, Atari):**
  - 16 faste EGA-farger. Fargejusteringen trengs ikke, og fargelåsen må løses opp.
  - `GdiV2`, `CharsetRendererV2`.
  - Verbene er tekst nederst på skjermen.
  - Gamle filer `NN.LFL` (`00.LFL` er indeksen), med lite hode (`GF_SMALL_HEADER`, `GF_OLD_BUNDLE`), som pipelinen ikke leser.
- **FM-Towns (v3, `GF_OLD256`):**
  - 256 farger. Den beste kilden hvis Tom har den.
  - Eget tekstlag, `_textSurface` med multiplikator 2, som må passe med DigHD.
- **v1:** C64 og PC.

## Arbeidsform med Tom

- **Språk og skriving:** svar på norsk. Dokumentasjon og logg uten emoji og uten tankestreker, vanlig og direkte. Si hva som er testet og hvordan, og hva som ikke er testet.
- **Roller:** Claude skriver koden, ChatGPT/Codex lager grafikken, Tom godkjenner.
- **Flyt:** kodeendringer går som PR; Tom fletter når CI er grønn. Logg, status, todo og minne går rett i `main`.
- **Tom tester på ekte skjerm** (Linux-laptop med KDE) og melder funn med skjermbilder. Ta hvert punkt for seg, logg dem først, og si hva som er gjenskapt, rettet og testet, og hva som ikke er funnet.
- **Det Tom vil ha:**
  - Spillet starter rett, som originalen, uten ekstra knapper rundt.
  - HD eller originalgrafikk velges i spillets egen meny.
  - Det virker på mobil.
  - Det finnes en komplett fil til nedlasting.
  - Spillet går i fullskjerm.
  - Spillet går aldri rett ut til skrivebordet; avslutning går via menyen.
  - Hver figur er riktig person og holder størrelse og form i alle rutene.
- **Opphav:** spillene tilhører Disney/Lucasfilm.
  - Spillfiler og alt laget fra dem holdes i egne grener, aldri i `main`.
  - Nettsiderepoet har bare motoren.
  - Konseptbilder fra andre: spør og krediter før noe vises offentlig.
- **Gjenbruk:** sjekk prosjektbiblioteket, github.com/Tombonator3000/prosjektbibliotek (offentlig), før du lager noe nytt. Nye løsninger skrives ned som løsningskort i `losninger/<domene>/` der.
- **Bakgrunnsstoff:** når Tom ber om research, skriv funnene som et dokument i repoet med kilder, legg tiltakene i todo og logg det.
