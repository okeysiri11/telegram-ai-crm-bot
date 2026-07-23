# Crypto Finance Integration

**Version:** `5.1.4-enterprise`  
**API:** `/api/finance-da/v1`  
**Integration:** Conceptual bridge to Crypto Enterprise (`4.8.0-enterprise`) without modifying that platform.

Finance Enterprise Digital Assets provides treasury accounting, wallet controls, and exchange reconciliation alongside Crypto Enterprise markets and custody patterns.

## Surfaces

| Concern | Finance DA | Crypto Enterprise |
|---------|------------|-------------------|
| Registry | Assets, tokens, chains, custody | Markets, instruments |
| Wallets | Hot/cold/multisig/HD treasury wallets | Trading / protocol wallets |
| Accounting | Cost basis, PnL, revaluation | Trade fills (imported) |
| Exchanges | Link, sync, reconcile | Venue connectivity |

## API

- `POST /api/finance-da/v1/bootstrap` — seed registry, wallets, ledger, ops, exchange, AI
- `GET/POST /api/finance-da/v1/registry|wallets|accounting|operations|exchange|ai|dashboard|knowledge`
