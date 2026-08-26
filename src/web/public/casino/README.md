# Odessa Prime visual assets (Sprint 21)

```
/public/assets/casino/entrance/   facade.jpg + facade.svg (cinematic night exterior)
/public/casino/                   room SVGs (not used as the /casino SPA prefix)
```

Entrance uses a compressed photographic still plus CSS architectural layers.
Static facade files live under `/assets/casino/` so production SPA catch-all for `/casino/*` does not swallow them.
Do not add multi-megabyte video or Three.js for the facade.
