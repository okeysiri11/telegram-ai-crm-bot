type Props = {
  entering: boolean;
  parallax: { x: number; y: number };
};

export function CasinoFacade({ entering, parallax }: Props) {
  const bg = { transform: `translate3d(${parallax.x * 3}px, ${parallax.y * 2}px, 0)` };
  const mid = { transform: `translate3d(${parallax.x * 6}px, ${parallax.y * 4}px, 0)` };
  const fg = { transform: `translate3d(${parallax.x * 10}px, ${parallax.y * 6}px, 0)` };

  return (
    <div className={`op-scene${entering ? " is-zooming" : ""}`} data-testid="casino-facade" aria-hidden>
      <div className="op-layer op-layer-back op-night-sky" style={bg} />
      <div className="op-layer op-city-glow" style={bg} />
      <div className="op-layer op-facade-photo" style={mid} />
      <div className="op-facade-architecture" style={mid} />
      <div className="op-marquee" style={mid}>
        <span className="op-marquee-sign">ODESSA PRIME</span>
        <span className="op-marquee-casino">CASINO</span>
      </div>
      <div className="op-chandelier" style={mid} />
      <div className="op-lamp-pool" style={mid} />
      <div className="op-brass-arch" style={mid} />
      <div className="op-columns" style={mid}>
        <span className="op-col" />
        <span className="op-col" />
        <span className="op-col" />
        <span className="op-col" />
      </div>
      <div className="op-doors" style={mid}>
        <span className="op-door" />
        <span className="op-door" />
      </div>
      <div className="op-marble" style={fg} />
      <div className="op-marble-sheen" style={fg} />
      <div className="op-runner" style={fg} />
      <div className="op-ropes" style={fg}>
        <span />
        <span />
      </div>
      <div className="op-silhouettes" style={fg}>
        <span />
        <span />
        <span />
      </div>
      <div className="op-fog" />
      <div className="op-dust" />
    </div>
  );
}
