import requests

HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

# DexScreener token addresses
TOKENS = {
    "ETH": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",  # WETH on Ethereum
    "SOL": "So11111111111111111111111111111111111111112"   # Wrapped SOL
}

def get_prices():
    try:
        prices = {}

        # ETH price
        eth_url = f"https://api.dexscreener.com/latest/dex/tokens/{TOKENS['ETH']}"
        eth_res = requests.get(eth_url, headers=HEADERS, timeout=10).json()
        eth_pair = eth_res["pairs"][0]
        prices["ETH"] = {
            "price": float(eth_pair["priceUsd"]),
            "change_24h": round(float(eth_pair.get("priceChange", {}).get("h24", 0)), 2)
        }

        # SOL price
        sol_url = f"https://api.dexscreener.com/latest/dex/tokens/{TOKENS['SOL']}"
        sol_res = requests.get(sol_url, headers=HEADERS, timeout=10).json()
        sol_pair = sol_res["pairs"][0]
        prices["SOL"] = {
            "price": float(sol_pair["priceUsd"]),
            "change_24h": round(float(sol_pair.get("priceChange", {}).get("h24", 0)), 2)
        }

        return prices

    except Exception as e:
        return {"error": str(e)}