# Zak: første spritesheet

Bestilt av Tom 15. oktober 2026: bare Zak først. Stil og klær følger det godkjente Zak-arket, med brun hårtopp, blå skjorte med oppbrettede ermer, rødt slips, svarte bukser og brune sko.

- `zak-spritesheet.png`: transparent RGBA, 1792 x 864, 24 sammensatte ruter i et 8 x 3-rutenett. Hver celle er 224 x 288. Fire ståretninger, seks gåfaser mot høyre og venstre, fire forfra og bakfra. Venstre er speilet fra høyre.
- `zak-spritesheet.json`: navn, rektangler, ankerpunkt og opprinnelige delnumre per rute. Ankeret er [112, 272] innenfor cellen.
- `jobber/fig001_01` til `fig001_03`: tre tegnede komponentark, 1536 x 1024, med faktiske bildeprompter og rutemetadata.
- `mottak/costumes/`: 51 separat tilpassede PNG-deler fra kostyme 1. Alle kommer fra de nye arkene, uten originalgrafikk som reserve.
- `mottak/myke.json` og `rapporter/forste-leveranse/`: importmålinger, eksplisitt kobling mellom tegnet del og originalrute, og SHA-256 for valgte ark.

## Kontroll og begrensning

Dette er en første pilot til visuell kontroll. De 24 hele figurene er en sammensatt kontrollvisning, ikke bekreftet animasjonstiming i spillmotoren. Kun kostyme 1 er tegnet; andre antrekk og figurer inngår ikke.

Alle 51 deler er koblet og importert: 38 er automatisk merket `ok`, 13 er merket `sjekk`, ingen mangler. De 13 er munnfragmenter (391, 385, 384, 389, 386, 390, 387), hatt (897), glassbolle (899, 898), oksygenmaske (770) og tape (1025, 1024). Merknadene gjelder avvik i silhuett/overlapp og er fortsatt åpne før bruk i motoren. Importen har mekanisk skalert delene til mottaksformatet; mål og flyttinger står i rapporten.

Bildene har ekte alfa, med 0 i tomme områder og maksimal alfa 254 i komponentarkene. Hele figurene er kontrollert visuelt; alle holder seg innenfor cellene uten avklipping. Det er ikke kjørt en spillmotortest av denne nye leveransen.

## Kilder og fremstilling

Originalinndelingen er fra engelsk FM-Towns, kostyme 1, 51 synlige deler. Godkjent stilanker: `grafikk/stil/zak-pilot-v1.png` i kodegrenen, `stil/zak-pilot-v1.png` i grafikkgrenen. Bildearbeidet er gjort med innebygd image_gen, mekanisk uttrekk/tilpasning med eksisterende `zakhd.myk`, sammensetting med FFmpeg og originalens delplasseringer. Ingen ny motor- eller pipelinekode er lagt til.

`prompt-sprite-v1.txt` er den faktiske prompten brukt for hver valgt leveranse. Den eldre automatisk lagde `prompt.txt` er beholdt uendret bare i grafikkgrenen og gjelder ikke denne tegningen; den har en foreldet skyggeregel. De faktiske promptene bevarer ekte v3-piksler og bruker det godkjente stilankeret. Et forsøk på side 2 v2 ble forkastet fordi små munnfragmenter forsvant. Alle tre valgte ark er v1.

Originalreferanser og automatiske sammenligningsbilder oppbevares i `gpt-arbeid`, ikke sammen med HD-leveransen i kodegrenen. [Originaljobber og referanser](https://github.com/Tombonator3000/ZakMcKracken-HD/tree/gpt-arbeid/sprites/zak/jobber). `genereringer.json` dokumenterer genereringskallene. `SHA256SUMS` dekker leveransefilene.
