# Historisk case: Sam & Max, 12. oktober 2026

Bevart etter Toms bestilling 13. oktober. Innhold og tellinger gjelder Sam & Max, ikke dette repoets eventuelle andre spill. SHA-256 for kildedokumentet før lenketilpasning: `5f49632503614cb0a58221e7c63311f01c4543b50bee22db24d10aaf9bafcc31`. Les [gjeldende stilanalyse](../../ANALYSE.md) først; den presiserer Bigfoot-strek, Purcell-referanser, hattebånd og Max sin munn. Diskplassbegrensningen nedenfor beskriver situasjonen 12. oktober; 13. oktober er det kontrollert rundt 37 GB ledig.

# Figur- og objektanalyse før HD-konvertering

Dette er en delvis konseptleveranse og et kontrollgrunnlag. Ingen av bildene er et godkjent spritesheet. HD-produksjonen er ikke startet.

## Kilder og omfang

Sam & Max Hit the Road, engelsk CD-utgave. Indeks-MD5: `d917f311a448e3cc7239c31bddb00dd2`. Uttrekket omfatter 348 kostymer, 16 052 PNG-ruter og 17 tomme ruter, 83 rombilder og 959 objektbilder. Kostymer er ressurser, ikke en telling av personer.

Brukeren ba om konsept av hvert monster og korrekt analyse av navn, personer og objekter. Arbeidet tar foreløpig med skapninger og øvrige figurer i Sam & Max. Spørsmålet om dette omfanget er riktig, er sendt til brukeren og ikke besvart. 33 motivgrupper er undersøkt; det er ikke bevist at listen dekker alle distinkte skapninger i hele spillet.

Kildearkene er originale pikselbilder forstørret med nearest. De er merket ORIGINAL. Konseptbildene er laget med den innebygde ChatGPT-bildegeneratoren. Verktøyet oppgir ikke eksakt modellnavn. Det er derfor ikke grunnlag for å påstå en bestemt modellversjon.

## Feil som analysen forebygger

- Doug er kostyme 102. Kostyme 103 til 105 er Trixie i tilbakeblikket, bekreftet i globalt skript 120. 107 inneholder Flambé og Trixie; 108 inneholder Bruno og Trixie. Det er ikke nye monstre.
- Bruno, Bigfoot-dørvakten, eldsten og gjestene er egne identiteter. En kostymeressurs kan også inneholde mer enn én person.
- Kostyme 158 viser hodet med lilla turban, briller og grått skjegg. Kokken bruker 159/160 i rom 32. De skal ikke slås sammen.
- Evelyn Morrison er den blonde figuren i kostyme 253, koblet til skuespiller 4 i rom 52 og navngitt i lokalt skript 206. Kostyme 254 viser en annen person som ennå ikke er sikkert navngitt.
- Sam og Max i Bigfoot-drakten er en sammensatt forkledning. Hvite fingre bak Max er en hånd, ikke et tredje hode.
- Conroys tupé er et objekt. Auberginer formet som hodet hans er også objekter.
- OBNA-navn i objekttabellen er interne utviklernavn. De er ikke automatisk navnene spilleren ser.
- Bandet og danserne i rom 53 er synlige i bakgrunnen. Klikkområdene 494/495 gir ikke egne eksporterte PNG-bilder i rooms.json. Ingen figur skal tildeles bandnavn bare fordi navnet finnes i rulleteksten.
- Den ansatte i Mystery Vortex er opp ned. Rosa hud øverst i råbildet er ikke et rosa hodeplagg.

## Viktig begrensning i animasjonsgrunnlaget

`pipeline/smhd/v6grafikk.py` samler hver rutekode bare én gang per animasjonslag (`c not in codes`) og utelater kontrollkodene 0x79, 0x7A og 0x7B. Listen `animasjoner[*].ruter` er derfor en ressursliste i første forekomst-rekkefølge, ikke et komplett avspillingsspor med gjentakelser, venting og varighet. Den må ikke brukes alene til å bygge eller godkjenne spritesheet-avspilling. Originalens kommandostrøm eller faktiske motoravspilling må brukes før produksjon. Ingen motor- eller pipelinekode er endret her.

## Krav før spritesheets

1. Identitet må være avklart for hvert kostyme og hver sammensatt rute. Uavklarte rader i kostymetabellen skal ikke få et oppdiktet navn.
2. Bekreft aktiv bruksrompalett og skuespillerpalett. Lagringsrommets palett i eksporten er bare startreferansen, særlig for frosne figurer, skygger og masker.
3. Behold original `cel`, `lag`, `kode`, mål, `rel_x`, `rel_y`, `move_x`, `move_y`, speiling og tomme ruter. Rute-ID er `lag * 128 + kode`.
4. Lag referanser for hode og kropp samlet i de faktiske retningene. Portrettstudier her gir ikke tillatelse til å finne på usett anatomi.
5. Behold originalens avspillingsrekkefølge, gjentakelser og tempo. En fast skalle skal ikke skifte størrelse når munnen beveger seg.
6. Kontroller hånd mot rekvisitt, fotpunkt, feste mellom lag, z-masker og relevante tilstandsoverganger i spillet.
7. Produksjonsark må ha ekte alfa, myke konturer, rutekart og SHA-256. De grå konseptarkene er ikke alfaressurser.
8. Tom godkjenner konsept/stil. Stilpiloten med ett rom og ett figurark må deretter kontrolleres i motoren før serieproduksjon.

## Kontrollnivå

- Originaluttrekk: 0 dekoderfeil i rooms.json og ved kostymeuttrekket. Begge grafikkfiler er hentet fra spilldata og MD5 er kontrollert. Talearkivet er ikke hentet eller testet.
- Dekompilering: 1179 av 1181 skript uten feil; 2 kjente descumm-feil er fortsatt åpne.
- Hele kostymeoversikten er sett i seks kontaktark. Dette viser én representativ rute per kostyme, ikke alle animasjoner.
- Konseptkandidater er sammenlignet visuelt med sine kildeark. Konkrete avvik er registrert og egne rettelser laget. Ingen kandidat er merket godkjent av Tom.
- Spillet er ikke bygget eller kjørt på nytt. Ingen hode/kropp-kontroll i motor, avspillingskontroll, mod-import eller spritesheet-test er utført.
- Systemdisken gikk full. Bare egne, nyopprettede regenererbare spill-/uttrekks-/dekompileringsfiler er flyttet til RAM-disken. Ingen eksisterende brukerfiler er slettet. Leveranse, kildeutvalg, metadata og skriptbevis ligger i gpt-arbeid.
- RAM-kildene under /tmp er midlertidige. De utvalgte 1x-originalene og skriptbevisene er bevart i leveransen. Hele uttrekket kan regenereres med prosjektets verktøy når diskplass finnes.

## Figurenes identitet og konseptkontroll

### Sam

Type: hovedfigur. Kostyme: 2, 4. Status: **konseptkandidat, ikke produksjonsgodkjent**.

Brun hund, lang snute, blågrå dress og fedora, hvit skjorte, mørk stripet slips.

Første kandidat avvist: oppdiktet hvitt lynmerke på hattebåndet. Ny kandidat skal ha vanlig bånd. Proporsjoner må fortsatt måles mot samlet original.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/sam.png) · [Konsept](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/bilder/sam-v2.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/sam-v2.txt)

Skriptbevis: [globale/scrp_001.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/globale/scrp_001.txt).

### Max

Type: hovedfigur. Kostyme: 3, 5. Status: **konseptkandidat, ikke produksjonsgodkjent**.

Hvit kaninaktig figur, lange ører med rosa innside, bredt glis, kompakt kropp uten klær.

Første kandidat avvist: trekantede sagtenner. Ny kandidat har blokktegnet tannrad. Hode, ører og kropp må kontrolleres gjennom alle taleruter.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/max.png) · [Konsept](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/bilder/max-v2.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/max-v2.txt)

Skriptbevis: [globale/scrp_001.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/globale/scrp_001.txt).

### Bruno

Type: bigfoot. Kostyme: 228, 238, 242. Status: **konseptkandidat, ikke produksjonsgodkjent**.

Brun langpelset Bigfoot, spiss hodelokk, hengende armer, brede føtter. Flere kostymer og sammensatte ruter.

Spiss pelslokk, brun pels og brede føtter er bevart som konseptretning. Sammenlign også den frosne tilbakeblikkvarianten før paletten låses. 242 inneholder ruter med både Bruno og Sam.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/bruno.png) · [Konsept](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/bilder/bruno.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/bruno.txt)

Skriptbevis: [rom_047/lokal_202.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_047/lokal_202.txt), [rom_047/lokal_203.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_047/lokal_203.txt).

### Bigfoot-dørvakten

Type: bigfoot. Kostyme: 255, 256, 257, 258. Status: **konseptkandidat, ikke produksjonsgodkjent**.

Stor mørkebrun pelsfigur med bred munn, tung kroppsbygning. Dørvakt ved konvensjonen, ikke Bruno.

Foldede armer og bandasjeaktige lyse fotpartier må bevares. De hvite feltene er ikke grunnlag for å finne på sko. Senere fil-/pedikyrhandling må vurderes separat.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/bigfoot-dorvakt.png) · [Konsept](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/bilder/bigfoot-dorvakt.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/bigfoot-dorvakt.txt)

Skriptbevis: [rom_052/inngang.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_052/inngang.txt), [rom_052/lokal_207.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_052/lokal_207.txt).

### Bigfoot-eldsten

Type: bigfoot. Kostyme: 271, 273, 274, 275, 277. Status: **konseptkandidat, ikke produksjonsgodkjent**.

Brun pels, svært langt lyst skjegg, spisst hode og vifteformet hodepynt med røde tupper. Bevegelseskostyme 264 har deler.

Langt lyst skjegg, medaljong og vifteformet hodepynt med røde tupper er synlige i kilden. Ikke kall hodepynten grener uten bedre bevis. Egennavn er ikke etablert.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/bigfoot-eldste.png) · [Konsept](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/bilder/bigfoot-eldste.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/bigfoot-eldste.txt)

Skriptbevis: [rom_054/inngang.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_054/inngang.txt), [rom_054/obj_0515_verb.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_054/obj_0515_verb.txt).

### Bigfoot-kvinnen ved bassenginngangen

Type: bigfoot. Kostyme: 267. Status: **konseptkandidat, ikke produksjonsgodkjent**.

Egen kvinnelig Bigfoot, ikke Trixie. Kostymet har adskilte deler; portrettet må beholde kildens hodeform.

Portrettstudie fra hodelag. Kropp finnes i andre lag og er ikke ferdig vurdert. Figuren er den kvinnelige vakten ved bassenginngangen, ikke Trixie.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/bigfoot-kvinne.png) · [Konsept](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/bilder/bigfoot-kvinne.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/bigfoot-kvinne.txt)

Skriptbevis: [rom_053/inngang.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_053/inngang.txt), [rom_053/lokal_202.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_053/lokal_202.txt), [rom_053/lokal_205.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_053/lokal_205.txt).

### Bigfoot-gjest, kostyme 265

Type: bigfoot. Kostyme: 265. Status: **konseptkandidat, ikke produksjonsgodkjent**.

Konvensjonsgjest i rom 53, skuespiller 6. Langt ansikt og spiss pels. Egennavn ikke funnet.

Portrettstudie. Skuespiller 6 i rom 53 er dokumentert. Egennavn mangler. Ikke bruk bandmedlemmenes navn fra rulleteksten på denne personen.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/bigfoot-gjest-265.png) · [Konsept](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/bilder/bigfoot-gjest-265.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/bigfoot-gjest-265.txt)

Skriptbevis: [rom_053/inngang.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_053/inngang.txt).

### Bigfoot-gjest, kostyme 266

Type: bigfoot. Kostyme: 266. Status: **konseptkandidat, ikke produksjonsgodkjent**.

Konvensjonsgjest i rom 53, skuespiller 5. Lysere grå partier og egen hodeform. Egennavn ikke funnet.

Portrettstudie. Skuespiller 5 i rom 53 er dokumentert. Kropp finnes som eget lag. Grå pels og ansiktsfarge må kontrolleres i aktiv rompalett.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/bigfoot-gjest-266.png) · [Konsept](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/bilder/bigfoot-gjest-266.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/bigfoot-gjest-266.txt)

Skriptbevis: [rom_053/inngang.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_053/inngang.txt).

### Doug

Type: muldvarpmann. Kostyme: 102. Status: **konseptkandidat, ikke produksjonsgodkjent**.

Kort og rund muldvarpmann, lys hud, lite rødlig hår, stor spiss nese, brun skjorte og blå/grønn skål. Kostyme 103 til 105 er Trixie i sekvensen, ikke Doug.

Kostyme 102 er Doug. 103 til 105 viser Trixie i tilbakeblikket. Konseptet bruker bare Doug. Skålinnholdet er ikke sikkert identifisert; blå former må ikke låses som blåbær uten dialog-/objektbevis.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/doug.png) · [Konsept](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/bilder/doug.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/doug.txt)

Skriptbevis: [rom_023/inngang.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_023/inngang.txt), [rom_023/obj_0229_verb.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_023/obj_0229_verb.txt).

### Shuv-Oohl

Type: muldvarpmann. Kostyme: 201, 202. Status: **konseptkandidat, ikke produksjonsgodkjent**.

Kort bøyd muldvarpmann med runde briller, lys hud, rød bart, sparsomt rødt hår og lilla klær. Må skilles fra Doug.

Kort kroppsform, runde briller, rød bart, sparsomt rødt hår og lilla skjorte er referansepunkter. Ikke gjenbruk Doug som ansiktsmal.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/shuv-oohl.png) · [Konsept](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/bilder/shuv-oohl.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/shuv-oohl.txt)

Skriptbevis: [rom_039/lokal_201.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_039/lokal_201.txt), [rom_026/lokal_205.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_026/lokal_205.txt).

### Trixie

Type: menneske. Kostyme: 229, 240, 241. Status: **konseptkandidat, ikke produksjonsgodkjent**.

Girafflang hals, gult antrekk og hatt, mørk hestehale, røde støvler. Ikke Bigfoot eller giraffdyr.

Lang hals, gult antrekk, hatt og mørk hestehale beholdes. Halspartiene skal behandles som originalens utforming, ikke gis ny metall-/tre-/robotforklaring. Tilbakeblikket har andre klær.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/trixie.png) · [Konsept](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/bilder/trixie.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/trixie.txt)

Skriptbevis: [rom_047/lokal_202.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_047/lokal_202.txt), [rom_047/lokal_203.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_047/lokal_203.txt).

### Conroy Bumpus

Type: menneske. Kostyme: 68, 231, 232, 233, 234, 244. Status: **konseptkandidat, ikke produksjonsgodkjent**.

Lav mann, overdreven blond tupé, mørke briller, gult antrekk. Tupé og avdekket hode er tilstander av samme person.

Tupé, bar hodebunn og flere handlingskostymer er tilstander av samme mann. Auberginer formet som hodet hans er objekter, ikke personer.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/conroy-bumpus.png) · [Konsept](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/bilder/conroy-bumpus.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/conroy-bumpus.txt)

Skriptbevis: [rom_025/lokal_217.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_025/lokal_217.txt), [rom_045/obj_0431_verb.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_045/obj_0431_verb.txt).

### Lee-Harvey

Type: menneske. Kostyme: 69, 245. Status: **konseptkandidat, ikke produksjonsgodkjent**.

Høy kraftig mann, blondt hår, mørk blå jakke, rød skjorte og mørke sko. Ikke Conroy.

Første kandidat avvist: harde pikselkanter og feil tolkning av bevegelsesstreker. Ny kandidat har glatte konturer og ingen oppdiktede ansiktsutstikkere.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/lee-harvey.png) · [Konsept](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/bilder/lee-harvey-v2.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/lee-harvey-v2.txt)

Skriptbevis: [rom_025/lokal_217.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_025/lokal_217.txt).

### Flambé

Type: menneske. Kostyme: 67, 73, 106, 107. Status: **konseptkandidat, ikke produksjonsgodkjent**.

Stor bar overkropp, bart, lilla hodeplagg og bukser, grønt belte. Ild er egen handling og effekt.

Bar mage, lilla turban/bukse og grønt belte er identitetsankere. 107 inneholder også Trixie. Luefjær, håndredskap og ild skal ikke blandes sammen.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/flambe.png) · [Konsept](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/bilder/flambe.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/flambe.txt)

Skriptbevis: [rom_015/inngang.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_015/inngang.txt).

### Kushman-brødrene

Type: menneskepar. Kostyme: 78, 79. Status: **konseptkandidat, ikke produksjonsgodkjent**.

To sammenvokste tivolibrødre i grønt. Behold begge ansiktene og det faktiske kroppsfestet.

Begge ansikter, sammenvoksingen og de to ulike uttrykkene er bevart som konseptretning. Tilknytning og bein må følges i hele animasjonen.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/kushman-brodrene.png) · [Konsept](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/bilder/kushman-brodrene.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/kushman-brodrene.txt)

Skriptbevis: [rom_016/inngang.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_016/inngang.txt), [rom_015/obj_0988_verb.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_015/obj_0988_verb.txt).

### Snuckey’s-ekspeditoren

Type: menneske. Kostyme: 63, 65. Status: **konsept mangler, diskplass nødvendig**.

Langt smalt ansikt og rød/hvit lue. Bare hode/deler i de valgte kildene.

Identitet og kildeark er ført opp. Konsept og full animasjonskontroll gjenstår.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/snuckeys-ekspeditor.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/snuckeys-ekspeditor.txt)

Skriptbevis: [rom_011/lokal_201.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_011/lokal_201.txt).

### Turisten ved Snuckey’s

Type: menneske. Kostyme: 64. Status: **konsept mangler, diskplass nødvendig**.

Kraftig turist, grønn skjorte, brun bukse og grå hatt. Rollebetegnelse.

Identitet og kildeark er ført opp. Konsept og full animasjonskontroll gjenstår.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/snuckeys-turist.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/snuckeys-turist.txt)

Skriptbevis: [rom_011/lokal_212.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_011/lokal_212.txt).

### Vakten ved tivoliet

Type: menneske. Kostyme: 81. Status: **konsept mangler, diskplass nødvendig**.

Blå lue, tatoveringer på begge overarmer, rød vest, blå bukse, hvite sko, sittende i stol.

Identitet og kildeark er ført opp. Konsept og full animasjonskontroll gjenstår.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/midway-vakt.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/midway-vakt.txt)

Skriptbevis: [rom_017/inngang.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_017/inngang.txt).

### Den ansatte ved garnnøstet

Type: menneske. Kostyme: 148. Status: **konsept mangler, diskplass nødvendig**.

Skallet/lyst hode, runde briller og lang nese. Ikke kokken i kostyme 158.

Identitet og kildeark er ført opp. Konsept og full animasjonskontroll gjenstår.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/twine-ansatt.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/twine-ansatt.txt)

Skriptbevis: [rom_028/inngang.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_028/inngang.txt), [rom_028/lokal_205.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_028/lokal_205.txt).

### Servitøren på garnnøstet

Type: menneske. Kostyme: 158. Status: **konsept mangler, diskplass nødvendig**.

Lilla turban med lys prikk, mørke briller, grå bart/skjegg, rosa ansikt. Ikke kokken i kostyme 160.

Identitet og kildeark er ført opp. Konsept og full animasjonskontroll gjenstår.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/twine-servitor.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/twine-servitor.txt)

Skriptbevis: [rom_030/inngang.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_030/inngang.txt).

### Kokken ved garnnøstet

Type: menneske. Kostyme: 160. Status: **konsept mangler, diskplass nødvendig**.

Rund kokk med hvit kokkehatt og kokkeklær, røde detaljer.

Identitet og kildeark er ført opp. Konsept og full animasjonskontroll gjenstår.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/twine-kokk.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/twine-kokk.txt)

Skriptbevis: [rom_032/inngang.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_032/inngang.txt).

### Fiskeren

Type: menneske. Kostyme: 165, 179, 186. Status: **konsept mangler, diskplass nødvendig**.

Smal mann, grønn/brun fiskerhatt, stor nese, fiskestang med blå snelle og vadeklær.

Identitet og kildeark er ført opp. Konsept og full animasjonskontroll gjenstår.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/fisker.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/fisker.txt)

Skriptbevis: [rom_035/lokal_200.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_035/lokal_200.txt), [rom_035/lokal_202.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_035/lokal_202.txt).

### Den ansatte i Mystery Vortex

Type: menneske. Kostyme: 206. Status: **konsept mangler, diskplass nødvendig**.

Runde blå briller, lyst krøllete hår og opp-ned-ansikt med rosa hud. Ingen bekreftet hodepynt. Rommets opp-ned-tilstand er tilsiktet.

Identitet og kildeark er ført opp. Konsept og full animasjonskontroll gjenstår.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/mystery-vortex-ansatt.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/mystery-vortex-ansatt.txt)

Skriptbevis: [rom_040/inngang.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_040/inngang.txt), [rom_040/lokal_207.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_040/lokal_207.txt).

### Evelyn Morrison

Type: menneske. Kostyme: 253. Status: **konsept mangler, diskplass nødvendig**.

Blondt hår, lyse briller, rosa ansikt. Kostyme 254 er en annen figur som ikke er sikkert identifisert.

Identitet og kildeark er ført opp. Konsept og full animasjonskontroll gjenstår.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/evelyn-morrison.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/evelyn-morrison.txt)

Skriptbevis: [rom_052/inngang.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_052/inngang.txt), [rom_052/lokal_206.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_052/lokal_206.txt).

### Katten i gaten

Type: dyr. Kostyme: 51. Status: **konsept mangler, diskplass nødvendig**.

Svart katt, store gulgrønne øyne, rosa ører, hvitt snuteparti. Max i katten er en annen tilstand.

Identitet og kildeark er ført opp. Konsept og full animasjonskontroll gjenstår.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/katt.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/katt.txt)

Skriptbevis: [rom_009/inngang.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_009/inngang.txt), [rom_009/lokal_213.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_009/lokal_213.txt).

### Budbringerrotten

Type: dyr. Kostyme: 35, 49. Status: **konsept mangler, diskplass nødvendig**.

Brun rotte med rosa ører, snute, labber og lang rosa hale. Ikke den grå figuren i kostyme 48.

Identitet og kildeark er ført opp. Konsept og full animasjonskontroll gjenstår.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/budbringerrotte.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/budbringerrotte.txt)

Skriptbevis: [rom_007/inngang.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_007/inngang.txt), [rom_009/lokal_206.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_009/lokal_206.txt).

### Alligatorene ved Gator Golf

Type: dyr. Kostyme: 126. Status: **konsept mangler, diskplass nødvendig**.

Grønne alligatorer, lang snute og tydelig hale. Plural/kombinert rute må bevares i produksjon.

Identitet og kildeark er ført opp. Konsept og full animasjonskontroll gjenstår.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/alligator.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/alligator.txt)

Skriptbevis: [rom_025/lokal_204.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_025/lokal_204.txt).

### Fisken ved fiskestedet

Type: dyr. Kostyme: 166, 172, 184, 187. Status: **konsept mangler, diskplass nødvendig**.

Stor grønn fisk med store øyne og gap. Fisk, garn og stang er ulike ressurser.

Identitet og kildeark er ført opp. Konsept og full animasjonskontroll gjenstår.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/fisk.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/fisk.txt)

Skriptbevis: [rom_035/lokal_202.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_035/lokal_202.txt).

### Forskeren i åpningsscenen

Type: menneske. Kostyme: 19, 20. Status: **konsept mangler, diskplass nødvendig**.

Mager figur med svart oppstående hår, stor nese og grønn hanske. Bare synlige deler skal tegnes.

Identitet og kildeark er ført opp. Konsept og full animasjonskontroll gjenstår.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/forsker.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/forsker.txt)

Skriptbevis: [globale/scrp_065.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/globale/scrp_065.txt).

### Kvinnen i åpningsscenen

Type: menneske. Kostyme: 8. Status: **konsept mangler, diskplass nødvendig**.

Brunt hår og rosa ansikt. Egennavn ikke etablert. Hode og bundet kropp er separate lag i samme kostyme.

Identitet og kildeark er ført opp. Konsept og full animasjonskontroll gjenstår.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/kvinne-apning.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/kvinne-apning.txt)

Skriptbevis: [rom_002/inngang.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_002/inngang.txt).

### Barnet ved strikkhoppet, kostyme 306

Type: menneske. Kostyme: 306. Status: **konsept mangler, diskplass nødvendig**.

Barn med lyst/brunt hår. Rollen har bare hodedeler i disse kildene.

Identitet og kildeark er ført opp. Konsept og full animasjonskontroll gjenstår.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/barn-bungee-306.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/barn-bungee-306.txt)

Skriptbevis: [rom_060/inngang.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_060/inngang.txt).

### Barnet ved strikkhoppet, kostyme 311

Type: menneske. Kostyme: 311. Status: **konsept mangler, diskplass nødvendig**.

Lyst hår i hestehale, rosa ansikt. Ikke samme hode som kostyme 306.

Identitet og kildeark er ført opp. Konsept og full animasjonskontroll gjenstår.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/barn-bungee-311.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/barn-bungee-311.txt)

Skriptbevis: [rom_061/inngang.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/rom_061/inngang.txt).

### Sam og Max i Bigfoot-drakt

Type: forkledning. Kostyme: 260, 261. Status: **konseptkandidat, ikke produksjonsgodkjent**.

Sammensatt drakt på skuespiller 2 mens Max skjules. Ikke ekte Bigfoot og ikke Conroy.

Første kandidat avvist: hvit hånd ble et ekstra Max-hode. Ny kandidat må vise bare Sam-snute, Max med blond tupé og Max sin hvite hånd. Dette er en forkledning, ikke en ny art.

[Originalreferanse](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/referanser/sam-max-bigfootdrakt.png) · [Konsept](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/bilder/sam-max-bigfootdrakt-v2.png) · [Prompt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/prompter/sam-max-bigfootdrakt-v2.txt)

Skriptbevis: [globale/scrp_100.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/globale/scrp_100.txt), [globale/scrp_103.txt](https://github.com/Tombonator3000/Sam-Max-HD/blob/gpt-arbeid/konsept/2026-10-12/kildebevis/globale/scrp_103.txt).

## Åpne identiteter og rester

Elmo er nevnt på postkortet i rom 26, men en bestemt tegnet ressurs er ikke sikkert koblet til ham. Kostyme 254, robotskuespillerens synlige innhold, frosne Bigfoot-varianter og eventuelle andre skapninger krever videre kontroll. De har ikke fått oppdiktede egennavn eller godkjente konsepter.

Resten av konseptbildene og mer utfyllende kildekontroll krever ledig diskplass. Se galleriet og figurer.json for nøyaktig hvilke motiver som mangler.
