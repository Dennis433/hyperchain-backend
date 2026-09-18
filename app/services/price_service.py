import requests

COINGECKO_URL = "https://api.coingecko.com/api/v3"

def get_prices():
    try:
        url = f"{COINGECKO_URL}/simple/price?ids=ethereum,solana&vs_currencies=usd&include_24hr_change=true"
        response = requests.get(url)
        data = response.json()
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
        return f"Error: {str(e)}"