# ZakMcKracken-HD

HD-utgave av *Zak McKracken and the Alien Mindbenders* (FM-Towns), bygget som The Dig HD Remake og Sam & Max HD: spillet kjører uendret i ScummVM, og en patch legger HD-grafikk over originalen.

Status 11. oktober 2026: repoet er satt opp, spillfilene ligger i grenen `spilldata`, all originalgrafikk er trukket ut, alle skript er dekompilert, og listen over grafikken som skal byttes ut finnes ([docs/grafikkliste.csv](docs/grafikkliste.csv)). HD-motoren er ikke portet til Zak ennå, så spillet vises med originalgrafikken. Se [STATUS.md](STATUS.md).

## Kom i gang

```sh
tools/hent_spilldata.sh                      # spillfilene til game/
python3 -m venv .venv && . .venv/bin/activate
pip install -e "pipeline[dev]"
zakhd info && zakhd extract && zakhd grafikkliste
engine/build.sh                              # ScummVM med patchen (libsdl2-dev, libpng-dev, libflac-dev)
./spill.sh                                   # starter spillet
```

## Dokumenter

- [docs/ANALYSE.md](docs/ANALYSE.md): spillfilene, formatet, tellinger og grafikken som skal byttes ut
- [docs/HD-MOTOR.md](docs/HD-MOTOR.md): hva som må til for HD-motoren i Zak
- [docs/VERBHJUL.md](docs/VERBHJUL.md): det dynamiske verbhjulet (høyst fire valg) og portrettene for figurbytte (bygget, med midlertidige ikoner)
- [docs/GRENSESNITT.md](docs/GRENSESNITT.md): verbhjul, ikoninventar og større bilde
- [docs/HD-REMASTER-METODE.md](docs/HD-REMASTER-METODE.md): arbeidsmetoden og godkjenningene
- [grafikk/stil/README.md](grafikk/stil/README.md): de godkjente stilankerne (figurene og rom 42)
- [AGENTS.md](AGENTS.md): regler for agentene som jobber i repoet

Spilleren velger selv HD eller originalgrafikk, også mens spillet går.

Spillet tilhører Disney/Lucasfilm. Spillfilene ligger i grenen `spilldata`, aldri i `main`. Godkjent HD-grafikk ligger i `main` under `grafikk/`.
