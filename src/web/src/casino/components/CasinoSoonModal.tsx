export function CasinoSoonModal({
  title,
  onClose,
}: {
  title: string;
  onClose: () => void;
}) {
  return (
    <div className="op-modal-veil" role="presentation" onClick={onClose} data-testid="casino-soon-modal">
      <div
        className="op-modal"
        role="dialog"
        aria-labelledby="op-soon-title"
        onClick={(event) => event.stopPropagation()}
      >
        <p className="op-kicker">ODESSA PRIME</p>
        <h2 id="op-soon-title">Скоро</h2>
        <p className="op-sub">{title} откроется в следующем зале. Вы остаётесь в казино.</p>
        <button className="op-cta" type="button" onClick={onClose}>
          ПОНЯТНО
        </button>
      </div>
    </div>
  );
}

export function CasinoSoonPage({ title }: { title: string }) {
  return (
    <section className="op-room op-soon-page" data-testid="casino-soon-page">
      <p className="op-kicker">ODESSA PRIME</p>
      <h1 className="op-title">{title}</h1>
      <p className="op-sub">Скоро. Этот зал готовится к открытию — вы остаётесь в казино.</p>
    </section>
  );
}
