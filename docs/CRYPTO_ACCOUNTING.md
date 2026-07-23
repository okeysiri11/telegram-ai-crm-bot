# Crypto Accounting

**Version:** `5.1.4-enterprise`  
**API:** `GET/POST /api/finance-da/v1/accounting`

## Ledger

Crypto ledger posts buy/sell lots with quantity and unit cost per asset and wallet.

## Cost basis

Average cost is derived from buy lots; used for realized and unrealized gain/loss.

## Gain / Loss

- **Realized** — on disposal at sell price vs average cost
- **Unrealized** — mark-to-market vs average cost
- **Revaluation** — book asset to new market price
- **Portfolio valuation** — aggregated holdings × prices
