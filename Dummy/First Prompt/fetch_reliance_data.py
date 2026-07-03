import yfinance as yf

# Define the stock symbol
symbol = "RELIANCE.NS"
print(f"Fetching the last 5 days of data for {symbol}...\n")
print("Hello")

# Fetch historical market data using the Ticker object
stock = yf.Ticker(symbol)
history = stock.history(period="6d")

# Print the table header
print(f"{'Date':<12} | {'Open':<10} | {'High':<10} | {'Low':<10} | {'Close':<10}")
print("-" * 62)

# Iterate over the rows and print formatted data
for date, row in history.iterrows():
    # Format the date as a simple string
    date_str = date.strftime('%Y-%m-%d')
    
    # Extract the OHLC prices
    open_price = row['Open']
    high_price = row['High']
    low_price = row['Low']
    close_price = row['Close']
    
    # Print each row with aligned columns and 2 decimal places
    print(f"{date_str:<12} | {open_price:<10.2f} | {high_price:<10.2f} | {low_price:<10.2f} | {close_price:<10.2f}")
