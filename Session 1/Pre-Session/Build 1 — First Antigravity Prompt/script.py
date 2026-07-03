import pandas as pd
import yfinance as yf

# Fetch the last 5 days of daily OHLC data for RELIANCE.NS
ticker = "RELIANCE.NS"
print(f"Fetching last 5 days of daily OHLC data for {ticker}...")
df = yf.download(ticker, period="5d", interval="1d", progress=False)

# Flatten columns if MultiIndex is returned (common in recent yfinance versions)
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.droplevel(1)

# Print headers for the table
print(f"\n{'Date':<12} | {'Open':<10} | {'High':<10} | {'Low':<10} | {'Close':<10}")
print("-" * 62)

# Print rows of daily data
for date, row in df.iterrows():
    date_str = date.strftime('%Y-%m-%d')
    open_val = float(row['Open'])
    high_val = float(row['High'])
    low_val = float(row['Low'])
    close_val = float(row['Close'])
    
    print(f"{date_str:<12} | {open_val:<10.2f} | {high_val:<10.2f} | {low_val:<10.2f} | {close_val:<10.2f}")
