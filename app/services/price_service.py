import requests

HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

def get_prices():
    try:
        symbols = ["ETHUSDT", "SOLUSDT"]
        prices = {}

        for symbol in symbols:
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
            response = requests.get(url, headers=HEADERS, timeout=10)
            data = response.json()
            token = symbol.replace("USDT", "")
            prices[token] = {
                "price": float(data["lastPrice"]),
                "change_24h": round(float(data["priceChangePercent"]), 2)
            }

        return prices

    except Exception as e:
        return {"error": str(e)}