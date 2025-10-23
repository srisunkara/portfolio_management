# pip install yahooquery

from yahooquery import Ticker

asset_profile = "asset_profile"
financial_data = "financial_data"
key_stats = "key_stats"
price = "price"
summary_detail = "summary_detail"


def populate_data(in_dict, new_value):
    if in_dict is None:
        return new_value
    else:
        in_dict.update(new_value)
        return in_dict

# define function to take a list of tickers and type of data needed. Once received, split the list into 50 at a time and request data.
# After all data is received, combine the results into a single dictionary, for the type of data requested.
# example, if asset profile data is needed, user will send 'asset_profile' as the data type.
def get_security_data(tickers_list, split_size:int = 50):
    # assert that the data type is valid
    # assert data_type in [asset_profile, financial_data, key_stats, price, summary_detail]

    data = dict.fromkeys([asset_profile, financial_data, key_stats, price, summary_detail], None)
    # store data in a dictionary of lists for each data type requested
    for i in range(0, len(tickers_list), split_size):
        ticker_list = tickers_list[i:i+split_size]
        ticker_data = Ticker(ticker_list, asynchronous=True)

        data['asset_profile'] = populate_data(data['asset_profile'], ticker_data.asset_profile)
        data['financial_data'] = populate_data(data['financial_data'], ticker_data.financial_data)
        data['key_stats'] = populate_data(data['key_stats'], ticker_data.key_stats)
        data['price'] = populate_data(data['price'], ticker_data.price)
        data['summary_detail'] = populate_data(data['summary_detail'], ticker_data.summary_detail)

    return data


if __name__ == "__main__":
    # tickers = Ticker(["AAPL", "MSFT", "GOOGL"], asynchronous=True)
    # data = {
    #     "profile": tickers.asset_profile,
    #     "financials": tickers.financial_data,
    #     "summary": tickers.summary_detail
    # }
    # print(data)

    tickers = ["AAPL", "MSFT", "GOOGL"]
    data = get_security_data(tickers, 2)
    print(data)

