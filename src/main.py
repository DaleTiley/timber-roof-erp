import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

# Import configuration - Added 2025-01-07 for Azure SQL support
from src.config import config

from src.models.user import db
from src.routes.user import user_bp
from src.routes.customer import customer_bp
from src.routes.contact import contact_bp
from src.routes.stock import stock_bp
from src.routes.quote_pricing import quote_pricing_bp

def create_app(config_name=None):
    """
    Application factory pattern
    Added: 2025-01-07 - Support for different configurations (dev/prod/azure)
    """
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    # Load configuration
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    
    # Enable CORS for all routes
    CORS(app)
    
    # Initialize database
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(customer_bp, url_prefix='/api')
    app.register_blueprint(contact_bp, url_prefix='/api')
    app.register_blueprint(stock_bp, url_prefix='/api')
    app.register_blueprint(quote_pricing_bp)
    
    # Create tables
    with app.app_context():
        db.create_all()
        
        # Seed initial data if needed
        try:
            from src.seed_data import seed_initial_data
            seed_initial_data()
        except Exception as e:
            print(f"Note: Could not seed data - {e}")
    
    # Health check endpoint - Added 2025-01-07
    @app.route('/api/health')
    def health_check():
        """Health check endpoint for deployment monitoring"""
        return jsonify({
            'status': 'healthy',
            'app_name': app.config.get('APP_NAME', 'Timber Roof ERP'),
            'version': app.config.get('APP_VERSION', '1.0.0'),
            'database': 'connected' if db.engine else 'disconnected'
        })
    
    return app

# Create app instance
app = create_app()

# Original routes preserved for compatibility
db.init_app(app)

# Import all models to ensure they are registered
from src.models.customer import Customer
from src.models.contact import Contact
from src.models.stock import StockItem, StockType, UnitOfMeasure, MarginGroup, DiscountGroup, CommissionGroup

with app.app_context():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

