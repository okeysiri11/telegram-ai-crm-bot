import { BlackjackTable } from "../games/blackjack/BlackjackTable";

export function BlackjackSalon() {
  return (
    <section className="op-room op-bj-room" data-testid="blackjack-room" aria-label="Blackjack salon">
      <div className="op-scene-live is-bj" aria-hidden>
        <div className="op-scene-glow" />
        <div className="op-chandelier is-flicker" />
        <div className="op-lamp-pool" />
        <div className="op-fog" />
      </div>
      <BlackjackTable />
    </section>
  );
}

export default BlackjackSalon;
