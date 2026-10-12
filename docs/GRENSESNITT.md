# Grensesnittet: verbhjul, ikoninventar og større bilde

Utredning 11. oktober 2026, etter spørsmål fra Tom: kan verblinjen med tekst byttes med et ikonbasert hjul som i *The Curse of Monkey Island* og *Full Throttle*, eller kan inventaret som bare er tekst bli ikoner som i *Monkey Island 2*, så bildet kan bli større?

Kort svar: ja, alle tre lar seg gjøre i HD-laget uten å endre spillets skript, men ikke med et hjul på tre ikoner. Zak bruker 14 verb, og flere gåter avhenger av hvilket verb man velger. Anbefalt rekkefølge står nederst. Ingenting her er bygget eller testet; det forutsetter at HD-motoren først er portet til Zak (docs/HD-MOTOR.md).

## Slik er skjermen i Zak FM-Towns

Funnet i de dekompilerte skriptene (work/skript, globalt skript 1 og 36) og i ScummVM ved c9091321:

| Linjer (y) | Innhold | Kilde |
| --- | --- | --- |
| 0 til 15 | Meldingslinjen (teksten figurene sier, systemmeldinger) | `SetScreen(16,144)` |
| 16 til 143 | Rommet, 128 linjer høyt | `SetScreen(16,144)`, alle rom er 128 høye (rom 46 er 136) |
| 144 til 151 | Setningslinjen ("Walk to door") | verb 100, `SetXY(0,144)` |
| 152 til 175 | 15 verb i tre rader og fem kolonner (x 0, 48, 104, 176, 256) | verb 1 til 14 og 31/36 |
| 176 til 215 | Inventaret: 10 plasser i to kolonner (x 0 og 168) og fem rader, piler på x 152 | verb 101 til 110, 115 og 116 |
| 216 til 239 | Tomt | ScummVM: FM-Towns v3 er 320 x 240 |

Rommet bruker altså 128 av 240 linjer (53 prosent). Verbene og inventaret er vanlige verbplasser som skriptene lager med `VerbOps` (navn, plass, tast). Inventarplassene viser navnet på objektet (`getName`), ikke et bilde.

Verbene i Zak: Push, Pull, Give, Open, Close, Read, Walk to, Pick up, What is, Put on, Take off, Use, Turn on, Turn off, og i noen situasjoner Buy, Sell, Teleport to, Switch og navnene på de fire figurene. Walk to heter Fly to og Swim to der det passer.

Et klikk går gjennom ScummVM sin `checkExecVerbs` (verbs.cpp): klikk på et verb blir `runInputScript(kVerbClickArea, verbnummer)`, klikk i rommet blir `runInputScript(kSceneClickArea, 0)`, og skriptene bygger setningen selv. Et nytt grensesnitt kan derfor sende nøyaktig de samme kallene som et klikk på originalen gjør. Det er nivå to av tre i Double Fines inndeling (endre tilstand, her bare inndata), ikke skriptlapping (docs/HD-REMASTER-METODE.md).

## Forbildene

- **The Curse of Monkey Island** (1997): en mynt med tre ikoner (hånd, hodeskalle, papegøye) dukker opp over objektet; høyreklikk gjør det mest opplagte. Inventaret ligger i en kiste som dekker det meste av skjermen. Siden verbene og inventaret ikke ligger nederst lenger, kan rommet fylle hele skjermen. Modellen kom fra *Full Throttle* (1995).
- **Monkey Island 2** (1991): verbene ble færre (Turn on og Turn off forsvant), og inventaret ble ikoner i stedet for tekst, med verbene nede til venstre og ikonene nede til høyre. Det samme oppsettet kom senere i CD-utgaven av det første spillet.
- **Monkey Island SE** (2010): nytt grensesnitt etter mønster av Curse, med originalen som valg. Kritikken (docs i Dig-repoet, REMASTER-FORBILDER.md): verb og inventar i egne menyer gjorde at man ikke så rommet og inventaret samtidig, og ordspillgåtene ble svakere.
- **Day of the Tentacle Remastered** (2016): et verbhjul rundt objektet med alle de ni verbene, og den gamle verbraden som valg. Grafikk, lyd og grensesnitt kan byttes hver for seg.

## Alternativene

### A. Rommet og panelet skalert hver for seg (16:9 uten å skjule noe)

Rommet (320 x 128) skaleres til full bredde, og verb- og inventarpanelet (320 x 72) tegnes under i sin egen, mindre skala. På en 1920 x 1080-skjerm:

| Oppsett | Rommet på skjermen | Panelet |
| --- | --- | --- |
| Som nå: hele 320 x 240 skalert 4,5 ganger | 1440 x 576 | 1440 x 324 |
| A: rommet 6 ganger, panelet 4,33 ganger | 1920 x 768 | 1386 x 312, midtstilt |

Rommet blir 33 prosent bredere og høyere, altså 78 prosent større flate, og ingenting er skjult: verbene, inventaret og setningslinjen står der hele tiden, som i originalen. Ingenting strekkes (FM-Towns har kvadratiske piksler). Meldingslinjen (y 0 til 15) legges over toppen av rommet med kant og skygge, eller over panelet.

Arbeid: bare i HD-laget: bygg skjermbildet av to deler, og regn musens posisjon om til originalens koordinater. Ingen ny grafikk. Dette er det enkleste og tryggeste.

### B. Inventaret som ikoner (som Monkey Island 2)

Hver inventarplass (verb 101 til 110) tegnes som et bilde av objektet i stedet for navnet, i HD-laget. Navnet vises fortsatt i setningslinjen når musen er over ikonet, så ingenting går tapt.

- Hvor mange: 95 objekter har verbet Pick up (71 ulike navn), og 85 av dem har et eget bilde i rommet (docs/grafikkliste.csv, kolonnen inventar). Noen ting gis av skriptene uten å ligge i et rom. Regn med 70 til 90 ikoner.
- Ikonene males som egne ark (ikonark, jobbformatet finnes fra The Dig), med objektbildet i rommet som referanse.
- Plassen: tekstplassene er 152 x 8 piksler. Ikoner trenger høyde, så panelet må få nytt oppsett (for eksempel to rader med seks ikoner på 24 x 24). Klikk på et ikon sendes som klikk på riktig verbplass, så skriptene merker ingen forskjell. Pilene (verb 115 og 116) beholdes.
- Kombinert med A gir det et lavere panel, så rommet kan bli enda litt større.

### C. Verbhjul (som Day of the Tentacle Remastered)

Langt trykk eller høyreklikk på et objekt åpner et hjul rundt det med alle verbene som ikoner. Valget sendes som klikk på verbet og så på objektet.

- Alle verb må være med. Zak skiller mellom Use, Put on, Turn on, Read og Push, og gåtene bruker forskjellen. Et hjul på tre ikoner som i Curse ville måtte gjette verbet og endre gåtene.
- Hjulet må ikke vise bare de verbene objektet har kode for (verbtabellen i OC-blokken), for det røper løsningen. Det kan eventuelt være et eget hjelpevalg.
- Passer godt på mobil, der verbraden er liten å treffe.
- Trenger 14 til 19 ikoner i samme stil, tegnet en gang.
- Med hjulet kan verbraden skjules, og panelet blir bare inventaret.

### D. Hjul med tre ikoner og fullskjerm som i Curse

Frarådes. Det skjuler verbskillene Zak bygger gåtene på, og inventaret må da skjules i en egen meny, som var hovedkritikken mot Monkey Island SE.

## Anbefaling

1. **A først.** Størst gevinst for minst arbeid, og ingenting skjules.
2. **B etterpå**, når ikonene kan bestilles sammen med objektene (samme grafikere, samme stil).
3. **C som eget valg**, særlig for mobil.
4. Alle valgene i spillets egen meny (F5), hver for seg, med originaloppsettet tilgjengelig hele tiden, slik Tom vil ha det og slik DOTT Remastered gjorde.

Rekkefølgen i arbeidet: HD-motoren portet til Zak (FM-Towns-tegningen), så A, så B og C. Punktene står i todo.md.

## Kilder

- ScummVM ved c9091321: `engines/scumm/verbs.cpp` (`checkExecVerbs`), `scumm.cpp` (FM-Towns v3 er 320 x 240), dekompilerte skript i work/skript (globalt skript 1 og 36).
- Wikipedia, The Curse of Monkey Island (myntmenyen, kisten, fullskjerm, modellert etter Full Throttle): https://en.wikipedia.org/wiki/The_Curse_of_Monkey_Island
- Wikipedia, Monkey Island 2: LeChuck's Revenge (ikoninventar, færre verb, SE-grensesnittet): https://en.wikipedia.org/wiki/Monkey_Island_2:_LeChuck%27s_Revenge
- Adventure Game Studio wiki, Verb coin: https://www.adventuregamestudio.co.uk/wiki/Verb_coin
- REMASTER-FORBILDER.md i Dig-HD-Remake (DOTT Remastered sitt verbhjul, kritikken av MI SE, med kilder).
