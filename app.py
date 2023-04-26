import streamlit as st
import pandas as pd
import numpy as np
from tvDatafeed import TvDatafeed, Interval
from matplotlib import pyplot as plt
import datetime as dt
import seaborn as sns
import time

st.set_page_config(page_title="Forex Correlation Analysis", page_icon=":bar_chart:")

st.title("Forex Correlation Analysis")

tv = TvDatafeed()

# Sidebar for selecting parameters
st.sidebar.header('Select Parameters')

# Select Forex Pairs
selected_pairs = st.sidebar.multiselect('Select Forex Pairs', 
                                         ['AUDNZD', 'AUDUSD', 'EURCAD', 'EURCHF', 'EURGBP', 'EURUSD',
                                          'GBPCAD', 'GBPCHF', 'GBPUSD', 'NZDUSD', 'USDCAD', 'USDCHF',
                                          'AUDJPY', 'EURJPY', 'GBPJPY', 'NZDJPY', 'USDJPY'], 
                                         default=['AUDNZD', 'AUDUSD', 'EURCAD', 'EURCHF', 'EURGBP', 'EURUSD',
                                          'GBPCAD', 'GBPCHF', 'GBPUSD', 'NZDUSD', 'USDCAD', 'USDCHF',
                                          'AUDJPY', 'EURJPY', 'GBPJPY', 'NZDJPY', 'USDJPY'])

# Select interval for data
interval = st.sidebar.selectbox('Select Interval', ['1 Minute', '5 Minute', '15 Minute', '30 Minute', '1 Hour', '4 Hour', 'Daily', 'Weekly', 'Monthly'], index=6)

# Initialize an empty DataFrame to store the results
df = pd.DataFrame()

# Loop through the forex_pairs dictionary and read in the data for each symbol
with st.spinner("Loading data..."):
    for symbol in selected_pairs:
        if interval == '1 Minute':
            n_bars = 5000
            interval_type = Interval.in_1_minute
        elif interval == '5 Minute':
            n_bars = 5000
            interval_type = Interval.in_5_minute
        elif interval == '15 Minute':
            n_bars = 5000
            interval_type = Interval.in_15_minute
        elif interval == '30 Minute':
            n_bars = 5000
            interval_type = Interval.in_30_minute
        elif interval == '1 Hour':
            n_bars = 5000
            interval_type = Interval.in_1_hour
        elif interval == '4 Hour':
            n_bars = 5000
            interval_type = Interval.in_4_hour
        elif interval == 'Daily':
            n_bars = 5000
            interval_type = Interval.in_daily
        elif interval == 'Weekly':
            n_bars = 5000
            interval_type = Interval.in_weekly
        elif interval == 'Monthly':
            n_bars = 5000
            interval_type = Interval.in_monthly
        data = tv.get_hist(symbol=symbol, exchange='OANDA', interval=interval_type, n_bars=n_bars)
        # Calculate the daily returns
        data['daily_returns'] = data['close'].pct_change()
        # Rename the 'close' column to the symbol name
        data.rename(columns={'close': symbol}, inplace=True)
        # Concatenate the data for this symbol with the existing DataFrame
        df = pd.concat([df, data[[symbol]]], axis=1)
        time.sleep(0.5)  # add a 0.5 second delay between each request

# Drop any rows with missing values (i.e. from when the market is closed)
df.dropna(inplace=True)

# Display the resulting DataFrame
st.subheader("Forex Returns")
st.write(df)

# Create a correlation matrix using the corr() method in pandas
correlation_matrix = df.corr()

# Display the correlation matrix as a heatmap
st.subheader("Correlation Matrix:")
fig, ax = plt.subplots(figsize=(10, 10))
ax = sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm')
st.pyplot(fig)

# Print the correlation matrix
st.table(correlation_matrix)

st.markdown("""
The heatmap shows the correlation between each currency pair, with brighter colors indicating higher positive correlation and darker colors indicating higher negative correlation. The resulting heatmap suggests that there are some strong positive and negative correlations between certain currency pairs, which could be useful for identifying potential trading opportunities or risk management strategies.

The numbers in the heatmap represent the correlation coefficient between two currency pairs. The correlation coefficient ranges from -1 to 1, with -1 indicating a perfectly negative correlation (i.e. the pairs move in opposite directions), 1 indicating a perfectly positive correlation (i.e. the pairs move in the same direction), and 0 indicating no correlation (i.e. the pairs move independently of each other). The closer the absolute value of the correlation coefficient is to 1, the stronger the correlation between the two pairs.
""")
