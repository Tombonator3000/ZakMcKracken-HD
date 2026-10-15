# Hjul og inventar, Purcell-retning

Tom bestilte grafikken direkte 15. oktober 2026 og presiserte underveis at den skulle ha mer av den rare, lekne og humoristiske stilen fra Steve Purcells Sam & Max. Leveransen ligger i gpt-arbeid, til kontroll. Tom har ikke godkjent disse nye bildene ennå.

## Innhold

15 verbikoner og 81 logiske inventarbilder, inkludert navn- og tilstandsvarianter. Identiske kopier og standardbilder gir 141 PNG-filer som dekker 105 objektnumre. De 18 objektnumrene merket «trolig ikke» i motivlisten er utelatt. Rader merket «usikker» i listen er fortsatt usikre; de finnes i manifest.json.

PNG er 512 x 512 med ekte alfa. Hjulet har kremfarget mynt og mørk kant. Inventaret har løse gjenstander. Samme gjenstand flere steder bruker identiske filer. Enkeltkortet obj074-cashcard er samme tegning som obj018.

## Stil og kilder

Jeg så farge- og tusjreferansene i Sam & Max-arbeidsbordet, samt det godkjente kontorankeret. De to Purcell-referansene er Toms vedlegg fra 13. oktober, ifølge repoets referansemanifest. Fargebildet og de nye UI-prøvene styrer den videre serien. Skjeve silhuetter, knoklete hender, asymmetri, varierende penntjukkelse, lettere detaljstreker og noen svarte skyggekiler gir særpreget. Motiver, fargekoder og handlinger følger GRAFIKK-HJUL-OG-INVENTAR.md.

Første, glattere serie er arkivert lokalt i stil01 og inngår ikke i leveransen. Sam & Max-figurene er ikke rekvisitter i Zak; medlemskortets feilaktige figurer er derfor erstattet med egen stjernedekor.

## Verktøy og prompter

Alle nytegninger og tegnede rettelser bruker innebygd image_gen. Verktøyet oppgir ikke modellnavn. FFmpeg brukes til vanlig eksport til 512 x 512 og til kontaktark. Python brukes til filkopier, sjekksummer, formatkontroll og pakking, ikke til å tegne eller rette motivene.

bestilling-v2.json og bestilling-v3.json bevarer promptsettene. kall/ inneholder de bevarte faktiske kallene og rettelsene. En post med -final gjelder foran en tidligere post for samme fil. Antallet promptposter er ikke et komplett antall forsøk: enkelte avviste eller avbrutte kall fra de stoppede seriene er ikke telt per objekt. Råfilene og vrakede kandidater er beholdt lokalt i raa/, revisjoner/ og stil01/, og inngår ikke i GitHub-leveransen eller ZIP-pakken.

## Kontroll

Alle 141 PNG er kontrollert for RGBA, 512 x 512, ekte alfa og filstørrelse under 90 MB. Alle er tatt inn med repoets build_ui, og de dekodede pikslene er identiske før og etter import. Alle aliaser er byteidentiske med kilden. SHA256SUMS, aliaser.json og manifest.json dokumenterer den valgte mengden.

Hjulet og alle 81 logiske inventarbilder er visuelt gjennomgått på kontaktark i liten størrelse. Rettet blant annet telefonregning tolket som pengeseddel, en nesten rett bøyd kniv, CashCard-bunke med feil dekor, medlemskort med figurer fra stilreferansen, A-stige, hele krystaller i stedet for biter og ujevne alfakanter i tom fiskebolle. Tent og slukket lighter, lommelykt og opptakslys er kontrollert som par.

Ikke testet i motoren eller i faktisk spilltilstand. Teknisk import og bildesjekk er ikke Toms visuelle godkjenning.

## Tolkninger som må beholdes synlige

Originalinventaret er tekst, så motivlisten beskriver mange ting ut fra navn og bruk. Filthatt, enkelte usikre inventargjenstander og den lysende gjenstandens nøyaktige design er ikke dokumentert med originalikon. Den lysende gjenstanden er tegnet som en enkel lysende form, uten oppdiktet flaske eller apparat. Kartvariantene er symbolske ikoner med gule fargestiftstreker, ikke erstatninger for spillets gåtekart.

## Mottak

ui/verbhjul/ og inventory/ kan brukes som --egne-kilde i den eksisterende pipelinen. Godkjente filer flyttes etter repoets mottaksflyt til grafikk/ui/verbhjul-gpt/ og grafikk/inventar/. Spillets motor, skript og main er ikke endret.

forhandsvisning.html er en lokal grafikkoversikt med søk, lys og mørk bakgrunn, alfa og forstørrelse. Kontaktarkene er forhåndsvisninger, ikke skjermbilder fra motoren.

## Innlegging i hovedrepoet, 15. oktober 2026

Tom ba om at hele leveransen legges i repoet via PR. De 15 verbikonene ligger nå i grafikk/ui/verbhjul-gpt/ og de 126 inventarfilene i grafikk/inventar/, slik build_ui forventer. Filene er byteidentiske med leveransen i gpt-arbeid. Manifest, aliaser, galleri og sjekksummer er tilpasset mappene. Produksjonsnotatene over beskriver status ved tegning; innleggingen er ingen påstand om ny spilltest eller visuell godkjenning.

## Toms godkjenning, 15. oktober 2026

Tom godkjente hele inventar- og verbhjulleveransen. Unntaket gjaldt The King i karakterarkene, ikke UI-bildene. Dette er visuell godkjenning og endrer ikke den oppgitte statusen for motorprøving.
