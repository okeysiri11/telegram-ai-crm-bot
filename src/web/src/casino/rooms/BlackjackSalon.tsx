import { BlackjackTable } from "../games/blackjack/BlackjackTable";

export function BlackjackSalon() {
  return (
    <section className="op-room op-bj-room" data-testid="blackjack-room" aria-label="Blackjack salon">
      <div className="op-room-depth is-bj">
        <div className="op-chandelier" />
      </div>
      <BlackjackTable />
    </section>
  );
}
