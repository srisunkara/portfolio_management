import yfinance as yf

ticker = yf.Ticker("AAPL")

# Get daily historical price data
daily_data = ticker.history(period="1d")
print(daily_data.head())

# Get issue details (e.g., dividends and splits)
actions = ticker.actions
print(actions.head())

# Get company fundamental info (e.g., market cap, industry)
info = ticker.info['longBusinessSummary']
print(f"\nBusiness Summary:\n{info[:200]}...") # Print a snippet
