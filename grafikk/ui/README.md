# Grensesnittet

Grafikk til grensesnittet i Zak McKracken HD, laget for prosjektet. Ingenting her er laget fra spillets grafikk, så det kan ligge i `main` og bygges inn i motoren og nettsiden.

| Mappe | Hva |
| --- | --- |
| [verbhjul/](verbhjul/) | De 15 ikonene til verbhjulet, som SVG (kilden) og PNG (160 x 160, RGBA) |
| [skrift/](skrift/) | Comic Neue Bold, skriften i teksten under hjulet. SIL Open Font License 1.1 ([OFL.txt](skrift/OFL.txt)), fra github.com/google/fonts (`ofl/comicneue`) |

## Verbhjulet

Ikonene er tegnet av Claude 15. oktober 2026 med `tools/verbhjul_ikoner.py`, etter stilankerne i [grafikk/stil/](../stil/README.md): mørk kontur, flate farger og ett skyggetrinn, i en kremfarget mynt. De er egne tegninger i samme ånd som ikonhjulene i Day of the Tentacle Remastered og markørene i Sam & Max, ikke kopier av dem.

| Verb | Fil | Motiv |
| --- | --- | --- |
| 1 Push | push | Hånd som dytter en kasse |
| 2 Open | open | Dør på gløtt med lys |
| 4 Put on | put-on | Hatt med pil ned |
| 5 Turn on | turn-on | Lyspære som lyser |
| 6 Pull | pull | Neve som drar i et håndtak |
| 7 Close | close | Lukket dør |
| 8 Pick up | pick-up | Hånd som griper en ball, pil opp |
| 9 Take off | take-off | Hatt med pil opp |
| 10 Turn off | turn-off | Lyspære som er av |
| 11 Give | give | Hånd som holder fram en gave |
| 12 Read | read | Øye |
| 14 Use | use | Tannhjul |
| 15 Buy | buy | Mynt med pil inn |
| 16 Sell | sell | Mynt med pil ut |
| 17 Teleport to | teleport | Glimt |

Zak har ikke Look at eller Talk to, så det er ingen munn eller snakkeboble.

Slik endres de: rediger tegningene i `tools/verbhjul_ikoner.py` (funksjonene `ikon_*`), og kjør

```sh
python3 tools/verbhjul_ikoner.py --ark work/ikonark.png --cpp engine/scummvm/engines/scumm/verbhjul_ikoner.h
tools/lag_patcher.sh
```

Skriptet skriver SVG og PNG hit og lager `verbhjul_ikoner.h`, der PNG-ene og skriften ligger som base64. Motoren trenger ingen filer ved siden av seg. Krever `rsvg-convert` (librsvg2-bin) og Pillow.

Malte ikoner fra ChatGPT trenger ingen ny bygging av motoren: legg de godkjente i `grafikk/ui/verbhjul-gpt/` med de samme filnavnene (PNG med alfa, gjerne 512 x 512). `zakhd build-mod` legger dem i modden (`ui/verbhjul/`), og motoren bruker dem i stedet for de innebygde. Bildene til inventaret går på samme måte i `grafikk/inventar/` (se [../inventar/README.md](../inventar/README.md)).
