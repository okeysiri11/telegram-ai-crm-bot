import { useState } from "react";
import { Link } from "react-router-dom";
import { Button, EmptyState, Skeleton } from "@/ui";
import { formatDemoChips, formatLedgerDelta, formatTimestamp } from "./currency";
import { grantDemoChips } from "./casinoApi";
import type { CasinoLedgerEntry, CasinoWallet } from "./types";

export function CasinoAuthGate({ message }: { message?: string }) {
  return (
    <EmptyState
      title="Нужна авторизация"
      description={message || "Войдите, чтобы получить демо-фишки и сделать PLAY-ставку. Реальных платежей нет."}
      actionLabel="Войти"
      actionTo="/login"
    />
  );
}

export function CasinoWalletBar({
  wallet,
  loading,
  error,
  onRefresh,
  onGranted,
}: {
  wallet: CasinoWallet | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
  onGranted: (next: CasinoWallet) => void;
}) {
  const [grantError, setGrantError] = useState<string | null>(null);

  async function grant() {
    setGrantError(null);
    try {
      onGranted(await grantDemoChips());
    } catch (err) {
      setGrantError(err instanceof Error ? err.message : "grant_failed");
    }
  }

  if (error === "auth_required") {
    return <CasinoAuthGate />;
  }
  if (loading && !wallet) {
    return <Skeleton rows={2} />;
  }
  if (error && !wallet) {
    return (
      <div className="casino-status" role="alert">
        {error}
        <Button size="sm" variant="secondary" onClick={onRefresh}>
          Повторить
        </Button>
      </div>
    );
  }

  return (
    <section className="casino-wallet" aria-label="PLAY wallet">
      <div>
        <p className="casino-kicker">PLAY · DEMO CHIPS</p>
        <p className="casino-wallet-balance">{wallet ? formatDemoChips(wallet.balance_chips) : "—"}</p>
        <p className="eds-type-helper">Только демо. Без вывода, без карт, без реальных денег.</p>
      </div>
      <div className="casino-actions">
        <Button
          aria-label="Получить демо-фишки"
          onClick={() => void grant()}
          disabled={!wallet?.demo_grant_available}
        >
          Получить демо-фишки
        </Button>
        {!wallet?.demo_grant_available && wallet?.demo_grant_retry_after_seconds ? (
          <span className="eds-type-helper">Пауза {wallet.demo_grant_retry_after_seconds} с</span>
        ) : null}
        {grantError ? (
          <span className="casino-status" role="alert">
            {grantError}
          </span>
        ) : null}
      </div>
    </section>
  );
}

export function CasinoLedgerPanel({
  items,
  loading,
  error,
}: {
  items: CasinoLedgerEntry[];
  loading: boolean;
  error: string | null;
}) {
  if (loading && items.length === 0) return <Skeleton rows={4} />;
  if (error === "auth_required") return <CasinoAuthGate message="История доступна после входа." />;
  if (error) return <p className="casino-status">{error}</p>;
  if (!items.length) {
    return <EmptyState title="История пуста" description="Ставки и демо-фишки появятся здесь." />;
  }
  return (
    <div className="casino-history" role="region" aria-label="История PLAY">
      <table>
        <thead>
          <tr>
            <th>Время</th>
            <th>Операция</th>
            <th>Ставка</th>
            <th>Результат</th>
            <th>Дельта</th>
            <th>Баланс</th>
          </tr>
        </thead>
        <tbody>
          {items.map((row) => (
            <tr key={row.entry_id}>
              <td>{formatTimestamp(row.created_ts)}</td>
              <td>{row.operation}</td>
              <td>{row.wager != null ? formatDemoChips(row.wager) : "—"}</td>
              <td>{row.win_loss === "win" ? "Выигрыш" : row.win_loss === "loss" ? "Проигрыш" : "—"}</td>
              <td>{formatLedgerDelta(row.balance_delta)}</td>
              <td>{formatDemoChips(row.resulting_balance)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function CasinoNav({ venueId }: { venueId: string }) {
  return (
    <nav className="casino-nav" aria-label="Казино">
      <Link to="/casino">Лобби</Link>
      <Link to={`/casino/venues/${venueId}`}>Зал</Link>
      <Link to={`/casino/venues/${venueId}/roulette`}>Рулетка</Link>
      <Link to="/enterprise-city">City</Link>
    </nav>
  );
}
