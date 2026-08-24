"""EUR/USD ↔ DXY correlation helpers."""

from __future__ import annotations

from typing import Any


def pearson(xs: list[float], ys: list[float]) -> float | None:
    n = min(len(xs), len(ys))
    if n < 3:
        return None
    xs, ys = xs[:n], ys[:n]
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    denx = sum((x - mx) ** 2 for x in xs) ** 0.5
    deny = sum((y - my) ** 2 for y in ys) ** 0.5
    if denx == 0 or deny == 0:
        return None
    return num / (denx * deny)


def eurusd_dxy_correlation(
    eurusd_closes: list[float],
    dxy_closes: list[float],
) -> dict[str, Any]:
    coef = pearson(eurusd_closes, dxy_closes)
    if coef is None:
        return {
            "pair": "EUR/USD vs DXY",
            "coefficient": None,
            "status": "insufficient_data",
            "message": "Нужны ряды цен обоих инструментов",
            "expected_relationship": "обычно обратная корреляция",
        }
    return {
        "pair": "EUR/USD vs DXY",
        "coefficient": round(coef, 4),
        "status": "ok",
        "message": "Расчёт по предоставленным рядам",
        "expected_relationship": "обычно обратная корреляция",
        "aligned_with_expectation": coef < 0,
    }
