from flask import Blueprint, jsonify, request
from app.services.eth_service import get_eth_balance, is_connected
from app.services.solana_service import get_sol_balance
from app.services.price_service import get_prices
import requests

wallet_bp = Blueprint('wallet', __name__)

HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

@wallet_bp.route('/balance/<eth_address>/<sol_address>', methods=['GET'])
def get_balance(eth_address, sol_address):
    eth_balance = get_eth_balance(eth_address)
    sol_balance = get_sol_balance(sol_address)
    prices = get_prices()

    return jsonify({
        "ETH": {
            "balance": eth_balance,
            "price_usd": prices["ETH"]["price"],
            "change_24h": prices["ETH"]["change_24h"]
        },
        "SOL": {
            "balance": sol_balance,
            "price_usd": prices["SOL"]["price"],
            "change_24h": prices["SOL"]["change_24h"]
        }
    })

@wallet_bp.route('/prices', methods=['GET'])
def get_token_prices():
    return jsonify(get_prices())

@wallet_bp.route('/connect', methods=['POST'])
def connect_wallet():
    data = request.get_json()
    address = data.get("address")
    return jsonify({
        "message": "Wallet connected successfully",
        "address": address,
        "eth_connected": is_connected()
    })

@wallet_bp.route('/markets', methods=['GET'])
def get_markets():
    try:
        chain = request.args.get('chain', 'all')
        tokens = []

        if chain in ['all', 'solana']:
            sol_url = "https://api.dexscreener.com/latest/dex/search?q=SOL&limit=20"
            sol_res = requests.get(sol_url, headers=HEADERS, timeout=10).json()
            for pair in sol_res.get("pairs", [])[:10]:
                if pair.get("chainId") != "solana":
                    continue
                tokens.append({
                    "name": pair.get("baseToken", {}).get("name", ""),
                    "symbol": pair.get("baseToken", {}).get("symbol", ""),
                    "address": pair.get("baseToken", {}).get("address", ""),
                    "price_usd": float(pair.get("priceUsd", 0) or 0),
                    "change_24h": float((pair.get("priceChange") or {}).get("h24", 0) or 0),
                    "volume_24h": float((pair.get("volume") or {}).get("h24", 0) or 0),
                    "liquidity": float((pair.get("liquidity") or {}).get("usd", 0) or 0),
                    "chain": "solana",
                    "pair_address": pair.get("pairAddress", ""),
                    "dex": pair.get("dexId", ""),
                })

        if chain in ['all', 'ethereum']:
            eth_url = "https://api.dexscreener.com/latest/dex/search?q=ETH&limit=20"
            eth_res = requests.get(eth_url, headers=HEADERS, timeout=10).json()
            for pair in eth_res.get("pairs", [])[:10]:
                if pair.get("chainId") != "ethereum":
                    continue
                tokens.append({
                    "name": pair.get("baseToken", {}).get("name", ""),
                    "symbol": pair.get("baseToken", {}).get("symbol", ""),
                    "address": pair.get("baseToken", {}).get("address", ""),
                    "price_usd": float(pair.get("priceUsd", 0) or 0),
                    "change_24h": float((pair.get("priceChange") or {}).get("h24", 0) or 0),
                    "volume_24h": float((pair.get("volume") or {}).get("h24", 0) or 0),
                    "liquidity": float((pair.get("liquidity") or {}).get("usd", 0) or 0),
                    "chain": "ethereum",
                    "pair_address": pair.get("pairAddress", ""),
                    "dex": pair.get("dexId", ""),
                })

        return jsonify({
            "tokens": tokens,
            "count": len(tokens)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
