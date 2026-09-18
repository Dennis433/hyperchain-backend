import requests

COINGECKO_URL = "https://api.coingecko.com/api/v3"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

def get_prices():
    try:
        url = f"{COINGECKO_URL}/simple/price?ids=ethereum,solana&vs_currencies=usd&include_24hr_change=true"
        response = requests.get(url, headers=HEADERS, timeout=10)
        data = response.json()

        if "ethereum" not in data or "solana" not in data:
            return {"error": "CoinGecko rate limited", "raw": data}

        return {
            "ETH": {
                "price": data["ethereum"]["usd"],
                "change_24h": round(data["ethereum"]["usd_24h_change"], 2)
            },
            "SOL": {
                "price": data["solana"]["usd"],
                "change_24h": round(data["solana"]["usd_24h_change"], 2)
            }
        }
    except Exception as e:
        return {"error": str(e)}