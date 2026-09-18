from flask import Blueprint, jsonify, request
from app.services.eth_service import get_eth_balance, is_connected
from app.services.solana_service import get_sol_balance
from app.services.price_service import get_prices

wallet_bp = Blueprint('wallet', __name__)

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