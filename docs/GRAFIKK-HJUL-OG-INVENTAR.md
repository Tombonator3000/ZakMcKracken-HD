# Grafikk til verbhjulet og inventaret: liste til ChatGPT

Skrevet 15. oktober 2026 (Claude) etter Toms ønske om en liste over tingene og hvordan de ser ut, så ChatGPT kan lage grafikken. Motoren er klar: bildene vises i spillet så snart de ligger i HD-modden (se [VERBHJUL.md](VERBHJUL.md)). Ingenting her er bestilt ennå; Tom bestemmer når.

Kilder: navnene og rommene er fra spillfilene (`docs/inventar.csv`, `tools/inventarliste.py`), navnebyttene fra skriptene (`setObjectName`). Utseendet er beskrevet ut fra navnet, rommet og hva tingen brukes til i spillet. Bildene av objektene i rommene viser for det meste stedet der tingen ligger (en åpen skuff, en tom hylle), ikke selve tingen, og er derfor ikke fasit. Det som er usikkert, står som usikkert.

## Felles for alle bildene

- Stilen fra stilankerne i [grafikk/stil/](../grafikk/stil/README.md): lett leken tegneserie inspirert av Steve Purcell, mørk brun-svart kontur, flate farger med ett skyggetrinn. Legg ved ett av ankrene som bilde to.
- PNG med gjennomsiktig bakgrunn (ekte alfa), 512 x 512.
- Én ting per bilde, alene, midt i bildet, sett litt ovenfra og forfra (tre fjerdedels vinkel), og fyll omtrent 80 prosent av bildet. Ingen tekst, ingen skygge på bakken, ingen bakgrunn.
- Tingen skal kunne kjennes igjen når bildet vises i 150 til 200 piksler.
- Ingen logoer eller merkenavn fra den virkelige verden.

Levering: `gpt-arbeid/ui/verbhjul/<fil>` og `gpt-arbeid/inventory/<fil>`, med `notat.md` som for de andre jobbene. Claude kontrollerer, og Tom godkjenner. Godkjente bilder flyttes til `grafikk/ui/verbhjul-gpt/` og `grafikk/inventar/`.

## Del 1: Ikonene i verbhjulet (15)

Claude har tegnet en første utgave som er bygget inn i spillet (`grafikk/ui/verbhjul/*.png`, se dem før du begynner). De malte erstatter dem ett og ett. Behold motivene og den runde mynten: motivet i en kremfarget mynt med mørk kant, som fyller hele bildet.

| Fil | Verb | Motiv (engelsk, til prompten) |
| --- | --- | --- |
| `pick-up.png` | Pick up | A cartoon hand reaching down and grabbing a small red ball, a green arrow pointing up |
| `open.png` | Open | A wooden door swung half open, warm yellow light coming through the gap |
| `close.png` | Close | A closed wooden panel door with a brass knob |
| `use.png` | Use | A grey metal cog wheel |
| `give.png` | Give | An open hand, palm up, offering a small red gift box with a yellow ribbon |
| `turn-on.png` | Turn on | A glowing yellow light bulb with short light rays |
| `turn-off.png` | Turn off | A grey, unlit light bulb |
| `put-on.png` | Put on | A blue hat with a red band, a green arrow pointing down onto it |
| `take-off.png` | Take off | A blue hat with a red band lifted up, a green arrow pointing up |
| `read.png` | Read | A wide-open cartoon eye with a blue iris and three eyelashes |
| `push.png` | Push | A hand with the palm forward pushing a wooden crate, motion lines behind the hand |
| `pull.png` | Pull | A fist gripping a red handle on a metal bar, a green arrow pointing left |
| `buy.png` | Buy | A gold coin with a dollar sign, a green arrow pointing down (into the pocket) |
| `sell.png` | Sell | A gold coin with a dollar sign, a red arrow pointing up (out) |
| `teleport.png` | Teleport to | A purple four-pointed sparkle with small golden sparkles around it |

Zak har ikke Talk to eller Look at, så det er ingen munn eller snakkeboble.

## Del 2: Tingene i inventaret

Filnavn: `objNNN.png` for tingen. Har tingen flere navn i spillet (den endrer seg), lages ett bilde per navn: `objNNN-<navn>.png`, med navnet i små bokstaver og bindestrek mellom ordene (for eksempel `obj014-taped-fish-bowl.png`). Motoren velger bildet som passer navnet tingen har akkurat nå, og bruker `objNNN.png` ellers. Står flere objektnummer på samme rad, er det samme ting flere steder i spillet: lag `objNNN.png` for det første nummeret og bruk samme bilde for de andre (Claude kopierer).

Kolonnen «Inventar»: **ja** = tingen havner i inventaret i spillet. **usikker** = skriptene gir den en eier eller Pick up-kode, men det er ikke sjekket i spillet. **trolig ikke** = en del av rommet som bare svarer på Pick up (lag den sist, eller ikke). Lag ja-radene først, i rekkefølgen her.

| Objekt | Fil(er) | Navn i spillet | Funnet | Inventar | Hvordan den ser ut | Motiv (engelsk) |
| --- | --- | --- | --- | --- | --- | --- |
| 14 | `obj014-sushi-in-fish-bowl.png`, `obj014-fish-bowl.png`, `obj014-taped-fish-bowl.png` | Sushi in fish bowl / fish bowl / taped fish bowl | Zaks soverom (1) | ja | Rund glassbolle med vann. Med Sushi: en liten oransje gullfisk i bollen. Tom: bare bollen. Teipet: bollen med grå teip rundt kanten (brukes som hjelm under vann) | A round glass fish bowl with water and a small orange goldfish / the same bowl empty / the empty bowl with grey duct tape around the rim |
| 15 | `obj015-phone-bill.png`, `obj015-phone-bill-map.png` | phone bill / phone bill map | Soverom (1) | ja | Telefonregning, et ark med linjer og et beløp. Etter at Zak har tegnet: kartet fra drømmen tegnet med gult fargestift på baksiden | A folded paper bill with printed lines / the same paper with a simple map drawn in yellow crayon |
| 16 | `obj016.png` | kazoo | Soverom (1) | ja | Liten kazoo, et kort blåseinstrument formet som en ubåt | A small metal kazoo |
| 17 | `obj017-torn-wallpaper.png`, `obj017-wallpaper-map.png` | torn wallpaper / wallpaper map | Soverom (1) | ja | En revet bit tapet med mønster. Senere med kart tegnet med fargestift | A torn strip of patterned wallpaper / the same strip with a crayon map drawn on it |
| 18, 32, 75 | `obj018.png` | CashCard | Soverom (1), kontor (6), Mars-bussen (30) | ja | Plastkort som et bankkort, blått med gull-stripe | A blue plastic bank card with a gold stripe and a chip |
| 74 | `obj074-cashcards.png`, `obj074-cashcard.png` | CashCards / CashCard | Mars-bussen (30) | ja | En liten bunke slike kort / ett kort | A small stack of blue plastic bank cards / a single card |
| 21, 188 | `obj021.png` | remote control | Stue og kjøkken (2), bruktbutikken (7) | ja | Svart fjernkontroll med knapper | A black TV remote control with coloured buttons |
| 22, 262 | `obj022.png` | egg | Kjøkkenet (2), flykabinen (11) | ja | Et hvitt egg | A white egg |
| 23, 623 | `obj023.png` | bread crumbs | Kjøkkenet (2), jungelen ved fuglemateren (42) | ja | En liten håndfull brødsmuler | A small pile of bread crumbs |
| 29, 130 | `obj029.png` | stale bread | Gaten (3), kjøkkenet (2) | ja | Et gammelt, hardt brødstykke | A hard, stale loaf of bread |
| 24 | `obj024.png` | small key | Stue og kjøkken (2) | ja | Liten messingnøkkel | A small brass key |
| 25 | `obj025-box-of-crayons.png`, `obj025-yellow-crayon.png` | box of crayons / yellow crayon | Stue og kjøkken (2) | ja | Eske med fargestifter / én gul fargestift | A cardboard box of crayons / a single yellow crayon |
| 26, 187 | `obj026-butter-knife.png`, `obj026-bent-butter-knife.png` | butter knife / bent butter knife | Kjøkkenet (2), bruktbutikken (7) | ja | Smørkniv / samme kniv bøyd | A plain butter knife / the same knife bent at an angle |
| 31, 395 | `obj031.png` | bobby pin sign | Gaten ved Lou's Loans (5), ørkenen (21) | ja | Et lite skilt med en hårnål festet på (hårnålen brukes som dirk) | A small cardboard sign with a black hair bobby pin clipped to it |
| 34 | `obj034.png` | tool kit | Bruktbutikken (7) | ja | Rød verktøykasse | A red metal tool box |
| 37, 110, 333 | `obj037.png` | rope | Bruktbutikken (7), soverom (1), fangerommet (16) | ja | Kveil med tau | A coiled brown rope |
| 39 | `obj039.png` | wet suit | Bruktbutikken (7) | ja | Svart våtdrakt | A black diving wet suit |
| 40 | `obj040.png` | nose glasses | Bruktbutikken (7) | ja | Falske briller med stor nese og bart (som på lagreskjermen og avisforsiden) | Novelty disguise glasses with a big pink nose and a black moustache |
| 41 | `obj041.png` | guitar | Bruktbutikken (7) | ja | Akustisk gitar | An acoustic guitar |
| 43 | `obj043.png` | hat | Bruktbutikken (7) | ja | Hatt (motivet usikkert; trolig en enkel filthatt) | A brown felt hat |
| 44 | `obj044.png` | golf club | Bruktbutikken (7) | ja | Golfkølle | A golf club |
| 45 | `obj045.png` | book | Flyplassen, avisstanden (8) | ja | Pocketbok | A paperback book |
| 46 | `obj046.png` | whiskey | Flyplassen (8) | ja | Liten flaske whisky | A small bottle of whiskey |
| 47 | `obj047.png` | toilet paper | Flykabinen (11) | ja | Dorull | A roll of toilet paper |
| 48 | `obj048.png` | cushion | Flykabinen (11) | ja | Setepute fra flyet | A small blue airplane seat cushion |
| 49 | `obj049-lighter.png`, `obj049-lit-lighter.png` | lighter / lit lighter | Flykabinen (11) | ja | Sigarettenner / samme med flamme | A cigarette lighter / the same lighter with a small flame |
| 50 | `obj050.png` | oxygen tank | Flykabinen (11) | ja | Liten oksygenflaske med maske | A small oxygen tank with a face mask |
| 51 | `obj051.png` | peanuts | Flykabinen (11) | ja | Liten pose peanøtter | A small bag of airline peanuts |
| 52 | `obj052.png` | tree branch | Ved Mt. Rainier (12) | ja | Grein fra et tre | A broken tree branch |
| 53 | `obj053.png` | abandoned bird nest | Hulen (13) | ja | Fuglereir av kvister | An empty bird nest made of twigs |
| 33 | `obj033.png` | squirrel nest | Hulen (13) | usikker | Ekornreir | A messy squirrel nest of leaves and twigs |
| 54, 56, 183, 184, 645, 646 | `obj054.png` | crystal shard | Flere steder (6, 7, 14, 44) | ja | Bit av en krystall | A small sharp shard of clear crystal |
| 653 | `obj653.png` | crystal shards | Stonehenge (44) | ja | Flere krystallbiter | A few sharp crystal shards |
| 55, 186, 431 | `obj055.png` | blue crystal | 14, 7, 25 | ja | Blå krystall | A glowing blue crystal |
| 57, 185, 429 | `obj057.png` | yellow crystal | 44, 7, 25 | ja | Gul krystall | A glowing yellow crystal |
| 58, 430 | `obj058.png` | white crystal | 15, 25 | ja | Hvit krystall | A glowing white crystal |
| 428 | `obj428.png` | crystalabra | Krystallkammeret (25) | ja | Lysestake med krystaller i stedet for lys | A candelabra holding crystals instead of candles |
| 80 | `obj080.png` | candelabra | Dalen (43) | ja | Lysestake i messing med tre armer | A brass three-armed candelabra |
| 59, 647 | `obj059.png` | flagpole | Utendørs med jak (17), Stonehenge (44) | ja | Flaggstang | A long flagpole |
| 60 | `obj060.png` | jail key | Fengselet (18) | ja | Stor jernnøkkel | A large iron jail key |
| 61, 62, 63 | `obj061.png` | token | Trikkestasjonen på Mars (27) | ja | Polet til trikken | A small metal transit token |
| 64 | `obj064.png` | burnt fuse | Hostellet på Mars (28) | ja | Brent sikring | A burnt-out glass fuse, blackened |
| 73, 471 | `obj073.png` | fuse | Mars-bussen (30), hostellet (28) | ja | Sikring | A glass cartridge fuse |
| 65, 66 | `obj065.png` | helmet | Mars-overflaten (26) | ja | Romhjelm | A round space helmet with a visor |
| 67 | `obj067.png` | vinyl tape | Hostellet (28) | ja | Rull med grå teip | A roll of grey duct tape |
| 68 | `obj068.png` | broom alien | Hostellet (28) | ja | Et koste-romvesen fra Mars (en kost med øyne) | A broom with small alien eyes, a Martian broom creature |
| 69 | `obj069-flashlight.png`, `obj069-lit-flashlight.png` | flashlight / lit flashlight | Hostellet (28) | ja | Lommelykt / samme med lys | A flashlight / the same flashlight switched on with a beam |
| 70, 535, 536, 537 | `obj070.png` | ladder | Hostellet (28), det store kammeret (29) | ja | Stige | A wooden ladder |
| 71 | `obj071-boom-box.png`, `obj071-recording-boom-box.png` | boom box / recording boom box | Mars-bussen (30) | ja | Stor kassettspiller / samme med rødt opptakslys | A large portable boom box / the same with a red recording light on |
| 72 | `obj072.png` | Digital Audio Tape | Mars-bussen (30) | ja | Liten lydkassett | A small digital audio tape cassette |
| 76 | `obj076.png` | golden key | Labyrinten (35) | ja | Gullnøkkel | An ornate golden key |
| 544 | `obj544.png` | large key | Labyrinten (35) | ja | Stor nøkkel | A large old key |
| 77 | `obj077.png` | parachute | Småflyet (40) | ja | Fallskjermsekk | A parachute pack with straps |
| 78, 427 | `obj078.png` | glowing object | Havbunnen (41), krystallkammeret (25) | ja | Lysende gjenstand | A small mysterious object glowing with light |
| 79 | `obj079.png` | scroll | Dalen (43) | ja | Gammel papyrusrull | An old rolled-up papyrus scroll |
| 81 | `obj081.png` | ankh | Kammeret med ankh (14) | ja | Egyptisk ankh i gull | A golden Egyptian ankh |
| 82, 83 | `obj082.png` | ticket | Sjefens kontor (59) | ja | Flybillett | A paper airline ticket |
| 189 | `obj189.png` | Lotto | Bruktbutikken (7) | ja | Lottokupong | A lottery ticket |
| 609, 610, 614 | `obj609.png` | seaweed | Havbunnen (41) | ja | Tang | A strand of green seaweed |
| 27 | `obj027.png` | fan club card | Gaten (3) | usikker | Medlemskort i en fanklubb | A small fan club membership card |
| 30 | `obj030.png` | application | The Phone Company (4) | usikker | Søknadsskjema | A paper application form |
| 20 | `obj020.png` | power cord | Stue og kjøkken (2) | usikker | Strømledning | A coiled electrical power cord with a plug |
| 106 | `obj106.png` | plastic card | Soverom (1) | usikker | Plastkort | A blank plastic card |
| 139 | `obj139.png` | letter | Gaten (3) | usikker | Brev i konvolutt | A letter in an envelope |
| 175 | `obj175.png` | blotter | Kontoret (6) | usikker | Skriveunderlag | A desk blotter |
| 176, 177 | `obj176.png` | books | Kontoret (6) | usikker | Noen bøker | A small stack of books |
| 179 | `obj179.png` | Yeti skull | Kontoret (6) | usikker | Hodeskalle av en yeti | A large hairy-browed yeti skull |
| 288 | `obj288.png` | paper | Hulen (13) | usikker | Et ark | A sheet of paper |
| 362 | `obj362.png` | yak pie | Utendørs med jak (17) | usikker | Jakmøkk | A flat round yak dung pie |
| 479 | `obj479.png` | can of gas | Hostellet (28) | usikker | Bensinkanne | A red gas can |
| 119, 131 | `obj119.png` | seat cushion | Stue og kjøkken (2) | usikker | Sofapute | A sofa seat cushion |
| 268, 285 | `obj268.png` | two-headed squirrel | Ved Mt. Rainier (12), hulen (13) | trolig ikke | Ekorn med to hoder | A two-headed squirrel |
| 19 | `obj019.png` | receiver | Soverom (1) | trolig ikke | Telefonrør | A telephone receiver |
| 87 | `obj087.png` | telephone | Soverom (1) | trolig ikke | Telefon | An old telephone |
| 95 | `obj095.png` | cat clock | Soverom (1) | trolig ikke | Katteklokke på veggen | A black cat wall clock |
| 107 | `obj107.png` | rug corner | Soverom (1) | trolig ikke | Hjørnet av et teppe | |
| 108 | `obj108.png` | loose boards | Soverom (1) | trolig ikke | Løse gulvbord | |
| 241 | `obj241.png` | exploded egg | Flykabinen (11) | trolig ikke | | |
| 257, 258, 259 | `obj257.png` | suitcase | Flykabinen (11) | trolig ikke | Koffert | |
| 264 | `obj264.png` | toilet paper holder | Flykabinen (11) | trolig ikke | | |
| 267 | `obj267.png` | loose dirt | Ved Mt. Rainier (12) | trolig ikke | | |
| 271 | `obj271.png` | Mt. Rainier | 12 | trolig ikke | | |
| 273 | `obj273.png` | fire pit | Hulen (13) | trolig ikke | | |
| 391 | `obj391.png` | sand pile | Ørkenen (21) | trolig ikke | | |
| 451 | `obj451.png` | sand | Trikkestasjonen (27) | trolig ikke | | |
| 478 | `obj478.png` | covers | Hostellet (28) | trolig ikke | | |

Mangler i listen: ting som bare blir laget eller byttet om underveis kan ha et annet objektnummer enn her. Ser du en ting i inventaret i spillet som ikke står her, si fra med navnet, så legger Claude den til.
