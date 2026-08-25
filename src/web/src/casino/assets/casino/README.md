# Odessa Prime asset layout (Sprint 18–19)

Conceptual folders. Large binaries are not duplicated; scenes use CSS + shared sprites.

```
casino/
  entrance/     entrance cinematic layers (CSS in odessa.css)
  lobby/        hall hotspots + pan stage
  roulette/     wheel / felt
  blackjack/    cards / salon
  slots/        Odessa Gold cabinet
  poker/        atmosphere felt (no engine yet)
  vip/          private salon atmosphere
  restaurant/   dining atmosphere
  bar/          bar atmosphere
  ambient/      light sweep, bokeh, silhouettes (`src/web/src/casino/ambient/`)
  shared/       live.css, world.css, shell chrome
```

Lobby-critical CSS loads with the shell. Secondary rooms are React.lazy in `CasinoApp`.
