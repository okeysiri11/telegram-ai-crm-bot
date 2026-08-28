type Props = {
  entering: boolean;
};

export function CasinoFacade({ entering }: Props) {
  return (
    <div className={`op-scene${entering ? " is-zooming" : ""}`} data-testid="casino-facade" aria-hidden>
      <div className="op-layer op-layer-back op-night-sky op-par-back" />
      <div className="op-layer op-city-glow op-par-back" />
      <div className="op-layer op-facade-photo op-par-mid" />
      <div className="op-gold-bloom op-par-mid" />
      <div className="op-chandelier op-par-mid" />
      <div className="op-lamp-pool op-par-mid" />
      <div className="op-marble op-par-fg" />
      <div className="op-marble-sheen op-par-fg" />
      <div className="op-runner op-par-fg" />
      <div className="op-ropes op-par-fg">
        <span />
        <span />
      </div>
      <div className="op-silhouettes op-par-fg">
        <span />
        <span />
        <span />
      </div>
      <div className="op-fog" />
    </div>
  );
}
