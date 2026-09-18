from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS

db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    CORS(app)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.wallet import wallet_bp
    from app.routes.portfolio import portfolio_bp
    from app.routes.swap import swap_bp
    from app.routes.transactions import transactions_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(wallet_bp, url_prefix='/api/wallet')
    app.register_blueprint(portfolio_bp, url_prefix='/api/portfolio')
    app.register_blueprint(swap_bp, url_prefix='/api/swap')
    app.register_blueprint(transactions_bp, url_prefix='/api/transactions')

    # Create tables
    with app.app_context():
        db.create_all()

    return app