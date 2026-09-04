from flask import Blueprint, request
from backend.utils.helpers import api_response, api_error
from backend.middleware.auth_middleware import token_required
from backend.services.notification_service import NotificationService

notification_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

@notification_bp.route('', methods=['GET'])
@token_required
def get_user_notifications():
    user_id = request.current_user['id']
    notes = NotificationService.get_user_notifications(user_id)
    return api_response(notes)

@notification_bp.route('/<note_id>/read', methods=['PUT'])
@token_required
def mark_notification_read(note_id):
    user_id = request.current_user['id']
    ok = NotificationService.mark_read(note_id, user_id)
    if not ok:
        return api_error("Notification not found", status_code=404)
    return api_response(None, message="Marked as read")

@notification_bp.route('/read-all', methods=['POST'])
@token_required
def mark_all_notifications_read():
    user_id = request.current_user['id']
    count = NotificationService.mark_all_read(user_id)
    return api_response({"updated": count}, message=f"Marked {count} notifications as read")
