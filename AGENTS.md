# AGENTS.md (grenen gpt-arbeid)

Denne grenen er arbeidsbordet for HD-grafikken til Zak McKracken HD Remake (engelsk FM-Towns-utgave). Du er grafikeren. Claude skriver koden, Tom godkjenner.

**Ikke aktiv ennå.** Stilankerne i `stil/` er godkjent av Tom (14. oktober 2026). Ikke lag grafikk før Claude har skrevet en `ORDRE.md` med jobber. Finnes det ingen `ORDRE.md` eller ingen jobber under `jobber/`, er det ingenting å gjøre.

Les `ORDRE.md` først. Den er siste beskjed fra Claude, med jobbene du skal gjøre nå. Les deretter `BESTILLING.md`, som gjelder foran alt annet her.

Les også [stil/README.md](stil/README.md), som beskriver de godkjente stilankerne, og [ANALYSE.md](ANALYSE.md) før nytegning. Analysen bevarer Toms DOTT-/strekrettelser og skiller spillets stil fra eksemplene i andre spill.

## Kildetro grafikk før produksjon

Les [remake-skillen i main](https://github.com/Tombonator3000/ZakMcKracken-HD/blob/main/docs/skills/scumm-hd-remake/SKILL.md), særlig «Før HD-produksjon: avklar motiv og design», før stilpilot og nytegning. Avklar motiv, funksjon, riktig palett, person/drakt og design fra originalen i spillkontekst. Bruk spillets egne godkjente stilankere og dokumenter grunnlaget i eksisterende analyse og jobbnotat. Kontroller samme identitet gjennom hele animasjonen og hode/kropp samlet i spillet; alfa og ruteantall beviser ikke riktig motiv.

Regelen gjelder også når jobbformatet ber om ordrett prompt. Ved påvist feil premiss: behold beskyttede jobbfiler, legg korrigert prompt og kildebegrunnelse i et separat notat, og bruk rettelsen. Avklar bare nødvendig manglende betydning eller design; eksisterende godkjenninger gjelder fortsatt. Fortsett uavhengig arbeid som allerede er autorisert.

## Faste regler

- Jobb bare i denne grenen (`gpt-arbeid`). Aldri push til `main`, og lag ikke egne grener eller PR-er for grafikken.
- Endre aldri `referanse.png`, `original_1x.png`, `prompt.txt` eller `jobb.json`.
- Lever `jobber/<jobb>/resultat.png` og `jobber/<jobb>/notat.md`. Resultatet kan være hele lerretet (1536 x 1024 med grå kant) eller bare bildet i samme sideforhold som utsnittet (16:10 for et rom på 320 x 200; sideforholdet står i `jobb.json`).
- Bruk `prompt.txt` ordrett når premisset stemmer. Ved påvist feil premiss gjelder rettelsen beskrevet over. Legg ved stilankeret fra `stil/` som bilde to når det finnes, eller det bildet ordren sier.
- Innholdet er originalens: samme motiv, ting, former og plassering. Tegnestilen og figurenes utseende følger de godkjente stilankerne i `stil/` (Tom 14. oktober 2026, se `stil/README.md`), også der de avviker fra FM-Towns-fargene, som Annies blå genser. Ellers er originalen fasiten; det finnes ingen offisiell remaster.
- Jobbene heter `romNNN` (rombakgrunner), `objNNN_SS` (objektjobber: store bilder som spillet tegner over rommet, som nærbilder og kart), `lagNNN_KK` (lagjobber), `ikonNN` (ikonark) eller `figCCC_KK` (figurark). Alle lages og leveres på samme måte. I en objektjobb viser `referanse.png` objektet lagt over rommet. Mal hele bildet som en bakgrunn. Leverer du bare bildet, skal det ha objektets sideforhold (`bilde_i_lerret` i `jobb.json`).
- Objekter med flere tilstander (`objNNN_01`, `_02` og så videre; i Zak har hvert objekt ett bilde, så dette gjelder trolig ikke): lag tilstand 01 først. For de andre legger du ved `jobber/<objekt>_01/resultat.png` som bilde to i stedet for stilankeret. Claude gjør det som er likt, helt likt etterpå.
- Lagjobber (`lagNNN_KK`, for eksempel `lagNNN_01_del2av3`): rommet med små objekter (dører, brytere, lys, ting) tegnet på plass. Mal alt trofast. Objektene klippes ut etter posisjonen, så hvert objekt må ligge nøyaktig der det er, med samme størrelse, omriss og farger, og ingen må mangle. Legg ved det godkjente HD-bildet som står i ordren (`bilde_to` i `jobb.json`) som bilde to i stedet for stilankeret. Står det i ordren at jobben skal lages etter en annen, vent til den er godkjent.
- Ikonark (`ikonNN`): ikoner i et rutenett på flat bakgrunn. Mal hvert ikon trofast i ruten sin, og hold bakgrunnen flat. Stilankeret som bilde to.
- Figurark (`figCCC_KK`, kostyme CCC, ark KK): animasjonsruter av samme figur, i den rekkefølgen spillet viser dem. Mal alle rutene som den samme figuren (samme ansikt, klær, farger og lys) i glatt stil med myke kanter, med samme pose og plass som originalen, på gjennomsiktig bakgrunn med ekte alfa. Deler av en figur (for eksempel hode og kropp hver for seg) males som de er. Ark 01 med stilankeret som bilde to, de andre arkene med det godkjente ark 01 (`bilde_to` i `jobb.json`). Skriv hvert levert ark inn under `leveranser` i `rapporter/*/fremdrift.json` med sha256, og lever et rutekart. Claude tar dem inn med `zakhd myke-figurer` (se `docs/BESTILLING-CHATGPT.md` i `main`).
- Kodeoppgaver i `ORDRE.md` er for den som har laptopen med spillet. Rapporter skrives i `rapporter/` i denne grenen. Kodeendringer går som PR mot `main`.
- Skriv på norsk i notater, uten emoji og uten tankestreker.
- Repoet er offentlig, men spillet tilhører Disney/Lucasfilm. Grafikken herfra skal ikke på offentlige sider eller i offentlige pakker. Godkjent HD-grafikk flyttes til `grafikk/` i `main` av Claude.

## Slik jobber du

1. Kjør `git pull` i grenen `gpt-arbeid` før hver økt. Ta jobbene i `ORDRE.md`, i den rekkefølgen de står. Når de er levert, fortsett med neste bestilling i `GRAFIKKLISTE.md` uten å vente på ny ordre. Hopp over jobber som er krysset av.
2. Lag bildet med bildeverktøyet: `referanse.png` er bildet som redigeres, `prompt.txt` er prompten, størrelse 1536 x 1024.
3. Sammenlign med `referanse.png` før du lagrer. Ligger noe feil, prøv igjen.
4. Lagre `resultat.png`. Skriv `notat.md` med verktøy og modell (hvis det vises), dato, antall forsøk og hva som var usikkert.
5. Har jobben en `retur.md`, bruk forslaget der og lever på nytt.
6. Commit 5 til 10 jobber om gangen med jobbene i meldingen, for eksempel `GPT: romNNN, objNNN_SS`, og push.

Claude kjører kontrollen (`zakhd gpt-inn`) og skriver `RAPPORT.md`, `status.csv` og `retur.md` tilbake hit.
