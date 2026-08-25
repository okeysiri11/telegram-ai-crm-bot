export function CardFan({ count = 2 }: { count?: number }) {
  return (
    <div className="op-card-row" data-testid="card-fan">
      {Array.from({ length: count }).map((_, i) => (
        <span key={i} className="op-card" style={{ animationDelay: `${i * 120}ms` }} />
      ))}
    </div>
  );
}
