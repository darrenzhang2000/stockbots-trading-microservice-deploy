import requests
import collections
from statistics import mean
from functools import lru_cache
from dotenv import load_dotenv
import os

load_dotenv()

# Caching api calls to reduce api calls. Will remove when deployed.
# @lru_cache(None)
def cachedAPICall(tickers):
    headers = {
        'accept': 'application/json',
        'X-API-KEY': os.environ['YAHOO_FINANCE_API_KEY'],
    }

    comparisons = ",".join(tickers)

    params = (
        ('comparisons', comparisons),
        ('range', '1wk'),
        ('region', 'US'),
        ('interval', '1d'),
        ('lang', 'en'),
        ('events', 'div,split'),
    )

    response = requests.get('https://yfapi.net/v8/finance/chart/AAPL', headers=headers, params=params)
    return response


class StockAction:
    def __init__(self, ticker, fiveDayAverage, lastBusinessDayClosePrice, action):
        self.ticker = ticker
        self.fiveDayAverage = fiveDayAverage
        self.lastBusinessDayClosePrice = lastBusinessDayClosePrice
        self.action = action

    def __str__(self):
        formatString = "Ticker: {}, fiveDayAverage: {}, lastBusinessDayClosePrice: {}, action: {}"
        return formatString.format(self.ticker, self.fiveDayAverage, self.lastBusinessDayClosePrice, self.action)


def makeStockDecision(avgPrice, prevPrice):
    if prevPrice >= 1.05 * avgPrice:
        return "sell"
    elif prevPrice <= .95 * avgPrice:
        return "buy"
    else:
        return "hold"


def stockActions(tickers):
    stockActionHt = {}  # {'GOOGL': 'buy', 'APPL': 'hold'}

    response = cachedAPICall(tickers)
    if response.status_code == 200:
        result = response.json()['chart']['result'][0]
        timestamps = result['timestamp']
        comparisons = result['comparisons']

        for stockInfo in comparisons:
            ticker = stockInfo['symbol']
            fiveDayClosePrices = list(filter(lambda p: p, stockInfo['close']))
            fiveDayAverage = round(mean(fiveDayClosePrices), 2)
            lastBusinessDayClosePrice = round(fiveDayClosePrices[-1], 2)
            action = makeStockDecision(fiveDayAverage, lastBusinessDayClosePrice)
            stockActionHt[ticker] = StockAction(ticker, fiveDayAverage, lastBusinessDayClosePrice, action)

    actionHt = { ticker: stockAction.action for ticker, stockAction in stockActionHt.items() }
    return actionHt


