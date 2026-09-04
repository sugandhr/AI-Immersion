import uuid
import datetime
from flask import Blueprint, request
from backend.utils.helpers import api_response, api_error
from backend.utils.validators import validate_required_fields
from backend.middleware.auth_middleware import token_required
from backend.middleware.role_middleware import require_role
from backend.services.queue_service import QueueService
from backend.services.supabase_service import db

queue_bp = Blueprint('queue', __name__, url_prefix='/api')

@queue_bp.route('/queues', methods=['GET'])
def get_all_queues():
    result = []
    for q in db.get_all_queues():
        details = QueueService.get_queue_details(q["id"])
        if details:
            result.append(details)
    return api_response(result)

@queue_bp.route('/queues/<queue_id>', methods=['GET'])
def get_queue_by_id(queue_id):
    details = QueueService.get_queue_details(queue_id)
    if not details:
        return api_error("Queue not found", status_code=404)
    return api_response(details)

@queue_bp.route('/queues/join', methods=['POST'])
@token_required
def join_queue_generic():
    data = request.get_json() or {}
    ok, err = validate_required_fields(data, ['department_id'])
    if not ok:
        return api_error(err, status_code=400)

    department_id = data['department_id']
    service_type = data.get('service_type', 'Consultation')
    doctor_id = data.get('doctor_id')
    patient_id = request.current_user['id']

    success, msg, res_data = QueueService.join_queue(
        patient_id=patient_id,
        department_id=department_id,
        service_type=service_type,
        doctor_id=doctor_id
    )

    if not success:
        return api_error(msg, status_code=409)

    return api_response(res_data, message=msg, status_code=201)

@queue_bp.route('/queues/<queue_id>/join', methods=['POST'])
@token_required
def join_queue_by_id(queue_id):
    all_queues = db.get_all_queues()
    queue = next((q for q in all_queues if str(q["id"]) == str(queue_id)), None)
    if not queue:
        return api_error("Queue not found", status_code=404)

    data = request.get_json() or {}
    patient_id = request.current_user['id']
    doctor_id = data.get('doctor_id')

    success, msg, res_data = QueueService.join_queue(
        patient_id=patient_id,
        department_id=queue['department_id'],
        service_type=queue['service_type'],
        doctor_id=doctor_id
    )

    if not success:
        return api_error(msg, status_code=409)

    return api_response(res_data, message=msg, status_code=201)

@queue_bp.route('/queue-entry/active', methods=['GET'])
@token_required
def get_active_patient_queue():
    patient_id = request.current_user['id']
    active_data = QueueService.get_active_entry_for_patient(patient_id)
    if not active_data:
        return api_response(None, message="No active queue entry found")
    return api_response(active_data)

@queue_bp.route('/queue-entry/<entry_id>/cancel', methods=['POST'])
@token_required
def cancel_queue_entry(entry_id):
    patient_id = request.current_user['id']
    entry = db.get_queue_entry_by_id(entry_id)
    if not entry:
        return api_error("Queue entry not found", status_code=404)

    if str(entry["patient_id"]) != str(patient_id) and request.current_user.get("role") not in ("staff", "admin"):
        return api_error("Unauthorized to cancel this queue entry", status_code=403)

    # Updates directly in Supabase queue_entries
    updated = db.update_queue_entry(entry_id, {"status": "cancelled"})
    return api_response(updated or entry, message="Queue entry cancelled successfully")

# Staff Operational Endpoints
@queue_bp.route('/queues/<queue_id>/next', methods=['POST'])
@token_required
@require_role(['staff', 'doctor', 'admin'])
def staff_call_next(queue_id):
    data = request.get_json() or {}
    counter = data.get('counter_number', 'Counter 1')
    success, msg, entry = QueueService.call_next(queue_id, counter)
    if not success:
        return api_error(msg, status_code=400)
    return api_response(entry, message=msg)

@queue_bp.route('/queue-entry/<entry_id>/call', methods=['POST'])
@token_required
@require_role(['staff', 'doctor', 'admin'])
def staff_call_specific(entry_id):
    data = request.get_json() or {}
    counter = data.get('counter_number', 'Counter 1')
    success, msg, entry = QueueService.recall_entry(entry_id, counter)
    if not success:
        return api_error(msg, status_code=404)
    return api_response(entry, message=msg)

@queue_bp.route('/queue-entry/<entry_id>/serving', methods=['POST'])
@token_required
@require_role(['staff', 'doctor', 'admin'])
def staff_start_serving(entry_id):
    success, msg, entry = QueueService.start_serving(entry_id)
    if not success:
        return api_error(msg, status_code=404)
    return api_response(entry, message=msg)

@queue_bp.route('/queue-entry/<entry_id>/complete', methods=['POST'])
@token_required
@require_role(['staff', 'doctor', 'admin'])
def staff_complete(entry_id):
    success, msg, entry = QueueService.complete_entry(entry_id)
    if not success:
        return api_error(msg, status_code=404)
    return api_response(entry, message=msg)

@queue_bp.route('/queue-entry/<entry_id>/skip', methods=['POST'])
@token_required
@require_role(['staff', 'doctor', 'admin'])
def staff_skip(entry_id):
    success, msg, entry = QueueService.skip_entry(entry_id)
    if not success:
        return api_error(msg, status_code=404)
    return api_response(entry, message=msg)

@queue_bp.route('/queue-entry/<entry_id>/priority', methods=['POST'])
@token_required
def request_priority(entry_id):
    data = request.get_json() or {}
    reason = data.get('reason', 'Senior Citizen / Mobility Assistance')
    patient_id = request.current_user['id']
    entry = db.get_queue_entry_by_id(entry_id)
    if not entry:
        return api_error("Queue entry not found", status_code=404)

    if str(entry["patient_id"]) != str(patient_id):
        return api_error("Unauthorized", status_code=403)

    # Updates queue entry in Supabase
    updated_entry = db.update_queue_entry(entry_id, {
        "priority_requested": True,
        "priority_approved": True
    })

    # Stores priority request in Supabase priority_requests table
    db.create_priority_request({
        "id": str(uuid.uuid4()),
        "patient_id": patient_id,
        "queue_entry_id": str(entry_id),
        "reason": reason,
        "status": "approved",
        "created_at": datetime.datetime.utcnow().isoformat() + "Z"
    })

    return api_response(updated_entry or entry, message="Priority request submitted and noted.")
