from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.eth_service import get_eth_transactions
from app.services.solana_service import get_sol_transactions
from app.models.user import User  # adjust import to match your actual User model

transactions_bp = Blueprint('transactions', __name__)


@transactions_bp.route('/eth/<address>', methods=['GET'])
def get_eth_tx(address):
    txs = get_eth_transactions(address)
    return jsonify({"chain": "Ethereum", "transactions": txs})


@transactions_bp.route('/sol/<address>', methods=['GET'])
def get_sol_tx(address):
    txs = get_sol_transactions(address)
    return jsonify({"chain": "Solana", "transactions": txs})


@transactions_bp.route('/recent', methods=['GET'])
@jwt_required()
def get_recent_tx():
    """
    Returns recent transactions for the logged-in user's wallet.
    Requires Authorization: Bearer <token> header.
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    all_txs = []

    # Fetch ETH transactions if user has an ETH wallet
    eth_address = getattr(user, 'eth_address', None)
    if eth_address:
        eth_txs = get_eth_transactions(eth_address)
        if isinstance(eth_txs, list):
            for tx in eth_txs:
                tx['chain'] = 'eth'
            all_txs.extend(eth_txs)

    # Fetch SOL transactions if user has a SOL wallet
    sol_address = getattr(user, 'sol_address', None)
    if sol_address:
        sol_txs = get_sol_transactions(sol_address)
        if isinstance(sol_txs, list):
            for tx in sol_txs:
                tx['chain'] = 'sol'
            all_txs.extend(sol_txs)

    # Sort by timestamp descending, most recent first
    all_txs.sort(key=lambda x: int(x.get('timestamp', 0)), reverse=True)

    return jsonify({"transactions": all_txs[:20]})
