# Patcher bare for nettleseren

`engine/build-web.sh` legger disse på etter motorpatchene i `engine/patches` (0001 DigHD og 0002 verbhjulet). De endrer bare ScummVMs nettleserdel (Emscripten), ikke SCUMM-motoren, og brukes ikke av `engine/build.sh` eller `tools/lag_patcher.sh`.

| Patch | Hva | Kilde |
| --- | --- | --- |
| `0001-browser-filesystem-cache.patch` | HTTP-filsystemet (`backends/fs/emscripten/http-fs.*`): én felles oversikt over filene per kjøring i stedet for å bygge søskenlisten på nytt ved hvert oppslag, og ingen lekkasjer av JSON, mapper og nedlastinger | Dig-HD-Web `engine/patches/0002-browser-filesystem-cache.patch`, a8e4474 (12. oktober 2026) |
| `0002-browser-canvas-coordinate-sync.patch` | Lerretet i fullskjerm: OpenGL-visningen og musekoordinatene følger lerretets faktiske størrelse, så klikk treffer der pekeren er | Dig-HD-Web `engine/patches/0005-browser-canvas-coordinate-sync.patch`, a8e4474 |

Begge er GPL-3.0-or-later som ScummVM. `python3 tools/sjekk_patcher.py` sjekker hunk-hodene her også, og `engine/build-pages.py` sjekker at hele stakken er lagt på før nettsiden pakkes. `engine/tests/test-http-fs-cache.sh` tester HTTP-filsystemet i Wasm etter byggingen (fra Dig-HD-Web).

Lagt på ScummVM `c9091321` sammen med 0001 og 0002 med `git apply` 14. oktober 2026. Ikke prøvd i nettleser med Zak før bygget i Actions.
