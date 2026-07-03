import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Set page config for wider layout
st.set_page_config(page_title="Trading Signal Scanner", layout="wide")

st.title("Trading Signal Scanner")
st.subheader("RELIANCE.NS - Moving Average Crossover (20-day vs 50-day)")

# Fetch data
ticker = "RELIANCE.NS"
ticker_obj = yf.Ticker(ticker)
data = ticker_obj.history(period="6mo", interval="1d")

if data.empty:
    st.error(f"No data found for {ticker}")
else:
    # Ensure index timezone is removed if any, for better plotting
    if isinstance(data.index, pd.DatetimeIndex) and data.index.tz is not None:
        data.index = data.index.tz_localize(None)

    # Calculate moving averages
    data['SMA20'] = data['Close'].rolling(window=20).mean()
    data['SMA50'] = data['Close'].rolling(window=50).mean()
    
    # Create signals
    # 1 if SMA20 > SMA50, 0 otherwise
    data['Signal'] = np.where(data['SMA20'] > data['SMA50'], 1.0, 0.0)
    
    # Calculate difference to find crossovers
    data['Position'] = data['Signal'].diff()
    
    # Buy signal when Position == 1 (Signal goes from 0 to 1)
    # Sell signal when Position == -1 (Signal goes from 1 to 0)
    buy_signals = data[data['Position'] == 1]
    sell_signals = data[data['Position'] == -1]

    # --- HISTORICAL PERFORMANCE CHECK ---
    total_buy_signals = len(buy_signals)
    profitable_signals = 0
    signals_checked = 0
    
    for i in range(total_buy_signals):
        buy_date = buy_signals.index[i]
        buy_idx = data.index.get_loc(buy_date)
        # Check what the price did in the 5 days following each buy signal
        if buy_idx + 5 < len(data):
            price_at_buy = data['Close'].iloc[buy_idx]
            price_5_days_later = data['Close'].iloc[buy_idx + 5]
            if price_5_days_later > price_at_buy:
                profitable_signals += 1
            signals_checked += 1
            
    win_rate = (profitable_signals / signals_checked * 100) if signals_checked > 0 else 0

    st.markdown("---")
    st.subheader("Signal Performance Summary")
    st.caption("⚠️ **Note:** This is a rough historical check, not a guarantee of future performance.")
    
    col1, col2 = st.columns(2)
    col1.metric("Total Buy Signals Fired", total_buy_signals)
    col2.metric(
        "Buy Signals Followed by Price Increase (after 5 days)", 
        f"{win_rate:.0f}%" if signals_checked > 0 else "N/A"
    )
    st.markdown("---")
    # ------------------------------------

    # Create plot
    fig = go.Figure()

    # Plot Close Price
    fig.add_trace(go.Scatter(
        x=data.index, 
        y=data['Close'], 
        mode='lines', 
        name='Close Price',
        line=dict(color='#1f77b4', width=2)
    ))

    # Plot SMA20
    fig.add_trace(go.Scatter(
        x=data.index, 
        y=data['SMA20'], 
        mode='lines', 
        name='20-Day SMA',
        line=dict(color='#ff7f0e', width=1.5)
    ))

    # Plot SMA50
    fig.add_trace(go.Scatter(
        x=data.index, 
        y=data['SMA50'], 
        mode='lines', 
        name='50-Day SMA',
        line=dict(color='#9467bd', width=1.5)
    ))

    # Plot Buy Signals
    fig.add_trace(go.Scatter(
        x=buy_signals.index,
        y=buy_signals['SMA20'], 
        mode='markers',
        name='Buy Signal',
        marker=dict(symbol='triangle-up', color='green', size=14, line=dict(width=1, color='darkgreen'))
    ))

    # Plot Sell Signals
    fig.add_trace(go.Scatter(
        x=sell_signals.index,
        y=sell_signals['SMA20'], 
        mode='markers',
        name='Sell Signal',
        marker=dict(symbol='triangle-down', color='red', size=14, line=dict(width=1, color='darkred'))
    ))

    fig.update_layout(
        title='RELIANCE.NS - Price Chart with Buy/Sell Signals',
        xaxis_title='Date',
        yaxis_title='Price (INR)',
        template='plotly_white',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=20, r=20, t=50, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)
