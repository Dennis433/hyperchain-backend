import requests

HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

def get_prices():
    try:
        url = "https://min-api.cryptocompare.com/data/pricemultifull?fsyms=ETH,SOL&tsyms=USD"
        response = requests.get(url, headers=HEADERS, timeout=10)
        data = response.json()["RAW"]

        return {
            "ETH": {
                "price": data["ETH"]["USD"]["PRICE"],
                "change_24h": round(data["ETH"]["USD"]["CHANGEPCT24HOUR"], 2)
            },
            "SOL": {
                "price": data["SOL"]["USD"]["PRICE"],
                "change_24h": round(data["SOL"]["USD"]["CHANGEPCT24HOUR"], 2)
            }
        }
    except Exception as e:
        return {"error": str(e)}