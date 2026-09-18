from flask import Blueprint, jsonify
from app.services.eth_service import get_eth_transactions
from app.services.solana_service import get_sol_transactions

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/eth/<address>', methods=['GET'])
def get_eth_tx(address):
    txs = get_eth_transactions(address)
    return jsonify({"chain": "Ethereum", "transactions": txs})

@transactions_bp.route('/sol/<address>', methods=['GET'])
def get_sol_tx(address):
    txs = get_sol_transactions(address)
    return jsonify({"chain": "Solana", "transactions": txs})