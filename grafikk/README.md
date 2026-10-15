# grafikk

HD-grafikk til Zak McKracken HD Remake. Tom bestemte 14. oktober 2026 at HD-grafikk kan ligge i `main`.

| Mappe | Innhold |
| --- | --- |
| [Zak spritesheet](sprites/zak/README.md) | Første pilot: 24 sammensatte ruter, tre komponentark og 51 deler |
| [stil/](stil/README.md) | Godkjente stilankere: figurarkene for Zak, Annie og Caponian, rom 42 og forsiden av The National Inquisitor |
| [ui/verbhjul-gpt/](ui/verbhjul-gpt/README.md) | 15 malte verbikoner, 512 x 512 med alfa |
| [inventar/](inventar/README.md) | 126 PNG, 81 logiske bilder for 105 objektnumre |
| [karakterkonsepter](konsept/2026-10-15-resten-av-figurene/README.md) | 22 nye ark for Melissa, Leslie, biroller, romvesener og dyr |
| [UI-galleri](rapporter/hjul-inventar-20261015/forhandsvisning.html) | Forhåndsvisning, prompter, manifest og kontroll av hjul og inventar |

Tom ba 15. oktober 2026 om at hele grafikkleveransen legges inn i repoet via PR. Hjul- og inventarbildene ligger i mappene pipelinen allerede leser. Karakterarkene er konsepter til vurdering, og er ikke animasjonsruter. Godkjent HD-grafikk fra nye grafikkjobber legges i egne mapper her. Jobbene og leveransene som ikke er godkjent ennå, ligger i grenen `gpt-arbeid`. Den ferdigbygde moden lages av pipelinen og ligger i grenen `hd-mod`.

Regler:

- Spillfilene (`*.LFL`, `Track*.fla`) og det som lages automatisk fra dem (uttrukket originalgrafikk, dekompilerte skript, `work/`, `mods/`) hører ikke hjemme her.
- Ingen fil over 90 MB.
- Spillet tilhører Disney/Lucasfilm. Grafikken skal ikke på offentlige sider eller i offentlige pakker.
- HD er alltid et valg for spilleren. Spillet skal kunne vises med originalgrafikken, og spilleren bytter selv mens spillet går (se AGENTS.md).
