# AGENTS.md

Instrukser for alle KI-agenter som jobber i dette repoet (Claude, Codex, ChatGPT).

## Før du starter

1. Les `memory.md` (faste fakta og beslutninger).
2. Les `todo.md`, særlig `## Neste`.
3. Les de siste oppføringene i `log.md`.
4. Les `STATUS.md` hvis du skal endre noe som er testet eller rapportert der.
5. Les `docs/ANALYSE.md`, `docs/HD-MOTOR.md` og `docs/HD-REMASTER-METODE.md` ved arbeid med motor, pipeline eller grafikk, og `docs/VERBHJUL.md` og `docs/GRENSESNITT.md` ved arbeid med verb, inventar eller skjermoppsett. Referansene er The Dig HD Remake (github.com/Tombonator3000/Dig-HD-Remake) og Sam & Max HD (github.com/Tombonator3000/Sam-Max-HD), som dette repoet er kopiert fra og tilpasset.
6. Før grafisk HD-arbeid: les [remake-skillen](docs/skills/scumm-hd-remake/SKILL.md), særlig «Før HD-produksjon: avklar motiv og design», og [de godkjente stilankerne](grafikk/stil/README.md) (Tom 14. oktober 2026). Innholdet er originalens (motiv, funksjon, plassering, positur); tegnestilen og figurenes utseende følger ankrene. Teknisk mottak alene er ikke visuell godkjenning.

## Mens du jobber

- Logg alt du gjør nederst i `log.md` med dato og klokkeslett i norsk tid, og hvem du er: `## 2026-10-11 18:05 (Claude)`, så punkter.
- Kryss av og legg til punkter i `todo.md` underveis.
- Oppdater `memory.md` når en beslutning eller et fast faktum endrer seg.
- Oppdater `STATUS.md` når noe nytt virker, er testet eller har fått en kjent begrensning.

## Stil

- Dokumentasjon og logg på norsk. Kode og kommentarer kan være på norsk eller engelsk, som filen rundt.
- Ingen emoji og ingen tankestreker. Skriv vanlig og direkte, uten fyllord og salgsspråk.
- Si hva som er testet og hvordan. Det som ikke er testet, står som ikke testet.

## Regler

- HD-grafikk kan ligge i `main` (Tom 14. oktober 2026). Godkjente stilankere, referansebilder og godkjent HD-grafikk legges under [`grafikk/`](grafikk/README.md). Ingen fil over 90 MB. Jobber og leveranser som ikke er godkjent, ligger i `gpt-arbeid`.
- Spillfilene (`*.LFL`, `Track*.fla`) ligger bare i grenen `spilldata`. Det som lages automatisk fra dem (`work/`, `mods/`, uttrukket originalgrafikk, dekompilerte skript) sjekkes ikke inn i `main` eller kodegrenene; det lages på nytt med verktøyene. Den ferdigbygde moden ligger i `hd-mod`.
- HD er alltid et valg for spilleren. Spilleren velger selv HD eller originalgrafikk, også mens spillet går: med Ctrl+H (finnes i patch 0001) og med en rad i spillets meny, så det virker på mobil uten tastatur. Valget lagres til neste start (`dighd_classic`). Originalgrafikken skal alltid virke, og HD legges oppå originalen uten at spillfilene endres.
- Repoet er offentlig, som The Dig og Sam & Max. *Zak McKracken and the Alien Mindbenders* tilhører Disney/Lucasfilm. Tom har bestemt at HD-grafikk kan ligge i `main` (14. oktober 2026), og at grafikk og annet fra spillet kan deles utenfor repoet til hans eget, private bruk: som filer til egne maskiner og telefoner, eller på private steder bare han har tilgang til (13. oktober 2026). Offentlige sider og pakker (GitHub Pages, releaser) har fortsatt ingen spillgrafikk.
- Kjør testene før du committer endringer i pipelinen eller motoren.
- Kodeendringer går via PR mot `main` og flettes når CI er grønn. Logg, status, todo og minne kan committes rett i `main`.
- Godkjent grafikk som flyttes fra `gpt-arbeid` til `grafikk/` i `main`, får README og sjekksummer (SHA-256) og går via PR.
- Ikke lapp spillets skript uten Toms ja. Nye grensesnitt (docs/GRENSESNITT.md) sender de samme verb- og klikkallene som originalen.

## Roller

- Claude: all kode (pipeline, motor, test, verktøy for grafikkjobbene) og kontrollen av grafikken.
- ChatGPT/Codex: HD-grafikken, etter `docs/BESTILLING-CHATGPT.md` når den er aktiv. Jobber bare i grenen `gpt-arbeid`.
- Tom: godkjenner stil og resultater.

## Oppsett

```sh
tools/hent_spilldata.sh          # spillfilene til game/ og sjekk av sjekksummene
python3 -m venv .venv && . .venv/bin/activate
pip install -e "pipeline[dev]"   # zakhd
zakhd info                       # sjekker spillfilene og viser nøkkeltall
zakhd extract                    # all originalgrafikk til work/extract (rom, objekter, kostymeruter, tegnsett)
zakhd grafikkliste               # docs/grafikkliste.csv og docs/rom-oversikt.csv fra uttrekket
tools/bygg_descumm.sh && python3 tools/dekompiler_skript.py   # alle skript som tekst i work/skript
python3 tools/skriptoversikt.py  # ROM.md, REPLIKKER.md, rom-koblinger.tsv og kostymer-i-rom.tsv i work/skript
engine/build.sh                  # ScummVM med patchen til engine/scummvm (krever libflac-dev for musikken)
./spill.sh                       # henter det som mangler, bygger og starter spillet
```

`zakhd extract` bruker egne dekodere for SCUMM v3 med 256 farger (`pipeline/zakhd/lfl.py` og `v3grafikk.py`, oversatt fra ScummVM). Rutenummeret i kostymene er lag * 128 + kode. Objektene har ett bilde hver (`objNNN_01`). HD-motoren (DigHD) er ikke slått på for Zak ennå: FM-Towns tegner gjennom `towns_drawStripToScreen`, forbi krokene. Se `docs/HD-MOTOR.md`.

## Kommandoer

```sh
cd pipeline && pytest            # etter endringer i pipelinen (game-testene hoppes over uten game/)
pytest -m "not game"             # det CI kjører
node --test engine/pages/tests/*.test.mjs   # nettsidekoden
engine/run.sh ingen              # spillet uten mod
python3 tools/indeks_info.py game/00.LFL
tools/verbhjul_test.sh           # verbhjulet mot originalpanelet uten skjerm
python3 tools/verbhjul_dynamisk.py  # ikonene i det dynamiske hjulet, per objekt (--cpp for motoren)
```

## Arbeid med motoren

- Patchene ligger i `engine/patches/` og legges på i rekkefølge: `0001-dighd-hd-grafikk.patch` (HD-motoren, den samme som i Sam & Max) og `0002-verbhjul.patch` (verbhjulet for Zak, `engines/scumm/verbhjul.*`, `verbhjul_zak.h` og krokene). Gjør endringer i `engine/scummvm`, og lag begge på nytt med `tools/lag_patcher.sh`. Ikke lag 0001 med `git diff` av hele kopien; da kommer hjulet med i den.
- Etter endringer i verbhjulet: `tools/verbhjul_test.sh` (originalpanelet og hjulet skal gi de samme setningene, omtrent fire minutter).
- Reglene for det dynamiske hjulet (`engines/scumm/verbhjul_zak.h`) lages av `python3 tools/verbhjul_dynamisk.py --cpp engine/scummvm/engines/scumm/verbhjul_zak.h` fra work/skript; regler for hånd står i `HAAND` i verktøyet, med kilden i skriptene. Lag så patchene på nytt og kjør testen.
- ScummVM-versjonen er låst i `engine/SCUMMVM_COMMIT`. Bytt den bare sammen med en test av patchen.
- Hva som må portes for Zak: `docs/HD-MOTOR.md`.

## Grener

| Gren | Innhold |
| --- | --- |
| `main` | Kode, dokumentasjon og godkjent HD-grafikk (`grafikk/`) |
| `spilldata` | Spillfilene med sjekksummer, uten felles historikk med `main` |
| `gpt-arbeid` | Arbeidsbordet med ChatGPT/Codex: jobber, leveranser, konsepter og stilankerne i `stil/` (de samme som `grafikk/stil/` i `main`). Ingen jobber ennå |
| `hd-mod` | Siste ferdige HD-mod, én commit som erstattes. Startgren uten mod |
