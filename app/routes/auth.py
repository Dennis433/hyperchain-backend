from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    return jsonify({"message": "User registered", "user": data.get("username")}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    token = create_access_token(identity=data.get("username"))
    return jsonify({"token": token}), 200