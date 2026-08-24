/**
 * Sprint 48.0/48.1 — Crypto/OTC transaction idempotency & duplicate-payout
 * protection (security-critical).
 *
 * Requirement 4/11: blocking warning shown before any payout action, with
 * the mandatory fields. Requirement 9 (Sprint 48.1): override is disabled in
 * production — no real step-up authentication provider exists yet (see
 * services.pg_crypto_tx_antifraud_engine.CryptoTxAntifraudEngine
 * ._verify_step_up_token) — so only Cancel and Send-for-review are offered.
 * The backend rejects an override attempt unconditionally (503) regardless
 * of what this component does; the button is removed here so the UI doesn't
 * promise something the server can't deliver, not as the actual security
 * boundary.
 *
 * Reused everywhere a payout can be initiated in the Web/Operator UI — do
 * not build a second duplicate-warning component; extend this one.
 */

import { useState } from "react";
import { Button, Modal } from "@/ui";
import {
  cancelCryptoTx,
  requestCryptoTxReview,
  type CryptoTransaction,
  type DuplicateWarning,
} from "./cryptoTxApi";

const ANOMALY_LABELS_RU: Record<string, string> = {
  resubmitted_after_cancellation: "Повторная подача после отмены",
  same_wallet_amount_short_window: "Тот же кошелёк/сумма за короткое время",
  linked_to_multiple_customers: "Связано с несколькими клиентами",
  repeated_operator_attempts: "Повторные попытки того же оператора",
};

export type DuplicateTxWarningModalProps = {
  open: boolean;
  transaction: CryptoTransaction;
  warning: DuplicateWarning;
  onClose: () => void;
  /** Called after cancel/review succeeds, so the caller can refresh
   * whatever payout UI triggered this warning. */
  onResolved: (transaction: CryptoTransaction) => void;
};

export function DuplicateTxWarningModal({
  open,
  transaction,
  warning,
  onClose,
  onResolved,
}: DuplicateTxWarningModalProps) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCancel() {
    setBusy(true);
    setError(null);
    try {
      const updated = await cancelCryptoTx(transaction.id, "Отменено оператором в веб-интерфейсе");
      onResolved(updated);
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось отменить.");
    } finally {
      setBusy(false);
    }
  }

  async function handleReview() {
    setBusy(true);
    setError(null);
    try {
      const updated = await requestCryptoTxReview(transaction.id);
      onResolved(updated);
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось отправить на проверку.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal open={open} title="Возможен дублирующий платёж" onClose={onClose}>
      <div className="space-y-3" data-testid="crypto-duplicate-warning">
        <div className="rounded-md border border-[var(--eds-danger)] bg-[var(--eds-surface-sunken)] p-3">
          <p className="eds-type-body font-semibold text-[var(--eds-danger)]">
            🛑 Эта транзакция уже зарегистрирована. Автоматическая обработка заблокирована.
          </p>
        </div>

        <dl className="grid grid-cols-2 gap-x-4 gap-y-1 eds-type-small">
          <dt className="text-[var(--eds-text-muted)]">Хэш транзакции</dt>
          <dd data-testid="dup-tx-hash">{warning.tx_hash}</dd>
          <dt className="text-[var(--eds-text-muted)]">Сеть</dt>
          <dd>{warning.network}</dd>
          <dt className="text-[var(--eds-text-muted)]">Токен</dt>
          <dd>{warning.token}</dd>
          <dt className="text-[var(--eds-text-muted)]">Сумма</dt>
          <dd>{warning.amount}</dd>
          <dt className="text-[var(--eds-text-muted)]">Кошелёк</dt>
          <dd>{warning.wallet_address}</dd>
          <dt className="text-[var(--eds-text-muted)]">Текущий статус</dt>
          <dd data-testid="dup-status">{warning.previous_status}</dd>
          {warning.previous_legacy_deal_id ? (
            <>
              <dt className="text-[var(--eds-text-muted)]">Предыдущая сделка</dt>
              <dd>#{warning.previous_legacy_deal_id}</dd>
            </>
          ) : null}
          {warning.previous_legacy_payment_id ? (
            <>
              <dt className="text-[var(--eds-text-muted)]">Предыдущий платёж</dt>
              <dd>#{warning.previous_legacy_payment_id}</dd>
            </>
          ) : null}
          <dt className="text-[var(--eds-text-muted)]">Предыдущий оператор</dt>
          <dd>{warning.previous_operator_id}</dd>
          {/* Backend already redacts previous_customer_id for non-privileged
              viewers (viewer_role passed into confirm_payout); if it's
              present at all, the server already decided this viewer may see
              it — no client-side role re-check needed for display. */}
          {warning.previous_customer_id != null ? (
            <>
              <dt className="text-[var(--eds-text-muted)]">Предыдущий клиент</dt>
              <dd data-testid="dup-customer">{warning.previous_customer_id}</dd>
            </>
          ) : null}
          <dt className="text-[var(--eds-text-muted)]">Впервые зарегистрирована</dt>
          <dd>{warning.first_seen_at}</dd>
        </dl>

        {warning.anomalies.length > 0 ? (
          <div className="rounded-md border border-[var(--eds-warning)] p-2 eds-type-small">
            <p className="font-semibold">Аномалии:</p>
            <ul className="list-disc pl-5">
              {warning.anomalies.map((a) => (
                <li key={a}>{ANOMALY_LABELS_RU[a] || a}</li>
              ))}
            </ul>
          </div>
        ) : null}

        {error ? <p className="eds-type-small text-[var(--eds-danger)]">{error}</p> : null}

        <div className="flex flex-wrap gap-2 pt-2">
          <Button variant="secondary" disabled={busy} onClick={handleCancel} data-testid="dup-action-cancel">
            ❌ Отмена
          </Button>
          <Button variant="secondary" disabled={busy} onClick={handleReview} data-testid="dup-action-review">
            🔍 На проверку
          </Button>
        </div>
        <p className="eds-type-small text-[var(--eds-text-muted)]" data-testid="dup-override-unavailable">
          ⚠️ Override недоступен: требуется реальная повторная аутентификация, которая пока не
          реализована.
        </p>
      </div>
    </Modal>
  );
}
