from flask import Blueprint, jsonify, request
import requests

swap_bp = Blueprint('swap', __name__)

HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

TOKEN_IDS = {
    "SOL": "SOL",
    "ETH": "ETH",
    "USDC": "USDC",
    "USDT": "USDT",
    "BTC": "BTC"
}

def get_crypto_prices(symbols):
    prices = {}
    for symbol in symbols:
        if symbol in ["USDC", "USDT"]:
            prices[symbol] = {"price": 1.0, "change_24h": 0.0}
            continue
        try:
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}USDT"
            response = requests.get(url, headers=HEADERS, timeout=10)
            data = response.json()
            prices[symbol] = {
                "price": float(data["lastPrice"]),
                "change_24h": round(float(data["priceChangePercent"]), 2)
            }
        except:
            prices[symbol] = {"price": 0, "change_24h": 0}
    return prices

@swap_bp.route('/quote', methods=['GET'])
def get_quote():
    from_token = request.args.get('from', 'SOL').upper()
    to_token = request.args.get('to', 'USDC').upper()
    amount = float(request.args.get('amount', 1))

    try:
        if from_token not in TOKEN_IDS or to_token not in TOKEN_IDS:
            return jsonify({
                "error": f"Token not supported. Available: {list(TOKEN_IDS.keys())}"
            }), 400

        data = get_crypto_prices([from_token, to_token])

        from_price = data[from_token]["price"]
        to_price = data[to_token]["price"]

        rate = from_price / to_price
        amount_out = round(amount * rate, 6)
        fee = round(amount_out * 0.003, 6)
        amount_after_fee = round(amount_out - fee, 6)

        return jsonify({
            "from": from_token,
            "to": to_token,
            "amount_in": amount,
            "amount_out": amount_after_fee,
            "rate": round(rate, 6),
            "fee": f"{fee} {to_token}",
            "from_price_usd": f"${from_price}",
            "to_price_usd": f"${to_price}",
            "price_impact": "< 0.01%",
            "slippage": "0.5%",
            "provider": "HyperChain DEX"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@swap_bp.route('/execute', methods=['POST'])
def execute_swap():
    data = request.get_json()
    from_token = data.get("from")
    to_token = data.get("to")
    amount = data.get("amount")

    return jsonify({
        "message": "Swap initiated successfully",
        "from": from_token,
        "to": to_token,
        "amount": amount,
        "status": "pending",
        "tx_hash": "0x0000000000000000000000000000000000000000",
        "note": "Sign transaction in your wallet to complete"
    })

@swap_bp.route('/tokens', methods=['GET'])
def get_supported_tokens():
    try:
        symbols = list(TOKEN_IDS.keys())
        data = get_crypto_prices(symbols)

        tokens = []
        for symbol in symbols:
            token_data = data.get(symbol, {})
            tokens.append({
                "symbol": symbol,
                "price_usd": token_data.get("price", 0),
                "change_24h": token_data.get("change_24h", 0)
            })

        return jsonify({
            "supported_tokens": tokens,
            "provider": "HyperChain DEX"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@swap_bp.route('/history', methods=['GET'])
def swap_history():
    return jsonify({
        "swaps": [],
        "message": "Connect wallet to see swap history"
    })