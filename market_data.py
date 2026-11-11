"""Optional Yahoo Finance market-data adapter.

No network calls occur during import, tests, or synthetic/CSV analysis.
Yahoo's public market-data feed can be delayed, throttled, or unavailable.
"""

from __future__ import annotations

import pandas as pd

from analysis import normalize_prices

# Explicit mapping avoids ticker-quotation ambiguity (e.g., JPY=X is USD/JPY).
YAHOO_TICKERS = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "AUDUSD": "AUDUSD=X",
    "NZDUSD": "NZDUSD=X",
    "USDJPY": "JPY=X",
    "USDCHF": "CHF=X",
    "USDCAD": "CAD=X",
    "EURGBP": "EURGBP=X",
    "EURJPY": "EURJPY=X",
    "GBPJPY": "GBPJPY=X",
}
PERIODS = ("6mo", "1y", "2y", "5y")
INTERVALS = {"Daily": "1d", "Weekly": "1wk", "Monthly": "1mo"}


def fetch_market_prices(
    pairs: list[str],
    *,
    period: str = "1y",
    interval: str = "1d",
    client=None,
) -> tuple[pd.DataFrame, list[str]]:
    """Fetch multiple currency pairs and return validated close prices + warnings.

    A missing/failed instrument is reported, not treated as a zero price.
    Caller chooses when to invoke this function (never run on page import).
    """
    if len(set(pairs)) < 2 or any(pair not in YAHOO_TICKERS for pair in pairs):
        raise ValueError("Select at least two distinct supported currency pairs.")
    if period not in PERIODS or interval not in INTERVALS.values():
        raise ValueError("Unsupported market-data period or interval.")
    if client is None:
        import yfinance as client  # lazy import to keep offline analysis independent

    closes = {}
    warnings = []
    for pair in pairs:
        ticker = YAHOO_TICKERS[pair]
        try:
            history = client.Ticker(ticker).history(
                period=period, interval=interval, auto_adjust=False
            )
            if history is None or history.empty or "Close" not in history:
                warnings.append(f"No closing prices returned for {pair} ({ticker}).")
                continue
            dates = pd.to_datetime(history.index, utc=True, errors="coerce")
            if dates.isna().any():
                warnings.append(f"Invalid timestamps in the feed for {pair} ({ticker}).")
                continue
            dates = pd.DatetimeIndex(dates).tz_convert(None).normalize()
            closes[pair] = pd.Series(
                pd.to_numeric(history["Close"], errors="coerce").to_numpy(dtype=float),
                index=dates,
                name=pair,
            )
        except Exception as exc:
            warnings.append(f"Could not retrieve {pair} ({ticker}): {type(exc).__name__}.")

    if len(closes) < 2:
        raise ValueError("Market data could not be retrieved for at least two pairs. Try the synthetic demo or upload a CSV.")

    return normalize_prices(pd.concat(closes.values(), axis=1)), warnings
