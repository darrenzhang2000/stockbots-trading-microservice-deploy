import requests

url = "http://localhost:5000/ownedStocks/purchase"

payload='email=testuser%40gmail.com&ticker=TSLA&purchaseAmt=100'
headers = {
  'X-API-KEY': 'Ehmj9CLOzr9TB4gkqCiHp2u8HoZ2JiKC9qVRNeva',
  'Content-Type': 'application/x-www-form-urlencoded'
}

response = requests.request("PUT", url, headers=headers, data=payload)

print(response.text)
