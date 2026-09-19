from flask import Blueprint, jsonify, request
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


@transactions_bp.route('/recent', methods=['GET'])
def get_recent_tx():
    """
    GET /api/transactions/recent?eth=0x...&sol=...
    Pass one or both wallet addresses as query params.
    Returns up to 20 most recent transactions merged and sorted.
    """
    eth_address = request.args.get('eth', '').strip()
    sol_address = request.args.get('sol', '').strip()

    if not eth_address and not sol_address:
        return jsonify({"error": "Provide at least one address: ?eth=0x... or ?sol=..."}), 400

    all_txs = []

    if eth_address:
        eth_txs = get_eth_transactions(eth_address)
        if isinstance(eth_txs, list):
            for tx in eth_txs:
                tx['chain'] = 'ETH'
            all_txs.extend(eth_txs)

    if sol_address:
        sol_txs = get_sol_transactions(sol_address)
        if isinstance(sol_txs, list):
            for tx in sol_txs:
                tx['chain'] = 'SOL'
            all_txs.extend(sol_txs)

    # Sort newest first
    all_txs.sort(key=lambda x: int(x.get('timestamp', 0)), reverse=True)

    return jsonify({"transactions": all_txs[:20]})
