"""Deterministic, offline-testable foreign-exchange correlation analysis.

Prices are strictly positive and indexed by unique timestamps. Return correlation
uses one-period percentage changes without filling missing observations.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def normalize_prices(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate a wide price table (timestamp/date column or datetime index).

    Blank prices are allowed and retained for pairwise completeness reporting.
    Invalid nonblank prices, duplicate columns, and duplicate dates are errors.
    """
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        raise ValueError("A nonempty table of closing prices is required.")

    data = frame.copy()
    date_columns = [c for c in data.columns if str(c).strip().lower() in ("timestamp", "date")]
    if len(date_columns) > 1:
        raise ValueError("Provide only one timestamp/date column.")
    if date_columns:
        raw_dates = data.pop(date_columns[0])
    elif isinstance(data.index, pd.DatetimeIndex):
        raw_dates = data.index
    else:
        raise ValueError("Include a 'timestamp' or 'date' column.")

    timestamps = pd.to_datetime(raw_dates, errors="coerce", utc=True)
    if timestamps.isna().any():
        raise ValueError("One or more dates are invalid or missing.")
    data.index = pd.DatetimeIndex(timestamps).tz_convert(None)
    data.index.name = "timestamp"

    names = [str(col).strip().upper() for col in data.columns]
    if len(names) != len(set(names)) or any(not name for name in names):
        raise ValueError("Currency-pair columns must have unique, nonempty names.")
    if len(names) < 2:
        raise ValueError("At least two currency-pair price columns are required.")
    data.columns = names

    if data.index.has_duplicates:
        raise ValueError("Duplicate timestamps found. Resolve these before comparing pairs.")

    for name in names:
        source = data[name]
        numeric = pd.to_numeric(source, errors="coerce")
        invalid_text = source.notna() & numeric.isna()
        if invalid_text.any():
            raise ValueError(f"{name} contains nonnumeric prices.")
        if (numeric.dropna() <= 0).any() or np.isinf(numeric.dropna().to_numpy()).any():
            raise ValueError(f"{name} contains zero, negative, or infinite prices.")
        data[name] = numeric.astype(float)

    return data.sort_index()


def correlation_analysis(
    prices: pd.DataFrame,
    *,
    method: str = "returns",
    min_observations: int = 30,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return (observations, Pearson correlation, pairwise observation counts).

    Rows with missing values in one pair do not discard valid observations from
    other pairs. Correlations with insufficient overlap remain NaN.
    """
    if method not in ("returns", "levels"):
        raise ValueError("Method must be 'returns' or 'levels'.")
    if min_observations < 3:
        raise ValueError("At least three overlapping observations are required.")
    clean = normalize_prices(prices)
    observations = (
        clean.pct_change(fill_method=None) if method == "returns" else clean
    )
    counts = observations.notna().astype(int).T.dot(observations.notna().astype(int))
    corr = observations.corr(method="pearson", min_periods=min_observations)
    return observations, corr, counts


def synthetic_prices(periods: int = 180, seed: int = 42) -> pd.DataFrame:
    """Generate clearly fictional, repeatable FX-like prices without an API."""
    if periods < 5:
        raise ValueError("At least five sample observations are required.")
    rng = np.random.default_rng(seed)
    shared = rng.normal(0.0, 0.004, periods)
    instruments = {
        "EURUSD": (1.08, 1.0),
        "GBPUSD": (1.26, 0.9),
        "AUDUSD": (0.67, 0.8),
        "USDJPY": (145.0, -0.95),
        "USDCHF": (0.89, -0.85),
        "EURGBP": (0.86, 0.3),
    }
    columns = {}
    for pair, (initial, loading) in instruments.items():
        log_changes = shared * loading + rng.normal(0.0, 0.002, periods)
        columns[pair] = initial * np.exp(np.cumsum(log_changes))
    result = pd.DataFrame(
        columns, index=pd.date_range(end="2026-10-30", periods=periods, freq="B")
    )
    result.index.name = "timestamp"
    return result
