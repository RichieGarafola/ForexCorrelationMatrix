import streamlit as st
import pandas as pd
import yfinance as yf
from matplotlib import pyplot as plt
import seaborn as sns

# Set Streamlit page configuration
st.set_page_config(page_title="Forex Correlation Analysis", page_icon=":bar_chart:")
st.title("Forex Correlation Analysis")

# Sidebar for selecting parameters
st.sidebar.header('Select Parameters')

# Define the list of Forex pairs for selection
selected_pairs = st.sidebar.multiselect('Select Forex Pairs', 
                                        ['AUDNZD', 'AUDUSD', 'EURCAD', 'EURCHF', 'EURGBP', 'EURUSD',
                                         'GBPCAD', 'GBPCHF', 'GBPUSD', 'NZDUSD', 'USDCAD', 'USDCHF',
                                         'AUDJPY', 'EURJPY', 'GBPJPY', 'NZDJPY', 'USDJPY'], 
                                        default=['AUDNZD', 'AUDUSD', 'EURCAD', 'EURCHF', 'EURGBP', 'EURUSD',
                                                 'GBPCAD', 'GBPCHF', 'GBPUSD', 'NZDUSD', 'USDCAD', 'USDCHF',
                                                 'AUDJPY', 'EURJPY', 'GBPJPY', 'NZDJPY', 'USDJPY'])

# Select interval for data
interval_map = {
    'Daily': '1d',
    'Weekly': '1wk',
    'Monthly': '1mo'
}
interval = st.sidebar.selectbox('Select Interval', list(interval_map.keys()), index=0)

# Function to fetch data using yfinance
@st.cache_resource()
def load_data(selected_pairs, interval):
    df = pd.DataFrame()
    for symbol in selected_pairs:
        data = yf.download(symbol + "=X", period='max', interval=interval_map[interval])
        if not data.empty:
            data['daily_returns'] = data['Close'].pct_change()
            data.rename(columns={'Close': symbol}, inplace=True)
            df = pd.concat([df, data[[symbol]]], axis=1)
    df.dropna(inplace=True)
    return df

# Call the function to fetch data
with st.spinner("Loading data..."):
    df = load_data(selected_pairs, interval)

# Create a correlation matrix using the corr() method in pandas
correlation_matrix = df.corr()

# Display the correlation matrix as a heatmap
st.subheader("Correlation Matrix:")
fig, ax = plt.subplots(figsize=(10, 10))
ax = sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm')
st.pyplot(fig)

# Explanation of the heatmap
st.markdown("""
The heatmap shows the correlation between each currency pair, with brighter colors indicating higher positive correlation and darker colors indicating higher negative correlation. The resulting heatmap suggests that there are some strong positive and negative correlations between certain currency pairs, which could be useful for identifying potential trading opportunities or risk management strategies.

The numbers in the heatmap represent the correlation coefficient between two currency pairs. The correlation coefficient ranges from -1 to 1, with:
- -1 indicating a perfectly negative correlation (i.e., the pairs move in opposite directions),
- 1 indicating a perfectly positive correlation (i.e., the pairs move in the same direction),
- 0 indicating no correlation (i.e., the pairs move independently of each other).

The closer the absolute value of the correlation coefficient is to 1, the stronger the correlation between the two pairs.
""")
