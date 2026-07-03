import datetime
import pandas as pd
import yfinance as yf
import streamlit as st

# Set page layout and title
st.set_page_config(page_title="Stock Price Dashboard", page_icon="📈", layout="wide")

# Dashboard Title
st.title("📈 Stock Price History Dashboard")
st.markdown("An interactive market data tool to visualize stock price trends.")

# Calculate default date range (last 6 months)
today = datetime.date.today()
default_start = today - datetime.timedelta(days=180)

# Controls in two columns at the top
col_input1, col_input2 = st.columns([1, 2])
with col_input1:
    ticker = st.text_input("Enter Stock Ticker", value="RELIANCE.NS").strip().upper()
with col_input2:
    date_range = st.date_input("Select Date Range", value=(default_start, today), max_value=today)

# Extract start and end dates safely
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = date_range[0] if isinstance(date_range, (list, tuple)) and len(date_range) > 0 else default_start
    end_date = today

# Only attempt to load if ticker is provided
if ticker:
    # Fetch stock data
    with st.spinner(f"Fetching data for {ticker}..."):
        df = yf.download(ticker, start=start_date, end=end_date, interval="1d", progress=False)

    if not df.empty:
        # Flatten MultiIndex columns if returned
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        if 'Close' in df.columns:
            # Calculate key metrics
            latest_close = float(df['Close'].iloc[-1])
            prev_close = float(df['Close'].iloc[-2]) if len(df) > 1 else latest_close
            price_change = latest_close - prev_close
            percent_change = (price_change / prev_close) * 100
            
            # Determine currency symbol based on exchange suffix
            currency = "₹" if ticker.endswith(".NS") or ticker.endswith(".BO") else "$"
            
            # Display metric cards
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    label=f"Latest Close ({df.index[-1].strftime('%Y-%m-%d')})",
                    value=f"{currency}{latest_close:.2f}",
                    delta=f"{price_change:+.2f} ({percent_change:+.2f}%)"
                )
            with col2:
                high_val = float(df['High'].max())
                st.metric(label="Period High", value=f"{currency}{high_val:.2f}")
            with col3:
                low_val = float(df['Low'].min())
                st.metric(label="Period Low", value=f"{currency}{low_val:.2f}")

            # Plotting price history
            st.subheader(f"Price Trend (Close Price) for {ticker}")
            st.line_chart(df['Close'])

            # Show raw data table
            with st.expander("View Raw Data (Recent 5 Days)"):
                st.dataframe(df.tail(5)[['Open', 'High', 'Low', 'Close', 'Volume']].style.format("{:.2f}"))
        else:
            st.error("The standard Close price column was not found in the downloaded data.")
    else:
        st.error(f"No data found for ticker '{ticker}' between {start_date} and {end_date}. Please verify the ticker symbol and date range.")
else:
    st.warning("Please enter a stock ticker symbol.")


