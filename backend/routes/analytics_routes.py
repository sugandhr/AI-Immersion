from flask import Blueprint
from backend.utils.helpers import api_response
from backend.middleware.auth_middleware import token_required
from backend.middleware.role_middleware import require_role
from backend.services.analytics_service import AnalyticsService
from backend.services.prediction_service import PredictionService

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

@analytics_bp.route('/dashboard', methods=['GET'])
@token_required
@require_role(['staff', 'doctor', 'admin'])
def get_dashboard_metrics():
    metrics = AnalyticsService.get_dashboard_metrics()
    return api_response(metrics)

@analytics_bp.route('/departments', methods=['GET'])
@token_required
@require_role(['staff', 'doctor', 'admin'])
def get_department_analytics():
    metrics = AnalyticsService.get_dashboard_metrics()
    return api_response(metrics.get("department_breakdown", []))

@analytics_bp.route('/peak-hours', methods=['GET'])
@token_required
@require_role(['staff', 'doctor', 'admin'])
def get_peak_hours():
    metrics = AnalyticsService.get_dashboard_metrics()
    return api_response(metrics.get("hourly_traffic", []))

@analytics_bp.route('/ai-insights', methods=['GET'])
@token_required
@require_role(['staff', 'doctor', 'admin'])
def get_operational_insights():
    insights = PredictionService.get_ai_insights()
    return api_response(insights)
