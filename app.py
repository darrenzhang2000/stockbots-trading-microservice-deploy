from flask import Flask
import requests
from both_algos import stockActions
import time
from dotenv import load_dotenv
import os
from flask import Flask
import threading

load_dotenv()

IEX_API_KEY = os.environ['IEX_API_KEY']
BACKEND_API = os.environ['BACKEND_API']

def getPortfolios():
    url = f"{BACKEND_API}/portfolios/all"

    payload={}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload).json()

    portfolios = response['portfolios']

    return portfolios

def runAlgoJob():
    print('running algo job')
    time.sleep(86400)
    portfolios = getPortfolios()
    emails = [p["email"] for p in portfolios]
    for email in emails:
        stockActions(['GOOGL', 'TSLA', 'FB', 'MSFT'], email)

    runAlgoJob()


thread1 = threading.Thread(target=runAlgoJob)
thread1.run()

if __name__ == '__main__':
    app = Flask(__name__)
    app.run(port=9000)