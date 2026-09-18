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
    fsyms = ",".join(symbols)
    url = f"https://min-api.cryptocompare.com/data/pricemultifull?fsyms={fsyms}&tsyms=USD"
    response = requests.get(url, headers=HEADERS, timeout=10)
    return response.json().get("RAW", {})

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

        from_price = data[from_token]["USD"]["PRICE"]
        to_price = data[to_token]["USD"]["PRICE"]

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
            token_data = data.get(symbol, {}).get("USD", {})
            tokens.append({
                "symbol": symbol,
                "price_usd": token_data.get("PRICE", 0),
                "change_24h": round(token_data.get("CHANGEPCT24HOUR", 0), 2)
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