# Verbhjulet (alternativ C)

Tom valgte 12. oktober 2026 et verbhjul som i *Day of the Tentacle Remastered*, og godkjente oppførselen under samme kveld («Lag det»). Hjulet er bygget som `engine/patches/0002-verbhjul.patch` (13. oktober), med midlertidige ikoner, og testet uten skjerm mot originalpanelet. Dokumentet sier hvordan DOTT gjorde det, hva skriptene i Zak krever, hvordan hjulet virker, hva som er testet og hva som gjenstår. Tallene er målt i FM-Towns-utgaven med `pipeline/zakhd/lfl.py` og de dekompilerte skriptene (work/skript).

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
- Skript 22 finner det som er under musen: først en skuespiller (`actorFromPos`), ellers et objekt (`findObject`), og legger det i Var[114].
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

**Hvilke verb som vises.** Som standard verbene objektet har en egen oppføring for i verbtabellen (OC-blokken, fra byte 19), som i DOTT. For ting i inventaret vises også Give og Sell, fordi setningsskriptet (globalt skript 15) håndterer dem for alle ting. Et verb vises bare når plassen i originalpanelet er på. Med valget «alle verb» vises alle verbene som er på, på de samme plassene.

**Betjening.**
- Venstreklikk eller trykk: Walk to, som i originalen. Det kjører også koden objekter har for Walk to (dører).
- Høyreklikk på et objekt eller en ting i inventaret: hjulet åpnes rundt pekeren. Klikk på et ikon velger, klikk utenfor lukker.
- Hold høyre knapp, dra til et ikon og slipp: velger i én bevegelse.
- Langt trykk på mobil og i nettleseren: nettsiden sender det som høyreklikk (`engine/pages/touch.mjs`, 0,5 sekunder), så hjulet åpnes, og et trykk på ikonet velger.
- Har objektet ingen verb for hjulet (bare Walk to, eller bare koden for alle verb), er høyreklikket et vanlig klikk.
- Esc lukker hjulet. Ctrl+W slår hjulet av og på; av betyr originalpanelet.

**Teksten.** Under hjulet står navnet på objektet, og mens pekeren er på et ikon hele setningen («Pull cat clock»). Teksten tegnes av hjulet selv: å bruke setningslinjen til forhåndsvisning ville betydd å klikke i spillet for hver bevegelse, og et nytt klikk på samme objekt kjører setningen.

**Det hjulet sender.** De samme klikkene som originalpanelet, ett per ramme, gjennom spillets eget inngangsskript (globalt skript 11):
1. Er verbet allerede valgt, først Walk to (ellers ville et nytt klikk på verbet kjørt setningen som venter).
2. Verbet.
3. Objektet: et klikk i rommet på punktet der hjulet ble åpnet (`VAR_VIRT_MOUSE` settes for det ene kallet), eller inventarplassen 101 til 110.
4. Har skriptet satt en preposisjon og mangler objekt nummer to: hjulet venter (se under). Ellers klikkes setningslinjen (verb 100), og setningen kjøres.

**To objekter.** Use på noe med klasse 1 til 4 og Give setter en preposisjon. Setningslinjen må da ikke klikkes, for skript 11 tømmer setningen hvis den klikkes før objekt nummer to er valgt (skript 18). Hjulet lukkes, setningslinjen viser for eksempel «Use ticket in», og neste venstreklikk i rommet eller på inventaret sendes som klikk på det objektet og så på setningslinjen. Høyreklikk avbryter: hjulet klikker Walk to, som tømmer setningen akkurat som i originalpanelet.

**Panelet.** Mens hjulet er på, tegnes ikke verb 1 til 17 i panelet, og de kan ikke klikkes; tastene for dem virker fortsatt. Setningslinjen, inventaret, pilene, Switch, navnene på figurene og verbene når man styrer et dyr står som før.

**Valgene** lagres i scummvm.ini under `[scummvm]`: `verbhjul` (av eller på, standard på) og `verbhjul_alle` (standard av). For tester: miljøvariablene `VERBHJUL=0` og `VERBHJUL_ALLE=1`.

## Ikonene

Listen står i [verbhjul-verb.csv](verbhjul-verb.csv): verbnummer, tekst, tast, plass i panelet, hvor mange objekter som har kode for verbet, og et forslag til motiv. Hjulet trenger 15 ikoner: Push, Pull, Open, Close, Pick up, Put on, Take off, Turn on, Turn off, Give, Read, Use, Buy, Sell og Teleport to. Walk to og What is trenger ikke ikon.

Bestillingen er ikke aktiv. Etter remake-skillen (docs/skills/scumm-hd-remake/SKILL.md, "Før HD-produksjon") skal motiv og design avklares først: ikonene skal passe til grafikken i FM-Towns-utgaven, være lesbare i 32 til 64 piksler, være ett sett i samme stil, og godkjennes av Tom sammen med stilpiloten. Motivene i CSV-filen er forslag.

## Arbeidet i motoren

Patch 0002 ligger oppå HD-patchen (0001, den samme som i The Dig og Sam & Max). `tools/lag_patcher.sh` lager begge på nytt fra `engine/scummvm`.

| Sted | Hva |
| --- | --- |
| `engines/scumm/verbhjul.cpp`, `verbhjul.h` | Klassen `VerbWheel`: urskiven, verbene for objektet, klikkene, ventingen på objekt nummer to, tegningen og testdriveren. Bare for `zak` på FM-Towns |
| `input.cpp`, `ScummEngine::parseEvent` | Hjulet ser hver hendelse først (høyreklikk, klikk mens hjulet er åpent, Ctrl+W) |
| `verbs.cpp`, `checkExecVerbs` | Ett klikk fra hjulet per ramme, før spillets egne klikk |
| `verbs.cpp`, `findVerbAtPos` og `drawVerb` | Verb 1 til 17 tegnes ikke og kan ikke klikkes mens hjulet er på |
| `scumm.cpp`, `waitForTimer` | Hjulet tegnes på skjermen rett før `updateScreen`, etter FM-Towns-lagene. Når det lukkes, legges området inn som skittent rektangel i FM-Towns-skjermen, så spillet tegnes der igjen |
| `script.cpp`, `doSentence` | Logger hver setning (for testene) |

Tegningen er foreløpig enkel: runde ikoner med tre bokstaver i ScummVMs konsollskrift på spillets egen skjerm (320 x 240). Når HD-motoren er portet, tegnes hjulet i HD med de tegnede ikonene.

## Tester

`tools/verbhjul_test.sh` kjører spillet uten skjerm to ganger samtidig, med originalpanelet og med hjulet, og sammenligner setningene spillet kjører (`doSentence`). Introen går av seg selv til rom 1, der man kan styre Zak etter rundt 1300 rammer.

Kjørt 13. oktober med motoren bygget av `engine/build.sh` (begge patchene): bestått.

| Handling | Hjulet | Setning |
| --- | --- | --- |
| Open door (84) | høyreklikk, klikk på ikonet | 2 84 0 |
| Pull dresser drawer (92) | hold og dra | 6 92 0 |
| Turn on lamp (103) | høyreklikk, klikk | 5 103 0 |
| Pull window shade (90) | høyreklikk, klikk | 6 90 0 |
| Turn on cat clock (95) | høyreklikk, klikk | 5 95 0 |
| Read ticket (82, inventaret) | høyreklikk på inventaret, klikk | 12 82 0 |
| Use ticket in door | høyreklikk på inventaret, Use, venter, klikk på døren | 14 82 84, så 14 84 82 (spillets eget andre forsøk, likt i originalen) |
| Use ticket, så høyreklikk | avbrudd | ingen setning; preposisjon og objekt er 0 etterpå |

Testet for hånd uten skjerm samme natt: «alle verb» (døren får alle tolv plassene), Ctrl+W av (originalpanelet tegnes igjen) og på (panelet skjules igjen), og skjermbilder som viser at hjulet ryddes bort når det lukkes.

Ikke testet: med skjerm og mus, Esc for å lukke hjulet, langt trykk i nettleseren og på mobil, butikken (Buy og Sell), teleporten, figurbytte, styring av dyr, andre rom enn rom 1, og at valget faktisk lagres i scummvm.ini (ScummVM skrev ingen scummvm.ini i testmiljøet, heller ikke ved avslutning).

## Dynamisk hjul (Toms forslag 13. oktober)

Tom spurte om hjulet kan være dynamisk: høyst tre eller fire ikoner per objekt, verbene slått sammen (øye for Look at og Read; hånd for Pick up, Push, Pull, Open og Close etter hva som går an; bryter for Turn on og Turn off; snakkeboble for Talk to), Fly utenfor hjulet (flybillett på skranken åpner kartet), og figurbytte som små portretter i et hjørne.

Målt med `tools/verbhjul_dynamisk.py` (verbtabellene og objektkoden i work/skript, klassene i 00.LFL):

| Ikoner per objekt | I dag | Lik kode slått sammen | Pluss Open/Close og Turn on/off etter tilstand |
| --- | ---: | ---: | ---: |
| 1 | 119 | 161 | 184 |
| 2 | 104 | 112 | 96 |
| 3 | 58 | 41 | 36 |
| 4 | 36 | 16 | 14 |
| 5 til 7 | 20 | 7 | 7 |

Av 337 objekter med verbkode. «Lik kode» betyr at verbene hopper til samme sted i objektkoden, og at koden ikke spør hvilket verb som ble valgt (Var[52], Var[116], Local[1], også i skript den starter). Give holdes alltid for seg (trenger mottaker), og Use for seg når objektet har preposisjonsklasse. 26 objekter har verb med samme kode som likevel må holdes adskilt av disse grunnene, for eksempel boom-boksen: sju verb går til skript 129, som ser på verbet. Kommoden (91) sender verbet videre til skuffen (92) med `startObject(92,Var[52])`.

Tilstand: spillets egen regel for dører og skuffer er 0 lukket og 1 åpen (globalt skript 31 og 32). 30 av 56 objekter med både Open og Close følger den påviselig i koden; de andre går gjennom lokale skript eller andre variabler og må leses før de slås sammen. For Turn on og Turn off er det påvist for 2 av 18; resten bruker klasser (lampen i rom 6 bruker klasse 6) eller variabler. Til de er lest, vises begge.

Fem eller flere etter sammenslåingen: Sushi i fiskebollen (14), kommoden (91), våtdrakten (39), oksygentanken (50), mikrobølgeovnen (260), boom-boksen (71) og fallskjermen (77). De trenger en regel hver, for eksempel Put on eller Take off etter om tingen er på, og Buy og Sell bare i butikken (hjulet viser allerede bare verb som er på i panelet).

Det betyr:

- Høyst fire valg går an uten å miste noe og uten å endre skriptene: 330 av 337 objekter med de to reglene over, og de sju med en regel for hånd.
- Et fast sett med fire ikoner dekker ikke spillet. Give, Put on, Take off, Buy, Sell og Teleport to finnes på 43 objekter og må være med, og noen objekter har to forskjellige håndhandlinger (strømledningen i rom 2: Pull og Pick up har hver sin kode; rullegardinen i rom 1 har Pull, som veksler, ved siden av Open og Close). Ikonene får derfor faste plasser etter type rundt pekeren, og teksten under hjulet sier hva som skjer («Åpne skuff»). Hånd, øye, tannhjul og bryter kan være motivene.
- Øye: Zak har ikke Look at. Read finnes (93 objekter), og What is er navnet under pekeren. Øyet kan være ikonet for Read.
- Snakkeboble: Zak har ikke Talk to. Samtalene startes av skriptene, når man kommer inn i et rom eller gir noe med Give. Et snakkeikon krever nye skript og ny tekst, og AGENTS sier at skriptene ikke lappes uten Toms ja. Ikke anbefalt.
- Fly: flyreisene virker allerede slik Tom beskriver. Use på reservasjonsterminalen på flyplassen (objekt 194 i rom 8, 220 i rom 9) med CashCard laster reisemålskjermen (rom 45, globalt skript 90, som setter eget inndataskript 92). Terminalen har bare Use og får ett ikon. «Fly to» er Walk to når Zak styrer fuglen (skuespiller 6, globalt skript 24 og 119), og er vanlig klikk, ikke i hjulet.
- Figurbytte: portretter kan sende de samme kallene som Switch og navnet (verb 36, så 37 til 40), slik ScummVM gjør for F1 til F4 i dag. Ingen skriptendring. Portrettene er grafikk og kommer etter stilpiloten; til da navn eller forbokstav.

Plan hvis Tom sier ja: `tools/verbhjul_dynamisk.py --tsv` lager tabellen med gruppene og tilstandsparene fra spillfilene (i work/ og i moden, ikke i main), motoren leser den når den finnes og oppfører seg som i dag uten. Ikonet sender ett av verbene i gruppen, så setningen er en originalen kunne gitt. `tools/verbhjul_test.sh` utvides med skuffen (Open og Close etter tilstand) og et objekt med delt gruppe.

Ikke testet: hjulet er ikke bygget slik. Tallene kommer fra tekstsøk i den dekompilerte koden; skript som startes gjennom en variabel (`startScript(Var[112],...)`) følges ikke.

## Det som gjenstår

- Navnet på objektet under pekeren mens hjulet er lukket (i dag gir What is det i originalen; What is er skjult når hjulet er på, men tasten c virker).
- Valgene i spillets meny (F5) i stedet for bare Ctrl+W og scummvm.ini.
- De 15 ikonene, etter motiv- og designavklaringen i remake-skillen, godkjent av Tom (gjerne sammen med stilpiloten i rom 1).
- Tegning i HD når HD-motoren er portet til Zak.
- Prøve med skjerm, i nettleseren og på mobil, og i butikken, teleporten, ved figurbytte og når man styrer dyr.

## Kilder

- PopMatters, "Day of the Tentacle Remastered: Remastering a Classic": https://www.popmatters.com/day-of-the-tentacle-remastered-remastering-a-classic-2495438589.html
- PCWorld, anmeldelse av Day of the Tentacle Remastered: https://www.pcworld.com/article/414548/day-of-the-tentacle-remastered-review-sludge-o-matic-sucker-for-love.html
- Destructoid, om grensesnittet i DOTT Remastered på PS4: https://vip-develop.destructoid.com/?p=176291
- ScummVM ved c9091321: `engines/scumm/verbs.cpp` (`checkExecVerbs`), `script.cpp` (`runInputScript`, `getVerbEntrypoint`), `vars.cpp`.
- De dekompilerte skriptene: globalt skript 7 (setter `VAR_VERB_SCRIPT`), 11, 15, 21, 22 og 36.
