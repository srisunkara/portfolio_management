import yfinance as yf
import pandas as pd
from typing import List, Dict, Any


def get_historical_data_list(
        tickers: List[str],
        start_date: str,
        end_date: str,
        interval: str = "1d"
) -> list[Any] | tuple[Any, list[str]]:
    """
    Downloads historical stock price data for multiple tickers and a date range
    from Yahoo Finance and returns the result as a flat list of dictionaries.

    The list is ordered by Date, then by Ticker.

    Args:
        tickers: A list of stock ticker symbols (e.g., ['AAPL', 'MSFT']).
        start_date: The start date in 'YYYY-MM-DD' format.
        end_date: The end date in 'YYYY-MM-DD' format (exclusive).
        interval: Data frequency ('1d' for daily, '1wk' for weekly, etc.).

    Returns:
        A list of dictionaries, where each dictionary represents one day's
        data for one ticker. Returns an empty list on failure.
    """
    print(f"--- Downloading data for {len(tickers)} tickers from {start_date} to {end_date} ---")

    try:
        # 1. Bulk Download Data
        # group_by='ticker' ensures the Ticker symbol is the top level in the columns
        df_multi = yf.download(
            tickers=tickers,
            start=start_date,
            end=end_date,
            interval=interval,
            group_by='ticker',
            progress=False  # Suppress download messages for cleaner output
        )

        # Check if the dataframe is empty
        if df_multi.empty:
            print("No data retrieved. Check ticker symbols or date range.")
            return [], []

        # 2. Flatten the MultiIndex DataFrame (Date and Ticker to columns)
        # Stack the first level of the column MultiIndex (the Ticker) into a row index
        df_flat = df_multi.stack(level=0)

        # The index is now (Date, Ticker). Convert these index levels back to columns.
        df_flat = df_flat.rename_axis(['Date', 'Ticker']).reset_index()

        # 3. Rename columns for clarity (yfinance uses spaces, which is often undesirable)
        # Old: ['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Adj_Close', 'Volume']
        # New:
        columns = ['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']
        """
            Sample data for df_multi:
            df_multi = {DataFrame} [('ZS', 'Open'), ('ZS', 'High'), ('ZS', 'Low'), ('ZS', 'Close'), ('ZS', 'Volume'), ('NVDA', 'Open'), ('NVDA', 'High'), ('NVDA', 'Low'), ('NVDA', 'Close'), ('NVDA', 'Volume'), ('MSFT', 'Open'), ('MSFT', 'High'), ('MSFT', 'Low'), ('MSFT', 'Close'), ('MSFT', 
             AAPL = {DataFrame} ['Open', 'High', 'Low', 'Close', 'Volume'] [Date                                                                ] [2025-10-01  255.039993  258.790009  254.929993  255.449997  48713900] [2025-10-02  256.579987  258.179993  254.149994  257.130005  42630200] [2025-10-03  254.669998  259.239990  253.949997  258.019989  49155600]
             MSFT = {DataFrame} ['Open', 'High', 'Low', 'Close', 'Volume'] [Date                                                                ] [2025-10-01  514.799988  520.510010  511.690002  519.710022  22632300] [2025-10-02  517.640015  521.599976  510.679993  515.739990  21222900] [2025-10-03  517.099976  520.489990  515.000000  517.349976  15112300]
             NVDA = {DataFrame} ['Open', 'High', 'Low', 'Close', 'Volume'] [Date                                                                 ] [2025-10-01  185.240005  188.139999  183.899994  187.240005  173844900] [2025-10-02  189.600006  191.050003  188.059998  188.889999  136805800] [2025-10-03  189.190002  190.360001  185.380005  187.619995  137596900]
        """
        # check if Adj Close is in df_multi (a dataframe) based on the first security in the list
        # column_tuple = (tickers[0] + "/" + 'Adj Close')
        # if column_tuple in df_multi.columns:
        #     columns.append('Adj Close')

        # df_flat.columns = columns


        # 4. Convert the DataFrame to the desired list of dictionaries
        data_list = df_flat.to_dict('records')

        print("Download successful and data restructured.")
        return data_list, df_flat.columns

    except Exception as e:
        print(f"An error occurred during data retrieval: {e}")
        return []


# --- Example Usage ---
if __name__ == '__main__':

    ticker = yf.Ticker("AAPL")

    # Get daily historical price data
    daily_data = ticker.history(period="1d")
    print(daily_data.head())

    # Get issue details (e.g., dividends and splits)
    actions = ticker.actions
    print(actions.head())

    # Get company fundamental info (e.g., market cap, industry)
    info = ticker.info['longBusinessSummary']
    print(f"\nBusiness Summary:\n{info[:200]}...")  # Print a snippet

    # Define parameters
    TICKERS_LIST = ['AAPL', 'MSFT', 'TSLA']
    START = '2024-06-01'
    END = '2024-06-15'

    # Call the function
    data, cols = get_historical_data_list(TICKERS_LIST, START, END)

    # Display results
    if data:
        print(cols)
        print("\n--- First 5 records (Ordered by Date, then Ticker) ---")
        for record in data[:5]:
            print(record)

        print(f"\nTotal records retrieved: {len(data)}")
        print(data)

    else:
        print("No data to display.")
