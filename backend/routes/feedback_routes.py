import uuid
import datetime
from flask import Blueprint, request
from backend.utils.helpers import api_response, api_error
from backend.middleware.auth_middleware import token_required
from backend.services.supabase_service import db

feedback_bp = Blueprint('feedback', __name__, url_prefix='/api')

@feedback_bp.route('/feedback', methods=['GET'])
@token_required
def get_feedback():
    user = request.current_user
    if user.get('role') in ('staff', 'admin'):
        return api_response(db.get_feedback())
    user_fb = db.get_feedback(patient_id=user['id'])
    return api_response(user_fb)

@feedback_bp.route('/feedback', methods=['POST'])
@token_required
def submit_feedback():
    data = request.get_json() or {}
    rating = data.get('overall_rating')
    if not rating or not (1 <= int(rating) <= 5):
        return api_error("Valid overall_rating between 1 and 5 is required", status_code=400)

    user_id = request.current_user['id']
    patient = db.get_profile_by_id(user_id)
    queue_entry_id = data.get('queue_entry_id')

    # Prevent duplicate feedback for the same completed visit
    if queue_entry_id:
        existing_fb = db.get_feedback()
        for f in existing_fb:
            if f.get('queue_entry_id') == str(queue_entry_id):
                return api_error("Feedback for this visit has already been submitted", status_code=409)

    dept = db.get_department_by_id(data.get('department_id')) if data.get('department_id') else None

    fb_entry = {
        "id": str(uuid.uuid4()),
        "patient_id": user_id,
        "patient_name": patient['full_name'] if patient else "Patient",
        "department_id": data.get('department_id'),
        "department_name": dept['name'] if dept else "General",
        "queue_entry_id": queue_entry_id,
        "overall_rating": int(rating),
        "waiting_rating": int(data.get('waiting_rating', rating)),
        "staff_rating": int(data.get('staff_rating', rating)),
        "doctor_rating": int(data.get('doctor_rating', rating)),
        "facility_rating": int(data.get('facility_rating', rating)),
        "comment": data.get('comment', '').strip(),
        "created_at": datetime.datetime.utcnow().isoformat() + "Z"
    }

    # Direct insert into Supabase table feedback
    db.create_feedback(fb_entry)
    return api_response(fb_entry, message="Thank you for your valuable feedback!", status_code=201)

@feedback_bp.route('/waiting-history', methods=['GET'])
@token_required
def get_waiting_history():
    user = request.current_user
    user_id = user['id']
    
    # Retrieve completed queue entries for this user
    all_user_entries = db.get_queue_entries(patient_id=user_id)
    history = [e for e in all_user_entries if e.get('status') == 'completed']
    history.sort(key=lambda x: x.get('completed_at', x.get('joined_at', '')), reverse=True)

    waits = [e.get('estimated_wait_minutes', 15) for e in history]
    total_visits = len(history)
    avg_wait = int(sum(waits) / total_visits) if total_visits > 0 else 0
    shortest_wait = min(waits) if total_visits > 0 else 0
    longest_wait = max(waits) if total_visits > 0 else 0

    return api_response({
        "total_visits": total_visits,
        "average_wait_minutes": avg_wait,
        "shortest_wait_minutes": shortest_wait,
        "longest_wait_minutes": longest_wait,
        "visits": history
    })
