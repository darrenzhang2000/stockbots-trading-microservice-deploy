import requests
import collections
from statistics import mean
from functools import lru_cache
import os
import numpy as np
import pandas as pd
import requests
import math
from requests import api
from scipy.stats import percentileofscore as score
from datetime import date
from dotenv import load_dotenv

load_dotenv()

IEX_API_KEY = os.environ['IEX_API_KEY']
BACKEND_API = os.environ['BACKEND_API']

#import xlsxwriter

#load_dotenv()

# Caching api calls to reduce api calls. Will remove when deployed.
# @lru_cache(None)
def cachedAPICall(tickers):
    headers = {
        'accept': 'application/json',
        'X-API-KEY': "Ehmj9CLOzr9TB4gkqCiHp2u8HoZ2JiKC9qVRNeva", #"YvMydmuOKM2ObYZhAU5wtHQnmO3Bqan6DhnjsJn5", 
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

# the purpose of this function is to look at a user's saved stocks and decide whether to buy or sell them and updates the database
#it is run automatically on a daily basis for each user to make that days' trades

def stockActions(tickers, email):
    if not tickers:
        return
    
    #this is for backend posts, some can't have a @, so it's replaced with %40
    forty_email = email.replace('@', '%40') 

    #--summon stocks from database and put in dictionary--
    headers = { #this is to summon the data from the database, response will have a .json() that I can summon to get data
            'accept': 'application/json',
    }
    params = {
        'email': email
    }
    database = requests.get(f"{BACKEND_API}/ownedStocks/",
                            headers=headers, params=params)

    if 'ownedStocks' not in database.json():
        return
    stockChanges = {} #this will save the name and number of the user's stocks in a hash table
    for i in range( len(database.json()['ownedStocks']) ):
        stockChanges[ database.json()['ownedStocks'][i]['ticker'] ] = database.json()['ownedStocks'][i]['quantity']['$numberDecimal']
   
    #/--end of summon stocks from database and put in dictionary--

    #--grab the spending money and set up money variables--
    url = f"{BACKEND_API}/portfolios?email={email}"
    payload={}
    headers = {
    }

    bank = requests.request("GET", url, headers=headers, data=payload)
    
    
    #liquid cash is money currently not in a stock, cash_in_stock is money in a stock, and total is those 2 added
    #original liquid cash is needed to find the money gained or lost that day later on when we post
    cash_in_stock = 0
    total_money = 0
    original_liquid_cash =float( bank.json()['portfolios'][0]['spendingPower']['$numberDecimal'] )
    liquid_cash = original_liquid_cash
  
    #/--end of grab the spending money and set up money variables--


    #--grab the prices and multiply them by the stocks to get cash_in_stock and total_money--
    for key in stockChanges:
        api_find_total =f'https://cloud.iexapis.com/stable/stock/{key}/quote?token={IEX_API_KEY}'
        stock_price = requests.get(api_find_total).json()
        cash_in_stock += float(stock_price['latestPrice']) * int(stockChanges[key])

    total_money = cash_in_stock + liquid_cash
    
    #/--end of grab the prices and multiply them by the stocks to get cash_in_stock and total_money--

    #--make fall, grow and stable databases--
    hqm_columns = [ 
    'Ticker',
    'Price',
    'One-Year Price Return',
    'Six-Month Price Return',
    'Three-Month Price Return',
    'One-Month Price Return',
    'Reason',
    'Decision',
    ]

    #depending on a stocks recent performance, it will end up in one of these 3 stocks
    grow_dataframe = pd.DataFrame(columns = hqm_columns)
    fall_dataframe = pd.DataFrame(columns = hqm_columns)
    stable_dataframe = pd.DataFrame(columns = hqm_columns)
    #/--end of make fall, grow and stable databases--


    #--transactions get--
    url = f"{BACKEND_API}/transactions/?email={email}"

    payload=f"email={forty_email}&ticker=GOOGL&quantity=10&action=buy&reason=because%20.."
    headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    
    #/--end of transactions get--

    #setup over

    response = cachedAPICall(tickers)
    
    if response.status_code == 200:
        result = response.json()['chart']['result'][0]
        timestamps = result['timestamp']
        comparisons = result['comparisons']

        #--grab stock info, find it's current price, change percent, and recent price shifts, and fill grow, fall, and stable dataframes--
        for stockInfo in comparisons:
            
            ticker = stockInfo['symbol'] 
            api_call_change = f'https://cloud.iexapis.com/stable/stock/{ticker}/stats/?token={IEX_API_KEY}'
            api_call_price =f'https://cloud.iexapis.com/stable/stock/{ticker}/quote?token={IEX_API_KEY}'
            
            changes = requests.get(api_call_change).json()
            price = requests.get(api_call_price).json()
    
            #if it's been falling in price for the last 3 days, add to fall dataframe
            if( (stockInfo['close'][2] - stockInfo['close'][1] > 0)
               and (stockInfo['close'][1] - stockInfo['close'][0] > 0) ):

                fall_dataframe = fall_dataframe.append( #we then stick price, name, and change percentages into the dataframe
                    pd.Series(
                    [
                        ticker, #'Ticker'
                        price['latestPrice'], #'today's Price'
                        changes['year1ChangePercent'],
                        changes['month6ChangePercent'],
                        changes['month3ChangePercent'],
                        changes['month1ChangePercent'],
                        'N/A',
                        'N/A'
                    ],
                        index = hqm_columns),
                        ignore_index = True
                )
            #if it's growing in price, add to grow datframe
            elif( (stockInfo['close'][2] - stockInfo['close'][1] < 0)
               and (stockInfo['close'][1] - stockInfo['close'][0] < 0) ):

                grow_dataframe = grow_dataframe.append( 
                    pd.Series(
                    [
                        ticker, #'Ticker'
                        price['latestPrice'], #'today's Price'
                        changes['year1ChangePercent'],
                        changes['month6ChangePercent'],
                        changes['month3ChangePercent'],
                        changes['month1ChangePercent'],
                        'N/A',
                        'N/A'
                    ],
                        index = hqm_columns),
                        ignore_index = True
                )
            #if it's up and down
            else:

                stable_dataframe = stable_dataframe.append( 
                    pd.Series(
                    [
                        ticker, #'Ticker'
                        price['latestPrice'], #'today's Price'
                        changes['year1ChangePercent'],
                        changes['month6ChangePercent'],
                        changes['month3ChangePercent'],
                        changes['month1ChangePercent'],
                        'N/A',
                        'N/A'
                    ],
                        index = hqm_columns),
                        ignore_index = True
                )

        #/--grab stock info, find it's current price, change percent, and recent price shifts, and fill grow, fall, and stable--
 
        #--since it's falling, sell all and update variables--
        for row in fall_dataframe.index:
            orig_stock = int( stockChanges[fall_dataframe.loc[row, 'Ticker']] ) #this searches stockChanges for the amount
            stockChanges[ fall_dataframe.loc[row, 'Ticker'] ] = orig_stock * -1 #replace the total amount with the amount bought or sold (psoitive for bought, negative for sold)
            liquid_cash +=  ( float( orig_stock) ) * fall_dataframe.loc[row, 'Price']
            cash_in_stock -=  ( float( orig_stock) ) * fall_dataframe.loc[row, 'Price']
            total_money = liquid_cash

            given_reason =  f"Sold all {orig_stock} of stock {fall_dataframe.loc[row, 'Ticker']} at {fall_dataframe.loc[row, 'Price']} because it's been falling for 3 consecutive days. New total is {total_money}"
            action = "SELL"
            if orig_stock == 0:
                action = "HOLD"
                given_reason = f"Didn't do anything for {fall_dataframe.loc[row, 'Ticker']} since it's falling and we own none of its stocks"
            
            #for every trade, update the transaction table
            url = f"{BACKEND_API}/transactions/"
            payload=f"email={forty_email}&ticker={fall_dataframe.loc[row,'Ticker']}&quantity={orig_stock}&action={action}&dateTime={date.today()}&reason={given_reason}&price={fall_dataframe.loc[row, 'Price']}"
            headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
            }
            response = requests.request("POST", url, headers=headers, data=payload)
           
        #/--since it's falling, sell all--

        #--since it's stable, sell all if the total price returns are negative, only sell half if it's positve. Since it's had a good history, it may not drop--
        for row in stable_dataframe.index:
            decision = 0 #decision will help decide the fate of the stock
            avg_past = (stable_dataframe.loc[row, 'One-Year Price Return'] + 
                       stable_dataframe.loc[row, 'Six-Month Price Return']  +
                       stable_dataframe.loc[row, 'Three-Month Price Return']  +
                       stable_dataframe.loc[row, 'One-Month Price Return']  )
            if(avg_past < 0):
                decision = decision - 1
            elif(avg_past > 0):
                decision = decision + 1
            else: #just in case it adds up to 0
                decision = decision + 0

            stable_dataframe.loc[row, 'Decision'] = decision

        #now we go the decision for each stable stock made, we go to either sell half or all
        for row in stable_dataframe.index: 
            if stable_dataframe.loc[row, 'Decision'] == 1:
                orig_stock = int( stockChanges[stable_dataframe.loc[row, 'Ticker']] )
                stock_in_half = math.floor( orig_stock / 2  )
                #there's a special case when if there's only one left
                if orig_stock == 1:
                    stock_in_half = 1
                    stockChanges[ stable_dataframe.loc[row, 'Ticker'] ] = -1 #in this case we sell the one
                    liquid_cash += stable_dataframe.loc[row, 'Price']
                    cash_in_stock -= stable_dataframe.loc[row, 'Price']
                else:
                    stockChanges[ stable_dataframe.loc[row, 'Ticker'] ] =  (orig_stock - stock_in_half) * -1
                    liquid_cash +=  ( float( stock_in_half) ) * stable_dataframe.loc[row, 'Price']
                    cash_in_stock -= ( float( stock_in_half) ) * stable_dataframe.loc[row, 'Price']
                total_money = liquid_cash + cash_in_stock

                given_reason = f"Sold half, {stock_in_half}, of stock {stable_dataframe.loc[row, 'Ticker']} at {stable_dataframe.loc[row, 'Price']} because it's platued for the past 3 days and it has an okay recent history. New total is {total_money}"
                action = "SELL"
                if orig_stock == 0:
                    action = "HOLD"
                    given_reason = f"Didn't do anything for {stable_dataframe.loc[row, 'Ticker']} since it's stable and has a decent history and we have own none of its stocks"

                #put in transactions
                url = f"{BACKEND_API}/transactions/"
                payload=f"email={forty_email}&ticker={stable_dataframe.loc[row, 'Ticker']}&quantity={stock_in_half}&action={action}&dateTime={date.today()}&reason={given_reason}&price={stable_dataframe.loc[row, 'Price']}"
                headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
                }

                response = requests.request("POST", url, headers=headers, data=payload)
                        
                   
            else: #here we sell all b/c the history isn't too great and it's risky to keep
                orig_stock = int( stockChanges[stable_dataframe.loc[row, 'Ticker']] )
                stockChanges[ stable_dataframe.loc[row, 'Ticker'] ] = orig_stock * -1
                liquid_cash +=  ( float( orig_stock) ) * stable_dataframe.loc[row, 'Price']
                cash_in_stock -= ( float( orig_stock) ) * stable_dataframe.loc[row, 'Price']
                total_money = liquid_cash + cash_in_stock

                given_reason = f"Sold all {orig_stock}, of stock {stable_dataframe.loc[row, 'Ticker']} at {stable_dataframe.loc[row, 'Price']} because it's platued for the past 3 days, but it has a poor recent history. New total is {total_money}"
                action = "SELL"

                if orig_stock == 0:
                    action = "HOLD"
                    given_reason = f"Didn't do anything for {stable_dataframe.loc[row, 'Ticker']} since it's stable and has a bad history and we have own none of its stocks"

                url = f"{BACKEND_API}/transactions/"
                payload=f"email={forty_email}&ticker={stable_dataframe.loc[row, 'Ticker']}&quantity={orig_stock}&action={action}&dateTime={date.today()}&reason={given_reason}&price={stable_dataframe.loc[row, 'Price']}"
                headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
                }

                response = requests.request("POST", url, headers=headers, data=payload)
                
            
        #make divvied up cash to see how much we can buy for each of the growers
        #we need to check these values for divide by 0 errors
        if(len(grow_dataframe.index) != 0 and liquid_cash != 0):
            divvied_up_cash = liquid_cash / len(grow_dataframe.index)

            for row in grow_dataframe.index:
                orig_stock = int( stockChanges[grow_dataframe.loc[row, 'Ticker']] )
                new_amount_to_buy = math.floor(divvied_up_cash/grow_dataframe.loc[i, 'Price'])
                stockChanges[grow_dataframe.loc[row, 'Ticker']] = new_amount_to_buy
                liquid_cash -=  (new_amount_to_buy * grow_dataframe.loc[i, 'Price'])
                cash_in_stock += (new_amount_to_buy * grow_dataframe.loc[i, 'Price'])
                total_money = liquid_cash + cash_in_stock

                given_reason = f"Bought {new_amount_to_buy} of {grow_dataframe.loc[row, 'Ticker']} for {grow_dataframe.loc[row, 'Price']} because it's been growing for the past 3 days. New total is {total_money}"
                action = "BUY"

                if new_amount_to_buy == 0:
                    given_reason = f"Didn't do buy any of {grow_dataframe.loc[row, 'Ticker']} even though it's growing because we don't currently have the money"
                    action = "HOLD"

                url = f"{BACKEND_API}/transactions/"
                payload=f"email={forty_email}&ticker={grow_dataframe.loc[row, 'Ticker']}&quantity={new_amount_to_buy}&action={action}&dateTime={date.today()}&reason={given_reason}&price={grow_dataframe.loc[row, 'Price']}"
                headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
                }

                response = requests.request("POST", url, headers=headers, data=payload)
                

            
        #--update stocks and the amount they changed by back in database--
        url = f"{BACKEND_API}/ownedStocks/purchase"

        for key in stockChanges:
            # Note the values for these calls are adding or subtracting from the total, not replacing it
            # example, if the original value of a stock was 20, and i put in -5, then it would change to 15
            payload=f'email={forty_email}&ticker={key}&purchaseAmt={stockChanges[key]}'
            headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
            }

            response = requests.request("PUT", url, headers=headers, data=payload)
                
        #/--update stocks and the amount they changed by back in database--


        #--we take the cash difference from the original to see how much it has changed and we update it--
        cash_difference = liquid_cash - original_liquid_cash

        url = f"{BACKEND_API}/portfolios/"

        payload=f'email={forty_email}&amount={cash_difference}'
        headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.request("PUT", url, headers=headers, data=payload)
        
        #/--we take the cash difference from the original to see how much it has changed and we update it--

        print("these are the dataframes")
        print(fall_dataframe)
        print(grow_dataframe)
        print(stable_dataframe)
        print(liquid_cash)
        print(cash_difference)
        print(stockChanges)


 
stockActions(['GOOGL', 'TSLA', 'FB', 'MSFT'], 'testuser@gmail.com') #okay, Apple's strange but it works
