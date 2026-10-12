# Verbhjulet (alternativ C)

Tom valgte 12. oktober 2026 et verbhjul som i *Day of the Tentacle Remastered*. Dette dokumentet klargjør det: hvordan DOTT Remastered gjorde det, hva skriptene i Zak krever, forslaget til oppførsel, ikonene, arbeidet i motoren og testene. Ingenting er bygget ennå. Tallene er målt i FM-Towns-utgaven med `pipeline/zakhd/lfl.py` og de dekompilerte skriptene (work/skript) 12. oktober.

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

## Forslag til oppførsel

Dette må Tom godkjenne før det bygges.

- **Peke:** navnet på objektet vises i setningslinjen, som What is gjør i dag. What is trenger da ikke noe ikon.
- **Trykk eller venstreklikk på et objekt:** Walk to, som i originalen. Det kjører også koden objekter har for Walk to (123 objekter, for eksempel dører).
- **Hold inne eller høyreklikk på et objekt:** hjulet åpnes rundt objektet med objektets verb. Høyreklikk har ingen egen betydning i v3 i dag (ScummVM sender det som et vanlig klikk), så det kan brukes.
- **Hvilke verb:** de som har en egen oppføring i objektets verbtabell (OC-blokken, fra byte 19), og som er på i verbpanelet akkurat nå. Det siste gjør at Buy bare vises i butikken og Teleport to bare når det verbet er på, uten at hjulet må kjenne spillets moduser.
- **Faste plasser:** hvert verb har alltid samme plass i hjulet, så hånden lærer det. Forslag: rekkefølgen i originalpanelet (Push, Open, Put on, Turn on øverst, så Pull, Close, Pick up, Take off, Turn off, så Give, Read, Use). Plassene som ikke gjelder objektet, står tomme eller grå.
- **Ikon og tekst:** hvert ikon har verbet som tekst ved siden av. Det hindrer gjetting og gjør hjulet lesbart før ikonene er tegnet.
- **Valg:** hjulet sender nøyaktig de samme kallene som originalpanelet: verbet (`runInputScript(1, verb, 0)`), så objektet (`runInputScript(2, 0, 0)` med musen på objektet), så setningslinjen (`runInputScript(1, 100, 0)`) for å kjøre. Ingen skript endres.
- **To objekter (Use with, Give to):** når Var[119] er satt etter valget, lukkes hjulet og setningen venter ("Use oxygen tank with"). Neste trykk på et objekt, en figur eller en ting i inventaret fullfører, og setningslinjen kjøres som over. For å avbryte sender hjulet et klikk på Walk to (verb 3). Når en preposisjon venter, kjører skript 11 da skript 18, som tømmer setningen, akkurat som når man klikker Walk to i originalpanelet. Et trykk på tomt gulv tømmer ikke setningen i originalen.
- **Inventaret:** hold eller høyreklikk på en ting i inventaret gir hjulet med tingens verb. Klikket sendes som klikk på verbplassen (101 til 110).
- **Objekter uten hjul:** objekter med bare Walk to eller bare 255 (152 objekter) gjør det de skal med et vanlig trykk. Kulisser uten verb får ikke hjul.
- **Spesialmodus:** når panelet viser verb 31 til 40 (dyr, Switch, figurvalg, tegning), vises panelet som i originalen og hjulet er av.
- **Panelet:** med hjulet på kan de tre verbradene (y 152 til 175) skjules. Setningslinjen og inventaret står. Panelet går fra 72 til 48 linjer.
- **Valg i spillets meny (F5):** Verbhjul av eller på, og hjulet med "verb for objektet" (som DOTT) eller "alle verb" (ingen hint). Originalpanelet kan alltid velges. Valget lagres.

Hinting: å vise bare verbene objektet har kode for, røper noe (at tapetet kan dras i, for eksempel). DOTT Remastered godtok det. Valget "alle verb" er for den som vil spille uten hint.

## Ikonene

Listen står i [verbhjul-verb.csv](verbhjul-verb.csv): verbnummer, tekst, tast, plass i panelet, hvor mange objekter som har kode for verbet, og et forslag til motiv. Hjulet trenger 15 ikoner: Push, Pull, Open, Close, Pick up, Put on, Take off, Turn on, Turn off, Give, Read, Use, Buy, Sell og Teleport to. Walk to og What is trenger ikke ikon.

Bestillingen er ikke aktiv. Etter remake-skillen (docs/skills/scumm-hd-remake/SKILL.md, "Før HD-produksjon") skal motiv og design avklares først: ikonene skal passe til grafikken i FM-Towns-utgaven, være lesbare i 32 til 64 piksler, være ett sett i samme stil, og godkjennes av Tom sammen med stilpiloten. Motivene i CSV-filen er forslag.

## Arbeidet i motoren

Kan bygges som en del av patchen, i denne rekkefølgen:

1. **Logikken:** tilstand for hjulet (lukket, åpent på objekt, venter på andre objekt), lesing av verbtabellen (eget oppslag uten 255, siden `getVerbEntrypoint` også godtar 255), sjekk av hvilke verb som er på i panelet (`_verbs[slot].curmode`), og sendingen av kallene over. Dette kan testes uten skjerm før HD-motoren er portet.
2. **Inndata:** høyreklikk og langt trykk (berøring) i `ScummEngine::parseEvent` eller der musetastene leses, og at `checkExecVerbs` ikke får klikkene mens hjulet er åpent.
3. **Tegningen:** i HD-laget når DigHD er portet til Zak (docs/HD-MOTOR.md). Til da kan en enkel versjon med bare tekst tegnes for å prøve oppførselen.
4. **Panelet:** skjule verbradene og flytte inventaret, sammen med alternativ A (rom og panel i hver sin skala) når det kommer.
5. **Menyvalgene** i F5-menyen.

## Tester

- **Samme resultat som originalen:** for hvert objekt i et rom: kjør setningen én gang med originalpanelet (verb, objekt, setningslinje) og én gang med hjulet, uten skjerm, og sammenlign `doSentence` (verb, objekt A, objekt B) i loggen. Skal være likt for alle objekter og verb i hjulet.
- **To objekter:** Use med preposisjon og Give, også fra inventaret.
- **Spesialmodus:** at hjulet er av når panelet viser verb 31 til 40, og at Buy bare vises i butikken.
- **Berøring:** langt trykk i nettleseren og på mobil.
- Tom spiller med skjerm og sier hva som føles feil.

## Åpne spørsmål til Tom

1. Standard: verb for objektet (som DOTT) eller alle verb?
2. Både høyreklikk og hold inne på PC, eller bare det ene?
3. Tekst ved siden av ikonene hele tiden, eller bare når man peker?
4. Ikonene i samme stilpilot som det første rommet og Zak, eller som en egen pilot?

## Kilder

- PopMatters, "Day of the Tentacle Remastered: Remastering a Classic": https://www.popmatters.com/day-of-the-tentacle-remastered-remastering-a-classic-2495438589.html
- PCWorld, anmeldelse av Day of the Tentacle Remastered: https://www.pcworld.com/article/414548/day-of-the-tentacle-remastered-review-sludge-o-matic-sucker-for-love.html
- Destructoid, om grensesnittet i DOTT Remastered på PS4: https://vip-develop.destructoid.com/?p=176291
- ScummVM ved c9091321: `engines/scumm/verbs.cpp` (`checkExecVerbs`), `script.cpp` (`runInputScript`, `getVerbEntrypoint`), `vars.cpp`.
- De dekompilerte skriptene: globalt skript 7 (setter `VAR_VERB_SCRIPT`), 11, 15, 21, 22 og 36.
