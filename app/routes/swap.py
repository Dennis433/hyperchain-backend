from flask import Blueprint, jsonify, request
import requests

swap_bp = Blueprint('swap', __name__)

TOKEN_IDS = {
    "SOL": "solana",
    "ETH": "ethereum",
    "USDC": "usd-coin",
    "USDT": "tether",
    "BTC": "bitcoin"
}

@swap_bp.route('/quote', methods=['GET'])
def get_quote():
    from_token = request.args.get('from', 'SOL').upper()
    to_token = request.args.get('to', 'USDC').upper()
    amount = float(request.args.get('amount', 1))

    try:
        from_id = TOKEN_IDS.get(from_token)
        to_id = TOKEN_IDS.get(to_token)

        if not from_id or not to_id:
            return jsonify({
                "error": f"Token not supported. Available: {list(TOKEN_IDS.keys())}"
            }), 400

        url = f"https://api.coingecko.com/api/v3/simple/price?ids={from_id},{to_id}&vs_currencies=usd"
        response = requests.get(url)
        data = response.json()

        from_price = data[from_id]["usd"]
        to_price = data[to_id]["usd"]

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
        ids = ",".join(TOKEN_IDS.values())
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true"
        response = requests.get(url)
        data = response.json()

        tokens = []
        for symbol, cg_id in TOKEN_IDS.items():
            token_data = data.get(cg_id, {})
            tokens.append({
                "symbol": symbol,
                "name": cg_id.replace("-", " ").title(),
                "price_usd": token_data.get("usd", 0),
                "change_24h": round(token_data.get("usd_24h_change", 0), 2)
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