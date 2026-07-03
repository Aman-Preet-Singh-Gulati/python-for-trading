import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import datetime

# Set page config for wider layout
st.set_page_config(page_title="Trading Signal Scanner", layout="wide")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("Strategy Controls")

ticker = st.sidebar.text_input("Ticker Symbol", value="RELIANCE.NS")

# Date range slider
today = datetime.date.today()
min_date = today - datetime.timedelta(days=365 * 5) # 5 years back
start_date, end_date = st.sidebar.slider(
    "Date Range",
    min_value=min_date,
    max_value=today,
    value=(today - datetime.timedelta(days=180), today),
    format="YYYY-MM-DD"
)

strategy = st.sidebar.selectbox(
    "Trading Strategy",
    options=["MA Crossover", "RSI", "Bollinger Bands"]
)

# Conditional Parameter Sliders
if strategy == "MA Crossover":
    ma_short = st.sidebar.slider("Short MA Period", min_value=5, max_value=50, value=20)
    ma_long = st.sidebar.slider("Long MA Period", min_value=20, max_value=200, value=50)
    subtitle = f"{ticker} - MA Crossover ({ma_short}-day vs {ma_long}-day)"
elif strategy == "RSI":
    rsi_period = st.sidebar.slider("RSI Period", min_value=5, max_value=30, value=14)
    rsi_oversold = st.sidebar.slider("Oversold Threshold", min_value=10, max_value=50, value=30)
    rsi_overbought = st.sidebar.slider("Overbought Threshold", min_value=50, max_value=90, value=70)
    subtitle = f"{ticker} - RSI ({rsi_period} period, {rsi_oversold}/{rsi_overbought} thresholds)"
elif strategy == "Bollinger Bands":
    bb_window = st.sidebar.slider("Window Size", min_value=10, max_value=100, value=20)
    bb_std = st.sidebar.slider("Std Dev Multiplier", min_value=1.0, max_value=4.0, value=2.0, step=0.1)
    subtitle = f"{ticker} - Bollinger Bands ({bb_window} window, {bb_std}x std dev)"

# --- MAIN DASHBOARD ---
st.title("Trading Signal Scanner")
st.subheader(subtitle)

# Fetch data
@st.cache_data
def load_data(ticker_symbol, start, end):
    return yf.download(ticker_symbol, start=start, end=end)

data = load_data(ticker, start_date, end_date)

if data.empty:
    st.error(f"No data found for {ticker} in the selected date range.")
else:
    # Ensure index timezone is removed if any, for better plotting
    if isinstance(data.index, pd.DatetimeIndex) and data.index.tz is not None:
        data.index = data.index.tz_localize(None)

    # We need a 1D series for Close to avoid MultiIndex issues in some yfinance versions
    if isinstance(data.columns, pd.MultiIndex):
        close_series = data['Close'][ticker]
    else:
        close_series = data['Close']

    df = pd.DataFrame({'Close': close_series})
    
    buy_signals = pd.Series(dtype=bool)
    sell_signals = pd.Series(dtype=bool)

    # Strategy Implementations
    if strategy == "MA Crossover":
        df['SMA_Short'] = df['Close'].rolling(window=ma_short).mean()
        df['SMA_Long'] = df['Close'].rolling(window=ma_long).mean()
        
        # 1 if short > long, 0 otherwise
        df['Signal'] = np.where(df['SMA_Short'] > df['SMA_Long'], 1.0, 0.0)
        df['Position'] = df['Signal'].diff()
        
        buy_signals = df[df['Position'] == 1]
        sell_signals = df[df['Position'] == -1]
        
    elif strategy == "RSI":
        # Calculate RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Signal generation for RSI (Crosses below oversold = Buy, Crosses above overbought = Sell)
        df['Buy_Signal'] = (df['RSI'] < rsi_oversold) & (df['RSI'].shift(1) >= rsi_oversold)
        df['Sell_Signal'] = (df['RSI'] > rsi_overbought) & (df['RSI'].shift(1) <= rsi_overbought)
        
        buy_signals = df[df['Buy_Signal']]
        sell_signals = df[df['Sell_Signal']]
        
    elif strategy == "Bollinger Bands":
        df['SMA'] = df['Close'].rolling(window=bb_window).mean()
        df['Std'] = df['Close'].rolling(window=bb_window).std()
        df['Upper'] = df['SMA'] + (bb_std * df['Std'])
        df['Lower'] = df['SMA'] - (bb_std * df['Std'])
        
        # Crosses below lower band = Buy, Crosses above upper band = Sell
        df['Buy_Signal'] = (df['Close'] < df['Lower']) & (df['Close'].shift(1) >= df['Lower'].shift(1))
        df['Sell_Signal'] = (df['Close'] > df['Upper']) & (df['Close'].shift(1) <= df['Upper'].shift(1))
        
        buy_signals = df[df['Buy_Signal']]
        sell_signals = df[df['Sell_Signal']]

    # --- HISTORICAL PERFORMANCE CHECK ---
    total_buy_signals = len(buy_signals)
    profitable_signals = 0
    signals_checked = 0
    
    for i in range(total_buy_signals):
        buy_date = buy_signals.index[i]
        buy_idx = df.index.get_loc(buy_date)
        # Check what the price did in the 5 days following each buy signal
        if buy_idx + 5 < len(df):
            price_at_buy = df['Close'].iloc[buy_idx]
            price_5_days_later = df['Close'].iloc[buy_idx + 5]
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
    
    # --- CHART GENERATION ---
    fig = go.Figure()

    # Plot Close Price
    fig.add_trace(go.Scatter(
        x=df.index, 
        y=df['Close'], 
        mode='lines', 
        name='Close Price',
        line=dict(color='#1f77b4', width=2)
    ))

    # Plot Strategy Specific Indicators on the main chart
    if strategy == "MA Crossover":
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_Short'], mode='lines', name=f'{ma_short}-Day SMA', line=dict(color='#ff7f0e', width=1.5)))
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_Long'], mode='lines', name=f'{ma_long}-Day SMA', line=dict(color='#9467bd', width=1.5)))
    elif strategy == "Bollinger Bands":
        fig.add_trace(go.Scatter(x=df.index, y=df['Upper'], mode='lines', name='Upper Band', line=dict(color='rgba(255, 0, 0, 0.5)', width=1, dash='dash')))
        fig.add_trace(go.Scatter(x=df.index, y=df['Lower'], mode='lines', name='Lower Band', line=dict(color='rgba(0, 128, 0, 0.5)', width=1, dash='dash'), fill='tonexty', fillcolor='rgba(128, 128, 128, 0.1)'))
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA'], mode='lines', name='SMA', line=dict(color='#ff7f0e', width=1.5)))

    # Y-coordinate for signal markers
    if strategy == "MA Crossover":
        buy_y = buy_signals['SMA_Short']
        sell_y = sell_signals['SMA_Short']
    elif strategy == "Bollinger Bands":
        buy_y = buy_signals['Lower']
        sell_y = sell_signals['Upper']
    elif strategy == "RSI":
        # For RSI, the signals happen on the price chart, we'll mark the Close price
        buy_y = buy_signals['Close']
        sell_y = sell_signals['Close']

    # Plot Buy Signals
    fig.add_trace(go.Scatter(
        x=buy_signals.index,
        y=buy_y, 
        mode='markers',
        name='Buy Signal',
        marker=dict(symbol='triangle-up', color='green', size=14, line=dict(width=1, color='darkgreen'))
    ))

    # Plot Sell Signals
    fig.add_trace(go.Scatter(
        x=sell_signals.index,
        y=sell_y, 
        mode='markers',
        name='Sell Signal',
        marker=dict(symbol='triangle-down', color='red', size=14, line=dict(width=1, color='darkred'))
    ))

    fig.update_layout(
        title=subtitle,
        xaxis_title='Date',
        yaxis_title='Price (INR)' if '.NS' in ticker else 'Price',
        template='plotly_white',
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=50, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Optional: Plot RSI in a separate chart below
    if strategy == "RSI":
        st.markdown("### Relative Strength Index (RSI)")
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], mode='lines', name='RSI', line=dict(color='purple')))
        fig_rsi.add_hline(y=rsi_overbought, line_dash="dash", line_color="red", annotation_text="Overbought")
        fig_rsi.add_hline(y=rsi_oversold, line_dash="dash", line_color="green", annotation_text="Oversold")
        
        fig_rsi.update_layout(
            height=300,
            template='plotly_white',
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig_rsi, use_container_width=True)
