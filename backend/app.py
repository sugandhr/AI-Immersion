import os
from pathlib import Path
from flask import Flask, send_from_directory, redirect
from flask_cors import CORS

from backend.config import Config
from backend.utils.helpers import api_error, api_response

# Import Blueprints
from backend.routes.auth_routes import auth_bp
from backend.routes.profile_routes import profile_bp
from backend.routes.queue_routes import queue_bp
from backend.routes.appointment_routes import appointment_bp
from backend.routes.department_routes import dept_bp
from backend.routes.doctor_routes import doctor_bp
from backend.routes.lab_routes import lab_bp
from backend.routes.billing_routes import billing_bp
from backend.routes.notification_routes import notification_bp
from backend.routes.navigation_routes import navigation_bp
from backend.routes.feedback_routes import feedback_bp
from backend.routes.analytics_routes import analytics_bp
from backend.routes.ai_routes import ai_bp

def create_app():
    base_dir = Path(__file__).resolve().parent.parent
    frontend_dir = base_dir / "frontend"
    css_dir = base_dir / "css"
    js_dir = base_dir / "js"

    app = Flask(__name__, static_folder=str(frontend_dir))
    app.config.from_object(Config)

    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(queue_bp)
    app.register_blueprint(appointment_bp)
    app.register_blueprint(dept_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(lab_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(navigation_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(ai_bp)

    # Healthcheck Endpoint
    @app.route('/api/health', methods=['GET'])
    def healthcheck():
        return api_response({
            "status": "healthy",
            "service": "SmartCare Queue AI Backend",
            "supabase_connected": Config.IS_SUPABASE_CONFIGURED,
            "version": "1.0.0"
        }, message="Service operational")

    # Static Assets & Frontend Routing
    @app.route('/')
    def index():
        return send_from_directory(str(frontend_dir), 'index.html')

    @app.route('/<path:filename>')
    def serve_frontend_or_static(filename):
        # 1. Check in frontend/
        if (frontend_dir / filename).exists():
            return send_from_directory(str(frontend_dir), filename)
        # 2. Check in css/
        if filename.startswith('css/') and (base_dir / filename).exists():
            return send_from_directory(str(base_dir), filename)
        # 3. Check in js/
        if filename.startswith('js/') and (base_dir / filename).exists():
            return send_from_directory(str(base_dir), filename)
        
        # If accessing root html pages directly
        if (frontend_dir / f"{filename}.html").exists():
            return send_from_directory(str(frontend_dir), f"{filename}.html")

        return api_error("Resource not found", status_code=404)

    # Error Handlers
    @app.errorhandler(404)
    def handle_404(e):
        return api_error("Requested API endpoint not found", status_code=404)

    @app.errorhandler(500)
    def handle_500(e):
        return api_error("Internal server error", status_code=500)

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5002))
    print(f"[SmartCare AI] Starting Flask server on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
