export function DealerPortrait({ name = "VICTORIA" }: { name?: string }) {
  return (
    <div className="op-dealer" data-testid="roulette-dealer" aria-label={`Крупье ${name}`}>
      <div className="op-dealer-bust">
        <span className="op-dealer-hair" />
        <span className="op-dealer-face" />
        <span className="op-dealer-collar" />
      </div>
      <div>
        <small className="op-kicker">КРУПЬЕ</small>
        <strong>{name}</strong>
      </div>
    </div>
  );
}
