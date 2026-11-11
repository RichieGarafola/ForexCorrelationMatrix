"""Streamlit UI for a reproducible FX-correlation research example."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from analysis import correlation_analysis, normalize_prices, synthetic_prices
from market_data import INTERVALS, PERIODS, YAHOO_TICKERS, fetch_market_prices


st.set_page_config(
    page_title="Forex Correlation | Richie Garafola",
    page_icon="📈",
    layout="wide",
)
st.title("Forex Correlation Explorer")
st.markdown(
    "**Compare how currency pairs move together, with transparent data quality and "
    "pairwise observation counts.**"
)
st.caption("Research demonstration only · Historical correlation is not a trading signal.")

with st.sidebar:
    st.header("Analysis settings")
    source = st.radio(
        "Data source",
        ["Synthetic demo", "Upload price CSV", "Yahoo Finance"],
        help="The demo works offline. Yahoo data may be delayed, throttled, or unavailable.",
    )
    measure = st.radio(
        "Correlation basis",
        ["Percentage returns (recommended)", "Closing price levels (exploratory)"],
    )
    minimum = st.slider(
        "Minimum overlapping observations",
        min_value=3,
        max_value=150,
        value=30,
        help="Pairs below this threshold show N/A instead of a correlation.",
    )

prices = None
feed_warnings = []

if source == "Synthetic demo":
    prices = synthetic_prices()
    st.info(
        "Using deterministic, fictional FX-like prices. No market data or network "
        "connection is required."
    )
elif source == "Upload price CSV":
    st.info(
        "Upload a wide CSV: one timestamp or date column and at least two currency-pair "
        "closing-price columns. Missing prices may be blank; duplicate dates are rejected."
    )
    upload = st.file_uploader("Upload closing-price CSV", type=["csv"])
    if upload is None:
        st.stop()
    try:
        prices = normalize_prices(pd.read_csv(upload))
    except (ValueError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        st.error(f"Invalid CSV: {exc}")
        st.stop()
else:
    st.warning(
        "Yahoo Finance data is a best-effort external source, not an exchange-grade "
        "or guaranteed real-time feed. Retrieval is only attempted when you submit."
    )
    with st.form("market_request"):
        selected_pairs = st.multiselect(
            "Currency pairs",
            options=list(YAHOO_TICKERS),
            default=["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"],
        )
        period = st.selectbox("Historical window", PERIODS, index=1)
        label = st.selectbox("Observation frequency", list(INTERVALS))
        requested = st.form_submit_button("Fetch historical market prices")
    if requested:
        try:
            with st.spinner("Fetching historical closing prices..."):
                latest, warnings = fetch_market_prices(
                    selected_pairs, period=period, interval=INTERVALS[label]
                )
            st.session_state["market_prices"] = latest
            st.session_state["market_warnings"] = warnings
            st.session_state["market_parameters"] = (
                ", ".join(selected_pairs) + f" | {period} | {label}"
            )
        except (ValueError, ImportError, RuntimeError) as exc:
            st.error(f"Market data unavailable: {exc}")
    if "market_prices" not in st.session_state:
        st.info("Choose two or more pairs and select 'Fetch historical market prices'.")
        st.stop()
    prices = st.session_state["market_prices"]
    feed_warnings = st.session_state.get("market_warnings", [])
    st.caption("Last successful fetch: " + st.session_state["market_parameters"])

for warning in feed_warnings:
    st.warning(warning)

method = "returns" if measure.startswith("Percentage") else "levels"
if method == "levels":
    st.warning(
        "Price-level correlations can be spurious when series trend together. "
        "Percentage returns are generally more appropriate for co-movement analysis."
    )

try:
    observations, correlations, counts = correlation_analysis(
        prices, method=method, min_observations=minimum
    )
except ValueError as exc:
    st.error(f"Analysis unavailable: {exc}")
    st.stop()

available = int(np.triu(correlations.notna().to_numpy(), k=1).sum())
total = len(prices.columns) * (len(prices.columns) - 1) // 2
m1, m2, m3 = st.columns(3)
m1.metric("Price observations", len(prices))
m2.metric("Currency pairs", len(prices.columns))
m3.metric("Valid correlations", f"{available} / {total}")

st.subheader("Correlation matrix")
st.caption(
    ("Pearson correlation of one-period percentage returns" if method == "returns"
     else "Pearson correlation of closing price levels")
    + f" · at least {minimum} pairwise overlapping observations"
)
if available == 0:
    st.warning("No cross-pair correlations meet the minimum sample size. Lower the threshold or provide more data.")

size = max(6.0, min(12.0, len(correlations) * 0.9))
fig, ax = plt.subplots(figsize=(size, size))
matrix = np.ma.masked_invalid(correlations.to_numpy(dtype=float))
im = ax.imshow(matrix, cmap="coolwarm", vmin=-1, vmax=1)
ax.set_xticks(range(len(correlations.columns)), labels=correlations.columns, rotation=45, ha="right")
ax.set_yticks(range(len(correlations.index)), labels=correlations.index)
for row in range(len(correlations)):
    for col in range(len(correlations.columns)):
        value = correlations.iat[row, col]
        ax.text(
            col, row, "N/A" if pd.isna(value) else f"{value:.2f}",
            ha="center", va="center", fontsize=9,
            color="white" if pd.notna(value) and abs(value) >= 0.65 else "black",
        )
fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Pearson r")
fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

st.dataframe(correlations.style.format("{:.3f}", na_rep="N/A"), use_container_width=True)
st.download_button(
    "Download correlation matrix (CSV)",
    data=correlations.to_csv().encode("utf-8"),
    file_name="forex_correlation_matrix.csv",
    mime="text/csv",
)
with st.expander("Inspect pairwise sample sizes and underlying observations"):
    st.write("Overlapping observations used for each pair:")
    st.dataframe(counts, use_container_width=True)
    st.write("Prices (not returns):")
    st.dataframe(prices.tail(20), use_container_width=True)
    st.write("Values used in the correlation analysis:")
    st.dataframe(observations.tail(20), use_container_width=True)
    st.download_button(
        "Download input prices (CSV)",
        data=prices.to_csv().encode("utf-8"),
        file_name="forex_closing_prices.csv",
        mime="text/csv",
    )

st.caption(
    "Missing values are not forward-filled. Correlations use overlapping timestamps "
    "for each pair; N/A indicates insufficient overlap or a zero-variance series. "
    "The synthetic dataset is fictional and is not suitable for trading decisions."
)
