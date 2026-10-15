# HD-motoren for Zak McKracken (FM-Towns)

Kort versjon for Zak. Hvordan motoren virker, innstillingene, testkrokene og hva som er testet, står i The Digs [HD-MOTOR.md](https://github.com/Tombonator3000/Dig-HD-Remake/blob/main/docs/HD-MOTOR.md) og i Sam & Max sin [HD-MOTOR.md](https://github.com/Tombonator3000/Sam-Max-HD/blob/main/docs/HD-MOTOR.md).

## Status 11. oktober 2026

- `engine/patches/0001-dighd-hd-grafikk.patch` er Sam & Max sin patch (The Digs patch utvidet for v6) mot ScummVM `c9091321` (`engine/SCUMMVM_COMMIT`). Den er ikke endret for Zak.
- 15. oktober 2026: 0001 er byttet til den felles patchen for The Dig og Sam & Max (byte for byte lik `engine/patches` i begge, Dig main bf582dc). Den har r12-rettingene fra The Dig og lista over det som vises uten HD (`dighd-uten-hd.txt`). 0002 (verbhjulet) legger seg uendret oppå; `tools/verbhjul_test.sh` bestått.
- DigHD er **ikke** på for Zak. `DigHD::create` godtar bare `GID_DIG` og `GID_SAMNMAX`. Spillet kjører som vanlig ScummVM, og en mod gjør ingenting.
- Verbhjulet ligger i en egen patch oppå denne, `engine/patches/0002-verbhjul.patch` (docs/VERBHJUL.md). Hjulet tegnes rett før `updateScreen`, etter FM-Towns-lagene, og må flyttes inn i HD-laget når DigHD er portet.
- Testet: `engine/build.sh` bygget motoren med patchen og FLAC her, og Zak startet uten skjerm: `Using gameid zak, variant FM-TOWNS`, SCUMM 3, riktig MD5, rommene 49, 1, 47, 9 og 50 ble lest (introen). Ikke spilt med skjerm og lyd.

## Status 15. oktober 2026: HD-laget virker i Zak

- Motoren bygges med FM-Towns-lagene av: `engine/build.sh` og `engine/build-web.sh` legger `-DDISABLE_TOWNS_DUAL_LAYER_MODE` i `config.mk`. Da går Zak gjennom den vanlige 8-bits tegningen der DigHD henger, i 320 x 240 (HD 1280 x 960). Uten definisjonen sier DigHD fra i loggen og er av.
- I den felles patchen (lik i The Dig og Sam & Max): `DigHD::create` godtar `GID_ZAK`; objektene slår opp `objNNN_01` uansett tilstand i SCUMM v3; testhoppet sammenligner romhøyden med spillflaten (128 linjer i Zak) i stedet for hele skjermen.
- Rom, objekter og figurer får HD. Kostymene går gjennom krokene fra Sam & Max uten endring. Tekst, verb og inventar (tekstflatene utenfor spillflaten) vises som originalpiksler skalert opp.
- Testet uten skjerm med en nearest-mod (`zakhd build-mod --name test-nearest --method nearest --kostymer alle`): `engine/test.sh` 3000 bilder gjennom introen (rom 46, 58, 51, 55), 0 avvik mot originalen og mot full ombygging i 12 av 12 kontroller. Esc forbi introen til soverommet: Zak tegnes med HD-ruter, 13 av 13 kontroller uten avvik. `tools/verbhjul_test.sh` med HD på: bestått, hjulet tegnes riktig på 1280 x 960. Testhoppet til rom 2 virker. Fargene ser ut som med FM-Towns-lagene på (sammenlignet med skjermbildene fra verbhjul-testen, ikke målt).
- Romtesten (`tools/romtest.sh --mod test-nearest --kamera ett`, alle 59 rom): 52 rom med HD-bakgrunn, ingen krasj, 0 avvik mot full ombygging. Rom 13 og 55 er svarte (mørke rom), 15 og 37 forlates før første bilde, 46 er startrommet, 47 er tomt. Rom 31 henger i sitt eget inngangsskript ved testhoppet, også med HD av. Rom 21 og 24 farges om av skriptet (`SO_ROOM_COLOR`): spillet tegner hver indeks 144 høyere enn i uttrekket, så DigHD viser originalpikslene der indeksene ikke stemmer. Det er riktig oppførsel, for et HD-bilde laget fra uttrekket ville fått feil farger (rødt i stedet for sand). Uttrekket må ta med omfargingen.
- Igjen: myk rulling (punkt 1 under, MOTOR-FORBEDRING del 4), HD-glyfer i `CharsetRendererV3`, menyraden HD Graphics i FM-Towns-menyen (Ctrl+H virker), pekeren, og prøving med skjerm, lyd og på nettsiden.

## Det som må til for Zak

Sjekket mot ScummVM-kilden ved `c9091321`. Ikke testet.

1. **FM-Towns tegner forbi krokene.** `ScummEngine::drawStripToScreen` (gfx.cpp, rundt linje 709 i den patchede kopien) sender FM-Towns-spill til `towns_drawStripToScreen` og returnerer før DigHD sin `blitVirtScreen` (rundt linje 823). FM-Towns-utgavene bruker et eget skjermlag (`_townsScreen`) med 16-bits farger (RGB555) og et tekstlag i dobbel oppløsning; i ScummVM blir skjermen 640 x 480. To veier:
   - **a) Slå av FM-Towns-laget** (`DISABLE_TOWNS_DUAL_LAYER_MODE` ved bygging). Da går v3-spillet gjennom vanlig 8-bits `drawStripToScreen` i 320 x 240 (scumm.cpp i `ScummEngine::init`: med laget slått av får FM-Towns v3 vanlig 8-bits grafikk, og bare v5-spillene stopper), og krokene fra Sam & Max kan brukes nesten som de er. Må sjekkes: om fargene og paletteffektene blir som med laget (`_townsPaletteFlags`), myk rulling, og tekstlaget.
   - **b) Egne kroker i `towns_drawStripToScreen`** og utdataene fra `_townsScreen`. Mer arbeid, men FM-Towns-tegningen beholdes.
   Anbefalt: prøv a) først, med `engine/test.sh` og en nearest-mod. Det avgjør om resten kan gjenbrukes.
   Men merk (14. oktober 2026): FM-Towns-laget gir myk rulling, én piksel per 1/60 sekund (`TownsScreen::scrollLayer`, valget `smooth_scroll`, på som standard). Med a) hopper kameraet 8 originalpiksler, som blir 32 i HD. Myk rulling må da lages i HD-laget før Tom spiller med skjerm. Se docs/MOTOR-FORBEDRING.md, del 4.
2. **Slå på DigHD for Zak.** `DigHD::create` må godta `GID_ZAK` med plattform FM-Towns. Testhoppet (`DIGHD_TEST_ROOM`) leser romstørrelsen fra RMHD; for v3 er det HD-blokken med små hoder (bredde, høyde, antall objekter).
3. **Rom og objekter.** Bakgrunnen og objektene bruker de samme blokkene i motoren som i v4 og v5, men med stripekodekene 1, 2, 3, 4 og 7 for GF_OLD256 (`unkDecode8` til `11`). Uttrekket gir de samme indeksene (pipeline/zakhd/v3grafikk.py). Objekter har **ett** bilde i v3 (`getObjectImage` ser bort fra tilstanden); det vises i alle tilstander unntatt 0. Uttrekket kaller det `objNNN_01.png`, så `noteObject` må slå opp `_01` uansett tilstand. Objektbildene er heldekkende (ingen gjennomsiktig farge i disse kodekene); maskingen mot figurene går gjennom z-planet.
4. **Kostymer.** Klassiske kostymer i format 0x58 (alle 40), tegnet av `ClassicCostumeRenderer`, som Sam & Max. Krokene fra Sam & Max (`drawLimb` med rutenummer lag * 128 + kode, `noteCel`) gjelder. For GF_OLD256 tegnes bare koder under 0x79 (costume.cpp), og startindeksen i animasjonene er én byte i v3; det har bare betydning for `DIGHD_TEST_COSTUME`, som leser COST-hodet.
5. **Tekst.** Tegnet av `CharsetRendererV3` fra 98.LFL og 99.LFL (8 piksler høye, 1 bit per piksel). Kroken `noteGlyph` finnes ikke der. Verbene og inventaret er tekst, så dette er viktigere i Zak enn i Sam & Max (se docs/GRENSESNITT.md).
6. **Ingen blast-objekter og ingen filmer.** v3 har ikke BOMP eller SMUSH.
7. **Ingen fargesykling.** Rommene har ingen CC-blokk, og ScummVM leser fargesykling bare fra versjon 4 (`resetRoomSubBlocks`).
8. **Menyen og pekeren.** Originalmenyen i FM-Towns-utgaven er en annen enn i v6 og v7; raden HD Graphics og pekerkroken må lages for den. F-tastene i Zak FM-Towns håndteres særskilt (verbs.cpp: F1 til F4 bytter figur, 0x8005 er F5). Krav fra Tom (14. oktober 2026): spilleren skal kunne bytte mellom HD og originalgrafikk mens spillet går, med Ctrl+H (`DigHD::handleKey`, finnes) og med menyraden, så det også går på mobil. Valget lagres som `dighd_classic`.
9. **Skjermen.** 320 x 240: meldingslinjen 0 til 15, rommet 16 til 143 (`SetScreen(16,144)`), verb og inventar 144 til 215. Valget `trim_fmtowns_to_200_pixels` gir 320 x 200. Sideforholdskorrigering trengs ikke (kvadratiske piksler).
10. **Grensesnittet** (verbhjul, ikoninventar, rom og panel skalert hver for seg) bygges i det samme laget etter at punkt 1 til 5 virker. Se docs/GRENSESNITT.md.

Rettingen for Esc i `script.cpp` fra The Dig gjelder alle spill i denne motoren, også Zak. Ikke testet med Zak.

## Testkrokene

Krokene (`DIGHD_*`) virker ikke for Zak før DigHD er på. Listen står i Sam & Max sin HD-MOTOR.md. `engine/test.sh` sjekker til da bare at spillet starter, og stopper med kode 3 med meldingen om at DigHD ikke er på.

## Lærdom fra The Dig og Sam & Max som gjelder her

- Pikselformatet: `createFormatRGBA32()` er rekkefølgen i minnet. Les kanalene med `rShift`, `gShift`, `bShift` og `aShift`.
- Paletten kan endres mellom tegningen av skuespillerne og sendingen til skjermen. Bygg det som trenger de nye pikslene, i kroken før `updateScreen`.
- PNG med tRNS blir RGBA i ScummVMs dekoder. Fjern tRNS og les den gjennomsiktige indeksen selv.
- Innstillinger lagres i `kApplicationDomain`.
- Sam & Max: når et tekstlag legges over bufferen før blit, må DigHD få både den sammensatte kopien og området i bufferen (`vsSrc`), ellers finner den ikke merkene per piksel.
- Patchen lages på nytt med `git add -N` på nye filer og `git diff` i ScummVM-kopien.
