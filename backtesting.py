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

#the purpose of this file is to test the algorithm to see how much money it makes on individual stocks
#since the main algorithm (located in both_algos.py in the definition stockActions) mainly works on groups of stocks
#at a time, there may not be enough given money to buy a stock on a particular day that it's growing
#so this runs 20 individual stocks over the course of 3 years using csv files 

#to run this file: python3 backtesting.py

#we want all the excel files in hist file so we get path
path = os.getcwd()
path += "/histdata"
csv_files = glob.glob(os.path.join(path, "*.csv"))

#since some stocks will ultimately lose money and some will gain, we will track the gain and loss of each so we know overall how much we make
overall_gain = 0



#for every csv file, it will run an individual report
#basically for each stock, it will simulate as if the algorithm has run for just that one stock for about 3 years
#so it's as if a user had only had one stock for us to manage, and they let it run for 3 years without change
for current_xl in csv_files:
    A_stock_xl = pd.read_csv(current_xl)

    #when the code is here, that means a new 5 year file will be run, so we resest all these values
    #we only run like 3 years since part of the algorithm requires to go back a year, so if 
    #liquid cash is money currently not in a stock, cash_in_stock is money in a stock, and total is those 2 added
    liquid_cash = 10000
    total_money = 10000
    A_stock_amount = 0
    cash_in_stock = 0

    #this is to help keep an index in the excel file produced
    csv_index = 0

    #this is added to whenever a decision is made for a stock that day
    daily_report_columns = ['ID', 'Date', 'Spending Power', 'Price', 'Quantity', 'Total', 'Report']
    report_dataframe = pd.DataFrame(columns = daily_report_columns)

    #we start at 500 rather than 0 because we can only run like 3 years since part of the algorithm requires to reach back a year for data
    for day in range(500, len(A_stock_xl)):
        
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

        #this is because i have to drop the file location and the .csv from the excel file to have the actual name
        ticker = ( str(current_xl).split("/")[-1] ).replace(".csv", "")

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
                and (A_stock_xl.loc[day - 1, 'Close'] - A_stock_xl.loc[day, 'Close'] ) > 0):
        
            fall_dataframe = fall_dataframe.append(
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
        elif((A_stock_xl.loc[day - 2, 'Close'] - A_stock_xl.loc[day - 1, 'Close'] ) < 0
                and (A_stock_xl.loc[day - 1, 'Close'] - A_stock_xl.loc[day, 'Close'] ) < 0):
    
            grow_dataframe = grow_dataframe.append(
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
            stable_dataframe = stable_dataframe.append( 
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
            orig_stock = A_stock_amount
            A_stock_amount = 0
            cash_in_stock =  0
            liquid_cash +=  float(orig_stock) * fall_dataframe.loc[row, 'Price']
            total_money = liquid_cash + cash_in_stock

            given_reason =  f"Sold all {orig_stock} of stock {fall_dataframe.loc[row, 'Ticker']} at {fall_dataframe.loc[row, 'Price']} because it's been falling for 3 consecutive days. New total is {total_money}"
            action = "SELL"

            #these have alternate values if nothing was actually bought or sold 
            if orig_stock == 0:
                action = "HOLD"
                given_reason = f"Didn't do anything for {fall_dataframe.loc[row, 'Ticker']} since it's falling and we own none of its stocks"
            
            #for every trade, update the report dataframe
            report_dataframe = report_dataframe.append(
                pd.Series(
                [
                    csv_index,
                    A_stock_xl.loc[day, 'Date'],
                    liquid_cash,
                    fall_dataframe.loc[row, 'Price'],
                    A_stock_amount,
                    total_money,
                    given_reason
                ],
                    index = daily_report_columns),
                    ignore_index = True
            )
            #this is to give an individual ID to each row in report_dataframe
            csv_index += 1
            


        #now we decide the fate of the stable stocks
        #whether or not they have an overall positive percent changes will help decide whether we sell half or all
        for row in stable_dataframe.index:
            decision = 0
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

        #now we decide how much we sell, either half if it has a good history, or all if it doesn't
        for row in stable_dataframe.index:
            if stable_dataframe.loc[row, 'Decision'] == 1:
                orig_stock = A_stock_amount
                stock_in_half = math.floor( orig_stock / 2  )

                #a special exception must be made if there is only 1 stock left
                if orig_stock == 1:
                    stock_in_half = 1 #this is needed for given_reason
                    A_stock_amount = 0
                    cash_in_stock = 0
                    liquid_cash += stable_dataframe.loc[row, 'Price']
                else:
                    A_stock_amount -= stock_in_half
                    cash_in_stock = ( float( A_stock_amount ) ) * stable_dataframe.loc[row, 'Price']
                    liquid_cash +=  ( float( stock_in_half) ) * stable_dataframe.loc[row, 'Price']
                total_money = cash_in_stock + liquid_cash

                given_reason = f"Sold half, {stock_in_half}, of stock {stable_dataframe.loc[row, 'Ticker']} at {stable_dataframe.loc[row, 'Price']} because it's platued for the past 3 days and it has an okay recent history. New total is {total_money}"
                action = "SELL"

                #again, depending if we actually sold anything will determine whether what we write
                if orig_stock == 0:
                    action = "HOLD"
                    given_reason = f"Didn't do anything for {stable_dataframe.loc[row, 'Ticker']} since it's stable and has a decent history and we have own none of its stocks"

                report_dataframe = report_dataframe.append(
                pd.Series(
                [
                    csv_index,
                    A_stock_xl.loc[day, 'Date'],
                    liquid_cash,
                    stable_dataframe.loc[row, 'Price'],
                    A_stock_amount,
                    total_money,
                    given_reason
                ],
                    index = daily_report_columns),
                    ignore_index = True
                )
                csv_index += 1
                #if it doesn't have a good recent history, we'll sell all, expecting it to go down
            else:
                orig_stock = A_stock_amount
                A_stock_amount = 0
                cash_in_stock = 0
                liquid_cash +=  float( orig_stock) * stable_dataframe.loc[row, 'Price']
                total_money = liquid_cash + cash_in_stock

                given_reason = f"Sold all {orig_stock}, of stock {stable_dataframe.loc[row, 'Ticker']} at {stable_dataframe.loc[row, 'Price']} because it's platued for the past 3 days, but it has a poor recent history. New total is {total_money}"
                action = "SELL"

                if orig_stock == 0:
                    action = "HOLD"
                    given_reason = f"Didn't do anything for {stable_dataframe.loc[row, 'Ticker']} since it's stable and has a bad history and we have own none of its stocks"

                report_dataframe = report_dataframe.append(
                pd.Series(
                [
                    csv_index,
                    A_stock_xl.loc[day, 'Date'],
                    liquid_cash,
                    stable_dataframe.loc[row, 'Price'],
                    A_stock_amount,
                    total_money,   
                    given_reason                 
                ],
                    index = daily_report_columns),
                    ignore_index = True
                )
                csv_index += 1


        #if it's growing for the past 3 days, we want to buy as much as possible
        #we must check these first to prevent divide by zero errors
        if(len(grow_dataframe.index) != 0 and liquid_cash != 0):
            #divvied_up_cash might be redundant, since we only have one stock
            #but it's important to keep this as similar to the orignal algorithm as poosible
            divvied_up_cash = liquid_cash / len(grow_dataframe.index)
            for row in grow_dataframe.index:
                orig_stock = A_stock_amount
                new_amount_to_buy = math.floor(divvied_up_cash/grow_dataframe.loc[row, 'Price'])
                liquid_cash -= ( new_amount_to_buy * grow_dataframe.loc[row, 'Price'])
                A_stock_amount = A_stock_amount + new_amount_to_buy
                cash_in_stock = ( A_stock_amount * grow_dataframe.loc[row, 'Price'])
                total_money = liquid_cash + cash_in_stock

                given_reason = f"Bought {new_amount_to_buy} of {grow_dataframe.loc[row, 'Ticker']} for {grow_dataframe.loc[row, 'Price']} because it's been growing for the past 3 days. New total is {total_money}"
                action = "BUY"

                if new_amount_to_buy == 0:
                    given_reason = f"Didn't do buy any of {grow_dataframe.loc[row, 'Ticker']} even though it's growing because we don't currently have the money"
                    action = "HOLD"

                report_dataframe = report_dataframe.append(
                pd.Series(
                [
                    csv_index,
                    A_stock_xl.loc[day, 'Date'],
                    liquid_cash,
                    grow_dataframe.loc[row, 'Price'],
                    A_stock_amount,
                    total_money,
                    given_reason
                ],
                    index = daily_report_columns),
                    ignore_index = True
                )
                csv_index += 1
               

    #overall_gain started the beginning of the program at 0, every time a stock file is done, it will add the difference
    #of the final total minus the original and will print out the ultimate cash difference
    overall_gain += (total_money - 10000)
    print(total_money)
    print(report_dataframe)
            
    writer = pd.ExcelWriter(str(current_xl).replace(".csv", "") + '_test_report.xlsx', engine='xlsxwriter')
    report_dataframe.to_excel(writer, sheet_name = "daily_report", index = False)
    writer.save()

print(overall_gain)
    