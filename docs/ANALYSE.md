# Zak McKracken HD Remake: analyse av filer, omfang og veien videre

Skrevet 11. oktober 2026. Grunnlaget er spillfilene i grenen `spilldata`, uttrekket med `zakhd extract`, de dekompilerte skriptene (`tools/dekompiler_skript.py`) og kildekoden til ScummVM ved commit `c9091321` (`engine/SCUMMVM_COMMIT`). Oppbyggingen følger analysen i The Dig HD Remake og Sam & Max HD.

## Kort fortalt

- Spillfilene er den engelske FM-Towns-utgaven av *Zak McKracken and the Alien Mindbenders*. MD5 for `00.LFL` stemmer med ScummVM sin oppføring for `zak`, FM-TOWNS, engelsk. Det er den beste kilden: 256 farger, mens PC- og Amiga-utgavene har 16.
- Spillet er SCUMM v3 med 256 farger (`GF_OLD256`, `GF_AUDIOTRACKS`), små blokkhoder (4 byte størrelse og 2 tegn), ikke kryptert. ScummVM kjører det som `zak`.
- 58 rom med grafikk (34 brede som ruller, opptil 960 piksler), alle 128 høye unntatt rom 46 (136). 770 objekter, 585 med eget bilde. 40 kostymer med 847 ruter. To tegnsett. 1094 skript, alle dekompilert uten feil.
- Musikken er 21 CD-spor (FLAC). Ingen tale, ingen filmer, ingen fargesykling.
- Grensesnittet er verbrad og inventar som tekst. Det tar 72 av 240 linjer; rommet bruker 128. Muligheter for et annet grensesnitt står i [GRENSESNITT.md](GRENSESNITT.md).
- HD-motoren må portes til FM-Towns-tegningen før noe HD kan vises ([HD-MOTOR.md](HD-MOTOR.md)).

## 1. Spillfilene

| Fil | Størrelse | Hva det er |
| --- | --- | --- |
| `00.LFL` | 7 520 byte | Indeksen: 0R (rom), 0S (skript), 0N (lyder), 0C (kostymer), 0O (objekter). Ingen romnavn (RN) |
| `01.LFL` til `59.LFL` | 16 til 172 kB | Ett rom per fil: RO-blokken først, så skript (SC), lyder (SO) og kostymer (CO). `47.LFL` har ingen RO, bare ressurser |
| `98.LFL`, `99.LFL` | 2 042 byte hver | Tegnsett 1 og 0 (`ScummEngine_v3::loadCharset` åpner `99 - nr`) |
| `Track1.fla` til `Track21.fla` | 2,5 til 25 MB | CD-musikken i FLAC. ScummVM spiller dem når den er bygget med FLAC |

Til sammen 83 filer, 315 MiB. Alle ligger i grenen `spilldata` med SHA-256 i `game/SHA256SUMS`. Ingen fil er over 90 MB, så ingenting er delt. `tools/hent_spilldata.sh` henter og sjekker.

**Utgave:** MD5 for `00.LFL` er `2d4536a56e01da4b02eb021e7770afa2`, i `scumm-md5.h` ved `c9091321`: `zak`, FM-TOWNS, 7520 byte, `EN_ANY`, plattform FM-Towns. I `detection_tables.h`: versjon 3, `GF_OLD256 | GF_AUDIOTRACKS`. FM-Towns v3 er 320 x 240 (valget `trim_fmtowns_to_200_pixels` gir 320 x 200).

**Formatet** (pipeline/zakhd/lfl.py, sjekket mot ScummVM): `ScummEngine_v3` arver indekslesingen fra v4. Skript, lyder og kostymer står som (rom, offset i rommets fil). Rommet: HD (bredde, høyde, antall objekter), BX, PA (256 farger), SA, BM (bakgrunn med z-plan), OI og OC (objektbilde og objektkode), NL og SL, EX, EN, LC og LS.

## 2. Telling

Målt med `zakhd info`, `zakhd extract` og `tools/dekompiler_skript.py` 11. oktober.

| Hva | Antall | Merknad |
| --- | ---: | --- |
| Rom med grafikk | 58 | 24 på 320 bredde, 34 bredere (384 til 960). Høyde 128, rom 46 er 136 |
| Rom med z-plan | 43 | Ett z-plan per rom (v3: `_numZBuffer = 2`) |
| Paletter | 58 | Én PA med 256 farger per rom |
| Fargesykling | 0 | Ingen CC-blokk; ScummVM leser sykling bare fra v4 |
| Objekter (OC) | 770 | 489 med verb og kode, 281 uten |
| Objektbilder (OI) | 585 | 185 objekter har OI på 8 byte, altså ikke noe eget bilde (en del av bakgrunnen) |
| Kostymer | 40 | Alle i format 0x58 (16 farger), klassisk kostyme, ingen speiling |
| Kostymeruter | 847 | Fra 1784 animasjoner og retninger. 17 animasjoner peker utenfor kostymet (står som advarsel i costumes.json) |
| Tegnsett | 2 | 226 tegn, 8 piksler høye, 1 bit per piksel. 128 og 127 tegn har piksler |
| Globale skript | 169 | Av 199 plasser |
| Lokale skript | 320 | Pluss 58 inngangs- og 58 utgangsskript |
| Lyder | 120 | Av 199 plasser (FM-Towns-lyd og CD-spor) |

**Stripekodeker** (hvor mange striper som bruker hver): rommene 3325 med kode 7, 228 med 2, 175 med 4, 154 med 3 og 128 med 1. Objektene 2824, 23, 176, 236 og 222. Ingen andre koder. Alle er dekodet uten feil.

**Figurene** (fra `ActorOps` i skriptene): skuespiller 1 Zak (kostyme 1), 2 Annie (kostyme 2), 3 Melissa (kostyme 7), 4 Leslie (kostyme 36). Andre: kostyme 10 pilot, 11 flyvertinne, 26 politi, 28 representant og Caponian. Resten er ikke koblet til navn ennå (`docs/figurer.csv`).

## 3. Grafikk som skal byttes ut

Hele listen står i [grafikkliste.csv](grafikkliste.csv) (én rad per rombakgrunn, objektbilde, kostyme og tegnsett), laget med `zakhd grafikkliste`. Romlisten står i [rom-oversikt.csv](rom-oversikt.csv). Sammendrag:

| Type | Antall | Originalpiksler | HD i 4x | Anslag grafikkjobber |
| --- | ---: | ---: | --- | ---: |
| Rombakgrunner | 58 | 4 108 800 | 1280 x 512 til 3840 x 512 | 105 |
| Objektbilder | 585 | 1 184 000 | Males på plass i rommet (lagjobber) | Inngår i rom og lag |
| Kostymeruter | 847 i 40 kostymer | 285 156 | Figurark | 58 |
| Tegnsett | 2 (255 tegn med piksler) | 16 320 | HD-skrift som i The Dig | Ingen (lages i motoren) |
| Inventarikoner (hvis valgt) | 70 til 90 | | Ikonark | Noen få ark |

Anslaget for jobber følger jobbformatet fra The Dig (ett lerret på 1536 x 1024, altså 384 x 256 originalpiksler, brede rom i deler med 64 piksler overlapp; figurark med rundt 24 ruter). Det er til planlegging, ikke jobblisten.

Det som ikke skal byttes: verb- og inventarteksten tegnes med tegnsettene, og blir HD-tekst i motoren, ikke grafikk fra grafikerne. Meldingslinjen likeså.

**Rekkefølge** (fra The Dig og Sam & Max): stilpilot med ett rom og ett figurark først (forslag: rom 1, Zaks leilighet, og kostyme 1, Zak), godkjent av Tom. Så master-figurark for de fire spillbare figurene, så rommene i spillrekkefølge.

## 4. Uttrekket

`zakhd extract` (pipeline/zakhd/eksport_v3.py) skriver til `work/extract`, i samme format som The Dig og Sam & Max:

- `rooms/roomNNN.png` og `_idx.png` (58)
- `objects/objNNN_01.png` og `_idx.png` (585). v3 har ett bilde per objekt; navnet bruker 01
- `costumes/costumeCCC_NNN.png` og `_idx.png` (847), rutenummer lag * 128 + kode
- `fonts/charset0.png` og `charset1.png`
- `rooms.json`, `costumes.json`, `fonts.json`

Kontroll 11. oktober: 0 feil. Alle rom sett på i et kontaktark, rom 1 med alle objektene lagt på plass (riktige plasser), og den største ruten fra hvert kostyme. Rom 46 og 55 er helt svarte i originalen. Ikke sammenlignet piksel for piksel med motoren; det gjøres med nearest-modden når DigHD er portet.

Kostymefargene er palettindekser i rommet. RGBA-bildene bruker paletten i rommet kostymet ligger i (12 av 40 ligger i rom 49, det første rommet introen laster), så fargene kan avvike fra det spillet viser i andre rom.

## 5. Skriptene

`tools/bygg_descumm.sh` bygger descumm (scummvm-tools `8665aa1d`), og `tools/dekompiler_skript.py` kjører den med `-3 -z` på hver skriptblokk. Resultat i `work/skript` (gitignorert): 1094 skript (169 globale, 320 lokale, 58 inngang, 58 utgang, 489 objektskript), alle uten feil, med `OVERSIKT.md` og `objekter.tsv` (nummer, rom, plass, størrelse, bilde, verb og navn).

Nyttig fra skriptene: verbene og inventaret settes opp i globalt skript 36 (verb 101 til 110 er inventarplassene, 115 og 116 pilene), skjermen deles med `SetScreen(16,144)`, og figurene får kostyme og navn med `ActorOps`.

## 6. Det som gjenstår

Står i todo.md. Det viktigste: porten av HD-motoren til FM-Towns-tegningen, så stilpiloten.
