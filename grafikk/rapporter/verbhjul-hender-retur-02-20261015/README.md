# Andre retur: buy, give og take-off

Tom påpekte på nytt at hender/fingre i disse tre ikonene var feil. Den forrige kontrollen fanget ikke opp anatomifeilene. Tidligere påstander om femfingrede grep er ikke visuell godkjenning av disse tre filene.

Hendene er tegnet helt om med enklere ledd, mykere håndflate og mindre innvendig skravering:

- buy: tommel og pekefinger i myntgrep; tre øvrige fingre løst bøyd inn mot håndflaten. Mynt, lommebok og pil er beholdt.
- give: håndflate vendt opp i trekvartvisning, fire atskilte fingre og separat tommel. Første nye kandidat manglet en synlig lillefinger og ble rettet i v2. Gaven er flyttet litt slik at fingrene er lettere å lese.
- take-off: naturlig løftegrep med tommel over bremmen og fire fingre under. Blå fedora med rødt bånd, midtfold og vanlig brem er beholdt.

Bare disse tre ikonene er erstattet. Tolv andre verbikoner og inventaret er uendret. Filer: 512 x 512 RGBA med ekte alfa, samme filnavn som mottaket allerede bruker. De nye hendene er visuelt gjennomgått i nærbilde og som 112-pikslers ikoner. Anatomikontrollen er manuell, ikke en konklusjon fra alfa eller filformat.

`forhandsvisning.html` viser før og etter. `for/` er de tre avviste filene fra forrige runde, bevart som historikk. `kontroll-112.png` viser de nye ikonene i liten størrelse. `genereringer.json`, `prompter/` og `SHA256SUMS` dokumenterer valgte filer og faktiske prompter. Fire kall med innebygd image_gen, ingen modellbetegnelse oppgitt. FFmpeg gjør bare eksport og kontaktark. Råfiler er bevart i generatorens standardmappe og lokalt i ignorert `raa/`.

Eksisterende build_ui tar inn de tre bildene med normal nedskalering til 256 piksler. Ingen motor- eller pipelinekode er endret. Ikke prøvd i spillmotoren og ikke registrert som godkjent av Tom.
