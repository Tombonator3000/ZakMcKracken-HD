# Verbhjul: hender og fedora, 15. oktober 2026

Tom ba om bedre fingre og bare hender, uten dressjakke på armene. Under rettingen presiserte han at hattene skal være en fedora. Direkte bestilling gjelder foran den eldre inaktive ORDRE.md. Ingen beskyttede jobbfiler er endret.

11 ikoner er rettet: buy, give, open, pick-up, pull, push, put-on, take-off, turn-off, turn-on og use. De fire ikonene uten hender er uendret. Inventaret er uendret.

Hver hånd er tegnet med én tommel og fire fingre, tydeligere grep og kort bart håndledd uten ermer, mansjetter eller jakke. Grepene er kontrollert visuelt for manglende, ekstra og sammenflytende fingre. Små gripefigurer overlapper fortsatt naturlig, men alle fem fingre inngår i den valgte tegningen. Ingen ny spillfunksjon er lagt til.

Begge hattikonene bruker en blå fedora med rødt bånd, lav krone, midtfold, innklemt front og sammenhengende brem. Inventarhatten obj043 er brukt som formreferanse. Det ferdige «Ta på»-ikonet er ekstra referanse i «Ta av», slik at de viser samme hatt. Fargene følger de eksisterende UI-ikonene.

## Filer og kontroll

- Eksportene er 512 x 512 RGBA med ekte alfa utenfor mynten, med de samme filnavnene som motoren allerede bruker.
- `forhandsvisning.html` viser de 11 ikonene før og etter, med kontrollstørrelser på 64 og 112 piksler.
- `verbhjul-oversikt.png` viser hele settet med 15 ikoner.
- `for/` bevarer de 11 erstattede bildene. `prompter/` inneholder de faktiske promptene for alle forsøk. `genereringer.json` peker på valgte og forkastede genereringer og råfilenes standardplassering.
- Bildearbeidet bruker innebygd image_gen. FFmpeg brukes bare til nedskalering og kontaktark; ingen fingre er tegnet med kode. Rå PNG er bevart både i generatorens standardmappe og lokalt i ignorert `raa/` i grafikkarbeidsbordet.
- SHA-256, alfa, størrelser, eksisterende mottak i `build_ui` og visuell kontroll av kontaktarket er kontrollert. Mottaket skalerer til 256 piksler som før. Piler og handlingsrekvisitter er bevart.

De nye rettelsene er ikke prøvd i spillmotoren og er ikke registrert som visuelt godkjent av Tom. De inngår i oppdateringen av grafikk-PR-en, uten motor- eller pipelineendringer. Tidligere visuell godkjenning gjelder den eldre leveransen; denne rettelsen følger hans konkrete retur.

## Andre retur
Tom avviste buy, give og take-off på nytt. De tre hendene er erstattet. [Ny tegning, kontroll og prompter](../verbhjul-hender-retur-02-20261015/README.md) gjelder foran anatomivurderingen over. Gamle valgte SHA-256 peker nå på de bevarte avviste filene i den nye rapportens for/-mappe.
