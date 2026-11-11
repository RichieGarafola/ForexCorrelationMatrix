"""Market-data adapter tests use fakes; they never make network requests."""

import pandas as pd
import pytest

from market_data import fetch_market_prices


class FakeTicker:
    def __init__(self, symbol):
        self.symbol = symbol

    def history(self, **kwargs):
        assert kwargs["period"] == "1y"
        assert kwargs["interval"] == "1d"
        if self.symbol == "JPY=X":
            return pd.DataFrame()
        return pd.DataFrame(
            {"Close": [1.1, 1.2, 1.3, 1.4]},
            index=pd.date_range("2026-01-01", periods=4, freq="B"),
        )


class FakeClient:
    Ticker = FakeTicker


def test_adapter_warns_about_missing_pair_but_keeps_valid_pairs():
    frame, warnings = fetch_market_prices(
        ["EURUSD", "GBPUSD", "USDJPY"], client=FakeClient
    )
    assert frame.columns.tolist() == ["EURUSD", "GBPUSD"]
    assert len(frame) == 4
    assert len(warnings) == 1
    assert "USDJPY" in warnings[0]


def test_adapter_rejects_unavailable_data():
    with pytest.raises(ValueError, match="at least two pairs"):
        fetch_market_prices(["EURUSD", "USDJPY"], client=FakeClient)


def test_invalid_pair_or_period_is_rejected_before_io():
    with pytest.raises(ValueError, match="distinct supported"):
        fetch_market_prices(["EURUSD", "EURUSD"], client=FakeClient)
    with pytest.raises(ValueError, match="Unsupported"):
        fetch_market_prices(["EURUSD", "GBPUSD"], period="99y", client=FakeClient)
