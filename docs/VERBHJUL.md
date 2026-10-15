# Verbhjulet (alternativ C)

Tom valgte 12. oktober 2026 et verbhjul som i *Day of the Tentacle Remastered*, og godkjente oppførselen under samme kveld («Lag det»). Hjulet er bygget som `engine/patches/0002-verbhjul.patch` (13. oktober), med midlertidige ikoner, og testet uten skjerm mot originalpanelet. Samme dag sa Tom ja til et dynamisk hjul med høyst fire valg og portretter for figurbytte; begge er bygget og er standard (se «Dynamisk hjul» og «Portretter for figurbytte»). Dokumentet sier hvordan DOTT gjorde det, hva skriptene i Zak krever, hvordan hjulet virker, hva som er testet og hva som gjenstår. Tallene er målt i FM-Towns-utgaven med `pipeline/zakhd/lfl.py` og de dekompilerte skriptene (work/skript).

Bakgrunn og de andre alternativene: [GRENSESNITT.md](GRENSESNITT.md). Verblisten: [verbhjul-verb.csv](verbhjul-verb.csv).

## Slik gjorde DOTT Remastered det

- Et klikk (eller en knapp på spillkontroll) på et objekt åpner hjulet, og det viser **verbene som gjelder det objektet**, ikke alle ni (PopMatters: hjulet viser "all the verbs that you are capable of using to interact with it"; PCWorld: "a list of suggested verbs for each object").
- Den klassiske verbraden kunne fortsatt velges.
- Hjulet erstatter verbraden nederst, og frigjør plass på skjermen.

Det jeg skrev i GRENSESNITT.md 11. oktober, at DOTT-hjulet hadde alle ni verbene, var feil og er rettet.

## Hvorfor ikke tre ikoner (øye, hånd, tannhjul)

Forslaget var å slå sammen verbene til tre ikoner. Skriptene viser at Zak ofte gir forskjellige verb ulik kode på samme objekt:

| Gruppe | Objekter der to verb i gruppen gjør forskjellige ting |
| --- | ---: |
| Hånd: Pick up, Push, Pull | 11 |
| Hånd med Open og Close | 59 |
| Tannhjul: Use og Give | 15 |
| Tannhjul med Turn on, Turn off, Put on og Take off | 39 |
| Øye: Read og What is | 0 |

Med alle verbene fordelt på tre ikoner får 97 av de 489 objektene med verbkode et ikon som ikke kan vite hvilken kode som skal kjøres. Brukes bare de sju verbene i forslaget, mister 145 objekter verb de har kode for (Open, Close, Turn on og off, Put on, Take off, Buy, Teleport to).

Eksempler fra rom 1: skuffen i kommoden (objekt 92) åpnes med Open eller Pull og lukkes med Push eller Close. Lampen (103) har egen kode for Turn on, Turn off og Use. Sushi i fiskebollen (14) har egen kode for Pick up, Put on, Use og Give.

Med DOTT sin metode trengs ingen sammenslåing, fordi hjulet bare viser verbene objektet har kode for. Hjulet blir lite likevel:

| Verb i hjulet | Objekter |
| --- | ---: |
| 0 (vanlig trykk er nok, eller bare kulisse) | 433 |
| 1 | 119 |
| 2 | 104 |
| 3 | 58 |
| 4 | 36 |
| 5 | 15 |
| 6 | 3 |
| 7 | 2 (bryteren 642 og boom-boksen 71) |

Telt av alle 770 objektene, uten Walk to (vanlig trykk), What is (navnet vises når man peker) og 255 (koden for alle andre verb).

## Slik tar Zak imot klikk

Fra globalt skript 11, som spillet setter som `VAR_VERB_SCRIPT` (globalt skript 7), og skript 15, 18, 21 og 22:

- Hvert klikk går til skript 11 med klikkområde (1 verb, 2 rom, 4 tast) og verbnummer.
- Setningen står i variabler: verb i Var[116], første objekt i Var[117], andre objekt i Var[118], preposisjon i Var[119]. Standardverbet er Var[120] (Walk to, 3).
- Skript 22 finner det som er under musen og legger det i Var[114]. Ved vanlige klikk ser det bare etter objekter (`findObject`). Skuespillere (`actorFromPos`) ser det bare etter når Give venter på mottakeren (`startScript(22,[133,1])`, bare figurer med klasse 133) og for What is.
- Når verbet byttes, beholder skriptet objektet. Walk to lamp og så Use gir «Use lamp with», fordi skript 21 kjøres på objektet som står i Var[117]. Setningen tømmes bare av skript 18: etter en setning med et annet verb enn Walk to, ved klikk på Give, ved et nytt verb mens en preposisjon venter, og ved klikk på setningslinjen mens verbet er Walk to.
- Setningen kjøres når man klikker det samme objektet en gang til, eller klikker setningslinjen (verb 100). Walk to kjøres med en gang.
- Use: skript 21 ser etter klasse 1 til 4 på objektet. Har det en, settes preposisjonen (129 in, 130 with, 131 on, 132 to), og setningen venter på et objekt til. 112 objekter med Use har en slik klasse.
- Give setter alltid preposisjonen 132 (to).
- Inventaret er verbplassene 101 til 110 (objektet står i Var[102] til Var[111]), og pilene er 115 og 116.
- I spesielle moduser bytter panelet verb: Fly to og Swim to i stedet for Walk to, Teleport to, Buy og Sell i butikken, Switch og navnene på figurene, og egne verb når man styrer et dyr (Chew, Poop, Left head, Right head, Swim forward, Swim backward, Chatter, Smile, verb 32 til 34).

## Oppførselen

Godkjent av Tom 12. oktober. Bygget i `engines/scumm/verbhjul.cpp` (patch 0002).

**Urskiven.** Hjulet har tolv faste plasser, én per handlingsverb, og hvert verb står alltid på samme klokkeslett:

| Klokke | Verb | I stedet, når panelet viser det |
| ---: | --- | --- |
| 12 | Pick up | Buy (i butikken) |
| 1 | Open | |
| 2 | Close | |
| 3 | Use | |
| 4 | Give | Sell (i butikken) |
| 5 | Turn on | |
| 6 | Turn off | |
| 7 | Put on | |
| 8 | Take off | |
| 9 | Read | |
| 10 | Push | Teleport to |
| 11 | Pull | |

Motsatte par står ved siden av hverandre. Use er det mest brukte verbet (171 objekter) og står klokka 3. Buy, Sell og Teleport to tar plassen til verbet de erstatter i originalpanelet (samme plass i panelet), så butikken og teleporten trenger ingen egen logikk.

**Hvilke verb som vises.** Som standard det dynamiske utvalget: høyst fire ikoner, der verb med lik kode er ett ikon og Open/Close og Turn on/Turn off viser det som passer tilstanden (se «Dynamisk hjul»). Ikonet står på plassen til verbet det sender. Med `verbhjul_dynamisk` av vises ett ikon per verb objektet har en egen oppføring for i verbtabellen (OC-blokken, fra byte 19), som i DOTT. For ting i inventaret vises også Give (Sell i butikken), fordi setningsskriptet (globalt skript 15) håndterer dem for alle ting. Et verb vises bare når plassen i originalpanelet er på. Med valget «alle verb» vises alle verbene som er på, på de samme plassene.

**Betjening.**
- Venstreklikk eller trykk: Walk to, som i originalen. Det kjører også koden objekter har for Walk to (dører).
- Høyreklikk på et objekt eller en ting i inventaret: hjulet åpnes rundt pekeren. Klikk på et ikon velger, klikk utenfor lukker.
- Hold høyre knapp, dra til et ikon og slipp: velger i én bevegelse.
- Langt trykk på mobil og i nettleseren: nettsiden sender det som høyreklikk (`engine/pages/touch.mjs`, 0,5 sekunder), så hjulet åpnes, og et trykk på ikonet velger.
- Har objektet ingen verb for hjulet (bare Walk to, eller bare koden for alle verb), er høyreklikket et vanlig klikk.
- Esc lukker hjulet. Ctrl+W slår hjulet av og på; av betyr originalpanelet.

**Teksten.** Under hjulet står navnet på objektet, og mens pekeren er på et ikon hele setningen («Pull cat clock»). Teksten tegnes av hjulet selv: å bruke setningslinjen til forhåndsvisning ville betydd å klikke i spillet for hver bevegelse, og et nytt klikk på samme objekt kjører setningen.

**Det hjulet sender.** De samme klikkene som originalpanelet, ett per ramme, gjennom spillets eget inngangsskript (globalt skript 11):
1. Står det noe igjen fra forrige setning (objekt, preposisjon, eller det samme verbet er valgt), tømmes setningen først: Walk to hvis et annet verb er valgt, så setningslinjen. Med Walk to og uten objekt kjører skript 11 da skript 18, og ingen setning kjøres. Uten dette ble objektet fra et vanlig klikk med i setningen: Walk to lamp, så Use på ticket i hjulet, kjørte «Use lamp with ticket» med en gang (funnet og rettet 13. oktober). I originalpanelet ser spilleren «Use lamp with» på setningslinjen og må klikke en gang til; hjulet kjører uten å vise noe, så det må tømme.
2. Verbet.
3. Objektet: et klikk i rommet på punktet der hjulet ble åpnet (`VAR_VIRT_MOUSE` settes for det ene kallet), eller inventarplassen 101 til 110.
4. Har skriptet satt en preposisjon og mangler objekt nummer to: hjulet venter (se under). Ellers klikkes setningslinjen (verb 100), og setningen kjøres.

**To objekter.** Use på noe med klasse 1 til 4 og Give setter en preposisjon. Setningslinjen må da ikke klikkes, for skript 11 tømmer setningen hvis den klikkes før objekt nummer to er valgt (skript 18). Hjulet lukkes, setningslinjen viser for eksempel «Use ticket in», og neste venstreklikk i rommet eller på inventaret sendes som klikk på det objektet og så på setningslinjen. Pilene i inventaret (115 og 116) blar uten å avbryte ventingen, fordi skript 11 bare kjeder til skript 20 for dem og lar setningen stå. Høyreklikk avbryter: hjulet klikker Walk to, som tømmer setningen akkurat som i originalpanelet.

**Panelet.** Mens hjulet er på, tegnes ikke verb 1 til 17 i panelet, og de kan ikke klikkes; tastene for dem virker fortsatt. Med portrettene på er Switch også borte fra panelet (tasten virker). Setningslinjen, inventaret, pilene, navnene på figurene og verbene når man styrer et dyr står som før.

**Valgene** lagres i scummvm.ini under `[scummvm]`: `verbhjul` (av eller på, standard på), `verbhjul_dynamisk` (standard på), `verbhjul_alle` (standard av) og `verbhjul_portretter` (standard på). Miljøvariablene med de samme navnene i store bokstaver (`VERBHJUL=0`, `VERBHJUL_DYNAMISK=0` og så videre) overstyrer dem.

## Ikonene

Tegnet 15. oktober 2026 (Tom: «verb hjul som ser bedre ut og med grafikk, hånd, munn osv. som Day of the Tentacle og Sam & Max»). 15 ikoner i en kremfarget mynt med mørk kontur og flate farger, i stilen fra stilankerne: hånd som dytter, neve som drar, hånd som griper, hånd som gir, dør åpen og lukket, lyspære på og av, hatt på og av, øye for Read, tannhjul for Use, mynter for Buy og Sell og glimt for Teleport to. Liste og kilder: [grafikk/ui/README.md](../grafikk/ui/README.md). Zak har ikke Talk to, så det er ingen munn.

Ikonene er egne tegninger (SVG fra `tools/verbhjul_ikoner.py`), ikke laget fra spillets grafikk. De ligger som PNG i base64 i `engines/scumm/verbhjul_ikoner.h`, sammen med skriften Comic Neue Bold (OFL). Motoren trenger ingen filer ved siden av seg, og det samme gjelder nettsiden.

Ikke godkjent av Tom ennå. Kan erstattes av ikoner malt av ChatGPT med de samme filnavnene.

## Tegningen i HD

- Hjulet tegnes i HD-laget (1280 x 960) med myke kanter: ikonene skalert ned fra 160 x 160 med flatemiddel, en skygge under hver mynt, en gul ring og større ikon under pekeren, og teksten under hjulet i en avrundet boks med verbet i gult og objektet i hvitt («Turn on lamp»). Ikonene glir ut fra punktet som ble klikket (140 ms).
- Pikslene under hjulet tas vare på, så de myke kantene blandes med spillets egne piksler i hver ramme, også der spillet tegner under hjulet. Når hjulet lukkes, legges de tilbake.
- HD-laget går nå også uten HD-pakke (originalpikslene fire ganger så store), så hjulet alltid er skarpt. `ZAKHD_LAV=1` gir spillets egen skjerm på 320 x 240, og da tegnes de gamle runde ikonene med bokstaver. Virker med 16 og 32 bits farger (programvaretegning og OpenGL).
- Portrettene for figurbytte er fortsatt de enkle boksene.

## Grafikk fra grafikerne

Motoren leser bilder fra HD-modden når de finnes, og bruker det innebygde ellers:

| I modden | Hva | Fra |
| --- | --- | --- |
| `ui/verbhjul/<navn>.png` | Ikonet til et verb i hjulet, i stedet for det innebygde (navnene i [grafikk/ui/README.md](../grafikk/ui/README.md)) | `grafikk/ui/verbhjul-gpt/` og `--egne` |
| `inventory/objNNN.png` | Bildet av en ting i inventaret, i stedet for navnet | `grafikk/inventar/` og `--egne` |
| `inventory/objNNN-<navn>.png` | Bildet for tingen når den har dette navnet (for eksempel `obj014-taped-fish-bowl.png`, `obj049-lit-lighter.png`); vinner over `objNNN.png` | samme |

PNG med alfa i hvilken som helst størrelse (minst 64 piksler); motoren skalerer ned med flatemiddel og bevarer formen. `zakhd build-mod` legger dem i modden (`build_ui` i `pipeline/zakhd/modpack.py`), og nettsiden tar dem med (`local-files.mjs`). Listen til ChatGPT med utseende og filnavn: [GRAFIKK-HJUL-OG-INVENTAR.md](GRAFIKK-HJUL-OG-INVENTAR.md). Tingene i [inventar.csv](inventar.csv) (`tools/inventarliste.py`).

## Inventaret som bilder

Med hjulet på og HD-laget i gang vises inventaret som et rutenett i HD som fyller hele området under setningslinjen, der verbpanelet og tekstinventaret var (Tom 15. oktober): fem ruter i to rader (spillets x 1 til 271, y 153 til 239). Kolonnen til høyre har pilene som gule trekanter øverst og nederst, og portrettene for figurbytte to og to mellom dem.

- En ting med bilde i modden vises som bildet. Pekeren over ruten gir en gul ramme og navnet i en boks over ruten.
- En ting uten bilde vises med navnet i HD-skriften, på én eller to linjer.
- Ruten sender det samme klikket som tekstplassen i originalen (verb 101 til 110, pilene 115 og 116), så skriptene ser ingen forskjell. Høyreklikk åpner hjulet som før.
- Viser panelet navnene på figurene, Done eller verbene for dyrene der rutenettet ville vært (verb 31 til 40), brukes tekstinventaret som i originalen så lenge de står der.
- `verbhjul_inventar` i scummvm.ini (standard på) og `VERBHJUL_INVENTAR=0` slår det av.

Testet uten skjerm 15. oktober: tekst i ruten (billetten), et testbilde for billetten (obj082) med navnet over ruten under pekeren, hjulet åpnet på ruten, og et ikon (Use) fra en testmod i stedet for det innebygde. `tools/verbhjul_test.sh` bestått med rutenettet på; inventarklikkene der traff ruten for billetten. Ikke testet: flere ting enn ti (pilene), og når panelet viser figurnavnene.

## Arbeidet i motoren

Patch 0002 ligger oppå HD-patchen (0001, den samme som i The Dig og Sam & Max). `tools/lag_patcher.sh` lager begge på nytt fra `engine/scummvm`.

| Sted | Hva |
| --- | --- |
| `engines/scumm/verbhjul.cpp`, `verbhjul.h` | Klassen `VerbWheel`: urskiven, verbene for objektet, det dynamiske utvalget, portrettene, klikkene, ventingen på objekt nummer to, tegningen og testdriveren. Bare for `zak` på FM-Towns |
| `engines/scumm/verbhjul_ikoner.h` | Ikonene og skriften som PNG i base64, laget av `tools/verbhjul_ikoner.py` |
| `engines/scumm/verbhjul_zak.h` | Reglene for det dynamiske hjulet, 337 objekter, laget av `tools/verbhjul_dynamisk.py --cpp` (bare objekt- og verbnummer) |
| `verbs.cpp`, `findVerbAtPos` | Med inventaret som rutenett: ruten under pekeren gir verbplassen 101 til 110, 115 eller 116 |
| `input.cpp`, `ScummEngine::parseEvent` | Hjulet ser hver hendelse først (høyreklikk, klikk mens hjulet er åpent, Ctrl+W) |
| `verbs.cpp`, `checkExecVerbs` | Ett klikk fra hjulet per ramme, før spillets egne klikk |
| `verbs.cpp`, `findVerbAtPos` og `drawVerb` | Verb 1 til 17 tegnes ikke og kan ikke klikkes mens hjulet er på, og Switch (36) ikke mens portrettene er på |
| `scumm.cpp`, `waitForTimer` | Hjulet tegnes på skjermen rett før `updateScreen`, etter FM-Towns-lagene. Når det lukkes, legges området inn som skittent rektangel i FM-Towns-skjermen, så spillet tegnes der igjen |
| `script.cpp`, `doSentence` | Logger hver setning (for testene) |

Klikkene hjulet og portrettene sender, sjekkes en gang til når de sendes, siden et skript kan ha endret noe i rammen imellom: et verb som ikke lenger er på i panelet, eller en figur som ikke kan velges, stopper hele setningen. Bytter spillet rom (eller lastes et lagret spill) mens klikk venter eller hjulet venter på objekt nummer to, kastes de. Betingelsene i reglene sjekkes mot spillets antall variabler og objekter før de brukes. Dette kom etter en gjennomgang av koden 13. oktober.

Hjulet tegnes i HD med de tegnede ikonene (se «Tegningen i HD»). Uten HD-lag tegnes runde ikoner med tre bokstaver i ScummVMs konsollskrift.

## Tester

`tools/verbhjul_test.sh` kjører spillet uten skjerm to ganger samtidig, med originalpanelet og med hjulet (dynamisk, med portrettene), og sammenligner setningene spillet kjører (`doSentence`). Introen går av seg selv til rom 1, der man kan styre Zak etter rundt 1300 rammer. Tar under fire minutter.

Kjørt 13. oktober med motoren bygget av `engine/build.sh` (begge patchene): bestått, 11 like setninger.

| Handling | Hjulet | Setning |
| --- | --- | --- |
| Open door (84) | høyreklikk, klikk på ikonet | 2 84 0 |
| Open dresser drawer (92) | hold og dra; Open og Pull er ett ikon | 2 92 0 |
| Turn on lamp (103) | høyreklikk, klikk | 5 103 0 |
| Pull window shade (90) | høyreklikk, klikk; rullegardinen er oppe, så hjulet viser Close og Pull | 6 90 0 |
| Turn off cat clock (95) | høyreklikk, klikk; klokken går når rom 1 starter (klasse 6 er ikke satt), så hjulet viser Turn off, ikke Turn on | 10 95 0 |
| Read ticket (82, inventaret) | høyreklikk på inventaret, klikk | 12 82 0 |
| Use ticket in door | høyreklikk på inventaret, Use, venter, klikk på døren | 14 82 84, så 14 84 82 (spillets eget andre forsøk, likt i originalen) |
| Use ticket, så høyreklikk | avbrudd | ingen setning; preposisjon og objekt er 0 etterpå |
| Close dresser drawer (92) | skuffen er åpen, hjulet viser bare Close | 7 92 0 |
| Open dresser (91) | regel for hånd: tilstanden til skuffen 92; hjulet viser Open og Use | 2 91 0 |
| Bytt til Annie | portrettet i hjulet, F2 i originalen | 38 0 0, og Annie (ego 2) i rom 6 etterpå i begge |

Figurbyttet krever at spillet har slått på Switch. Det skjer senere i spillet, så testen setter variablene ScummVM sjekker for F1 til F4 (Var[145] bit 0 for Annie) og dem globalt skript 24 bruker for Switch (Var[152] bit 4 og Var[250]), og kjører skript 24. Det er bare i testen.

Testet for hånd uten skjerm 13. oktober: «alle verb» (døren får alle tolv plassene), Ctrl+W av (originalpanelet tegnes igjen) og på (panelet skjules igjen), skjermbilder som viser at hjulet ryddes bort når det lukkes, hjulet med `verbhjul_dynamisk` av (skuffen får Open, Close, Push og Pull, katteklokken fem verb, som før) og Esc (lukker hjulet).

Ikke testet: med skjerm og mus, langt trykk i nettleseren og på mobil, butikken (Buy og Sell), teleporten, styring av dyr, andre rom enn rom 1, figurbytte på det stedet i spillet der Switch faktisk kommer, og at valgene lagres i scummvm.ini (ScummVM skrev ingen scummvm.ini i testmiljøet). Reglene for hånd er lest i skriptene, men bare kommoden er prøvd i spillet.

## Dynamisk hjul (Toms forslag 13. oktober)

Tom spurte om hjulet kan være dynamisk: høyst tre eller fire ikoner per objekt, verbene slått sammen (øye for Look at og Read; hånd for Pick up, Push, Pull, Open og Close etter hva som går an; bryter for Turn on og Turn off; snakkeboble for Talk to), Fly utenfor hjulet (flybillett på skranken åpner kartet), og figurbytte som små portretter i et hjørne. Etter målingen under sa han ja til det dynamiske hjulet og portrettene, uten snakkeboblen. Bygget samme dag og er standard.

**Reglene.** `tools/verbhjul_dynamisk.py` leser verbtabellene og objektkoden i de dekompilerte skriptene og klassene i 00.LFL, og skriver én regel per objekt til `engines/scumm/verbhjul_zak.h` (formatet står i verktøyet og i `verbhjul.h`):

1. Lik kode blir ett ikon: verbene hopper til samme sted i objektkoden, og koden spør ikke hvilket verb som ble valgt (lesing av Var[52], Var[116] eller Local[1], også i skript den starter). Give holdes alltid for seg (trenger mottaker), og Use for seg når objektet har preposisjonsklasse 1 til 4. Eksempel: skuffen i rom 1 har Open og Pull på samme kode, og Push og Close.
2. Par etter tilstand: Open/Close og Turn on/Turn off viser bare det ene ikonet. Spillets egen regel er 0 lukket eller av, 1 åpen eller på (globalt skript 31 og 32). Verktøyet godtar paret bare når begge sider sjekker tilstanden før de gjør noe (`getState(...) == 0` og `== 1`, eller skript 31 og 32), på objektet selv (også som `VAR_ME` og Var[50]), i koden eller i skriptene den starter. Da gjør verbet som skjules ingenting i den tilstanden. Det samme for klasse 6 når den brukes som av og på og begge sider sjekker den (lampen i rom 6). Bare `setState` er ikke nok: telefonsvareren i rom 1 spiller av nye beskjeder med Turn on også når den står på, så den beholder begge ikonene. Det gjelder også vasken i rom 2 og bryterne i rom 16, 25 og 35, der Turn on gjør noe på nytt (for eksempel husker hvilken figur som slo på bryteren i rom 25).
3. Regler for hånd, lest i skriptene, med kilden som kommentar i verktøyet (19 objekter):

| Objekt | Regel |
| --- | --- |
| Sushi i fiskebollen (14) | Put on eller Take off etter Var[222] (bollen på hodet), Give bare i inventaret, Pick up bare i rommet |
| Kommoden (91) | Sender verbet videre til skuffen (92): Open og Pull ett ikon, Push og Close ett, valgt etter tilstanden til skuffen |
| Våtdrakten (39) | Put on eller Take off etter klasse 6 (settes når den tas på, globalt skript 75), Give bare i inventaret |
| Oksygentanken (50) | Put on eller Take off etter Var[219] (15 når den er på), Give bare i inventaret, Pick up bare i rommet |
| Mikrobølgeovnen (260) | Open eller Close etter tilstanden til 260, Turn on eller Turn off etter tilstanden til 261 (lokalt skript 206, 223, 224 og 225) |
| Boom-boksen (71) | Turn off når den tar opp (klasse 6) eller spiller av (Var[143] bit 0), ellers Turn on; Give vises ikke (gir bare «No way, it's mine!»); Read (merket) bare i inventaret; Pick up bare i rommet |
| Døren 247 (rom 11) | Open eller Close etter tilstanden til døren 246 |
| Skapet 367 (rom 18) | Open eller Close etter tilstanden til skapdøren 368 |
| Verktøykassen (34) | Open når klasse 6 er satt (lukket), ellers Close |
| Koffertene 258 og 259 | Fire verb til ett ikon: koffert 257 svarer det samme på alle |
| Fallskjermen (77) | Put on vises ikke (gir bare «I'm already wearing it.») |
| Lighteren (49), lommelykten (69), radioen (492) | Turn on eller Turn off etter klasse 6, som settes når de slås på. Koden sjekker ikke klassen først, men det skjulte verbet ville bare gjort det samme en gang til |
| Katteklokken (95) | Som over, motsatt vei: klassen fjernes når den startes, og rom 1 starter animasjonen når klassen ikke er satt |
| Setet (119, rom 2), skriveunderlaget (175, rom 6) | Open eller Close etter tilstanden; Close setter bare tilstanden tilbake |
| Vasken (242, rom 11) | Turn on eller Turn off etter tilstanden; Turn on starter bare overløpet på nytt |

**Resultatet** (337 objekter med verbkode):

| Ikoner | Hjulet før | Dynamisk, i rommet | Dynamisk, i inventaret |
| ---: | ---: | ---: | ---: |
| 1 | 119 | 202 | |
| 2 | 104 | 89 | 42 |
| 3 | 58 | 36 | 59 |
| 4 | 36 | 10 | 21 |
| 5 til 7 | 20 | 0 | 0 |

Inventaret gjelder de 122 objektene som kan plukkes opp, kjøpes eller gis til en figur i skriptene, og tallet tar med Give, som hjulet alltid gir for ting i inventaret. Til sammen er det 56 par etter tilstand, 8 etter klasse 6 og 2 etter en variabel.

Motoren sjekker at den leser alle reglene riktig: testkommandoen `rules` skriver hver regel tilbake og sammenligner med tabellen (337 regler, 0 avvik 13. oktober).

**Det som er mistet.** Ingen handling med egen virkning. Tre replikker vises ikke lenger fra hjulet: Give på boom-boksen («No way, it's mine!»), Read på boom-boksen mens den står i rommet (merket kan leses når Melissa har den), og Put on på fallskjermen («I'm already wearing it.»). Ved par vises bare det ene verbet; det andre gir som regel bare «It's already open» og lignende.

**Det ikonet sender.** Ett av verbene i gruppen: verbet paret har valgt, ellers det første av Open, Close, Pick up, Turn on, Turn off, Put on, Take off, Read, Use, Push, Pull, Give, Buy, Sell, Teleport to. Ikonet står på plassen til det verbet på urskiven. Setningen er altså alltid en originalpanelet kunne gitt. Teksten under hjulet viser verbet og objektet («Close dresser drawer»).

**Svar på resten av forslaget:**

- Øye: Zak har ikke Look at. Read finnes (93 objekter), og What is er navnet under pekeren. Øyet kan være ikonet for Read.
- Snakkeboble: Zak har ikke Talk to. Samtalene startes av skriptene, når man kommer inn i et rom eller gir noe med Give. Et snakkeikon krever nye skript og ny tekst. Tom sa nei til det.
- Fly: flyreisene virker allerede slik Tom beskriver. Use på reservasjonsterminalen på flyplassen (objekt 194 i rom 8, 220 i rom 9) med CashCard laster reisemålskjermen (rom 45, globalt skript 90, som setter eget inndataskript 92). Terminalen har bare Use og får ett ikon. «Fly to» er Walk to når Zak styrer fuglen (skuespiller 6, globalt skript 24 og 119), og er vanlig klikk, ikke i hjulet.
- Et fast sett med fire ikoner dekker ikke spillet: Give, Put on, Take off, Buy, Sell og Teleport to finnes på 43 objekter, og noen objekter har to ulike håndhandlinger (strømledningen i rom 2: Pull og Pick up). Derfor står ikonene på plassen til verbet de sender. Hånd, øye, tannhjul og bryter kan være motivene når ikonene tegnes.

Usikkert: tallene og reglene kommer fra tekstsøk i den dekompilerte koden. Skript som startes gjennom en variabel (`startScript(Var[112],...)`) følges ikke, og lokale skript følges bare fra objektkoden selv. Reglene for hånd er lest, men bare kommoden er prøvd i spillet.

## Portretter for figurbytte

Mens spillet lar spilleren bytte figur (Switch er på i panelet), står små portretter av figurene nederst til høyre, under inventaret, der panelet ikke tegner noe. Den man styrer er gul. Bare figurene som kan velges vises, etter de samme bitene ScummVM bruker for F1 til F4 (Var[144] bit 15 for Zak, Var[145] bit 0 til 2 for Annie, Melissa og Leslie). Et klikk på et portrett sender det samme som navnet på figuren etter Switch (verb 37 til 40) gjennom skript 11, slik F1 til F4 gjør. Ingen skriptendring. Switch-knappen tegnes ikke mens portrettene er på; tasten virker.

Portrettene virker også med hjulet av (Ctrl+W). Valget er `verbhjul_portretter` (standard på). Foreløpig står det «Zak», «Ann», «Mel» og «Les» i boksene; de tegnede portrettene kommer etter stilpiloten.

## Det som gjenstår

- Mens hjulet sender klikkene sine (tre eller fire rammer), og i rammen etter et klikk på et portrett, tar ikke spillet imot andre taster og klikk; de går tapt. Gjelder bare svært raske trykk.
- Navnet på objektet under pekeren mens hjulet er lukket (i dag gir What is det i originalen; What is er skjult når hjulet er på, men tasten c virker).
- Valgene i spillets meny (F5) i stedet for bare Ctrl+W og scummvm.ini.
- Toms godkjenning av de 15 ikonene (tegnet 15. oktober), og de fire portrettene.
- Prøve med skjerm, i nettleseren og på mobil, og i butikken, teleporten, ved figurbytte der Switch kommer i spillet og når man styrer dyr. Prøve reglene for hånd i spillet (Sushi, våtdrakten, oksygentanken, mikrobølgeovnen, boom-boksen, fallskjermen).

## Kilder

- PopMatters, "Day of the Tentacle Remastered: Remastering a Classic": https://www.popmatters.com/day-of-the-tentacle-remastered-remastering-a-classic-2495438589.html
- PCWorld, anmeldelse av Day of the Tentacle Remastered: https://www.pcworld.com/article/414548/day-of-the-tentacle-remastered-review-sludge-o-matic-sucker-for-love.html
- Destructoid, om grensesnittet i DOTT Remastered på PS4: https://vip-develop.destructoid.com/?p=176291
- ScummVM ved c9091321: `engines/scumm/verbs.cpp` (`checkExecVerbs`), `script.cpp` (`runInputScript`, `getVerbEntrypoint`), `vars.cpp`.
- De dekompilerte skriptene: globalt skript 7 (setter `VAR_VERB_SCRIPT`), 11, 15, 21, 22 og 36.
