import requests

HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

TOKENS = {
    "ETH": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
    "SOL": "So11111111111111111111111111111111111111112"
}

def find_usd_pair(pairs):
    for pair in pairs:
        quote = pair.get("quoteToken", {}).get("symbol", "").upper()
        if quote in ["USDT", "USDC", "USD"]:
            return pair
    return pairs[0]  # fallback to first pair

def get_prices():
    try:
        prices = {}

        for token, address in TOKENS.items():
            url = f"https://api.dexscreener.com/latest/dex/tokens/{address}"
            res = requests.get(url, headers=HEADERS, timeout=10).json()
            pair = find_usd_pair(res["pairs"])
            prices[token] = {
                "price": float(pair["priceUsd"]),
                "change_24h": round(float(pair.get("priceChange", {}).get("h24", 0)), 2)
            }

        return prices

    except Exception as e:
        return {"error": str(e)}