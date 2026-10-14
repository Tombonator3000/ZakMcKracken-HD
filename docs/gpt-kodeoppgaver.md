Ingen kodeoppgaver nå. HD-motoren er ikke slått på for Zak, og det finnes ingen HD-mod, så det er ingenting å teste i HD ennå. `./spill.sh` starter spillet med originalgrafikken. Oppgavene under er for senere, når porten av HD-motoren til Zak er gjort og Claude har skrevet i `ORDRE.md` at de gjelder. De er for Codex eller ChatGPT med tilgang til laptopen og repoet. Ta én om gangen, og skriv i `rapporter/` i denne grenen hva du gjorde og fant.

1. **Test HD-modden på laptopen med skjerm og tastatur.** `git checkout main && git pull && ./spill.sh` henter, bygger og starter alt. Rommene som skal sjekkes, står i `ORDRE.md`. Følg `docs/SPILLTEST.md`. Sjekk:
   - at figurene går bak ting i forgrunnen der de skal,
   - at objekter som tas eller flyttes, forsvinner og dukker opp riktig (Zak har ett bilde per objekt),
   - at Ctrl+H bytter mellom HD og klassisk, og at Ctrl+Shift+H viser gult felt der HD mangler,
   - at HD-valget kan slås av og på i spillet, og at valget huskes (hvor det ligger i Zak, er ikke bestemt),
   - at teksten (verblinje, replikker og inventar) står der den skal og er lesbar,
   - at mellomsekvenser vises riktig (Zak har ingen filmer, de tegnes av motoren),
   - at ingenting krasjer når du går mellom rom med og uten HD.
   Ta skjermbilder i `rapporter/laptop-test/` og skriv `rapporter/laptop-test.md`: hva du testet, hva som var feil, med rom og omtrentlig sted. Ikke rett i motoren selv. Beskriv feilen, så retter Claude den.
2. **Mål fart og lyd.** Kjør ett rom i ett minutt med og uten modden. Noter bilder per sekund hvis ScummVM viser det, og om CD-musikken (`Track1.fla` til `Track21.fla`) spilles og om den hakker. Spillet har ingen tale. Uten FLAC i motoren blir det ingen musikk, så sjekk `scummvm --version` først. Skriv det i `rapporter/laptop-test.md`.

Kodeendringer går rett i `main` (Tom 14. oktober 2026), etter testene i `AGENTS.md` i `main`. Skjermbilder og andre filer fra spillet skal bare ligge i denne grenen.
