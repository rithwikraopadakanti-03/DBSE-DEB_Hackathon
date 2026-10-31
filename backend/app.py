import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import Config
from database import init_db, check_db_connection
from ml_classifier import classifier
from routes.auth import auth_bp
from routes.complaints import complaints_bp
from routes.admin import admin_bp
from routes.departments import departments_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def create_app():
    """Application factory for Campus Complaint Management System."""
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Enable CORS for frontend applications (default: http://localhost:5173)
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    CORS(
        app,
        resources={r"/api/*": {"origins": allowed_origins}},
        supports_credentials=True,
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"]
    )

    # Initialize JWT Manager
    jwt = JWTManager(app)

    @jwt.unauthorized_loader
    def unauthorized_response(callback):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authorization header with Bearer token is missing or invalid'
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_response(callback):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'The provided authentication token is invalid'
        }), 401

    @jwt.expired_token_loader
    def expired_token_response(jwt_header, jwt_payload):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication token has expired. Please log in again.'
        }), 401

    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(complaints_bp, url_prefix='/api/complaints')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(departments_bp, url_prefix='/api/departments')

    # Root endpoint
    @app.route('/', methods=['GET'])
    def root():
        return jsonify({
            'name': 'Campus Complaint Management System API',
            'version': '1.0.0',
            'endpoints': {
                'health': '/api/health',
                'auth': '/api/auth',
                'complaints': '/api/complaints',
                'admin': '/api/admin',
                'departments': '/api/departments'
            }
        }), 200

    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        db_connected = check_db_connection()
        ml_ready = classifier is not None and classifier.category_pipeline is not None

        return jsonify({
            'status': 'healthy' if db_connected else 'degraded',
            'message': 'Campus Complaint Management System API is active',
            'database': 'connected' if db_connected else 'disconnected',
            'ml_classifier': 'ready' if ml_ready else 'offline',
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    # Global 404 handler
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not Found', 'message': 'The requested resource was not found'}), 404

    # Global 500 handler
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({'error': 'Server Error', 'message': 'An unexpected error occurred'}), 500

    # Initialize Database Indexes
    with app.app_context():
        try:
            init_db()
        except Exception as e:
            logger.warning(f"Database initialization warning on startup: {e}")

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', '1') == '1'
    logger.info(f"Starting Campus Complaint System API on http://localhost:{port} (debug={debug})")
    app.run(host='0.0.0.0', port=port, debug=debug)
