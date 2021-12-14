import requests
import collections
from statistics import mean
from functools import lru_cache
import os
import numpy as np
import pandas as pd
import requests
import math
from scipy.stats import percentileofscore as score
import xlsxwriter
from datetime import datetime
from dateutil.relativedelta import relativedelta
import glob

#the purpose of this file is to fill the transactions table as if
#the website had already been running for 6 months. It uses the
#algorithm almost exactly like generateBacktestData.py however instead
#of making a report, it posts to the testuser's transactions table
#it is NOT recommended that you run this file, as it was only
#meant to fill the teststuser's transactions table, and running it will only fill
#it more with bad dates, since it uses stock history csv files
#but if you really must run this, you can run this with: python3 six_mo_hist.py


G_stock = pd.read_csv('GOOGL.csv')
F_stock = pd.read_csv('FB.csv')
M_stock = pd.read_csv('MSFT.csv')
T_stock = pd.read_csv('TSLA.csv')

csv_files = [G_stock, F_stock, M_stock, T_stock]

#liquid cash is money currently not in a stock, cash_in_stock is money in a stock, and total is those 2 added
liquid_cash = 10000
total_money = 10000
stockChanges = {'GOOGL' : 0, 'FB': 0, 'MSFT': 0, 'TSLA': 0}
cash_in_stock = 0


#this keeps track of the name, since it's hard to match the csv files with their stock name
#when doing them all simutaneously
i = 0

#we start a 1100 because the files go to about 1200 and we only want about 6 months
for day in range(1100, len(G_stock)):

    #at the beginning of the day, prices are different, so i must reset
    #cash_in_stock

    cash_in_stock = ( (G_stock.loc[day, 'Close'] * stockChanges['GOOGL']) +
                      (F_stock.loc[day, 'Close'] * stockChanges['FB']) +  
                       (M_stock.loc[day, 'Close'] * stockChanges['MSFT']) +
                    (T_stock.loc[day, 'Close'] * stockChanges['TSLA'])      )

    total_money = cash_in_stock + liquid_cash

    hqm_columns = [
    'Ticker',
    'Price',
    'One-Year Price Return',
    'Six-Month Price Return',
    'Three-Month Price Return',
    'One-Month Price Return',
    'Reason',
    'Decision'
    ]

    #every "day", the stock will go into one of these dataframes
    grow_dataframe = pd.DataFrame(columns = hqm_columns)
    fall_dataframe = pd.DataFrame(columns = hqm_columns)
    stable_dataframe = pd.DataFrame(columns = hqm_columns)

    #here is where first each stock gets placed into one of the three dataframes
    i = 0
    for A_stock_xl in csv_files:
        if i == 0:
            ticker = 'GOOGL'
        elif i == 1:
            ticker = 'FB'
        elif i == 2:
            ticker = 'MSFT'
        else:
            ticker = 'TSLA'
        
        i += 1
       
        #this is an estimate, since stock market is only open on weekdays, so 52 of those groups of 5 should be a year ago
        a_year_ago = day - (52 * 5)
        six_months_ago = day - (26 * 5)
        three_months_ago = day - (13 * 5)
        one_month_ago = day - (4 * 5)


        #part of the algorithm requires the percentage change of the stock at certain points of time, 
        #the percentage change is calculated here
        #it's ( (new value - orig value / (orig value) )  * 100
        yr1change = ( (A_stock_xl.loc[day, 'Close'] - A_stock_xl.loc[a_year_ago, 'Close']) / A_stock_xl.loc[a_year_ago, 'Close'] ) * 100
        mo6change = ( (A_stock_xl.loc[day, 'Close'] - A_stock_xl.loc[six_months_ago, 'Close']) / A_stock_xl.loc[six_months_ago, 'Close'] ) * 100
        mo3change = ( (A_stock_xl.loc[day, 'Close'] - A_stock_xl.loc[three_months_ago, 'Close']) / A_stock_xl.loc[three_months_ago, 'Close'] ) * 100
        mo1change = ( (A_stock_xl.loc[day, 'Close'] - A_stock_xl.loc[one_month_ago, 'Close']) / A_stock_xl.loc[one_month_ago, 'Close'] ) * 100

        #first part of the algortihm is to see how it's been doing the past 3 days, if been going down
        # put into fall dataframe, if it's been growing, put into grow dataframe, if neither, put into stable
        if( (A_stock_xl.loc[day - 2, 'Close'] - A_stock_xl.loc[day - 1, 'Close'] ) > 0
                and (A_stock_xl.loc[day - 1, 'Close'] - A_stock_xl.loc[day - 0, 'Close'] ) > 0):
        
            fall_dataframe = fall_dataframe.append( #we then stick price, name, and change percentages into the dataframe
                pd.Series(
                [
                    ticker, #'Ticker'
                    A_stock_xl.loc[day, 'Close'], #'today's Price'
                    yr1change,
                    mo6change,
                    mo3change,
                    mo1change,
                    'N/A',
                    'N/A'
                ],
                    index = hqm_columns),
                    ignore_index = True
            )
        elif( (A_stock_xl.loc[day - 2, 'Close'] - A_stock_xl.loc[day - 1, 'Close'] ) < 0
                and (A_stock_xl.loc[day - 1, 'Close'] - A_stock_xl.loc[day, 'Close'] ) < 0):

            grow_dataframe = grow_dataframe.append( #we then stick price, name, and change percentages into the dataframe
                pd.Series(
                [
                    ticker, #'Ticker'
                    A_stock_xl.loc[day, 'Close'], #'today's Price'
                    yr1change,
                    mo6change,
                    mo3change,
                    mo1change,
                    'N/A',
                    'N/A'
                ],
                    index = hqm_columns),
                    ignore_index = True
            )
        else:
            stable_dataframe = stable_dataframe.append( #we then stick price, name, and change percentages into the dataframe
                pd.Series(
                [
                    ticker, #'Ticker'
                    A_stock_xl.loc[day, 'Close'], #'today's Price'
                    yr1change,
                    mo6change,
                    mo3change,
                    mo1change,
                    'N/A', 
                    'N/A'
                ],
                    index = hqm_columns),
                    ignore_index = True
            )

        #now that the stock is in one of the three dataframes, we judge whether to buy or sell or hold
    

    #if it's falling, we just want to sell everything, as well as update the values and add to the report dataframe
    for row in fall_dataframe.index:
        orig_stock = stockChanges[ fall_dataframe.loc[row, 'Ticker'] ] #okay, i'm only updating 1 stock
        stockChanges[ fall_dataframe.loc[row, 'Ticker'] ] = 0
        cash_in_stock -= float(orig_stock) * fall_dataframe.loc[row, 'Price']
        liquid_cash +=  float(orig_stock) * fall_dataframe.loc[row, 'Price']
        total_money = liquid_cash + cash_in_stock

        action = "SELL"
        given_reason =  f"Sold all {orig_stock} of stock {fall_dataframe.loc[row, 'Ticker']} at {fall_dataframe.loc[row, 'Price']} because it's been falling for 3 consecutive days. New total is {total_money}"
        
        #these have alternate values if nothing was actually bought or sold 
        if orig_stock == 0:
            action = "HOLD"
            given_reason = f"Didn't do anything for {fall_dataframe.loc[row, 'Ticker']} since it's falling and we have own none of its stocks"
        
        #for every trade, update the transaction table
        url = "http://localhost:8000/transactions/"
        payload=f"email=testuser%40gmail.com&ticker={fall_dataframe.loc[row,'Ticker']}&quantity={orig_stock}&action={action}&dateTime={datetime.strptime(A_stock_xl.loc[day, 'Date'], '%Y-%m-%d')}&reason={given_reason}&price={fall_dataframe.loc[row, 'Price']}"
        headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        print("print to transactiopns")
        print(response.text)
       

    #now we decide the fate of the stable stocks
    #whether or not they have an overall positive percent changes will help decide whether we sell half or all
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

    #we were able to see it's long term growth, so now we decide how much we sell
    for row in stable_dataframe.index:
        if stable_dataframe.loc[row, 'Decision'] == 1:
            orig_stock = int( stockChanges[stable_dataframe.loc[row, 'Ticker']] )
            stock_in_half = math.floor( orig_stock / 2  )

            #a special exception must be made if there is only 1 stock left
            if orig_stock == 1:
                stock_in_half = 1
                stockChanges[ stable_dataframe.loc[row, 'Ticker'] ] = 0
                cash_in_stock -= stable_dataframe.loc[row, 'Price']
                liquid_cash += stable_dataframe.loc[row, 'Price']
            else:
                stockChanges[ stable_dataframe.loc[row, 'Ticker'] ] -= stock_in_half
                cash_in_stock -= ( float( stock_in_half) ) * stable_dataframe.loc[row, 'Price']
                liquid_cash +=  ( float(stock_in_half) ) * stable_dataframe.loc[row, 'Price']
            total_money = cash_in_stock + liquid_cash

            action = "SELL"
            given_reason = f"Sold half, {stock_in_half}, of stock {stable_dataframe.loc[row, 'Ticker']} at {stable_dataframe.loc[row, 'Price']} because it's platued for the past 3 days and it has an okay recent history. New total is {total_money}"

            if orig_stock == 0:
                action = "HOLD"
                given_reason = f"Didn't do anything for {stable_dataframe.loc[row, 'Ticker']} since it's stable and has a decent history and we have own none of its stocks"

            #put in transactions
            url = "http://localhost:8000/transactions/"
            payload=f"email=testuser%40gmail.com&ticker={stable_dataframe.loc[row, 'Ticker']}&quantity={stock_in_half}&action={action}&dateTime={datetime.strptime(A_stock_xl.loc[day, 'Date'], '%Y-%m-%d')}&reason={given_reason}&price={stable_dataframe.loc[row, 'Price']}"
            headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
            }

            response = requests.request("POST", url, headers=headers, data=payload)
            print("print to transactiopns")
            print(response.text)
            #if we're in this else statement, it's becasue the percentage changes were
            # negative overall, so we will sell everything and update the variables
        else:
            orig_stock = int( stockChanges[stable_dataframe.loc[row, 'Ticker']] )
            stockChanges[ stable_dataframe.loc[row, 'Ticker'] ] = 0
            cash_in_stock -= orig_stock * stable_dataframe.loc[row, 'Price']
            liquid_cash +=  float( orig_stock) * stable_dataframe.loc[row, 'Price']
            total_money = liquid_cash + cash_in_stock

            given_reason = f"Sold all {orig_stock}, of stock {stable_dataframe.loc[row, 'Ticker']} at {stable_dataframe.loc[row, 'Price']} because it's platued for the past 3 days, but it has a poor recent history. New total is {total_money}"
            action = "SELL"

            if orig_stock == 0:
                action = "HOLD"
                given_reason = f"Didn't do anything for {stable_dataframe.loc[row, 'Ticker']} since it's stable and has a bad history and we have own none of its stocks"

            url = "http://localhost:8000/transactions/"
            payload=f"email=testuser%40gmail.com&ticker={stable_dataframe.loc[row, 'Ticker']}&quantity={orig_stock}&action={action}&dateTime={datetime.strptime(A_stock_xl.loc[day, 'Date'], '%Y-%m-%d')}&reason={given_reason}&price={stable_dataframe.loc[row, 'Price']}"
            headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
            }

            response = requests.request("POST", url, headers=headers, data=payload)
            print("print to transactiopns")
            print(response.text)
    
    #if it's growing for the past 3 days, we want to buy as much as possible
    #we must check these first to prevent divide by zero errors
    if(len(grow_dataframe.index) != 0 and liquid_cash != 0):
        divvied_up_cash = liquid_cash / len(grow_dataframe.index)
        for row in grow_dataframe.index:
            orig_stock = int( stockChanges[grow_dataframe.loc[row, 'Ticker']] )
            new_amount_to_buy = math.floor(divvied_up_cash/grow_dataframe.loc[row, 'Price'])
            liquid_cash -= ( new_amount_to_buy * grow_dataframe.loc[row, 'Price'])
            stockChanges[grow_dataframe.loc[row, 'Ticker']] = orig_stock + new_amount_to_buy
            cash_in_stock += ( new_amount_to_buy * grow_dataframe.loc[row, 'Price'] )
            total_money = liquid_cash + cash_in_stock

            given_reason = f"Bought {new_amount_to_buy} of {grow_dataframe.loc[row, 'Ticker']} for {grow_dataframe.loc[row, 'Price']} because it's been growing for the past 3 days. New total is {total_money}"
            action = "BUY"

            if new_amount_to_buy == 0:
                action = "HOLD"
                given_reason = f"Didn't do buy any of {grow_dataframe.loc[row, 'Ticker']} even though it's growing because we don't currently have the money"



            url = "http://localhost:8000/transactions/"
            payload=f"email=testuser%40gmail.com&ticker={grow_dataframe.loc[row, 'Ticker']}&quantity={new_amount_to_buy}&action={action}&dateTime={datetime.strptime(A_stock_xl.loc[day, 'Date'], '%Y-%m-%d')}&reason={given_reason}&price={grow_dataframe.loc[row, 'Price']}"
            headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
            }

            response = requests.request("POST", url, headers=headers, data=payload)
            print("print to transactiopns")
            print(response.text)

           
#the print statements here are for the programmer, to make sure everything was successfully updated
print(liquid_cash)
print(total_money)
print(stockChanges)
        


