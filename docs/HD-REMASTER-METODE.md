# Arbeidsmetode for trofast HD-remaster

Skrevet av Codex for The Dig HD Remake 10. oktober 2026, tilpasset Sam & Max samme dag og Zak McKracken 11. oktober 2026. Metoden er generell. Funn som gjaldt The Dig, står som erfaringer derfra.

Dette er en plan for arbeidet, ikke en rapport om tester eller ferdige funksjoner. Den supplerer [BESTILLING-CHATGPT.md](BESTILLING-CHATGPT.md). Den endrer ikke originalens spillregler, og den endrer ikke at stilen avgjøres i stilpiloten, med Tom.

## Før nytegning: motiv og design

Følg [remake-skillen](skills/scumm-hd-remake/SKILL.md), delen «Før HD-produksjon: avklar motiv og design», før stilpilot og produksjon. Avklar hva hver ressurs forestiller og gjør i originalens riktige palett og spilltilstand. Før kilde, funksjon, låst figuridentitet, materialer, stilanker og reell usikkerhet inn i eksisterende analyse og bestilling. Bevar spillets egne stilvalg gjennom hele animasjoner og varianter.

Et påvist feil premiss i en prompt skal rettes før generering, med korrigert grunnlag i separat notat når jobbfilene er beskyttet. Kontroller motiv og design samlet i spillet i tillegg til alfa, geometri og rutekobling. Denne regelen er innført 12. oktober 2026; den innebærer ikke at analysen eller spillkontrollen av alle ressurser allerede er utført.

## 1. Målet

Samme spill og visuelle identitet i klar HD. Behold komposisjon, former, figuridentitet, lys, palett og gåteledetråder. Mer detalj er bare nyttig når den forklarer originalen. Ikke legg til materialer, effekter eller former bare fordi verktøyet kan.

Zak beholder uttrykket i den engelske FM-Towns-utgaven (SCUMM v3, 256 farger): samme motiv og farger, med mer detalj. Det finnes ingen offisiell remaster av Zak, så originalen er fasiten, og stilankerne må hentes fra selve spillutgaven. Hvert spill trenger egne stilankere fra spillutgaven som er valgt. Coveret og annet materiale kan støtte figuridentiteten, men erstatter ikke geometrien i skjermbildet.

## 2. Hva de offisielle remasterne lærer oss

Dokumenterte forhold:

- Double Fine beskriver DOTT Remastered som ny håndtegnet høyoppløst grafikk. Spilleren kan kombinere klassisk og remastret grafikk, lyd og UI.
- Tim Schafer beskriver et nytt verb dial rundt interessepunktet og valgfri gammel verbbar. Han og Matt Hansen oppga over 100 bakgrunner og 10 000 animasjonsbilder som måtte males om.
- GDC-presentasjonen fra Double Fine og Shiny Shoe viser original SCUMM-logikk med et lag som leser og oversetter spilltilstand til ny grafikk, lyd og input. Den beskriver også kostymer, animasjoner og kroppsdeler.
- Craig Derrick forklarer at første Monkey Island Special Edition vurderte et trevalgs verb coin, men beholdt de ni handlingene i separat tilgjengelige verb- og inventarmenyer. Figurene var en nytolkning basert på flere spill og covere.
- Monkey Island 2 SE tilbyr håndtegnet HD, direkte kontroll som alternativ og bytte til originalgrafikken.

Konsekvens for oss: DOTT er det nærmeste forbildet for trofast nytegning. DOTT er SCUMM v6, mens Zak her er v3, så metoden gjelder, men filformatene og motorkrokene er ikke de samme. Bevar originalens handlinger når UI endres. Ikke påstå at alle prosjektene brukte samme hjul eller samme arbeidsmetode.

**Fra piksel til HD-strek.** Tom viste 13. oktober 2026 Bernard, Laverne og Hoagie fra DOTT side om side, original og remaster. Remasteren er den samme figuren tegnet over: samme positur, silhuett, proporsjoner og plass, hver pikselklynge tolket som det den forestiller (briller, navneskilt, joggesko, hodeskalle med flammer), samme farge per flate, ren mørk kontur, flate farger med ett skyggetrinn og ingen nye detaljer. Det er målet for figurene våre. Detaljene står i remake-skillen under «Fra piksel til HD-strek».

Kildene dokumenterer prinsippene og omfanget. Lagstrukturen og kontrollpunktene nedenfor er vårt forslag, ikke en påstand om hvilket tegneprogram eller hvilken overtegningsprosedyre Double Fine brukte.

Kilder:

- https://www.doublefine.com/games/day-of-the-tentacle-remastered
- https://www.doublefine.com/games/day-of-the-tentacle-remastered/making
- https://www.p1xelcoder.com/resources/GDC_2017_Remastering_DotT_and_Grim.pdf
- https://www.shacknews.com/article/91891/double-fines-tim-schafer-on-day-of-the-tentacle-remastered-it-was-kind-of-now-or-never
- https://www.adventureclassicgaming.com/index.php/site/interviews/536/
- https://www.craigderrick.com/2010/03/10/monkey-island-2-special-addition-announced/
- https://store.steampowered.com/app/32460/Monkey_Island_2_Special_Edition_LeChucks_Revenge/

## 3. Erfaringer fra The Dig

Codex gikk gjennom repoet til The Dig HD Remake 10. oktober 2026. Funnene gjaldt det repoet. De står her fordi de samme verktøyene er kopiert hit.

| Funn i The Dig | Hva det betyr for Zak |
| --- | --- |
| Infrastrukturen for trofast utskifting (motor, mottak, romtest, original ScummVM-logikk) var god | Behold og utvid kontrollene. Ikke bygg ny spillogikk for å modernisere grafikken |
| Jobber med status sjekk kom med i modden når bare godkjente ikke var valgt, og myke ruter ble skrevet med status sjekk | Skill arbeidsmod fra visuelt godkjent pakke. Til det finnes, merk pakken som arbeidsversjon |
| Myke ruter hadde ikke samme kontrollvei som vanlige figurark | Lag egen kontroll av identitet, farger, fotfeste og flimmer for myke animasjoner |
| Rutene ble koblet etter rad og rekkefølge når rutekart manglet, og hoder og kropper ble skalert hver for seg | Krev eksplisitt rutekart for alle leveranser |
| Et rom ble avvist fordi vann var tegnet som stein, selv om geometrimålingene var gode | Kontroller materialer og gåteledetråder visuelt i tillegg til tallene |
| Myke figurer hadde kjente begrensninger: en figur bak en smalere myk tegning kunne erstattes av bakgrunn, og z-maskene er i originaloppløsning | Test flere figurer, masker, skalering og menyer før nye effekter |
| Mottaket brukte mye minne, og nettleseren holdt kopier av filene | Mål mottak og nettleser hver for seg. Mindre grupper i produksjonen, ingen svekking av kontrollen |
| README, STATUS og loggen oppga ulike tall for levert grafikk | Ta tellinger fra én verifisert pakke, med dato. Ikke bland levert, sjekk og godkjent |

## 4. Produksjon per ressurs

### A. Referanse og låsing

1. Identifiser spillutgave, ressurs-ID, rom, kostyme eller tilstand, palett og sjekksum.
2. Bruk den uttrukne ressursen som hovedreferanse. Skjermbilder viser sammenhengen, men inneholder også andre lag.
3. Lag et låst underlag i 1x og 4x med samme sideforhold. Skill spillkoordinater fra visningsformat. Ikke strekk til 16:9.
4. Marker viktige punkter: føtter, øyne, hodefeste, dørkanter, brytere, skilt, symboler og kontaktpunkter mellom figur og objekt.
5. Bruk godkjent stilanker som tillegg. Originalen bestemmer innhold og plassering.

### B. Nytegning

- Arbeidslag: låst original, konturer, grunnfarger, skygger og lys, materialdetaljer, alfa og eksport.
- Bevar den store formen først. Tegn detaljene etter at sammenligningen stemmer.
- Hold originalens fargeflater og lysretning. Unngå ekstra glans, støy, skarphetsglorier og oppdiktede teksturer. Behold konturene og de flate fargefeltene der originalen har dem.
- Bildegenerering brukes til kandidater og avgrensede rettelser. En vellykket prompt er ikke dokumentasjon på nøyaktig plassering.
- Rett én konkret feil om gangen med original og godkjent kandidat som referanser. Ikke lag hele rommet på nytt når bare én kant er feil.
- Skilt, symboler og tekst på rekvisitter kontrolleres tegn for tegn. Tekst i spillet (verblinje, replikker, inventar) tegnes av motoren, ikke i bildene. Zak bruker tegnsettene i `98.LFL` og `99.LFL`. The Dig fikk en HD-skrift (Exo 2); om Zak skal ha det samme, er ikke bestemt.
- Behold både rå kandidat og ferdig behandlet eksport. Fargelås eller skalering kan gi nye feil.

### C. Lag, objekter og tilstander

- Bakgrunn, bevegelige objekter og figurer leveres hver for seg gjennom jobbformatet.
- Bruk det godkjente HD-rommet som sammenheng for lagjobber, slik bestillingen krever.
- Kontroller åpnet og lukket, tent og slukket, før og etter i samme bildeområde. Uendrede områder må ikke hoppe i farge eller form. Zak har ett bilde per objekt (OI-blokkene), uten tilstander med egne bilder, så kontroller i spillet at objekter som skriptene tar inn eller ut av rommet, passer med HD-rommet.
- Kontroller sømmer før og etter sammensying og fargelås. I The Dig kunne grensen synes der et HD-objekt møter HD-rommet, når de to var malt hver for seg. `tools/romtest.sh` måler disse sømmene.
- Palettbytte og fargesykling må sees i bevegelse. Motoren viser fargesykling i HD gjennom et glatt fargekart (se [HD-MOTOR.md](HD-MOTOR.md)), når den er portet til Zak. Hvilke rom i Zak som sykler farger, er ikke målt. FM-Towns tegner i 16 bit (RGB555), så palettbytte og fargesykling må sjekkes på nytt etter porten.

### D. Figurer og animasjoner

- Én godkjent identitetsreferanse per figur: ansikt, kroppsform, klær, lys og palett. De spillbare er Zak McKracken, Annie Larris, Melissa China og Leslie Bennett. Resten av figurene fylles inn fra skriptene og de uttrukne kostymerutene (klassiske kostymer i CO-blokker). Alle skal se ut som i originalen.
- Ekte alfa og myke kanter fra starten. Ikke bruk originalens harde pikselmaske som ny kontur; Tom avviste det i The Dig fordi det ga trappetrinn i 4x.
- Rutekartet skal koble hver original-ID til riktig tegnet del og boks. Antall, rekkefølge, hode og kropp og tomme ruter må stemme.
- Vurder fotpunkt og hodefeste i tillegg til størst mulig overlapp med omrisset. Høy overlapp garanterer ikke riktig ansikt eller stabil gange.
- Spill hele animasjonen i originalens rekkefølge og tempo, med hode og kropp samlet. Stillbilder alene er ikke nok.
- Kontroller minst én hel sløyfe og overgangen til neste handling: ansikt, størrelse, klær, skygge, alfa, glorie og at føttene ikke glir.
- Et bevisst avvik i omrisset kan godkjennes av Tom, men må knyttes til konkret rute og sjekksum. Ingen automatisk omtegning for å nå terskelen.

## 5. Godkjenning

Foreslått arbeidsflyt, ikke statusverdier som finnes i verktøyene:

| Trinn | Betydning | Bevis |
| --- | --- | --- |
| Levert | Kandidaten og rutekartet finnes | Fil og sjekksum |
| Teknisk kontrollert | Format, plassering og ressurskobling stemmer | Mottaksrapporten |
| Visuelt kontrollert | Motiv, stil, figurer og gåteledetråder stemmer | Overlegg, kontaktark og konkret vurdering |
| Kontrollert i bevegelse | Tilstander, animasjon og lag virker sammen | Sekvens eller opptak og testscenario |
| Godkjent av Tom | Godkjent stil eller resultat innen avtalt omfang | Notat med dato, ressurs og sjekksum |

Status godkjent i mottaket er en teknisk status. Behold den betydningen i filene til kode og rapporter er oppdatert. Legg heller ved en egen vurdering enn å endre statusformatet på egen hånd.

Arbeidsmodden kan bruke jobber med status sjekk for løpende spilltesting. En pakke som kalles ferdig, må utelate slike avvik eller ha dokumentert godkjenning av dem. Utelates en rute, bekreft at originalen faktisk vises i stedet, og at gamle eksportfiler ikke blir liggende.

Kontrollpakken per ressurs:

- original og HD side om side
- 50 prosent overlegg og kantvisning
- rå kandidat og behandlet eksport
- relevante objekttilstander eller animasjon
- spillvisning med lag, tekst og menyer
- vurdering, åpne feil og sjekksummer

Geometriske mål er et hjelpemiddel. De oppdager ikke sikkert vann som blir stein, feil figur, endrede symboler eller feil objekt.

## 6. Testrekkefølge

Bruk testene som finnes, før nye verktøy lages. Motortestene og romtesten krever at HD-patchen er portet til Zak, og ingen av dem er kjørt med Zak ennå.

- Pipelineendring: `cd pipeline && pytest -m "not game"`.
- Med spillfilene i `game/`: `pytest -m game`.
- Motorendring: `engine/test.sh`, med en `nearest`-mod som referanse.
- Rom: `tools/romtest.sh` og `tools/romtest.sh --objekter`.
- Manuell sammenligning: Ctrl+H, gult felt og lagrede spill som gjenskaper ekte skripttilstand.

Tillegg Claude bør lage og teste i PR (forslag fra The Dig, ikke laget):

1. Forhåndsvisning av en animasjon i riktig rekkefølge, med original og myk HD side om side.
2. Liste over visuell godkjenning, knyttet til ressurs-ID og sjekksum for resultatet, også for myke ruter.
3. Pakkerapport som skiller levert, teknisk ok, sjekk, visuelt kontrollert og vist som original.
4. Kontroll som hindrer gamle avviste eksportfiler i å bli med når modden bygges på nytt.
5. Målinger av minne og tid for mottak og nettleser, med et scenario som kan kjøres igjen.

Scenarioer som må testes i ekte spill:

- Flere myke figurer foran og bak hverandre, for eksempel flere av de spillbare i samme rom.
- Skalerte myke figurer og figurer bak flere forgrunnsplan.
- Meny, banner og replikker over myke figurer, også etter at de forsvinner.
- Toning, palettbytte og fargesykling.
- Objekter på hver side av en sammensydd del.
- Mellomsekvenser og eventuelle minispill, som tegnes av motoren og skriptene. Zak har ingen filmer og ingen blast-objekter.
- Lagring og lasting etter objektbytte og HD-bytte.
- Ekte PC med lyd og mus, og ekte telefon med lyd og minnemåling. CD-musikken (`Track1.fla` til `Track21.fla`) spilles bare når motoren er bygget med FLAC.
- Gjennomspilling. Romhopp beviser ikke at gåter og skript virker i vanlig spill.

## 7. UI uten å endre gåtene

Zak har en verblinje med tekst, og inventaret er tekst nederst på skjermen. Behold samhandlingen fra originalen i første ferdige versjon. Undersøk konkrete problemer med klikk og berøring først. Verblinjen og inventaret er tekst i FM-Towns-laget, så et annet grensesnitt krever egne motorkroker.

Hvis et handlingshjul vurderes senere:

- Registrer alle originalhandlinger og hvordan de brukes på objekt og inventar.
- Et hjul sender samme handling og samme objekt som originalsystemet. Det må også håndtere kombinasjoner og mottakerobjekt.
- Ikke fjern valg som virker lite nyttige. De kan ha morsomme eller viktige svar. Et konteksthjul må ikke avsløre løsningen på en gåte.
- Et lite hjul bør presentere verbene som finnes i verblinjen, ikke finne på nye.
- PC: pek og klikk, og valgfritt høyreklikk for hjul. Mobil: trykk og tydelige valg med god avstand. Tilby et alternativ til å holde fingeren, for brukere som ikke oppdager det.
- Test menyen ved skjermkanten, avbryt, inventar mot inventar, inventar mot rom, dialog og tastatur.
- UI og HD-bryteren bør være uavhengige.
- Ikke legg nye knapper rundt spillet på nettsiden. Tom vil at spillet starter rett, som originalen.

## 8. Prioritert plan

Forslag, i samme rekkefølge som `todo.md`:

| Prioritet | Arbeid | Ferdig når |
| --- | --- | --- |
| P0 | Motoren: DigHD portet til Zak (FM-Towns, v3) og slått på, rom og objekter først. Enten egne kroker i `towns_drawStripToScreen` (16 bit), eller FM-Towns-laget av så spillet går gjennom 8-bit `drawStripToScreen`. Ikke bestemt | `nearest`-mod gir 0 avvik mot originalen |
| P0 | Uttrekk av rom (RO/HD/BM), objekter (OI) og kostymeruter (CO) | Tellingene stemmer med spillfilene |
| P0 | Stilpilot: ett rom og ett figurark sett i motoren | Godkjent av Tom, med stilankere |
| P1 | Forhåndsvisning av animasjoner og liste over godkjenning | En hel bevegelse kan kontrolleres før den kalles ferdig |
| P1 | Flere figurer, z-masker, tekst og menyer i samme scenario | Kontrollert i ekte spilltilstand uten feil ved gjennomsyn |
| P1 | Tellinger fra én pakke | Rapport med SHA for pakken, dato, kilde og kontrollnivå |
| P2 | Ekte PC og mobil, og gjennomspilling | Logget test med åpne avvik |
| Senere | Mulig handlingshjul | Spillet ferdig i trofast HD og egne piloter godkjent |

Nye shadere, ekstra glød og parallakse kommer etter at grafikken er trofast og spilltestet, og skal være valgfrie hvis de endrer originalens uttrykk.

## 9. Samarbeid og leveranse

- Claude lager kontrollverktøy og motorendringer gjennom PR og CI.
- ChatGPT/Codex lager og retter grafikk i `gpt-arbeid` etter `ORDRE.md`.
- Tom godkjenner stilen og bevisste avvik.
- Ikke skriv over en godkjent leveranse med en ny kandidat uten konkret sammenligning.
- Logg hva som er laget, kontrollert og fortsatt usikkert. Sjekk metadata fra samme pakke før status oppdateres.
- Dokumentasjon kan ligge i `main`. Spillfiler og grafikk laget fra spillet ligger i datagrenene.
