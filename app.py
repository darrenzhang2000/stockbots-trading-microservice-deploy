import requests
from both_algos import stockActions
import time
from dotenv import load_dotenv
import os

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
    url = f"{BACKEND_API}/users/register"

    payload='email=aaaa%40gmail.com&password=aaa&firstName=a&lastName=a'
    headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)
    time.sleep(86400)
    
    portfolios = getPortfolios()
    emails = [p["email"] for p in portfolios]
    for email in emails:
        stockActions(['GOOGL', 'TSLA', 'FB', 'MSFT'], email)

    runAlgoJob()



if __name__ == '__main__':
    runAlgoJob()
