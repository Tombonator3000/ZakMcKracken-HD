# AGENTS.md

Instrukser for alle KI-agenter som jobber i dette repoet (Claude, Codex, ChatGPT).

## Før du starter

1. Les `memory.md` (faste fakta og beslutninger).
2. Les `todo.md`, særlig `## Neste`.
3. Les de siste oppføringene i `log.md`.
4. Les `STATUS.md` hvis du skal endre noe som er testet eller rapportert der.
5. Les `docs/ANALYSE.md`, `docs/HD-MOTOR.md` og `docs/HD-REMASTER-METODE.md` ved arbeid med motor, pipeline eller grafikk, og `docs/GRENSESNITT.md` ved arbeid med verb, inventar eller skjermoppsett. Referansene er The Dig HD Remake (github.com/Tombonator3000/Dig-HD-Remake) og Sam & Max HD (github.com/Tombonator3000/Sam-Max-HD), som dette repoet er kopiert fra og tilpasset.

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

- Spillfiler (`*.LFL`, `Track*.fla`) og alt som lages fra dem (`work/`, `mods/`, HD-bilder, dekompilerte skript) skal aldri inn i `main` eller kodegrener. De ligger i egne grener (se under).
- Repoet er offentlig, som The Dig og Sam & Max. *Zak McKracken and the Alien Mindbenders* tilhører Disney/Lucasfilm. Ingenting fra spillet deles utenfor repoet.
- Kjør testene før du committer endringer i pipelinen eller motoren.
- Kodeendringer går via PR mot `main` og flettes når CI er grønn. Logg, status, todo og minne kan committes rett i `main`.
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
```

## Arbeid med motoren

- Patchen ligger i `engine/patches/` og er den samme som i Sam & Max. Gjør endringer i `engine/scummvm`, og lag patchen på nytt med
  `git -C engine/scummvm add -N engines/scumm/dighd.cpp engines/scumm/dighd.h && git -C engine/scummvm diff > engine/patches/0001-dighd-hd-grafikk.patch`.
- ScummVM-versjonen er låst i `engine/SCUMMVM_COMMIT`. Bytt den bare sammen med en test av patchen.
- Hva som må portes for Zak: `docs/HD-MOTOR.md`.

## Grener

| Gren | Innhold |
| --- | --- |
| `main` | Kode og dokumentasjon |
| `spilldata` | Spillfilene med sjekksummer, uten felles historikk med `main` |
| `gpt-arbeid` | Arbeidsbordet med ChatGPT/Codex. Startgren uten jobber; ingen jobber før stilpiloten er godkjent |
| `hd-mod` | Siste ferdige HD-mod, én commit som erstattes. Startgren uten mod |
