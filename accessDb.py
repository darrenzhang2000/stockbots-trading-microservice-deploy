import requests

def getPortfolios():
    url = "http://localhost:5000/portfolios/all"

    payload={}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload).json()

    portfolios = response['portfolios']

    return portfolios
