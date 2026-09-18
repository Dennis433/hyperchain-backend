import requests

HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

# Correct token addresses for USD pricing
TOKENS = {
    "ETH": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",  # Native ETH
    "SOL": "So11111111111111111111111111111111111111112"   # Native SOL
}

# Fallback addresses if native doesn't work
FALLBACK_TOKENS = {
    "ETH": "0x2170ed0880ac9a755fd29b2688956bd959f933f8",  # ETH on BSC
    "SOL": "So11111111111111111111111111111111111111112"
}

def find_usd_pair(pairs):
    if not pairs:
        return None
    
    # Priority: USDT > USDC > USD > WETH > anything
    priority = ["USDT", "USDC", "USD", "WETH", "WBNB"]
    
    for quote_symbol in priority:
        for pair in pairs:
            quote = pair.get("quoteToken", {}).get("symbol", "").upper()
            if quote == quote_symbol:
                # Make sure price is reasonable
                price = float(pair.get("priceUsd", 0))
                if price > 0.01:  # Filter out tiny prices
                    return pair
    
    # Fallback to first pair with a valid price
    for pair in pairs:
        price = float(pair.get("priceUsd", 0))
        if price > 0.01:
            return pair
    
    return pairs[0]

def get_token_price(token, address):
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{address}"
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        
        pairs = res.get("pairs", [])
        if not pairs:
            return None
            
        pair = find_usd_pair(pairs)
        if not pair:
            return None
            
        price = float(pair.get("priceUsd", 0))
        change = float(pair.get("priceChange", {}).get("h24", 0))
        
        print(f"{token} price: ${price} from pair {pair.get('dexId')} {pair.get('quoteToken', {}).get('symbol')}")
        
        return {
            "price": price,
            "change_24h": round(change, 2)
        }
    except Exception as e:
        print(f"Error fetching {token}: {str(e)}")
        return None

def get_prices():
    try:
        prices = {}

        for token, address in TOKENS.items():
            result = get_token_price(token, address)
            
            # Try fallback address if primary fails or price looks wrong
            if not result or result["price"] < 1:
                print(f"{token} primary failed, trying fallback...")
                fallback = FALLBACK_TOKENS.get(token)
                if fallback and fallback != address:
                    result = get_token_price(token, fallback)
            
            if result:
                prices[token] = result
            else:
                prices[token] = {"price": 0, "change_24h": 0, "error": "Price unavailable"}

        return prices

    except Exception as e:
        return {"error": str(e)}

def get_all_token_prices():
    try:
        all_tokens = {
            "ETH": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
            "SOL": "So11111111111111111111111111111111111111112",
            "BTC": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
            "USDC": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            "USDT": "0xdac17f958d2ee523a2206206994597c13d831ec7"
        }
        
        prices = {}
        for token, address in all_tokens.items():
            result = get_token_price(token, address)
            if result:
                prices[token] = result
                
        return prices
    except Exception as e:
        return {"error": str(e)}
