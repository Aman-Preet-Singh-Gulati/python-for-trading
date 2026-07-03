import streamlit as st
import yfinance as yf
from datetime import datetime, timedelta

# Configure the Streamlit page
st.set_page_config(page_title="Stock Dashboard", page_icon="📈")

# Title of the dashboard
st.title("Stock Price History")

# Inputs for ticker and date range in a row
col1, col2 = st.columns(2)

with col1:
    symbol = st.text_input("Stock Ticker", value="RELIANCE.NS")

with col2:
    # Default to the last 6 months (approx 180 days)
    end_date = datetime.today().date()
    start_date = end_date - timedelta(days=180)
    
    date_range = st.date_input("Date Range", value=(start_date, end_date))

# Ensure the user has selected both a start and end date before rendering the chart
if len(date_range) == 2:
    start_dt, end_dt = date_range
    
    # We use Streamlit's caching to avoid re-fetching on every app interaction
    @st.cache_data
    def load_data(ticker, start, end):
        stock = yf.Ticker(ticker)
        # Fetch daily data within the selected date range
        data = stock.history(start=start, end=end)
        return data

    data = load_data(symbol, start_dt, end_dt)
    
    if not data.empty:
        # Display a clear subtitle for the chart
        st.subheader(f"Closing Price: {symbol}")
        
        # Plot the closing price as a line chart
        # Streamlit's native line_chart automatically uses the DataFrame's datetime index for the x-axis
        st.line_chart(data['Close'])
    else:
        st.warning(f"No data found for '{symbol}'. Please check the ticker and date range.")
else:
    st.info("Please select an end date for the date range.")
