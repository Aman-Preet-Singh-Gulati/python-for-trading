import streamlit as st
import yfinance as yf

# Configure the Streamlit page
st.set_page_config(page_title="Reliance Stock Dashboard", page_icon="📈")

# Title of the dashboard
st.title("Reliance Industries Stock Price History")

# Define the stock symbol
symbol = "RELIANCE.NS"

# Fetch 6 months of daily data using yfinance
# We use Streamlit's caching to avoid re-fetching on every app interaction
@st.cache_data
def load_data(ticker):
    stock = yf.Ticker(ticker)
    data = stock.history(period="9mo")
    return data

data = load_data(symbol)

# Display a clear subtitle for the chart
st.subheader(f"Closing Price - Last 9 Months ({symbol})")

# Plot the closing price as a line chart
# Streamlit's native line_chart automatically uses the DataFrame's datetime index for the x-axis
st.line_chart(data['Close'])
