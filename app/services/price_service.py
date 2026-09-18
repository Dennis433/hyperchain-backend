import requests

HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

def get_prices():
    try:
        url = "https://min-api.cryptocompare.com/data/pricemultifull?fsyms=ETH,SOL&tsyms=USD"
        response = requests.get(url, headers=HEADERS, timeout=10)
        data = response.json()
        return {"raw": data}
    except Exception as e:
        return {"error": str(e)}