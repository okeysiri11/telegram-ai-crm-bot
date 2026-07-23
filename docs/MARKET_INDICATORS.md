# Market Indicators

**Version:** `4.7.1-enterprise`  
**Sprint:** 16.1  
**Package:** `applications/crypto_enterprise/technical_analysis/`  
**API:** `/api/crypto-ta/v1`

## Supported Indicators

| Indicator | Key |
|-----------|-----|
| Moving Average (SMA) | `sma` |
| Exponential Moving Average (EMA) | `ema` |
| MACD | `macd` |
| RSI | `rsi` |
| Stochastic RSI | `stoch_rsi` |
| Bollinger Bands | `bollinger` |
| VWAP | `vwap` |
| ATR | `atr` |
| ADX | `adx` |
| Ichimoku Cloud | `ichimoku` |
| Parabolic SAR | `parabolic_sar` |
| SuperTrend | `supertrend` |

## Endpoint

`POST /api/crypto-ta/v1/indicators` with `indicator`, `symbol`, `timeframe`, optional `period`/`params`.
