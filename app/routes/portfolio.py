from flask import Blueprint, jsonify

portfolio_bp = Blueprint('portfolio', __name__)

@portfolio_bp.route('/<address>', methods=['GET'])
def get_portfolio(address):
    return jsonify({"address": address, "total_value": "$0.00", "tokens": []})