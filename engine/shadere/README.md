# Shadere for Zak McKracken HD

Libretro-oppsett (`.glslp`) som ScummVM sin OpenGL-tegning kjører på det ferdige bildet. Skrevet for dette repoet 14. oktober 2026. Bakgrunn og begrensninger: [docs/MOTOR-FORBEDRING.md](../../docs/MOTOR-FORBEDRING.md), del 5.

| Oppsett | Til | Parametere |
| --- | --- | --- |
| `klassisk-crt.glslp` | Originalgrafikken: skannlinjer, stråle, skyggemaske og litt krumning | `KILDEPIKSEL` (1 uten HD-laget, 4 med HD-laget i klassisk modus), `SKANNLINJE`, `MASKE`, `SKARPHET`, `KURVE`, `LYS` |
| `hd-glod.glslp` | HD-bildet: glød rundt lyse partier, vignett, metning og kontrast | `GLOD_TERSKEL`, `GLOD_BREDDE`, `GLOD_STYRKE`, `VIGNETT`, `METNING`, `KONTRAST` |

Prøv:

```sh
engine/run.sh ingen --shader=engine/shadere/klassisk-crt.glslp
engine/run.sh ingen --shader=engine/shadere/hd-glod.glslp
engine/run.sh ingen --shader=crt/crt-lottes-fast.glslp   # en av de 451 i ScummVMs shaders.dat
```

Krever OpenGL (`--gfx-mode=opengl`, som `engine/run.sh` bruker). Parameterne kan endres i ScummVMs grafikkvalg mens spillet går.

Testet 14. oktober 2026 under Xvfb med Mesa llvmpipe (programvare-OpenGL 4.5): begge lastet og ga riktig bilde i rom 1. Ikke testet på ekte skjermkort, i nettleseren eller på mobil.
