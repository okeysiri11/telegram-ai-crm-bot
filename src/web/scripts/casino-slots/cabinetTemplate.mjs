// Odessa Prime Slots — Phase 4.3 asset-bake templates.
// Renders a physical cabinet / hall background to flat HTML+CSS so Playwright
// (see generate-cabinet-assets.mjs) can screenshot it once into a static
// transparent PNG. Runtime never re-renders this markup — it only displays
// the baked <img>. Keep this file as the source of truth for regenerating
// or replacing assets later.

const VARIANT_GEOMETRY = {
  curved: { w: 640, h: 1180, topRadius: 120, bodyRadius: 46, screenRadius: 46 },
  square: { w: 600, h: 1180, topRadius: 18, bodyRadius: 14, screenRadius: 8 },
  slim: { w: 460, h: 1180, topRadius: 60, bodyRadius: 28, screenRadius: 24 },
};

export function variantGeometry(variant) {
  return VARIANT_GEOMETRY[variant] ?? VARIANT_GEOMETRY.square;
}

function symbolGlyphs(symbols) {
  return symbols.slice(0, 6).map((s) => s.label);
}

export function cabinetHtml({ variant, accent, accent2, title, jackpot, symbols }) {
  const g = variantGeometry(variant);
  const glyphs = symbolGlyphs(symbols);
  const reelRow = glyphs.map((s) => `<span>${s}</span>`).join("");
  return `<!doctype html>
<html><head><meta charset="utf-8" />
<style>
  html,body{margin:0;padding:0;background:transparent;}
  * { box-sizing: border-box; }
  body{width:${g.w}px;height:${g.h}px;position:relative;font-family:'Georgia',serif;overflow:hidden;}

  .cab{
    position:absolute; inset:0;
    --accent:${accent}; --accent2:${accent2};
    filter: drop-shadow(0 34px 46px rgba(0,0,0,.55));
  }

  .cab-shadow{
    position:absolute; left:2%; right:2%; bottom:0; height:90px;
    background: radial-gradient(ellipse at center, color-mix(in srgb, var(--accent) 60%, black) 0%, transparent 72%);
    filter: blur(8px);
    opacity:.5;
  }

  /* outer gold trim reads as a lacquered/gilded rim around the whole cabinet */
  .cab-trim{
    position:absolute; left:5.4%; right:5.4%; top:1.4%; bottom:9.6%;
    border-radius: ${g.topRadius + 6}px ${g.topRadius + 6}px ${g.bodyRadius + 4}px ${g.bodyRadius + 4}px;
    background: linear-gradient(155deg, #e9d8a6 0%, #a3792f 22%, #7a5a22 46%, #caa54a 62%, #6d4f1e 100%);
    box-shadow: 0 18px 34px rgba(0,0,0,.5);
  }

  .cab-body{
    position:absolute; left:6%; right:6%; top:2%; bottom:9%;
    border-radius: ${g.topRadius}px ${g.topRadius}px ${g.bodyRadius}px ${g.bodyRadius}px;
    background:
      repeating-linear-gradient(100deg, rgba(255,255,255,.05) 0 1px, rgba(255,255,255,0) 1px 5px),
      linear-gradient(100deg, rgba(255,255,255,.14) 0%, rgba(255,255,255,0) 12%, rgba(255,255,255,0) 88%, rgba(255,255,255,.05) 100%),
      linear-gradient(165deg, #34343e 0%, #1c1c22 30%, #101013 58%, #08080a 82%, #040405 100%);
    box-shadow:
      inset 0 2px 0 rgba(255,255,255,.16),
      inset 0 -70px 100px rgba(0,0,0,.7),
      inset 26px 0 44px rgba(0,0,0,.5),
      inset -26px 0 44px rgba(0,0,0,.6);
  }

  .cab-edge{
    position:absolute; top:2.6%; bottom:9.6%; width:2.2%;
    background: linear-gradient(var(--accent2), var(--accent));
    box-shadow: 0 0 26px 5px color-mix(in srgb, var(--accent) 75%, transparent);
    border-radius:6px;
    opacity:.95;
  }
  .cab-edge.l{ left:6.6%; }
  .cab-edge.r{ right:6.6%; }

  .cab-crown{
    position:absolute; left:9%; right:9%; top:4%; height:19%;
    border-radius: ${g.topRadius * 0.72}px ${g.topRadius * 0.72}px 8px 8px;
    background:
      radial-gradient(120% 90% at 50% 0%, color-mix(in srgb, var(--accent2) 22%, transparent) 0%, transparent 60%),
      linear-gradient(180deg, #26262d 0%, #131316 55%, #0a0a0c 100%);
    box-shadow: inset 0 0 0 2px color-mix(in srgb, var(--accent2) 60%, transparent),
                inset 0 12px 22px rgba(255,255,255,.07),
                0 0 34px color-mix(in srgb, var(--accent2) 40%, transparent);
    display:flex; flex-direction:column; align-items:center; justify-content:center;
    color: var(--accent2); padding: 6% 8% 4%;
  }
  .cab-crown small{
    font-family: Georgia, serif; font-size:11px; letter-spacing:.34em; opacity:.8; color:#e9ddc4;
  }
  .cab-crown .jp-plate{
    margin-top:6%;
    padding: 3% 8%;
    border-radius:6px;
    background: #050506;
    box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--accent2) 55%, transparent), inset 0 2px 8px rgba(0,0,0,.8);
  }
  .cab-crown .jp{
    font-family: 'Courier New', monospace; font-size:25px; font-weight:700;
    color: var(--accent2);
    text-shadow: 0 0 10px color-mix(in srgb, var(--accent2) 95%, transparent), 0 0 22px color-mix(in srgb, var(--accent2) 65%, transparent);
    letter-spacing:.03em; white-space:nowrap;
  }
  .cab-crown b{
    display:block; margin-top:7%;
    font-family: Georgia, 'Times New Roman', serif;
    font-size: 19px; letter-spacing:.1em; font-weight:700;
    text-shadow: 0 0 10px color-mix(in srgb, var(--accent2) 85%, transparent);
    color: #fff8e6; text-align:center;
  }

  .cab-screen-bezel{
    position:absolute; left:10%; right:10%; top:26%; height:38%;
    border-radius: ${g.screenRadius}px;
    background: linear-gradient(165deg, #2a2a30, #08080a);
    box-shadow:
      inset 0 0 0 11px #0d0d0f,
      inset 0 0 46px rgba(0,0,0,.95),
      inset 0 0 0 13px color-mix(in srgb, var(--accent) 35%, transparent),
      0 0 30px color-mix(in srgb, var(--accent) 22%, transparent);
  }
  .cab-screen{
    position:absolute; inset: 15px;
    border-radius: ${Math.max(g.screenRadius - 15, 4)}px;
    overflow:hidden;
    background: radial-gradient(120% 90% at 50% 6%, color-mix(in srgb, var(--accent) 32%, #050505) 0%, #050505 60%);
  }
  .cab-reels{
    position:absolute; inset:0; display:flex;
  }
  .cab-reels span{
    flex:1; display:flex; align-items:center; justify-content:center;
    font-size:38px; border-right:1px solid rgba(255,255,255,.06);
    filter: drop-shadow(0 0 6px rgba(0,0,0,.6));
  }
  .cab-reels span:last-child{ border-right:none; }
  .cab-glass-sheen{
    position:absolute; inset:0;
    background: linear-gradient(115deg, rgba(255,255,255,.20) 0%, rgba(255,255,255,0) 16%, rgba(255,255,255,0) 84%, rgba(255,255,255,.06) 100%);
  }

  .cab-belly{
    position:absolute; left:14%; right:14%; top:65.5%; height:6.5%;
    border-radius:6px;
    background: linear-gradient(155deg, #d8c58c 0%, #8a6a2c 45%, #caa54a 60%, #6d4f1e 100%);
    box-shadow: inset 0 1px 0 rgba(255,255,255,.4), 0 3px 8px rgba(0,0,0,.5);
    display:flex; align-items:center; justify-content:center;
  }
  .cab-belly span{
    font-family: Georgia, serif; font-size:14px; letter-spacing:.18em; font-weight:700;
    color:#2a1d08; text-transform:uppercase;
  }

  .cab-deck{
    position:absolute; left:8%; right:8%; top:74%; height:13%;
    clip-path: polygon(4% 0, 96% 0, 100% 100%, 0% 100%);
    background: linear-gradient(180deg, #26262c 0%, #141417 55%, #08080a 100%);
    box-shadow: inset 0 2px 0 rgba(255,255,255,.09), inset 0 -12px 22px rgba(0,0,0,.65);
    display:flex; align-items:center; justify-content:center; gap:5.5%;
  }
  .cab-btn{
    border-radius:999px;
    background: radial-gradient(circle at 32% 26%, rgba(255,255,255,.4), rgba(255,255,255,0) 42%),
                linear-gradient(160deg, #46464e, #121215);
    box-shadow: inset 0 0 0 1px rgba(255,255,255,.14), 0 3px 7px rgba(0,0,0,.55);
  }
  .cab-btn.sm{ width:11%; height:32px; }
  .cab-btn.spin{
    width:20%; height:56px;
    background: radial-gradient(circle at 32% 26%, rgba(255,255,255,.6), rgba(255,255,255,0) 48%),
                linear-gradient(160deg, color-mix(in srgb, var(--accent) 88%, white 12%), color-mix(in srgb, var(--accent) 55%, black 35%));
    box-shadow: inset 0 0 0 1px rgba(255,255,255,.3), 0 0 26px color-mix(in srgb, var(--accent) 75%, transparent), 0 4px 9px rgba(0,0,0,.55);
  }

  .cab-base{
    position:absolute; left:1%; right:1%; bottom:0; height:12%;
    clip-path: polygon(6% 0, 94% 0, 100% 100%, 0% 100%);
    background: linear-gradient(180deg, #1c1c20 0%, #0a0a0c 100%);
    box-shadow: inset 0 2px 0 rgba(255,255,255,.07);
  }
  .cab-base .tray{
    position:absolute; left:28%; right:28%; top:30%; height:28%;
    border-radius:4px;
    background:#020203;
    box-shadow: inset 0 3px 7px rgba(0,0,0,.95), inset 0 0 0 1px rgba(255,255,255,.06);
  }
  .cab-base .glow{
    position:absolute; left:4%; right:4%; bottom:-3px; height:7px;
    background: var(--accent);
    box-shadow: 0 0 26px 10px color-mix(in srgb, var(--accent) 80%, transparent);
    border-radius:3px;
  }

  .cab-vents{
    position:absolute; left:14%; right:14%; top:23.5%; height:2px;
    background: repeating-linear-gradient(90deg, rgba(0,0,0,.55) 0 2px, transparent 2px 10px);
  }
</style>
</head>
<body>
  <div class="cab" data-variant="${variant}">
    <div class="cab-shadow"></div>
    <div class="cab-trim"></div>
    <div class="cab-body"></div>
    <div class="cab-edge l"></div>
    <div class="cab-edge r"></div>
    <div class="cab-crown">
      <small>JACKPOT</small>
      <div class="jp-plate"><span class="jp">$${jackpot}</span></div>
      <b>${title}</b>
    </div>
    <div class="cab-vents"></div>
    <div class="cab-screen-bezel" data-bake-screen>
      <div class="cab-screen">
        <div class="cab-reels">${reelRow}</div>
        <div class="cab-glass-sheen"></div>
      </div>
    </div>
    <div class="cab-belly"><span>${title}</span></div>
    <div class="cab-deck">
      <div class="cab-btn sm"></div>
      <div class="cab-btn sm"></div>
      <div class="cab-btn spin"></div>
      <div class="cab-btn sm"></div>
      <div class="cab-btn sm"></div>
    </div>
    <div class="cab-base">
      <div class="tray"></div>
      <div class="glow"></div>
    </div>
  </div>
</body></html>`;
}

export function hallBackgroundHtml({ w = 2560, h = 1440 } = {}) {
  return `<!doctype html>
<html><head><meta charset="utf-8" />
<style>
  html,body{margin:0;padding:0;width:${w}px;height:${h}px;overflow:hidden;background:#050405;}
  *{box-sizing:border-box;}
  .room{position:absolute;inset:0;}

  .back-wall{
    position:absolute; inset:0 0 42% 0;
    background:
      radial-gradient(60% 55% at 50% 0%, rgba(120,90,40,.35) 0%, rgba(0,0,0,0) 60%),
      linear-gradient(180deg, #241a10 0%, #150f0a 45%, #0a0708 100%);
  }
  .ceiling-glow{
    position:absolute; left:0; right:0; top:0; height:30%;
    background: radial-gradient(48% 100% at 50% 0%, rgba(255,214,140,.5) 0%, rgba(255,214,140,0) 70%);
    filter: blur(2px);
  }
  .chandelier{
    position:absolute; left:50%; top:2%; width:22%; height:16%;
    transform: translateX(-50%);
    background: radial-gradient(60% 60% at 50% 20%, rgba(255,238,190,.9) 0%, rgba(255,214,120,.25) 45%, rgba(255,214,120,0) 75%);
    filter: blur(1px);
  }
  .column{
    position:absolute; top:2%; bottom:38%; width:3.4%;
    background: linear-gradient(90deg, #0a0705 0%, #3a2c18 18%, #6b5330 42%, #3a2c18 60%, #0a0705 100%);
    box-shadow: 0 0 40px rgba(0,0,0,.6);
  }
  .col-1{ left:4%; } .col-2{ left:16%; } .col-3{ right:16%; } .col-4{ right:4%; }

  .floor{
    position:absolute; left:0; right:0; bottom:0; height:40%;
    background:
      repeating-linear-gradient(100deg, rgba(0,0,0,.12) 0 2px, transparent 2px 64px),
      linear-gradient(180deg, #241914 0%, #140d0a 55%, #0a0605 100%);
  }
  .floor-sheen{
    position:absolute; left:0; right:0; bottom:0; height:40%;
    background: radial-gradient(70% 60% at 50% 0%, rgba(255,222,160,.18) 0%, rgba(0,0,0,0) 70%);
  }
  .haze{
    position:absolute; inset:0;
    background: radial-gradient(80% 60% at 50% 30%, rgba(255,200,120,.10) 0%, rgba(0,0,0,0) 65%);
  }
  .vignette{
    position:absolute; inset:0;
    background: radial-gradient(75% 75% at 50% 45%, rgba(0,0,0,0) 45%, rgba(0,0,0,.65) 100%);
  }
</style>
</head>
<body>
  <div class="room">
    <div class="back-wall"></div>
    <div class="ceiling-glow"></div>
    <div class="chandelier"></div>
    <div class="column col-1"></div>
    <div class="column col-2"></div>
    <div class="column col-3"></div>
    <div class="column col-4"></div>
    <div class="floor"></div>
    <div class="floor-sheen"></div>
    <div class="haze"></div>
    <div class="vignette"></div>
  </div>
</body></html>`;
}
