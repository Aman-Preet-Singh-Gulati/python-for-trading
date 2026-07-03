import pandas as pd
import yfinance as yf
import streamlit as st

# Set page layout and title
st.set_page_config(page_title="RELIANCE.NS Stock Dashboard", page_icon="📈", layout="wide")

# Dashboard Title
st.title("📈 RELIANCE.NS Price History Dashboard")
st.markdown("A simple, real-time market data tool showing the 6-month historical closing prices.")

ticker = "RELIANCE.NS"

# Fetch stock data
df = yf.download(ticker, period="6mo", interval="1d", progress=False)

if not df.empty:
    # Flatten MultiIndex columns if returned
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
        
    # Calculate key metrics
    latest_close = float(df['Close'].iloc[-1])
    prev_close = float(df['Close'].iloc[-2]) if len(df) > 1 else latest_close
    price_change = latest_close - prev_close
    percent_change = (price_change / prev_close) * 100
    
    # Display metric cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Latest Close Price", value=f"₹{latest_close:.2f}", delta=f"{price_change:+.2f} ({percent_change:+.2f}%)")
    with col2:
        st.metric(label="6-Month High", value=f"₹{float(df['High'].max()):.2f}")
    with col3:
        st.metric(label="6-Month Low", value=f"₹{float(df['Low'].min()):.2f}")

    # Plotting price history
    st.subheader("6-Month Price Trend (Close Price)")
    # Streamlit line chart automatically plots index (Date) as x-axis
    st.line_chart(df['Close'])

    # Show raw data table
    with st.expander("View Raw Data (Recent 5 Days)"):
        st.dataframe(df.tail(5)[['Open', 'High', 'Low', 'Close', 'Volume']].style.format("{:.2f}"))

else:
    st.error(f"Failed to fetch data for {ticker}. Please check connection or ticker symbol.")

