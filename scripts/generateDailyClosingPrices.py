'''
Get the S&P 500 stocks

Find the yahoo finance api that gets historical daily data

Make batch calls to this api and write info into csv file
'''

import pandas as pd
import requests
from bs4 import BeautifulSoup as soup


# There are 2 tables on the Wikipedia page
# we want the first table

payload=pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
first_table = payload[0]

df = first_table

df.head()

symbols = df['Symbol'].values.tolist()

print(symbols)

# import urllib.request
# # url = https://query1.finance.yahoo.com/v7/finance/download/GOOGL?period1=1480464000&amp;period2=1638230400&amp;interval=1d&amp;events=history&amp;includeAdjustedClose=true
# url = "https://query1.finance.yahoo.com/v7/finance/download/GOOGL?period1=1480464000&amp;period2=1638230400&amp;interval=1d&amp;events=history&amp;includeAdjustedClose=true"
# # urllib.request.urlretrieve(url, 'csv')

# from selenium import webdriver
# from selenium.webdriver.common.keys import Keys

# driver = webdriver.Firefox()
# driver.get(url)


# for symbol in symbols:
#     html_page = requests.get("https://finance.yahoo.com/quote/{}/history?period1=1480464000&period2=1638230400&interval=1d&filter=history&frequency=1d&includeAdjustedClose=true".format(symbols))
#     soup_page = soup(html_page, "html")
#     soup_page.find_all('a', class_="FL(end) Mt(3px) Cur(p)")
#     soup_page
    

# headers = {
#     'accept': 'application/json',
#     'X-API-KEY': 'Ehmj9CLOzr9TB4gkqCiHp2u8HoZ2JiKC9qVRNeva',
# }

# params = (
#     ('comparisons', 'MSFT,^VIX'),
#     ('range', '1mo'),
#     ('region', 'US'),
#     ('interval', '1d'),
#     ('lang', 'en'),
#     ('events', 'div,split'),
# )

# response = requests.get('https://yfapi.net/v8/finance/chart/AAPL', headers=headers, params=params)

# print(response.data)