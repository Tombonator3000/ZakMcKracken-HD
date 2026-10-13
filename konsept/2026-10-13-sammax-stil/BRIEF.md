# Zak-scene i Sam & Max-stil

Bestilt av Tom 13. oktober 2026: ett testbilde av en valgfri Zak-scene tegnet i Sam & Max-stilen, etter kontroll av de forbedrede metodene i Sam & Max-repoet. Denne særskilte konseptbestillingen autoriserer stiloverføringen for testen. Den endrer ikke serieordren eller gjør testen til et godkjent Zak-stilanker.

## Motivet

Rom 42, jungelen med inka-fuglemateren. `origin/main:docs/romnavn.csv` kobler rommet til objektnavn og replikken «Ancient Incan Bird Feeder». Originalreferansen er engelsk FM-Towns-skjermbilde fra ScummVM: https://www.scummvm.org/data/screenshots/scumm/zak/zak_fmtowns_en_1_1_full.png

Originalskjermen er 640 x 480. Konseptet viser bare romfeltet, x 0 til 640 og y 32 til 288, med sideforhold 2,5:1. Verbpanel, inventartekst og svarte kanter inngår ikke i denne tegnestiltesten. Ingen ny funksjon eller nytt grensesnitt foreslås.

Låst innhold: skog til venstre, fjell og skyer i bakgrunnen, grusgrunn og steiner i forgrunnen, én Zak, én fugl på én steinfuglemater, skilt ved materens venstre side. Behold relativ plassering og størrelse, og lokal palett. Fuglemateren er et interaksjonsobjekt, ikke en tilfeldig tempelruin. Skiltets pikselmerker gir ikke grunnlag for ny lesbar tekst.

Zak beholder menneskelig identitet, kort brunt hår, smalt kantete ansikt, blå skjorte, rødt slips, brunt belte med gul spenne, mørke bukser og brune sko. Ingen Sam & Max-personer eller kontorrekvisitter overføres. Dette er én stillestående pose; animasjonsidentitet testes ikke.

## Metode hentet fra dagens Sam & Max-arbeid

Kontrollert grafikkworktree: `Sam-Max-HD/work/.gpt-gren`, `gpt-arbeid`, commit `f77b860a` ved undersøkelsen. Aktivt arbeid der er bare lest.

Stilreferansen er `rapporter/stilpilot-fortsettelse-20261013/kontor-helrom.png`, kopiert byteidentisk til `referanser/sammax-godkjent-kontor.png`. Godkjenningen er dokumentert i samme rapports `TOMS-GODKJENNING.json` og `stil/manifest.json`. De to romdelene i stilmanifestet er SHA-kontrollert. Eldre konseptkandidater fra 12. oktober brukes ikke som ankre.

- Originalen er bilde 1 og innholdsfasit. Godkjent fullscene er bilde 2 og styrer kun tegnebehandlingen.
- Nyere rettelse om tynnere, varierte konturer og lettere innvendige streker inngår i prompten.
- Hele scenen med figur tegnes samlet, slik at figur, lys og materialer hører sammen.
- Råresultat, faktisk prompt, referanser og sjekksummer bevares. Synlige motivavvik vurderes separat fra filformat og mål.
- Én konseptkandidat leveres. Brukergodkjenning, produksjonsimport og spilltest er egne senere tilstander.

## Verktøy

Innebygd ChatGPT-bildegenerator. Verktøyet eksponerer ikke et bekreftet modellnavn. Ingen ekstern kredittjeneste brukes.
