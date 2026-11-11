"""Regression tests for parsing, alignment, and FX correlation calculations."""

import numpy as np
import pandas as pd
import pytest

from analysis import correlation_analysis, normalize_prices, synthetic_prices


def prices(**columns):
    size = len(next(iter(columns.values())))
    return pd.DataFrame(
        columns, index=pd.date_range("2026-01-01", periods=size, freq="B")
    )


def test_returns_are_used_instead_of_closing_price_levels():
    frame = prices(
        EURUSD=[100, 102, 120, 115, 140, 138, 155],
        GBPUSD=[200, 201, 185, 188, 170, 172, 173],
    )
    values, actual, counts = correlation_analysis(frame, min_observations=3)
    expected = frame.pct_change(fill_method=None).corr()
    assert actual.loc["EURUSD", "GBPUSD"] == pytest.approx(
        expected.loc["EURUSD", "GBPUSD"]
    )
    assert abs(actual.loc["EURUSD", "GBPUSD"] - frame.corr().iat[0, 1]) > 0.01
    assert values.iloc[0].isna().all()
    assert counts.loc["EURUSD", "GBPUSD"] == 6


def test_pairwise_missing_data_not_forward_filled():
    frame = prices(
        EURUSD=[100, 110, np.nan, 121, 130, 132],
        GBPUSD=[1, 2, 3, 4, 5, 6],
        USDJPY=[90, 91, 92, 93, 94, 95],
    )
    observations, corr, counts = correlation_analysis(frame, min_observations=3)
    assert pd.isna(observations.loc[frame.index[2], "EURUSD"])
    assert pd.isna(observations.loc[frame.index[3], "EURUSD"])
    assert counts.loc["EURUSD", "GBPUSD"] == 3
    assert counts.loc["GBPUSD", "USDJPY"] == 5
    assert pd.notna(corr.loc["GBPUSD", "USDJPY"])


def test_minimum_observation_threshold_returns_nan():
    frame = prices(A=[1, 2, 3, 5, 8], B=[5, 4, 3, 2, 1])
    _, corr, count = correlation_analysis(frame, min_observations=5)
    assert count.loc["A", "B"] == 4
    assert np.isnan(corr.loc["A", "B"])


def test_level_mode_is_explicitly_distinct():
    frame = prices(A=[1, 2, 3, 4, 5], B=[5, 4, 3, 2, 1])
    observations, corr, counts = correlation_analysis(
        frame, method="levels", min_observations=3
    )
    assert len(observations) == 5
    assert corr.loc["A", "B"] == pytest.approx(-1)
    assert counts.loc["A", "B"] == 5


@pytest.mark.parametrize(
    "input_frame,match",
    [
        (pd.DataFrame({"timestamp": ["2026-01-01", "2026-01-01"],
                       "A": [1, 2], "B": [3, 4]}), "Duplicate timestamps"),
        (pd.DataFrame({"timestamp": ["invalid", "2026-01-02"],
                       "A": [1, 2], "B": [3, 4]}), "dates are invalid"),
        (pd.DataFrame({"timestamp": ["2026-01-01", "2026-01-02"],
                       "A": [1, 0], "B": [3, 4]}), "zero, negative"),
        (pd.DataFrame({"timestamp": ["2026-01-01", "2026-01-02"],
                       "A": [1, "bad"], "B": [3, 4]}), "nonnumeric"),
        (pd.DataFrame({"timestamp": ["2026-01-01", "2026-01-02"],
                       "A": [1, 2]}), "At least two"),
    ],
)
def test_invalid_input_is_rejected(input_frame, match):
    with pytest.raises(ValueError, match=match):
        normalize_prices(input_frame)


def test_csv_style_timestamps_and_numeric_strings_are_normalized():
    raw = pd.DataFrame(
        {"timestamp": ["2026-01-02", "2026-01-01"],
         " eurusd ": ["1.20", "1.10"], "gbpusd": ["1.5", "1.4"]}
    )
    clean = normalize_prices(raw)
    assert clean.index.is_monotonic_increasing
    assert clean.columns.tolist() == ["EURUSD", "GBPUSD"]
    assert clean.iloc[0, 0] == pytest.approx(1.1)


def test_constant_series_has_no_misleading_correlation():
    frame = prices(A=[1, 2, 4, 7, 11], B=[2, 2, 2, 2, 2])
    _, correlations, _ = correlation_analysis(frame, min_observations=3)
    assert np.isnan(correlations.loc["A", "B"])


def test_synthetic_demo_is_reproducible_and_positive():
    first, again = synthetic_prices(), synthetic_prices()
    pd.testing.assert_frame_equal(first, again)
    assert first.shape == (180, 6)
    assert first.gt(0).all().all()
    _, matrix, counts = correlation_analysis(first)
    assert matrix.loc["EURUSD", "EURUSD"] == pytest.approx(1.0)
    assert counts.loc["EURUSD", "GBPUSD"] == 179


def test_invalid_method_and_threshold_rejected():
    frame = synthetic_prices()
    with pytest.raises(ValueError, match="Method"):
        correlation_analysis(frame, method="invented")
    with pytest.raises(ValueError, match="three"):
        correlation_analysis(frame, min_observations=2)
